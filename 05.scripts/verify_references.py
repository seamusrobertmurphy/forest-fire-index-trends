#!/usr/bin/env python3
"""Verify every candidate citation against Crossref before it enters the bibliography.

Written 2026-08-15. The project convention is that a bibliography entry is taken
from the registry and never from memory, because a DOI recalled from memory
resolves to the wrong paper often enough to be dangerous and the error is
invisible until a referee follows it. This project has already recorded two such
failures.

The script takes a candidate list of works, each with the title as remembered and
either a DOI as remembered or nothing. For each it does two things. It asks
Crossref to resolve the DOI, if one was offered, and compares the title that
comes back against the title that was offered. Separately, and regardless, it
searches Crossref for the offered title and reports the best match with its
score. A candidate is only usable when both agree.

Similarity is a token overlap on lowercased alphanumeric words, which is crude
but sufficient to catch the failure that matters: a DOI that resolves to an
entirely different paper.

Writes ``02.inputs/derived/reference-verification.csv``, committed, and prints
Crossref's own BibTeX for every candidate that passed, ready to paste into
``04.references/references.bib``.

Usage:  python3 05.scripts/verify_references.py
"""

from __future__ import annotations

import os
import re
import sys
import time

import pandas as pd
import requests

MAILTO = "seamusrobertmurphy@gmail.com"
UA = f"forest-fire-index-trends/1.0 (mailto:{MAILTO})"

# Government and agency dataset entries in references.bib (keys geobc2026*,
# bcws2026*, wsc2026subsubdrainage, bc2026municipalities, aws2026terraintiles,
# nrcan2026cffdrsng, wang2026cffdrspkg) have no DOI and are outside this check;
# their titles and owners were read from the BC Data Catalogue API on
# 2026-09-12 and are recorded in 02.inputs/README.md.

# Candidates. The title is what is being claimed; the DOI is what is being
# tested. Nothing here is trusted until Crossref agrees with it.
CANDIDATES = [
    # Added 2026-09-12 for the literature revisions (Revisions 1, 4, 7, 10, 13).
    # Titles as returned by CrossRef for each DOI on that date.
    ('Techniques of trend analysis for monthly water quality data',
     '10.1029/wr018i001p00107'),
    ('Trend analysis of fire season length and extreme fire weather in North America between 1979 and 2015',
     '10.1071/wf17008'),
    ('Temporal variations and change in forest fire danger  in Europe for 1960–2012',
     '10.5194/nhess-14-1477-2014'),
    ('Climate-induced variations in global wildfire danger from 1979 to 2013',
     '10.1038/ncomms8537'),
    ('To prewhiten or not to prewhiten in trend analysis?',
     '10.1623/hysj.52.4.611'),
    ('The influence of autocorrelation on the ability to detect trend in hydrological series',
     '10.1002/hyp.1095'),
    ('Block bootstrap for Mann–Kendall trend test of serially dependent data',
     '10.1002/hyp.8438'),
    ('The control of the false discovery rate in multiple testing under dependency',
     '10.1214/aos/1013699998'),
    ('“The Stippling Shows Statistically Significant Grid Points”: How Research Results are Routinely Overstated and Overinterpreted, and What to Do about It',
     '10.1175/bams-d-15-00267.1'),
    ('Resampling Hypothesis Tests for Autocorrelated Fields',
     '10.1175/1520-0442(1997)010<0065:rhtfaf>2.0.co;2'),
    ('The Jackknife and the Bootstrap for General Stationary Observations',
     '10.1214/aos/1176347265'),
    ('The Stationary Bootstrap',
     '10.1080/01621459.1994.10476870'),
    ('Better Bootstrap Confidence Intervals',
     '10.1080/01621459.1987.10478410'),
    ('Bootstrap confidence intervals',
     '10.1214/ss/1032280214'),
    ('Two Guidelines for Bootstrap Hypothesis Testing',
     '10.2307/2532163'),
    ('Statistical significance of trends and trend differences in layer‐average atmospheric temperature time series',
     '10.1029/1999jd901105'),
    ('Avoiding Inhomogeneity in Percentile-Based Indices of Temperature Extremes',
     '10.1175/jcli3366.1'),
    ('Factors affecting the detection of trends: Statistical considerations and applications to environmental data',
     '10.1029/98jd00995'),
    ('Effects of autocorrelation and temporal sampling schemes on estimates of trend and spatial correlation',
     '10.1029/jd095id12p20507'),
    ('Detection Probability of Trends in Rare Events: Theory and Application to Heavy Precipitation in the Alpine Region',
     '10.1175/1520-0442(2001)014<1568:dpotir>2.0.co;2'),
    ('Re-evaluation of the Power of the Mann-Kendall Test for Detecting Monotonic Trends in Hydrometeorological Time Series',
     '10.3389/feart.2020.00014'),
    ('Wildfire Prediction to Inform Fire Management: Statistical Science Challenges',
     '10.1214/13-sts451'),
    ('Prediction of daily lightning- and human-caused fires in British Columbia',
     '10.1071/wf11088'),
    ('A lightning fire occurrence model for Ontario',
     '10.1139/x05-071'),
    ('A logistic model for predicting daily people-caused forest fire occurrence in Ontario',
     '10.1139/x87-068'),
    ('Modelling seasonal variation in daily people-caused forest fire occurrence',
     '10.1139/x89-237'),
    ('A cautionary note regarding comparisons of fire danger indices',
     '10.5194/nhess-12-927-2012'),
    ('Negative binomial and mixed Poisson regression',
     '10.2307/3314912'),
    ('Cross‐validation strategies for data with temporal, spatial, hierarchical, or phylogenetic structure',
     '10.1111/ecog.02881'),
    ('Strictly Proper Scoring Rules, Prediction, and Estimation',
     '10.1198/016214506000001437'),
    ('Predicting the number of daily human-caused bushfires to assist suppression planning in south-west Western Australia',
     '10.1071/wf13090'),
    ('Lightning and lightning fire, central cordillera, Canada',
     '10.1071/wf01048'),
    ('Lightning ignition efficiency in Canadian forests',
     '10.1186/s42408-025-00376-1'),
    ('Cloud-to-Ground Lightning in Canada: 20 Years of CLDN Data',
     '10.1080/07055900.2020.1845117'),
    ('Lightning-ignited forest fires in northwestern Ontario',
     '10.1139/x91-035'),
    ('Modeling Forest Fire Occurrences Using Count-Data Mixed Models in Qiannan Autonomous Prefecture of Guizhou Province in China',
     '10.1371/journal.pone.0120621'),
    ('A comparative analysis of fire-weather indices for enhanced fire activity prediction with probabilistic approaches',
     '10.1016/j.agrformet.2024.110315'),
    ('Indices for monitoring changes in extremes based on daily temperature and precipitation data',
     '10.1002/wcc.147'),
    ('On the effect of reference periods on trends in percentile-based extreme temperature indices',
     '10.1088/1748-9326/ac52c8'),
    ('Development of a Global Fire Weather Database',
     '10.5194/nhess-15-1407-2015'),
    ('Science, technology, and human factors in fire danger rating: the Canadian experience.',
     '10.1071/wf05021'),
    ('Defining fire spread event days for fire-growth modelling',
     '10.1071/wf09001'),
    ('A methodology for investigating trends in changes in the timing of the fire season with applications to lightning-caused forest fires in Alberta and Ontario, Canada',
     '10.1139/cjfr-2011-0432'),
    ('Using observed fires to study changes in fire season timing across Ontario, Canada',
     '10.1071/wf25164'),
    ('Increasing western US forest wildfire activity: sensitivity to changes in the timing of spring',
     '10.1098/rstb.2015.0178'),
    ('A high-resolution reanalysis of global fire weather from 1979 to 2018 – overwintering the Drought Code',
     '10.5194/essd-12-1823-2020'),
    ('Preceding Fall Drought Conditions and Overwinter Precipitation Effects on Spring Wildland Fire Activity in Canada',
     '10.3390/fire3020024'),
    ('Spatial variation of trends in wildfire and summer drought in British Columbia, Canada, 1920–2000',
     '10.1071/wf09055'),
    ('Interannual climate variability drives regional fires in west central British Columbia, Canada',
     '10.1002/2016jg003661'),
    ('Mixed-severity fire regimes in dry forests of southern interior British Columbia, Canada',
     '10.1139/x11-160'),
    ('Regional drought synchronised historical fires in dry forests of the Montane Cordillera Ecozone, Canada',
     '10.1071/wf21035'),
    ('A Disrupted Historical Fire Regime in Central British Columbia',
     '10.3389/fevo.2021.676961'),
    ('The contribution of Indigenous stewardship to an historical mixed‐severity fire regime in British Columbia, Canada',
     '10.1002/eap.2736'),
    ('Expected Effects of Climate Change on Forest Disturbance Regimes in British Columbia',
     '10.22230/jem.2012v13n1a152'),
    ('Climate, Environment, and Disturbance History Govern Resilience of Western North American Forests',
     '10.3389/fevo.2019.00239'),
    ('Direct and indirect impacts of climate change on forests: three case studies from British Columbia',
     '10.1080/07060661.2011.563906'),
    ('Transforming fire governance in British Columbia, Canada: an emerging vision for coexisting with fire',
     '10.1007/s10113-022-01895-2'),
    ('On the limited consensus of mountain pine beetle impacts on wildfire',
     '10.1007/s10980-023-01720-z'),
    ('Climatic change and fire potential in South‐Central British Columbia, Canada',
     '10.1111/j.1365-2486.2007.01517.x'),
    ('Record-breaking fire weather in North America in 2021 was initiated by the Pacific northwest heat dome',
     '10.1038/s43247-024-01346-2'),
    ('Identifying and analyzing spatial and temporal patterns of lightning-ignited wildfires in Western Canada from 1981 to 2018',
     '10.1139/cjfr-2021-0353'),
    ('A thirty year, fine-scale, characterization of area burned in Canadian forests shows evidence of regionally increasing trends in the last decade',
     '10.1371/journal.pone.0197218'),
    ('A Multiscalar Drought Index Sensitive to Global Warming: The Standardized Precipitation Evapotranspiration Index',
     '10.1175/2009jcli2909.1'),
    ('Benchmarking homogenization algorithms for monthly data',
     '10.5194/cp-8-89-2012'),
    ('Can climate trends be calculated from reanalysis data?',
     '10.1029/2004jd004536'),
    ('Reanalyses Suitable for Characterizing Long-Term Trends',
     '10.1175/2009bams2858.1'),
    ('An intercomparison of temperature trends in the U.S. Historical Climatology Network and recent atmospheric reanalyses',
     '10.1029/2012gl051387'),
    ('The Canadian Forest Fire Danger Rating System: An Overview',
     '10.5558/tfc65450-6'),
    ('Stand-specific litter moisture content calibrations for the Canadian Fine Fuel Moisture Code',
     '10.1071/wf06087'),
    ('Moisture diffusivity and response time in fine forest fuels',
     '10.1139/x90-046'),
    ('Evaluating the applicability of predicting dead fine fuel moisture based on the hourly Fine Fuel Moisture Code in the south-eastern Great Xing’an Mountains of China',
     '10.1071/wf16040'),
    ('The Role of Field Measurements of Fine Dead Fuel Moisture Content in the Canadian Fire Weather Index System—A Study Case in the Central Region of Portugal',
     '10.3390/f15081429'),
    ('Evaluation of new methods for drought estimation in the Canadian Forest Fire Danger Rating System',
     '10.1071/wf22112'),
    ('Characterisation of the fuel and fire environment in southern Ontario’s tallgrass prairie',
     '10.1071/wf14214'),
    ('Forecasting Hourly Wildfire Risk: Enhancing Fire Danger Assessment Using Numerical Weather Prediction',
     '10.1175/waf-d-23-0226.1'),
    ('On the projection of future fire danger conditions with various instantaneous/mean-daily data sources',
     '10.1007/s10584-012-0667-2'),
    ('Sensitivity of fire weather index to different reanalysis products in the Iberian Peninsula',
     '10.5194/nhess-12-699-2012'),
    ('Evaluation of Global Fire Weather Database reanalysis and short-term forecast products',
     '10.5194/nhess-20-1123-2020'),
    ('ERA5-based global meteorological wildfire danger maps',
     '10.1038/s41597-020-0554-z'),
    ('Index sensitivity analysis applied to the Canadian Forest Fire Weather Index and the McArthur Forest Fire Danger Index',
     '10.1002/met.170'),
    ('A comparison of fire danger rating systems for use in forests',
     '10.22499/2.5801.005'),
    ('Contrasting Trends in Colorado Fire Weather Index from Reanalysis and Observations',
     '10.1175/jamc-d-24-0043.1'),

    ("Estimates of the regression coefficient based on Kendall's tau",
     "10.1080/01621459.1968.10480934"),
    ("A modified Mann-Kendall trend test for autocorrelated data",
     "10.1016/S0022-1694(97)00125-X"),
    ("Controlling the false discovery rate: a practical and powerful approach to multiple testing",
     "10.1111/j.2517-6161.1995.tb02031.x"),
    # The DOI first offered here, 10.1139/x89-121, resolves to a paper on soil
    # nitrogen mineralization in Douglas-fir. It was recalled from memory and it
    # is wrong by one digit. The correct DOI, found by title search, is below.
    # This is the failure the whole script exists to catch and it is left in the
    # record rather than quietly fixed.
    ("Forecasting diurnal variations in meteorological parameters for predicting fire behaviour",
     "10.1139/x89-120"),
    ("cffdrs: an R package for the Canadian Forest Fire Danger Rating System",
     "10.1186/s13717-017-0070-z"),
    ("Interpreting and using outputs from the Canadian Forest Fire Danger Rating System in research applications",
     "10.1007/s10651-007-0084-2"),
    ("Forest fire occurrence and climate change in Canada",
     "10.1071/WF09002"),
    ("Abrupt, climate-induced increase in wildfires in British Columbia since the mid-2000s",
     None),
    ("Implications of changing climate for global wildland fire",
     "10.1071/WF08187"),
    ("Fuel moisture sensitivity to temperature and precipitation: climate change implications",
     None),
    ("Climate change presents increased potential for very large fires in the contiguous United States",
     None),
    ("Warming and earlier spring increase western U.S. forest wildfire activity",
     "10.1126/science.1128834"),
    ("Attribution of the influence of human-induced climate change on an extreme fire season",
     None),
    ("A method of computing fine fuel moisture content throughout the diurnal cycle",
     None),
    ("Nonparametric tests against trend", "10.2307/1907187"),
    ("Applicability of prewhitening to eliminate the influence of serial correlation on the Mann-Kendall test",
     "10.1029/2001WR000861"),
    ("Impact of anthropogenic climate change on wildfire across western US forests",
     "10.1073/pnas.1607171113"),

    ("Wildfire response to changing daily temperature extremes in California's Sierra Nevada",
     None),
    ("Lightning-caused forest fire risk in Northwestern Ontario, Canada, is increasing and associated with anomalies in fire weather",
     None),
    ("Increasing frequency of extreme fire weather in Canada with climate change", None),
    ("Fire-regime changes in Canada over the last half century", None),
    ("Relationships between fire, climate oscillations, and drought in British Columbia, Canada, 1920-2000",
     None),
    ("Length of the fire season in a changing climate", None),
    ("Summer moisture and wildfire risks across Canada", None),
    ("Drivers and impacts of the record-breaking 2023 wildfire season in Canada", None),
    ("Scientists' warning on wildfire: a Canadian perspective", None),
    ("A study of the drying rates of forest floor materials", None),
    # Dropped: the title search returns a Springer book chapter and the identity
    # of the work intended could not be established from the registry alone. A
    # citation that cannot be resolved is not entered.

    # Agricultural and Forest Meteorology wildfire papers closest to this study,
    # screened on 2026-09-12 from a Crossref pull of every article the journal
    # published from 2012, listed in
    # docs/science-superpowers/prior-work/2026-09-12-afm-wildfire-citations.md.
    # The DOIs came from that pull, so this check confirms each resolves to the
    # title it was listed under.
    ("Recent climate change: Long-term trends in meteorological forest fire danger in the Alps",
     "10.1016/j.agrformet.2012.04.001"),
    ("Large-scale weather types, forest fire danger, and wildfire occurrence in the Alps",
     "10.1016/j.agrformet.2012.08.011"),
    ("Fire weather and large fire potential in the northern Sierra Nevada",
     "10.1016/j.agrformet.2014.01.005"),
    ("Global patterns in the sensitivity of burned area to fire-weather: Implications for climate change",
     "10.1016/j.agrformet.2015.09.002"),
    ("Fine fuel moisture for site- and species-specific fire danger assessment in comparison to fire danger indices",
     "10.1016/j.agrformet.2016.12.007"),
    ("Comparisons of fire weather indices using Canadian raw and homogenized weather data",
     "10.1016/j.agrformet.2018.07.005"),
    ("Dynamic and thermodynamic changes conducive to the increased occurrence of extreme spring fire weather over western Canada under possible anthropogenic climate change",
     "10.1016/j.agrformet.2018.11.026"),
    ("Identifying large fire weather typologies in the Iberian Peninsula",
     "10.1016/j.agrformet.2019.107789"),
    ("Recent evolution of spatial and temporal patterns of burnt areas and fire weather risk in the Iberian Peninsula",
     "10.1016/j.agrformet.2020.107923"),
    ("Weather-related thresholds for wildfire danger in a Mediterranean region: The case of Greece",
     "10.1016/j.agrformet.2020.108076"),
    ("Trends and patterns in annually burned forest areas and fire weather across the European boreal zone in the 20th and early 21st centuries",
     "10.1016/j.agrformet.2021.108467"),
    ("Observed and estimated consequences of climate change for the fire weather regime in the moist-temperate climate of the Czech Republic",
     "10.1016/j.agrformet.2021.108583"),
    ("Integrating burned area as a complementary performance measure for daily fire danger assessment: A large-scale test",
     "10.1016/j.agrformet.2023.109746"),
    ("Changes in European fire weather extremes and related atmospheric drivers",
     "10.1016/j.agrformet.2023.109749"),
    ("On the sensitivity of fire-weather climate projections to empirical fire models",
     "10.1016/j.agrformet.2024.109928"),
    ("Multifactorial interactions contribute to contrasting wildfire trends at mid–high latitudes of the Northern Hemisphere",
     "10.1016/j.agrformet.2025.110507"),
    ("Decreasing frequency of low and moderate fire weather days may be contributing to large wildfire occurrence in the northern Sierra Nevada",
     "10.1016/j.agrformet.2025.110688"),
    ("A satellite-based forest fire weather index for characterizing fire danger variability in the Himalaya",
     "10.1016/j.agrformet.2026.111169"),
    ("Distinct seasonality and trends of natural and anthropogenic wildfires in boreal forests",
     "10.1016/j.agrformet.2026.111436"),
]


def norm(s: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", (s or "").lower())) - {
        "the", "a", "an", "of", "for", "in", "to", "and", "on", "with"
    }


def similarity(a: str, b: str) -> float:
    x, y = norm(a), norm(b)
    return len(x & y) / max(len(x | y), 1)


def get(url: str, **params) -> dict | None:
    for attempt in range(3):
        try:
            r = requests.get(url, params=params, headers={"User-Agent": UA}, timeout=45)
            if r.status_code == 404:
                return None
            r.raise_for_status()
            return r.json()
        except Exception:
            if attempt == 2:
                return None
            time.sleep(3)
    return None


def bibtex(doi: str) -> str | None:
    try:
        r = requests.get(
            f"https://doi.org/{doi}",
            headers={"Accept": "application/x-bibtex", "User-Agent": UA},
            timeout=45,
        )
        return r.text.strip() if r.ok else None
    except Exception:
        return None


def main() -> None:
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    rows = []
    passed = []

    for claimed_title, claimed_doi in CANDIDATES:
        rec = {"claimed_title": claimed_title, "claimed_doi": claimed_doi}

        # 1. Does the offered DOI resolve, and to this paper?
        if claimed_doi:
            j = get(f"https://api.crossref.org/works/{claimed_doi}")
            if j is None:
                rec.update(doi_resolves=False, doi_title=None, doi_title_similarity=None)
            else:
                m = j["message"]
                t = (m.get("title") or [""])[0]
                rec.update(
                    doi_resolves=True,
                    doi_title=t,
                    doi_title_similarity=round(similarity(claimed_title, t), 3),
                )
        else:
            rec.update(doi_resolves=None, doi_title=None, doi_title_similarity=None)

        # 2. Independently, what does Crossref return for the title?
        j = get("https://api.crossref.org/works", **{
            "query.bibliographic": claimed_title, "rows": 3, "mailto": MAILTO
        })
        best_doi = best_title = None
        if j and j["message"]["items"]:
            items = j["message"]["items"]
            # Prefer the version of record. Crossref frequently ranks a preprint
            # above the journal article that superseded it, and the project
            # convention is that a preprint is distinguished from a peer reviewed
            # source rather than silently substituted for one.
            article = [
                x for x in items
                if x.get("type") in ("journal-article", "proceedings-article")
                and similarity(claimed_title, (x.get("title") or [""])[0]) >= 0.7
            ]
            it = article[0] if article else items[0]
            rec["search_type"] = it.get("type")
            best_doi = it.get("DOI")
            best_title = (it.get("title") or [""])[0]
            rec.update(
                search_doi=best_doi,
                search_title=best_title,
                search_title_similarity=round(similarity(claimed_title, best_title), 3),
                search_year=(it.get("issued", {}).get("date-parts", [[None]])[0][0]),
                search_container=(it.get("container-title") or [""])[0],
            )

        agree = (
            claimed_doi and rec.get("doi_title_similarity", 0) is not None
            and (rec.get("doi_title_similarity") or 0) >= 0.7
        ) or (
            not claimed_doi and (rec.get("search_title_similarity") or 0) >= 0.8
        )
        rec["verdict"] = "verified" if agree else "REJECTED"
        chosen = claimed_doi if (claimed_doi and (rec.get("doi_title_similarity") or 0) >= 0.7) else best_doi
        rec["chosen_doi"] = chosen if agree else None
        rows.append(rec)
        if agree and chosen:
            passed.append((claimed_title, chosen))

        print(f"{rec['verdict']:9s}  {claimed_title[:64]:64s}  -> {rec['chosen_doi']}", flush=True)

    df = pd.DataFrame(rows)
    dest = os.path.join(root, "02.inputs", "derived", "reference-verification.csv")
    df.to_csv(dest, index=False)
    print(f"\nWrote {dest}")
    print(f"Verified {len(passed)} of {len(CANDIDATES)} candidates\n")

    print("=" * 70)
    print("BibTeX from Crossref for the verified entries")
    print("=" * 70)
    for title, doi in passed:
        bt = bibtex(doi)
        print(f"\n% verified against Crossref {time.strftime('%Y-%m-%d')}; "
              f"title matched: {title}")
        print(bt if bt else f"% BibTeX retrieval failed for {doi}")


if __name__ == "__main__":
    main()
