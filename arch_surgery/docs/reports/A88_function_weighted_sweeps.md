# A88 (function-weighted-sweeps) — the per-node table leaves the main text; the per-module sweep tables weighted per function

> **Document status** — **OPEN.** Task **A88 (function-weighted-sweeps)**, branch
> `A88-function-weighted-sweeps` (worktree `.claude/worktrees/A88-function-weighted-sweeps`, seeded
> with A87 (v3-grid-polish)'s records tree), base **`c04c93bb`**, tip **`f8147a00`** — **the last
> commit that touches code or a generated document, and where every gate verdict this report cites
> was pressed** (rule xiii); the only commit after it is this document. The user's instruction of
> 2026-09-17 is the queue's row A88. **Zero PROCESS runs** (stamp survey: 1 102 records before and
> after, 0 re-made, 0 new); `EXECUTION_APPROVED` untouched; no file under
> `MDA_partitioning_experiment_v4/PROCESS/`, `harness/child/` or the root `process/` changed. The
> sibling `PROCESS_code_analysis` was read and its `driver_order` run in its own environment with
> `PYTHONDONTWRITEBYTECODE=1` and a scratch working directory; nothing under its `src/` or `output/`
> was written (§5.4). Arm names are today's (`AR/A0/A1/A2`, `BR/B0/B1/B2`); the records stamp the
> names of their day and `records.read` translates (trap T16). Every number below is printed by a
> committed script named beside it (protocol §15); the report's own change-log entry is written.

---

## 1. Verdict

**The direction of the saving does not depend on how the modules are weighted; its magnitude does,
by up to a quarter of the ratio.** The user asked (2026-09-17) to see how weighting the per-module
sweep ratios *per function* — a model's callable submodels in the dependency analysis's
decomposition — skews the headline average. It skews it **up** (toward 1) on every configuration
and in both phases, as weighting by collapsed-DSM rows already did, because both weights put most
of the weight on M1 (178 of the 344 functions the four modules hold on `large_tokamak_nof`; 24 of
their 47 rows), where the partition saves least, while node calls weight the aggregate toward M3's
twelve nodes and the once-per-run set, where it saves most.

**The six aggregate ratios under the three weightings** (each cell a rendered cell of the report;
node calls are the acceptance quantity, the two brackets are the `[v = 1, v = 0]` attribution
interval of the once-per-run nodes' rows or functions, trap T9; `report_counts_check.py` §13 at
`f8147a00` reads every one of them back from the stage records and finds each in the report's
Appendix D.4 paragraph):

| phase | configuration | node calls (Table 8 / Table 16) | DSM rows (Table 9 / Table 17, total) | functions (Table D.23 / Table D.24, total) |
|---|---|---|---|---|
| one evaluation, `A2` against its reference | nof | **0.5625** | [0.724, 0.767] | [0.695, 0.794] |
| | lad | **0.5772** | [0.742, 0.786] | [0.709, 0.811] |
| | st | **0.5016** | [0.655, 0.709] | [0.626, 0.720] |
| the optimisation, `B2` against `B0` | nof | **0.6395** | [0.690, 0.736] | [0.650, 0.746] |
| | lad | **0.4504** | [0.476, 0.508] | [0.448, 0.514] |
| | st | **0.5331** | [0.599, 0.653] | [0.565, 0.653] |

**What does not depend on the weighting.** Under any non-negative weighting the aggregate is a
weighted mean of the per-module ratios (Σ_g w_g s_g^arm / Σ_g w_g s_g^ref = Σ_g W_g r_g / Σ_g W_g
with W_g = w_g Σ_k s_gk^ref ≥ 0) and so lies between the smallest and the largest of them. **Every
per-module ratio in Tables 9 and 17 is at or below 1 except one**: M2 on `large_tokamak_nof` in
the evaluation phase reads **1.0078** (the brief's premise *"every per-module ratio is at or below 1
in every configuration and both phases"* is therefore not exactly true; the maximum is stated
instead). The largest in the optimisation phase is M2 on the same configuration at **0.8691**. So
only a weighting that put essentially all its weight on that one module could read otherwise, and
across the three weightings the evaluation-phase aggregate spans **0.50–0.81** and the
optimisation-phase aggregate **0.45–0.75**. The function brackets are wider than the DSM-row
brackets because the once-per-run nodes carry **50 functions** (`costs` 42, `vacuum` 5,
`water_use` 3; 51 with `pulse` on st) against 3 or 4 rows, so the `[v = 1, v = 0]` unknown moves
more of the weight.

**The definition of a function does not matter at the third decimal.** Under the alternative
reading — `1 + submodels`, the entry method counted beside its callables — the six brackets read
**[0.698, 0.791] / [0.713, 0.808] / [0.629, 0.719]** (one evaluation) and **[0.655, 0.745] /
[0.451, 0.514] / [0.569, 0.653]** (the optimisation): every end within 0.004 of the table's
(`report_counts_check.py` §14 at `f8147a00`, derived from the committed counts' `functions_alternative`
fields and the sweep tables' own per-arm means — a method that reproduces the tables' own brackets
exactly, checked before it was used).

**The two new appendix tables, as rendered** (`EXPERIMENT_REPORT.md` at `f8147a00`, Appendix D.4;
the captions abridged here to their first sentence, the grids whole):

**Table D.23.** *The main text's module sweeps table, weighted per function.* …

**`nof`** (n = 25 per arm)

| module | functions | AR | A0 | A1 | A2 | reference | A2 / reference | pairs |
|---|---|---|---|---|---|---|---|---|
| M1 | 178 | 4.96 [4, 5] | 5.52 [5, 6] | 5.12 [4, 6] | 4 | A1 | **0.7812** | 25 |
| M2 | 90 | 4.96 [4, 5] | 5.52 [5, 6] | 5.12 [4, 6] | 5.16 [5, 6] | A1 | **1.0078** | 25 |
| M3 | 68 | 4.96 [4, 5] | 5.52 [5, 6] | 5.12 [4, 6] | 3 | A1 | **0.5859** | 25 |
| PULSE | 3 | 4.96 [4, 5] | 5.52 [5, 6] | 5.12 [4, 6] | 1 | A1 | **0.1953** | 25 |
| once per run | 50 | 4.96 [4, 5] | 5.52 [5, 6] | 5.12 [4, 6] | 0 | A1 | **0.0000** | 25 |
| total calls | 389 | 1929 | 2147 | 1992 | 1383 | A1 | **[0.695, 0.794]** | 25 |

**`lad`** (n = 25 per arm)

| module | functions | AR | A0 | A1 | A2 | reference | A2 / reference | pairs |
|---|---|---|---|---|---|---|---|---|
| M1 | 177 | 5 | 5 | 4.92 [4, 5] | 4 | A1 | **0.8130** | 25 |
| M2 | 90 | 5 | 5 | 4.92 [4, 5] | 4.88 [4, 5] | A1 | **0.9919** | 25 |
| M3 | 68 | 5 | 5 | 4.92 [4, 5] | 3 | A1 | **0.6098** | 25 |
| PULSE | 3 | 5 | 5 | 4.92 [4, 5] | 1 | A1 | **0.2033** | 25 |
| once per run | 50 | 5 | 5 | 4.92 [4, 5] | 0 | A1 | **0.0000** | 25 |
| total calls | 388 | 1940 | 1940 | 1909 | 1354 | A1 | **[0.709, 0.811]** | 25 |

**`st`** (n = 25 per arm)

| module | functions | AR | A0 | A1 | A2 | reference | A2 / reference | pairs |
|---|---|---|---|---|---|---|---|---|
| M1 | 178 | 4.92 [4, 5] | 5.84 [5, 6] | — | 4 | A0 | **0.6849** | 25 |
| M2 | 79 | 4.92 [4, 5] | 5.84 [5, 6] | — | 5.84 [5, 6] | A0 | **1.0000** | 25 |
| M3 | 72 | 4.92 [4, 5] | 5.84 [5, 6] | — | 3 | A0 | **0.5137** | 25 |
| once per run | 51 | 4.92 [4, 5] | 5.84 [5, 6] | — | 0 | A0 | **0.0000** | 25 |
| total calls | 380 | 1870 | 2219 | — | 1389 | A0 | **[0.626, 0.720]** | 25 |

**Table D.24.** *The main text's optimisation-phase module sweeps table, weighted per function.* …

**`nof`** (n = 22)

| module | functions | BR | B0 | B1 | B2 | B2/B0 pooled | B2/B0 per-run median [min, max] | runs B2 > B0 |
|---|---|---|---|---|---|---|---|---|
| M1 | 178 | 1978 [1758, 2280] | 2028 [1793, 2396] | 2041 [1821, 2381] | 1389 [1241, 1624] | **0.6851** | 0.6909 [0.598, 0.799] | 0/22 |
| M2 | 90 | 1978 [1758, 2280] | 2028 [1793, 2396] | 2041 [1821, 2381] | 1762 [1573, 2058] | **0.8691** | 0.8765 [0.761, 1.013] | 1/22 |
| M3 | 68 | 1978 [1758, 2280] | 2028 [1793, 2396] | 2041 [1821, 2381] | 1542 [1378, 1805] | **0.7603** | 0.7670 [0.657, 0.887] | 0/22 |
| PULSE | 3 | 1978 [1758, 2280] | 2028 [1793, 2396] | 2041 [1821, 2381] | 641 [573, 749] | **0.3161** | 0.3189 [0.276, 0.369] | 0/22 |
| once per run | 50 | 1978 [1758, 2280] | 2028 [1793, 2396] | 2041 [1821, 2381] | 2 | **0.0010** | 0.001 | 0/22 |
| total calls | 389 | 769530 | 788715 | 793984 | 512717 | **[0.650, 0.746]** | 0.6556 [0.567, 0.758] | 0/22 |

**`lad`** (n = 11)

| module | functions | BR | B0 | B1 | B2 | B2/B0 pooled | B2/B0 per-run median [min, max] | runs B2 > B0 |
|---|---|---|---|---|---|---|---|---|
| M1 | 177 | 8096 [2904, 31870] | 7860 [2810, 31216] | 5437 [2535, 17172] | 3671 [1709, 11595] | **0.4671** | 0.5420 [0.084, 4.126] | 2/11 |
| M2 | 90 | 8096 [2904, 31870] | 7860 [2810, 31216] | 5437 [2535, 17172] | 4661 [2175, 14723] | **0.5930** | 0.6891 [0.106, 5.240] | 2/11 |
| M3 | 68 | 8096 [2904, 31870] | 7860 [2810, 31216] | 5437 [2535, 17172] | 4274 [1992, 13488] | **0.5438** | 0.6324 [0.097, 4.800] | 2/11 |
| PULSE | 3 | 8096 [2904, 31870] | 7860 [2810, 31216] | 5437 [2535, 17172] | 1715 [799, 5419] | **0.2182** | 0.2539 [0.039, 1.928] | 2/11 |
| once per run | 50 | 8096 [2904, 31870] | 7860 [2810, 31216] | 5437 [2535, 17172] | 2 | **0.0003** | 0.0005 [0.000, 0.001] | 0/11 |
| total calls | 388 | 3141072 | 3049680 | 2109521 | 1365163 | **[0.448, 0.514]** | 0.5200 [0.080, 3.954] | 2/11 |

**`st`** (n = 22; arms BR·B0·B2)

| module | functions | BR | B0 | B1 | B2 | B2/B0 pooled | B2/B0 per-run median [min, max] | runs B2 > B0 |
|---|---|---|---|---|---|---|---|---|
| M1 | 178 | 6044 [1890, 39952] | 5051 [1895, 14084] | — | 3251 [1363, 9635] | **0.6437** | 0.7156 [0.165, 0.894] | 0/22 |
| M2 | 79 | 6044 [1890, 39952] | 5051 [1895, 14084] | — | 3374 [1368, 10319] | **0.6680** | 0.7235 [0.169, 0.955] | 0/22 |
| M3 | 72 | 6044 [1890, 39952] | 5051 [1895, 14084] | — | 3325 [1389, 9929] | **0.6583** | 0.7314 [0.168, 0.929] | 0/22 |
| once per run | 51 | 6044 [1890, 39952] | 5051 [1895, 14084] | — | 2 | **0.0004** | 0.0007 [0.000, 0.001] | 0/22 |
| total calls | 380 | 2296841 | 1919363 | — | 1084735 | **[0.565, 0.653]** | 0.6260 [0.144, 0.793] | 0/22 |

Every cell of the module rows and of the `pairs` / `runs B2 > B0` columns above is **the sweep
table's own cell, republished** (rule xviii, `shares_tables_with`); the new cells are the
`functions` column and the total row's per-arm cells and bracket — **80 cells carrying a value**
over 6 stage tables, counted by `report_cells_preserved.py` (§5.3).

### 1.1 The census

Every line printed by `report_cells_preserved.py --base c04c93bb` at `f8147a00` (protocol §15),
the table counts by the renderer's own census.

| | before (`c04c93bb`) | after (`f8147a00`) |
|---|---|---|
| tables in §4 (main text) | 12 | **11** |
| tables in Appendix D | 22 | **24** |
| tables in the companion file | 15 | **15** |
| markdown grids in the report | 38 | **43** |
| grids in §4 | 16 | **15** |
| grids in Appendix D | 22 | **28** |
| markdown grids in the companion | 23 | **23** |
| **tables with one row** | **0** | **0** |
| widest grid in §4, in columns | 13 | **13** |
| widest grid in Appendix D, in columns | 25 | **25** |
| widest grid in the companion, in columns | 26 | **26** |
| stage tables the tally emits | 141 | **147** |
| cells the two implementations compare | 17 554 | **18 036** |
| teeth in the gate table | 167 | **168** |

*Appendix D gains six grids for two tables: each twin prints three per-configuration blocks, as the
sweep tables it twins do. §4 loses Table 9's one grid. The companion is byte-identical to the base
except its footer, which counts the second implementation's 147 tables.*

---

## 2. The function counts — where they come from, and what was found on the way

### 2.1 The route (trap T9) and the provenance recorded

`arch_surgery/fixedpoint/gen_function_counts.py` (committed at `2d9ffe4e`, beside
`gen_node_map.py`) read the sibling's three per-configuration exports **once** and wrote
`arch_surgery/docs/data/dsm_function_counts.json` (150 924 bytes, sha256
`215577fc…74c11`); `harness/experiment/data_provenance.py add dsm_function_counts.json
--source-commit 2d9ffe4e` (a new sub-command, `e182faa5`) copied it into `harness/data/` from **that
commit**, never a working tree, and entered it in `PROVENANCE.json` with its own `source_commit`
— a measurement artifact (`config.MEASUREMENT_ARTIFACTS`), read by `tally_*` and `analysis` and
never by the driver, so `DRIVER_FIXED_ARTIFACTS` and everything `artifacts.py` iterates are
untouched. The self-check's **data** check now compares 17 files + the predicate module = 18, all
identical, each read at its own commit (`commit 2d9ffe4e, commit 30198919`). **The tally and the
analysis read only the committed file**; a file of another format, or one stating no block for the
configuration, is a refusal (`tally_evaluation.function_counts`).

The generator re-run at `f8147a00` reproduces the committed file **byte for byte**: sha256
`215577fc470240bd099b8919df9c2b60ecdf1b6208b6e0537bab8d8b65d74c11` before and after (the file
stamps no commit of this tree for that reason; the commit that adds it is its stamp).

Recorded in the file (`sibling`, `node_map`, `driver_model_container`, per configuration `export`):

| field | value |
|---|---|
| sibling `HEAD` at reading, working tree clean | `1a0428650ab2224f3212003b69d3084bdff5ed5d`, yes |
| pin, read from `src/PROCESS_DSM/inputs/config.py` (`ANALYSIS_PIN_NAME`, never typed) | `PROCESS_at_36ac820e` — equal to the node map's, asserted |
| are the exports tracked in the sibling? | **no**: `output/` is gitignored (`.gitignore:94`), so an export has no committed state of its own; "their committed state" is the sibling's HEAD at reading plus each export's own sha256 and mtime |
| `output/tokamak/process_dependencies.json` | sha256 `b751526a…`, 18 629 408 bytes, mtime 2026-09-17 14:22 UTC — **regenerated today**; `a33_postsolve.py` read it on 2026-09-03 at `d02dd73d…` |
| `output/low_aspect_ratio_DEMO/process_dependencies.json` | sha256 `0c3f23b7…`, mtime 2026-09-03 — byte-identical to what A33 read |
| `output/st_regression/process_dependencies.json` | sha256 `582b4a5f…`, mtime 2026-09-03 — byte-identical to what A33 read |
| the node map read | `arch_surgery/docs/data/dsm_node_map.json`, sha256 `5195c268…` (the harness copy's source) |
| the driver's model container parsed for node → class | `MDA_partitioning_experiment_v4/PROCESS/process/main.py`, sha256 `3b37f2be…`, by `harness.child.postsolve.container_classes` |

### 2.2 The row → model mapping, from the sibling's own ordering

D8's row numbers are the row order of the sibling's *unsequenced collapsed* figure
(`dsm_collapsed.html`; `MDA_PARTITION_EXPERIMENT.md` §2 says so). That figure sorts the top-level
actors by `PROCESS_DSM.output.figures.driver_order(interleave_drivers=True)` — each actor at its
**first** position on the process line (`walk_rank`'s `setdefault` over `process_line_order`). The
generator derives that order from the export's own `process_line_order` annotation **and** runs the
sibling's `driver_order` on the same export in `ESL_env` (found beside this environment;
`PYTHONDONTWRITEBYTECODE=1`, working directory a scratch tempdir), and **refuses if the two differ**
— they agree row for row on all three exports (a first run had taken the sibling's own import-time
print as row 1; the script now reads rows after a sentinel). The four rows our documents state
(`Build` 5, `Pulse` 39, `FirstWall` 41, `Power` 48) fall where D8 put them; so do the range ends
(`PlasmaConfinementTime` 28, `pfcoil_functions` 37, `Divertor` 40, `Availability` 51).

**Which module a row is in.** On the `tokamak` export, by the node map's row ranges (D8): the four
in-sweep modules count **24 / 10 / 12 / 1** rows and FF 5, exactly the map's `n_dsm_rows` (asserted;
the generator refuses otherwise). The other two exports have their **own** row order, so there the
module is assigned **by model name** from the tokamak assignment, with three documented
substitutions and nothing else (`SUBSTITUTIONS`, each with the committed sentence that places it):
`ElectronCyclotron` → M1 (node map caveat 2), `CROCOSuperconductingTFCoil` → M2 (the map's
`membership_note`), `Constraints` → FF (D8's row 55). Anything else would be named unassigned,
never placed.

### 2.3 Found and named, not placed

1. **The sibling's tokamak export has drifted from D8 — the M125 constraint split.** Regenerated
   today at their `1a04286`, it carries **57** actor rows, not 56: D8's single `Constraints` row is
   now `ConsistencyConstraints` (row 55, inside FF's range) and `EngineeringConstraints` (row 56,
   **outside every range** of the node map, where D8 placed `MDA_Output`, which is at 57). Rows
   1–55 and every in-sweep module are unaffected; the row is recorded in `unassigned_rows` with the
   drift named (`known_drift`) and is in no count. Trap T9 in the flesh: had the file been read
   live by a measurement, a feed-forward row would have appeared or vanished between two runs of
   the same code.
2. **On `st_regression` the node map's row ranges do not hold, and M1 has 25 rows there, not 24.**
   `ElectronCyclotron` is a supermodel row at 21 (it is not a *node* — the map's caveat is right at
   node granularity — but it is a collapsed-DSM row) and `CsFatigue` is absent (`i_pulsed_plant =
   0`), so from row 21 everything is shifted by one: `PlasmaConfinementTime` sits at 29, which the
   tokamak ranges call M2 (`first_row_on_which_they_do_not`). By model name the modules count **25 /
   10 / 12 / 1** and FF 4. **The `models` column of Tables 9 and 17 is the node map's `units.dsm_rows`
   — the tokamak deck's counts — on every configuration, and reads 24 for M1 on st.** Not changed
   here (no existing cell changes; and DSM_VALIDATION V6 records the substitution as
   "boundary-respecting", which it is — no cross-module cell moves); proposed for the DSM
   validation register in §9. The DSM-row bracket on st would move by one row in 47 if it were.
3. **On `low_aspect_ratio_DEMO` the ranges hold exactly** (`row_ranges_of_the_node_map_apply:
   true`): the 52-node model layer V6 called identical is identical.

### 2.4 The listing, summarised (the whole of it is in the file: `configurations.*.rows`)

Functions = `max(1, submodels)`; in brackets `1 + submodels`. Every export's hierarchy is exactly two
deep (no sub-actor has children — asserted). Subdrivers (a `workflow_driver` with a parent: the
root-finders inside `CICCSuperconductingTFCoil` / `CROCOSuperconductingTFCoil`, `pfcoil_functions`
and `Vacuum`) are counted beside and not among the functions: 2 in M2 and 1 in M3 on every
configuration.

| module | nof: rows → functions | lad | st | the rows (tokamak numbering; submodels per model) |
|---|---|---|---|---|
| M1 | 24 → **178** (202) | 24 → **177** (201) | 25 → **178** (203) | 4 PlasmaGeom 7; 6 Physics 8; 7 impurity_radiation_functions 5; 8 PlasmaCurrent 3; 9 physics_functions 5 (4 on lad and st); 10 PlasmaFields 5; 11 PlasmaInductance 6; 12 NeProfile 8; 13 PlasmaDensityLimit 11; 14 PlasmaProfile 5; 15 TeProfile 7; 16 PlasmaBeta 13; 17 PlasmaDiamagneticCurrent 3; 18 PlasmaBootstrapCurrent 15; 19 SauterBootstrapCurrent 12; 20 CurrentDrive 3; 21 FusionReactionRate 9; 22 fusion_reactions_functions 9; 23 radiation_power_functions 2; 24 ImpurityRadiation 7; 25 PlasmaConfinementTransition 23; 26 PlasmaExhaust 4; 27 ScrapeOffLayer 5; 28 PlasmaConfinementTime 3; **st adds** ElectronCyclotron 1 at its row 21 |
| M2 | 10 → **90** (100) | 10 → **90** (100) | 10 → **79** (89) | 5 Build 6; 29 CICCSuperconductingTFCoil 25 (**st**: CROCOSuperconductingTFCoil 24); 30 tfcoil.base_functions 5; 31 materials_functions 2; 32 superconducting_functions 4; 33 superconductors_functions 10 (11 on st); 34 quench_functions 9; 35 PFCoil 12 (11 on st); 36 CSCoil 11 (**1** on st); 37 pfcoil_functions 6 |
| M3 | 12 → **73** (85) | 12 → **73** (85) | 12 → **77** (89) | 40 Divertor 5; 41 FirstWall 6; 42 ivc_functions 3; 43 Shield 4; 44 VacuumVessel 3; 45 CCFE_HCPB 21 (24 on st); 46 Cryostat 2; 47 Structure 2; 48 Power 17; 49 Vacuum 5; 50 Buildings 2; 51 Availability 3 (4 on st) |
| PULSE | 1 → **3** (4) | 1 → **3** (4) | 1 → **1** (2) | 39 Pulse |
| FF (in no table) | 5 → 51 (55) | 5 → 62 (66) | 4 → 55 (58) | 38 CsFatigue 2 (absent on st); 52 WaterUse 3; 53 Costs 42; 54 Objective 0 → 1; 55 Constraints 14 / 9 (tokamak: ConsistencyConstraints 3, and EngineeringConstraints unassigned at 56) |
| once-per-run nodes (their own rows) | `costs` 42, `vacuum` 5, `water_use` 3 | the same | the same, and `pulse` 1 | derived node → class → row through the driver's model container (`Costs` chosen from {`Costs`, `Costs2015`} by the export's supermodel set); each resolves to exactly one row, in the module the node map places the node in (asserted) |

The per-configuration differences are the exports resolving conditionals per configuration; the
caption says the column differs per block and why. Under `v = 1` the twin's once-per-run row carries
50 (51) functions and M3 loses `Vacuum`'s 5; under `v = 0` the modules keep every function and the
once-per-run row is 0.

---

## 3. What was built, item by item

| # | what | where |
|---|---|---|
| 1 | **Table 9 (node calls per block, displaced) leaves the main text.** The construction is rendered **whole** as Appendix D's **Table D.3** — merged with the other three regimes into one stacked table of all four (the layout `node_calls_per_block`, `sources` all four regimes, bold ratio and blanked configuration as the main-text grid had), *not* placed beside it: with the main text carrying the per-module result in sweeps, the one reason for two tables of one construction (amendment 29's rule, one construction one table) went with it, and the acceptance regime is now one row group among four. D.3 and D.14 stay where they were. §4.2's RQ1 paragraph reads the headline ratio and the absolute totals from **Table 8** and the per-module ratios from **Table 9** (the sweep table; identical numbers), pointing at D.3's displaced row group for the node-call form; §5.2's transfer inputs are Table 8's rung cells. The rendered block's removal is done by the committed re-pointing script (§6). | `plan_tables.LAYOUTS`, `GROUPS` D.2; `report_citations_repoint.py` |
| 2 | **`stats.functions_by_group`** beside `dsm_rows_by_group`: `functions` per group under `v = 1` / `v = 0`, from the configuration's block of the committed file; refuses a module without a count and a once-per-run node without one row of its own. `weighted_total` reused with the new weight (its docstring now says it takes either). | `harness/measurement/stats.py` |
| 3 | **A tally construction carrying only the new cells**, both phases: `module sweeps per run, function-weighted total — <configuration> — <source>` (kind `module_sweeps_functions`): `functions` per group, and a total row of Σ sweeps × functions per arm with the ratio (evaluation: `[v = 1, v = 0]`; optimisation: pooled bracket, per-run median with bracket, runs `B2 > B0`). Its module rows' per-arm cells are **absent** (`absent_cell` renders `""`, never `—`). Computed for the acceptance regime alone (`tally.ACCEPTANCE_REGIME`) in the evaluation phase; the optimisation phase has one source. Same population, grouping, pairing and reference arm as `module_sweeps`. | `tally_evaluation.module_sweeps_function_weighted`, `tally_optimisation.module_sweeps_function_weighted`, `tally.py` |
| 4 | **Twins in `analysis.py`**: `_functions_by_group`, `_module_sweeps_function_weighted_evaluation` / `_optimisation`, importing nothing from the tally; the acceptance regime re-typed. Gate `recomputation`: 147 tables, **18 036 compared, 0 mismatched** (from 141 / 17 554). | `harness/measurement/analysis.py` |
| 5 | **One tooth on `tally_contracts`** — *a function count the file does not state*: a file with no count for M3 is REFUSED, then one giving `vacuum` no single row is REFUSED; the sound case must read M3 68 / 73 and the once-per-run group 5 / 0. **18/18 teeth**, 168 in the gate table. | `harness/gates/gate_tally.py` |
| 6 | **The renderer**: a `merge` may print **blocks** (one merged grid per configuration under the block heading line); in a merge **an empty cell never claims a column** (`_merge_group`, factored out of `_merge`). The twin layouts `module_sweeps_functions_evaluation` / `_optimisation`: `kinds = ("module_sweeps_functions", "module_sweeps")`, `join = "module"`, `blocks`, mutual `shares_tables_with` with the sweep layouts, the sweep tables' `merges` and `bold`, `omit = ("models",)`. | `harness/measurement/plan_tables.py` |
| 7 | **Group D.4 "The aggregate under three weightings"** with the context paragraph stating the skew (§1's numbers, the largest per-module ratio, what does not depend on the weight) and the two twins as Tables D.23 and D.24 — a new group rather than two tables spliced into D.2 and D.3, so the six ratios are read in one place and D.4–D.22 keep their numbers. D.2's context (the T17 third-addition kind) and D.3's context re-pointed. | `plan_tables.GROUPS` |
| 8 | **§6** gains one marked sentence after RQ2: direction weighting-independent, magnitude not, with the ranges per weighting and phase; nothing else in §6 changes. | `EXPERIMENT_REPORT.md` |
| 9 | **The change log entry** (Appendix C, 2026-09-17), written by this task; and the change log is now **held out of the renderer's dangling-reference scan** — A86's entry says "Tables 11–18" and is a record of its day, which the checker had begun to flag once Table 18 ceased to exist (T17's second addition applied to the scan; 134 lines held out and said so). | `plan_tables._outside_the_change_log` |
| 10 | **The committed checks**: `report_cells_preserved.py` finds an old grid by its stage tables as well as its title (the renamed D.3 was otherwise 51 rows "missing") and counts **new cells by construction**; `report_counts_check.py` gains §13 (the eighteen quoted ratios and the two maxima read back from the records and found in the D.4 paragraph) and §14 (the alternative definition's totals). | `report_cells_preserved.py`, `report_counts_check.py` |
| 11 | **`harness/README.md`** §0 (the merge-in-blocks form, the empty-cell rule, the twins, the change log held out), the data-file table and count (seventeen; `add`), §12.1's row. | `harness/README.md` |

**Why a merge and not a second tally table of the same cells.** A87's assessment refused the
alternative for Table 11 — *"a second tally table for the same cells would put one construction's
numbers into the records twice"* — and the brief asks for the sweep cells to be *republished, not
recomputed*. The merge does exactly that: the six sweep stage tables are rendered twice (Tables 9
and D.23; 17 and D.24), declared and counted, and the records hold each per-module cell once.

---

## 4. Deviations from the V3 grids, all of them in one place

A85's, A86's and A87's are carried forward so the merged report's deviations are listed here and
nowhere else; the two new tables are not V3 tables and their departures from Tables 9 and 17 are
listed as this task's.

### 4.1 Named in the specification (A85's §3.1, unchanged)

| V3 | V4 | what differs | why |
|---|---|---|---|
| T4.5, T5.10 columns `A0 / A1u / A1`, `R / B0 / B1 / B2 / B3` | `AR / A0 / A1 / A2`, `BR / B0 / B1 / B2` | `A1u` and V3's `B2` dropped, `AR` and `A1` added | `A1u` is not run in V4 (the prime is inside the intervention); V3's `B2` was removed by D22; `AR` and `A1` are V4's reference and ownership rungs. The specification's §0 translation, applied |
| T4.5 ratio against `A0` | ratio against `A1` on a pulsed configuration, `A0` on st | the declared reference arm changed | V4 declares the reference per configuration (`tally_evaluation.reference_arm`); the *reference* column names it in every row |

### 4.2 Introduced at A85 (v3-table-formats), carried forward

| # | V3 | V4 | what differs | why |
|---|---|---|---|---|
| 1 | T4.5 / T5.10 rows `M1, M2, M3 live, vacuum, PULSE, FF` | `M1, M2, M3, PULSE, once per run` | V4 groups the configuration's own deferred nodes into one *once per run* row | V4's existing derived grouping (`stats.node_groups`), already used and already gated; the caption names the row's nodes |
| 2 | `models` total 52 | 49 | three collapsed-DSM rows are attributed to no group | Those are FF's rows whose nodes execute on no configuration; each caption states the map's 52 and the configuration's 49 |
| 3 | total ratio bracketed over `vacuum`'s row | bracketed over the whole once-per-run group's rows | the unknown is three or four rows, not one | Follows deviation 1 |
| 4 | configurations abbreviated `tok / lad / st` | `nof / lad / st` | the first configuration's short name | The V4 report writes `nof` throughout §4–§6; a table renaming it would be one the prose cannot cite |
| 5 | numbers spaced (`102 868`) | unspaced (`96933`) | no thousands separator | The existing V4 cells carry none, and a separator inside a cell makes the committed cell-preservation comparison presentation-sensitive |
| 6 | T5.4 columns `n, R, B0, B3, ratios` | closed at A86 | — | the constant `quantity` column is in the caption (`omit`) |
| 7 | cross-configuration tables blank the configuration on continuation rows | closed at A87 | — | the sub-heading row carries the group and its n and nothing more |
| 8 | V3 §5.2.1 has `within-cluster med / p90 / would accept` | V4's same-optimum table has `below resolution` | a different companion construction | V4 never built the within-cluster construction; `below_resolution` is what it has |
| 9 | node calls per module was §4.3's table | Appendix D.14 | the node-call per-module table left the main text | Its sweeps twin (Table 17) is the previous revision's headline; keeping both in §4 would be the same grid twice in two units |

### 4.3 Introduced or closed by A86 (v3-tables-remainder), carried forward

| # | V3 | V4 | what differs, and why |
|---|---|---|---|
| i | T5.4 `B2/B0 mean` — the ratio of the means | **closed.** `B2/B0 mean` is the ratio of the means; the mean of the per-seed ratios is renamed beside it (`RENAMED_HEADINGS`) | A V3-shaped table with a V3 heading over a different statistic |
| ii | T5.10 `runs B3 > B0` as one cell `0/22` | **closed.** One cell `k/n` by a `fraction` join | It was two columns |
| iii | block heading `tok` (n = 25) | **closed.** `**\`nof\`** (n = 22)`, the population sentence in the caption, the per-arm count declared (`Table.block_denominator`) | The evaluation table's own denominator is over four arms |
| iv | T5.4 has no `quantity` and no `arms` column | **closed.** Both in the caption (`Layout.omit`, 24 label cells) | They are labels, not numbers |
| v | `vacuum` and `FF` rows | one `once per run` row, its nodes named in the caption | A85's deviation 1 accepted at assessment with this addition |
| vi | `M3 live` | `M3` | V4's `M3` group is already the live one; the name is the committed node map's key |
| vii | `tok` | `nof` | as deviation 4 |
| viii | V3's §4 check-1 grid has no stencil rows | Tables 7 and 8 carry the displaced regime only; the stencil regimes are companion Tables F.1 and F.2 | Reproducing *that grid* means the acceptance regime alone. **A deviation from the specification, not from V3** |
| ix | V3 §5.2.2 repeats check 1's verdict column | Table D.15 repeats the median and p90 and **not** the verdict | Repeating a verdict in two tables is two places for it to go stale |
| x | V3 §5.1 is six columns | Table 10 was twenty-three | **closed at A87** |
| xi | — | a merged `median / p90` both of whose parts are missing reads `— / —`, not `—` | A collapse that rewrites an already-published string was withdrawn at A86; a rendering change may move a cell, never rewrite one |
| xii | V3 §5.5 publishes **ok** and **converged** seed sets | Table 16 publishes *every arm accepted* and *without retried seeds* | V4 has one acceptance set; the caption says which |

### 4.4 Introduced or closed by A87 (v3-grid-polish), carried forward

| # | V3 | V4 | what differs, and why |
|---|---|---|---|
| A87-1 | §5.1 is `config \| invalid seeds \| arm \| ok \| converged \| not-converged`, six columns; cross-configuration tables blank the configuration on continuation rows | **closed.** §4.3's Table 10 is per-arm success alone in that form, eight columns, the configurations as row groups; the merge with the taxonomy and the seed set is Table D.12 | A placement question, not a width one; the configuration is a row group because the stage tables carry no `configuration` column |
| A87-2 | T4.1 prints `both exactly 0 → **PASS**` where the ratio is 0/0 | `—, — → **PASS**` | V3 wrote a phrase into the cell; V4's cells already read `—` and a rendering change may move a cell, never rewrite one; the caption carries V3's sentence |
| A87-3 | T4.1 has no `verdict note` column | dropped into the caption (`omit`, 3 cells, no number among them) | The *reference* column says which pair is declared; the caption states the trivially-similar clause |
| A87-4 | T5.1 collapses arms with identical counts into one row | four rows on `large_tokamak_nof`, each reading `22` | **Not done**: collapsing rewrites cells |
| A87-5 | T5.1's `invalid seeds` carries the seed numbers | the count is Table D.12's; the seeds are companion Table F.6 | Putting the seed numbers back into the main grid puts the merged table back |

### 4.5 Introduced by this task

| # | Tables 9 / 17 (the grids twinned) | Tables D.23 / D.24 | what differs, and why |
|---|---|---|---|
| **A88-1** | `models` column | **`functions`** column; `models` **omitted** | The user asked for the same table "but then with a per function weight"; `models` is Table 9's / 17's cell and is not lost. Both columns side by side is the reversal (drop `omit`). A88-1 uses `omit` for a column of **numbers** printed in another table, not for a label stated in the caption — a widening of `omit`'s declared use that the caption states in one sentence and that no number in a hand-written caption pays for |
| **A88-2** | total row: `models` Σ 49; per-arm Σ sweeps × models; `[v = 1, v = 0]` over rows | total row: `functions` Σ 389 / 388 / 380; per-arm Σ sweeps × functions; `[v = 1, v = 0]` over functions | The construction the user asked for; the same attribution unknown, one weight over |
| **A88-3** | the block heading `**\`nof\`** (n = 25 per arm)` | the same | Not a deviation: the twin takes the heading from the constituent that declares a block denominator |
| **A88-4** | §4.2's Table 9 of that day (node calls per block, displaced, a main-text table in V3's §4 too — V3 §4.4's shape) | one row group of Appendix D's Table D.3, the construction whole over four regimes | The user's instruction; the per-module result stays in the main text in sweeps, whose ratios are the same cells. A departure from V3's §4, which printed the node-call form in the text — **recorded as a deviation from the specification (`REPORT_TABLE_FORMATS.md`) at the user's later instruction**, not a V3 reproduction defect |
| **A88-5** | — | the twins' captions name the three totals side by side in words and point at the D.4 paragraph for the numbers | A caption is hand-written and protocol §15 keeps measured numbers out of it; the numbers are in the generated context paragraph, which `report_counts_check.py` §13 reads back against the cells |

---

## 5. Verification

The sequence, worktree root, tree clean and committed at every press, nothing else running. **Zero
PROCESS runs.** Four presses are superseded and this report cites none of them: the four gates were first
pressed at `506a5aec`, where **`self_containment` FAILED** (§5.2), then at `38a5875f`, `dd425c50` and
`f4f1ec98` (identical numbers, superseded by later commits to the counts check, §4.1's sentence and
the change-log entry); every verdict was pressed again at the tip.

| # | step (at `f8147a00`) | result |
|---|---|---|
| 1 | `--measure all --resume` | five stages re-pressed (`tally_evaluation` **96** tables, `tally_optimisation` **51**, `recomputed_tables` **147**, `gate_table`, `exclusion_review`); **0 runs made** |
| 2 | `--plan-tables write` | both documents written; **11 + 24 + 15** tables, 44 584 cells; `git status` empty afterwards — the committed documents are what the records produce |
| 3 | `--plan-tables check` | **IDENTICAL** for all eleven §4 blocks, Appendix D (1 332/1 332 lines) and the companion (1 705/1 705) — 13 IDENTICAL comparisons; **0 dangling** of 41 + 66 + 18 references, the change log's 134 lines held out |
| 4 | `--gate recomputation --resume` | **PASS** at `f8147a00` — 147 tables, **18 036 compared, 0 mismatched**, 9/9 teeth |
| 5 | `--gate tally_contracts --resume` | **PASS** at `f8147a00` — **441 table checks (147 × 3) + 256 reference cells, 0 mismatched**, **18/18 teeth** — the new tooth trips (REFUSE on the file with no count for M3, REFUSE on the once-per-run node with no single row) |
| 6 | `--gate run_kind_separation --resume` | **PASS** at `f8147a00` — **3 000 compared, 0 mismatched**, 9/9 teeth |
| 7 | `--gate self_containment --resume` | **PASS** at `f8147a00` — **52 files, 0 mismatched**, 1/1 tooth (49 lines naming either directory, 14 executable, all classified) |
| 8 | `--measure gate_table --resume` | **30 PASS, 0 FAIL, 168 of 168 teeth tripped** |
| 9 | `--plan-tables write`, then `check` again | **IDENTICAL** everywhere, **0 dangling**; nothing re-rendered, `git status` empty |
| 10 | `--selfcheck` | **PASS**; the **data** check 17 files + the predicate module = 18 comparisons, all identical, read from `commit 2d9ffe4e, commit 30198919` |
| 11 | `report_cells_preserved.py --base c04c93bb` | §5.3 |
| 12 | `run_stamp_survey.py --against` (before the first press / after the last) | **1 102 records** then and now, the same nine commits, 949 at `57dc0c14`; **0 changed, 0 disappeared, 0 new** |
| 13 | `report_counts_check.py` | runs; **4 lines differ**, the same four that differed at the base (A86's Limit 7); §13's 20 lines and §12's all `same` |
| 14 | `gen_function_counts.py` re-run | sha256 `215577fc…74c11` before and after — **byte-identical** |

### 5.1 The stamps

| verdict | `tree_git_head` | is that the tip's code? |
|---|---|---|
| `recomputation` | **`f8147a00`** | yes — the tip |
| `tally_contracts` | **`f8147a00`** | yes — the tip |
| `run_kind_separation` | **`f8147a00`** | yes — the tip |
| `self_containment` | **`f8147a00`** | yes — the tip |

The `gate_table` stage record's `records_read` names the commit of each of the thirty verdicts it
read: **4 at `f8147a00`** and 26 at the commits they were pressed at in the seeded records tree —
`8996b843` 23, `6f5ba612` 2, `350a58c4` 1 — the records-reuse rule. The two tally stage records
and `recomputed_tables` are provenanced by `runs_provenance` (949 records at `57dc0c14`) and were
re-pressed at the tip in step 1.

### 5.2 A gate that failed, and what it found

At `506a5aec` `self_containment` **FAILED**: **2 findings** of 51 lines naming the superseded
directories — the two new tables' caption clauses named the generator by path
(`"the generator arch_surgery/fixedpoint/gen_function_counts.py wrote once …"`) in an executable
string, which the gate classifies as neither heritage prose nor a declared provenance file. The
gate is right that a caption is not the place to depend on a path outside the harness: the clause
now says the counts are read from the committed file *and nothing else* and that the file's own
`generated_by` and the provenance record name the generator (which they do); the path stays in the
function's docstring as heritage, and the declared reference for `data_provenance.py` says what it
now covers. Committed at `eb49561d`; every gate re-pressed. The FAIL had reached Table D.1 through
the `gate_table` stage at `38a5875f` — the committed document carried "29 PASS, 1 FAIL" for one
commit, truthfully — and D.1 was re-rendered at `dd425c50`. Not tuned: the finding was answered by
removing the dependency the gate exists to find.

### 5.3 The standing checks

| check | result |
|---|---|
| `report_cells_preserved.py --base c04c93bb` | **1 969 of 1 969 rows and 20 990 of 20 990 cells preserved** (15 842 carrying a number); **0 missing**; **3 differing rows, all the gate table's own** — `self_containment` (its population sentence counts 49 lines naming the directories, was 46), `tally_contracts` (697 compared, 18/18 teeth; was 679, 17/17), `recomputation` (147 tables, 18 036; was 141, 17 554). Nothing else differs |
| | **republished, declared** (`shares_tables_with`): the six `module sweeps per run` stage tables, each in a main-text grid and an appendix twin — 3 + 3 grids of 6 / 6 / 5 rows, **153 cells** per phase, all carrying a value; and A87's per-arm success (88 / 220) as before |
| | **new cells by construction**: `module sweeps per run, function-weighted total` — 6 stage tables, 34 rows, **80 cells carrying a value** (34 `functions` cells; the total rows' 20 evaluation-phase and 26 optimisation-phase cells) |
| | the 3 label cells A87 declared into a caption (`omit`), as before; `models` omitted from the twins is found in Tables 9 and 17 first and counted nowhere |
| `run_stamp_survey.py` | 1 102 records, byte-identical histogram — **0 re-made, 0 new** |
| `report_counts_check.py` | runs; 4 lines differ (the crash-class split, the plan's stencil budget, the second nonzero-mismatched PASS row — A86's Limit 7); §13 20/20 `same`, §14 derived |

### 5.4 The sibling, untouched

`git -C PROCESS_code_analysis status --porcelain` is empty before and after; `find src output
-newer` than the task's start returns nothing. Files under `.claude/worktrees/M126/` and pytest's
`__pycache__` under `tests/` carry 17:19 timestamps: the sibling's own M126 session running its test
suite while this task read (pytest's assertion-rewrite caches, `*-pytest-9.0.2.pyc`, which nothing
here invokes). Every invocation of the sibling's code from here ran with `PYTHONDONTWRITEBYTECODE=1`
and a scratch working directory.

---

## 6. The citations, re-pointed and re-read

`report_citations_repoint.py` was rewritten for this move and executed (protocol §15). It (1)
removes the orphaned rendered block of Table 9 — the renderer never removes a block whose layout is
gone — (2) applies four phrases by meaning, then (3) the number map (main text: 9 → D.3, 10–18 →
9–17; Appendix D and the companion do not move) to every citation span outside the rendered
blocks and Appendix C.

- **26 numbers moved**, all in the main text's hand-written prose and §5.
- **Four phrases**, three of them the T17 addition — *a number that still resolves can still be
  the wrong table*: the map would have sent every "Table 9" to D.3, which resolves and is wrong for
  the sentences that read the headline ratio and the absolute totals (Table 8's cells), the
  per-module ratios (Table 9's, identical numbers) and §5.2's transfer inputs ("Table 9's TOTAL
  rows" → Table 8's `A1→A2` / `A0→A2` cells). The fourth is §4.4's range, `Tables 7–17 and Tables
  D.2–D.24`.
- **Every numbered citation was then re-read** against the table it now names — 41 to §3/§4, 66 to
  Appendix D, 18 to the companion. `--plan-tables check` reports **0 dangling**.
- **Generated text re-read too** (T17's third addition): the `cost_sums` layout caption said *"the
  per-run reading is Table 18's last columns"* → 17; D.2's context said Table 9 was in §4.2 and
  not repeated → D.3's row group; D.3's context renumbered (10, 11, 12–15, 16, 17) and pointing at
  D.24. `report_counts_check.py`'s four "Table 11" labels → 10. §4.1's hand-written gate sentence
  read 167 teeth → 168 with the tooth named.
- **Appendix C is held out of the sweep** (A86's decision 8, T17's second addition) — and now of the
  renderer's dangling scan too (§3 item 9): A86's entry says "§4.3 Tables 11–18", which is true of
  its day and which the scan had begun to flag. This task's entry is written in words where a
  number would be a record ("the tables numbered 10 to 18 on that day").

---

## 7. Autonomous decisions, each with its reversal

| # | decision | reversal |
|---|---|---|
| 1 | **Table 9 merged into D.3** (the construction whole, four row groups) rather than placed beside it | Restore a `where="report"` layout for the displaced source alone and narrow D.3's `sources` back to three; D.3's caption reverts |
| 2 | **The twins are merges of the sweep table with a construction carrying only the new cells**, in blocks, rather than a second tally table of the whole grid | A whole twin table in the tally (recomputes the sweep cells into the records twice — what A87's assessment refused) or a twin rendered from `select`ed rows (cannot work: the total row differs, not the row set) |
| 3 | **An empty cell never claims a column in a merge** — the rule that lets the new construction's module rows leave the sweep cells alone | Give the new construction's module rows `—` and order the sweep table first in `kinds`; the total row's function-weighted cells are then hidden by the sweep table's — no reversal keeps both without this rule or a per-column precedence declaration |
| 4 | **`models` omitted from the twins** (A88-1) | Drop `omit`; both columns print, the grid is one column wider than Tables 9 / 17 |
| 5 | **The function-weighted construction is computed for the acceptance regime alone** in the evaluation phase | Emit it for the stencil and entry-reference sources too and add a companion twin merged with `module_sweeps_other_regimes` (which needs blocks grouped by configuration *and* regime) |
| 6 | **A new group D.4** holds both twins and the skew paragraph, at the end of Appendix D | Two layouts in D.2 and D.3 beside the sweep tables' node-call siblings, renumbering D.4–D.22 and stating the skew twice or in one of the two |
| 7 | **The skew is prose in the generated context paragraph, read back by a committed check** (`report_counts_check.py` §13), not a fourth table | A tally construction *aggregate under three weightings* with the six node-call ratios recomputed beside the two brackets — new cells, one of them a recomputation of Tables 8's and 16's |
| 8 | **The generator cross-checks the row order against the sibling's own `driver_order` and refuses without it** (needs `ESL_env` beside this environment) | Derive the order from `process_line_order` alone and record that the cross-check was not made |
| 9 | **The st row shift and the M125 split are named, not placed**: `EngineeringConstraints` unassigned; `models` on st left at the node map's 24 | Place `EngineeringConstraints` in FF (FF then counts 6 rows on tokamak, against the map's 5) and give the node map per-configuration row counts (a change to `dsm_node_map.json`, which is the driver's, and to Tables 9 and 17's `models` cells — not this task's) |
| 10 | **The data file stamps no commit of this tree** so that a re-run reproduces it byte for byte | Stamp `tree_git_head` as `gen_node_map.py` does and accept that the re-run differs in one field |
| 11 | **`data_provenance.py add`**: one file entered from its own commit, the record otherwise untouched; `build_provenance` keeps such entries rather than re-reading them at the record's commit | Re-bless the whole record with `record --force` at a new single commit (re-reads sixteen files nobody changed) |
| 12 | **The change log held out of the dangling scan** | Revert `_outside_the_change_log`; A86's entry then reports one dangling number until someone rewrites a record |
| 13 | **The `self_containment` finding answered by rewording the caption**, not by declaring the two tally modules in `DECLARED_OUTSIDE_REFERENCES` | Declare them (the gate's own route for a provenance string) and keep the path in the caption |

---

## 8. Limits

1. **The attribution bracket is wider in functions than in rows.** The once-per-run nodes own 50 (51)
   functions of 389 (380) against 3 (4) rows of 49, so `[v = 1, v = 0]` spans up to 0.10 of the
   ratio (lad, one evaluation: [0.709, 0.811]) where the row bracket spans 0.044. The unknown is the
   same — which module's work the deferred nodes' rows and functions belong to — and it is not
   resolved here; it cannot be without a per-node row attribution the node map does not carry.
2. **A function count is a proxy for work, not a measure of it.** `Costs` has 42 submodels and
   `Pulse` 3; nothing here says a `Costs` submodel costs what a `PlasmaBeta` one does. The three
   weightings are three defensible unit choices and the report says so; node calls remain the
   acceptance unit (D19, D29).
3. **The `models` column is the tokamak deck's on every configuration.** On `st_regression` the
   export has 25 M1 rows (§2.3); Tables 9 and 17 read 24 there, from the node map. Not changed —
   no existing cell changes in this task — and proposed for the DSM validation register (§9). The
   `functions` column is per configuration and carries st's 25th row (`ElectronCyclotron`, one
   function).
4. **The exports are untracked in the sibling**, so "at their committed state" could only be
   recorded as the sibling's HEAD plus each export's digest and mtime. The tokamak export was
   regenerated the day this task ran (M125's split); a later regeneration changes its digest and the
   generator's re-run would show it — but the committed file is what the tables read, and it does
   not move.
5. **The row → module assignment on `low_aspect_ratio_DEMO` and `st_regression` is by model name
   from the tokamak export**, plus three documented substitutions. The alternative — per-configuration
   row ranges — does not exist in any committed document.
6. **Two `omit` uses now differ in kind.** A86's and A87's `omit` drop a label stated in the caption;
   A88-1 drops a column of numbers that another table prints. `report_cells_preserved.py` finds the
   cells in the other table and counts nothing into the caption; the rule text ("a column dropped
   into a caption may carry a label, never a measured number") is satisfied because nothing is
   carried into the caption — but the field's name now covers two things. Amendment 33 (§9) says so.
7. **The D.4 paragraph's eighteen numbers are typed in `plan_tables.GROUPS`** and checked, not
   generated from the records. `report_counts_check.py` §13 reads each back from the stage records and
   finds it in the paragraph; a drift would be caught there, not at render.
8. **`report_counts_check.py` still differs on four lines** — A86's Limit 7, unchanged.
9. **Three of the eleven `B1 → B2` pairs on `low_aspect_ratio_DEMO` still differ in the last bits of
   `norm_objf`** (I-27). Not this task's; nothing here touches it.

---

## 9. What should change elsewhere (proposals; the queue, TRAPS and the registers are not this task's to edit)

**Harness plan, Appendix A, amendment 33 — proposed text.**

> **33. A construction may weight the same cells a second way, and the weight is committed data
> (task A88 (function-weighted-sweeps), the user's instruction of 2026-09-17).** The per-module
> sweep tables are twinned in Appendix D with the aggregate weighted per **function** — the
> dependency analysis's callable submodels behind each module's collapsed-DSM rows, a model with
> none counting as one — the counts committed once as `harness/data/dsm_function_counts.json` by
> the node map's own route (trap T9: `arch_surgery/fixedpoint/gen_function_counts.py` read the
> sibling's per-configuration exports once, the row → model order taken from the sibling's own
> `driver_order`, provenance recorded, the copy entered by `data_provenance.py add` from its own
> source commit as a **measurement artifact** the driver never reads; `config.MEASUREMENT_ARTIFACTS`).
> `stats.functions_by_group` beside `dsm_rows_by_group`; `weighted_total` takes either weight. The
> twin is a **merge** of the sweep table with a construction carrying only the new cells
> (`functions`, the total row), so each per-module cell is in the records once and printed twice
> (rule xviii): a `Layout` in `merge` mode may print **blocks**, and **in a merge an empty cell
> never claims a column** — empty is a column the row does not have, `—` a value that is missing.
> `omit` may drop a column another table prints (the twin's `models`), which the preservation check
> finds there; it may still never move a measured number into a caption. The aggregate under the
> three weightings is stated once, in Appendix D.4's context paragraph, and `report_counts_check.py`
> §13 reads every number of it back from the stage records; the change log is held out of the
> renderer's dangling-reference scan as it is of the citation sweep. The per-node table (node calls
> per block) is rendered whole in Appendix D, the acceptance regime one row group among four — one
> construction, one table — and the main text's only per-module breakdowns are the two sweep
> tables. Census after A88: §4 11 tables, Appendix D 24, companion 15, 0 one-row grids; 20 990 /
> 20 990 cells preserved and 80 added; `recomputation` 147 tables / 18 036 cells / 0 mismatched;
> `tally_contracts` 18/18; gates at `f8147a00`; stamp survey 1 102 records, 0 re-made — **0
> PROCESS runs**.

**`harness/README.md`** — done on the branch (§3, item 11).

**DSM validation register (`docs/reports/DSM_VALIDATION.md`) — proposed entry, the orchestrator's to
make (protocol §11).** *V-new (A88, 2026-09-17): on the `st_regression` export the collapsed DSM
has 25 M1 rows, not 24 — `ElectronCyclotron` is a supermodel row at 21 (V6's "boundary-respecting
substitution" is an addition to M1 at row granularity, though not a node at node granularity) and
`CsFatigue` is absent, so every row from 21 is shifted by one against D8's tokamak numbering and
the node map's `units.dsm_rows` (24 / 10 / 12 / 1 / 5) is the tokamak deck's on every
configuration. Consequence: the `models` column of the per-module sweep tables reads 24 for M1 on
st where the export has 25; the DSM-row total bracket on st would move by one row in 47. Also: the
sibling's tokamak export regenerated on 2026-09-17 (their M125) splits D8's row 55 `Constraints`
into `ConsistencyConstraints` (55) and `EngineeringConstraints` (56) — a feed-forward row, in no
module's count, and a demonstration of trap T9. Both are named in
`harness/data/dsm_function_counts.json` (`row_order`, `unassigned_rows`, `known_drift`).*

**TRAPS — proposed additions (the orchestrator's to make).** *T9:* the exports are **untracked** in
the sibling (`output/` is gitignored), so a task instructed to read them "at their committed state"
can record only the sibling's HEAD plus each export's own digest; the tokamak export was regenerated
the day A88 ran and no longer matches D8's row set. *T17, a fourth kind:* the renderer's
dangling-reference scan read the change log, so a record of a past table set ("Tables 11–18") became
a dangling reference the day the set shrank; the scan now holds the change log out, as the citation
sweep does.

**For the queue (a proposal, not a minting).** Nothing of the brief remains. Two items surfaced and
are not this task's: (a) whether the node map should carry per-configuration DSM-row counts (the
`models` column on st; a change to a driver-read artifact and to existing cells); (b) whether the
function-weighted construction should exist for the stencil and entry-reference regimes too
(decision 5's reversal).

---

## 10. Change log

| commit | what |
|---|---|
| `2d9ffe4e` | `gen_function_counts.py` and `arch_surgery/docs/data/dsm_function_counts.json` |
| `e182faa5` | `config.MEASUREMENT_ARTIFACTS`; `data_provenance.py` per-file source commit and `add`; the harness copy and its `PROVENANCE.json` entry |
| `506a5aec` | `stats.functions_by_group`; the tally construction in both phases; the analysis twins; the tooth; the renderer (merge in blocks, empty cells); the layouts, Group D.4, the contexts; Table 9's move and the re-pointing script executed; §6's sentence; Appendix C's entry; the change log held out of the dangling scan; the preservation check's host lookup and new-cell census; counts check §13; README; both documents |
| `eb49561d` | the `self_containment` finding answered (the generator's path out of the two captions; the declared reference's text) |
| `38a5875f` | both documents re-rendered at the tip |
| `dd425c50` | Table D.1 re-rendered after the press (30 PASS) |
| `dcad3aa6` | §4.1's gate sentence and the counts check read 168 teeth |
| `f4f1ec98` | counts check §14 (the alternative definition's totals) |
| `f8147a00` | the change-log entry names the gate table's three grown rows and the 80 new cells — **the tip, and where every verdict this report cites was pressed** |
| *(this file)* | this report |

---

## Orchestrator's critical assessment (protocol §5)

*Written 2026-09-17 at `2d03d572` by the orchestrating session, by checks that differ from the agent's; gates the merge.*

**Checks.** (1) **Stamps read from the four `gate.json` files**: each carries one `tree_git_head`, `f8147a00`, all PASS; `git diff --stat f8147a00..2d03d572` is this report alone. Rule xiii met. (2) **`--plan-tables check` re-run by me**: thirteen IDENTICAL comparisons, 41 + 66 + 18 references, 0 dangling. (3) **`report_cells_preserved.py --base c04c93bb` re-run by me**: 1 969 rows, 20 990 cells, 0 missing, 3 differing — the gate table's own rows, populations grown. (4) **Census by my own counts**: 17 `Table n` (6 + 11), 24 `Table D.n`, 15 `Table F.n`. (5) **The function counts recounted by my own path**: I read the sibling's tokamak export directly and counted, per top-level model, the nodes of kind `model` whose parent is that model; every one of the 57 rows in the committed data file agrees with my count (the four top-level drivers at 0, in no module, are the only rows where "max(1, count)" does not apply and the file rightly gives 0). The once-per-run row's 50 is Costs 42 + Vacuum 5 + WaterUse 3; M3's 73 in the file is the table's 68 plus Vacuum's 5; 178 + 90 + 68 + 3 + 50 = 389, the table's total. The committed copy under `harness/data/` is byte-identical to the generator's output (`215577fc…`). (6) **The six ratios**, read from Tables D.23 and D.24's total rows and Tables 8 and 16: evaluation 0.5625 / [0.724, 0.767] / [0.695, 0.794] on nof, and the same pattern on lad and st; optimisation 0.6395 / [0.690, 0.736] / [0.650, 0.746] on nof. Function weighting sits between node calls and DSM rows on the optimisation phase and at or above DSM rows on the evaluation phase; in no case does it reverse the direction. (7) **Scope**: 21 files, nothing under `PROCESS/`, `harness/child/` or the root `process/`; the sibling's working tree is clean (`git status` empty); stamp survey 1 102 records, 0 re-made — zero PROCESS runs. (8) Appendix C entry written by the task.

**The brief's premise was wrong and the agent said so.** I wrote "every per-module ratio is at or below 1"; M2 on nof in the evaluation phase reads 1.0078. The §6 sentence and the D.4 paragraph state the exception. That is the right outcome: the direction claim now rests on the aggregate being a weighted mean of ratios that are at most 1.0078, which holds under any non-negative weighting.

**A gate failed once and was answered, not tuned.** `self_containment` FAILED at `506a5aec` because two captions named the generator's path in executable strings; the captions were reworded and the gate re-pressed. The provenance is in the data file, where it belongs.

**Decisions I accept.** 2 (the twin is a merge carrying only the new cells — a whole second tally table would have put the sweep cells into the records twice); 4 (`models` omitted from the twins — the cells are printed in Tables 9 and 17 and the preservation check finds them there; the field now covers two kinds and amendment 33 says so); 5 (acceptance regime only — Tables 9 and 17 themselves are displaced-regime tables); 8 (the row order cross-checked against the sibling's own `driver_order`, refusing without it); 10 (no tree commit stamped in the data file so a re-run reproduces it byte for byte — the copy's own commit is in `data_provenance`).

**One residual I do not like but accept.** Limit 7: the D.4 paragraph's eighteen numbers are typed into `plan_tables.GROUPS` and read back by `report_counts_check.py` §13 (20/20 same) rather than generated from the records. Protocol §15 is met by the committed check, but a check that must be run is weaker than a render that cannot differ. The reversal — a small tally construction holding the six aggregates — is one task's hour and would make the paragraph a rendered table; recorded for the queue, not blocking.

**Two findings for the registers.** (a) On `st_regression` the export has 25 M1 rows, not the node map's 24 (`ElectronCyclotron` is a row there; `CsFatigue` absent), so the `models` column of Tables 9 and 17 is the tokamak deck's on st — one row in 47, no existing cell changed, registered as DSM validation V17 and issue I-28. (b) The sibling's tokamak export was regenerated the day this task ran and now has 57 rows (D8's `Constraints` split in two); named in the data file's `known_drift`, in no count, and a live demonstration of trap T9 — added to T9.

**Verdict: merge.** The per-node table is out of the main text with no cell lost, the function-weighted twins are in the appendix with their counts imported once by the node map's route and independently recounted here, the skew is stated with the exception, the headlines are unchanged, every verdict names the committed code it was pressed on, zero PROCESS runs.
