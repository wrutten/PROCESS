# Reports

One report per task, written by the task's agent.

## Conventions

- **Verdict first.** The first section says what was found and whether the gates passed,
  before any method.
- **Gates are reported as they landed.** A failed gate is a result; it is never tuned into
  passing, and the report carries the numbers that failed.
- **Autonomous decisions are listed with their reversal paths** — what the agent decided
  without asking, and how to undo it.
- **Append-only change log** at the foot of each report.
- **Jargon is spelled out at first use.** Decision numbers, issue numbers and internal
  vocabulary are explained, so the report reads without the queue open beside it.
- The orchestrator appends a **critical assessment** to every report before merge.

## Lifecycle

Live reports sit here while their task is open. **At merge the report is archived to
[`deprecated/`](deprecated/)** — this directory holds only open tasks' reports.
