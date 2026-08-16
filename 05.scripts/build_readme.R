## ---------------------------------------------------------------------------
## Build the root README from the manuscript's own render artefacts.
##
## Written 2026-08-15 on Seamus's instruction: the README carries the title, the
## abstract, and the figures and tables, and nothing else. No prose sections, no
## restatement of the methods.
##
## The rule that makes this safe is that the README quotes rather than recomputes.
## Every number in it comes from a file the render wrote: the abstract from
## `03.outputs/abstract.txt`, each table from `03.outputs/tables/<label>.csv`, and
## each figure from the PNG knitr produced. So the README cannot say something the
## manuscript does not, and it goes stale in an obvious way, by disappearing, if
## the render has not been run.
##
## GitHub renders this file, not Pandoc, so tables are written as GFM pipe tables.
## Pandoc grid tables, the `+---+---+` style Quarto emits, print on GitHub as a
## wall of plus signs.
##
## Usage:  Rscript 05.scripts/build_readme.R
## ---------------------------------------------------------------------------

root <- normalizePath(".")
while (!all(dir.exists(file.path(root, c("01.manuscript", "03.outputs"))))) {
  up <- dirname(root)
  if (up == root) stop("Not inside the forest-fire-index-trends repository.")
  root <- up
}
outputs <- file.path(root, "03.outputs")
tbl_dir <- file.path(outputs, "tables")
fig_dir <- file.path(outputs, "figures")

need <- file.path(outputs, "abstract.txt")
if (!file.exists(need))
  stop("No render artefacts at ", need,
       ". Render 01.manuscript/manuscript.qmd first; this script only quotes it.")

## The manuscript writes its figures straight into `fig_dir` by setting knitr's
## fig.path, because with embed-resources Quarto deletes the render sidecar once
## it has inlined the images, leaving nothing on disk. Nothing to copy here.
dir.create(fig_dir, recursive = TRUE, showWarnings = FALSE)

## A GFM pipe table. Cells have their pipes escaped and their newlines replaced,
## because either would break the row.
pipe_table <- function(df) {
  clean <- function(x) {
    x <- format(x, trim = TRUE, big.mark = "", scientific = FALSE)
    x <- gsub("\\|", "\\\\|", x)
    trimws(gsub("[\r\n]+", " ", x))
  }
  cells <- as.data.frame(lapply(df, clean), stringsAsFactors = FALSE)
  hdr <- paste0("| ", paste(gsub("\\|", "\\\\|", names(df)), collapse = " | "), " |")
  ## Numeric columns right aligned, everything else left, which is the house
  ## style the manuscript's own tables use.
  align <- vapply(df, function(col) if (is.numeric(col)) "---:" else ":---", "")
  sep <- paste0("| ", paste(align, collapse = " | "), " |")
  rows <- apply(cells, 1, function(r) paste0("| ", paste(r, collapse = " | "), " |"))
  c(hdr, sep, rows)
}

read_caption <- function(label) {
  f <- file.path(tbl_dir, paste0(label, ".caption.txt"))
  if (file.exists(f)) paste(readLines(f, warn = FALSE), collapse = " ") else ""
}

## Order of appearance in the manuscript. Anything the render did not write is
## skipped silently here and is therefore visibly absent from the README.
TABLE_ORDER <- c("tbl-stations", "tbl-completeness", "tbl-verify", "tbl-thresholds",
                 "tbl-capability", "tbl-trends", "tbl-slopediff", "tbl-sensitivity",
                 "tbl-ignition", "tbl-stationarity", "tbl-shift", "tbl-limits")
FIGURE_ORDER <- c("fig-study-area", "fig-distributions", "fig-mechanism",
                  "fig-trends", "fig-slopediff", "fig-ignition")

figcaps <- character(0)
capfile <- file.path(fig_dir, "captions.tsv")
if (file.exists(capfile)) {
  cc <- strsplit(readLines(capfile, warn = FALSE), "\t")
  figcaps <- setNames(vapply(cc, function(x) x[2], ""), vapply(cc, function(x) x[1], ""))
}

title <- paste(readLines(file.path(outputs, "title.txt"), warn = FALSE), collapse = " ")
subtitle <- paste(readLines(file.path(outputs, "subtitle.txt"), warn = FALSE), collapse = " ")
abstract <- readLines(file.path(outputs, "abstract.txt"), warn = FALSE)

out <- c(
  paste("#", title),
  "",
  paste0("*", subtitle, "*"),
  "",
  "Seamus Murphy, ORCID 0000-0002-1792-0351.",
  "",
  paste("Everything below is generated from the render of",
        "`01.manuscript/manuscript.qmd` by `05.scripts/build_readme.R`, which",
        "quotes the manuscript's own output files and computes nothing of its own."),
  "",
  "## Abstract",
  "",
  abstract,
  "",
  "## Figures",
  ""
)

n_fig <- 0
for (lab in FIGURE_ORDER) {
  png <- file.path(fig_dir, paste0("mfig-", lab, "-1.png"))
  if (!file.exists(png)) next
  n_fig <- n_fig + 1
  cap <- if (lab %in% names(figcaps)) figcaps[[lab]] else ""
  out <- c(out,
           paste0("**Figure ", n_fig, ".** ", cap),
           "",
           paste0("![", lab, "](03.outputs/figures/", basename(png), ")"),
           "")
}
if (n_fig == 0) out <- c(out, "No figure files found. Render the manuscript first.", "")

out <- c(out, "## Tables", "")

n_tbl <- 0
for (lab in TABLE_ORDER) {
  f <- file.path(tbl_dir, paste0(lab, ".csv"))
  if (!file.exists(f)) next
  n_tbl <- n_tbl + 1
  df <- read.csv(f, check.names = FALSE, stringsAsFactors = FALSE)
  out <- c(out,
           paste0("**Table ", n_tbl, ".** ", read_caption(lab)),
           "",
           pipe_table(df),
           "")
}
if (n_tbl == 0) out <- c(out, "No table files found. Render the manuscript first.", "")

writeLines(out, file.path(root, "README.md"))
cat(sprintf("Wrote README.md: %d figures, %d tables, %d lines.\n",
            n_fig, n_tbl, length(out)))
