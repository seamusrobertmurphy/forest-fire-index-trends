"""Merge the screening decisions of the 2026-10-13 literature review into the screening table.

Reads every decisions-*.csv under 02.inputs/searches/review-batches/, checks that each id
was decided exactly once and that every exclusion carries a code from the protocol, and
writes decision, reason and note into 02.inputs/derived/review-records.csv. A record that
already carries a decision in the table (hand-found records, records excluded by the
document-type rule) keeps it. Run from the repository root with python3 -I.
"""
import csv, glob, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TABLE = os.path.join(ROOT, "02.inputs", "derived", "review-records.csv")
BATCHES = os.path.join(ROOT, "02.inputs", "searches", "review-batches")
CODES = {"off-topic", "wrong-population", "wrong-concept", "not-research", "out-of-window", "not-english", "duplicate"}

def main():
    with open(TABLE, encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    fields = list(rows[0].keys())
    if "note" not in fields: fields.append("note")
    decided = {}
    for p in sorted(glob.glob(os.path.join(BATCHES, "decisions-*.csv"))):
        with open(p, encoding="utf-8", newline="") as f:
            for d in csv.DictReader(f):
                if d["id"] in decided:
                    sys.exit(f"id decided twice: {d['id']} in {p}")
                if d["decision"] not in {"include", "exclude", "undecided"}:
                    sys.exit(f"bad decision {d['decision']!r} for {d['id']} in {p}")
                if d["decision"] == "exclude" and d["reason"] not in CODES:
                    sys.exit(f"bad reason {d['reason']!r} for {d['id']} in {p}")
                decided[d["id"]] = d
    n_set = 0
    for r in rows:
        r.setdefault("note", "")
        if r.get("decision"):
            continue
        d = decided.get(r["id"])
        if d:
            r["decision"], r["reason"], r["note"] = d["decision"], d["reason"], d.get("note", ""); n_set += 1
    missing = [r["id"] for r in rows if not r.get("decision")]
    with open(TABLE, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(rows)
    from collections import Counter
    print("decisions merged", n_set, "| undecided rows left without any decision", len(missing))
    print("by decision", Counter(r["decision"] for r in rows).most_common())
    print("by reason", Counter(r["reason"] for r in rows if r["decision"] == "exclude").most_common())
    if missing: print("first missing ids", missing[:10])

if __name__ == "__main__":
    main()
