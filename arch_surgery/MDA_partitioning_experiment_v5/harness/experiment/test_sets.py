"""The census test sets: the stage that measures them, and the artifact they become.

V5 converges every block loop on the components of the coupling state the
loop **carries** — the read-before-write set measured at run time in the
arm's own execution order (decision D32; V5 plan §3) — instead of on the
block's whole write set (V4's predicate, kept as the fallback under D39).
This module is the stage that measures those sets and writes them as the
committed artifact ``harness/data/test_sets_<configuration>.json`` the
driver binds under ``PROCESS_ARCH_TEST_SET=census``.

What the stage does (``experiment_runner.py --census``)
-------------------------------------------------------
1. **Runs the census** on the optimisation runs of the census job set: seeds
   0 and 1, every configuration, every iterating optimisation arm active on it
   (``B0``, ``B1``, ``B2``; ``B1`` where the configuration is pulsed), with the
   read-before-write instrument installed in the child
   (:mod:`harness.child.read_before_write_census`).  **Under the fallback
   predicate**: the census is observation-only, and it is taken on runs that
   test V4's whole write set at V4's tolerance, so that every censused run
   has an uncensused twin it must reproduce.
2. **Checks the instrument is observation-only**: each censused run against
   its twin — the same job without the instrument — on status, the
   optimiser's exit code, its iterations, the evaluation count, the
   solve-phase node calls and ``norm_objf`` to the bit.  A difference is a
   result and the stage fails.
3. **Unions** the per-run sets over the two seeds, per configuration, arm and
   block, and **compares** them with the two prior populations committed in
   ``harness/data/``: A89's eight-entry sets (displaced entries of the
   evaluation-phase arms) and A92's optimisation-path sets (whole
   optimisations on V4's copy).  The binding population of a block is the
   census union **unioned with the prior optimisation-path set of the twin
   arm** where one exists (the brief's rule: A92's sets — which contain A89's
   and the four cold-start components — are the starting population, verified
   by re-deriving); the delta against each prior is reported by name.
4. **Writes** one artifact per configuration, keyed by **loop key** —
   ``<mda>/<burn-time owner>`` as the driver resolves them, which is how the
   driver, which never knows an arm's name, selects the sets for the loop it
   runs — with the provenance of every record the sets were derived from.
   The artifact goes under ``runs/census_test_sets/`` and, with ``--census
   write``, into ``harness/data/`` where it is committed; the ``artifacts``
   check validates it there (``artifacts._check_test_sets``).

A block the census never saw sweep has **no entry** for the loop key, and the
driver then tests nothing in it: such a block converges at its first pass.
The artifact records the blocks each loop key carries so that a reader sees
which blocks were observed; the README says the same.

Task **A100 (v5-test-set)**; the machinery is A89's ``run_trial.py
--derive-rbw`` and A92's ``optimisation_path_census.py --census
--summarise-census``, made a harness stage.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Mapping, Sequence

from ..child import read_before_write_census as census_mod
from ..core import framework
from ..core import pool as pool_mod
from ..core import records as records_mod
from ..core.config import (
    Campaign,
    Config,
    TAU_BY_TEST_SET,
    V4_TEST_SET,
)
from ..core.framework import GateError
from . import arms as arms_mod
from .artifacts import StageCheck, rebuild_components_sha256, sha256_of

FORMAT = "census-test-sets-1"

#: The seeds the census is taken over: the input file's own start and the
#: first displaced one (A92's choice, kept).
CENSUS_SEEDS: tuple[int, ...] = (0, 1)

#: The iterating optimisation arms the census runs, in the matrix's order.
CENSUS_ARMS: tuple[str, ...] = ("B0", "B1", "B2")

#: Which optimisation arm's census an evaluation-phase arm binds: the same
#: loop shape in the phase that has an optimiser (A92's twin rule, extended
#: to the ownership rung by A100).
TWIN_OF: dict[str, str] = {"A0": "B0", "A1": "B1", "A2": "B2"}

#: The two prior populations, committed in ``harness/data/`` with their own
#: source commits (the ``data`` gate checks them): A89's eight-entry sets and
#: A92's optimisation-path sets.
PRIOR_EIGHT_ENTRY = "test_set_prior_eight_entry.json"
PRIOR_OPTIMISATION_PATH = "test_set_prior_optimisation_path.json"

#: The twin arms as the priors name them (A89 censused the evaluation-phase
#: arms; A92 the optimisation-phase ones).
PRIOR_EIGHT_ENTRY_ARM: dict[str, str] = {"B0": "A0", "B2": "A2"}
PRIOR_PATH_ARM: dict[str, str] = {"B0": "B0", "B2": "B2"}

#: Where the stage's own records go, relative to ``runs/``.
RUNS_SUBPATH = "census_test_sets"

#: The six fields a censused run must reproduce from its twin, and where each
#: is read from.
REPRODUCTION_FIELDS: tuple[tuple[str, str], ...] = (
    ("status", "status"),
    ("ifail", "mfile.ifail"),
    ("n_solver_iterations", "n_solver_iterations"),
    ("n_evaluations", "sweeps_per_eval.n_evaluations"),
    ("node_calls_solve_phase", "node_calls_solve_phase"),
    ("norm_objf_hex", "exact.norm_objf"),
)


class TestSetError(GateError):
    """The stage refusing, with the reason."""


# --------------------------------------------------------------------------
# the job set
# --------------------------------------------------------------------------


def census_campaign(campaign: Campaign) -> Campaign:
    """The campaign the census runs under: the fallback predicate, by construction.

    The census observes runs that stop on V4's whole write set at V4's
    tolerance, whatever the campaign it is pressed from composes; a job's test
    set is the campaign's, so the stage builds the fallback campaign rather
    than overriding jobs one by one.
    """
    if campaign.test_set == V4_TEST_SET and campaign.tau == TAU_BY_TEST_SET[V4_TEST_SET]:
        return campaign
    return replace(campaign, test_set=V4_TEST_SET, tau=None)


@dataclass(frozen=True)
class CensusPair:
    config: Config
    arm: str
    seed: int
    twin: pool_mod.Job
    censused: pool_mod.Job


def census_pairs(campaign: Campaign) -> list[CensusPair]:
    """One pair per configuration, active census arm and seed."""
    under = census_campaign(campaign)
    pairs: list[CensusPair] = []
    for config in under.configurations:
        for arm in CENSUS_ARMS:
            if arm in config.skips:
                continue
            for seed in CENSUS_SEEDS:
                common = dict(
                    phase="B",
                    arm=arm,
                    config=config,
                    seed=seed,
                    regime="perturbed" if seed != 0 else "unperturbed",
                    delta=under.delta,
                    run_kind="gate",
                )
                pairs.append(
                    CensusPair(
                        config,
                        arm,
                        seed,
                        twin=pool_mod.Job(
                            **common, override_env={census_mod.VARIABLE: census_mod.OFF}
                        ),
                        censused=pool_mod.Job(
                            **common, override_env={census_mod.VARIABLE: census_mod.ON}
                        ),
                    )
                )
    return pairs


def jobs_read(campaign: Campaign) -> list[pool_mod.Job]:
    """Every job the stage reads: both members of every pair."""
    jobs: list[pool_mod.Job] = []
    for pair in census_pairs(campaign):
        jobs.append(pair.twin)
        jobs.append(pair.censused)
    return jobs


# --------------------------------------------------------------------------
# the derivation
# --------------------------------------------------------------------------


def loop_key(arm: str, config: Config) -> str:
    """The key the driver selects a loop's sets by: ``<mda>/<burn-time owner>``."""
    return arms_mod.ARMS[arm].loop_key(config)


def _value(record: Mapping[str, Any], path: str) -> Any:
    return records_mod.resolve_path(record, path) if records_mod.has_path(record, path) else None


def reproduction_row(pair: CensusPair, campaign: Campaign) -> dict[str, Any]:
    """The censused run against its twin on the six declared fields."""
    twin_dir = pool_mod.directory_for(pair.twin, campaign)
    census_dir = pool_mod.directory_for(pair.censused, campaign)
    twin = records_mod.read(twin_dir)
    censused = records_mod.read(census_dir)
    fields: dict[str, dict[str, Any]] = {}
    identical = True
    for label, path in REPRODUCTION_FIELDS:
        a, b = _value(twin, path), _value(censused, path)
        same = a == b
        identical = identical and same
        fields[label] = {"twin": a, "censused": b, "identical": same}
    return {
        "configuration": pair.config.name,
        "arm": pair.arm,
        "seed": pair.seed,
        "twin": {
            "path": str(twin_dir),
            "tree_git_head": twin.get("tree_git_head"),
            "job_digest": twin.get("job_digest"),
        },
        "censused": {
            "path": str(census_dir),
            "tree_git_head": censused.get("tree_git_head"),
            "job_digest": censused.get("job_digest"),
            "census_file": str(census_dir / census_mod.FILE),
        },
        "fields": fields,
        "identical": identical,
    }


def read_census(directory: Path) -> dict[str, Any]:
    path = Path(directory) / census_mod.FILE
    if not path.exists():
        raise TestSetError(
            f"no census file at {path}: the censused run wrote no "
            f"{census_mod.FILE}, so there is no set to derive from"
        )
    census = json.loads(path.read_text())
    if census.get("format") != census_mod.FORMAT:
        raise TestSetError(
            f"{path} has format {census.get('format')!r}, not {census_mod.FORMAT!r}"
        )
    return census


def _sets_sha256(sets: Mapping[str, Mapping[str, Sequence[str]]]) -> str:
    digest = hashlib.sha256()
    for key in sorted(sets):
        digest.update(key.encode())
        blocks = sets[key]
        for block in sorted(blocks):
            digest.update(b"/")
            digest.update(block.encode())
            for name in blocks[block]:
                digest.update(b"|")
                digest.update(name.encode())
        digest.update(b"\n")
    return digest.hexdigest()


def sets_sha256(record: Mapping[str, Any]) -> str:
    """The digest the artifact carries, rebuilt from the sets it lists."""
    return _sets_sha256({key: entry["blocks"] for key, entry in record["sets"].items()})


def _load_prior(campaign: Campaign, name: str) -> dict[str, Any] | None:
    path = Path(campaign.data_dir) / name
    if not path.exists():
        return None
    return json.loads(path.read_text())


def prior_sets(campaign: Campaign, config: Config, arm: str) -> dict[str, Any]:
    """The two priors' sets for the twin of *arm*, or what is missing and why."""
    out: dict[str, Any] = {"eight_entry": None, "optimisation_path": None}
    eight = _load_prior(campaign, PRIOR_EIGHT_ENTRY)
    path_sets = _load_prior(campaign, PRIOR_OPTIMISATION_PATH)
    twin8 = PRIOR_EIGHT_ENTRY_ARM.get(arm)
    twinp = PRIOR_PATH_ARM.get(arm)
    if eight is not None and twin8 is not None:
        entry = (eight.get("configurations") or {}).get(config.name, {}).get(twin8)
        if entry is not None:
            out["eight_entry"] = {
                "file": PRIOR_EIGHT_ENTRY,
                "sha256": sha256_of(Path(campaign.data_dir) / PRIOR_EIGHT_ENTRY),
                "arm": twin8,
                "sets": {b: sorted(k) for b, k in entry["sets"].items()},
            }
    if path_sets is not None and twinp is not None:
        entry = (path_sets.get("configurations") or {}).get(config.name, {}).get(twinp)
        if entry is not None:
            out["optimisation_path"] = {
                "file": PRIOR_OPTIMISATION_PATH,
                "sha256": sha256_of(Path(campaign.data_dir) / PRIOR_OPTIMISATION_PATH),
                "arm": twinp,
                "sets": {b: sorted(k) for b, k in entry["sets"].items()},
            }
    if twin8 is None and twinp is None:
        out["why_none"] = (
            f"{arm} has no prior: A89 censused A0 and A2, A92 B0 and B2; the "
            f"lifted flat block ({arm}) is measured here for the first time"
        )
    return out


def _compare_sets(census: Mapping[str, Sequence[str]], prior: Mapping[str, Sequence[str]] | None) -> dict[str, Any]:
    if prior is None:
        return {"available": False}
    blocks = sorted(set(census) | set(prior))
    out: dict[str, Any] = {"available": True, "blocks": {}}
    for block in blocks:
        c = set(census.get(block, ()))
        p = set(prior.get(block, ()))
        out["blocks"][block] = {
            "n_census": len(c),
            "n_prior": len(p),
            "n_common": len(c & p),
            "census_not_prior": sorted(c - p),
            "prior_not_census": sorted(p - c),
            "identical": c == p,
        }
    out["identical"] = all(b["identical"] for b in out["blocks"].values())
    return out


def derive(campaign: Campaign, pairs: Sequence[CensusPair]) -> dict[str, Any]:
    """Per configuration: the union per arm and block, the priors, the binding sets."""
    by_config: dict[str, dict[str, Any]] = {}
    for pair in pairs:
        census_dir = pool_mod.directory_for(pair.censused, campaign)
        census = read_census(census_dir)
        record = records_mod.read(census_dir)
        entry = by_config.setdefault(pair.config.name, {"arms": {}})
        arm_entry = entry["arms"].setdefault(
            pair.arm,
            {
                "loop_key": loop_key(pair.arm, pair.config),
                "applies_to": sorted(
                    a for a, twin in TWIN_OF.items() if twin == pair.arm and a not in pair.config.skips
                ) + [pair.arm],
                "runs": [],
                "union": {},
                "detail": {},
                "sweeps_observed_by_block": {},
            },
        )
        arm_entry["runs"].append(
            {
                "seed": pair.seed,
                "status": record.get("status"),
                "n_evaluations": census.get("n_evaluations"),
                "tree_git_head": record.get("tree_git_head"),
                "job_digest": record.get("job_digest"),
                "norm_objf_hex": _value(record, "exact.norm_objf"),
                "path": framework._relative(census_dir, Path(campaign.runs_dir)),
            }
        )
        for label, keys in census["union_by_block"].items():
            if label == census_mod.UNLABELLED:
                continue
            arm_entry["union"].setdefault(label, set()).update(keys)
            detail = arm_entry["detail"].setdefault(label, {})
            for key, d in census["detail_by_block"][label].items():
                e = detail.setdefault(key, {"reader": d["reader"], "writer": d["writer"], "n_sweeps": 0, "n_runs": 0})
                e["n_sweeps"] += int(d["n_sweeps"])
                e["n_runs"] += 1
        for label, n in census["sweeps_observed_by_block"].items():
            arm_entry["sweeps_observed_by_block"][label] = (
                arm_entry["sweeps_observed_by_block"].get(label, 0) + int(n)
            )
    for name, entry in by_config.items():
        config = campaign.configuration(name)
        for arm, arm_entry in entry["arms"].items():
            arm_entry["union"] = {b: sorted(k) for b, k in sorted(arm_entry["union"].items())}
            priors = prior_sets(campaign, config, arm)
            arm_entry["priors"] = {
                "eight_entry": priors["eight_entry"] and {
                    k: v for k, v in priors["eight_entry"].items() if k != "sets"
                },
                "optimisation_path": priors["optimisation_path"] and {
                    k: v for k, v in priors["optimisation_path"].items() if k != "sets"
                },
                "why_none": priors.get("why_none"),
            }
            arm_entry["against_eight_entry"] = _compare_sets(
                arm_entry["union"], (priors["eight_entry"] or {}).get("sets")
            )
            arm_entry["against_optimisation_path"] = _compare_sets(
                arm_entry["union"], (priors["optimisation_path"] or {}).get("sets")
            )
            # The binding population: the census union, unioned with the prior
            # optimisation-path set of the twin where one exists.
            binding: dict[str, set[str]] = {b: set(k) for b, k in arm_entry["union"].items()}
            prior_path = (priors["optimisation_path"] or {}).get("sets") or {}
            added_from_prior: dict[str, list[str]] = {}
            for block, keys in prior_path.items():
                extra = sorted(set(keys) - binding.get(block, set()))
                if extra:
                    added_from_prior[block] = extra
                binding.setdefault(block, set()).update(keys)
            arm_entry["binding"] = {b: sorted(k) for b, k in sorted(binding.items())}
            arm_entry["added_from_prior_optimisation_path"] = added_from_prior
            arm_entry["n_by_block"] = {b: len(k) for b, k in arm_entry["binding"].items()}
            arm_entry["n_by_block_census_only"] = {b: len(k) for b, k in arm_entry["union"].items()}
    return by_config


def artifact_for(campaign: Campaign, config: Config, derived: Mapping[str, Any], *, head: str | None) -> dict[str, Any]:
    """The committed artifact for one configuration."""
    coupling = json.loads(Path(config.coupling_state_path).read_text())
    sets: dict[str, Any] = {}
    for arm, arm_entry in derived["arms"].items():
        entry = {
            "blocks": arm_entry["binding"],
            "census_arm": arm,
            "applies_to_arms": arm_entry["applies_to"],
            "n_by_block": arm_entry["n_by_block"],
            "n_by_block_census_only": arm_entry["n_by_block_census_only"],
            "added_from_prior_optimisation_path": arm_entry["added_from_prior_optimisation_path"],
            "sweeps_observed_by_block": arm_entry["sweeps_observed_by_block"],
        }
        sets[arm_entry["loop_key"]] = entry
        # The twin rule, made explicit in the artifact: an evaluation-phase
        # arm whose loop key differs from its census arm's (the burn time
        # owned by a constant, A1 and A2 on a pulsed configuration, where
        # the optimisation arms B1 and B2 hand it to the optimiser) binds
        # the same sets under its own key.  No loop node writes the burn
        # time under either owner, so the carried set is the same; the
        # entry says whose census it is.  Found by the first press of gate
        # GT, which refused A1's loop 'flat/constant' as unknown.
        for applies in arm_entry["applies_to"]:
            key = arms_mod.ARMS[applies].loop_key(config)
            if key not in sets:
                sets[key] = {**entry, "twin_of": arm_entry["loop_key"], "bound_for_arm": applies}
    record = {
        "format": FORMAT,
        "scenario": config.name,
        "generated_by": "harness/experiment/test_sets.py (experiment_runner.py --census)",
        "generated_at_tree_git_head": head,
        "rule": (
            "a component of y that, in some observed sweep of the block, is "
            "read before it is first written in that sweep and written later "
            "in it; observed over every evaluation of whole optimisation runs "
            "(seeds 0 and 1) of each iterating optimisation arm, unioned, and "
            "unioned with the prior optimisation-path set of the twin arm where "
            "one exists"
        ),
        "selection": (
            "the driver selects the entry whose key is '<mda>/<burn-time "
            "owner>' as it resolved them (module_solve.MDA_MODE, "
            "subsolve.BURN_TIME_OWNER); a block with no entry under that key "
            "tests nothing and converges at its first pass"
        ),
        "census_seeds": list(CENSUS_SEEDS),
        "census_test_set": V4_TEST_SET,
        "census_tau": TAU_BY_TEST_SET[V4_TEST_SET],
        "census_instrument": census_mod.FORMAT,
        "ystate_components_sha256": rebuild_components_sha256(coupling),
        "n_components": len(coupling["components"]),
        "census_runs": {
            arm: arm_entry["runs"] for arm, arm_entry in derived["arms"].items()
        },
        "priors": {
            arm: arm_entry["priors"] for arm, arm_entry in derived["arms"].items()
        },
        "against_eight_entry": {
            arm: arm_entry["against_eight_entry"] for arm, arm_entry in derived["arms"].items()
        },
        "against_optimisation_path": {
            arm: arm_entry["against_optimisation_path"] for arm, arm_entry in derived["arms"].items()
        },
        "detail": {
            arm: arm_entry["detail"] for arm, arm_entry in derived["arms"].items()
        },
        "sets": sets,
    }
    record["sets_sha256"] = sets_sha256(record)
    return record


# --------------------------------------------------------------------------
# the stage
# --------------------------------------------------------------------------


def stage_root(campaign: Campaign) -> Path:
    return Path(campaign.runs_dir) / RUNS_SUBPATH


def artifact_path(campaign: Campaign, config: Config, *, committed: bool) -> Path:
    if committed:
        return Path(config.test_sets_path)
    return stage_root(campaign) / Path(config.test_sets_path).name


def stage(
    campaign: Campaign,
    *,
    resume: bool = False,
    write_data: bool = False,
    configurations: Sequence[str] | None = None,
) -> tuple[int, dict[str, Any]]:
    """Take the census, check it is observation-only, derive and write the sets."""
    check = StageCheck(
        name="census test sets",
        binds=(
            "the test set every block loop stops on under "
            "PROCESS_ARCH_TEST_SET=census: measured on this tree, checked "
            "observation-only against uncensused twins, compared with the "
            "two prior populations, written with the provenance of every "
            "record it was derived from"
        ),
    )
    under = census_campaign(campaign)
    pairs = [
        p for p in census_pairs(campaign)
        if configurations is None or p.config.name in configurations
    ]
    if not pairs:
        raise TestSetError("the census job set is empty; nothing to derive from")
    jobs: list[pool_mod.Job] = []
    for pair in pairs:
        jobs.append(pair.twin)
        jobs.append(pair.censused)
    print(
        f"census: {len(pairs)} pair(s) = {len(jobs)} optimisation(s) under the "
        f"fallback ({under.test_set} at tau={under.tau!r}), "
        f"{pool_mod.workers(under)} worker(s)",
        flush=True,
    )
    pool_mod.run_all(jobs, under, resume=resume)

    rows = [reproduction_row(pair, under) for pair in pairs]
    n_identical = sum(1 for r in rows if r["identical"])
    check.n_compared += len(rows) * len(REPRODUCTION_FIELDS)
    check.n_mismatched += sum(
        1 for r in rows for f in r["fields"].values() if not f["identical"]
    )
    not_ok = [r for r in rows if r["fields"]["status"]["twin"] != "ok" or r["fields"]["status"]["censused"] != "ok"]
    if not_ok:
        check.passed = False
        check.note(
            f"{len(not_ok)} pair(s) did not finish: "
            + ", ".join(f"{r['configuration']}/{r['arm']}/seed{r['seed']}" for r in not_ok)
        )
    if n_identical != len(rows):
        check.passed = False
        for r in rows:
            if not r["identical"]:
                differing = [k for k, f in r["fields"].items() if not f["identical"]]
                check.note(
                    f"{r['configuration']}/{r['arm']}/seed{r['seed']}: the censused "
                    f"run does not reproduce its twin on {differing}"
                )
    check.note(
        f"{n_identical} of {len(rows)} censused run(s) reproduce their uncensused "
        f"twin on all {len(REPRODUCTION_FIELDS)} fields ({', '.join(l for l, _ in REPRODUCTION_FIELDS)})"
    )

    derived = derive(under, pairs) if not not_ok else {}
    head = framework.git_head()
    root = stage_root(under)
    root.mkdir(parents=True, exist_ok=True)
    artifacts: dict[str, Any] = {}
    for name, entry in derived.items():
        config = under.configuration(name)
        record = artifact_for(under, config, entry, head=head)
        out = artifact_path(under, config, committed=False)
        out.write_text(json.dumps(record, indent=1) + "\n")
        written = {"runs_copy": str(out)}
        if write_data:
            target = artifact_path(under, config, committed=True)
            target.write_text(json.dumps(record, indent=1) + "\n")
            written["committed_copy"] = str(target)
        artifacts[name] = {
            "written": written,
            "sets_sha256": record["sets_sha256"],
            "n_by_block": {k: v["n_by_block"] for k, v in record["sets"].items()},
            "n_by_block_census_only": {k: v["n_by_block_census_only"] for k, v in record["sets"].items()},
            "added_from_prior_optimisation_path": {
                k: v["added_from_prior_optimisation_path"] for k, v in record["sets"].items()
            },
            "against_eight_entry": record["against_eight_entry"],
            "against_optimisation_path": record["against_optimisation_path"],
        }
        for arm, cmp in record["against_optimisation_path"].items():
            if cmp.get("available"):
                check.note(
                    f"{name}/{arm}: census union {'identical to' if cmp['identical'] else 'DIFFERS from'} "
                    f"A92's optimisation-path set"
                    + (
                        "" if cmp["identical"] else ": " + "; ".join(
                            f"{b}: +{len(d['census_not_prior'])} census-only, "
                            f"-{len(d['prior_not_census'])} prior-only"
                            for b, d in cmp["blocks"].items() if not d["identical"]
                        )
                    )
                )
        for arm, cmp in record["against_eight_entry"].items():
            if cmp.get("available"):
                check.note(
                    f"{name}/{arm}: census union against A89's eight-entry set: "
                    + "; ".join(
                        f"{b}: {d['n_census']} vs {d['n_prior']}, common {d['n_common']}, "
                        f"census-only {len(d['census_not_prior'])}, prior-only {len(d['prior_not_census'])}"
                        for b, d in cmp["blocks"].items()
                    )
                )
    check.population = (
        f"{len(pairs)} pair(s) over {len({p.config.name for p in pairs})} configuration(s); "
        f"arms {sorted({p.arm for p in pairs})}; seeds {list(CENSUS_SEEDS)}; "
        f"{len(rows) * len(REPRODUCTION_FIELDS)} reproduction field(s) compared"
    )
    record = {
        **check.as_record(),
        "tree_git_head": head,
        "census_campaign": {"test_set": under.test_set, "tau": under.tau},
        "reproduction": rows,
        "artifacts": artifacts,
        "runs_read": [
            {"key": j.key, "job_digest": pool_mod.digest_for(j, under), "path": str(pool_mod.directory_for(j, under))}
            for j in jobs
        ],
    }
    (root / "stage.json").write_text(json.dumps(record, indent=2, default=str) + "\n")
    return (0 if check.passed else 3), record


# --------------------------------------------------------------------------
# teeth
# --------------------------------------------------------------------------


def stage_teeth(campaign: Campaign) -> tuple[int, dict[str, Any]]:
    """The stage's own ability to fail, on doctored copies; no PROCESS run."""
    import tempfile  # noqa: PLC0415 - teeth only

    check = StageCheck(
        name="census test sets — teeth",
        binds="the derivation's own refusals",
        population="3 deliberate breaks, each on a throwaway copy",
    )
    config = campaign.configurations[0]
    coupling = json.loads(Path(config.coupling_state_path).read_text())
    keys = [c["key"] for c in coupling["components"]]

    # 1. a censused record whose norm_objf differs from its twin is reported
    #    as not reproducing.
    twin = {"status": "ok", "mfile": {"ifail": 1}, "n_solver_iterations": 8,
            "sweeps_per_eval": {"n_evaluations": 630}, "node_calls_solve_phase": 100,
            "exact": {"norm_objf": "0x1.0p+0"}}
    censused = json.loads(json.dumps(twin))
    censused["exact"]["norm_objf"] = "0x1.0000000000001p+0"
    fields = {
        label: {"twin": _value(twin, path), "censused": _value(censused, path)}
        for label, path in REPRODUCTION_FIELDS
    }
    differs = [l for l, f in fields.items() if f["twin"] != f["censused"]]
    check.tooth(
        "one ulp on norm_objf between a censused run and its twin",
        differs == ["norm_objf_hex"],
        f"a copy of a twin record with norm_objf moved by one unit in the last place: "
        f"the comparison names {differs}",
    )

    # 2. a census file naming a key y lacks is refused by the artifact check.
    from . import artifacts as artifacts_mod  # noqa: PLC0415

    with tempfile.TemporaryDirectory() as tmp:
        sets = {"flat/loop": {"blocks": {"FLAT": keys[:3] + ["nowhere.no_such_key"]}, "census_arm": "B0", "applies_to_arms": ["A0", "B0"]}}
        record = {
            "format": FORMAT,
            "scenario": config.name,
            "ystate_components_sha256": rebuild_components_sha256(coupling),
            "census_runs": {"B0": [{"seed": 0, "tree_git_head": "0" * 40, "job_digest": "0" * 64, "norm_objf_hex": "0x0p+0", "path": "nowhere"}]},
            "sets": sets,
        }
        record["sets_sha256"] = sets_sha256(record)
        row = artifacts_mod.Row(config.name, "test_sets", str(Path(tmp) / "t.json"), True)
        artifacts_mod._check_test_sets(row, record, config, coupling, campaign)
        failing = [c["what"] for c in row.checks if not c["ok"]]
        check.tooth(
            "a test-set key the coupling state does not have",
            "every test-set key is a coupling component" in failing,
            f"a throwaway artifact naming nowhere.no_such_key: failing checks {failing}",
        )

        # 3. a corrupted sets digest does not rebuild.
        record["sets"]["flat/loop"]["blocks"]["FLAT"] = keys[:3]
        record["sets_sha256"] = "0" * 64
        row = artifacts_mod.Row(config.name, "test_sets", str(Path(tmp) / "t.json"), True)
        artifacts_mod._check_test_sets(row, record, config, coupling, campaign)
        failing = [c["what"] for c in row.checks if not c["ok"]]
        check.tooth(
            "a corrupted sets digest",
            "sets_sha256 rebuilt" in failing,
            f"sets_sha256 set to zeros on a throwaway artifact: failing checks {failing}",
        )
    return (0 if check.passed else 3), check.as_record()
