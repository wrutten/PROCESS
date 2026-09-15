# The V4 method against published benchmarking practice

> **Document status** — **CURRENT · EVALUATION, 2026-09-15.** Written by task **A81
> (benchmarking-practices)** at the user's instruction (*"this article suggest best practises for
> comparing optimisation algorithms/approaches. Can you evaluate the v4 methodology based on the
> criteria outlined in the paper?"*). It evaluates the method of the fourth revision of the MDA
> partitioning experiment as reported in
> [`../MDA_partitioning_experiment_v4/EXPERIMENT_REPORT.md`](../MDA_partitioning_experiment_v4/EXPERIMENT_REPORT.md)
> **at commit `589138ef`** (the report is being audited in parallel by A80 (report-accuracy-audit);
> nothing here depends on A80's corrections, and every table cited is cited by number *and* by
> the construction name printed under it, trap T17) against the criteria of
>
> > V. Beiranvand, W. Hare and Y. Lucet, *Best practices for comparing optimization algorithms*,
> > Optimization and Engineering **18** (2017) 815–848, doi 10.1007/s11081-017-9366-1
> > (arXiv 1709.08242v1, whose section numbering is used here and matches the published one).
>
> Doc-only: zero PROCESS runs, no code change, no edit to the experiment folder or to the V5
> improvement list; V5 candidates are *proposed* in §3 in that list's format for the orchestrator
> to add. Arm names are today's (`AR / A0 / A1 / A2`, `BR / B0 / B1 / B2`; trap T16). Every claim
> about V4 cites a report section, decision or table; every claim about the paper cites its
> section. Decision and issue numbers are spelled out at first use (protocol §4). No number here is
> new: each is a cell of the report, a count of rows in one of its tables (said so where done), or
> the paper's.

---

## 0. What is being compared with what

The paper is written for *benchmarking*: several solvers, a test set of many problems, one
computing environment, the aim of ranking. V4 is one code (PROCESS at the frozen base commit
`c0ae5b28`) whose *driver* is rearranged while every model is frozen (report §1.1; decision D5,
"only the driver changes"); it is run on **three** optimisation problems (report §3.3, decision
D17, "three configurations") from **25** starts each (report §3.5, §3.10 Table 6), and the
question is whether the arrangement alone changes the cost of solving at unchanged quality
(report §1.2). Three things follow for the evaluation and are applied throughout:

- **The "algorithms" are arms of a ladder, not independent solvers.** Adjacent arms differ by one
  named switch set (report §3.2, Table 3), so the comparison of interest is always a *pair*, and
  it is *paired by start* (report §1.3 "seed-pairing"; gate G6). The paper's apparatus (§5.3–5.5)
  assumes independent solvers on a common problem set; it still applies to a pair, and where it
  applies differently this document says so.
- **The "test problems" are, in the paper's own words, each run.** §4.2 of the paper: *"data
  collection is best performed by considering each algorithmic run as a separate test
  problem"*. Read that way V4's test set is 25 starts × 3 configurations, but configurations are
  never pooled (report §3.11; decision D21 (b)), so the paper's per-problem statistics are
  evaluated **per configuration over 25 starts** here.
- **Three configurations is a small test set whatever the reason.** The paper's prescription for
  a small set is not "do not do it" but "call it a case study and do not over-interpret" (§3,
  consideration i; Figure 1). V4 already uses those words (report §3.7 decision (b), §3.11). The
  evaluation asks whether the report's conclusions stay inside that label.

---

## 1. The criteria, extracted from the paper

Every concrete recommendation in the paper, numbered in reading order, with the section it comes
from, a short quotation, and a one-line paraphrase in this project's vocabulary. Remarks the paper
makes about the literature without recommending anything (e.g. its history in §1.1, the tool
survey in §6) are not criteria.

| # | Paper § | The paper's words | In this project's vocabulary |
|---|---|---|---|
| **C1** | §2 | *"Having a clear understanding of the purpose of a numerical comparison is a crucial step that guides the rest of the benchmarking process."* Four reasons listed; reason 4 is *"to evaluate the performance of an optimization algorithm when different option settings are used"*. | State the research question before the campaign and let it choose the configurations, the metrics and the analysis. |
| **C2** | §2 | *"it is valuable to think about exactly where the algorithm differs from previous methods … If they had compared their method against a quasi-Newton method on smooth convex optimization problems, then very little insight would have been gained."* | Compare the intervention against the baseline it actually differs from, and only on the difference. |
| **C3** | §2 | *"Is a fast algorithm that returns infeasible solutions acceptable? Is it more important that an algorithm solves every problem, or that its average performance is very good? Is the goal to find a global minimizer, or a highly accurate local minimizer? … Answering these types of questions before running the experiments is time well spent."* | Decide in advance what counts as solved, whether reliability or average cost matters, and whether the same optimum must be reached; pick the metrics from those answers. |
| **C4** | §3 | *"benchmarking only yields meaningful results when competing algorithms are evaluated on the same test set with the same performance measures."* | Every arm sees the same configurations, the same starts, the same τ, the same counters. |
| **C5** | §3 | *"if the goal is to determine the best algorithm to use for a particular real-world application, then a real-world test set focused on that application is usually the best option."* | The configurations should be PROCESS problems of the kind PROCESS is used for. |
| **C6** | §3 (i) | *"If the test set contains only few problems, then the experiment should be referred to as a case study or a proof of concept, but not benchmarking … an experiment should contain at least 20 test problems (preferably more). In the specific case of comparing a new version of an optimization algorithm with a previous version, the number of test problems should be significantly greater – in the order of 100 or more."* | With fewer than 20 configurations the result is a case study and must be labelled and read as one. |
| **C7** | §3 (ii) | *"a test set should include at least two groups of problems: an easy group … and a hard group that contains the problems which are solvable but computationally expensive"* | The configuration set should span easy and hard, by design. |
| **C8** | §3 (iii); §4.3 | *"Whenever possible, ensure at least a portion of the test set includes problems with known solutions"*; when none is known, *"replace f(x∗) with the best known value for the problem"*. | Where no optimum is known, the incumbent's optimum is the reference and the report says so. |
| **C9** | §3 (iv); §4.2 | *"every algorithm should be provided the same starting point … starting points should be generated and stored outside of the testing process"*; *"repeating tests on the same function with a variety of starting points"* increases reliability. | Starts are generated once, stored, bit-identical across arms, and there are several per configuration. |
| **C10** | §3 (v) | *"Examine the test set with a critical eye and try to determine any hidden structure."* (The shift test `f(x − p)` is offered as one probe.) | Look for structure in the configuration set that one arm could exploit or that confounds the comparison, and disclose it. |
| **C11** | §3; Table 1 | *"Using suitable standard test sets is usually a good option … it is usually easier to compare results across research groups when standard tests are employed"* | Use a standard problem collection where one exists. |
| **C12** | §4; Table 3 | *"it is recommended to collect at least some data from every performance category"* — efficiency, reliability, quality of solution. | Record cost, failures and optimum quality for every run. |
| **C13** | §4.1 | *"The number of fundamental evaluations can be used as a standard unit of time, and is often assumed to be platform independent … Note however that this measure is unreasonable when fundamental evaluations do not dominate the internal workings of the algorithm."* | Node calls are a valid unit only if node calls dominate the run's cost; that condition has to be shown, not assumed. |
| **C14** | §4.1 | *"any manuscript regarding the benchmarking should clearly state which form of running time was collected"*; *"the wall-clock time along with the hardware specifications are usually reported"*; *"the onus is on the researchers to explain how simplified measurements support the conclusions drawn"*. | Report running time (saying whether wall or CPU) and the hardware, and state how the count-based conclusion relates to time. |
| **C15** | §4.1 | *"when deciding on the choice of a suitable efficiency measure, the type of algorithms to be evaluated should also be taken into account"* (nodes for branch-and-bound, iterations for simplex). | The unit should be the natural one for an MDA-inside-SQP solve. |
| **C16** | §4.2; Table 3 | *"The most common performance measure to evaluate the reliability is success rate … counting the number of test problems that are successfully solved within a pre-selected tolerance"*; also *"number of constraint violations"*. | Publish, per arm, how many of the 25 starts reached an accepted optimum, and the constraint violations. |
| **C17** | §4.2 | *"consider whether the algorithms are deterministic, or non-deterministic, and repeat tests multiple times if the algorithm is non-deterministic … it is often better to use multiple starting points."* | State determinism; use several starts. |
| **C18** | §4.2 | *"If averaging is used, then it is important to also include standard deviations … data collection is best performed by considering each algorithmic run as a separate test problem"* | Per-run records first; any average carries its spread. |
| **C19** | §4.3 | *"In the fixed-target method … the termination criterion cannot rely only on accuracy, but should also include some safety breaks such as the maximum computational budget … If the algorithm terminates before reaching the desired accuracy, then it should be considered unsuccessful on that test problem."* | Declare fixed-target or fixed-cost; cap budgets; count a cap hit as a failure, never as a cheap success. |
| **C20** | §4.3 | Accuracy as `f(x̄) − f(x∗)`, normalised, in digits, capped at `M`; constraint violation as a sum, mean or product; *"The researcher should also carefully select the success criteria, e.g., how to fairly compare a solution that barely satisfies the constraints versus a solution that barely violates the constraints"* | Define the optimum-quality statistic and the feasibility rule before the campaign, symmetric across arms. |
| **C21** | §4.3 | *"if no known solution is available, then fixed-target approaches cannot be applied [to accuracy] … the simplest approach is to replace f(x∗) with the best known value"* | Against an unknown optimum, compare arms with each other and calibrate the tolerance on the incumbent's own spread. |
| **C22** | §4.4 | *"different stopping conditions can drastically change the output of an algorithm … if stopping tests are internalized within a method, it may not be possible to ensure all algorithms use the same stopping conditions … researchers should recognize this potential source of error"* | Either equalise the stopping rules or measure their effect as its own term. |
| **C23** | §4.4 | *"researchers should mention the parameter settings used and how they were selected … it is not appropriate to tune the parameters of some methods while leaving other methods at their default settings"*; hand-tuning reported *"separately from more systematic comparative experiments"*. | Declare every knob with its value and its origin; tune none of the arms, or all of them the same way. |
| **C24** | §7.1 | *"A robust study should investigate a range of parameters and report on their impact on the validity of the conclusions."* | Show how the verdicts move when τ, δ, the similarity factor, the floor and the iteration bound move. |
| **C25** | §5.1 | *"we recommend making full tables of results readily available … often better included in an appendix or in additional online material"* | Publish the per-run tables in full, somewhere. |
| **C26** | §5.1 | Summary tables *"provide good talking points … but fail to give a complete picture"*; the criticism of a cut-off table is that *"it does not explore how much the table would change if … the cut-off … was changed"*. | A verdict column must show what happens to it when its threshold moves. |
| **C27** | §5.2–5.5; Table 4 | *"Include at least one of these three profiles [performance, accuracy, data] whenever possible"*; per-problem plots *"are poor for benchmarking as they can only be used to analyze one test problem at a time"*. | Draw a profile over the 25 starts per configuration. |
| **C28** | §5.3 | Performance ratio `r_p,s = t_p,s / min_s t_p,s`, **∞ if the convergence test failed**; *"the researcher must select a definition for the convergence test passing and failing"*; create both log and linear τ axes; *"the interpretation of the results should be limited to comparison to the best method"*; *"if a fixed-cost approach is used … performance profiles become inappropriate"*. | Failures enter the profile as infinite ratios; the convergence test is the declared one; read only against the best arm. |
| **C29** | §5.5 | Data profiles answer *"what percentage of problems (for a given tolerance τ) can be solved within the budget of k function evaluations?"*; *"the data profile for a given solver s ∈ S is independent of other solvers"*; the unit may be *"any measure of fundamental evaluations"*. | Per arm and configuration, the fraction of the 25 starts that reach an accepted optimum within `k` node calls. |
| **C30** | §5.4 | *"accuracy profiles are designed for fixed-cost data sets"* | Applicable only if the runs were stopped at a fixed budget. |
| **C31** | §7 | *"an a priori benchmarking design is required … clarify the questions that are to be answered … The data must be analyzed and processed in a transparent, fair, and complete manner."* | Pre-register the questions, the test set, the measures and the acceptance rules; change them only by dated amendment. |
| **C32** | §7 | *"describe algorithms, parameters, test problems, the computational environment, and the statistical techniques employed … the minimum standard for replication of the experiments is that at least the authors themselves should be able to replicate the experiments … keep all the programs and data necessary to redo all the computations and recreate all graphs."* | Records, scripts and commits sufficient to re-make every table; the environment stated in the report. |
| **C33** | §7.1 | *"how to compare algorithms that approach the same problem from fundamentally different view points … one assumes an infeasible starting point and the other assumes a feasible starting point … the tolerance parameter could greatly influence the result"* | Where an arm solves a differently formulated problem, isolate the formulation change and say what the comparison then means. |
| **C34** | §1; §7.1 | Scope: *"single-objective optimization algorithms that run in serial"*; parallel and multi-objective benchmarking are open problems. | The paper applies as written only if V4's arms are serial single-objective solves. |

Thirty-four criteria. C28–C30 are the paper's rules for constructions V4 does not have; they are
kept separate from C27 because their applicability differs.

---

## 2. The evaluation

One row per criterion: how V4 meets it, with the report section, decision or table that shows it;
where it falls short; a verdict. *Met* means the report as written satisfies the paper's
recommendation; *partly met* that it does so with a named gap; *not met* that the recommendation
is applicable and not followed; *not applicable* carries its reason.

| # | How V4 meets it (where shown) | Where it falls short | Verdict |
|---|---|---|---|
| **C1** purpose first | The question is one sentence (§1.2) decomposed into RQ1–RQ5, each with its arm pair and acceptance rule; §3.1 states the design in one sentence. The purpose is the paper's reason 4 (option settings of one code) with a flavour of reason 2 (a new arrangement against the classical one). The metrics follow: cost in node calls (RQ1, RQ2), same optimum (RQ2, D6 — decision D6, correctness on `norm_objf` plus feasibility, never on iteration variables), the stopping rule as its own question (RQ4). | — | **met** |
| **C2** compare on the difference | The ladder (§3.2 Table 3): adjacent arms differ by one named switch set, the harness refuses a pair whose composed environments differ otherwise; the predicate-matched control `B0` exists so that the headline `B0 → B2` does not bundle the architecture with the stopping rule (§2.1, decision D18 — the predicate-matched control is the headline's base). `BR → B2` is published beside, never instead (§3.2). | — | **met** |
| **C3** decide what "solved" means | Declared before the campaign (§3.5 checks 1–4, §3.11): an accepted optimum is `status == ok` and `ifail == 1`; same optimum is judged on `norm_objf` within `max(F × yardstick, 1e-6)`; location is *not* claimed identical (D6, §3.11); no robustness claim is made (§3.11, §5.7). The paper's three questions are each answered in §3.11 before any run. | The answer to "solves every problem or good average?" is "average cost on the starts every arm solved" — see C16 for what that leaves out. | **met** |
| **C4** same test set, same measures | Same three configurations, same 25 seeds, bit-identical entries verified by gate G6 (§3.4, §3.9), one τ for every converger (decision D23 — one tolerance, τ = 1e-6, no inner tolerance), the same counters (`NODE_CALLS`, §3.8 (i)), the same exit audit position and ruler in every arm (§3.3, decision D25 — the exit audit restores the whole data structure). | — | **met** |
| **C5** real-world set for an application goal | The configurations are PROCESS's own shipped input files (`large_tokamak_nof`, `low_aspect_ratio_DEMO`, `st_regression`; §3.3), i.e. instances of the application the result is for. | — | **met** |
| **C6** enough problems; else "case study" | Three configurations. V4 says so in the paper's terms: *"Three case studies; the confound is disclosed in every cross-configuration caption and no synthesis is claimed"* (§3.7 decision (b)); *"three configurations (three case studies …)"* (§3.11); configurations are never pooled (D21 (b)). | Three is below the paper's 20 by a factor of about seven, and the paper's *"comparing a new version … with a previous version"* case (100 or more) is the nearer description of an architecture change to one code. The §6 conclusion states its licensed sentence per configuration but does not carry the word "case study"; a reader of §6 alone is not told the paper's caveat. PROCESS ships more input files than the three used (the repository's `tests/regression/input_files/` holds nine, one of which — `large_tokamak_eval` — was dropped for a pre-declared reason, decision D17), so the set is small partly by choice, not only by supply. | **not met** (disclosed, as the paper prescribes for a small set; the disclosure does not reach §6) |
| **C7** easy and hard groups | The three configurations span the range in the event: `large_tokamak_nof` loses 3 of 25 starts in every arm, `st_regression` none to a crash, `low_aspect_ratio_DEMO` reaches an accepted optimum in every arm on 11 of 25 (§4.3, Tables D.61–D.66, `failure taxonomy` / `the seed set`). | Not by design: no easy/hard grouping was declared, and the hardness of `low_aspect_ratio_DEMO` was found (V3, §2.2 item 5) rather than chosen. | **partly met** |
| **C8** known solutions | No optimum of a PROCESS configuration is known analytically; the paper accepts this for real-world sets and prescribes the best-known value. V4 uses the incumbent's optimum as the reference (check 1 is `B0 → B1`, `B0 → B2`) and calibrates the tolerance on the incumbent's own spread (`BR → B0` yardstick; §3.5 check 1; Tables D.67–D.69, `same optimum (check 1)`). Multiple optima are handled by clustering with a declared resolution (check 1a/1b). | — | **met** |
| **C9** same, stored starting points | Phase A entries are derived from a hash of (seed, component) and verified bit-identical across arms by G6 (§3.4); Phase B starts are `1 + δ·u` keyed on the variable *number* so shared variables get identical factors even though the lifted design vector is one longer (§3.5); the unperturbed start is included (`start000`); the reference arm enters from the same displaced snapshot (decision D26). Bit-identity is gated, not assumed. | One asymmetry is disclosed and should be read: the lifted arms' new variable 178 starts at *"the burn time the baseline's own loop settles on at the configuration's starting design vector"* (§3.3) — a value produced by a baseline run and handed to the intervention arm. It is plausibly neutral (the flat loop recovers it inside its first solve) and it is stated, which is what the paper asks (*"ensure no algorithm is abusing starting point information"*). | **met** |
| **C10** hidden structure | V4 found and disclosed the structure that matters: the objective/structure confound (improvement-list item 4; §2.2 item 4; §3.3; §3.7 (b)) — `st_regression` is at once the only steady-state, un-lifted, Q-objective, post-solve-`pulse` configuration, and `low_aspect_ratio_DEMO`'s objective *is* the lifted variable. Disclosed in every cross-configuration caption; §5.8 says it bites on `low_aspect_ratio_DEMO`. | Disclosed, not broken: the user ruled no fourth configuration in V4 (§3.7 (b)). The paper's shift test does not translate (the configurations are not test functions), but its purpose — a probe that would move if an arm exploited structure — has a V4 analogue that was *not* run: the same configuration under a second objective (item 4 (a)). | **partly met** |
| **C11** standard test sets | No standard collection of fusion systems-code optimisation problems exists; the paper's Table 1 lists none. PROCESS's own regression suite is the nearest thing and V4's three configurations come from it. | — | **not applicable** (no standard set exists; the nearest one is used) |
| **C12** data from every category | Efficiency: node calls per run and per evaluation, sweeps, predicate evaluations (Tables D.2–D.21, D.73–D.75, companion F.16/F.19/F.22). Reliability: the failure taxonomy with denominators of 25, the seed set, the failure table with each failed arm's cost and the others' at the same start (Tables D.61–D.66, companion F.14/F.17/F.20). Quality: check 1, the exit audit, the fixed-point distance, constraint 93 (Tables D.67–D.69, D.76–D.80, D.34–D.42). Memory and time are *recorded* per run (`wall_s`, `cpu_s`, `maxrss_kb`, `harness/core/records.py` field table) though not published. | — | **met** |
| **C13** evaluations as the unit, if they dominate | Node calls are exact, concurrency-invariant and reproduce bit for bit (CLAUDE.md working rules; §2.3; §3.11); the paper's *"platform independent"* virtue is exactly why V4 chose them, and the rule *"no conclusion rests on a timing"* is justified by a measured instability (issue I-10 — identical work varying up to 35 % in CPU-seconds; trap T5). V4 also counts the one non-node cost term it hypothesised, the per-sweep predicate overhead (§3.5 check 5; §5.5), and finds it cannot explain a wall-clock gap. | The paper's condition — that fundamental evaluations *dominate* the algorithm's internal work — is exactly what V3 found in doubt: *"The node-call win does not reach wall clock: V3's `B3` is 0–15 % slower despite far fewer node evaluations, and a non-node-proportional cost term must exist"* (§2.1). V4 counts one candidate term and rules it out (§5.5) but does not identify the term or show that node calls dominate; §6 therefore withholds any wall-clock claim, which is correct, but the unit's licence in the paper's sense is not established. The prime's calls (13 per evaluation; §5.8) are stamped beside and excluded from the unit by ruling (decision D19); a reader who counts them as work must add them, and the report says so. | **partly met** |
| **C14** report running time and hardware | Every run record carries wall-clock seconds, user and system CPU seconds, peak resident memory and the load average (`stamp_resources`, `harness/child/child.py`; `records.py` fields `wall_s`, `cpu_s`), stamped *"context, never evidence"*. §6 states plainly that the result does not license a wall-clock claim — the paper's *"explain how simplified measurements support the conclusions"*. | **No running time is published anywhere in the report or its companion file** — §3.5 check 5 promised *"wall-clock context (3 serial repetitions, median and range) is reported in its own section"*, and no such section exists in §4 or §5, no table in Appendix D or the companion carries a time. The hardware, operating system and Python version are not stated in the report (they are in the repository's CLAUDE.md and trap T5, not in the document a reader of the result holds). The campaign ran three workers concurrently (W = 3, Table 6), which the paper's *"background operations … kept to a minimum"* would count against any timing taken from those records. | **partly met** (the refusal is reasoned and the conclusion is limited accordingly; the paper still asks for the time to be on the page with its form and the hardware, and V4's own plan promised it) |
| **C15** unit suited to the algorithm type | For an MDA inside an SQP optimiser the natural units are model-node executions (the fundamental evaluation), `call_models` evaluations (the optimiser's unit) and optimiser iterations; V4 publishes all three and the identity between them, `R = ρ × ε` (Table D.5, `the optimiser's path`; §4.3). | — | **met** |
| **C16** success rate; constraint violations | The failure taxonomy gives, per arm, scheduled / crashed / ok / unconverged with the traceback (Tables D.61–D.63); the seed set gives `n` (every arm converged), the configuration-invalid count and retried seeds per arm (Tables D.64–D.66); the failure table lists every seed outside the set with the failed arm, `ifail`, attempts and cost (companion F.14/F.17/F.20). Feasibility is required of every accepted optimum (`ifail == 1`). | **The paper's statistic — per-arm success rate over the 25 starts — is not printed as a number.** It can be counted by hand from the failure tables (and this document did, §2.1), but the headline tables are over the every-arm-converged set and the per-arm rate appears nowhere as a cell. Constraint violations: the per-run constraint residual vector is recorded (§3.8 (ii)) and only constraint 93's residual is published (Tables D.79–D.80). | **partly met** |
| **C17** determinism; several starts | PROCESS is deterministic; every arm's run is one subprocess; the counters are concurrency-invariant (§3.5 check 5); 25 starts per configuration per arm in both phases (Table 6) and, in Phase A, a second deterministic regime of `2(nvar + 1)` stencil points (§3.4). | — | **met** |
| **C18** per-run data; spread with averages | Every run is a record; the companion file publishes the per-run and per-seed tables (`RESULTS_TABLES_FULL.md`, 150 tables, Appendix D preamble); absolute cells are per-run means with the seed bracket `[min, max]`, ratios as pooled, per-run median with bracket and count above 1 (D.0 conventions; decision D21 (c)). | The paper asks for standard deviations; V4 gives the full range instead. For `n ≤ 25` the range carries more than a standard deviation would and is exact, so this is a difference of letter, not of substance; the report could say so once. | **met** |
| **C19** fixed-target with safety breaks; a cap hit is a failure | V4 is fixed-target throughout: every converger runs to τ (D23), the optimiser to its own convergence, and the safety breaks are declared — inner cap 20 sweeps per block (*"a cap hit is a refusal, not a budget"*), upstream's 10-pass cap recorded as `unconverged-at-cap`, VMCON's retry ladder counted per attempt (§3.4 check 4; §3.5; Table 6). A run that ends without `ifail == 1` is outside the seed set and in the failure table; the harness never retries a job (§3.5). | — | **met** |
| **C20** accuracy statistic and feasibility rule declared | Paired relative objective difference `|Δ norm_objf| / max(|a|, |b|)` with a floor and a calibrated threshold, median and p90, declared before the campaign (§3.5 check 1); clusters with a declared resolution category (1a, 1b); constraint 93 in seconds and relative (check 3); feasibility as `ifail == 1` symmetric across arms; the exit audit on the coupling state on both rulers (§3.6; Tables D.76–D.78). | The paper's digits-of-accuracy form (`γ`, capped at `M`) is not used; V4's relative difference against a floor is the same information with a threshold instead of a cap. The "barely feasible vs barely infeasible" question is answered by VMCON's own feasibility test being identical in every arm, which is stated only implicitly (the same optimiser, same settings). | **met** |
| **C21** best-known optimum as the reference | `B0` is the reference in every check; the `BR → B0` spread inside the campaign is the yardstick that calibrates the threshold, and the floor 1e-6 binds where the yardstick is smaller (§3.5 check 1; Tables D.67–D.69, where the yardstick reads 2.082e-15 / 1.982e-14 / 1.553e-13 median and the floor governs). | — | **met** |
| **C22** stopping conditions equalised or measured | This is the criterion V4 answers most directly. The stopping rule is *an arm pair* (`AR → A0`, `BR → B0`, RQ4; §3.2 Table 3), so its effect is a published term rather than a source of error: upstream's test is cheaper per call by 3–16 % and stops 30–50× further from the fixed point on two configurations (§4.2, §6 RQ4). One τ for every converger (D23). Matched accuracy is *verified per run* by the exit audit, never assumed from a shared τ (§3.6 last paragraph), and the headline pair's exit residuals are identical (§4.2). | — | **met** (exceeds the paper: the paper asks that the source of error be recognised; V4 measures it) |
| **C23** parameters declared, none tuned one-sidedly | Table 6 (§3.10) lists every knob — N, δ, τ, F, floor, cluster gap, iteration bound, median construction, caps, W — with value and provenance, frozen at approval, changed only by dated amendment. No arm is tuned: every arm runs the same optimiser at the same settings; the driver switches *are* the arms (§3.2). The retry ladder (`epsfcn × 10`) is upstream's and identical in every arm. | *"How they were selected"* is answered by provenance (V2 Appendix B, V3, upstream) rather than by rationale: why F = 10, why the iteration bound is 1.05, why the cluster gap is ten times the floor (the report's own §2.2 item 5 says that last one is a known weakness). The Phase A entry regime was chosen on A44 (transfer-gap)'s measurement (§3.4 "Why not a smaller δ") — a parameter selected on data, before the campaign and disclosed, which the paper permits if reported separately; it is. | **partly met** |
| **C24** parameter sensitivity | δ at two regimes, both published (§3.4, §4.2); the predicate on two rulers (`frozen` / `mixed`, §3.6, §5.6); τ's exchange rate measured once on V3's records (A43 (st-trust-gap), §3.3: block loops at 1e-8 reproduce the removed joint-test arm at 1e-6). | F, the floor, the cluster gap and the iteration bound are each at one value, and the one FAIL in the report sits close to its threshold: check 1 on `low_aspect_ratio_DEMO` fails at p90 2.148e-6 against a floor of 1e-6 (§4.3, Table D.68) — a factor of about two. The report does not show at what floor the verdict would flip, nor what the check-2 verdicts would read at a bound of 1.00 or 1.10. τ is at one value in the campaign. | **partly met** |
| **C25** full tables available | The companion `RESULTS_TABLES_FULL.md` carries every per-run, per-seed and per-pair table and the second implementation's tables (150 tables), generated by the same renderer and guarded by the same check (Appendix A Table A.1; Appendix D preamble). The records themselves are kept untracked at a named path with their commit (header). | — | **met** |
| **C26** summary tables as talking points; cut-off sensitivity | Every summary ratio is given three ways — pooled, median with `[min, max]`, count above 1 — so a single cut-off never carries a reading alone (D.0 conventions); the verdict columns of checks 1 and 2 sit beside the raw medians and p90s they are judged from (Tables D.67–D.72). | The paper's specific criticism applies: a verdict column shows PASS/FAIL at one threshold and the table does not say how the column would change if the threshold moved (see C24). The reader has the raw statistic and can do it; the table does not. | **partly met** |
| **C27** at least one profile | — | **No figure of any kind in the report or its companion.** Profiles are applicable: per configuration the "problems" are the 25 starts (the paper's own reading, §4.2), the solvers are the arms, the performance measure is solve-phase node calls, the convergence test is the declared accepted-optimum rule. A data profile per arm (fraction of 25 starts solved within `k` node calls) and a performance profile over the arm group are both constructible from the existing records without a run. This is the one construction the paper calls a *gold standard* and V4 has none of it. | **not met** |
| **C28** performance-profile rules | The ingredients are all declared and recorded: the convergence test (`status == ok` and `ifail == 1`), a failed start's node calls (companion F.14/F.17/F.20), the pairing. | Not built; see C27. When built, the paper's rules bind: a failed start is `r = ∞` — the opposite of V4's every-arm-converged filter, which removes the start from the population — and the reading is against the best arm only. With four arms on the pulsed configurations the "switching phenomenon" the paper warns of could arise between the second- and third-best arms; a pairwise profile (`B0` vs `B2`) avoids it and is the ladder's own reading. | **not met** (applicable; ingredients present) |
| **C29** data profiles | — | Not built. The data-profile question — *what fraction of the 25 starts does each arm bring to an accepted optimum within a budget of `k` node calls?* — is the one question V4's tables cannot answer, because every cost cell is conditioned on all arms having converged. It is also solver-independent, so it needs no pairing and no filter, and it is computable from `node_calls_solve_phase`, `status` and `ifail` in the records. | **not met** (applicable; no run needed) |
| **C30** accuracy profiles | V4 is fixed-target, not fixed-cost (C19). | — | **not applicable** (fixed-cost only). *An analogue exists and is half-built:* the exit-audit residual over the 25 starts per arm is a fixed-target accuracy distribution; V4 gives its median and p90/max (Tables D.25–D.33, D.76–D.78), which are two points of the curve the paper would draw. |
| **C31** a priori design | §1–§3 are the plan as approved on 2026-09-14, changed only by dated amendments recorded in Appendix C (header); acceptance rules, expectations and the seed set are pre-declared (§3.4, §3.5, §3.10); refuted expectations are named as such (§5.1 "Refuted or qualified expectations"); the campaign was refused by the button until `EXECUTION_APPROVED` flipped at a recorded commit (header; Appendix A). | — | **met** |
| **C32** reproducibility | Every number from a committed script (protocol §15; Appendix A); records stamp tree, commit, dirty flag, full environment, provenance of the PROCESS copy (§3.8 (ii)); the reproduction gate GR re-made twenty of the previous revision's records bit-exactly through a rewritten harness (§3.9, §4.1) — the paper's minimum standard, *"the authors themselves should be able to replicate"*, met in the strongest form; every published cell recomputed by a second implementation (§4.4). | The paper's list includes *"the computational environment"*: hardware, OS and interpreter are not in the report (see C14). Programs and records are kept, but the records are untracked (3 GB) and thus not *"made available"* in the paper's sense beyond the machine they sit on; the report says where they are and at what commit. | **met** (one gap: the environment line, already counted under C14) |
| **C33** differently formulated problems | The lifted arms (`B1`, `B2`) solve a problem with one more variable and one more equality constraint than `B0` and `BR` (§3.3 "The lifted input file"); V4 puts that formulation change on its own rung (`B0 → B1`) so that the headline rung `B1 → B2` compares like with like (§3.2 Table 3), and §5.8 names the surviving confound. The one FAIL in the report is localised to that rung (§4.3 check 1: `B0 → B1` and `B0 → B2` read the same `r` on `low_aspect_ratio_DEMO`). | — | **met** |
| **C34** scope | Each arm is a serial single-objective solve; the W = 3 pool runs independent jobs, not a parallel algorithm; counts are unaffected by the pool (§3.5 check 5). | — | **not applicable** (in scope as written; nothing to evaluate) |

**Tally over 34 criteria, each counted once: 19 met · 8 partly met · 4 not met · 3 not applicable.**
Met: C1, C2, C3, C4, C5, C8, C9, C12, C15, C17, C18, C19, C20, C21, C22, C25, C31, C32, C33.
Partly met: C7, C10, C13, C14, C16, C23, C24, C26. Not met: C6, C27, C28, C29. Not applicable:
C11, C30, C34. Several rows share one cause — C14 and C32 the absent environment line, C27–C29 the
absent profiles — which is why §3 lists fewer distinct shortfalls than there are non-met rows.

### 2.1 The points the brief asked to be addressed explicitly

**The reason for benchmarking and whether the metrics follow (C1–C3).** They do. The question is
about cost at unchanged quality, and the acceptance quantities are a cost count (node calls) and a
quality statistic (`norm_objf` within a calibrated tolerance plus feasibility). The one place the
metric does not follow the question is robustness: §1.2 asks about cost *"at unchanged quality of
the optimum"* and the design answers on the starts where every arm reached one; whether the
arrangement changes *how often* an optimum is reached is declared out of scope (§3.11 "No
robustness claim") and then observed anyway (§5.7: the intervention arms fail on 1–3 more
`low_aspect_ratio_DEMO` starts than the incumbent). The paper would say the second question was
asked by the data and should be answered by a statistic (C16), not by a disclaimer.

**Test-set size, selection and representativeness (C5–C7, C10, C11).** Three configurations from
the code's own regression suite, inherited from V2/V3 with one dropped for a pre-declared reason
(D17). The paper's threshold for benchmarking is 20 and V4 does not pretend otherwise: it calls
them case studies and never pools. What the paper would ask instead: more configurations (the
suite has nine input files; some are not tokamaks and would need the partition re-derived, which
is a real cost, not an excuse), a declared easy/hard grouping, and — for the confound V4 itself
identified — one configuration run under a second objective (item 4 (a) of the V4 list, never
executed). The representativeness question the paper poses for real-world sets (results *"may be
difficult to generalize"*) is answered honestly in §3.11 and §6; the shortfall is that §6's
licensed sentence does not carry the label.

**Efficiency measures (C13–C15).** V4's unit is the paper's preferred one — fundamental
evaluations, platform-independent, exact — and V4 adds a reason the paper does not have: the
counts reproduce bit for bit and the wall clock on this machine demonstrably does not (I-10, T5).
The paper's caveat is that the unit is *"unreasonable when fundamental evaluations do not dominate
the internal workings"*, and V3's own measurement that the node-call saving did not reach wall
clock (§2.1) is evidence that condition may fail here. V4's answer is two-fold: count the
hypothesised overhead and show it cannot be the cause (§5.5), and withhold any wall-clock claim
(§6). What it does not do is put the timing context it recorded on the page. Every campaign record
carries `wall_s`, `cpu_user_s`, `cpu_sys_s`, `maxrss_kb` and the load average; the report publishes
none of them, though §3.5 check 5 said it would. A context table — per arm, per configuration,
median and range of wall and CPU seconds, with the W = 3 concurrency and the load average stated as
the reason it is context — would satisfy the paper's letter at zero runs and would let the reader
see the size of the gap between counts and time that V3 reported and V4 left unstated.

**Reliability (C16–C19).** V4's handling of failures is careful and is the paper's own
recommendation in one respect — every start is a separate record, the taxonomy has denominators,
the failure table shows the failed arm's cost beside the others' — and departs from it in another:
the paper counts a failure *against the arm* (success rate; `r = ∞` in a profile), V4 removes the
start from every cost cell (the every-arm-converged set) and reports it beside. The two readings
differ most on `low_aspect_ratio_DEMO`, where the headline `B2/B0 = 0.450` is over 11 of 25
starts. Counting rows of the companion failure tables (Tables F.17 and F.20; a hand tally by this
document, not a published cell — a script should confirm it): on `low_aspect_ratio_DEMO` `BR` and
`B0` reach an accepted optimum on 12 of 25 starts and `B1` and `B2` on 11 of 25 (seed 10 fails in
the two intervention arms only); on `st_regression` seed 5 fails in `B2` alone after 479 630 node
calls where `B0` converged at 175 413, and seed 10 fails in `B0` alone after 667 989 where `B2`
converged at 129 012. Both st cases are outside the seed set and outside every ratio; a
performance profile would carry them as infinite ratios, one against each arm. So the dropped
seeds do *not* bias the headline in one direction on st (one each way) and bias it slightly in
the intervention's favour on `low_aspect_ratio_DEMO` (one start the incumbent solved and the
intervention did not). The report's §5.7 sentence is correct; the paper would want the per-arm
rate printed as a number with its denominator of 25, beside the cost ratio, in the headline
table.

**Quality of output (C8, C20, C21).** The paper's fixed-target logic is followed exactly: an
accepted optimum is defined before the campaign, a run that does not reach one is a failure, and
against an unknown optimum the incumbent's own spread calibrates the tolerance. The `low_aspect_ratio_DEMO`
FAIL is reported as a result and localised to the ownership rung (§4.3, §5.1 (a)); the paper's
"how much would the table change if the cut-off moved" applies (the p90 is 2.15× the floor) and is
not answered in the table.

**Parameter tuning and stopping conditions (C22–C24).** Matched *final accuracy* rather than
matched *tolerance settings* is V4's central methodological move (§2.1, §3.6) and it is stronger
than anything the paper asks: the paper asks that unequal stopping rules be recognised as a source
of error, V4 makes the stopping rule an arm and verifies the achieved accuracy per run. One τ
everywhere (D23) and the retry ladder as a counted term with both readings (§3.5) are the same
discipline applied to the optimiser. What is missing is the paper's §7.1 remark: a *range* of the
declared parameters and the verdicts' response to it.

**Tables versus profiles (C25–C29).** V4's tables are complete (150 in the companion) and its
summary format — pooled, median with bracket, count above 1 — reports three points of the
distribution the paper's performance profile would draw in full. Concretely, for two arms paired by
start, the performance profile *is* the cumulative distribution of the per-start ratio with failed
starts at infinity; V4's "median 0.5237 [min, max], 2 of 11 above 1" is that curve at three
abscissae over the converged starts only. A profile is applicable (25 starts per configuration is a
25-step curve; the paper's own Figure 4 is over 60 problems) and it would add exactly two things the
tables lack: the whole shape between the bracket ends, and the failed starts. The data profile adds
a third: a budget reading — with `k` node calls, what fraction of starts is solved — that no
V4 table gives. None needs a run.

**Statistical treatment.** The paper recommends per-run data, averages with standard deviations,
and profiles; it does not recommend hypothesis tests, and neither does V4 use any. V4's paired
design, its medians with brackets and its counts above 1 are at least as informative as the paper's
means with standard deviations for `n = 11–25`, and its refusal to pool configurations is stricter
than the paper's practice. Nothing here suggests V4 should add a test statistic; the paper would
ask for the *distributions* (profiles), not for p-values.

**Failures and negative results.** Reported as results: the crashes with tracebacks (Tables
D.61–D.63), the FAIL on `low_aspect_ratio_DEMO`, the refuted `ε = 1` expectation in evaluations
(§4.3 Table D.5), the robustness events without a robustness claim (§5.7), the trial that changed
nothing (§5.6). Protocol §6 forbids tuning a gate into passing. This is the paper's *"transparent,
fair, and complete"* met in full.

**Reproducibility.** Exceeds the paper's minimum (C32): committed scripts, stamped records, a
reproduction gate against the previous revision's records, and a second implementation
recomputing every cell. The one line the paper asks for that is absent is the computing environment.

---

## 3. Findings, ranked by how much they could change a V4 conclusion

Ranked by potential effect on a conclusion of §6, not by ease. For each: what V4 can do on its
existing records without a run (**R**), what needs a new campaign (**V5**), and what is a
reporting change only (**T**).

### F1 — Reliability is measured but not stated, and the paper counts it where V4 filters it (C16, C28, C29)

*Could change:* the reading of RQ2 on `low_aspect_ratio_DEMO`. The headline 0.450 is the cost on
the 11 starts every arm solved; the paper's reliability statistic would put beside it that the
intervention arms solved 11 of 25 starts and the incumbent 12 (hand count from Table F.17, §2.1).
The §6 sentence *"reaches … a different optimum within 2.2e-6 relative on the third at 0.45"*
would then carry *"on the 11 of 25 starts every arm solved; the incumbent solved one more"*. On
`st_regression` the two asymmetric failures (Table F.20) cancel in count and not in cost, and a
profile would show it.

- **R:** a per-arm success table — accepted optima out of 25 per arm per configuration, with the
  crashed / unconverged / `ifail ≠ 1` split — as a new tally construction beside the seed-set
  table; and a data profile per arm (the construction at the end of this section). Both read `status`, `ifail` and
  `node_calls_solve_phase`, which every record carries.
- **T:** §6's RQ2 sentence and the abstract-level sentence carry the per-arm rate with its
  denominator.
- **V5 candidate item** (in the V5 list's format):

  > ### n. Publish reliability as a statistic, not a filter *(A81 (benchmarking-practices), 2026-09-15, from Beiranvand, Hare & Lucet 2017 §4.2 and §5.3; not the user's)*
  >
  > V4 conditions every cost cell on the seeds every arm converged on and publishes the failed
  > starts beside (report §3.5, decision D21 (c)). The paper's reliability measure is the
  > per-arm success rate at a pre-selected tolerance, and its performance profile carries a
  > failed start as an infinite ratio against the arm that failed. A V5 plan declares, before the
  > campaign: (i) the per-arm success rate over the 25 starts as a published (not gated) quantity
  > in the headline cost table, with its split by failure kind; (ii) a data profile per arm and
  > configuration over the 25 starts in solve-phase node calls; (iii) a performance profile of
  > the headline pair with failures at infinity. None is an acceptance rule; the cost ratio over
  > the converged set stays the headline and the profiles say what it leaves out.

### F2 — The efficiency unit's licence is not shown, and the recorded timings are not published (C13, C14)

*Could change:* nothing in §6 as written, because §6 already withholds the wall-clock claim. It
could change what a reader concludes *from* §6: the paper's reader wants to know whether a
node-call saving of 36–55 % is a saving in any currency they pay in, and V3's answer (0–15 %
*slower*, §2.1) is the last word on the page. V4 recorded the data to update that word and did
not print it.

- **R:** a timing-context table per arm and configuration from `wall_s`, `cpu_user_s`,
  `cpu_sys_s`, `maxrss_kb` and `loadavg` over the campaign records — median and range, the
  W = 3 concurrency and the load average stated in the caption, the paper's form-of-time
  statement (wall and CPU, both) — placed where §3.5 check 5 promised it. Context, never
  evidence, as every record already says. The paper's *"background operations kept to a
  minimum"* is not met by a W = 3 campaign and the caption must say so; a serial repetition on
  an idle machine is a run and therefore V5.
- **T:** a hardware / OS / interpreter line in §3.10 or Appendix A.
- **V5 candidate item:**

  > ### n. The non-node cost term: identify it or bound it *(A81 (benchmarking-practices), 2026-09-15, from Beiranvand, Hare & Lucet 2017 §4.1; not the user's)*
  >
  > The paper licenses evaluation counts as the unit of cost only where evaluations dominate
  > the algorithm's internal work. V3 measured the partitioned arm 0–15 % slower in wall clock
  > at 36–55 % fewer node calls (V4 report §2.1); V4 counted the predicate overhead and excluded
  > it (§5.5) and published no timing. A V5 plan declares a serial, idle-machine timing pass
  > (3 repetitions, CPU and wall, hardware stated) on one seed per arm and configuration as a
  > *context* stage, and one count-based instrument for the remaining candidate term (the
  > prime's cost per call, the block schedule's dispatch cost) so that the gap between counts and
  > time is either attributed or bounded in counts. No conclusion rests on the timing; the
  > conclusion that *may* rest on the count is whether node calls dominate.

### F3 — Three configurations is a case study, and §6 does not say so (C6, C7, C10)

*Could change:* the generality any reader attaches to §6. The report's own §3.7 (b) and §3.11 use
the paper's exact words; §6 does not, and §6 is what is quoted.

- **T:** §6's licensed sentence gains the clause *"on three configurations — a case study by the
  benchmarking literature's threshold of twenty"*, with the citation.
- **V5:** more configurations, an easy/hard grouping declared in advance, and the second-objective
  probe of item 4 (a). The regression suite's nine input files include non-tokamak machines whose
  partition would have to be re-derived from their own dependency structure; the cost is real and
  the paper's reply would be that a version comparison wants a hundred problems, not three.
- **V5 candidate item:**

  > ### n. The configuration set: size, grouping and the second-objective probe *(A81 (benchmarking-practices), 2026-09-15, from Beiranvand, Hare & Lucet 2017 §3; not the user's)*
  >
  > V4 runs three configurations and calls them case studies (report §3.7 (b), §3.11). The
  > paper's threshold for a benchmark is twenty problems, a hundred for a version comparison,
  > and it asks for an easy and a hard group and for hidden structure to be probed. A V5 plan
  > (i) declares the configuration set with its membership rule before the campaign (as V5 item 1
  > already asks for `st_regression`), (ii) adds every regression-suite tokamak configuration
  > whose partition can be derived by the committed stages, (iii) declares which are easy and
  > which hard by a pre-declared statistic (V4's own: accepted optima out of 25 in the incumbent),
  > and (iv) runs one pulsed configuration under a second objective to break the
  > objective/structure confound (V4 list item 4 (a)). If the set stays below twenty, §6 carries
  > the case-study label in its licensed sentence.

### F4 — No profile, no figure (C27–C29)

*Could change:* not a verdict — the tables carry the medians and brackets — but the completeness
of the picture: the shape of the per-start ratio distribution between its bracket ends, the failed
starts, and the budget reading. The paper calls this a gold standard and asks for at least one.

- **R:** per configuration, (a) a data profile — for each arm, the fraction of 25 starts at an
  accepted optimum within `k` solve-phase node calls, `k` on a log axis; (b) a performance profile
  of the arm group with `r = ∞` for a failed start, log and linear τ, read against the best arm
  only; (c) the exit-audit residual's empirical distribution over the 25 starts per arm, as the
  fixed-target analogue of an accuracy profile. All three from `node_calls_solve_phase`,
  `status`, `ifail` and the audit fields in the records, rendered by a committed script under
  protocol §15 and recomputed by the second implementation like every other table. Figures are a
  new output kind for the renderer and the recomputation gate; the underlying step functions are
  tables and can be tallied cell by cell as the tables are.

### F5 — Verdicts at one threshold, no sensitivity (C24, C26)

*Could change:* the check-1 verdict on `low_aspect_ratio_DEMO` (FAIL at p90 2.148e-6 against
1e-6) and the check-2 verdicts (PASS at ≤ 1.05, with medians 1.0000 / 0.8125 / 1.0000). The
paper's criticism of cut-off tables is that they do not say how they would change if the cut-off
did.

- **R:** beside each verdict column, the threshold at which the verdict would flip (for check 1,
  the p90 itself is that number and is already printed; for check 2, the median is); a one-line
  caption sentence saying so costs nothing. A small table of verdicts at F ∈ {3, 10, 30} and floor
  ∈ {1e-7, 1e-6, 1e-5} is a re-tally of published cells.
- **V5:** declare the sensitivity band with the threshold (V5 item 1 already retires check 2 as
  an acceptance rule and publishes ε instead, which is this finding's remedy for check 2).

### F6 — The parameter rationale is provenance, not reasoning (C23)

*Could change:* nothing measured; what a reader can judge. Table 6 says where F = 10, the 1.05
bound and the cluster gap came from, not why those values.

- **T:** one sentence per knob in §3.10.

### F7 — The computing environment is not in the report (C14, C32)

- **T:** hardware, OS, interpreter and environment name in §3.10 or Appendix A. (The repository's
  CLAUDE.md and trap T5 hold the facts; the report should not depend on them.)

### F8 — Constraint violations recorded, only one published (C16, C20)

- **R:** a per-arm summary of the constraint residual vector at accepted optima (max and count above
  VMCON's own feasibility tolerance), from the recorded vector (§3.8 (ii)).

### The data profile's construction on V4's records — stated as a construction, not as numbers

For configuration `c` and arm `s`, with `N_{c,s}(i)` the solve-phase node calls of start `i`
(summed over attempts, check 4's unit) and `ok_{c,s}(i)` true when the start reached an accepted
optimum: `d_{c,s}(k) = |{ i ∈ 1..25 : ok_{c,s}(i) and N_{c,s}(i) ≤ k }| / 25`. Its value as
`k → ∞` is the per-arm success rate of F1; its value at the incumbent's median cost is the budget
reading. No filter, no pairing, no reference arm — the paper's *"the data profile for a given
solver is independent of other solvers"*. It is built from fields every campaign record carries
and it is not built here: the brief forbids edits to the experiment folder and this document
publishes no number that is not in the report.

---

## 4. What the paper would ask us to publish that we do not, and what V4 does that the paper does not ask for

**Asked for, absent:**

1. A per-arm success rate with denominator 25, in the headline table (§4.2 of the paper).
2. At least one profile — performance, data or accuracy — per configuration (§5.2–5.5, Table 4).
3. Running time in a stated form (wall and/or CPU) with the hardware, even as context (§4.1); V4's
   own §3.5 check 5 promised it.
4. The computing environment — hardware, OS, interpreter (§7).
5. The sensitivity of every verdict to its threshold (§5.1, §7.1).
6. The rationale for each declared parameter, not only its origin (§4.4).
7. The case-study label in the conclusion, given three configurations (§3 (i)).
8. A summary of constraint violations at the accepted optima (§4.2, §4.3), beyond constraint 93.
9. Standard deviations beside means (§4.2) — V4 prints the range instead, which is at least as
   informative here; a sentence saying so would close the point.

**Done, not asked for:**

1. **Gates with teeth** (§3.9, Table 5): every gate must be shown able to fail before its zeros
   are accepted — 161 of 161 teeth tripped (§4.1). The paper has no concept of a gate that proves
   its own capacity to fail.
2. **Recomputation by a second implementation** sharing no construction with the first — 14 394
   cells, 0 mismatched (§4.4). The paper asks that authors be able to replicate; V4 replicates
   inside the report.
3. **Bit-comparison as an acceptance quantity** — hex-float identity, exact counts, no tolerance
   anywhere in a gate (§2.3, §3.9). The paper's measures are all real-valued.
4. **Matched achieved accuracy verified per run** by an exit audit on the same ruler in every
   arm (§3.6), instead of matched tolerance settings; the paper's discussion of stopping conditions
   stops at "recognise the source of error".
5. **The stopping rule as an arm** (RQ4; `AR → A0`, `BR → B0`), so that its cost and its
   accuracy are published terms.
6. **A ladder whose rungs differ by one declared thing, enforced by the harness** (§3.2 Table 3),
   with a predicate-matched control between the incumbent and the intervention (D18).
7. **Pre-registration with dated amendments and a button that refuses the campaign until
   approval** (header; Appendix C; Appendix A) — the paper asks for a priori design, not for
   its enforcement.
8. **Retries as a counted term with both readings** (§3.5), and the attempt-summation identity
   printed per run (companion F.15/F.18/F.21).
9. **A reproduction gate against the previous revision's records through a rewritten harness**
   (GR, 256 of 256).
10. **The rule that a failed gate is a result, never retried with other settings** (protocol §6;
    §3.9), and that no number is published from a shell command (protocol §15).

None of the second list excuses anything in the first. The paper's standards and V4's are largely
orthogonal: the paper is about *what to measure and how to show it*; V4's strengths are in *proving
the measurement is what it says*. The shortfalls above are all on the paper's side of that line.

---

## 5. Limits of this evaluation

- **One reader, one pass.** The criteria were extracted by one agent from one reading of the
  arXiv text; a second reader would draw the section boundaries differently (C28–C30 could be one
  criterion or five) and the tally would move by a few rows without changing the findings.
- **One paper.** Beiranvand, Hare and Lucet is a review, and its recommendations are the field's
  consensus as of 2017; it cites Gould & Scott (2016) on the limits of performance profiles and
  Moré & Wild (2009) on data profiles, and does not cover paired designs, which are V4's backbone.
  A criterion the paper does not state (for example on pairing, or on the choice between medians
  and means) is not evaluated here.
- **The report at one commit.** Everything about V4 is read from `EXPERIMENT_REPORT.md` and
  `RESULTS_TABLES_FULL.md` at `589138ef`, the harness source for the record fields, and the queue's
  decision register. A80 (report-accuracy-audit) is correcting the report in parallel; issue I-26
  (the check-2 *evaluations median* column is the sweep ratio) is known and not re-found here.
  Table numbers are positions (trap T17) and every citation above also names the construction.
- **Hand counts.** The per-arm success counts in §2.1 and F1 (12 / 12 / 11 / 11 of 25 on
  `low_aspect_ratio_DEMO`; the two asymmetric st failures) are row counts from companion Tables
  F.17 and F.20 made by reading, not by a committed script (protocol §15 binds published numbers;
  these are offered as the illustration of a finding and are to be re-derived by the script F1
  proposes before any is cited as a result).
- **No run, no figure.** The profiles this document says are constructible were not constructed;
  their constructibility is asserted from the record schema (`harness/core/records.py` field table)
  and the companion tables that already print the fields per run.
- **Fairness in both directions was attempted, not guaranteed.** The evaluator is a participant in
  the project whose method it evaluates.
