#!/usr/bin/env Rscript
# ---------------------------------------------------------------------------
# Which official boundary is "the entire Okanagan watershed"?
#
# Written 2026-08-14, on Seamus's instruction to settle the study area from
# official government geographic data rather than from the identifier the
# framing document carried. The framing named Freshwater Atlas identifier 212,
# which is Turnagain River in the far north of the province and cannot be what
# was meant.
#
# Three official definitions exist and they disagree by a factor of two, so the
# choice has to be made on evidence rather than on the first layer that returns
# a polygon named Okanagan. This script retrieves all three, measures them, and
# measures what the differences between them consist of. Every number the
# framing document and the review protocol quote about the study-area ruling is
# computed here.
#
#   1. WHSE_BASEMAPPING.FWA_WATERSHED_GROUPS_POLY, WATERSHED_GROUP_ID 161, code
#      OKAN. The Freshwater Atlas is the province's authoritative hydrological
#      framework at 1:20,000.
#   2. WHSE_BASEMAPPING.BC_MAJOR_WATERSHEDS, MAJOR_WATERSHED_CODE WA2, named
#      "Okanagan River".
#   3. WHSE_IMAGERY_AND_BASE_MAPS.DRP_SUB_SUB_DRAINAGES_1M_SP, sub-sub-drainage
#      08NM, named "Okanagan". This is the federal Standard Drainage Area
#      Classification of the Water Survey of Canada, generalised to 1:1,000,000
#      and independent of the provincial framework.
#
# Nothing here computes an outcome. It measures polygons.
#
# Usage:  Rscript 05.scripts/resolve_study_area_boundary.R
# ---------------------------------------------------------------------------

suppressPackageStartupMessages({
  library(sf)
})

# The comparison is planar in BC Albers over areas of a few thousand square
# kilometres, where the projection is the appropriate measurement surface and
# s2's spherical predicates only introduce edge cases on the boundary overlaps.
sf::sf_use_s2(FALSE)

CRS_WORK <- 3005                    # NAD83 / BC Albers, metric, per framing

root <- normalizePath(".")
while (!all(dir.exists(file.path(root, c("02.inputs", "05.scripts"))))) {
  up <- dirname(root)
  if (up == root) stop("Not inside the forest-fire-index-trends repository.")
  root <- up
}
derived_dir <- file.path(root, "02.inputs", "derived")

WFS <- "https://openmaps.gov.bc.ca/geo/pub/wfs"

wfs_get <- function(layer, cql = NULL, page = 10000) {
  q <- c(service = "WFS", version = "2.0.0", request = "GetFeature",
         typeName = layer, outputFormat = "application/json",
         srsName = paste0("EPSG:", CRS_WORK), count = page)
  url <- paste0(WFS, "?", paste0(names(q), "=",
                                 vapply(q, utils::URLencode, "", reserved = TRUE),
                                 collapse = "&"))
  if (!is.null(cql))
    url <- paste0(url, "&CQL_FILTER=", utils::URLencode(cql, reserved = TRUE))
  sf::st_make_valid(sf::st_read(url, quiet = TRUE))
}

ha <- function(x) as.numeric(sum(sf::st_area(x))) / 1e4
msg <- function(...) cat(sprintf(...), "\n")

# --- The three candidates --------------------------------------------------
fwa <- wfs_get("WHSE_BASEMAPPING.FWA_WATERSHED_GROUPS_POLY",
               "WATERSHED_GROUP_ID=161")
bcmw <- wfs_get("WHSE_BASEMAPPING.BC_MAJOR_WATERSHEDS",
                "MAJOR_WATERSHED_SYSTEM LIKE '%kanagan%'")
wsc <- wfs_get("WHSE_IMAGERY_AND_BASE_MAPS.DRP_SUB_SUB_DRAINAGES_1M_SP",
               "SUB_SUB_DRAINAGE_AREA_CD='08NM'")
groups <- wfs_get("WHSE_BASEMAPPING.FWA_WATERSHED_GROUPS_POLY")
prov <- wfs_get("WHSE_LEGAL_ADMIN_BOUNDARIES.ABMS_PROVINCE_SP")

msg("FWA watershed group 161 OKAN   %10.0f ha", ha(fwa))
msg("BC major watershed WA2         %10.0f ha", ha(bcmw))
msg("WSC sub-sub-drainage 08NM      %10.0f ha", ha(wsc))

# --- What BC's major watershed adds ----------------------------------------
# Decomposing WA2 against the Freshwater Atlas groups, rather than eyeballing
# the polygon, is what identifies the extra basin by name.
decompose <- function(target, label) {
  ix <- suppressWarnings(sf::st_intersection(groups, sf::st_union(target)))
  ix$ha <- as.numeric(sf::st_area(ix)) / 1e4
  ix$frac <- ix$ha / groups$AREA_HA[match(ix$WATERSHED_GROUP_ID,
                                          groups$WATERSHED_GROUP_ID)]
  ix <- ix[ix$frac > 0.01, ]
  ix <- ix[order(-ix$ha), ]
  msg("\nFreshwater Atlas groups making up %s:", label)
  for (i in seq_len(nrow(ix)))
    msg("  %-20s %9.0f ha  %5.1f%% of that group",
        ix$WATERSHED_GROUP_NAME[i], ix$ha[i], 100 * ix$frac[i])
  ix
}
wa2_parts <- decompose(bcmw, "BC major watershed WA2 Okanagan River")
nm_parts <- decompose(wsc, "WSC sub-sub-drainage 08NM Okanagan")

# --- Where the federal unit's excess lies ----------------------------------
# 08NM is larger than the Freshwater Atlas group. The question is whether that
# excess is Canadian drainage the provincial group omits, which would matter, or
# the United States portion of the basin, which does not, because the ignition
# record and the fire weather network are both provincial.
resid <- suppressWarnings(sf::st_difference(sf::st_union(wsc), sf::st_union(fwa)))
resid_bc <- suppressWarnings(sf::st_intersection(resid, sf::st_union(prov)))
resid_ha <- ha(resid)
resid_bc_ha <- ha(resid_bc)
msg("\n08NM outside the Freshwater Atlas group: %.0f ha", resid_ha)
msg("  inside British Columbia:  %8.0f ha", resid_bc_ha)
msg("  outside British Columbia: %8.0f ha", resid_ha - resid_bc_ha)

ll <- sf::st_bbox(sf::st_transform(wsc, 4326))
msg("08NM southern limit: %.3f degrees north (the border is 49.000)", ll["ymin"])

# --- Record ----------------------------------------------------------------
similkameen <- wa2_parts$ha[wa2_parts$WATERSHED_GROUP_NAME == "Similkameen River"]
out <- data.frame(
  item = c("fwa_okan_ha", "bcmw_wa2_ha", "wsc_08nm_ha",
           "wa2_similkameen_ha", "nm_outside_fwa_ha", "nm_outside_fwa_in_bc_ha",
           "nm_outside_fwa_outside_bc_ha", "nm_south_limit_deg",
           "agreement_fwa_vs_wsc_in_bc_pct"),
  value = c(round(ha(fwa)), round(ha(bcmw)), round(ha(wsc)),
            round(if (length(similkameen)) similkameen else NA_real_),
            round(resid_ha), round(resid_bc_ha), round(resid_ha - resid_bc_ha),
            round(as.numeric(ll["ymin"]), 3),
            round(100 * resid_bc_ha / ha(fwa), 2)),
  stringsAsFactors = FALSE)
write.csv(out, file.path(derived_dir, "study-area-boundary-candidates.csv"),
          row.names = FALSE)
msg("\nWritten 02.inputs/derived/study-area-boundary-candidates.csv")

# --- The ruling this evidence supports --------------------------------------
# Recorded here so the reasoning sits beside the numbers rather than only in the
# framing document.
#
# BC's major watershed WA2 is the Freshwater Atlas Okanagan group plus the
# Similkameen group. The two are joined in that layer because the Similkameen
# reaches the Okanogan River in Washington State, not because the Similkameen
# drains to Okanagan Lake. It is a separate valley with its own climate and its
# own fire regime, and no ordinary use of "the Okanagan watershed" includes it.
#
# The federal unit 08NM is the whole binational basin. Almost all of its excess
# over the Freshwater Atlas group is south of the international boundary. Within
# Canada the two frameworks describe the same basin, differing by about one per
# cent, which is what a 1:1,000,000 generalisation costs against 1:20,000.
#
# The study area is therefore Freshwater Atlas watershed group 161, OKAN,
# Okanagan River: the Canadian portion of the Okanagan watershed, entire. The
# United States portion is excluded because the ignition record is the BC
# Wildfire Service historical incident layer and the validation weather is the
# BC Fire Weather Network, neither of which crosses the border. That exclusion
# is a stated boundary of the study, not an oversight.
