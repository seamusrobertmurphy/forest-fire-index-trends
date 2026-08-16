#!/usr/bin/env python3
"""
Pass one of the prior-work scoping review: retrieval, not screening.

Written 2026-08-14, after Seamus's PRESS sign-off of the same date. Executes the
nine pass-one strings plus the citation-led union intersected with the fire
block, retrieves every record each one returns, deduplicates by bibcode and
writes the screening sheet the single reviewer works from.

The strings are not restated here. They are imported from
`ads_search_calibration.py`, which is what the sign-off covers, so the executed
search and the approved search cannot drift apart. A string whose live yield
differs from its calibrated yield is reported as a difference rather than
quietly accepted, because PRISMA-S requires the search to be reported as it
actually happened.

This script retrieves and deduplicates. It makes no inclusion or exclusion
decision: `screen_decision` and `screen_reason` are written empty and are the
reviewer's to fill.

Three outputs.

  02.inputs/searches/ads-pass-one-records.csv   Full retrieval with abstracts.
      Not committed. Abstracts are publisher text and the repository does not
      redistribute third-party literature, in any format.
  02.inputs/derived/ads-pass-one-searchlog.csv  PRISMA-S search log: one row per
      executed string with its source, query, date, yield and retrieved count.
  02.inputs/derived/ads-pass-one-screening.csv  Deduplicated screening sheet,
      bibliographic metadata only, one row per unique record.

Credential is read from ~/.ads/dev_key and is never printed.

Usage:  python3 05.scripts/ads_pass_one_retrieve.py
"""

import csv
import json
import os
import sys
import time
import urllib.parse
import urllib.request

API = "https://api.adsabs.harvard.edu/v1/search/query"
HERE = os.path.dirname(os.path.abspath(__file__))
RAW_OUT = os.path.join(HERE, "..", "02.inputs", "searches",
                       "ads-pass-one-records.csv")
LOG_OUT = os.path.join(HERE, "..", "02.inputs", "derived",
                       "ads-pass-one-searchlog.csv")
SCREEN_OUT = os.path.join(HERE, "..", "02.inputs", "derived",
                          "ads-pass-one-screening.csv")

# The search date is passed in rather than taken from the clock, so that a rerun
# reproduces the log it produced rather than restamping it with today's date.
SEARCH_DATE = os.environ.get("ADS_SEARCH_DATE", "2026-08-14")

# ADS caps a single response at 2000 rows and caps deep paging by `start`;
# cursorMark is the documented way through a result set of any size. Solr
# requires the cursor sort to end in the index's unique key, which in ADS is
# `id` and not `bibcode`: `sort=date desc,bibcode desc` returns HTTP 400.
PAGE = 200
SORT = "date desc,id desc"
FIELDS = ("bibcode,title,abstract,author,year,pubdate,doi,pub,bibstem,"
          "doctype,property,citation_count,keyword")

sys.path.insert(0, HERE)
from ads_search_calibration import (            # noqa: E402
    FIRE, SEEDS, STRINGS, YEARS, read_key,
)


def request(key, params):
    url = f"{API}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {key}"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def retrieve(key, q):
    """Every record for q. Returns (numFound, docs). Raises on API failure.

    A partial retrieval that is silently treated as complete would put a wrong
    denominator in the flow diagram, so a failure here is fatal rather than
    warned about.
    """
    docs, cursor = [], "*"
    num_found = None
    while True:
        resp = request(key, {"q": q, "rows": PAGE, "fl": FIELDS,
                             "sort": SORT, "cursorMark": cursor})
        block = resp["response"]
        if num_found is None:
            num_found = block["numFound"]
        docs.extend(block["docs"])
        nxt = resp.get("nextCursorMark")
        if nxt is None or nxt == cursor or len(docs) >= num_found:
            break
        cursor = nxt
        time.sleep(0.05)
    return num_found, docs


def dated(strand, q):
    """Apply the protocol's date limits. Unchanged from the calibration run."""
    yr = YEARS.get(strand)
    return f"{q} AND {yr}" if yr and not q.startswith("citations(") else q


def flat(doc, field):
    v = doc.get(field)
    if isinstance(v, list):
        return "; ".join(str(x) for x in v)
    return "" if v is None else str(v)


def refereed(doc):
    """ADS returns `property` in upper case, so the test is case-folded."""
    return "REFEREED" in {str(p).upper() for p in (doc.get("property") or [])}


def first(doc, field):
    v = doc.get(field)
    if isinstance(v, list):
        return str(v[0]) if v else ""
    return "" if v is None else str(v)


def main():
    key = read_key()
    log, records = [], {}

    # --- Database searching: the nine pass-one strings ---------------------
    print(f"Pass one, {SEARCH_DATE}. Nine strings, then the citation-led set.\n")
    pass_one = [(s, lab, q) for s, lab, q, p in STRINGS if p == 1]
    if len(pass_one) != 9:
        sys.exit(f"Expected nine pass-one strings, found {len(pass_one)}. "
                 "The sign-off covers nine; refusing to run.")

    for strand, label, q in pass_one:
        q_dated = dated(strand, q)
        n_found, docs = retrieve(key, q_dated)
        for d in docs:
            rec = records.setdefault(d["bibcode"], {"doc": d, "hits": []})
            rec["hits"].append((strand, label))
        log.append(["database", strand, label, q_dated, SEARCH_DATE,
                    n_found, len(docs)])
        print(f"  {strand}  {n_found:>5} found, {len(docs):>5} retrieved  "
              f"{label}")
        time.sleep(0.05)

    n_db_records = sum(r[6] for r in log)
    n_db_unique = len(records)

    # --- Other means: citation-led, intersected with the fire block --------
    union = " OR ".join(f"citations(bibcode:{b})" for _, _, b in SEEDS)
    q_cite = f"({union}) AND {FIRE}"
    n_found, docs = retrieve(key, q_cite)
    for d in docs:
        rec = records.setdefault(d["bibcode"], {"doc": d, "hits": []})
        rec["hits"].append(("S1+S5", "citation-led, seeds intersected with fire"))
    log.append(["citation chaining", "S1+S5",
                "forward chaining from three verified seeds, fire-intersected",
                q_cite, SEARCH_DATE, n_found, len(docs)])
    print(f"  S1+S5  {n_found:>5} found, {len(docs):>5} retrieved  "
          f"citation-led, fire-intersected")

    n_cite_records = len(docs)
    n_total_hits = n_db_records + n_cite_records
    n_unique = len(records)
    print(f"\n  Identified by database searching: {n_db_records}")
    print(f"  Identified by citation chaining:  {n_cite_records}")
    print(f"  Records before deduplication:     {n_total_hits}")
    print(f"  Unique records:                   {n_unique}")
    print(f"  Duplicates removed:               {n_total_hits - n_unique}")
    print(f"  Of which the citation set added:  {n_unique - n_db_unique} new")

    # --- Calibration comparison -------------------------------------------
    # The calibrated yields the sign-off was given on are in
    # 02.inputs/derived/ads-search-calibration.csv. A live count that has moved
    # is a fact about the index between the two dates, and it is reported.
    calib = os.path.join(HERE, "..", "02.inputs", "derived",
                         "ads-search-calibration.csv")
    if os.path.exists(calib):
        with open(calib) as fh:
            prior = {(r["strand"], r["label"]): int(r["n_found"])
                     for r in csv.DictReader(fh)
                     if r["kind"] == "string-pass1" and r["n_found"].isdigit()}
        moved = [(s, lab, prior[(s, lab)], n)
                 for kind, s, lab, q, d, n, got in log
                 if (s, lab) in prior and prior[(s, lab)] != n]
        if moved:
            print("\n  Yields that moved since calibration:")
            for s, lab, was, now in moved:
                print(f"    {s}  {was} -> {now}  {lab}")
        else:
            print("\n  Every string reproduced its calibrated yield exactly.")

    # --- Write ------------------------------------------------------------
    for path in (RAW_OUT, LOG_OUT, SCREEN_OUT):
        os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(LOG_OUT, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["route", "strand", "label", "query", "search_date",
                    "n_found", "n_retrieved"])
        w.writerows(log)

    ordered = sorted(records.items(),
                     key=lambda kv: (kv[1]["doc"].get("year") or "", kv[0]))

    with open(RAW_OUT, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["bibcode", "year", "pubdate", "doi", "pub", "bibstem",
                    "doctype", "refereed", "citation_count", "authors",
                    "title", "abstract", "keywords", "strands", "found_by"])
        for bib, rec in ordered:
            d = rec["doc"]
            w.writerow([
                bib, d.get("year", ""), d.get("pubdate", ""), first(d, "doi"),
                d.get("pub", ""), first(d, "bibstem"), d.get("doctype", ""),
                refereed(d), d.get("citation_count", ""), flat(d, "author"),
                first(d, "title"), first(d, "abstract"), flat(d, "keyword"),
                "|".join(sorted({s for s, _ in rec["hits"]})),
                "|".join(lab for _, lab in rec["hits"]),
            ])

    # The screening sheet carries bibliographic metadata and the reviewer's two
    # decision columns, and no abstract text. Screening is done against the raw
    # file above; what is committed is the decision and its reason.
    #
    # Once screening has run, `screen_pass_one_merge.py` owns this file. Rerunning
    # this script would otherwise blank 2,010 recorded decisions in silence, which
    # is a day's work and an auditable record gone, so a sheet that already holds
    # decisions is left alone and the run says so.
    if os.path.exists(SCREEN_OUT):
        with open(SCREEN_OUT) as fh:
            decided = sum(1 for r in csv.DictReader(fh)
                          if (r.get("screen_decision") or "").strip())
        if decided:
            print(f"\n{os.path.relpath(SCREEN_OUT, os.path.join(HERE, '..'))} "
                  f"holds {decided} recorded decisions and was NOT overwritten.")
            print("Delete it deliberately if a fresh screening sheet is wanted.")
            print(f"\nWritten {os.path.relpath(RAW_OUT, os.path.join(HERE, '..'))}"
                  f" and {os.path.relpath(LOG_OUT, os.path.join(HERE, '..'))}.")
            return

    with open(SCREEN_OUT, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["bibcode", "year", "doi", "bibstem", "doctype", "refereed",
                    "citation_count", "title", "strands", "n_strings",
                    "screen_decision", "screen_reason"])
        for bib, rec in ordered:
            d = rec["doc"]
            w.writerow([
                bib, d.get("year", ""), first(d, "doi"), first(d, "bibstem"),
                d.get("doctype", ""), refereed(d),
                d.get("citation_count", ""), first(d, "title"),
                "|".join(sorted({s for s, _ in rec["hits"]})),
                len(rec["hits"]), "", "",
            ])

    print(f"\nWritten:")
    print(f"  {os.path.relpath(RAW_OUT, os.path.join(HERE, '..'))}  "
          f"({n_unique} records, with abstracts, not committed)")
    print(f"  {os.path.relpath(LOG_OUT, os.path.join(HERE, '..'))}  "
          f"({len(log)} executed strings)")
    print(f"  {os.path.relpath(SCREEN_OUT, os.path.join(HERE, '..'))}  "
          f"({n_unique} rows, decisions empty)")
    print("\nNothing screened. Every screen_decision is blank.")


if __name__ == "__main__":
    main()
