## ---------------------------------------------------------------------------
## Build the root README from the manuscript's own render artefacts.
##
## Written 2026-08-15 on Seamus's instruction: the README carries the title, the
## abstract, and the figures and tables, and nothing else. No prose sections, no
## restatement of the methods.
##
## Rewritten 2026-10-26. The README quotes rather than recomputes, and since that
## day it quotes the rendered HTML itself: every figure and table caption, every
## table body and the order and numbering of both are read from
## `01.manuscript/manuscript.html`, so the README shows exactly what the
## manuscript shows, including the two tables typed as Markdown in the prose and
## the figure in the appendix. The abstract and title come from the text files the
## `export-artefacts` chunk writes, and each figure from the PNG knitr wrote. The
## README goes stale in an obvious way, by disappearing, if the render has not run.
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
fig_dir <- file.path(outputs, "figures")
html_file <- file.path(root, "01.manuscript", "manuscript.html")

for (f in c(file.path(outputs, "abstract.txt"), html_file))
  if (!file.exists(f))
    stop("No render artefact at ", f,
         ". Render 01.manuscript/manuscript.qmd to HTML first; this script only quotes it.")

html <- paste(readLines(html_file, warn = FALSE, encoding = "UTF-8"), collapse = "\n")

## Plain text from a fragment of HTML: tags removed, entities decoded, whitespace
## collapsed. Nothing is reworded.
plain <- function(x) {
  x <- gsub("<[^>]+>", "", x)
  x <- gsub("\u00a0", " ", x)
  for (e in list(c("&amp;", "&"), c("&lt;", "<"), c("&gt;", ">"), c("&quot;", "\""),
                 c("&#39;", "'"), c("&nbsp;", " "), c("&ndash;", "–"), c("&mdash;", "—")))
    x <- gsub(e[1], e[2], x, fixed = TRUE)
  trimws(gsub("\\s+", " ", x))
}

## Every float caption in document order, with its label and the number Quarto
## gave it. The caption text is kept as rendered, minus the "Figure 3: " prefix,
## which the README restates in its own bold form.
cap_pat <- '(?s)<figcaption class="[^"]*" id="((fig|tbl)-[A-Za-z0-9_-]+)-caption-[^"]*">(.*?)</figcaption>'
caps <- regmatches(html, gregexpr(cap_pat, html, perl = TRUE))[[1]]
floats <- lapply(caps, function(m) {
  parts <- regmatches(m, regexec(cap_pat, m, perl = TRUE))[[1]]
  txt <- plain(parts[4])
  num <- sub("^(Figure|Table) ([0-9A-Z.]+):.*$", "\\2", txt)
  list(label = parts[2], kind = parts[3], number = num,
       caption = sub("^(Figure|Table) [0-9A-Z.]+:\\s*", "", txt))
})

## A GFM pipe table from the rendered <table> that follows a float's id. Cells
## have their pipes escaped and their newlines replaced, because either would
## break the row. Right alignment is kept where the render set it.
pipe_table <- function(label) {
  start <- regexpr(paste0('<div id="', label, '"'), html, fixed = TRUE)
  if (start < 0) return(NULL)
  rest <- substr(html, start, nchar(html))   # substring() stops at one million characters
  t0 <- regexpr("<table", rest, fixed = TRUE)
  if (t0 < 0) return(NULL)
  t1 <- regexpr("</table>", substring(rest, t0), fixed = TRUE)
  if (t1 < 0) return(NULL)
  tbl <- substring(rest, t0, t0 + t1 + 6)
  rows <- regmatches(tbl, gregexpr("(?s)<tr[^>]*>.*?</tr>", tbl, perl = TRUE))[[1]]
  cells <- lapply(rows, function(r) {
    cs <- regmatches(r, gregexpr("(?s)<t[hd][^>]*>.*?</t[hd]>", r, perl = TRUE))[[1]]
    txt <- vapply(cs, function(c) gsub("\\|", "\\\\|", plain(c)), "")
    right <- grepl('text-align:\\s*right|class="[^"]*right[^"]*"', cs)
    list(txt = txt, right = right)
  })
  hdr <- cells[[1]]$txt
  align <- vapply(seq_along(hdr), function(j) {
    col_right <- vapply(cells[-1], function(r) length(r$right) >= j && r$right[j], logical(1))
    if (length(col_right) && all(col_right)) "---:" else ":---"
  }, "")
  c(paste0("| ", paste(hdr, collapse = " | "), " |"),
    paste0("| ", paste(align, collapse = " | "), " |"),
    vapply(cells[-1], function(r) paste0("| ", paste(r$txt, collapse = " | "), " |"), ""))
}

title <- paste(readLines(file.path(outputs, "title.txt"), warn = FALSE), collapse = " ")
abstract <- paste(readLines(file.path(outputs, "abstract.txt"), warn = FALSE), collapse = " ")

out <- c(
  paste("#", title),
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
for (fl in floats) {
  if (fl$kind != "fig") next
  png <- file.path(fig_dir, paste0("mfig-", fl$label, "-1.png"))
  if (!file.exists(png)) { message("no PNG for ", fl$label, ", skipped"); next }
  n_fig <- n_fig + 1
  out <- c(out,
           paste0("**Figure ", fl$number, ".** ", fl$caption),
           "",
           paste0("![", fl$label, "](03.outputs/figures/", basename(png), ")"),
           "")
}
if (n_fig == 0) out <- c(out, "No figure files found. Render the manuscript first.", "")

out <- c(out, "## Tables", "")

n_tbl <- 0
for (fl in floats) {
  if (fl$kind != "tbl") next
  body <- pipe_table(fl$label)
  if (is.null(body)) { message("no table body for ", fl$label, ", skipped"); next }
  n_tbl <- n_tbl + 1
  out <- c(out, paste0("**Table ", fl$number, ".** ", fl$caption), "", body, "")
}
if (n_tbl == 0) out <- c(out, "No tables found. Render the manuscript first.", "")

writeLines(out, file.path(root, "README.md"), useBytes = TRUE)
cat(sprintf("Wrote README.md: %d figures, %d tables, %d lines.\n",
            n_fig, n_tbl, length(out)))
