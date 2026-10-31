"""Download raw NSE files for the mainboard IPO dataset into data/raw/ipo/.

    uv run python scripts/download_ipo.py lists     # past-issue lists, one per year
    uv run python scripts/download_ipo.py details   # per-issue JSON for every symbol in the lists

Source: www.nseindia.com, the JSON endpoints behind its "Public Issues -> Past Issues"
and "Issue Information" pages (read from the pages' own scripts,
dist/js/sections/live-market/upcoming-ipo.js and issue-information.js):

- /api/public-past-issues?from_date=DD-MM-YYYY&to_date=DD-MM-YYYY&security_type=Equity
  -> nse_past_issues/eq_<year>.json
- /api/ipo-detail?symbol=<SYMBOL>&series=EQ -> nse_ipo_detail/<SYMBOL>.json
  (issue information, consolidated category-wise bids, ISIN and listing date)

Bodies are stored byte for byte. A file that already exists is not fetched again, except
the current year's list, which is always refreshed. The site needs a session cookie, taken
from the IPO page before the first API call. Nothing outside data/raw/ipo/ is written.
"""

import http.cookiejar
import json
import sys
import time
import urllib.request
from datetime import UTC, datetime
from urllib.error import HTTPError

from nsealgo.data.calendar import IST
from nsealgo.data.ipo_read import list_rows
from nsealgo.settings import REPO_ROOT

OUT = REPO_ROOT / "data" / "raw" / "ipo"
FIRST_YEAR = 2016
SITE = "https://www.nseindia.com"
IPO_PAGE = SITE + "/market-data/all-upcoming-issues-ipo"
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/130.0 Safari/537.36"
)
PAUSE_SECONDS = 1.2


class NseSession:
    """Cookie-holding opener for www.nseindia.com; re-primes the cookie on 401/403."""

    def __init__(self) -> None:
        self._opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar())
        )
        self._primed = False

    def _open(self, url: str, referer: str) -> bytes:
        req = urllib.request.Request(
            url, headers={"User-Agent": UA, "Referer": referer, "Accept": "*/*"}
        )
        with self._opener.open(req, timeout=60) as resp:
            return resp.read()

    def get(self, url: str, referer: str = IPO_PAGE, tries: int = 3) -> bytes:
        for attempt in range(1, tries + 1):
            try:
                if not self._primed:
                    self._open(IPO_PAGE, SITE + "/")
                    self._primed = True
                body = self._open(url, referer)
                time.sleep(PAUSE_SECONDS)
                return body
            except HTTPError as err:
                if err.code not in (401, 403, 429, 500, 502, 503) or attempt == tries:
                    raise
                self._primed = False
            except OSError:
                if attempt == tries:
                    raise
            time.sleep(5 * attempt)
        raise AssertionError("unreachable")


def download_lists(nse: NseSession) -> dict:
    out = OUT / "nse_past_issues"
    out.mkdir(parents=True, exist_ok=True)
    this_year = datetime.now(IST).year
    counts = {}
    # 'all' as well as 'Equity': NSE overwrites an issue's list row with the company's later
    # listed security (NTPC Green's 2024 IPO row shows a 2026 bond, type N0), and the
    # Equity filter then drops the IPO
    for kind, security_type in (("eq", "Equity"), ("all", "all")):
        for year in range(FIRST_YEAR, this_year + 1):
            path = out / f"{kind}_{year}.json"
            if not path.exists() or year == this_year:
                url = (
                    f"{SITE}/api/public-past-issues?from_date=01-01-{year}"
                    f"&to_date=31-12-{year}&security_type={security_type}"
                )
                path.write_bytes(nse.get(url))
            counts[f"{kind}_{year}"] = len(json.loads(path.read_bytes()))
            print(f"list {kind} {year}: {counts[f'{kind}_{year}']} rows")
    return {"endpoint": SITE + "/api/public-past-issues", "rows": counts}


def download_details(nse: NseSession) -> dict:
    out = OUT / "nse_ipo_detail"
    out.mkdir(parents=True, exist_ok=True)
    symbols = sorted({r["symbol"].strip() for r in list_rows(OUT)})
    failed: dict[str, str] = {}
    for sym in symbols:
        path = out / f"{sym}.json"
        if path.exists():
            continue
        referer = f"{SITE}/market-data/issue-information?symbol={sym}&series=EQ&type=Active"
        url = f"{SITE}/api/ipo-detail?symbol={urllib.request.quote(sym)}&series=EQ"
        try:
            body = nse.get(url, referer)
            json.loads(body)
        except (HTTPError, ValueError) as err:
            failed[sym] = repr(err)
            print(f"detail {sym}: FAILED {err!r}")
            continue
        path.write_bytes(body)
        print(f"detail {sym}: {len(body)} bytes")
    return {"endpoint": SITE + "/api/ipo-detail", "symbols": len(symbols), "failed": failed}


STEPS = {"lists": download_lists, "details": download_details}


def main(argv: list[str]) -> None:
    steps = argv or list(STEPS)
    unknown = [s for s in steps if s not in STEPS]
    if unknown:
        raise SystemExit(f"unknown step(s) {unknown}; choose from {list(STEPS)}")
    OUT.mkdir(parents=True, exist_ok=True)
    manifest_path = OUT / "manifest.json"
    manifest = json.loads(manifest_path.read_text("utf-8")) if manifest_path.exists() else {}
    nse = NseSession()
    for step in steps:
        manifest[step] = STEPS[step](nse) | {"downloaded_at": datetime.now(UTC).isoformat()}
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main(sys.argv[1:])
