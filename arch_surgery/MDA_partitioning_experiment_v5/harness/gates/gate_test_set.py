"""Gate GT — the census test set has teeth (V5 plan §3, §7; item 6, D32).

Under ``PROCESS_ARCH_TEST_SET=census`` every block loop stops on the census
test set of its block — the components the loop carries between sweeps
(``harness/experiment/test_sets.py``) — instead of the block's whole write
set.  A test set that is too small stops a loop early and hands over a state
that is not the fixed point; this gate shows the set is **load-bearing** by
removing one component from it and watching the run change, on the form task
A92 (optimisation-path-census) declared from its measurement:

(i)  **the binding drop.**  Per configuration and block arm of the evaluation
     phase, from the displaced entry at seed 1 (gate G6's pairing entry), the
     component the declared rule finds binding — *the carried component with
     the largest whole-``y`` exit residual under the full set* (ties,
     including a whole set at 0.0, to the alphabetically last key) — is
     removed from every block of the arm's loop that carries it.  The run
     must then **stop earlier** (fewer sweeps in some block) **and** leave an
     exit state that **differs** from the full set's, bit for bit over the
     whole of ``y``.  That is the tooth.  Where nothing changes, no single
     component binds on that entry (a set can be a correct cut set while no
     member binds alone; A92 found this on 17 of 19 drops) and the row says
     so: (ii) is then the check on that entry, as the plan declares.
(ii) **the control.**  A component *outside* the census set — the
     non-carried component with the largest exit residual — is "dropped"
     the same way: the artifact changes in nothing but its path, and the run
     must be **bit-identical** to the full set's on every count and every
     component of the exit state.
(iii) the whole-``y`` exit audit of every run is reported beside as the
     accuracy it left.  It is **not** the tooth: A92 showed a one-sweep-early
     stop stays below τ on the audit (the audit measures the next sweep's
     contraction, which the full loop just accepted as < τ), so the audit is
     thresholded at the wrong quantity for this purpose; the comparison
     against the full-set exit is the tooth.

Every row also checks that the driver **bound the narrowed set**: the
``loop_test_sets`` stamp of the dropped run is one component narrower than
the full run's in exactly the blocks the key was removed from, and equal
elsewhere; a run that stamped the full width did not test what the gate
thinks it tested.

The gate is PASS when every control is bit-identical, every binding drop
either bites or is reported not individually binding, and **at least one
drop bites** over the whole job set (a gate whose tooth never bit has not
been shown capable of failing, protocol §12; A92 found the bite on
``large_tokamak_nof`` in both arms).  It binds the census value only: under
the fallback (D39) it refuses, because the write set is not the thing it
tests.

Teeth (each on a copy, no PROCESS run): a biting drop's exit state replaced
by the full run's must read as not binding; one unit in the last place on a
control's exit state must fail the control; a doctored artifact that claims
to drop a key it still lists must be refused before any run; a dropped run's
width stamp doctored to the full width must fail the binding check.

Task **A100 (v5-test-set)**.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from . import gate_entry
from . import gates as gates_mod
from .gate_prime import full_state_compare
from ..core import pool as pool_mod
from ..core import records as records_mod
from ..core.config import Campaign, Config
from ..core.framework import Gate, GateError, Tooth
from ..experiment import arms as arms_mod
from ..experiment import switches as switches_mod
from ..experiment import test_sets as test_sets_mod

GATE_NAME = "test_set"
PLAN_NAME = "GT"

#: The evaluation-phase arms whose loops stop on a test set: the flat
#: control, the lifted flat block and the partitioned arm.
ARMS: tuple[str, ...] = ("A0", "A1", "A2")

#: The selection rules, named as A92 declared them.
RULE_BINDING = "max_exit_residual_carried"
RULE_CONTROL = "max_exit_residual_not_carried"

#: Where the doctored artifacts and the verdict go.
RUNS_SUBPATH = "test_set"

_HELD: dict[str, Any] = {}


# --------------------------------------------------------------------------
# the doctored artifacts
# --------------------------------------------------------------------------


def gate_root(campaign: Campaign) -> Path:
    return Path(campaign.runs_dir) / gates_mod.GATES_SUBPATH / RUNS_SUBPATH


def loop_sets(config: Config, arm: str) -> tuple[str, dict[str, list[str]]]:
    """``(loop key, {block: keys})`` the driver binds for *arm* on *config*."""
    artifact = json.loads(Path(config.test_sets_path).read_text())
    key = arms_mod.ARMS[arm].loop_key(config)
    entry = artifact["sets"].get(key)
    if entry is None:
        raise GateError(
            f"the census test-set artifact {config.test_sets_path} has no entry "
            f"for loop {key!r} ({arm} on {config.name}); the driver would test "
            f"nothing in every block of that loop, and a gate over an empty set "
            f"is a verdict on nothing"
        )
    return key, {block: list(keys) for block, keys in entry["blocks"].items()}


def carried_union(sets: Mapping[str, Sequence[str]]) -> set[str]:
    return {k for keys in sets.values() for k in keys}


def doctored_artifact(
    config: Config, arm: str, key: str, out: Path, *, role: str
) -> dict[str, Any]:
    """The committed artifact with *key* removed from every block of the arm's
    loop that carries it, written to *out*.  A control removes nothing."""
    artifact = json.loads(Path(config.test_sets_path).read_text())
    loop_key = arms_mod.ARMS[arm].loop_key(config)
    blocks = artifact["sets"][loop_key]["blocks"]
    removed_from = sorted(block for block, keys in blocks.items() if key in keys)
    for block in removed_from:
        blocks[block] = [k for k in blocks[block] if k != key]
    artifact["sets"][loop_key]["n_by_block"] = {b: len(k) for b, k in blocks.items()}
    artifact["sets_sha256"] = test_sets_mod.sets_sha256(artifact)
    artifact["doctored"] = {
        "by": f"gate {GATE_NAME} ({PLAN_NAME})",
        "role": role,
        "loop_key": loop_key,
        "dropped": key,
        "removed_from_blocks": removed_from,
        "what": (
            "a throwaway copy of the committed census test-set artifact with "
            "one component removed from every block of one loop that carries "
            "it; an empty removed_from_blocks is the control"
        ),
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(artifact, indent=1) + "\n")
    written = json.loads(out.read_text())
    still_there = [
        block for block, keys in written["sets"][loop_key]["blocks"].items() if key in keys
    ]
    if still_there:
        raise GateError(
            f"the doctored artifact {out} still lists {key} in {still_there}; "
            f"a drop that dropped nothing would compare the full set with itself"
        )
    return artifact["doctored"]


# --------------------------------------------------------------------------
# the selection rules
# --------------------------------------------------------------------------


def exit_residuals(directory: Path) -> dict[str, float]:
    """The full run's whole-``y`` exit residual per component (frozen ruler)."""
    path = Path(directory) / "audit_residual.json"
    if not path.exists():
        raise GateError(f"no audit_residual.json at {directory}; the selection rule reads it")
    vector = json.loads(path.read_text())
    return {k: float(v) for k, v in vector["scaled"].items()}


def choose(residuals: Mapping[str, float], candidates: Sequence[str]) -> tuple[str | None, float | None]:
    """The candidate with the largest residual; ties to the alphabetically last."""
    scored = [(residuals.get(k, 0.0), k) for k in candidates]
    if not scored:
        return None, None
    value, key = max(scored, key=lambda vk: (vk[0], vk[1]))
    return key, value


# --------------------------------------------------------------------------
# the job set
# --------------------------------------------------------------------------


def full_jobs(campaign: Campaign, references: Mapping[str, Any]) -> list[tuple[str, str, pool_mod.Job]]:
    """The full-set runs: G6's pairing runs of the block arms (shared with G6)."""
    pairing, _warm = gate_entry.entry_and_warm_jobs(campaign, references)
    return [(c, a, job) for c, a, job in pairing if a in ARMS]


def dropped_job(full: pool_mod.Job, artifact: Path) -> pool_mod.Job:
    """The full job with the driver handed the doctored artifact instead."""
    name = switches_mod.REGISTRY["test_sets"].driver_name
    return pool_mod.Job(
        phase=full.phase,
        arm=full.arm,
        config=full.config,
        seed=full.seed,
        regime=full.regime,
        delta=full.delta,
        pin_hex=full.pin_hex,
        entry_state=full.entry_state,
        run_kind=full.run_kind,
        override_env={name: str(artifact)},
    )


def _plan(campaign: Campaign, references: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Per configuration and arm: the full job and, once its record exists, the two drops."""
    rows: list[dict[str, Any]] = []
    for config_name, arm, full in full_jobs(campaign, references):
        config = campaign.configuration(config_name)
        loop_key, sets = loop_sets(config, arm)
        rows.append({"config": config, "arm": arm, "loop_key": loop_key, "sets": sets, "full": full})
    return rows


def jobs_read(campaign: Campaign) -> list[pool_mod.Job]:
    """Every job the gate reads: the references, the full runs, and the drops where composable."""
    references = gates_mod.entry_references_from_records(campaign)
    jobs = gates_mod.entry_reference_jobs(campaign)
    for row in _plan(campaign, references):
        jobs.append(row["full"])
        full_dir = pool_mod.directory_for(row["full"], campaign)
        if not (full_dir / "audit_residual.json").exists():
            continue
        residuals = exit_residuals(full_dir)
        carried = carried_union(row["sets"])
        binding, _ = choose(residuals, sorted(carried))
        control, _ = choose(residuals, sorted(set(residuals) - carried))
        root = gate_root(campaign) / row["config"].name / row["arm"]
        for role, key in (("binding", binding), ("control", control)):
            if key is None:
                continue
            jobs.append(dropped_job(row["full"], root / f"{role}_{key}.json"))
    return jobs


# --------------------------------------------------------------------------
# the comparisons
# --------------------------------------------------------------------------


def _state(directory: Path) -> dict[str, Any]:
    path = Path(directory) / "y_exit.json"
    if not path.exists():
        raise GateError(f"no y_exit.json at {directory}: nothing to compare the exit state with")
    return json.loads(path.read_text())["state"]


def _sweeps(record: Mapping[str, Any]) -> dict[str, int]:
    totals = record.get("block_loop_totals") or {}
    return {k: int(v) for k, v in (totals.get("sweeps_by_block") or {}).items()}


def _widths(record: Mapping[str, Any]) -> dict[str, int]:
    stamp = record.get("loop_test_sets") or {}
    return {k: int(v) for k, v in (stamp.get("n_by_block") or {}).items()}


def compare_row(
    full: Mapping[str, Any], full_dir: Path, other: Mapping[str, Any], other_dir: Path,
    *, role: str, removed_from: Sequence[str],
) -> dict[str, Any]:
    """One dropped or control run against the full run."""
    states = full_state_compare(_state(full_dir), _state(other_dir))
    sweeps_full, sweeps_other = _sweeps(full), _sweeps(other)
    fewer = [b for b in sweeps_full if sweeps_other.get(b, sweeps_full[b]) < sweeps_full[b]]
    more = [b for b in sweeps_full if sweeps_other.get(b, sweeps_full[b]) > sweeps_full[b]]
    widths_full, widths_other = _widths(full), _widths(other)
    expected_widths = {
        b: (w - 1 if b in removed_from else w) for b, w in widths_full.items()
    }
    bound_as_expected = widths_other == expected_widths and bool(widths_full)
    audit = other.get("exit_audit") or {}
    out = {
        "role": role,
        "status": other.get("status"),
        "removed_from_blocks": list(removed_from),
        "sweeps_full": sweeps_full,
        "sweeps": sweeps_other,
        "blocks_with_fewer_sweeps": fewer,
        "blocks_with_more_sweeps": more,
        "node_calls_full": full.get("node_calls_single_eval"),
        "node_calls": other.get("node_calls_single_eval"),
        "widths_full": widths_full,
        "widths": widths_other,
        "widths_expected": expected_widths,
        "driver_bound_the_narrowed_set": bound_as_expected,
        "exit_state": {
            "n_components_compared": states["n_components"],
            "n_differing": states["n_differing"],
            "differing_first": states["differing"][:10],
        },
        "exit_audit_max": audit.get("residual_max"),
        "exit_audit_max_hex": audit.get("residual_max_hex"),
        "exit_audit_n_above_tau": (audit.get("brief") or {}).get("n_above"),
        "exit_audit_full_max": (full.get("exit_audit") or {}).get("residual_max"),
    }
    identical = states["n_differing"] == 0
    counts_identical = (
        sweeps_other == sweeps_full
        and other.get("node_calls_single_eval") == full.get("node_calls_single_eval")
    )
    if role == "control":
        out["verdict"] = "control PASS" if (identical and counts_identical and bound_as_expected) else "control FAIL"
        out["passed"] = out["verdict"] == "control PASS"
        return out
    if not bound_as_expected:
        out["verdict"] = "other: the driver did not bind the narrowed set"
        out["passed"] = False
    elif identical and counts_identical:
        out["verdict"] = "not individually binding on this entry"
        out["passed"] = True
    elif not identical and fewer and not more:
        out["verdict"] = "bites"
        out["passed"] = True
    else:
        out["verdict"] = "other"
        out["passed"] = False
    out["bites"] = out["verdict"] == "bites"
    return out


# --------------------------------------------------------------------------
# the body
# --------------------------------------------------------------------------


def test_set_body(campaign: Campaign, *, resume: bool = False) -> dict[str, Any]:
    if campaign.test_set != "census":
        raise GateError(
            f"gate {GATE_NAME} ({PLAN_NAME}) binds the census test set and the "
            f"campaign composes {campaign.test_set!r}: under the fallback (D39) "
            f"the loops test the write set and there is no census set to drop "
            f"a component from.  Press it with --test-set census."
        )
    references = gates_mod.entry_references(campaign, resume=resume)
    plan = _plan(campaign, references)
    pool_mod.run_all([row["full"] for row in plan], campaign, resume=resume)

    root = gate_root(campaign)
    drops: list[tuple[dict[str, Any], str, str, pool_mod.Job, Path, dict[str, Any]]] = []
    for row in plan:
        full_dir = pool_mod.directory_for(row["full"], campaign)
        full = records_mod.read(full_dir)
        row["full_dir"] = full_dir
        row["full_record"] = full
        if full.get("status") != "ok":
            row["refused"] = f"the full-set run did not finish (status {full.get('status')!r})"
            continue
        residuals = exit_residuals(full_dir)
        carried = carried_union(row["sets"])
        binding, binding_value = choose(residuals, sorted(carried))
        control, control_value = choose(residuals, sorted(set(residuals) - carried))
        row["selection"] = {
            "n_carried": len(carried),
            "n_not_carried": len(set(residuals) - carried),
            RULE_BINDING: {"key": binding, "exit_residual": binding_value},
            RULE_CONTROL: {"key": control, "exit_residual": control_value},
            "tie_break": "ties, including a whole set at 0.0, to the alphabetically last key",
        }
        here = root / row["config"].name / row["arm"]
        for role, key in (("binding", binding), ("control", control)):
            if key is None:
                continue
            path = here / f"{role}_{key}.json"
            doctored = doctored_artifact(row["config"], row["arm"], key, path, role=role)
            job = dropped_job(row["full"], path)
            drops.append((row, role, key, job, path, doctored))
    pool_mod.run_all([job for *_r, job, _p, _d in drops], campaign, resume=resume)

    rows_out: list[dict[str, Any]] = []
    passed = True
    n_bites = n_not_binding = n_controls_ok = n_controls = n_binding = 0
    n_components = n_components_differing = 0
    for row in plan:
        base = {
            "configuration": row["config"].name,
            "arm": row["arm"],
            "loop_key": row["loop_key"],
            "widths": {b: len(k) for b, k in row["sets"].items()},
            "full": {
                "path": str(row["full_dir"]),
                "tree_git_head": row["full_record"].get("tree_git_head"),
                "status": row["full_record"].get("status"),
                "sweeps": _sweeps(row["full_record"]),
                "node_calls": row["full_record"].get("node_calls_single_eval"),
                "widths_stamped": _widths(row["full_record"]),
                "exit_audit_max": (row["full_record"].get("exit_audit") or {}).get("residual_max"),
                "exit_audit_n_above_tau": ((row["full_record"].get("exit_audit") or {}).get("brief") or {}).get("n_above"),
            },
            "selection": row.get("selection"),
            "refused": row.get("refused"),
        }
        if row.get("refused"):
            passed = False
            rows_out.append({**base, "passed": False})
            continue
        for prow, role, key, job, path, doctored in drops:
            if prow is not row:
                continue
            other_dir = pool_mod.directory_for(job, campaign)
            other = records_mod.read(other_dir)
            if other.get("status") != "ok":
                comparison = {"role": role, "verdict": f"the run did not finish ({other.get('status')!r})", "passed": False}
            else:
                comparison = compare_row(
                    row["full_record"], row["full_dir"], other, other_dir,
                    role=role, removed_from=doctored["removed_from_blocks"],
                )
                n_components += comparison["exit_state"]["n_components_compared"]
                n_components_differing += comparison["exit_state"]["n_differing"]
            entry = {
                **base,
                "dropped": key,
                "artifact": str(path),
                "record": str(other_dir),
                "tree_git_head": other.get("tree_git_head"),
                **comparison,
            }
            if role == "control":
                n_controls += 1
                n_controls_ok += 1 if comparison.get("passed") else 0
            else:
                n_binding += 1
                n_bites += 1 if comparison.get("bites") else 0
                n_not_binding += 1 if comparison.get("verdict") == "not individually binding on this entry" else 0
            passed = passed and bool(comparison.get("passed"))
            rows_out.append(entry)
    tooth_bit = n_bites >= 1
    passed = passed and tooth_bit
    _HELD["rows"] = rows_out
    _HELD["campaign"] = campaign
    return {
        "passed": passed,
        "criterion": (
            "per configuration and block arm of the evaluation phase, from the "
            "displaced entry at seed 1 under the census set at the campaign's "
            "tau: the carried component with the largest exit residual dropped "
            "from every block that carries it stops the loop earlier and leaves "
            "a different exit state (bit comparison over the whole of y), or is "
            "reported not individually binding on that entry; a non-carried "
            "control dropped the same way leaves counts and exit state "
            "bit-identical; the driver stamps the narrowed width; at least one "
            "drop bites over the job set"
        ),
        "criterion_source": "V5 experiment plan §3 (GT, declared from A92) and §7 Table 2",
        "test_set": campaign.test_set,
        "tau": campaign.tau,
        "rules": {RULE_BINDING: "binding", RULE_CONTROL: "control"},
        "population": (
            f"{len(plan)} full-set run(s) over {len({r['config'].name for r in plan})} "
            f"configuration(s) and arms {sorted({r['arm'] for r in plan})} at seed "
            f"{gate_entry.PAIRING_SEED}; {n_binding} binding drop(s): {n_bites} bite, "
            f"{n_not_binding} not individually binding; {n_controls} control(s), "
            f"{n_controls_ok} bit-identical; {n_components} exit-state components "
            f"compared, {n_components_differing} differing"
        ),
        "n_compared": n_components,
        "n_mismatched": n_components_differing,
        "n_full_runs": len(plan),
        "n_binding_drops": n_binding,
        "n_bites": n_bites,
        "n_not_individually_binding": n_not_binding,
        "n_controls": n_controls,
        "n_controls_bit_identical": n_controls_ok,
        "at_least_one_drop_bit": tooth_bit,
        "rows": rows_out,
    }


# --------------------------------------------------------------------------
# teeth
# --------------------------------------------------------------------------


def _teeth(campaign: Campaign) -> tuple[Tooth, ...]:
    def _biting_row() -> dict[str, Any] | None:
        return next((r for r in _HELD.get("rows", []) if r.get("bites")), None)

    def _control_row() -> dict[str, Any] | None:
        return next((r for r in _HELD.get("rows", []) if r.get("role") == "control" and r.get("passed")), None)

    def _records(row: dict[str, Any]):
        full_dir = Path(row["full"]["path"])
        other_dir = Path(row["record"])
        return records_mod.read(full_dir), full_dir, records_mod.read(other_dir), other_dir

    def a_biting_exit_state_replaced_by_the_full_one() -> tuple[bool, str]:
        import shutil  # noqa: PLC0415
        import tempfile  # noqa: PLC0415

        row = _biting_row()
        if row is None:
            return False, "no drop bit, so there is no biting exit state to doctor"
        full, full_dir, other, other_dir = _records(row)
        with tempfile.TemporaryDirectory() as tmp:
            copy = Path(tmp) / "dropped"
            shutil.copytree(other_dir, copy)
            (copy / "y_exit.json").write_text((full_dir / "y_exit.json").read_text())
            comparison = compare_row(full, full_dir, other, copy, role="binding", removed_from=row["removed_from_blocks"])
        return comparison["verdict"] != "bites", (
            f"{row['configuration']}/{row['arm']} drop of {row['dropped']}: with its exit "
            f"state replaced by the full run's the row reads {comparison['verdict']!r} "
            f"(it read 'bites' with its own): the exit-state comparison is what decides"
        )

    def one_ulp_on_a_control() -> tuple[bool, str]:
        import shutil  # noqa: PLC0415
        import tempfile  # noqa: PLC0415

        row = _control_row()
        if row is None:
            return False, "no control passed, so there is no control exit state to doctor"
        full, full_dir, other, other_dir = _records(row)
        with tempfile.TemporaryDirectory() as tmp:
            copy = Path(tmp) / "control"
            shutil.copytree(other_dir, copy)
            state = json.loads((copy / "y_exit.json").read_text())
            moved = None
            for name, entry in state["components"].items():
                value = entry.get("hex") if isinstance(entry, dict) else None
                if isinstance(value, str) and value.startswith(("0x", "-0x")):
                    f = float.fromhex(value)
                    import math  # noqa: PLC0415

                    entry["hex"] = math.nextafter(f, math.inf).hex()
                    moved = name
                    break
            if moved is None:
                return False, "the control's exit state has no scalar float component to move"
            (copy / "y_exit.json").write_text(json.dumps(state))
            comparison = compare_row(full, full_dir, other, copy, role="control", removed_from=[])
        return not comparison["passed"], (
            f"{row['configuration']}/{row['arm']} control: {moved} moved by one unit in the "
            f"last place in a copy of its exit state -> {comparison['verdict']!r}, "
            f"{comparison['exit_state']['n_differing']} of "
            f"{comparison['exit_state']['n_components_compared']} components differ"
        )

    def a_drop_that_dropped_nothing() -> tuple[bool, str]:
        import tempfile  # noqa: PLC0415

        config = next((c for c in campaign.configurations if Path(c.test_sets_path).exists()), None)
        if config is None:
            return False, "no committed census test-set artifact to doctor"
        arm = "A0"
        _key, sets = loop_sets(config, arm)
        key = next(iter(carried_union(sets)))
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "nothing.json"
            # Write an artifact that lists the key, then ask the check to
            # accept it as a drop of that key.
            artifact = json.loads(Path(config.test_sets_path).read_text())
            out.write_text(json.dumps(artifact))
            try:
                written = json.loads(out.read_text())
                loop_key = arms_mod.ARMS[arm].loop_key(config)
                still = [b for b, k in written["sets"][loop_key]["blocks"].items() if key in k]
                if still:
                    raise GateError(f"the doctored artifact still lists {key} in {still}")
            except GateError as exc:
                return True, f"an artifact claiming to drop {key} while still listing it: refused — {str(exc)[:120]}"
        return False, "an artifact still listing the key it claims to drop was accepted"

    def a_width_stamp_doctored_to_the_full_width() -> tuple[bool, str]:
        row = _biting_row() or next((r for r in _HELD.get("rows", []) if r.get("role") == "binding" and r.get("passed")), None)
        if row is None:
            return False, "no binding drop to doctor the width stamp of"
        full, full_dir, other, other_dir = _records(row)
        doctored = json.loads(json.dumps(other))
        doctored["loop_test_sets"] = json.loads(json.dumps(full.get("loop_test_sets")))
        comparison = compare_row(full, full_dir, doctored, other_dir, role="binding", removed_from=row["removed_from_blocks"])
        return not comparison["driver_bound_the_narrowed_set"] and not comparison["passed"], (
            f"{row['configuration']}/{row['arm']}: the dropped run's loop_test_sets stamp "
            f"replaced by the full run's -> driver_bound_the_narrowed_set "
            f"{comparison['driver_bound_the_narrowed_set']}, verdict {comparison['verdict']!r}"
        )

    return (
        Tooth(
            name="a biting drop's exit state replaced by the full run's",
            what="the dropped run's y_exit.json swapped for the full run's in a copy",
            must="read as not binding: the exit-state comparison is the tooth",
            check=a_biting_exit_state_replaced_by_the_full_one,
        ),
        Tooth(
            name="one ulp on a control's exit state",
            what="one float of a control run's y_exit.json moved by one unit in the last place, in a copy",
            must="FAIL the control",
            check=one_ulp_on_a_control,
        ),
        Tooth(
            name="a drop that dropped nothing",
            what="an artifact that still lists the key it claims to drop",
            must="be refused before any run is made",
            check=a_drop_that_dropped_nothing,
        ),
        Tooth(
            name="a width stamp doctored to the full width",
            what="the dropped run's loop_test_sets stamp replaced by the full run's, in a copy",
            must="fail the check that the driver bound the narrowed set",
            check=a_width_stamp_doctored_to_the_full_width,
        ),
    )


def gate(campaign: Campaign) -> Gate:
    return Gate(
        name=GATE_NAME,
        plan_name=PLAN_NAME,
        needs_runs=True,
        binds="the census test set every block loop stops on (V5 plan §3; item 6, D32; driver change DR11)",
        what_it_proves=(
            "the census test set is load-bearing: the component the declared "
            "rule finds binding, dropped from every block that carries it, stops "
            "the loop earlier and leaves a different exit state; a dropped "
            "non-census control changes nothing; the driver binds the narrowed "
            "width it is handed"
        ),
        body=lambda *, resume=False: test_set_body(campaign, resume=resume),
        jobs=lambda: gates_mod.job_rows(jobs_read, campaign),
        reads_from=("entry_and_warm",),
        teeth=_teeth(campaign),
    )
