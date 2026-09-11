# A62 (exit-audit-restore) — the exit audit sweeps the loop's own map

> **Document status** — **OPEN.** Task **A62 (exit-audit-restore)**, branch `A62-exit-audit-restore`
> off `architecture_surgery` at `fb0a7130`. Harness only: nothing under
> `arch_surgery/MDA_partitioning_experiment_v4/PROCESS/` or the repository-root `process/` is
> touched, by ruling **D25**. Run records live in
> `arch_surgery/MDA_partitioning_experiment_v4/runs/` and are untracked by design; the retire
> script relocates them at merge. Folder position records lifecycle, not validity (trap T3).

---

## 0. The words, spelled out once

*Caption: one row per term this report uses in a particular way. "Means" is the definition in
force here; where the project's vocabulary already fixes a word, this is that definition and not
a new one.*

| term | means |
|---|---|
| **exit audit** | **one further full sweep of the whole model set**, taken past termination from the state the solve handed over, on the identical instrument in every arm and charged to no arm. Its residual is read as *how far from converged the accepted point still was* |
| **snapshot position** | where the audited state is taken from. The driver offers two — the entry to `write_output_files` (the state the solve handed over, which is the position the experiment plan declares) and immediately before the files are written — and the harness offers two audit positions: the declared one, and `after_run`, which gate GR alone uses |
| **restored set** | the data-structure fields the audit puts back before its sweep, so that the sweep evaluates the map the loop iterated and not the one PROCESS's output path left behind. **Derived** — what differs between the snapshot and the state the sweep would otherwise start from — never a hand-written list |
| **instrument version** | which mechanism produced a residual, stamped in every record at `exit_audit.instrument.restores`. Two residuals made by different instruments are two measurements, not a difference |
| **residual** | the largest scaled movement of the coupling state under the audit's sweep, `max_i |Δy_i| / s_i`, published on both rulers — **frozen** (`s_i` measured once and committed) and **mixed** (`max(|y_i|, s_i)`) — on every run, always |
| **restricted statistic** | the residual over the components that are **not** written by the nodes an arm defers to once per run. Membership is derived from the committed per-run deferral artifact and the committed run-time write census, never listed |
| **straddle** | a run of gate G1 whose two captures are at two different commits, so that a zero is a statement about a change rather than about determinism. The "before" capture is never re-made |

---

## 1. Verdict

**Ruling D25 is implemented, and the reading it was meant to fix is gone.** The exit audit now
snapshots the whole data structure at each position the driver offers and, before its sweep, puts
back a **derived** set — what differs between the snapshot and the state the sweep would otherwise
start from — so the sweep evaluates the map the loop iterated rather than the one PROCESS's output
path left behind. Harness only: nothing under `…_v4/PROCESS/` or the repository-root `process/`
changed.

*Caption: the five things the task was to show, each with the measurement that settles it and the
section that carries it. Every number is a count or a bit comparison; no conclusion rests on a
timing.*

| what had to hold | result | where |
|---|---|---|
| `tfcoil.insstrain` at exactly `0x0.0p+0` on `BR`, `B0`, `B1`, `B3`, both pulsed configurations | **yes, 8 of 8 arms**, and the diagnosis stage's leave-one-out pair has **nothing left to attribute (9 of 9 runs)** | §8 |
| the restricted and whole-state maxima are the loop's own map's, 0 components above τ everywhere | **0 above τ on 31 of 31 records made by this instrument** at the declared position; the maxima are ≤ 1.24e-11, and `0x0.0p+0` on `low_aspect_ratio_DEMO` | §5.1, §5.2 |
| every record stamps the instrument, what it restored and what it could not, declared in `records.SCHEMA` and covered by G7 | **yes** — `exit_audit.instrument`, four declared fields, 89 / 82 per phase; G7 **PASS**, 9/9 teeth | §3.2, §7 |
| G1 as a genuine straddle, everything but the audit identical | **PASS**, `fd480aff` → `3d64625c`: **0 of 2 831** record values and **0 of 51 319** output-file lines differ; 957 excluded by the new kind, **0 of them outside the exit audit and its stamp**; 7/7 teeth | §7, §7.2 |
| GR's compared set loses the audit residual with its reason, the reference not regenerated | **PASS**, **270 → 256**: 14 excluded by name, 0 of 256 mismatched, 20/20 runs; the doctored-residual tooth reports *excluded* | §6 |

**Two results beyond the brief.**

1. **A defect the gate caught, and the instrument was fixed rather than the gate.** Restoring
   *everything* outside the coupling state rewound PROCESS's own call counter, so `n_model_calls`
   — a value gate GR compares — read two lower on the reference arm. One namespace, `numerics`, is
   now held back by a named rule whose boundary a G4 tooth measures and flips (§3.4).
2. **The audit after the run now measures something.** Its residual used to be trivially
   `0x0.0p+0`; with the solve-phase settings put back it is 6.99e-03 on `large_tokamak_nof` and
   7.02e-03 on `low_aspect_ratio_DEMO`, argmax `tfcoil.insstrain`, **on PROCESS exactly as
   shipped**. That is the distance between the state PROCESS *writes out* and a fixed point of the
   map its own solve iterated — a direct handle on issue **I-21** (§5.3).

---

## 2. How to re-run everything in this report

Every number below comes from one of these commands, pressed from the **repository root** with
`/home/wrutten/anaconda3/envs/PROCESS_surgery_env/bin/python`. No number in this report was
produced by a shell invocation (protocol §15).

```bash
PY=/home/wrutten/anaconda3/envs/PROCESS_surgery_env/bin/python
RUNNER=arch_surgery/MDA_partitioning_experiment_v4/experiment_runner.py
V3DECKS=/home/wrutten/projects/PROCESS_surgery/arch_surgery/MDA_partitioning_experiment_v3/runs/_decks

# gate G1's "after" capture; the "before" capture is the orchestrator's, at trunk
# fd480aff, and is NEVER re-made
$PY $RUNNER --gate switch_neutrality --capture after
$PY $RUNNER --gate switch_neutrality --resume

# every gate, from nothing, with its teeth
$PY $RUNNER --gate all --census-entry evaluation --lifted-from $V3DECKS

# the measurements, the artifacts, the self-check, the preflight
$PY $RUNNER --measure all
$PY $RUNNER --artifacts all --census-entry evaluation
$PY $RUNNER --selfcheck
$PY $RUNNER

# the copy's own gates and the view of where this experiment changed PROCESS
$PY arch_surgery/MDA_partitioning_experiment_v4/PROCESS/copy_gates.py all
$PY arch_surgery/MDA_partitioning_experiment_v4/PROCESS_diff.py --markdown

# A61's diagnosis stage, re-run against the changed instrument
cd arch_surgery/MDA_partitioning_experiment_v4
HARNESS_WORKERS=3 PYTHONPATH=PROCESS $PY -m harness.exit_audit_diagnosis all
```

---

## 3. What changed, and why that is the whole of it

### 3.1 The defect, restated in one paragraph

The exit audit is one further sweep of the model set, taken from the state the solve handed over,
and its residual is read as *how far from converged that state was*. That reading has a premise:
the sweep must be the **same map** the loop iterated. Task A61 (insstrain-diagnosis) measured the
premise failing. PROCESS's output path raises `tfcoil.n_rad_per_layer` — the radial
discretisation of the TF-coil stress calculation — from 100 to 500 through four latching writes,
and puts it back nowhere. The field is not a coupling-state component, so the audit's snapshot did
not capture it and its restore did not restore it, and the audit's sweep ran the stress model on a
different mesh than the loop had. One component then sat at ~7e-3 scaled, far above τ = 1e-6, in
every arm on both pulsed configurations — including the reference arm, PROCESS as shipped — and
was published for two revisions as a convergence result.

### 3.2 The mechanism, as built

Ruling **D25** is implemented in four pieces, all harness-side.

* **`harness/data_structure.py` (new).** Snapshot every field of every namespace of PROCESS's data
  structure, exactly (floats as hexadecimal literals, float arrays as hex element lists, by the
  same serialiser the coupling-state snapshot uses); compare two snapshots; write one back and
  prove the write took by reading every field back. A namespace that is not a dataclass is
  *named*, not dropped; a field that cannot be rebuilt is *named*, not counted as restored. The
  three functions were A61's, inside a gate instrument that is refused on campaign runs; they move
  here because the exit audit runs on every run, and `harness/audit_map.py` now imports them.
* **`child.install_exit_snapshot`.** The driver's hook now takes **two** snapshots at each of the
  two positions the driver offers: the coupling state, as before, and the whole data structure.
  The structure snapshots stay in memory and never enter the run record — two thousand fields per
  position is a file a gate would walk value by value — and what the record carries is the
  restore's own counts and names. The hook is installed **whatever audit position was asked for**,
  which it was not before.
* **`child.take_exit_audit`.** Before the sweep: take a snapshot of the live structure, derive what
  differs from the snapshot position's, and put that derived set back. Then the coupling-state
  restore, proved bit-exact as before, at the declared position. Then a census of *the state the
  sweep actually starts from* against the snapshot — which is the claim the residual rests on, and
  is stronger than "everything I asked to restore worked".
* **The instrument stamps itself.** `exit_audit.instrument.restores` names the mechanism in every
  record, and the block beside it says which positions were snapshotted, how many fields the
  derived set held, how many were restored, how many could not be **and which by name**.

### 3.3 What the coupling state is *not* restored from, and why that is the point

The derived set deliberately **excludes the coupling state's own components**, and that is what
keeps the two audit positions distinct rather than collapsing one into the other:

* at the **declared** position the coupling state is restored from the coupling snapshot, bit for
  bit, and an audit whose restore is not bit-exact still refuses rather than report a residual of
  a state nobody chose;
* at **`after_run`** the coupling state is deliberately the state the run ended in — that is what
  the position *means* — while everything outside it is put back to its solve-phase value, so the
  sweep there is the loop's map too.

### 3.4 One namespace the audit does not put back, and the gate that found it

The first version of this restore put back *everything* outside the coupling state. Gate G1 caught
it: `n_model_calls` — a value gate GR compares — read **two lower** on the reference arm, because
PROCESS's output-time loop increments `numerics.n_model_calls` twice between the snapshot and the
audit and the restore wound it back. The record would then have published the instrument's
bookkeeping as the run's cost.

The answer to a gate catching an instrument contaminating a measurement is to fix the instrument.
`child.NAMESPACES_THE_AUDIT_DOES_NOT_RESTORE` names **one namespace**, with its reason:
`numerics` is the optimiser's own account of the run — the design vector, the constraint
residuals, the iteration and call counters, the finite-difference step — the record reads it
*after* the audit, and the models reach none of it except through the design vector, which the
audit injects explicitly. It is a rule about a namespace, not a list of fields, and **whatever it
holds back is named per run** in `exit_audit.instrument.held_back_by_rule`, so it cannot quietly
grow.

**Why the optimiser's own accounting is the right boundary.** The audit's sweep reads the design
vector from `x`, which it injects explicitly, and reads model state from the namespaces the models
write. `numerics` is neither: it is where VMCON keeps what it did — the vector, the constraint
residuals, the iteration and call counters, the finite-difference step — and the run record reads
it *after* the audit, which is the only reason the audit can contaminate it at all. Putting a
counter back is not making the map the loop's; it is un-counting work the run did.

**What would be hidden if that stopped being true.** If PROCESS's output path ever wrote a
*model input* into `numerics` — a tolerance a model reads, say — the rule would leave it changed
and the audit's sweep would again not be the loop's map, in exactly the way this task exists to
stop. Two things keep that from being silent. The record names every field the rule held back, per
run, so a new name appearing there is visible without anyone looking for it; and the census of the
state the sweep starts from counts those same fields as **still differing**, so the claim "the
sweep starts from the snapshot" is never made about them. A gate tooth pins the boundary as well:
gate G4 reads one of its own optimisation records and requires the TF-coil stress mesh to be in
the restored set and the held-back fields to be exactly the differing fields of the held-back
namespaces, then swaps the two names between namespaces and requires them to change sides — so the
rule is the namespace and nothing else.

---

## 4. What the instrument now does, measured

*Caption: one optimisation run of the reference arm `BR` on `large_tokamak_nof` at seed 0, at the
plan's declared audit position, from its own record's `exit_audit.instrument` block. "Snapshot"
is the whole data structure as it stood at the entry to `write_output_files`; "the sweep's start"
is the state the audit's sweep was actually taken from, after both restores. Every count is over
the same 2 288 fields of 36 namespaces.*

| quantity | value |
|---|---|
| fields in the snapshot | 2 288, over 36 namespaces, 0 skipped |
| positions snapshotted | `entry_to_write_output_files`, `before_finalise` |
| fields differing between the snapshot and the sweep's start, before any restore | 99 |
| of those, inside the coupling state | 13 |
| of those, outside it | 86 |
| held back by the namespace rule | 1 — `numerics.n_model_calls` |
| **derived restored set** | **85**, `tfcoil.n_rad_per_layer` among them |
| restored and read back bit-identical | 85 |
| could not be restored | 0 |
| fields of the snapshot that could never be put back (round-trip census) | 2 — `globals.fileprefix` (a bare `repr`), `numerics.name_xc` (does not serialise back equal) |
| **fields still differing from the snapshot when the sweep starts** | **1**, and it is the one the rule held back; 0 the restore asked for and missed; 0 inside the coupling state |

The last row is the claim the residual rests on, and it is stronger than "everything I asked to
restore worked": the state the sweep is taken from *is* the state the snapshot recorded, field by
field, except for the one field a named rule declines to rewind.

---

## 5. The audit tables, before and after

### 5.1 The restricted statistic at the declared audit position

This is the table A52 (harness-gates) §6.4 published, re-taken. The **before** column is quoted
from that report — the runs behind it no longer exist in this worktree and cannot be re-made
without reverting the instrument; A61 (insstrain-diagnosis) §9.1 reproduced those numbers exactly
with a third instrument, which is the only independent check this report has of them. The
**after** column is this task's own records, read by gate G4's census
(`runs/gates/audit_restriction/gate.json`).

*Caption: the restricted exit-audit maximum at the accepted point, at the plan's declared audit
position, on the frozen ruler, one row per distinct (arm, configuration) at seed 0. "Above τ"
counts restricted components at or above τ = 1e-6; "kept" is the restricted statistic's own
denominator. Instrument before: the coupling state alone. Instrument after:
`whole_data_structure_derived_set`.*

| arm | configuration | before: max | before: argmax | above τ | after: max | after: argmax | above τ | kept |
|---|---|---|---|---:|---|---|---:|---:|
| `BR` | `large_tokamak_nof` | 6.991e-03 | **`tfcoil.insstrain`** | 1 | **1.150556e-11** (`0x1.94d0e2a68b136p-37`) | `heat_transport.tlvpmw` | **0** | 696 |
| `B0` | `large_tokamak_nof` | 6.991e-03 | **`tfcoil.insstrain`** | 1 | **1.150556e-11** (`0x1.94d0e2a68b136p-37`) | `heat_transport.tlvpmw` | **0** | 696 |
| `B1` | `large_tokamak_nof` | 7.119e-03 | **`tfcoil.insstrain`** | 1 | **`0x0.0p+0`** | `blanket.deg_blkt_inboard_poloidal_plasma` | **0** | 696 |
| `B3` | `large_tokamak_nof` | 7.119e-03 | **`tfcoil.insstrain`** | 1 | **`0x0.0p+0`** | `blanket.deg_blkt_inboard_poloidal_plasma` | **0** | 696 |
| `BR` | `low_aspect_ratio_DEMO` | 7.021e-03 | **`tfcoil.insstrain`** | 1 | **`0x0.0p+0`** | `blanket.deg_blkt_inboard_poloidal_plasma` | **0** | 701 |
| `B0` | `low_aspect_ratio_DEMO` | 7.021e-03 | **`tfcoil.insstrain`** | 1 | **`0x0.0p+0`** | `blanket.deg_blkt_inboard_poloidal_plasma` | **0** | 701 |
| `B1` | `low_aspect_ratio_DEMO` | 7.021e-03 | **`tfcoil.insstrain`** | 1 | **`0x0.0p+0`** | `blanket.deg_blkt_inboard_poloidal_plasma` | **0** | 701 |
| `B3` | `low_aspect_ratio_DEMO` | 7.021e-03 | **`tfcoil.insstrain`** | 1 | **`0x0.0p+0`** | `blanket.deg_blkt_inboard_poloidal_plasma` | **0** | 701 |
| `BR` | `st_regression` | 4.894e-14 | `physics.f_beta_alpha_beam_thermal` | 0 | 4.893726e-14 (`0x1.b8c9a121abb97p-45`) | `physics.f_beta_alpha_beam_thermal` | 0 | 682 |
| `B0` | `st_regression` | 4.930e-14 | `physics.f_beta_alpha_beam_thermal` | 0 | 4.930383e-14 (`0x1.bc16e29405387p-45`) | `physics.f_beta_alpha_beam_thermal` | 0 | 682 |
| `B3` | `st_regression` | 1.604e-11 | `fwbs.p_cp_shield_nuclear_heat_mw` | 0 | 1.604178e-11 (`0x1.1a35bc8aaced8p-36`) | `fwbs.p_cp_shield_nuclear_heat_mw` | 0 | 682 |

**Three things this says.**

* **On the two pulsed configurations the maximum falls by eight orders of magnitude or to exactly
  zero, and `tfcoil.insstrain` is no longer the argmax anywhere.** The component now sits at
  exactly `0x0.0p+0` — its own residual, not merely below the maximum — in every arm on both
  pulsed configurations (§8).
* **On `st_regression` nothing moves at all**, to every digit published. That configuration's
  `insstrain` is `None` from the first sweep (A61 §3), so the mesh change never reached the
  statistic there, and the fact that the three rows are unchanged is the control this table has
  for "did the restore move anything it should not have".
* **What the argmax is now.** `heat_transport.tlvpmw` on `large_tokamak_nof` at 1.150556e-11,
  five orders below τ; nothing at all on `low_aspect_ratio_DEMO`, where the handed-over state is a
  bit-exact fixed point of the loop's map; `physics.f_beta_alpha_beam_thermal` and
  `fwbs.p_cp_shield_nuclear_heat_mw` on `st_regression`, unchanged. **G4's whole census: 31 of 31
  records made by this instrument at the declared position have 0 components above τ**, and the
  only 4 of 37 that still show `tfcoil.insstrain` are reused records made by the previous
  instrument (§7).

### 5.2 A57 (driver-output-path) §10.3 — the arms whose output path is the one-call path

*Caption: the same quantity on gate G9's own runs, which is the population A57 §10.3 published.
"Whole state" counts every tested component; "restricted" excludes the components the per-run
deferred nodes write. The whole-state count on an arm that defers is the deferral working, not
non-convergence — those nodes' outputs move because the audited state is from before they ran.*

| arm | configuration | tested | before: above τ, restricted | after: above τ, restricted | after: restricted max | after: restricted argmax |
|---|---|---:|---:|---:|---|---|
| `B1` | `large_tokamak_nof` | 818 | **1** | **0** | `0x0.0p+0` | `blanket.deg_blkt_inboard_poloidal_plasma` |
| `B3` | `large_tokamak_nof` | 818 | **1** | **0** | `0x0.0p+0` | `blanket.deg_blkt_inboard_poloidal_plasma` |
| `B1` | `low_aspect_ratio_DEMO` | 824 | **1** | **0** | `0x0.0p+0` | `blanket.deg_blkt_inboard_poloidal_plasma` |
| `B3` | `low_aspect_ratio_DEMO` | 824 | **1** | **0** | `0x0.0p+0` | `blanket.deg_blkt_inboard_poloidal_plasma` |
| `B3` | `st_regression` | 805 | **0** | **0** | 1.604178e-11 | `fwbs.p_cp_shield_nuclear_heat_mw` |

**The sentence A57 and A52 could not write, and this report can:** at the accepted point, on every
configuration and in every arm, **0 coupling-state components are above the tolerance** on the
restricted statistic. What was read for two revisions as "one component of the accepted state is
still above τ" was the instrument's own mesh change, and with the mesh put back there is nothing
above τ at all.

### 5.3 What the audit after the run now measures, and it is not nothing

The reproduction gate's position — after the whole run, which is after the output path — gets the
same treatment: its sweep is the loop's map too, while the state it sweeps from is deliberately
the state the run ended in. That makes a number that used to be trivially zero into a measurement.

*Caption: the whole-state exit-audit maximum at `after_run` on the reference arm at seed 0, from
gate G1's two captures. Before: the previous instrument, whose sweep ran on the mesh the output
path had set, so the state was already a fixed point of that map. After: the solve-phase settings
put back, so the sweep is the loop's own map on the state PROCESS wrote out.*

| configuration | before | after | argmax after | above τ |
|---|---|---|---|---:|
| `large_tokamak_nof` | `0x0.0p+0` | 6.990979e-03 (`0x1.ca292b56b673fp-8`) | `tfcoil.insstrain` | 1 |
| `low_aspect_ratio_DEMO` | `0x0.0p+0` | 7.021185e-03 (`0x1.cc23ee7f371aep-8`) | `tfcoil.insstrain` | 1 |
| `st_regression` | `0x0.0p+0` | `0x0.0p+0` | `blanket.deg_blkt_inboard_poloidal_plasma` | 0 |

**Read it the right way round.** This is not a convergence failure and it is not about the
architecture: it is the distance between **the state PROCESS writes into its output file** and a
fixed point of the map its own solve iterated, on PROCESS exactly as shipped. It is the same
0.70 % A61 §8 measured between the written `insstrain` and the solved one, expressed as a residual.
It is a direct handle on issue **I-21** — what else the output pass leaves inconsistent in the
written file — and it is now a per-run record field rather than a special study.

---

## 6. Gate GR — the compared set, its reason, and the new count

**270 values in the committed reference, 14 excluded by name with their reason, 256 compared,
0 mismatched, 20 of 20 runs reproduced, 8 of 8 teeth tripped.** The reference file is **not**
regenerated: it holds the previous revision's own numbers, and re-extracting it to remove a field
would be editing the thing being reproduced. A field leaves the comparison by being named in
`reference.FIELDS_NOT_COMPARED`, and the name, the reason and the resulting count all travel in
the gate's verdict and in every row.

*Caption: what left the compared set, and what did not. "Values" is the count over the twenty
reference runs.*

| phase | field | values | in the comparison? | why |
|---|---|---:|---|---|
| B (14 runs) | `exit_audit.residual_max_hex` | 14 | **excluded** | an instrument value, not a measurement this experiment compares on. The previous revision's optimisation-phase audit swept from the state PROCESS's output path left, on the discretisation that path had already changed; this revision's puts the data structure back to its solve-phase state first. The two numbers are made by two instruments |
| A (6 runs) | `exit_audit.residual_max_hex` | 6 | **kept, and reproduces** | that phase evaluates the model set once and never enters the output path, so there is nothing for the restore to put back and the two instruments coincide. Measured: all six reproduce bit for bit |
| both | everything else | 250 | compared | 0 mismatched |

**270 → 256.** The 14 that left are exactly the optimisation phase's residuals, one per run.

**The tooth the ruling asked for.** A reference residual doctored by one character in a copy of the
committed document is reported as **excluded with its reason**, is **not** among the mismatches,
and the run still reproduces on its 14 compared values. That is the half an exclusion has to be
shown to have: it must be distinguishable from "we compared it and it agreed". The other seven
teeth — a raised count, a doctored objective hex, a missing reference file, a missing key, a bad
name map, a composition run with one switch deliberately wrong, and per-attempt costs that do not
sum — all still make the gate refuse.

---

## 7. The gate table — what was re-made, what was reused, and why

The user reduced the run budget mid-task: instead of pressing `--gate all` from nothing, the
gates this change can reach were re-made on fresh records and the rest reuse task A52
(harness-gates)'s verdicts and records at `eb38c34a`. **The reduction is not what `--resume` would
have given** — see §7.1 — so the reuse is at the level of verdicts, stated gate by gate.

*Caption: one row per gate. "Records" is how many run records that gate read and at which commit.
A gate marked **re-made** ran on records made at this task's commit `3d64625c`; one marked
**reused** was not run and its verdict record is A52's, at `eb38c34a`, with the reason this change
cannot reach it. Every re-made gate's verdict states the commit of the records it read, which is
what `--resume` prints.*

| gate | plan | re-made or reused | records | verdict | the number |
|---|---|---|---|---|---|
| `reproduction` | GR | **re-made** | 30 at `3d64625c` | **PASS** | 20/20 runs; 270 in the reference, 14 excluded, **256 compared, 0 mismatched**; 8/8 teeth |
| `switch_neutrality` | G1 | **re-made** (after capture) | 6 at `3d64625c`, 6 at `fd480aff` | **PASS** | straddles `fd480aff` → `3d64625c`; **0 of 2 831** record values, **0 of 51 319** output-file lines; 1 626 excluded, 957 of them by the instrument change; 7/7 teeth. Re-taken after the §7.2 correction, on the same two captures and with **no run made**: the same numbers |
| `audit_restriction` | G4 | **re-made** | 18 at `3d64625c` | **PASS** | 13 doctored runs over 3 configurations; 12 compared, 0 mismatched; **6/6 teeth**, including the restore's boundary |
| `output_path` | G9 | **re-made** | 17 at `3d64625c` | **PASS** | 11 runs; **0 of 3 825** coupling-state components, **0 of 54** solve-describing values; 4/4 teeth |
| `predicate_mode` | G8 | **re-made** | 27 at `3d64625c` | **PASS** | 12 pairs; **0 of 7 852** record values, 0 of 84 output-file lines; 4/4 teeth |
| `record_completeness` | G7 | **re-made** | 2 at `3d64625c` | **PASS** | 89 declared fields in the optimisation phase, 82 in the evaluation phase; 171 compared, 0 mismatched; 9/9 teeth |
| `g0prime` | G0′ | **re-made** (no runs) | — | **PASS** | the copy's models byte-identical to `c0ae5b28` bar the one approved edit; 4/4 teeth |
| `data`, `provenance`, `rungs`, `capability`, `composition`, `run_path`, `artifacts_check` | — | **re-made** (no runs, or cheap) | — | **PASS** (7) | the promoted self-checks and artifact check |
| `prime_map` | G2 | **reused** | 12 at `eb38c34a` | PASS (A52) | the arrangement's method-level move changes nothing once the first-wall model has run — a statement about states and counts, which this change does not touch |
| `cold_chain` | G3 / G3c | **reused** | 16 at `eb38c34a` | PASS (A52) | no cut edge carries a stale value into a one-pass exit — the same |
| `entry_and_warm` | G6 | **reused** | 13 at `eb38c34a` | PASS (A52) | the entries pair and a warm arm lands — states and counts |
| `switch_composition` | G5 | **reused** | 6 at `eb38c34a` | PASS (A52) | the matrix equals the arm, composed switch by switch — a comparison of compositions |
| artifact stages (`census`, `per_run`, `derive_inputs`) | — | **reused** | 6 census records | PASS (A52) | derived artifacts, unchanged by this task |

**Also run, all at this commit:** `--measure all` (six measurement stages), `--selfcheck` (6/6
checks, every declared tooth tripped), the preflight (**READY**), `PROCESS/copy_gates.py all`
(**ALL GATES PASS**, 4/4 teeth, the only model file differing from the base being the one approved
edit `process/models/pulse.py`), and `PROCESS_diff.py --markdown` (exit 0).

**What the reused gates would and would not have caught.** Each compares states, counts or
compositions; none reads the exit audit's residual, and none of their criteria mentions a field
this change adds. What they cannot say is that *their own runs* would still pass with the new
instrument — they were not re-made. The gates that do read the audit were all re-made, and the
record contract makes the boundary visible rather than assumed: a record from the previous
instrument is **incomplete** under the current schema, so no summary can mix the two silently.

### 7.1 Why `--resume` could not do what it looks like it does

The instruction that replaced the from-scratch press assumed `--resume` would keep A52's records.
**It would not, and that is measured, not predicted.** All 156 run records under A52's gate tree
are judged incomplete by the current record contract: 152 are missing exactly
`exit_audit.instrument{,.restores,.n_restored,.n_not_restorable}`, 3 those plus `per_run_artifact`,
1 those plus `node_calls_solve_phase`. `pool.run`'s resume consults
`records.is_complete_for` → `records.missing_fields`, which reads the **current** `SCHEMA`; an
incomplete record is re-run. Pressing `--gate all --resume` over them would have re-made every one.

This is the same mechanism A52 §4.3 recorded for `per_run_artifact` against G1's trunk capture,
one schema change later, and it is not a defect: a record made by the previous exit-audit
instrument genuinely is a different population for every gate that reads the audit. Exempting the
new field from the resume contract to make the runs cheaper would be tuning a contract to get a
cheaper answer, so it was not done. What the reduction bought instead is stated above: **47 gate
runs and 6 census records not re-made.**

### 7.2 The instrument exclusion, measured by where its leaves sit

*Caption: every record leaf gate G1's instrument-change group removed from the comparison, counted
by where it sits, over the gate's 6 run pairs. The group's claim is that it takes out the audit's
residual and the instrument's own account of itself **and nothing else**; this is the measurement
of that claim rather than the assertion. From `--measure exclusion_review`.*

| prefix | leaves |
|---|---:|
| `exit_audit.instrument` | 510 |
| `exit_audit.` (the residual and what it determines) | 438 |
| `audit_position_note` | 6 |
| `audit_snapshot.installed` | 3 |
| **anywhere else** | **0** |
| **total** | **957** |

The 510 under `exit_audit.instrument` are the new block itself, absent on the earlier side. The
438 are the residual and the summaries it determines, named leaf by leaf per ruler rather than by
excluding the blocks that hold them — which would have taken a further **75 leaves per
optimisation record** out of the comparison (the tolerance, the ruler's name, the restriction's
population and digest), none of which the instrument moves. Measured: 2 831 values compared with
the leaves named against 2 609 with the blocks excluded.

**The same rule applied to `audit_snapshot`, on review.** The group first named the whole
`audit_snapshot` block. The orchestrator re-compared the six pairs with that name and
`audit_position_note` lifted out and found that **only two leaves differ across this straddle**:
`audit_position_note` (the rewritten sentence, 3 pairs) and `audit_snapshot.installed`
(`False` → `True`, 3 pairs). So the block exclusion hid nothing here — but it is a block exclusion
of exactly the kind decision 5 rejects, and on a later straddle it would hide
`audit_snapshot.positions.*.components_sha256`, the coupling-state digest at each snapshot
position, which is a **behaviour witness**: it says the driver snapshotted the same state at the
same places. The group now names **`audit_snapshot.installed`** alone, for the one reason that
flips it — the hook is installed at every audit position now, because the whole-structure snapshot
is needed even where the coupling-state one is not — and the positions, their component counts and
their digests stay in the comparison. The leaf counts above are unchanged by the correction, which
is the point: it costs this pairing nothing and buys every later one the digests.

*Caption: the same two names as the exclusion review tabulates them after the correction, over
G1's 6 pairs. "Group" is which condition excludes the name; "leaves" is how many record leaves it
covers on each side.*

| name | group | leaves before | leaves after | verdict at this pairing |
|---|---|---:|---:|---|
| `audit_snapshot` | excluded only where one side lacks the field | 6 | 75 | EXCLUDED — one side lacks them |
| `audit_snapshot.installed` | excluded only where the instruments differ | 3 | 3 | EXCLUDED — the two captures' instruments differ |

The first row is the pre-existing conditional exclusion doing its own work: the 69 leaves the
after side has and the before side does not are one-sided, and they return to the comparison of
their own accord the moment both sides carry them. The tooth shows the effect directly — in its
synthetic comparison, where both sides carry the whole block, the instrument rule now removes
**234 leaves instead of 258**, and **24 more values are compared**.

---

## 8. Nothing left to attribute

A61's diagnosis stage is this task's gate, re-run in full at `3d64625c`: 9 runs plus the 2-run
inertness check, `census`, `runs`, `inertness`, `report`.

**`nothing left to attribute: PASS — 9 of 9 rows`, 9 runs declared, 0 missing.** Each row requires
three things at once: the "put back only `tfcoil.n_rad_per_layer`" and "put back nothing" rows must
be the same sweep; the candidate must no longer be among the fields the output path left changed
when the sweep begins; and `tfcoil.insstrain` must sit at exactly `0x0.0p+0` wherever it is a
continuous coupling-state component.

*Caption: the stage's own leave-one-out table, re-taken. Every cell is the maximum scaled residual
of one further full sweep on the frozen ruler. The three columns that used to disagree now
coincide in every row, which is what "nothing left to attribute" means.*

| run | as found (put back nothing) | only the candidate put back | every other field put back | `tfcoil.insstrain`'s own residual |
|---|---|---|---|---|
| `large_tokamak_nof/B0/seed000` | `0x1.94d12c769164ep-37` | same | same | **`0x0.0p+0`** |
| `large_tokamak_nof/BR/seed000` | `0x1.94d0e2a68b136p-37` | same | same | **`0x0.0p+0`** |
| `large_tokamak_nof/B0/seed001` | `0x1.b49f565f80d44p-37` | same | same | **`0x0.0p+0`** |
| `large_tokamak_nof/B1/seed000` | `0x0.0p+0` | same | same | **`0x0.0p+0`** |
| `large_tokamak_nof/B3/seed000` | `0x1.1089de0293f4bp+0` (112 above τ: the per-run deferred nodes' own outputs) | same | same | **`0x0.0p+0`** |
| `low_aspect_ratio_DEMO/B0/seed000` | `0x0.0p+0` | same | same | **`0x0.0p+0`** |
| `low_aspect_ratio_DEMO/BR/seed000` | `0x0.0p+0` | same | same | **`0x0.0p+0`** |
| `low_aspect_ratio_DEMO/B3/seed000` | `0x1.00000e47dfe8dp+0` (112 above τ, the same reason) | same | same | **`0x0.0p+0`** |
| `st_regression/B0/seed000` | `0x1.bc16e29405387p-45` | same | same | — (the component is `None` there) |

**The difference set is empty where it used to hold 86 names.** The stage's own census of what
changed outside the coupling state between the entry to the output path and the moment the audit
sweeps now reads **1 field on 8 of 9 runs and 0 on the ninth** — `numerics 1` every time, the call
counter the rule holds back — against 83–86 fields before, and `tfcoil.n_rad_per_layer` is **not
among them** on any run. A61's headline mechanism has nothing left to act on.

**And the whole-structure restore's own accounting, per run:** the coupling-state restore is
bit-exact on **11 of 11** sweeps that take one, on 9 of 9 runs; the put-back restores are bit-exact
**4 of 4**; the two fields that could never be put back are named in every row —
`globals.fileprefix` (not rebuildable) and `numerics.name_xc` (does not read back equal) — and
neither is read by a model, neither is in any run's derived set, and the record says so rather than
claiming 2 288 of 2 288.

---

## 9. The runs this task made

*Caption: PROCESS runs started through `harness/pool.py`, every one `--run-kind gate`; no campaign
record was made and `EXECUTION_APPROVED` stayed `False`. "Final population" is the records on disk
that every number in this report is read from; they are all at one commit, which each gate's
verdict states.*

| | runs |
|---|---:|
| final population, all at `3d64625c` | **116** |
| — gate GR | 30 |
| — gate G8 (`predicate_mode`) | 27 |
| — gate G4 (`audit_restriction`) | 18 |
| — gate G9 (`output_path`) | 17 |
| — A61's diagnosis stage (9 + the 2-run inertness check) | 11 |
| — gate G1's "after" capture | 6 |
| — the shared cold-flat entry references | 3 |
| — gate G7 (`record_completeness`) | 2 |
| — the lifted input files' baseline evaluations | 2 |
| reused, at `eb38c34a` (task A52's) | **47** + 6 census records |
| gate G1's "before" capture, at `fd480aff`, never re-made | 6 |
| superseded during development and discarded | about 70 |

The superseded runs are two G1 "after" captures re-made after defects were found and fixed (the
`numerics` rewind, §3.4, and the round-trip census on the evaluation path), one complete
reproduction-gate run superseded by a later commit, an aborted from-scratch gate press, and three
hand smoke runs. None of their numbers is cited anywhere.

**Wall clock is context and nothing rests on it** (trap T5). The whole re-run chain — GR, G1, G4,
G9, G8, G7, the cheap gates, the measurements, the artifacts, the self-check, the preflight, the
copy gates and the diff view — took about 25 minutes at three workers on this machine, and the
diagnosis stage about 3 minutes more. Every acceptance quantity above is a count or a
bit-comparison.

---

## 10. Autonomous decisions, each with the way back

*Caption: one row per decision taken without asking. "Reversal" is what undoing it costs and what
would have to be re-run.*

| # | decision | why | reversal |
|---|---|---|---|
| 1 | The audit position **after the run** gets the restore too, so its sweep is the loop's map as well | ruling D25 says the audit's sweep must evaluate the loop's own map, and it says "both audit positions". The position's *state* is still the state the run ended in — only what the models read around it is put back | pass `restore_from_position=None` for that position in `optimise.py`. Its residual returns to `0x0.0p+0` on the reference arm and the finding of §5.3 disappears with it |
| 2 | The derived set **excludes the coupling state's own components**, whose restore the audit position governs | restoring them at `after_run` would silently turn that position into the declared one | drop the `coupling_names` filter. The two audit positions then measure the same thing and one of them stops meaning anything |
| 3 | **One namespace** — `numerics` — is held back from the restore, by a named rule with its reason, and what it holds back is reported per run | the gate measured the alternative: restoring it rewound PROCESS's own call counter and moved `n_model_calls`, a value gate GR compares, by two (§3.4) | delete `NAMESPACES_THE_AUDIT_DOES_NOT_RESTORE`. `n_model_calls` then differs from the previous revision's on every optimisation record and gate GR fails on it |
| 4 | Gate GR keeps the **evaluation phase's** audit residual and drops only the **optimisation phase's** | the ruling's own reason — "the previous revision's instrument did not restore the output path's mesh" — does not apply to a phase that never enters the output path, and the six evaluation-phase residuals reproduce bit for bit after the change (measured, §6). Dropping a comparison that works would weaken the gate for a reason that is not about it | add `exit_audit.residual_max_hex` to `reference.FIELDS_NOT_COMPARED["A"]`. GR's compared set falls 256 → 250 and six bit-comparisons of the evaluation phase's accuracy leave the gate |
| 5 | G1's instrument exclusion names the **leaves the residual determines**, generated per ruler, rather than the audit blocks that hold them | excluding the blocks hid 75 further leaves per optimisation record — the tolerance, the ruler's name, the restriction's population and digest — none of which the instrument moves. Measured: 2 609 compared values with the blocks excluded against 2 831 with the leaves named | replace the generated table with `exit_audit.frozen` / `exit_audit.mixed` / `exit_audit.brief` / `exit_audit.restricted`. G1 then compares 222 fewer values and says so |
| 6 | The whole-structure snapshots stay **in memory** and never enter the run record | two positions × 2 288 fields per record is a file every gate would walk value by value, and the record already carries the restore's counts and names | write them beside `y_<position>.json`. Every gate's denominator grows by some thousands of leaves that are a copy of the state, not a measurement of it |
| 7 | The diagnosis trace's "as found" mark moved **inside** the audit, to the moment its sweep starts | otherwise A61's leave-one-out pair would keep diagnosing the *old* instrument, and the check the ruling asks for — that the pair has nothing left to attribute — could not be made | revert the `on_ready_to_sweep` callback. The diagnosis stage then measures a state the record's audit no longer sweeps |
| 8 | `records.FORMAT` and `harness.__version__` are **not** bumped | the change is additive and self-describing: `exit_audit.instrument.restores` says which instrument made a record, which is exactly what a version bump would have been for, and it is checkable rather than declared | bump both, and add two more named G1 exclusions for no further information |

---

## 11. Handover

### To A53 (harness-tally)

* **Record fields that changed.** `exit_audit.instrument` is new on every finished record, with
  `restores`, `n_restored`, `n_not_restorable` and the names beside them; `audit_snapshot` now
  carries `data_structure_positions` and is a block on **every** optimisation record, including
  runs at the `after_run` position where it used to be a sentence saying the hook was not
  installed. Nothing was removed and nothing was renamed.
* **The caption rule the queue asks for, stated.** Every table of residuals must name the
  **instrument version** beside the audit position, because the two together fix what the number
  means. Concretely: *"exit-audit residual on the frozen ruler, at `entry_to_write_output_files`,
  instrument `whole_data_structure_derived_set`"*. A table that mixes two instrument versions in
  one column is reporting a change of instrument as a change of accuracy, which is the same trap
  as mixing the two rulers (improvement item 5a) and the same trap as mixing the two audit
  positions (A57's rule). The stamp is in the record; the tally must read it and refuse a column
  whose rows disagree on it, exactly as it refuses a column that mixes rulers.
* **Numbers that moved.** Every published exit-audit residual changes. The restricted statistic on
  the two pulsed configurations falls from ~7e-3 with `tfcoil.insstrain` as argmax to the values
  in §5, with 0 components above τ. Any V3-to-V4 residual comparison must say which instrument
  each side used.

### To A55 (harness-smoke)

* **G9's claim and I-21.** The `after_run` audit now measures something it did not measure before:
  how far the state PROCESS *writes out* is from a fixed point of the loop's own map. On the
  reference arm on `large_tokamak_nof` that is §5.3's number, and its argmax is `tfcoil.insstrain`.
  That is a direct handle on issue **I-21** — what else the output pass leaves inconsistent in the
  written file — and it is now a per-run record field rather than a special study.
* The instrument is inert where there is no output path: the evaluation phase's records carry
  `exit_audit.instrument.restored = false` with the reason, and their residuals are unchanged
  (measured: GR's six evaluation-phase residuals reproduce bit for bit).

---

## 12. Limits

* **The "before" half of every straddle is quoted, not re-derived.** Gate G1's "before" capture is
  the orchestrator's, at trunk `fd480aff`, and a capture made at an earlier commit cannot be
  re-made. The before columns of §5's audit tables are quoted from A57 (driver-output-path) §10.3
  and A52 (harness-gates) §6.4, whose own run records no longer exist in this worktree; A61
  (insstrain-diagnosis) §9.1 reproduced them exactly with a third instrument, which is the only
  independent check this report has of them.
* **One seed on every row.** Seed 0 except where a row says otherwise. These are gate runs, not a
  distribution, and none is claimed to be one.
* **The restore is not provably total, and the record says so per run.** Two fields of the 2 288
  cannot survive a round trip — `globals.fileprefix`, carried as a bare `repr`, and
  `numerics.name_xc`, which does not serialise back equal — and the round-trip census names both
  in every record. Neither is read by a model and neither is in any run's derived set. The claim
  the residual rests on is not "everything was restored" but the census of the state the sweep
  starts from, which is 0 fields differing outside the coupling state at the declared position.
* **One namespace is held back by rule** (§3.4), and the fields it holds back are named per run.
  Today that is one field on the runs measured; if PROCESS's output path ever changed another
  `numerics` field the record would name it and nobody would have to notice.
* **No conclusion here rests on a timing**, and none is quoted as evidence.

---

## 13. What the plans, the queue and the improvement list should gain

Not edited here — those documents are shared. The exact text they should take:

* **Experiment plan §3.3**, at the end of the `MDA_Output` paragraph, after the D25 sentence:
  *"Landed with A62 (exit-audit-restore): the audit snapshots the whole data structure at both of
  the driver's positions and restores a derived set before its sweep, at both audit positions; one
  namespace (`numerics`, the optimiser's own accounting) is held back by a named rule and what it
  holds back is named per run. Measured at the declared position: 0 of 31 records have a component
  above τ, and `tfcoil.insstrain` sits at exactly `0x0.0p+0` in every arm on both pulsed
  configurations."*
* **Experiment plan §7.1 / harness plan §7.1 (the GR compared-field list):** *"**20 entries, 270
  values, of which 256 are compared**: the optimisation phase's `exit_audit.residual_max_hex` (14
  values) is excluded by name with its reason from A62 (exit-audit-restore) onward — it is an
  instrument value and the previous revision's instrument did not restore the output path's mesh.
  The evaluation phase's six are kept and reproduce bit for bit. The reference is not regenerated;
  `harness/reference.py` exports the exclusion as `FIELDS_NOT_COMPARED`."*
* **Harness plan, Appendix A, amendment 15**, at this merge: D25 implemented; G1's exclusion set is
  **127 declared entries in three groups over 126 distinct names** (`audit_position_note` is in
  two) — 36 structural, 34 conditional on the field's own presence, 57
  conditional on the two records' instrument stamps — with the third group's leaves measured by
  prefix (957 leaves, 0 outside the exit audit and its stamp); the record contract now makes a
  record from the previous instrument **incomplete**, which is why `--resume` cannot reuse one
  (§7.1) and is worth stating as a standing property rather than rediscovering.
* **Queue, decision register:** D25 is discharged. The rule the harness plan's amendment 14 states
  — *snapshot the whole data structure and restore a derived difference set before any sweep taken
  after an output call; count and name what cannot be restored* — now has an exception with a
  reason and a tooth: **the namespace holding the run's own accounting is not restored**, because
  an instrument that rewinds a run's counters publishes its own bookkeeping as the run's cost.
* **Improvement list item 11**, already closed as a convergence finding at A61's merge: it can now
  record that the statistic it was about reads **0 components above τ** everywhere.
* **Issue I-21** gains a handle: the `after_run` audit residual is now a per-run measurement of how
  far the written state is from a fixed point of the loop's map (§5.3), 6.99e-03 and 7.02e-03 on
  the two pulsed configurations on the reference arm.

---

## 14. Change log

*Caption: append-only. One row per change to this document or to the code it reports on.*

| date | change |
|---|---|
| 2026-09-11 | Created. `harness/data_structure.py` added (the three functions moved out of A61's gate instrument); the exit audit snapshots and restores the whole data structure at both audit positions, with a derived set and a named namespace rule; `records.SCHEMA` gains four fields; gate G1 gains a third exclusion kind conditional on the two records' instrument stamps, with a tooth and a prefix census; gate GR's compared set loses the optimisation phase's audit residual with its reason and a tooth; gate G4 gains a tooth that measures and flips the restore's boundary; A61's diagnosis stage gains the "nothing left to attribute" check. Gates re-made at `3d64625c`: GR, G1, G4, G7, G8, G9 and the no-run gates, all PASS; G2, G3/G3c, G5, G6 and the artifact stages reuse A52's verdicts at `eb38c34a`. |
| 2026-09-11 | **A defect gate G1 caught, fixed on the branch**: restoring every field outside the coupling state rewound `numerics.n_model_calls`, moving `n_model_calls` — a value gate GR compares — by two on the reference arm. `child.NAMESPACES_THE_AUDIT_DOES_NOT_RESTORE` holds that namespace back by a named rule; what it holds back is named per run and a G4 tooth measures the boundary. |
| 2026-09-11 | **Correction at the orchestrator's review, no run made.** Gate G1's instrument-change group named the whole `audit_snapshot` block; it now names `audit_snapshot.installed` alone. The block exclusion hid nothing on this straddle — measured by the orchestrator, only `audit_position_note` and `audit_snapshot.installed` differ once it is lifted — but it would have hidden `audit_snapshot.positions.*.components_sha256`, a behaviour witness, on a later one. `--gate switch_neutrality --resume` (both captures reused, 0 runs) PASS, 0 of 2 831 values and 0 of 51 319 lines, 7/7 teeth; `--measure exclusion_review` PASS with the two names tabulated separately. The leaf census is unchanged at 957 with the `audit_snapshot` line reading 3, which are the `installed` leaves; the tooth's own comparison excludes 234 leaves instead of 258. |
| 2026-09-11 | **Run budget reduced by the user mid-task.** The from-scratch `--gate all` press was stopped and replaced by re-making only the gates this change can reach, reusing A52's verdicts for the rest. Measured and reported: `--resume` could not have reused A52's records, because the record contract makes them incomplete (§7.1). |
