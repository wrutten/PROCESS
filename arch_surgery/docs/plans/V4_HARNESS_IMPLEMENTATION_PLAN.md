# V4 harness — implementation plan

> **Document status** — **DRAFT · NOT APPROVED. PLAN ONLY, NO CODE WRITTEN.** Opened
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
> [`../MDA_partitioning_experiment_v4/V4_EXPERIMENT_PLAN.md`](../../MDA_partitioning_experiment_v4/V4_EXPERIMENT_PLAN.md)
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
| **τ** (tau) | the convergence tolerance on `y`, per component, scaled: `max_i |Δy_i| / s_i < τ`. τ = 1e-6 |
| **configuration** (V3's "deck") | one input file defining one optimisation problem: `large_tokamak_nof` (nof), `low_aspect_ratio_DEMO` (lad), `st_regression` (st). Display term is "configuration"; identifiers in code and records still say `deck` |
| **arm** | one assignment of the driver's environment switches. Phase A arms `AR A0 A0p A1`; Phase B arms `BR B0 B1 B2 B3` |
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

**So "self-contained in `harness/`" is achievable and cheap** — with **one exception the user
has to rule on**: `process/core/solver/module_solve.py:529-534` loads
`arch_surgery/fixedpoint/ystate.py` **by absolute path**, and `process/core/caller.py:245-251`
and `:356-362` read `arch_surgery/docs/data/node_writesets.json` and `dsm_node_map.json` the same
way. The driver reaches into the research tree at three fixed paths with no environment
override. Moving those files into a *version-numbered* experiment directory would make
`process/` depend on `…_v4/`, and V5 would move it again. §5 and decision **(2)/(3)** propose
the resolution: make the three paths environment-overridable with today's values as defaults, so
`harness/` can own its copies without the driver ever depending on a versioned directory.

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
   measurement is not a rewrite, it is a new experiment.

**Cost, honestly.** The V3 stack measures **8 828 lines** (`wc -l` over the six V3 files plus
`run_one.py`, `v2_eval_one.py`, `run_a28.py`, `a25_variant_deck.py` and `fixedpoint/ystate.py`).
The proposed V4 stack estimates at **≈ 6 570**: `harness/` ≈ 4 220 of which **821 are
`ystate.py` moved verbatim**, the three top-level scripts ≈ 1 450, `analysis.py` ≈ 900. That is
roughly a **26 % reduction** *and* self-containment — not a dramatic shrink, because most of the
V3 code is load-bearing measurement, not accident. Anyone expecting "minimal" to mean "a few
hundred lines" should read §4.6, which prices what minimality costs in lost diagnostics.

**What needs the user.** §9 lists eleven decisions. Three are load-bearing: where the
convergence-predicate module lives (**2**), what happens to the A18 harvest the committed
artifacts derive from and which no committed stage can regenerate (**4**), and the names of the
two renamed deferral switches (**1**).

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
| `fixedpoint/ystate.py` (the predicate) | **decision (2)** | recommended: **move** to `harness/ystate.py` with the driver's path made environment-overridable |
| `docs/data/*.json` artifacts | **decision (3)** | recommended: **resolve + validate** in place; `harness/artifacts.py` owns resolution, sha checking and the refusals |
| the a26 artifact **derivation** | **stage, partially** | `harness/artifacts.py` gains `--check` (validate) and `--derive` (regenerate); the harvest it derives from is **decision (4)** |
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

**Everything in this section is a change to `process/`, needs the user's approval before merge
(the D11 review rule), and carries its own switch-neutrality gate with teeth.** It is written
here only because the harness cannot be specified without knowing what it drives. **No task
that builds the harness may make these changes**; they are separate, separately approved.

### 3.1 What exists today

Fourteen `PROCESS_ARCH_*` switches, all read once at import, all guarded so that with everything
unset the driver's behaviour is byte-identical to upstream. Their refusals are already strict —
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

*Caption: one row per driver change the V4 experiment plan requires (its §3.7 decision (d), plus
the renames of improvement-list item 1d). "Harness impact" is what the harness must do
differently once the change exists; "if declined" is what the harness does instead.*

| # | driver change | harness impact | if declined |
|---|---|---|---|
| **DR1** | **Rename** `PROCESS_ARCH_HOIST` → `PROCESS_ARCH_DEFER_PER_CALL`, `PROCESS_ARCH_POST_SOLVE` → `PROCESS_ARCH_DEFER_PER_RUN` (names proposed here — **decision (1)**). Additionally: setting a **retired** name must **raise**, naming the new one | switch registry carries `retired_as`; the V3→V4 map lives in `harness/switches.py` and is used by G0 and by any V3 record read | the matrix keeps V3's names; every table and record field keeps `hoist`/`post_solve`; item 1d is not implemented |
| **DR2** | **Output path without `MDA_Output`** for the intervention arms: `write_output_files` calls `finalise` once on the accepted state, environment-switched | one more matrix row (`output_path`), one more recorded field, gate G9 | `B1`/`B2`/`B3` keep the incumbent's second loop; the exit audit reads a state the flat loop has already relaxed twice, and the V4 plan's §3.3 claim about what the intervention *is* cannot be made |
| **DR3** | **Empty-block / empty-node skipping**: drop a block whose membership is empty after deferral; skip a `per_run` node whose measured write set is empty | nothing to compose; the harness records `blocks_dropped` and `per_run_nodes_skipped` and the tally reports them | st keeps 570–1131 empty `PULSE` visits per run (I-20a); item 3's per-sweep-overhead question keeps a confound |
| **DR4** | **Predicate-evaluation and components-compared counters** | two more record fields; one more tally column; the V4 plan §3.5 check 5 | check 5 cannot be answered on counts and the per-sweep-overhead hypothesis stays open, or rests on a timing — which nothing may (I-10) |
| **DR5** | **Predicate mode `frozen \| mixed`** in the one coupling-state module both driver and harness import, recorded in every artifact preamble and every run record | `predicate_mode` becomes an arm/campaign parameter; artifacts gain a preamble field; G8 | the item 5a trial does not run; the frozen denominator stands with I-12 unaddressed |
| **DR6** | **Environment overrides for the three hard-coded research-tree paths** (§3.3) — *this one is proposed by this plan, not by the experiment plan* | `harness/` can own the predicate module and, if wanted, the artifacts | the harness cannot be self-contained for those files; decision (2)/(3) resolve to "resolve in place" |

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
refuses for the prime, and exactly what item 1d warns about.

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
That reasoning is right and V4 must not break it. **DR6 keeps it and adds one degree of freedom**:
each of the three becomes `os.environ.get("PROCESS_ARCH_<NAME>", <today's path>)`, so the default
is byte-identical (switch-neutral by construction — an unset override cannot change anything) and
a harness may point the driver at its own copy *while there is still exactly one implementation in
play per run*, recorded in the run record.

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
├── V4_EXPERIMENT_PLAN.md       the methodology (not this task's)
├── V4_EXPERIMENT_REPORT.md     written from the committed analysis only
├── experiment_runner.py        THE BUTTON: no arguments, owns the whole chain
├── phase_a.py                  Phase A stages
├── phase_b.py                  Phase B stages
├── analysis.py                 independent recomputation: --verify / --teeth / --tables
├── runs/                       untracked bulk artifacts (.gitignore: `runs/`)
└── harness/
    ├── README.md               what the package is, how a run flows, how to add an arm
    ├── __init__.py             version + the one public import surface
    ├── config.py               every declared setting; Config and Campaign dataclasses
    ├── switches.py             the driver's switch vocabulary + the capability probe
    ├── arms.py                 THE SWITCH MATRIX AS DATA -> environments; rung diffs
    ├── provenance.py           interpreter, tree, git stamp, environment stamp
    ├── artifacts.py            resolve + validate the committed per-configuration artifacts
    ├── decks.py                frozen configurations; derived decks as a committed stage
    ├── ystate.py               the coupling state and its predicate  (decision (2))
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

Twenty-one files. `phase_a.py`, `phase_b.py`, `experiment_runner.py` and `analysis.py` stay at the
top level because the user asked for the one-button layout and because they are what a reader
opens first. Everything else is `harness/`, importable as
`from harness import arms, config, gates`.

### 4.2 What each module is responsible for

**`config.py`** — every declared setting, in one place, as frozen dataclasses rather than module
globals: `Config` (name, `pulsed`, figure of merit, input path, artifact paths, expected
component count, `skips` — the arms inactive on it), `Campaign` (N, the δ tuple, τ, F, floors,
median construction, W, predicate modes), `EXECUTION_APPROVED`. **Configurations are a list, not
three constants** — the V4 plan's open decision (b) may add a fourth (one pulsed configuration
under a second figure of merit), and nothing downstream may assume three or assume that "pulsed"
means "one of two named strings".

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
(`tree_git_head`, `branch`, `describe`, `dirty`, `contains_base_commit`).

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
convergence predicate**, in both modes (`frozen`, `mixed`). Moved verbatim from
`arch_surgery/fixedpoint/ystate.py` under decision **(2)**; the `mixed` mode is DR5. **There is
exactly one implementation and both the driver and the harness import it** (D14(c)).

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

**`pool.py`** — a `Job` is (phase, config, arm, seed, amplitude, output directory, flags). Running
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
bracket. Each carries its definition in its docstring, and the docstring is what the report's
caption quotes.

**`gates.py`** — a `Gate` has a name, what it binds, a criterion, **at least one `Tooth`**, and a
record path; a gate with no tooth cannot be registered. `run()` returns PASS/FAIL with the record
written, and a failed gate stops the dependent stage and is reported with its numbers.

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
                        pool.py  Job ──► fresh subprocess, own cwd, PYTHONPATH=this tree
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
| **add — schedule** | `blocks_dropped`, `per_run_nodes_skipped` | DR3 |
| **add — campaign identity** | `v4_amplitude` (δ), `v4_run_kind` (`campaign`\|`gate`\|`smoke`\|`reference`) | two Phase A amplitudes; and V3's `v3_machinery_smoke` boolean generalises |
| **add — taxonomy** | `failure_class` ∈ `ok` \| `crashed` \| `refused` \| `unconverged` \| **`unconverged-at-cap`** \| `infeasible-at-audit` \| `machinery` | item 1: upstream's loop raises after ten passes, and `AR` at δ = 0.10 may hit it. That is a **finding about the shipped code**, not a machinery failure — and V3's first launch proved how badly the two can be confused |
| **keep, emphatically** | `tree`, `tree_git_head`, `tree_git_branch`, `tree_git_dirty`, `tree_contains_base_commit`, `process_file`, `python`, `pythonpath` | trap T6/T10; every one of V3's 599 records carried them and that is why the campaign is auditable |

### 4.5 Naming, and the map back to V3

`AR A0 A0p A1` / `BR B0 B1 B2 B3` (V4 plan §3.2). V3's `R` becomes `BR`; V3's `A1u` is retired
(improvement item 0). The **V3 → V4 map** lives in `switches.py` as one dict covering arm names,
environment-variable names and record field names, and is used in exactly two places: gate G0's
reference lookup, and any V4 table that carries a V3 baseline. **A lookup that misses must raise**
— trap T11's shape is a check with no population, and the V4 plan makes it explicit: *"a gate that
cannot find its reference must refuse, not pass over an empty comparison."*

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
| `dsm_node_map.json` | the study (framework component C8; trap **T9** forbids reading the dependency-analysis repository's exports live) | `census`/`preflight` validate; a regeneration path exists but is not run per campaign | `arch_surgery/docs/data/` (unchanged) |
| `node_writesets.json` | the study | `census` can regenerate; `preflight` validates | `arch_surgery/docs/data/` (unchanged) |
| `ystate_a26_<config>.json` (defines `y` and the scales) | the study | `artifacts --check` validates against the recorded harvest identity; `artifacts --derive` regenerates **if the harvest is present** — **decision (4)** | `arch_surgery/docs/data/` (unchanged) |
| `writeset_a26_<config>.json` | the study | as above | `arch_surgery/docs/data/` |
| `postsolve_<config>.json`, `postsolve_nolift_<config>.json` (the `per_run` sets) | **harness** | `per_run` — derivation with class-level classification and the runtime read census (item 6a) | `arch_surgery/docs/data/`; the derivation is a harness stage |
| the convergence predicate (`ystate.py`) | shared: driver **and** harness | — | **decision (2)** |
| run records | harness | every campaign stage | `runs/` untracked; tallies and verdicts committed |

### 5.2 Why the artifacts are recommended to stay in `docs/data/`

Three reasons, in order of weight.

1. **The driver reads three of them** (§3.3). An artifact in `…_v4/harness/data/` is an artifact
   `process/` cannot find unless DR6 lands *and* the harness sets the override on every run —
   including gate runs, smoke runs and any future replay. One missed override is a run against a
   different definition of `y`, and it would not error.
2. **They are shared across revisions.** V2's and V3's records were made against these exact
   files; the reproduction gate (§7) re-runs V3 arms, and it must read the same bytes. A copy
   under `…_v4/` is a second file that can drift, which is D14(c)'s objection to vendoring.
3. **They are not V4's.** `ystate_a26_*` was derived by task A26/A31/A32; `node_writesets.json`
   and `dsm_node_map.json` are framework components. Putting them inside a version-numbered
   experiment directory says they belong to that revision, which they do not.

What the harness **does** own is the *resolution and validation*: `artifacts.py` is the only place
that names a path, every path is validated before any run, and a missing or mismatched artifact
refuses by name with the stage that would produce it. That satisfies the user's requirement — the
harness no longer *depends on `idf_probe/` code* to reach them — without moving shared data into a
versioned directory. **Decision (3)** puts the alternative to the user.

### 5.3 The predicate module is the genuine conflict

The user's instruction is that everything used from `/idf_probe` or `/fixedpoint` lives in
`/harness`. For `fixedpoint/`, that is exactly one file — `ystate.py` — and the driver loads it by
absolute path. Three options, in the order this plan ranks them:

*Caption: one row per option for the convergence-predicate module. "Two implementations?" is the
D14(c) question: does the option create a second copy that can drift from the one the driver runs?*

| option | self-contained? | two implementations? | cost |
|---|---|---|---|
| **(i) move to `harness/ystate.py`; driver path becomes `PROCESS_ARCH_PREDICATE_MODULE` with today's path as default** — *recommended* | yes | **no**, if `fixedpoint/ystate.py` is left as the frozen V2/V3 copy and a gate asserts the V4 copy reproduces it bit-for-bit in `frozen` mode | DR6 (a small driver change); one gate; the V4 harness sets the override on every run |
| (ii) leave it in `fixedpoint/`; `harness/predicate.py` imports it by the driver's own constant | no — one file stays outside | no | zero; but the user's instruction is not met and the buried `importlib` load survives, merely relocated |
| (iii) copy it into `harness/` and leave the driver pointing at `fixedpoint/` | yes, apparently | **yes** — two predicates, the driver running one and the audit running the other | rejected: this is precisely the failure D14(c) and `module_solve.py:524-528` are written against, and it would fail silently |

Option (i) also happens to be what DR5 (the `frozen | mixed` predicate trial) needs: the trial
requires *one* implementation with a mode, imported by both sides, and a neutrality gate proving
the default mode reproduces V3 bit-for-bit. That gate is the same gate that proves the move did
not change the predicate.

### 5.4 The A18 harvest — a chain that no committed stage can currently close

`ystate_a26_<config>.json` is produced by `fixedpoint/gen_ystate.py`, which reads
`arch_surgery/idf_probe/runs/a18/<config>/harvest/harvest.pkl`. Those files exist in the main
checkout (35 MB / 69 MB / 34 MB, dated 2026-09-01) and are **untracked by policy**. This project
has destroyed untracked run artifacts on worktree removal **three times** (I-14, I-15, I-16), and
I-14 cost the evidence behind a headline correction.

So today: the committed artifacts that define `y` — the quantity the whole experiment converges —
rest on 138 MB of untracked pickle that one `git worktree remove` deletes, after which
`gen_ystate.py --check` can no longer even verify them. The artifacts themselves already carry a
`harvest_identity` block (file hash plus a content hash over the coupling-key set, the model
sequence and every design point's exact hex-float design vector), so **verification is possible
from the artifact alone; regeneration is not**. **Decision (4)** asks the user which of three to
take. This plan does not resolve it unilaterally because the cheapest option (commit 138 MB)
changes what the repository holds.

---

## 6. Non-negotiables, designed in rather than bolted on

*Caption: one row per binding rule from `CLAUDE.md` and the orchestration protocol; "where it
lives in the design" names the module that makes violating it hard, rather than the review that
would catch it.*

| rule | where it lives in the design |
|---|---|
| **One entry point owns the whole chain, failure paths included** (§15) | `experiment_runner.py` runs preflight → artifacts → gates → campaigns → tallies → analysis, and each of those returns a code rather than raising past it. A dropped configuration, a refused arm and a failed gate are *stages that report*, not exceptions that escape |
| **No stage exists only as a shell invocation** (§15) | every derivation in §5.1 — decks, census, `per_run` sets, artifact validation — is a stage of `experiment_runner.py`, not a `python -m …` line in a report |
| **Every gate can be shown to fail** (§12) | `gates.Gate` requires at least one `Tooth` at construction. A gate with no tooth is unregisterable, so "we forgot the tooth" is a `TypeError` at import, not an omission at review |
| **Every count carries its denominator** (§12, trap T11) | `stats.py` returns `(value, n, population_description)` triples, and `tables.py` will not emit a cell whose `n` is absent. The population phrase goes into the caption automatically |
| **Every table carries a caption** (§16) | `tables.emit(rows, caption=...)` — caption is a required keyword |
| **Fresh subprocess, own working directory, per run** | `pool.py` is the only place a PROCESS run starts; there is no in-process path. `OutputFileManager` holds file handles as class attributes and initialisation mutates a global, so two runs in one process contaminate each other |
| **`process.__file__` asserted against the exact tree** | `provenance.assert_tree(expected)` compares the resolved parent directory for **equality**, not prefix (trap T6), and never looks at `__version__` (trap T10) |
| **`PYTHONPATH` names this tree on every subprocess** | `pool.py`, unconditionally — a worktree does not redirect the editable install |
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

### 7.1 What it compares

*Caption: the GR reference set. One row per reference run; "V3 record" is the path under
`arch_surgery/MDA_partitioning_experiment_v3/runs/` in the main checkout, at V3's campaign commit
`362c0b47`. `start000` is the unperturbed start; Phase A seeds are 1-based.*

| phase | V4 arm | V3 arm | runs | V3 record |
|---|---|---|---|---|
| B | `BR` | `R` | 3 (one per configuration) | `phase_b/campaign/<config>/R/start000/metrics.json` |
| B | `B0` | `B0` | 3 | `phase_b/campaign/<config>/B0/start000/metrics.json` |
| B | `B3` | `B3` | 3 | `phase_b/campaign/<config>/B3/start000/metrics.json` |
| A | `A0` | `A0` | 3 | `phase_a/campaign/<config>/A0/start001/metrics.json` |
| A | `A1` | `A1` | 3 | `phase_a/campaign/<config>/A1/start001/metrics.json` |

Fifteen runs: nine optimisations and six single evaluations. Context cost, from V3's timings:
under an hour at W = 3.

**Compared fields, all exact:** `node_calls_solve_phase`, `node_calls_total`, `n_model_calls`,
`n_prime_calls`, `exact.norm_objf` (hex float), `exit_audit.residual_max_hex`,
`module_solve_totals.{n_call_models, block_sweeps, outer_pass_hist, inner_sweeps_by_block}`,
`n_solver_iterations`, `mfile.ifail`, and for Phase A `node_calls_single_eval`,
`n_model_calls_sweeps`. No tolerance anywhere — these are counts and bit-comparisons, which is
the only kind of quantity this project accepts (I-10).

### 7.2 The composition problem, and the design rule it forces

V4's arms are **not** V3's arms: `B3` loses `MDA_Output` (DR2), gains empty-block skipping (DR3)
and may run a different predicate mode (DR5). Compared naively, `B3` **must** differ, and the gate
would be measuring V4's driver changes rather than the rewrite.

So GR runs a **`v3_compat` composition**: each V4 driver change is environment-switched with the
V3 behaviour as its *unset* state, and `arms.py` can emit any arm with those switches forced to
their V3 values. This is not extra machinery — it is the switch-neutrality requirement DR2–DR5
already carry, used deliberately. **It is also a hard design rule for DR2–DR5: any V4 driver
change that cannot be composed back to V3's behaviour makes the rewrite unverifiable.** If one of
them cannot (for instance if empty-block skipping is implemented as an unconditional fix rather
than a switch), that arm drops out of GR and the gate says so with the reason — a smaller gate
honestly described, never a silent pass.

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
| composition | run `B3` **without** the `v3_compat` switches | FAIL (this is the positive control: it proves GR is sensitive to the driver changes it is holding fixed) |

### 7.4 The reference must not depend on untracked bulk

V3's `runs/` is untracked and this project has destroyed untracked run artifacts three times.
Before the rewrite starts, a small stage should extract the fifteen reference records' compared
fields into **`harness/reference/v3_reference.json`** — the field values, V3's campaign commit,
each source record's path and its sha256 — and commit it. GR then reads a committed file, with
the live records used only to *re-derive* it (a second stage, run once, whose output must match
byte-for-byte). Cost: one small stage and a ~10 KB committed file. Benefit: the gate survives the
next worktree removal.

---

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
| **R8** | **Keep V3's `runs/` layout**, adding one level for the Phase A amplitude: `runs/phase_a/campaign/<config>/<arm>/d100/start001` and `…/d001/…` | S | low; changing the layout would force a second mapping in GR on top of the arm-name map | **propose** — decision (5) |
| **R9** | **Caption-required table emitter** (protocol §16 enforced by the signature) | S | low | **propose** |
| **R10** | **Record schema as declared data** plus the completeness contract, used by both the tally and the analysis | S–M | low | **propose** |
| **R11** | Merge the tally into the analysis (one implementation) | S (a deletion) | **high** — removes the mechanism that caught I-18 and I-19 | **reject**, unless the user prefers it (decision (6)) |
| **R12** | Have the harness own copies of the committed artifacts under `harness/data/` | S | **high** — the driver reads three of them by hard-coded path, and a missed override runs against a different definition of `y` without erroring | **reject** in favour of resolve-and-validate (decision (3)) |

---

## 9. Decisions for the user

*Caption: one row per open choice. "Recommendation" is what the rest of this plan is written
under; "if the other way" says what changes. Nothing here is decided.*

| # | decision | recommendation | if the other way |
|---|---|---|---|
| **1** | **Names for the two renamed deferral switches** (item 1d; the experiment plan defers this here) | `PROCESS_ARCH_DEFER_PER_CALL` (values `off \| feedforward \| feedforward_lifted`) and `PROCESS_ARCH_DEFER_PER_RUN` (artifact path). **And the retired names `PROCESS_ARCH_HOIST` / `PROCESS_ARCH_POST_SOLVE` must raise if set, not be ignored** | `PROCESS_ARCH_PER_CALL` / `…_PER_RUN` is the shorter alternative; keeping V3's names means item 1d is not implemented and every V4 table keeps the words "hoist" and "post-solve". If the retired-name refusal is declined, a stale caller silently measures the wrong arm under the right name |
| **2** | **Where the convergence predicate module lives.** `process/core/solver/module_solve.py` loads `arch_surgery/fixedpoint/ystate.py` by absolute path | **Move it to `harness/ystate.py`** and make the driver's path an environment override with today's value as the default (DR6), with a gate proving the V4 copy reproduces the frozen predicate bit-for-bit. Self-contained, one implementation per run | Leave it in `fixedpoint/` and import it (§5.3 option ii): everything else is self-contained, one file is not. **Do not** copy it (option iii) — two predicates that can drift is what D14(c) exists to prevent |
| **3** | **Where the committed artifacts live** (`ystate_a26_*`, `writeset_a26_*`, `postsolve_*`, `node_writesets.json`, `dsm_node_map.json`) | **Keep them in `arch_surgery/docs/data/`**; the harness owns resolution and validation, not the files. They are shared with V2/V3 and read by the driver by hard-coded path | Copy them under `…_v4/harness/data/`: literally self-contained, but requires DR6 *and* an override set on every single run including gates and smokes, and creates a second copy that can drift from the one V3's records were made against |
| **4** | **The A18 harvest** — the committed artifacts defining `y` derive from 138 MB of **untracked** pickle that no committed stage can regenerate without it, in a repository that has destroyed untracked run artifacts three times (I-14/I-15/I-16) | **(a)** add an `artifacts --check` stage that validates the committed artifacts against their recorded harvest identity and **refuses** when the harvest is absent rather than passing quietly; **and (b)** commit a small extracted "harvest identity + scales" record so the chain is auditable without the pickles | **(c)** commit the three `harvest.pkl` files (138 MB) — the only option that makes regeneration reproducible, at a real cost in repository size; or **(d)** accept the gap and state it in the V4 report's provenance section. This is the user's call because it changes what the repository holds |
| **5** | **`runs/` layout** | Keep V3's, adding one level for the Phase A amplitude (`…/<arm>/d100/start001`) | A flat run-id layout with a manifest is tidier but forces a second mapping inside GR, on top of the arm-name map, for no measurement benefit |
| **6** | **One tally implementation or two** | **Two** — the tally and the independent analysis compute the declared definitions separately and `--verify` compares them cell by cell. This is what caught I-18 (26 of 144 cells wrong) and I-19 | One implementation plus a golden-record test: ≈ 30 % less code, and the class of defect that has bitten twice becomes undetectable |
| **7** | **Smoke scope before execution approval** | A `--mode smoke` on every stage **plus** a one-seed end-to-end pass (campaign → tally → analysis → `--verify`) runnable while `EXECUTION_APPROVED = False` | Machinery-only smokes as in V3: cheaper, but the tally and analysis are then first exercised on the real campaign, which is when V3's launch failure and I-18 were found |
| **8** | **What the "minimal" harness drops** | Drop the four probe modes from the run path, `--exit-audit-at-call`, the A18-mode specs, the per-pass trace composition, and 19 of 20 `fixedpoint/` modules. **Keep** the per-node census, `sweeps_per_eval`, the entry census and the exit forensics (§4.6) | Dropping the censuses would remove the per-module tables, the transfer factorisation (the answer to I-17) and the cost unit's own consistency check |
| **9** | **The GR reference record** | Commit `harness/reference/v3_reference.json` — the fifteen reference runs' compared fields, V3's commit, and each source record's sha — **before** the rewrite starts | Read V3's live `runs/` directly: no new committed file, and the gate stops working the day that worktree is retired |
| **10** | **Which `process/` changes are approved, and in what order** | Approve DR1–DR5 as the experiment plan's decision (d) proposes, **plus DR6** (environment overrides for the three research-tree paths), each as its own change with its own neutrality gate and its own merge | Any subset. A declined DR2 removes gate G9 and the `output_path` matrix row; a declined DR3 leaves I-20a's empty sweeps in place; a declined DR4 leaves the per-sweep-overhead question unanswerable on counts; a declined DR5 cancels the predicate trial; a declined DR6 forces decision (2) to option (ii) and decision (3) to "keep in `docs/data/`" |
| **11** | **The three A18-era root scripts** (`arch_surgery/experiment_runner.py`, `MDA_partition_experiment.py`, `MDA_partition_opt_experiment.py`) | **Leave frozen and untouched.** They are the record of the A18/A28-generation experiment and are cited by A28's report. V4's one-button entry point is `…_v4/experiment_runner.py`, a different file with the same basename as the first of them | Retiring them is a separate decision; if taken, it should be its own task with the citing reports updated |

---

## 10. Proposed task decomposition for the rebuild

**Proposals only — only the user adds tasks** (protocol §8). Ordered; each row says what it
delivers and what gates it. The estimate column is honest rather than optimistic; V3's harness
took one task (A41) and produced two issues (I-18, I-19) that a later task had to repair.

*Caption: one row per proposed task; "gated by" is the check that must pass before the task is
merged, per protocol §6 (a failed gate blocks the merge and is reported as a result).*

| # | proposed task | delivers | gated by | size |
|---|---|---|---|---|
| **H1** | *harness-skeleton* | `config.py`, `switches.py`, `arms.py`, `provenance.py`, `harness/README.md`, the `experiment_runner.py` shell with preflight only | all nine arms compose on every configuration; `rung()` reproduces the V4 plan §3.2 rung table exactly; the capability probe **refuses** an arm whose switch the tree does not implement (tooth: ask for a switch name that does not exist); no PROCESS run yet | M |
| **H2** | *harness-reference* | the GR reference extraction stage and `harness/reference/v3_reference.json` (decision (9)) | the extracted file re-derives byte-identically from V3's records; a missing record path **refuses** | S |
| **H3** | *harness-run* | `child.py`, `optimise.py`, `evaluate.py`, `pool.py`, `records.py`, `perturb.py`, `predicate.py` (+ `ystate.py` per decision (2)) | **gate GR** (§7): fifteen runs reproduce V3 bit-exactly on the listed fields, all six teeth trip, including the `v3_compat` positive control | **L — the largest single piece** |
| **H4** | *harness-artifacts* | `artifacts.py`, `decks.py`, `census.py`, `postsolve.py` and their stages | derived decks byte-identical to V3's; `per_run` sets re-derived equal to the committed ones **under the class-level classifier** (item 6a(a)), with any difference reported as a finding rather than absorbed; `artifacts --check` refuses on an absent harvest | M–L |
| **H5** | *harness-gates* | `gates.py` and G0, G4, G5, G6, G7 in the new framework | every gate PASSes with every tooth tripping at the V4 commit; G0 refuses on a missing reference key | M |
| **H6** | *harness-tally* | `stats.py`, `phase_a.stage_tally`, `phase_b.stage_tally`, `tables.py` | the tally reproduces V3's published cells for the GR reference runs; every declared construction of V4 plan §3.5 present, including item 6's within-cluster field **in the tally as well as the analysis** | M |
| **H7** | *harness-analysis* | `analysis.py` with `--verify`, `--teeth`, `--tables` | 0 mismatches over the full cell set with the denominator stated; every tooth trips; `--verify` refuses on an empty comparison | M |
| **H8** | *harness-smoke* | the one-seed end-to-end mode and the draft-mode chain in `experiment_runner.py` | a full one-seed pass on the cheapest configuration reaches a `--verify` with 0 mismatches, from the one button, with `EXECUTION_APPROVED = False` | S |
| **D-a…D-f** | *driver changes DR1–DR6* | one task each, on `process/` | each: byte-identity with the switch unset, on three configurations, with a 1-ULP tooth (gate G1's shape); the user's approval before merge | S–M each, six of them |

**Sequencing constraints that matter.** H2 before H3 (GR needs its reference committed first).
H3 before H4 (the artifact stages are validated by running the arms they feed). DR1 (the renames)
should land **after** H3, so GR compares against V3 through one map rather than two. DR2–DR5 must
each be composable back to V3's behaviour (§7.2) or they make the rewrite unverifiable.

**Total scope, stated plainly.** ≈ 3 400 lines of new `harness/` code plus **821 moved verbatim**
(`ystate.py`), ≈ 1 450 lines across `phase_a.py` / `phase_b.py` / `experiment_runner.py`, ≈ 900
lines of `analysis.py` — ≈ **6 570** against the V3 stack's measured **8 828**, about a 26 %
reduction. Plus six small driver changes each with its own gate, and one reproduction gate of
fifteen runs. The gain is not the line count: it is self-containment, one arm composition instead
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
