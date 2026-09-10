# V4 harness — implementation plan

> **Document status** — **APPROVED FOR THE REBUILD — 2026-09-10, by the user, with three notes (§11).** Was: DRAFT · NOT APPROVED. PLAN ONLY, NO CODE WRITTEN. Opened
> 2026-09-10 by task **A45 (v4-harness-plan)** on the user's instruction to rewrite the
> experiment harness: *"self-contained in `MDA_partitioning_experiment_v4/harness`… a minimal
> implementation of what we need for the V4 plan, with a clear code structure… retain the
> one-button run approach with `phase_a.py`, `phase_b.py` and `experiment_runner.py`… all that
> is used from `/idf_probe` or `/fixedpoint` should be in the new `/harness` folder… very
> concise but clear docstrings… a harness `README.md`."* (2026-09-10, paraphrased minimally.)
>
> **Nothing here may be built until the user approves this plan.** No file under `process/`,
> `arch_surgery/idf_probe/`, `arch_surgery/fixedpoint/`,
> `arch_surgery/MDA_partitioning_experiment_v2/` or `…_v3/` was changed by the task that wrote
> this document. **§9 "Decisions for the user" is the part that needs an answer**; the rest is
> written under the recommendation in each row.
>
> **The methodology is not this document's business.** It is
> [`../MDA_partitioning_experiment_v4/EXPERIMENT_PLAN.md`](../../MDA_partitioning_experiment_v4/EXPERIMENT_PLAN.md)
> (the V4 experiment plan) and
> [`V4_IMPROVEMENT_LIST.md`](V4_IMPROVEMENT_LIST.md) (the item list behind it). This plan says
> how a harness implements them, and where the harness *forces* a methodological choice it says
> so and asks rather than deciding.

---

## 0. Reading guide — the vocabulary, spelled out once

This project's shorthand is dense and this document is meant to be readable without the queue
open beside it (protocol §4). Everything used below, defined here.

*Caption: one row per term; the meaning is the one this repository uses, not a general one.
"Driver" always means the arrangement of solvers and loops; "model" always means a frozen
physics or engineering calculation.*

| term | meaning |
|---|---|
| **PROCESS** | the fusion power-plant systems code this repository forks. An optimiser (VMCON) wrapped around a loop that runs ~26 physics and engineering **models** until their outputs stop changing |
| **driver** | the arrangement of solvers and loops: `process/core/caller.py` and `process/core/solver/`. The experiment's *independent variable* |
| **model** | a physics or engineering calculation under `process/models/`. **Frozen** at base commit `c0ae5b28` — the whole point (decision **D5**) |
| **MDA** | multidisciplinary analysis: the loop that drives the models to a consistent state at a fixed design vector |
| **node** | one model call site inside `call_models` (`physics`, `build`, `costs`, …). One **node call** = one execution of one node. The cost unit |
| **sweep** | one pass over a node sequence — the whole loop (flat) or one block's nodes (partitioned) |
| **coupling state `y`** | the measured set of state fields written by in-loop models: 840 / 846 / 827 components on the three configurations. What the MDA converges |
| **τ** (tau) | the convergence tolerance on `y`, per component, scaled: `max_i \|Δy_i\| / s_i < τ`. τ = 1e-6 |
| **configuration** (V3's "deck") | one input file defining one optimisation problem: `large_tokamak_nof` (nof), `low_aspect_ratio_DEMO` (lad), `st_regression` (st). Display term is "configuration"; identifiers in code and records still say `deck` |
| **arm** | one assignment of the driver's environment switches. Phase A arms `AR A0 A0p A1`; Phase B arms `BR B0 B1 B3` *(**D22**, 2026-09-10: `B2` removed from the arm set)* |
| **rung** | an ordered pair of adjacent arms differing by one named thing |
| **prime** | executing the first-wall geometry method at the head of every sweep so `build` reads this pass's first-wall thickness instead of the previous pass's. A driver choice about *when a method runs* (decision **D19**) |
| **hoist** (V3) → **`per_call`** (V4) | running a feed-forward node once per `call_models` evaluation instead of once per sweep |
| **post-solve** (V3) → **`per_run`** (V4) | running a feed-forward node once in total, at the accepted optimum |
| **lift** | taking the burn time out of the loop. Its **owner** becomes a *constant* (Phase A: the **pin**) or *the optimiser* (Phase B: iteration variable 178 + equality constraint 93) |
| **teeth** | a gate's demonstrated ability to fail: a deliberately broken input that must trip it before the gate's zeros are believed (protocol §12) |
| **δ** (delta) | the entry displacement of a Phase A evaluation, or the start displacement of a Phase B optimisation |
| **`ifail`** | VMCON's exit code; `1` = converged |
| **`norm_objf`** | the normalised objective at exit. The correctness quantity (decision **D6**: never iteration variables) |
| **switch neutrality** | with every `PROCESS_ARCH_*` variable unset the driver's behaviour is byte-identical to upstream. A gate, not an aspiration |
| **D`<n>` / I-`<n>` / A`<n>`** | a recorded user decision / a filed issue / a queue task, in [`MASTER_TODO.md`](MASTER_TODO.md) |
| **protocol §`<n>`** | a numbered rule of the orchestration protocol in the same file. §12 = gates need teeth and counts need denominators; §15 = every published number comes from a committed script; §16 = every table carries a caption |
| **trap T`<n>`** | a recorded way this project has already been misled, in [`../TRAPS.md`](../TRAPS.md) |

The decisions and issues cited below, in one place: **D2** base commit frozen · **D5** models
frozen, only the driver changes · **D6** correctness on `norm_objf`, never iteration variables ·
**D9** frozen scenario decks are never edited · **D11** minimal `process/models/` edits need the
user's approval · **D14(c)** one implementation of a shared definition, never two · **D15**
δ = 0.10 calibrated · **D17** three configurations · **D19** the prime · **I-10** a wall-clock
weight moved 6.4 % → 4.4 % across runs of identical code · **I-12** a median-scaled tolerance
became ~10¹⁸× too tight at a divergent point · **I-14 / I-15 / I-16** untracked run artifacts
destroyed by worktree removal, three separate times · **I-17** the Phase A → Phase B transfer
over-predicts · **I-18 / I-19** a declared definition reached one implementation and not the
other · **I-20a** empty blocks are still swept.

---

## 1. Verdict, in one page

**What was inventoried.** Every import, subprocess call, artifact path and environment variable
the V3 harness uses from outside its own directory, at file and function level (§2), and the
driver-side instrument it drives (§3).

**The finding that shapes everything else: the coupling to `idf_probe/` and `fixedpoint/` is
tiny, and the convolution is inside the files, not between them.** The whole external surface of
the V3 harness is **three Python names imported from two modules, three subprocess entry points,
seven committed artifacts, one scenario directory and one hard-coded absolute path into the main
checkout.** `arch_surgery/fixedpoint/` is not imported by the V3 harness at all — it is reached
once, at runtime, through an `importlib` file-path load buried two levels deep. What is actually
convoluted is that the two run drivers (`run_one.py`, 1 126 lines, one 1 000-line `main()`;
`v2_eval_one.py`, 996 lines) duplicate each other, that arm composition exists twice in two
divergent implementations, and that a hand-maintained ledger of booleans stands in for a
measurement of what the driver can actually do.

**So "self-contained in `harness/`" is achievable and cheap.** One obstacle stood in the way and
**decision D20 removed it** *(amendment 2, 2026-09-10)*. The obstacle: the driver reaches into the
research tree at three fixed paths with no override — `module_solve.py:529-534` loads
`arch_surgery/fixedpoint/ystate.py` **by absolute path**, and `caller.py:245-251` / `:356-362`
read `docs/data/node_writesets.json` and `dsm_node_map.json` the same way — so moving those files
into a *version-numbered* directory would have made `process/` depend on `…_v4/`. **D20's answer
is to copy the whole of `process/` into `…_v4/PROCESS/` and let V4 own it**: the copied driver
re-points those three paths statically at V4's own locations, nothing is selectable at run time,
and the repository-root tree stays V2/V3's, untouched. The plan is written under that frame
throughout; §3's preamble, §5.2–§5.4 and §7 carry the consequences, and **gate G0′** (§7.6) is what
keeps a second copy of the models honest.

**What is proposed.** A `harness/` package of 19 modules (§4), built around four ideas:

1. **The switch matrix is data.** One `dict` of `Arm` dataclasses transcribing the V4 plan's
   §3.2 table; `env_for(arm, config, seed)` walks it. This deletes both of V3's `if`-chains and
   makes the rung difference (`what does `B0 → B1` change?`) a computed field diff rather than a
   sentence in a docstring.
2. **Capability is measured, not declared.** V3's `INSTRUMENTATION` ledger is a hand-edited dict
   of booleans, and the inventory found it is consulted on one side and not the other. It is
   replaced by a **capability probe**: a child process that imports the driver and reports what
   it *resolved*, so an arm that composes a switch the tree does not recognise **refuses** —
   which is what the orchestrator's brief requires and what V3 already does, but for one switch
   only.
3. **One run path, two entry points.** The perturbation hook, the two censuses, the forensics
   hook and the exit audit live in one module used by both the optimisation entry point and the
   single-evaluation entry point, instead of being written twice.
4. **The rewrite is gated on reproducing V3 bit-for-bit** (§7). A rewrite that changes the
   measurement is not a rewrite, it is a new experiment. Under D20 that gate is **run once**, at
   the commit that copies `process/` and **before any driver change**, so the only variable in the
   comparison is the harness.

**Cost, honestly.** The V3 stack measures **8 828 lines** (`wc -l` over the six V3 files plus
`run_one.py`, `v2_eval_one.py`, `run_a28.py`, `a25_variant_deck.py` and `fixedpoint/ystate.py`).
The proposed V4 stack estimates at **≈ 6 570**: `harness/` ≈ 4 220 of which **821 are
`ystate.py` moved verbatim**, the three top-level scripts ≈ 1 450, `analysis.py` ≈ 900. That is
roughly a **26 % reduction** *and* self-containment — not a dramatic shrink, because most of the
V3 code is load-bearing measurement, not accident. Anyone expecting "minimal" to mean "a few
hundred lines" should read §4.6, which prices what minimality costs in lost diagnostics.

**What needed the user — all of it now settled** *(amendment 3, 2026-09-10)*. §9's eleven
decisions are ruled and nothing is open. Highlights: the **predicate module goes whole to
`harness/ystate.py`**, reached by the copied `module_solve.py` through **one re-pointed path
constant** — the user's standing preference being *do not modify the copied `process/` tree beyond
necessity*, so the copy receives **three path constants and nothing else** (§3.3). The committed
**artifacts are copied into `harness/data/`** with a sha256 gate and a `PROVENANCE.json`. The A18
harvest is **left as it is** — V4 never regenerates the frozen ruler, so no `--derive` stage
exists. Driver changes **DR1, DR2, DR4, DR5, DR7 are approved**; **DR3 is rejected** (the empty
`PULSE` visits stay and are disclaimed in every per-sweep caption) and **DR6 is dropped** by D20.
**D22 removes `B2` from the arm set**, leaving Phase B as `BR / B0 / B1 / B3` — 275 optimisations.
And one requirement arrived with the rulings and is binding: **every verification gate is
implemented inside `harness/`**, none imported from `idf_probe/` or `fixedpoint/`.

---

## 2. Inventory — what the V3 harness actually uses from outside itself

Read at commit `16a6e87e` in this task's worktree; every line number below is from that tree.
The V3 harness is six files in `arch_surgery/MDA_partitioning_experiment_v3/`: `run_experiment.py`
(129 lines), `v3_config.py` (157), `v3_runner.py` (263), `phase_a.py` (1 615), `phase_b.py`
(1 052), `v3_report_analysis.py` (1 724).

### 2.1 Python imports from outside the V3 directory — three names, two modules

*Caption: one row per import crossing the directory boundary. "Names" are the exact symbols
bound. All three are reached after `sys.path.insert(0, cfg.IDF_PROBE)` in `v3_runner.py:34`,
whose side effect on `sys.path` is what makes `phase_a.py`'s two imports resolve at all.*

| importer | line | module | names | what they do |
|---|---|---|---|---|
| `v3_runner.py` | 35 | `idf_probe/run_a28.py` | `_ARCH_VARS`, `PULSED as A28_PULSED` | `_ARCH_VARS` is the list of every architecture/probe environment variable that must be **cleared** before composing an arm. `A28_PULSED` **is never used** — dead import, and `cfg.PULSED` duplicates the same set independently, so the two can drift |
| `phase_a.py` | 61 | `idf_probe/a34_instruments.py` | `_cross_residual`, `load_spec_offline` | `load_spec_offline` rebuilds a committed coupling-state artifact into a `YSpec` with its `components_sha256` re-checked; `_cross_residual` (a **private** name, imported across a module boundary) summarises the residual between two states |
| `phase_a.py` | 62 | `idf_probe/v2_eval_one.py` | `perturb_factor`, `restore_snapshot` | `perturb_factor(seed, name, δ)` = `1 + δ·u` from a hash of (seed, component **name**) — used at `phase_a.py:1009` so the burn-time pin rides the *same* δ-stream as the state perturbation; `restore_snapshot` turns a snapshot file back into the list layout `spec.residual` takes |

`run_experiment.py`, `v3_config.py`, `phase_b.py` and `v3_report_analysis.py` import **nothing**
from outside the V3 directory.

**The one `fixedpoint/` touch, and why no static scan finds it.**
`phase_a.py:682` → `a34_instruments.load_spec_offline` → `a34_instruments._ystate_module()`
(`a34_instruments.py:234-239`) → `importlib.util.spec_from_file_location(…,
TREE/"arch_surgery"/"fixedpoint"/"ystate.py")` + `exec_module`. That is the **entire** coupling
between the V3 harness and `arch_surgery/fixedpoint/`. Nineteen of the twenty `fixedpoint/`
modules — `engine.py`, `replay.py`, `arms.py`, `manifest.py`, `accounting.py`, `accuracy.py`,
`analyse.py`, `nodemap.py`, `predicate_reads.py`, `a22_*`, `a23_*`, `a26_gates.py`,
`run_phase_a.py`, `run_a2[236].py`, `tables.py`, the three `gen_*.py` — are **untouched by V3**.

**Transitive cost of those two lines.** Importing `a34_instruments` pulls in
`a31_drift_probe`, `run_a28` and `v2_eval_one`, and `v2_eval_one` pulls in `run_one`. So
`import phase_a` loads **five** `idf_probe` modules to obtain **four** functions. That is the
convolution the user is describing.

### 2.2 Subprocess entry points — four, of which three run PROCESS

*Caption: one row per `subprocess.run` crossing the directory boundary; "consumes" is what the
caller reads back, which in three of four cases is a file, not stdout.*

| caller | line | launches | consumes |
|---|---|---|---|
| `run_experiment.py` | 47-53 | `sys.executable -c "import process; print(process.__file__)"` | stdout; refuses to start if the interpreter cannot import `process` from the tree. Added after the 2026-09-04 launch failure where a wrong interpreter was reported as *"the A0 reference did not converge"* — a machinery failure wearing a physics result's clothes |
| `v3_runner.derive_lifted_decks` | 69-82 | `idf_probe/run_a28.py decks --runs … --decks … --scenarios nof lad` → which itself spawns `idf_probe/a25_variant_deck.py` | return code only; the product is the file `<decks>/<config>/<config>_lifted.IN.DAT` |
| `v3_runner.run_job` | 193-225 | `idf_probe/run_one.py --scenario --mode control --outdir --expect-tree --input --exit-audit --entry-census [--node-census] [--perturb-delta --perturb-seed] [--force-maxcal]` | `<outdir>/metrics.json`, re-stamped with `v3_arm/v3_deck/v3_seed/v3_delta/v3_tau` |
| `phase_a.run_eval_job` | 252-272 | `idf_probe/v2_eval_one.py --scenario --input --outdir --expect-tree --perturb-spec --exit-audit --audit-exclude-postsolve --seed --node-census [--delta] [--entry-state]` | `metrics.json`, `audit_residual.json`, `perturbation.json`, `y_entry.json`, `y_exit.json` |

`idf_probe/a33_postsolve.py` is **never invoked** by V3 — its outputs are consumed as committed
artifacts. `run_a28.py` is invoked with the `decks` subcommand only; its `gate`, `calibrate`,
`ladder`, `campaign` and `audit` subcommands are dead to V3.

### 2.3 Committed artifacts and fixed paths

*Caption: one row per file or directory outside the V3 directory that V3 reads. "Who else reads
it" matters because an artifact the **driver** also reads cannot be moved by the harness alone.*

| path | read by | who else reads it | V4 needs it? |
|---|---|---|---|
| `docs/data/ystate_a26_<config>.json` (3) | `v3_config.ystate_for`, passed as `PROCESS_ARCH_YSTATE` and as both Phase A specs | **the driver**, `module_solve.load_spec` | yes — the definition of `y` |
| `docs/data/writeset_a26_<config>.json` (3) | `v3_config.writeset_for`, passed as `PROCESS_ARCH_WRITESET` | **the driver**, `module_solve` | yes — the per-block subsets |
| `docs/data/postsolve_<config>.json` (3) | `PROCESS_ARCH_POST_SOLVE`; `phase_a.excluded_keys`; `v3_report_analysis.excluded_keys` | **the driver**, `caller._post_solve_nodes` | yes — becomes the `per_run` set |
| `docs/data/postsolve_nolift_<config>.json` (2) | Phase A block arms on pulsed configurations (they run the frozen deck, so the artifact must be stamped for the base constraint set) | the driver | yes — `A0p`/`A1` need it |
| `docs/data/node_writesets.json` | `phase_a.py:115,342`; `v3_report_analysis.py:114` | **the driver**, `caller.py:350,583` — **hard-coded path, no override** | yes |
| `docs/data/dsm_node_map.json` | `v3_report_analysis.py:1084,1314` | **the driver**, `caller.py:382,570,703` — **hard-coded path, no override** | yes |
| `docs/data/a21_published.json`, `a28_published.json` | **nobody in V3** | — | no |
| `idf_probe/scenarios/<config>.IN.DAT` | `v3_runner.deck_for:66`, `phase_a.py:255` | — | yes — the frozen configurations (D9) |
| `arch_surgery/fixedpoint/ystate.py` | transitively, §2.1 | **the driver**, `module_solve.py:529-534` — **hard-coded path, no override** | yes — the predicate |
| `/home/wrutten/projects/PROCESS_surgery/…/_v2/runs/phase_b/campaign/<deck>/R/start000/metrics.json` | `phase_b.py:56-60,246` — gate G0's comparator | — | **replaced**: V4's G0 compares against **V3's** records |

The last row is the harness's only **absolute** path. It resolves to the *main checkout*, not to
the worktree the harness is running in. That was deliberate in V3 (V2's records live there and
are untracked), but it means a harness run from a worktree silently reads a tree it is not
measuring. V4 should resolve it through one named constant with the tree stamped into the gate
record — see §7.

### 2.4 Environment variables

`v3_runner._ALL_ARCH_VARS` (lines 42-47) is `run_a28._ARCH_VARS` plus four names, deduplicated:
**every** variable is cleared before an arm is composed, so an inherited value can never change
what is measured. That discipline is correct and V4 keeps it. The cleared set is
`PROCESS_IDF_PROBE`, `PROCESS_ARCH_SEQUENCE`, `_HOIST`, `_LIFT`, `_MODULE_SOLVE`, `_TAU`,
`_INNER_TAU`, `_YSTATE`, `_WRITESET`, `_PASS_TRACE`, `_PASS_TRACE_FULL_FROM`, `_POST_SOLVE`,
`_OUTER`, `_PIN_BURN_TIME`, `_PRIME`.

**Composition exists twice, and the two copies differ.** `v3_runner.env_for` (Phase B, lines
85-147) and `phase_a.env_for_phase_a` (Phase A, lines 139-193) are separate `if`-chains over the
same switch vocabulary. Inventory found two asymmetries: `phase_a` sets `PROCESS_ARCH_OUTER=trust`
**unconditionally** for block arms while `v3_runner` gates it on the ledger entry; and `phase_a`
sets `PROCESS_ARCH_POST_SOLVE` unconditionally while `v3_runner` gates it. Neither is wrong today;
both are the shape of defect that a single composition function makes impossible.

The only variable the harness *reads* is `V3_WORKERS` (`v3_runner.py:56`), the pool-width
override.

### 2.5 The disposition table — what happens to each piece in V4

*Caption: one row per external dependency of §2.1–§2.4. **move** = the code comes into
`harness/`; **stage** = `harness/` regenerates it from a committed stage; **resolve** = the
harness locates and validates a file it does not own; **drop** = V4 does not need it.*

| piece | disposition | where it lands / why it goes |
|---|---|---|
| `run_a28._ARCH_VARS` (clear list) | **move** | `harness/switches.py` — as a registry of `Switch` records, not a bare tuple |
| `run_a28.PULSED` / `cfg.PULSED` | **drop** (both) | `Config.pulsed` field; one source, no duplicate to drift |
| `run_a28.py decks` + `a25_variant_deck.py` | **move** (the derivation only) | `harness/decks.py` — the three-line lifted-deck edit as a stage; the rest of `run_a28` is A28-era campaign machinery V4 does not use |
| `a34_instruments.load_spec_offline` | **move** | `harness/predicate.py` — the same rebuild-and-sha-check, without the `importlib` indirection |
| `a34_instruments._cross_residual` | **move** | `harness/predicate.py`, made public |
| `v2_eval_one.perturb_factor` | **move** | `harness/perturb.py` (or `child.py`) — one implementation, used by both phases |
| `v2_eval_one.restore_snapshot` | **move** | `harness/predicate.py` |
| `run_one.py` (Phase B run driver) | **move, split** | `harness/optimise.py` + `harness/child.py` + `harness/provenance.py` + `harness/records.py`; the four probe modes and `--exit-audit-at-call` drop (§2.6) |
| `v2_eval_one.py` (Phase A run driver) | **move, split** | `harness/evaluate.py` + the same shared `child.py` |
| `fixedpoint/ystate.py` (the predicate) | **move, whole, into `harness/`** *(amended 2026-09-10; decision (2) **ruled option (v)**)* | `…_v4/harness/ystate.py`; the copied `module_solve.py` reaches it through one re-pointed path constant at a fixed relative path |
| `docs/data/*.json` artifacts | **copy** *(amended 2026-09-10, D20 — this row was "resolve + validate in place")* | `…_v4/harness/data/`, sha-gated byte-identical at copy time with a `PROVENANCE.json` — decision (3) |
| the a26 artifact **derivation** | **drop** *(amended 2026-09-10)* | no `--derive` stage exists; the scales are the frozen ruler and V4 never regenerates them. `artifacts --check` validates from the artifact's own `harvest_identity` — decision (4) |
| `postsolve_*` derivation (`a33_postsolve.py classify`) | **move** | `harness/postsolve.py` — plus the class-level classifier fix and the runtime read census (improvement item 6a) |
| `idf_probe/scenarios/*.IN.DAT` | **resolve** | frozen configurations stay where they are (D9); `Config.input_path` names them |
| the V2 G0 reference path | **drop** | V4's G0 compares against V3's records through the V3→V4 name map (§7) |
| `INSTRUMENTATION` ledger | **drop** | replaced by the measured capability probe (§4.2, §6 R5) |
| `arch_surgery/experiment_runner.py`, `MDA_partition_experiment.py`, `MDA_partition_opt_experiment.py` | **leave frozen** | the A18/A28-generation entry points, superseded by V2/V3's `run_experiment.py`. V4 does not use them; they are the record of what ran and are cited by A28's report. Do not delete — decision **(11)** |

### 2.6 What is dead, and why it can go

*Caption: one row per capability the V3 stack carries that V4 does not need. "Evidence" is what
establishes it is unused, not an opinion about it.*

| dead thing | evidence | consequence of dropping |
|---|---|---|
| `run_one.py --mode {baseline,modules,frozen,harvest}` in the *run* path | V3 passes `--mode control` at `v3_runner.py:197`, always | the four probe submodules are never imported on the measurement path. **But the `modules` probe is still needed** as its own stage — improvement item 6a(a) asks for a committed runtime read census — so it moves to `harness/census.py`, not to nothing |
| `--exit-audit-at-call N` | never passed by V3's campaign; the V4 plan §3.3 fixes **one** audit position (the entry to `write_output_files`) for every arm | the call-indexed variant goes; the audit mechanism stays and gains the recorded `audit_position` field the V4 plan requires |
| A18-mode coupling-state specs (`SPEC_MODE_A18`, `ystate_<config>.json`, `writeset_<config>.json` without the `a26` infix) | V3 uses `ystate_a26_*` / `writeset_a26_*` everywhere (`v3_config.py:74,77`) | the mode parameter stays in the artifact preamble — improvement item 5a needs a *predicate* mode there — but A18 stops being the default and the non-a26 artifacts are not resolved by V4 |
| `PROCESS_ARCH_PASS_TRACE`, `PROCESS_ARCH_PASS_TRACE_FULL_FROM` | never set by V3's harness | still **cleared** (they are driver capabilities and an inherited value would change the run); never composed |
| unguarded routing: `run_a28`'s `gate`, `calibrate`, `ladder`, `campaign`, `audit` subcommands; `a31_drift_probe`, `a25_*`, `a13_*`, `a3_*`, `a26_pulse_gate`, `noise_*` | not reachable from V3's six files except as transitive imports | ≈ 400 KB of A13/A24/A25/A28/A31-era task machinery stops being on the harness's import path. It stays in `idf_probe/` as the record of those tasks |
| 19 of 20 `fixedpoint/` modules | §2.1 | the A18-generation replay engine (`engine.py`, `replay.py`, `arms.py`, `accuracy.py`, `manifest.py`) is not carried into V4. It is Phase A's *replay* architecture, superseded by V2's single-evaluation design |
| superseded gates: V3's G0 against **V2**'s `R`; V2's `armgate` in its ad-hoc form | V4's G0 is against V3 (V4 plan §3.9); G5 becomes "matrix-composed equals switch-by-switch composed" | one reference generation back, one gate expressed against the matrix |
| `v3_runner.py:35` `A28_PULSED` | never referenced | — |

**One thing that looks dead and is not.** `SWEEPS_PER_EVAL_HIST` and the per-node census add a
Python frame per model call and are excluded from timing runs — it is tempting to call them
diagnostics. They are the input to the V4 plan §3.5 transfer factorisation and to §4.5-style
per-module tables. Dropping them would remove the only instrument that can answer I-17. Keep.

---

## 3. The driver side — *this is not harness*

> **Amended 2026-09-10 (amendment 2) by decision D20.** The user ruled: *"don't make changes
> considering backwards compatibility. If v3 would break we have to make a new process folder and
> modify that. Duplicate the code into `MDA_partitioning_experiment_v4/PROCESS`."* **V4 therefore
> runs its own copy of the whole `process/` package**, at
> `arch_surgery/MDA_partitioning_experiment_v4/PROCESS/process/`. **The copy is taken at the
> `architecture_surgery` commit current when task H0 runs** (user, 2026-09-10: *"yes, ensure it is
> the same commit"*), that commit is recorded in `PROCESS/PROVENANCE.json`, and a gate checks the
> copy **byte-for-byte against `git show <that commit>:process/`** — against the commit, never
> against a working tree, so an uncommitted edit in the source tree cannot ride along unnoticed. **Every V4 driver change below is made in the copy**;
> the repository-root `process/` stays as V2/V3's tree and is not touched for V4. The harness
> imports the copy by setting `PYTHONPATH` to `…_v4/PROCESS`, with the exact-tree assertion on
> `process.__file__`; the editable install is never relied on. Cost, measured: `du -sh process/`
> = **5.6 MB** over **224 tracked files** (171 Python; 3.0 MB of it `process/models/`, mostly the
> non-corona radiation data tables). That is what D20 adds to the repository.

**Everything in this section is a change to the copied `process/`, needs the user's approval
before merge (the D11 review rule), and carries its own switch-neutrality gate with teeth.** It is
written here only because the harness cannot be specified without knowing what it drives. **No
task that builds the harness may make these changes**; they are separate, separately approved.

**What D20 buys, and what it costs.** It buys the removal of every backwards-compatibility
constraint this plan was carrying: no environment override for code paths (DR6, dropped), no
`v3_compat` composition inside the reproduction gate (§7, restated), and no obligation on a V4
driver change to be expressible as "V3's behaviour when unset". It costs a second copy of the
physics, which is exactly the thing D5 freezes — so it comes with **gate G0′** (§7.6):
`…_v4/PROCESS/process/models/` must be **byte-identical to `c0ae5b28`** at every V4 commit, with a
tooth. A duplicated tree that nobody checks is how a frozen model quietly stops being frozen.

### 3.1 What exists today

Fourteen `PROCESS_ARCH_*` switches (inventoried in the root tree, which the copy starts as), all
read once at import, all guarded so that with everything unset the driver's behaviour is
byte-identical to upstream. Their refusals are already strict —
the two the harness leans on most are `subsolve.py:154-162` (**a pin without a lift refuses**:
without the lift, the model would overwrite the pin on the first sweep) and `caller.py:910-918`
(**a configuration naming iteration variable 178 refuses the pin**: the design-vector injection
at the head of every sweep would overwrite it — *"two owners is a refusal, not a race"*). Nine
counters are stamped as module-level globals in `caller.py`; a harness reads them by importing
`process.core.caller` **in the same process as the run** and reading them after it — which is why
the run driver must live inside the measurement subprocess, not outside it.

**Neutrality is numerical, not literal-source**, and V4's plan must not overclaim it: even with
every switch unset, `_SWEEP_CALLS[0] += 1`, `NODE_CALLS[0] += 1` inside the `_node` indirection,
the `try/finally` histogram binning in `call_models` and the `NODE_CALLS_AT_OUTPUT` freeze all
execute. All are integer-only, touch no float and change no branch a result depends on. That is
the discipline the file states for itself, and the G1-shape gates test it.

### 3.2 What V4 needs from the driver, and what each costs the harness

*Caption: one row per driver change V4 needs, **all of them made in `…_v4/PROCESS/process/`**
(D20). Status column records the user's ruling of 2026-09-10. "Harness impact" is what the harness
must do differently once the change exists; "if declined" is what the harness does instead. Every
accepted row carries its own switch-neutrality gate with teeth — under D20 "neutral" means *the
copy's behaviour before the change*, since there is no longer anything to be compatible with.
**DR3 was rejected and DR6 was dropped; both rows are kept, struck through in the status column,
so the record shows what was considered.***

| # | driver change | status (user, 2026-09-10) | harness impact | if declined |
|---|---|---|---|---|
| **DR1** | **Rename** `PROCESS_ARCH_HOIST` → `PROCESS_ARCH_DEFER_PER_CALL`, `PROCESS_ARCH_POST_SOLVE` → `PROCESS_ARCH_DEFER_PER_RUN` (names proposed here — **decision (1)**). Additionally: setting a **retired** name must **raise**, naming the new one | **accepted** | switch registry carries `retired_as`; the V3→V4 map lives in `harness/switches.py` and is used by G0 and by any V3 record read | the matrix keeps V3's names; every table and record field keeps `hoist`/`post_solve`; item 1d is not implemented |
| **DR2** | **Output path without `MDA_Output`** for the intervention arms: `write_output_files` calls `finalise` once on the accepted state, environment-switched | **accepted** | one more matrix row (`output_path`), one more recorded field, gate G9 | `B1`/`B3` keep the incumbent's second loop; the exit audit reads a state the flat loop has already relaxed twice, and the V4 plan's §3.3 claim about what the intervention *is* cannot be made |
| ~~**DR3**~~ | ~~**Empty-block / empty-node skipping**~~ | **REJECTED** — the user's ruling: the empty `PULSE` visits **stay**, and are **disclaimed** rather than fixed. They are one of PROCESS's oddities this experiment does not undertake to repair, and repairing them would change node weights | **none.** The harness composes nothing for it and records no `blocks_dropped` / `per_run_nodes_skipped` fields. **Instead — binding**: every per-sweep and per-block table caption must state that on `st_regression` the `PULSE` block is swept with **empty membership** (570 visits per run in `B3` — V3's measured figure, I-20a; V3 also measured 1 131 in `B2`, an arm D22 has since removed) and that those visits execute no model, so per-sweep node weights are not uniform across blocks | — (this *is* the declined branch) |
| **DR4** | **Predicate-evaluation and components-compared counters** | **accepted** (2026-09-10) | two more record fields; one more tally column; the V4 plan §3.5 check 5 | check 5 cannot be answered on counts and the per-sweep-overhead hypothesis stays open, or rests on a timing — which nothing may (I-10) |
| **DR5** | **Predicate mode `frozen \| mixed`** in the one coupling-state module both the copied driver and the harness import, recorded in every artifact preamble and every run record | **accepted** — *"clean this up for v4 anyway"* | `predicate_mode` becomes an arm/campaign parameter; artifacts gain a preamble field; G8 | the item 5a trial does not run; the frozen denominator stands with I-12 unaddressed |
| ~~**DR6**~~ | ~~**Environment overrides for the three hard-coded research-tree paths**~~ | **DROPPED under D20.** With V4 running its own copy of `process/`, the copy hard-codes its own paths (or imports normally), and the user's stated preference is copying over an opaque environment override — *"an env override for a code module means the record has to carry which module was loaded"*. Nothing needs an override | none — the copy's paths are the copy's business, and decisions (2) and (3) are settled by copying rather than by indirection | — |
| **DR7** | **Per-attempt node-call accounting** (amended 2026-09-10). Stamp `NODE_CALLS` and the sweep histogram at **each retry-ladder attempt boundary**, in the shape of the existing `NODE_CALLS_AT_OUTPUT` freeze (`caller.py:1825-1826`): integer-only, no float touched, no branch a result depends on, switch-neutral | **accepted** | the record gains `attempts[]` (§4.4); `stats.py` gains "retried seeds per arm" and "ratio with / without retried seeds" (§4.2); the failure table gains per-attempt columns; GR gains the summation tooth (§7.3) | **the headline stays partly an artefact of the mismatch**: node calls are run totals while `n_solver_iterations` and `ifail` are per VMCON attempt. Task A44 established from V3's records that this is most of `low_aspect_ratio_DEMO`'s published `B3/B0 = 0.450` — 0.659 without the one retried `B0` seed — and the V4 experiment plan §3.5 now requires the per-attempt figures and both ratios |

**On DR1's exact names.** The V4 experiment plan §3.2 marks them *proposed, fixed by the harness
implementation plan*. This plan proposes **`PROCESS_ARCH_DEFER_PER_CALL`** with values
`off | feedforward | feedforward_lifted` (unchanged semantics) and
**`PROCESS_ARCH_DEFER_PER_RUN`** taking the artifact path. Reasons: the shared `DEFER_` prefix
says the two are one ladder, which is item 1d's whole point; each name states the frequency the
node runs at; both are greppable and neither collides with an existing name. The alternative
`PROCESS_ARCH_PER_CALL` / `…_PER_RUN` reads as a frequency rather than an action and loses the
grouping. **The retired-name refusal is the load-bearing half**: today an unrecognised
`PROCESS_ARCH_*` name is simply ignored, so a stale caller setting `PROCESS_ARCH_HOIST` after the
rename would run the wrong arm under the right name — exactly the failure `env_for_phase_a`
refuses for the prime, and exactly what item 1d warns about. **Under D20 the retired names can
simply cease to exist in the copy** — nothing outside V4 imports it — so the refusal is a small
guard against a stale *caller*, not against a stale tree.

### 3.3 The three hard-coded paths from `process/` into `arch_surgery/`

*Caption: one row per path the driver resolves relative to its own file, with no environment
override and no fallback. These are why "everything in `harness/`" is not a pure harness
decision.*

| driver site | resolves to | read when | missing ⇒ |
|---|---|---|---|
| `caller.py:245-251` `NODE_WRITESET_PATH` | `arch_surgery/docs/data/node_writesets.json` | `per_call` deferral on (`caller.py:350`); `per_run` deferral on (`caller.py:583`) | `RuntimeError` naming the generator on the first path; **a raw `FileNotFoundError` on the second** — `caller.py:583` has no existence check. A one-line asymmetry worth fixing inside DR6 |
| `caller.py:356-362` `NODE_MAP_PATH` | `arch_surgery/docs/data/dsm_node_map.json` | deferral, `per_run`, and module-solve paths | checked on all three paths; `RuntimeError` |
| `module_solve.py:529-534` `YSTATE_MODULE_PATH` | `arch_surgery/fixedpoint/ystate.py` — **code, not data** | whenever `PROCESS_ARCH_MODULE_SOLVE` is on | `RuntimeError` |

The comment at `module_solve.py:524-528` states the reason the driver reaches for the file rather
than vendoring a copy: *"the research tree is not an importable package, and vendoring a second
copy of the predicate into `process/` would create exactly the drift D14(c) exists to prevent."*
That reasoning is right and V4 must not break it. **Amendment 2 (D20) resolves it by copying
rather than by indirection; amendment 3 settles exactly how.** In the V4 copy the three paths are
re-pointed *statically*, by **three path constants and nothing else**:

*Caption: the complete list of edits `…_v4/PROCESS/process/` receives at H0. Everything else in
the copied tree is byte-identical to the source commit, which is what makes H0's diff reviewable
by inspection.*

| constant | file in the copy | re-pointed to | settled by |
|---|---|---|---|
| `YSTATE_MODULE_PATH` | `core/solver/module_solve.py` | `…_v4/harness/ystate.py`, fixed relative path | decision (2), ruled option (v) |
| `NODE_WRITESET_PATH` | `core/caller.py` | `…_v4/harness/data/node_writesets.json` | decision (3), ruled |
| `NODE_MAP_PATH` | `core/caller.py` | `…_v4/harness/data/dsm_node_map.json` | decision (3), ruled |

**DR6 is dropped**: none of the three is an environment variable, so nothing is selectable at run
time and no run record has to carry "which module or artifact was loaded". The `caller.py:583`
missing-existence-check asymmetry is repaired in the copy as part of the same edit — it touches
the same constant's readers and is the one place where "beyond necessity" is worth spending a
second line. *Amended 2026-09-10, after A46 (process-copy) merged: the copy commit carries the
three constants and nothing else, so that it is reviewable by one tree hash; the one-line
existence check (now `caller.py:587` in the copy), the stale generator string at `caller.py:350`
and the two comments naming `docs/data/` sources land with **A48 (harness-data)**, the task that
gives the constant its target — each as a recorded hunk in `PROCESS/PROVENANCE.json` and a row in
`PROCESS_diff.py`'s annotation map.*

### 3.4 The rule the harness enforces against the driver

**An arm that composes a switch the tree does not recognise must refuse, never degrade.** V3 does
this for the prime alone, by hand, from a ledger (`v3_runner.py:137-143`). V4 does it for
**every** switch, by measurement (§4.2 `harness/switches.py`). The failure this prevents is
specific and has cost this project runs before: a switch the tree ignores produces a *successful*
run of a *different* arm under the right name, with no error anywhere — the same shape as traps
**T6** (a worktree does not redirect the editable install) and **T10** (`__version__` reports the
wrong commit in a frozen archive). It is the reason the run record must record **what the driver
resolved**, read back from the imported modules, and not what the harness asked for.

---

## 4. Target structure

### 4.1 The tree

```
arch_surgery/MDA_partitioning_experiment_v4/
├── EXPERIMENT_PLAN.md       the methodology (not this task's)
├── V4_EXPERIMENT_REPORT.md     written from the committed analysis only
├── experiment_runner.py        THE BUTTON: no arguments, owns the whole chain
├── phase_a.py                  Phase A stages
├── phase_b.py                  Phase B stages
├── analysis.py                 independent recomputation: --verify / --teeth / --tables
├── PROCESS/                    D20: V4's own copy of the code under test
│   ├── PROVENANCE.json           source tree, commit, date, per-file sha256
│   └── process/                  the copied package; every V4 driver change lives here
│       ├── models/                 FROZEN — byte-identical to c0ae5b28, gate G0' (§7.6)
│       └── core/                   caller.py, solver/ — the driver, where DR1/2/5/7 land
├── runs/                       untracked bulk artifacts (.gitignore: `runs/`)
└── harness/
    ├── README.md               what the package is, how a run flows, how to add an arm
    ├── __init__.py             version + the one public import surface
    ├── config.py               every declared setting; Config and Campaign dataclasses
    ├── switches.py             the driver's switch vocabulary + the capability probe
    ├── arms.py                 THE SWITCH MATRIX AS DATA -> environments; rung diffs
    ├── provenance.py           interpreter, tree, git stamp, environment stamp
    ├── artifacts.py            resolve + validate the committed per-configuration artifacts
    ├── data/                   D20: V4's own copy of the committed artifacts (decision (3))
    │                             ystate_a26_*, writeset_a26_*, postsolve_*,
    │                             node_writesets.json, dsm_node_map.json, PROVENANCE.json
    ├── decks.py                frozen configurations; derived decks as a committed stage
    ├── ystate.py               the coupling state and its predicate  (decision (2): RULED here)
    ├── predicate.py            thin: rebuild a spec from an artifact, residuals, snapshots
    ├── perturb.py              the seeded delta stream, one implementation, both phases
    ├── child.py                everything that runs INSIDE a measurement subprocess
    ├── optimise.py             child entry point: one full optimisation      (was run_one.py)
    ├── evaluate.py             child entry point: one call_models evaluation (was v2_eval_one.py)
    ├── pool.py                 jobs, isolation, the W-wide pool, resume
    ├── records.py              the run-record schema, extraction, completeness contract
    ├── census.py               the runtime read/write census stage (item 6a)
    ├── postsolve.py            derive the per_run node set; class-level classification
    ├── stats.py                the declared constructions, in one place
    ├── gates.py                Gate and Tooth as first-class objects
    └── tables.py               a table cannot be emitted without a caption
```

Twenty-one files in `harness/` (19 modules, `__init__.py`, `README.md`), plus `harness/data/` and
the copied `PROCESS/` tree. `phase_a.py`, `phase_b.py`, `experiment_runner.py` and `analysis.py`
stay at the top level because the user asked for the one-button layout and because they are what a
reader opens first. Everything else is `harness/`, importable as
`from harness import arms, config, gates`.

**Two D20 consequences for the layout** *(amendment 2, updated by amendment 3)*. `PROCESS/` is a
**sibling** of `harness/`, not a subdirectory of it: the harness sets `PYTHONPATH=…_v4/PROCESS` so
`import process` resolves there and nowhere else, and `harness/` itself must never shadow or wrap
it. And **`harness/ystate.py` does exist** — decision (2) is ruled **option (v)**: the whole
predicate module lives there, and the copied `module_solve.py` reaches it by one re-pointed path
constant at a fixed relative path (§3.3, §5.3). `harness/predicate.py` remains the thin layer above
it (spec rebuild from an artifact, snapshots, cross-state residual).

### 4.2 What each module is responsible for

**`config.py`** — every declared setting, in one place, as frozen dataclasses rather than module
globals: `Config` (name, `pulsed`, figure of merit, input path, artifact paths, expected
component count, `skips` — the arms inactive on it), `Campaign` (N, the δ tuple, τ, F, floors,
median construction, W, predicate modes), `EXECUTION_APPROVED`. **Configurations are a list, not
three constants** — the V4 plan's open decision (b) may add a fourth (one pulsed configuration
under a second figure of merit), and nothing downstream may assume three or assume that "pulsed"
means "one of two named strings".
**And the list must be able to shrink** *(amendment 3)*. `Config.skips` already records the arms
inactive on a configuration; the same mechanism must express **removing a configuration entirely
by a recorded decision**. The live case: if task **A43 (st-trust-gap)** shows `st_regression`'s
trust-mode `B3` unreliable, `st_regression` is dropped from the analysis and probably from the
experiment. When that happens **every table's population is re-derived, never patched** — a
denominator that was computed over three configurations and then edited down to two is trap
**T11** in its purest form. So the configuration list is read once, at the top, and every `n` in
every table descends from it; no count is ever written by hand.

**`switches.py`** — the driver's switch vocabulary as data: for each switch, its name, legal
values, its V3 name if renamed, whether it is composed or only cleared, and **how to read back
what the driver resolved**. Owns `clear_all(env)` and the **capability probe**: one child process
per distinct switch set that imports the driver modules and reports the resolved values, so
`assert_capable(arm, config)` fails loudly on a tree that does not implement a switch the arm
composes (§3.4). This replaces V3's hand-maintained `INSTRUMENTATION` ledger of booleans.

**`arms.py`** — the V4 plan §3.2 matrix transcribed as a `dict[str, Arm]` of frozen dataclasses,
one field per matrix row. Three functions and nothing else: `env_for(arm, config, *, seed,
pin_hex, predicate_mode)` builds the environment from nothing (clear, then set); `deck_for(arm,
config)` chooses frozen or derived; `rung(a, b)` returns the field-level difference between two
arms. `rung` is what makes the V4 plan's *"the harness refuses an arm pair whose declared
difference does not match its composed environments"* a computation instead of a promise.

**`provenance.py`** — the interpreter refusal (V3's `run_experiment._assert_interpreter`, which
exists because a wrong interpreter once got reported as a physics result), the **exact-tree**
assertion on `process.__file__` (trap **T6**: a prefix match passes on the main tree even when
running from a worktree; trap **T10**: never assert on `__version__`), and the git stamp
(`tree_git_head`, `branch`, `describe`, `dirty`, `contains_base_commit`). **Under D20 the asserted
tree is `…_v4/PROCESS`**, not the repository root, and the assertion is equality — which is
precisely the check that makes a copied tree safe.
**Two amendments (2026-09-10, amendment 2).** *(a)* **The dirty flag is split.** V3's stamp is
`git status --porcelain` non-empty, which counts **untracked** files as dirt: A44's records
stamped `tree_git_dirty = True` for that reason alone, while the measured code was clean. The
record therefore carries `tree_modified_tracked` (a `--porcelain` scan restricted to tracked
modifications — the thing that can change a measurement) **and** `tree_untracked_paths` (a count
plus the top-level paths, as context), and the old boolean is derived from the first, not from
both. A campaign refusing on untracked scratch files is a false alarm; a campaign passing over a
modified tracked file is the real failure. *(b)* The copy's own identity — `PROCESS/PROVENANCE.json`
(source tree, commit, date, per-file sha256) — is read and stamped into every record, so a record
names the code that produced it without depending on the worktree's git state.

**`artifacts.py`** — resolves each configuration's committed artifacts, validates each
(`format`, `components_sha256` rebuild, `i_figure_merit_expected`, the constraint set, and — new
— `predicate_mode`), and refuses by name with the stage that would produce it. Also the
preflight ledger, which becomes a *measured* table rather than a declared one.

**`decks.py`** — the frozen configurations (never edited, D9) and every derived deck as a
committed stage: the lifted deck's three-line edit (iteration variable 178, equality constraint
93 inside the equality block with the count raised in the same edit, and the initial value set to
the burn time the baseline's own loop settles on) and, if decision (b) is taken, the
second-figure-of-merit variant. Byte-identical output for the same input is a gate.

**`ystate.py`** — the coupling state: component spec, categories, scales, the residual, and **the
convergence predicate**, in both modes (`frozen`, `mixed`, DR5). Moved whole from
`arch_surgery/fixedpoint/ystate.py`; **decision (2) is ruled option (v)** *(amendment 3)*, so it
lives here and the copied `module_solve.py` reaches it through **one re-pointed path constant** at
a fixed relative path — no environment variable, so nothing about which module was loaded needs
recording. **Exactly one implementation per version** (D14(c) holds by construction under D20:
each version owns its own tree), and the `frozen` mode must reproduce V3's Phase A records
bit-for-bit, which is DR5's gate 1 and certifies the move at the same time.

**`predicate.py`** — the thin layer above it: rebuild a `YSpec` from a committed artifact with its
sha re-checked (V3's `load_spec_offline`), restore a snapshot into the layout `residual` takes,
and summarise a cross-state residual (V3's `_cross_residual`, made public).

**`perturb.py`** — `factor(seed, name, delta) = 1 + delta·u`, `u` uniform in `[−1, 1)` from a hash
of `(seed, name)`, and the two streams built on it: the Phase A entry-state stream keyed on
**component name**, and the Phase B start stream keyed on **iteration-variable number** (so a
lifted design vector one element longer still gives bit-identical factors to shared variables).
One implementation; V3 has it in `v2_eval_one` and re-imports it into `phase_a`.

**`child.py`** — everything that executes inside the measurement subprocess and is common to both
phases: install the perturbation hook, the per-node census (wrapping `Caller._node`), the entry
census, the exit-forensics hook, read back what the driver *resolved* from the imported modules,
take the uncharged exit audit at the declared position, and harvest the counters. This is the
deduplication of `run_one.py` against `v2_eval_one.py` and is the single highest-value and
highest-risk refactor in the plan (§8 R2).

**`optimise.py` / `evaluate.py`** — the two child entry points. `optimise.py` runs one full
optimisation through `SingleRun`; `evaluate.py` runs one `call_models` at a prepared entry state.
Each is an argument parser, a call into `child.py`, and a record write. Neither should exceed
~350 lines.
**`evaluate.py` additionally needs the stencil-point entry** *(amended 2026-09-10)*: the V4
experiment plan's §3.4 second Phase A regime is no longer δ = 0.001 but the **stencil regime** —
forward stencil points taken from the reference fixed point and backward points from each forward
exit, `2(nvar + 1)` evaluations per arm per configuration — because task **A44 (transfer-gap)**
measured that δ = 0.001 does not reproduce the in-loop regime. The reference implementation is
A44's `a44_eval_one.py` (`--x-fd-column I`, `--x-fd-sign +1|-1`), verified against the optimiser's
own arithmetic: `process/core/solver/evaluators.py:132-143` builds `xfor`/`xbac` as
`xv[j] * (1 ± numerics.epsfcn)` **on a copy** of the scaled design vector, one column at a time.
`evaluate.py` reproduces exactly that — the same multiplicative step on a copy, the column refused
rather than clamped when out of range — and records the `x_fd` block (§4.4).

**`pool.py`** — a `Job` is (phase, config, arm, seed, **regime**, output directory, flags) —
`regime` being `perturbed` at δ = 0.10 or a named `stencil` point (§4.2's `evaluate.py`). Running
one means: fresh subprocess, own working directory, `PYTHONPATH` set to **this** tree, timeout,
stdout/stderr to files, the record re-stamped with the job's identity. `resume` skips only a
directory holding a *complete, matching* record — a directory alone is never evidence of a
completed run. Jobs are never retried; a crash is a taxonomy row. The pool width is `W` with an
environment override, stamped per stage.

**`records.py`** — the run-record schema (§4.4): the field list as data, the extractor the tally
and the analysis both use, and the completeness contract (V3's G7: an `ok` record missing
`n_solver_iterations`, `ifail`, ladder stage, constraint residual vector or active set makes the
tally **refuse**).

**`census.py`** — the runtime read/write census stage (`PROCESS_IDF_PROBE=modules`, closed at the
`_call_models_once` boundary — traps **T1** and **T7**: ten models call their own `run()` from
`output()`, so hooking `run()` alone invents dependency edges). Produces `node_writesets` and the
read census improvement item 6a(a) asks for.

**`postsolve.py`** — derives each configuration's `per_run` node set from the census, classifying
read sites **by enclosing class, not by file prefix** (item 6a(a): `process/models/vacuum.py`
holds both `Vacuum` and `VacuumVessel`, and the prefix rule would silently mark a live read dead).

**`stats.py`** — every declared construction, once: nearest-rank upper-middle median
(`sorted[n // 2]`), nearest-rank p90, the accepted-optimum predicate (`status == ok` **and** MFILE
`ifail == 1`), the one Phase B seed set (every arm converged), the failure table, the clustering
rule and its resolution category, the pooled/median/worse-count ratio triple, and the seed
bracket. **Plus, from DR7** (amended 2026-09-10): **retried seeds per arm** (a seed whose record
carries more than one attempt), the cost ratio published **with and without** retried seeds, and
the failure table's per-attempt columns (`stage`, `epsfcn`, `ifail`, node calls). Each carries its
definition in its docstring, and the docstring is what the report's caption quotes.

**`gates.py`** — a `Gate` has a name, what it binds, a criterion, **at least one `Tooth`**, and a
record path; a gate with no tooth cannot be registered. `run()` returns PASS/FAIL with the record
written, and a failed gate stops the dependent stage and is reported with its numbers.
**Binding requirement from the user (2026-09-10):** **every verification gate V4 runs is
implemented inside `harness/` — none is imported from `arch_surgery/idf_probe/` or
`arch_surgery/fixedpoint/`, and none is invoked as a subprocess into them.** That includes the
gates V3 inherited from task machinery (G1/G2/G3/G3c's comparators, G4's doctoring, G5's
switch-equivalence, G6's warm equivalence, G7's completeness checker) and the new ones
(G0, G0′, G8, G9, GR). Where a V3 gate's *criterion* is reused, the criterion is restated in
`harness/gates.py` and its agreement with the V3 record is itself a gate result, not an assumed
equivalence.

**`tables.py`** — emits a table only with a caption stating units, what a row is, what a column
is, the population, and the construction (protocol §16). A caption-less call is a `TypeError`,
not a review comment.

### 4.3 Data flow, end to end

```
config.py declarations
   │
   ├─► decks.py       frozen config ──► derived deck (lifted / objective variant)   [stage: decks]
   ├─► census.py      runtime read/write census ──► node write sets                 [stage: census]
   ├─► postsolve.py   census ──► per_run node set per configuration                 [stage: per_run]
   └─► artifacts.py   resolve + validate ystate / writeset / per_run / node map     [stage: preflight]
                                   │
                        switches.py capability probe  ──► refuse if the tree lacks a switch
                                   │
                        arms.py  (arm, config, seed) ──► environment + deck path
                                   │
                        pool.py  Job ──► fresh subprocess, own cwd,
                                 PYTHONPATH = …_v4/PROCESS  (D20: V4's own copy)
                                   │
                    optimise.py / evaluate.py  ──►  child.py  ──► metrics.json
                                   │                (+ audit_residual, y_entry, y_exit,
                                   │                 perturbation, entry_census_series)
                        records.py  read + completeness contract
                                   │
                        stats.py ──► phase_a.stage_tally / phase_b.stage_tally ──► tally.json
                                   │
                        analysis.py  independent recomputation from the SAME records
                                   │
                        --verify: cell-by-cell against tally.json   --teeth: each comparison can fail
                                   │
                        tables.py ──► the report's tables, each with its caption
```

Two properties of that flow are deliberate. **The tally and the analysis start from the records,
not from each other** — I-18 and I-19 were both *"a declared definition reached one implementation
and not the other"*, and `--verify` is the only thing that catches it. And **every stage above the
dashed line is reachable from `experiment_runner.py`**, including its failure paths (protocol
§15): a dropped configuration, a refused arm, a failed gate.

### 4.4 The run-record schema

V3's record is a good baseline; it is ~90 top-level fields and the campaign proved it sufficient.
V4's is V3's, minus the dead, plus what the V4 plan requires, with one renaming rule.

*Caption: one row per change to V3's `metrics.json` schema. "Why" cites the plan item or the
inventory finding that requires it. Fields not listed are carried unchanged.*

| change | fields | why |
|---|---|---|
| **drop** | `mode`, `probe_env`, `probe_enabled`, `probe_mode`, `probe_module_present`, `probe`, `audit_at_call` | the four probe modes leave the run path (§2.6); the audit position is fixed |
| **rename** | `v3_*` → `v4_*`; `arch_hoist_*` → `arch_defer_per_call_*`; `arch_post_solve_*` → `arch_defer_per_run_*`; `arch_sequence_*` + `arch_prime_*` → `arch_arrangement_node` / `arch_arrangement_method` | item 1d; the V3→V4 map in `switches.py` is what lets G0 read a V3 record |
| **add — provenance** | `post_solve_totals` and the **full** `env_PROCESS_ARCH_*` list **in Phase A records too** | item 6a(b): V3's Phase A records carry `post_solve_totals: null` and no `PROCESS_ARCH_POST_SOLVE` entry although `phase_a.py:173` sets it, so a Phase A per-block table could not be read from the run's own record. Confirmed by direct inspection of `runs/phase_a/campaign/st_regression/A1/start001/metrics.json` |
| **add — predicate** | `predicate_mode` (`frozen`\|`mixed`) at top level **and in every artifact preamble** | item 5a trap (i): a `mixed` run whose record does not name the mode is indistinguishable from a `frozen` one after the fact |
| **add — audit** | `audit_position` (`entry_to_write_output_files`) | V4 plan §3.3: a residual table whose arms were audited at different points without saying so is the thing that must not happen |
| **add — output path** | `output_path` (`mda_output` \| `finalise_once`), `mda_output_sweeps` | DR2; and item 1b's first task is to commit the `MDA_Output` sweep count per run by arm and configuration |
| **add — counters** | `predicate_evaluations`, `components_compared` | DR4 / plan §3.5 check 5 |
| ~~add — schedule~~ | ~~`blocks_dropped`, `per_run_nodes_skipped`~~ | **removed 2026-09-10**: DR3 was rejected, so there is nothing to record. The empty-`PULSE` fact is carried in table captions instead (§3.2) |
| **add — regime** *(amended 2026-09-10)* | `regime` ∈ `perturbed` \| `stencil`; and for a stencil point the `x_fd` block `{column, sign, epsfcn, ixc, name, xcm_base_hex, xcm_hex}` | the V4 plan §3.4's second Phase A regime is the **stencil** regime, not δ = 0.001 (A44). The block is A44's, verbatim in shape, so a V4 record and an A44 record are readable side by side |
| **amend — provenance** *(amended 2026-09-10)* | `tree_modified_tracked` **and** `tree_untracked_paths` replace the single `tree_git_dirty` boolean, which is derived from the first only; plus `process_copy_provenance` (commit + tree sha of `…_v4/PROCESS`) | A44's records stamped `tree_git_dirty = True` purely because the scan counted **untracked** files while the measured code was clean. A campaign refusing on scratch files is a false alarm; one passing over a modified tracked file is the real failure |
| **add — per attempt** *(amended 2026-09-10)* | `attempts: [{stage, epsfcn, n_iterations, ifail, node_calls_solve_phase, sweeps}]`, one entry per retry-ladder attempt, in order | DR7. V3's record has `exit_forensics.attempts` for the solver-owned fields but **no node calls per attempt** — the cost is a run total while `n_solver_iterations` and `ifail` are per attempt. A44 measured what that costs: most of lad's `B3/B0 = 0.450`, which is 0.659 without the one retried `B0` seed. The run total stays and must equal the sum of the attempts, which is a gate (§7.3) |
| **add — campaign identity** | `v4_delta` (δ, null for a stencil point), `v4_run_kind` (`campaign`\|`gate`\|`smoke`\|`reference`) | Phase A runs two regimes (the row above); and V3's `v3_machinery_smoke` boolean generalises |
| **add — taxonomy** | `failure_class` ∈ `ok` \| `crashed` \| `refused` \| `unconverged` \| **`unconverged-at-cap`** \| `infeasible-at-audit` \| `machinery` | item 1: upstream's loop raises after ten passes, and `AR` at δ = 0.10 may hit it. That is a **finding about the shipped code**, not a machinery failure — and V3's first launch proved how badly the two can be confused |
| **keep, emphatically** | `tree`, `tree_git_head`, `tree_git_branch`, `tree_git_dirty`, `tree_contains_base_commit`, `process_file`, `python`, `pythonpath` | trap T6/T10; every one of V3's 599 records carried them and that is why the campaign is auditable |

### 4.5 Naming, and the map back to V3

`AR A0 A0p A1` / `BR B0 B1 B3` (V4 plan §3.2). V3's `R` becomes `BR`; V3's `A1u` is retired
(improvement item 0). The **V3 → V4 map** lives in `switches.py` as one dict covering arm names,
environment-variable names and record field names, and is used in exactly two places: gate G0's
reference lookup, and any V4 table that carries a V3 baseline. **A lookup that misses must raise**
— trap T11's shape is a check with no population, and the V4 plan makes it explicit: *"a gate that
cannot find its reference must refuse, not pass over an empty comparison."*

**`B2` is removed from the arm set — decision D22 (user, 2026-09-10)** *(amendment 3)*. Phase B is
**`BR` / `B0` / `B1` / `B3`**: **275 optimisations** (4 arms × 25 starts × 2 pulsed configurations,
plus 3 arms × 25 on `st_regression`, where `B1` degenerates to `B0`). `arms.py` transcribes the V4
experiment plan's §3.2 matrix, which no longer has a `B2` column, so the arm simply does not exist
in the table; **no rung, check, tally column or table may name `B0 → B2` or `B2 → B3`.** GR's
reference set (§7.1) is unaffected — it never held `B2`. The `verify` outer-loop mode remains a
**driver** capability (`PROCESS_ARCH_OUTER=verify`, the driver default) and is still what GR's
composition tooth perturbs; what is removed is the *arm*, not the switch.

### 4.6 What "minimal" costs, priced

*Caption: one row per capability a smaller harness would drop; "what is lost" is the specific
table or answer that becomes unavailable. The recommendation column is this plan's.*

| capability | cost to carry | what is lost if dropped | recommendation |
|---|---|---|---|
| per-node census on every campaign run | one Python frame per model call; excluded from timing runs anyway | the per-module tables (V3 report §4.5, §5.5.1), the per-block split, and the cost unit's own check (the per-name counts must sum to `node_calls_solve_phase`) | **keep** |
| `sweeps_per_eval` histogram | a `try/finally` per `call_models` | the transfer factorisation of V4 plan §3.5 — i.e. the answer to I-17 | **keep** |
| entry census (net electric power at each `call_models` entry) | one float per entry | the I-12 diagnostic: whether a seed's entries are infeasible, which is what makes the frozen denominator pathological | **keep** |
| exit forensics at *every* exit | five fields | the failure table of item 5b, and G7 | **keep** |
| per-pass residual trace (`PROCESS_ARCH_PASS_TRACE`) | a JSONL file per run | nothing V4 publishes; it is a debugging instrument | **drop from composition, keep as a driver capability** |
| timing repetitions | 3 serial repetitions per arm per configuration ≈ 45 optimisations | the wall-clock context section. **No conclusion may rest on it** (I-10) | **keep, cheapest form**, clearly labelled context |
| a second tally implementation (the analysis) | ≈ 30 % duplicated statistics | the only mechanism that caught I-18 and I-19 | **keep** — decision (6) |

---

## 5. What the harness owns, and what stays where it is

### 5.1 The three classes of thing

*Caption: one row per artifact or code asset the experiment depends on; "owner" is who is
responsible for it existing and being correct; "V4 stage" is the committed stage that produces or
validates it (protocol §15: no stage may exist only as a shell invocation).*

| asset | owner | V4 stage | committed where |
|---|---|---|---|
| frozen configuration decks `<config>.IN.DAT` | the study (D9 — never edited) | `preflight` validates presence and sha | `arch_surgery/idf_probe/scenarios/` (unchanged) |
| **derived decks** (lifted; objective variant) | **harness** | `decks` — derivation from the frozen deck, byte-identical for the same input | regenerated into `runs/_decks/` each campaign; the **derivation** is committed, the deck is not |
| `dsm_node_map.json` | the study (framework component C8; trap **T9** forbids reading the dependency-analysis repository's exports live) | `preflight` validates | **`…_v4/harness/data/`** — copied under D20, sha-gated against the `docs/data` original |
| `node_writesets.json` | the study | `census` can regenerate into the copy; `preflight` validates | **`…_v4/harness/data/`** — copied, sha-gated |
| `ystate_a26_<config>.json` (defines `y` and the scales) | the study | `artifacts --check` validates from the artifact's **own** `harvest_identity` block. **No `--derive` stage exists** — decision (4) | **`…_v4/harness/data/`** — copied, sha-gated |
| `writeset_a26_<config>.json` | the study | as above | **`…_v4/harness/data/`** — copied, sha-gated |
| `postsolve_<config>.json`, `postsolve_nolift_<config>.json` (the `per_run` sets) | **harness** | `per_run` — derivation with class-level classification and the runtime read census (item 6a) | **`…_v4/harness/data/`**; the derivation is a harness stage |
| the convergence predicate | **harness** | — | `…_v4/harness/ystate.py` — **decision (2), ruled option (v)**; the copied `module_solve.py` reaches it by one re-pointed path constant |
| the copied `process/` package | **V4** | the `copy` stage (H0) writes `PROCESS/PROVENANCE.json`; **gate G0′** (§7.6) re-checks `models/` at every V4 commit | `…_v4/PROCESS/` — 5.6 MB, 224 files |
| run records | harness | every campaign stage | `runs/` untracked; tallies and verdicts committed |

### 5.2 Where the artifacts live — **reversed by D20** *(amended 2026-09-10)*

This section originally recommended keeping the committed artifacts in `arch_surgery/docs/data/`
and having the harness only *resolve and validate* them. **Under D20 that recommendation is
reversed**, and the reversal is recorded rather than silently rewritten, because the original
reasons are worth reading against the new frame:

*Caption: one row per original reason to keep the artifacts in `docs/data/`, and what D20 does to
it. This is the audit trail of a changed recommendation, not a live argument.*

| original reason | what D20 does to it |
|---|---|
| **1. The driver reads three of them by hard-coded path**, so an artifact elsewhere is one `process/` cannot find | **gone**: the *copied* driver hard-codes `…_v4/harness/data/` statically. There is no override to forget on a gate or smoke run, because there is no override |
| **2. They are shared across revisions** — V2's and V3's records were made against these exact bytes, and gate GR re-runs V3 arms | **handled by the sha gate**: the copy is byte-identical to its `docs/data` original at copy time, proven once by sha256 and recorded with the source path and commit. GR then reads the same bytes through a different path |
| **3. They are not V4's** — `ystate_a26_*` came from A26/A31/A32; the node map and write sets are framework components | **restated, not denied**: the copy carries `PROVENANCE.json` naming the source path, its sha256 and the commit, so the copy says whose it is. Under D20 a version owning its own inputs is the point |

**RULED (2026-09-10): copy** `ystate_a26_*`, `writeset_a26_*`, `postsolve_*`,
`postsolve_nolift_*`, `node_writesets.json` and `dsm_node_map.json` into `…_v4/harness/data/`, with
**a one-off gate that each copy is byte-identical (sha256) to its `docs/data` original at copy
time** and a `PROVENANCE.json` naming the source path and commit. The copied `caller.py` is
re-pointed by **one path constant each** — `NODE_WRITESET_PATH` and `NODE_MAP_PATH` — which,
together with decision (2)'s `YSTATE_MODULE_PATH`, are the **only three edits the copied tree
receives** (§3.3). **V3's root `process/` keeps reading `docs/data/`** and is unaffected. *(The
user had asked whether this was a gates-only concern: it is not — under D20 the recommendation
flipped from resolve-in-place to copy, and this is the ruling on that flip.)*

### 5.3 The predicate module — **RULED: option (v)** *(amendment 3, 2026-09-10)*

**The ruling.** The whole predicate module goes to **`harness/ystate.py`**, and the copied
`module_solve.py` is re-pointed by **one path constant** — `YSTATE_MODULE_PATH` set to the harness
file at a **fixed relative path**, no environment variable. The reason given, and it is the right
one for this project: **do not modify the copied `process/` tree beyond necessity.** A one-line
constant change is the smallest edit that makes the copy self-consistent, and it keeps V4's
`process/` reviewable as "the tree at commit X plus three re-pointed path constants" rather than
as a tree with a new module in it.

*Caption: what the ruling settles, and what each part costs. "Edit to the copy" is the only thing
`…_v4/PROCESS/process/` receives beyond the copy itself.*

| | |
|---|---|
| **where the predicate lives** | `…_v4/harness/ystate.py` — the whole module, moved from `arch_surgery/fixedpoint/ystate.py`: component spec, categories, scales, residual, and the convergence predicate in both modes (`frozen`, `mixed`, DR5) |
| **how the copied driver finds it** | `module_solve.YSTATE_MODULE_PATH` re-pointed to that file by a **fixed relative path** from the copied module's own location. The existing `importlib` load stays; what goes is the *reach outside the experiment directory* |
| **why not an environment variable** | an env-selected *code* module forces the run record to carry the loaded module's path **and** hash, or two runs on different predicates are indistinguishable afterwards (improvement item 5a's trap (i)). A fixed path is unambiguous after the fact with nothing recorded |
| **edit to the copy** | one constant. Together with decision (3)'s two (`NODE_WRITESET_PATH`, `NODE_MAP_PATH` in `caller.py`), **three path constants are the only edits the copy receives at H0** |
| **how it is certified** | the `frozen`-mode predicate must reproduce V3's Phase A records bit-for-bit — which is also DR5's gate 1, so the move and the predicate trial are gated by one measurement |
| **`harness/predicate.py` still exists** | the thin layer above it: rebuild a `YSpec` from a committed artifact with its sha re-checked, restore snapshots, summarise a cross-state residual |

**Audit trail: the options not taken.** Four alternatives were considered and are recorded here
rather than deleted, because the reasoning is what makes the ruling legible. **(i)** an
environment-overridable path — retired: it makes the loaded module a run-time choice, which the
record would then have to disambiguate. **(ii)** leave the module in `arch_surgery/fixedpoint/`
and import it — retired: under D20 there is no reason for V4's driver to reach outside its own
experiment directory, and it fails the user's "everything from `/fixedpoint` in `/harness`"
instruction. **(iii)** copy it into `harness/` while the driver keeps reading `fixedpoint/` —
rejected outright: two predicates inside one version is the drift D14(c) exists to prevent, and it
would fail silently. **(iv)** move the predicate and residual into the copied driver at
`…_v4/PROCESS/process/core/solver/ystate.py` and import them normally — this plan's amendment-2
recommendation and the orchestrator's; **not taken**, because it adds a module to the copied tree
and the user's standing preference is to leave that tree as close to the copy as possible. (iv)
would have been marginally cleaner as Python; (v) is cleaner as *provenance*, and provenance is
what this experiment is built on.

### 5.4 The A18 harvest — **left as it is** *(amended 2026-09-10)*

`ystate_a26_<config>.json` was produced by `fixedpoint/gen_ystate.py` from
`arch_surgery/idf_probe/runs/a18/<config>/harvest/harvest.pkl` — 35 / 69 / 34 MB, **untracked by
policy**, in a repository that has destroyed untracked run artifacts three times (I-14, I-15,
I-16). So the artifacts that define the coupling state can be *verified* from the
`harvest_identity` block they carry (a file hash plus a content hash over the coupling-key set,
the model sequence and every design point's exact hex-float design vector) but not *regenerated*
without the pickles.

**The user's ruling (2026-09-10): *"do we need this harvest for v4? If not leave it as is."***
V4 does not need it. V4 uses the **committed** a26 artifacts and **never regenerates them** —
their scales `s_i` are the **frozen ruler**, and re-deriving them from a new harvest would change
what τ means and break comparability with V2, V3, A35 and A38, whose residual figures are quoted
on that ruler. So:

- **No `artifacts --derive` stage exists in the V4 harness.** Not disabled, not guarded — absent.
  There is nothing for `experiment_runner.py` to reach, and a campaign that finds an artifact
  missing **refuses** rather than deriving one.
- **`artifacts --check` validates from the artifact's own `harvest_identity` block** and from the
  sha of the `docs/data` original at copy time (§5.2), never from the pickles.
- **The gap is stated once**, in the V4 report's provenance section: the a26 scales are inherited
  from a harvest that is not committed, and V4 treats them as given.

This is the honest position and it costs nothing V4 wants. It would matter only to a future
revision that wanted a *different* ruler, which would then be re-deriving deliberately and would
need the harvest, or a new one, as its own task.

## 6. Non-negotiables, designed in rather than bolted on

*Caption: one row per binding rule from `CLAUDE.md` and the orchestration protocol; "where it
lives in the design" names the module that makes violating it hard, rather than the review that
would catch it.*

| rule | where it lives in the design |
|---|---|
| **One entry point owns the whole chain, failure paths included** (§15) | `experiment_runner.py` runs preflight → artifacts → gates → campaigns → tallies → analysis, and each of those returns a code rather than raising past it. A dropped configuration, a refused arm and a failed gate are *stages that report*, not exceptions that escape |
| **No stage exists only as a shell invocation** (§15) | every derivation in §5.1 — decks, census, `per_run` sets, artifact validation — is a stage of `experiment_runner.py`, not a `python -m …` line in a report |
| **Every gate can be shown to fail** (§12) | `gates.Gate` requires at least one `Tooth` at construction. A gate with no tooth is unregisterable, so "we forgot the tooth" is a `TypeError` at import, not an omission at review |
| **Every verification gate is reproduced inside `harness/`** *(user, 2026-09-10; added in amendment 2)* | `harness/gates.py` and its per-gate modules implement **every** gate V4 runs — G0, G0′, G1, G2, G3/G3c, G4, G5, G6, G7, G8, G9, GR. **Nothing is imported from `arch_surgery/idf_probe/` or `arch_surgery/fixedpoint/`, and nothing is invoked as a subprocess into them.** Where a criterion is inherited from a V3-era gate, the criterion is restated here and its agreement with the V3 record is a gate *result*, not an assumed equivalence |
| **`process/models/` stays frozen even in a copy** (D5, and D20's cost) | **gate G0′** (§7.6): `…_v4/PROCESS/process/models/` byte-identical to `c0ae5b28` at every V4 commit, with a 1-byte tooth. A duplicated tree nobody checks is how a frozen model quietly stops being frozen |
| **Every count carries its denominator** (§12, trap T11) | `stats.py` returns `(value, n, population_description)` triples, and `tables.py` will not emit a cell whose `n` is absent. The population phrase goes into the caption automatically |
| **Every table carries a caption** (§16) | `tables.emit(rows, caption=...)` — caption is a required keyword |
| **Fresh subprocess, own working directory, per run** | `pool.py` is the only place a PROCESS run starts; there is no in-process path. `OutputFileManager` holds file handles as class attributes and initialisation mutates a global, so two runs in one process contaminate each other |
| **`process.__file__` asserted against the exact tree** | `provenance.assert_tree(expected)` compares the resolved parent directory for **equality**, not prefix (trap T6), and never looks at `__version__` (trap T10) |
| **`PYTHONPATH` names the tree under test on every subprocess** | `pool.py`, unconditionally. **Under D20 that tree is `…_v4/PROCESS`** — a worktree does not redirect the editable install, and the editable install is never relied on at all |
| **No timing is evidence** | `stats.py` has no timing function. Timings are produced by one stage (`phase_b.stage_timing`), written to their own file, and `tables.py` refuses to place a timing column in an acceptance table |
| **Declared constructions stated in code** | `stats.py` docstrings *are* the declaration: nearest-rank upper-middle median, nearest-rank p90, accepted optimum = `status ok` **and** MFILE `ifail == 1`, the one seed set, the clustering rule. The report quotes the docstring |
| **Records stamp tree, commit, dirty and the full architecture environment** | `records.py` schema; and the arm's composed environment is recorded **as the driver resolved it**, read back from the imported modules, not as the harness asked (§3.4) |
| **Explicit staging, never `git add -A`** | the harness writes nothing outside `runs/` and its own directory; the task instructions carry the staging rule (protocol §12a — a bare `git add -A` once committed 21 character devices) |
| **`TaskStop`, never `pkill`** | documented in `harness/README.md`; each sandboxed shell call has its own PID namespace, so `ps` sees nothing from a sibling and `pkill` reports success while killing nothing (trap **T8**; A2 lost a set of runs to it) |
| **Correctness on `norm_objf`, never iteration variables** (D6) | `stats.accepted_optimum` and the check-1 statistic take `norm_objf` only; there is no iteration-variable comparator in the package |
| **Compare at matched achieved accuracy, not matched settings** | the exit audit is taken on the same ruler at the same position in every arm, and `stats.py`'s similarity verdict is computed before any cost ratio is reported. A pair failing similarity is reported as *not comparable in cost* |
| **A failed gate is a result** | `gates.Gate.run()` returns a verdict and writes its record; the caller stops the dependent stage. Nothing in the package retries a gate with different settings |

---

## 7. The reproduction gate for the rewrite itself

A rewritten harness that changes the measurement is not a rewrite. **Gate GR** is what proves it
did not, and it is a *precondition for the rewrite being accepted*, not a step of the campaign.

> **Restated 2026-09-10 (amendment 2) under D20.** GR is now **run once**, at the commit where
> `…_v4/PROCESS` is copied and **before any V4 driver change is made**, with the rewritten harness
> driving the untouched copy. At that moment the copy *is* V3's driver, so any difference from
> V3's records is the harness's — which is exactly and only what GR is for. After GR passes, the
> driver changes land one at a time, each gated by **its own** switch-neutrality (unset = the
> copy's pre-change behaviour) and by **G0′** (the frozen-physics check, §7.6). **The `v3_compat`
> composition is gone, and so is the design rule that every V4 driver change must be composable
> back to V3's behaviour** — under D20 there is nothing to be compatible with. The V3→V4 name map
> survives in one place only: GR's reference extraction (§7.4).

### 7.1 What it compares

*Caption: the GR reference set. One row per group of reference runs; "V3 record" is the path
under `arch_surgery/MDA_partitioning_experiment_v3/runs/` in the main checkout, at V3's campaign
commit `362c0b47`. `start000` is the **unperturbed** start and `start001` the first **perturbed**
one; Phase A seeds are 1-based, so `start001` is Phase A's first perturbed entry. The last two
rows were added on 2026-09-10 so that the Phase B perturbation stream is exercised — see below.*

| phase | V4 arm | V3 arm | runs | V3 record |
|---|---|---|---|---|
| B | `BR` | `R` | 3 (one per configuration) | `phase_b/campaign/<config>/R/start000/metrics.json` |
| B | `B0` | `B0` | 3 | `phase_b/campaign/<config>/B0/start000/metrics.json` |
| B | `B3` | `B3` | 3 | `phase_b/campaign/<config>/B3/start000/metrics.json` |
| A | `A0` | `A0` | 3 | `phase_a/campaign/<config>/A0/start001/metrics.json` |
| A | `A1` | `A1` | 3 | `phase_a/campaign/<config>/A1/start001/metrics.json` |
| **B — perturbed** | `B3` | `B3` | **3** | `phase_b/campaign/<config>/B3/start001/metrics.json` |
| **B — perturbed, lifted vector** | `B1` | `B1` | **2** (pulsed configurations only; `B1` degenerates to `B0` at `k = 0` and V3 did not run it on st) | `phase_b/campaign/<config>/B1/start001/metrics.json` |

**Twenty runs: fourteen optimisations and six single evaluations**, all driven against
`…_v4/PROCESS` **before any V4 driver change** (§7.2). Context cost, from V3's timings: roughly an
hour and a half at W = 3.

**Why the last two rows exist.** Every `start000` row is the *unperturbed* start, so without them
`perturb.py`'s **Phase B** stream is exercised by nothing in the gate. That stream is keyed on the
iteration-variable **number**, not on its position, precisely so that a lifted design vector — one
element longer, because the burn time becomes iteration variable 178 — still gives bit-identical
factors to every variable the two arms share. `B1 start001` on the two pulsed configurations is
where those two vector lengths meet, and is therefore the row that actually tests the keying;
`B3 start001` tests the same stream through the full intervention. The Phase A stream (keyed on
component name) is already exercised by the `A0`/`A1` rows, whose seeds are perturbed entries.

**Compared fields, all exact:** `node_calls_solve_phase`, `node_calls_total`, `n_model_calls`,
`n_prime_calls`, `exact.norm_objf` (hex float), `exit_audit.residual_max_hex`,
`module_solve_totals.{n_call_models, block_sweeps, outer_pass_hist, inner_sweeps_by_block}`,
`n_solver_iterations`, `mfile.ifail`, and for Phase A `node_calls_single_eval`,
`n_model_calls_sweeps`. No tolerance anywhere — these are counts and bit-comparisons, which is
the only kind of quantity this project accepts (I-10). *Amended 2026-09-10 at A49
(harness-reference)'s merge, from the records rather than from this list:* the optimisation phase
also compares `exit_forensics.n_solver_iterations_summed_over_attempts`, `exit_forensics.n_attempts`
and `exit_forensics.attempts[].n_solver_iterations` (check 2's second construction); the
evaluation phase compares `exact.objf` (no Phase A record carries `norm_objf` — without it six of
twenty entries would have had no objective bit-comparison), `n_prime_calls`,
`exit_audit.residual_max_hex`, the block-solver totals and `exit_forensics.n_attempts` (always 0
there, compared as a value); and the block-solver totals are present on **every** record, the
reference arm's in the never-entered shape (0 calls, empty histograms), and are compared as values
rather than marked not applicable — so a harness that entered the block solver under `BR`'s name
would move that zero. **20 entries, 270 compared values** (15 × 14 + 10 × 6);
`harness/reference.py` exports the list as `REFERENCE_FIELDS`.

### 7.2 When GR runs, and why once is enough *(restated 2026-09-10)*

**GR runs at one commit: the one that adds `…_v4/PROCESS` and the rewritten harness, before any
driver change.** At that commit the copied driver is byte-identical to the tree V3's campaign ran
on, so the only thing that has changed between V3's records and GR's runs is **the harness**. That
is a clean single-variable comparison, and it is the whole argument the rewrite needs.

The earlier version of this section proposed a `v3_compat` composition — every V4 driver change
environment-switched with V3's behaviour as its unset state, so GR could keep comparing after the
changes landed — and made "composable back to V3" a hard design rule on DR2–DR5. **D20 removes the
need and the rule.** V4 owns its tree; a change may be made outright rather than added as a switch
whose off-state imitates the previous revision. What replaces the continuing comparison is
narrower and stronger:

*Caption: one row per thing that used to be GR's job after the driver changes, and what does it
now. Each successor is a gate of the V4 experiment plan's §3.9 or of §7.6 below.*

| what needed proving | before (amendment 1) | now (D20) |
|---|---|---|
| the rewrite did not move the measurement | GR at every commit, through `v3_compat` | **GR once**, at the copy commit, before any change |
| a driver change is inert when its switch is unset | the same `v3_compat` composition, doing double duty | **G1**, per change: unset ⇒ byte-identical to the copy immediately before that change, three configurations, 1-ULP tooth |
| the physics did not move | not covered | **G0′** (§7.6): `PROCESS/process/models/` byte-identical to `c0ae5b28`, at **every** V4 commit |

**One consequence to hold to.** Because GR runs before the driver changes, a defect introduced by
a *later* driver change is caught by that change's own G1 and by G0′, not by GR. So G1 must be run
per change and never batched: three changes merged together with one G1 between them tells you
that the batch is inert, not which member is.

### 7.3 Teeth

*Caption: one row per tooth; each is a deliberately broken input that must make GR fail before
GR's zeros are accepted (protocol §12).*

| tooth | construction | must |
|---|---|---|
| count | add 1 to one reproduced count | FAIL |
| hex | append one character to one `norm_objf` hex string | FAIL |
| **missing reference** | point the comparator at a V3 record path that does not exist | **FAIL, not skip** — the V4 plan's G0 requirement, trap T11's shape: a check with no population is not a check |
| **missing key** | delete one compared field from a copy of the reference record | **FAIL, not skip** |
| **bad name map** | ask for V3 arm `BR` (which V3 never had) without the map | **RAISE** — the map is what makes `BR → R` legal, and a lookup that misses must raise |
| **composition** *(restated 2026-09-10)* | run `B3` with one switch of its composition deliberately wrong — `PROCESS_ARCH_OUTER` unset, so the run carries the **verified** outer loop under `B3`'s name | FAIL (the positive control: it proves GR is sensitive to *which arm* it ran, not merely to whether a run succeeded. The `v3_compat` tooth it replaces is gone with the composition itself, D20) |
| **attempt summation** *(added 2026-09-10, DR7)* | a record whose `attempts[]` node calls do **not** sum to `node_calls_solve_phase` | **REFUSED** — per-attempt accounting whose parts do not add up to the whole it replaces is worse than no per-attempt accounting, because the "with / without retried seeds" ratio would then be computed over quantities that do not decompose the published one |

### 7.4 The reference must not depend on untracked bulk

V3's `runs/` is untracked and this project has destroyed untracked run artifacts three times.
Before the rewrite starts, a small stage should extract the twenty reference records' compared
fields into **`harness/reference/reproduction_reference.json`** (§11.1's name; this section said `v3_reference.json` until A49 merged) — the field values, V3's campaign commit,
each source record's path and its sha256 — and commit it. GR then reads a committed file, with
the live records used only to *re-derive* it (a second stage, run once, whose output must match
byte-for-byte). Cost: one small stage and a ~10 KB committed file. Benefit: the gate survives the
next worktree removal.

### 7.5 What GR cannot cover, and what does *(added 2026-09-10)*

GR compares against V3's records, so it can only cover arms V3 ran. **Two V4 arms are new, and a
gate silent about what it does not cover is trap T11's shape.** Each is covered by a named gate of
the V4 experiment plan §3.9 instead, and the GR record states so.

*Caption: one row per V4 arm outside GR's reach; "covered instead by" is the gate that does test
the path, with its criterion. Neither substitute is a bit-comparison against a prior record,
because no prior record exists — both are internal consistency checks against a reference the run
itself produces.*

| arm | why GR cannot cover it | covered instead by |
|---|---|---|
| **`A0p`** (flat + lift + pin; improvement item 1c) | V3 never ran flat-with-pin: its Phase A pin appears only on the block arms, so there is no V3 record to reproduce | **G6, the warm-equivalence gate.** Pinned at the reference's *converged* burn time, `A0p` must reproduce the reference fixed point with cross-state maximum scaled residual `< τ` **and** the pinned component bit-identical. That is the same construction V3's G6 already passes on both pulsed configurations for the block arms, applied to the new arm |
| **`AR`** (Phase A reference: every switch unset; improvement item 1) | V3 had no Phase A reference arm at all | **a G1-shape check**: `evaluate.py` with every architecture switch cleared must reproduce the **first `call_models`** of `BR start000` on the counts that call records — node calls for the call, sweeps for the call, and the objective hex at its exit. Both sides are then upstream's own loop entered from the same state, so any difference is the harness's, which is exactly what the check is for |

Two consequences the plan holds to. **The GR record names both rows explicitly**, so a reader
sees the coverage boundary rather than inferring it from an arm's absence. And **`AR`'s
substitute cannot be run before `BR` reproduces** — it is anchored on a `BR` run — which fixes
its position in H3's gate order.

### 7.6 Gate G0′ — the physics stays frozen in the copy *(added 2026-09-10, D20)*

D20 puts a second copy of the models in the repository. **D5 freezes the models; a copy nobody
checks is how a frozen model quietly stops being frozen**, and it would fail silently — the run
would succeed and the numbers would be of different physics, which is the same shape as traps
**T6** and **T10**.

*Caption: gate G0′. It runs at **every** V4 commit, not once — it is a repository-state check, not
a measurement, so it costs seconds and there is no reason to run it less often.*

| | |
|---|---|
| **binds** | every V4 commit, every arm, both phases |
| **criterion** | every file under `…_v4/PROCESS/process/models/` is **byte-identical** (sha256, per file, plus the file *set*) to the same path at base commit `c0ae5b28`. The comparison is against `git show c0ae5b28:process/models/…`, not against the repository-root working tree, so a root-tree edit cannot mask a copy-tree edit or vice versa |
| **teeth** | a **1-byte** change to one model file — a single character in a comment is enough — must be caught; and a **file removed** and a **file added** must each be caught, since a per-file sha loop that never compares the file set would pass on both |
| **record** | `runs/gates/g0prime/gate.json`: the commit compared against, the file count, the per-file verdict summary, and the three tooth results |
| **on failure** | a result, not an obstacle: the campaign stops and the report states which model file differs. There is no "re-copy and continue" path — a divergence means something edited the physics, and finding out what is the finding |

**Why not simply diff the two `process/` trees?** Because the root tree is V2/V3's and may
legitimately carry driver changes of its own; only `models/` is claimed identical, and only
against `c0ae5b28`, which is the actual freeze (D2/D5). Comparing copy against root would pass
whenever both had drifted the same way.

## 8. Refactoring proposals, each with its cost and its risk

The user asked for these to be thought about and discussed rather than assumed. Each row is a
proposal; §9 turns the contested ones into decisions.

*Caption: one row per proposed change against the V3 design. "Cost" is implementation effort in
this plan's own units (S ≈ under half a day, M ≈ a day, L ≈ two or more). "Risk" is the chance of
silently changing a measurement, which is the only risk that matters here.*

| # | proposal | cost | risk | verdict |
|---|---|---|---|---|
| **R1** | **Arm composition as a declarative table.** The V4 plan §3.2 matrix becomes `dict[str, Arm]` of frozen dataclasses; `env_for` walks the fields. Replaces two divergent `if`-chains (`v3_runner.env_for`, `phase_a.env_for_phase_a`), whose asymmetries the inventory found. Gives `rung(a, b)` — the declared-difference check — for free | M | **low**: the composed environments are compared switch-by-switch against a hand-written expectation in gate G5, so a transcription error in the table fails a gate rather than a campaign | **propose** |
| **R2** | **One child-side instrumentation module.** `run_one.py`'s 1 000-line `main()` and `v2_eval_one.py`'s parallel body collapse into `child.py` plus two thin entry points | L | **medium-high** — it changes *both* measurement paths at once. Mitigated only by GR (§7), which is why GR must be built before this lands, not after | **propose, gated by GR** |
| **R3** | **Typed configuration.** Frozen dataclasses instead of module globals; configurations a list, not three constants; `Campaign` carries N, δ tuple, τ, F, floors, W, predicate modes | S | low | **propose** |
| **R4** | **Gate framework with teeth first-class.** `Gate(name, binds, criterion, teeth=[...], record=...)`; a gate without a tooth cannot be constructed | M | low | **propose** |
| **R5** | **Capability probe replacing the `INSTRUMENTATION` ledger.** A child imports the driver and reports what it *resolved*; an arm composing an unrecognised switch refuses | S–M | low, and it *removes* a risk: V3's ledger is hand-edited and consulted asymmetrically | **propose** — the orchestrator's brief requires the behaviour; this is how it is obtained by measurement rather than by declaration |
| **R6** | **Keep the tally and the analysis as two implementations** of the declared definitions, with `--verify` comparing cell by cell and `--teeth` doctoring records to show each comparison can fail | recurring ≈ 30 % duplication in `stats`-shaped code | low; the duplication is the instrument | **propose to keep** — decision (6). I-18 (26 of 144 cells) and I-19 were both caught by exactly this |
| **R7** | **A `smoke` mode runnable before execution approval**, including a one-seed end-to-end pass through campaign → tally → analysis → `--verify` | S | low | **propose** |
| **R8** | **Keep V3's `runs/` layout**, adding one level for the Phase A **regime**: `runs/phase_a/campaign/<config>/<arm>/d100/start001` (δ = 0.10) and `…/stencil/col07p/…` (column 7, forward) *(amended 2026-09-10: the second regime is the stencil, not δ = 0.001)* | S | low; changing the layout would force a second mapping in GR on top of the arm-name map | **propose** — decision (5) |
| **R9** | **Caption-required table emitter** (protocol §16 enforced by the signature) | S | low | **propose** |
| **R10** | **Record schema as declared data** plus the completeness contract, used by both the tally and the analysis | S–M | low | **propose** |
| **R11** | Merge the tally into the analysis (one implementation) | S (a deletion) | **high** — removes the mechanism that caught I-18 and I-19 | **reject**, unless the user prefers it (decision (6)) |
| **R12** | Have the harness own copies of the committed artifacts under `harness/data/` | S | ~~**high**~~ → **low under D20** — the objection was that the driver reads three of them by hard-coded path and a *missed environment override* would run against a different definition of `y` without erroring. With V4 owning its `process/` copy the paths are re-pointed **statically**: there is no override to miss | ~~reject~~ → **adopt** *(reversed 2026-09-10 by D20; see §5.2 and decision (3))*, with a one-off sha256 gate that each copy is byte-identical to its `docs/data` original and a `PROVENANCE.json` naming source path and commit |

---

## 9. Decisions for the user — **rulings of 2026-09-10 recorded** *(amendment 2)*

The user ruled on all eleven on 2026-09-10, in the same session that produced **D20** (V4 runs its
own copy of `process/`) and **D22** (`B2` removed from the arm set). The table below keeps each
decision's original recommendation and records the ruling; two rows changed recommendation because
D20 changed the frame, and both are marked. **All rows are now settled** — the last three, (2)'s
final choice, (3)'s approval and DR4, were ruled on the same date and are recorded here as
amendment 3.

*Caption: one row per decision. "Ruling" is the user's, 2026-09-10, or the state it is still in.
"Recommendation" is what the plan is written under; where D20 reversed it, both the old and the
new are shown so the change is auditable.*

| # | decision | recommendation | ruling |
|---|---|---|---|
| **1** | **Names for the two renamed deferral switches** (item 1d) | `PROCESS_ARCH_DEFER_PER_CALL` (`off \| feedforward \| feedforward_lifted`) and `PROCESS_ARCH_DEFER_PER_RUN` (artifact path); the retired names must **raise** if set | **ACCEPTED as recommended.** Under D20 the retired names can simply cease to exist in the copy; the refusal remains as a guard against a stale *caller* |
| **2** | **Where the convergence predicate lives** | *(reversed twice — see §5.3's audit trail)* | **RULED (v)** *(amendment 3)*: the **whole predicate module goes to `harness/ystate.py`**, and the copied `module_solve.py` is re-pointed by **one path constant** (`YSTATE_MODULE_PATH` → that file, fixed relative path, **no environment variable**). Reason, from the user: **do not modify the copied `process/` tree beyond necessity**. Options (i)–(iv) retired to §5.3's audit-trail note |
| **3** | **Where the committed artifacts live** | *(reversed by D20)* originally "keep in `docs/data/`, resolve and validate". **Now: copy** into `…_v4/harness/data/` with the sha256 gate and a `PROVENANCE.json` | **RULED as proposed** *(amendment 3)*: copy, sha-gated against `docs/data`, with `PROVENANCE.json`; the copied `caller.py` re-pointed by **one path constant each** (`NODE_WRITESET_PATH`, `NODE_MAP_PATH`). With decision (2)'s constant these are the **only three edits the copied tree receives**. V3's root `process/` keeps reading `docs/data/` |
| **4** | **The A18 harvest** — the artifacts defining `y` derive from 138 MB of untracked pickle no committed stage can regenerate without | *(replaced by the ruling)* **Leave it as it is.** V4 uses the committed a26 artifacts and never regenerates them; **no `--derive` stage exists** in the harness; `artifacts --check` validates from the artifact's own `harvest_identity` block; the gap is stated once in the V4 report's provenance section | **RULED: *"do we need this harvest for v4? If not leave it as is."*** V4 does not need it — the a26 scales are the **frozen ruler**, and regenerating them would change what τ means and break comparability with V2, V3, A35 and A38. §5.4 restated |
| **5** | **`runs/` layout** | Keep V3's, adding one level for the Phase A regime (`…/<arm>/d100/start001`, `…/stencil/…`) | **ACCEPTED as recommended** |
| **6** | **One tally implementation or two** | **Two** — tally and independent analysis computed separately, `--verify` comparing cell by cell. What caught I-18 (26 of 144 cells) and I-19 | **ACCEPTED as recommended** |
| **7** | **Smoke scope before execution approval** | `--mode smoke` on every stage **plus** a one-seed end-to-end pass (campaign → tally → analysis → `--verify`) while `EXECUTION_APPROVED = False` | **ACCEPTED as recommended** |
| **8** | **What the "minimal" harness drops** | Drop the four probe modes from the run path, `--exit-audit-at-call`, the A18-mode specs, the per-pass trace composition, and 19 of 20 `fixedpoint/` modules. **Keep** the per-node census, `sweeps_per_eval`, the entry census, the exit forensics | **ACCEPTED as recommended** |
| **9** | **The GR reference record** | Commit `harness/reference/v3_reference.json` — the twenty reference runs' compared fields, V3's commit, each source record's sha — **before** the rewrite starts | **ACCEPTED as recommended** |
| **10** | **Which driver changes are approved** *(all now made in `…_v4/PROCESS/process/`)* | DR1, DR2, DR4, DR5, DR7 approved; DR3 and DR6 as discussed | **DR1 accepted. DR2 accepted. DR3 REJECTED** — the empty `PULSE` visits stay and are **disclaimed** (node weights differ across blocks; one of PROCESS's oddities this experiment does not fix), and the disclaimer becomes a required clause in every per-sweep and per-block table caption. **DR4 ACCEPTED** *(amendment 3)*. **DR5 accepted** — *"clean this up for v4 anyway"*. **DR6 dropped** (D20 removes the need). **DR7 stands**. **Decision (10) is now fully ruled: DR1, DR2, DR4, DR5, DR7 approved; DR3 rejected; DR6 dropped** |
| **11** | **The three A18-era root scripts** | Leave frozen and untouched | **ACCEPTED as recommended** |
| **new** | **Every verification gate reproduced inside `harness/`** | — (raised by the user, not by this plan) | **REQUIRED.** No gate is imported from `arch_surgery/idf_probe/` or `arch_surgery/fixedpoint/`, and none is invoked as a subprocess into them. Stated in §4.2, §6 and H5 |

**Nothing is open** *(amendment 3, 2026-09-10)*. All eleven decisions plus the new gate
requirement are ruled, and decision (10) is fully settled — DR1, DR2, DR4, DR5, DR7 approved, DR3
rejected, DR6 dropped. One further ruling arrived with them and is carried through the plan:
**D22 — `B2` is removed from the arm set** (§4.5). The rebuild's first task (H0) is unblocked.

---

## 10. Proposed task decomposition for the rebuild

**Proposals only — only the user adds tasks** (protocol §8). Ordered; each row says what it
delivers and what gates it. The estimate column is honest rather than optimistic; V3's harness
took one task (A41) and produced two issues (I-18, I-19) that a later task had to repair.

*Caption: one row per proposed task; "gated by" is the check that must pass before the task is
merged, per protocol §6 (a failed gate blocks the merge and is reported as a result).*

| # | proposed task | delivers | gated by | size |
|---|---|---|---|---|
| **H0** | *v4-process-copy* *(new 2026-09-10, D20)* | `…_v4/PROCESS/process/` copied **at the `architecture_surgery` commit current when H0 runs** (user: *"yes, ensure it is the same commit"*), with `PROCESS/PROVENANCE.json` (source tree, that commit, date, per-file sha256); the **three re-pointed path constants** and nothing else (§3.3); `…_v4/harness/data/` with its own provenance; `harness/ystate.py` moved whole; the `.gitignore` for `runs/` | **the copy gate**: `PROCESS/process/` byte-for-byte against **`git show <that commit>:process/`** — against the commit, never a working tree, so an uncommitted source edit cannot ride along — with the three constants as the *only* permitted diff, listed and shown. **G0′** (§7.6): `PROCESS/process/models/` byte-identical to `c0ae5b28`, with the 1-byte / file-removed / file-added teeth. **And** every `harness/data/` file byte-identical (sha256) to its `docs/data` original. **No driver *behaviour* change in this task** | S, but **it must be its own task**: mixing the copy with an edit makes the copy unreviewable |
| **H1** | *harness-skeleton* | `config.py`, `switches.py`, `arms.py`, `provenance.py`, `harness/README.md`, the `experiment_runner.py` shell with preflight only | all nine arms compose on every configuration; `rung()` reproduces the V4 plan §3.2 rung table exactly; the capability probe **refuses** an arm whose switch the tree does not implement (tooth: ask for a switch name that does not exist); no PROCESS run yet | M |
| **H2** | *harness-reference* | the GR reference extraction stage and `harness/reference/v3_reference.json` (decision (9)) | the extracted file re-derives byte-identically from V3's records; a missing record path **refuses** | S |
| **H3** | *harness-run* | `child.py`, `optimise.py`, `evaluate.py` (including the stencil-point entry), `pool.py`, `records.py`, `perturb.py`, `predicate.py`; `harness/ystate.py` (decision (2), ruled option (v)) | **gate GR** (§7): twenty runs reproduce V3 bit-exactly on the listed fields, all seven teeth trip, including the `v3_compat` positive control and the DR7 attempt-summation refusal; plus §7.5's two substitutes for the arms GR cannot cover | **L — the largest single piece** |
| **H4** | *harness-artifacts* | `artifacts.py`, `decks.py`, `census.py`, `postsolve.py` and their stages | derived decks byte-identical to V3's; `per_run` sets re-derived equal to the committed ones **under the class-level classifier** (item 6a(a)), with any difference reported as a finding rather than absorbed; `artifacts --check` refuses on an absent harvest | M–L |
| **H5** | *harness-gates* | `gates.py` and **every** gate reimplemented inside `harness/` — G0, G0′, G1, G2, G3/G3c, G4, G5, G6, G7 (G8/G9 with their driver changes) | every gate PASSes with every tooth tripping at the V4 commit; G0 refuses on a missing reference key; **and the user's requirement is met literally: `grep` finds no import of, and no subprocess into, `idf_probe/` or `fixedpoint/` anywhere in `harness/`** — where a criterion is inherited from a V3-era gate, its agreement with the V3 record is reported as a gate result, not assumed | M–L *(larger than amendment 1 estimated: G1/G2/G3/G3c were previously inherited)* |
| **H6** | *harness-tally* | `stats.py`, `phase_a.stage_tally`, `phase_b.stage_tally`, `tables.py` | the tally reproduces V3's published cells for the GR reference runs; every declared construction of V4 plan §3.5 present, including item 6's within-cluster field **in the tally as well as the analysis** | M |
| **H7** | *harness-analysis* | `analysis.py` with `--verify`, `--teeth`, `--tables` | 0 mismatches over the full cell set with the denominator stated; every tooth trips; `--verify` refuses on an empty comparison | M |
| **H8** | *harness-smoke* | the one-seed end-to-end mode and the draft-mode chain in `experiment_runner.py` | a full one-seed pass on the cheapest configuration reaches a `--verify` with 0 mismatches, from the one button, with `EXECUTION_APPROVED = False` | S |
| **D-a…D-e** | *driver changes DR1, DR2, DR4, DR5, DR7* *(amended 2026-09-10: DR4 approved; DR3 rejected, DR6 dropped)* | one task each, **in `…_v4/PROCESS/process/`, never in the repository-root tree** | each: **G1** — with the switch unset, byte-identical to the copy *immediately before that change*, three configurations, 1-ULP tooth — **run per change and never batched** (§7.2); **G0′** at the same commit; the user's approval before merge *(D24, 2026-09-10: delegated — merged by the orchestrator on the gates alone; the physics freeze is unchanged)*. **DR7 additionally**: the per-attempt node calls must sum to `node_calls_solve_phase` on every record, with a tooth that breaks the sum and is refused | S–M each, four or five of them |

**Sequencing constraints that matter** *(restated 2026-09-10 under D20)*. **H0 first and alone** —
the copy is reviewable only if its diff contains nothing but the copy. H2 before H3 (GR needs its
reference committed first). **Every driver change lands after H3**, because **GR runs once, at the
copy commit, before any of them** (§7.2); a change merged before GR would put the harness rewrite
and a driver edit into one unexplained difference. H3 before H4 (the artifact stages are validated
by running the arms they feed). **DR7 should still land before H6**: the tally's declared
constructions include "ratio with / without retried seeds", and a tally written against records
lacking `attempts[]` would be rewritten rather than extended. **`AR`'s substitute check (§7.5) is
anchored on a `BR` run**, so it follows GR's `BR` rows inside H3's gate order. **G0′ runs at every
V4 commit**, H0 onward, including the harness-only ones — it costs seconds.

**Total scope, stated plainly.** ≈ 3 400 lines of new `harness/` code plus **821 moved verbatim**
(`ystate.py`), ≈ 1 450 lines across `phase_a.py` / `phase_b.py` / `experiment_runner.py`, ≈ 900
lines of `analysis.py` — ≈ **6 570** against the V3 stack's measured **8 828**, about a 26 %
reduction, **plus the 5.6 MB / 224-file `process/` copy D20 adds**. Plus **five** small driver
changes each with its own gate, and one reproduction gate of
twenty runs. The gain is not the line count: it is self-containment, one arm composition instead
of two, measured capability instead of a declared ledger, and a rewrite that is *provably* the
same measurement.
Anyone who expected "minimal" to mean an order of magnitude smaller should read §4.6 first: most
of what looks like bulk is the instrument.

---

## Appendix A — Change log

- **2026-09-10** — written by task **A45 (v4-harness-plan)** at branch point `16a6e87e`.
  Inventory taken at that commit; the V4 experiment plan and improvement-list items 1c and 1d
  were read **uncommitted** from the main checkout on the same date and may have moved since.
  Status **DRAFT · NOT APPROVED**; decisions (1)–(11) open. No code written; no file under
  `process/`, `idf_probe/`, `fixedpoint/`, `…_v2/` or `…_v3/` touched.
- **2026-09-10 — amendment 1, from the orchestrator's critical assessment (protocol §5).**
  **(A) Per-attempt node-call accounting added**: new driver change **DR7** in §3.2 (stamp
  `NODE_CALLS` and the sweep histogram at each retry-ladder attempt boundary, in the shape of the
  existing `NODE_CALLS_AT_OUTPUT` freeze); record field `attempts[]` in §4.4; the "retried seeds"
  and "with / without retried seeds" constructions in `stats.py` (§4.2); an attempt-summation
  tooth in §7.3; DR7 in decision (10) and in §10's task table, with the note that it should land
  before H6. Reason: node calls are recorded as **run totals** while `n_solver_iterations` and
  `ifail` are **per VMCON attempt**, and task **A44** established from V3's records that this
  mismatch is most of `low_aspect_ratio_DEMO`'s published `B3/B0 = 0.450` — 0.659 without the one
  retried `B0` seed. The V4 experiment plan §3.5 now requires both figures; that amendment landed
  after this plan first read it.
  **(B) Gate GR's coverage widened and its boundary named**: §7.1 gains `B3 start001` on all three
  configurations and `B1 start001` on the two pulsed ones — the **perturbed** Phase B starts,
  without which `perturb.py`'s Phase B stream (keyed on iteration-variable number, so a lifted
  design vector one element longer leaves shared variables bit-identical) was exercised by nothing
  in the gate. GR is now **twenty** runs, ≈ 1.5 h at W = 3. New **§7.5** names the two arms GR
  cannot cover and what covers them instead: `A0p` by the V4 plan's **G6** warm gate (pinned at the
  reference's converged burn time, reproducing the reference fixed point below τ with the pinned
  component bit-identical) and `AR` by a **G1-shape** check that `evaluate.py` with every switch
  cleared reproduces the first `call_models` of `BR start000` on that call's counts.
  **(C) Decision (2) gains option (iv)** — *the predicate is driver code*: split `ystate.py`, the
  predicate and residual to `process/core/solver/ystate.py` imported normally by both sides, the
  spec generation to `harness/`. Added to §5.3's table with the comparison to option (i), and to
  decision (2) with the orchestrator's recommendation of (iv) beside A45's (i). Consequently
  **DR6 is now stated conditionally** in §3.2 and decision (10).
  **(D) Decision (4) gains a binding rule**: `artifacts --derive` must **never** run inside a
  campaign — the a26 scales are part of the frozen ruler and regenerating them changes what τ
  means; derivation is a provenance stage only.
- **2026-09-10 — amendment 2, from the user's rulings and decision D20.**
  **The frame changed.** **D20** (user, verbatim intent): *"don't make changes considering
  backwards compatibility. If v3 would break we have to make a new process folder and modify that.
  Duplicate the code into `MDA_partitioning_experiment_v4/PROCESS`."* V4 now runs **its own copy of
  the whole `process/` package** at `…_v4/PROCESS/process/`, taken at a named commit with a
  `PROVENANCE.json`; every V4 driver change is made in the copy; the repository-root `process/`
  stays as V2/V3's tree; the harness sets `PYTHONPATH` to the copy with the exact-tree assertion
  and never relies on the editable install. Measured cost of the copy: **5.6 MB, 224 tracked
  files** (`du -sh process/`). Carried through: §1's verdict; §3's preamble, §3.2 and §3.3; §4.1's
  tree (`PROCESS/`, `harness/data/`); §4.3's data flow; §5.2, §5.3, §5.4; §6; §7; §8's R12; §9;
  §10.
  **Driver-change rulings.** DR1 accepted; DR2 accepted; **DR3 rejected** — the empty `PULSE`
  visits stay and are **disclaimed**, and the disclaimer is now a required clause in every
  per-sweep and per-block table caption (§3.2), with the `blocks_dropped` /
  `per_run_nodes_skipped` record fields removed (§4.4); **DR4 pending**; DR5 accepted; **DR6
  dropped** (D20 removes the need for path overrides); DR7 stands.
  **Gate changes.** §7 restated: **GR runs once**, at the copy commit, **before any driver
  change**, so the only variable is the harness; the **`v3_compat` composition and the
  "composable back to V3" design rule are gone**; GR's composition tooth is replaced by a
  wrong-switch positive control; the V3→V4 name map survives only inside GR's reference
  extraction. New **§7.6 gate G0′**: `…_v4/PROCESS/process/models/` byte-identical to `c0ae5b28`
  at **every** V4 commit, teeth for a 1-byte edit, a removed file and an added file. **G1 is run
  per driver change and never batched.**
  **Decisions (2) and (3) reversed by D20**, with the old reasoning kept visible as an audit
  trail: (2) recommends **option (iv)**, the predicate as driver code in
  `…_v4/PROCESS/process/core/solver/ystate.py`, with **option (v)** (the whole file in `harness/`
  at a fixed relative path) as the live alternative — the user prefers copying to an opaque
  environment override, and the final choice is pending; (3) recommends **copying** the committed
  artifacts into `…_v4/harness/data/` with a one-off sha256 gate and a provenance record, approval
  pending. **Decision (4)** settled: leave the harvest as it is, **no `--derive` stage exists**.
  **New binding requirement (user):** **every verification gate is implemented inside
  `harness/`** — none imported from `idf_probe/` or `fixedpoint/`, none invoked as a subprocess
  into them (§4.2, §6, H5).
  **Also carried:** the V4 experiment plan's §3.4 second Phase A regime is the **stencil** regime
  — forward stencil points from the reference fixed point and backward points from each forward
  exit, `2(nvar + 1)` evaluations per arm per configuration — not δ = 0.001, which A44 measured
  does not reproduce the in-loop regime; `evaluate.py` therefore needs the stencil-point entry
  (A44's `--x-fd-column` / `--x-fd-sign`, verified here against `evaluators.py:132-143`), and the
  record carries `regime` and the `x_fd` block (§4.2, §4.4). Provenance splits `tree_git_dirty`
  into `tree_modified_tracked` and `tree_untracked_paths`, because A44's records stamped dirty
  purely on untracked files (§4.2, §4.4). **§10 gains task H0** (*v4-process-copy*), which must be
  its own task so its diff is reviewable by inspection.
- **2026-09-10 — amendment 3: the final rulings. Nothing is open.**
  **Decision (2) RULED option (v)**: the **whole** predicate module goes to `harness/ystate.py`,
  and the copied `module_solve.py` is re-pointed by **one path constant** (`YSTATE_MODULE_PATH` →
  that file, a fixed relative path, **no environment variable**). Reason, from the user: **do not
  modify the copied `process/` tree beyond necessity**. §5.3 rewritten as the ruling with options
  (i)–(iv) retired to an audit-trail note; §4.1, §4.2, §2.5 and §5.1 restore `harness/ystate.py`.
  **Decision (3) RULED as proposed**: the committed artifacts are copied into `…_v4/harness/data/`
  with the sha256 gate against `docs/data` and a `PROVENANCE.json`; the copied `caller.py` is
  re-pointed by one constant each (`NODE_WRITESET_PATH`, `NODE_MAP_PATH`). **§3.3 now lists the
  three path constants as the complete set of edits the copied tree receives** — which is what
  makes H0's diff reviewable by inspection.
  **DR4 ACCEPTED**, so decision (10) is fully ruled: **DR1, DR2, DR4, DR5, DR7 approved; DR3
  rejected; DR6 dropped.**
  **D22 — `B2` is removed from the arm set.** Phase B is **`BR` / `B0` / `B1` / `B3`**, **275
  optimisations** (4 × 25 × 2 pulsed + 3 × 25 on st). `arms.py` transcribes a §3.2 matrix with no
  `B2` column; **no rung, check, tally column or table may name `B0 → B2` or `B2 → B3`**; GR's
  reference set is unaffected (it never held `B2`); the `verify` outer-loop mode survives as a
  *driver* capability and is still what GR's composition tooth perturbs (§4.5, §7.3). Carried into
  `config.py`: **`Config.skips` must also express removing a whole configuration by a recorded
  decision** — the live case is `st_regression` if A43 (st-trust-gap) finds its trust-mode `B3`
  unreliable — and when that happens **every table's population is re-derived, never patched**
  (trap T11).
  **The copy's commit RULED**: H0 copies `process/` at the **`architecture_surgery` commit current
  when H0 runs**, records it in `PROCESS/PROVENANCE.json`, and the copy gate compares
  **byte-for-byte against `git show <that commit>:process/`** — against the commit, never a working
  tree, so an uncommitted source edit cannot ride along (§3's preamble, H0's row).
  **No errata to the V3 report** (user); this plan proposes none and never did.
  Status **DRAFT · NOT APPROVED**; still no code; **all decisions settled**, the rebuild's first
  task (H0) unblocked.
- **2026-09-10 — amendment 4, at the merge of A46 (process-copy).** H0's copy is delivered and
  gated: `…_v4/PROCESS/process/` at `f2dc9243`, tree hash identical to the source commit; the
  three constants and nothing else; `models/` against `c0ae5b28` = `pulse.py` (D14(b)) alone;
  `copy-identity` and G0′ live in `PROCESS/copy_gates.py` with nine teeth, and `PROCESS_diff.py`
  claims every hunk. Two things measured there bind the run-path task: without `PYTHONPATH` the
  import lands in the **main checkout** (trap T6), and `process.__version__` is identical for the
  copy and the root tree and names a third commit (trap T10, live in this repository) — §6's
  exact-tree rule is the only witness. §3.3 amended: the `caller.py` existence check and the stale
  string move to **A48 (harness-data)**, minted for H0's remainder (§11.5). §10's H3 row still
  lists `harness/ystate.py`; it is A48's. The `…_v4/.gitignore` (`runs/`, and a `!*.dat`
  re-include for the copy's 42 data files) was added by the orchestrator at the merge.
- **2026-09-10 — amendment 5, at the merge of A47 (harness-skeleton) and decision D24.** H1 delivered
  and gated (five checks, 15 teeth; six shared arms equal V3's composition switch for switch). The
  orchestrator's five rulings at review — "deck" → input file with "frozen" reserved; `input_dir`
  under `harness/data/`; Phase A arms without the output-time-loop switch (`A1` runs before DR2);
  the `B0 → B1` wording; `--tree repository` preflight/self-check only — are recorded in §11.2 and
  approved by the user (D24). D24 also delegates the rest of the rebuild: every remaining task is
  minted (§11.5, A48–A60), the driver changes merge on their gates without a per-change approval,
  and one whole-implementation assessment closes it. Run directories are `seed000…`.

---

## 11. Approval, and the user's three notes (2026-09-10) — binding on every rebuild task

*"With these comments, the refactor for v4 is approved."* The three notes below override any
earlier name in this document; §11.4 maps the earlier names to their replacements.

### 11.1 No task numbers and no version tokens in file or method names

A file or function is named for **what it does**, never for the task that wrote it or the revision
it belongs to. `a44_eval_one.py` becomes `evaluate.py`; `v3_reference.json` becomes
`reproduction_reference.json`; record fields `v3_*`/`v4_*` become `campaign_*`; the plan and report
inside the versioned folder are `EXPERIMENT_PLAN.md` and `EXPERIMENT_REPORT.md` — the folder
`MDA_partitioning_experiment_v4/` carries the version. **Heritage lives in docstrings and
metadata**: a module's docstring names the file it descends from and the commit ("derived from
`arch_surgery/idf_probe/v2_eval_one.py` at `16a6e87e`; task A44 added the stencil-point entry"),
and `PROCESS/PROVENANCE.json` names the copy's source commit. Task labels (`A<n> (keyword)`) appear
in docstrings, change logs and reports — never in identifiers.

### 11.2 Terminology: assessed, homogenised, simplified

*Caption: one row per term the harness, the plan and the README use; the V3 words it replaces; the
reason. `A47 (harness-skeleton)` owns this table in `harness/README.md` and the switch registry; the
experiment plan's §1.3 follows it.*

| V4 term | replaces | why |
|---|---|---|
| **configuration** (`Config`) | deck, scenario, config | one word for one optimisation problem; "deck" is PROCESS jargon a reader does not know |
| **input file** — *committed* or *lifted* *(ruled 2026-09-10, orchestrator, at A47 (harness-skeleton)'s assessment)* | "deck" kept for the file; "frozen deck" / "lifted deck"; `deck_for()`; `scenario_dir`; the plan's `decks.py` | a configuration has two files, so the file needs a word, and it is the plain one: `input_file_for()`, `input_dir`, `harness/input_files.py`. **"frozen" is reserved** for the physics freeze and the predicate mode (`frozen \| mixed`) and names no file, field or matrix cell. The per-run deferral artifacts follow: `defer_per_run_{name}.json` for the committed input file (the unmarked default), `defer_per_run_lifted_{name}.json` for the lifted one |
| **arm** | arm, variant, arrangement | kept — one column of the switch matrix |
| **flat** / **partitioned** (switch values) | `flat_state` / `per_module` | say what the MDA is, not how V3 spelt it |
| **block loop**; **one τ** | inner loop / outer loop; `INNER_TAU`; trust / verify | there is one kind of loop and one tolerance (D23); "trust/verify" named an arm V4 does not have |
| **deferral `per_call` / `per_run`** | hoist / post-solve | item 1d; the name says the frequency |
| **arrangement · node** / **arrangement · method** | `SEQUENCE=build_after_physics` / `PRIME=fw_geometry` | both are *when* something runs; the prime is a method-level reorder (matrix rows) |
| **burn-time owner**: loop / constant / optimiser | lift, pin, `ixc 178`, constraint 93 | the matrix row; "lift" and "pin" survive only as the mechanism names in docstrings |
| **reference arm** `AR` / `BR` | `R`, "PROCESS as shipped" | the phase in the name |
| **seed** (both phases) | seed (A) / start (B) | one word; Phase B's `start000` is seed 0. **Run directories are `seed000…`, not `start000…`** *(ruled 2026-09-10 at A47's assessment; approved, D24)* |
| **coupling state**, **coupling-state spec**, **write sets** | ystate, spec, writeset, harvest | plain nouns; "harvest" is the frozen ruler's origin and appears only in provenance |
| **output-time loop** | `MDA_Output`, idempotence loop | says when it runs |
| **stencil regime** / **δ regime** | E3/E3b, warm δ-stream | the two Phase A entry regimes by what displaces the state |
| **teeth**, **tally**, **analysis** | — | kept, each defined in the README in one sentence |

Switch names follow the terms: `PROCESS_ARCH_MDA = flat | partitioned`, `PROCESS_ARCH_TAU`,
`PROCESS_ARCH_ARRANGEMENT_NODE`, `PROCESS_ARCH_ARRANGEMENT_METHOD`, `PROCESS_ARCH_DEFER_PER_CALL`,
`PROCESS_ARCH_DEFER_PER_RUN`, `PROCESS_ARCH_BURN_TIME_OWNER = loop | constant:<hex> | optimiser`,
`PROCESS_ARCH_OUTPUT_LOOP = upstream | none`, `PROCESS_ARCH_PREDICATE = frozen | mixed`. The
retired V3 names raise if set (decision 1). `PROCESS_ARCH_OUTER` and `PROCESS_ARCH_INNER_TAU` are
retired with `B2` and D23. `A47` finalises the list; a name the driver copy does not implement is
refused by the capability probe, never ignored.

### 11.3 `PROCESS_diff.py` — where the experiment changed PROCESS, in one view

A top-level script beside `experiment_runner.py`. It reads `PROCESS/PROVENANCE.json` for the source
commit, runs `git diff <source commit>:process/ -- PROCESS/process/` (against the commit, never a
working tree), and prints an overview: per file, the lines added/removed and the switch or
mechanism each hunk serves (from a small annotation map in the harness — every hunk must be
claimed by a named switch or by "provenance/path constant", or the script flags it as unexplained);
a one-paragraph summary per driver file; and a confirmation that `process/models/` shows **no
diff** (gate G0′'s statement, restated for a reader). Options: `--full` for the raw diff,
`--markdown` for a table the report can include. It runs in seconds, needs no PROCESS run, and is
the reviewer's first stop before any driver-change merge.

### 11.4 The README is in plain language

`harness/README.md` explains, for a reader who has not followed the project: what the experiment
measures and why the models are frozen; what one run does, end to end; every term of §11.2 in a
sentence; how to run the button, the smoke and a single arm; how to add an arm or a configuration;
where records go and what a record contains; what the gates prove and what "teeth" are. No D-, I- or
A-numbers without their meaning beside them.

### 11.5 The rebuild tasks, as minted

*Caption: the proposed decomposition of §10 with the task labels the orchestrator minted on the
user's approval; sequencing as §10. Driver changes follow the reproduction gate.*

| plan task | minted as | scope |
|---|---|---|
| H0 | **A46 (process-copy)** | `PROCESS/process/` copied at the current tip, `PROVENANCE.json`, byte-identity gate against `git show`, the three path constants, `PROCESS_diff.py` |
| H1 | **A47 (harness-skeleton)** | `config`, `switches`, `arms`, `provenance`, the runner shell with preflight, `README.md`, the terminology table; no PROCESS run |
| H0, remainder | **A48 (harness-data)** *(minted 2026-09-10 at A46's merge; dispatched when A47 merges)* | `harness/data/` — the committed artifacts the copied driver and the harness read, each sha256-identical to its `docs/data/` original, named per §11.1/§11.2 and as the skeleton's environment composer asks, with their own `PROVENANCE.json`; `harness/ystate.py` moved whole; the two one-line copy edits of §3.3 (existence check, stale string) with `copy_gates.py`'s permitted-edit model generalised from constant names to recorded hunks; no PROCESS run |
| H2 | **A49 (harness-reference)** *(minted 2026-09-10, D24)* | the 20-record reproduction reference, extraction and verification stages |
| H3 | **A50 (harness-run)** | the run path; gate GR at the copy commit before any driver change; `seed000…` directories |
| H4 | **A51 (harness-artifacts)** | `artifacts`, `input_files` (the plan's `decks.py`), `census`, `postsolve` |
| H5 | **A52 (harness-gates)** | `gates.py`, every gate inside `harness/` |
| H6 | **A53 (harness-tally)** | `stats`, tally stages, `tables` — after DR7 |
| H7 | **A54 (harness-analysis)** | `analysis.py` |
| H8 | **A55 (harness-smoke)** | the one-seed end-to-end mode |
| DR1 | **A56 (driver-renames)** | switch names of §11.2, `OUTER` folded into `partitioned` |
| DR2 | **A57 (driver-output-path)** | `PROCESS_ARCH_OUTPUT_LOOP`; G9 |
| DR4 | **A58 (driver-predicate-counters)** | per-sweep and predicate counters |
| DR5 | **A59 (driver-predicate-mode)** | `frozen \| mixed` |
| DR7 | **A60 (driver-attempts)** | per-attempt accounting, before the tally |
