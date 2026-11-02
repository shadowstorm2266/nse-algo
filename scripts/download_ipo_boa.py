"""Download NSE basis-of-allotment adverts for listed mainboard IPOs into data/raw/ipo/nse_boa/.

    uv run python scripts/download_ipo_boa.py

Needs data/raw/ipo/ from scripts/download_ipo.py and scripts/download_bhavcopy.py: the
ISIN and listing date come from the bhavcopy match (nsealgo.data.ipo_build). NSE files
each advert as nsearchives.nseindia.com/corporate/ADV_<ISIN>_<DDMONYYYY>.pdf with no
index, so dates are tried in the order of nsealgo.data.ipo_boa.boa_probe_dates until one
exists. probe_log.json records, per issue, the ISIN, the file found (or none) and every
date tried; an issue already probed under the same ISIN is not probed again. Files are stored byte
for byte; a few are zips of newspaper pages served under the .pdf name.
"""

import json
import time
import urllib.request
from urllib.error import HTTPError

from nsealgo.data.ipo_boa import advert_name, boa_probe_dates
from nsealgo.data.ipo_read import BOA_DIR, read_issues, read_listings
from nsealgo.settings import REPO_ROOT

RAW = REPO_ROOT / "data" / "raw" / "ipo"
URL = "https://nsearchives.nseindia.com/corporate/{name}"
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/130.0 Safari/537.36"
)
PAUSE_SECONDS = 0.4


def _get(url: str, tries: int = 3) -> bytes | None:
    """Body, or None on 404. A body shorter than its Content-Length (seen once: a 4.4 MB
    advert cut at 2.3 MB without an error) is retried."""
    for attempt in range(1, tries + 1):
        try:
            with urllib.request.urlopen(
                urllib.request.Request(url, headers={"User-Agent": UA}), timeout=60
            ) as resp:
                body = resp.read()
                expected = resp.headers.get("Content-Length")
                if expected is not None and len(body) != int(expected):
                    raise OSError(f"{url}: got {len(body)} of {expected} bytes")
                return body
        except HTTPError as err:
            if err.code == 404:
                return None
            if attempt == tries:
                raise
        except OSError:
            if attempt == tries:
                raise
        time.sleep(5 * attempt)
    raise AssertionError("unreachable")


def main() -> None:
    out = RAW / BOA_DIR
    out.mkdir(parents=True, exist_ok=True)
    log_path = out / "probe_log.json"
    log: dict = json.loads(log_path.read_text("utf-8")) if log_path.exists() else {}
    issues = read_issues(RAW)
    listings, _, _ = read_listings(RAW, issues, REPO_ROOT / "data" / "clean" / "ipo" / "_cache")
    listed = issues.merge(listings, on="issue_id").dropna(subset=["listing_date"])
    for _, r in listed.iterrows():
        if log.get(r["issue_id"], {}).get("isin") == r["isin"]:
            continue  # probed already under this ISIN
        entry: dict = {"isin": r["isin"], "found": None, "tried": []}
        for day in boa_probe_dates(r["issue_close"], r["listing_date"]):
            name = advert_name(r["isin"], day)
            entry["tried"].append(day.isoformat())
            body = _get(URL.format(name=name))
            time.sleep(PAUSE_SECONDS)
            if body is not None:
                if not body.startswith((b"%PDF", b"PK\x03\x04")):
                    raise ValueError(f"{name}: neither a PDF nor a zip")
                (out / name).write_bytes(body)
                entry["found"] = name
                break
        log[r["issue_id"]] = entry
        log_path.write_text(json.dumps(log, indent=1, sort_keys=True), encoding="utf-8")
        print(
            f"{r['issue_id']}: {entry['found'] or 'none'} ({len(entry['tried'])} tried)", flush=True
        )


if __name__ == "__main__":
    main()
