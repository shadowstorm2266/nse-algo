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
  of the last 14 true ranges. RVOL windows skip `no_trade` sessions (partial days).
- `config/holidays.csv` is for live/paper trading only; the historical calendar comes
  from the data.
