# Search results

Raw retrievals from the prior-work scoping review. Written by the scripts in
`05.scripts/`, read by the screening step, and **not committed**: the files carry
publisher abstract text, and the repository does not redistribute third-party
literature in any format. What is committed is the search log and the screening
decisions, both under `02.inputs/derived/`.

Everything here regenerates from saved code. Nothing here is hand-edited.

| File | Written by | Contents |
|---|---|---|
| `ads-pass-one-records.csv` | `05.scripts/ads_pass_one_retrieve.py`, 2026-08-14 | 2,010 unique records from pass one, deduplicated by bibcode, with abstracts, keywords, authors and the strings that retrieved each one. |
| `batches/` | `05.scripts/screen_pass_one_prepare.py`, 2026-08-14 | Stage-one screening batches, one per strand, as handed to the screeners. |
| `fulltext-cache/` | `05.scripts/fulltext_pass_one_locate.py`, 2026-08-14 | Raw Crossref and Unpaywall responses for the full-text stage, one JSON file per DOI per registry. |

## Provenance

Source NASA ADS, `https://api.adsabs.harvard.edu/v1/search/query`, queried with
Seamus's personal API token from `~/.ads/dev_key`. Retrieval date 2026-08-14. The
exact queries are in `02.inputs/derived/ads-pass-one-searchlog.csv`.

ADS terms of use permit programmatic access under a personal token for research
use. Abstracts are held locally for screening and are not redistributed.

The full-text cache comes from Crossref, `https://api.crossref.org/works/`, and
Unpaywall, `https://api.unpaywall.org/v2/`, both queried from 2026-08-14 with
Seamus's address in the polite-pool header, which both APIs require and neither
treats as a credential. Both serve openly licensed metadata: Crossref places its
metadata in the public domain and Unpaywall is CC0. The cache is kept because it is
the artefact a bibliographic finding is re-checked against, and it is not committed
only because it is bulky and regenerable, not because it is restricted.
