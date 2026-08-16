#!/usr/bin/env python3
"""Check this project's FWI1987 module against an independent implementation.

Written 2026-08-15. ``05.scripts/fwi1987.py`` is code written for this study, so
no number it produces is reportable until something else produces the same
number. This script runs the first of two checks: the CRAN package ``cffdrs``,
the implementation published with Wang et al. (2017) and maintained by the
Canadian Forest Service, run over the same input through R.

The test input is the Petawawa Research Forest 2007 daily weather that ships
with the NG-CFFDRS repository, used here only because it is a public file with a
known provenance that both implementations can read. The second check, against
the FWI1987 codes BC Wildfire Service computed operationally at the Okanagan
stations, is run inside ``05.scripts/compute_fwi_series.py`` where those codes
are already in hand.

Writes ``02.inputs/derived/fwi1987-validation.csv``, which is committed.

Usage:  python3 05.scripts/validate_fwi1987.py
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import fwi1987  # noqa: E402

R_BIN = "/usr/local/bin/R"

R_SCRIPT = r"""
suppressPackageStartupMessages(library(cffdrs))
inp <- read.csv("{inp}")
inp$long <- -abs(inp$long)
# lat.adjust = FALSE holds the day length tables at Van Wagner's 46 degrees north
# values, which is what the Python module uses and what Canadian operational
# practice applies across the country.
out <- fwi(inp, init = c(ffmc = 85, dmc = 6, dc = 15, lat = inp$lat[1]),
           lat.adjust = FALSE)
write.csv(out[, c("FFMC", "DMC", "DC", "ISI", "BUI", "FWI", "DSR")],
          "{out}", row.names = FALSE)
"""


def main() -> None:
    src = os.path.join(HERE, "vendor", "cffdrs-ng", "PRF2007_daily_wx.csv")
    daily = pd.read_csv(src)

    mine = fwi1987.run(daily.copy())

    with tempfile.TemporaryDirectory() as tmp:
        inp = os.path.join(tmp, "in.csv")
        outp = os.path.join(tmp, "out.csv")
        daily.to_csv(inp, index=False)
        script = os.path.join(tmp, "run.R")
        with open(script, "w") as fh:
            fh.write(R_SCRIPT.format(inp=inp, out=outp))
        res = subprocess.run(
            [R_BIN, "--vanilla", "--quiet", "-f", script],
            capture_output=True,
            text=True,
        )
        if not os.path.exists(outp):
            sys.exit(f"cffdrs run failed:\n{res.stdout}\n{res.stderr}")
        theirs = pd.read_csv(outp)

    rows = []
    for a, b in [("ffmc", "FFMC"), ("dmc", "DMC"), ("dc", "DC"),
                 ("isi", "ISI"), ("bui", "BUI"), ("fwi", "FWI"), ("dsr", "DSR")]:
        x, y = mine[a].to_numpy(float), theirs[b].to_numpy(float)
        rows.append(
            {
                "component": b,
                "n": len(x),
                "max_abs_diff": float(np.nanmax(np.abs(x - y))),
                "mean_abs_diff": float(np.nanmean(np.abs(x - y))),
                "max_value": float(np.nanmax(y)),
            }
        )

    res = pd.DataFrame(rows)
    dest = os.path.join(ROOT, "02.inputs", "derived", "fwi1987-validation.csv")
    res.to_csv(dest, index=False)
    print(res.to_string(index=False))
    print(f"\nWrote {dest}")


if __name__ == "__main__":
    main()
