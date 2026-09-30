#!/usr/bin/env python
"""Where two arms' optimiser paths split, and what the later arm does after the split.

Task A104 (st-stall-mechanism), measurement M1.  **No PROCESS run**: this reads the
V5 campaign's phase B records and the supplementary stage's (``st_census_exact``,
τ = 1e-12), read-only, through the harness's own ``records.read`` (trap T16: the
one place a record's arm names are translated).

What a record holds that this uses
----------------------------------
* ``stdout.log`` -- the optimiser prints one line per iteration,
  ``<k> | Convergence Parameter: <x>`` with ``x`` formatted ``%.3E`` (four
  significant digits; ``process/core/solver/solver.py:202`` of the V5 copy).  The
  numbering restarts at 1 in each attempt of the retry ladder; the lines are split
  into attempts by the record's ``attempts[i].n_iterations`` and the split is
  checked (a count that does not match is reported, never repaired).
* ``entry_census_series.json`` -- the net electric power ``p_net_mw`` at the entry of
  every ``call_models`` of the run, all attempts concatenated.  The entry of
  evaluation ``e`` is the exit of evaluation ``e - 1``, so the series is the exit
  value of every evaluation shifted by one.  **It is the only per-evaluation
  quantity the records carry that depends on the design point**: the records do
  **not** hold the design vector per iteration (only the final one, ``values.xcs``
  as hex).  ``p_net`` is therefore used as a one-scalar fingerprint of the design
  point, never as the design point itself.
* ``values.xcs`` / ``exact.norm_objf`` -- the final design vector and objective, exact.

Mapping evaluations to iterations
---------------------------------
PROCESS's VMCON (``pyvmcon.solve``) evaluates ``problem(x)`` at the head of every
iteration and then line-searches, each ``problem`` call being ``2n + 2``
evaluations (the point, ``2n`` central-difference points, the reconcile call;
``process/core/solver/evaluators.py``).  When every line search accepts its first
trial (α = 1) an attempt of ``K`` iterations costs exactly ``(2n+2)(2K-1)``
evaluations if it converged and ``(2n+2)2K`` if it stopped at the cap, and the
head of iteration ``k`` is evaluation ``(2n+2)·2(k-1)``.  An attempt whose count
matches is **mapped** and its per-iteration ``p_net`` read at the head evaluation's
exit; any other attempt is reported **unmapped** (a line search took a second
trial somewhere, and which iteration it was in is not recoverable from counts).

The comparison of two arms on one start (a pair ``a -> b``)
----------------------------------------------------------
* **split iteration** ``k``: the first iteration of attempt 1 whose printed
  convergence measure differs between the arms as a string -- "differs" means a
  relative difference of at least about 5e-4 in the measure (four printed
  digits); two measures agreeing to four digits are "the same".  If one attempt
  ends before any difference, ``k`` is the first iteration only one arm has.
* the measure of each arm at ``k``;
* ``b``'s iterations from ``k`` in attempt 1, and how many of them read within a
  factor 1000 of the configuration's ``epsvmc`` (below ``1000 × epsvmc``: the
  **near band**; ``epsvmc`` is read from the ``epsvmc`` line of the input file the
  run itself read, copied into its directory);
* ``p_net`` of each arm at the head of iteration ``k`` (both mapped), their
  relative difference -- are they at the same point when the paths split;
* ``p_net`` of ``b`` at the head of iteration ``k`` against ``b``'s final head
  (mapped) -- did the extra iterations move the point, on this proxy;
* the final objective ``norm_objf`` relative difference and the largest relative
  difference of the final iteration variables, both arms accepted
  (``ifail = 1``).  Iteration variables are context only (D6: some are not
  identified by the problem).

The classification rule (declared here, before any count is printed)
-------------------------------------------------------------------
Per start and pair, on **attempt 1** of each arm:

``retried``      either arm was called more than once by the retry ladder (the
                 attempt-1 class is printed beside it, but the start is counted
                 here: what the later attempts did is not a path comparison);
``identical``    the printed measure sequences are equal, same length;
``early``        the paths split at an iteration where either arm's measure is
                 **at or above 1000 × epsvmc** -- the path differs before the
                 measure is small;
``stall``        split with both measures in the near band (below 1000 × epsvmc),
                 and ``b``'s attempt 1 is **longer** than ``a``'s -- the same path,
                 then ``b`` takes more iterations at a small measure;
``shorter``      split with both measures in the near band, ``b``'s attempt 1 not
                 longer.

**What would refute H1** (the partitioned arm follows the flat arm's path to the
optimum and then stalls): starts classed ``early``; or ``stall`` starts whose final
objective differs by more than the same-optimum floor (1e-6 relative, V5 plan
§5 B1), or whose ``p_net`` at the split head differs from the final head by more
than a finite-difference step moves it (about 1e-3 relative, read from the series
itself: see the per-record ``stencil_pnet_rel_step``).

Per record, independent of pairing (declared before any count was read): the
final measure (the reading that stopped the last attempt), and ``n_near`` -- the
iterations, over **all** attempts, whose measure lies in the near band (below
``1000 × epsvmc``), the final iteration of an accepted run excluded (it is the
reading that stopped the run).  A run **hovers** when ``n_near > 10``.  The
population is the accepted runs (final ``ifail = 1``) of each arm.

Usage::

    PYTHONDONTWRITEBYTECODE=1 python optimiser_path_split.py [--runs <v5 runs dir>] [--json <out>]
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
V5 = HERE.parent / "MDA_partitioning_experiment_v5"
sys.path.insert(0, str(V5))

from harness.core import records as records_mod  # noqa: E402

LINE = re.compile(r"^(\d+) \| Convergence Parameter: (\S+)\s*$")
NEAR_FACTOR = 1000.0
HOVER_MIN = 10
SAME_OPTIMUM_FLOOR = 1e-6
N_SEEDS = 25

#: (label, relative directory under runs/, arm) per configuration.
SOURCES = {
    "st_regression": [
        ("BR", "campaign/optimisation/st_regression/BR", "BR"),
        ("B0@1e-8", "campaign/optimisation/st_regression/B0", "B0"),
        ("B2@1e-8", "campaign/optimisation/st_regression/B2", "B2"),
        ("B0@1e-12", "supplementary/st_census_exact/st_regression/B0", "B0"),
        ("B2@1e-12", "supplementary/st_census_exact/st_regression/B2", "B2"),
    ],
    "large_tokamak_nof": [
        ("BR", "campaign/optimisation/large_tokamak_nof/BR", "BR"),
        ("B0", "campaign/optimisation/large_tokamak_nof/B0", "B0"),
        ("B1", "campaign/optimisation/large_tokamak_nof/B1", "B1"),
        ("B2", "campaign/optimisation/large_tokamak_nof/B2", "B2"),
    ],
    "low_aspect_ratio_DEMO": [
        ("BR", "campaign/optimisation/low_aspect_ratio_DEMO/BR", "BR"),
        ("B0", "campaign/optimisation/low_aspect_ratio_DEMO/B0", "B0"),
        ("B1", "campaign/optimisation/low_aspect_ratio_DEMO/B1", "B1"),
        ("B2", "campaign/optimisation/low_aspect_ratio_DEMO/B2", "B2"),
    ],
}

#: The pairs compared, per configuration, ``(a, b)``: ``b`` is read against ``a``.
PAIRS = {
    "st_regression": [
        ("B0@1e-8", "B2@1e-8"),
        ("B0@1e-12", "B2@1e-12"),
        ("BR", "B0@1e-8"),
        ("BR", "B2@1e-8"),
        ("B0@1e-12", "B0@1e-8"),
        ("B2@1e-12", "B2@1e-8"),
    ],
    "large_tokamak_nof": [("B1", "B2"), ("B0", "B1"), ("BR", "B0")],
    "low_aspect_ratio_DEMO": [("B1", "B2"), ("B0", "B1"), ("BR", "B0")],
}


# --------------------------------------------------------------------------
# one record
# --------------------------------------------------------------------------


def read_run(directory: Path, arm: str) -> dict:
    """Everything M1 needs from one run directory, with the checks it made."""
    rec = records_mod.read(directory)
    out: dict = {"dir": str(directory), "status": rec.get("status")}
    if rec.get("status") == "no_record" or "attempts" not in rec:
        out["usable"] = False
        return out
    if rec.get("campaign_arm") != arm:
        raise SystemExit(f"{directory}: record arm {rec.get('campaign_arm')!r} is not {arm!r}")
    out["usable"] = True
    out["arm"] = rec["campaign_arm"]
    out["tau"] = rec.get("campaign_tau")
    out["run_kind"] = rec.get("campaign_run_kind")
    out["tree_git_head"] = rec.get("tree_git_head")
    out["nvar"] = int(rec["nvar"]) if rec.get("nvar") is not None else None
    mf = rec.get("mfile") or {}
    out["ifail"] = mf.get("ifail")
    attempts = rec.get("attempts") or []
    out["n_attempts"] = len(attempts)
    out["iters_per_attempt"] = [int(a.get("n_iterations") or 0) for a in attempts]
    out["ifail_per_attempt"] = [a.get("ifail") for a in attempts]
    out["evals_per_attempt"] = [
        int(((a.get("sweeps_per_eval") or {}).get("n_evaluations")) or 0) for a in attempts
    ]
    out["node_calls_solve_phase"] = rec.get("node_calls_solve_phase")
    exact = rec.get("exact") or {}
    values = rec.get("values") or {}
    out["norm_objf"] = (
        float.fromhex(exact["norm_objf"]) if exact.get("norm_objf") else values.get("norm_objf")
    )
    out["xcs"] = [float.fromhex(h) for h in exact.get("xcs") or []] or None
    out["itvar_names"] = rec.get("itvar_names")

    # the convergence measure per iteration, split into attempts
    lines = []
    stdout = Path(directory) / "stdout.log"
    for line in stdout.read_text(errors="replace").splitlines():
        m = LINE.match(line)
        if m:
            lines.append((int(m.group(1)), m.group(2)))
    per_attempt: list[list[str]] = []
    pos = 0
    ok = True
    for n in out["iters_per_attempt"]:
        chunk = lines[pos : pos + n]
        if [k for k, _ in chunk] != list(range(1, n + 1)):
            ok = False
        per_attempt.append([s for _, s in chunk])
        pos += n
    if pos != len(lines):
        ok = False
    out["measure_split_checked"] = ok
    out["measure_str"] = per_attempt
    out["measure"] = [[float(s) for s in a] for a in per_attempt]

    # p_net per evaluation (entry), and the head of every iteration where mapped
    series_path = Path(directory) / "entry_census_series.json"
    series = json.loads(series_path.read_text()) if series_path.exists() else None
    out["n_series"] = len(series) if series is not None else None
    heads: list[list[float] | None] = []
    offset = 0
    per_call = 2 * out["nvar"] + 2 if out["nvar"] else None
    for i, (K, n_ev) in enumerate(zip(out["iters_per_attempt"], out["evals_per_attempt"], strict=True)):
        mapped = None
        if series is not None and per_call and K > 0:
            converged_shape = per_call * (2 * K - 1)
            capped_shape = per_call * 2 * K
            if n_ev in (converged_shape, capped_shape):
                mapped = []
                for k in range(1, K + 1):
                    j = offset + per_call * 2 * (k - 1) + 1
                    mapped.append(series[j] if j < len(series) else None)
        heads.append(mapped)
        offset += n_ev
    out["series_length_checked"] = series is not None and offset == len(series)
    out["pnet_heads"] = heads
    # what one finite-difference step moves p_net by, relative, at the first head
    # (context for "materially"): the largest |p_net(stencil exit) / p_net(head) - 1|
    # over the first problem call's stencil.
    out["stencil_pnet_rel_step"] = None
    if series is not None and per_call and len(series) > per_call and series[1]:
        base = series[1]
        steps = [abs(series[j] / base - 1.0) for j in range(2, per_call) if series[j] is not None]
        out["stencil_pnet_rel_step"] = max(steps) if steps else None

    # per-record: epsvmc as the run read it, the final measure, the near band
    out["epsvmc"] = epsvmc_in(Path(directory))
    near = NEAR_FACTOR * out["epsvmc"]
    last = out["measure"][-1] if out["measure"] else []
    out["final_measure"] = last[-1] if last else None
    every = [v for att in out["measure"] for v in att]
    if out["ifail"] == 1 and every:
        every = every[:-1]  # the reading that stopped an accepted run
    out["n_near"] = sum(1 for v in every if v < near)
    out["hovers"] = out["n_near"] > HOVER_MIN
    out["at_bound"] = at_bound(Path(directory), out["xcs"], out["itvar_names"])
    return out


def at_bound(directory: Path, xcs, names) -> list[str] | None:
    """Iteration variables whose final value lies within one finite-difference step of a bound.

    The ``ixc = N`` lines name the variables; the design vector is in **ascending**
    ``ixc`` order (checked: every value must lie inside the bounds the file sets for
    the variable it is mapped to, or the mapping is refused and nothing is judged).
    ``boundl(N)`` / ``boundu(N)`` are the bounds; a variable whose bound the file does
    not set is not judged.  "Within one step" means a relative distance below
    ``epsfcn`` = 1e-3.
    """
    if not xcs:
        return None
    files = sorted(directory.glob("*.IN.DAT"))
    text = files[0].read_text(errors="replace").splitlines()
    order, lo, hi = [], {}, {}
    for line in text:
        m = re.match(r"^\s*ixc\s*=\s*(\d+)", line)
        if m:
            order.append(int(m.group(1)))
        m = re.match(r"^\s*bound([lu])\((\d+)\)\s*=\s*([^\s*]+)", line)
        if m:
            (lo if m.group(1) == "l" else hi)[int(m.group(2))] = float(m.group(3).lower().replace("d", "e"))
    order = sorted(order)
    if len(order) != len(xcs):
        return None
    for ix, x in zip(order, xcs, strict=True):
        if (ix in lo and x < lo[ix] * (1 - 1e-12)) or (ix in hi and x > hi[ix] * (1 + 1e-12)):
            return None
    out = []
    for i, (ix, x) in enumerate(zip(order, xcs, strict=True)):
        for side, table in (("lower", lo), ("upper", hi)):
            b = table.get(ix)
            if b is not None and abs(x - b) <= 1e-3 * abs(b):
                out.append(f"{names[i] if names and i < len(names) else ix} near {side} {b:g}")
    return out


def epsvmc_in(directory: Path) -> float:
    """``epsvmc`` from the input file the run read (its copy in the run directory)."""
    files = sorted(directory.glob("*.IN.DAT"))
    if len(files) != 1:
        raise SystemExit(f"{directory}: expected one input file, found {files}")
    for line in files[0].read_text(errors="replace").splitlines():
        s = line.strip()
        if s.startswith("epsvmc") and "=" in s:
            return float(s.split("=", 1)[1].split()[0])
    raise SystemExit(f"{files[0]}: no epsvmc line")


# --------------------------------------------------------------------------
# one pair on one start
# --------------------------------------------------------------------------


def rel(a: float | None, b: float | None) -> float | None:
    if a is None or b is None:
        return None
    if a == b:
        return 0.0
    d = max(abs(a), abs(b))
    return abs(a - b) / d if d else None


def compare(a: dict, b: dict) -> dict:
    out: dict = {}
    if not (a.get("usable") and b.get("usable")):
        out["class"] = "unusable"
        return out
    sa = a["measure_str"][0] if a["measure_str"] else []
    sb = b["measure_str"][0] if b["measure_str"] else []
    ma = a["measure"][0] if a["measure"] else []
    mb = b["measure"][0] if b["measure"] else []
    k = None
    for i in range(max(len(sa), len(sb))):
        if i >= len(sa) or i >= len(sb) or sa[i] != sb[i]:
            k = i + 1
            break
    out["iters_a"] = len(sa)
    out["iters_b"] = len(sb)
    out["split"] = k
    out["retried"] = a["n_attempts"] > 1 or b["n_attempts"] > 1
    out["attempts"] = (a["n_attempts"], b["n_attempts"])
    out["ifail"] = (a["ifail"], b["ifail"])
    if k is None:
        cls = "identical"
    else:
        va = ma[k - 1] if k - 1 < len(ma) else None
        vb = mb[k - 1] if k - 1 < len(mb) else None
        out["measure_a_at_split"] = va
        out["measure_b_at_split"] = vb
        near = NEAR_FACTOR * b["epsvmc"]
        vals = [v for v in (va, vb) if v is not None]
        if any(v >= near for v in vals):
            cls = "early"
        elif len(sb) > len(sa):
            cls = "stall"
        else:
            cls = "shorter"
        rest = mb[k - 1 :] if k - 1 < len(mb) else []
        out["b_iters_from_split"] = len(rest)
        out["b_from_split_near"] = sum(1 for v in rest if v < near)
        ha = (a["pnet_heads"] or [None])[0]
        hb = (b["pnet_heads"] or [None])[0]
        if ha is not None and k - 1 < len(ha):
            out["pnet_a_at_split"] = ha[k - 1]
        if hb is not None and k - 1 < len(hb):
            out["pnet_b_at_split"] = hb[k - 1]
            out["pnet_b_split_vs_b_final_attempt1"] = rel(hb[k - 1], hb[-1])
        out["pnet_split_a_vs_b"] = rel(out.get("pnet_a_at_split"), out.get("pnet_b_at_split"))
    out["attempt1_class"] = cls
    out["class"] = "retried" if out["retried"] else cls
    if a["ifail"] == 1 and b["ifail"] == 1:
        out["norm_objf_rel"] = rel(a["norm_objf"], b["norm_objf"])
        if a["xcs"] and b["xcs"] and len(a["xcs"]) == len(b["xcs"]):
            diffs = [(rel(x, y) or 0.0, i) for i, (x, y) in enumerate(zip(a["xcs"], b["xcs"], strict=True))]
            out["x_max_rel"], i_max = max(diffs)
            names = b.get("itvar_names") or []
            out["x_max_rel_variable"] = names[i_max] if i_max < len(names) else i_max
        # the final heads, both single-attempt and mapped
        if a["n_attempts"] == 1 and b["n_attempts"] == 1:
            ha = a["pnet_heads"][0]
            hb = b["pnet_heads"][0]
            if ha and hb:
                out["pnet_final_a_vs_b"] = rel(ha[-1], hb[-1])
    return out


# --------------------------------------------------------------------------
# rendering
# --------------------------------------------------------------------------


def fmt(v, spec=".1e"):
    if v is None:
        return "—"
    if isinstance(v, float):
        return format(v, spec)
    return str(v)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--runs", default=str(V5 / "runs"))
    p.add_argument("--json", default=None, help="write the per-start results here")
    args = p.parse_args(argv)
    runs = Path(args.runs)

    result: dict = {"runs": str(runs), "configurations": {}}
    hover_rows = []
    class_rows = []
    for config, sources in SOURCES.items():
        recs: dict[str, dict[int, dict]] = {}
        for label, sub, arm in sources:
            recs[label] = {}
            for seed in range(N_SEEDS):
                d = runs / sub / f"seed{seed:03d}"
                recs[label][seed] = read_run(d, arm) if d.exists() else {"usable": False, "status": "absent"}
        cres: dict = {"records": {}, "pairs": {}}
        print(f"\n## {config}\n")
        print("Per record: checks, and the near band (measure below 1000 × epsvmc) over the accepted runs.\n")
        print("| arm | usable | stdout split checked | series length checked | attempt 1 mapped | accepted (ifail 1) | "
              "of which one attempt | epsvmc (from the runs' input files) | final measure median [min, max] | "
              "n_near median [min, max] | hovering (n_near > 10) | p_net step of one FD column, median |")
        print("|---|---|---|---|---|---|---|---|---|---|---|---|")
        for label, _sub, _arm in sources:
            rs = [r for r in recs[label].values() if r.get("usable")]
            acc = [r for r in rs if r["ifail"] == 1]
            acc1 = [r for r in acc if r["n_attempts"] == 1]
            eps = sorted({r["epsvmc"] for r in rs})
            fm = [r["final_measure"] for r in acc if r["final_measure"] is not None]
            nn = [r["n_near"] for r in acc]
            hov = sum(1 for r in acc if r["hovers"])
            steps = [r["stencil_pnet_rel_step"] for r in rs if r.get("stencil_pnet_rel_step")]
            mapped = sum(1 for r in rs if r["pnet_heads"] and r["pnet_heads"][0] is not None)
            print(
                f"| {label} | {len(rs)}/25 | {sum(r['measure_split_checked'] for r in rs)}/{len(rs)} | "
                f"{sum(r['series_length_checked'] for r in rs)}/{len(rs)} | {mapped}/{len(rs)} | {len(acc)} | {len(acc1)} | "
                f"{', '.join(format(e, 'g') for e in eps)} | "
                f"{fmt(statistics.median(fm)) if fm else '—'} [{fmt(min(fm)) if fm else '—'}, {fmt(max(fm)) if fm else '—'}] | "
                f"{statistics.median(nn) if nn else '—'} [{min(nn) if nn else '—'}, {max(nn) if nn else '—'}] | "
                f"{hov} of {len(acc)} | {fmt(statistics.median(steps)) if steps else '—'} |"
            )
            hover_rows.append((config, label, hov, len(acc), statistics.median(nn) if nn else None))
            cres["records"][label] = {
                str(s): {k: v for k, v in r.items() if k not in ("measure_str",)}
                for s, r in recs[label].items()
            }
        for a_label, b_label in PAIRS[config]:
            rows = {}
            for seed in range(N_SEEDS):
                rows[seed] = compare(recs[a_label][seed], recs[b_label][seed])
            counts: dict[str, int] = {}
            for r in rows.values():
                counts[r["class"]] = counts.get(r["class"], 0) + 1
            class_rows.append((config, f"{a_label} → {b_label}", counts))
            cres["pairs"][f"{a_label} -> {b_label}"] = {"per_seed": {str(s): r for s, r in rows.items()}, "counts": counts}
            print(f"\n### {config}: {a_label} → {b_label}\n")
            print("Classes (rule in the script docstring): " + ", ".join(f"{k} {v}" for k, v in sorted(counts.items())) + " (of 25)\n")
            print("| seed | class (attempt-1 class) | attempts a/b | ifail a/b | iterations a/b (attempt 1) | split k | "
                  "measure a / b at k | b's iterations from k: all / in the near band | p_net a vs b at k | "
                  "p_net b at k vs b final (attempt 1) | norm_objf rel diff | x max rel diff (variable) |")
            print("|---|---|---|---|---|---|---|---|---|---|---|---|")
            for seed, r in rows.items():
                if r["class"] == "unusable":
                    print(f"| {seed} | unusable | | | | | | | | | | |")
                    continue
                cls = r["class"] + (f" ({r['attempt1_class']})" if r["class"] == "retried" else "")
                split = r.get("split")
                meas = (f"{fmt(r.get('measure_a_at_split'), '.2e')} / {fmt(r.get('measure_b_at_split'), '.2e')}"
                        if split else "—")
                after = (f"{r.get('b_iters_from_split')} / {r.get('b_from_split_near')}" if split else "—")
                xv = f"{fmt(r.get('x_max_rel'))} ({r.get('x_max_rel_variable', '—')})" if r.get("x_max_rel") is not None else "—"
                bnd = recs[b_label][seed].get("at_bound") if recs[b_label][seed].get("usable") else None
                bnd_a = recs[a_label][seed].get("at_bound") if recs[a_label][seed].get("usable") else None
                if bnd or bnd_a:
                    xv += f"; at a bound: a {', '.join(bnd_a or []) or 'none'}; b {', '.join(bnd or []) or 'none'}"
                print(
                    f"| {seed} | {cls} | {r['attempts'][0]}/{r['attempts'][1]} | "
                    f"{fmt(r['ifail'][0], '.0f')}/{fmt(r['ifail'][1], '.0f')} | {r['iters_a']}/{r['iters_b']} | {split or '—'} | "
                    f"{meas} | {after} | {fmt(r.get('pnet_split_a_vs_b'))} | "
                    f"{fmt(r.get('pnet_b_split_vs_b_final_attempt1'))} | {fmt(r.get('norm_objf_rel'))} | {xv} |"
                )
        result["configurations"][config] = cres
    print("\n## Summary: hovering runs (n_near > 10), accepted runs as denominator\n")
    print("| configuration | arm | hovering | median n_near |")
    print("|---|---|---|---|")
    for config, label, hov, n, med in hover_rows:
        print(f"| {config} | {label} | {hov} of {n} | {med} |")
    print("\n## Context: retries and node calls per evaluation\n")
    print("Retried: runs whose optimiser used more than one attempt of its retry ladder, over the runs that "
          "finished (status ok: not crashed).  Node calls per evaluation: the solve phase's node calls over its "
          "evaluations, pooled (ratio of sums) over the configuration's seed set -- the seeds on which every "
          "campaign arm of the configuration reached an accepted optimum (the paper's population); the "
          "supplementary arms are read over the same seeds.\n")
    print("| configuration | arm | retried / finished | seed set size | node calls per evaluation (seed set) | over BR's | over the path-matched flat arm's at the same τ |")
    print("|---|---|---|---|---|---|---|")
    for config, sources in SOURCES.items():
        recs = result["configurations"][config]["records"]
        campaign_labels = [lb for lb, sub, _ in sources if sub.startswith("campaign/")]
        seed_set = [
            str(s) for s in range(N_SEEDS)
            if all(recs[lb][str(s)].get("usable") and recs[lb][str(s)].get("ifail") == 1 for lb in campaign_labels)
        ]
        per_eval = {}
        for label, _sub, _arm in sources:
            nodes = sum(recs[label][s]["node_calls_solve_phase"] or 0 for s in seed_set)
            evals = sum(sum(recs[label][s]["evals_per_attempt"]) for s in seed_set)
            per_eval[label] = nodes / evals if evals else None
        flat_of = {"B2": "B1", "B2@1e-8": "B0@1e-8", "B2@1e-12": "B0@1e-12"}
        for label, _sub, _arm in sources:
            rs = [r for r in recs[label].values() if r.get("usable") and r.get("status") == "ok"]
            retried = sum(1 for r in rs if r["n_attempts"] > 1)
            per = per_eval[label]
            over_ref = per / per_eval["BR"] if per and per_eval.get("BR") else None
            flat = flat_of.get(label)
            over_flat = per / per_eval[flat] if flat and per and per_eval.get(flat) else None
            print(f"| {config} | {label} | {retried} / {len(rs)} | {len(seed_set)} | {fmt(per, '.1f')} | "
                  f"{fmt(over_ref, '.2f')} | {fmt(over_flat, '.2f')} |")
    print("\n## Where the accepted runs end: iteration variables within one finite-difference step (1e-3 "
          "relative) of a bound the input file sets, runs per variable over the accepted runs\n")
    print("| configuration | arm | accepted runs judged | variable: runs ending within one step of its bound |")
    print("|---|---|---|---|")
    for config, sources in SOURCES.items():
        recs = result["configurations"][config]["records"]
        for label, _sub, _arm in sources:
            acc = [r for r in recs[label].values() if r.get("usable") and r.get("ifail") == 1]
            judged = [r for r in acc if r.get("at_bound") is not None]
            tally: dict[str, int] = {}
            for r in judged:
                for item in r["at_bound"]:
                    tally[item] = tally.get(item, 0) + 1
            cells = "; ".join(f"{k}: {v}" for k, v in sorted(tally.items()))
            print(f"| {config} | {label} | {len(judged)} of {len(acc)} | {cells or 'none'} |")
    print("\n## Summary: classes per pair (of 25 starts)\n")
    print("| configuration | pair | identical | early | stall | shorter | retried | unusable |")
    print("|---|---|---|---|---|---|---|---|")
    for config, pair, c in class_rows:
        print(f"| {config} | {pair} | " + " | ".join(str(c.get(k, 0)) for k in ("identical", "early", "stall", "shorter", "retried", "unusable")) + " |")
    if args.json:
        Path(args.json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.json).write_text(json.dumps(result, indent=1, default=str))
        print(f"\nper-start results written to {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
