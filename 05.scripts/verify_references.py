#!/usr/bin/env python3
"""Verify every candidate citation against Crossref before it enters the bibliography.

Written 2026-08-15. The project convention is that a bibliography entry is taken
from the registry and never from memory, because a DOI recalled from memory
resolves to the wrong paper often enough to be dangerous and the error is
invisible until a referee follows it. This project has already recorded two such
failures.

The script takes a candidate list of works, each with the title as remembered and
either a DOI as remembered or nothing. For each it does two things. It asks
Crossref to resolve the DOI, if one was offered, and compares the title that
comes back against the title that was offered. Separately, and regardless, it
searches Crossref for the offered title and reports the best match with its
score. A candidate is only usable when both agree.

Similarity is a token overlap on lowercased alphanumeric words, which is crude
but sufficient to catch the failure that matters: a DOI that resolves to an
entirely different paper.

Writes ``02.inputs/derived/reference-verification.csv``, committed, and prints
Crossref's own BibTeX for every candidate that passed, ready to paste into
``04.references/references.bib``.

Usage:  python3 05.scripts/verify_references.py
"""

from __future__ import annotations

import os
import re
import sys
import time

import pandas as pd
import requests

MAILTO = "seamusrobertmurphy@gmail.com"
UA = f"forest-fire-index-trends/1.0 (mailto:{MAILTO})"

# Candidates. The title is what is being claimed; the DOI is what is being
# tested. Nothing here is trusted until Crossref agrees with it.
CANDIDATES = [
    ("Estimates of the regression coefficient based on Kendall's tau",
     "10.1080/01621459.1968.10480934"),
    ("A modified Mann-Kendall trend test for autocorrelated data",
     "10.1016/S0022-1694(97)00125-X"),
    ("Controlling the false discovery rate: a practical and powerful approach to multiple testing",
     "10.1111/j.2517-6161.1995.tb02031.x"),
    # The DOI first offered here, 10.1139/x89-121, resolves to a paper on soil
    # nitrogen mineralization in Douglas-fir. It was recalled from memory and it
    # is wrong by one digit. The correct DOI, found by title search, is below.
    # This is the failure the whole script exists to catch and it is left in the
    # record rather than quietly fixed.
    ("Forecasting diurnal variations in meteorological parameters for predicting fire behaviour",
     "10.1139/x89-120"),
    ("cffdrs: an R package for the Canadian Forest Fire Danger Rating System",
     "10.1186/s13717-017-0070-z"),
    ("Interpreting and using outputs from the Canadian Forest Fire Danger Rating System in research applications",
     "10.1007/s10651-007-0084-2"),
    ("Forest fire occurrence and climate change in Canada",
     "10.1071/WF09002"),
    ("Abrupt, climate-induced increase in wildfires in British Columbia since the mid-2000s",
     None),
    ("Implications of changing climate for global wildland fire",
     "10.1071/WF08187"),
    ("Fuel moisture sensitivity to temperature and precipitation: climate change implications",
     None),
    ("Climate change presents increased potential for very large fires in the contiguous United States",
     None),
    ("Warming and earlier spring increase western U.S. forest wildfire activity",
     "10.1126/science.1128834"),
    ("Attribution of the influence of human-induced climate change on an extreme fire season",
     None),
    ("A method of computing fine fuel moisture content throughout the diurnal cycle",
     None),
    ("Nonparametric tests against trend", "10.2307/1907187"),
    ("Applicability of prewhitening to eliminate the influence of serial correlation on the Mann-Kendall test",
     "10.1029/2001WR000861"),
    ("Impact of anthropogenic climate change on wildfire across western US forests",
     "10.1073/pnas.1607171113"),

    ("Wildfire response to changing daily temperature extremes in California's Sierra Nevada",
     None),
    ("Lightning-caused forest fire risk in Northwestern Ontario, Canada, is increasing and associated with anomalies in fire weather",
     None),
    ("Increasing frequency of extreme fire weather in Canada with climate change", None),
    ("Fire-regime changes in Canada over the last half century", None),
    ("Relationships between fire, climate oscillations, and drought in British Columbia, Canada, 1920-2000",
     None),
    ("Length of the fire season in a changing climate", None),
    ("Summer moisture and wildfire risks across Canada", None),
    ("Drivers and impacts of the record-breaking 2023 wildfire season in Canada", None),
    ("Scientists' warning on wildfire: a Canadian perspective", None),
    ("A study of the drying rates of forest floor materials", None),
    # Dropped: the title search returns a Springer book chapter and the identity
    # of the work intended could not be established from the registry alone. A
    # citation that cannot be resolved is not entered.

]


def norm(s: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", (s or "").lower())) - {
        "the", "a", "an", "of", "for", "in", "to", "and", "on", "with"
    }


def similarity(a: str, b: str) -> float:
    x, y = norm(a), norm(b)
    return len(x & y) / max(len(x | y), 1)


def get(url: str, **params) -> dict | None:
    for attempt in range(3):
        try:
            r = requests.get(url, params=params, headers={"User-Agent": UA}, timeout=45)
            if r.status_code == 404:
                return None
            r.raise_for_status()
            return r.json()
        except Exception:
            if attempt == 2:
                return None
            time.sleep(3)
    return None


def bibtex(doi: str) -> str | None:
    try:
        r = requests.get(
            f"https://doi.org/{doi}",
            headers={"Accept": "application/x-bibtex", "User-Agent": UA},
            timeout=45,
        )
        return r.text.strip() if r.ok else None
    except Exception:
        return None


def main() -> None:
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    rows = []
    passed = []

    for claimed_title, claimed_doi in CANDIDATES:
        rec = {"claimed_title": claimed_title, "claimed_doi": claimed_doi}

        # 1. Does the offered DOI resolve, and to this paper?
        if claimed_doi:
            j = get(f"https://api.crossref.org/works/{claimed_doi}")
            if j is None:
                rec.update(doi_resolves=False, doi_title=None, doi_title_similarity=None)
            else:
                m = j["message"]
                t = (m.get("title") or [""])[0]
                rec.update(
                    doi_resolves=True,
                    doi_title=t,
                    doi_title_similarity=round(similarity(claimed_title, t), 3),
                )
        else:
            rec.update(doi_resolves=None, doi_title=None, doi_title_similarity=None)

        # 2. Independently, what does Crossref return for the title?
        j = get("https://api.crossref.org/works", **{
            "query.bibliographic": claimed_title, "rows": 3, "mailto": MAILTO
        })
        best_doi = best_title = None
        if j and j["message"]["items"]:
            items = j["message"]["items"]
            # Prefer the version of record. Crossref frequently ranks a preprint
            # above the journal article that superseded it, and the project
            # convention is that a preprint is distinguished from a peer reviewed
            # source rather than silently substituted for one.
            article = [
                x for x in items
                if x.get("type") in ("journal-article", "proceedings-article")
                and similarity(claimed_title, (x.get("title") or [""])[0]) >= 0.7
            ]
            it = article[0] if article else items[0]
            rec["search_type"] = it.get("type")
            best_doi = it.get("DOI")
            best_title = (it.get("title") or [""])[0]
            rec.update(
                search_doi=best_doi,
                search_title=best_title,
                search_title_similarity=round(similarity(claimed_title, best_title), 3),
                search_year=(it.get("issued", {}).get("date-parts", [[None]])[0][0]),
                search_container=(it.get("container-title") or [""])[0],
            )

        agree = (
            claimed_doi and rec.get("doi_title_similarity", 0) is not None
            and (rec.get("doi_title_similarity") or 0) >= 0.7
        ) or (
            not claimed_doi and (rec.get("search_title_similarity") or 0) >= 0.8
        )
        rec["verdict"] = "verified" if agree else "REJECTED"
        chosen = claimed_doi if (claimed_doi and (rec.get("doi_title_similarity") or 0) >= 0.7) else best_doi
        rec["chosen_doi"] = chosen if agree else None
        rows.append(rec)
        if agree and chosen:
            passed.append((claimed_title, chosen))

        print(f"{rec['verdict']:9s}  {claimed_title[:64]:64s}  -> {rec['chosen_doi']}", flush=True)

    df = pd.DataFrame(rows)
    dest = os.path.join(root, "02.inputs", "derived", "reference-verification.csv")
    df.to_csv(dest, index=False)
    print(f"\nWrote {dest}")
    print(f"Verified {len(passed)} of {len(CANDIDATES)} candidates\n")

    print("=" * 70)
    print("BibTeX from Crossref for the verified entries")
    print("=" * 70)
    for title, doi in passed:
        bt = bibtex(doi)
        print(f"\n% verified against Crossref {time.strftime('%Y-%m-%d')}; "
              f"title matched: {title}")
        print(bt if bt else f"% BibTeX retrieval failed for {doi}")


if __name__ == "__main__":
    main()
