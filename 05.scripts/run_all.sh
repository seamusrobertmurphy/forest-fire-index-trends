#!/bin/sh
# ---------------------------------------------------------------------------
# Rebuild everything, in dependency order, from the public sources.
#
# Written 2026-08-15. Each step writes into 02.inputs/derived and the next step
# reads what the previous one wrote, so the order is not cosmetic. The whole run
# takes a few hours, almost all of it in the first step: the BC Wildfire Service
# weather data mart publishes province-wide files of up to about 210 MB per
# season and this retrieves every one of them from 1987, keeping only the five
# basin stations.
#
# Steps 2 to 6 are minutes, not hours. If the weather record is already present
# at 02.inputs/weather/bcws-okanagan-hourly.csv, start at step 2.
#
# Usage:  sh 05.scripts/run_all.sh
# ---------------------------------------------------------------------------
set -e
cd "$(dirname "$0")/.."

echo "== 1. study area, ignitions and station locations =="
/usr/local/bin/R --vanilla --quiet -f 05.scripts/fetch_study_area.R

echo "== 2. hourly fire weather, 1987 to 2025 (hours) =="
python3 05.scripts/fetch_fire_weather.py

echo "== 3. check the FWI1987 implementation against CRAN cffdrs =="
python3 05.scripts/validate_fwi1987.py

echo "== 4. compute the three danger series =="
python3 05.scripts/compute_fwi_series.py

echo "== 5. seasonal metrics, thresholds and the basin daily series =="
python3 05.scripts/build_seasonal_metrics.py

echo "== 6. daily ignition counts and record completeness =="
python3 05.scripts/build_ignition_series.py

echo "== 7. verify every citation against Crossref =="
python3 05.scripts/verify_references.py

echo "== 7b. verify every quotation against the report it cites =="
python3 05.scripts/verify_quotations.py

echo "== 8. render the manuscript, both formats =="
cd 01.manuscript && quarto render manuscript.qmd --to html && quarto render manuscript.qmd --to docx
cd ..

echo "== 9. rebuild the root README from the render's own artefacts =="
/usr/local/bin/R --vanilla --quiet -f 05.scripts/build_readme.R

echo "Done. 01.manuscript/manuscript.html, 01.manuscript/manuscript.docx, README.md"
