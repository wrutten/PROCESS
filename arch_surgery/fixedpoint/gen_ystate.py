#!/usr/bin/env python
"""Write the committed record of what every coupling quantity was decided to be.

**Why this exists.**  The convergence predicate scales each quantity by a
characteristic magnitude measured from the harvest, and decides from the same
measurement whether a quantity is tested at all.  Those scales were previously
computed, used and thrown away: the harvest cache lives under
``arch_surgery/idf_probe/runs/``, which is untracked, so after a run nobody
could inspect which scale a given quantity received or notice that one was
absurd.  The numbers still reproduced -- the harvest is deterministic and the
replay determinism gate is bit-for-bit -- so this is not a correctness fix.
What was missing is **auditability**, and it matters here more than it usually
would, because the scales are exactly what separates an excluded quantity from
an included one, and a wrong exclusion makes every architecture declare a
convergence that has not happened, with no symptom.

The artifact is ``arch_surgery/docs/data/ystate_<scenario>.json``, a tracked
path.  ``replay.py`` re-derives the same categorisation from the harvest and
**refuses to run** if it does not match the committed record, so a scale set
cannot be silently paired with a different harvest.

Usage
-----
    PYTHONPATH=<tree> python gen_ystate.py            # every scenario
    PYTHONPATH=<tree> python gen_ystate.py --check    # verify, do not write
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pickle
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from fixedpoint.ystate import (  # noqa: E402
    SCALE_FLOOR,
    SPEC_MODE_A18,
    SPEC_MODES,
    YSpec,
)

TREE = HERE.parent.parent
RUNS = TREE / "arch_surgery" / "idf_probe" / "runs" / "a18"
OUT_DIR = TREE / "arch_surgery" / "docs" / "data"

#: **Three decks, from 2026-09-02 (D17).**  ``large_tokamak_eval`` is dropped:
#: it runs 0 solver iterations, so it cannot inform a study about how an
#: architecture behaves when the optimiser reacts; its inequality constraints
#: are never enforced, so its "solution" is not a feasible optimum; and A22
#: found its evidence weaker than the other pulsed decks (555 of 840 coupling
#: components classified constant from a 10-point harvest).  It was carrying
#: two of the results report's largest percentages on ten design points.
#: **Merged four-deck tables stand as the record of what was run** and are not
#: retro-edited; anything generated from here on is a three-deck table.  Pass
#: ``--scenarios`` explicitly to run the dropped deck for a historical
#: re-derivation.
DROPPED_2026_09_02 = ("large_tokamak_eval",)

SCENARIOS = [
    "large_tokamak_nof",
    "low_aspect_ratio_DEMO",
    "st_regression",
]


def harvest_identity(path: Path, harvest: dict) -> dict:
    """Two hashes: the file as bytes, and its content as meaning.

    The file hash is the cheap one.  The content hash is the one that matters:
    it covers the coupling-key set, the model sequence and, per design point,
    the identity and the design vector as exact hex float literals.  It is
    therefore invariant to how ``pickle`` happens to lay bytes out, and it
    changes if and only if the harvest is a different measurement.
    """
    fh = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            fh.update(chunk)

    ch = hashlib.sha256()
    for k in harvest["y_keys"]:
        ch.update(f"{k[0]}.{k[1]}\n".encode())
    ch.update(("|".join(harvest["node_order"]) + "\n").encode())
    for p in harvest["points"]:
        ch.update(
            f"{p['call_index']}|{p.get('phase')}|{p.get('s_global')}|"
            f"{p.get('m')}|{p['nvars']}|".encode()
        )
        ch.update(",".join(float(v).hex() for v in p["x"]).encode())
        ch.update(b"\n")

    phases: dict = {}
    for p in harvest["points"]:
        phases[p.get("phase")] = phases.get(p.get("phase"), 0) + 1
    try:
        rel = str(path.relative_to(TREE))
    except ValueError:
        # A harvest reached through a symlink into another checkout's
        # untracked run tree.  Recorded as given rather than raising: the file
        # and content hashes above are what identify the harvest, and the path
        # is provenance.
        rel = str(path)
    return {
        "path": rel,
        "file_sha256": fh.hexdigest(),
        "content_sha256": ch.hexdigest(),
        "n_design_points": len(harvest["points"]),
        "design_points_by_phase": dict(
            sorted(phases.items(), key=lambda kv: str(kv[0]))
        ),
        "n_coupling_keys": len(harvest["y_keys"]),
        "node_order": list(harvest["node_order"]),
    }


def out_path(scenario: str, mode: str, scale_floor: float) -> Path:
    """Where a scenario's committed record lives, per spec mode.

    A26's mode gets its own file rather than overwriting A18's: A18, A22 and
    A23's recorded artifacts have to keep re-deriving, and ``replay.py``
    refuses to run against a record that does not match.  A non-canonical
    scale floor gets its own name too --- such a run is a sensitivity probe and
    is *meant* to have no committed record, so it reports ``MISSING`` rather
    than passing silently.
    """
    if mode == SPEC_MODE_A18:
        return OUT_DIR / f"ystate_{scenario}.json"
    if float(scale_floor) == float(SCALE_FLOOR):
        return OUT_DIR / f"ystate_a26_{scenario}.json"
    return OUT_DIR / f"ystate_a26_{scenario}_floor{scale_floor:g}.json"


def build(scenario: str, mode: str = SPEC_MODE_A18,
          scale_floor: float = SCALE_FLOOR) -> tuple[dict, Path]:
    hp = RUNS / scenario / "harvest" / "harvest.pkl"
    if not hp.exists():
        raise SystemExit(
            f"no harvest for {scenario} at {hp}; run "
            f"'run_phase_a.py harvest --scenarios {scenario}' first"
        )
    with open(hp, "rb") as fh:
        harvest = pickle.load(fh)
    assert harvest["format"] == "a18-harvest-1", harvest["format"]
    spec = YSpec.from_harvest(harvest["y_keys"], harvest["points"],
                             mode=mode, scale_floor=scale_floor)
    rec = spec.audit_record(
        scenario=scenario, harvest=harvest_identity(hp, harvest)
    )
    rec["tree_git_head"] = (
        subprocess.run(
            ["git", "-C", str(TREE), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
        ).stdout.strip()
        or None
    )
    return rec, out_path(scenario, mode, scale_floor)


def render(rec: dict) -> str:
    """Pretty at the top level, **one component per line** below it.

    Every component is recorded in full -- nothing is truncated -- but a
    component per line keeps the file greppable and makes a diff show exactly
    which quantity's category or scale moved.  Fully expanded at ``indent=2``
    these files are ~270 kB each; one line per component is ~200 kB and reads
    better.  See the note in the A18 report on why they are committed at all.
    """
    comps = rec.pop("components")
    head = json.dumps(rec, indent=2)
    assert head.endswith("\n}")
    body = ",\n".join(
        "    " + json.dumps(c, separators=(", ", ": ")) for c in comps
    )
    rec["components"] = comps  # leave the caller's dict as it was found
    return head[:-2] + ',\n  "components": [\n' + body + "\n  ]\n}\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenarios", nargs="*", default=SCENARIOS)
    ap.add_argument("--mode", default=SPEC_MODE_A18, choices=list(SPEC_MODES))
    ap.add_argument("--scale-floor", type=float, default=SCALE_FLOOR)
    ap.add_argument(
        "--check",
        action="store_true",
        help="do not write; fail if the committed record differs",
    )
    args = ap.parse_args()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    bad = 0
    for s in args.scenarios:
        rec, out = build(s, args.mode, args.scale_floor)
        text = render(rec)
        if args.check:
            if not out.exists():
                print(f"{s:24s} MISSING  {out.name}")
                bad += 1
                continue
            committed = json.loads(out.read_text())
            # Compare what the predicate depends on, not the raw text.
            # ``tree_git_head`` is provenance and moves with every commit; if
            # it were part of the comparison this check would cry wolf after
            # every commit, and a guard that cries wolf is a guard that gets
            # ignored.
            diffs = [
                k
                for k in ("components_sha256", "census", "n_components",
                          "scales_measured_over_n_design_points")
                if committed.get(k) != rec.get(k)
            ]
            diffs += [
                f"harvest.{k}"
                for k in ("content_sha256", "file_sha256", "n_design_points")
                if (committed.get("harvest") or {}).get(k)
                != (rec.get("harvest") or {}).get(k)
            ]
            if committed.get("components") != rec.get("components"):
                diffs.append("components")
            note = ""
            if committed.get("tree_git_head") != rec.get("tree_git_head"):
                note = (
                    f"  (recorded at {str(committed.get('tree_git_head'))[:8]}, "
                    f"tree now {str(rec.get('tree_git_head'))[:8]} -- "
                    f"provenance only, not compared)"
                )
            print(
                f"{s:24s} {'MATCH' if not diffs else 'DIFFERS'}  {out.name}"
                f"{'' if not diffs else '  ' + ', '.join(diffs)}{note}"
            )
            bad += 0 if not diffs else 1
            continue
        out.write_text(text)
        c = rec["census"]
        print(
            f"{s:24s} {len(text):>8d} bytes  {rec['n_components']} components  "
            f"({c['n_continuous']} continuous, {c['n_discrete']} discrete, "
            f"{c['n_constant']} constant, {c['n_nan_in_harvest']} nan, "
            f"{c['n_nonfinite']} nonfinite, {c['n_excluded_accumulator']} "
            f"excluded)  tested {c['n_tested']}/{c['n_components']}, "
            f"{c['n_scale_from_floor']} at the floor  "
            f"sha={rec['components_sha256'][:12]}"
        )
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
