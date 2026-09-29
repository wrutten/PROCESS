"""The test-set smoke pairs: two optimisations under each test set, compared.

Not a campaign and not a gate: a smoke of driver change DR11 from the button
(task A100 (v5-test-set)), so that the records carrying the new stamps —
``campaign_test_set``, ``campaign_tau`` and the loops' widths in
``loop_test_sets`` — exist and are compared with what they must reproduce.

Three pairs of records, every one ``run_kind == "smoke"`` in a named
directory under ``runs/single/test_set_smoke/``:

* ``B0`` and ``B2`` on the cheapest pulsed configuration at seed 0 under the
  **census** set at its declared tolerance (the campaign as pressed);
* the same pair under the **fallback** — the block's whole write set at
  1e-6, V4's predicate (decision D39).  Each of these two must reproduce
  the seeded reproduction gate's record of the same arm and seed on status,
  exit code, iterations, evaluations, solve-phase node calls and
  ``norm_objf`` to the bit: the fallback is V4 on this tree;
* the declared supplementary stage's ``B2`` on ``st_regression`` at seed 0
  (the census set at 1e-12; V5 plan §3 after A96 (st-trajectory-ladder)),
  compared with a record of that run made elsewhere when one is handed in
  (``--ladder-record``): evaluations, iterations, node calls and
  ``norm_objf`` — a difference is a result (the ladder ran on V4's driver
  copy before DR9 and DR10).

Beside each pair the per-evaluation node-call ratio ``B2/B0`` is printed as
**context** (V5 plan §5 B3's ρ; A93 read 0.48–0.49 under the census set at
1e-8 and V4 0.61 under the whole write set at 1e-6) — never a verdict.
"""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Any, Mapping

from ..core import framework
from ..core import pool as pool_mod
from ..core import records as records_mod
from ..core.config import TAU_BY_TEST_SET, V4_TEST_SET, Campaign
from ..core.framework import GateError

RUNS_SUBPATH = Path("single") / "test_set_smoke"

#: The arms of each pair, and the fields a fallback record must reproduce.
ARMS: tuple[str, ...] = ("B0", "B2")
REPRODUCTION_FIELDS: tuple[tuple[str, str], ...] = (
    ("status", "status"),
    ("ifail", "mfile.ifail"),
    ("n_solver_iterations", "n_solver_iterations"),
    ("n_evaluations", "sweeps_per_eval.n_evaluations"),
    ("node_calls_solve_phase", "node_calls_solve_phase"),
    ("norm_objf_hex", "exact.norm_objf"),
)
LADDER_FIELDS: tuple[tuple[str, str], ...] = (
    ("n_evaluations", "sweeps_per_eval.n_evaluations"),
    ("n_solver_iterations", "n_solver_iterations"),
    ("node_calls_solve_phase", "node_calls_solve_phase"),
    ("norm_objf_hex", "exact.norm_objf"),
)


def _value(record: Mapping[str, Any], path: str) -> Any:
    return records_mod.resolve_path(record, path) if records_mod.has_path(record, path) else None


def _cheapest_pulsed(campaign: Campaign):
    pulsed = [c for c in campaign.configurations if c.pulsed]
    if not pulsed:
        raise GateError("no pulsed configuration in the campaign")
    return min(pulsed, key=lambda c: c.n_iteration_variables)


def _job(campaign: Campaign, config, arm: str, label: str, *, test_set: str | None = None, tau: float | None = None) -> pool_mod.Job:
    return pool_mod.Job(
        phase="B",
        arm=arm,
        config=config,
        seed=0,
        outdir=Path(campaign.runs_dir) / RUNS_SUBPATH / label / config.name / arm / pool_mod.seed_directory(0),
        regime="unperturbed",
        delta=campaign.delta,
        run_kind="smoke",
        test_set=test_set,
        tau=tau,
    )


def _stamps(record: Mapping[str, Any]) -> dict[str, Any]:
    loops = record.get("loop_test_sets") or {}
    return {
        "campaign_test_set": record.get("campaign_test_set"),
        "campaign_tau": record.get("campaign_tau"),
        "resolved_test_set": (record.get("resolved_switches") or {}).get(
            "process.core.solver.module_solve.TEST_SET"
        ),
        "resolved_tau": (record.get("resolved_switches") or {}).get(
            "process.core.solver.module_solve.TAU"
        ),
        "loop_key": loops.get("loop_key"),
        "widths": loops.get("n_by_block"),
        "blocks_never_censused": loops.get("blocks_never_censused"),
        "tree_git_head": record.get("tree_git_head"),
        "job_digest": record.get("job_digest"),
    }


def _ratio(b2: Mapping[str, Any], b0: Mapping[str, Any]) -> float | None:
    try:
        rb2 = b2["node_calls_solve_phase"] / b2["sweeps_per_eval"]["n_evaluations"]
        rb0 = b0["node_calls_solve_phase"] / b0["sweeps_per_eval"]["n_evaluations"]
        return rb2 / rb0
    except (KeyError, TypeError, ZeroDivisionError):
        return None


def _compare(a: Mapping[str, Any], b: Mapping[str, Any], fields) -> dict[str, Any]:
    out = {label: {"this": _value(a, path), "other": _value(b, path)} for label, path in fields}
    for entry in out.values():
        entry["identical"] = entry["this"] == entry["other"]
    return {"fields": out, "identical": all(e["identical"] for e in out.values())}


def stage(
    campaign: Campaign, *, resume: bool = False, ladder_record: Path | None = None
) -> tuple[int, dict[str, Any]]:
    """Make the three pairs and compare them.  0 on every comparison holding."""
    from ..gates import reproduction as reproduction_mod  # noqa: PLC0415

    if campaign.test_set != "census":
        raise GateError(
            f"the smoke pairs are pressed from the census campaign (the fallback "
            f"pair is composed by the stage itself); this press composes "
            f"{campaign.test_set!r}"
        )
    fallback = replace(campaign, test_set=V4_TEST_SET, tau=None)
    config = _cheapest_pulsed(campaign)
    census_jobs = [_job(campaign, config, arm, "census") for arm in ARMS]
    fallback_jobs = [_job(fallback, config, arm, "write_set") for arm in ARMS]
    st = campaign.configuration("st_regression")
    supplementary = next(
        (s for s in campaign.supplementary if "st_regression" in s.configurations and "B2" in s.arms),
        None,
    )
    if supplementary is None:
        raise GateError("no declared supplementary stage covers B2 on st_regression")
    ladder_job = _job(
        campaign, st, "B2", f"supplementary_{supplementary.name}",
        test_set=supplementary.test_set, tau=float(supplementary.tau),
    )

    print(f"smoke pairs: {config.name} {ARMS} under census/{campaign.tau!r} and under {V4_TEST_SET}/{fallback.tau!r}; "
          f"st_regression B2 under {supplementary.test_set}/{supplementary.tau!r} ({supplementary.name})", flush=True)
    pool_mod.run_all(census_jobs, campaign, resume=resume)
    pool_mod.run_all(fallback_jobs, fallback, resume=resume)
    pool_mod.run_all([ladder_job], campaign, resume=resume)

    records: dict[str, dict[str, Any]] = {}
    for label, jobs in (("census", census_jobs), ("write_set", fallback_jobs)):
        for job in jobs:
            records[f"{label}/{job.arm}"] = records_mod.read(job.outdir)
    records[f"supplementary/{supplementary.name}/B2"] = records_mod.read(ladder_job.outdir)

    # The fallback pair against the seeded reproduction records of the same
    # arm and seed: GR's own jobs, composed under the fallback campaign so
    # they carry V4's identity and resolve to the seeded records.
    root = Path(fallback.runs_dir) / reproduction_mod.RUNS_SUBPATH
    planned, _prereq = reproduction_mod.plan(fallback, root)
    against_reference: dict[str, Any] = {}
    for arm in ARMS:
        item = next(
            (i for i in planned if i.run.arm == arm and i.run.seed == 0 and i.run.configuration == config.name),
            None,
        )
        if item is None:
            against_reference[arm] = {"available": False, "why": "the reproduction gate plans no such run"}
            continue
        directory = pool_mod.directory_for(item.job, fallback)
        if not (directory / "metrics.json").exists():
            against_reference[arm] = {"available": False, "why": f"no record at {directory}"}
            continue
        reference = records_mod.read(directory)
        comparison = _compare(records[f"write_set/{arm}"], reference, REPRODUCTION_FIELDS)
        comparison["reference"] = {
            "path": str(directory),
            "tree_git_head": reference.get("tree_git_head"),
            "campaign_test_set": reference.get("campaign_test_set"),
            "campaign_tau": reference.get("campaign_tau"),
        }
        comparison["available"] = True
        against_reference[arm] = comparison

    against_ladder: dict[str, Any] = {"available": False}
    if ladder_record is not None:
        if not ladder_record.exists():
            raise GateError(f"the ladder record {ladder_record} is not there")
        other = json.loads(ladder_record.read_text())
        against_ladder = _compare(records[f"supplementary/{supplementary.name}/B2"], other, LADDER_FIELDS)
        against_ladder["available"] = True
        against_ladder["ladder"] = {
            "path": str(ladder_record),
            "tree_git_head": other.get("tree_git_head"),
            "campaign_tau": other.get("campaign_tau"),
            "campaign_arm": other.get("campaign_arm"),
        }

    ratios = {
        "census": _ratio(records["census/B2"], records["census/B0"]),
        "write_set": _ratio(records["write_set/B2"], records["write_set/B0"]),
    }
    finished = all(r.get("status") == "ok" for r in records.values())
    reproduced = all(v.get("identical") for v in against_reference.values() if v.get("available"))
    ladder_ok = (not against_ladder.get("available")) or against_ladder.get("identical")
    record = {
        "stage": "test_set_smoke",
        "what": __doc__.strip().splitlines()[0],
        "tree_git_head": framework.git_head(),
        "configuration": config.name,
        "census_tau": campaign.tau,
        "fallback_tau": fallback.tau,
        "supplementary": {"name": supplementary.name, "test_set": supplementary.test_set, "tau": supplementary.tau},
        "records": {
            key: {"path": str(r.get("outdir")), "status": r.get("status"), "stamps": _stamps(r),
                  **{label: _value(r, path) for label, path in REPRODUCTION_FIELDS}}
            for key, r in records.items()
        },
        "against_reproduction_records": against_reference,
        "against_ladder_record": against_ladder,
        "per_evaluation_node_call_ratio_B2_over_B0": ratios,
        "ratio_context": (
            "context, never evidence (D33): A93 read 0.48-0.49 under the census "
            "set at 1e-8 and V4's campaign 0.61 under the whole write set at 1e-6"
        ),
        "every_run_finished": finished,
        "fallback_reproduces_the_reproduction_records": reproduced,
        "ladder_record_reproduced": ladder_ok,
    }
    ok = finished and reproduced and ladder_ok
    return (0 if ok else 3), record


def report(record: Mapping[str, Any]) -> list[str]:
    lines = [f"  {record['configuration']}: census at tau={record['census_tau']!r}, fallback at tau={record['fallback_tau']!r}"]
    for key, r in record["records"].items():
        st = r["stamps"]
        lines.append(
            f"  {key:44s} status={r['status']} set={st['campaign_test_set']} tau={st['campaign_tau']!r} "
            f"loop={st['loop_key']} widths={st['widths']} norm_objf={r['norm_objf_hex']} "
            f"evals={r['n_evaluations']} iters={r['n_solver_iterations']} node_calls={r['node_calls_solve_phase']}"
        )
    for arm, cmp in record["against_reproduction_records"].items():
        if not cmp.get("available"):
            lines.append(f"  write_set/{arm} against the reproduction record: {cmp.get('why')}")
            continue
        lines.append(
            f"  write_set/{arm} against the reproduction record at {cmp['reference']['tree_git_head'][:8]}: "
            + ("IDENTICAL on " + ", ".join(cmp["fields"]) if cmp["identical"] else
               "DIFFERS on " + ", ".join(k for k, v in cmp["fields"].items() if not v["identical"]))
        )
    lad = record["against_ladder_record"]
    if lad.get("available"):
        lines.append(
            f"  supplementary B2 st_regression against the ladder record at {str(lad['ladder']['tree_git_head'])[:8]}: "
            + ("IDENTICAL on " + ", ".join(lad["fields"]) if lad["identical"] else
               "DIFFERS on " + ", ".join(f"{k} ({v['this']} vs {v['other']})" for k, v in lad["fields"].items() if not v["identical"]))
        )
    for label, ratio in record["per_evaluation_node_call_ratio_B2_over_B0"].items():
        lines.append(f"  per-evaluation node-call ratio B2/B0 under {label}: {ratio!r}  ({record['ratio_context']})")
    return lines
