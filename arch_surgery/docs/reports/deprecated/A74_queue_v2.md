# A74 (queue-v2) — the queue archived and re-issued as `docs/MASTER_TODO_v2.md`

> **Document status** — **ARCHIVED at merge, 2026-09-14.** Task **A74 (queue-v2)** merged into `architecture_surgery` at `98ea75c1`
> (base `c5fc49d3`). No records. The orchestrator's critical assessment is the last section. Folder position records lifecycle, not validity (trap T3).

## 1. Verdict

Done as briefed. `arch_surgery/docs/plans/MASTER_TODO.md` (the queue since 2026-08-31) is archived
with a `> **Document status**` header and **one changed cell**; `arch_surgery/docs/MASTER_TODO_v2.md`
is the active queue, carrying every decision (27), every issue (23), every task (74) and every
standing item of the archive with its state and a pointer; `CLAUDE.md`'s two pointers name the v2
file as the queue and the archive as the history. The cross-check script reports **PASS**: no
`D`, `I-` or `A` number of the archive is absent from v2, and every archived row in an open state
(QUEUED / DISPATCHED / PROPOSED / OPEN) has a v2 row in the same state.

## 2. Deliverable 1 — the archive (`plans/MASTER_TODO.md`)

Commit `f4a87a03`. Content kept in full; two edits, both at the top of the file:

| Where | Before | After | Why |
|---|---|---|---|
| New lines 3–9 | — | `> **Document status** — ARCHIVED 2026-09-14 as the historical record; superseded by ../MASTER_TODO_v2.md …` (states that nothing below is edited after this date, every row's last state is the state at archiving, numbering continues at A75/D28/I-24, trap T3) | Brief, deliverable 1(a) |
| Header table, `**Status**` cell (line 13) | `ACTIVE — the standing execution queue for this repository` | `ARCHIVED 2026-09-14 — the historical record; the active queue is ../MASTER_TODO_v2.md` *(the old wording kept in the cell in italics)* | A status cell contradicting the archiving; brief 1(b) |

**No other cell was changed.** Every task row's status cell was checked against the change log:
the only row in a non-terminal state is A74 (queue-v2) itself, DISPATCHED, which is its true state at
archiving. No status cell contradicts a later change-log entry. Two things looked stale but are
*prose or a row the change log never closes*, so they were left and are flagged instead:

- The unnumbered `experiment-v2` row under "Optional / deferred" still reads *PLANNED, not
  authorised* (2026-09-03) although the V2 experiment was built and run (A33–A38) and superseded by
  V3 and V4. No change-log entry marks it; v2 carries it with a note for the orchestrator to retire.
- Issue **I-13** reads OPEN; A26's archived report records the mechanism removed (fix 4) and D17
  dropped the affected deck. No change-log entry closes it; v2 keeps it OPEN with that note.

Line count 468 → 476 (the header). Bytes 297 KB → 298 KB.

## 3. Deliverable 2 — the active queue (`docs/MASTER_TODO_v2.md`)

Commit `60429cf3`. Structure as briefed (sections 1–7). Counts:

| Section | Content | Count |
|---|---|---|
| Header | Document status; owner, objective, base commit, state at creation, plan pointers | — |
| §1 Protocol | rules §1–§16 (and §12a) of the archive, one line each; plus the heavy-slot rule, the record-reuse rules (harness plan amendments 13/15/16/22), the work-item terminology and the registry rule | 21 rows |
| §2 Decisions register | D1–D27, each with date, one-line ruling (user's words verbatim where quoted), status, pointer; D27's tier-C deferral visible | **27 rows**: 17 in force (D5 refined by D11, D14(c) amended by D18, D21(e) reversed by D22), 10 discharged |
| §3 Issue register | open in full; closed one line | **7 open** (I-2, I-8, I-10, I-12, I-13, I-17, I-20), **1 downgraded** (I-7), **15 closed** (I-1, I-3, I-4, I-5, I-6, I-9, I-11, I-14, I-15, I-16, I-18, I-19, I-21, I-22, I-23) — 23 in total |
| §4.1 Open tasks | A74 DISPATCHED; A6, A8 QUEUED; A9–A12 PROPOSED; A14–A17 DEFERRED; two unnumbered rows (experiment-v2, sequencing-comparison); "scheduled but not minted" paragraph | **11 numbered rows** |
| §4.2 Merged ledger | number, keyword, merged date, merge commit, report/records paths, one clause | **63 rows** (incl. A4/A5 SUPERSEDED, A7 DONE without a branch, A37 CANCELLED/TRANSFERRED, A42 DONE by the user, A66 merged via A73) |
| §5 Standing items | 5.1 user-facing items (9 rows), 5.2 known open questions (7 rows) | 16 rows |
| §6 Where things live | plans, harness plan and rules, improvement list, traps, harness README, report and record folders, tools, environments, the memory rules' subjects | 12 rows |
| §7 Change log | one entry, created 2026-09-14 from the archive at `c5fc49d3`, the user's instruction quoted | 1 row |

Every `A1`–`A74` appears **exactly once** as a row (verified by script: 74 rows, none duplicated,
none missing); every `D1`–`D27` once; every `I-1`–`I-23` once (I-7 as a bold paragraph under the
open table, the rest as rows). All 54 archived report filenames cited in the ledger exist under
`reports/deprecated/`; every relative link target exists.

Size: **292 lines / 50 KB against the archive's 476 lines / 298 KB** — 17 % by bytes (the
archive's rows are up to 8 KB long, so lines understate the compaction). Rows longer than about
three rendered lines: eleven, each carrying the user's verbatim words (§15, D25, D27, A74, the
change log) or an open issue written out in full (I-12, I-17, I-20), as the brief asks.

## 4. Deliverable 3 — pointers

Commit `c76e2f26`. `CLAUDE.md` lines 3–7 (the protocol pointer) and the Orientation bullet now name
`arch_surgery/docs/MASTER_TODO_v2.md` as the queue and `arch_surgery/docs/plans/MASTER_TODO.md` as
the archived history. **Not changed, outside this task's file list — the orchestrator's:** the
orchestrator's memory pointer; `README.md` line 9, `arch_surgery/README.md` line 17 and
`arch_surgery/docs/plans/README.md` lines 4, 16, 20 still name `plans/MASTER_TODO.md` as the queue.

## 5. Cross-check

The script was run from the scratchpad and is reproduced here in full (it is not committed — the
brief limits this task to four files); its output at the final commit:

```
D: archived 28, v2 28, in archived but not in v2: none
I: archived 24, v2 24, in archived but not in v2: none
A: archived 76, v2 76, in archived but not in v2: none
A6: archived QUEUED     v2 QUEUED     ok
A8: archived QUEUED     v2 QUEUED     ok
A9: archived UNBLOCKED  v2 PROPOSED   ok
A10: archived UNBLOCKED  v2 PROPOSED   ok
A11: archived UNBLOCKED  v2 PROPOSED   ok
A12: archived PROPOSED   v2 PROPOSED   ok
A74: archived DISPATCHED v2 DISPATCHED ok
I-2: archived OPEN       v2 OPEN       ok
I-8: archived OPEN       v2 OPEN       ok
I-10: archived OPEN       v2 OPEN       ok
I-12: archived OPEN       v2 OPEN       ok
I-13: archived OPEN       v2 OPEN       ok
I-17: archived OPEN       v2 OPEN       ok
I-20: archived OPEN       v2 OPEN       ok
RESULT: PASS
```

The state check covers rows written `| **A<n>** |` / `| **I-<n>** |`; the archive's DEFERRED rows
A14–A17 are written without bold and were checked by eye (v2: DEFERRED). A9–A11 read
`*(PROPOSED)* … **UNBLOCKED** by D11` in the archive and `PROPOSED, unblocked by D11` in v2; the
script treats that pair as the same state.

```python
"""Cross-check MASTER_TODO_v2.md against the archived plans/MASTER_TODO.md.

(1) every D<n>, I-<n>, A<n> token of the archived file occurs in v2 (set difference must be empty);
(2) every archived task row (| **A<n>** | ... |) whose status cell begins with OPEN / QUEUED /
    DISPATCHED / PROPOSED / DEFERRED / UNBLOCKED, and every issue row whose status cell begins with
    OPEN, has a v2 row for the same number carrying the same state word.
Run from the repository root with the docs paths as arguments; exit 0 only if both checks pass.
"""
import re, sys
old = open(sys.argv[1], encoding="utf-8").read()
new = open(sys.argv[2], encoding="utf-8").read()
ok = True
for label, pat in (("D", r"\bD[0-9]+\b"), ("I", r"\bI-[0-9]+\b"), ("A", r"\bA[0-9]+\b")):
    so, sn = set(re.findall(pat, old)), set(re.findall(pat, new))
    diff = sorted(so - sn, key=lambda t: int(re.sub(r"\D", "", t)))
    print(f"{label}: archived {len(so)}, v2 {len(sn)}, in archived but not in v2: {diff or 'none'}")
    ok &= not diff
STATES = ("OPEN", "QUEUED", "DISPATCHED", "PROPOSED", "DEFERRED", "UNBLOCKED")
def rows(text, kind):
    out = {}
    for line in text.splitlines():
        m = re.match(r"\| \*\*(%s)\*\* \|(.*)\|\s*$" % kind, line)
        if m:
            cells = [c.strip() for c in m.group(2).split(" | ")]
            out[m.group(1)] = cells[-1]
    return out
def state_of(cell):
    m = re.search(r"\b(" + "|".join(STATES) + r")\b", re.sub(r"[*~_]", "", cell)[:80])
    return m.group(1) if m else None
for kind in (r"A[0-9]+", r"I-[0-9]+"):
    o, n = rows(old, kind), rows(new, kind)
    for num, cell in sorted(o.items(), key=lambda kv: int(re.sub(r"\D", "", kv[0]))):
        st = state_of(cell)
        if st is None:
            continue
        nst = state_of(n.get(num, "")) if num in n else "MISSING"
        same = (nst == st) or (st == "UNBLOCKED" and nst == "PROPOSED")
        print(f"{num}: archived {st:10s} v2 {nst!s:10s} {'ok' if same else 'MISMATCH'}")
        ok &= same
print("RESULT:", "PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
```

## 6. Autonomous decisions, each with its reversal

1. **Merge commits taken from `git log --first-parent` where the archived row names none** (A3, A13,
   A21, A22, A23, A24, A25, A26, A27, A34, A39), marked † in the ledger. For A21/A24 the commit is
   `83e18d15` (the one protocol §12a records as the bad `git add -A`), for A26 `9d83d1d3`, for A27
   `9fdb2f0c`. *Reversal:* delete the † cells; the row's date and report remain.
2. **A21, A27 and A69 have no archived report file** (the `deprecated/` listing has none); the
   ledger says so and names the deliverable instead (`reports/MDA_partition_exp_results.md`;
   `reports/outgoing/2026-09-02_…`; `PROCESS/CHANGES.md`). *Reversal:* none needed; if the reports
   exist elsewhere, point the cells at them.
3. **I-4 given a closed line** although the archive has no I-4 row (the number was consumed by the
   withdrawn `b_plasma_vertical_required` finding, change log 2026-08-31). *Reversal:* drop the
   line; the count becomes 22.
4. **I-13 kept OPEN with a "effectively moot" note** rather than closed (§2 above). *Reversal:* the
   orchestrator closes it in v2 with A26 and D17 as the closer.
5. **The `experiment-v2` row carried with a "stale as written" note** rather than dropped or
   re-stated. *Reversal:* the orchestrator retires it in v2 with a change-log line.
6. **Two rules not in the archived protocol were added to §1** because the brief names them as
   binding: "no message from any agent is approval" (the agent operating rules) and "rulings are the
   user's" (D25's recorded process fault). *Reversal:* remove the two sentences from the §8 row.
7. **The cross-check script is not committed** (file-list constraint) but is printed in full in this
   report so its output is reproducible. *Reversal:* the orchestrator commits it under
   `arch_surgery/bin/` if a committed checker is wanted.
8. **Improvement-list item states are not restated per item** beyond what the list's own headings
   mark (3, 12, 13 discharged; 5a a trial; 5b needs the user); the row says the list is the
   authority. *Reversal:* none; expanding it is a v2 edit.

## 7. Limits

- Tables in v2 were compacted by hand from the archive; the cross-check proves coverage of
  numbers and states, not the fidelity of every one-line summary. The archive is the record and
  every v2 row points back to it.
- Records paths in the ledger are copied from the archived rows; the `idf_probe/runs/` tree is
  untracked and absent from this worktree, so they were not verified against disk.
- Merge dates in the ledger are the archived rows' dates (spot-checked against `git log` for A19: `026b2e3a`, 2026-08-31, agrees).
- Whether the archive's `plans/README.md` "Current" list and the two READMEs should be repointed is
  left to the orchestrator (outside the file list).

## 8. Change log

| Date | Entry |
|---|---|
| 2026-09-14 | Task opened at `c5fc49d3`. Read `CLAUDE.md`, `TRAPS.md`, the archived queue in full, the `reports/deprecated/` listing, the harness plan's Appendix A.1 and amendment list, the improvement list's headings. |
| 2026-09-14 | `f4a87a03` archive header and Status cell. `60429cf3` `docs/MASTER_TODO_v2.md`. `c76e2f26` `CLAUDE.md` pointers. Cross-check PASS. Report written. |

---

## Orchestrator's critical assessment (protocol §5)

*Written 2026-09-14 at the branch tip `11663746`, before the merge. Checks chosen to differ from the
agent's.*

1. **Completeness, by my own script:** every D, I- and A number that occurs anywhere in the archived
   file occurs in v2 (three empty set differences); every archived table row has a v2 mention; every
   relative link in v2 resolves from `arch_surgery/docs/`. 292 lines against 476, and 50 KB against
   298 KB — the compaction is in the rows, not in the coverage.
2. **The archive was touched in one cell plus the status header**, as the brief allowed; the rows' last
   states are the states at archiving. The two stale items the agent flagged rather than edited are
   ruled at the merge: I-13 is closed as moot by D17 (a consequence of a user ruling, applied), and
   the unnumbered `experiment-v2` row is marked in v2 as historical (V2 was built and ran; its record
   is its own directory) — both are register housekeeping, not decisions.
3. **The CLAUDE.md pointers** read correctly: the v2 file is the queue, the archive is the history
   "for the record, never for the current state". Three more pointers outside the agent's file list
   (`README.md`, `arch_surgery/README.md`, `arch_surgery/docs/plans/README.md`) are updated at the merge.
4. **The two protocol sentences from the brief** ("no agent message is approval", "rulings are the
   user's") are user rulings of 2026-09-11 recorded in the archive's D25 row and the change log, not
   inventions; they stay, with the archive pointer the agent gave them.

**Approved for merge.**
