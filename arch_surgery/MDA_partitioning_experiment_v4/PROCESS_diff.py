"""Every change this experiment has made to PROCESS, in one view.

V4 runs its own copy of the PROCESS package under ``PROCESS/`` (decision D20).
This script answers, in a minute of reading, the only question a reviewer has
before a driver change is merged: **what does the copy do differently from the
PROCESS it was copied from, and why?**

It reads ``PROCESS/PROVENANCE.json`` for the source commit, extracts that
commit's ``process/`` into a temporary directory, diffs the copy against it
with ``git diff --no-index`` -- against the commit, never against the
repository-root working tree -- and prints, per changed file, the lines added
and removed and, per hunk, the switch or mechanism it serves.  A hunk that the
annotation map does not claim is printed as **UNEXPLAINED** and the exit status
is non-zero: an unclaimed hunk is a change nobody wrote down.

It closes with the frozen-physics statement -- gate G0' re-run live against the
base commit ``c0ae5b28``, naming the one model edit the experiment has ever
approved.

Later driver-change tasks extend ``ANNOTATIONS`` by one line each and add a
paragraph to ``SUMMARIES``.

New in A46 (process-copy); it derives from no earlier file.  A48
(harness-data) added the annotations and summaries for the copy's second round
of edits.  A56 (driver-renames) added the switch renames, restricted a hunk's
annotation match to the hunk's **changed** lines (a context line carrying a
marker used to be able to claim a hunk for a mechanism it does not serve), and
grouped the annotations by mechanism so a claim names a switch rather than a
file.  Stdlib only, no PROCESS run, runs in seconds.

Usage
-----
    python PROCESS_diff.py             # the overview
    python PROCESS_diff.py --full      # the raw unified diff as well
    python PROCESS_diff.py --markdown  # a table a report can include

Exit status: 0 every hunk is claimed and G0' passes, 1 otherwise, 2 setup error.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).resolve().parent
COPY_ROOT = HERE / "PROCESS"
PROVENANCE = COPY_ROOT / "PROVENANCE.json"
GATES = COPY_ROOT / "copy_gates.py"


@dataclass(frozen=True)
class Annotation:
    """One reason a hunk may exist: a marker in the hunk, and what it serves."""

    path: str
    marker: str
    serves: str


#: The annotation map.  A hunk in ``path`` whose text contains ``marker`` is
#: claimed by ``serves``.  One line per mechanism; adding a driver change means
#: adding a line here (and a paragraph to SUMMARIES below).
#: What each mechanism is called in this view.  One entry per *thing the copy
#: does differently*, so that a hunk's claim names a switch or a mechanism and
#: not merely a file.
_PATHS = "harness paths"
_ARR_NODE = "switch PROCESS_ARCH_ARRANGEMENT_NODE (was …_SEQUENCE): arrangement at node granularity"
_ARR_METHOD = "switch PROCESS_ARCH_ARRANGEMENT_METHOD (was …_PRIME): arrangement at method granularity"
_DEFER_CALL = "switch PROCESS_ARCH_DEFER_PER_CALL (was …_HOIST): deferral at per-call frequency"
_DEFER_RUN = "switch PROCESS_ARCH_DEFER_PER_RUN (was …_POST_SOLVE): deferral at per-run frequency"
_MDA = "switch PROCESS_ARCH_MDA (was …_MODULE_SOLVE): the shape of the analysis loop"
_ARTIFACTS = "switches PROCESS_ARCH_COUPLING_STATE / …_WRITE_SETS (were …_YSTATE / …_WRITESET)"
_OWNER = "switch PROCESS_ARCH_BURN_TIME_OWNER (was …_LIFT plus …_PIN_BURN_TIME): who owns the burn time"
_OUTER = "retired switch PROCESS_ARCH_OUTER: the block schedule runs once, so the repeated schedule is removed (D22)"
_INNER = "retired switch PROCESS_ARCH_INNER_TAU: one tolerance for every converger (D23)"
_REFUSAL = "the typed refusal ArchitectureRefusal, raised by every refusal of an architecture setting"
_RETIRED = "the retired-name guard: a stale switch name raises instead of being ignored"
_WORDS = "vocabulary only: the words of the terminology table in comments and messages (no behaviour)"
_OUTPUT_LOOP = "switch PROCESS_ARCH_OUTPUT_LOOP: whether the accepted state is re-solved before it is written out"
_SNAPSHOT = "the exit-audit snapshot hook: the coupling state captured at the declared audit position, so the residual can be computed after the run"
_PREDICATE_COUNT = "DR4 counters: how often a convergence test was evaluated in the solve phase, and how many components each one walked"
_BLOCK_VISITS = "DR4 counters: the block schedule's visits to each block, and the visits that executed no node (issue I-20a: counted and disclaimed, never repaired)"
_SWEEP_COUNT = "DISPATCH_SWEEPS: the run's count of sweeps of the dispatch body, under a public name (was _SWEEP_CALLS)"
_READS_BY_NODE = "the census instrument reports each node's read set by name, beside the write set it already reported"

ANNOTATIONS: list[Annotation] = [
    # --- the copy's harness paths (A46, A48) -----------------------------
    Annotation("process/core/solver/module_solve.py", "YSTATE_MODULE_PATH", "harness path constant YSTATE_MODULE_PATH -> harness/ystate.py (D20, decision 2 option v)"),
    Annotation("process/core/caller.py", "NODE_WRITESET_PATH", "harness path constant NODE_WRITESET_PATH -> harness/data/ (D20, decision 3)"),
    Annotation("process/core/caller.py", "NODE_MAP_PATH", "harness path constant NODE_MAP_PATH -> harness/data/ (D20, decision 3)"),
    Annotation("process/core/caller.py", "its source, its sha256", "comment: the artifacts the two path constants name are committed here, and their provenance file says so"),
    Annotation("process/core/caller.py", "copied into ", "comment: the per-call refusal names the committed artifact and its provenance file instead of a generator script in the research tree"),
    Annotation("process/core/caller.py", "harness/data/defer_per_run", "comment: the per-run deferral artifact named by the file the copy reads"),
    Annotation("process/core/caller.py", '/ "harness"', _PATHS),
    Annotation("process/core/solver/module_solve.py", "its source, its sha256", "comment: the predicate module the path constant names is committed here, and its provenance file says so"),
    Annotation("process/core/solver/module_solve.py", "harness/data/coupling_state_", "comment: the coupling-state artifact named by the file the copy reads"),
    Annotation("process/core/solver/module_solve.py", "harness/data/write_sets_", "comment: the write-set artifact named by the file the copy reads"),
    # --- A56: the switch renames -----------------------------------------
    Annotation("process/core/caller.py", "ARRANGEMENT_NODE", _ARR_NODE),
    Annotation("process/core/caller.py", "SEQUENCE", _ARR_NODE),
    Annotation("process/core/caller.py", "ARRANGEMENT_METHOD", _ARR_METHOD),
    Annotation("process/core/caller.py", "PRIME", _ARR_METHOD),
    Annotation("process/core/caller.py", "prime", _ARR_METHOD),
    Annotation("process/core/caller.py", "DEFER_PER_CALL", _DEFER_CALL),
    Annotation("process/core/caller.py", "HOIST", _DEFER_CALL),
    Annotation("process/core/caller.py", "hoist", _DEFER_CALL),
    Annotation("process/core/caller.py", "defer", _DEFER_CALL),
    Annotation("process/core/caller.py", "DEFER_PER_RUN", _DEFER_RUN),
    Annotation("process/core/caller.py", "POST_SOLVE", _DEFER_RUN),
    Annotation("process/core/caller.py", "post-solve", _DEFER_RUN),
    Annotation("process/core/caller.py", "per-run", _DEFER_RUN),
    Annotation("process/core/caller.py", "MDA", _MDA),
    Annotation("process/core/caller.py", "MODULE_SOLVE", _MDA),
    Annotation("process/core/caller.py", "module_solve.FLAT", _MDA),
    Annotation("process/core/caller.py", "block schedule", _MDA),
    Annotation("process/core/caller.py", "BURN_TIME_OWNER", _OWNER),
    Annotation("process/core/caller.py", "BURN_TIME_CONSTANT", _OWNER),
    Annotation("process/core/caller.py", "CONSTANT_OWNS_BURN_TIME", _OWNER),
    Annotation("process/core/caller.py", "is_out_of_loop", _OWNER),
    Annotation("process/core/caller.py", "burn time", _OWNER),
    Annotation("process/core/caller.py", "pin", _OWNER),
    Annotation("process/core/caller.py", "outer", _OUTER),
    Annotation("process/core/caller.py", "OUTER", _OUTER),
    Annotation("process/core/caller.py", "trust", _OUTER),
    Annotation("process/core/caller.py", "schedule_passes", _OUTER),
    Annotation("process/core/caller.py", "inner_tau", _INNER),
    Annotation("process/core/caller.py", "INNER_TAU", _INNER),
    Annotation("process/core/caller.py", "ArchitectureRefusal", _REFUSAL),
    Annotation("process/core/caller.py", "deck", _WORDS),
    Annotation("process/core/caller.py", "configuration", _WORDS),
    Annotation("process/core/caller.py", "input file", _WORDS),
    Annotation("process/core/caller.py", "V2", _WORDS),
    # --- A56 in module_solve.py ------------------------------------------
    Annotation("process/core/solver/module_solve.py", "MDA", _MDA),
    Annotation("process/core/solver/module_solve.py", "MODULE_SOLVE", _MDA),
    Annotation("process/core/solver/module_solve.py", "FLAT_STATE", _MDA),
    Annotation("process/core/solver/module_solve.py", "flat_state", _MDA),
    Annotation("process/core/solver/module_solve.py", "per_module", _MDA),
    Annotation("process/core/solver/module_solve.py", "partitioned", _MDA),
    Annotation("process/core/solver/module_solve.py", "COUPLING_STATE", _ARTIFACTS),
    Annotation("process/core/solver/module_solve.py", "WRITE_SETS", _ARTIFACTS),
    Annotation("process/core/solver/module_solve.py", "YSTATE_PATH", _ARTIFACTS),
    Annotation("process/core/solver/module_solve.py", "WRITESET_PATH", _ARTIFACTS),
    Annotation("process/core/solver/module_solve.py", "OUTER", _OUTER),
    Annotation("process/core/solver/module_solve.py", "outer", _OUTER),
    Annotation("process/core/solver/module_solve.py", "trust", _OUTER),
    Annotation("process/core/solver/module_solve.py", "schedule", _OUTER),
    Annotation("process/core/solver/module_solve.py", "INNER_TAU", _INNER),
    Annotation("process/core/solver/module_solve.py", "inner_tau", _INNER),
    Annotation("process/core/solver/module_solve.py", "inner", _INNER),
    Annotation("process/core/solver/module_solve.py", "tolerance", _INNER),
    Annotation("process/core/solver/module_solve.py", "ArchitectureRefusal", _REFUSAL),
    Annotation("process/core/solver/module_solve.py", "deck", _WORDS),
    Annotation("process/core/solver/module_solve.py", "configuration", _WORDS),
    Annotation("process/core/solver/module_solve.py", "arrangement", _WORDS),
    Annotation("process/core/solver/module_solve.py", "arm", _WORDS),
    Annotation("process/core/solver/module_solve.py", "ystate artifact", _WORDS),
    Annotation("process/core/solver/module_solve.py", "coupling-state", _WORDS),
    # --- A56 in subsolve.py, constraints.py and the package __init__ -----
    Annotation("process/core/solver/subsolve.py", "BURN_TIME_OWNER", _OWNER),
    Annotation("process/core/solver/subsolve.py", "BURN_TIME_CONSTANT", _OWNER),
    Annotation("process/core/solver/subsolve.py", "OUT_OF_LOOP", _OWNER),
    Annotation("process/core/solver/subsolve.py", "out of the loop", _OWNER),
    Annotation("process/core/solver/subsolve.py", "LIFT", _OWNER),
    Annotation("process/core/solver/subsolve.py", "PIN", _OWNER),
    Annotation("process/core/solver/subsolve.py", "pin", _OWNER),
    Annotation("process/core/solver/subsolve.py", "owner", _OWNER),
    Annotation("process/core/solver/subsolve.py", "constant", _OWNER),
    Annotation("process/core/solver/subsolve.py", "lift", _OWNER),
    Annotation("process/core/solver/subsolve.py", "ArchitectureRefusal", _REFUSAL),
    Annotation("process/core/solver/constraints.py", "PROCESS_ARCH_BURN_TIME_OWNER", _OWNER),
    Annotation("process/core/solver/constraints.py", "PROCESS_ARCH_LIFT", _OWNER),
    Annotation("process/core/solver/__init__.py", "ArchitectureRefusal", _REFUSAL),
    Annotation("process/core/solver/__init__.py", "RETIRED_SWITCHES", _RETIRED),
    # --- A57: the output path, and the audit snapshot hook ---------------
    Annotation("process/core/caller.py", "OUTPUT_LOOP", _OUTPUT_LOOP),
    Annotation("process/core/caller.py", "OUTPUT_PATH", _OUTPUT_LOOP),
    Annotation("process/core/caller.py", "output-time loop", _OUTPUT_LOOP),
    Annotation("process/core/caller.py", "output path", _OUTPUT_LOOP),
    Annotation("process/core/caller.py", "finalise", _OUTPUT_LOOP),
    Annotation("process/core/caller.py", "EXIT_SNAPSHOT", _SNAPSHOT),
    Annotation("process/core/caller.py", "_take_exit_snapshot", _SNAPSHOT),
    Annotation("process/core/caller.py", "snapshot", _SNAPSHOT),
    Annotation("process/core/caller.py", "exit audit", _SNAPSHOT),
    # --- A58: the predicate counters, the block visits, the sweep count ---
    Annotation("process/core/caller.py", "DR4", _PREDICATE_COUNT),
    Annotation("process/core/caller.py", "PREDICATE_EVALUATIONS", _PREDICATE_COUNT),
    Annotation("process/core/caller.py", "COMPONENTS_COMPARED", _PREDICATE_COUNT),
    Annotation("process/core/caller.py", "_objf_agrees", _PREDICATE_COUNT),
    Annotation("process/core/caller.py", "convergence test", _PREDICATE_COUNT),
    Annotation("process/core/caller.py", "BLOCK_VISITS", _BLOCK_VISITS),
    Annotation("process/core/caller.py", "empty", _BLOCK_VISITS),
    Annotation("process/core/caller.py", "DISPATCH_SWEEPS", _SWEEP_COUNT),
    # --- A58: the census instrument's report (A51's handover) ------------
    Annotation("process/core/_idf_probe_modules.py", "reads_by_node", _READS_BY_NODE),
]

#: One paragraph per changed driver file, for a reader who will not read the
#: diff.  Keyed by path; a file with no entry is reported as undocumented.
SUMMARIES: dict[str, str] = {
    "process/core/caller.py": (
        "Two path constants are re-pointed, one existence check is added and "
        "three comments name the copied artifacts.  The driver reads two "
        "committed artifacts by absolute path -- the per-node write sets and "
        "the DSM node map -- and in the repository-root tree it resolves both "
        "under arch_surgery/docs/data/.  In the copy they resolve under "
        "MDA_partitioning_experiment_v4/harness/data/ instead, so the "
        "experiment's driver reads the experiment's artifacts and nothing "
        "outside its own folder.  The write sets are read on two paths and "
        "only one of them checked that the file was there: the per-call "
        "deferral path raised a RuntimeError naming the artifact, the per-run "
        "deferral path raised a bare FileNotFoundError.  The second now "
        "raises the same kind of error, naming the artifact and the "
        "provenance file that records where it came from.  Nothing else "
        "changes: on every path where the file exists the code does exactly "
        "what it did, and the same code reads the same shape of file from a "
        "different place.  On top of that the four architecture switches this "
        "file reads take the names the experiment settled on -- arrangement at "
        "node and at method granularity, deferral at per-call and at per-run "
        "frequency -- together with the module-level names a harness reads "
        "them back through; every table, branch and derivation is the same "
        "code under a different spelling.  One thing here is a removal rather "
        "than a rename: the block schedule now runs exactly once, so the loop "
        "over schedule passes, the joint residual evaluation that decided "
        "whether to repeat it, that evaluation's trace hook and the pass-cap "
        "refusal are gone.  Every arm this experiment runs already took the "
        "single-pass path -- the measurement that removed the other one found "
        "it firing zero times in 91 888 evaluations -- so nothing any arm does "
        "changes, and the reproduction gate is what checks that claim rather "
        "than restating it.  Finally, every refusal of an architecture setting "
        "raises the typed refusal instead of a bare RuntimeError; upstream's "
        "own ten-pass raise is deliberately left alone, because it is a "
        "finding about the shipped code and not a setting being refused.  Last, the "
        "output path itself becomes a choice.  Upstream writes its output "
        "files through a *second* flat idempotence loop: it evaluates the "
        "whole model set, writes an output file to a scratch location, and "
        "repeats -- up to ten times -- until two successive files agree float "
        "by float, and only then writes the real ones.  That loop belongs to "
        "the incumbent's stopping rule, not to the models: an arm whose solve "
        "already converged the coupling state to its own tolerance has "
        "nothing left for it to find, and re-solving the state before writing "
        "it means the numbers in the output files are not the numbers the "
        "optimiser accepted.  PROCESS_ARCH_OUTPUT_LOOP=none therefore calls "
        "finalise once on the accepted state and runs no output-time sweep; "
        "unset, the loop is there unchanged, and two integer counters now say "
        "how many sweeps it took and how many times the output path was "
        "entered.  Alongside it is a hook: a callable slot the measurement "
        "subprocess installs, called at the entry to the output path and "
        "again immediately before the file-writing call.  The experiment "
        "audits how accurate each arm's answer is by taking one further sweep "
        "past termination and measuring how far the state moves, and it must "
        "take that measurement at the same point in every arm -- the point "
        "the solve handed over.  The sweep mutates what it measures, so it "
        "cannot simply be run there; the hook captures the state instead and "
        "the residual is computed after the run.  With nothing installed the "
        "hook is two 'is None' tests per run, and a hook that raises is "
        "recorded rather than allowed to change the run's outcome.  "
        "Finally, the file counts what its convergence tests cost.  The "
        "intervention runs many more sweeps of the dispatch body than the "
        "control while executing far fewer model nodes, and the earlier "
        "revision found it no faster; that can only be true if a sweep costs "
        "something not proportional to the nodes it runs, and the convergence "
        "test is the prime suspect, because a flat block loop compares the "
        "whole coupling state -- 827 to 846 components -- on every sweep while "
        "a block loop compares only its own block's write set.  No conclusion "
        "here may rest on a clock, so the question is asked in counts: how "
        "many times a convergence test was evaluated, and how many components "
        "each of those tests walked.  The two predicates are counted "
        "separately rather than pooled, because an arm runs exactly one of "
        "them and they are not the same test -- the coupling-state predicate "
        "the flat and partitioned arrangements stop on, and upstream's own "
        "idempotence test on the objective and the constraint vector, whose "
        "width is counted exactly since the pair short-circuits.  Beside them "
        "the schedule's visits to each block are counted, and the subset of "
        "those visits that executed no node at all -- measured on the node "
        "counter, because a block can be visited with its member still in it "
        "and that member skipped at the call site.  Measured, the partitioned "
        "arm visits two empty blocks per evaluation on every configuration: "
        "on the two pulsed ones both are empty of members and cost no sweep, "
        "and on the steady-state one the block whose member is skipped costs "
        "a full walk of the sequence.  The user ruled that this stays and is "
        "disclaimed rather than repaired, because dropping the block would "
        "change the node weights the comparison rests on.  Every one of these is a plain integer "
        "increment in the solve phase, touching no float and changing no "
        "branch a result depends on; the output-time loop's own comparisons "
        "are counted by neither, exactly as the per-evaluation sweep "
        "histogram excludes them.  The per-run sweep counter loses its "
        "leading underscore in the same change: it existed only to be "
        "differenced across one evaluation, and the per-sweep-overhead "
        "question needs the run total, which cannot be read from a name a "
        "harness has to reach into the module's privates for."
    ),
    "process/core/_idf_probe_modules.py": (
        "One line.  The census instrument attributes every data-structure read "
        "and write to the model node that made it, and its summary reported "
        "each node's *write* set by name but only the *count* of its reads.  "
        "The names of the reads are what the deferral routing rule is derived "
        "from, so the harness was reaching into the instrument's own "
        "module-level dictionary to get them, from inside the same process -- "
        "a caller coupled to an instrument's internals rather than to its "
        "report.  The summary now carries reads_by_node beside writes_by_node, "
        "built by the same expression from the same dictionary.  The whole "
        "file is a no-op with PROCESS_IDF_PROBE unset, so this changes nothing "
        "any measured run does; that the read sets are identical either way "
        "was measured on all three configurations rather than assumed."
    ),
    "process/core/solver/__init__.py": (
        "Two additions to a file that was one line of docstring.  The first is "
        "ArchitectureRefusal, the exception every driver-side refusal of an "
        "architecture setting now raises: a measurement harness has to tell a "
        "refused run -- the guards working -- from a crashed one, and until "
        "this class existed it did so by matching fragments of the sentences "
        "the driver writes, which puts a reworded message in the wrong row of "
        "the failure table.  The second is the list of switch names the rename "
        "retired, each with the switch that replaced it, checked at the import "
        "of this package.  That check is the load-bearing half of a rename: "
        "before it, an unrecognised switch name was simply ignored, so a "
        "script still setting an old name would produce a *successful* run of "
        "a different arrangement under the right name, with no error anywhere. "
        "It lives in the package's own __init__ because that is the earliest "
        "point every route into the driver passes through."
    ),
    "process/core/solver/subsolve.py": (
        "One switch replaces two.  Taking the burn time out of the model and "
        "naming what holds it instead were two settings -- a list of lifted "
        "sites, and a pinned value -- and they could be set inconsistently: "
        "'a constant owns it, but the model still solves for it' had to be "
        "refused explicitly, because the model would overwrite the constant on "
        "the first sweep. PROCESS_ARCH_BURN_TIME_OWNER says who owns the "
        "quantity in one value -- the loop (the default, and upstream's own "
        "behaviour), the optimiser, or a named constant passed as a hex float "
        "so a measured value survives the round trip exactly -- and the "
        "inconsistent combination can no longer be written down, so its "
        "refusal is gone with it. The seam itself does not change: the "
        "residual is still the contract, the model's own solve is still the "
        "default path, and the tripwire that catches an overwritten constant "
        "still runs at the end of every sweep. The general list form is not "
        "needed while exactly one quantity is ever taken out of the loop; the "
        "module docstring records that a second one would need it back."
    ),
    "process/core/solver/constraints.py": (
        "One docstring. The burn-time consistency constraint explains that it "
        "is what determines the burn time when the model stops solving for it, "
        "and it named the switch that used to say so. It names the switch that "
        "says so now. Nothing the constraint computes changes, and the file "
        "carries no other difference from the source commit."
    ),
    "process/core/solver/module_solve.py": (
        "One path constant is re-pointed and two comments name the copied "
        "files.  The per-module solver loads the coupling-state predicate as "
        "a module by path, because the harness is not an importable package; "
        "in the repository-root tree that is arch_surgery/fixedpoint/"
        "ystate.py.  In the copy it is MDA_partitioning_experiment_v4/harness/"
        "ystate.py -- the same module, moved whole, its body byte-identical "
        "to its source and gated as such.  Same loader, same contract, "
        "different file.  The docstring's reference to the coupling-state "
        "artifact follows the file the copy actually reads.  On top of that, "
        "the shape of the analysis loop takes its intended switch name and its "
        "intended values -- flat and partitioned, with the variable unset "
        "meaning upstream's own loop -- and the two committed artifacts a "
        "block loop reads take theirs.  Two switches are retired outright.  "
        "The one that chose between running the block schedule once and "
        "repeating it is gone, because the schedule now runs once by "
        "definition: the repeated form was measured triggering a further pass "
        "zero times in 91 888 evaluations and the arm that used it was "
        "removed.  So are its mode table, its two composition refusals and its "
        "pass cap.  The other is the second, inner tolerance: there is one "
        "tolerance for every converger in every arm, and comparisons are made "
        "at matched achieved accuracy, which the exit audit records per run, "
        "rather than at matched settings.  Every refusal in the file raises "
        "the typed refusal."
    ),
}


@dataclass
class FileDiff:
    """One changed file: its hunks, its line counts, and who claims them."""

    path: str
    added: int = 0
    removed: int = 0
    hunks: list[dict] = field(default_factory=list)

    @property
    def unexplained(self) -> list[dict]:
        return [h for h in self.hunks if not h["serves"]]


def load_gates():
    """Import ``copy_gates`` by path, so G0' has exactly one implementation."""
    spec = importlib.util.spec_from_file_location("_copy_gates", GATES)
    if spec is None or spec.loader is None:
        raise SystemExit(f"cannot load {GATES}")
    module = importlib.util.module_from_spec(spec)
    # Registered before exec: @dataclass resolves annotations through
    # sys.modules[cls.__module__] and fails on a module that is not there.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def repo_root() -> Path:
    """The working tree's top level -- ``git archive``'s pathspec is relative."""
    return Path(
        subprocess.run(
            ["git", "-C", str(HERE), "rev-parse", "--show-toplevel"],
            check=True,
            stdout=subprocess.PIPE,
            text=True,
        ).stdout.strip()
    )


def extract(commit: str, dest: Path) -> Path:
    """The source commit's ``process/``, in a temporary directory."""
    dest.mkdir(parents=True, exist_ok=True)
    archive = subprocess.run(
        ["git", "-C", str(repo_root()), "archive", commit, "process"],
        check=True,
        stdout=subprocess.PIPE,
    ).stdout
    subprocess.run(["tar", "-x", "-C", str(dest)], input=archive, check=True)
    return dest / "process"


def diff_text(src: Path, copy: Path, context: int) -> str:
    proc = subprocess.run(
        [
            "git",
            "diff",
            "--no-index",
            f"--unified={context}",
            "--",
            str(src),
            str(copy),
        ],
        stdout=subprocess.PIPE,
        text=True,
    )
    if proc.returncode not in (0, 1):
        raise SystemExit(f"git diff --no-index failed ({proc.returncode})")
    return proc.stdout


def parse(raw: str, src: Path, copy: Path) -> list[FileDiff]:
    """Split a unified diff into files and hunks, and claim each hunk."""
    files: list[FileDiff] = []
    current: FileDiff | None = None
    hunk: dict | None = None

    def close_hunk() -> None:
        if current is not None and hunk is not None:
            # Only the **changed** lines are offered to the annotation map.  A
            # context line that happens to contain a marker would otherwise let
            # a hunk be claimed by a mechanism it does not serve, and a claim
            # nobody can check is worse than an UNEXPLAINED nobody can miss.
            text = "\n".join(
                line
                for line in hunk["lines"]
                if line[:1] in "+-" and not line.startswith(("+++", "---"))
            )
            claims = [
                a.serves
                for a in ANNOTATIONS
                if a.path == current.path and a.marker in text
            ]
            hunk["serves"] = "; ".join(dict.fromkeys(claims))
            current.hunks.append(hunk)

    def normalise(raw_path: str) -> str:
        """``+++ b/home/.../PROCESS/process/core/caller.py`` -> ``process/...``.

        ``git diff --no-index`` prefixes ``a/``/``b/`` and drops the leading
        slash of an absolute path, so both have to be put back before the
        package-relative name can be recovered.
        """
        s = raw_path.strip().split("\t")[0]
        if s.startswith(("a/", "b/")):
            s = s[2:]
        if s == "dev/null" or s == "/dev/null":
            return ""
        if not s.startswith("/"):
            s = "/" + s
        for root in (copy.parent, src.parent):
            s = s.removeprefix(str(root) + "/")
        return s

    pending_old = ""
    for line in raw.splitlines():
        if line.startswith("--- "):
            pending_old = normalise(line[4:])
        elif line.startswith("+++ "):
            close_hunk()
            hunk = None
            current = FileDiff(normalise(line[4:]) or pending_old)
            files.append(current)
        elif line.startswith("@@"):
            close_hunk()
            hunk = {"header": line, "lines": [], "serves": ""}
        elif current is not None and hunk is not None:
            hunk["lines"].append(line)
            if line.startswith("+") and not line.startswith("+++"):
                current.added += 1
            elif line.startswith("-") and not line.startswith("---"):
                current.removed += 1
    close_hunk()
    return [f for f in files if f.hunks]


def frozen_statement(gates, prov: dict) -> tuple[bool, list[str]]:
    """Gate G0' re-run live, restated for a reader."""
    res = gates.check_frozen_physics(prov, COPY_ROOT)
    fp = prov["frozen_physics"]
    lines = [
        f"The physics is frozen at base commit {fp['base_commit']} (decision D5). "
        f"Of the {res.compared} files under process/models/ in this copy, "
        f"{res.identical} are byte-identical to that commit and the file set "
        "matches exactly.",
    ]
    for a in fp["approved_differences"]:
        lines.append(
            f"The one file that differs is {a['path']}, and it is approved: "
            f"{a['decision']}."
        )
    if res.detail["unapproved_differences"]:
        lines.append(
            "UNAPPROVED model differences: "
            f"{res.detail['unapproved_differences']} -- this is a finding."
        )
    lines.append(f"Gate G0' verdict: {'PASS' if res.passed else 'FAIL'}.")
    return res.passed, lines


def wrap(text: str, width: int = 78, indent: str = "  ") -> str:
    import textwrap

    return textwrap.fill(text, width=width, initial_indent=indent, subsequent_indent=indent)


def render_text(prov: dict, files: list[FileDiff], frozen: list[str]) -> None:
    src = prov["source"]
    print("=" * 78)
    print("PROCESS_diff -- what V4's copy of PROCESS does differently")
    print("=" * 78)
    print(f"copy          : PROCESS/process/  ({src['file_count']} files)")
    print(f"source commit : {src['commit']}  ({src['commit_full']})")
    print(f"copied on     : {prov['copy_date']}  by {prov['task']}")
    print(f"changed files : {len(files)}")
    print()

    for f in files:
        print("-" * 78)
        print(f"{f.path}   +{f.added} / -{f.removed}   {len(f.hunks)} hunk(s)")
        summary = SUMMARIES.get(f.path)
        print(wrap(summary) if summary else "  (no summary written for this file)")
        print()
        for h in f.hunks:
            tag = h["serves"] or "UNEXPLAINED -- no annotation claims this hunk"
            print(f"  {h['header'].split('@@')[1].strip():<20} {tag}")
        print()

    print("=" * 78)
    print("FROZEN PHYSICS")
    print("=" * 78)
    for line in frozen:
        print(wrap(line, indent=""))
        print()


def render_markdown(prov: dict, files: list[FileDiff], frozen: list[str]) -> None:
    src = prov["source"]
    print(
        "*Caption: one row per file in which V4's copy of the PROCESS package "
        f"differs from its source commit `{src['commit']}`. Columns: the file's "
        "path inside the package; lines added and removed by `git diff` against "
        "the commit (not against any working tree); the number of hunks; and, "
        "per hunk, the switch or mechanism the annotation map in "
        "`PROCESS_diff.py` says it serves, with the number of the file's hunks "
        "that claim names in brackets. A hunk may serve more than one "
        "mechanism. `UNEXPLAINED` means no annotation claims the hunk. "
        "Population: all "
        f"{src['file_count']} files of the copied package.*"
    )
    print()
    print("| file | + | − | hunks | serves |")
    print("|---|---:|---:|---:|---|")
    for f in files:
        # Claims are deduplicated **individually**, not as whole per-hunk
        # strings: a hunk usually serves more than one mechanism, and joining
        # first would make every distinct combination a separate row entry and
        # the column unreadable.  The count beside each claim is how many of
        # the file's hunks it claims.
        counts: dict[str, int] = {}
        for hunk in f.hunks:
            for claim in (hunk["serves"] or "**UNEXPLAINED**").split("; "):
                counts[claim] = counts.get(claim, 0) + 1
        serves = "; ".join(f"{claim} ({n})" for claim, n in counts.items())
        print(f"| `{f.path}` | {f.added} | {f.removed} | {len(f.hunks)} | {serves} |")
    print()
    for f in files:
        if SUMMARIES.get(f.path):
            print(f"**`{f.path}`** — {SUMMARIES[f.path]}")
            print()
    print("**Frozen physics.** " + " ".join(frozen))


def analyse(prov: dict, package: Path, context: int) -> tuple[str, list[FileDiff]]:
    """Diff ``package`` against the source commit and claim every hunk."""
    with tempfile.TemporaryDirectory() as td:
        src = extract(prov["source"]["commit_full"], Path(td) / "source")
        raw = diff_text(src, package, context)
        return raw, parse(raw, src, package)


def teeth(prov: dict, context: int) -> dict:
    """An unannotated change must be reported UNEXPLAINED.

    Protocol section 12: a check whose failure mode has never been exercised is
    an assertion, not a measurement.  A throwaway copy of the package gains one
    line no annotation claims; the real tree is never touched.
    """
    with tempfile.TemporaryDirectory() as td:
        staged = Path(td) / "process"
        shutil.copytree(
            COPY_ROOT / "process",
            staged,
            ignore=shutil.ignore_patterns("__pycache__"),
        )
        victim = staged / "core" / "constants.py"
        victim.write_text(victim.read_text() + "\n# a change nobody wrote down\n")
        _, files = analyse(prov, staged, context)
    unexplained = [(f.path, h["header"]) for f in files for h in f.unexplained]
    return {
        "tooth": "unannotated_hunk",
        "perturbation": "one unclaimed line appended to process/core/constants.py",
        "unexplained_hunks": unexplained,
        "tooth_result": "TRIPPED" if unexplained else "DID NOT TRIP",
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--full", action="store_true", help="print the raw unified diff")
    ap.add_argument("--markdown", action="store_true", help="print a report table")
    ap.add_argument("--context", type=int, default=3, help="diff context lines")
    ap.add_argument(
        "--teeth",
        action="store_true",
        help="show that an unannotated hunk is caught, then exit",
    )
    args = ap.parse_args(argv)

    if not PROVENANCE.exists():
        raise SystemExit(f"{PROVENANCE} is not present; nothing to diff against.")
    prov = json.loads(PROVENANCE.read_text())
    gates = load_gates()

    if args.teeth:
        t = teeth(prov, args.context)
        print(f"tooth {t['tooth']}: {t['tooth_result']}")
        print(f"  perturbation      : {t['perturbation']}")
        for path, header in t["unexplained_hunks"]:
            print(f"  reported UNEXPLAINED: {path}  {header}")
        return 0 if t["tooth_result"] == "TRIPPED" else 1

    raw, files = analyse(prov, COPY_ROOT / "process", args.context)
    frozen_ok, frozen = frozen_statement(gates, prov)

    if args.markdown:
        render_markdown(prov, files, frozen)
    else:
        render_text(prov, files, frozen)
        if args.full:
            print("=" * 78)
            print("RAW UNIFIED DIFF")
            print("=" * 78)
            print(raw)

    unexplained = [(f.path, h["header"]) for f in files for h in f.unexplained]
    undocumented = [f.path for f in files if f.path not in SUMMARIES]
    if unexplained:
        print("\nUNEXPLAINED HUNKS:", file=sys.stderr)
        for path, header in unexplained:
            print(f"  {path}  {header}", file=sys.stderr)
    if undocumented:
        print(f"\nFILES WITHOUT A SUMMARY: {undocumented}", file=sys.stderr)
    return 0 if (frozen_ok and not unexplained and not undocumented) else 1


if __name__ == "__main__":
    sys.exit(main())
