#!/usr/bin/env python
"""Render the A19 report's tables from the analysis JSON."""
from __future__ import annotations
import json, sys
from pathlib import Path

r = json.loads(Path(sys.argv[1]).read_text())
SC = [s for s in r["scenarios"] if r["scenarios"][s].get("samples")]

def m(sc, k):
    v = r["scenarios"][sc]["sweeps"].get(k)
    return f"{v['mean']:.3f}" if v else "--"

print("\n## Gate N19 (neutrality)\n")
print("| Scenario | MFILE lines | differing | signature identical | ifail | status |")
print("|---|---|---|---|---|---|")
for s in SC:
    g = r["gate_neutrality"][s]
    print(f"| `{s}` | {g['mfile_lines']} | {g['mfile_differing']} | {g['signature_identical']} | {g['ifail']} | **{g['status']}** |")

print("\n## Method control (full-sequence replay == coupled S_i)\n")
print("| Scenario | M1 match/compared | M2 | M3 | censored M1/M2/M3 |")
print("|---|---|---|---|---|")
for s in SC:
    mc = r["scenarios"][s]["method_control"]
    cells = [f"{mc[f'M{i}']['match']}/{mc[f'M{i}']['uncensored_compared']}" for i in (1,2,3)]
    cen = "/".join(str(mc[f"M{i}"]["censored"]) for i in (1,2,3))
    print(f"| `{s}` | {cells[0]} | {cells[1]} | {cells[2]} | {cen} |")

print("\n## Validation control\n")
for s in SC:
    print(f"\n**`{s}`**\n")
    print("| comparison | n | identical | fraction | difference histogram (b − a) |")
    print("|---|---|---|---|---|")
    for k, v in r["scenarios"][s]["validation_control"].items():
        print(f"| {k} | {v['n']} | {v['identical']} | {v['frac_identical']} | {v['diff_hist']} |")

print("\n## Sweep counts (mean per call_models, every call sampled)\n")
keys = ["s_global","S1_fullreplay","S2_fullreplay","S3_fullreplay",
        "S1_alone","S2_frozen","S3_frozen","S1_liftreplay","S2_liftreplay","S3_liftreplay",
        "S1_coupled","S2_coupled","S3_coupled"]
print("| Scenario | " + " | ".join(k for k in keys) + " |")
print("|" + "---|"*(len(keys)+1))
for s in SC:
    print(f"| `{s}` | " + " | ".join(m(s,k) for k in keys) + " |")

print("\n## By phase\n")
for s in SC:
    print(f"\n**`{s}`**\n")
    ph = r["scenarios"][s]["sweeps_by_phase"]
    ks = ["s_global","S1_fullreplay","S2_fullreplay","S3_fullreplay","S1_alone","S2_frozen","S3_frozen"]
    print("| phase | n | " + " | ".join(ks) + " |")
    print("|" + "---|"*(len(ks)+2))
    for p in ph:
        row = ph[p]
        n = row["s_global"]["n"] if row["s_global"] else 0
        print(f"| {p} | {n} | " + " | ".join(f"{row[k]['mean']:.3f}" if row.get(k) else "--" for k in ks) + " |")

print("\n## Ordering hypothesis\n")
for s in SC:
    print(f"\n**`{s}`**\n")
    print("| counts | n | S1<=S2<=S3 | S1<=S2 | S2<=S3 | all equal | joint-last M1/M2/M3 | strictly last |")
    print("|---|---|---|---|---|---|---|---|")
    for tag, o in r["scenarios"][s]["ordering"].items():
        jl = o["joint_last"]
        print(f"| {tag} | {o['n']} | {o['frac_S1<=S2<=S3']} | {o['frac_S1<=S2']} | {o['frac_S2<=S3']} | "
              f"{o['frac_all_equal']} | {jl['M1']}/{jl['M2']}/{jl['M3']} | {o['strictly_last']} |")
    print()
    for tag, o in r["scenarios"][s]["ordering"].items():
        print(f"- {tag}: `S2-S1` {o['S2-S1']} · `S3-S2` {o['S3-S2']}")

print("\n## The gate\n")
print("| Scenario | S_i used | weighting | censoring | total | hoist | **partition** |")
print("|---|---|---|---|---|---|---|")
for s in SC:
    for k, v in r["scenarios"][s]["gates"].items():
        src, w, c = k.split("/")
        print(f"| `{s}` | {src} | {w} | {c} | {v['total_pct']} % | {v['hoist_pct']} % | **{v['partition_pct']} %** |")

print("\n## Weights and hygiene\n")
for s in SC:
    b = r["scenarios"][s]
    print(f"- `{s}`: calls {b['call_models_total']}, samples {b['samples']}, "
          f"cost weights {b['weights_measured_cost']}, restore mismatches {b['restore_mismatches']}, "
          f"seq match {b['sequence_check']['match']}, inject overlap "
          f"{b['inject_overlap']['n_also_written_by_a_model']}/{b['inject_overlap']['n_injected_fields']}, "
          f"subsolve errors {b['subsolve_errors'][:2]}, fatal {b['fatal'][:1]}, phases {b['phase_counts']}")
