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
selection by the `review-queries` chunk in `04.references/review/review.qmd`. Calibration
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

2026-10-14. A second pass was opened on Seamus's instruction of 2026-10-14 for "a extra
large and extensive literature review", under escalation case 1 of the library protocol,
because the manuscript's contribution rests on the sentence that no study has separated the
FWI2025 version change from the hourly input change. The second pass runs as the full
scoping review of the `scoping-review` skill, following Arksey and O'Malley (2005), Levac
et al. (2010) and Peters et al. (2020), and reports to PRISMA-ScR (Tricco et al. 2018). The
four questions, the adjudication rules and the criteria above stand unchanged. Eight
keywords were added to the front matter so that the strands below could be searched, and
the terms selected from them were committed with this entry before any second pass query
ran. The first pass protocol was itself committed on 2026-10-14, after its searches,
which the deviation of 2026-10-13 records.

2026-10-14. The second pass ran on 2026-10-14 and 2026-10-15 after the protocol section
and the terms were committed as b7df8e8. OpenAlex now refuses cursor paging past the first
page without a key, so the `review-openalex` chunk pages by number, and the two queries that
had stopped at 200 records were rerun in full after their rows were removed from the log and
the hits. Semantic Scholar ran without a key, because Seamus holds none, at one request every
two seconds, and all seven new queries answered after a single retry of one HTTP 429. The
Consensus route gives three records per query without an account and no DOI, so it is logged
with a cap of three and its hits were typed from the session's results with DOIs matched on
Crossref by exact title, 30 of 32. Google Scholar was not used because it has no search
interface for scripts, blocks automated queries behind CAPTCHAs, and returns counts that
change between sessions, so a query there cannot be logged and rerun. The screening pack had
treated the text "NA" as an abstract, so the 37 undecided records of the first pass had never
had their abstracts fetched from OpenAlex; that was fixed, and the 413 records left open
after the document type rule, the 37 among them, were screened by hand on 2026-10-14, 47
included. Grey literature for strands 1 and 9 entered by hand as eight rows with route grey
or crossref, each address read on 2026-10-15; the Canadian Forest Service publication
warehouse links have moved to the NRCan Open Science and Technology Repository, and the Van
Wagner 1977 report is logged as out of window and retained through citation.

2026-10-19. Twenty-one of the files the fetch step had logged as saved from the
publisher's landing page, all from American Meteorological Society journals, were two-page
first-page previews rather than articles, found when their text layers were extracted for
note writing. The fetch step now removes any downloaded PDF of two pages or fewer and tries
the next route, and those twenty-one records were refetched through the remaining routes.
Notes with page-cited verbatim quotations were written for the 43 saved full texts that had
none, and every quotation was checked by script against the page text, letters and digits
only, with running headers and manuscript line numbers removed. Three saved files were not
the article their DOI names, a thesis, a preprint and an accepted manuscript, and their notes
record that in the text route.

2026-10-19, write-back. The 64 texts reached in full were written back to library-science
the same day, the PDFs into its store, one source note per paper with the quotations checked
by its own checker, which passes a quotation only inside one page, so a quotation crossing a
page was split or left out and the note says so. The 22 American Meteorological Society
records answered HTTP 403 to every scripted route and wait on the browser.

2026-10-19, browser route. With Seamus's approval the 25 American Meteorological Society
records were read in Chrome and the text of the article page saved for 20 of them, cited by
section because a page carries no page numbers; the other five, scanned articles from before
2005 and two reanalysis descriptions, show only the abstract on the page and stay abstract
only until their PDF is approved for download one file at a time.

2026-10-19, synthesis and checklist. `synthesis.md` was rewritten question by question in
the four parts, `review-attributes.csv` refilled with fifteen rows, and the eleven checklist
items scripted. Nine pass. Items 8 and 10 fail for the 28 records read from an article web
page rather than a PDF, which the library's checker cannot verify, so they hold no library
source note and no `library.bib` entry. Seamus accepted them as read on 2026-10-19 with that
gap recorded, and the manuscript's own tables are the record of what was read.

## Second pass

The second pass opened on 2026-10-14, the questions are the four above, and no question
was added. Each strand below names the question it serves, and the search strings are
built from the selected terms by the `review-queries` chunk, one sub-query per strand,
labelled q1a to q3a.

Strands.

1. The Canadian Forest Fire Weather Index System and its 2025 update, question 4 and the
   Data section. Searched through the citing works of the 2025 report and of the hourly
   Fine Fuel Moisture Code paper, not by string.
2. Fire danger and fire weather trends in British Columbia, Canada and western North
   America, question 1. The first pass q1 string stands, and the named leads enter by DOI.
3. Hourly against once-daily input, question 2, sub-query q2c.
4. Danger rating systems revised elsewhere, as comparators for a version change on a long
   record, question 2, sub-query q2a. The 2016 revision of the United States National Fire
   Danger Rating System, the Australian Fire Danger Rating System of 2022 and the Fire
   Weather Index in the European Forest Fire Information System are the named cases.
5. Station weather homogeneity and instrument change, question 2 and the Methods,
   sub-query q2b, with the general homogenisation papers entered by DOI.
6. Percentile against absolute thresholds, question 2, sub-query q2d.
7. Daily fire occurrence models and the stationarity of the danger to occurrence link,
   question 3, sub-query q3a.
8. Trend estimation and resampling, question 1 and the Methods, sub-query q1a, with every
   cited methods paper retrieved in full.
9. The Okanagan basin's fire and climate record, question 1 and the Discussion, sub-query
   q1b, with the 2003, 2017, 2021 and 2023 seasons and the independent reviews of 2017 and
   2023 entered by hand as grey records.

Sources, in order, each logged by route in `review-search-log.csv`.

1. `library-science`, through the `review-store` chunk.
2. OpenAlex, titles and abstracts, unkeyed, cap 3,000 per query.
3. NASA ADS, abstracts, under the token held outside the repository; q1a runs there
   without its trend concept and the log says so.
4. Semantic Scholar, bulk search, only if a key is obtained; otherwise logged as missing
   for the second pass.
5. The Consensus search tool of the session, logged as the route `consensus`, one row per
   query, with its results folded into `review-records.csv` by DOI.
6. Crossref, for bibliographic records of the named leads only.
7. Grey literature by hand from Natural Resources Canada, the Canadian Wildland Fire
   Information System and BC Wildfire Service, route `grey`, with URL and date.
8. A second round of citation chasing through OpenAlex, from every record read in full in
   either pass rather than from six seeds, each chase logged by DOI.

Screening. The agent screens title and abstract as single reader, as the Screening section
states, and every one of the 37 undecided records of the first pass is resolved to include
or exclude or has its failed abstract and full text routes logged.

Full text. Every one of the 285 kept records and every record kept in the second pass is
tried in order through the publisher's DOI landing page, Unpaywall, the Internet Archive,
the author's institutional repository and the session's browser, and the route or the
failure is logged in `review-fulltext-log.csv`. A text reached through the browser is
downloaded only with Seamus's approval of that file. Where no route reaches a text the
note says so and the manuscript claims only what the abstract carries.

No reading budget is set, so the novelty question and every absence claim are checked
against the full text of every candidate.

Charting. `review-attributes.csv` holds one row per model variable and one row per
expectation in the Introduction's expectation table, with direction, reasoning and key,
and is the charting table PRISMA-ScR item 11 asks for. No critical appraisal is made, and
the Methods say so.

Reporting. The Methods report both passes together, with counts read from
`review_counts`, the flow diagram drawn by the `fig-review-flow` chunk, and the coverage
gaps named, among them the ADS stopword, any Semantic Scholar refusal, every reached cap
and the publisher blocks of 2026-10-13 that `review-fulltext-log.csv` records.

## Third pass

2026-11-05, third pass opened. Seamus asked on 2026-11-05 for an exhaustive pass on one
subject, the methodology of the Canadian Forest Fire Danger Rating System, its Fire
Weather Index System and the 2025 revision, in every form of publication. His reason was
that the manuscript examines a federal revision closely and its authors are the likely
referees. The request is `05.tasks/TASK-REQUEST-LITREVIEW-CFFDRS-EXHAUSTIVE-2026-11-05.md`.
The four questions, the adjudication rules and the exclusion codes stand. The pass is
subject led rather than question led. A record is kept when it describes the System's
components, equations, calibration, weather inputs, observation time, start-up,
overwintering, danger classes, versions or implementations, whatever question it serves.
Document types widen to the Canadian Forest Service report series in full, provincial
agency documents, theses, proceedings, preprints and any commentary on the revision. The
1987 opening year is lifted for this subject, because the System's own reports run from
1933. Routes run in this order. First, a backward chase from the 31 references of the
2025 report, from Van Wagner 1987, the 1985 listing and Lawson and Armitage 2008, and
from the sources the reference implementation's comments cite. Seamus ruled on 2026-11-05
that every one of the 31 is read in full and that the references found inside them enter
the review as well. Second, a forward chase through OpenAlex and CrossRef from the keys
`cffdg2025fwi2025`, `vanwagner1987fwi`, `vanwagner1977hourly`, `lawson2008weather`,
`beck1989diurnal`, `wang2017cffdrs` and `nrcan2026cffdrsng`. Third, registry search on
OpenAlex, CrossRef, NASA ADS, Semantic Scholar and Consensus under the label q5, with
these terms, "Canadian Forest Fire Danger Rating System", "CFFDRS", "Fire Weather Index
System", "Fine Fuel Moisture Code", "Duff Moisture Code", "Drought Code", "Initial Spread
Index", "Buildup Index", "hourly FFMC", "diurnal", "overwinter", "start-up", "danger
class", "FWI2025", "CFFDRS2025" and "next generation", added to `search-terms.csv` under
q5. Fourth, the grey literature portals, the Natural Resources Canada repository,
Government of Canada Publications, the Canadian Wildland Fire Information System, BC
Wildfire Service and the BC Data Catalogue, the other provincial agencies, the Canadian
Interagency Forest Fire Centre, FPInnovations, the Library and Archives Canada theses
portal and the university repositories. The central store is searched before any
registry. Canadian Forest Service reports are fetched from the DSpace back end of the
Open Science and Technology Repository, the handle resolved through its `pid/find`
endpoint and the file taken from the ORIGINAL bundle. Every record retrieved is merged
into `review-records.csv` by DOI or handle with a decision and a reason, every text read
gets a note under `notes/`, and the gap table is `05.tasks/LITREVIEW-GAPS-2026-11-05.md`.
