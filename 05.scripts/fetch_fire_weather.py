#!/usr/bin/env python3
"""Retrieve the hourly fire weather record for the Okanagan basin stations.

Written 2026-08-15. Source is the BC Wildfire Service weather data mart, a public
directory published by the BC Ministry of Forests at

    https://www.for.gov.bc.ca/ftp/HPR/external/!publish/BCWS_DATA_MART/

The archive is stored two ways and this script reads both. Seasons 1987 to 2023
are one comma-separated file per year, province wide, named
``<year>/<year>_BCWS_WX_OBS.csv``, the largest of which is roughly 210 MB.
Seasons 2024 onward are one file per calendar day, named ``<year>/<date>.csv``.
Nothing here holds a whole provincial year in memory: each response is streamed
and every row whose station code is not one of the basin stations is dropped as
it arrives.

Station selection is not by bounding box. The five stations are the ones the
BC Data Catalogue layer ``WHSE_LAND_AND_NATURAL_RESOURCE.PROT_WEATHER_STATIONS_SP``
places inside Freshwater Atlas watershed group 161, already clipped to the basin
polygon by ``05.scripts/fetch_study_area.R`` and stored in the ``stations`` layer
of ``02.inputs/spatial/study-area.gpkg``. This script reads that layer rather
than repeating the spatial test, so the two cannot disagree.

The columns kept are the raw hourly observations, the operational FWI1987 codes
that BC Wildfire Service itself computed at the time, and the daily
accumulated precipitation. The operational codes are kept for one purpose: they
are an independent check on this project's own FWI1987 implementation, computed
by a different party with different code, and ``05.scripts/compute_fwi_series.py``
reports the agreement.

Output is written uncompressed to ``02.inputs/weather/bcws-okanagan-hourly.csv``,
which is gitignored for size, together with a small retrieval log at
``02.inputs/derived/fire-weather-retrieval-log.csv`` that is committed.

Usage:  python3 05.scripts/fetch_fire_weather.py [--first 1987] [--last 2025]
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import io
import os
import sys
import time

import requests

BASE = "https://www.for.gov.bc.ca/ftp/HPR/external/!publish/BCWS_DATA_MART"

# Columns carried forward from the data mart. The names are the data mart's own.
KEEP = [
    "STATION_CODE",
    "STATION_NAME",
    "DATE_TIME",
    "HOURLY_PRECIPITATION",
    "HOURLY_TEMPERATURE",
    "HOURLY_RELATIVE_HUMIDITY",
    "HOURLY_WIND_SPEED",
    "HOURLY_WIND_DIRECTION",
    "HOURLY_FINE_FUEL_MOISTURE_CODE",
    "HOURLY_INITIAL_SPREAD_INDEX",
    "HOURLY_FIRE_WEATHER_INDEX",
    "PRECIPITATION",
    "FINE_FUEL_MOISTURE_CODE",
    "DUFF_MOISTURE_CODE",
    "DROUGHT_CODE",
    "INITIAL_SPREAD_INDEX",
    "BUILDUP_INDEX",
    "FIRE_WEATHER_INDEX",
]


def repo_root(start: str) -> str:
    """Walk up to the repository root, identified by the layout convention."""
    root = os.path.abspath(start)
    while not all(os.path.isdir(os.path.join(root, d)) for d in ("02.inputs", "05.scripts")):
        up = os.path.dirname(root)
        if up == root:
            sys.exit("Not inside the forest-fire-index-trends repository.")
        root = up
    return root


def basin_station_codes(root: str) -> dict[str, str]:
    """Station codes inside watershed group 161, read from the study area package."""
    import geopandas as gpd

    gpkg = os.path.join(root, "02.inputs", "spatial", "study-area.gpkg")
    st = gpd.read_file(gpkg, layer="stations")
    return {str(int(c)): str(n) for c, n in zip(st["STATION_CODE"], st["STATION_NAME"])}


def stream_csv(url: str, session: requests.Session, retries: int = 4):
    """Yield dict rows from a remote CSV without holding the file in memory."""
    for attempt in range(retries):
        try:
            with session.get(url, stream=True, timeout=(30, 600)) as r:
                if r.status_code == 404:
                    return
                r.raise_for_status()
                lines = (
                    b.decode("utf-8-sig", errors="replace")
                    for b in r.iter_lines(chunk_size=1 << 20)
                )
                for row in csv.DictReader(lines):
                    yield row
                return
        except Exception as exc:  # network faults are expected over 4 GB of transfer
            if attempt == retries - 1:
                raise
            print(f"    retry {attempt + 1} after {type(exc).__name__}: {exc}", flush=True)
            time.sleep(5 * (attempt + 1))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--first", type=int, default=1987)
    ap.add_argument("--last", type=int, default=2025)
    args = ap.parse_args()

    root = repo_root(os.path.dirname(os.path.abspath(__file__)))
    stations = basin_station_codes(root)
    print("Basin stations:", ", ".join(f"{c} {n}" for c, n in sorted(stations.items())), flush=True)

    out_dir = os.path.join(root, "02.inputs", "weather")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "bcws-okanagan-hourly.csv")
    log_path = os.path.join(root, "02.inputs", "derived", "fire-weather-retrieval-log.csv")

    session = requests.Session()
    session.headers["User-Agent"] = "forest-fire-index-trends/1.0 (research; contact repository owner)"

    log: list[dict] = []
    kept_total = 0

    with open(out_path, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=KEEP, extrasaction="ignore")
        writer.writeheader()

        for year in range(args.first, args.last + 1):
            t0 = time.time()
            kept = 0
            seen = 0

            # Seasons 1987 to 2023: one provincial file per year.
            annual = f"{BASE}/{year}/{year}_BCWS_WX_OBS.csv"
            got_annual = False
            for row in stream_csv(annual, session):
                got_annual = True
                seen += 1
                if str(row.get("STATION_CODE", "")).strip().strip('"') in stations:
                    writer.writerow(row)
                    kept += 1

            # Seasons 2024 onward: one file per calendar day.
            if not got_annual:
                day = dt.date(year, 1, 1)
                end = dt.date(year, 12, 31)
                while day <= end:
                    url = f"{BASE}/{year}/{day.isoformat()}.csv"
                    for row in stream_csv(url, session):
                        seen += 1
                        if str(row.get("STATION_CODE", "")).strip().strip('"') in stations:
                            writer.writerow(row)
                            kept += 1
                    day += dt.timedelta(days=1)

            kept_total += kept
            elapsed = round(time.time() - t0, 1)
            layout = "annual" if got_annual else "daily"
            print(f"{year}  {layout:6s}  rows seen {seen:>9,}  kept {kept:>7,}  {elapsed:>7.1f}s", flush=True)
            log.append(
                {"year": year, "layout": layout, "rows_seen": seen, "rows_kept": kept, "seconds": elapsed}
            )

    with open(log_path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["year", "layout", "rows_seen", "rows_kept", "seconds"])
        w.writeheader()
        w.writerows(log)

    print(f"\nWrote {kept_total:,} hourly observations to {out_path}", flush=True)
    print(f"Retrieval log at {log_path}", flush=True)


if __name__ == "__main__":
    main()
