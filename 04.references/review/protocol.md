# Review protocol

Written 2026-10-13, before any query ran, for `forest-fire-index-trends`. Follows
`library-science/protocols/literature-review.md`. Frozen by the commit that adds it.
Nothing above "Deviations" is edited after that commit. Seamus asked on 2026-10-13, in
his words, for "a deep dive and extensive literature review to support and inform our
introduction, methods, and discussion sections". The August 2026 scoping review of trend
methods, recorded in `docs/science-superpowers/prior-work/2026-08-13-review-protocol.md`,
screened 2,010 NASA ADS records and stopped at full text when the pipeline gates were
overridden; the bibliography of 2026-09-12 added 82 sources, 59 of them read from the
abstract only. This review is run against the manuscript's three research questions as
drafted, plus a novelty question, and it keeps what those earlier passes established.

## Objectives

Copied from the Introduction of `01.manuscript/manuscript.qmd` as it stood on 2026-10-13.

1. "The first asked what the 1991 to 2025 trend in seasonal fire danger in the Okanagan
   basin was under each series, estimated identically."
2. "The second asked whether the three series gave different trends, and if so whether the
   difference lay in the version or in the input resolution."
3. "The third asked whether any of the three predicted daily ignition counts better than
   the others, and whether the relationship between danger and ignition was stationary
   across the record."

## Questions

1. What trends in fire danger computed from the Canadian Forest Fire Weather Index System
   have been reported for British Columbia and Canada from station or gridded weather,
   with which estimator, period, autocorrelation treatment and multiple-testing
   correction? Population fire danger series, concept trend estimation, context British
   Columbia and Canada, 1987 onward.
2. What is known about how the weather input of a fire danger index, hourly against
   once-daily, changes the level, the tail and the trend of the index, and how a change
   of version or of input has been handled as a homogeneity problem? Population fire
   danger indices, concept hourly input and version change, context any region.
3. How have daily fire occurrence counts been modelled against fire danger in Canada and
   British Columbia, with what distribution, what seasonal terms, what validation, and has
   the danger to occurrence relationship been tested for change over time? Population
   daily fire occurrence records, concept count models and stationarity, context Canada
   and British Columbia.
4. Novelty. Has FWI2025 been evaluated, compared with FWI1987 on an observed record, or
   used in a trend or occurrence study since its release, and has any study separated the
   version change from the input change? Population studies citing or naming FWI2025,
   concept evaluation and comparison, context any region, 2025 onward.

## Adjudication

1. If a published Theil-Sen or Mann-Kendall trend in a Fire Weather Index metric exists
   for the Okanagan or the southern interior of British Columbia, the Discussion compares
   this study's slopes with it by metric and period, and the Introduction cites it as the
   prior estimate rather than saying the region's trend is unreported.
2. If a study shows that hourly against daily input changes the trend of an index and not
   only its level, the Introduction's expectation table and the Discussion's reading of
   the null slope result are revised to say so. If a study already treats a fire danger
   version change as a homogeneity break with a documented correction, the Methods credit
   it and the Discussion compares the correction with percentile reporting.
3. If a prior Canadian study tested whether the danger to occurrence relationship changed
   over time, the stationarity test here is reported as a replication of it and compared
   with its result. If the negative binomial daily count model with season fixed effects
   has a named Canadian precedent, the Methods credit it.
4. If any study has compared FWI2025 with FWI1987 on an observed record for levels, tails
   or trends, the sentence "no study has separated them" is withdrawn from the Introduction
   and the abstract, and this study is reported as an extension of that work. If none has,
   the claim stands and the Methods state the search that supports it.

## Criteria

1. Document types: peer-reviewed articles, reviews, book chapters and conference papers;
   theses, flagged as such; agency reports and standards where they are the primary source
   of a method, a threshold or a data product, among them the Canadian Forest Service
   information report series and BC Wildfire Service documents.
2. Published 1987 to 2026, opening at 1987 because that is the year the Fire Weather Index
   System specification the study tests was published; older methods papers already in
   the bibliography are retained through citation and are not searched for.
3. Language English.
4. Bears on at least one question, meaning a fire danger or fire weather index from station
   or gridded weather, a trend in such an index, an hourly or once-daily input to one, a
   version or homogeneity change in one, or a daily fire occurrence model driven by one.

Exclusions use the codes in the library protocol. No extra code.

## Sources

1. `library-science`, searched with the `review-store` chunk.
2. OpenAlex, titles and abstracts, with the `review-openalex` chunk. OpenAlex answered an
   unkeyed request with HTTP 200 on 2026-10-13, which it had refused in August 2026.
3. NASA ADS, abstracts, with the `review-ads` chunk, under the personal token held outside
   the repository. ADS treats "trend" as a stopword, so the question 1 string runs there
   without its trend concept and the log says so.
4. Semantic Scholar bulk search, with the `review-semantic-scholar` chunk. It answered
   HTTP 429 to every unkeyed request on 2026-10-13; the chunk logs the refusal and the
   strand is reported as missing unless a key is obtained.
5. Grey literature by hand: Natural Resources Canada publications, the Canadian Wildland
   Fire Information System, BC Wildfire Service. Each record found this way is added to
   `review-records.csv` with the route `grey`, its URL and the date.
6. Citation chasing through OpenAlex from six central records, the 2025 report
   (10.4095/st000101), Rodell et al. 2024 (10.1175/waf-d-23-0226.1), Tsinko et al. 2018
   (10.1016/j.agrformet.2018.07.005), Herrera et al. 2013 (10.1007/s10584-012-0667-2),
   Jain et al. 2017 (10.1071/wf17008) and Magnussen and Taylor 2012 (10.1071/wf11088).
   The papers citing the 2025 report are the main net for question 4.

Search terms are selected in `04.references/review/search-terms.csv`, from candidates the
`review-terms` chunk drew from the manuscript's title and keywords, and committed with this
file. The keywords "hourly weather" and "fire occurrence" were added to the front matter on
2026-10-13 so that the search could carry those concepts. The queries are built from that
selection by the `review-queries` chunk in `01.manuscript/manuscript.qmd`. Calibration
counts read from OpenAlex on 2026-10-13 before freezing: question 1, 113 records; question
2, 109; question 3, 105 with the place concept and 404 without it, so the place concept is
kept; question 4, 1 record for the term alone, which is why the chase from the report is
part of the source list.

## Screening

Every record is screened on title and abstract against the criteria and given a decision
and, for an exclusion, a code. Screening on 2026-10-13 was done by a single reader under
Seamus's direction, and no second reader checked the decisions; Seamus may
overturn any decision by editing `review-records.csv`, and the file records the state at
the time of the render.

## Deviations

2026-10-13. The protocol was written before any query ran, but it was not committed first,
because Seamus had not authorised a commit that day; the file's write time and the search
log's dates stand in for the freeze until the commit is made.

2026-10-13. Semantic Scholar answered HTTP 429 to the question 1 bulk query after three
tries and answered the other three, so that strand is complete for questions 2 to 4 and
missing for question 1, as `review-search-log.csv` records. NASA ADS ran question 1 without
its trend concept because "trend" is a stopword there, which is why that strand returned
593 records for question 1 and most of them were screened out.

2026-10-13. The chased records were folded into `review-records.csv` and screened with the
rest, which the template keeps in a separate file, and the `review-chase` chunk therefore
sits above the `review-records` chunk. Records of an ineligible document type (OpenAlex
types abstract, conference-abstract, dataset, peer-review, paratext, erratum, editorial,
letter and other) were excluded by rule with the code not-research in
`05.scripts/review_screening_pack.py` before any abstract was read, 350 of 1,275.

2026-10-13. Abstracts for records that only Semantic Scholar or the chase returned were
fetched from OpenAlex by DOI for screening and kept under `02.inputs/searches/`, which is
not committed. Three records found by hand were added to `review-records.csv` with the
routes web and grey, Daniels and others 2025 on the 2023 British Columbia fires, the
cffdrs-ng repository README of February 2026, and the Natural Resources Canada next
generation page dated 2025-11-18, the last two saved under `04.references/reports/`.

2026-10-13. Screening was done by four readers, one per batch, each reading every
abstract in its batch, under the single-reader limit the Screening section states.
