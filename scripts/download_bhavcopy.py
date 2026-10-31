"""Download NSE equity bhavcopies (end-of-day, every symbol) into data/raw/ipo/bhavcopy/.

    uv run python scripts/download_bhavcopy.py [START [END]]   # ISO dates; default 2016-01-01 on

One request per weekday. Two archive formats, both on nsearchives.nseindia.com:
- up to 2024-07-05: content/historical/EQUITIES/YYYY/MON/cmDDMONYYYYbhav.csv.zip
- from 2024-07-08: content/cm/BhavCopy_NSE_CM_0_0_0_YYYYMMDD_F_0000.csv.zip (UDiFF)
Zips are stored byte for byte. A 404 means no session that day (weekend sessions are not
fetched); 404 days are listed in bhavcopy_misses.json so a rerun does not ask again.
Existing files are never fetched again.
"""

import json
import sys
import time
import urllib.request
from datetime import date, datetime, timedelta
from urllib.error import HTTPError

from nsealgo.data.calendar import IST
from nsealgo.settings import REPO_ROOT

OUT = REPO_ROOT / "data" / "raw" / "ipo" / "bhavcopy"
MISSES = OUT / "bhavcopy_misses.json"
ARCHIVE = "https://nsearchives.nseindia.com"
LAST_OLD_FORMAT = date(2024, 7, 5)
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/130.0 Safari/537.36"
)
PAUSE_SECONDS = 0.4


MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]


def bhavcopy_name(day: date) -> str:
    if day <= LAST_OLD_FORMAT:
        return f"cm{day.day:02d}{MONTHS[day.month - 1]}{day.year}bhav.csv.zip"
    return f"BhavCopy_NSE_CM_0_0_0_{day:%Y%m%d}_F_0000.csv.zip"


def bhavcopy_url(day: date) -> str:
    name = bhavcopy_name(day)
    if day <= LAST_OLD_FORMAT:
        return f"{ARCHIVE}/content/historical/EQUITIES/{day.year}/{MONTHS[day.month - 1]}/{name}"
    return f"{ARCHIVE}/content/cm/{name}"


def _fetch(url: str, tries: int = 3) -> bytes | None:
    """Body, or None on 404. A body shorter than its Content-Length is retried."""
    for attempt in range(1, tries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=60) as resp:
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


def main(argv: list[str]) -> None:
    start = date.fromisoformat(argv[0]) if argv else date(2016, 1, 1)
    end = date.fromisoformat(argv[1]) if len(argv) > 1 else datetime.now(IST).date()
    OUT.mkdir(parents=True, exist_ok=True)
    misses: set[str] = set(json.loads(MISSES.read_text("utf-8"))) if MISSES.exists() else set()
    got = 0
    day = start
    while day <= end:
        path = OUT / bhavcopy_name(day)
        if day.weekday() < 5 and not path.exists() and day.isoformat() not in misses:
            body = _fetch(bhavcopy_url(day))
            if body is None:
                misses.add(day.isoformat())
            else:
                path.write_bytes(body)
                got += 1
            time.sleep(PAUSE_SECONDS)
            if (got + len(misses)) % 100 == 0:
                MISSES.write_text(json.dumps(sorted(misses), indent=0), encoding="utf-8")
                print(f"{day}: {got} new files", flush=True)
        day += timedelta(days=1)
    MISSES.write_text(json.dumps(sorted(misses), indent=0), encoding="utf-8")
    print(f"done: {got} new files, {len(misses)} weekday misses on record")


if __name__ == "__main__":
    main(sys.argv[1:])
