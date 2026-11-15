# 04.references, source manifest

Every source in this folder is recorded here: what it is, where it came from, whether it
is peer-reviewed, and whether it has been read. PDFs are not committed to git; this
manifest is how a fresh clone knows what to retrieve. Verify each bibliographic record
against CrossRef before it enters `references.bib`, and flag any hand-entered record in
a comment beside it.

## literature/

The read status and supporting pages of every cited source are kept in
`02.inputs/derived/literature-cited.csv`; the files themselves are not committed.
The four Canadian Forest Service reports below were fetched on 2026-11-04 from the
Natural Resources Canada Open Science and Technology Repository through its
DSpace back end (`ostr-backend-prod.azure.cloud.nrcan-rncan.gc.ca/server/api/core/bitstreams/<uuid>/content`),
because the old `cfs.nrcan.gc.ca/pubwarehouse` links redirect to a page the plain
download tool cannot follow.

Three abstracts quoted in the Discussion are saved as `wastl2013large.txt`,
`rodrigues2020identifying.txt` and `wastl2012climate.txt`, copied on 2026-11-05 from the
NASA ADS records of the second-pass search, because CrossRef and OpenAlex return no
abstract for those papers and the quotation checker reads a saved text when it finds one.
Each file's first line says it is the abstract and not the full text.

| File | Identity (verified against the PDF and the repository record) | Status |
|---|---|---|
| `vanwagner1987fwi.pdf` | Van Wagner, C.E. 1987. Development and structure of the Canadian Forest Fire Weather Index System. Forestry Technical Report 35. Handle 1845/228434. 48 pages, scanned, text layer patchy. | Read 2026-11-04 for the System's structure and the printed coefficient 147.2 (equations 2a and 2b, printed page 4, PDF page 15). On 2026-11-06 pages vi, 2 and 4 (PDF pages 9, 13 and 15) were checked and cited for the first edition of 1970, the 1600 hours peak and the 1984 version. Later that day pages 12 and 14 (PDF pages 23 and 25) were cited for the monthly day length factors, whose Drought Code table followed on page 15. |
| `vanwagner1977hourly.pdf` | Van Wagner, C.E. 1977. A method of computing fine fuel moisture content throughout the diurnal cycle. Information Report PS-X-69. Handle 1845/222928. 17 pages. | Read 2026-11-04, abstract and method. |
| `vanwagner1985fortran.pdf` | Van Wagner, C.E. and Pickett, T.L. 1985. Equations and FORTRAN program for the Canadian Forest Fire Weather Index System. Forestry Technical Report 33. Handle 1845/228362. 25 pages. | Read 2026-11-04; the listing prints 147.2 at statements 110 and 150, not 147.2772. |
| `lawson2008weather.pdf` | Lawson, B.D. and Armitage, O.B. 2008. Weather guide for the Canadian Forest Fire Danger Rating System. Northern Forestry Centre. Handle 1845/219568. 87 pages. | Read 2026-11-04 for the weather inputs (p. 1), the start-up values FFMC 85, DMC 6, DC 15 (p. 14) and the anemometer height (p. 21, Figure 10). On 2026-11-06 page 71 (PDF page 85), in Appendix 3, was checked and cited. It warned that changing how day length entered the Duff Moisture and Drought Codes would invalidate past calibrations. On 2026-11-13 page 14 was also cited for the second start rule, three successive noon days at 12 °C or higher. On 2026-11-15 page 4 (PDF page 18) was cited in the Introduction for the diurnal FFMC of Lawson et al. (1996), look-up tables that gave a code for each hour without hourly weather data. |
| `hanes2021classes.pdf` | Hanes, C.C., Wotton, B.M., McFayden, C. and Jurko, N. 2021. An approach for defining physically based Fire Weather Index System classes for Ontario. Information Report GLC-X-29, Great Lakes Forestry Centre. Handle 1845/245388. 42 pages; the printed page is the PDF page less seven. No DOI in CrossRef on 2026-11-14, so the bibliography entry is hand-entered. | Read in full 2026-11-06 in the third pass (note `review/notes/1845-245388.md`). Page 2 (PDF page 9) cited from 2026-11-14 in the Results, Threshold Positions, for its expectation that the planned changes might shift the frequency of code and index values. Copied that day from the pass's download for the quotation checker. The Discussion cited the abstract page (PDF page 8, unnumbered) the same day for Ontario's classes. |
| `lawson1977bc.pdf` | Lawson, B.D. 1977. Fire Weather Index, the basis for fire danger rating in British Columbia: a slide tape presentation. Report BC-P-17, Pacific Forest Research Centre. Handle 1845/220185. 24 pages; printed pages equal PDF pages. No DOI in CrossRef on 2026-11-14, so the bibliography entry is hand-entered. | Read in full 2026-11-06 in the third pass (note `review/notes/1845-220185.md`). The text layer interleaves the columns, so pages 14 and 15 were read from page images on 2026-11-14 and cited that day in the Discussion, Published Trends, for the regional Class V thresholds. Not quoted, because the text layer cannot pass the quotation check. Copied that day from the pass's download. |
| `weatherhead1998detection.pdf` | Weatherhead, E.C., Reinsel, G.C., Tiao, G.C. and ten others 1998. Factors affecting the detection of trends: statistical considerations and applications to environmental data. Journal of Geophysical Research: Atmospheres 103(D14), 17149 to 17161. DOI 10.1029/98JD00995. 13 pages; the printed page is the PDF page plus 17,148. | Read 2026-11-15. Saved that day from the publisher's free access PDF through Seamus's Chrome, with a copy in `library-science/library/staging/`. Plain pdftotext reads the columns in order; the layout mode interleaves them. Cited in the Methods for the AR(1) noise model (p. 17,150), the autocorrelation factor and the detection probability of 0.90 (p. 17,151). |
| `podur2011spread.pdf` | Podur, J. and Wotton, B.M. 2011. Defining fire spread event days for fire-growth modelling. International Journal of Wildland Fire 20, 497 to 507. DOI 10.1071/WF09001. 11 pages; the printed page is the PDF page plus 496. | Read 2026-11-15. Sourced by Seamus into `library-science/library/staging/` that day, since the journal's new host, ConnectSci, sells it. Cited in the Methods for the threshold of FWI above 19 recommended for Ontario (p. 506); p. 505 gives "19 or above". |
| `hall1991guidelines.pdf` | Hall, P. and Wilson, S.R. 1991. Two guidelines for bootstrap hypothesis testing. Biometrics 47(2), 757 to 762. DOI 10.2307/2532163. JSTOR copy, 7 pages with a cover page; the printed page is the PDF page plus 755. | Read 2026-11-15. Sourced by Seamus into `library-science/library/staging/` that day. Cited in the Methods for the first guideline (p. 758), which the slope difference test follows. |
| `vanwagner1987hindsight.pdf` | Van Wagner, C.E. 1987. Forest fire research, hindsight and foresight. Pages 115 to 120 in the Proceedings of the Symposium on Wildland Fire 2000, General Technical Report PSW-101, Pacific Southwest Forest and Range Experiment Station, Berkeley. Handle 1845/224963. 6 pages, scanned; the printed page is the PDF page plus 114. CrossRef holds a DOI for the volume only, 10.2737/psw-gtr-101, so the bibliography entry takes the volume from CrossRef and the paper from the PDF. | Read in full 2026-11-05 in the third pass (note `review/notes/1845-224963.md`). The OCR text layer prints commas as full stops, so the quoted words were checked against the page image on 2026-11-15. Page 117 (PDF page 3) cited that day in the Introduction for the weather input as "the weakest link in the present chain" and the four elements read once daily at noon. Copied that day from the pass's download, with a copy already in `library-science/library/staging/`. |
| `heinsch2009percentiles.pdf` | Heinsch, F.A., Andrews, P.L. and Kurth, L.L. 2009. Implications of using percentiles to define fire danger levels. Poster P1.5, Eighth Symposium on Fire and Forest Meteorology, American Meteorological Society, Kalispell, Montana, 13 October 2009. 12 page handout from https://ams.confex.com/ams/pdfpapers/156081.pdf, which prints no page numbers. No DOI in CrossRef on 2026-11-15, so the bibliography entry is hand-entered. | Read in full 2026-11-15 in the ranked reading of the unread records (note `review/notes/implications-of-using-percentiles-to-define-fire-danger-levels.md`). Handout page 4 cited that day in the Discussion, Published Trends, for the fuel model comparison at Missoula over 1999 to 2008. Its text layer moves superscript ordinals and interleaves figure text, so quotations were confirmed on page images. A copy is in `library-science/library/staging/`. |
| `wang2025spread.pdf` | Wang, X., Swystun, T., Oliver, J., Levesque, K. and Flannigan, M.D. 2025. When is fire weather extreme enough for active fire spread in Canada? Philosophical Transactions of the Royal Society B 380, 20230465. DOI 10.1098/rstb.2023.0465. 10 pages; printed pages equal PDF pages from page 2. | Read in full 2026-11-15 in the ranked reading (note `review/notes/10-1098-rstb-2023-0465.md`). Saved that day from the publisher's open access PDF through Seamus's Chrome, with a copy in `library-science/library/staging/`. Tables 1 and 2 (pp. 5 and 6) were read from page images and cited in the Discussion, Published Trends, for the national and ecozone spread thresholds of the Fire Weather Index over 2001 to 2021. |
| `jain2017seasonlength.pdf` | Jain, P., Wang, X. and Flannigan, M.D. 2017. Trend analysis of fire season length and extreme fire weather in North America between 1979 and 2015. International Journal of Wildland Fire 26, 1009 to 1020. DOI 10.1071/WF17008. 12 pages; the printed page is the PDF page plus 1,008. | Cited from its abstract until 2026-11-15, when Seamus supplied the PDF through `library-science/library/staging/` and it was read in full (note `review/notes/10-1071-wf17008.md`). Pages 1009, 1011 and 1013 cited that day after corrections to the Introduction and the expectations table. The spread day definition, "FWI >19", was read from the page image, since the text layer drops the symbol. |
| `tsinko2018comparisons.pdf` | Tsinko, Y., Bakhshaii, A., Johnson, E.A. and Martin, Y.E. 2018. Comparisons of fire weather indices using Canadian raw and homogenized weather data. Agricultural and Forest Meteorology 262, 110 to 119. DOI 10.1016/j.agrformet.2018.07.005. 10 pages; the printed page is the PDF page plus 109. | Cited without a full read until 2026-11-15, when Seamus supplied the PDF through `library-science/library/staging/` and it was read in full (note `review/notes/10-1016-j-agrformet-2018-07-005.md`). Pages 110 and 117 cited that day after the Introduction's two sentences were corrected. Its text layer joins letters such as "ﬀ", which a letters-only check must expand. |

## reports/

Empty.

## standards/

Guidance documents, index specifications and journal author guides live here, each with a
provenance record giving the URL, the date read and whether it is the current version.

| File | Identity | Provenance | Status |
|---|---|---|---|
| `CFS-FireDangerGroup-2025-GLC-X-42-FWI2025.pdf` | Canadian Forest Service Fire Danger Group. 2025. *The 2025 Update to the FWI System: Structure, Changes and Interpretation.* Information Report GLC-X-42. Natural Resources Canada, Canadian Forest Service, Great Lakes Forestry Centre. ISBN 978-0-660-77629-3. ISSN 2562-0738. Cat. no. Fo123-2/42-2025E-PDF. 58 pp. | Retrieved 2026-08-13 from `https://publications.gc.ca/collections/collection_2026/rncan-nrcan/Fo123-2-42-2025-eng.pdf`. SHA-256 `552a01deb0fb4a7676e916e84e67f2c434f39644a25860928f79b3513d8bdc6c`. Text layer extracted with `pypdf`; no image read required. Current version as published, no successor found on 2026-08-13. | Read, as of 2026-08-15, in every section the study depends on: preface, executive summary, section 3.1 and all of 3.1.1 on weather inputs and the three input pathways, section 3.2, section 4.1 on the standard pine components including 4.1.1 to 4.1.3, Appendix A on the Beck and Trevitt diurnal method and its Table A-1 coefficients, and Appendices C-1 and C-2. **Still not read:** section 3.3 on the optional solar radiation and curing inputs, and sections 4.2 and 4.3 on the grassland and peatland components, all of which are outside this study's scope by design. Government report, no DOI, so the `references.bib` entry will be hand-entered and flagged as such. On 2026-11-06 pages 3, 8 and 29 (PDF pages 9, 14 and 35) were cited for the FWI1987 label, the user's choice of daily hour and the peak burn definition. Later that day pages 18 to 20 and 40 (PDF pages 24 to 26 and 46) were also cited. They gave the purpose of the adjustments, the field comparison in Figures 7 and 8 and the purpose of hourly calculation. Pages 6, 20 and 22 (PDF pages 12, 26 and 28) were then cited. They gave the sunrise and sunset inputs and the reasons for the hourly heavy-fuel codes and the wind function. On 2026-11-13 the Methods cited pages 7, 9, 10 to 13, 20 to 23, 41, 49 and 50 (PDF pages 13, 15, 16 to 19, 26 to 29, 47, 55 and 56) for the report's own reasons beside each design decision, every quotation checked by script. On 2026-11-14 the Results cited pages 29 and 30 (PDF pages 35 and 36) for the daily summaries offered as examples and the burning window's threshold of a smoothed Initial Spread Index of five or more. The Discussion then cited page 21 (PDF page 27) for the two-rain-event condition of the dry side, page 29 for the peak burn hour as a mathematical maximum and page 31 (PDF page 37) for its warning on weather estimates. |

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

## Citation style file

`elsevier-harvard.csl`, "Elsevier (author-date/Harvard, with titles)", fetched 2026-10-19
from https://raw.githubusercontent.com/citation-style-language/styles/master/elsevier-harvard.csl
for the Ecological Modelling submission, whose guide (read the same day) applies a name and
year style at proof and accepts any consistent style at submission. `apa.csl` stays for the
record of earlier renders.
