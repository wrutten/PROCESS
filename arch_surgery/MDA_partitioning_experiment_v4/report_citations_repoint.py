"""Re-point every table citation in EXPERIMENT_REPORT.md at the new set."""
import sys

PAIRS = [
    # citations split across a line break, and the ones whose first half the
    # pairs above already moved
    ("Table D.4 and D.25–D.27", "Tables D.4 and D.5"),
    ("companion\nTables F.53–F.55", "companion Table F.12"),
    ("companion\nTables F.15, F.19 and F.23", "companion Table F.4"),
    ("the recomputed tables themselves are companion Tables F.56–F.162",
     "the recomputed copies themselves are not rendered — that row is the check, and the gate's record holds the cells"),
    ("headline Tables\nD.2–D.5", "headline Tables 8 and 9"),
    ("companion Tables F.14,\nF.18 and F.22", "companion Table F.3"),
    ("companion Tables F.14, F.18 and F.22", "companion Table F.3"),
    ("the three headline shapes as Tables D.2–D.9", "the three headline shapes as Tables D.2\u2013D.9 of that day"),
    # --- phrases that name several old tables at once -----------------------
    ("Tables F.16, F.20 and F.24 (the identity) and F.17, F.21 and F.25 (the per-run overhead)",
     "companion Table F.5 (the identity) and companion Table F.6 (the per-run overhead)"),
    ("companion Tables F.17, F.21 and F.25", "companion Table F.6"),
    ("companion Tables F.15, F.19 and F.23", "companion Table F.4"),
    ("companion Tables F.14,\nF.18 and F.22", "companion Table F.3"),
    ("companion Tables F.14, F.18\nand F.22", "companion Table F.3"),
    ("Tables F.1–F.12", "companion Table F.1"),
    ("companion Tables F.53–F.55", "companion Table F.12"),
    ("companion Tables F.47–F.49", "companion Table F.10"),
    ("companion Table F.54", "companion Table F.12"),
    ("companion Table F.13", "companion Table F.2"),
    ("companion Table F.19", "companion Table F.4"),
    ("companion Table F.23", "companion Table F.4"),
    ("companion Table F.17's", "companion Table F.6's"),
    ("Table F.19;", "companion Table F.4;"),
    ("companion Table F.7", "companion Table F.12"),
    # --- the appendix's own tables -----------------------------------------
    ("Tables D.2–D.83", "Tables 7–9 and Tables D.2–D.14"),
    ("Tables D.55–D.60", "Table D.8"),
    ("Tables D.49–D.60", "Tables D.3 and D.8"),
    ("Tables D.61–D.63", "Table D.9"),
    ("Tables D.61–D.66", "Table D.9"),
    ("Tables D.64–D.66", "Table D.9"),
    ("Tables D.67–D.69", "Table D.9"),
    ("Tables D.62, D.65", "Table D.9"),
    ("Table D.62", "Table D.9"),
    ("Tables D.13–D.15", "Table D.4"),
    ("Tables D.16–D.21", "Table D.4"),
    ("Table D.13's", "Table D.4's"),
    ("Tables D.25–D.27", "Table D.5"),
    ("Tables D.34–D.36", "Table D.6"),
    ("Tables D.34–D.35", "Table D.6"),
    ("Tables D.37–D.42", "Table D.6"),
    ("Tables D.34–D.42", "Table D.6"),
    ("Table D.40", "Table D.6"),
    ("Tables D.43–D.44", "Table D.7"),
    ("Tables D.70–D.72", "Table D.10"),
    ("Table D.71's", "Table D.10's"),
    ("Tables D.73–D.74", "Table D.11"),
    ("Tables D.73–D.75", "Table D.11"),
    ("Tables D.76–D.78", "Table D.12"),
    ("Tables D.79–D.81", "Table D.13"),
    ("Tables D.82–D.83", "Table D.14"),
    # --- the three headline tables, now in §4 -------------------------------
    ("Tables D.2–D.4", "Table 8"),
    ("Table D.5's", "Table 9's"),
    ("Table D.5", "Table 9"),
    ("Table D.7's", "Table 7's"),
    ("Table D.7", "Table 7"),
]


def main(path: str) -> int:
    text = open(path).read()
    head, sep, rest = text.partition("## Appendix D — Results tables")
    if not sep:
        raise SystemExit("no Appendix D heading")
    applied = []
    for old, new in PAIRS:
        n = head.count(old)
        if n:
            head = head.replace(old, new)
        applied.append((old, new, n))
    open(path, "w").write(head + sep + rest)
    total = sum(n for _o, _n, n in applied)
    for old, new, n in applied:
        print(f"  {n:>3} × {old!r} → {new!r}")
    print(f"  {total} citation(s) re-pointed in the hand-written text")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
