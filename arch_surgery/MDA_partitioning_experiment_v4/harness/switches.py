"""The driver's switch vocabulary as data, and the capability probe.

Derived from ``arch_surgery/idf_probe/run_a28.py::_ARCH_VARS`` and
``arch_surgery/MDA_partitioning_experiment_v3/v3_runner.py::_ALL_ARCH_VARS``
at ``f2dc9243`` (task A47), and from the driver's own module-level switch
definitions in ``process/core/caller.py``,
``process/core/solver/module_solve.py`` and ``process/core/solver/subsolve.py``
read at the same commit.

Three things live here and nowhere else.

**The vocabulary.**  One :class:`Switch` per thing the driver can be told to
do: the term V4 uses for it, the environment variable the tree *currently*
implements, the name it is intended to carry once the rename lands, its legal
values, whether an arm composes it or the harness only clears it, and how to
read back what the driver actually resolved.  When the rename happens this
file is the only one that changes.

**The clearing discipline.**  Every known variable is removed before an arm is
composed (V3's ``_ALL_ARCH_VARS``), so an inherited value can never change
what is measured without saying so.

**The capability probe.**  A child process imports the driver under a given
environment and reports what it resolved.  It replaces V3's hand-edited
``INSTRUMENTATION`` ledger of booleans, which said what a human believed the
tree could do and was consulted on one code path and not the other.  A switch
the tree does not implement is *ignored* by the driver: the run succeeds, and
measures a different arm under the right name.  That is the failure this
module exists to make impossible — the same shape as trap T6 (a worktree does
not redirect the editable install) and trap T10 (a version string agreeing
with the wrong answer).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Mapping, MutableMapping

CALLER = "process.core.caller"
MODULE_SOLVE = "process.core.solver.module_solve"
SUBSOLVE = "process.core.solver.subsolve"


# --------------------------------------------------------------------------
# the record
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Switch:
    """One thing the driver can be told to do."""

    #: V4's term for it (README §3), used as the key everywhere in the harness.
    term: str
    #: Environment variable the tree implements *today*, or None when the
    #: capability does not exist yet and an approved driver change will add it.
    driver_name: str | None
    #: The name it is intended to carry.  None when the switch is intended to
    #: disappear rather than be renamed.
    intended_name: str | None
    #: "enum" | "path" | "number" | "hexfloat" | "csv"
    value_kind: str
    #: Legal values for an enum switch; empty otherwise.  The driver's own
    #: default (the variable unset) is not listed.
    values: tuple[str, ...]
    #: True when an arm composes it; False when the harness only clears it.
    composed: bool
    #: ``(module, attribute)`` pairs a child process reads back to say what the
    #: driver resolved.
    readbacks: tuple[tuple[str, str], ...]
    #: ``(resolved, requested) -> bool``: did the driver resolve as asked?
    resolved_as_asked: Callable[[Mapping[str, object], str], bool] = field(
        compare=False, repr=False, default=lambda resolved, value: True
    )
    #: Names that must never appear in a composed environment, with the reason.
    #: A stale caller setting a retired name would run the wrong arm under the
    #: right name; this is the guard against that.
    retired_names: tuple[str, ...] = ()
    retired_because: str = ""
    #: The driver change that will supply or rename it, for the refusal message.
    pending_change: str = ""
    note: str = ""

    @property
    def implemented(self) -> bool:
        """Whether any tree can be asked for this at all today."""
        return self.driver_name is not None


def _resolved(resolved: Mapping[str, object], module: str, attribute: str):
    return resolved.get(f"{module}.{attribute}", _MISSING)


class _Missing:
    def __repr__(self) -> str:  # pragma: no cover - display only
        return "<not implemented by this tree>"


_MISSING = _Missing()


# --------------------------------------------------------------------------
# the registry
# --------------------------------------------------------------------------
#
# Row order is the order of EXPERIMENT_PLAN.md §3.2's switch list, then the
# switches an arm never composes.  Every legal value below was read from the
# driver's own guard tables, not from a document: an unrecognised value is an
# import-time error in the driver, so a wrong spelling here is refused rather
# than run.

REGISTRY: dict[str, Switch] = {
    "mda": Switch(
        term="mda",
        driver_name="PROCESS_ARCH_MODULE_SOLVE",
        intended_name="PROCESS_ARCH_MDA",
        value_kind="enum",
        values=("flat_state", "per_module"),
        composed=True,
        readbacks=(
            (MODULE_SOLVE, "MODULE_SOLVE_NAME"),
            (MODULE_SOLVE, "ENABLED"),
            (MODULE_SOLVE, "FLAT_STATE"),
        ),
        resolved_as_asked=lambda r, v: _resolved(r, MODULE_SOLVE, "MODULE_SOLVE_NAME") == v,
        note=(
            "Shape of the analysis loop: one block over every in-loop node "
            "(flat) or three block solves in feed-forward order "
            "(partitioned).  The driver spells these 'flat_state' and "
            "'per_module'; V4 says flat and partitioned.  Unset is upstream's "
            "own loop, which is what the reference arms run."
        ),
    ),
    "tolerance": Switch(
        term="tolerance",
        driver_name="PROCESS_ARCH_TAU",
        intended_name="PROCESS_ARCH_TAU",
        value_kind="number",
        values=(),
        composed=True,
        readbacks=((MODULE_SOLVE, "TAU"),),
        resolved_as_asked=lambda r, v: _resolved(r, MODULE_SOLVE, "TAU") == float(v),
        note=(
            "The one tolerance of every converger (D23, the user's ruling of "
            "2026-09-10): the flat loop and each block loop alike, both "
            "phases, every arm."
        ),
    ),
    "coupling_state": Switch(
        term="coupling_state",
        driver_name="PROCESS_ARCH_YSTATE",
        intended_name="PROCESS_ARCH_COUPLING_STATE",
        value_kind="path",
        values=(),
        composed=True,
        readbacks=((MODULE_SOLVE, "YSTATE_PATH"),),
        resolved_as_asked=lambda r, v: _resolved(r, MODULE_SOLVE, "YSTATE_PATH") == v,
        note=(
            "The committed artifact naming the fields that make up the "
            "coupling state and the measured scale of each.  No default: "
            "another configuration's components would silently test the wrong "
            "thing."
        ),
    ),
    "write_sets": Switch(
        term="write_sets",
        driver_name="PROCESS_ARCH_WRITESET",
        intended_name="PROCESS_ARCH_WRITE_SETS",
        value_kind="path",
        values=(),
        composed=True,
        readbacks=((MODULE_SOLVE, "WRITESET_PATH"),),
        resolved_as_asked=lambda r, v: _resolved(r, MODULE_SOLVE, "WRITESET_PATH") == v,
        note=(
            "The committed artifact naming which coupling-state components "
            "each block writes, so a block loop tests its own subset."
        ),
    ),
    "arrangement_node": Switch(
        term="arrangement_node",
        driver_name="PROCESS_ARCH_SEQUENCE",
        intended_name="PROCESS_ARCH_ARRANGEMENT_NODE",
        value_kind="enum",
        values=("build_after_physics",),
        composed=True,
        readbacks=((CALLER, "SEQUENCE_NAME"), (CALLER, "SEQUENCE_HEAD")),
        resolved_as_asked=lambda r, v: _resolved(r, CALLER, "SEQUENCE_NAME") == v,
        note=(
            "When a node runs: 'build' moved after 'physics' so the physics "
            "block is contiguous in the call order.  A permutation of three "
            "existing calls; no model changes."
        ),
    ),
    "arrangement_method": Switch(
        term="arrangement_method",
        driver_name="PROCESS_ARCH_PRIME",
        intended_name="PROCESS_ARCH_ARRANGEMENT_METHOD",
        value_kind="enum",
        values=("fw_geometry",),
        composed=True,
        readbacks=((CALLER, "PRIME_NAME"), (CALLER, "PRIME_FW_GEOMETRY")),
        resolved_as_asked=lambda r, v: _resolved(r, CALLER, "PRIME_NAME") == v,
        note=(
            "When a method runs: the run-constant first-wall geometry method "
            "executed at the head of every sweep, so 'build' reads this "
            "pass's thickness instead of the previous pass's."
        ),
    ),
    "defer_per_call": Switch(
        term="defer_per_call",
        driver_name="PROCESS_ARCH_HOIST",
        intended_name="PROCESS_ARCH_DEFER_PER_CALL",
        value_kind="enum",
        values=("feedforward", "feedforward_lifted"),
        composed=True,
        readbacks=(
            (CALLER, "HOIST_NAME"),
            (CALLER, "HOIST_ENABLED"),
            (CALLER, "HOIST_NODES"),
        ),
        resolved_as_asked=lambda r, v: _resolved(r, CALLER, "HOIST_NAME") == v,
        note=(
            "How often a node runs: once per evaluation of the model set "
            "instead of once per sweep.  'feedforward_lifted' additionally "
            "defers the burn-time node, which is only correct once the burn "
            "time has left the loop — the driver refuses the combination "
            "otherwise."
        ),
    ),
    "defer_per_run": Switch(
        term="defer_per_run",
        driver_name="PROCESS_ARCH_POST_SOLVE",
        intended_name="PROCESS_ARCH_DEFER_PER_RUN",
        value_kind="path",
        values=(),
        composed=True,
        readbacks=((CALLER, "POST_SOLVE_PATH"), (CALLER, "POST_SOLVE_ENABLED")),
        resolved_as_asked=lambda r, v: _resolved(r, CALLER, "POST_SOLVE_PATH") == v,
        note=(
            "How often a node runs: once in total, at the accepted optimum.  "
            "The value is the committed artifact naming that node set; there "
            "is no default, because a run asked to defer nodes must refuse "
            "rather than quietly run all of them."
        ),
    ),
    "burn_time_lift": Switch(
        term="burn_time_lift",
        driver_name="PROCESS_ARCH_LIFT",
        intended_name="PROCESS_ARCH_BURN_TIME_OWNER",
        value_kind="csv",
        values=("burn_time",),
        composed=True,
        readbacks=(
            (SUBSOLVE, "LIFTED_SITES"),
            (SUBSOLVE, "LIFT_ENABLED"),
            (SUBSOLVE, "SITES"),
        ),
        resolved_as_asked=lambda r, v: sorted(
            _resolved(r, SUBSOLVE, "LIFTED_SITES") or []
        )
        == sorted(part for part in v.split(",") if part),
        note=(
            "Takes the burn time out of the loop: the model stops solving for "
            "it and reads it from wherever its new owner put it.  Today a "
            "list of lifted sites with exactly one member; the intended "
            "single switch states the owner instead."
        ),
    ),
    "burn_time_pin": Switch(
        term="burn_time_pin",
        driver_name="PROCESS_ARCH_PIN_BURN_TIME",
        intended_name="PROCESS_ARCH_BURN_TIME_OWNER",
        value_kind="hexfloat",
        values=(),
        composed=True,
        readbacks=((SUBSOLVE, "PIN_BURN_TIME"), (SUBSOLVE, "PIN_ENABLED")),
        resolved_as_asked=lambda r, v: _resolved(r, SUBSOLVE, "PIN_BURN_TIME")
        == float.fromhex(v),
        note=(
            "Names a constant as the burn time's owner, for the phase that "
            "has no optimiser to own it.  Passed as a C99 hex float so a "
            "measured value survives the round trip exactly.  The driver "
            "refuses a pin without the lift (the model would overwrite it on "
            "the first sweep) and refuses a deck that also names the burn "
            "time as an optimiser variable (two owners is a refusal, not a "
            "race)."
        ),
    ),
    "schedule_passes": Switch(
        term="schedule_passes",
        driver_name="PROCESS_ARCH_OUTER",
        intended_name=None,
        value_kind="enum",
        values=("trust",),
        composed=True,
        readbacks=((MODULE_SOLVE, "OUTER_MODE"), (MODULE_SOLVE, "TRUST_OUTER")),
        resolved_as_asked=lambda r, v: _resolved(r, MODULE_SOLVE, "OUTER_MODE") == v,
        pending_change="folded into the partitioned setting of the analysis-loop switch",
        note=(
            "The partitioned arms run their block schedule once (D23).  The "
            "driver still expresses that as a separate 'trust' mode because "
            "its default is to repeat the whole schedule while anything is "
            "still moving; V4 has no arm that repeats it, so the value is a "
            "consequence of choosing the partitioned loop, not a choice of "
            "its own.  It is composed by this registry, never declared per "
            "arm, and it disappears when the driver stops offering the "
            "repeat."
        ),
    ),
    "output_loop": Switch(
        term="output_loop",
        driver_name=None,
        intended_name="PROCESS_ARCH_OUTPUT_LOOP",
        value_kind="enum",
        values=("none",),
        composed=True,
        readbacks=((CALLER, "OUTPUT_LOOP_NAME"),),
        resolved_as_asked=lambda r, v: _resolved(r, CALLER, "OUTPUT_LOOP_NAME") == v,
        pending_change="approved driver change DR2 (the output path without the output-time loop)",
        note=(
            "Upstream writes its output files through a second loop that "
            "re-solves the accepted state until the output stops changing.  "
            "The arms whose solve already handed over a verified state do not "
            "run it.  No tree implements this switch yet, so every arm that "
            "asks for it is refused rather than run with the loop still on."
        ),
    ),
    "predicate_mode": Switch(
        term="predicate_mode",
        driver_name=None,
        intended_name="PROCESS_ARCH_PREDICATE",
        value_kind="enum",
        values=("mixed",),
        composed=True,
        readbacks=((MODULE_SOLVE, "PREDICATE_MODE"),),
        resolved_as_asked=lambda r, v: _resolved(r, MODULE_SOLVE, "PREDICATE_MODE") == v,
        pending_change="approved driver change DR5 (predicate mode frozen | mixed)",
        note=(
            "Which denominator the convergence test scales by: the frozen "
            "measured ruler, or one that may move with the state.  'frozen' "
            "is the driver's behaviour today and composes nothing; 'mixed' "
            "is the trial and needs the switch."
        ),
    ),
    "inner_tolerance": Switch(
        term="inner_tolerance",
        driver_name="PROCESS_ARCH_INNER_TAU",
        intended_name=None,
        value_kind="number",
        values=(),
        composed=False,
        readbacks=((MODULE_SOLVE, "INNER_TAU"),),
        retired_names=("PROCESS_ARCH_INNER_TAU",),
        retired_because=(
            "D23 (user, 2026-09-10): one tolerance for every converger, so a "
            "second one cannot be set.  A run carrying it would report a "
            "block accuracy the campaign never declared"
        ),
        note=(
            "The driver still offers a separate tolerance for a block loop.  "
            "V4 never sets it: an environment carrying it is refused, not "
            "cleared and forgotten."
        ),
    ),
    "pass_trace": Switch(
        term="pass_trace",
        driver_name="PROCESS_ARCH_PASS_TRACE",
        intended_name="PROCESS_ARCH_PASS_TRACE",
        value_kind="path",
        values=(),
        composed=False,
        readbacks=((MODULE_SOLVE, "PASS_TRACE_PATH"), (MODULE_SOLVE, "TRACE_ENABLED")),
        note=(
            "A per-pass residual trace.  A debugging instrument the "
            "experiment publishes nothing from: cleared before every arm so "
            "an inherited value cannot add work, never composed."
        ),
    ),
    "pass_trace_full_from": Switch(
        term="pass_trace_full_from",
        driver_name="PROCESS_ARCH_PASS_TRACE_FULL_FROM",
        intended_name="PROCESS_ARCH_PASS_TRACE_FULL_FROM",
        value_kind="number",
        values=(),
        composed=False,
        readbacks=((MODULE_SOLVE, "TRACE_FULL_FROM"),),
        note="Companion of the trace above; same treatment.",
    ),
}


#: Instrumentation variables that are not architecture switches: they select
#: and tune the in-driver probe.  Cleared before every arm for the same reason
#: the switches are — an inherited one changes what a run does — and never
#: composed by an arm.  Read from ``process/core/_idf_probe*.py``.
PROBE_VARIABLES: tuple[str, ...] = (
    "PROCESS_IDF_PROBE",
    "PROCESS_IDF_PROBE_OUT",
    "PROCESS_IDF_PROBE_READ_BUDGET",
    "PROCESS_IDF_PROBE_READ_STRIDE",
    "PROCESS_IDF_PROBE_FROZEN_GRAD_STRIDE",
    "PROCESS_IDF_PROBE_FROZEN_OTHER_STRIDE",
    "PROCESS_IDF_PROBE_FROZEN_MAX_SUBSWEEPS",
    "PROCESS_IDF_PROBE_FROZEN_NOINJECT",
    "PROCESS_IDF_PROBE_FROZEN_TRACE",
    "PROCESS_IDF_PROBE_HARVEST_OUT",
    "PROCESS_IDF_PROBE_HARVEST_GRAD_STRIDE",
    "PROCESS_IDF_PROBE_HARVEST_MAX_POINTS",
    "PROCESS_IDF_PROBE_HARVEST_ALL_POINTS",
)


#: Arms the earlier revision ran under different names.  A lookup that misses
#: raises: a reference a gate cannot find must refuse, never pass over an
#: empty comparison (trap T11).
PREVIOUS_ARM_NAMES: dict[str, str] = {"R": "BR"}

#: Arms the earlier revision ran that V4 does not: ``A1u`` was the prime-free
#: counterfactual, retired with the prime's own gate; ``B2`` repeated the
#: block schedule and measured nothing the exit audit does not (D22).
RETIRED_ARM_NAMES: tuple[str, ...] = ("A1u", "B2")


def all_names() -> tuple[str, ...]:
    """Every environment variable the harness knows about, current and future.

    Cleared before composing an arm: current names because they change what
    the driver does, intended names because a tree that already implements one
    would pick up an inherited value, retired names because a stale one would
    run the wrong arm under the right name.
    """
    names: list[str] = []
    for sw in REGISTRY.values():
        names.extend(
            n
            for n in (sw.driver_name, sw.intended_name, *sw.retired_names)
            if n is not None
        )
    names.extend(PROBE_VARIABLES)
    return tuple(dict.fromkeys(names))


def retired_names() -> dict[str, str]:
    """Names that must never appear in a composed environment, and why."""
    return {
        name: sw.retired_because
        for sw in REGISTRY.values()
        for name in sw.retired_names
    }


def clear_all(env: MutableMapping[str, str]) -> MutableMapping[str, str]:
    """Remove every known variable from *env*, in place, and return it."""
    for name in all_names():
        env.pop(name, None)
    return env


def assert_no_retired(env: Mapping[str, str]) -> None:
    """Raise if *env* carries a name V4 has retired."""
    retired = retired_names()
    present = sorted(name for name in retired if name in env)
    if present:
        raise SwitchError(
            "the composed environment carries retired "
            + ", ".join(f"{n} ({retired[n]})" for n in present)
        )


class SwitchError(RuntimeError):
    """A composition or capability refusal.  Never degraded into a warning."""


# --------------------------------------------------------------------------
# the capability probe
# --------------------------------------------------------------------------

#: The child program.  It imports the driver under the environment it inherits
#: and prints what the driver resolved.  Module-level names only: nothing is
#: run, no model is called, no output file is opened.  ``process.__file__`` is
#: reported so the caller can assert the exact tree (trap T6) — and the
#: version string is never consulted (trap T10: a frozen archive's version
#: agrees with the wrong commit).
_PROBE_SOURCE = r"""
import importlib, json, sys

SENTINEL = "@@HARNESS-PROBE@@"
spec = json.loads(sys.stdin.read())


def coerce(v):
    if isinstance(v, (str, int, float, bool)) or v is None:
        return v
    if isinstance(v, (set, frozenset)):
        return sorted(str(x) for x in v)
    if isinstance(v, (list, tuple)):
        return [coerce(x) for x in v]
    if isinstance(v, dict):
        return {str(k): coerce(x) for k, x in v.items()}
    return repr(v)


out = {"resolved": {}, "missing": [], "ok": True, "error": None}
try:
    import process

    out["process_file"] = process.__file__
    for module, attrs in spec.items():
        m = importlib.import_module(module)
        for attr in attrs:
            key = module + "." + attr
            if hasattr(m, attr):
                out["resolved"][key] = coerce(getattr(m, attr))
            else:
                out["missing"].append(key)
except BaseException as exc:
    out["ok"] = False
    out["error"] = type(exc).__name__ + ": " + str(exc)

sys.stdout.write(SENTINEL + json.dumps(out) + SENTINEL)
"""

_SENTINEL = "@@HARNESS-PROBE@@"


@dataclass(frozen=True)
class Capability:
    """What one child process reported about one environment."""

    ok: bool
    resolved: Mapping[str, object]
    missing: tuple[str, ...]
    process_file: str | None
    error: str | None

    def value(self, module: str, attribute: str):
        return _resolved(self.resolved, module, attribute)


def probe(
    tree: Path,
    env: Mapping[str, str],
    *,
    readbacks: tuple[tuple[str, str], ...] | None = None,
    timeout: int = 300,
) -> Capability:
    """Import the driver from *tree* under *env* and report what it resolved.

    A fresh child process, because every switch is read once at import: the
    only way to ask "what would this environment do" is to be that process.
    """
    spec: dict[str, list[str]] = {}
    pairs = readbacks if readbacks is not None else default_readbacks()
    for module, attr in pairs:
        spec.setdefault(module, []).append(attr)
    child_env = dict(env)
    child_env["PYTHONPATH"] = str(tree)
    proc = subprocess.run(
        [sys.executable, "-c", _PROBE_SOURCE],
        input=json.dumps(spec),
        env=child_env,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    body = proc.stdout.split(_SENTINEL)
    if len(body) < 3:
        return Capability(
            ok=False,
            resolved={},
            missing=(),
            process_file=None,
            error=(
                f"probe child produced no report (rc={proc.returncode}): "
                f"{(proc.stderr or proc.stdout or '').strip()[-600:]}"
            ),
        )
    raw = json.loads(body[1])
    return Capability(
        ok=bool(raw["ok"]),
        resolved=raw["resolved"],
        missing=tuple(raw["missing"]),
        process_file=raw.get("process_file"),
        error=raw.get("error"),
    )


def default_readbacks() -> tuple[tuple[str, str], ...]:
    """Every readback the registry names, deduplicated."""
    pairs: list[tuple[str, str]] = []
    for sw in REGISTRY.values():
        pairs.extend(sw.readbacks)
    return tuple(dict.fromkeys(pairs))


def unimplemented(terms: Mapping[str, str]) -> tuple[str, ...]:
    """Which of the composed *terms* no tree implements yet."""
    return tuple(
        term for term in terms if term in REGISTRY and not REGISTRY[term].implemented
    )


def assert_capable(
    tree: Path,
    terms: Mapping[str, str],
    env: Mapping[str, str],
    *,
    label: str = "",
    timeout: int = 300,
) -> Capability:
    """Refuse unless *tree* resolved every composed switch exactly as asked.

    *terms* maps the V4 term to the value the arm asked for.  Refusal, never
    degradation: a tree that does not implement a switch ignores it silently,
    runs to completion, and reports a different arm under the right name.
    """
    where = f" for {label}" if label else ""
    pending = unimplemented(terms)
    if pending:
        raise SwitchError(
            f"refusing{where}: this tree implements no switch for "
            + "; ".join(
                f"{t} (needs {REGISTRY[t].pending_change or 'a driver change'})"
                for t in pending
            )
        )
    assert_no_retired(env)
    cap = probe(tree, env, timeout=timeout)
    if not cap.ok:
        raise SwitchError(
            f"refusing{where}: the driver refused this environment at import "
            f"— {cap.error}"
        )
    for term, value in terms.items():
        sw = REGISTRY[term]
        for module, attr in sw.readbacks:
            if f"{module}.{attr}" not in cap.resolved:
                raise SwitchError(
                    f"refusing{where}: the tree at {tree} has no "
                    f"{module}.{attr}, so it cannot implement {term} "
                    f"({sw.driver_name}={value!r}).  A tree that ignores a "
                    f"switch runs a different arm under this arm's name."
                )
        if not sw.resolved_as_asked(cap.resolved, value):
            raise SwitchError(
                f"refusing{where}: asked for {sw.driver_name}={value!r} "
                f"({term}) but the driver resolved "
                + ", ".join(
                    f"{a}={cap.value(m, a)!r}" for m, a in sw.readbacks
                )
            )
    return cap


def base_environment(tree: Path, *, runs_dir: Path | None = None) -> dict[str, str]:
    """A copy of this process's environment with every known switch cleared.

    Nothing is assumed absent: V3's discipline, kept.  ``PYTHONPATH`` names
    the tree under test because the editable install points at the main
    checkout and a worktree does not redirect it (trap T6).
    """
    env = dict(os.environ)
    env["PYTHONPATH"] = str(tree)
    if runs_dir is not None:
        env["MPLCONFIGDIR"] = str(Path(runs_dir) / "_mplconfig")
    clear_all(env)
    return env
