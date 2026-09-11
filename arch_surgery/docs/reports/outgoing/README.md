# Outgoing — findings addressed to another study

Documents here are **written for a sibling repository** and staged in this one because
`CLAUDE.md`'s hard rules forbid writing into a sibling clone. They are the handoff, not the
filing: moving or copying them into the destination is the user's call.

| File | Destination | Subject |
|---|---|---|
| `2026-09-11_tfcoil_output_mesh_written_insstrain_and_none_latch.md` | `PROCESS_code_analysis/docs/bug_reports/` | **FILED 2026-09-11 — written directly into the destination by the orchestrating session at the user's instruction (no agent was active there; left uncommitted for the user), and indexed in its `README.md`.** From A61 (insstrain-diagnosis): the output path forces `tfcoil.n_rad_per_layer` 100 → 500 through four latching writes and never restores it (the mechanism behind their owed M36 R1 headline, now with its measured size: one further sweep moves `tfcoil.insstrain` by ~7e-3 of its scale and nothing else); the MFILE's `insstrain` is not the solved value by 0.70–0.72 % in every arm including PROCESS as shipped, and neither is mesh-converged (`v(n) = v_∞ + C/n`); the `insstrain` guard latches `None` (`superconducting.py:2651`). Code lines confirmed at `c0ae5b28` by the orchestrator; numbers are A61's |
| `2026-09-04_first_wall_thickness_read_before_write.md` | `PROCESS_code_analysis/docs/bug_reports/` | **DRAFT — staged, not yet handed over; the handoff is the orchestrator's call.** The full write-up of their Owed (M117) row: the first-wall thickness pair is written mid-sweep (`fw.py:347-352`) but read earlier in the schedule (`build.py:836/840`, `:1940-1947`) and by its own model (`fw.py:54-55` before `:110`); A35's measured displaced-state magnitudes (depth-1 transport delay, 1.459e-2 → 8.3e-16 in one verified pass, δ-ratio ≈ 2.00), A38's per-deck images, and the initialisation-time fix shape (compute the pair in `init.check_process`; same treatment for the `vpfskv` literal). Drafted by task A39 (v3-plan), deliverable D-a |
| `2026-09-02_process_defects_from_the_architecture_experiment.md` | `PROCESS_code_analysis/docs/bug_reports/` | **Current handoff.** Five defects in upstream PROCESS: the NaN convergence loophole; `np.allclose`'s hidden absolute tolerance; the 1990 cost model diverging at negative net electric power; constraint equality membership decided by position in the deck; two wrong loop bounds in `init.py` |
| `2026-09-01_call_models_equal_nan_converged.md` | `PROCESS_code_analysis/docs/bug_reports/` | `check_agreement` reports a NaN state as converged. **SUPERSEDED** by the row above, which carries it as its §A and corrects three details; kept because it may already have been filed |

Naming follows the destination's convention (`<date>_<slug>.md`).
**Read each document's `> Document status` header, not its position in this table** (trap T3).
