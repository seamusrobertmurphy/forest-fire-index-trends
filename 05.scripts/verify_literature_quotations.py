#!/usr/bin/env python3
"""Check every direct quotation the manuscript attributes to a source other than
the 2025 FWI System report against that source's own text.

Written 2026-09-12, the sibling of verify_quotations.py, which covers the 2025
report alone. The manuscript is read, every passage in double quotation marks is
paired with the citation that follows it in the same sentence, and the passage is
searched for in the source. The source text is the PDF saved as
04.references/literature/<key>.pdf, extracted with pdftotext, or, for a source
read from its abstract only, the abstract returned by CrossRef or OpenAlex for the
DOI in references.bib. Comparison is on letters and digits only, so wording must
match exactly while quotation marks, dashes, ligatures, spacing and line-break
hyphenation are ignored.

Writes 02.inputs/derived/literature-quotation-verification.csv and exits non-zero
if any quotation is not found.

Usage:  python3 05.scripts/verify_literature_quotations.py
"""

from __future__ import annotations

import csv
import json
import os
import re
import subprocess
import sys
import time
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QMD = os.path.join(ROOT, "01.manuscript", "manuscript.qmd")
BIB = os.path.join(ROOT, "04.references", "references.bib")
LIT = os.path.join(ROOT, "04.references", "literature")
OUT = os.path.join(ROOT, "02.inputs", "derived", "literature-quotation-verification.csv")
# Catalogue records are read through the catalogue API.
CATALOGUE = {"bcws2026psta": "bc-wildfire-psta-head-fire-intensity",
             "bcws2026stations": "bc-wildfire-active-weather-stations"}
UA = {"User-Agent": "forest-fire-index-trends/1.0"}


def letters(s: str) -> str:
    s = s.replace("ﬁ", "fi").replace("ﬂ", "fl")
    return re.sub(r"[^a-z0-9]", "", s.lower())


def get_json(url: str) -> dict | None:
    for _ in range(3):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=45) as r:
                return json.load(r)
        except Exception:
            time.sleep(3)
    return None


def abstract_for(doi: str) -> str:
    cr = get_json("https://api.crossref.org/works/" + urllib.parse.quote(doi))
    text = (cr or {}).get("message", {}).get("abstract", "") if cr else ""
    oa = get_json("https://api.openalex.org/works/doi:" + urllib.parse.quote(doi))
    inv = (oa or {}).get("abstract_inverted_index") or {}
    pos = {i: w for w, idx in inv.items() for i in idx}
    return text + " " + " ".join(pos[i] for i in sorted(pos))


def main() -> None:
    qmd = open(QMD, encoding="utf-8").read()
    prose = re.sub(r"```\{r\}.*?\n```", "", qmd, flags=re.S)
    prose = re.sub(r"^---\n.*?\n---\n", "", prose, count=1, flags=re.S)
    # Inline R expressions are code, not quotation.
    prose = re.sub(r"`r [^`]*`", "N", prose)
    # Quotations from the 2025 report are recorded here against the report's own
    # text as well, so that quotations added after verify_quotations.py was written
    # are not left unchecked.
    glc = os.path.join(ROOT, "04.references", "standards", "CFS-FireDangerGroup-2025-GLC-X-42-FWI2025.pdf")
    glc_text = letters(subprocess.run(["pdftotext", glc, "-"], capture_output=True, text=True).stdout) if os.path.exists(glc) else ""
    bib = open(BIB, encoding="utf-8").read()
    dois = {k: d for k, d in re.findall(r"@\w+\{([^,]+),[^@]*?doi\s*=\s*[{\"]([^}\"]+)", bib, flags=re.S | re.I)}

    # A quotation is paired with the first citation key after it in its sentence.
    pairs = []
    for sent in re.split(r"(?<=[.?!])\s+(?=[A-Z@])", prose):
        for m in re.finditer(r'"([^"]{12,})"', sent):
            # A quotation of four words or fewer is a name, not a passage.
            if len(m.group(1).split()) < 5 and not re.search(r"@\w+, p\.", sent[m.end():m.end() + 40]):
                continue
            if glc_text and letters(m.group(1)) in glc_text:
                pairs.append(("cffdg2025fwi2025", m.group(1)))
                continue
            after = sent[m.end():]
            k = re.search(r"@([a-z][a-z0-9]+)", after) or re.search(r"@([a-z][a-z0-9]+)", sent[:m.start()][::-1][::-1])
            if not k:
                continue
            key = k.group(1)
            if key.startswith(("tbl", "fig", "sec")):
                continue
            pairs.append((key, m.group(1)))

    cache: dict[str, str] = {}
    rows, failed = [], 0
    for key, quote in pairs:
        if key not in cache:
            pdf = os.path.join(LIT, key + ".pdf")
            if key == "cffdg2025fwi2025":
                cache[key] = subprocess.run(["pdftotext", glc, "-"], capture_output=True, text=True).stdout
                src = "2025 report pdf"
            elif key in CATALOGUE:
                j = get_json("https://catalogue.data.gov.bc.ca/api/3/action/package_show?id=" + CATALOGUE[key])
                cache[key] = ((j or {}).get("result") or {}).get("notes", "")
                src = "catalogue record"
            elif os.path.exists(pdf):
                cache[key] = subprocess.run(["pdftotext", pdf, "-"], capture_output=True, text=True).stdout
                src = "pdf"
            elif key in dois:
                cache[key] = abstract_for(dois[key])
                src = "abstract"
            else:
                cache[key] = ""
                src = "no source text"
            cache[key + "::src"] = src
        found = letters(quote) in letters(cache[key])
        failed += not found
        rows.append({"key": key, "quotation": quote, "source_text": cache[key + "::src"], "found_verbatim": found})
        print(f"{'ok  ' if found else 'FAIL'}  {key:32s} {quote[:70]}")

    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["key", "quotation", "source_text", "found_verbatim"])
        w.writeheader()
        w.writerows(rows)
    print(f"\n{len(rows)} quotations checked, {failed} not found. Wrote {OUT}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
