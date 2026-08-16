# Derived inputs

Small CSVs written by saved scripts and read by the manuscript. Committed, because
the manuscript cites the numbers in them and no number may be quoted from code that
was not saved.

## ads-pass-one-searchlog.csv

The PRISMA-S search log for pass one, written 2026-08-14 by
`05.scripts/ads_pass_one_retrieve.py`. One row per executed string: `route` (database
searching or citation chaining), `strand`, `label`, the full `query` as sent, `search_date`,
`n_found` and `n_retrieved`. The last two columns are equal for every row, which is the
evidence that no result set was truncated at a page boundary.

## ads-pass-one-screening.csv

The screening sheet for pass one, one row per unique record, 2,010 rows, written by the same
script. Columns: `bibcode`, `year`, `doi`, `bibstem`, `doctype`, `refereed`,
`citation_count`, `title`, `strands`, `n_strings`, then `screen_decision` and
`screen_reason`, which the script writes empty.

It carries no abstract text. The full retrieval with abstracts is
`02.inputs/searches/ads-pass-one-records.csv`, which is not committed: abstracts are
publisher text and this repository does not redistribute third-party literature in any
format. Screening is done against that file; what is committed is the decision and the
reason for it.

## fulltext-pass-one-register.csv

The stage-two working register, one row per record carried to full text, written
2026-08-14 by `05.scripts/fulltext_pass_one_locate.py`. It is the artefact every
full-text assessment cites back to, and it holds three things that were previously
separate: the verified bibliographic record, the check that the DOI resolves to the
right paper, and the route by which the full text can be obtained.

Bibliography comes from Crossref by DOI, never from the ADS metadata and never from
memory, under the protocol's Verification section. The `cr_` columns are the registry
response as returned.

`verify_status` is the guard. `verified` means the Crossref title matches the ADS title
at or above 0.60 on a normalised similarity ratio. `title mismatch` means the DOI
resolves to a real record that is not this paper, which has happened in this project
before and is the reason the column exists. `doi does not resolve` and `no doi, hand
entry` are what they say. `registry unreachable, retry` is a network state, not a
finding, and is cleared by re-running.

`record_class` is the eligibility class the criteria are applied to: `article`,
`preprint`, `report`, `conference`, `chapter`, `book`, `thesis`, `other`. Theses became
an admitted class on Seamus's ruling of 2026-08-14 and carry the flag that class name
gives them, so no thesis can be cited as peer-reviewed by accident.

`fulltext_route` and `obtainable` say how the text is reached. `open access` is a legal
copy located by Unpaywall, `arxiv` an identifier read off the ADS bibcode, `request` a
record whose copy exists but has no automatic route and goes to the institutional route
by hand, `hand entry` a record with no DOI at all.

## fulltext-pass-one-counts.csv

The tallies of the register, `measure`, `level`, `n`, written by the same script so the
prose quotes a saved number rather than a recounted one. The `obtainable` measure is
what feeds `fulltext_unobtainable` in the PRISMA-ScR flow.

## fulltext-pass-one-charted.csv

The stage-two result: one row per record assessed at full text, written by
`05.scripts/fulltext_pass_one_merge.py` from the assessors' returns. This is the table
the synthesis is built from, and the only artefact in the review that records what each
included paper actually contributes rather than merely that it was kept.

`ft_decision` is `include`, `exclude` or `unobtainable`. The third is a reported
PRISMA-ScR stage, not a quiet failure: it means the paper could not be reached, and it is
counted separately from the papers that were read and rejected.

`ft_code` is the controlled code the reason opens with, and it is what the charting groups
on. Include codes: `method`, `modification`, `theoretical position`, `data constraint`,
`quantitative precedent`. Exclude codes: `application only`, `domain does not transfer`,
`off topic`, `not English`, `ineligible record type`, `no contribution`.

`evidence_basis` is `full text` or `abstract`, and it exists so the synthesis can never
report an abstract-based judgement as though the paper had been read. The merge refuses
any row coded `quantitative precedent` that is not `full text`, because an effect size
read off an abstract is the number most likely to be wrong and it would go straight into
a power calculation.

Charting columns: `study_type`, `region`, `variable` and `bears_on` are required on every
include; `record_years`, `estimator`, `autocorrelation`, `multiplicity`, `enso_handling`,
`effect_size` and `limitation` are filled where the paper reports them, with
`not reported` as the honest entry and blank disallowed.

The merge is a hard gate. It refuses to write at all if any record is decided twice or not
at all, if a reason does not open with a controlled code, if an include has empty required
charting, or if a record is called unobtainable when the register located a copy for it.

## study-area-boundary-candidates.csv

Measurements of the three official boundaries that carry the name Okanagan, written
2026-08-14 by `05.scripts/resolve_study_area_boundary.R` to settle the study area on
Seamus's ruling. Columns `item`, `value`, in hectares except the two marked as degrees
and per cent. It records that BC's major watershed WA2 is the Freshwater Atlas Okanagan
group plus the Similkameen, and that the federal sub-sub-drainage 08NM is the binational
basin with 402,172 ha south of the border, which is why neither is the study area.

## prisma-scr-counts.csv

Screening counts for the prior-work scoping review, one row per strand per stage.
Written from the strand files under `docs/science-superpowers/prior-work/strands/`.
Read by `05.scripts/prisma_scr_flow.R`, which draws the PRISMA-ScR flow diagram and
refuses to draw it if the counts do not balance.

Columns: `strand`, `stage`, `n`.

Permitted `stage` values, and nothing else:

| Stage | Meaning |
|---|---|
| `identified_database` | Records identified by database searching. |
| `identified_other` | Records identified by other means, including citation chaining. |
| `duplicates_removed` | Duplicates removed before screening. |
| `screened` | Records screened on title and abstract. |
| `excluded_screening` | Excluded at title and abstract. |
| `fulltext_sought` | Full text sought. |
| `fulltext_unobtainable` | Full text sought but not retrieved. |
| `fulltext_assessed` | Full text assessed for eligibility. |
| `excluded_fulltext` | Excluded at full text, with reasons recorded in the strand file. |
| `included` | Records included in the review. |

The script enforces four identities and stops rather than warns if any fails:
screened equals identified minus duplicates removed; full text sought equals screened
minus excluded at screening; full text assessed equals sought minus unobtainable;
included equals assessed minus excluded at full text.

Status 2026-08-14: written through `fulltext_sought` only. The three later stages are
empty because the full-text stage is in progress, so `05.scripts/prisma_scr_flow.R` will
stop on its identities if run, which is the guard working rather than failing. Do not run
it until `fulltext_unobtainable`, `fulltext_assessed`, `excluded_fulltext` and `included`
are filled from the register.

The script was tested against synthetic counts on 2026-08-13, both the success path and
both guard paths, and the synthetic file and its outputs were deleted so that no
fabricated number persists in a committed folder.

---

## Fire danger analysis

Added 2026-08-15.

Everything below is written by the scripts named, in the order named, and read by
`01.manuscript/manuscript.qmd`. Nothing here is hand-edited.

### fire-weather-retrieval-log.csv

Written by `05.scripts/fetch_fire_weather.py`. One row per season retrieved from the
BCWS weather data mart: `year`, `layout` (annual file or per-day files), `rows_seen`
province wide, `rows_kept` inside the basin, and elapsed `seconds`. It is the evidence
that a season was actually read rather than skipped, and the ratio of kept to seen is a
sanity check on the station filter.

### station-metadata.csv

Written by `05.scripts/compute_fwi_series.py` on first run, from the `stations` layer of
`02.inputs/spatial/study-area.gpkg`. The five station codes, names, coordinates and
elevations. It is cached so the weather computation does not need a spatial library, and
the station code is written as a string because reading it back as an integer once broke
the join to the weather record silently.

### timezone-verification.csv

Written by `05.scripts/compute_fwi_series.py`. Three numbers that establish the timestamp
convention of the weather record rather than assuming it: how many operational daily FWI
codes appear at hour 12, how many appear at any other hour, and the modal hour of daily
maximum temperature in summer. The second must be zero.

### fwi1987-validation.csv

Written by `05.scripts/validate_fwi1987.py`. Agreement between this project's FWI1987
implementation and the CRAN package `cffdrs`, over the Petawawa Research Forest 2007 daily
test record: `component`, `n`, `max_abs_diff`, `mean_abs_diff`, `max_value`. Agreement is
at machine precision, which is the intended result: the two are the same arithmetic.

### fwi1987-operational-check.csv

Written by `05.scripts/compute_fwi_series.py`. The second, independent check: this
project's FWI1987 against the FWI1987 codes BC Wildfire Service itself computed at these
stations at the time. One row per station, season and component, with `n`, `pearson_r`,
`mean_bias` and `rmse`. This check is not expected to be exact. The service overwinters
the Drought Code and this study does not, because the stations report no winter weather,
so a large negative bias in `DROUGHT_CODE` and a smaller one in `BUILDUP_INDEX` is the
expected signature of that difference and not a fault.

### fwi-station-season-coverage.csv

Written by `05.scripts/compute_fwi_series.py`. One row per station and season across the
full grid, including seasons a station did not report at all, so that an absence appears
as a row rather than vanishing. `observed_fraction` is the share of 1 April to 30
September hours with temperature, humidity and wind all present, before any gap filling.
`status` is `kept`, `dropped, coverage`, `station not reporting` or `no data in window`.

### fwi-series-daily.csv

Written by `05.scripts/compute_fwi_series.py`. The core table: one row per station-day
over 1 May to 30 September, with all seven components under each of the three series.
Columns prefixed `s1_` are FWI1987 from the 13:00 observation; `s2_` are FWI2025 from the
same observation through pathway C; `s3_` are FWI2025 from the observed hourly weather
through pathway A. Columns suffixed `_max` are the daily maximum over 24 hours, carried
as a sensitivity on the choice of daily summary hour. `peak_hr` and `duration` come from
the specification's own daily summary module and have no FWI1987 counterpart.

### example-season-hourly.csv

Written by `05.scripts/compute_fwi_series.py`. One station-season, Penticton RS 2003, of
hourly output under S2 and S3 kept whole, so that the mechanism figure draws real output
rather than an illustration.

### seasonal-metrics.csv

Written by `05.scripts/build_seasonal_metrics.py`. One row per station, season and series,
with the seasonal metrics the trend analysis runs on: mean and maximum Fire Weather Index,
seasonal severity rating, peak Buildup Index, and day counts above the absolute thresholds
(FFMC 91, FWI 19, FWI 30) and above each series' own 90th and 95th percentile of its 1991
to 2020 reference distribution.

### threshold-percentiles.csv

Written by `05.scripts/build_seasonal_metrics.py`. Where each absolute threshold falls in
each series' own reference distribution, per station. This is the direct test of the
comparability claim in section 4.1 of GLC-X-42.

### basin-daily.csv

Written by `05.scripts/build_seasonal_metrics.py`. Basin mean daily danger, averaged over
a fixed set of stations rather than whichever reported that day, so the basin value cannot
jump when a station joins or leaves. Input to the ignition models.

### ignitions-daily.csv, ignition-completeness.csv, ignition-attribution.csv

Written by `05.scripts/build_ignition_series.py` from the `ignitions` layer of the study
area package. Daily counts on a complete calendar so that a day with no fire is a zero and
not an absence, split by cause (lightning, person, all) and by minimum size (none, 1 ha,
4 ha). The two companion tables document why the counts must be read carefully: roughly a
quarter of incidents carry no ignition date at all and cannot be placed on a day, and both
dating and cause attribution fall sharply after 2000.

### reference-verification.csv

Written by `05.scripts/verify_references.py`. One row per candidate citation, recording
the title claimed, the DOI claimed, the title that DOI actually resolves to, the title
Crossref returns for an independent title search, the similarity of each, and the verdict.
An entry reaches `04.references/references.bib` only where both agree.
