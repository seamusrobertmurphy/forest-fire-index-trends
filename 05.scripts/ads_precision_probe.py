#!/usr/bin/env python3
"""
Precision probe for the calibrated ADS strand strings.

Written 2026-08-14. A yield count says how much work a string makes. It says
nothing about whether the work is worth doing. This pulls the top records for
the largest strings so their precision can be judged before PRESS sign-off.

This is search-strategy validation, not screening. No inclusion or exclusion
decision is recorded here, and nothing written by this script enters the
charting table or the flow-diagram counts. Its output is titles for inspection.

Ranking is by citation count rather than relevance, because a relevance sort on
a 36.8-million-record astronomy corpus is dominated by term frequency and tells
you little, whereas the most-cited records in a genuine methods literature are
the ones a scoping review must not miss.

Credential is read from ~/.ads/dev_key and never printed.

Usage:  python3 05.scripts/ads_precision_probe.py
"""

import csv
import json
import os
import sys
import time
import urllib.parse
import urllib.request

API = "https://api.adsabs.harvard.edu/v1/search/query"
KEY_PATH = os.path.expanduser("~/.ads/dev_key")
OUT = os.path.join(os.path.dirname(__file__), "..", "02.inputs", "derived",
                   "ads-precision-probe.csv")
TOP_N = 12

# Import the block definitions from the calibration script so the two cannot
# drift apart. If that import fails the probe is meaningless, so it is fatal.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ads_search_calibration import (          # noqa: E402
    AC, DOMAIN, EST, ENSO, FWX, REANAL, RECLEN, CP, read_key,
)

# The strings large enough that their precision governs whether they are worth
# running, plus two candidate replacements for the S5 string under question.
PROBES = [
    ("S5", "current, record length AND estimator AND domain",
     f"{RECLEN} AND {EST} AND {DOMAIN} AND year:1990-2026"),
    ("S5", "candidate, detection-length phrasing only",
     '(abs:"number of years" OR abs:"years required" OR abs:detectability '
     'OR abs:"minimum record length") AND '
     '(abs:autocorrelation OR abs:"serial correlation") AND year:1990-2026'),
    ("S5", "candidate, citation-led from Weatherhead",
     'citations(bibcode:1998JGR...10317149W) AND '
     '(abs:autocorrelation OR abs:"record length" OR abs:detectability)'),
    ("S2", "window choice, hiatus, endpoint sensitivity",
     f'{ENSO} AND (abs:hiatus OR abs:slowdown OR abs:"endpoint sensitivity") '
     f'AND year:1990-2026'),
    ("S4", "reanalysis AND fire weather",
     f"{REANAL} AND {FWX} AND year:1990-2026"),
    ("S1", "estimators AND change point or structural break",
     f"{EST} AND {CP}"),
    ("S1", "estimators AND autocorrelation", f"{EST} AND {AC}"),
]


def query(key, q, rows, sort):
    params = {"q": q, "rows": rows, "sort": sort,
              "fl": "bibcode,title,year,citation_count,bibstem"}
    url = f"{API}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {key}"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)["response"]
    except Exception as exc:                       # noqa: BLE001
        print(f"  ERROR: {type(exc).__name__}", file=sys.stderr)
        return None


def main():
    key = read_key()
    rows = []
    for strand, label, q in PROBES:
        resp = query(key, q, TOP_N, "citation_count desc")
        if resp is None:
            continue
        n = resp["numFound"]
        print(f"\n{strand}  {label}   [{n} records]")
        for d in resp["docs"]:
            title = (d.get("title") or [""])[0]
            stem = (d.get("bibstem") or [""])[0]
            print(f"   {d.get('year')}  {d.get('citation_count'):>5}  "
                  f"{stem:<8} {title[:78]}")
            rows.append([strand, label, n, d.get("year"),
                         d.get("citation_count"), stem, title])
        time.sleep(0.05)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["strand", "string", "n_found", "year", "citations",
                    "bibstem", "title"])
        w.writerows(rows)
    print(f"\nWritten to {os.path.relpath(OUT)}")
    print("Titles for inspection only. Nothing screened, nothing included.")


if __name__ == "__main__":
    main()
