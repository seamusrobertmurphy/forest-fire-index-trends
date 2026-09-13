#!/usr/bin/env Rscript
# ---------------------------------------------------------------------------
# The located study-area figure for the methods section.
#
# Written 2026-08-14. Defines plot_study_area(), which the manuscript calls in a
# visible chunk so the figure is drawn at render time from the GeoPackage that
# 05.scripts/fetch_study_area.R retrieved. Nothing is placed by hand.
#
# What the map may honestly show, and what it may not. The study area and the
# ignition record are settled in the framing document and are drawn as data. The
# weather input is NOT settled: the framing names ERA5-Land as the leading
# candidate pending station validation, and the design gate has not chosen. So
# the map draws the ERA5-Land 0.1 degree cells as a support graticule, labelled
# candidate, and the Fire Weather Network stations that would validate it. It
# does not draw a climate variable, because none has been retrieved and drawing
# one would put a number on the page that no saved code computed.
#
# Sourced, not run: it defines functions and returns a plot.
# ---------------------------------------------------------------------------

# Packages are loaded once by the manuscript setup chunk (easypackages::packages).

# Municipal names arrive in their legal form, "The Corporation of the District
# of Peachland". The map wants the placename.
short_place <- function(x) {
  x <- sub("^The Corporation of the ", "", x)
  x <- sub("^(City|Town|District|Village|Township|Corporation) of ", "", x)
  sub("^District Municipality of ", "", x)
}

# Representative fraction, computed rather than asserted. The map's ground width
# divided by its width on the page, both in metres.
rep_fraction <- function(bbox, panel_width_in) {
  ground_m <- as.numeric(bbox["xmax"] - bbox["xmin"])
  page_m <- panel_width_in * 0.0254
  round(ground_m / page_m / 1000) * 1000
}

plot_study_area <- function(
    gpkg = file.path("02.inputs", "spatial", "study-area.gpkg"),
    dem_path = file.path("02.inputs", "spatial", "dem-z9.tif"),
    panel_width_in = 5.2,
    # The ERA5-Land graticule was drawn when a gridded reanalysis was still a
    # candidate weather source. The weather source is now the station network
    # itself, so the graticule is off by default and the argument is kept only
    # so the earlier figure can still be reproduced.
    show_era5 = FALSE) {

  basin <- sf::st_read(gpkg, "basin", quiet = TRUE)
  ign <- sf::st_read(gpkg, "ignitions", quiet = TRUE)
  lakes <- sf::st_read(gpkg, "lakes", quiet = TRUE)
  streams <- sf::st_read(gpkg, "streams", quiet = TRUE)
  places <- sf::st_read(gpkg, "places", quiet = TRUE)
  stations <- sf::st_read(gpkg, "stations", quiet = TRUE)
  era5 <- sf::st_read(gpkg, "era5_grid", quiet = TRUE)
  prov <- sf::st_read(gpkg, "province", quiet = TRUE)

  # 6 km of margin, enough that a placename on the basin edge is not clipped by
  # the panel: Osoyoos sits within a kilometre of the international boundary.
  bb <- sf::st_bbox(sf::st_buffer(basin, 6000))

  # Relief. Hillshade from the DEM, cropped to the panel and coarsened to keep
  # the embedded figure small; the basin is 102 km wide, so 200 m cells are
  # already finer than the page can resolve.
  dem <- terra::rast(dem_path)
  dem <- terra::crop(dem, terra::ext(bb["xmin"], bb["xmax"],
                                     bb["ymin"], bb["ymax"]))
  dem <- terra::aggregate(dem, fact = 2, fun = "mean")
  hs <- terra::shade(terra::terrain(dem, "slope", unit = "radians"),
                     terra::terrain(dem, "aspect", unit = "radians"),
                     angle = 40, direction = 315)
  hs_df <- as.data.frame(hs, xy = TRUE)
  names(hs_df)[3] <- "shade"

  ign$cause <- ifelse(is.na(ign$FIRE_CAUSE) | ign$FIRE_CAUSE == "",
                      "Unknown", ign$FIRE_CAUSE)
  ign$cause <- factor(ign$cause, levels = c("Lightning", "Person", "Unknown"))
  places$label <- short_place(places$name)

  cause_cols <- c(Lightning = "#0B6E4F", Person = "#B3242B",
                  Unknown = "#8A8A8A")

  # Placenames and lake names go through one repel pass, not two, so that a
  # settlement label and a lake label push each other apart instead of landing
  # on top of one another. Colour, face and size travel as plain vectors, since
  # the colour scale is already carrying ignition cause.
  lake_lab <- lakes[lakes$AREA_HA >= 300, ]
  labels <- rbind(
    data.frame(label = places$label,
               suppressWarnings(sf::st_coordinates(places)),
               col = "grey10", face = "plain", size = 2.5),
    data.frame(label = lake_lab$GNIS_NAME_1,
               suppressWarnings(sf::st_coordinates(
                 sf::st_point_on_surface(sf::st_geometry(lake_lab)))),
               col = "#1F4E79", face = "italic", size = 2.1))

  main <- ggplot() +
    geom_raster(data = hs_df, aes(x, y, alpha = shade), fill = "grey15",
                show.legend = FALSE) +
    scale_alpha(range = c(0.55, 0), guide = "none") +
    {if (show_era5)
       geom_sf(data = era5, aes(linetype = "ERA5-Land 0.1 degree cells, candidate"),
               fill = NA, colour = "grey55", linewidth = 0.15)} +
    geom_sf(data = streams, colour = "#4A7EBB", linewidth = 0.22,
            alpha = 0.8) +
    geom_sf(data = lakes, fill = "#9CC3E5", colour = "#4A7EBB",
            linewidth = 0.2) +
    geom_sf(data = ign, aes(colour = cause), size = 0.55, alpha = 0.55,
            stroke = 0) +
    geom_sf(data = basin, fill = NA, colour = "grey10", linewidth = 0.7) +
    geom_sf(data = stations, aes(shape = "BC Wildfire Service fire weather station"),
            fill = "#F0C808", colour = "grey10", size = 2.1, stroke = 0.4) +
    scale_shape_manual(name = NULL, values = c(24)) +
    scale_linetype_manual(name = NULL, values = c(1)) +
    ggrepel::geom_text_repel(
      data = labels, aes(X, Y, label = label), colour = labels$col,
      fontface = labels$face, size = labels$size, bg.colour = "white",
      bg.r = 0.12, min.segment.length = 0.15, segment.size = 0.18,
      segment.colour = "grey45", max.overlaps = Inf, max.iter = 20000,
      box.padding = 0.28, point.padding = 0.1, seed = 1) +
    scale_colour_manual(values = cause_cols, name = "Ignition cause",
                        drop = FALSE) +
    ggspatial::annotation_scale(location = "bl", width_hint = 0.28,
                                height = unit(0.12, "cm"), text_cex = 0.6,
                                pad_x = unit(0.35, "cm"),
                                pad_y = unit(0.35, "cm")) +
    ggspatial::annotation_north_arrow(
      location = "tr", which_north = "true",
      height = unit(0.9, "cm"), width = unit(0.7, "cm"),
      pad_x = unit(0.3, "cm"), pad_y = unit(0.3, "cm"),
      style = ggspatial::north_arrow_fancy_orienteering(
        text_size = 7, line_width = 0.8)) +
    coord_sf(xlim = c(bb["xmin"], bb["xmax"]),
             ylim = c(bb["ymin"], bb["ymax"]), expand = FALSE,
             crs = sf::st_crs(basin), datum = sf::st_crs(4326)) +
    guides(colour = guide_legend(order = 1,
                                 override.aes = list(size = 2.4, alpha = 1)),
           shape = guide_legend(order = 2,
                                override.aes = list(fill = "#F0C808")),
           linetype = if (show_era5)
             guide_legend(order = 3, override.aes = list(colour = "grey55"))
           else "none") +
    labs(x = NULL, y = NULL) +
    theme_bw(base_size = 8) +
    theme(panel.grid = element_line(colour = "grey85", linewidth = 0.15),
          legend.position = "bottom",
          # Three legends side by side overflow the page width, so they stack.
          legend.box = "vertical",
          legend.box.just = "left",
          legend.key.size = unit(0.4, "cm"),
          legend.text = element_text(size = 7),
          legend.title = element_text(size = 7),
          legend.margin = margin(0, 0, 0, 0),
          legend.spacing.y = unit(0.05, "cm"),
          legend.box.spacing = unit(0.2, "cm"),
          axis.text = element_text(size = 6))

  # Locator inset. The province, with the basin shown filled at its true
  # position rather than as a box, which at this scale is legible.
  inset <- ggplot() +
    geom_sf(data = prov, fill = "grey92", colour = "grey40",
            linewidth = 0.2) +
    geom_sf(data = basin, fill = "#B3242B", colour = "#B3242B",
            linewidth = 0.3) +
    coord_sf(datum = NA, expand = FALSE) +
    theme_void() +
    theme(panel.background = element_rect(fill = "white", colour = "grey30",
                                          linewidth = 0.3))

  rf <- rep_fraction(bb, panel_width_in)
  # Top left: the only quarter of the panel carrying neither the basin nor a
  # placename, so the inset covers nothing.
  list(plot = main + patchwork::inset_element(
         inset, left = 0.005, bottom = 0.82, right = 0.34, top = 0.995,
         align_to = "panel"),
       rf = rf,
       n_ign = nrow(ign),
       n_cause = table(ign$cause),
       n_stations = nrow(stations),
       n_cells = nrow(era5),
       crs = sf::st_crs(basin)$input)
}

# Run directly to write a standalone copy for inspection. The manuscript does
# not read this file; it calls the function and renders the figure itself.
if (sys.nframe() == 0) {
  out <- plot_study_area()
  dir.create(file.path("03.outputs", "figures"), recursive = TRUE,
             showWarnings = FALSE)
  ggplot2::ggsave(file.path("03.outputs", "figures", "fig-study-area.png"),
                  out$plot, width = 6.5, height = 7.4, dpi = 300)
  cat(sprintf("Representative fraction 1:%s at a 5.2 in panel\n",
              format(out$rf, big.mark = ",")))
  cat(sprintf("%d ignitions, %d stations, CRS %s\n",
              out$n_ign, out$n_stations, out$crs))
}
