# Plans

Stage- and task-level planning documents. The queue that sequences them is
[`../MASTER_TODO_v2.md`](../MASTER_TODO_v2.md); [`MASTER_TODO.md`](MASTER_TODO.md) here is the archived history (2026-09-14).

## Conventions

- **One document per task or stage**, named `A<n>_<keyword>.md` for task plans; standing
  experiment plans keep a descriptive name.
- A plan states its **hypothesis, the evidence it rests on, its gates, and its stop rules**.
  A plan without a stop rule is not finished.
- **Every claim is sourced.** A number carries the run that produced it; a code claim carries
  the file and line. Claims inherited from the superseded `710a75c9` study are not evidence
  (D4) and may not be restated without remeasurement.
- Plans are **revised in place** as evidence arrives, with the change recorded in
  `../MASTER_TODO_v2.md`'s change log. Superseded plans move to `deprecated/`.

## Current

- [`MASTER_TODO.md`](MASTER_TODO.md) — the queue **as archived 2026-09-14**; the active queue is [`../MASTER_TODO_v2.md`](../MASTER_TODO_v2.md).
- [`../MDA_PARTITION_EXPERIMENT.md`](../MDA_PARTITION_EXPERIMENT.md) — the standing experiment
  plan (relocation here is queued as A8 (plan-relocation)).
