"""Download daily history of the Nifty 50 and NSE sectoral indices into data/raw/indices/.

    uv run python scripts/download_indices.py

Source: niftyindices.com (NSE Indices Ltd, the index provider), the endpoints behind its
"Historical Data" page. For each index in INDICES:

- <key>_price.csv: date, open, high, low, close of the price index
  (POST /BackPage/getHistoricaldatatabletoString).
- <key>_tri.csv: date, tri, ntr: the total-return and net total-return index
  (POST /BackPage/getTotalReturnIndexString).

Values are kept as the text the source returns; only the date is rewritten as ISO. The
site serves at most one year per request, so each index is fetched by calendar year, and
every row must name the requested index. Also writes nse_etf_list.csv (NSE's
eq_etfseclist.csv, byte for byte) and manifest.json. Files in data/raw/indices/ are
overwritten; nothing else is touched.
"""

import csv
import json
import time
from datetime import UTC, date, datetime
from pathlib import Path
from urllib.request import Request, urlopen

from nsealgo.data.calendar import IST
from nsealgo.settings import REPO_ROOT

OUT = REPO_ROOT / "data" / "raw" / "indices"
FIRST_YEAR = 2015
SITE = "https://www.niftyindices.com"
PRICE_EP = "/BackPage/getHistoricaldatatabletoString"
TRI_EP = "/BackPage/getTotalReturnIndexString"
ETF_LIST_URL = "https://nsearchives.nseindia.com/content/equities/eq_etfseclist.csv"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/130.0 Safari/537.36",
    "Content-Type": "application/json; charset=utf-8",
    "Referer": SITE + "/reports/historical-data",
    "Origin": SITE,
    "X-Requested-With": "XMLHttpRequest",
}
PAUSE_SECONDS = 1.0
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# key: (trading name, long name), as in niftyindices.com's IndexMapping.json
INDICES = {
    "nifty50": ("Nifty 50", "Nifty 50"),
    "bank": ("Nifty Bank", "Nifty Bank"),
    "it": ("Nifty IT", "Nifty IT"),
    "pharma": ("Nifty Pharma", "Nifty Pharma"),
    "fmcg": ("Nifty FMCG", "Nifty FMCG"),
    "auto": ("Nifty Auto", "Nifty Auto"),
    "metal": ("Nifty Metal", "Nifty Metal"),
    "realty": ("Nifty Realty", "Nifty Realty"),
    "energy": ("Nifty Energy", "Nifty Energy"),
    "psubank": ("Nifty PSU Bank", "Nifty PSU Bank"),
    "infra": ("Nifty Infra", "Nifty Infrastructure"),
    "media": ("Nifty Media", "Nifty Media"),
    "finserv": ("Nifty Fin Service", "Nifty Financial Services"),
}
PRICE_FIELDS = {"open": "OPEN", "high": "HIGH", "low": "LOW", "close": "CLOSE"}
TRI_FIELDS = {"tri": "TotalReturnsIndex", "ntr": "NTR_Value"}


def _site_date(d: date) -> str:
    return f"{d.day:02d}-{MONTHS[d.month - 1]}-{d.year}"


def _iso(site_date: str) -> str:
    """'09 Jan 2015' -> '2015-01-09'."""
    day, mon, year = site_date.split()
    return date(int(year), MONTHS.index(mon[:3].title()) + 1, int(day)).isoformat()


def _fetch(url: str, body: bytes | None = None, tries: int = 3) -> bytes:
    for attempt in range(1, tries + 1):
        try:
            req = Request(url, data=body, headers=HEADERS, method="POST" if body else "GET")
            with urlopen(req, timeout=60) as resp:
                return resp.read()
        except OSError:
            if attempt == tries:
                raise
            time.sleep(5 * attempt)
    raise AssertionError("unreachable")


def _post(endpoint: str, names: tuple[str, str], start: date, end: date) -> list[dict]:
    trading, long_name = names
    cinfo = (
        f"{{'name':'{trading.upper()}','startDate':'{_site_date(start)}',"
        f"'endDate':'{_site_date(end)}','indexName':'{long_name}'}}"
    )
    raw = json.loads(_fetch(SITE + endpoint, json.dumps({"cinfo": cinfo}).encode()))
    rows = json.loads(raw["d"]) if isinstance(raw, dict) else raw
    return rows or []


def _check_name(row: dict, names: tuple[str, str]) -> None:
    got = (row.get("INDEX_NAME") or row.get("Index Name") or "").replace(" ", "").upper()
    if got not in {n.replace(" ", "").upper() for n in names}:
        raise ValueError(f"asked for {names[0]!r}, got a row for {got!r}")


def _rows(endpoint: str, names: tuple[str, str], fields: dict[str, str]) -> list[dict]:
    date_key = "HistoricalDate" if endpoint == PRICE_EP else "Date"
    out: dict[str, dict] = {}
    today = datetime.now(IST).date()
    for year in range(FIRST_YEAR, today.year + 1):
        end = min(date(year, 12, 31), today)
        for row in _post(endpoint, names, date(year, 1, 1), end):
            _check_name(row, names)
            day = _iso(row[date_key])
            if day in out:
                raise ValueError(f"{names[0]}: duplicate date {day}")
            out[day] = {"date": day} | {k: row[src] for k, src in fields.items()}
        time.sleep(PAUSE_SECONDS)
    return [out[d] for d in sorted(out)]


def _write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    manifest: dict = {"downloaded_at": datetime.now(UTC).isoformat(), "indices": {}}
    for key, names in INDICES.items():
        price = _rows(PRICE_EP, names, PRICE_FIELDS)
        tri = _rows(TRI_EP, names, TRI_FIELDS)
        _write_csv(OUT / f"{key}_price.csv", price, ["date", *PRICE_FIELDS])
        _write_csv(OUT / f"{key}_tri.csv", tri, ["date", *TRI_FIELDS])
        manifest["indices"][key] = {
            "trading_name": names[0],
            "long_name": names[1],
            "price": {"endpoint": SITE + PRICE_EP, "rows": len(price)},
            "tri": {"endpoint": SITE + TRI_EP, "rows": len(tri)},
        }
        print(f"{key}: {len(price)} price rows, {len(tri)} TRI rows")
    (OUT / "nse_etf_list.csv").write_bytes(_fetch(ETF_LIST_URL))
    manifest["etf_list"] = ETF_LIST_URL
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
