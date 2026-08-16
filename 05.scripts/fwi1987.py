#!/usr/bin/env python3
"""The 1987 Canadian Forest Fire Weather Index System, daily, from the 13:00 observation.

Written 2026-08-15. This is FWI1987 as specified by Van Wagner (1987), Forestry
Technical Report 35, whose equations are the FORTRAN listing of Van Wagner and
Pickett (1985), Forestry Technical Report 33. The two changes FWI2025 makes to
the fire behaviour outputs are deliberately NOT applied here: the Initial Spread
Index uses the original wind function, not the Fire Behaviour Prediction System
limiter, because the point of this module is to reproduce the legacy system that
every published Canadian fire danger trend rests on.

Day length factors are the standard Canadian tables. The Duff Moisture Code
factors Le are Van Wagner's table for 46 degrees north and the Drought Code
factors Lf are his table for the same latitude. Canadian operational practice
applies these tables across the country rather than interpolating by latitude,
and BC Wildfire Service does so at the stations used here, so the same tables are
used rather than a latitude adjustment that the comparison series would not share.

Nothing in this module is original. It exists so that FWI1987 and FWI2025 are
computed inside one process from one weather record, and it is checked twice:
against the CRAN package cffdrs, an independent published implementation, and
against the FWI1987 codes BC Wildfire Service itself computed operationally at
these stations at the time. Both checks are run by
``05.scripts/validate_fwi1987.py`` and their results are reported in the
manuscript rather than asserted here.

References
    Van Wagner, C.E. 1987. Development and structure of the Canadian Forest Fire
        Weather Index System. Forestry Technical Report 35. Canadian Forestry
        Service, Ottawa.
    Van Wagner, C.E.; Pickett, T.L. 1985. Equations and FORTRAN program for the
        Canadian Forest Fire Weather Index System. Forestry Technical Report 33.
        Canadian Forestry Service, Ottawa.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

# Van Wagner (1987) Table 3.1: effective day length for the DMC, 46 degrees north.
DAY_LENGTH_DMC = [6.5, 7.5, 9.0, 12.8, 13.9, 13.9, 12.4, 10.9, 9.4, 8.0, 7.0, 6.0]

# Van Wagner (1987) Table 4.1: day length adjustment for the DC, 46 degrees north.
DAY_LENGTH_DC = [-1.6, -1.6, -1.6, 0.9, 3.8, 5.8, 6.4, 5.0, 2.4, 0.4, -1.6, -1.6]

# The exact coefficient of the FFMC to moisture content transform. Van Wagner
# (1987) prints 147.2; the FORTRAN listing carries 147.2772, which is the value
# that makes the scale close, since 59.5 * 250 / 101 = 147.27722772. The exact
# value is used here because the published implementations use it and a rounded
# constant would put a spurious difference into a version comparison.
FFMC_COEFFICIENT = 147.2772277227723

# Startup values, Van Wagner (1987) section 6, and the defaults the NG-CFFDRS
# reference implementation uses, so the three series start from one point.
FFMC_START = 85.0
DMC_START = 6.0
DC_START = 15.0


def ffmc(temp: float, rh: float, ws: float, prec: float, ffmc_prev: float) -> float:
    """Fine Fuel Moisture Code. Van Wagner (1987) equations 1 to 10."""
    mo = FFMC_COEFFICIENT * (101.0 - ffmc_prev) / (59.5 + ffmc_prev)  # eq 1

    if prec > 0.5:                                                  # eq 2, 3a, 3b
        rf = prec - 0.5
        # Both the test and the second term take the moisture content before the
        # rain is applied, not after it. Van Wagner writes mo on the right hand
        # side of 3b throughout.
        wetting = 42.5 * rf * math.exp(-100.0 / (251.0 - mo)) * (1.0 - math.exp(-6.93 / rf))
        if mo > 150.0:
            wetting += 0.0015 * (mo - 150.0) ** 2 * math.sqrt(rf)
        mo = min(mo + wetting, 250.0)

    ed = (                                                          # eq 4
        0.942 * rh ** 0.679
        + 11.0 * math.exp((rh - 100.0) / 10.0)
        + 0.18 * (21.1 - temp) * (1.0 - math.exp(-0.115 * rh))
    )

    if mo > ed:
        ko = 0.424 * (1.0 - (rh / 100.0) ** 1.7) + 0.0694 * math.sqrt(ws) * (
            1.0 - (rh / 100.0) ** 8
        )                                                           # eq 6a
        kd = ko * 0.581 * math.exp(0.0365 * temp)                    # eq 6b
        m = ed + (mo - ed) * 10.0 ** (-kd)                           # eq 8
    else:
        ew = (                                                       # eq 5
            0.618 * rh ** 0.753
            + 10.0 * math.exp((rh - 100.0) / 10.0)
            + 0.18 * (21.1 - temp) * (1.0 - math.exp(-0.115 * rh))
        )
        if mo < ew:
            kl = 0.424 * (1.0 - ((100.0 - rh) / 100.0) ** 1.7) + 0.0694 * math.sqrt(
                ws
            ) * (1.0 - ((100.0 - rh) / 100.0) ** 8)                  # eq 7a
            kw = kl * 0.581 * math.exp(0.0365 * temp)                # eq 7b
            m = ew - (ew - mo) * 10.0 ** (-kw)                       # eq 9
        else:
            m = mo

    return max(0.0, min(101.0, 59.5 * (250.0 - m) / (FFMC_COEFFICIENT + m)))  # eq 10


def dmc(temp: float, rh: float, prec: float, dmc_prev: float, month: int) -> float:
    """Duff Moisture Code. Van Wagner (1987) equations 11 to 17."""
    p = dmc_prev

    if prec > 1.5:                                                   # eq 11
        re = 0.92 * prec - 1.27
        # eq 12, in the FORTRAN listing's form, 280 / exp(0.023 P), rather than
        # the paper's 20 + exp((244.72 - P) / 43.43). The two agree to about one
        # part in four thousand and the listing is what the published code runs.
        mo = 20.0 + 280.0 / math.exp(0.023 * p)                       # eq 12
        if p <= 33.0:                                                # eq 13a
            b = 100.0 / (0.5 + 0.3 * p)
        elif p <= 65.0:                                              # eq 13b
            b = 14.0 - 1.3 * math.log(p)
        else:                                                        # eq 13c
            b = 6.2 * math.log(p) - 17.2
        mr = mo + 1000.0 * re / (48.77 + b * re)                      # eq 14
        # eq 15, again in the listing's form: 43.43 (5.6348 - ln(Mr - 20)) rather
        # than the paper's 244.72 - 43.43 ln(Mr - 20). 43.43 x 5.6348 = 244.7194.
        p = max(0.0, 43.43 * (5.6348 - math.log(mr - 20.0)))          # eq 15

    if temp > -1.1:                                                   # eq 16
        k = 1.894 * (temp + 1.1) * (100.0 - rh) * DAY_LENGTH_DMC[month - 1] * 1e-6
    else:
        k = 0.0

    return max(0.0, p + 100.0 * k)                                    # eq 17


def dc(temp: float, prec: float, dc_prev: float, month: int) -> float:
    """Drought Code. Van Wagner (1987) equations 18 to 23."""
    d = dc_prev

    if prec > 2.8:                                                    # eq 18
        rd = 0.83 * prec - 1.27
        qo = 800.0 * math.exp(-d / 400.0)                              # eq 19
        qr = qo + 3.937 * rd                                           # eq 20
        d = max(0.0, 400.0 * math.log(800.0 / qr))                     # eq 21

    v = 0.36 * (max(temp, -2.8) + 2.8) + DAY_LENGTH_DC[month - 1]      # eq 22
    v = max(0.0, v)

    return max(0.0, d + 0.5 * v)                                       # eq 23


def isi(ws: float, ffmc_val: float) -> float:
    """Initial Spread Index, the original wind function. Van Wagner (1987) eq 24 to 26.

    FWI2025 replaces the wind function here with the Fire Behaviour Prediction
    System form, which limits the effect of winds above 40 km/h. That change is
    not applied in this module by design.
    """
    m = FFMC_COEFFICIENT * (101.0 - ffmc_val) / (59.5 + ffmc_val)      # eq 1
    fw = math.exp(0.05039 * ws)                                        # eq 24
    ff = 91.9 * math.exp(-0.1386 * m) * (1.0 + m ** 5.31 / 4.93e7)     # eq 25
    return 0.208 * fw * ff                                             # eq 26


def bui(dmc_val: float, dc_val: float) -> float:
    """Buildup Index. Van Wagner (1987) equations 27a and 27b."""
    if dmc_val == 0.0 and dc_val == 0.0:
        return 0.0
    if dmc_val <= 0.4 * dc_val:                                        # eq 27a
        u = 0.8 * dmc_val * dc_val / (dmc_val + 0.4 * dc_val)
    else:                                                              # eq 27b
        u = dmc_val - (1.0 - 0.8 * dc_val / (dmc_val + 0.4 * dc_val)) * (
            0.92 + (0.0114 * dmc_val) ** 1.7
        )
    return max(0.0, u)


def fwi(isi_val: float, bui_val: float) -> float:
    """Fire Weather Index. Van Wagner (1987) equations 28 to 31."""
    if bui_val <= 80.0:                                                # eq 28a
        fd = 0.626 * bui_val ** 0.809 + 2.0
    else:                                                              # eq 28b
        fd = 1000.0 / (25.0 + 108.64 * math.exp(-0.023 * bui_val))
    b = 0.1 * isi_val * fd                                             # eq 29
    if b > 1.0:                                                        # eq 30
        return math.exp(2.72 * (0.434 * math.log(b)) ** 0.647)
    return b                                                           # eq 31


def dsr(fwi_val: float) -> float:
    """Daily Severity Rating. Van Wagner (1987) equation 32."""
    return 0.0272 * fwi_val ** 1.77


def run(
    df: pd.DataFrame,
    ffmc_old: float = FFMC_START,
    dmc_old: float = DMC_START,
    dc_old: float = DC_START,
) -> pd.DataFrame:
    """Run FWI1987 over one station-season of daily 13:00 observations.

    Parameters
    ----------
    df
        Daily weather with columns ``yr``, ``mon``, ``day``, ``temp``, ``rh``,
        ``ws``, ``prec``, in chronological order, one row per day, no gaps.
        Temperature in degrees Celsius, relative humidity in per cent, wind speed
        in kilometres per hour at 10 m, precipitation the 24 hour total in
        millimetres ending at the observation.
    ffmc_old, dmc_old, dc_old
        Startup values carried into the first day.

    Returns
    -------
    The input frame with ``ffmc``, ``dmc``, ``dc``, ``isi``, ``bui``, ``fwi`` and
    ``dsr`` appended.
    """
    out = {k: np.empty(len(df)) for k in ("ffmc", "dmc", "dc", "isi", "bui", "fwi", "dsr")}
    f, p, d = ffmc_old, dmc_old, dc_old

    for i, row in enumerate(df.itertuples(index=False)):
        t, h, w, r, mon = row.temp, row.rh, row.ws, row.prec, int(row.mon)
        # Van Wagner's equations are undefined outside these ranges and the
        # operational convention is to clamp rather than to drop the day.
        h = min(max(h, 0.0), 100.0)
        w = max(w, 0.0)
        r = max(r, 0.0)

        f = ffmc(t, h, w, r, f)
        p = dmc(t, h, r, p, mon)
        d = dc(t, r, d, mon)
        i_ = isi(w, f)
        u = bui(p, d)
        s = fwi(i_, u)

        out["ffmc"][i], out["dmc"][i], out["dc"][i] = f, p, d
        out["isi"][i], out["bui"][i], out["fwi"][i] = i_, u, s
        out["dsr"][i] = dsr(s)

    return df.assign(**out)
