#!/usr/bin/env Rscript
# ---------------------------------------------------------------------------
# Study area layers for the located methods figure.
#
# Written 2026-08-14. Retrieves every layer the study-area map draws, from the
# BC Data Catalogue WFS and the AWS terrain tiles, and writes them to one
# GeoPackage with a checksum manifest. Nothing is hand-digitised and nothing is
# hand-placed: every feature on the map comes from a named public layer that
# this script fetched, so the figure regenerates from code alone.
#
# Study area. Settled 2026-08-14 by Seamus's ruling that the study area is the
# entire Okanagan watershed as official government data defines it. The framing
# document had named "Freshwater Atlas identifier 212", which is Turnagain River
# in the far north and cannot have been meant.
#
# Three official boundaries carry the name and they disagree by a factor of two.
# 05.scripts/resolve_study_area_boundary.R retrieves and measures all three, and
# writes 02.inputs/derived/study-area-boundary-candidates.csv. Its finding: BC's
# major watershed WA2 "Okanagan River", 1,554,467 ha, is this group plus the
# Similkameen, joined only because the Similkameen reaches the Okanogan River in
# Washington; and the federal Water Survey of Canada sub-sub-drainage 08NM,
# 1,203,045 ha, is the whole binational basin, 402,172 ha of it south of the
# border. Within Canada the federal and provincial frameworks agree to 10,327
# ha, 1.3 per cent.
#
# The study area is therefore WATERSHED_GROUP_ID 161, code OKAN, Okanagan River,
# 795,417 ha: the Canadian portion of the Okanagan watershed, entire. The United
# States portion is excluded because neither the BC Wildfire Service incident
# record nor the BC Fire Weather Network crosses the border, and that exclusion
# is a stated boundary of the study.
#
# Nothing here computes an outcome. It retrieves geometry and counts features.
#
# Usage:  Rscript 05.scripts/fetch_study_area.R
# ---------------------------------------------------------------------------

suppressPackageStartupMessages({
  library(sf)
  library(terra)
})

GROUP_ID <- 161                     # FWA watershed group, Okanagan River
FIRST_YEAR <- 1980                  # Framing: 1980 to 2025 fire seasons
LAST_YEAR <- 2025
CRS_WORK <- 3005                    # NAD83 / BC Albers, metric, per framing

# Run from anywhere: walk up from the working directory to the repository root,
# identified by the folders the layout convention fixes.
root <- normalizePath(".")
while (!all(dir.exists(file.path(root, c("02.inputs", "05.scripts"))))) {
  up <- dirname(root)
  if (up == root) stop("Not inside the forest-fire-index-trends repository.")
  root <- up
}
spatial_dir <- file.path(root, "02.inputs", "spatial")
derived_dir <- file.path(root, "02.inputs", "derived")
dir.create(spatial_dir, recursive = TRUE, showWarnings = FALSE)
gpkg <- file.path(spatial_dir, "study-area.gpkg")

WFS <- "https://openmaps.gov.bc.ca/geo/pub/wfs"

# The service caps a response at 10,000 features, so every call pages by
# startIndex until a page comes back short. A silent truncation here would put
# the wrong ignition count on the figure, which is exactly the kind of number
# that never gets questioned once it is drawn.
wfs_get <- function(layer, cql = NULL, page = 5000) {
  out <- list()
  start <- 0
  repeat {
    q <- c(service = "WFS", version = "2.0.0", request = "GetFeature",
           typeName = layer, outputFormat = "application/json",
           srsName = paste0("EPSG:", CRS_WORK), count = page,
           startIndex = start)
    url <- paste0(WFS, "?", paste0(names(q), "=", vapply(q, utils::URLencode,
                                                         "", reserved = TRUE),
                                   collapse = "&"))
    if (!is.null(cql))
      url <- paste0(url, "&CQL_FILTER=", utils::URLencode(cql, reserved = TRUE))
    got <- sf::st_read(url, quiet = TRUE)
    out[[length(out) + 1]] <- got
    if (nrow(got) < page) break
    start <- start + page
  }
  do.call(rbind, out)
}

msg <- function(...) cat(sprintf(...), "\n")

# --- Basin -----------------------------------------------------------------
basin <- wfs_get("WHSE_BASEMAPPING.FWA_WATERSHED_GROUPS_POLY",
                 sprintf("WATERSHED_GROUP_ID=%d", GROUP_ID))
stopifnot(nrow(basin) == 1)
msg("Basin: %s (%s), %.0f ha", basin$WATERSHED_GROUP_NAME,
    basin$WATERSHED_GROUP_CODE, basin$AREA_HA)
bb <- sf::st_bbox(basin)
bbox_cql <- sprintf("BBOX(SHAPE,%f,%f,%f,%f,'EPSG:%d')",
                    bb["xmin"], bb["ymin"], bb["xmax"], bb["ymax"], CRS_WORK)

# --- Ignitions -------------------------------------------------------------
# Retrieved on the bounding box, then clipped to the basin polygon, because the
# WFS spatial filter is a rectangle. The clip is what the count reports.
inc <- wfs_get("WHSE_LAND_AND_NATURAL_RESOURCE.PROT_HISTORICAL_INCIDENTS_SP",
               sprintf("%s AND FIRE_YEAR>=%d AND FIRE_YEAR<=%d",
                       bbox_cql, FIRST_YEAR, LAST_YEAR))
msg("Incidents in bounding box, %d to %d: %d", FIRST_YEAR, LAST_YEAR, nrow(inc))
inc <- inc[lengths(sf::st_intersects(inc, basin)) > 0, ]
msg("Incidents inside the basin: %d", nrow(inc))

# --- Landscape features ----------------------------------------------------
lakes <- wfs_get("WHSE_BASEMAPPING.FWA_LAKES_POLY",
                 sprintf("WATERSHED_GROUP_ID=%d AND AREA_HA>100", GROUP_ID))
lakes <- lakes[lengths(sf::st_intersects(lakes, basin)) > 0, ]
msg("Lakes over 100 ha: %d, of which named: %d", nrow(lakes),
    sum(!is.na(lakes$GNIS_NAME_1)))

streams <- wfs_get("WHSE_BASEMAPPING.FWA_STREAM_NETWORKS_SP",
                   sprintf("WATERSHED_GROUP_ID=%d AND STREAM_ORDER>=5",
                           GROUP_ID))
msg("Stream segments of order 5 or greater: %d", nrow(streams))

# --- Placenames ------------------------------------------------------------
# Municipal boundaries carry the authoritative name; the label goes on the
# centroid. BCGN geographical names is not served on this endpoint.
munis <- wfs_get("WHSE_LEGAL_ADMIN_BOUNDARIES.ABMS_MUNICIPALITIES_SP",
                 bbox_cql)
munis <- munis[lengths(sf::st_intersects(munis, basin)) > 0, ]
places <- sf::st_centroid(sf::st_geometry(munis))
places <- sf::st_sf(name = munis$ADMIN_AREA_NAME,
                    type = munis$ADMIN_AREA_BOUNDARY_TYPE,
                    geometry = places)
msg("Municipalities intersecting the basin: %d", nrow(places))

# --- Weather ---------------------------------------------------------------
# BC Fire Weather Network stations. The framing names these as the validation
# source for whatever gridded product is adopted at the design gate.
stations <- wfs_get("WHSE_LAND_AND_NATURAL_RESOURCE.PROT_WEATHER_STATIONS_SP",
                    bbox_cql)
stations <- stations[lengths(sf::st_intersects(stations, basin)) > 0, ]
msg("Fire weather stations inside the basin: %d", nrow(stations))

# ERA5-Land grid, the leading candidate weather input. Its cells are a fixed
# 0.1 degree geographic graticule, so the geometry is constructed rather than
# downloaded: drawing it states the support at which a candidate climate input
# would be resolved, which is the point of putting it on a methods map. No
# ERA5-Land values are retrieved, because the weather source is not settled.
b_ll <- sf::st_bbox(sf::st_transform(basin, 4326))
gx <- seq(floor(b_ll["xmin"] * 10) / 10, ceiling(b_ll["xmax"] * 10) / 10, 0.1)
gy <- seq(floor(b_ll["ymin"] * 10) / 10, ceiling(b_ll["ymax"] * 10) / 10, 0.1)
era5 <- sf::st_as_sf(sf::st_make_grid(
  sf::st_as_sfc(sf::st_bbox(c(xmin = min(gx), ymin = min(gy),
                              xmax = max(gx), ymax = max(gy)),
                            crs = 4326)),
  cellsize = 0.1, offset = c(min(gx), min(gy))))
names(era5)[1] <- "geometry"
sf::st_geometry(era5) <- "geometry"
era5 <- sf::st_transform(era5, CRS_WORK)
era5 <- era5[lengths(sf::st_intersects(era5, basin)) > 0, ]
msg("ERA5-Land 0.1 degree cells intersecting the basin: %d", nrow(era5))

# --- Province, for the inset -----------------------------------------------
prov <- wfs_get("WHSE_LEGAL_ADMIN_BOUNDARIES.ABMS_PROVINCE_SP")
msg("Province polygons: %d", nrow(prov))

# --- Terrain ---------------------------------------------------------------
# Landscape relief. AWS terrain tiles via elevatr, zoom 9, roughly 300 m in
# these latitudes, which is enough for a hillshade at page scale and small
# enough to keep on an 8 GB machine.
dem_path <- file.path(spatial_dir, "dem-z9.tif")
if (!file.exists(dem_path)) {
  dem <- elevatr::get_elev_raster(
    locations = sf::st_as_sf(sf::st_as_sfc(sf::st_bbox(
      sf::st_buffer(basin, 5000)))),
    z = 9, clip = "bbox", prj = sf::st_crs(basin)$wkt)
  terra::writeRaster(terra::rast(dem), dem_path, overwrite = TRUE)
}
dem <- terra::rast(dem_path)
msg("DEM: %d by %d cells, %.0f m resolution, elevation %.0f to %.0f m",
    nrow(dem), ncol(dem), terra::res(dem)[1],
    terra::global(dem, "min", na.rm = TRUE)[1, 1],
    terra::global(dem, "max", na.rm = TRUE)[1, 1])

# --- Write -----------------------------------------------------------------
if (file.exists(gpkg)) file.remove(gpkg)
w <- function(x, layer) sf::st_write(x, gpkg, layer, quiet = TRUE, append = FALSE)
w(basin, "basin"); w(inc, "ignitions"); w(lakes, "lakes"); w(streams, "streams")
w(places, "places"); w(stations, "stations"); w(era5, "era5_grid")
w(prov, "province")
msg("\nWritten %s", gpkg)

# --- Counts the manuscript cites -------------------------------------------
# Written to derived/ and committed, because the prose quotes them and no number
# may be quoted from code that was not saved.
cause <- as.character(inc$FIRE_CAUSE)
cause[is.na(cause) | cause == ""] <- "Unknown"
counts <- data.frame(
  item = c("watershed_group_id", "watershed_group_name", "basin_area_ha",
           "first_year", "last_year", "n_seasons",
           "ignitions_total", sprintf("ignitions_%s", sort(unique(cause))),
           "fire_weather_stations", "era5_land_cells",
           "dem_min_elev_m", "dem_max_elev_m"),
  value = c(GROUP_ID, basin$WATERSHED_GROUP_NAME, round(basin$AREA_HA),
            FIRST_YEAR, LAST_YEAR, LAST_YEAR - FIRST_YEAR + 1,
            nrow(inc), as.integer(table(cause)[sort(unique(cause))]),
            nrow(stations), nrow(era5),
            round(terra::global(dem, "min", na.rm = TRUE)[1, 1]),
            round(terra::global(dem, "max", na.rm = TRUE)[1, 1])),
  stringsAsFactors = FALSE)
write.csv(counts, file.path(derived_dir, "study-area-counts.csv"),
          row.names = FALSE)

# Per-season ignition counts by cause, so the figure's inset series and any
# prose about the record come from one saved file.
season <- data.frame(year = inc$FIRE_YEAR, cause = cause)
tab <- as.data.frame(table(season$year, season$cause))
names(tab) <- c("fire_year", "fire_cause", "n")
tab$fire_year <- as.integer(as.character(tab$fire_year))
write.csv(tab[order(tab$fire_year, tab$fire_cause), ],
          file.path(derived_dir, "ignitions-by-season.csv"), row.names = FALSE)

msg("Written %s and %s", "02.inputs/derived/study-area-counts.csv",
    "02.inputs/derived/ignitions-by-season.csv")

# --- Integrity manifest ----------------------------------------------------
files <- list.files(spatial_dir, full.names = TRUE, pattern = "[.](gpkg|tif)$")
sums <- vapply(files, function(f) as.character(tools::md5sum(f)), "")
writeLines(sprintf("%s  %s", sums, basename(files)),
           file.path(spatial_dir, "MD5SUMS.txt"))
msg("Retrieved %s. No outcome variable computed.", format(Sys.Date()))
