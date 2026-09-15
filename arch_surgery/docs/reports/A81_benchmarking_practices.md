# A81 (benchmarking-practices) — the V4 method against Beiranvand, Hare & Lucet 2017

> **Document status** — **OPEN TASK REPORT, 2026-09-15.** Task **A81 (benchmarking-practices)**,
> branch `A81-benchmarking-practices` off `architecture_surgery` at `589138ef`. Minted at the user's
> instruction (*"this article suggest best practises for comparing optimisation
> algorithms/approaches. Can you evaluate the v4 methodology based on the criteria outlined in the
> paper?"*). **Doc-only: zero PROCESS runs, no code change, no edit to the experiment folder
> (`arch_surgery/MDA_partitioning_experiment_v4/`) or to the V5 improvement list.** One new document,
> [`../V4_METHOD_AGAINST_BENCHMARKING_PRACTICE.md`](../V4_METHOD_AGAINST_BENCHMARKING_PRACTICE.md),
> and this report. The report evaluated is `EXPERIMENT_REPORT.md` at `589138ef`, read while A80
> (report-accuracy-audit) edits it in its own worktree; nothing here depends on A80's corrections.
> At merge this report moves to `reports/deprecated/` — folder position records lifecycle, not
> validity (trap T3).

## 1. Verdict in one page

- **The paper.** Beiranvand, Hare & Lucet, *Best practices for comparing optimization algorithms*,
  Optimization and Engineering 18 (2017) 815–848, doi 10.1007/s11081-017-9366-1; read in full from
  the arXiv text (1709.08242v1) at `runs/_reading/bhl2017.txt` (untracked, not committed). **34
  concrete recommendations extracted** as criteria C1–C34, each with its section and a quotation
  (document §1).
- **The tally** (document §2, one row per criterion, each with the report section, decision or
  table that shows it): **19 met · 8 partly met · 4 not met · 3 not applicable.**
  - Met: C1 purpose stated first; C2 comparison on the difference (the ladder, the
    predicate-matched control); C3 "solved" decided in advance; C4 same set and measures; C5
    real-world set; C8 best-known optimum as reference; C9 stored, bit-identical starts; C12 data
    from every category; C15 unit suited to the algorithm; C17 determinism and multiple starts;
    C18 per-run records with spread; C19 fixed-target with safety breaks; C20 quality statistic
    declared; C21 tolerance calibrated on the incumbent; C22 stopping conditions equalised *and*
    measured (exceeds the paper); C25 full tables; C31 a priori design; C32 reproducibility
    (exceeds, one gap); C33 differently formulated problems isolated on their own rung.
  - Partly met: C7 easy/hard groups (by accident, not design); C10 hidden structure (the
    objective/structure confound found and disclosed, not broken); C13 evaluations as the unit —
    the paper's condition that evaluations dominate is exactly what V3's wall-clock finding put in
    doubt, and V4 does not establish it; C14 running time and hardware — recorded per run, promised
    in §3.5 check 5, **published nowhere**; C16 success rate — the parts are on the page, the
    per-arm rate is not a cell; C23 parameter rationale is provenance, not reasoning; C24 no
    sensitivity of verdicts to F, floor, cluster gap, 1.05; C26 verdict columns at one threshold.
  - Not met: C6 three configurations against the paper's twenty (disclosed as "case studies" in
    §3.7 (b) and §3.11 exactly as the paper prescribes; the label does not reach §6); C27–C29 no
    profile and no figure of any kind, though performance and data profiles are applicable per
    configuration over the 25 starts and constructible from the records without a run.
  - Not applicable: C11 no standard test set exists for fusion systems codes; C30 accuracy
    profiles are for fixed-cost data (V4 is fixed-target); C34 scope (serial, single-objective).
- **Findings, ranked by how much they could change a §6 conclusion** (document §3, eight, each
  with its remedy classed as *no run on existing records* / *V5 campaign* / *reporting only*):
  1. **F1 — reliability is measured but not stated, and the paper counts it where V4 filters it.**
     The headline `B2/B0 = 0.450` on `low_aspect_ratio_DEMO` is over the 11 of 25 starts every arm
     solved; counting rows of companion Table F.17 (a hand tally, flagged as such), `BR`/`B0` reach
     an accepted optimum on 12 of 25 and `B1`/`B2` on 11 — seed 10 fails in the intervention arms
     alone. On `st_regression` the two asymmetric failures of Table F.20 (seed 5 `B2`-only, seed 10
     `B0`-only) cancel in count and not in cost. Remedy: a per-arm success table and a data profile
     from the records (no run); §6 carries the rate with its denominator; a V5 item proposed.
  2. **F2 — the efficiency unit's licence is not shown and the recorded timings are not published.**
     Every record carries `wall_s`, `cpu_user_s`, `cpu_sys_s`, `maxrss_kb`, `loadavg`; the report
     and companion carry no time, no hardware, no OS. V3's "0–15 % slower at 36–55 % fewer node
     calls" is the last word on the page. Remedy: a context table from the records with the W = 3
     concurrency stated (no run); an environment line (reporting); a V5 item for the non-node term.
  3. **F3 — three configurations is a case study and §6 does not say so.** Remedy: one clause in
     §6 (reporting); a V5 item on configuration-set size, grouping and the second-objective probe.
  4. F4 no profile (remedy: data, performance and exit-audit profiles from the records, no run);
     F5 verdicts at one threshold (re-tally at F ∈ {3, 10, 30}, floor ∈ {1e-7, 1e-6, 1e-5}, no
     run); F6 parameter rationale (reporting); F7 environment line (reporting); F8 constraint
     violations beyond constraint 93 (from the recorded residual vector, no run).
- **What the paper asks for that V4 lacks / what V4 does that the paper does not ask for** —
  document §4, nine and ten items respectively, stated plainly. The two lists are largely
  orthogonal: the paper is about what to measure and how to show it; V4's strengths (gates with
  teeth, recomputation, bit-comparison, per-run matched accuracy, the stopping rule as an arm) are
  about proving the measurement is what it says.

## 2. What was written

| file | what |
|---|---|
| `arch_surgery/docs/V4_METHOD_AGAINST_BENCHMARKING_PRACTICE.md` (new) | §0 what is compared with what (arms not solvers; runs as problems per the paper's §4.2; three is small whatever the reason); §1 the 34 criteria with section, quotation and paraphrase; §2 the evaluation table and tally, with §2.1 addressing each point the brief named (reason, test set, efficiency, reliability, quality, tuning/stopping, tables vs profiles, statistics, failures, reproducibility); §3 findings F1–F8 ranked, remedies classed, three V5 candidate items in the list's format, the data-profile construction stated without numbers; §4 asked-for-absent and done-not-asked lists; §5 limits |
| `arch_surgery/docs/reports/A81_benchmarking_practices.md` (this file) | task report |

Nothing else touched. `git status` clean apart from the two files; both committed with explicit
paths, no `git add -A`.

## 3. Autonomous decisions, each with its reversal

1. **Criteria granularity.** The paper's profile rules were split into four criteria (C27 include
   one; C28 performance-profile rules; C29 data profiles; C30 accuracy profiles) because their
   applicability to V4 differs (C30 is not applicable, the others are). Reversal: merge them; the
   tally moves by three rows and no finding changes.
2. **Hand counts admitted, flagged.** Per-arm success counts on `low_aspect_ratio_DEMO` (12 / 12 /
   11 / 11 of 25) and the two st failures are row counts from companion Tables F.17 and F.20, made
   by reading. The brief forbids numbers not in the report or the paper; these are derived from
   published tables and are labelled as a hand tally to be re-derived by the script F1 proposes
   before any is cited as a result. Reversal: strike the counts; F1 stands on the report's own
   "22 / 11 / 22 of 25" and §5.7's sentence.
3. **C13 and C14 judged "partly met", not "met by reasoned refusal".** V4's refusal of timings is
   justified (I-10, T5) and its §6 disclaimer is exactly what the paper's "explain how simplified
   measurements support the conclusions" asks; but the paper also asks for the time to be on the
   page with its form and the hardware, V4's own §3.5 check 5 promised it, and the records hold
   it. Reversal: rule that "context, never evidence" satisfies §4.1 without publication — then C14
   becomes met and F2 becomes a reporting note.
4. **C6 judged "not met" although V4 discloses exactly what the paper prescribes.** Three is three;
   the disclosure is credited in the verdict's parenthesis and F3's remedy is one clause. Reversal:
   judge disclosure as compliance — C6 becomes partly met.
5. **V5 items proposed, not added.** Three candidate items are written in the V5 list's format
   inside the document (F1, F2, F3); the list is untouched per the brief. Reversal: none needed.
6. **No figure drawn.** The profiles are stated as constructions from named record fields; drawing
   one would be a new output kind for the renderer and belongs to a task with a script under
   protocol §15.

## 4. What should change elsewhere (for the orchestrator; nothing edited here)

- **Queue, live pointer:** add to `MASTER_TODO_v2.md` §5.1 "Live pointers" a row for
  `docs/V4_METHOD_AGAINST_BENCHMARKING_PRACTICE.md` — *the V4 method evaluated against
  Beiranvand, Hare & Lucet 2017; 34 criteria, 19/8/4/3; findings F1–F8; three V5 candidates
  awaiting the user's word*.
- **V5 improvement list:** three candidate items, text in the document's §3 under F1, F2 and F3
  (reliability as a statistic not a filter; the non-node cost term identified or bounded; the
  configuration set's size, grouping and second-objective probe). Each is marked *not the user's*.
  Adding them is the orchestrator's; ruling on them is the user's.
- **A possible no-run task on the V4 records** (a proposal, not a mint): the remedies classed
  "R" in F1, F2, F4, F5 and F8 — per-arm success table, timing-context table with the environment
  line, data / performance / exit-audit profiles, verdict sensitivity re-tally, constraint-violation
  summary — are all tally constructions over fields every campaign record carries, would go through
  the renderer and the recomputation gate like every other table, and would be dated Appendix C
  entries. Whether any is wanted for V4 or deferred to V5 needs the user.
- **Reporting-only changes to the V4 report** (F3, F6, F7): one clause in §6, one sentence per knob
  in §3.10, an environment line — candidates for A80 (report-accuracy-audit)'s pass if the user
  wants them in V4; they are not accuracy corrections and A80's brief may not cover them.

## 5. Needs a decision

1. Whether any of the no-run remedies (per-arm success rate, timing context, profiles, verdict
   sensitivity, constraint violations) is added to the **V4** report as dated Appendix C entries,
   or whether all of it waits for V5. The strongest case for V4 is F1's success table (one
   construction, closes the paper's most-cited reliability measure); the case against is that V4
   is measured and published and its rules were not to change after the numbers.
2. Whether the three V5 candidate items enter the V5 list.
3. Whether §6 of the V4 report gains the case-study clause (F3) — a reporting change to a
   published conclusion, so the user's.

## 6. Change log

| date | entry |
|---|---|
| 2026-09-15 | Paper read in full; criteria extracted; report at `589138ef` read (§1, §3, §4–§6, Appendix D, companion failure tables F.14/F.17/F.20); record fields checked in `harness/core/records.py` and `harness/child/child.py` (`stamp_resources`) for what is recorded but unpublished; document and this report written; two commits |
