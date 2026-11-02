# Historical data layer

Source: Kaggle NSE 1-minute CSVs in `data/raw/` (40 symbols, 2015-02-02 .. 2026-04-08),
never modified. Build everything with:

    uv run python scripts/build_data.py

Settings: `config/data.yaml`. Outputs:

| Output | What |
|---|---|
| `data/clean/{1m,5m,15m}/symbol=X/year=Y/` | bars: `ts` (bar start, IST), `available_at`, `session_date`, OHLCV, `n_bars` (5m/15m) |
| `data/clean/daily/features/symbol=X/` | prior-session features per (symbol, session), `available_at` = 09:15 of that session |
| `data/clean/daily/rvol/symbol=X/` | 20-session average volume per 5-minute bucket (`ts`, `tod`) |
| `data/clean/calendar/calendar.parquet` | sessions with `no_trade` flag |
| `research/data_quality.csv` | per-symbol quality summary |
| `research/data_quality_events.csv` | every dropped row/day and every flag |
| `research/short_sessions.csv` | raw sessions with < 300 bars and their status |
| `config/universe.yaml` | default universe (not point-in-time) |

Query through `nsealgo.data.store.connect()`: views `bars_1m`, `bars_5m`, `bars_15m`,
`daily_features`, `rvol_profile`, `bars_5m_rvol`, `calendar`.

## Rules

- Clean range 2016-01-01 .. 2026-04-07. 2015 is excluded (zero-price blocks, an
  unadjusted ADANIENT demerger, off-grid timestamps); 2026-04-08 is a partial session.
- Raw prices are already split/bonus adjusted by the source. Do not add a
  `config/corporate_actions.csv`: it would adjust twice.
- Regular-session bars only (09:15 .. 15:29 start times). Muhurat and Saturday DR-site
  sessions are dropped entirely. NSE outage days are kept with `no_trade = true`;
  the engine must never open a trade on them.
- Dropped: rows with any price <= 0. Flagged only (kept in data): suspect prints
  (spike heuristic in `config/data.yaml`; it also fires on real crash and circuit-halt
  days, so it never drops data), OHLC inconsistencies, overnight moves beyond 15%,
  out-of-line days. Every one is listed in `research/data_quality_events.csv`.
- A bar is visible at `available_at = ts + length`. The first 15m bar covers
  09:15:00 .. 09:29:59 and is available at 09:30:00.
- Daily features use sessions strictly before D, need complete windows, and are NaN
  until a symbol has 20 prior sessions. Nothing is filled. ATR(14) is the simple mean
  of the last 14 true ranges. RVOL windows skip short sessions (< 300 bars, i.e. the
  outage days) but keep full no_trade sessions.
- 2021-02-25 is `no_trade` (`prev_session_outage_close`): its previous-session values
  come from 2021-02-24, whose stored close is from ~11:40 (trading resumed 15:45-17:00,
  outside our window).
- `config/holidays.csv` is for live/paper trading only; the historical calendar comes
  from the data.

## Index data (strategy 4, raw only)

Daily history from 2015-01-01 of the Nifty 50 and 12 sectoral indices, from
niftyindices.com (NSE Indices Ltd), plus NSE's ETF list. Download with:

    uv run python scripts/download_indices.py

| Output | What |
|---|---|
| `data/raw/indices/<key>_price.csv` | price index: `date`, `open`, `high`, `low`, `close` |
| `data/raw/indices/<key>_tri.csv` | total-return index `tri` and net total-return `ntr` (`-` where the source has none) |
| `data/raw/indices/nse_etf_list.csv` | NSE `eq_etfseclist.csv` as downloaded (symbol, underlying, date of listing) |
| `data/raw/indices/manifest.json` | download time, index names, endpoints, row counts |

Values are the source's text; only dates are rewritten as ISO. A re-download
overwrites them, and the source may revise history, so the manifest's download time
matters.

## ETF proxy dataset (strategy 4)

Tradable proxies for NSE equity ETFs, one daily series per index in
`config/etf_proxy.yaml`: the 11 sectors with an ETF on NSE today (`PX_BANK` ...
`PX_FINSERV`; Media has none) at a 0.40% a year expense ratio, and `PX_NIFTY50` at
0.05% (benchmark 2 only, never traded). Build after `scripts/build_data.py`, which
clears data/clean:

    uv run python scripts/build_etf_proxy.py

| Output | What |
|---|---|
| `data/clean/etf_proxy/bars.parquet` | `symbol`, `session_date`, `open`, `high`, `low`, `close` (no volume) |
| `data/clean/etf_proxy/manifest.json` | settings, rows, date range, SHA-256 of every raw file read |

Construction (`src/nsealgo/data/etf_proxy.py`):

- Only the sessions of `data/clean/calendar` (2016-01-04 .. 2026-04-07) are kept;
  muhurat and DR-site sessions in the index files are dropped, and so is the index
  history outside that range. A session without a complete, positive price and TRI row
  fails the build.
- close = TRI rebased to 100 on 2016-01-04, times `(1 - e / 365) ^ d`, where `d` is the
  calendar days since 2016-01-04 and `e` the expense ratio (daily accrual, actual/365).
- open, high, low = that close x the price index's open, high, low over its close the
  same day.

DuckDB view `etf_proxy_1d`. The loader reads it for instrument ETF, under the same
holdout lock as the equity data. It is a proxy, not ETF prices: no tracking error, no
premium or discount to NAV, no spread beyond the slippage tier, no volume, and most
sector ETFs listed only in 2020 or later.

## Mainboard IPO dataset (phase 2, IPO track step 1)

One row per mainboard IPO whose bidding ran on NSE, bid opening 2016-01-01 onward. Data
only: no strategy reads it yet. Report: `research/ipo_dataset.md`. Download, then build
(the build needs xpdf `pdftotext` 4.x on PATH, which Git for Windows ships; poppler's has
no `-table` mode):

    uv run python scripts/download_ipo.py            # NSE past-issue lists + per-issue JSON
    uv run python scripts/download_bhavcopy.py       # every NSE bhavcopy since 2016-01-01
    uv run python scripts/download_ipo_boa.py        # basis-of-allotment adverts (needs both above)
    uv run python scripts/build_ipo.py               # -> data/clean/ipo/
    uv run python scripts/report_ipo.py              # -> research/ipo_dataset_tables.md
    uv run python scripts/check_ipo_tapetide.py      # aggregator cross-checks -> research/ipo_*_tapetide.csv

`scripts/build_data.py` deletes all of `data/clean`, so rerun `build_ipo.py` after it.
`data/clean/ipo/_cache/` holds advert text and the bhavcopy first-seen table, keyed by
their input files; delete it to force a full rebuild (about 10 minutes).

| Raw (`data/raw/ipo/`) | Source (all PRIMARY except the last) |
|---|---|
| `nse_past_issues/eq_<year>.json`, `all_<year>.json` | NSE `/api/public-past-issues`, `security_type=Equity` and `all`: symbol, company, bid dates, price band, issue price, listing date |
| `nse_ipo_detail/<SYMBOL>.json` | NSE `/api/ipo-detail`: issue information (bid period, lot, registrar), consolidated category-wise bids at close, ISIN and listing date |
| `bhavcopy/*.csv.zip` | NSE end-of-day bhavcopies, old format to 2024-07-05, UDiFF after; `bhavcopy_misses.json` lists weekdays with no file |
| `nse_boa/ADV_<ISIN>_<DDMONYYYY>.pdf`, `probe_log.json` | NSE copies of the basis-of-allotment advert (a few are zips of newspaper pages under the .pdf name); the log has every date tried per issue |
| `aggregator_tapetide/ipo_listing_gains_<year>.md` | Tapetide yearly pages (UNVERIFIED), used only by the cross-checks |
| `benchmark/nifty50_tri.csv` (+ price, manifest) | niftyindices.com Nifty 50 TRI for the IPO v1 benchmark: `scripts/download_indices.py --only nifty50 --out data/raw/ipo/benchmark` |

Hand-made decisions, each with a reason and a source: `config/ipo_dataset.yaml` (one
entry: CAMS 2020, listed on BSE only).

`data/clean/ipo/ipos.parquet` (and `.csv`), columns `nsealgo.data.ipo_build.CLEAN_COLS`:

- **Universe** (`nsealgo.data.ipo`). Rows of NSE's Equity list, minus those it marks as
  FPOs, NCDs (NSE page code contains `ncd`), partly-paid lines or a "special withdrawal"
  window (`list_row_kind`). Plus rows only the unfiltered list has: NSE overwrites an
  issue's row with the company's later listed security, which drops the IPO from the
  Equity filter (`overwritten_ipo_rows`; 17 issues, e.g. NTPC Green 2024). REIT and InvIT
  units are left out.
- **Identity and status.** `issue_id` = list symbol + bid open date. `status`: `listed`,
  `withdrawn` (NSE's list says so), `pending` (closed within 30 days of the last bhavcopy),
  `already_listed` (traded before bidding: an unlabelled follow-on offer),
  `not_listed_on_nse_at_ipo` (config exception), or `not_found_on_nse` (no new ISIN within
  45 days of the close).
- **Issue terms.** `issue_open`, `issue_close`, `price_band_low/high` from the list.
  `issue_price` is the list's price when the listing-day bhavcopy base price agrees, else
  whichever of the two lies in the band, the list's first (`issue_price_src`). `lot_size`
  from the per-issue JSON, else the advert's 1-lot category (`lot_size_src`).
  `lot_value_at_cap` = lot x upper band. `retail_discount` (Rs per share) from the advert.
- **Subscription.** `retail_sub_exch`: consolidated retail bids / retail shares at the
  close of bidding (NSE JSON, before rejections). A JSON bid book stamped before the
  bid close is an intraday snapshot: its bids and multiples are dropped and the row is
  flagged `exch_snapshot_before_close` (Adani Wilmar 2022, H.G. Infra 2018). `retail_sub_boa`: the advert's "subscribed
  to the extent of" figure (after rejections). `retail_sub` is the advert's figure where
  there is one, else the exchange figure (`retail_sub_src`).
- **Retail basis of allotment** (advert, `nsealgo.data.ipo_boa`): `retail_valid_applications`
  and `retail_shares_applied` (TOTAL row), `retail_allottees` and `retail_shares_allotted` ("... Equity Shares to N
  successful ..."), `retail_lots_allotted` = shares / lot, `min_bid_applications` and
  `min_bid_ratio` (the 1-lot row: the row with NSE's lot as its category and the most
  applications). `p_1lot` (`p_1lot_method`): that row's ratio when it allots one lot; else
  allottees / applications; else 100% when the advert's retail multiple is below 1. A
  candidate outside [0.9/x, 6/x] (capped at 1; x = retail multiple) is dropped. A 1-lot row
  holding under 10% of the shares applied for is dropped with its TOTAL, and an allottee
  figure the applications or shares cannot support is dropped. `allotment_date`
  (`allotment_date_src`): the date the basis was finalised with the designated exchange
  (`designated_exchange`), else the date the board took it on record and allotted.
- **Listing day** (bhavcopy, first session the ISIN appears): `listing_date`, `list_open`
  (on an IPO's listing day the open is the price discovered in the pre-open call auction;
  rule as reproduced from SEBI circular CIR/MRD/DP/01/2012, not read in the original),
  `list_high/low/close`, `base_price`, `listing_match` (rule used, `nsealgo.data.ipo_listing`).
  `ret_open` and `ret_close` are over `issue_price`, gross.
- **Checks.** `checks` lists failed cross-checks: lot (JSON vs advert), list price vs base
  price, advert offer price vs issue price (gross or net of the discount), allotment date
  between close and listing, OHLC order, advert unreadable (scan or no character map) or
  without a retail section, 1-lot row missing or too small, allottees implausible, 1-lot
  chance outside the subscription bound, 1-lot ratio vs allottees/applications (2%
  relative). A failing value is left empty or kept as built and flagged, never corrected
  by hand. Readers: `nsealgo.data.ipo_read`; assembly and checks: `nsealgo.data.ipo_build`.

No field comes from an aggregator. NSE's advert archive starts in Sep/Oct 2018: issues
before that have no retail basis-of-allotment fields and no allotment date.

## Live IPO recorder (IPO track step 3, data only)

Records what NSE shows for every mainboard IPO open for bidding from 2 Nov 2026 on. No
strategy reads it, nothing is simulated and no trial is logged. Code:
`scripts/record_ipo_live.py` (runs, schedule check, log), `scripts/ipo_live_steps.py`
(per-issue steps), `nsealgo.data.ipo_live` (parsing, file names) and
`nsealgo.data.live_schedule` (slots, missed runs).

    uv run python scripts/record_ipo_live.py              # one manual run
    uv run python scripts/record_ipo_live.py --status     # issues on disk, last runs, missed slots
    uv run python scripts/make_ipo_task_xml.py            # Task Scheduler definition (creates no task)

Sources (all PRIMARY, www.nseindia.com and nsearchives.nseindia.com):
`/api/ipo-current-issue` (the IPO page's "Current Issues" table; found in the page's own
script `dist/js/sections/live-market/upcoming-ipo.js`), `/api/ipo-detail` (per-issue JSON
with the consolidated category-wise book and its "Updated as on" stamp), the daily
bhavcopy, and the basis-of-allotment advert. Mainboard = series `EQ`, not an FPO or
partly-paid line; SME and other rows are listed in the run log with the reason.

Layout under `data/live/ipo/` (gitignored, local only). Files are created once and never
rewritten:

| Path | What |
|---|---|
| `current_issue/<stamp>.json` | each run's `/api/ipo-current-issue` body |
| `<issue_id>/<stamp>.json` | per-issue JSON fetched on a bid day, close day included |
| `<issue_id>/final_<stamp>.json` | per-issue JSON from the first run on a day after the close day |
| `<issue_id>/listing_<YYYYMMDD>.json` | the issue's row in the listing day's bhavcopy: open, high, low, close, base price, match method, bhavcopy SHA-256 |
| `<issue_id>/ADV_<ISIN>_<DDMONYYYY>.pdf` | basis-of-allotment advert, NSE's file name |
| `bhavcopy/*.csv.zip`, `bhavcopy/misses.jsonl` | bhavcopies read to find the listing day; days with no file |
| `run_log.jsonl` | one line per run: slot, lateness, missed slots, actions, warnings, errors, git hash |

`<stamp>` is the fetch time in IST, `YYYYMMDDTHHMMSS+0530`; `<issue_id>` is
`<SYMBOL>_<YYYYMMDD of bid open>` as in the research dataset. The live bhavcopies are kept
apart from `data/raw/ipo/bhavcopy/`, whose first-seen logic needs an unbroken run of days.

Schedule: 12:00, 15:30 and 19:30 IST on NSE trading days (weekdays not in
`config/holidays.csv`), from one Task Scheduler task with three weekly triggers, created
from the XML because `schtasks` flags cannot set "wake the computer to run this task".
Each run compares its start with the log: a slot no scheduled run covered is printed and
logged as missed, and a run more than 30 minutes after its slot as late. The task runs
`uv run --frozen` (never rewrites `uv.lock`), only while the owner is logged on (no stored
password, no admin rights), and opens a console window while it runs.

Machine paths are in `config/ipo_live.yaml`: pdftotext by full path (a task's PATH is not
the shell's; checked and logged every run) and the backup git directory.

Backup: the recordings cannot be downloaded again, so the scheduled run for the 19:30 slot
commits and pushes `data/live/ipo/` to a private GitHub repo, nse-algo-live-data
(`scripts/ipo_live_backup.py`). Its git directory is a bare repo outside the main repo,
and every git call passes `--git-dir` and `--work-tree`, so git never touches the main
repo. A commit is refused unless every change is a new file or an append to
`run_log.jsonl` / `bhavcopy/misses.jsonl`. The 19:30 run's own log line goes into the next
backup.

    uv run python scripts/ipo_live_backup.py init|run|check
    uv run python scripts/make_ipo_task_xml.py                      # then, as the owner:
    schtasks /Create /TN "nse-algo-record-ipo-live" /XML "<repo>\data\live\ipo\record_ipo_live_task.xml"
    uv run python scripts/make_ipo_task_xml.py --check-env REPORT.json --out CHECK.xml
    # create CHECK.xml as a task, schtasks /Run it, read REPORT.json, delete the task
