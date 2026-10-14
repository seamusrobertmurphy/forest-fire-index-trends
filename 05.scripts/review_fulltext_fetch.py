"""Fetch open-access full texts for the included records of the 2026-10-13 literature review.

For every row of 02.inputs/derived/review-records.csv with decision include and a DOI, asks
OpenAlex for the work's best open-access location and downloads the PDF into
04.references/literature/review/, which is not committed. Writes one row per record to
02.inputs/derived/review-fulltext-log.csv with the route and the outcome, so the count of
records whose full text could not be obtained is measured rather than estimated. Downloaded
files are untrusted data and nothing is executed from that folder. Run from the repository
root with python3 -I.
"""
import csv, json, os, re, time, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TABLE = os.path.join(ROOT, "02.inputs", "derived", "review-records.csv")
LOG = os.path.join(ROOT, "02.inputs", "derived", "review-fulltext-log.csv")
OUT = os.path.join(ROOT, "04.references", "literature", "review")
MAILTO = "seamusrobertmurphy@gmail.com"
UA = "forest-fire-index-trends review fetch (mailto:" + MAILTO + ")"

def get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)

def download(url, path):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/pdf"})
    with urllib.request.urlopen(req, timeout=90) as r:
        data = r.read()
    if not data.startswith(b"%PDF"):
        return "not a pdf"
    with open(path, "wb") as f:
        f.write(data)
    return "saved"

def main():
    os.makedirs(OUT, exist_ok=True)
    with open(TABLE, encoding="utf-8", newline="") as f:
        rows = [r for r in csv.DictReader(f) if r["decision"] == "include" and r["doi"]]
    done = {}
    if os.path.exists(LOG):
        with open(LOG, encoding="utf-8", newline="") as f:
            done = {r["doi"]: r for r in csv.DictReader(f)}
    log = list(done.values())
    for r in rows:
        if r["doi"] in done and done[r["doi"]]["status"] == "saved":
            continue
        name = re.sub(r"[^A-Za-z0-9._-]", "_", r["doi"]) + ".pdf"
        path = os.path.join(OUT, name)
        status, url = "", ""
        if os.path.exists(path):
            status = "saved"
        else:
            try:
                # OpenAlex works endpoint, https://docs.openalex.org/api-entities/works
                w = get_json("https://api.openalex.org/works/https://doi.org/" + urllib.parse.quote(r["doi"]) + "?mailto=" + MAILTO)
                loc = w.get("best_oa_location") or {}
                url = loc.get("pdf_url") or (w.get("open_access") or {}).get("oa_url") or ""
                if not url:
                    status = "no open copy"
                else:
                    try:
                        status = download(url, path)
                    except Exception as e:
                        status = "download failed " + str(e)[:80]
            except Exception as e:
                status = "openalex failed " + str(e)[:80]
            time.sleep(0.3)
        done[r["doi"]] = {"id": r["id"], "doi": r["doi"], "year": r["year"], "title": r["title"][:120], "url": url, "file": name if status == "saved" else "", "status": status, "date": time.strftime("%Y-%m-%d")}
    with open(LOG, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["id", "doi", "year", "title", "url", "file", "status", "date"]); w.writeheader(); w.writerows(done.values())
    from collections import Counter
    print(Counter(v["status"][:20] for v in done.values()).most_common())

if __name__ == "__main__":
    main()
