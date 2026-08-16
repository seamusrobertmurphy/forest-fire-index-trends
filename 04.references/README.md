# 04.references, source manifest

Every source in this folder is recorded here: what it is, where it came from, whether it
is peer-reviewed, and whether it has been read. PDFs are not committed to git; this
manifest is how a fresh clone knows what to retrieve. Verify each bibliographic record
against CrossRef before it enters `references.bib`, and flag any hand-entered record in
a comment beside it.

## literature/

Empty. No seed corpus supplied yet.

| File | Identity (verified against the PDF and CrossRef) | Status |
|---|---|---|
| | | |

## reports/

Empty.

## standards/

Guidance documents, index specifications and journal author guides live here, each with a
provenance record giving the URL, the date read and whether it is the current version.

| File | Identity | Provenance | Status |
|---|---|---|---|
| `CFS-FireDangerGroup-2025-GLC-X-42-FWI2025.pdf` | Canadian Forest Service Fire Danger Group. 2025. *The 2025 Update to the FWI System: Structure, Changes and Interpretation.* Information Report GLC-X-42. Natural Resources Canada, Canadian Forest Service, Great Lakes Forestry Centre. ISBN 978-0-660-77629-3. ISSN 2562-0738. Cat. no. Fo123-2/42-2025E-PDF. 58 pp. | Retrieved 2026-08-13 from `https://publications.gc.ca/collections/collection_2026/rncan-nrcan/Fo123-2-42-2025-eng.pdf`. SHA-256 `552a01deb0fb4a7676e916e84e67f2c434f39644a25860928f79b3513d8bdc6c`. Text layer extracted with `pypdf`; no image read required. Current version as published, no successor found on 2026-08-13. | Read, as of 2026-08-15, in every section the study depends on: preface, executive summary, section 3.1 and all of 3.1.1 on weather inputs and the three input pathways, section 3.2, section 4.1 on the standard pine components including 4.1.1 to 4.1.3, Appendix A on the Beck and Trevitt diurnal method and its Table A-1 coefficients, and Appendices C-1 and C-2. **Still not read:** section 3.3 on the optional solar radiation and curing inputs, and sections 4.2 and 4.3 on the grassland and peatland components, all of which are outside this study's scope by design. Government report, no DOI, so the `references.bib` entry will be hand-entered and flagged as such. |

Quotations taken from this document into the framing at
`docs/science-superpowers/questions/2026-08-13-fwi-version-okanagan.md` were copied from
the extracted text layer and are cited to their section number.

Every quotation that reached the manuscript **has** been re-checked against the PDF, by
`05.scripts/verify_quotations.py`, which searches the text layer for the exact string with
hyphenation across line breaks repaired and case significant, and writes
`02.inputs/derived/quotation-verification.csv` with the page each was found on. All nine
verified on 2026-08-15. One failed on the first run and was corrected: the executive
summary bullet reads "Using hourly weather to better reflect maximum burning conditions",
and the manuscript had carried it with a lower case initial letter, taken from a project
note rather than from the report.

## Software cited

| Item | Identity | Provenance | Status |
|---|---|---|---|
| `05.scripts/vendor/cffdrs-ng/` | Canadian Forest Service Fire Danger Group. NG-CFFDRS reference implementation of FWI2025, Python module. Mozilla Public License 2.0. | Cloned 2026-08-15 from `https://github.com/nrcan-cfs-fire/cffdrs-ng` at commit `ed143d739c9ab4bda896efcb47a84ff1d5c21e39`, dated 2026-08-13, recorded in `COMMIT.txt`. Named at page 8 of GLC-X-42 as the System's open-source code repository. | **Committed**, unlike the PDFs, because it is the code that produced the results and MPL 2.0 permits redistribution with the licence retained. Reproduces the standard output distributed with it exactly over the 2,623 hour Petawawa Research Forest test record. |
| CRAN `cffdrs` | Wang et al. (2017), `10.1186/s13717-017-0070-z`. R implementation of FWI1987. | Installed 2026-08-15 from CRAN into the global user library. | Used only as an independent check on this project's FWI1987 implementation, never to produce a reported series. |

## Assets

- `references.bib`, committed, CrossRef-verified entries only.
- `apa.csl`, citation style for the HTML build.
- `style-formal.docx`, reference document for the Word submission build.
