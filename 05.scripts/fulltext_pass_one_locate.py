#!/usr/bin/env python3
"""Locate and verify the full text of every record carried to stage two.

Written 2026-08-14. Stage two of screening is assessment against the eligibility
criteria, and it cannot begin on a record that has not been found. This script
does the finding, and does the bibliographic verification the protocol requires
at the same time, because both are DOI lookups and running them together means
one pass over the set rather than two.

For each of the 758 records carried forward it does three things.

**Verifies the record against Crossref.** The protocol's Verification section is
binding: every bibliographic record is taken from Crossref by DOI and not from
memory or from a search-result snippet. The registry response is what enters the
register, not the ADS metadata.

**Checks that the DOI resolves to the paper it claims to.** A DOI that resolves
to a real but unrelated article is the failure mode this project has already
met: two DOIs recalled during drafting resolved to a radar-roughness study and
to "Do Nash values have value?". So the Crossref title is compared with the ADS
title and anything below the match threshold is flagged rather than trusted. The
guard is exercised by `--self-test`, because a guard that cannot fail is not a
guard.

**Finds an obtainable copy.** Unpaywall is queried for a legal open-access
location, arXiv identifiers are read off the ADS bibcode for eprints, and what
is left is marked as needing a route that is not automatic. PRISMA-ScR counts
full text sought and full text unobtainable separately, so the count of records
with no reachable copy is an output of this script and not an afterthought.

Nothing is downloaded here. This writes a register; retrieval reads it.

Outputs:
  02.inputs/derived/fulltext-pass-one-register.csv   committed, the register
  02.inputs/derived/fulltext-pass-one-counts.csv     committed, the stage counts
  02.inputs/searches/fulltext-cache/                 not committed, raw responses

Usage:
  python3 05.scripts/fulltext_pass_one_locate.py --self-test
  python3 05.scripts/fulltext_pass_one_locate.py
  python3 05.scripts/fulltext_pass_one_locate.py --limit 25   # a sighting shot
"""

from __future__ import annotations

import argparse
import csv
import difflib
import json
import pathlib
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

# Crossref's polite pool and Unpaywall both key on a contact address. It is
# Seamus's, it is already public on his commits, and neither API works without
# one.
MAILTO = "seamusrobertmurphy@gmail.com"

# Below this, the Crossref title and the ADS title are not the same paper and
# the record is flagged for hand-checking rather than accepted. Calibrated in
# --self-test against a known-good and a known-bad pair.
TITLE_MATCH_MIN = 0.60

CROSSREF = "https://api.crossref.org/works/"
UNPAYWALL = "https://api.unpaywall.org/v2/"
# Crossref is not the whole DOI system. arXiv, most institutional repositories
# and NCAR register with DataCite, so a Crossref 404 on those DOIs is the wrong
# registry being asked rather than a bad DOI. Checked second, and which registry
# answered is recorded, because "verified" has to name its source.
DATACITE = "https://api.datacite.org/dois/"


class _Failed:
    """The registry could not be reached. Distinct from "the registry said no"."""

    def __repr__(self):
        return "FAILED"

    def __bool__(self):
        return False


FAILED = _Failed()

# Courtesy pause between calls. Crossref's polite pool allows far more than
# this; the review has no deadline and a throttled run that finishes beats a
# fast one that gets the address blocked.
PAUSE = 0.12

FIELDS = [
    "bibcode", "doi", "strands", "ads_doctype", "ads_refereed", "ads_year",
    "ads_title",
    "verify_status", "verify_registry", "title_match",
    "cr_type", "cr_title", "cr_container", "cr_year", "cr_volume", "cr_pages",
    "cr_first_author", "cr_publisher",
    "record_class",
    "oa_is_oa", "oa_status", "oa_host_type", "oa_version", "oa_url",
    "arxiv_id",
    "fulltext_route", "obtainable",
]


def repo_root() -> pathlib.Path:
    here = pathlib.Path(__file__).resolve()
    for cand in [here.parent, *here.parents]:
        if (cand / "02.inputs").is_dir() and (cand / "05.scripts").is_dir():
            return cand
    sys.exit("Not inside the forest-fire-index-trends repository.")


ROOT = repo_root()
SCREENING = ROOT / "02.inputs" / "derived" / "ads-pass-one-screening.csv"
DERIVED = ROOT / "02.inputs" / "derived"
CACHE = ROOT / "02.inputs" / "searches" / "fulltext-cache"


# --- fetching ---------------------------------------------------------------

def fetch(url: str, cache_key: str, cache_dir: pathlib.Path):
    """GET a JSON document, caching it on disk.

    The cache is what makes this script re-runnable. 758 records is roughly
    1,500 API calls; a re-run after a crash or an added column must not repeat
    them, and a cached response is also the artefact a finding can be re-checked
    against later.

    A 404 is cached too, as an explicit null. Not caching it would mean every
    re-run paying again for the records that will never resolve.

    A network failure that survives the retries returns the sentinel FAILED and
    is **not** cached. A transient DNS blip once killed this run at record 12
    and discarded the work; a set this size has to survive one, mark the records
    it could not reach, and let a re-run pick up only those, since every success
    is already on disk. The distinction is the point: a 404 is an answer, an
    unreachable host is not, and caching the second as if it were the first
    would quietly turn a network outage into a bibliographic finding.
    """
    cache_dir.mkdir(parents=True, exist_ok=True)
    safe = re.sub(r"[^A-Za-z0-9._-]", "_", cache_key)[:180]
    path = cache_dir / f"{safe}.json"
    if path.exists():
        return json.loads(path.read_text())

    req = urllib.request.Request(
        url, headers={"User-Agent": f"forest-fire-index-trends/1.0 (mailto:{MAILTO})"}
    )
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                doc = json.load(r)
            path.write_text(json.dumps(doc))
            time.sleep(PAUSE)
            return doc
        except urllib.error.HTTPError as e:
            if e.code in (404, 422):
                path.write_text("null")
                time.sleep(PAUSE)
                return None
            if e.code in (429, 500, 502, 503, 504) and attempt < 3:
                time.sleep(2 ** attempt * 2)
                continue
            return FAILED
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
            if attempt < 3:
                time.sleep(2 ** attempt * 2)
                continue
            return FAILED
    return FAILED


# --- verification -----------------------------------------------------------

def normalise(s: str) -> str:
    """Strip a title to comparable words.

    ADS carries LaTeX and entity markup that Crossref does not, and Crossref
    carries publisher HTML that ADS does not, so a raw string comparison
    reports a mismatch on two records of the same paper.
    """
    s = re.sub(r"<[^>]+>", " ", s or "")
    s = re.sub(r"[${}\\]|&[a-z]+;", " ", s)
    s = re.sub(r"[^a-z0-9 ]", " ", s.lower())
    return " ".join(s.split())


def title_match(a: str, b: str) -> float:
    a, b = normalise(a), normalise(b)
    if not a or not b:
        return 0.0
    return difflib.SequenceMatcher(None, a, b).ratio()


def crossref_record(doi: str):
    url = f"{CROSSREF}{urllib.parse.quote(doi)}?mailto={MAILTO}"
    doc = fetch(url, f"cr_{doi}", CACHE / "crossref")
    if doc is FAILED:
        return FAILED
    return (doc or {}).get("message") if doc else None


def datacite_record(doi: str):
    """Ask the other registry, normalised into the shape Crossref returns.

    DataCite nests everything under attributes and names its fields differently,
    so it is mapped here rather than at the call site: the register has one set
    of `cr_` columns and a `verify_registry` column saying who filled them.
    """
    doc = fetch(f"{DATACITE}{urllib.parse.quote(doi)}", f"dc_{doi}", CACHE / "datacite")
    if doc is FAILED:
        return FAILED
    a = ((doc or {}).get("data") or {}).get("attributes")
    if not a:
        return None
    titles = a.get("titles") or [{}]
    creators = a.get("creators") or [{}]
    c0 = creators[0]
    name = c0.get("name") or ", ".join(
        x for x in [c0.get("familyName", ""), c0.get("givenName", "")] if x)
    types = a.get("types") or {}
    return {
        "title": [titles[0].get("title", "")],
        "type": (types.get("resourceTypeGeneral") or "").lower(),
        "container-title": [a.get("publisher") or ""],
        "issued": {"date-parts": [[a.get("publicationYear") or ""]]},
        "volume": "", "page": "",
        "author": [{"family": name, "given": ""}],
        "publisher": a.get("publisher") or "",
    }


# DataCite's vocabulary for what a thing is, mapped onto the eligibility classes.
DC_CLASS = {
    "text": "", "preprint": "preprint", "dissertation": "thesis",
    "report": "report", "conferencepaper": "conference", "journalarticle": "article",
}


def repair_doi(doi: str) -> str:
    """Put back what the upstream metadata dropped.

    Legacy Ecological Society and AMS DOIs end `...2.0.CO;2`. ADS stores them
    with the semicolon stripped, which resolves nowhere. Only tried after the
    DOI as given has already failed, so a working DOI is never rewritten.
    """
    m = re.search(r"(\d\.\d)\.CO2$", doi)
    return doi[: m.start()] + m.group(1) + ".CO;2" if m else ""


def unpaywall_record(doi: str):
    url = f"{UNPAYWALL}{urllib.parse.quote(doi)}?email={MAILTO}"
    return fetch(url, f"up_{doi}", CACHE / "unpaywall")


# --- classification ---------------------------------------------------------

# The eligibility criteria admit four record classes and the charting table
# groups on this, so it is derived once, here, from the registry type where
# Crossref supplies one and from the ADS doctype otherwise.
CR_CLASS = {
    "journal-article": "article",
    "proceedings-article": "conference",
    "posted-content": "preprint",
    "report": "report",
    "report-component": "report",
    "book-chapter": "chapter",
    "book": "book",
    "dissertation": "thesis",
    "monograph": "book",
}
ADS_CLASS = {
    "article": "article",
    "eprint": "preprint",
    "inproceedings": "conference",
    "inbook": "chapter",
    "techreport": "report",
    "phdthesis": "thesis",
    "mastersthesis": "thesis",
    "book": "book",
}


def classify(cr_type: str, ads_doctype: str, refereed: str) -> str:
    """Name the record class the eligibility criteria will be applied to.

    Theses became an admitted class on Seamus's ruling of 2026-08-14 and carry
    a flag, exactly as preprints do. That flag is this column, which is why it
    is computed rather than left implicit in the ADS doctype.
    """
    cls = (CR_CLASS.get(cr_type or "") or DC_CLASS.get(cr_type or "")
           or ADS_CLASS.get(ads_doctype or "") or "other")
    # A Crossref "journal-article" that ADS holds as an eprint is a preprint
    # that has since been published; the published version is the citable one.
    if cls == "article" and str(refereed).lower() == "false" and ads_doctype == "eprint":
        cls = "preprint"
    return cls


ARXIV_BIBCODE = re.compile(r"^\d{4}arXiv(\d{4})(\d{4,5})")
ARXIV_DOI = re.compile(r"^10\.48550/arXiv\.(.+)$", re.I)


def arxiv_id(bibcode: str, doi: str = "") -> str:
    """Read an arXiv identifier off an ADS bibcode, or off the DOI.

    ADS encodes it in the bibcode: 2023arXiv230112345X is arXiv:2301.12345.
    Identifiers issued before 2015 have four digits after the dot rather than
    five, so the pattern has to admit both; requiring five silently missed every
    pre-2015 preprint, which is most of the statistics literature in S1.

    The DOI is the second route. arXiv mints 10.48550/arXiv.NNNN.NNNNN, which is
    unambiguous when the bibcode is a published-version one.
    """
    m = ARXIV_BIBCODE.match(bibcode or "")
    if m:
        return f"{m.group(1)}.{m.group(2)}"
    m = ARXIV_DOI.match((doi or "").strip())
    return m.group(1) if m else ""


def route(oa: dict | None, arx: str, doi: str) -> tuple[str, str]:
    """Decide how this record's full text will be obtained, and whether it can be.

    "request" is not a failure: it means the copy exists but no automatic legal
    route reaches it, and it goes to the institutional or interlibrary route by
    hand. Only records with nothing to request are unobtainable, and those are
    the ones PRISMA-ScR wants counted.
    """
    if oa and oa.get("is_oa") and (oa.get("best_oa_location") or {}).get("url"):
        return "open access", "yes"
    if arx:
        return "arxiv", "yes"
    if doi:
        return "request", "unknown"
    return "hand entry", "unknown"


# --- the run ----------------------------------------------------------------

def load_included() -> list[dict]:
    if not SCREENING.exists():
        sys.exit(f"Screening sheet not found: {SCREENING}")
    with SCREENING.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    inc = [r for r in rows if r["screen_decision"] == "include"]
    if not inc:
        sys.exit("No included records. Has stage-one screening been merged?")
    return inc


def build(limit: int | None = None) -> list[dict]:
    inc = load_included()
    total = len(inc)
    print(f"Records carried to full text: {total}")
    if limit:
        inc = inc[:limit]
        print(f"Limited to the first {limit} for this run.")

    out = []
    for i, r in enumerate(inc, 1):
        doi = (r.get("doi") or "").strip()
        arx = arxiv_id(r["bibcode"], doi)
        rec = {k: "" for k in FIELDS}
        rec.update(
            bibcode=r["bibcode"], doi=doi, strands=r.get("strands", ""),
            ads_doctype=r.get("doctype", ""), ads_refereed=r.get("refereed", ""),
            ads_year=r.get("year", ""), ads_title=r.get("title", ""),
            arxiv_id=arx,
        )

        cr = crossref_record(doi) if doi else None
        registry = "crossref" if cr and cr is not FAILED else ""

        # Crossref first, DataCite second, and only then a repaired DOI. Each
        # step runs only because the one before it came back empty, so a record
        # that resolved cleanly is never touched by the repair path.
        if doi and cr is None:
            cr = datacite_record(doi)
            registry = "datacite" if cr and cr is not FAILED else registry
        if doi and cr is None:
            fixed = repair_doi(doi)
            if fixed:
                cr = crossref_record(fixed)
                if cr and cr is not FAILED:
                    registry, rec["doi"] = "crossref, doi repaired", fixed
                    doi = fixed

        rec["verify_registry"] = registry
        if not doi:
            rec["verify_status"] = "no doi, hand entry"
        elif cr is FAILED:
            rec["verify_status"] = "registry unreachable, retry"
        elif cr is None:
            rec["verify_status"] = "doi does not resolve"
        else:
            cr_title = (cr.get("title") or [""])[0]
            m = title_match(rec["ads_title"], cr_title)
            rec["title_match"] = f"{m:.3f}"
            rec["verify_status"] = "verified" if m >= TITLE_MATCH_MIN else "title mismatch"
            issued = (cr.get("issued") or {}).get("date-parts") or [[""]]
            auth = (cr.get("author") or [{}])[0]
            rec.update(
                cr_type=cr.get("type", ""),
                cr_title=cr_title,
                cr_container=(cr.get("container-title") or [""])[0],
                cr_year=str(issued[0][0] or ""),
                cr_volume=cr.get("volume", ""),
                cr_pages=cr.get("page", ""),
                cr_first_author=", ".join(
                    x for x in [auth.get("family", ""), auth.get("given", "")] if x
                ),
                cr_publisher=cr.get("publisher", ""),
            )

        oa = unpaywall_record(doi) if doi else None
        if oa is FAILED:
            oa = None
            rec["oa_status"] = "unreachable, retry"
        elif oa:
            best = oa.get("best_oa_location") or {}
            rec.update(
                oa_is_oa=str(oa.get("is_oa", "")),
                oa_status=oa.get("oa_status", "") or "",
                oa_host_type=best.get("host_type", "") or "",
                oa_version=best.get("version", "") or "",
                oa_url=best.get("url_for_pdf") or best.get("url") or "",
            )

        rec["record_class"] = classify(rec["cr_type"], rec["ads_doctype"],
                                       rec["ads_refereed"])
        rec["fulltext_route"], rec["obtainable"] = route(oa, arx, doi)
        out.append(rec)

        if i % 25 == 0 or i == len(inc):
            print(f"  {i}/{len(inc)}")
    return out


def write(rows: list[dict]) -> None:
    reg = DERIVED / "fulltext-pass-one-register.csv"
    with reg.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    print(f"\nWritten {reg.relative_to(ROOT)}")

    def tally(key):
        c = {}
        for r in rows:
            c[r[key] or "(blank)"] = c.get(r[key] or "(blank)", 0) + 1
        return sorted(c.items(), key=lambda kv: -kv[1])

    counts = [("fulltext_sought", "total", len(rows))]
    for key in ("verify_status", "record_class", "fulltext_route", "obtainable",
                "oa_status"):
        for k, n in tally(key):
            counts.append((key, k, n))
    path = DERIVED / "fulltext-pass-one-counts.csv"
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["measure", "level", "n"])
        w.writerows(counts)
    print(f"Written {path.relative_to(ROOT)}\n")
    for measure, level, n in counts:
        print(f"  {measure:16s} {level:34s} {n:5d}")

    # An unreachable registry is a state to clear, not a result to report. Say
    # so loudly, because the register looks complete either way.
    retry = sum(1 for r in rows if "unreachable" in r["verify_status"]
                or "unreachable" in r["oa_status"])
    if retry:
        print(f"\n  {retry} records were not reached. Re-run to pick up only "
              f"those: every success is cached.")


def self_test() -> None:
    """Exercise the guards on cases whose answers are known in advance.

    The title guard is the one that matters. It is tested on a pair that must
    pass and on the exact pair that failed in this project before: a fire and
    Southern Oscillation paper against "Do Nash values have value?", which is
    what a mis-recalled DOI resolved to.
    """
    same = title_match(
        "Fire-Southern Oscillation Relations in the Southwestern United States",
        "Fire-Southern Oscillation Relations in the Southwestern United States")
    markup = title_match(
        "Trends in the $\\alpha$ component of the Fire Weather Index",
        "Trends in the <i>&alpha;</i> component of the Fire Weather Index")
    wrong = title_match(
        "Fire-Southern Oscillation Relations in the Southwestern United States",
        "Do Nash values have value?")
    print(f"identical titles      {same:.3f}  must be >= {TITLE_MATCH_MIN}")
    print(f"same paper, markup    {markup:.3f}  must be >= {TITLE_MATCH_MIN}")
    print(f"unrelated paper       {wrong:.3f}  must be <  {TITLE_MATCH_MIN}")
    assert same >= TITLE_MATCH_MIN
    assert markup >= TITLE_MATCH_MIN, "markup normalisation is too weak"
    assert wrong < TITLE_MATCH_MIN, "the title guard cannot fail and is worthless"

    assert arxiv_id("2023arXiv230112345X") == "2301.12345"
    assert arxiv_id("2011arXiv11080754X") == "1108.0754", "pre-2015 ids are 4 digits"
    assert arxiv_id("1990Sci...249.1017S") == ""
    assert arxiv_id("1990Sci...249.1017S", "10.48550/arXiv.2104.12306") == "2104.12306"

    # The repair must fire on the malformed legacy form and on nothing else.
    assert repair_doi("10.1890/1540-9295(2004)002[0067:TABAOS]2.0.CO2") == \
        "10.1890/1540-9295(2004)002[0067:TABAOS]2.0.CO;2"
    assert repair_doi("10.1126/science.249.4972.1017") == ""
    assert repair_doi("10.48550/arXiv.2104.12306") == ""
    assert classify("preprint", "eprint", "False") == "preprint"
    assert classify("dissertation", "mastersthesis", "False") == "thesis"
    assert classify("dissertation", "phdthesis", "False") == "thesis"
    assert classify("", "mastersthesis", "False") == "thesis"
    assert classify("journal-article", "eprint", "False") == "preprint"
    assert classify("journal-article", "article", "True") == "article"
    assert route({"is_oa": True, "best_oa_location": {"url": "x"}}, "", "d") == \
        ("open access", "yes")
    assert route({"is_oa": False}, "2301.12345", "d") == ("arxiv", "yes")
    assert route({"is_oa": False}, "", "d") == ("request", "unknown")
    assert route(None, "", "") == ("hand entry", "unknown")

    # FAILED must be falsy, so it never reads as an open-access hit, and must
    # stay distinguishable from None, so an unreachable host is never recorded
    # as a DOI that does not resolve.
    assert not FAILED
    assert FAILED is not None
    assert route(FAILED, "", "d") == ("request", "unknown")
    print("\nAll guards fire. Classification and routing behave as specified.")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test", action="store_true",
                    help="exercise the guards and exit, retrieving nothing")
    ap.add_argument("--limit", type=int, default=None,
                    help="process only the first N records")
    a = ap.parse_args()
    if a.self_test:
        self_test()
        return
    write(build(a.limit))


if __name__ == "__main__":
    main()
