#!/usr/bin/env python3
"""
Prepare pass one for title and abstract screening.

Written 2026-08-14. Two jobs, and a rule about which is which.

1. Rule-based exclusion. ADS indexes meeting abstracts, funding proposals and
   datasets alongside articles, and the signed-off strings carry no `doctype`
   filter, so 741 of the 2,010 unique records are of a record type the
   eligibility criteria cannot admit under any reading. Excluding them is
   arithmetic, not judgement, so it is done here in code with a fixed reason
   rather than by a reviewer one record at a time. Each such record is still
   identified and still screened; it is excluded with its reason recorded, which
   is what the PRISMA-ScR flow requires.

2. Batching. Every remaining record is assigned to exactly one screening batch
   and written out with its title and abstract, so that no record is screened
   twice and none is missed. A record retrieved by several strands is assigned
   to the first strand in PRIORITY that retrieved it; the assignment is recorded
   in the batch file, and the full strand list travels with the record so the
   screener can see it.

Nothing here makes a judgement-based inclusion or exclusion. The batch files
carry no decision column of their own: decisions come back in separate files and
are merged by `screen_pass_one_merge.py`, which refuses to merge unless every
record was decided exactly once.

Usage:  python3 05.scripts/screen_pass_one_prepare.py
"""

import csv
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RECORDS = os.path.join(HERE, "..", "02.inputs", "searches",
                       "ads-pass-one-records.csv")
BATCH_DIR = os.path.join(HERE, "..", "02.inputs", "searches", "batches")
RULES_OUT = os.path.join(HERE, "..", "02.inputs", "derived",
                         "pass-one-decisions-rules.csv")

# Record types no eligibility criterion in the protocol admits. `inproceedings`
# is NOT here: a conference paper can carry a method. `eprint` is not here
# either: preprints are eligible, flagged as preprints. `abstract` is a meeting
# abstract, a few hundred words with no method to extract.
INELIGIBLE = {
    "abstract": "meeting abstract, not a full record; no method to extract",
    "proposal": "funding proposal, not a research output",
    "dataset": "dataset record, not a bibliographic source",
}

# A record retrieved by more than one strand is screened once, in the first
# strand listed here that retrieved it.
PRIORITY = ["S1", "S2", "S3", "S4", "S5", "S1+S5"]

# Batches are capped so that one screener reads one file in one pass. A strand
# larger than the cap splits into equal numbered parts and keeps its strand
# identity. Equal rather than cap-then-remainder, so a strand of 413 becomes
# three batches of 138 rather than 200, 200 and 13.
CAP = 200

STRAND_QUESTION = {
    "S1": "Estimation under variability: how a monotonic trend is estimated in "
          "an autocorrelated geophysical series of 40 to 50 seasons, and the "
          "documented failure modes.",
    "S2": "ENSO handling: how ENSO is removed, adjusted for or stratified "
          "against in trend work, what that does to the estimate, and the "
          "ENSO and PDO teleconnection to fire activity in western North "
          "America.",
    "S3": "Detection theory: what the field takes a detected trend to mean. "
          "Detection against attribution, fingerprinting, time of emergence, "
          "large ensembles as a null, storyline against probabilistic.",
    "S4": "Satellite positioning: what the satellite and reanalysis record "
          "permits and forbids. Sensor bounds, product generations and "
          "intercalibration, climate data record criteria, transition "
          "artefacts presenting as trends.",
    "S5": "Record-length limits: the minimum record length needed to detect a "
          "trend of a given size at a given variance and autocorrelation, and "
          "what that arithmetic says about a 46-season window.",
    "S1+S5": "Citation-led set, forward chaining from Yue et al. 2002, Hamed "
             "and Rao 1998 and Weatherhead et al. 1998, intersected with the "
             "fire block. Bears on S1 and S5 both.",
}


def batch_of(strands):
    for p in PRIORITY:
        if p in strands:
            return p
    return None


def main():
    with open(RECORDS) as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        sys.exit(f"No records at {RECORDS}. Run ads_pass_one_retrieve.py first.")

    ruled, keep = [], []
    for r in rows:
        reason = INELIGIBLE.get(r["doctype"])
        if reason:
            ruled.append([r["bibcode"], "rule", "exclude",
                          f"ineligible record type: {reason}",
                          "05.scripts/screen_pass_one_prepare.py"])
        else:
            keep.append(r)

    os.makedirs(os.path.dirname(RULES_OUT), exist_ok=True)
    with open(RULES_OUT, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["bibcode", "batch", "screen_decision", "screen_reason",
                    "decided_by"])
        w.writerows(ruled)

    groups = {}
    for r in keep:
        b = batch_of(r["strands"].split("|"))
        if b is None:
            sys.exit(f"Record {r['bibcode']} has no recognised strand: "
                     f"{r['strands']}")
        groups.setdefault(b, []).append(r)

    os.makedirs(BATCH_DIR, exist_ok=True)
    for f in os.listdir(BATCH_DIR):
        os.remove(os.path.join(BATCH_DIR, f))

    manifest = []
    for strand in PRIORITY:
        recs = groups.get(strand, [])
        if not recs:
            continue
        recs.sort(key=lambda r: r["bibcode"])
        n_parts = -(-len(recs) // CAP)
        size = -(-len(recs) // n_parts)
        parts = [recs[i:i + size] for i in range(0, len(recs), size)]
        for i, part in enumerate(parts, 1):
            name = (strand.replace("+", "-") if len(parts) == 1
                    else f"{strand.replace('+', '-')}-{i}")
            path = os.path.join(BATCH_DIR, f"{name}.jsonl")
            with open(path, "w") as fh:
                for r in part:
                    fh.write(json.dumps({
                        "bibcode": r["bibcode"],
                        "year": r["year"],
                        "doctype": r["doctype"],
                        "refereed": r["refereed"],
                        "journal": r["pub"],
                        "strands": r["strands"],
                        "title": r["title"],
                        "abstract": r["abstract"],
                    }) + "\n")
            manifest.append((name, strand, len(part), path))

    print(f"Rule-based exclusions: {len(ruled)} records, "
          f"{os.path.relpath(RULES_OUT, os.path.join(HERE, '..'))}")
    print(f"Carried to screening:  {len(keep)} records in "
          f"{len(manifest)} batches\n")
    for name, strand, n, path in manifest:
        print(f"  {name:<8} {n:>4} records  "
              f"{os.path.relpath(path, os.path.join(HERE, '..'))}")
    total = sum(n for _, _, n, _ in manifest)
    if total != len(keep):
        sys.exit(f"Batching lost records: {total} batched, {len(keep)} kept.")
    print(f"\n  {total} batched, {len(keep)} kept, no record lost.")
    print("No judgement-based decision has been made. Batches carry no "
          "decision column.")


if __name__ == "__main__":
    main()
