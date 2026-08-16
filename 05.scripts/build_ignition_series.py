#!/usr/bin/env python3
"""Daily ignition counts for the Okanagan basin, split by cause and by size.

Written 2026-08-15. The outcome series for the third objective. Source is the BC
Wildfire Service historical incident record,
``WHSE_LAND_AND_NATURAL_RESOURCE.PROT_HISTORICAL_INCIDENTS_SP``, already clipped
to Freshwater Atlas watershed group 161 by ``05.scripts/fetch_study_area.R`` and
stored in the ``ignitions`` layer of ``02.inputs/spatial/study-area.gpkg``. This
script only counts; it retrieves nothing.

Two threats govern the design and neither is repaired here, because neither can
be. They are made visible instead.

Cause attribution is not stationary. Of the 8,176 incidents in the basin over the
1980 to 2025 seasons, 3,633 carry no recorded cause, and the unattributed share
runs from about five per cent in the 1980s to about sixty-eight per cent in the
2000s. A lightning caused count that falls after 2000 may therefore be recording
a change in how cause was coded rather than a change in ignition. Three response
series are written for that reason: lightning, person, and all causes together.
The all-cause series cannot be affected by cause coding at all, so it is the one
that carries the weight when the three disagree.

Reporting of small fires is not stationary either. Detection improved over the
record, so an apparent rise in ignitions per unit danger is confounded with it.
The control is a minimum size, and the threshold cannot be chosen by looking at
the count series, since that is the outcome. Counts are therefore written at
three fixed sizes, no size limit, one hectare and four hectares, and every
result that uses them is reported at all three. A conclusion that survives only
at one threshold is reported as not surviving.

Writes ``02.inputs/derived/ignitions-daily.csv``, one row per basin-day within
the observed fire season window, and ``02.inputs/derived/ignition-attribution.csv``,
the decade by decade cause attribution table that documents the first threat.

Usage:  python3 05.scripts/build_ignition_series.py
"""

from __future__ import annotations

import os

import geopandas as gpd
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

FIRST_YEAR, LAST_YEAR = 1980, 2025
SIZE_THRESHOLDS = [0.0, 1.0, 4.0]


def main() -> None:
    gpkg = os.path.join(ROOT, "02.inputs", "spatial", "study-area.gpkg")
    ig = gpd.read_file(gpkg, layer="ignitions")

    ig["ignition_date"] = pd.to_datetime(ig["IGNITION_DATE"], errors="coerce")
    ig["size_ha"] = pd.to_numeric(ig["CURRENT_SIZE"], errors="coerce")
    ig["cause"] = ig["FIRE_CAUSE"].fillna("Unknown").astype(str).str.strip()

    # Completeness, before anything is dropped. This is the table that decides
    # what the daily series can be asked. Of the 8,176 incidents in the basin,
    # a substantial minority carry no ignition date at all and so cannot be
    # placed on any day, and the missing date and the missing cause are largely
    # the same records. Both concentrate in the recent decades, which is the
    # opposite of the direction one would guess.
    comp = ig.groupby(ig["FIRE_YEAR"].astype(int)).agg(
        n_incidents=("FIRE_NUMBER", "size"),
        n_dated=("ignition_date", lambda s: int(s.notna().sum())),
        n_caused=("cause", lambda s: int((s != "Unknown").sum())),
        n_sized=("size_ha", lambda s: int(s.notna().sum())),
    )
    comp["pct_dated"] = (100 * comp.n_dated / comp.n_incidents).round(1)
    comp["pct_caused"] = (100 * comp.n_caused / comp.n_incidents).round(1)
    comp.index.name = "year"
    comp.to_csv(os.path.join(ROOT, "02.inputs", "derived", "ignition-completeness.csv"))

    undated = int(ig["ignition_date"].isna().sum())
    undated_unknown = int(
        (ig["ignition_date"].isna() & (ig["cause"] == "Unknown")).sum()
    )

    # A handful of records carry an ignition date in a different season from the
    # fire year they are filed under. The date is the event; the year is the file.
    ig = ig[ig["ignition_date"].notna()].copy()
    ig["year"] = ig["ignition_date"].dt.year
    ig = ig[(ig.year >= FIRST_YEAR) & (ig.year <= LAST_YEAR)].copy()
    ig["date"] = ig["ignition_date"].dt.normalize()

    # The attribution table that documents the cause coding threat.
    ig["decade"] = (ig["year"] // 10) * 10
    att = (
        ig.pivot_table(index="decade", columns="cause", values="FIRE_NUMBER",
                       aggfunc="count", fill_value=0)
        .assign(total=lambda t: t.sum(axis=1))
    )
    for c in ("Lightning", "Person", "Unknown"):
        if c in att.columns:
            att[f"pct_{c.lower()}"] = (100 * att[c] / att["total"]).round(1)
    att.to_csv(os.path.join(ROOT, "02.inputs", "derived", "ignition-attribution.csv"))

    # Daily counts on a complete calendar, so that zero days are zeros and not
    # absences. Restricting to the fire season window is left to the analysis,
    # which does it with the weather derived season, not with a fixed calendar.
    calendar = pd.date_range(f"{FIRST_YEAR}-01-01", f"{LAST_YEAR}-12-31", freq="D")
    out = pd.DataFrame({"date": calendar})

    for thr in SIZE_THRESHOLDS:
        sub = ig[ig["size_ha"].fillna(0.0) >= thr] if thr > 0 else ig
        tag = "all" if thr == 0 else f"ge{int(thr)}ha"
        for cause, label in [("Lightning", "lightning"), ("Person", "person"), (None, "total")]:
            s = sub if cause is None else sub[sub["cause"] == cause]
            counts = s.groupby("date").size()
            out[f"n_{label}_{tag}"] = out["date"].map(counts).fillna(0).astype(int)

    out["year"] = out["date"].dt.year
    out["doy"] = out["date"].dt.dayofyear
    dest = os.path.join(ROOT, "02.inputs", "derived", "ignitions-daily.csv")
    out.to_csv(dest, index=False)

    print(f"Incidents with no ignition date: {undated:,}, of which "
          f"{undated_unknown:,} also carry no cause")
    print(f"Ignitions in window: {len(ig):,}")
    print(f"Size recorded for {ig['size_ha'].notna().sum():,}; "
          f"at least 1 ha {int((ig['size_ha'] >= 1).sum()):,}; "
          f"at least 4 ha {int((ig['size_ha'] >= 4).sum()):,}")
    print("\nCause attribution by decade (per cent):")
    print(att.filter(like="pct_").to_string())
    print(f"\nWrote {dest} with {len(out):,} basin-days")


if __name__ == "__main__":
    main()
