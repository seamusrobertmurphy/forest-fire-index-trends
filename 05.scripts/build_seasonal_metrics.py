#!/usr/bin/env python3
"""Seasonal fire danger metrics, and the daily basin series, from the three series.

Written 2026-08-15. Reads ``02.inputs/derived/fwi-series-daily.csv`` and writes
three tables the manuscript reads directly.

Thresholding is where the second objective lives, so both schemes are built and
neither is preferred here.

    Absolute thresholds are fixed numbers on the index scale, applied unchanged
    to all three series. They are the scheme an agency uses, because a danger
    class is a number in a manual. Three are used. FFMC 91 is taken from
    GLC-X-42 section 4.1, which states that "an FFMC of 91 in FWI1987 should
    correspond to an FFMC of approximately 91 in FWI2025"; counting days above it
    tests that sentence directly. FWI 19 and FWI 30 are the Canadian high and
    extreme class boundaries in common use.

    Relative thresholds are percentiles of each series' own distribution over a
    common reference period, 1991 to 2020, the current World Meteorological
    Organization normal. A day exceeding a series' own 90th percentile means the
    same thing in each series by construction, so a difference in trend under
    relative thresholds cannot be an artefact of the two systems sitting at
    different levels.

    The prediction under test is that the two schemes disagree: that the version
    change widens the upper tail without moving the level, so absolute counts
    diverge and relative counts do not. Agreement under both schemes, or under
    neither, refutes that mechanism. Building both is what makes the hypothesis
    falsifiable, so both are computed here whatever they show.

Reference distributions are per station and per series. Pooling stations would
mix a 492 m valley station with a 1,463 m ridge station, and the percentile would
then describe the network rather than the site.

Outputs, in ``02.inputs/derived``:
    ``seasonal-metrics.csv``      one row per station, season and series.
    ``basin-daily.csv``           basin mean daily danger, for the ignition models.
    ``threshold-percentiles.csv`` where each absolute threshold falls in each
                                  series' own distribution, the direct test of the
                                  comparability claim.

Usage:  python3 05.scripts/build_seasonal_metrics.py
"""

from __future__ import annotations

import os

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DERIVED = os.path.join(ROOT, "02.inputs", "derived")

SERIES = {"s1": "FWI1987, 13:00 observation",
          "s2": "FWI2025, 13:00 observation",
          "s3": "FWI2025, hourly observation"}

REFERENCE = (1991, 2020)      # WMO normal, fixed before any metric was computed
ABSOLUTE = {"ffmc": [91.0], "fwi": [19.0, 30.0]}
PERCENTILES = [90, 95]


def main() -> None:
    daily = pd.read_csv(os.path.join(DERIVED, "fwi-series-daily.csv"), parse_dates=["date"])
    if daily.empty:
        raise SystemExit("fwi-series-daily.csv is empty; run compute_fwi_series.py first")

    rows = []
    pct_rows = []

    for (sid, name), g in daily.groupby(["station_code", "station_name"], sort=True):
        ref = g[(g.year >= REFERENCE[0]) & (g.year <= REFERENCE[1])]

        for s in SERIES:
            fwi_col, ffmc_col = f"{s}_fwi", f"{s}_ffmc"
            if fwi_col not in g.columns:
                continue

            # Relative thresholds from this station's own reference distribution.
            rel = {}
            ref_fwi = ref[fwi_col].dropna()
            for p in PERCENTILES:
                rel[p] = float(np.percentile(ref_fwi, p)) if len(ref_fwi) >= 500 else np.nan

            # Where the absolute thresholds fall in this series' own distribution.
            for comp, cuts in ABSOLUTE.items():
                col = f"{s}_{comp}"
                v = ref[col].dropna()
                for cut in cuts:
                    pct_rows.append({
                        "station_code": sid, "station_name": name, "series": s,
                        "component": comp, "threshold": cut,
                        "reference_n": len(v),
                        "percentile_of_threshold": (
                            float((v < cut).mean() * 100) if len(v) >= 500 else np.nan
                        ),
                        "reference_median": float(v.median()) if len(v) else np.nan,
                    })

            for yr, gy in g.groupby("year"):
                fwi = gy[fwi_col]
                rec = {
                    "station_code": sid, "station_name": name, "series": s, "year": int(yr),
                    "n_days": int(fwi.notna().sum()),
                    "mean_fwi": float(fwi.mean()),
                    "max_fwi": float(fwi.max()),
                    "mean_ffmc": float(gy[ffmc_col].mean()),
                    "peak_bui": float(gy[f"{s}_bui"].max()),
                    "ssr": float(gy[f"{s}_dsr"].sum()),
                    "n_ffmc_ge91": int((gy[ffmc_col] >= 91.0).sum()),
                    "n_fwi_ge19": int((fwi >= 19.0).sum()),
                    "n_fwi_ge30": int((fwi >= 30.0).sum()),
                }
                for p in PERCENTILES:
                    rec[f"n_fwi_p{p}"] = (
                        int((fwi > rel[p]).sum()) if np.isfinite(rel[p]) else np.nan
                    )
                    rec[f"threshold_p{p}"] = rel[p]

                # The two quantities FWI2025 can report and FWI1987 cannot:
                # when peak burning conditions occur and how long the burning
                # window stays open. A capability difference, not a level one.
                if f"{s}_peak_hr" in gy.columns:
                    rec["mean_peak_hr"] = float(gy[f"{s}_peak_hr"].mean())
                    rec["mean_duration"] = float(gy[f"{s}_duration"].mean())
                    rec["n_duration_ge6"] = int((gy[f"{s}_duration"] >= 6).sum())

                # The daily maximum variants, carried as a sensitivity on the
                # choice of daily summary hour.
                mx = f"{s}_fwi_max"
                if mx in gy.columns:
                    rec["mean_fwi_max"] = float(gy[mx].mean())
                    rec["n_fwi_max_ge19"] = int((gy[mx] >= 19.0).sum())
                    rec["n_ffmc_max_ge91"] = int((gy[f"{s}_ffmc_max"] >= 91.0).sum())
                rows.append(rec)

    metrics = pd.DataFrame(rows)
    metrics.to_csv(os.path.join(DERIVED, "seasonal-metrics.csv"), index=False)
    pd.DataFrame(pct_rows).to_csv(
        os.path.join(DERIVED, "threshold-percentiles.csv"), index=False
    )

    # The basin daily series for the ignition models. Averaging across whichever
    # stations happened to report that day would let the basin value jump when a
    # station joins or leaves, which is a change in the network rather than in
    # the weather. The mean is therefore taken over a core set: the stations
    # present in at least 80 per cent of the seasons the analysis keeps.
    #
    # No station is present in every kept season, so a strictly balanced panel
    # would be empty and the 80 per cent rule is the compromise. The residual
    # composition effect is recorded rather than hidden: ``n_stations`` is
    # written alongside every day and enters the ignition models as a covariate.
    # It cannot affect the comparison between series in any case, since all three
    # are averaged over exactly the same stations on exactly the same days.
    kept_years = sorted(daily["year"].unique())
    per_station_years = daily.groupby("station_code")["year"].nunique()
    core = per_station_years[
        per_station_years >= 0.8 * len(kept_years)
    ].index.tolist()
    if not core:
        core = [per_station_years.idxmax()]
    balanced = daily[daily["station_code"].isin(core)]
    cols = [f"{s}_{c}" for s in SERIES for c in ("ffmc", "dmc", "dc", "isi", "bui", "fwi", "dsr")]
    cols = [c for c in cols if c in balanced.columns]
    basin = balanced.groupby("date")[cols].mean().reset_index()
    basin["n_stations"] = balanced.groupby("date")["station_code"].nunique().values
    basin["year"] = basin["date"].dt.year
    basin["doy"] = basin["date"].dt.dayofyear
    basin["core_stations"] = ";".join(map(str, core))
    basin.to_csv(os.path.join(DERIVED, "basin-daily.csv"), index=False)

    print(f"Seasonal metrics: {len(metrics):,} rows, "
          f"{metrics.station_code.nunique()} stations, {metrics.year.nunique()} seasons")
    print(f"Core panel stations ({len(core)} of {len(per_station_years)}): {core}")
    print(f"Basin daily series: {len(basin):,} days")


if __name__ == "__main__":
    main()
