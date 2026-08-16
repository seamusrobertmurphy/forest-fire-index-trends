#!/usr/bin/env python3
"""
Merge pass-one screening decisions and enforce that they are complete.

Written 2026-08-14. Screening was distributed across batches, so the failure to
guard against is a record decided twice, decided with an unrecognised verdict,
or not decided at all and quietly dropped from the denominator. Every one of
those corrupts the PRISMA-ScR flow silently, which is why this refuses to write
rather than warning.

Inputs. `02.inputs/derived/pass-one-decisions-rules.csv` for the record-type
exclusions, and one `<batch>-decisions.csv` per batch file under
`02.inputs/searches/batches/`, each with columns `bibcode`, `screen_decision`,
`screen_reason`.

Outputs. `02.inputs/derived/ads-pass-one-screening.csv` rewritten with the two
decision columns filled and a `decided_by` column, and
`02.inputs/derived/prisma-scr-counts.csv` carrying the stage counts for the flow
diagram, per strand, in the vocabulary `02.inputs/derived/README.md` fixes.

Checks, all fatal.

  Every record in the retrieval is decided exactly once.
  Every decision is `include` or `exclude`.
  Every reason is non-empty and starts with a recognised code.
  Every batch decisions file covers its own batch and no other record.

Usage:  python3 05.scripts/screen_pass_one_merge.py
"""

import collections
import csv
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RECORDS = os.path.join(HERE, "..", "02.inputs", "searches",
                       "ads-pass-one-records.csv")
BATCH_DIR = os.path.join(HERE, "..", "02.inputs", "searches", "batches")
RULES = os.path.join(HERE, "..", "02.inputs", "derived",
                     "pass-one-decisions-rules.csv")
SCREEN = os.path.join(HERE, "..", "02.inputs", "derived",
                      "ads-pass-one-screening.csv")
COUNTS = os.path.join(HERE, "..", "02.inputs", "derived",
                      "prisma-scr-counts.csv")

DECISIONS = {"include", "exclude"}

# Controlled reason codes. A free-text note follows the code after a colon; the
# code is what the charting table groups on, so it is not left to prose.
INCLUDE_CODES = {"method", "modification", "theoretical position",
                 "record constraint", "quantitative precedent"}
EXCLUDE_CODES = {"application only", "domain does not transfer", "off topic",
                 "not English", "ineligible record type"}


def code_of(reason):
    return reason.split(":", 1)[0].strip().lower()


def fail(msg):
    sys.exit(f"REFUSING TO MERGE. {msg}")


def main():
    with open(RECORDS) as fh:
        records = {r["bibcode"]: r for r in csv.DictReader(fh)}
    if not records:
        fail(f"No records at {RECORDS}.")

    decided = {}

    def add(bibcode, decision, reason, by, source):
        if bibcode not in records:
            fail(f"{source} decides {bibcode}, which is not in the retrieval.")
        if bibcode in decided:
            fail(f"{bibcode} decided twice: {decided[bibcode][2]} and {source}.")
        if decision not in DECISIONS:
            fail(f"{source}: {bibcode} has decision {decision!r}, "
                 f"not one of {sorted(DECISIONS)}.")
        if not reason.strip():
            fail(f"{source}: {bibcode} has an empty reason.")
        codes = INCLUDE_CODES if decision == "include" else EXCLUDE_CODES
        # Codes are compared case-folded: `not English` carries a capital that a
        # screener has no reason to preserve, and rejecting the row over it
        # would discard a sound decision on a typographic detail.
        codes = {c.lower() for c in codes}
        if code_of(reason) not in codes:
            fail(f"{source}: {bibcode} reason starts {code_of(reason)!r}, "
                 f"not one of {sorted(codes)}.")
        decided[bibcode] = (decision, reason, source, by)

    with open(RULES) as fh:
        for r in csv.DictReader(fh):
            add(r["bibcode"], r["screen_decision"], r["screen_reason"],
                r["decided_by"], "rules")

    batches = sorted(f[:-6] for f in os.listdir(BATCH_DIR)
                     if f.endswith(".jsonl"))
    if not batches:
        fail(f"No batch files under {BATCH_DIR}.")

    for name in batches:
        with open(os.path.join(BATCH_DIR, f"{name}.jsonl")) as fh:
            expect = {json.loads(line)["bibcode"] for line in fh if line.strip()}
        path = os.path.join(BATCH_DIR, f"{name}-decisions.csv")
        if not os.path.exists(path):
            fail(f"Batch {name} has {len(expect)} records and no decisions "
                 f"file at {os.path.relpath(path)}.")
        with open(path) as fh:
            got = list(csv.DictReader(fh))
        seen = set()
        for r in got:
            bib = r["bibcode"].strip()
            if bib not in expect:
                fail(f"{name}-decisions.csv decides {bib}, which is not in "
                     f"batch {name}.")
            seen.add(bib)
            add(bib, r["screen_decision"].strip().lower(),
                r["screen_reason"].strip(), f"screener:{name}", name)
        missing = expect - seen
        if missing:
            fail(f"Batch {name}: {len(missing)} records undecided, first five "
                 f"{sorted(missing)[:5]}.")

    undecided = set(records) - set(decided)
    if undecided:
        fail(f"{len(undecided)} records in the retrieval were never decided.")

    # --- Write the screening sheet ---------------------------------------
    ordered = sorted(records.items(),
                     key=lambda kv: (kv[1].get("year") or "", kv[0]))
    with open(SCREEN, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["bibcode", "year", "doi", "bibstem", "doctype", "refereed",
                    "citation_count", "title", "strands", "n_strings",
                    "screen_decision", "screen_reason", "decided_by"])
        for bib, r in ordered:
            dec, reason, source, by = decided[bib]
            w.writerow([bib, r["year"], r["doi"], r["bibstem"], r["doctype"],
                        r["refereed"], r["citation_count"], r["title"],
                        r["strands"], len(r["found_by"].split("|")),
                        dec, reason, by])

    # --- Write the flow-diagram counts ------------------------------------
    # Strand attribution follows the batching rule: a record retrieved by
    # several strands is counted once, under the first strand that retrieved it.
    # `identified_other` is the citation-led route; everything else is database
    # searching. Duplicates are attributed to the strand that kept the record.
    PRIORITY = ["S1", "S2", "S3", "S4", "S5", "S1+S5"]

    def strand_of(r):
        ss = r["strands"].split("|")
        for p in PRIORITY:
            if p in ss:
                return p
        return "?"

    ident = collections.Counter()
    other = collections.Counter()
    dupes = collections.Counter()
    screened = collections.Counter()
    excluded = collections.Counter()
    sought = collections.Counter()
    for bib, r in records.items():
        s = strand_of(r)
        n_hits = len(r["found_by"].split("|"))
        if s == "S1+S5":
            other[s] += 1
        else:
            ident[s] += 1
        dupes[s] += n_hits - 1
        screened[s] += 1
        if decided[bib][0] == "exclude":
            excluded[s] += 1
        else:
            sought[s] += 1

    rows = []
    for s in PRIORITY:
        rows.append([s, "identified_database", ident[s]])
        rows.append([s, "identified_other", other[s]])
        rows.append([s, "duplicates_removed", dupes[s]])
        rows.append([s, "screened", screened[s]])
        rows.append([s, "excluded_screening", excluded[s]])
        rows.append([s, "fulltext_sought", sought[s]])
    with open(COUNTS, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["strand", "stage", "n"])
        w.writerows(rows)

    n_inc = sum(sought.values())
    print(f"Decided {len(decided)} records, none twice, none missed.")
    print(f"  Rule-based exclusions:        {sum(1 for d in decided.values() if d[2] == 'rules')}")
    print(f"  Excluded at title and abstract: {sum(excluded.values())}")
    print(f"  Carried to full text:         {n_inc}")
    print(f"\nWritten {os.path.relpath(SCREEN, os.path.join(HERE, '..'))}")
    print(f"Written {os.path.relpath(COUNTS, os.path.join(HERE, '..'))}, "
          "stages through fulltext_sought only.")
    print("The later stages are written when full text has been assessed.")


if __name__ == "__main__":
    main()
