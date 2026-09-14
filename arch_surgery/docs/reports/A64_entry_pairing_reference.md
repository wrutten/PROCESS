# A64 (entry-pairing-reference) — the reference arm joins the entry pairing

> **Document status** — **OPEN.** Task **A64 (entry-pairing-reference)**, branch
> `A64-entry-pairing-reference` off `architecture_surgery` at base `9ffad6da`. Worktree
> `/home/wrutten/projects/PROCESS_surgery_worktrees/A64-entry-pairing-reference`. Records under the
> worktree's `arch_surgery/MDA_partitioning_experiment_v4/runs/`, untracked, to be relocated by the
> retire script at merge. Folder position records lifecycle, not validity (trap T3).

---

## 1. Verdict

Gate **G6** now pairs the reference arm's entry with every other evaluation-phase arm's, on every
configuration, and **PASSES**: 8 entry pairs at seed 1, **6 717 compared, 0 mismatched, 3/3 teeth**
(was 5 pairs, 4 204 compared). Three new PROCESS runs — `AR` at the pairing seed, one per
configuration — and nothing else re-made.

The two passages that disagreed now agree, and they agree with the chain:

| | said | now |
|---|---|---|
| `harness/chain.stage_evaluation_displaced` | every Phase A arm, `AR` included, is entered from the same displaced snapshot at the same seed | unchanged — this was always the behaviour |
| `harness/gate_entry.PAIRED_ARMS` | `("A0", "A0p", "A1")`, with a comment that the reference arm "is entered from the input file's own point and never from a snapshot, which is what 'PROCESS as shipped' means" | `("AR", "A0", "A0p", "A1")`, with a comment stating **D26** |

## 2. What changed and why

**D26**, ruled by the user 2026-09-14 (`MASTER_TODO.md` row D26, the user's words):

> *"I think it is fine if AR is initialized from the same points as the other phase A arms. It is
> not a full reference to a process run anyway, as that would need harvesting of an optimisation
> run to compare fully. So here we compare just the stopping rule, so thats fine."*

The row's headline: **the reference arm `AR` is entered from the same displaced snapshot as every
other Phase A arm.** The ruling is for the chain's reading — "as shipped" is a statement about the
**switches**, not about where the run starts, and the cost of starting from the input file's own
point is already §3.4's separate once-per-run **cold-start term**, reported beside and never pooled
(measured by `gates.entry_references`).

### 2.1 `harness/gate_entry.py` (commit `7ad8ea04`)

Three edits, no behaviour outside the gate:

1. **The comment.** The old comment is replaced by one that states D26, names the ruling and its
   date, says what "PROCESS as shipped" is about, and points at the cold-start term as the quantity
   that *does* measure entry from the input file's own point. It also records that an earlier
   revision said the opposite, so a reader who finds the old sentence quoted elsewhere can place it.
2. **`PAIRED_ARMS` gains `AR`**, first, in the plan's rung order (`AR → A0 → A0p → A1`, §3.3).
3. **Two docstrings** brought into line: the module docstring's list of the arms whose entry bytes
   must agree, and `_pin`'s, which now says why the reference arm needs no pin treatment (§2.3).

### 2.2 What the pairing check actually compares — read before the arm was added

`entry_and_warm_body` groups the pairing jobs by configuration, takes `arms_here[0]` as the
**anchor**, and compares every other arm's `y_entry.json` against it with `compare_entries`. That
function refuses outright if the two states were taken against different component specs
(`components_sha256`), then compares the state dictionaries **key by key, value by value** — the
hex literal of every float — and reports `n_differing`. The row's checks are two: every declared
component was compared (`n_components == config.n_coupling_components`), and `n_differing == 0`.

Three consequences, each checked in the tree before the edit:

- **`y_entry.json` is written unconditionally** by `evaluate.py`, from `spec.read(spec.bind(data))`
  after the snapshot has been written in and the displacement applied, *before* any caller exists.
  It does not depend on the arm's `mda`, so the reference arm writes one like any other.
- **The pins are recorded in the row but never compared**, so an arm with no pin does not weaken
  the comparison.
- **`AR` becomes the anchor**, because it is first. Previously the anchor was `A0` and the pairs
  were `(A0, A0p)` and `(A0, A1)`; they are now `(AR, A0)`, `(AR, A0p)`, `(AR, A1)`. Bit-identity
  is transitive, so the old pairs remain implied and one more pair is added — coverage strictly
  grows. Recorded here rather than left to be noticed, because the pair *names* in the verdict
  record changed as a side effect of the ordering.

### 2.3 `AR` needs no `pin_hex` treatment — as the task expected

`_pin` returns `None` for any arm whose `arms.ARMS[arm].burn_time_owner` is not `"constant"`.
`AR`'s owner is `"loop"` (`harness/arms.py`), exactly as `A0`'s is, so `AR` is handed no constant
on either pulsed configuration and the two-routes-to-one-number reconciliation `_pin` exists for
does not arise for it. The verdict record confirms it: every `AR` side of every pair reads
`pins[0] = None`. `AR` also reads the configuration's committed input file, not the lifted one
(`arms.input_file_for`), so no derived artifact enters.

## 3. The G6 verdict

Pressed from the **repository root** of the worktree as
`experiment_runner.py --gate entry_and_warm --resume`, at `7ad8ea04`.

```
verdict      : PASS
population   : 8 entry pair(s) at seed 1; 5 warm run(s); 16 evaluations
runs read    : 19 record(s) — 16 at f8bce151, 3 at 7ad8ea04 (this commit)  [resumed]
n_compared   : 6717     n_mismatched : 0
```

`6 717 = 840×3 + 846×3 + 827×2` entry-state components over the eight pairs, plus the five warm
rows. Every pair compared **every declared component** of its configuration's coupling state, and
**zero** differed:

| configuration | pair | components compared / declared | differing | `AR` pin | other pin |
|---|---|---|---|---|---|
| `large_tokamak_nof` | `AR`–`A0` | 840 / 840 | 0 | — | — |
| `large_tokamak_nof` | `AR`–`A0p` | 840 / 840 | 0 | — | `0x1.55eb4185b7330p+11` |
| `large_tokamak_nof` | `AR`–`A1` | 840 / 840 | 0 | — | `0x1.55eb4185b7330p+11` |
| `low_aspect_ratio_DEMO` | `AR`–`A0` | 846 / 846 | 0 | — | — |
| `low_aspect_ratio_DEMO` | `AR`–`A0p` | 846 / 846 | 0 | — | `0x1.5a131c44802b3p+13` |
| `low_aspect_ratio_DEMO` | `AR`–`A1` | 846 / 846 | 0 | — | `0x1.5a131c44802b3p+13` |
| `st_regression` | `AR`–`A0` | 827 / 827 | 0 | — | — |
| `st_regression` | `AR`–`A1` | 827 / 827 | 0 | — | — |

**Teeth 3/3, all tripped.** The third now bites on the new arm, because the anchor moved:

| tooth | what it did | what it reported |
|---|---|---|
| a continuous component bumped by three tolerances | `blanket.deg_blkt_inboard_poloidal_plasma` + `3 τ × scale` in a copy of nof's warm exit state | cross-state maximum `3.000e-06` against `τ = 1e-06` — the criterion stops holding |
| a discrete component flipped | `blanket.n_fw_inboard_channels` flipped in a copy of nof's warm exit state | categorically clean `= False` — stops holding however small the maximum |
| a doctored entry state | `blanket.deg_blkt_inboard_poloidal_plasma` × 1.5 in a copy of nof's **`AR`** entry state | **1 differing component of 840** |

## 4. The stamp survey

Every run record under `runs/gates/entry_and_warm/`, surveyed on `tree_git_head` after the press
(trap T13, harness plan amendment 13 (i)). **Exactly three records are new**; the other thirteen
are the seeded A63 records, kept by `--resume`:

```
large_tokamak_nof/pairing/A0       f8bce151  ok
large_tokamak_nof/pairing/A0p      f8bce151  ok
large_tokamak_nof/pairing/A1       f8bce151  ok
large_tokamak_nof/pairing/AR       7ad8ea04  ok   <- new
large_tokamak_nof/warm/A0p         f8bce151  ok
large_tokamak_nof/warm/A1          f8bce151  ok
low_aspect_ratio_DEMO/pairing/A0   f8bce151  ok
low_aspect_ratio_DEMO/pairing/A0p  f8bce151  ok
low_aspect_ratio_DEMO/pairing/A1   f8bce151  ok
low_aspect_ratio_DEMO/pairing/AR   7ad8ea04  ok   <- new
low_aspect_ratio_DEMO/warm/A0p     f8bce151  ok
low_aspect_ratio_DEMO/warm/A1      f8bce151  ok
st_regression/pairing/A0           f8bce151  ok
st_regression/pairing/A1           f8bce151  ok
st_regression/pairing/AR           7ad8ea04  ok   <- new
st_regression/warm/A1              f8bce151  ok

n_records = 16   heads: {f8bce151: 13, 7ad8ea04: 3}
```

The verdict's own line agrees and says so without being asked: *"19 record(s) — 16 at `f8bce151`,
3 at `7ad8ea04` (this commit) [resumed]"*. The 19 is 16 here plus the three `entry_references`
records, which the gate also declares under `runs_under`.

**Which gates ran on reused records, and at what commit.** Every gate other than
`entry_and_warm`, `recomputation` and `run_kind_separation` was **not re-run at all**: §4.1's table
is assembled by `--measure gate_table` from the verdict records already on disk, which were made
at `f8bce151` and earlier commits (`1f281529`, `47be2b0d`, `b784158c`, `d6f0fdf4`). The
`gate_table` stage record's `records_read` block names all 29 of them with their digests, and
`--plan-tables` confirmed *"every one of them is byte-identical to what is on disk now"* (A63's
mechanism, trap T14). The three gates that did re-run read 33 kept records plus the 3 new ones.

## 5. The runs made

**Three**, all `AR` at seed 1, regime `perturbed`, δ as the campaign declares it, `run_kind=gate`,
entered from the configuration's reference snapshot:

| configuration | status | taxonomy | sweeps | node calls | exit-audit maximum (`after_single_evaluation`) |
|---|---|---|---|---|---|
| `large_tokamak_nof` | ok | ok | 5 | 105 | `1.333e-07` |
| `low_aspect_ratio_DEMO` | ok | ok | 5 | 105 | `0.0` |
| `st_regression` | ok | ok | 5 | 105 | `8.846e-08` |

**Wall clock, context only, not evidence** (CLAUDE.md; trap T5): 43.7 s, 43.8 s and 44.0 s, one
sample each, three workers, a machine that was not otherwise idle. No conclusion here rests on it.

Two things worth recording about the runs, each with the condition that limits it (trap T11):

- **None hit upstream's ten-pass cap.** §3.4 anticipates that a Phase A entry at δ = 0.10 may reach
  it and reserves the taxonomy row `unconverged-at-cap`; at **this one seed on these three
  configurations** upstream's loop stopped at 5 sweeps every time. That is three runs at one seed,
  not a statement about the 25-seed campaign.
- **Upstream's stopping rule lands just below τ here.** The exit-audit maxima above are
  `1.3e-07`, `0` and `8.8e-08` against `τ = 1e-06` — the "≈ τ or ≪ τ" end of §3.3's three outcomes.
  This is **one single evaluation per configuration from one displaced entry**, in the gate
  population, and is not the RQ4 answer: that is the campaign's, over 25 seeds, in the table that
  carries both arms' residuals.

## 6. What else in the tree asserted the input-file entry for `AR` — grep, and the answer

Grepped over `MDA_partitioning_experiment_v4/` for `PAIRED_ARMS`, `"as shipped"` and
`"input file's own point"`, and over the plan's §3.3/§3.4 and §3.9 for any sentence stating `AR`'s
entry.

| where | what it says | action |
|---|---|---|
| `harness/gate_entry.py:69-72` | the comment under correction | **corrected** (§2.1) |
| `harness/gate_entry.py` module docstring | listed the arms whose entry bytes must agree, without the reference arm | **corrected** |
| `harness/gate_entry.py::_pin` docstring | silent on arms that own no constant | **extended** (§2.3) |
| `harness/arms.py:110`, `:204`, `:260`; `harness/README.md:91`; `harness/census.py:124`; plan §3.3 ("Reference arms `AR`/`BR` … every architecture switch unset"), §3.2's matrix note, §2 | "PROCESS as shipped" used of the **switches** | **correct as written** — these are exactly the reading D26 ruled for; left alone |
| `harness/chain.py:461` | "One flat evaluation per configuration, from the input file's own point" — the docstring of the **cold-start reference stage** | **correct as written**; it is the once-per-run term, and the corrected comment now points at it |
| `harness/perturb.py:88`, `harness/optimise.py:209-211`, `harness/evaluate.py:271`, `harness/input_files.py:319` | "the input file's own point" as the house name for seed 0 / no displacement | **correct as written**; nothing to do with `AR` |
| `EXPERIMENT_PLAN.md` §3.4, "Entries" | "seed-paired across arms and verified bit-identical per configuration" — **no arm exempted** | **already consistent with D26**; no edit |
| `EXPERIMENT_PLAN.md` §3.9, G6 row | "seed-paired entries bit-identical **across arms** per configuration" | **already consistent**; no edit |
| `EXPERIMENT_PLAN.md` §3.3 | states `AR`'s **role** and the `AR → A0` binding rule; says nothing about its entry point | **no edit** |

**No prose of `EXPERIMENT_PLAN.md` was edited.** The only change to that document is §4, rendered
by `--plan-tables write` (§7). This is stated explicitly because the task licensed an edit to the
plan's prose where it states `AR`'s entry, and the finding is that no such sentence exists: the
plan never said it, which is why the two harness passages could disagree unnoticed.

No selfcheck fixture, tooth, table caption or gate registry entry names the paired-arm set; the set
is read from `PAIRED_ARMS` in one place. Nothing under `PROCESS/` or the repository-root `process/`
was touched; `records.SCHEMA` is unchanged; `harness/config.py` is unchanged and
`EXECUTION_APPROVED` is `False`.

## 7. The measurement stages and §4

`--measure gate_table --resume` at `7ad8ea04`: **25 PASS, 0 FAIL, 147/147 teeth.** G6's row moves
from `5 entry pair(s) … 13 evaluations | 4204 | 0 | 3/3` to
`8 entry pair(s) … 16 evaluations | 6717 | 0 | 3/3`.

`--plan-tables write` (commit `cbbf0073`) rewrote §4 and nothing else — 134 changed lines, all
between the `## 4. Results` heading and `## 5. Discussion`. Two substantive changes: G6's row, and
the population marker that every caption carries, which gains the commit `7ad8ea04` and moves from
167 to 170 run records (168 gate + 2 smoke).

`--selfcheck`: **PASS**, 7 checks, 52 teeth tripped, 0 failed.

### 7.1 A consequence the brief did not name, applied rather than left (autonomous decision 1)

The tally's declared source **`paired_entries` is `runs/gates/entry_and_warm/*/pairing`** —
`tally.SOURCES`, re-derived in `analysis.SOURCES`. Adding `AR` to `PAIRED_ARMS` therefore adds
three records to the population of every stage computed over that source. Measured before acting:
the `tally_evaluation`, `tally_optimisation` and `recomputed_tables` stage records all declared
`runs_provenance` of **33 records at `f8bce151`**, while disk now held **36 at two commits**. That
is precisely the disagreement `analysis.assert_the_tally_read_these_runs` refuses on, and §4.2–§4.4
would otherwise have been published from stage records over a population that no longer exists —
trap T14's shape, one level down.

So, after the brief's four presses were committed, and with nothing running:

| press | result |
|---|---|
| `--gate recomputation --resume` | **PASS** — 2 066 compared, 0 mismatched, 9/9 teeth, over **36** run records (33 at `f8bce151`, 3 at `7ad8ea04`). The gate declares `reads_from` the two tally stages, so the button re-made `tally_evaluation` and `tally_optimisation` itself before running it. Previously 1 901/0 over 33. |
| `--measure recomputed_tables` | 65 tables, 1 951 cells, over the same 36 |
| `--gate run_kind_separation --resume` | **PASS** — 209 compared, 0 mismatched, 6/6 teeth, 178 run records under `runs/`, 31 covered by a declared source (previously 203/0, 175 records, 28 covered) |
| `--measure gate_table --resume` | 25 PASS, 0 FAIL, **147/147 teeth** — unchanged headline, now over the fresh verdicts |
| `--plan-tables write` | §4 re-rendered: 131 tables, **3 927 cells** (was 3 621) |
| `--plan-tables check` | **1 792 / 1 792 lines identical, 0 hunks** |

**No PROCESS run was made by any of these** — every run record was resumed. §4's diff stayed inside
lines 677–2469. Commit `fe504589`.

`AR` now carries a row in §4.2's cost, matched-accuracy, per-sweep-overhead and taxonomy tables,
which is what §3.3's binding rule on `AR → A0` asks for: the ratio published only in a table
carrying both arms' audit residuals. At **n = 1 per configuration** in the gate population, with
`EXECUTION_APPROVED` False, no cell there is a campaign statistic and every caption says so.

## 8. Autonomous decisions, each with its reversal

| | decision | why | how to reverse |
|---|---|---|---|
| 1 | After the brief's four presses, also press `--gate recomputation --resume`, `--measure recomputed_tables`, `--gate run_kind_separation --resume`, then `--measure gate_table --resume` and `--plan-tables write` again | §7.1: the change moves the tally's own population, so leaving those stage records would publish §4.2–§4.4 over 33 records that no longer describe disk, and the next `--gate all` would refuse. Applying a ruling's derived consequence rather than asking. Zero PROCESS runs | `git revert fe504589`; the tree returns to exactly what the brief's four presses produced (commit `cbbf0073`), with the staleness reported instead of closed |
| 2 | `AR` placed **first** in `PAIRED_ARMS`, in the plan's rung order, making it the pairing anchor | §3.3's rung table order is `AR → A0 → A0p → A1`, and the tuple's docstring already promised "in the plan's order". Coverage strictly grows (§2.2) | move `"AR"` to the end of the tuple; `A0` is the anchor again and the pairs read `(A0, A0p)`, `(A0, A1)`, `(A0, AR)`. One line; re-press G6 with `--resume` (no new runs) |
| 3 | `EXPERIMENT_PLAN.md`'s prose left untouched | §6: no sentence in §3.3, §3.4 or §3.9 states `AR`'s entry point; §3.4's "seed-paired across arms" already covers it | add a sentence to §3.4's "Entries" paragraph naming `AR` explicitly, if the orchestrator wants the plan to say in prose what the gate now enforces |
| 4 | The correction recorded in the code comment that an earlier revision said the opposite, rather than silently replacing it | the old sentence is quoted verbatim in D26's row and in A55's report; a reader meeting it needs to be able to place it | delete the last clause of the `PAIRED_ARMS` comment |

## 9. Limits

1. **One seed.** The pairing is checked at `PAIRING_SEED = 1` only — the first displaced seed, by
   the gate's own design (an undisplaced entry is the snapshot itself and pairs trivially). That
   `AR`'s entry pairs at seed 1 on three configurations is not a statement about seeds 2–25; the
   campaign's own entries are separately verified bit-identical per configuration (§3.4).
2. **The gate checks the entry, not the exit.** G6's pairing half says the four arms *started* from
   the same bytes. It says nothing about where `AR` ends up; that is the exit audit's, and the
   `AR → A0` comparison's, business.
3. **`AR` has no warm half.** `WARM_ARMS` is unchanged (`A0p`, `A1`) and was not widened: the warm
   check is "a **block** arm entered from the reference's exit state and pinned at the reference's
   converged burn time reproduces the reference fixed point", and `AR` is neither a block arm nor
   pinnable. Not an oversight; stated so nobody reads the asymmetry as one.
4. **Three runs are not a population.** Everything in §5 is three single evaluations at one seed in
   the gate population, with `EXECUTION_APPROVED` False. The taxonomy observation and the
   upstream-residual observation are both conditioned on that in the sentences that carry them.
5. **`f8bce151` is not this commit.** Thirteen of the sixteen G6 records, and every verdict §4.1
   reports other than the three gates of §7.1, were made at earlier commits and kept by `--resume`.
   That is what the brief asked for and what harness plan amendment 15 licenses, and every verdict
   states its own straddle; it is not a from-scratch press and is not reported as one.
6. **Three census records remain `census-1`.** The three optimisation-entry censuses still carry no
   tree stamp — A63's open item, named by `--selfcheck` and untouched here. Unrelated to this task,
   recorded so the selfcheck output is not misread.

## 10. What the queue, the harness plan and the improvement list should gain

Not edited here, per the brief. Proposed:

- **`MASTER_TODO.md`, row A64** → MERGED with: G6 PASS 6 717/0, 3/3 teeth, 8 pairs (was 5, 4 204);
  three new runs, thirteen reused at `f8bce151`; the derived consequence of §7.1 (the tally's
  `paired_entries` source moves with `PAIRED_ARMS`, so `recomputation`, `run_kind_separation` and
  the three stages over it were re-made: 2 066/0 over 36, 209/0 over 178); §4 re-rendered, 131
  tables / 3 927 cells, `--plan-tables check` 1 792/1 792 identical; 25 gates PASS, 147/147 teeth;
  selfcheck 7 checks, 52 teeth. Records relocated to `idf_probe/runs/A64_runs/`.
- **`MASTER_TODO.md`, row D26** → discharged by A64, with the note that the plan's prose never
  stated `AR`'s entry either way (§6) — which is *why* the two harness passages could disagree.
- **`V4_HARNESS_IMPLEMENTATION_PLAN.md`, a new amendment rule:** *a gate's arm set is also a tally
  population.* `tally.SOURCES`/`analysis.SOURCES` declare gate run directories by path, so widening
  what a gate runs silently widens what the tally publishes; a change to a gate's arm, seed or
  configuration set must re-make every stage over that source in the same press. §7.1 is the
  measured instance.
- **`TRAPS.md`** — optional, a paragraph on T14 rather than a new trap: the same staleness reaches
  a stage record through its **run population** (`runs_provenance`) and not only through its
  **file list** (`records_read`), and only the first kind is invisible to `--plan-tables`, which
  checks freshness on §4.1 alone.
- **`V4_IMPROVEMENT_LIST.md`** — nothing. No improvement item is affected.

## 11. Commits

| commit | what |
|---|---|
| `7ad8ea04` | `harness/gate_entry.py`: `PAIRED_ARMS` gains `AR`; the comment states D26; two docstrings |
| `cbbf0073` | `EXPERIMENT_PLAN.md` §4 re-rendered from the re-made `gate_table` record |
| `fe504589` | `EXPERIMENT_PLAN.md` §4 re-rendered again, over the tally/analysis stages re-made for the new population (§7.1) |

Base `9ffad6da`. Nothing pushed. `runs/` untracked.

---

## 12. Orchestrator's critical assessment (protocol §5)

*Written 2026-09-14 at the branch tip `c08446f6`, before the merge. Checks chosen to differ from
the agent's own, not to repeat its presses.*

1. **The diff, read.** One code file, 32 lines, all comment and the four-element tuple. No behaviour
   other than the arm set changes; `_pin` is untouched and returns `None` for `AR` because its owner
   is `loop` — confirmed by importing the merged module on a trial merge of the branch onto trunk
   (`6e98a852`): `[('AR','loop'),('A0','loop'),('A0p','constant'),('A1','constant')]`.
2. **The pairing, checked by a different instrument.** The gate compares `y_entry.json` key by key.
   I took the SHA-256 of each pairing directory's `y_entry.json` whole: one digest per configuration
   across `AR`, `A0`, `A0p`, `A1` (`f2570b0495e6`, `cf9fde19753b`, `b648299e79df`; `A0p` absent on
   `st_regression` by its skip). Same conclusion, reached without the gate's code.
3. **Merge and the record-less tree.** The trial merge onto trunk is clean (3 files). On that tree,
   with no `runs/`, `--selfcheck` PASSes and `--plan-tables check` refuses by name for the missing
   `gate_table` stage record — the refusal A63 built, working.
4. **Autonomous decision 1 (re-making the tally stages) is right and was necessary.** Widening a
   gate's arm set widens the tally population that gate's directory feeds; leaving §4.2–§4.4 over
   33 records would have been trap T14's shape. The agent measured the disagreement before acting
   and every re-made stage was a resume (0 PROCESS runs). Its proposed rule — *a gate's arm, seed or
   configuration set is also a tally population; changing it re-makes every stage over that source
   in the same press* — is written into the harness plan as amendment 21 at the merge.
5. **Autonomous decision 2 (`AR` as anchor).** Accepted; bit-identity is transitive and the plan's
   order is the tuple's declared order.
6. **Decision 3 (plan prose).** Overruled in the small: D26 is the user's ruling, and the plan should
   say in one sentence what the gate enforces. Added to §3.4 at the merge, quoting D26.
7. **Numbers checked against the record, not the summary:** §4 shows the `AR` row at n = 1 per
   configuration with `after_single_evaluation` as its audit position and "no snapshot recorded on
   this record" — correct for a Phase A evaluation, which never reaches the output path.

**Approved for merge.** Records relocate to `arch_surgery/idf_probe/runs/A64_runs/` (path from the
retire script).
