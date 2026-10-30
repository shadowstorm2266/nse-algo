# Track comparison: ORB v1 (intraday) vs swing momentum v2 (delivery)

Dev period only (2016-01-01 .. 2023-12-31). Validation and holdout untouched for both.
Numbers only. The owner decides; the status section repeats decisions already recorded.
Details: `research/orb_v1_result.md` and `research/swing_v1_result.md` (swing v1 in
sections 1-5, v2 in sections 6-7).

## What is shared and what differs

Shared:

- Rs 20,000 starting capital.
- The same 40-symbol universe (`config/universe.yaml`). **It is today's large caps, not
  point-in-time, so survivorship bias is built in.** It flatters momentum most directly:
  the swing strategy buys recent winners, and the winners that later collapsed are the
  stocks missing from the data.
- Statutory charges from `config/costs.yaml`, shoonya brokerage preset, and the same
  slippage tiers (base 3, stress1 6, stress2 10 bps per side).

| | ORB v1 (strategy 1) | Swing momentum v2 (strategy 2) |
|---|---|---|
| Product, bars | MIS intraday, 5m | CNC delivery, daily |
| Signal | 30-minute opening range breakout, OCO stop entries at 09:45 | month-end rank: 6-month return skipping the latest month, above the 200-session average, top 4 |
| Exits | bracket stop / 2R target, time exit 14:30, flat by 14:50 | sold when it drops out of the top 4 at a month-end |
| Sizing basis in research | fixed capital (Rs 20,000 every session) | current equity, as paper and live |
| Sizing | Rs 100 risk per trade, 2 trades a day, Rs 60,000 gross (MIS margin 25%) | 4 equal slots, each 99% of (equity / 4 - buy charges): Rs 4,944 at the start; 30% cap, 100% gross, cash only |
| Holding period | intraday (09:45 at the earliest to 14:50 at the latest) | median 58 calendar days, mean 71.5, max 364 |
| Brokerage (shoonya) | lower of Rs 5 and 0.03% per order | zero, plus DP Rs 9 + GST per sale |
| Trials | 1-7 (1-6 current-equity sizing, 7 fixed capital) | 12-13 (v2, 213926c); v1 was 8-11 (fixed capital, c6a7edf) |

## Side by side, base tier (shoonya, 3 bps)

ORB is trial 7 (fixed capital); swing is trial 12 (v2, current equity). Max DD % is of
capital for ORB and of the running peak for swing. Sharpe is on daily P&L over capital
for ORB and on daily returns over the previous equity for swing. Turnover and costs are
over the Rs 20,000 starting capital for both; the swing account ended at Rs 37,552.

| Metric | ORB v1 | Swing v2 |
|---|---|---|
| Trades | 3,785 | 139 |
| Win % | 39.5% | 51.1% |
| Gross bps per trade | 3.6 | 377.8 |
| Cost bps per trade (charges + slippage) | 16.3 | 50.1 |
| Net bps per trade, mean | -12.7 | +327.7 |
| Net bps per trade, median | -27.8 | +15.7 |
| Net bps per trade, std dev / std error | 85.6 / 1.4 | 3,086 / 262 |
| Profit factor | 0.68 | 1.50 |
| Cost share of gross P&L | 434% | 17% |
| Net Rs over the period | -66,066 | +17,552 |
| Max drawdown Rs | 66,648 | 11,732 |
| Max drawdown % | 333.2% of capital | 48.0% of peak |
| Sharpe (daily, annualized) | -3.60 | 0.46 |
| 15% account-drawdown halt would fire (record mode) | 2016-05-12 | 2018-03-06 |
| Turnover, one-way, x capital per year (run total / 7.8 years) | 342 | 4.96 |
| Costs % of capital per year (run total / 7.8 years) | 54.9% | 2.3% |

Net bps per trade by cost tier:

| Tier | ORB v1 | Swing v1 (fixed capital) | Swing v2 |
|---|---|---|---|
| Reference: zero brokerage, 0 bps (not tradeable) | +0.1 (trial 2) | +373.8 (trial 9) | not run |
| Base, 3 bps | -14.1 (trial 1) / -12.7 (trial 7) | +335.6 (trial 8) | +327.7 (trial 12) |
| Stress1, 6 bps | -19.2 (trial 3) | +329.3 (trial 10) | +331.6 (trial 13) |
| Stress2, 10 bps | -23.8 (trial 4) | +321.0 (trial 11) | not run |

ORB trials 1-4 sized off current equity and drained the account. Their bps are the
comparable figure; their rupee figures are not (see `orb_v1_result.md`).

## By calendar year, base tier

P&L is from session-end equity, so a swing position held across years counts in the
year the P&L accrued. In-year max DD is % of capital for ORB and % of the running peak
(starting at the year's opening equity) for swing. Turnover and costs are by the year of
each fill, over Rs 20,000; for ORB they come from trades.parquet, which is exact for
intraday trades.

| Year | ORB P&L Rs | Swing P&L Rs | ORB in-year max DD % cap | Swing in-year max DD % peak | ORB turnover x | Swing turnover x | ORB costs % cap | Swing costs % cap |
|---|---|---|---|---|---|---|---|---|
| 2016 | -5,137 | -1,764 | 32.1% | 12.4% | 337.6 | 0.37 | 53.8% | 0.1% |
| 2017 | -11,715 | +4,451 | 61.5% | 12.1% | 411.5 | 4.81 | 64.4% | 2.3% |
| 2018 | -7,721 | -4,626 | 40.5% | 26.8% | 341.5 | 5.19 | 55.1% | 2.7% |
| 2019 | -10,981 | +1,579 | 57.6% | 21.6% | 336.0 | 4.42 | 54.2% | 2.3% |
| 2020 | -7,129 | +484 | 38.3% | 42.7% | 252.0 | 2.90 | 41.3% | 1.7% |
| 2021 | -7,023 | +13,284 | 38.9% | 19.0% | 303.7 | 5.23 | 49.7% | 2.4% |
| 2022 | -7,542 | +1,261 | 38.6% | 23.7% | 301.2 | 5.96 | 49.1% | 2.5% |
| 2023 | -8,818 | +2,884 | 47.8% | 15.6% | 391.8 | 9.91 | 61.8% | 4.3% |

Swing held nothing until 2016-11-01: the 200-session average needs ten months of data,
and the data starts 2016-01-01.

## Swing v2 vs equal-weight buy-and-hold of the same universe

The benchmark (`reporting/benchmark.py`) holds all 40 symbols in equal rupee amounts in
fractional shares, bought at the 2016-01-04 open with one base-tier buy, never
rebalanced, no sell costs. It is not a strategy and not a trial. Definitions and caveats:
`swing_v1_result.md` section 7.

| Year | Swing v2 return % | Swing v2 max DD % | Benchmark return % | Benchmark max DD % | Swing excess return, pp |
|---|---|---|---|---|---|
| 2016 | -8.8% | 12.4% | 10.5% | 12.3% | -19.4 |
| 2017 | 24.4% | 12.1% | 45.0% | 5.8% | -20.6 |
| 2018 | -20.4% | 26.8% | -0.3% | 15.4% | -20.1 |
| 2019 | 8.7% | 21.6% | 14.3% | 13.6% | -5.6 |
| 2020 | 2.5% | 42.7% | 21.2% | 40.6% | -18.8 |
| 2021 | 66.0% | 19.0% | 52.2% | 10.7% | +13.8 |
| 2022 | 3.8% | 23.7% | 18.4% | 18.0% | -14.7 |
| 2023 | 8.3% | 15.6% | 11.5% | 23.2% | -3.2 |
| All, 2016-2023 | 87.8% | 48.0% | 345.6% | 40.6% | -257.8 |

Final equity: swing Rs 37,552, benchmark Rs 89,114.

## Gate A items measured so far

| Gate A item | Threshold | ORB v1 | Swing v2 |
|---|---|---|---|
| Dev-period trades | >= 300 intraday, >= 100 swing | 3,785 (trial 7) | 139 (trial 12) |
| Net expectancy at double the modeled slippage (stress1) | > 0 | -19.2 bps (trial 3) | +331.6 bps (trial 13) |
| Long-only: beats equal-weight buy-and-hold of the universe after costs | overall and in at least 5 of 8 dev years | not long-only | -257.8 pp overall; ahead in 1 of 8 years |
| Walk-forward OOS expectancy, profit factor | > 0, >= 1.15 | not run | not run |
| Parameter neighbours | >= 50% of chosen | not run | not run |
| Deflated Sharpe | >= 0.90 | not computed | not computed |
| Holdout | net positive, once | not run | not run |
| P(15% DD within 250 days) | < 10% | not computed | not computed |

The DSR trial count was 13 (7 ORB, 6 swing) when these tables were made. It is now 21,
with pullback trials 14-17 and sector_rotation trials 18-21.

## Caveats that differ between the tracks

- **Per-trade bps are not like for like.** An ORB trade is Rs 10,500-16,700 notional
  (median by year, trial 7) for a few hours. A swing trade is about Rs 4,970 (median,
  trial 12) for about two months.
- **Rupee figures are not like for like.** ORB sizes off a fixed Rs 20,000 every
  session; swing v2 compounds, so its later trades are larger (the account was
  Rs 33,407 at the end of 2021).
- **Swing's sample is small and concentrated (trial 12).**
  - 139 trades; the standard error of the mean net bps is 262.
  - One ADANIENT trade (2020-11-02 to 2021-11-01) nets Rs 12,722 of the Rs 17,552;
    ADANIENT's 6 trades net Rs 10,913.
  - Without the ADANIENT trades, base net is Rs 6,640 (+33.2%); without the 5 largest
    winners, Rs -5,130.
  - ADANIENT is in the data because it is a large cap today. It is also 17.8% of the
    benchmark's final value.
- **ORB's sample is large and its gross edge is small.** Gross 3.6 bps per trade against
  16.3 bps of costs. The statutory-only reference tier is about break-even.
- **Swing entry rejections (trial 12).** 10 buys rejected for cash at the open, 5 sized
  to under one share, and 1 skipped because one share was above the 30% cap (MARUTI,
  2017-10-31). Each left a slot in cash for the month. The engine's CNC cash check and
  gross-room sizing changed after trials 12-13 (`swing_v1_result.md`, end of section 7);
  the trials were not rerun.
- **Drawdown halt.** In paper and live the 15% halt latches. ORB's would have fired on
  2016-05-12 and swing's on 2018-03-06, before 2020-2021, when swing's large gains came.

## Status

- ORB v1: "fails Gate A, parked" (owner's decision, 2026-10-27).
- Swing momentum v1 and v2: "loses to equal-weight buy-and-hold of the same universe;
  parked" (owner's decision, 2026-10-27).
- Pullback mean reversion v1 (strategy 3, swing track, trials 14-17): "fails Gate A,
  parked" (owner's decision, 2026-10-28). No fixed-capital run: the reference tier (no
  brokerage, no slippage) already loses, -7.6 bps/trade (trial 14). Not in the tables
  above; details in `research/strategy3_result.md`.
- Sector rotation v1 (strategy 4, swing track, CNC on 11 sector-ETF proxies, trials
  18-21): "fails first-pass checks 2 and 3; parked. Research phase ended per the
  pre-registered rule." (owner's decision, 2026-10-31). Base tier (trial 19): +118.0%
  total return vs +222.6% for equal-weight buy-and-hold of the 11 series and +201.2%
  for PX_NIFTY50. Not in the tables above; details in `research/strategy4_result.md`,
  rule in `research/strategy4_plan.md` section 2.
