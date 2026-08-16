#!/usr/bin/env python3
"""Compute the three fire danger series from one Okanagan weather record.

Written 2026-08-15. The design question is that FWI1987 and FWI2025 differ in two
respects at once, the version of the system and the resolution of the weather
driving it, so a two way comparison could not attribute a difference to either.
Three series are computed from a single hourly weather record so that each
contrast moves one thing:

    S1  FWI1987, driven by the daily 13:00 observation.
    S2  FWI2025, driven by the same daily 13:00 observation, pathway C.
    S3  FWI2025, driven by the observed hourly weather, pathway A.

S1 against S2 isolates the version change at fixed input. S2 against S3 isolates
the input resolution change at fixed version. S1 against S3 is the operational
contrast an agency faces and is the sum of the other two.

Weather record
    BC Wildfire Service hourly observations at the five fire weather stations
    inside Freshwater Atlas watershed group 161, retrieved by
    ``05.scripts/fetch_fire_weather.py``. Timestamps are Pacific Standard Time
    year round, which this script does not assume but verifies: the daily
    FWI1987 codes that BC Wildfire Service computed operationally appear in the
    record at hour 12 and at no other hour, and the standard fire weather
    observation is 13:00 Local Daylight Time, so hour 12 is 13:00 LDT and the
    stamp is Local Standard Time, UTC-8.

Season window
    A fixed calendar window, not a weather derived one. The Canadian rule in
    GLC-X-42 section C-2.3, three days above 12 degrees Celsius where snow cover
    cannot be observed, was implemented first and then abandoned, because these
    stations do not report through the winter and the rule fired on whatever day
    a station was switched on. It produced a "season" of three days at Brenda
    Mines in 1991 and 244 days at Fintry in 1999, and those numbers describe
    field operations rather than climate.

    The window is therefore 1 May to 30 September, 153 days, with the calculation
    spun up from 1 April so that thirty days of weather precede the first reported
    day. One consequence is stated rather than repaired: fire season length cannot
    be estimated from a network whose stations are switched on and off for
    operational reasons, so it is not among the metrics, and the seasonal metrics
    that remain are counts and sums over a window of fixed length.

Startup and overwintering
    Each station season starts from FFMC 85, DMC 6, DC 15, the values Van Wagner
    (1987) gives and the NG-CFFDRS reference implementation defaults to. The
    Drought Code is not overwintered. These stations do not report through the
    winter, so an overwintering calculation would have no weather to run on. The
    same startup is used for all three series, so it cannot bias a contrast
    between them.

Daily summary of the hourly series
    FWI1987 produces one value per day. FWI2025 produces one per hour, and
    GLC-X-42 section 3.1.1 says the daily interpretation may be taken either at a
    user selected hour or at the modelled peak. This script writes both. The
    primary daily value is taken at 16:00 LST, which is 17:00 Local Daylight Time,
    the conventional peak burn hour and, in this record, the modal hour of daily
    maximum temperature. The daily maximum over all 24 hours is written alongside
    it as ``*_max``, and is a sensitivity rather than the primary, because the
    maximum of 24 draws exceeds a single daily value for reasons that have
    nothing to do with the version change.

Gaps
    The reference implementation requires a gap free hourly stream. Runs of
    missing temperature, humidity or wind up to 24 hours are filled by linear
    interpolation; missing precipitation is filled with zero, since rain cannot be
    invented. A station season is kept only when at least 95 per cent of the hours
    from 1 April to 30 September were observed and no single gap exceeded 24
    hours. Every drop is recorded in the coverage table rather than being silently
    absorbed.

    Filling a gap with no rain makes a missing wet spell look dry and pushes fire
    danger up. The direction matters and is stated here: coverage is worse in the
    early record than the late, so this bias, where it acts at all, inflates
    danger early and therefore works against an increasing trend rather than for
    one. It is identical across S1, S2 and S3 by construction, since all three run
    on the same filled record, so it cannot move a contrast between versions.

Outputs, all written to ``02.inputs/derived``:
    ``fwi-series-daily.csv``          one row per station-day, the three series.
    ``fwi-station-season-coverage.csv``  what was kept, what was dropped, and why.
    ``fwi1987-operational-check.csv``    S1 against BC Wildfire Service's own codes.

Each station season is independent, because the moisture codes are carried forward
within a season and reset at its start, so nothing crosses the boundary. The work
is therefore split across processes; the hourly loop inside the reference
implementation is pure Python and is the whole cost of this script.

Usage:  python3 05.scripts/compute_fwi_series.py [--jobs N] [--weather PATH]
"""

from __future__ import annotations

import os
import sys
import warnings

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "vendor", "cffdrs-ng"))

import fwi1987  # noqa: E402
from make_minmax import daily_to_minmax  # noqa: E402
from make_hourly import minmax_to_hourly  # noqa: E402
from NG_FWI import hFWI  # noqa: E402
from daily_summaries import generate_daily_summaries  # noqa: E402

warnings.filterwarnings("ignore", category=FutureWarning)

TIMEZONE = -8.0          # Pacific Standard Time, verified below, not assumed
NOON_HOUR = 12           # 13:00 Local Daylight Time, the standard observation
PEAK_HOUR = 16           # 17:00 Local Daylight Time, the conventional peak burn hour

SPINUP_MONTH_DAY = (4, 1)   # calculation starts here, 30 days before reporting
WINDOW_START = (5, 1)       # metrics are reported from here
WINDOW_END = (9, 30)        # to here, 153 days

MAX_GAP_HOURS = 24
MIN_OBSERVED_FRACTION = 0.95

COMPONENTS = ["ffmc", "dmc", "dc", "isi", "bui", "fwi", "dsr"]

# The station season whose hourly output is written out whole for the mechanism
# figure. Penticton RS, station 328, is the longest record in the basin, and 2003
# is the season of the Okanagan Mountain Park fire.
EXAMPLE_SEASON = ("328", 2003)


def load_hourly(path: str | None = None) -> pd.DataFrame:
    """Read the retrieved record and put it into the reference implementation's names."""
    path = path or os.path.join(ROOT, "02.inputs", "weather", "bcws-okanagan-hourly.csv")
    d = pd.read_csv(path, low_memory=False)
    d["DATE_TIME"] = d["DATE_TIME"].astype(str).str.strip().str.strip('"')
    d = d[d["DATE_TIME"].str.len() == 10].copy()

    d["yr"] = d["DATE_TIME"].str[0:4].astype(int)
    d["mon"] = d["DATE_TIME"].str[4:6].astype(int)
    d["day"] = d["DATE_TIME"].str[6:8].astype(int)
    d["hr"] = d["DATE_TIME"].str[8:10].astype(int)

    for src, dst in [
        ("HOURLY_TEMPERATURE", "temp"),
        ("HOURLY_RELATIVE_HUMIDITY", "rh"),
        ("HOURLY_WIND_SPEED", "ws"),
        ("HOURLY_PRECIPITATION", "prec"),
    ]:
        d[dst] = pd.to_numeric(d[src], errors="coerce")

    d["id"] = d["STATION_CODE"].astype(str).str.strip().str.strip('"')
    d["timestamp"] = pd.to_datetime(
        dict(year=d.yr, month=d.mon, day=d.day, hour=d.hr), errors="coerce"
    )
    d = d[d["timestamp"].notna()].copy()
    return d.sort_values(["id", "timestamp"]).reset_index(drop=True)


def verify_timezone(d: pd.DataFrame) -> dict:
    """Confirm that the operational daily codes sit at hour 12 and nowhere else."""
    by_hour = d.groupby("hr")["FINE_FUEL_MOISTURE_CODE"].apply(lambda s: s.notna().sum())
    at_noon = int(by_hour.get(NOON_HOUR, 0))
    elsewhere = int(by_hour.drop(index=NOON_HOUR, errors="ignore").sum())
    if at_noon == 0 or elsewhere > 0:
        sys.exit(
            "Daily codes are not stamped exclusively at hour 12; the timezone "
            f"assumption fails. At hour 12: {at_noon}. At other hours: {elsewhere}."
        )
    summer = d[(d.mon.isin([6, 7, 8])) & d.temp.notna()].copy()
    peak = summer.loc[summer.groupby(["id", "yr", "mon", "day"])["temp"].idxmax(), "hr"]
    return {
        "daily_codes_at_hour_12": at_noon,
        "daily_codes_at_other_hours": elsewhere,
        "modal_hour_of_max_temp_summer": int(peak.mode().iloc[0]),
    }


def quality_control(d: pd.DataFrame) -> pd.DataFrame:
    """Void observations outside the physically possible range for this basin."""
    d.loc[(d.temp < -50) | (d.temp > 50), "temp"] = np.nan
    d.loc[(d.rh < 0) | (d.rh > 100), "rh"] = np.nan
    d.loc[(d.ws < 0) | (d.ws > 200), "ws"] = np.nan
    d.loc[(d.prec < 0) | (d.prec > 200), "prec"] = np.nan
    return d


def window_bounds(year: int) -> tuple[pd.Timestamp, pd.Timestamp, pd.Timestamp]:
    """Spin-up start, reporting start and reporting end for one season."""
    spin = pd.Timestamp(year, *SPINUP_MONTH_DAY)
    start = pd.Timestamp(year, *WINDOW_START)
    end = pd.Timestamp(year, *WINDOW_END)
    return spin, start, end


def fill_gaps(h: pd.DataFrame) -> tuple[pd.DataFrame, int, int]:
    """Reindex to a complete hourly stream and fill short gaps.

    Returns the filled frame, the number of hours filled, and the longest run of
    consecutive filled hours.
    """
    full = pd.date_range(h["timestamp"].min(), h["timestamp"].max(), freq="h")
    h = h.set_index("timestamp").reindex(full)
    h.index.name = "timestamp"

    missing = h[["temp", "rh", "ws"]].isna().any(axis=1)
    n_filled = int(missing.sum())
    longest = 0
    run = 0
    for flag in missing.to_numpy():
        run = run + 1 if flag else 0
        longest = max(longest, run)

    for c in ("temp", "rh", "ws"):
        h[c] = h[c].interpolate(limit_direction="both")
    h["prec"] = h["prec"].fillna(0.0)

    h = h.reset_index()
    h["yr"] = h.timestamp.dt.year
    h["mon"] = h.timestamp.dt.month
    h["day"] = h.timestamp.dt.day
    h["hr"] = h.timestamp.dt.hour
    return h, n_filled, longest


def noon_daily(h: pd.DataFrame) -> pd.DataFrame:
    """The daily 13:00 LDT observation with the preceding 24 hours of rain.

    The 24 hour total is accumulated from the hourly record over the window that
    ends at the observation, which is what the FWI1987 input is defined to be,
    rather than the calendar day total.
    """
    h = h.sort_values("timestamp").reset_index(drop=True)
    # Rolling 24 hour rainfall ending at each hour, inclusive of that hour.
    h = h.set_index("timestamp")
    h["prec24"] = h["prec"].rolling("24h").sum()
    h = h.reset_index()

    noon = h[h.hr == NOON_HOUR].copy()
    noon["prec"] = noon["prec24"]
    noon["date"] = noon["timestamp"].dt.normalize()
    return noon[["id", "lat", "long", "timezone", "yr", "mon", "day", "date",
                 "temp", "rh", "ws", "prec"]].reset_index(drop=True)


def summarise_hourly(res: pd.DataFrame, tag: str) -> pd.DataFrame:
    """Reduce an hourly FWI2025 run to one row per day, three ways.

    The primary daily value is taken at a fixed hour, so that it is one draw and
    not the maximum of 24. The daily maximum is carried alongside as a
    sensitivity. The specification's own daily summary is carried too, because it
    reports two quantities FWI1987 cannot produce at all: the hour at which peak
    burning conditions occur, and the number of hours the burning window stays
    open. Those are a capability difference rather than a level difference and
    they are reported as such.
    """
    res = res.copy()
    res["date"] = pd.to_datetime(dict(year=res.yr, month=res.mon, day=res.day))

    at_peak = res[res.hr == PEAK_HOUR].set_index("date")[COMPONENTS]
    at_peak.columns = [f"{tag}_{c}" for c in COMPONENTS]

    daily_max = res.groupby("date")[COMPONENTS].max()
    daily_max.columns = [f"{tag}_{c}_max" for c in COMPONENTS]

    out = at_peak.join(daily_max, how="outer")

    try:
        rep = generate_daily_summaries(res, silent=True)
        rep["date"] = pd.to_datetime(dict(year=rep.yr, month=rep.mon, day=rep.day))
        rep = rep.set_index("date")[["peak_hr", "duration", "isi_smooth"]]
        rep.columns = [f"{tag}_{c}" for c in rep.columns]
        out = out.join(rep, how="left")
    except Exception as exc:  # the summary is supplementary, not load bearing
        print(f"    daily summaries unavailable for {tag}: {exc}", flush=True)

    return out


def _run_station_season(task):
    """Compute the three series for one station season.

    Returns a tuple of (coverage record, daily output or None, operational check
    rows, example frame or None, progress message). Written as a free function
    taking one argument so that it can be handed to a process pool: the season is
    the natural unit of parallelism, because the moisture codes are carried
    forward within a season and reset at its start, so nothing crosses the
    boundary.
    """
    sid, yr, (lat, lon, name, elev), g = task

    if g is None:
        return ({
            "station_code": sid, "station_name": name, "year": int(yr),
            "elevation_m": elev, "expected_hours": np.nan, "observed_hours": 0,
            "observed_fraction": 0.0, "filled_hours": np.nan,
            "longest_gap_h": np.nan, "status": "station not reporting",
        }, None, [], None, None)

    g = g.sort_values("timestamp")
    spin, wstart, wend = window_bounds(int(yr))
    expected = int((wend + pd.Timedelta(days=1) - spin).total_seconds() // 3600)

    window = g[(g.timestamp >= spin) & (g.timestamp < wend + pd.Timedelta(days=1))].copy()
    # One row per hour: the data mart occasionally repeats a timestamp.
    window = window.drop_duplicates(subset="timestamp", keep="first")
    observed = int(window[["temp", "rh", "ws"]].notna().all(axis=1).sum())

    rec = {
        "station_code": sid,
        "station_name": name,
        "year": int(yr),
        "elevation_m": elev,
        "expected_hours": expected,
        "observed_hours": observed,
        "observed_fraction": round(observed / expected, 4),
    }

    if observed == 0:
        rec.update(status="no data in window", filled_hours=np.nan, longest_gap_h=np.nan)
        return (rec, None, [], None, None)

    # Reindex over the whole spin-up-to-window span, not merely over the hours the
    # station happened to report, so that a station switched on in July counts the
    # preceding months as missing rather than as absent.
    window = window.set_index("timestamp").reindex(
        pd.date_range(spin, wend + pd.Timedelta(hours=23), freq="h")
    ).reset_index(names="timestamp")

    h, n_filled, longest = fill_gaps(window[["timestamp", "temp", "rh", "ws", "prec"]])
    h["id"], h["lat"], h["long"], h["timezone"] = sid, lat, lon, TIMEZONE

    rec.update(filled_hours=n_filled, longest_gap_h=longest)
    if rec["observed_fraction"] < MIN_OBSERVED_FRACTION or longest > MAX_GAP_HOURS:
        rec["status"] = "dropped, coverage"
        return (rec, None, [], None, None)
    rec["status"] = "kept"

    daily = noon_daily(h)
    if len(daily) < 150:
        rec["status"] = "dropped, short season"
        return (rec, None, [], None, None)

    # S1: FWI1987 on the daily 13:00 observation.
    s1 = fwi1987.run(daily.copy())
    s1 = s1.set_index("date")[COMPONENTS]
    s1.columns = [f"s1_{c}" for c in COMPONENTS]

    # S2: FWI2025 pathway C, the same daily observation estimated to hourly.
    d13 = daily[["id", "lat", "long", "timezone", "yr", "mon", "day",
                 "temp", "rh", "ws", "prec"]].copy()
    mm = daily_to_minmax(d13, silent=True)
    hourly_c = minmax_to_hourly(mm, silent=True)
    run_c = hFWI(hourly_c, silent=True)
    s2 = summarise_hourly(run_c, "s2")

    # S3: FWI2025 pathway A, the observed hourly weather.
    hourly_a = h[["id", "lat", "long", "timezone", "yr", "mon", "day", "hr",
                  "temp", "rh", "ws", "prec"]].copy()
    run_a = hFWI(hourly_a, silent=True)
    s3 = summarise_hourly(run_a, "s3")

    # One station season of the hourly runs is kept whole, so that the mechanism
    # figure in the manuscript draws real hourly output rather than an illustration.
    example = None
    if (sid, int(yr)) == EXAMPLE_SEASON:
        ex = run_a[["yr", "mon", "day", "hr", "temp", "rh", "ws", "prec",
                    "ffmc", "isi", "fwi", "sunrise", "sunset"]].copy()
        ex.columns = [c if c in ("yr", "mon", "day", "hr") else f"s3_{c}"
                      for c in ex.columns]
        exc = run_c[["yr", "mon", "day", "hr", "temp", "rh", "ws", "prec",
                     "ffmc", "isi", "fwi"]].copy()
        exc.columns = [c if c in ("yr", "mon", "day", "hr") else f"s2_{c}"
                       for c in exc.columns]
        example = ex.merge(exc, on=["yr", "mon", "day", "hr"], how="inner")

    out = s1.join(s2, how="left").join(s3, how="left")
    # April is spin-up only. The codes it produces are still carrying the startup
    # values and are not reported.
    out = out[(out.index >= wstart) & (out.index <= wend)]
    out.insert(0, "station_code", sid)
    out.insert(1, "station_name", name)
    out.insert(2, "year", int(yr))
    out = out.reset_index()

    # Independent check: BC Wildfire Service's own operational FWI1987 codes.
    checks = []
    ops = g[g.hr == NOON_HOUR][
        ["timestamp", "FINE_FUEL_MOISTURE_CODE", "DUFF_MOISTURE_CODE",
         "DROUGHT_CODE", "INITIAL_SPREAD_INDEX", "BUILDUP_INDEX", "FIRE_WEATHER_INDEX"]
    ].copy()
    ops["date"] = ops["timestamp"].dt.normalize()
    merged = ops.set_index("date").join(s1, how="inner")
    for a, b in [("FINE_FUEL_MOISTURE_CODE", "s1_ffmc"),
                 ("DUFF_MOISTURE_CODE", "s1_dmc"),
                 ("DROUGHT_CODE", "s1_dc"),
                 ("INITIAL_SPREAD_INDEX", "s1_isi"),
                 ("BUILDUP_INDEX", "s1_bui"),
                 ("FIRE_WEATHER_INDEX", "s1_fwi")]:
        x = pd.to_numeric(merged[a], errors="coerce")
        y = merged[b]
        ok = x.notna() & y.notna()
        if ok.sum() >= 20:
            checks.append({
                "station_code": sid, "year": int(yr), "component": a,
                "n": int(ok.sum()),
                "pearson_r": float(np.corrcoef(x[ok], y[ok])[0, 1]),
                "mean_bias": float((y[ok] - x[ok]).mean()),
                "rmse": float(np.sqrt(((y[ok] - x[ok]) ** 2).mean())),
            })

    msg = f"  {name:14s} {yr}  days {len(daily):>3}  filled {n_filled:>3}"
    return (rec, out, checks, example, msg)


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--weather", default=None,
                    help="alternative hourly record, for testing against a partial retrieval")
    ap.add_argument("--jobs", type=int, default=max(1, (os.cpu_count() or 2) - 2),
                    help="parallel worker processes; 1 runs serially")
    args = ap.parse_args()
    jobs = max(1, args.jobs)

    d = load_hourly(args.weather)
    tz_check = verify_timezone(d)
    print("Timezone verification:", tz_check, flush=True)

    d = quality_control(d)

    stations = pd.read_csv(
        os.path.join(ROOT, "02.inputs", "derived", "station-metadata.csv")
    ) if os.path.exists(
        os.path.join(ROOT, "02.inputs", "derived", "station-metadata.csv")
    ) else None
    if stations is None:
        import geopandas as gpd

        st = gpd.read_file(
            os.path.join(ROOT, "02.inputs", "spatial", "study-area.gpkg"), layer="stations"
        )
        stations = st[["STATION_CODE", "STATION_NAME", "LATITUDE", "LONGITUDE", "ELEVATION"]].copy()
        stations["STATION_CODE"] = stations["STATION_CODE"].astype(int).astype(str)
        stations.to_csv(
            os.path.join(ROOT, "02.inputs", "derived", "station-metadata.csv"), index=False
        )
    # The station code is an identifier, not a number. Reading the cached CSV
    # back turns it into an integer and the join against the weather record,
    # whose codes are strings, then silently matches nothing.
    stations["STATION_CODE"] = stations["STATION_CODE"].astype(str).str.strip()
    meta = {
        r.STATION_CODE: (float(r.LATITUDE), float(r.LONGITUDE), r.STATION_NAME, float(r.ELEVATION))
        for r in stations.itertuples()
    }
    if not set(meta) & set(d["id"].unique()):
        sys.exit(f"No station code in the weather record matches the station table: "
                 f"{sorted(meta)} against {sorted(d['id'].unique())}")

    # Enumerate the full station by season grid rather than only the pairs the
    # record happens to contain, so that a season a station did not report at all
    # appears in the coverage table as an absence instead of vanishing from it.
    present = {k: v for k, v in d.groupby(["id", "yr"], sort=True)}
    all_years = range(int(d.yr.min()), int(d.yr.max()) + 1)
    grid = [(sid, yr) for sid in sorted(meta) for yr in all_years]

    tasks = [(sid, int(yr), meta[sid], present.get((sid, yr))) for sid, yr in grid]

    # Each station season is independent: the codes are carried forward within a
    # season and reset at its start, so nothing crosses the boundary and the work
    # parallelises exactly. The hourly loop inside the reference implementation is
    # pure Python and is the whole cost of this script.
    if jobs > 1:
        import multiprocessing as mp

        # imap rather than map, so results stream back and the run reports
        # progress instead of going silent for half an hour.
        pool = mp.get_context("spawn").Pool(jobs)
        results = pool.imap(_run_station_season, tasks, chunksize=1)
    else:
        pool = None
        results = (_run_station_season(t) for t in tasks)

    rows, coverage, op_check = [], [], []
    for rec, out, checks, example, msg in results:
        coverage.append(rec)
        if out is not None:
            rows.append(out)
        op_check.extend(checks)
        if example is not None:
            example.to_csv(
                os.path.join(ROOT, "02.inputs", "derived", "example-season-hourly.csv"),
                index=False,
            )
        if msg:
            print(msg, flush=True)

    if pool is not None:
        pool.close()
        pool.join()

    derived = os.path.join(ROOT, "02.inputs", "derived")
    series = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()
    series.to_csv(os.path.join(derived, "fwi-series-daily.csv"), index=False)
    pd.DataFrame(coverage).to_csv(
        os.path.join(derived, "fwi-station-season-coverage.csv"), index=False
    )
    pd.DataFrame(op_check).to_csv(
        os.path.join(derived, "fwi1987-operational-check.csv"), index=False
    )
    pd.DataFrame([tz_check]).to_csv(
        os.path.join(derived, "timezone-verification.csv"), index=False
    )

    print(f"\nWrote {len(series):,} station-days across "
          f"{series['station_code'].nunique() if len(series) else 0} stations, "
          f"{series['year'].nunique() if len(series) else 0} seasons.")


if __name__ == "__main__":
    main()
