"""The substitutions this trial makes to V4's driver copy, from outside the V4 folder.

Task A89 (coupling-subset-trial).  One module so the evaluation wrapper, the
census, the noise measurement and the timing child all make **the same**
substitution.  Nothing in the V4 folder is edited: every change is a wrapper
installed in the measurement subprocess after ``process`` is imported.

What :func:`install` changes
----------------------------
1. **The loops' test set.**  ``module_solve.load_subsets`` — the one place the
   driver learns which components of ``y`` each loop tests — is wrapped:

   * ``full``: V4's own subsets, unchanged (the flat block tests all of ``y``);
   * ``interface`` / ``feedback``: each block's V4 write set intersected with
     the DSM-derived set of ``test_sets.json``; the flat block gets the set;
   * ``rbw``: each block's **read-before-write** set, measured by the census
     for *this arm's* execution order (``rbw_sets.json``), used as it stands.

2. **Once-per-run nodes execute once** (V5 improvement list item 5, extended by
   the user on 2026-09-29 to every evaluation-phase arm).  After the loop
   converges, ``call_models`` runs the per-run deferral set once, the way the
   output path does in the optimisation phase (``caller.write_output_files``:
   a fresh Caller's ``_sweep_block`` over that set).  It is counted like any
   other node call.  Only active when the arm defers per run.

3. **Instruments** (no model call, no change to what any loop decides):
   a timer on the coupling-state reads and on the residual (the predicate's
   cost), a timer on ``call_models``, and optionally a per-pass log of the
   narrowed residual beside the whole-``y`` residual of the same snapshots.

``install`` is idempotent per process: the timing child builds a fresh Caller
per repetition and each one reloads the subsets.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEST_SETS_FILE = HERE / "test_sets.json"
RBW_SETS_FILE = HERE / "rbw_sets.json"
TEST_SETS = ("full", "interface", "feedback", "rbw")

#: Accumulated in-process; the caller reads and resets.
TIMERS = {"call_models_s": 0.0, "predicate_read_s": 0.0, "predicate_residual_s": 0.0,
          "n_read": 0, "n_residual": 0, "once_per_run_s": 0.0}
STATE: dict = {"installed": False, "narrowing": None, "in_once": False}


def _chosen_sets(test_set, configuration, arm):
    if test_set in ("interface", "feedback"):
        return json.loads(TEST_SETS_FILE.read_text())["configurations"][configuration][
            "sets"][test_set]
    if test_set == "rbw":
        return json.loads(RBW_SETS_FILE.read_text())["configurations"][configuration][
            arm]["sets"]
    return None


def install(ms, caller_mod, *, test_set, configuration, arm, outdir=None,
            pass_log=False, once_per_run=True):
    """Install the substitutions once in this process.  See the module docstring.

    ``once_per_run=False`` installs substitution 1 (the test set) only and
    leaves ``call_models`` untouched: an **optimisation** run executes the
    per-run deferred nodes once at the output path already (V4's
    ``caller.write_output_files``), so running them after every evaluation
    would add node calls no arm of the campaign makes.  Task A93
    (tolerance-phase-b) uses it; the default keeps A89's evaluation-phase
    behaviour exactly.
    """
    if STATE["installed"]:
        return STATE["narrowing"]
    STATE["installed"] = True
    perf = time.perf_counter
    chosen = _chosen_sets(test_set, configuration, arm)
    narrowing = {"test_set": test_set, "configuration": configuration, "arm": arm,
                 "flat_block_label": ms.FLAT_BLOCK_LABEL, "once_per_run": once_per_run}
    STATE["narrowing"] = narrowing
    log = open(Path(outdir) / "pass_log.jsonl", "w") if (pass_log and outdir) else None  # noqa: SIM115
    original = ms.load_subsets
    done: dict = {}

    def narrowed(spec, path=None):
        if id(spec) in done:
            return done[id(spec)]
        subsets, provenance = original(spec, path)
        index = {spec.name(i): i for i in range(len(spec.keys))}
        if test_set == "full":
            new = dict(subsets)
        elif test_set == "rbw":
            new = {}
            for label, keys in chosen.items():
                missing = [k for k in keys if k not in index]
                if missing:
                    raise RuntimeError(f"rbw set {label} names keys y lacks: {missing[:5]}")
                new[label] = frozenset(index[k] for k in keys)
            # a block the census never saw sweep keeps nothing to test
            for label in subsets:
                new.setdefault(label, frozenset())
            new.setdefault(ms.FLAT_BLOCK_LABEL, frozenset())
        else:
            test = frozenset(index[k] for k in chosen)
            new = {label: frozenset(s & test) for label, s in subsets.items()}
            new[ms.FLAT_BLOCK_LABEL] = test
        narrowing["n_by_block"] = {k: len(v) for k, v in sorted(new.items())}
        narrowing["n_by_block_v4"] = {k: len(v) for k, v in sorted(subsets.items())}
        narrowing["n_y"] = len(spec.keys)
        if outdir:
            (Path(outdir) / "narrowing.json").write_text(json.dumps(narrowing, indent=1))

        inner_residual = spec.residual
        inner_read = spec.read
        label_of = {v: k for k, v in new.items()}

        def read(bound):
            t0 = perf()
            out = inner_read(bound)
            TIMERS["predicate_read_s"] += perf() - t0
            TIMERS["n_read"] += 1
            return out

        def residual(prev, cur, subset=None, **kw):
            t0 = perf()
            res = inner_residual(prev, cur, subset=subset, **kw)
            TIMERS["predicate_residual_s"] += perf() - t0
            TIMERS["n_residual"] += 1
            if log is not None and (subset is not None or test_set == "full"):
                full = inner_residual(prev, cur, subset=None, **kw)
                sel = set(subset) if subset is not None else set(range(len(spec.keys)))
                tau = ms.TAU
                outside = sorted(
                    ((spec.name(int(i)), float(v)) for i, v in zip(full.idx_c, full.scaled)
                     if int(i) not in sel and v >= tau), key=lambda kv: -kv[1])
                log.write(json.dumps({
                    "block": label_of.get(frozenset(subset), "?") if subset is not None else "FULL",
                    "width": len(sel), "narrow_max": float(res.max),
                    "narrow_converged": bool(res.converged(tau)),
                    "full_max": float(full.max), "full_n_above": int(full.n_above(tau)),
                    "outside_n_above": len(outside), "outside_top": outside[:15]}) + "\n")
                log.flush()
            return res

        spec.read = read
        spec.residual = residual
        done[id(spec)] = (new, provenance)
        return new, provenance

    ms.load_subsets = narrowed

    if not once_per_run:
        return narrowing

    orig_cm = caller_mod.Caller.call_models

    def call_models(self, xc, m):
        t0 = perf()
        objf, conf = orig_cm(self, xc, m)
        if caller_mod.DEFER_PER_RUN_ENABLED:
            ps = caller_mod._defer_per_run_nodes(self.data)
            if ps:
                t1 = perf()
                STATE["in_once"] = True
                try:
                    caller_mod.Caller(self.models, self.data)._sweep_block(xc, ps)
                finally:
                    STATE["in_once"] = False
                TIMERS["once_per_run_s"] += perf() - t1
        TIMERS["call_models_s"] += perf() - t0
        STATE["timers_at_call_end"] = dict(TIMERS)  # before any exit-audit residual
        return objf, conf

    caller_mod.Caller.call_models = call_models
    return narrowing


def reset_timers():
    for k in TIMERS:
        TIMERS[k] = 0 if k.startswith("n_") else 0.0
