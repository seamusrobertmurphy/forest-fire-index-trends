#!/bin/sh
# ---------------------------------------------------------------------------
# Render the manuscript and rebuild the README from its artefacts.
#
# Written 2026-08-15, cut down 2026-10-14. Every step that retrieves, computes,
# screens or verifies anything now lives in 01.manuscript/manuscript.qmd as a
# guarded chunk, which runs only when the output it writes is missing. To
# rebuild a stage, delete its output under 02.inputs and render again. The
# weather retrieval is the long stage, a few hours over the province-wide data
# mart files; everything else is minutes.
#
# Usage:  sh 05.scripts/run_all.sh
# ---------------------------------------------------------------------------
set -e
cd "$(dirname "$0")/.."

echo "== 1. render the manuscript, both formats, as two separate calls =="
cd 01.manuscript && quarto render manuscript.qmd --to html && quarto render manuscript.qmd --to docx
cd ..

echo "== 2. rebuild the root README from the render's own artefacts =="
/usr/local/bin/R --vanilla --quiet -f 05.scripts/build_readme.R

echo "Done. 01.manuscript/manuscript.html, 01.manuscript/manuscript.docx, README.md"
