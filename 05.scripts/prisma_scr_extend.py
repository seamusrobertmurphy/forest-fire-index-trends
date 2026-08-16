#!/usr/bin/env python3
"""Extend the PRISMA-ScR counts with the full-text stages, per strand.

Written 2026-08-14. `prisma-scr-counts.csv` carried stages through
`fulltext_sought` only, so `05.scripts/prisma_scr_flow.R` refused to draw the
diagram, which is the guard working. This fills the three remaining stages from
the charted table rather than by hand, so the counts the diagram draws and the
decisions they summarise cannot drift apart.

The three stages, and what each is counted from:

  fulltext_unobtainable   ft_decision == unobtainable
  fulltext_assessed       sought minus unobtainable
  included                ft_decision == include

`excluded_fulltext` follows as assessed minus included, and is written rather
than derived at draw time so that the CSV is self-describing.

Counting is per strand, on the same one-strand-per-record assignment the
batching used, because the flow diagram reports per strand and a record that
several strands retrieved must not be counted in each of them.

This script **replaces** any existing rows for the three stages rather than
appending, so it is safe to re-run after a re-merge. It refuses to write
anything if the resulting flow would not balance, on the same identities the R
script enforces: catching that here gives a message naming the strand, rather
than a stop from the drawing code.

Usage:  python3 05.scripts/prisma_scr_extend.py
"""

from __future__ import annotations

import csv
import pathlib
import sys

PRIORITY = ["S1", "S2", "S3", "S4", "S5", "S1+S5"]
WRITES = ["fulltext_unobtainable", "fulltext_assessed", "excluded_fulltext",
          "included"]


def repo_root() -> pathlib.Path:
    here = pathlib.Path(__file__).resolve()
    for cand in [here.parent, *here.parents]:
        if (cand / "02.inputs").is_dir() and (cand / "05.scripts").is_dir():
            return cand
    sys.exit("Not inside the forest-fire-index-trends repository.")


ROOT = repo_root()
CHARTED = ROOT / "02.inputs" / "derived" / "fulltext-pass-one-charted.csv"
COUNTS = ROOT / "02.inputs" / "derived" / "prisma-scr-counts.csv"


def strand_of(strands: str) -> str:
    got = set((strands or "").split("|"))
    for s in PRIORITY:
        if s in got:
            return s
    return sorted(got)[0] if got else "unassigned"


def main() -> None:
    if not CHARTED.exists():
        sys.exit("Charted table not found. Run fulltext_pass_one_merge.py first.")

    with CHARTED.open(newline="", encoding="utf-8") as fh:
        charted = list(csv.DictReader(fh))
    with COUNTS.open(newline="", encoding="utf-8") as fh:
        existing = [r for r in csv.DictReader(fh)]

    sought = {}
    for r in existing:
        if r["stage"] == "fulltext_sought":
            sought[r["strand"]] = int(r["n"])

    tallies: dict[str, dict[str, int]] = {}
    for r in charted:
        s = strand_of(r["strand"])
        t = tallies.setdefault(s, {"unobtainable": 0, "include": 0, "exclude": 0})
        d = r["ft_decision"]
        if d in t:
            t[d if d != "unobtainable" else "unobtainable"] += 1

    rows = [r for r in existing if r["stage"] not in WRITES]
    problems = []
    for s in sorted(tallies, key=lambda x: (PRIORITY.index(x)
                                            if x in PRIORITY else 99)):
        t = tallies[s]
        n_sought = sought.get(s)
        n_assessed = t["include"] + t["exclude"]
        if n_sought is None:
            problems.append(f"{s}: no fulltext_sought row to reconcile against")
            continue
        if n_sought != n_assessed + t["unobtainable"]:
            problems.append(
                f"{s}: sought {n_sought} but assessed {n_assessed} plus "
                f"unobtainable {t['unobtainable']} is "
                f"{n_assessed + t['unobtainable']}")
        rows += [
            {"strand": s, "stage": "fulltext_unobtainable",
             "n": t["unobtainable"]},
            {"strand": s, "stage": "fulltext_assessed", "n": n_assessed},
            {"strand": s, "stage": "excluded_fulltext", "n": t["exclude"]},
            {"strand": s, "stage": "included", "n": t["include"]},
        ]

    if problems:
        print("REFUSING TO WRITE. The flow would not balance:", file=sys.stderr)
        for p in problems:
            print(f"  {p}", file=sys.stderr)
        sys.exit(1)

    order = ["identified_database", "identified_other", "duplicates_removed",
             "screened", "excluded_screening", "fulltext_sought"] + WRITES
    rows.sort(key=lambda r: (PRIORITY.index(r["strand"])
                             if r["strand"] in PRIORITY else 99,
                             order.index(r["stage"]) if r["stage"] in order
                             else 99))
    with COUNTS.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["strand", "stage", "n"])
        w.writeheader()
        w.writerows(rows)

    tot = {}
    for r in rows:
        tot[r["stage"]] = tot.get(r["stage"], 0) + int(r["n"])
    print(f"Written {COUNTS.relative_to(ROOT)}\n")
    for st in order:
        if st in tot:
            print(f"  {st:24s} {tot[st]:5d}")
    print("\nThe flow balances. 05.scripts/prisma_scr_flow.R can now draw it.")


if __name__ == "__main__":
    main()
