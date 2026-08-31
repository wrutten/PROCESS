# Architecture surgery on PROCESS

> **Document status** — CURRENT · entry point for the study · 2026-08-31.

Does the **arrangement of solvers and optimisers alone** change the cost and robustness of solving
[PROCESS](https://github.com/ukaea/PROCESS), UKAEA's fusion power-plant systems code — with every
physics and engineering model left exactly as upstream wrote it?

That constraint is the whole design. A rewritten back-end cannot answer the question, because any
measured difference confounds the architecture with the rewrite. Here the models are frozen and
only the driver changes.

## Start here

| | |
|---|---|
| [`docs/plans/MASTER_TODO.md`](docs/plans/MASTER_TODO.md) | **The queue** — protocol, decisions, issues, task rows. Read before working. |
| [`docs/TRAPS.md`](docs/TRAPS.md) | **Binding.** Five recorded ways this project has already misled someone. |
| [`../CLAUDE.md`](../CLAUDE.md) | Hard rules, working rules, environments. |
| [`docs/plans/MDA_PARTITION_EXPERIMENT.md`](docs/plans/MDA_PARTITION_EXPERIMENT.md) | The live experiment. |

## The base commit, and why it is frozen

Everything is measured at **`c0ae5b28`** — upstream PROCESS, *"Rename optimisation problem setup
variables (#4481)"*. It is not an arbitrary pin:

- It is the last commit before [`functional_PROCESS`](https://github.com/timobogaarts/PROCESS)
  begins adding its rewritten back-end, so that rewrite is derived from this exact `process/` tree.
- It is the ancestor of the dependency-analysis pin `PROCESS_at_36ac820e` in
  `PROCESS_code_analysis`.

So this study, the functional rewrite and the static analysis **share one coordinate system**.
Moving the base forfeits every cross-study comparison, which is why it is frozen (decision D2).

## Layout

```
arch_surgery/
  docs/plans/       the queue, experiment plans, registry allocations
  docs/reports/     task reports; deprecated/ holds merged and superseded ones
  docs/TRAPS.md     recurring ways to be misled
  idf_probe/        the measurement instrument, its scenario deck and run harness
process/            upstream PROCESS at c0ae5b28 — the subject, not the product
```

`process/`, `tests/` and `documentation/` are upstream's. The only files this study changes there
are the driver (`process/core/caller.py`, `process/core/solver/`) and its probe
(`process/core/_idf_probe.py`).

## Where things stand

**Stage 0 is complete.** A1 (stage0-rebaseline) established the measurement apparatus at
`c0ae5b28` and passed three gates 4/4 — switch-neutrality, determinism, and all four scenarios
solving. Its report is the authoritative baseline:
[`docs/reports/deprecated/A1_stage0_rebaseline.md`](docs/reports/deprecated/A1_stage0_rebaseline.md).

The measured baseline: **3.2–3.5 sweeps per `call_models`** against a structural floor of 2, with
**38–42 % of sweeps above the floor** — the headroom the partition targets — and **94–96 % of all
sweeps being finite-difference gradient perturbations**.

Two live experiments and one deferred register are described in `docs/plans/`.

## Reading the documents

Two conventions worth knowing before you trust a number:

- **Nothing measured at `710a75c9` is evidence** (decision D4). An earlier IDF study ran at that
  commit; its plan and memos are retained for methodology only and every one carries a status
  header saying so.
- **Folder position records lifecycle, not validity.** `docs/reports/deprecated/` holds both merged
  task reports (still authoritative) and superseded documents (stale). Read the
  `> **Document status**` header, not the path.

## Related repositories

| | |
|---|---|
| `PROCESS_code_analysis` | The static-analysis instrument that produces the dependency graph and DSM this study reasons from. |
| `functional_PROCESS` | A separate rewrite with a different purpose, sharing the `c0ae5b28` base. |
| `ukaea/PROCESS` | Upstream, on the `upstream` remote, read-only for drift measurement. |
