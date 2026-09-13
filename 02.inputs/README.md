# Input data manifest

Every dataset entered here records what it is, where it came
from, its licence as read from the source on a stated date, and the saved script that
fetched it. Raw data are gitignored; this manifest and the retrieval scripts are the
reproducible record. Integrity hashes go in `SHA256SUMS.txt` beside the data.

Public data only unless Seamus approves an exception in writing, and an approved
exception is recorded here with the licence text as read and the conditions of use.

## Downloaded

| Folder | Dataset | Source | Licence | Notes |
|---|---|---|---|---|
| `spatial/` | `study-area.gpkg`, eight layers: `basin`, `ignitions`, `lakes`, `streams`, `places`, `stations`, `era5_grid`, `province` | BC Data Catalogue WFS, `https://openmaps.gov.bc.ca/geo/pub/wfs`, retrieved 2026-08-14 by `05.scripts/fetch_study_area.R`. Object names are in the script and in the layer table below. | Open Government Licence, British Columbia | Study-area geometry for the methods figure. `era5_grid` is not downloaded: it is a constructed 0.1 degree graticule that showed the support of a candidate gridded weather input. That candidate was set aside on 2026-08-15 in favour of the station network, which carries genuinely hourly precipitation, and the graticule is no longer drawn. The layer is kept so the earlier figure can be reproduced. Integrity hashes in `spatial/MD5SUMS.txt`. |
| `spatial/` | `dem-z9.tif`, 99 m digital elevation model over the basin and a 5 km margin | AWS Terrain Tiles, zoom 9, via `elevatr::get_elev_raster`, retrieved 2026-08-14 | Terrain Tiles are public domain, sourced from SRTM and national datasets | Relief for the hillshade in the study-area figure only. Not an analysis input. |
| `weather/` | `bcws-okanagan-hourly.csv`, hourly fire weather observations at the five BC Wildfire Service stations inside the basin | BCWS Weather Data Mart, `https://www.for.gov.bc.ca/ftp/HPR/external/!publish/BCWS_DATA_MART/`, retrieved 2026-08-15 by `05.scripts/fetch_fire_weather.py` | Published by the BC Ministry of Forests as an open public file directory. No licence statement accompanies the directory; the ministry's data are ordinarily released under the Open Government Licence, British Columbia, and that is the assumption recorded here, with the date it was made. Not redistributed. | **The weather record of this study.** Hourly temperature, relative humidity, wind speed and precipitation, plus the FWI1987 codes BC Wildfire Service computed operationally at the time, which are used as an independent check on this project's implementation. Seasons 1987 to 2023 are annual province-wide files; 2024 onward are one file per day. The retrieval streams each response and discards non-basin rows as they arrive, so no provincial file is ever stored. Retrieval log at `derived/fire-weather-retrieval-log.csv`. |
| `searches/` | `ads-pass-one-records.csv`, 2,010 bibliographic records with abstracts | NASA ADS API, retrieved 2026-08-14 by `05.scripts/ads_pass_one_retrieve.py` | Personal API token, research use. Abstracts are publisher text and are not redistributed | Prior-work review, pass one. Screening is done against this file; the committed artefacts are the search log and the decisions under `derived/`. |

Layers taken from the BC Data Catalogue, with the object name each came from:
`WHSE_BASEMAPPING.FWA_WATERSHED_GROUPS_POLY`,
`WHSE_LAND_AND_NATURAL_RESOURCE.PROT_HISTORICAL_INCIDENTS_SP`,
`WHSE_BASEMAPPING.FWA_LAKES_POLY`, `WHSE_BASEMAPPING.FWA_STREAM_NETWORKS_SP`,
`WHSE_LEGAL_ADMIN_BOUNDARIES.ABMS_MUNICIPALITIES_SP`,
`WHSE_LAND_AND_NATURAL_RESOURCE.PROT_WEATHER_STATIONS_SP`,
`WHSE_LEGAL_ADMIN_BOUNDARIES.ABMS_PROVINCE_SP`. The incident record's own metadata note
reads "Not to be used for legal purposes", and it is used here only to locate and count
ignitions.

## Bibliography keys

Each dataset above is cited in the manuscript under the key given here, so the
manifest and the bibliography cannot drift. Catalogue titles and owners were read
from the BC Data Catalogue API on 2026-09-12.

| Dataset | Key |
|---|---|
| Freshwater Atlas watershed groups | `geobc2026fwagroups` |
| Freshwater Atlas lakes | `geobc2026fwalakes` |
| Freshwater Atlas stream network | `geobc2026fwastreams` |
| BC Major Watersheds | `geobc2026majorwatersheds` |
| Water Survey of Canada sub-sub-drainage areas | `wsc2026subsubdrainage` |
| Municipalities | `bc2026municipalities` |
| Province outline | `geobc2026province` |
| BC Wildfire active weather stations | `bcws2026stations` |
| BC Wildfire fire incident locations, historical | `bcws2026incidents` |
| BCWS Weather Data Mart | `bcws2026datamart` |
| AWS Terrain Tiles | `aws2026terraintiles` |
| NG-CFFDRS reference implementation | `nrcan2026cffdrsng` |
| CRAN package cffdrs 1.9.2 | `wang2026cffdrspkg` |

## Derived

Derived products state the script or manuscript chunk that builds them, whether they are
regenerable, and whether they are committed. Those under `derived/` are committed and
documented in `derived/README.md`; `study-area-counts.csv` and `ignitions-by-season.csv`
are written by `05.scripts/fetch_study_area.R` and are the only source of the study-area
numbers quoted in the manuscript.

## Streaming or on-demand

Crossref, `https://api.crossref.org`, queried 2026-08-15 by
`05.scripts/verify_references.py` to resolve and verify every bibliographic entry before
it enters `04.references/references.bib`. Public API, no authentication, polite pool with
a mailto header. Nothing is stored except the verification table at
`derived/reference-verification.csv`. Record here any source read at analysis time rather than downloaded, with
its access terms and any redistribution limit.
