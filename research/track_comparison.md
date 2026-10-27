# Track comparison: ORB v1 (intraday) vs swing momentum v1 (delivery)

Dev period only (2016-01-01 .. 2023-12-31). Validation and holdout untouched for both.
Numbers only. The owner decides; the status row repeats decisions already recorded.
Details: `research/orb_v1_result.md` and `research/swing_v1_result.md`.

## What is shared and what differs

Shared:

- Rs 20,000 capital, sized off fixed capital in research.
- The same 40-symbol universe (`config/universe.yaml`). **It is today's large caps, not
  point-in-time, so survivorship bias is built in.** It flatters momentum most directly:
  the swing strategy buys recent winners, and the winners that later collapsed are the
  stocks missing from the data.
- Statutory charges from `config/costs.yaml`, shoonya brokerage preset, and the same
  slippage tiers (base 3, stress1 6, stress2 10 bps per side).

| | ORB v1 (strategy 1) | Swing momentum v1 (strategy 2) |
|---|---|---|
| Product, bars | MIS intraday, 5m | CNC delivery, daily |
| Signal | 30-minute opening range breakout, OCO stop entries at 09:45 | month-end rank: 6-month return skipping the latest month, above the 200-session average, top 4 |
| Exits | bracket stop / 2R target, time exit 14:30, flat by 14:50 | sold when it drops out of the top 4 at a month-end |
| Sizing | Rs 100 risk per trade, 2 trades a day, Rs 60,000 gross (MIS margin 25%) | 4 slots of about Rs 4,994, 30% cap, 100% gross, cash only |
| Holding period | intraday (09:45 at the earliest to 14:50 at the latest) | median 59 calendar days, mean 71.5, max 364 |
| Brokerage (shoonya) | lower of Rs 5 and 0.03% per order | zero, plus DP Rs 9 + GST per sale |
| Trials | 1-7 (1-6 current-equity sizing, 7 fixed capital) | 8-11 (all fixed capital, clean c6a7edf) |

## Side by side, base tier (shoonya, 3 bps), fixed-capital sizing

ORB is trial 7; swing is trial 8.

| Metric | ORB v1 | Swing v1 |
|---|---|---|
| Trades | 3,785 | 133 |
| Win % | 39.5% | 51.1% |
| Gross bps per trade | 3.6 | 391.3 |
| Cost bps per trade (charges + slippage) | 16.3 | 55.7 |
| Net bps per trade, mean | -12.7 | +335.6 |
| Net bps per trade, median | -27.8 | +17.3 |
| Net bps per trade, std dev / std error | 85.6 / 1.4 | 3,170 / 275 |
| Profit factor | 0.68 | 1.73 |
| Cost share of gross P&L | 434% | 13% |
| Net Rs over the period | -66,066 | +21,761 |
| Max drawdown Rs | 66,648 | 9,886 |
| Max drawdown % of capital | 333.2% | 49.4% |
| Sharpe (daily P&L / capital, annualized) | -3.60 | 0.55 |
| 15% account-drawdown halt would fire (record mode) | 2016-05-12 | 2018-03-06 |
| Turnover, one-way, x capital per year (run total / 7.8 years) | 342 | 3.9 |
| Costs % of capital per year (run total / 7.8 years) | 54.9% | 2.0% |

Net bps per trade by cost tier:

| Tier | ORB v1 | Swing v1 |
|---|---|---|
| Reference: zero brokerage, 0 bps (not tradeable) | +0.1 (trial 2) | +373.8 (trial 9) |
| Base, 3 bps | -14.1 (trial 1) / -12.7 (trial 7) | +335.6 (trial 8) |
| Stress1, 6 bps | -19.2 (trial 3) | +329.3 (trial 10) |
| Stress2, 10 bps | -23.8 (trial 4) | +321.0 (trial 11) |

ORB trials 1-4 sized off current equity and drained the account. Their bps are the
comparable figure; their rupee figures are not (see `orb_v1_result.md`).

## By calendar year, base tier, fixed capital

P&L is from session-end equity, so a swing position held across years counts in the
year the P&L accrued. Turnover and costs are by the year of each fill; for ORB they come
from trades.parquet, which is exact for intraday trades.

| Year | ORB P&L Rs | Swing P&L Rs | ORB in-year max DD % cap | Swing in-year max DD % cap | ORB turnover x | Swing turnover x | ORB costs % cap | Swing costs % cap |
|---|---|---|---|---|---|---|---|---|
| 2016 | -5,137 | -1,764 | 32.1% | 12.5% | 337.6 | 0.37 | 53.8% | 0.1% |
| 2017 | -11,715 | +4,730 | 61.5% | 12.7% | 411.5 | 4.56 | 64.4% | 2.2% |
| 2018 | -7,721 | -4,175 | 40.5% | 29.5% | 341.5 | 5.03 | 55.1% | 2.6% |
| 2019 | -10,981 | +2,347 | 57.6% | 23.7% | 336.0 | 4.74 | 54.2% | 2.4% |
| 2020 | -7,129 | +2,486 | 38.3% | 46.3% | 252.0 | 3.30 | 41.3% | 1.8% |
| 2021 | -7,023 | +15,508 | 38.9% | 31.5% | 303.7 | 3.24 | 49.7% | 1.6% |
| 2022 | -7,542 | +1,672 | 38.6% | 26.7% | 301.2 | 3.17 | 49.1% | 1.7% |
| 2023 | -8,818 | +957 | 47.8% | 20.0% | 391.8 | 5.77 | 61.8% | 3.1% |

Swing held nothing until 2016-11-01: the 200-session average needs ten months of data,
and the data starts 2016-01-01.

## Gate A items measured so far

| Gate A item | Threshold | ORB v1 | Swing v1 |
|---|---|---|---|
| Dev-period trades | >= 300 intraday, >= 100 swing | 3,785 (trial 7) | 133 (trial 8) |
| Net expectancy at double the modeled slippage (stress1) | > 0 | -19.2 bps (trial 3) | +329.3 bps (trial 10) |
| Walk-forward OOS expectancy, profit factor | > 0, >= 1.15 | not run | not run |
| Parameter neighbours | >= 50% of chosen | not run | not run |
| Deflated Sharpe | >= 0.90 | not computed | not computed |
| Holdout | net positive, once | not run | not run |
| P(15% DD within 250 days) | < 10% | not computed | not computed |

The DSR trial count is 11 (both strategies together).

## Caveats that differ between the tracks

- **Per-trade bps are not like for like.** An ORB trade is Rs 10,500-16,700 notional
  (median by year, trial 7) for a few hours. A swing trade is about Rs 4,800 (median)
  for about two months. Rupee P&L and costs as % of capital, both on the same
  Rs 20,000, compare more directly.
- **Swing's sample is small and concentrated.**
  - 133 trades; the standard error of the mean net bps is 275.
  - One ADANIENT trade (2020-11 to 2021-11) nets Rs 15,905 of the Rs 21,761.
  - Without ADANIENT, base net is Rs 8,410; without the 5 largest winners, Rs -2,757.
  - ADANIENT is in the data because it is a large cap today.
- **ORB's sample is large and its gross edge is small.** Gross 3.6 bps per trade against
  16.3 bps of costs. The statutory-only reference tier is about break-even.
- **Fixed-capital sizing affects the two differently.**
  - ORB: it keeps every year at full size (the current-equity runs drained).
  - Swing: together with `resize_holdings: false`, it blocked or shrank new buys while
    ADANIENT was worth most of the Rs 20,000 gross cap. The book held one stock from
    2021-06-01 to 2021-10-29. Paper and live (current equity) would size differently.
- **Swing entry rejections.** Base had 7 buys rejected for cash at the open, 19 sized to
  under one share, and 4 skipped because one share was above the 30% cap (2 MARUTI,
  2 ULTRACEMCO). Each left a slot in cash for the month.
- **Drawdown halt.** In paper and live the 15% halt latches. ORB's would have fired on
  2016-05-12 and swing's on 2018-03-06, before 2020-2021, when swing's large gains came.

## Status

- ORB v1: "fails Gate A, parked" (owner's decision, 2026-10-27).
- Swing momentum v1: no decision recorded.
