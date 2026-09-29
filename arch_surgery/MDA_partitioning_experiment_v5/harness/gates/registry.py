"""The gate registry: every gate and every measurement stage this package runs, by name.

``registry`` is the one place a reader finds every stage; ``ordered_gate_names``
derives the order ``--gate all`` runs in from each gate's declared
``reads_from``; ``assert_declared_dependencies`` refuses a dependency on
something nobody runs; ``measurements`` lists the stages that publish numbers
and have nothing to pass; ``gate_table`` fills the experiment plan's §4.1 table
from the verdict records; ``print_verdict`` and ``main`` are the printers and
the module's own command line.  No criterion is implemented here: each gate is
constructed by its own module's ``gate(campaign)`` and collected below.

Moved verbatim out of ``harness/gates/gates.py`` (its ``_plan_gates``, tally,
analysis, chain, ``the measurement stages``, ``the registry`` and ``the gate
table`` sections and its ``main``) by the code-move task of the simplification
survey; the registry was written by task **A52 (harness-gates)**.

**This revision's registry is the V5 plan's §7 Table 2** (task A98
(v5-reporting-trim), 2026-09-29, list item 10): the predicate-mode gate G8,
the prime's cold-chain gate G3/G3c and the recomputation gate with its
``recomputed_tables`` stage are gone; the test-set gate GT and the
count-neutrality gate GC are **declared placeholders that refuse with "not
implemented"** until the driver changes they bind (DR11, DR9/DR10) land; the
reproduction gate GR is **run once**, at the copy commit, and refuses to
re-make its runs.

Usage
-----
    python -m harness.gates.registry g0prime
    python -m harness.gates.registry switch-neutrality --capture before
    python -m harness.gates.registry switch-neutrality --capture after
    python -m harness.gates.registry switch-neutrality --compare
    python -m harness.gates.registry all            # every gate that needs no capture

The one button is ``experiment_runner.py --gate`` / ``--measure``; this command
line predates it and runs the same registry entries.

Exit status: 0 every gate passed with every tooth tripping, 1 otherwise.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

_EXPERIMENT_DIR = Path(__file__).resolve().parents[2]
if str(_EXPERIMENT_DIR) not in sys.path:
    sys.path.insert(0, str(_EXPERIMENT_DIR))

from harness.core import framework  # noqa: E402
from harness.core.config import Campaign, default_campaign  # noqa: E402
from harness.gates import exclusion_review as exclusion_review_mod  # noqa: E402
from harness.gates import gate_neutrality  # noqa: E402
from harness.gates import gate_output_path  # noqa: E402
from harness.gates import gates as gates_mod  # noqa: E402
from harness.gates.gate_neutrality import capture_neutrality  # noqa: E402
from harness.gates.gate_output_path import capture_output_path  # noqa: E402

GATES_SUBPATH = framework.GATES_SUBPATH
Gate = framework.Gate
Measurement = framework.Measurement
GateError = framework.GateError


# --------------------------------------------------------------------------
# the V5 plan's declared placeholders, and the run-once gate
# --------------------------------------------------------------------------


#: The gates the V5 plan declares (§7 Table 2) whose bodies do not exist yet:
#: each binds a driver change that has not been made, and a gate that PASSed
#: over an unmade change would be a verdict on nothing.  Each entry **refuses**
#: with "not implemented" when pressed, so the gate table prints it as NOT RUN
#: rather than as a PASS, and ``--gate all`` stops at it as at any refusal.
#: The body is the task's that lands the driver change, not this registry's.
DECLARED_NOT_IMPLEMENTED: dict[str, dict[str, str]] = {
    "test_set": {
        "plan_name": "GT",
        "binds": "the census test set of plan §3 (item 6, D32; driver change DR11)",
        "what_it_proves": (
            "per configuration and arm, from the displaced entry at τ: dropping "
            "the component the declared rule finds binding stops the loop "
            "earlier and leaves an exit state that differs from the full set's; "
            "dropping a declared non-census control leaves the run bit-identical; "
            "the whole-y audit of the truncated run is reported beside"
        ),
        "pending": "DR11 (the loop's predicate binding a declared test set per block)",
    },
    "count_neutrality": {
        "plan_name": "GC",
        "binds": "items 7 and 8 of the V5 list (driver changes DR9 and DR10)",
        "what_it_proves": (
            "on a job set of both phases, every arm, one seed per configuration: "
            "node calls, sweeps, predicate evaluations, components compared and "
            "every exit state identical to the digit before and after the change"
        ),
        "pending": "DR9 (the deferral sets resolved once per run) and DR10 (the prime once per evaluation)",
    },
}

#: The gate that is pressed **once**, at the copy commit, and never re-made
#: (V5 plan §7: "No GR beyond the copy").  Its record is read under
#: ``--resume``; a press without ``--resume`` would re-run twenty PROCESS jobs
#: to reproduce what the copy commit already proved, and is refused.
RUN_ONCE: dict[str, str] = {
    "reproduction": (
        "run and PASSed at d6c246a1 by task A94 (v5-copy): 20 of 20 reference "
        "records reproduced, 256 values compared, 0 mismatched, 8 of 8 teeth; "
        "read under --resume, never re-made"
    ),
}


def _not_implemented_gate(name: str, spec: Mapping[str, str]) -> Gate:
    def refuse(*, resume: bool = False) -> dict[str, Any]:
        raise GateError(
            f"gate {name} ({spec['plan_name']}) is not implemented: it binds "
            f"{spec['pending']}, which has not been made.  A declared "
            f"placeholder refuses rather than passes; the task that lands the "
            f"driver change supplies the body and its teeth."
        )

    def a_press_is_refused() -> tuple[bool, str]:
        try:
            refuse(resume=True)
        except GateError as exc:
            return True, f"pressed with --resume: refused — {str(exc)[:120]}"
        return False, "pressed with --resume: NOT refused; a placeholder that runs is a verdict on nothing"

    return Gate(
        name=name,
        binds=spec["binds"],
        what_it_proves=spec["what_it_proves"],
        body=refuse,
        # A gate cannot be constructed without a tooth (framework.Gate); the
        # placeholder's one tooth is that it cannot be made to pass.
        teeth=(
            framework.Tooth(
                "a_press_of_the_placeholder",
                "the placeholder pressed, with --resume",
                "REFUSE with 'not implemented'",
                a_press_is_refused,
            ),
        ),
        plan_name=spec["plan_name"],
        needs_runs=False,
    )


def _run_once(name: str, gate: Gate) -> Gate:
    """*gate* with its body refusing to make runs: ``--resume`` reads the record."""
    body = gate.body

    def once(*, resume: bool = False) -> dict[str, Any]:
        if not resume:
            raise GateError(
                f"gate {name} is pressed once, at the copy commit, and is not "
                f"re-made: {RUN_ONCE[name]}.  Press it with --resume to read "
                f"its record; a from-scratch press would re-run its twenty "
                f"PROCESS jobs to prove what the copy commit already proved."
            )
        return body(resume=True)

    return dataclasses.replace(gate, body=once)


# --------------------------------------------------------------------------
# the experiment plan's gates
# --------------------------------------------------------------------------


def _plan_gates(campaign: Campaign) -> dict[str, Gate]:
    """The gates of the experiment plan's §3.9 table, by name.

    The plan's label for each is on the gate as ``plan_name``, so a reader can
    go from the plan's table to this dictionary and back without a second
    mapping to maintain.  ``G0`` and ``G0'`` are **one gate** here: the V4 plan
    §3.9's G0 row and §7.6's G0' state the same criterion — the copy's
    ``process/models/`` byte-identical to the frozen base commit — and giving
    one criterion two entries is how two implementations start.

    Each literal lives in the module that implements the gate, as that
    module's ``gate(campaign)``; this function only collects them.
    """
    from . import gate_audit, gate_composition, gate_entry, gate_prime, gate_records

    return {
        "reproduction": _run_once("reproduction", gates_mod.reproduction_gate(campaign)),
        "g0prime": gates_mod.g0prime_gate(campaign),
        "switch_neutrality": gate_neutrality.gate(campaign),
        "prime_map": gate_prime.prime_map_gate(campaign),
        "audit_restriction": gate_audit.audit_restriction_gate(campaign),
        "switch_composition": gate_composition.switch_composition_gate(campaign),
        "entry_and_warm": gate_entry.entry_and_warm_gate(campaign),
        "record_completeness": gate_records.record_completeness_gate(campaign),
        "output_path": gate_output_path.gate(campaign),
        # The V5 plan's two new gates, declared and refusing (see the module
        # docstring): GT the test set's teeth, GC count neutrality.
        **{
            name: _not_implemented_gate(name, spec)
            for name, spec in DECLARED_NOT_IMPLEMENTED.items()
        },
    }


# --------------------------------------------------------------------------
# the tally: two measurement stages and one gate  (task A53 (harness-tally))
# --------------------------------------------------------------------------
#
# Kept as one contiguous block so that the registry's other entries and this
# one can be merged past each other without a conflict in the middle of a
# dictionary.  The two stages publish the experiment plan's section 4 tables
# and have nothing to pass; the gate is the set of things a table may not be,
# plus the previous revision's published cells.


def _tally_gates(campaign: Campaign) -> dict[str, Gate]:
    """The tally's own gate, with its ten teeth."""
    from harness.gates import gate_tally as gate_tally_mod  # noqa: PLC0415

    return {"tally_contracts": gate_tally_mod.gate(campaign)}


def _tally_measurements(campaign: Campaign) -> dict[str, Measurement]:
    """The two tally stages: one per phase, each with nothing to pass."""
    from harness.measurement import tally_evaluation as tally_a_mod  # noqa: PLC0415
    from harness.measurement import tally_optimisation as tally_b_mod  # noqa: PLC0415

    return {
        "tally_evaluation": Measurement(
            name="tally_evaluation",
            reports=(
                "the evaluation phase's tables of the experiment plan's "
                "section 4.2 -- cost per call, matched accuracy on both "
                "rulers, the fixed-point distance between arms, the ownership "
                "rung, the per-sweep overhead and the failure taxonomy -- each "
                "with its caption, its denominator "
                "and the audit position it was measured at"
            ),
            guarded_by="tally_contracts",
            body=lambda *, resume=False: tally_a_mod.tally(campaign, resume=resume),
            printer=tally_a_mod.print_tally,
        ),
        "tally_optimisation": Measurement(
            name="tally_optimisation",
            reports=(
                "the optimisation phase's tables of the experiment plan's "
                "section 4.3 -- the one seed set and the failure table, the "
                "same-optimum check, check 2 in both iteration constructions, "
                "the attempt summation identity, the cost with and without "
                "the retried seeds, and the lift's residual"
            ),
            guarded_by="tally_contracts",
            body=lambda *, resume=False: tally_b_mod.tally(campaign, resume=resume),
            printer=tally_b_mod.print_tally,
        ),
    }


# The second implementation (task A54 (harness-analysis)'s ``analysis.py``,
# gate ``recomputation`` and stage ``recomputed_tables``) was removed under
# V5 list item 10; its replacement is the short independent recount of the
# paper's cells, ``paper_cells_recount.py`` beside the runner, which is a
# script and not a registry entry.


# --------------------------------------------------------------------------
# the chain: one gate  (task A55 (harness-smoke))
# --------------------------------------------------------------------------
#
# Its own contiguous block, for the same merge reason as the two above.  The
# chain is not itself a gate — it is what the button runs, as the smoke and as
# the campaign — and what it registers here is the one thing about it that can
# be checked without running it: that the two parameterisations stay apart, so
# that a one-seed test of the machinery is never summarised as a measurement
# and a campaign record is never made by a path the user has not approved.


def _written_file_gates(campaign: Campaign) -> dict[str, Gate]:
    """The gate that measures the written-file gap on the one-call output path (I-21).

    Not one of the experiment plan's §3.9 gates -- it publishes a finding about
    PROCESS's output pass and gates only on its runs' composition and audit
    position -- so it carries no ``plan_name`` and is listed under its own name.
    """
    from . import gate_written_file

    return {gate_written_file.GATE_NAME: gate_written_file.gate(campaign)}


def _identity_gates(campaign: Campaign) -> dict[str, Gate]:
    """The resume-identity gate (task A72): the job identity and the shared pool."""
    from . import gate_resume_identity

    return {gate_resume_identity.GATE_NAME: gate_resume_identity.gate(campaign)}


def _chain_gates(campaign: Campaign) -> dict[str, Gate]:
    """The run-kind separation gate, with its six teeth."""
    from harness import chain as chain_mod  # noqa: PLC0415

    return {"run_kind_separation": chain_mod.gate(campaign)}


# --------------------------------------------------------------------------
# the measurement stages
# --------------------------------------------------------------------------


def measurements(campaign: Campaign) -> dict[str, Measurement]:
    """Every stage that publishes numbers and has nothing to pass.

    They are listed beside the gates because a reader looking for "what does
    this package run?" should find one answer, and they are a different type
    because a measurement has no verdict and must never be read as one.
    """
    return {
        "gate_table": Measurement(
            name="gate_table",
            reports=(
                "the experiment plan §4.1's gate table, filled in from the "
                "verdict records: one row per registered gate with its "
                "population, its denominator, its mismatches and its teeth"
            ),
            guarded_by="each gate is its own guard; this reads what they wrote",
            body=lambda *, resume=False: gate_table(campaign),
            printer=print_gate_table,
            # The verdict records this table is made of, declared so that the
            # framework stamps what it read and the plan's renderer can refuse
            # a section built from verdicts that have since been re-made
            # (I-22 (a)).  The pattern, not the list: a gate run *after* this
            # stage leaves a verdict nobody read, and only the pattern finds it.
            reads_records=("*/gate.json",),
        ),
        "exclusion_review": Measurement(
            name="exclusion_review",
            reports=(
                "every exclusion of every gate that compares two records, "
                "classified by kind and measured against that gate's own "
                "captured records: how many leaves each name covers on each "
                "side, whether both sides carry them, and what this review "
                "did with the name"
            ),
            guarded_by="switch_neutrality",
            body=lambda *, resume=False: exclusion_review_mod.exclusion_review(campaign),
            printer=exclusion_review_mod.print_exclusion_review,
        ),
        **_tally_measurements(campaign),
    }


# --------------------------------------------------------------------------
# the registry
# --------------------------------------------------------------------------


def assert_declared_dependencies(entries: Mapping[str, Any]) -> None:
    """Refuse a gate whose ``reads_from`` names something the registry lacks.

    A dependency may name **either** a gate or a measurement stage: a gate that
    reads another gate's runs has to follow it, and a gate that reads a
    measurement stage's *output* has to follow that stage (the removed
    ``recomputation`` gate compared the tally's emitted tables, which only
    ``--measure tally_evaluation`` and ``--measure tally_optimisation``
    produce; the mechanism stays).  What may not be named is something nobody runs: a gate declaring
    one would be ordered after nothing and would read whatever happened to be
    on disk, which is the failure the declaration exists to prevent.

    Called by :func:`registry` so the refusal happens as the registry is built,
    not later at ordering time, and so every consumer of the registry gets it.
    """
    unknown = {
        name: sorted(set(entry.reads_from) - set(entries))
        for name, entry in entries.items()
        if isinstance(entry, Gate) and set(entry.reads_from) - set(entries)
    }
    if unknown:
        raise GateError(
            f"gate(s) declare a dependency on something the registry does not "
            f"hold: {unknown}.  A dependency may name a gate or a measurement "
            f"stage; it may not name something nobody runs, because such a "
            f"gate is ordered after nothing and reads whatever happened to be "
            f"on disk."
        )


def measurement_dependencies(campaign: Campaign, name: str) -> tuple[str, ...]:
    """The measurement stages gate *name* declares it reads, in declared order.

    The button runs these **before** the gate, so a gate that compares a
    stage's output is never run against a stage record that was never made.
    """
    entries = registry(campaign)
    gate = entries.get(name)
    if not isinstance(gate, Gate):
        return ()
    stages = measurements(campaign)
    return tuple(
        dependency for dependency in gate.reads_from if dependency in stages
    )


def registry(campaign: Campaign) -> dict[str, Any]:
    """**Every** gate and every measurement stage this package runs, by name.

    Three groups, in one dictionary because a reader should not have to know
    which group a name is in to look it up:

    * the experiment plan's §3.9 gates — ``GR``, ``G0``/``G0'``, ``G1``–``G9``
      — each carrying the plan's own label in ``plan_name``;
    * the copy's two other gates, ``copy_identity`` and ``edit_behaviour``,
      loaded from ``PROCESS/copy_gates.py`` by path as G0' is;
    * the harness's own checks, promoted: the six self-checks and the four
      artifact stages, with their criteria unchanged;
    * the measurement stages, which have no verdict and are a different type so
      that nothing can read one as a gate.

    Every entry has ``.run(records_dir=…)`` and writes its record under
    ``runs/gates/<name>/``.
    """
    entries: dict[str, Any] = {}
    entries.update(_plan_gates(campaign))
    entries.update(gates_mod.copy_gates(campaign))
    entries["self_containment"] = gates_mod.self_containment_gate(campaign)
    entries.update(gates_mod._selfcheck_gates(campaign))
    entries.update(gates_mod._artifact_gates(campaign))
    entries.update(_tally_gates(campaign))
    entries.update(_written_file_gates(campaign))
    entries.update(_identity_gates(campaign))
    entries.update(_chain_gates(campaign))
    entries.update(measurements(campaign))
    assert_declared_dependencies(entries)
    return entries


# --------------------------------------------------------------------------
# the gate table the experiment plan's §4.1 asks for
# --------------------------------------------------------------------------
#
# The plan carries a placeholder table — one row per gate, with its verdict, its
# tooth and its record — and says that no number in the results section is cited
# unless every row is PASS with its tooth tripped.  This stage fills it in from
# the verdict records themselves, so the table in the report and the files on
# disk cannot drift apart: there is no hand-copied cell in it.
#
# It is a measurement and not a gate.  It has nothing to pass: what passes is
# each gate, and this reads what they wrote.


#: The pairs of (compared, differing) fields a gate's verdict can carry.  A gate
#: whose criterion is a count of compared values writes one of these pairs;
#: three of them write more than one, because they compare more than one kind of
#: thing — coupling-state components, record values, output-file lines — and a
#: denominator that silently added them together without saying which is which
#: would be a count over a population nobody can state.  The table sums them and
#: names the pairs it summed.
COUNT_FIELDS: tuple[tuple[str, str], ...] = (
    ("n_compared", "n_mismatched"),
    ("n_values_compared", "n_values_differing"),
    ("n_components_compared", "n_components_differing"),
    ("n_reference_values_compared", "n_reference_values_differing"),
    ("n_mfile_lines_compared", "n_mfile_lines_differing"),
)


def _counts(verdict: Mapping[str, Any]) -> tuple[int | None, int | None, list[str]]:
    compared = differing = None
    named: list[str] = []
    for compared_field, differing_field in COUNT_FIELDS:
        value = verdict.get(compared_field)
        if not isinstance(value, int):
            continue
        compared = (compared or 0) + value
        differing = (differing or 0) + int(verdict.get(differing_field) or 0)
        named.append(f"{compared_field} = {value}")
    return compared, differing, named


def gate_table(campaign: Campaign, records_dir: Path | None = None) -> dict[str, Any]:
    """Every gate's verdict record, as the plan's §4.1 table."""
    root = Path(records_dir or (Path(campaign.runs_dir) / GATES_SUBPATH))
    entries = registry(campaign)
    rows: list[dict[str, Any]] = []
    for name in ordered_gate_names(campaign):
        gate = entries[name]
        path = root / name / "gate.json"
        if not path.exists():
            rows.append(
                {
                    "gate": name,
                    "plan_name": gate.plan_name,
                    "binds": gate.binds,
                    "verdict": "NOT RUN",
                    "population": "—",
                    "n_compared": None,
                    "n_mismatched": None,
                    "n_teeth": len(gate.teeth),
                    "n_teeth_tripped": None,
                    "record": str(path),
                }
            )
            continue
        verdict = json.loads(path.read_text())
        teeth = verdict.get("teeth") or []
        compared, differing, named = _counts(verdict)
        rows.append(
            {
                "gate": name,
                "plan_name": gate.plan_name,
                "binds": gate.binds,
                "verdict": verdict.get("verdict"),
                "population": verdict.get("population") or "—",
                "n_compared": compared,
                "n_mismatched": differing,
                "denominators_summed": named,
                "n_teeth": len(teeth),
                "n_teeth_tripped": sum(1 for t in teeth if t.get("caught")),
                "teeth": [t.get("tooth") for t in teeth],
                "generated": verdict.get("generated"),
                "tree_git_head": verdict.get("tree_git_head"),
                "record": str(path.relative_to(Path(campaign.runs_dir).parent)),
            }
        )
    plan_rows = [row for row in rows if row["plan_name"]]
    harness_rows = [row for row in rows if not row["plan_name"]]
    return {
        "what_this_is": (
            "the experiment plan §4.1's gate table, filled in from the verdict "
            "records rather than by hand"
        ),
        # The full reading of the columns is the declaration, printed once in
        # the results appendix's constructions subsection; the caption is the
        # few lines the report prints under the table (task A79
        # (report-captions), the user's ruling of 2026-09-15).
        "declaration": (
            "'plan' is the label the experiment plan's §3.9 table uses, empty "
            "where the gate is one of the harness's own checks rather than one "
            "of the plan's. 'verdict' is PASS/FAIL on the gate's criterion "
            "**and** on every tooth tripping. 'population' is what the gate "
            "compared, in its own words; 'compared' is the denominator and "
            "'mismatched' the count of things that differed — both are the "
            "gate's own headline pair, and a gate whose criterion is not a "
            "count of compared values leaves them empty and states its "
            "population in words instead. Where a gate compares more than one "
            "kind of thing — coupling-state components, record values, "
            "output-file lines — the denominator is their sum and the row's "
            "'denominators summed' names each. 'teeth' is tripped / declared. "
            "A gate whose tooth did not trip is not accepted whatever its "
            "verdict."
        ),
        "caption": (
            "Every registered gate from its verdict record: the verdict on "
            "the criterion and every tooth, what it compared (the denominator) "
            "and how many differed, teeth tripped / declared. No number in "
            "this appendix is cited unless every row is PASS with its teeth "
            "tripped; the two PASS rows with a nonzero mismatched count are "
            "the frozen-physics gate (1: the one approved model file, by name) "
            "and the copy-identity gate (8: the recorded permitted driver-edit "
            "files, by name and digest). A compared count that sums more than "
            "one kind of thing shows its parts in brackets."
        ),
        "population": (
            f"{len(rows)} registered gate(s): {len(plan_rows)} of the "
            f"experiment plan's §3.9 table and {len(harness_rows)} of the "
            f"harness's own checks, promoted"
        ),
        "n_gates": len(rows),
        "n_pass": sum(1 for row in rows if row["verdict"] == "PASS"),
        "n_fail": sum(1 for row in rows if row["verdict"] not in ("PASS", "NOT RUN")),
        "n_not_run": sum(1 for row in rows if row["verdict"] == "NOT RUN"),
        "n_teeth": sum(row["n_teeth"] for row in rows),
        "n_teeth_tripped": sum(row["n_teeth_tripped"] or 0 for row in rows),
        "rows": rows,
        "markdown": _gate_table_markdown(rows),
    }


def _gate_table_markdown(rows: Sequence[Mapping[str, Any]]) -> str:
    lines = [
        "| gate | plan | binds | verdict | population | compared | mismatched "
        "| teeth | record |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        teeth = (
            f"{row['n_teeth_tripped']}/{row['n_teeth']}"
            if row["n_teeth_tripped"] is not None
            else f"—/{row['n_teeth']}"
        )
        population = str(row["population"]).replace("|", "/")
        if len(population) > 150:
            population = population[:147] + "…"
        # A 'compared' count summed over more than one kind of thing shows its
        # parts, so that 559 reads as 303 table checks + 256 reference cells
        # and not as one population (task A80 (report-accuracy-audit), on A79's
        # finding; the declaration's 'denominators summed' clause made concrete).
        compared = "—" if row["n_compared"] is None else str(row["n_compared"])
        summed = row.get("denominators_summed") or []
        if len(summed) > 1:
            parts = " + ".join(item.split("=")[-1].strip() for item in summed)
            compared = f"{compared} ({parts})"
        lines.append(
            f"| `{row['gate']}` | {row['plan_name'] or '—'} | "
            f"{str(row['binds'])[:90]} | **{row['verdict']}** | {population} | "
            f"{compared} | "
            f"{row['n_mismatched'] if row['n_mismatched'] is not None else '—'} | "
            f"{teeth} | `{row['record']}` |"
        )
    return "\n".join(lines)


def print_gate_table(block: Mapping[str, Any]) -> None:
    print(f"\n  {block['what_this_is']}")
    print(f"\n  {block['caption']}\n")
    print(f"  population: {block['population']}\n")
    print(
        f"    {'gate':<24} {'plan':<10} {'verdict':<8} {'compared':>9} "
        f"{'mismatch':>9}  teeth"
    )
    for row in block["rows"]:
        teeth = (
            f"{row['n_teeth_tripped']}/{row['n_teeth']}"
            if row["n_teeth_tripped"] is not None
            else f"—/{row['n_teeth']}"
        )
        print(
            f"    {row['gate']:<24} {str(row['plan_name'] or '—'):<10} "
            f"{str(row['verdict']):<8} "
            f"{str(row['n_compared'] if row['n_compared'] is not None else '—'):>9} "
            f"{str(row['n_mismatched'] if row['n_mismatched'] is not None else '—'):>9}"
            f"  {teeth}"
        )
    print(
        f"\n    {block['n_pass']} PASS, {block['n_fail']} FAIL, "
        f"{block['n_not_run']} not run; "
        f"{block['n_teeth_tripped']} of {block['n_teeth']} teeth tripped"
    )
    print("\n  as markdown:\n")
    print(block["markdown"])


def gates_only(campaign: Campaign) -> dict[str, Gate]:
    """The registry's gates: everything with a verdict."""
    return {
        name: entry
        for name, entry in registry(campaign).items()
        if isinstance(entry, Gate)
    }


#: The order ``--gate all`` runs in: cheapest first, so a repository-state
#: failure is reported in seconds rather than after an hour of runs.  A name
#: absent from this tuple still runs — it is appended in registry order — so a
#: gate added later cannot be silently left out of the button.
GATE_ORDER: tuple[str, ...] = (
    "g0prime",
    # The copy's two other gates: the same criterion library as G0', loaded
    # by path, no PROCESS run.
    "copy_identity",
    "edit_behaviour",
    # The package scanned for the two superseded directories: a gate since
    # the simplification survey's item B8, no PROCESS run.
    "self_containment",
    "composition",
    "rungs",
    "provenance",
    "data",
    "run_path",
    # The job identity and the shared pool's distinctness pairs: composed
    # from the gate modules' own job constructors, no PROCESS run.
    "resume_identity",
    "capability",
    "artifacts_check",
    "artifacts_derive_inputs",
    "artifacts_census",
    "artifacts_per_run",
    "record_completeness",
    "prime_map",
    "audit_restriction",
    "entry_and_warm",
    "switch_composition",
    "output_path",
    # Six runs; it reads G9's records for its beside-column, so the dependency
    # already puts it after output_path whatever this preference says.
    "written_file_gap",
    "switch_neutrality",
    "reproduction",
    "tally_contracts",
    # Last by preference and not by dependency: it reads every record the press
    # made, so running it after the press is what makes its denominator the
    # whole tree rather than whatever existed when it started.
    "run_kind_separation",
)
# The two declared placeholders are not in the preference: they rank after
# every name, listed or not (``ordered_gate_names``), because each refuses and
# a refusal stops ``--gate all`` — so nothing is left unpressed behind them.


def ordered_gate_names(campaign: Campaign) -> list[str]:
    """Every gate's name, cheapest first **and after what it reads**.

    :data:`GATE_ORDER` is a *preference*: run the cheap repository-state checks
    before the hour of runs, so a failure is reported in seconds.  It is not a
    correctness order, and treating it as one was a defect the from-scratch run
    found: gate G9 reads the reproduction gate's own runs, and cheapest-first
    put the reproduction gate last, so on a tree with no runs at all G9 refused
    for want of records that were about to be made.  With everything resumed
    from an earlier session it had never surfaced.

    So the order is now *derived*: the preference decides between gates that do
    not depend on each other, and a declared ``reads_from`` decides when they
    do.  A dependency naming a gate that does not exist, or a cycle, raises —
    an order nobody can compute is not an order.
    """
    entries = registry(campaign)          # refuses an undeclared dependency
    available = {n: e for n, e in entries.items() if isinstance(e, Gate)}
    preference = {name: i for i, name in enumerate(GATE_ORDER)}
    last = len(GATE_ORDER) + 1
    rank = sorted(
        available,
        key=lambda n: (
            last if n in DECLARED_NOT_IMPLEMENTED else preference.get(n, len(GATE_ORDER)),
            n,
        ),
    )
    # Only a **gate** dependency takes part in this order.  A measurement
    # dependency is not ordered here because a stage has no verdict and no
    # place in the gate sequence: the button runs it immediately before the
    # gate that declares it (``measurement_dependencies``), which is what makes
    # "the gate never reads a stage record nobody made" true.
    pending = {
        name: {
            dependency
            for dependency in available[name].reads_from
            if dependency in available
        }
        for name in rank
    }
    ordered: list[str] = []
    while pending:
        ready = [name for name in rank if name in pending and not pending[name]]
        if not ready:
            raise GateError(
                f"the declared reads-from dependencies are cyclic among "
                f"{sorted(pending)}; no order runs each gate after what it reads"
            )
        chosen = ready[0]
        ordered.append(chosen)
        del pending[chosen]
        for remaining in pending.values():
            remaining.discard(chosen)
    return ordered


def print_verdict(verdict: Mapping[str, Any]) -> None:
    print(f"\n=== gate {verdict['gate']} — {verdict['what_it_proves']}")
    print(f"    binds        : {verdict['binds']}")
    print(f"    verdict      : {verdict['verdict']}")
    print(f"    population   : {verdict.get('population', '(none stated)')}")
    provenance = verdict.get("runs_provenance") or {}
    if provenance.get("n_records"):
        own = verdict.get("tree_git_head")
        heads = provenance["records_by_head"]
        summary = ", ".join(
            f"{count} at {head[:8]}" + (" (this commit)" if head == own else "")
            for head, count in sorted(heads.items(), key=lambda kv: -kv[1])
        )
        print(
            f"    runs read    : {provenance['n_records']} record(s) — {summary}"
            + ("  [resumed]" if verdict.get("resumed") else "")
        )
    if verdict.get("runs_are_not_this_commit's"):
        print(f"    NOTE         : {verdict["runs_are_not_this_commit's"]}")
    for key in (
        "n_compared",
        "n_identical",
        "n_mismatched",
        "n_pairs",
        "n_values_compared",
        "n_values_excluded",
        "n_values_differing",
        "n_mfile_lines_compared",
        "n_mfile_lines_excluded",
        "n_mfile_lines_differing",
    ):
        if key in verdict:
            print(f"    {key:<28}: {verdict[key]}")
    for key in (
        "n_runs",
        "n_components_compared",
        "n_components_differing",
        "n_reference_values_compared",
        "n_reference_values_differing",
    ):
        if key in verdict:
            print(f"    {key:<28}: {verdict[key]}")
    for row in verdict.get("runs", []):
        if "checks" in row:
            print(
                f"      {row['arm']:<3} {row['configuration']:<22} "
                f"loop={row['matrix_cell']:<8} path={str(row['output_path']):<14} "
                f"sweeps={row['output_loop_sweeps']}  "
                f"{'PASS' if row['passed'] else 'FAIL'}"
            )
            for check in row["checks"]:
                print(f"        [{'ok ' if check['passed'] else 'FAIL'}] "
                      f"{check['check']} — {check['detail']}")
            continue
        print(
            f"      {row['arm']:<3} {row['configuration']:<22} "
            f"values {row['record']['n_mismatched']}/{row['record']['n_compared']} "
            f"lines {row['mfile']['n_lines_differing']}/"
            f"{row['mfile']['n_lines_compared']}  "
            f"{'PASS' if row['passed'] else 'FAIL'}"
        )
        for mismatch in row["record"]["mismatches"][:10]:
            print(f"        DIFFERS {mismatch['field']}: {mismatch.get('before')!r} "
                  f"-> {mismatch.get('after')!r}")
        for line in row["mfile"]["differing"][:10]:
            print(f"        LINE {line['line']}: {line['before']!r} -> {line['after']!r}")
    for failure in verdict.get("failures", []) or []:
        print(f"    FAILURE: {failure}")
    for tooth in verdict.get("teeth", []):
        print(f"    tooth {tooth['tooth']:<32} {tooth['tooth_result']:<13} {tooth['evidence']}")
    print(f"    record       : {verdict.get('record')}")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "gate",
        choices=(
            "g0prime",
            "switch-neutrality",
            "output-path",
            "all",
        ),
        help="which gate to run; 'all' runs the gates that need no capture",
    )
    parser.add_argument(
        "--capture",
        choices=("before", "after", "runs"),
        help="switch-neutrality: run the two reference arms on every "
        "configuration and record them under this label ('before' or "
        "'after'), then stop.  output-path: 'runs' makes the gate's own "
        "runs, then stops",
    )
    parser.add_argument(
        "--compare",
        action="store_true",
        help="switch-neutrality: compare the two captures (the default)",
    )
    parser.add_argument("--resume", action="store_true", help="skip completed runs")
    parser.add_argument("--no-teeth", action="store_true", help="skip the teeth")
    parser.add_argument(
        "--records", default=None, help="where the verdict goes (default runs/gates)"
    )
    args = parser.parse_args(argv)

    campaign = default_campaign()
    records_dir = Path(args.records) if args.records else Path(campaign.runs_dir) / GATES_SUBPATH

    if args.gate == "output-path" and args.capture:
        manifest = capture_output_path(campaign, resume=args.resume)
        print(f"captured {manifest['n_runs']} run(s) at "
              f"{manifest['tree_git_head']}")
        for row in manifest["runs"]:
            print(f"  {row['arm']:<3} {row['configuration']:<22} "
                  f"{row['status']} {row['outdir']}")
        print(f"  manifest: {manifest['manifest']}")
        return 0

    if args.gate == "switch-neutrality" and args.capture:
        manifest = capture_neutrality(campaign, args.capture, resume=args.resume)
        print(f"captured {manifest['n_runs']} run(s) as {args.capture!r} at "
              f"{manifest['tree_git_head']}")
        for row in manifest["runs"]:
            print(f"  {row['arm']:<3} {row['configuration']:<22} {row['outdir']}")
        print(f"  manifest: {manifest['manifest']}")
        return 0

    names = (
        ["g0prime"]
        if args.gate in ("g0prime", "all")
        else []
    )
    if args.gate == "switch-neutrality":
        names = ["switch_neutrality"]
    elif args.gate == "output-path":
        names = ["output_path"]
    elif args.gate == "all":
        names.append("switch_neutrality")
        names.append("output_path")

    gates = registry(campaign)
    status = 0
    for name in names:
        try:
            verdict = gates[name].run(records_dir=records_dir, teeth=not args.no_teeth)
        except GateError as exc:
            print(f"\n=== gate {name} — REFUSED TO RUN\n    {exc}")
            status = 1
            continue
        print_verdict(verdict)
        if verdict["verdict"] != "PASS":
            status = 1
    return status


if __name__ == "__main__":
    sys.exit(main())
