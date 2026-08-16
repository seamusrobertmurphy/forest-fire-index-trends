#!/usr/bin/env python3
"""Merge the full-text assessments into one charted table, or refuse.

Written 2026-08-14. The counterpart to `screen_pass_one_merge.py` for stage two.
Its job is not to tidy the returns: it is to make a bad return impossible to
mistake for a good one.

The guarantees it enforces, each a stop rather than a warning:

* Every record in the register is decided exactly once. Not once on average, and
  not "all but a few". A record decided twice means two assessors disagreed
  without either knowing; a record decided zero times means the synthesis rests
  on a set nobody defined.
* Every decision is one of three, and `unobtainable` is one of them, because
  PRISMA-ScR counts full text sought, unobtainable and assessed as separate
  stages and collapsing them misstates the flow.
* Every reason opens with a controlled code. The charting table groups on that
  code, so a free-text reason that does not start with one is not chartable.
* Every included record carries the charting fields the protocol names. An
  inclusion with empty charting is an assertion that the paper is relevant with
  no record of what it contributes, which is what this stage exists to prevent.
* A record marked unobtainable must have been unobtainable in the register.
  Otherwise "I could not get it" and "I did not fetch it" become the same entry.

Usage:  python3 05.scripts/fulltext_pass_one_merge.py
"""

from __future__ import annotations

import csv
import pathlib
import sys

INCLUDE_CODES = {
    "method", "modification", "theoretical position",
    "data constraint", "quantitative precedent",
}
EXCLUDE_CODES = {
    "application only", "domain does not transfer", "off topic",
    "not English", "ineligible record type", "no contribution",
}
UNOBTAINABLE_CODES = {"full text unobtainable"}

# Charting fields the protocol lists. Every included record must fill the first
# group; the second group is filled where the paper reports it and "not
# reported" is an answer, but blank is not.
CHART_REQUIRED = ["study_type", "region", "variable", "bears_on"]

# What the judgement rests on. Without this column an assessment made from the
# abstract and one made from the paper are indistinguishable in the charted
# table, and the synthesis would report both as though the paper had been read.
# A quantitative precedent is held to the stricter standard: an effect size is
# exactly the kind of number that is mis-transcribed from an abstract, and this
# project has already been burned by numbers taken from summaries.
EVIDENCE_BASIS = {"full text", "abstract"}
CHART_EXPECTED = ["record_years", "estimator", "autocorrelation", "multiplicity",
                  "enso_handling", "effect_size", "limitation"]

OUT_FIELDS = (["bibcode", "doi", "year", "journal", "record_class", "strand",
               "title", "ft_decision", "ft_reason", "ft_code", "evidence_basis"]
              + CHART_REQUIRED + CHART_EXPECTED + ["decided_by"])


def repo_root() -> pathlib.Path:
    here = pathlib.Path(__file__).resolve()
    for cand in [here.parent, *here.parents]:
        if (cand / "02.inputs").is_dir() and (cand / "05.scripts").is_dir():
            return cand
    sys.exit("Not inside the forest-fire-index-trends repository.")


ROOT = repo_root()
REGISTER = ROOT / "02.inputs" / "derived" / "fulltext-pass-one-register.csv"
BATCH_DIR = ROOT / "02.inputs" / "searches" / "batches-fulltext"
OUT = ROOT / "02.inputs" / "derived" / "fulltext-pass-one-charted.csv"
COUNTS = ROOT / "02.inputs" / "derived" / "fulltext-pass-one-counts.csv"

problems: list[str] = []


def fail(msg: str) -> None:
    problems.append(msg)


def code_of(reason: str, decision: str) -> str:
    """Read the controlled code off the front of a reason."""
    codes = (INCLUDE_CODES if decision == "include"
             else UNOBTAINABLE_CODES if decision == "unobtainable"
             else EXCLUDE_CODES)
    low = (reason or "").strip().lower()
    for c in sorted(codes, key=len, reverse=True):
        if low.startswith(c.lower()):
            return c
    return ""


def main() -> None:
    with REGISTER.open(newline="", encoding="utf-8") as fh:
        register = {r["bibcode"]: r for r in csv.DictReader(fh)}

    files = sorted(BATCH_DIR.glob("*-charted.csv"))
    if not files:
        sys.exit(f"No assessment files in {BATCH_DIR.relative_to(ROOT)}. "
                 f"Expected one <batch>-charted.csv per batch.")

    seen: dict[str, str] = {}
    rows: dict[str, dict] = {}

    for path in files:
        who = path.name.replace("-charted.csv", "")
        with path.open(newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                bib = (r.get("bibcode") or "").strip()
                if not bib:
                    fail(f"{path.name}: a row has no bibcode")
                    continue
                if bib not in register:
                    fail(f"{path.name}: {bib} is not in the register")
                    continue
                if bib in seen:
                    fail(f"{bib} decided twice, by {seen[bib]} and by {who}")
                    continue
                seen[bib] = who

                dec = (r.get("ft_decision") or "").strip().lower()
                reason = (r.get("ft_reason") or "").strip()
                if dec not in {"include", "exclude", "unobtainable"}:
                    fail(f"{path.name}: {bib} decision {dec!r} is not one of "
                         f"include, exclude, unobtainable")
                    continue

                code = code_of(reason, dec)
                if not code:
                    fail(f"{path.name}: {bib} reason does not open with a "
                         f"controlled code: {reason[:70]!r}")

                if dec == "unobtainable" and register[bib]["obtainable"] == "yes":
                    fail(f"{path.name}: {bib} marked unobtainable but the "
                         f"register located a copy at "
                         f"{register[bib]['fulltext_route']}")

                basis = (r.get("evidence_basis") or "").strip().lower()
                if dec != "unobtainable" and basis not in EVIDENCE_BASIS:
                    fail(f"{path.name}: {bib} evidence_basis {basis!r} is not "
                         f"one of {sorted(EVIDENCE_BASIS)}")
                if code == "quantitative precedent" and basis != "full text":
                    fail(f"{path.name}: {bib} reports a quantitative precedent "
                         f"from the {basis or 'unstated'}; an effect size entering "
                         f"the synthesis must be read in the paper")

                if dec == "include":
                    blank = [f for f in CHART_REQUIRED if not (r.get(f) or "").strip()]
                    if blank:
                        fail(f"{path.name}: {bib} included with empty charting "
                             f"fields {blank}")

                reg = register[bib]
                out = {k: "" for k in OUT_FIELDS}
                out.update(
                    bibcode=bib, doi=reg["doi"],
                    year=reg["cr_year"] or reg["ads_year"],
                    journal=reg["cr_container"], record_class=reg["record_class"],
                    strand=reg["strands"], title=reg["cr_title"] or reg["ads_title"],
                    ft_decision=dec, ft_reason=reason, ft_code=code,
                    evidence_basis=basis, decided_by=who,
                )
                for f in CHART_REQUIRED + CHART_EXPECTED:
                    out[f] = (r.get(f) or "").strip()
                rows[bib] = out

    undecided = [b for b in register if b not in seen]
    if undecided:
        fail(f"{len(undecided)} records were never decided, first "
             f"{undecided[:5]}")

    if problems:
        print(f"REFUSING TO MERGE. {len(problems)} problems:\n", file=sys.stderr)
        for p in problems[:60]:
            print(f"  {p}", file=sys.stderr)
        if len(problems) > 60:
            print(f"  ... and {len(problems) - 60} more", file=sys.stderr)
        sys.exit(1)

    ordered = [rows[b] for b in sorted(rows)]
    with OUT.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=OUT_FIELDS)
        w.writeheader()
        w.writerows(ordered)
    print(f"Merged {len(ordered)} assessments into {OUT.relative_to(ROOT)}")

    tally: dict[tuple[str, str], int] = {}
    for r in ordered:
        for key, val in (("ft_decision", r["ft_decision"]),
                         ("ft_code", r["ft_code"]),
                         ("evidence_basis", r["evidence_basis"] or "(none)"),
                         ("record_class", r["record_class"]),
                         ("bears_on", r["bears_on"] or "(none)")):
            tally[(key, val)] = tally.get((key, val), 0) + 1
    with COUNTS.open("a", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        for (k, v), n in sorted(tally.items()):
            w.writerow([k, v, n])
    print(f"Appended tallies to {COUNTS.relative_to(ROOT)}\n")
    for (k, v), n in sorted(tally.items()):
        if k == "ft_decision" or k == "ft_code":
            print(f"  {k:14s} {v:30s} {n:5d}")


if __name__ == "__main__":
    main()
