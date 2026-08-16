#!/usr/bin/env python3
"""Prepare the 758 carried records for full-text assessment and charting.

Written 2026-08-14. Stage two differs from stage one in what it produces, not
just in what it reads. Stage one returned a decision and a reason. Stage two
returns a decision, a reason, and the charting fields the protocol lists, which
are what the synthesis is actually built from: a review whose records are
included but not charted has sorted the literature without reading it.

Each batch record carries what an assessor needs to work without going back to
another file: the verified bibliography from the register, the abstract from the
retrieval, an open-access link where one exists, and the stage-one reason, so
the assessor can see what the record was carried forward *for* and test that
claim rather than form a fresh impression of the title.

Assessment is against the eligibility criteria at full text. Three outcomes are
possible and the third is not a failure: a record whose full text cannot be
obtained is recorded as unobtainable and counted as such in the PRISMA-ScR flow,
never quietly excluded and never assessed on its abstract as though the abstract
were the paper.

Usage:  python3 05.scripts/fulltext_pass_one_prepare.py
"""

from __future__ import annotations

import csv
import json
import pathlib
import sys

# One assessor reads one batch in one pass. Stage one used 48 and that worked;
# charting is heavier per record than screening, so the target is smaller.
BATCH_TARGET = 40

# A record retrieved by several strands is assessed once, under the first
# strand here that retrieved it. Same order as stage one, so a record does not
# change hands between stages.
PRIORITY = ["S1", "S2", "S3", "S4", "S5", "S1+S5"]


def repo_root() -> pathlib.Path:
    here = pathlib.Path(__file__).resolve()
    for cand in [here.parent, *here.parents]:
        if (cand / "02.inputs").is_dir() and (cand / "05.scripts").is_dir():
            return cand
    sys.exit("Not inside the forest-fire-index-trends repository.")


ROOT = repo_root()
REGISTER = ROOT / "02.inputs" / "derived" / "fulltext-pass-one-register.csv"
RECORDS = ROOT / "02.inputs" / "searches" / "ads-pass-one-records.csv"
SCREENING = ROOT / "02.inputs" / "derived" / "ads-pass-one-screening.csv"
BATCH_DIR = ROOT / "02.inputs" / "searches" / "batches-fulltext"


def strand_of(strands: str) -> str:
    """Assign one strand to a record that several strands retrieved."""
    got = set(strands.split("|"))
    for s in PRIORITY:
        if s in got:
            return s
    return sorted(got)[0] if got else "unassigned"


def main() -> None:
    if not REGISTER.exists():
        sys.exit("Register not found. Run fulltext_pass_one_locate.py first.")

    with REGISTER.open(newline="", encoding="utf-8") as fh:
        register = {r["bibcode"]: r for r in csv.DictReader(fh)}
    with RECORDS.open(newline="", encoding="utf-8") as fh:
        abstracts = {r["bibcode"]: r for r in csv.DictReader(fh)}
    with SCREENING.open(newline="", encoding="utf-8") as fh:
        stage1 = {r["bibcode"]: r for r in csv.DictReader(fh)}

    # The register is the authority on what is in stage two. Anything in it that
    # lost its abstract between stages would be assessed blind, so that is a
    # stop, not a warning.
    missing = [b for b in register if b not in abstracts]
    if missing:
        sys.exit(f"{len(missing)} register records have no retrieved abstract, "
                 f"first {missing[:3]}. Stage two cannot proceed blind.")

    by_strand: dict[str, list[dict]] = {}
    for bib, reg in register.items():
        a = abstracts[bib]
        rec = {
            "bibcode": bib,
            "doi": reg["doi"],
            "year": reg["cr_year"] or reg["ads_year"],
            "journal": reg["cr_container"] or a.get("pub", ""),
            "record_class": reg["record_class"],
            "verify_status": reg["verify_status"],
            "strands": reg["strands"],
            "title": reg["cr_title"] or reg["ads_title"],
            "abstract": a.get("abstract", ""),
            "obtainable": reg["obtainable"],
            "fulltext_route": reg["fulltext_route"],
            "oa_url": reg["oa_url"],
            "arxiv_id": reg["arxiv_id"],
            "stage1_reason": stage1.get(bib, {}).get("screen_reason", ""),
        }
        by_strand.setdefault(strand_of(reg["strands"]), []).append(rec)

    BATCH_DIR.mkdir(parents=True, exist_ok=True)
    for old in BATCH_DIR.glob("*.jsonl"):
        old.unlink()

    total, written = 0, []
    for strand in sorted(by_strand, key=lambda s: (PRIORITY.index(s)
                                                   if s in PRIORITY else 99)):
        rows = sorted(by_strand[strand], key=lambda r: r["bibcode"])
        # Equal-sized parts rather than cap-then-remainder, so a strand of 250
        # becomes seven batches of about 36 and not six of 40 plus one of 10.
        nparts = max(1, -(-len(rows) // BATCH_TARGET))
        size = -(-len(rows) // nparts)
        for i in range(nparts):
            chunk = rows[i * size:(i + 1) * size]
            if not chunk:
                continue
            name = strand.replace("+", "-") + (f"-{i + 1}" if nparts > 1 else "")
            path = BATCH_DIR / f"{name}.jsonl"
            with path.open("w", encoding="utf-8") as fh:
                for r in chunk:
                    fh.write(json.dumps(r, ensure_ascii=False) + "\n")
            written.append((name, len(chunk)))
            total += len(chunk)

    if total != len(register):
        sys.exit(f"Batched {total} but the register holds {len(register)}. "
                 f"Every record must be assessed exactly once.")

    print(f"{len(register)} records in {len(written)} batches, "
          f"written to {BATCH_DIR.relative_to(ROOT)}\n")
    for name, n in written:
        print(f"  {name:12s} {n:4d}")
    print(f"\n  {'total':12s} {total:4d}")


if __name__ == "__main__":
    main()
