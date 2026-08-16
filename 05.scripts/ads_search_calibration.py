#!/usr/bin/env python3
"""
ADS search calibration for the prior-work scoping review.

Written 2026-08-14. Two jobs, both required by PRESS before any search round runs.

1. Stopword sweep. NASA ADS silently drops some tokens from queries, including
   from inside quotation marks. The word "trend" returns zero in every field, so a
   string built on it returns a large plausible set driven by its other terms.
   Every content word intended for use is tested on its own and must return a
   non-zero count, or it cannot appear in a string.

2. Yield calibration. Each rewritten strand string is executed with rows=0 so no
   records are retrieved and none are screened. The counts set the screening
   burden the single reviewer is signing up to.

Neither job is a search round. Nothing here screens or includes a record.

Credential is read from ~/.ads/dev_key and is never printed. Results are written
to 02.inputs/derived/ads-search-calibration.csv so the protocol can quote them.

Usage:  python3 05.scripts/ads_search_calibration.py
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
                   "ads-search-calibration.csv")

# Tokens are tested singly against abs:. A zero is a veto: the word cannot be
# used, in a phrase or otherwise. Drawn from every block of all five strands.
TOKENS = [
    # S1, estimation under variability
    "trend", "trends", "detection", "estimation", "monotonic", "linear",
    "Mann-Kendall", "Theil-Sen", "slope", "quantile", "regression",
    "generalized", "squares", "autocorrelation", "serial", "correlation",
    "prewhitening", "pre-whitening", "prewhitened", "effective", "sample",
    "size", "bootstrap", "block", "memory", "persistence", "Hurst",
    "breakpoint", "segmentation", "structural", "significance", "discovery",
    "multiple", "testing", "nonparametric", "nonstationarity",
    # S2, ENSO handling
    "ENSO", "Nino", "Oscillation", "teleconnection", "removal", "adjustment",
    "dynamical", "compositing", "stratification", "hiatus", "slowdown",
    "endpoint", "wildfire", "burned", "danger", "season", "Columbia",
    "Pacific", "Northwest", "interior",
    # S3, detection theory
    "attribution", "fingerprinting", "emergence", "signal", "noise",
    "climate", "variability", "ensemble", "storyline", "probabilistic",
    # S4, satellite positioning
    "MODIS", "VIIRS", "Landsat", "Sentinel", "MCD64", "FireCCI",
    "intercalibration", "consistency", "homogenisation", "homogenization",
    "artefact", "artifact", "reanalysis", "ERA5", "evaluation", "validation",
    "bias", "terrain", "mountain", "satellite", "sensor",
    # S5, record-length limits
    "record", "length", "detectability", "power", "variance", "minimum",
    "fire", "weather", "index",
]

# Rewritten strand strings. Option A, estimator-led and mechanism-led: the
# concept blocks pivot on named methods and named phenomena, never on "trend".
# Approved by Seamus 2026-08-14 in principle; the strings themselves are what
# the PRESS sign-off covers.
EST = ('(abs:"Mann-Kendall" OR abs:"Theil-Sen" OR abs:"Sen slope" '
       'OR abs:"Kendall tau" OR abs:"quantile regression")')
AC = ('(abs:autocorrelation OR abs:"serial correlation" OR abs:prewhitening '
      'OR abs:"pre-whitening" OR abs:"effective sample size" '
      'OR abs:"block bootstrap" OR abs:"long memory" OR abs:Hurst)')
CP = ('(abs:"change point" OR abs:breakpoint OR abs:"structural break" '
      'OR abs:segmentation)')
FS = ('(abs:"field significance" OR abs:"false discovery rate" '
      'OR abs:"multiple testing" OR abs:"multiple comparisons")')
ENSO = ('(abs:ENSO OR abs:"El Nino" OR abs:"Southern Oscillation" '
        'OR abs:"Pacific Decadal Oscillation" '
        'OR abs:"Interdecadal Pacific Oscillation")')
FIRE = ('(abs:wildfire OR abs:"area burned" OR abs:"burned area" '
        'OR abs:"fire danger" OR abs:"fire weather" OR abs:"fire season")')
REGION = ('(abs:"British Columbia" OR abs:"western North America" '
          'OR abs:"Pacific Northwest" OR abs:Canada)')
# ADS is an astronomy-first corpus of 36.8 million records, so generic physics
# and statistics vocabulary is enormous in it. The first calibration pass on
# 2026-08-14 returned 230,908 for the S3 block, 295,094 for S5 and 24,226 for
# S4, because "signal to noise", "variance", "noise" and "consistency" are
# everyday astronomy words. Every strand block below therefore carries a domain
# anchor. The over-broad first-pass forms are recorded in the protocol as the
# reason the anchors exist, not discarded silently.
DOMAIN = ('(abs:climate OR abs:climatic OR abs:atmospheric OR abs:warming '
          'OR abs:meteorological OR abs:hydrological)')
DA = ('(abs:"detection and attribution" OR abs:"optimal fingerprinting" '
      'OR abs:"time of emergence")')
SENSOR = ('(abs:MODIS OR abs:VIIRS OR abs:Landsat OR abs:"Sentinel-2" '
          'OR abs:"active fire" OR abs:MCD64 OR abs:FireCCI)')
CONSIST = ('(abs:intercalibration OR abs:consistency OR abs:homogenisation '
           'OR abs:homogenization OR abs:"climate data record" '
           'OR abs:artefact OR abs:artifact)')
REANAL = '(abs:ERA5 OR abs:"ERA5-Land" OR abs:reanalysis)'
FWX = '(abs:"fire weather" OR abs:"fire danger" OR abs:"fire weather index")'
RECLEN = ('(abs:"record length" OR abs:"number of years" OR abs:detectability '
          'OR abs:"statistical power" OR abs:"minimum length")')

# Fourth field is the screening pass, fixed at the sign-off of 2026-08-14.
# Pass 1 is the high-precision set and executes on approval. Pass 2 executes per
# strand only where pass 1 has not satisfied the saturation stopping rule. A
# strand closed at pass 1 is reported as closed by saturation; a strand whose
# pass 2 is curtailed is reported as under-searched and named.
STRINGS = [
    ("S1", "core, estimators and autocorrelation", f"{EST} AND {AC}", 2),
    ("S1", "core, refereed only", f"{EST} AND {AC} AND property:refereed", 0),
    ("S1", "change point and structural break", f"{EST} AND {CP}", 2),
    ("S1", "field significance and multiplicity", f"{EST} AND {FS}", 1),
    ("S2", "ENSO with a named adjustment method",
     f'{ENSO} AND (abs:"dynamical adjustment" OR abs:"phase compositing" '
     f'OR abs:"phase stratification" OR abs:"regression removal" '
     f'OR abs:"ENSO removal" OR abs:"ENSO adjustment")', 1),
    # Retained on Seamus's decision of 2026-08-14 rather than tightened. Two
    # tightening candidates were tested and both were worse, 2,648 and 30,101
    # against 1,791. Its precision probe was the weakest of the set, so it is
    # deferred to pass 2 instead of being dropped.
    ("S2", "window choice and endpoint sensitivity",
     f'{ENSO} AND (abs:hiatus OR abs:slowdown OR abs:"endpoint sensitivity")',
     2),
    ("S2", "ENSO and fire teleconnection", f"{ENSO} AND {FIRE}", 1),
    ("S2", "ENSO, fire, western North America",
     f"{ENSO} AND {FIRE} AND {REGION}", 1),
    ("S3", "detection and attribution, climate-anchored",
     f"{DA} AND {DOMAIN} AND property:refereed", 2),
    ("S3", "with internal variability or large ensemble",
     f'{DA} AND (abs:"internal variability" OR abs:"large ensemble")', 1),
    ("S3", "storyline debate, climate-anchored",
     f'(abs:storyline OR abs:"conditional attribution" '
     f'OR abs:"probabilistic event attribution") AND {DOMAIN}', 2),
    ("S4", "sensor record consistency, fire-anchored",
     f"{SENSOR} AND {CONSIST} AND {FIRE}", 2),
    ("S4", "sensor record length framing, fire-anchored",
     f'{SENSOR} AND (abs:"record length" OR abs:"satellite era" '
     f'OR abs:"climate data record") AND {FIRE}', 1),
    ("S4", "reanalysis as fire weather input", f"{REANAL} AND {FWX}", 2),
    ("S4", "reanalysis fire weather in complex terrain",
     f'{REANAL} AND {FWX} AND (abs:"complex terrain" OR abs:mountain '
     f'OR abs:validation OR abs:evaluation)', 1),
    ("S5", "record length and autocorrelation, climate-anchored",
     f'{RECLEN} AND (abs:autocorrelation OR abs:"serial correlation") '
     f'AND {DOMAIN}', 2),
    # Replaces the estimator-block form, which returned 2,499. That string was
    # topically precise at its most-cited head but eligibility-poor in its tail:
    # only 253 of its 2,499 overlapped the S1 core, and the 2,246 unique records
    # were dominated by applications of a method, which the eligibility criteria
    # exclude. The citation-led form below returns records that compute how long
    # a record must be, which is what S5 exists to deliver. Decided 2026-08-14.
    ("S5", "detectability, citation-led from Weatherhead",
     'citations(bibcode:1998JGR...10317149W) AND '
     '(abs:autocorrelation OR abs:"record length" OR abs:detectability)', 1),
    ("S5", "time of emergence applied to fire",
     f'abs:"time of emergence" AND {FWX}', 1),
]

# Option B, citation-led. Seeds are Crossref-verified anchors; ADS bibcodes were
# resolved by DOI on 2026-08-14. Forward chaining is intersected with a domain
# block so the yield is screenable.
SEEDS = [
    ("S1", "Yue et al. 2002, trend-free prewhitening", "2002HyPr...16.1807Y"),
    ("S1", "Hamed and Rao 1998, modified Mann-Kendall", "1998JHyd..204..182H"),
    ("S5", "Weatherhead et al. 1998, detection factors", "1998JGR...10317149W"),
]


def read_key():
    try:
        with open(KEY_PATH) as fh:
            return fh.read().strip()
    except OSError:
        sys.exit(f"No ADS token at {KEY_PATH}. See "
                 "05.tasks/TASK-REQUEST-2026-08-14-ads-api-access.md")


def query(key, q, rows=0):
    """Return numFound for q, or None on error. Never logs the token."""
    url = f"{API}?{urllib.parse.urlencode({'q': q, 'rows': rows})}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {key}"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)["response"]["numFound"]
    except Exception as exc:                      # noqa: BLE001
        print(f"  ERROR on {q[:60]}: {type(exc).__name__}", file=sys.stderr)
        return None


# Date limits are the protocol's, not new: no lower bound for S1 and S3, since
# the foundational estimator and detection papers predate any sensible cutoff;
# 1990 onward for S2, S4 and S5.
YEARS = {"S1": None, "S3": None, "S2": "year:1990-2026",
         "S4": "year:1990-2026", "S5": "year:1990-2026"}


def main():
    key = read_key()
    rows = []

    print("Stopword sweep. A zero vetoes the token.")
    dead = []
    for tok in TOKENS:
        n = query(key, f'abs:"{tok}"')
        rows.append(("stopword", "", tok, f'abs:"{tok}"', n))
        if n == 0:
            dead.append(tok)
        time.sleep(0.05)
    print(f"  {len(TOKENS)} tokens tested, {len(dead)} returned zero: "
          f"{', '.join(dead) if dead else 'none'}")

    print("\nStrand string yields. Date limits and pass staging per the "
          "protocol.")
    by_pass = {1: 0, 2: 0}
    for strand, label, q, pas in STRINGS:
        yr = YEARS.get(strand)
        # A citation-led string carries its own scope; a year filter on it would
        # silently drop the older records the seed exists to reach.
        q_dated = (f"{q} AND {yr}"
                   if yr and not q.startswith("citations(") else q)
        n = query(key, q_dated)
        rows.append((f"string-pass{pas}", strand, label, q_dated, n))
        if n is not None and pas in by_pass:
            by_pass[pas] += n
        flag = {0: "diag", 1: "PASS 1", 2: "pass 2"}[pas]
        print(f"  {strand}  {flag:<6} {n!s:>7}  {label}")
        time.sleep(0.05)
    print(f"\n  Pass 1, executes on approval:      {by_pass[1]:>7}")
    print(f"  Pass 2, released per strand:       {by_pass[2]:>7}")
    print(f"  Total before deduplication:        {sum(by_pass.values()):>7}")

    print("\nOption B, citation-led yields.")
    fire_block = FIRE
    for strand, label, bib in SEEDS:
        n_all = query(key, f"citations(bibcode:{bib})")
        n_fire = query(key, f"citations(bibcode:{bib}) AND {fire_block}")
        rows.append(("citations", strand, label, f"citations({bib})", n_all))
        rows.append(("citations-fire", strand, label,
                     f"citations({bib}) AND fire block", n_fire))
        print(f"  {strand}  {n_all!s:>7} citing, {n_fire!s:>5} of them fire  "
              f"{label}")
        time.sleep(0.05)

    union = " OR ".join(f"citations(bibcode:{b})" for _, _, b in SEEDS)
    n_union = query(key, union)
    n_union_fire = query(key, f"({union}) AND {fire_block}")
    rows.append(("citations", "S1+S5", "union of seeds", "union", n_union))
    rows.append(("citations-fire", "S1+S5", "union of seeds, fire only",
                 "union AND fire block", n_union_fire))
    print(f"  union   {n_union!s:>7} citing, {n_union_fire!s:>5} of them fire")

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["kind", "strand", "label", "query", "n_found"])
        w.writerows(rows)
    print(f"\nWritten to {os.path.relpath(OUT)}")
    print("No records were retrieved or screened. rows=0 throughout.")


if __name__ == "__main__":
    main()
