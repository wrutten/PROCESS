#!/usr/bin/env python
"""The runtime census: what each model node writes, and what the predicate reads.

A **census** here is a direct observation, not an inference.  The driver carries
an instrument that, while it is switched on, attributes every read and every
write of a data-structure field to the model node executing at the time.  This
module runs one PROCESS run with that instrument on and turns what it recorded
into two things:

* the **write sets** — per node, which fields it wrote.  Three committed
  artifacts rest on this: the per-node write census the driver reads to decide
  which nodes may leave the loop, the per-block subsets each block's convergence
  test is taken over, and the per-run deferral sets;
* the **read census** — per node, which fields it read, including the
  objective/constraint block, which is what the predicate layer reads for the
  configuration's figure of merit.  The improvement list asks for this because
  the strongest claim in the deferral derivation rested on a source scan plus a
  crawl of the dependency model, and a runtime census turns that into a direct
  observation.

Two traps are structural here, not matters of care
--------------------------------------------------
Ten model objects call their own ``run()`` from inside their ``output()``
method, three times each per run, during the final output idempotence check.  An
instrument that hooks ``run()`` alone therefore attributes post-solve reporting
traffic to the analysis loop and invents dependency edges — it produced two
phantom back edges before it was fixed.  The driver's instrument closes the
sweep at the boundary of one pass over the model sequence and **refuses**
anything entering afterwards, so the exclusion is structural.  This module
records the refusal count so a reader can see the mechanism worked rather than
assume it (traps T1 and T7).

What this module does not do
----------------------------
It does not write a committed artifact.  The committed write census is the one
the earlier revisions measured, and the driver reads it; regenerating it here
would change the definition of the coupling state under every residual figure
this experiment has published.  What this stage does is **compare**: a
difference between what a run does now and what the committed file says is a
finding, reported with its content.

Derived from the census probe ``process/core/_idf_probe_modules.py`` (read, not
modified) and from ``arch_surgery/fixedpoint/gen_node_writesets.py`` and
``arch_surgery/idf_probe/a25_writeset.py``, read at ``f1f90c20``; task
**A51 (harness-artifacts)**.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import traceback
from pathlib import Path
from typing import Any, Mapping, Sequence

_HERE = Path(__file__).resolve().parent
_EXPERIMENT_DIR = _HERE.parent
if sys.path and Path(sys.path[0] or ".").resolve() == _HERE:
    sys.path[0] = str(_EXPERIMENT_DIR)
elif str(_EXPERIMENT_DIR) not in sys.path:
    sys.path.insert(0, str(_EXPERIMENT_DIR))

from harness.artifacts import StageCheck  # noqa: E402
from harness.config import Campaign, Config  # noqa: E402

#: The probe mode that attributes reads and writes to nodes.
PROBE_MODE = "modules"

#: The probe's own environment variables.  These belong to the *instrument*,
#: not to the architecture: they select what is observed, never what is
#: computed.  They are named here literally, and only here, because the
#: architecture switches are composed through the arm registry and a literal
#: architecture name anywhere in this package would be a second place to change
#: when one is renamed.
PROBE_VARIABLE = "PROCESS_IDF_PROBE"
PROBE_READ_BUDGET_VARIABLE = "PROCESS_IDF_PROBE_READ_BUDGET"
PROBE_READ_STRIDE_VARIABLE = "PROCESS_IDF_PROBE_READ_STRIDE"

#: The two pseudo-nodes the census records that are not model calls: the
#: injection of the design vector, and the objective/constraint block.  The
#: second is the **predicate layer**, and its read set is the direct
#: observation of what the optimiser consumes.
DESIGN_VECTOR_NODE = "<x_inject>"
PREDICATE_NODE = "objective_constraints"

#: Where this stage's records go.  Untracked, like every run artifact.
RUNS_SUBPATH = "census"

#: Which arm a census is taken under, per entry.  It is the **reference** arm
#: in both cases — PROCESS as shipped, every architecture switch unset — because
#: the committed census describes what the models write when nothing has been
#: rearranged, and a census taken under an intervention arm would describe that
#: arm's schedule instead.  The instrument itself is not an architecture switch:
#: it observes, and the run it observes is byte-identical to one without it.
CENSUS_ARM = {"evaluation": "AR", "optimisation": "BR"}

#: What one run of the census costs, stated so a reader can choose.  Neither is
#: evidence of anything; both are how long to wait.
ENTRIES = {
    "evaluation": (
        "one evaluation of the model set at the input file's own design point "
        "— every node runs, so every node's write set is observed, but only at "
        "one point of the design space"
    ),
    "optimisation": (
        "one full optimisation — the same population of design points the "
        "committed census was measured over, and the only entry that can "
        "reproduce it; far more expensive"
    ),
}


class CensusError(RuntimeError):
    """A refusal to census, or to compare one."""


# ==========================================================================
# the child: one PROCESS run with the instrument on
# ==========================================================================


def _reads_by_node(probe_modules) -> dict[str, list[str]]:
    """The read census, per node, from the instrument's own bookkeeping.

    The instrument records reads per node and reports their **count** in its
    summary, but not the field names.  The names are what the deferral
    derivation needs, so they are read here from the instrument's own state
    inside the same process that produced them.

    This is deliberately on the harness side of the line.  Adding the field
    lists to the instrument's summary is a one-line change to
    ``_idf_probe_modules.summary()`` — ``"reads_by_node": {n: sorted(f"{a}.{b}"
    for a, b in v) for n, v in _reads_all.items()}``, exactly beside the
    ``writes_by_node`` entry already there — and it belongs to whichever driver
    task next touches the instrument, because a driver change made from a
    harness task would land outside its own neutrality gate.  Until then the
    harness reads the state rather than the report, and this docstring is the
    handover.
    """
    return {
        node: sorted(f"{namespace}.{field}" for namespace, field in fields)
        for node, fields in probe_modules._reads_all.items()
    }


def run_child(args: argparse.Namespace) -> int:
    """One PROCESS run with the census instrument on, inside this process.

    Reached only as a subprocess started by the pool: the tree is asserted for
    equality before anything else happens, and this file never runs a model in
    the parent.
    """
    import os

    outdir = Path(args.outdir).resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    os.environ[PROBE_VARIABLE] = PROBE_MODE
    if args.read_census:
        os.environ.pop(PROBE_READ_BUDGET_VARIABLE, None)
        os.environ.pop(PROBE_READ_STRIDE_VARIABLE, None)
    else:
        # The read hooks override attribute *access* on every data-structure
        # object, which is the expensive half of the instrument.  A write-only
        # census switches them off rather than paying for names it will not use.
        os.environ[PROBE_READ_BUDGET_VARIABLE] = "0"
        os.environ[PROBE_READ_STRIDE_VARIABLE] = "0"

    from harness import provenance as prov

    record: dict[str, Any] = {
        "record_format": "census-1",
        "campaign_phase": "census",
        "campaign_configuration": args.configuration,
        "campaign_arm": args.arm,
        "campaign_seed": 0,
        "campaign_run_kind": args.run_kind,
        "regime": "unperturbed",
        "entry": args.entry,
        "read_census": bool(args.read_census),
        "probe_mode": PROBE_MODE,
        "status": "started",
    }
    started = time.perf_counter()
    try:
        process_file = prov.assert_tree(Path(args.tree))
        record["process_file"] = str(process_file)
        record["provenance"] = prov.stamp(Path(args.tree), process_file=str(process_file))

        source = Path(args.input)
        local_input = outdir / f"{args.configuration}.IN.DAT"
        local_input.write_text(source.read_text())

        from process.core import _idf_probe as probe
        from process.core import _idf_probe_modules as probe_modules
        from process.core.caller import Caller
        from process.core.solver.iteration_variables import (
            load_iteration_variables,
            load_scaled_bounds,
        )
        from process.main import SingleRun

        if not probe.ENABLED or probe.MODE != PROBE_MODE:
            raise CensusError(
                f"the census instrument is not on: {PROBE_VARIABLE} resolved "
                f"to {probe.MODE!r} inside the child.  A census taken with the "
                f"instrument off would report an empty write set for every "
                f"node and look like a passing comparison against nothing."
            )

        single_run = SingleRun(
            str(local_input), solver="vmcon", update_obsolete=True
        )
        data = single_run.data
        load_iteration_variables(data)
        load_scaled_bounds(data)
        numerics = data.numerics
        n = int(numerics.n_iteration_variables)
        m = int(numerics.n_equality_constraints) + int(
            numerics.n_inequality_constraints
        )
        record["nvar"] = n
        record["n_constraints"] = m
        record["i_figure_merit"] = int(numerics.i_figure_merit)

        if args.entry == "evaluation":
            caller = Caller(single_run.models, data)
            caller.call_models(numerics.xcm[:n], m)
        elif args.entry == "optimisation":
            single_run.run()
        else:  # pragma: no cover - argparse restricts it
            raise CensusError(f"unknown census entry {args.entry!r}")
        record["status"] = "ok"
        record["failure_class"] = "ok"
    except BaseException as exc:  # noqa: BLE001 - recorded, then reported
        record["status"] = "crashed"
        record["failure_class"] = "machinery"
        record["error"] = f"{type(exc).__name__}: {exc}"
        record["traceback"] = traceback.format_exc()
        (outdir / "metrics.json").write_text(json.dumps(record, indent=2))
        return 1

    summary = probe.summary()
    modules = summary.get("modules") or {}
    census = {
        "configuration": args.configuration,
        "entry": args.entry,
        "read_census": bool(args.read_census),
        "probe_mode": PROBE_MODE,
        "sweeps_total": modules.get("sweeps_total"),
        "read_sweeps": modules.get("read_sweeps"),
        "output_path_calls_refused": modules.get("output_path_calls_refused"),
        "node_calls": {
            entry["name"]: entry["calls"] for entry in modules.get("nodes", [])
        },
        "writes_by_node": {
            node: fields
            for node, fields in (modules.get("writes_by_node") or {}).items()
        },
        "reads_by_node": _reads_by_node(probe_modules) if args.read_census else None,
        "n_call_models": len(modules.get("calls") or []),
    }
    (outdir / "census.json").write_text(json.dumps(census, indent=2))
    record["census_written_to"] = "census.json"
    record["sweeps_total"] = census["sweeps_total"]
    record["n_nodes_with_writes"] = sum(
        1 for fields in census["writes_by_node"].values() if fields
    )
    record["wall_s"] = time.perf_counter() - started
    (outdir / "metrics.json").write_text(json.dumps(record, indent=2))
    return 0


# ==========================================================================
# the parent: run one census through the pool, then compare it
# ==========================================================================


def take(
    config: Config,
    campaign: Campaign,
    *,
    entry: str = "evaluation",
    read_census: bool = True,
    outdir: Path | None = None,
    resume: bool = False,
) -> dict[str, Any]:
    """One census of one configuration, through the pool.

    Fresh subprocess, own working directory, ``PYTHONPATH`` naming the tree
    under test, the exact tree asserted inside the child — the same isolation
    every PROCESS run in this package gets, for the same reason: the output-file
    manager holds its handles as class attributes and initialisation mutates a
    global, so two runs in one interpreter contaminate each other.
    """
    from . import pool as pool_mod  # noqa: PLC0415 - pool imports this module

    directory = Path(
        outdir or (Path(campaign.runs_dir) / RUNS_SUBPATH / config.name / entry)
    )
    existing = directory / "census.json"
    if resume and existing.exists():
        previous = json.loads(existing.read_text())
        matches = (
            previous.get("configuration") == config.name
            and previous.get("entry") == entry
            and (previous.get("read_census") or not read_census)
        )
        if matches:
            # A census already on disk for exactly this configuration and entry,
            # carrying at least the halves this call asks for.  Resume means
            # *this*: a directory alone is never evidence, and a census taken
            # with the read half off cannot stand in for one that needs it.
            print(
                f"  {config.name:24s} census   entry={entry:<12s} resumed "
                f"(a matching census is already on disk)",
                flush=True,
            )
            previous.setdefault("run", {})["resumed"] = True
            previous["run"]["outdir"] = str(directory)
            return previous
    job = pool_mod.Job(
        phase="census",
        arm=CENSUS_ARM[entry],
        config=config,
        seed=0,
        outdir=directory,
        regime="unperturbed",
        run_kind="gate",
        census_entry=entry,
        census_read=read_census,
        node_census=False,
    )
    result = pool_mod.run(job, campaign, resume=False)
    path = directory / "census.json"
    if not path.exists():
        raise CensusError(
            f"{config.name}: the census run wrote no census "
            f"(status {result.get('status')!r}, taxonomy "
            f"{result.get('failure_class')!r}, directory {directory}).  "
            f"Refused rather than compared against nothing: a comparison over "
            f"an empty census reports zero differences and means nothing."
        )
    census = json.loads(path.read_text())
    census["run"] = {
        "outdir": str(directory),
        "status": result.get("status"),
        "wall_s": result.get("wall_s"),
        "resumed": result.get("resumed", False),
    }
    return census


# --------------------------------------------------------------------------
# comparisons
# --------------------------------------------------------------------------


def compare_write_sets(
    census: Mapping[str, Any], committed: Mapping[str, Any], configuration: str
) -> dict[str, Any]:
    """The measured write sets against the committed per-node census.

    Reported with both denominators, because the two directions mean different
    things.  A field the committed census has and this run did not write is a
    field written somewhere else in the design space (or under a branch this
    entry did not take): the committed set is the larger, and nothing that reads
    it is wrong.  A field this run wrote that the committed census does **not**
    have is the dangerous direction — a node writing state nobody recorded — and
    is reported node by node.
    """
    per_configuration = committed.get("per_scenario", {}).get(configuration)
    if per_configuration is None:
        raise CensusError(
            f"the committed write census has no entry for {configuration}; it "
            f"covers {sorted(committed.get('per_scenario', {}))}"
        )
    committed_writes = {
        node: set(fields)
        for node, fields in per_configuration["writes_by_node"].items()
    }
    measured_writes = {
        node: set(fields)
        for node, fields in census["writes_by_node"].items()
        if fields
    }
    nodes = sorted(set(committed_writes) | set(measured_writes))
    rows = []
    n_fields_committed = n_fields_measured = 0
    n_only_committed = n_only_measured = 0
    for node in nodes:
        committed_fields = committed_writes.get(node, set())
        measured_fields = measured_writes.get(node, set())
        only_committed = sorted(committed_fields - measured_fields)
        only_measured = sorted(measured_fields - committed_fields)
        n_fields_committed += len(committed_fields)
        n_fields_measured += len(measured_fields)
        n_only_committed += len(only_committed)
        n_only_measured += len(only_measured)
        rows.append(
            {
                "node": node,
                "n_committed": len(committed_fields),
                "n_measured": len(measured_fields),
                "n_in_both": len(committed_fields & measured_fields),
                "only_in_committed": only_committed,
                "only_in_this_run": only_measured,
                "identical": not only_committed and not only_measured,
            }
        )
    return {
        "configuration": configuration,
        "n_nodes_compared": len(nodes),
        "n_nodes_identical": sum(1 for row in rows if row["identical"]),
        "n_fields_committed": n_fields_committed,
        "n_fields_measured": n_fields_measured,
        "n_fields_only_in_committed": n_only_committed,
        "n_fields_only_in_this_run": n_only_measured,
        "nodes_in_committed_only": sorted(set(committed_writes) - set(measured_writes)),
        "nodes_in_this_run_only": sorted(set(measured_writes) - set(committed_writes)),
        "per_node": rows,
        "caption": (
            "One row per model node; a field is one data-structure field the "
            "node wrote. 'committed' is the per-node write census this "
            "experiment reads; 'this run' is the census just taken. The two "
            "directions are not symmetric: a field only in the committed set "
            "was written at a design point this entry did not visit, while a "
            "field only in this run is state nobody recorded."
        ),
    }


def compare_block_subsets(
    census: Mapping[str, Any],
    node_map: Mapping[str, Any],
    write_sets: Mapping[str, Any],
    coupling_state: Mapping[str, Any],
    configuration: str,
) -> dict[str, Any]:
    """The measured write sets, mapped to blocks, against the committed subsets.

    The mapping is the committed module node map's, and the intersection is with
    the coupling state's component list: a block's convergence test is taken
    over the components that block writes, so the subset is *writes ∩ state* and
    nothing else.  That is the construction the committed file used, restated
    here rather than imported.
    """
    nodes = node_map["nodes"]
    keys = {component["key"] for component in coupling_state["components"]}
    measured: dict[str, set[str]] = {}
    unmapped: list[str] = []
    for node, fields in census["writes_by_node"].items():
        if node == DESIGN_VECTOR_NODE or not fields:
            continue
        module = (nodes.get(node) or {}).get("module")
        if not module:
            unmapped.append(node)
            continue
        measured.setdefault(module, set()).update(set(fields) & keys)
    committed = {
        module: set(module_keys)
        for module, module_keys in write_sets["subsets"].items()
    }
    blocks = sorted(set(committed) | set(measured))
    rows = []
    n_committed = n_measured = n_only_committed = n_only_measured = 0
    for block in blocks:
        committed_keys = committed.get(block, set())
        measured_keys = measured.get(block, set())
        only_committed = sorted(committed_keys - measured_keys)
        only_measured = sorted(measured_keys - committed_keys)
        n_committed += len(committed_keys)
        n_measured += len(measured_keys)
        n_only_committed += len(only_committed)
        n_only_measured += len(only_measured)
        rows.append(
            {
                "block": block,
                "n_committed": len(committed_keys),
                "n_measured": len(measured_keys),
                "only_in_committed": only_committed,
                "only_in_this_run": only_measured,
                "identical": not only_committed and not only_measured,
            }
        )
    return {
        "configuration": configuration,
        "n_blocks_compared": len(blocks),
        "n_blocks_identical": sum(1 for row in rows if row["identical"]),
        "n_components": len(keys),
        "n_component_slots_committed": n_committed,
        "n_component_slots_measured": n_measured,
        "n_only_in_committed": n_only_committed,
        "n_only_in_this_run": n_only_measured,
        "nodes_with_no_module": sorted(unmapped),
        "per_block": rows,
        "caption": (
            "One row per block of the partition; an entry is one coupling-state "
            "component that block writes. 'committed' is the per-block subset "
            "the block solves test over; 'this run' is the census just taken, "
            "mapped node -> block through the committed module node map and "
            "intersected with the coupling state's own component list."
        ),
    }


def compare_predicate_reads(
    census: Mapping[str, Any],
    tree: Path,
    i_figure_merit: int,
    *,
    written_fields: set[str],
) -> dict[str, Any]:
    """What the predicate layer actually read, against what the source says.

    The routing rule that decides which nodes may leave the loop is derived from
    a source scan of the objective and constraint layers.  This is the direct
    observation of the same thing: the instrument attributes the
    objective/constraint block's reads to their own node, so the census names
    the fields the optimiser's own layer touched during the run.

    The expected relation is **containment, not equality**, and the direction
    matters.  The source scan takes the whole constraint layer rather than the
    configuration's own constraints, so it over-reports on purpose: a field it
    lists and the run never read is a constraint this configuration does not
    activate.  A field the run *read* and the scan does not list is the
    dangerous direction — it would mean the routing rule is derived from an
    incomplete read set.

    Two constructions, and the second is the one that binds
    -------------------------------------------------------
    The runtime window is slightly wider than the two source files: the
    instrument opens it at the driver's own call site, so a field the *driver*
    reads while dispatching into the objective is attributed to this node too.
    The raw comparison therefore reports such reads, and the raw numbers are
    published.  But the routing rule only ever asks about fields **a model node
    writes** — a field no node writes cannot make a node live, whatever reads it
    — so the binding construction restricts both sides to the write census's own
    field set, and every read excluded by that restriction is listed by name
    rather than counted away.
    """
    from .artifacts import compare_with_driver, predicate_read_fields  # noqa: PLC0415

    reads = census.get("reads_by_node") or {}
    if PREDICATE_NODE not in reads:
        return {
            "available": False,
            "why": (
                f"this census carries no read set for {PREDICATE_NODE!r}: it "
                f"was taken with the read half of the instrument off"
            ),
        }
    observed = set(reads[PREDICATE_NODE])
    declared = set(predicate_read_fields(tree, i_figure_merit))
    unlisted = sorted(observed - declared)
    routing = sorted((observed - declared) & written_fields)
    not_written = sorted((observed - declared) - written_fields)
    return {
        "available": True,
        "i_figure_merit": i_figure_merit,
        "n_read_at_runtime": len(observed),
        "n_in_source_scan": len(declared),
        "n_read_and_listed": len(observed & declared),
        "n_listed_but_not_read": len(declared - observed),
        "n_read_but_not_listed": len(unlisted),
        "read_but_not_listed": unlisted[:50],
        "containment_holds_over_every_field": not unlisted,
        "n_written_by_some_node": len(written_fields),
        "n_read_but_not_listed_and_written_by_some_node": len(routing),
        "read_but_not_listed_and_written_by_some_node": routing,
        "read_but_not_listed_and_written_by_no_node": not_written,
        "containment_holds_where_it_binds": not routing,
        "restatement_against_the_driver": compare_with_driver(tree, i_figure_merit),
        "caption": (
            "The objective/constraint block's own read set, observed during one "
            "run, against the read set the source scan derives for the same "
            "figure of merit. Two constructions: over every field the block "
            "read, and over only those fields some model node writes — the "
            "second is what the routing rule uses, and the fields the "
            "restriction removes are listed by name. 'restatement against the "
            "driver' compares this package's copy of the scan rule with the "
            "driver's own, in a child process."
        ),
    }


# ==========================================================================
# the stage
# ==========================================================================


def stage(
    campaign: Campaign,
    *,
    configurations: Sequence[str] | None = None,
    entry: str = "evaluation",
    read_census: bool = True,
    resume: bool = False,
) -> tuple[int, dict[str, Any]]:
    """Take a census of every configuration and compare it with the committed one."""
    from .artifacts import load  # noqa: PLC0415 - one direction

    check = StageCheck(
        name="census",
        binds=(
            "the committed per-node write census, the per-block subsets built "
            "from it, and the read set the routing rule is derived from"
        ),
    )
    names = list(configurations) if configurations else list(campaign.population)
    committed_census = load(
        campaign.data_dir / "node_writesets.json", role="node_write_sets"
    )
    node_map = load(campaign.data_dir / "dsm_node_map.json", role="node_map")
    rows: list[dict[str, Any]] = []
    for name in names:
        config = campaign.configuration(name)
        try:
            census = take(
                config,
                campaign,
                entry=entry,
                read_census=read_census,
                resume=resume,
            )
        except (CensusError, RuntimeError) as exc:
            check.fail(f"{name}: REFUSED — {exc}")
            rows.append({"configuration": name, "verdict": "REFUSED", "error": str(exc)})
            continue
        writes = compare_write_sets(census, committed_census, name)
        blocks = compare_block_subsets(
            census,
            node_map,
            load(config.write_sets_path, role="write_sets"),
            load(config.coupling_state_path, role="coupling_state"),
            name,
        )
        written_fields: set[str] = set()
        for fields in committed_census["per_scenario"][name]["writes_by_node"].values():
            written_fields |= set(fields)
        for fields in census["writes_by_node"].values():
            written_fields |= set(fields)
        reads = compare_predicate_reads(
            census,
            Path(campaign.tree),
            config.figure_of_merit,
            written_fields=written_fields,
        )
        check.n_compared += writes["n_nodes_compared"] + blocks["n_blocks_compared"]
        rows.append(
            {
                "configuration": name,
                "entry": entry,
                "sweeps_total": census.get("sweeps_total"),
                "output_path_calls_refused": census.get("output_path_calls_refused"),
                "write_sets": writes,
                "block_subsets": blocks,
                "predicate_reads": reads,
                "run": census.get("run"),
            }
        )
        check.note(
            f"{name}: {writes['n_nodes_identical']}/{writes['n_nodes_compared']} "
            f"node write sets identical; "
            f"{writes['n_fields_measured']} field(s) written in this run "
            f"against {writes['n_fields_committed']} committed "
            f"({writes['n_fields_only_in_committed']} committed-only, "
            f"{writes['n_fields_only_in_this_run']} this-run-only); "
            f"{blocks['n_blocks_identical']}/{blocks['n_blocks_compared']} "
            f"block subsets identical over "
            f"{blocks['n_components']} coupling components; "
            f"{census.get('sweeps_total')} sweep(s), "
            f"{sum((census.get('output_path_calls_refused') or {}).values())} "
            f"output-path call(s) refused by the sweep boundary"
        )
        if writes["n_fields_only_in_this_run"]:
            check.fail(
                f"{name}: {writes['n_fields_only_in_this_run']} field(s) written "
                f"in this run that the committed census does not record — "
                f"state nobody recorded, reported node by node in the stage "
                f"record and not absorbed"
            )
        if blocks["nodes_with_no_module"]:
            check.fail(
                f"{name}: node(s) {blocks['nodes_with_no_module']} wrote state "
                f"and are not in the committed module node map, so their "
                f"components belong to no block"
            )
        if reads.get("available"):
            check.note(
                f"{name}: the predicate layer read "
                f"{reads['n_read_at_runtime']} field(s) at run time; "
                f"{reads['n_read_and_listed']} of them are in the "
                f"{reads['n_in_source_scan']}-field source scan the routing "
                f"rule uses, and "
                f"{reads['n_read_but_not_listed_and_written_by_some_node']} of "
                f"the {reads['n_read_but_not_listed']} that are not are "
                f"written by some model node "
                f"(not written by any node: "
                f"{reads['read_but_not_listed_and_written_by_no_node']}); the "
                f"restatement of the scan rule agrees with the driver's own on "
                f"{reads['restatement_against_the_driver'].get('n_driver')} "
                f"field(s): "
                f"{reads['restatement_against_the_driver'].get('agrees')}"
            )
            if not reads["containment_holds_where_it_binds"]:
                check.fail(
                    f"{name}: the predicate layer read "
                    f"{reads['n_read_but_not_listed_and_written_by_some_node']} "
                    f"field(s) that a model node writes and the source scan "
                    f"does not list: "
                    f"{reads['read_but_not_listed_and_written_by_some_node']} — "
                    f"the routing rule would be derived from an incomplete "
                    f"read set"
                )
            if reads["restatement_against_the_driver"].get("agrees") is not True:
                check.fail(
                    f"{name}: this package's restatement of the predicate read "
                    f"rule does not agree with the driver's own: "
                    f"{reads['restatement_against_the_driver']}"
                )
    check.population = (
        f"{len(names)} configuration(s) ({', '.join(names)}); one "
        f"{entry} census each, taken with the read half of the instrument "
        f"{'on' if read_census else 'off'}"
    )
    return (0 if check.passed else 3), {
        **check.as_record(),
        "entry": entry,
        "entry_meaning": ENTRIES[entry],
        "read_census": read_census,
        "committed_census": {
            "path": str(campaign.data_dir / "node_writesets.json"),
            "union_sha256": committed_census.get("union_sha256"),
            "derived_from": committed_census.get("derived_from"),
            "tree_git_head": committed_census.get("tree_git_head"),
        },
        "configurations": rows,
    }


def stage_teeth(
    campaign: Campaign,
    *,
    record: Mapping[str, Any] | None = None,
) -> tuple[int, dict[str, Any]]:
    """Two ways the census comparison must fail.  No PROCESS run.

    Both breaks are made on a throwaway copy of a census taken by the stage
    above; nothing on disk is written to.
    """
    from .artifacts import load  # noqa: PLC0415 - one direction

    check = StageCheck(
        name="census — teeth",
        binds="the census comparison's own ability to fail",
        population="2 deliberate breaks, on a throwaway copy of one census",
    )
    census = _one_census_for_teeth(campaign, record)
    if census is None:
        check.fail(
            "no census is available to break: run the census stage first.  A "
            "tooth that runs over nothing proves nothing, so this refuses "
            "rather than reporting a vacuous pass."
        )
        return 3, check.as_record()
    configuration = census["configuration"]
    committed = load(
        campaign.data_dir / "node_writesets.json", role="node_write_sets"
    )

    # 1. a node's write removed from the measured census: the committed set
    #    then has a field this run did not write, which is the benign
    #    direction — so the tooth is on the *count*, which must move.
    baseline = compare_write_sets(census, committed, configuration)
    broken = json.loads(json.dumps(census))
    node = next(
        name
        for name, fields in sorted(broken["writes_by_node"].items())
        if fields and name != DESIGN_VECTOR_NODE
    )
    removed = broken["writes_by_node"][node].pop(0)
    after = compare_write_sets(broken, committed, configuration)
    check.tooth(
        "one node's write removed from the census",
        after["n_fields_only_in_committed"]
        == baseline["n_fields_only_in_committed"] + 1
        and after["n_nodes_identical"] < baseline["n_nodes_identical"],
        f"{removed!r} removed from {node!r} in a throwaway copy; the "
        f"comparison must report one more committed-only field and one fewer "
        f"identical node",
    )

    # 2. a node writing state nobody recorded: the dangerous direction, which
    #    must fail the stage rather than be counted.
    broken = json.loads(json.dumps(census))
    broken["writes_by_node"].setdefault(node, []).append("physics.a_field_nobody_recorded")
    after = compare_write_sets(broken, committed, configuration)
    check.tooth(
        "a node writing a field the committed census does not have",
        after["n_fields_only_in_this_run"] == 1,
        "an invented field added to a throwaway copy; the comparison must "
        "report it as this-run-only, which is what fails the stage",
    )
    return (0 if check.passed else 3), check.as_record()


def _one_census_for_teeth(
    campaign: Campaign, record: Mapping[str, Any] | None
) -> dict[str, Any] | None:
    """A census already on disk, for the teeth to break a copy of."""
    if record:
        for row in record.get("configurations", []):
            path = Path((row.get("run") or {}).get("outdir", "")) / "census.json"
            if path.exists():
                return json.loads(path.read_text())
    root = Path(campaign.runs_dir) / RUNS_SUBPATH
    for path in sorted(root.glob("*/*/census.json")):
        return json.loads(path.read_text())
    return None


# ==========================================================================
# entry point (child only; the stage is reached from experiment_runner.py)
# ==========================================================================


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--child", action="store_true", required=True)
    parser.add_argument("--tree", required=True)
    parser.add_argument("--configuration", required=True)
    parser.add_argument("--arm", required=True)
    parser.add_argument("--input", required=True)
    parser.add_argument("--outdir", required=True)
    parser.add_argument("--entry", default="evaluation", choices=tuple(ENTRIES))
    parser.add_argument("--read-census", action="store_true")
    parser.add_argument("--run-kind", default="gate", choices=("gate", "smoke"))
    return parser


def main(argv: list[str] | None = None) -> int:
    return run_child(build_parser().parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
