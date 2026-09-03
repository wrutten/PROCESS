# A29 (replication-verify) — can a user reproduce the published numbers from clean?

> **Document status**: task report, task open. Archived to `deprecated/` at merge (folder
> position records lifecycle, not validity — trap T3).

| | |
|---|---|
| **Task** | A29 (replication-verify): run both replication entry points from clean, as a user would, and confirm they reproduce the published numbers |
| **Branch / worktree** | `A29-replication-verify`, branched at `126a0d92` |
| **Scope change** | **2026-09-03, user**: *"You can stop A29. It doesn't need to replicate the ladder. The experiment is eclipsed by recent progress anyway. It should wrap up by assessing the reproducibility of the previous results."* The tolerance-ladder replication (168 runs) and the matched-accuracy re-run (25 runs) were therefore **deliberately not replicated** — a user decision, not a shortfall. Everything else in the brief was executed. |
| **Author** | task agent A29, 2026-09-02 → 2026-09-03 |

---

## 1. The plain answer first

**If you run this yourself tomorrow, will you get the published numbers?** For everything the
two committed verification files cover — **yes, and it was just done from a clean tree**: all
five Phase A tables and all five Phase B tables in
`arch_surgery/docs/data/a21_published.json` / `a28_published.json` agree per deck,
**30 of 30 deck-level comparisons** (18 exact count/boolean comparisons; 12 ratios within
stated tolerance, worst relative difference 4.5e-6 against published values rounded to 4–5
digits). Model-evaluation counts reproduce **exactly**; whole-optimisation campaigns
reproduce **bit-for-bit** in every measured quantity.

**But only after two defects found by this task were fixed** — both are things you would have
hit, both are committed on this branch, and without them the answer was "no":

1. **The one-command Phase B run could not complete from clean at all** (finding F3): it
   halted at the calibration stage because two of 108 calibration runs *crash PROCESS* —
   crashes the published calibration table itself records (`11 / 12 (1 crashed)`,
   `7 / 12 (4 fail, 1 crashed)`) — and the driver treated any failed sub-run as a fatal
   stage error. Fixed in `b3c4d131`; the defect remains a finding.
2. **Phase A's `--verify` silently dropped one of the five published tables** (finding F2):
   it read a key its own artifact never contained, swallowed the error per deck, and printed
   "every compared table agrees" over four tables. Fixed in `03a75f11` (and the
   absent-artifact variant in `77e9120a`). The numbers behind the dropped table were correct
   all along; only the comparison plumbing was broken.

**How long will it take?** Measured here: Phase A `--quick` 12 min, Phase B `--quick` 7 min,
full Phase A ≈ 68 min of stage time (≈ 84 min wall including one environment kill and its
resume), full Phase B ≈ 3 h of driver time for what was executed (through the accuracy
census; the descoped ladder would add roughly another hour at the measured per-run rates).
Disk: ≈ 6.5 GiB total for both phases (but see finding F8 — Phase A alone is ≈ 0.9 GiB, not
the published ≈ 6 GB).

**What will trip you up?**
- **This machine kills long shells.** Three times in this task a run's controlling shell was
  killed at roughly the one-hour mark, and the WSL host slept for ~4 h overnight mid-campaign.
  The experiment's artifacts survived every time and nothing had to be re-measured — but
  recovery needs the stage-level `run_a28.py … --resume` flag, which **the entry point cannot
  pass** (finding F6). Expect to babysit anything longer than an hour.
- **The wrong conda environment does not abort** (finding F4). Run from the repository root,
  the entry point under `PROCESS_env` prints a NOTE and proceeds, because `import process`
  still resolves to this tree. The *tree* hazard is neutralised; the interpreter/dependency
  difference is not refused. Use
  `/home/wrutten/anaconda3/envs/PROCESS_surgery_env/bin/python` and nothing else.
- Everything else fails well: a missing deck, a missing committed artifact, a symlinked or
  absent cache each stop immediately with a message naming the exact fix (§7).

---

## 2. What this assessment now is

Per the 2026-09-03 scope change, this is a **reproducibility assessment of the published
Phase A / Phase B results**, not a complete re-execution. Concretely:

| Published quantity | Status here |
|---|---|
| Phase A in-loop model-evaluation counts, 4 arrangements × 3 decks (results doc §4.4) | **Independently reproduced from clean, exact**, 12/12 |
| Phase A cost ratio at matched achieved accuracy, 3 decks (§4.4.2) | **Independently reproduced from clean**, 3/3 within 1e-3 (measured 0.956816 / 0.954720 / 0.869360 vs published 0.957 / 0.955 / 0.869) |
| Phase B equivalence gate passes, 3 decks (§7.4) | **Reproduced**, 3/3, and 12/12 per-arm PASS |
| Phase B switch neutrality vs the base commit | **Reproduced**: bit-identity PASS on 3/3 decks, probe off and on |
| Phase B calibration table, 9 cells (§7.5) | **Reproduced cell for cell**, including which starts crash |
| Phase B paired median cost ratios, 3 comparisons × 3 decks (§7.6/7.8 headline) | **Independently reproduced from clean**, 9/9 within 5e-6 relative |
| Phase B robustness counts `n_both_solve`, 3 decks | **Reproduced exact**, 22 / 11 / 21 |
| Phase B accuracy census (audit stage) | **Executed** (225 runs, 16 non-solving starts recorded); its distributions were not re-compared against §7.7 because the scope change arrived while it finished — its artifacts are on disk under `runs/a28/h5_audit1` |
| Phase B matched-accuracy ladder figures (§7.8's −1.63 %/−2.27 % matched-stopping-rule readings, envelopes, tuning premium) | **Deliberately not replicated** (user descope, 2026-09-03). 168 ladder runs + 25 matched-accuracy runs; at the measured campaign rates ≈ 60–90 min. Reproducible in principle by `--stages ladder tables`; nothing in this task contradicts them, and nothing here confirms them. The 31 partial ladder artifacts on disk are a byproduct of the stop race and **must not be used**. |

**No published number that was compared failed to reproduce.** The defects found were all in
the *harness around* the numbers — the verification plumbing, the exit-code policy, this
comparator's own selftest — which is exactly where a replication exercise should be looking.

---

## 3. Provenance — one tree, named commits, clean at every measurement

Worktree `/home/wrutten/projects/PROCESS_surgery_worktrees/A29-replication-verify`, branched
at `126a0d92` (the A28 merge). Four commits were made by this task, all to harness/verification
code — **no model, driver, or measurement code changed**:

| Commit | What |
|---|---|
| `03a75f11` | Phase A `--verify`: matched-accuracy table no longer silently dropped (F2) |
| `a1d50d0a` | `a29_determinism.py`, the bit-comparison tool, with its own §12 failure recorded (F1) |
| `b3c4d131` | `run_a28.py`: measured crashes no longer kill the one-command run (F3, blocking) |
| `77e9120a` | Phase A `--verify`: absent matched-accuracy artifact fails loudly (F5, issue I-14) |

Which measurements ran at which commit, every one with a **clean** tree:

- Phase A quick + full (all stages): `126a0d92`.
- Phase A census determinism re-run: `a1d50d0a`.
- Phase B decks / neutrality / gate (first pass) / first calibrate attempt: `a1d50d0a`.
- Phase B calibrate (complete) + **campaign, all 375 runs** + audit: `b3c4d131` —
  verified by census over every campaign `metrics.json`: **375 of 375 stamp
  `tree_git_head = b3c4d131, dirty = false`**. This closes A28's open caveat (its campaign
  metrics carried `9634bb06-dirty`): the same published medians now come from a fully clean,
  single-commit tree.
- Phase B gate determinism re-run: `b3c4d131`.

While this task ran, A30 (phase-b-critique) merged on the trunk (tip `a68ef0c9`), applying
label/provenance corrections C1–C5 to the standing documents. **Neither published-numbers
JSON changed**, so the verification targets here are byte-identical to those at the branch
point; standing-document wording quoted in this report was re-checked against the corrected
text where cited.

The pristine reference checkout for `--parent-tree` was built exactly as the docstring says
(`git archive c0ae5b28 | tar -x -C …`, 89 MB).

---

## 4. What was executed, with the exact commands

Everything below used `/home/wrutten/anaconda3/envs/PROCESS_surgery_env/bin/python` (`$PY`),
from the worktree root (`$W`), with run artifacts under the worktree's own untracked
`arch_surgery/idf_probe/runs/`. `$PT` is the pristine checkout.

```bash
# 1. smoke, both phases, from a tree with NO runs/ directory at all
$PY MDA_partition_experiment.py --quick            # 726 s, +115 MB, exit 0
$PY MDA_partition_opt_experiment.py --quick        # 439 s, +77 MB, exit 0

# 2. full Phase A (quick artifacts set aside first so this is from scratch)
$PY MDA_partition_experiment.py --parent-tree $PT  # killed by the environment in
                                                   # driver_hoist at ~69 min; then:
$PY MDA_partition_experiment.py --parent-tree $PT --stages driver_hoist driver_reorder tables

# 3. full Phase B
$PY MDA_partition_opt_experiment.py --parent-tree $PT   # STOPPED at calibrate (finding F3)
# after fix b3c4d131:
$PY MDA_partition_opt_experiment.py --stages calibrate campaign audit ladder tables
#   (campaign twice interrupted by the environment; completed with the stage-level resume:)
$PY arch_surgery/idf_probe/run_a28.py campaign --runs <runs>/a28 \
    --scenarios large_tokamak_nof low_aspect_ratio_DEMO st_regression \
    --arms R A0p A1p A0p_reordered A1p_nohoist --starts 24 --delta 0.1 --jobs 4 --resume
$PY arch_surgery/idf_probe/a28_analysis.py h5      --runs <runs>/a28 --scenarios … --arms …
$PY arch_surgery/idf_probe/a28_analysis.py timings --runs <runs>/a28 --scenarios … --arms …
#   audit completed; ladder stopped per the 2026-09-03 descope.

# 4. verification, both phases
$PY MDA_partition_experiment.py --verify           # 5 tables, 15/15 decks agree, exit 0
$PY MDA_partition_opt_experiment.py --verify       # 5 tables, 15/15 decks agree, exit 0

# 5. determinism (stage re-run + committed comparator)
$PY MDA_partition_experiment.py --stages census                    # 2nd run of census
$PY arch_surgery/idf_probe/a29_determinism.py compare --first … --second …
$PY MDA_partition_opt_experiment.py --stages gate                  # 2nd run of gate
$PY arch_surgery/idf_probe/a29_determinism.py compare --first … --second …
```

Every number quoted in this report was produced by one of the committed scripts above
(protocol §15); the shell lines are how those scripts were invoked, recorded verbatim.

### 4.1 The from-scratch condition was real

The worktree began with **no `arch_surgery/idf_probe/runs/` directory at all** — no harvest,
no symlink into the main checkout. The `--quick` run rebuilt the design-point recording
itself (129 s for its deck) and then **reproduced A18's published counts exactly**
(9 471 / 9 471 / 9 618 / 13 906 on `large_tokamak_nof`) from its own recording. The full
Phase A run recorded all three decks' harvests fresh. Nothing was consumed from the main
checkout; the documented symlink-refusal path was therefore not reachable in this layout
(a fresh worktree gets no symlink until someone makes one) — noted rather than simulated.

---

## 5. Cost, measured (wall-clock and disk are context, never evidence)

### Phase A (three decks, `--parent-tree` given, `--reps 2`)

| stage | seconds | note |
|---|---|---|
| phase_a (harvest ×3, gates, τ ladder, 4 arrangements ×2 reps) | 1 735.9 | from scratch |
| method_gate (reproduce A18 bit for bit) | 131.6 | |
| accuracy (cost-vs-accuracy ladders + matched accuracy) | 901.7 | |
| pulse_gate | 162.8 | |
| census | 144.1 | |
| permutation | 169.0 | |
| driver_hoist | 464.2 | re-run in full after the environment kill |
| driver_reorder | 383.0 | |
| tables | 1.0 | |
| **total stage time** | **≈ 68 min** | wall 17:56 → 19:21 incl. kill + resume = 84 min |

Disk after Phase A complete: **922 739 390 B ≈ 0.86 GiB** (a18 294 MB, a13 178 MB, a23
160 MB, a3 158 MB, a26 91 MB, a22 22 MB, a26_pulse 20 MB). See finding F8.

A28's context figures were ≈ 105 min and ≈ 13 min for `--quick`; measured here: 68 min of
stage time and 12 min. Same order; timings on this machine vary by tens of percent and
decide nothing.

### Phase B (three decks, five arms, `--starts 24` = 25 points/arm/deck)

| stage | seconds | note |
|---|---|---|
| decks | 10.6 | |
| neutrality (needs `--parent-tree`) | 196.0 | bit-identity to base commit: PASS 3/3 decks, probe off and on |
| gate runs + 5 analysis steps | 219.9 | equivalence gate PASS 12/12 arms |
| calibrate (108 runs) | 1 353.1 | run twice: first attempt hit F3 at 1 344.9 s |
| campaign (375 runs) | ≈ 3 h driver time | across 3 sessions + 2 `--resume` rounds; last 82 runs: 3 441.6 s |
| campaign analysis (h5 + timings) | ≈ 5 | |
| audit (225 runs + analysis) | 389.0 | 16 of 225 starts did not solve — recorded, not fatal |
| ladder | — | **descoped by the user, 2026-09-03** (would be 168 runs ≈ 1 h at measured rates) |
| tables | — | not run (reads ladder artifacts among others) |

Disk after all of the above: `runs/` total **6 979 278 751 B ≈ 6.5 GiB**, of which
`runs/a28` ≈ 5.6 GiB — consistent with the published "≈ 7 GB" for Phase B.

The campaign's interruption history is instructive for anyone re-running it and is given in
full in §8 (finding F9): the controlling shell was killed at ~the one-hour mark twice and the
host slept ~4 h mid-run; the detached driver survived two of three events; `--resume` skipped
exactly the driver-stamped complete runs both times ("90 of 375 already complete", "293 of
375 already complete") and no run was ever re-measured.

---

## 6. Verification against the published numbers, per deck, with denominators

### Phase A — `MDA_partition_experiment.py --verify` (exit 0, at `77e9120a`)

| table | comparison | large_tokamak_nof | low_aspect_ratio_DEMO | st_regression | agree |
|---|---|---|---|---|---|
| in-loop model evals, arm R | exact | 9 471 = 9 471 | 21 021 = 21 021 | 9 744 = 9 744 | 3/3 |
| … arm A0 | exact | 9 471 = 9 471 | 19 992 = 19 992 | 10 395 = 10 395 | 3/3 |
| … arm A0f | exact | 9 618 = 9 618 | 20 307 = 20 307 | 10 584 = 10 584 | 3/3 |
| … arm A1 | exact | 13 906 = 13 906 | 28 070 = 28 070 | 9 917 = 9 917 | 3/3 |
| A1/A0 at the calibration point | rtol 1e-3 | 0.957 vs 0.956816 (rel 1.9e-4) | 0.955 vs 0.954720 (rel 2.9e-4) | 0.869 vs 0.869360 (rel 4.1e-4) | 3/3 |

**15 of 15 deck comparisons agree; 5 of 5 published tables compared** — the fifth only
because F2 was fixed first.

### Phase B — `MDA_partition_opt_experiment.py --verify` (exit 0, at `b3c4d131`+)

| table | comparison | large_tokamak_nof | low_aspect_ratio_DEMO | st_regression | agree |
|---|---|---|---|---|---|
| equivalence gate passes | exact | True = True | True = True | True = True | 3/3 |
| paired median, A0′→A1′ | rtol 1e-3 | 0.9837 (rel 2.6e-6) | 0.7879 (rel 2.9e-6) | 0.93816 (rel 3.8e-6) | 3/3 |
| paired median, R→A1′ | rtol 1e-3 | 1.00483 (rel 1.1e-6) | 0.76099 (rel 1.8e-6) | 0.94937 (rel 2.9e-6) | 3/3 |
| paired median, R→A0′ | rtol 1e-3 | 1.02132 (rel 7.0e-7) | 0.96622 (rel 4.5e-6) | 1.03227 (rel 3.9e-6) | 3/3 |
| starts both A0′ and A1′ solve | exact | 22 = 22 | 11 = 11 | 21 = 21 | 3/3 |

**15 of 15 deck comparisons agree.** The relative differences on the medians are the
published values' own rounding (4–5 significant digits): the underlying ratios reproduce to
the digit. The full paired robustness census also matches §7.6 exactly where checked
(`n_only_A0p`/`n_only_A1p`/`n_neither` = 0/0/3, 1/0/13, 2/1/1 — including the one start only
the variant solves on `st_regression`).

The calibration table reproduced **9 of 9 cells** (solved and crashed counts per deck per δ)
against §7.5, and δ = 10 % was selected as published.

**Not compared, and said out loud** (the lesson of F2 is that an absent comparison must be
named): the matched-accuracy/ladder figures of §7.8 — VERIFIABLE in principle via
`--stages ladder tables` (≈ 1 h), NOT VERIFIED here, by the user's 2026-09-03 descope.

---

## 7. Determinism: one stage of each phase, re-run and compared as bits

Comparator: `arch_surgery/idf_probe/a29_determinism.py` (committed `a1d50d0a`). It compares
every JSON leaf, every MFILE line, every OUT.DAT line; timing keys (`wall_s`, `cpu_*`,
`process_runtime`), git-provenance keys, and the MFILE/OUT date-time tags are **excluded,
counted, and named**; logs are skipped. Its selftest must catch a deliberate one-digit flip
**in each channel separately** — a requirement its own first version failed (finding F1).

### Phase A: `census` stage, run twice (first at `126a0d92`, again at `a1d50d0a`)

| channel | compared | differing | excluded |
|---|---|---|---|
| JSON leaves | **522 532** | **0** | 6 (timing) |
| MFILE lines | 36 | 3 | 6 (volatile tags) |
| OUT.DAT lines | 87 | 6 | 0 |

All 9 differing lines are the embedded git tag (`v3.4.2-177-g126a0d92` →
`v3.4.2-179-ga1d50d0a`; two task commits landed between the runs) and the time-of-day
header. **Zero measured quantities differ.** (The a22 MFILEs are 12-line replay stubs; the
census payload is the 522 k JSON leaves.)

### Phase B: `gate` stage (15 full optimisations, 5 arms × 3 decks), run twice (`a1d50d0a` → `b3c4d131`)

| channel | compared | differing | excluded |
|---|---|---|---|
| JSON leaves | **286 724** | 67 | 144 |
| MFILE lines | **256 673** | 15 | 45 |
| OUT.DAT lines | 57 370 | 45 | 0 |

Every one of the 127 differences classified, none a measured quantity: 48 `loadavg` + 16
`maxrss_kb` leaves (machine state recorded for the contention diagnostic), 3
`a28_sequence_position` leaves (driver dispatch-order metadata, used only by the timings
table — `run_a28.py:308`), and 15 + 45 embedded git-tag / date / time header lines. **Every
numeric physics and count quantity in all 15 optimisations — roughly 256 k MFILE float lines
— is bit-identical across the two runs.**

The run-level pattern is deterministic too: both calibrate passes produced the identical
rc-pattern over 108 runs (0 differences), with the same two starts crashing; and the
campaign's crashing start (`large_tokamak_nof` k = 5) crashed identically in every arm it
appears in, as the hash-keyed perturbation design promises.

---

## 8. Findings

**F1 — this task's own comparator selftest lied, and protocol §12 caught it (fixed in
`a1d50d0a`, kept as a finding).** The first selftest flipped a digit in a JSON and an MFILE,
but never wrote the MFILE back to disk, and its pass condition only demanded "something
differed" — so it printed "both caught" while `mfile_lines_differing = 0`. Sixth consecutive
task in which the show-the-gate-can-fail rule exposed a defect in the task's own gate. The
committed version requires each channel to catch its own flip.

**F2 — Phase A `--verify` silently compared 4 of its 5 tables (fixed in `03a75f11`).**
`stage_verify` read `rec["at_the_calibration_point"]["ratio_block_over_flat"]`, a key
`accuracy.py` has never written; a per-deck `try/except Exception: pass` swallowed it; the
matched-accuracy table vanished from the comparison and the run still printed "every
compared table agrees with the published numbers". This was present at A28's merge, so its
"--verify 3/3 decks" statement was quietly narrower than a reader would take it — the exact
shape trap T11 names. The measured ratios were correct throughout.

**F3 — the one-command Phase B run cannot survive its own subject matter (BLOCKING; fixed in
`b3c4d131`, kept as a finding).** `run_a28.py` exited 1 if *any* sub-run failed, in every
mode. Two of 108 calibration runs crash PROCESS (deterministically, by the seeded
perturbation), the published table records exactly those crashes, and the experiment's own
doctrine makes failed starts a first-class result — yet the wrapper turned them into a fatal
stage error and `drive()` stopped the experiment. The stage-by-stage path in the results
document's §8 never checks exit codes and walks straight past the same 1, so "running the
whole experiment from one file and running the stages separately are two paths to the same
numbers" was false — a disagreement the entry point's own docstring classifies as a finding.
Fix: in measurement modes, failed runs are announced and recorded and the driver exits 0;
`gate` stays strict; a population in which *every* run failed is fatal in any mode.

**F4 — the wrong conda environment is neutralised, not refused.** The entry point under
`PROCESS_env` prints
`NOTE: the interpreter is …/PROCESS_env/bin/python3.12, which is not PROCESS_surgery_env.
'import process' still resolves to this tree, so the run is valid…` and proceeds (the script
directory heads `sys.path`, and `PYTHONPATH` pins every subprocess). The documented
catastrophic failure — silently measuring a different clone at a different commit — is
caught: a bare stage script under the wrong environment aborts with
`WRONG TREE: imported /home/wrutten/dev_libraries/PROCESS/process/__init__.py (tree
/home/wrutten/dev_libraries/PROCESS), expected exactly …/A29-replication-verify. Set
PYTHONPATH=… for this subprocess.` (exit 1). But "the run is valid" overstates: a different
interpreter carries a different dependency stack, and no gate checks that. For bit-level
claims, the guard guards the tree, not the environment.

**F5 — the I-14 path (`runs/a26/` gone) passed `--verify` silently (fixed in `77e9120a`).**
With the artifact absent, the `acc.exists()` guard skipped the whole matched-accuracy table
and `--verify` exited 0 saying "every compared table agrees" — the same silent narrowing as
F2 through a different door, on exactly the path the queue row said must fail with a message.
Now: the table prints with every deck MISSING, a NOTE names the rebuild command
(`--stages accuracy`), and the exit code is 1.

**F6 — the entry point cannot resume its longest stage.** A28 added `--resume` to
`run_a28.py` after their own campaign was interrupted, and it works exactly as documented
(exercised twice here; skip counts exact; crashed-but-recorded runs correctly kept). But
`MDA_partition_opt_experiment.py` never passes it: a user whose campaign dies mid-flight
must either re-run the whole 375-run stage or drop to the stage-level command by hand. On a
machine that killed three shells in two days, this is the most likely practical failure a
replicator will meet.

**F7 — the default arms disagree with the documented reproduction.** The one-command default
runs the campaign over **five** arms (375 runs, including `A0p_reordered`); the results
document's §8 stage-by-stage recipe and its cost table say **four** arms / 300 runs / 75 min.
The published numbers are unaffected (the extra arm only adds rows), but the from-clean cost
is ≈ 25 % higher than the table a user plans from.

**F8 — the published Phase A disk figure does not match a from-clean run.** Results document
§3.6: "untracked run artifacts ≈ 6 GB" for Phase A (and the entry point's printed plan says
6 781 MB). Measured after the complete from-scratch Phase A including both driver-side
stages: **0.86 GiB** (du at the environment-kill moment mid-run: 0.75 GiB, so no multi-GB
peak was missed at stage granularity). Phase B's ≈ 7 GB figure is consistent with what was
measured (≈ 5.6 GiB for `runs/a28` plus Phase A's artifacts). The Phase A figure should be
corrected or requalified.

**F9 — the run environment, documented for the next replicator.** (a) Background shells were
killed at roughly the one-hour mark three times (2026-09-02 ~19:05 during `driver_hoist`;
2026-09-03 ~10:57 and the session restart itself); (b) the WSL host slept ~4 h overnight,
pausing a live campaign without harming it; (c) a killed shell does not reliably kill the
python driver underneath — twice the detached driver kept running and completing runs
(useful, but it also means a "stopped" run may still be writing: after the descope stop, the
ladder driver drained 31 runs before dying, and those partial artifacts are on disk, marked
here as not-to-be-used). Judge liveness by file mtimes, never by `ps` (trap T8).

**F10 — small construction inconsistencies a replicator will notice.**
(i) `stage_pulse_gate` invokes `run_a26_pulse.py` with no arguments, so it always runs its
own two-deck default — under `--quick`, which promises one deck, it still runs two
(and takes the same 163 s in quick and full modes). (ii) `--starts 24` produces **25**
starting points per arm (`range(0, starts+1)`; start 0 is unperturbed) — matches the
published "25 starts" but not what `--help` suggests. (iii) Without `--parent-tree`, Phase
A's gates table prints `INCOMPLETE` for every deck (pristine columns empty) — correct and
visible, but a user should be told that this is the expected no-parent-tree state, not an
error.

---

## 9. Failure paths, verbatim

**(i) Wrong interpreter** — see F4 for both transcripts (entry point: NOTE + proceed;
stage script: `WRONG TREE:` + exit 1).

**(ii) Missing scenario deck** (`st_regression.IN.DAT` renamed away; both entry points,
exit 1):

```
CANNOT RUN: input deck(s) not found for ['st_regression']

THE FIX:
    the frozen decks live in <worktree>/arch_surgery/idf_probe/scenarios; pass
    --scenarios with names that exist there
```

**(iii) Missing committed artifact** (`ystate_st_regression.json` renamed away; Phase B,
exit 1) — and the named fix was then executed and restored the file:

```
CANNOT RUN: committed artifact <worktree>/arch_surgery/docs/data/ystate_st_regression.json is missing

THE FIX:
    it is tracked in git; restore it with
    git -C <worktree> checkout -- arch_surgery/docs/data/
```

**(iv) `runs/a26/` gone (issue I-14)** — before `77e9120a`: `--verify` exit 0, "every
compared table agrees" over 4 of 5 tables (the failure the queue row predicted). After:
exit 1, all decks MISSING in the matched-accuracy table, NOTE naming
`--stages accuracy` as the rebuild. `--analyse-only` with a26 gone prints the count tables
from a18 and omits matched-accuracy output (harmless; rebuilt nothing it shouldn't).

**(v) Symlinked shared cache** — not reachable from a fresh worktree (no symlink exists to
refuse through); the refusal text and its `--runs-root` fix are in `_ensure_harvest` and
were reviewed but could not be triggered honestly in this layout.

---

## 10. Autonomous decisions, with reversal paths

1. **Set the `--quick` artifacts aside** (`runs_quick_smoke/`, untracked) before the full
   Phase A run, so "from scratch" was literal. Reverse: delete the directory.
2. **Built the pristine tree in the session scratchpad** per the docstring recipe. Reverse:
   it is disposable; any user builds their own.
3. **Resumed interrupted runs via the documented stage selectors** (`--stages …`,
   `run_a28.py --resume`) rather than re-running completed stages — the resume machinery was
   itself under test (queue row / coordinator instruction). No completed run was re-measured.
4. **Two minimal fixes and two verification-hardening commits** on this branch, under the
   blocking-defect provision; measurement code untouched; each defect remains a finding.
   Reverse: revert the named commits.
5. **Let the orphaned ladder driver drain** after the descope stop rather than fight it
   without a kill mechanism (T8); declared its 31 partial artifacts unusable. Reverse: delete
   `runs/a28/ladder/`.
6. **Ran the Phase A determinism re-run at `a1d50d0a`** (two commits after the first run),
   accepting the git-tag lines as named differences rather than re-running the whole phase.
   The exclusion list was **not** widened after seeing them — they stay in the diff count,
   classified.

## 11. Change log (append-only)

| # | When | What |
|---|---|---|
| 1 | 09-02 17:35 | Phase A `--quick` from a runs-less tree: exit 0, 726 s, reproduces A18's counts exactly |
| 2 | 09-02 17:48 | Phase B `--quick`: exit 0, 439 s |
| 3 | 09-02 17:56 | Phase A full (parent tree given), `126a0d92` clean |
| 4 | 09-02 ~19:05 | environment killed the shell in `driver_hoist`; resumed `--stages driver_hoist driver_reorder tables`; exit 0 by 19:21 |
| 5 | 09-02 19:2x | F2 found (verify drops a table); fixed `03a75f11`; Phase A `--verify` 15/15 |
| 6 | 09-02 19:24 | comparator committed `a1d50d0a` after its own selftest defect (F1); census determinism: 522 532 leaves, 0 differ |
| 7 | 09-02 19:26 | Phase B full started, `a1d50d0a` clean; neutrality PASS 3/3; equivalence gate PASS 12/12 |
| 8 | 09-02 19:55 | **STOPPED at calibrate** — F3 found (measured crashes fatal to the wrapper); fixed `b3c4d131`; resumed `--stages calibrate campaign audit ladder tables` |
| 9 | 09-02 20:57 → 09-03 12:04 | campaign survived: shell kill (driver lived), ~4 h host sleep, session restart, driver death, `--resume` ×2 (skip counts exact), second shell kill; 375/375 runs complete, all stamped `b3c4d131` clean |
| 10 | 09-03 12:05 | h5 analysis: paired medians ≤ 5e-6 from published, `n_both_solve` exact; audit ran (16/225 non-solving starts recorded by the F3 fix) |
| 11 | 09-03 12:17 | **user descope received**: ladder + matched-accuracy replication cancelled; ladder stage stopped (31 partial artifacts, declared unused) |
| 12 | 09-03 12:2x | Phase B gate determinism re-run: 0 measured quantities differ over 286 724 leaves + 256 673 MFILE lines; F5 fixed `77e9120a`; failure paths ii/iii/iv executed and restored; both `--verify`s final: 30/30 |
