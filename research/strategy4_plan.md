# Strategy 4: sector rotation over sector-ETF proxies (swing, CNC, daily bars): pre-registration

Written and committed before any backtest of this strategy. The rules and parameters
below are fixed. They are not tuned on any result. Strategy name `sector_rotation`,
version 1. If a code bug is found after a run, the fix bumps the version and the rerun is
a new trial. Earlier trial lines stay in `research/trials.jsonl`.

## 1. Hypothesis

Strategy 2's monthly momentum rules may work better on whole sectors than on single
stocks. The rules: keep what is above its 200-session average, rank by 6-month return
skipping the latest month, hold the top 4. Sector ETFs have much lower delivery charges
than stocks (STT 0.001% on the sell only, against 0.1% on each side). Applied to 11 NSE
sector indices, held through ETFs, the hypothesis is that the rotation earns more after
ETF costs than:

1. holding the same 11 sectors at equal weight (the Gate A buy-and-hold rule); and
2. holding a Nifty 50 ETF.

## 2. Owner's decision rule (fixed before the runs)

> "If Strategy 4 fails any first-pass check, the research phase ends. If it passes, the
> next step is the Phase 4 validation suite; real money only after Gate B."

## 3. Data: tradable proxy series

Built by `scripts/build_etf_proxy.py` from `data/raw/indices/` (niftyindices.com, step 1,
c5d91a2). Settings are in `config/etf_proxy.yaml`. Output is `data/clean/etf_proxy/`, a
separate daily dataset with its own `manifest.json` (the raw files' SHA-256 hashes and
the settings). `data/raw` is not modified.

**Series.** The 11 sectors that have an ETF on NSE today, plus the Nifty 50 for
benchmark 2. Nifty Media is excluded because it has no ETF.

| Symbol | Index | Expense ratio a year | Earliest ETF on NSE (NSE ETF list) |
|---|---|---|---|
| PX_BANK | Nifty Bank | 0.40% | BANKBEES, 2004 |
| PX_IT | Nifty IT | 0.40% | ITBEES, Jul 2020 |
| PX_PHARMA | Nifty Pharma | 0.40% | PHARMABEES, Jul 2021 |
| PX_FMCG | Nifty FMCG | 0.40% | FMCGIETF, Aug 2021 |
| PX_AUTO | Nifty Auto | 0.40% | AUTOIETF, Jan 2022 |
| PX_METAL | Nifty Metal | 0.40% | METALIETF, Aug 2024 |
| PX_REALTY | Nifty Realty | 0.40% | MOREALTY, Mar 2024 |
| PX_ENERGY | Nifty Energy | 0.40% | MOENERGY, Oct 2025 |
| PX_PSUBANK | Nifty PSU Bank | 0.40% | PSUBNKBEES, 2007 |
| PX_INFRA | Nifty Infrastructure | 0.40% | INFRABEES, 2010 |
| PX_FINSERV | Nifty Financial Services | 0.40% | BFSI, Aug 2021 |
| PX_NIFTY50 (benchmark 2 only, never traded) | Nifty 50 | 0.05% | NIFTYBEES, 2002 |

The `PX_` prefix marks a proxy. It keeps these names apart from real NSE tickers, some
of which are plain sector names (`IT`, `PSUBANK`, `METAL`, `ENERGY`, `INFRA`).

**Construction, per series.**

- **Sessions.** Only our calendar's sessions (`data/clean/calendar`, 2016-01-04 ..
  2026-04-07, 2,529 sessions). Muhurat and Saturday DR-site sessions in the index files
  are dropped. Index history before 2016-01-04 and after 2026-04-07 is not used. Every
  calendar session must have both a price-index row and a TRI row, or the build fails;
  nothing is filled. The 3 no_trade sessions keep their bars, as in the equity data.
- **Close.** Close = the total-return index rebased to 100 on the first kept session
  (2016-01-04): `R_t = 100 x TRI_t / TRI_2016-01-04`.
- **Expense ratio.** Deducted by daily accrual over calendar days (actual/365), the way
  a fund's NAV accrues its expenses:
  - `F_t = (1 - e / 365) ^ d_t`, where `d_t` is the calendar days from 2016-01-04 to
    session t and `e` is 0.0040 (0.0005 for PX_NIFTY50).
  - `close_t = R_t x F_t`.
  - A year costs `1 - (1 - e/365)^365`: 0.399% for the sectors, 0.050% for the Nifty 50.
- **Open, high, low.** That day's close scaled by the price index's own ratio:
  `open_t = close_t x O_t / C_t`, and the same for high and low. O, H, L, C are the
  price index's values that day. The ordering low <= open, close <= high carries over.
- **Volume.** None. The engine's bar frame gets 0, and nothing in this strategy reads
  volume.
- **Bars.** One daily bar per session, ts 09:15 and available_at 15:30 IST, as for the
  equity daily bars.

**Holdout lock.** The dataset runs to 2026-04-07, which includes the holdout. The loader
refuses any read on or after `holdout_start` (2025-04-08) unless the owner types "run
holdout", as for the equity data. Dates after 2026-04-07 are not in the dataset.

**What the proxy leaves out (read before the results).**

- **ETF existence.** It assumes an ETF tracking each index existed from 2016. Most did
  not; see the listing dates above. Only Bank, PSU Bank and Infra had one through all
  of dev.
- **Tracking and pricing.** No tracking error, no premium or discount to NAV, and no bid-ask
  spread beyond the slippage tier. Volume and liquidity are not modelled: every order
  fills in full at the open.
- **Dividends.** The TRI reinvests dividends on the ex-date. A real ETF collects them
  later and holds some cash.
- **The open.** The index open comes from the constituents' first trades, not an ETF's
  own opening auction.
- **Choice of sectors.** The 11 sectors were chosen today, from today's ETF list. Index
  membership is point-in-time (the stock universe's survivorship bias does not apply),
  but the set of sectors is not.

## 4. Rules

The rules are swing v2's (`swing_momentum.py`, version 2), unchanged, applied to the 11
`PX_` sector series. Code: `src/nsealgo/strategies/sector_rotation.py`, a subclass of
`SwingMomentumStrategy` that changes only the name, the version and the instrument.
Parameters: `config/strategies/sector_rotation.yaml`.

| Parameter | Value | Meaning |
|---|---|---|
| `top_n` | 4 | hold the top 4 |
| `lookback_months` | 6 | momentum over 6 months ... |
| `skip_months` | 1 | ... skipping the latest month |
| `trend_ma_sessions` | 200 | keep only series whose close is above their 200-session simple average |
| `resize_holdings` | false | holdings still in the top 4 are kept as they are |
| `market_filter.enabled` | false | no market filter (as in swing v2) |

- **Universe:** the 11 `PX_` sector series of `config/etf_proxy.yaml`. PX_NIFTY50 is
  not in it.
- **Decision:** after the close of the last tradeable session of each month M, when
  the calendar's next tradeable session is in another month. It uses daily bars up to
  and including that close. A month whose last session is no_trade decides on the last
  tradeable session before it. No decision is made when no tradeable session follows.
- **Momentum:** the series' last close in month M-1, divided by its last close in month
  M-7, minus 1.
- **Ranked:** series with a bar on the decision day, at least 200 closes, and a close
  strictly above the simple average of their last 200 closes (that day's included).
  Highest momentum first; ties by symbol.
- **Target:** the top 4 ranked. If fewer than 4 qualify, the rest stays in cash.
  - **Exits:** holdings not in the target get a market exit at the next tradeable
    open.
  - **Entries:** target series not held get a market entry with their rank.
  - **Kept:** holdings still in the target are not topped up or trimmed.
  - Only newcomers are bought. A newcomer the RiskGovernor skips, or a buy rejected for
    cash at the open, leaves its slot in cash until the next month's decision.
- **Buying:** the RiskGovernor buys within the swing block of `config/risk.yaml`,
  exactly as it is:
  - at most 4 positions, equal weight (slot = equity / 4);
  - current-equity sizing, a 1% cash buffer, 30% position cap and 100% gross cap;
  - at most 8 orders a day;
  - whole units.

  Exits fill before entries at the open, so the morning's sale proceeds fund the
  morning's buys. ETF buy charges are used in the RiskGovernor's size estimate.
- **No stop loss.**
- **Last session:** positions still open after the run's last session (2023-12-29) are
  closed at its close (`end_of_run`) and pay sell costs, as in the engine.
- **Warm-up:**
  - The dataset starts 2016-01-04. The 200-session average first exists at the 200th
    session, in October 2016.
  - The strategy holds cash until its first decision after that. The benchmarks are
    invested from 2016-01-04. This is the same as for strategies 2 and 3.
  - The 2015 index history in `data/raw/indices` is not used, because the dataset keeps
    only our calendar's sessions.
- **Unit size:** the series start at 100 on 2016-01-04. Before costs, a unit costs
  about Rs 40 to Rs 530 during dev. A Rs 5,000 slot buys whole units, and the leftover
  stays in cash.

## 5. Costs

- **Charges:** every fill, buy or sell, pays `costs.py` charges with `instrument="ETF"`:
  - STT 0.001% on sell, nil on buy;
  - stamp duty 0.015% on buy;
  - NSE transaction charge 0.00297% and SEBI fee Rs 10 per crore, both legs;
  - GST 18% on brokerage + transaction charge + SEBI fee + DP charge.
- **Broker (shoonya):** zero delivery brokerage, and a DP charge of Rs 9 + GST per scrip
  on each sell day.
- **ETF slippage tiers:** a new `etf_slippage_bps_per_side` block in
  `config/costs.yaml`, applied to every fill price:

  | Tier | Brokerage preset | Slippage per side |
  |---|---|---|
  | none (reference, not tradeable) | zero (no DP charge) | 0 bps |
  | base | shoonya | 10 bps |
  | stress1 | shoonya | 20 bps |
  | stress2 | shoonya | 30 bps |

  - The reference tier uses the `zero` preset, as every earlier strategy's reference
    run did. It is labelled as a reference and is not used by any check.
  - The equity tiers (3/6/10 bps) are unchanged and are not used for ETFs.

## 6. Benchmarks (reporting only, not strategies and not trials)

Each benchmark:

- starts with Rs 20,000;
- is bought at the first dev session's open (2016-01-04), in fractional units;
- pays one base-tier ETF buy: `instrument="ETF"` charges, shoonya, and 10 bps of
  slippage;
- is held to 2023-12-29 and never rebalanced;
- is marked at each session's close, with no sell costs.

The benchmarks:

1. **Benchmark 1 (the Gate A benchmark):** equal-weight buy-and-hold of the same 11
   `PX_` sector series, Rs 20,000 / 11 each.
2. **Benchmark 2:** PX_NIFTY50, the Nifty 50 TRI with a 0.05% a year expense ratio,
   built as in section 3.

Both use `reporting/benchmark.py buy_and_hold` and print from
`uv run python scripts/report_runs.py benchmark <base run dir>`.

## 7. Runs (exactly four, all dev)

- **Trials:** 18-21. The DSR trial count goes from 17 to 21.
- **Period:** dev only, 2016-01-01 .. 2023-12-31. That is 1,971 sessions; the first is
  2016-01-04 and the last 2023-12-29. Validation and holdout are not touched.

| Tier | Command |
|---|---|
| none (reference) | `uv run python -m nsealgo.backtest --strategy sector_rotation --period dev --cost-tier none --brokerage zero` |
| base | `uv run python -m nsealgo.backtest --strategy sector_rotation --period dev --cost-tier base` |
| stress1 | `uv run python -m nsealgo.backtest --strategy sector_rotation --period dev --cost-tier stress1` |
| stress2 | `uv run python -m nsealgo.backtest --strategy sector_rotation --period dev --cost-tier stress2` |

- All four run on one clean commit that contains this plan, the dataset code and the
  strategy.
- No parameter variants, no validation run and no holdout run.

## 8. First-pass checks (fixed before the runs)

Each check is reported as PASS or FAIL with its number. "Beats" means strictly greater;
a tie is a FAIL.

| # | Check | Run | PASS when |
|---|---|---|---|
| 1 | Net expectancy > 0 at stress1 | stress1 (20 bps) | net P&L per trade in rupees (net P&L / trades) > 0 **and** mean net bps per trade (each trade's net P&L / entry notional, averaged) > 0. If the two disagree in sign, it is a FAIL and both numbers are shown. |
| 2 | Beats benchmark 1 overall and in at least 5 of 8 dev years | base (10 bps) | the run's total return over dev > benchmark 1's, **and** the run's in-year return > benchmark 1's in at least 5 of the 8 calendar years 2016-2023 |
| 3 | Beats benchmark 2 overall | base (10 bps) | the run's total return over dev > benchmark 2's |

**Definitions:**

- **Total return:** final session-end equity / Rs 20,000 - 1.
- **In-year return:** the year's last session-end equity / the previous year's last
  session-end equity - 1. 2016 starts from Rs 20,000. This is `report_runs.py
  benchmark`'s definition, used for strategies 2 and 3.
- **Sell costs:** the run's last equity is after the `end_of_run` sale, so it has paid
  sell costs. The benchmarks pay none, as in the earlier benchmark reports.

## 9. Reported (numbers only, no verdict)

The same tables as the strategy 2 and 3 dev write-ups:

1. **Tier summary:** one row per run.
   - Trades, win %, average win and loss.
   - Gross, cost and net bps per trade; profit factor.
   - Max drawdown (Rs and % of peak), Sharpe, net Rs, final equity.
   - Cap skips, turnover x per year, costs % of capital per year.
2. **First-pass checks** (section 8), PASS or FAIL with numbers.
3. **Gate A items table** (section 10).
4. **By entry year, base tier:** trade metrics, in-year max drawdown and Sharpe.
5. **Net bps per trade and trade count, by year and tier.**
6. **Turnover and costs, base tier, by year of each fill.** Bought and sold Rs, turnover,
   charges, DP, slippage, costs % of capital. Also costs % of capital by year and tier.
7. **Holding period:** sessions held (from the buy's fill session to the sale's fill
   session, both counted) and calendar days. Median, mean and max.
8. **Trades per year:** the run total over 1,971 / 252 years, and the count by entry
   year.
9. **By exit reason, base tier:** `strategy` vs `end_of_run`.
10. **By symbol, base tier:** all 11 series.
11. **Rejections by reason,** including cap skips (`PRICE_ABOVE_POSITION_CAP`) and
    `MAX_POSITIONS`.
12. **Both benchmark reports by year and overall,** for the base run: return and max
    drawdown, run vs benchmark, excess in percentage points.
13. **Without the single best symbol:** the symbol with the largest total net Rs in the
    base run. Two views:
    - the base run's trade metrics without its trades;
    - the benchmark 1 report with `--exclude <symbol>`.

    Neither is a rerun.

## 10. Gate A items (backtest to paper)

| Gate A item | Threshold | Measured from |
|---|---|---|
| Dev-period trades (swing) | >= 100 | base run |
| Net expectancy at double the modeled slippage | > 0 | stress1 run (20 bps), net bps and Rs per trade |
| Long-only: beats equal-weight buy-and-hold of the same universe after costs | overall and in at least 5 of 8 dev years | base run vs benchmark 1 |
| Walk-forward out-of-sample net expectancy and profit factor | > 0 and >= 1.15 | not run in this round |
| Parameter neighbours keep >= 50% of the chosen setting's net expectancy | >= 50% | not run in this round (it would add trials) |
| Deflated Sharpe | >= 0.90 | not computed in this round (21 trials logged after these runs) |
| Holdout net positive, run once | > 0 | not run; only the owner can ask for it |
| P(15% drawdown within 250 trading days) at configured risk | < 10% | not computed in this round; the date the 15% halt would have fired (record mode) is reported |

## 11. Engine changes needed (before any run, with tests)

1. **Instrument.** Strategies declare an `instrument`: "EQ" for ORB, swing and
   pullback, and "ETF" for sector_rotation.
   - Declaring "EQ" changes no logic in the existing strategies, so none of them gets a
     new version.
   - The Backtester passes the instrument to the SimBroker (charges on every fill) and
     to the RiskGovernor (the estimated buy charges in swing sizing).
   - "ETF" is allowed with CNC only.
2. **Slippage.** `config/costs.yaml` gains `etf_slippage_bps_per_side`. The backtest CLI
   takes a tier's slippage from the table for the strategy's instrument. The trial
   record gains `instrument`.
3. **Data.** An ETF strategy reads its daily bars from `data/clean/etf_proxy` (a DuckDB
   view) and its universe from `config/etf_proxy.yaml`, under the same holdout lock.
4. **Benchmarks.** `reporting/benchmark.py buy_and_hold` takes the instrument.
   `report_runs.py benchmark` on an ETF run prints both benchmarks, each with its own
   by-year table.

Nothing changes in `config/risk.yaml` or in the statutory rates of `config/costs.yaml`.

After the four runs and the report, work stops for the owner's review.
