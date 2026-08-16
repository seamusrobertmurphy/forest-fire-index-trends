# prisma_scr_flow.R
#
# Draws the PRISMA-ScR flow diagram for the prior-work scoping review from saved
# screening counts. Nothing here is typed by hand: every number in the figure is
# read from 02.inputs/derived/prisma-scr-counts.csv, which the strand agents fill
# and which is committed. The figure therefore cannot drift from the counts it
# depicts, which is the whole reason this is drawn in R rather than generated as
# a schematic from a prompt.
#
# Reporting standard: Tricco et al. 2018, PRISMA Extension for Scoping Reviews,
# Annals of Internal Medicine 169:467-473, doi:10.7326/M18-0850.
#
# Usage, from the repository root:
#   Rscript 05.scripts/prisma_scr_flow.R
#
# Inputs : 02.inputs/derived/prisma-scr-counts.csv
# Outputs: 03.outputs/figures/prisma-scr-flow.png
#          03.outputs/prisma-scr-counts-summary.csv

# Resolve the repository root without depending on how the script was invoked:
# walk up from the working directory until the marker folder appears.
find_root <- function(start = normalizePath(".")) {
  p <- start
  for (i in 1:6) {
    if (dir.exists(file.path(p, "05.scripts")) &&
        dir.exists(file.path(p, "01.manuscript"))) return(p)
    parent <- dirname(p)
    if (identical(parent, p)) break
    p <- parent
  }
  stop("Could not locate the repository root from ", start)
}
root <- find_root()

counts_path <- file.path(root, "02.inputs", "derived", "prisma-scr-counts.csv")
fig_path    <- file.path(root, "03.outputs", "figures", "prisma-scr-flow.png")
sum_path    <- file.path(root, "03.outputs", "prisma-scr-counts-summary.csv")

# ---------------------------------------------------------------------------
# Stage vocabulary. The CSV must use these stage names exactly. Any other value
# is an error rather than a silent drop, because a miscounted stage would
# produce a plausible but wrong flow diagram, which is worse than a crash.
# ---------------------------------------------------------------------------
main_stages <- c(
  "identified_database",
  "identified_other",
  "duplicates_removed",
  "screened",
  "fulltext_sought",
  "fulltext_assessed",
  "included"
)
side_stages <- c(
  "excluded_screening",
  "fulltext_unobtainable",
  "excluded_fulltext"
)
valid_stages <- c(main_stages, side_stages)

main_labels <- c(
  identified_database   = "Records identified,\ndatabase searching",
  identified_other      = "Records identified,\nother sources",
  duplicates_removed    = "Records after\nduplicates removed",
  screened              = "Records screened,\ntitle and abstract",
  fulltext_sought       = "Full text sought",
  fulltext_assessed     = "Full text assessed\nfor eligibility",
  included              = "Records included\nin the review"
)
side_labels <- c(
  excluded_screening    = "Excluded at\ntitle and abstract",
  fulltext_unobtainable = "Full text not\nretrieved",
  excluded_fulltext     = "Excluded at\nfull text"
)

# ---------------------------------------------------------------------------
# Read and validate
# ---------------------------------------------------------------------------
if (!file.exists(counts_path)) {
  stop("Counts file not found at ", counts_path,
       ". The flow diagram is built from saved counts only; it is not drawn ",
       "until the strand agents have written them.")
}

cnt <- utils::read.csv(counts_path, stringsAsFactors = FALSE)

required_cols <- c("strand", "stage", "n")
missing_cols <- setdiff(required_cols, names(cnt))
if (length(missing_cols)) {
  stop("prisma-scr-counts.csv is missing column(s): ",
       paste(missing_cols, collapse = ", "))
}

cnt$stage <- trimws(cnt$stage)
bad <- setdiff(unique(cnt$stage), valid_stages)
if (length(bad)) {
  stop("Unrecognised stage name(s) in prisma-scr-counts.csv: ",
       paste(bad, collapse = ", "),
       ". Permitted values are: ", paste(valid_stages, collapse = ", "))
}

if (!is.numeric(cnt$n) || any(is.na(cnt$n))) {
  stop("Column n must be numeric with no missing values.")
}

# ---------------------------------------------------------------------------
# Aggregate across strands, and check the flow is arithmetically coherent.
# A flow diagram whose boxes do not balance is a reporting error, so this is a
# hard stop rather than a warning.
# ---------------------------------------------------------------------------
tot <- tapply(cnt$n, cnt$stage, sum)
g <- function(s) if (s %in% names(tot)) as.integer(tot[[s]]) else 0L

identified <- g("identified_database") + g("identified_other")
checks <- c(
  "duplicates removed cannot exceed records identified" =
    g("duplicates_removed") <= identified,
  "screened equals identified minus duplicates removed" =
    g("screened") == identified - g("duplicates_removed"),
  "full text sought equals screened minus excluded at screening" =
    g("fulltext_sought") == g("screened") - g("excluded_screening"),
  "full text assessed equals sought minus unobtainable" =
    g("fulltext_assessed") == g("fulltext_sought") - g("fulltext_unobtainable"),
  "included equals assessed minus excluded at full text" =
    g("included") == g("fulltext_assessed") - g("excluded_fulltext")
)
if (any(!checks)) {
  stop("PRISMA-ScR flow does not balance:\n  ",
       paste(names(checks)[!checks], collapse = "\n  "),
       "\nFix the counts in prisma-scr-counts.csv rather than the diagram.")
}

# Per-strand summary, committed alongside the figure so the reader can see which
# strand contributed what rather than only the pooled total.
wide <- stats::reshape(
  cnt[, c("strand", "stage", "n")],
  idvar = "strand", timevar = "stage", direction = "wide"
)
names(wide) <- sub("^n\\.", "", names(wide))
dir.create(dirname(sum_path), recursive = TRUE, showWarnings = FALSE)
utils::write.csv(wide, sum_path, row.names = FALSE)

# ---------------------------------------------------------------------------
# Draw. Base R, per the project convention that base R is preferred for tables
# and figures.
# ---------------------------------------------------------------------------
box <- function(x, y, w, h, label, n, cex = 0.72) {
  graphics::rect(x - w / 2, y - h / 2, x + w / 2, y + h / 2,
                 col = "white", border = "grey25", lwd = 1.1)
  graphics::text(x, y, paste0(label, "\n(n = ", n, ")"),
                 cex = cex, col = "black")
}
arrow <- function(x0, y0, x1, y1) {
  graphics::arrows(x0, y0, x1, y1, length = 0.07, angle = 20,
                   col = "grey25", lwd = 1.1)
}

dir.create(dirname(fig_path), recursive = TRUE, showWarnings = FALSE)
grDevices::png(fig_path, width = 1800, height = 2300, res = 300)
op <- graphics::par(mar = c(0, 0, 0, 0))

graphics::plot(NA, xlim = c(0, 10), ylim = c(0, 15),
               axes = FALSE, xlab = "", ylab = "")

bw <- 3.4; bh <- 1.35; xm <- 3.4; xs <- 7.6

box(1.9, 14.0, bw * 0.95, bh, main_labels[["identified_database"]],
    g("identified_database"))
box(6.0, 14.0, bw * 0.95, bh, main_labels[["identified_other"]],
    g("identified_other"))

box(xm, 11.6, bw, bh, main_labels[["duplicates_removed"]],
    g("duplicates_removed"))
box(xm,  9.3, bw, bh, main_labels[["screened"]],              g("screened"))
box(xm,  7.0, bw, bh, main_labels[["fulltext_sought"]],       g("fulltext_sought"))
box(xm,  4.7, bw, bh, main_labels[["fulltext_assessed"]],     g("fulltext_assessed"))
box(xm,  2.2, bw, bh, main_labels[["included"]],              g("included"))

box(xs,  9.3, bw * 0.85, bh, side_labels[["excluded_screening"]],
    g("excluded_screening"), cex = 0.66)
box(xs,  7.0, bw * 0.85, bh, side_labels[["fulltext_unobtainable"]],
    g("fulltext_unobtainable"), cex = 0.66)
box(xs,  4.7, bw * 0.85, bh, side_labels[["excluded_fulltext"]],
    g("excluded_fulltext"), cex = 0.66)

arrow(1.9, 14.0 - bh / 2, xm - 0.5, 11.6 + bh / 2)
arrow(6.0, 14.0 - bh / 2, xm + 0.5, 11.6 + bh / 2)
arrow(xm, 11.6 - bh / 2, xm,  9.3 + bh / 2)
arrow(xm,  9.3 - bh / 2, xm,  7.0 + bh / 2)
arrow(xm,  7.0 - bh / 2, xm,  4.7 + bh / 2)
arrow(xm,  4.7 - bh / 2, xm,  2.2 + bh / 2)
arrow(xm + bw / 2, 9.3, xs - bw * 0.85 / 2, 9.3)
arrow(xm + bw / 2, 7.0, xs - bw * 0.85 / 2, 7.0)
arrow(xm + bw / 2, 4.7, xs - bw * 0.85 / 2, 4.7)

graphics::text(5, 0.6,
  paste0("PRISMA-ScR flow. Sources searched: Crossref, arXiv, web. ",
         "Web of Science, Scopus and NASA ADS were not reachable."),
  cex = 0.55, col = "grey30")

graphics::par(op)
grDevices::dev.off()

message("Wrote ", fig_path)
message("Wrote ", sum_path)
message("Included records: ", g("included"))
