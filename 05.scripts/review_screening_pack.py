"""Build the title-and-abstract screening batches for the 2026-10-13 literature review.

Reads the committed screening table 02.inputs/derived/review-records.csv, applies the
document-type rule of the review protocol (records of an ineligible type are excluded by
rule with the code not-research), attaches each remaining record's abstract from the
uncommitted search files under 02.inputs/searches, fetches the abstract from OpenAlex by
DOI where no search file holds it, and writes one batch per question under
02.inputs/searches/review-batches/. Abstracts are publisher text and never leave
02.inputs/searches. Run from the repository root with python3 -I.
"""
import csv, json, os, sys, time, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DERIVED = os.path.join(ROOT, "02.inputs", "derived")
SEARCHES = os.path.join(ROOT, "02.inputs", "searches")
BATCHES = os.path.join(SEARCHES, "review-batches")
MAILTO = "seamusrobertmurphy@gmail.com"
INELIGIBLE = {"abstract", "conference-abstract", "dataset", "peer-review", "paratext", "erratum", "editorial", "letter", "other"}

def read(p):
    with open(p, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))

def write(p, rows, fields):
    with open(p, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(rows)

def abstract_from_inverted(inv):
    if not inv: return ""
    pos = []
    for word, idx in inv.items():
        for i in idx: pos.append((i, word))
    return " ".join(w for _, w in sorted(pos))

def fetch_openalex(dois):
    out = {}
    for i in range(0, len(dois), 50):
        chunk = dois[i:i + 50]
        # OpenAlex works endpoint, https://docs.openalex.org/api-entities/works
        url = "https://api.openalex.org/works?" + urllib.parse.urlencode({
            "filter": "doi:" + "|".join(chunk), "per-page": 50,
            "select": "doi,abstract_inverted_index,type", "mailto": MAILTO})
        for attempt in range(4):
            try:
                with urllib.request.urlopen(url, timeout=60) as r:
                    body = json.load(r)
                break
            except Exception as e:
                time.sleep(3 * (attempt + 1)); body = {"results": []}
        for w in body.get("results", []):
            d = (w.get("doi") or "").replace("https://doi.org/", "").lower()
            out[d] = (abstract_from_inverted(w.get("abstract_inverted_index")), w.get("type") or "")
        time.sleep(0.2)
    return out

def main():
    records = read(os.path.join(DERIVED, "review-records.csv"))
    abstracts = {}
    for name in ("review-openalex-records.csv", "review-ads-records.csv"):
        p = os.path.join(SEARCHES, name)
        if not os.path.exists(p): continue
        for r in read(p):
            key = (r.get("doi") or "").lower() or r["title"].lower()
            if r.get("abstract"): abstracts.setdefault(key, r["abstract"])
    need = [r["doi"] for r in records if r["doi"] and r["doi"].lower() not in abstracts]
    fetched = fetch_openalex(need)
    for d, (a, t) in fetched.items():
        if a: abstracts[d] = a
    n_rule = 0
    for r in records:
        if not r["type"] and r["doi"] and r["doi"].lower() in fetched:
            r["type"] = fetched[r["doi"].lower()][1]
        if r["type"] in INELIGIBLE:
            r["decision"], r["reason"] = "exclude", "not-research"; n_rule += 1
    write(os.path.join(DERIVED, "review-records.csv"), records, list(records[0].keys()))
    os.makedirs(BATCHES, exist_ok=True)
    batches = {}
    for r in records:
        if r["decision"]: continue
        key = (r["doi"] or "").lower() or r["id"]
        row = {"id": r["id"], "doi": r["doi"], "title": r["title"], "year": r["year"], "venue": r["venue"],
               "type": r["type"], "questions": r["questions"], "cited": r["cited"],
               "abstract": abstracts.get(key, "")}
        q = r["questions"].split()[0] if r["questions"] else "chase"
        batches.setdefault(q, []).append(row)
    fields = ["id", "doi", "title", "year", "venue", "type", "questions", "cited", "abstract"]
    for q, rows in batches.items():
        if q == "chase" and len(rows) > 220:
            half = (len(rows) + 1) // 2
            write(os.path.join(BATCHES, "chase-a.csv"), rows[:half], fields)
            write(os.path.join(BATCHES, "chase-b.csv"), rows[half:], fields)
        else:
            write(os.path.join(BATCHES, f"{q}.csv"), rows, fields)
    print("records", len(records), "excluded by type rule", n_rule,
          "to screen", sum(len(v) for v in batches.values()),
          "with abstract", sum(1 for v in batches.values() for r in v if r["abstract"]))
    for q, rows in batches.items(): print(" ", q, len(rows))

if __name__ == "__main__":
    main()
