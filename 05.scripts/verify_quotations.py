#!/usr/bin/env python3
"""Check every quotation from GLC-X-42 in the manuscript against the report itself.

Written 2026-08-15. The project convention is that a source is quoted verbatim and
the quotation is checked against the source, because a paraphrase attributed as a
quotation survives drafts unnoticed. A sibling manuscript in this library spent
several drafts attributing the word "additive" to an abstract in which it never
appears, and the error survived because nobody opened the PDF and searched it.

This script opens the PDF and searches it. Each quotation below is the exact
string the manuscript puts inside quotation marks, paired with the section the
manuscript attributes it to. The comparison runs against the extracted text layer
with line-break hyphenation repaired and whitespace collapsed, because a PDF
breaks words across lines and a naive search would fail on formatting rather than
on substance. Case is significant: the check is exact.

The check earned its keep on first run. The manuscript had
"using hourly weather to better reflect maximum burning conditions" with a lower
case u, taken from a project note rather than from the report. The report's first
bullet under "Key updates include" reads "Using hourly weather to better reflect
maximum burning conditions." The substance was right and the transcription was
not, which is precisely the class of error this check exists to find.

Writes ``02.inputs/derived/quotation-verification.csv``, committed. Exits non-zero
if any quotation fails, so it can gate a build.

Usage:  python3 05.scripts/verify_quotations.py
"""

from __future__ import annotations

import os
import re
import sys

import pandas as pd
import pypdf

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PDF = os.path.join(ROOT, "04.references", "standards",
                   "CFS-FireDangerGroup-2025-GLC-X-42-FWI2025.pdf")

# (quotation as the manuscript prints it, section the manuscript attributes it to)
QUOTATIONS = [
    ("Using hourly weather to better reflect maximum burning conditions",
     "section 1, executive summary, first key update"),
    ("the time lag function used in the FWI2025 for the FFMC has been cut in half",
     "section 4.1.1"),
    ("an FFMC of 91 in FWI1987 should correspond to an FFMC of approximately 91 in FWI2025",
     "section 4.1"),
    ("should reflect meaningful differences in fuel moisture content",
     "section 4.1"),
    ("calculations always use hourly weather",
     "section 3.1.1.1"),
    ("a single daily weather observation from approximately solar noon",
     "section 3.1"),
    ("numerical weather model outputs are not strictly the same as point observations "
     "of weather from a weather station",
     "Appendix C-1"),
    ("At the grid cell scale, outputs from numerical models typically represent what can "
     "be thought of as average conditions across that cell",
     "Appendix C-1"),
    ("start calculation three days after the disappearance of snow cover",
     "Appendix C-2.3"),
]


def normalise(text: str) -> str:
    """Repair line-break hyphenation and collapse whitespace, changing nothing else."""
    text = re.sub(r"-\s*\n\s*", "", text)
    return re.sub(r"\s+", " ", text)


def main() -> None:
    if not os.path.exists(PDF):
        sys.exit(f"The report is not in the tree at {PDF}. "
                 "04.references/README.md records how to retrieve it.")

    reader = pypdf.PdfReader(PDF)
    pages = [p.extract_text() or "" for p in reader.pages]
    whole = normalise("\n".join(pages))

    rows = []
    failures = 0
    for quote, attribution in QUOTATIONS:
        q = normalise(quote)
        found = q in whole
        page = None
        if found:
            for i, p in enumerate(pages, start=1):
                if q in normalise(p):
                    page = i
                    break
        rows.append({
            "quotation": quote,
            "attributed_to": attribution,
            "found_verbatim": found,
            "pdf_page": page,
        })
        if not found:
            failures += 1
        print(f"{'OK  ' if found else 'FAIL'}  p{page if page else '--':>3}  "
              f"{quote[:72]}", flush=True)

    dest = os.path.join(ROOT, "02.inputs", "derived", "quotation-verification.csv")
    pd.DataFrame(rows).to_csv(dest, index=False)
    print(f"\n{len(QUOTATIONS) - failures} of {len(QUOTATIONS)} verified verbatim")
    print(f"Wrote {dest}")

    if failures:
        sys.exit(f"{failures} quotation(s) do not appear in the source as written.")


if __name__ == "__main__":
    main()
