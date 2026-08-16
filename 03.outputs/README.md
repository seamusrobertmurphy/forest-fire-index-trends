# Generated outputs

Tables and figures the manuscript writes, committed because the manuscript cites the
numbers in them and because they are the artefacts a reader checks without re-running the
analysis. Everything here is regenerated on every render of
`01.manuscript/manuscript.qmd`; nothing here is hand-edited, and a file that is not
overwritten by a render does not belong here.

| File | Written by | Holds |
|---|---|---|
| `trend-estimates.csv` | `trend-compute` chunk | One row per station, series and metric: the Theil-Sen slope, its bootstrap interval, the Mann-Kendall p value corrected for serial correlation and the uncorrected one, Kendall's tau, the effective sample size ratio the correction used, the false discovery rate adjusted q value, and the minimum detectable trend. |
| `slope-differences.csv` | `slopediff-compute` chunk | One row per station, contrast and metric: both slopes, their difference, the paired bootstrap interval on the difference, the two-sided bootstrap p value and its q value. |
| `hypothesis-scoring.csv` | `slopediff-reading` chunk | The second question scored as it was posed: how often a difference excluded zero under absolute against relative thresholding, for each of the three contrasts. |
| `level-shifts.csv` | `discussion-numbers` chunk | How many days per season each change moves the two absolute-threshold counts, and whether the version and input changes push the same way. |
| `ignition-models.csv` | `ignition-compute` chunk | The negative binomial fits: the danger coefficient, its Wald interval, its p value, the dispersion parameter, and the held-out log likelihood where it was computed. |
| `stationarity-tests.csv` | `stationarity` chunk | The interaction between the danger term and season number, which asks whether the within-season danger to ignition relationship has changed. |
| `detectability.csv` | `limits-compute` chunk | Per metric: the observed slope, the minimum slope this record could resolve at 80 per cent power, and both expressed as change over the whole window. |
| `figures/fig-study-area.png` | `05.scripts/map_study_area.R` run directly | A standalone copy of the study area map for inspection. The manuscript does not read it; it calls the function and renders the figure itself. |
