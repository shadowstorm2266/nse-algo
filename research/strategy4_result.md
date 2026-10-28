# Strategy 4, sector rotation v1: dev-period result

The strategy was pre-registered in `research/strategy4_plan.md` (da0dcd6), which was
committed and pushed before any run. The rules, parameters, costs, benchmarks and checks
are exactly as written there.

## Run facts

- **Code:** `sector_rotation` version 1 at 0d4fb85. All four runs used that commit with
  a clean tree. No run printed a warning.
- **Data:** the ETF proxy dataset from 85d00c2 (`data/clean/etf_proxy`; plan section 3).
  It was checked against the raw index files by an independent recomputation, with a
  maximum relative difference of 0.
- **Trials:** 18 (none), 19 (base), 20 (stress1) and 21 (stress2). The DSR trial count
  is now 21: 7 ORB, 6 swing, 4 pullback and 4 sector_rotation.
- **Period:** dev, 2016-01-04 .. 2023-12-29. That is 1,971 sessions, or 7.82 years of
  252. Validation and holdout were not touched.
- **Universe:** the 11 `PX_` sector series. PX_NIFTY50 is benchmark 2 only.
- **Warm-up:** the 200-session average first existed on 2016-10-26. The first decision
  was on 2016-10-28, and the first buys filled on 2016-11-01. Until then the run held
  cash; both benchmarks were invested from 2016-01-04.
- **Risk:** the swing block of `config/risk.yaml`, unchanged. Sizing used current
  equity, 4 positions, a 1% cash buffer, a 30% position cap and a 100% gross cap. The
  first slot was Rs 4,949, and the first buys were Rs 4,859 to Rs 4,925 in whole units.
- **Costs:** every fill paid ETF charges (`instrument="ETF"`) with shoonya (DP charge Rs
  9 + GST = Rs 10.62 per sale day per scrip), plus ETF slippage per tier. The reference
  tier uses the `zero` preset (no DP charge) and 0 bps.
- **Definitions:** as in `swing_v1_result.md` and `strategy3_result.md`.
  - Bps are means over trades of P&L / entry notional; cost = charges + slippage.
  - Max DD % is of the running peak. Sharpe uses daily returns over the previous
    equity.
  - Turnover (one-way) and "costs % capital" are over the Rs 20,000 starting capital.

## 1. First-pass checks (plan section 8)

| # | Check | Run | Value | Result |
|---|---|---|---|---|
| 1 | Net expectancy > 0 at stress1 (20 bps): Rs per trade **and** bps per trade | trial 20 | Rs +253.69 per trade; +479.4 bps per trade | **PASS** |
| 2 | Beats benchmark 1 (equal-weight buy-and-hold of the 11 series) overall **and** in at least 5 of 8 dev years | trial 19 (base) | Overall: run +118.0% vs benchmark +222.6% (-104.7 pp). Ahead in 2 of 8 years: 2019 (+0.6 pp) and 2021 (+7.1 pp). | **FAIL** |
| 3 | Beats benchmark 2 (PX_NIFTY50) overall | trial 19 (base) | Run +118.0% vs benchmark +201.2% (-83.3 pp) | **FAIL** |

The owner's decision rule, fixed before the runs (plan section 2):

> "If Strategy 4 fails any first-pass check, the research phase ends. If it passes, the
> next step is the Phase 4 validation suite; real money only after Gate B."

## 2. Cost tiers (trials 18-21)

| Run | Trades | Win % | Avg win Rs | Avg loss Rs | Gross bps | Cost bps | Net bps | PF | Max DD Rs | Max DD % | Sharpe (daily, ann.) | Net Rs | Final equity Rs | Cap skips | Turnover x/yr | Costs % cap/yr |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Reference: zero brokerage, 0 bps (trial 18), REFERENCE | 86 | 55.8% | 964 | -503 | 543.2 | 2.4 | 540.8 | 2.42 | 7,829 | 32.2% | 0.77 | 27,192 | 47,192 | 0 | 3.53 | 0.1% |
| Base: shoonya, 10 bps (trial 19) | 86 | 53.5% | 931 | -481 | 542.6 | 41.8 | 500.8 | 2.23 | 7,765 | 33.0% | 0.70 | 23,591 | 43,591 | 0 | 3.37 | 1.3% |
| Stress1: shoonya, 20 bps (trial 20) | 86 | 52.3% | 913 | -470 | 542.1 | 62.7 | 479.4 | 2.13 | 7,850 | 33.7% | 0.67 | 21,817 | 41,817 | 0 | 3.29 | 2.0% |
| Stress2: shoonya, 30 bps (trial 21) | 86 | 51.2% | 891 | -461 | 541.5 | 83.5 | 458.1 | 2.03 | 8,040 | 34.7% | 0.63 | 19,870 | 39,870 | 0 | 3.21 | 2.6% |

- The reference tier is not a tradeable result.
- **Net per trade:** Rs +316.19 (reference), +274.31 (base), +253.69 (stress1) and
  +231.05 (stress2).
- **Total return:** +136.0% (reference), +118.0% (base), +109.1% (stress1) and +99.4%
  (stress2).
- **Base P&L split:** gross P&L at reference prices was Rs +25,679. Slippage was
  Rs 1,054, charges Rs 1,034, and net Rs +23,591.
- **The 15% drawdown halt** (record mode) would have fired in every tier, in October
  2018:

  | Tier | Date | Drawdown |
  |---|---|---|
  | none | 2018-10-25 | 15.46% |
  | base | 2018-10-23 | 15.63% |
  | stress1 | 2018-10-11 | 15.06% |
  | stress2 | 2018-10-11 | 15.39% |

  In paper or live (latch) there would be no new entries after that date.
- **Trade counts:** all four tiers made the same 86 trades. No buy was skipped or
  rejected in any tier.

## 3. Gate A items

| Gate A item | Threshold | Value |
|---|---|---|
| Dev-period trades (swing) | >= 100 | 86 (base, trial 19) |
| Net expectancy at double the modeled slippage (stress1, 20 bps) | > 0 | +479.4 bps/trade, Rs +253.69/trade (trial 20) |
| Long-only: beats equal-weight buy-and-hold of the universe after costs | overall and in at least 5 of 8 dev years | -104.7 pp overall; ahead in 2 of 8 years (section 4) |
| Walk-forward OOS expectancy and profit factor | > 0 and >= 1.15 | not run |
| Parameter neighbours | >= 50% of chosen | not run |
| Deflated Sharpe | >= 0.90 | not computed (21 trials logged) |
| Holdout net positive, run once | > 0 | not run |
| P(15% drawdown within 250 trading days) | < 10% | not computed; the 15% halt would have fired on 2018-10-23 (base, record mode) |

## 4. Base (trial 19) vs both benchmarks

Command: `uv run python scripts/report_runs.py benchmark <base run dir>`. Each benchmark:

- starts with Rs 20,000, in fractional units;
- is bought at the 2016-01-04 open with one base-tier ETF buy (shoonya, 10 bps);
- is held to the 2023-12-29 close, never rebalanced, with no sell costs.

Returns and drawdowns are in-year; "All" is the whole period. Excess = run return -
benchmark return, in percentage points.

**Benchmark 1:** equal-weight buy-and-hold of the 11 sector series.

| Year | Run return % | Run max DD % | Benchmark return % | Benchmark max DD % | Excess return, pp |
|---|---|---|---|---|---|
| 2016 | -10.0% | 13.3% | 6.8% | 16.4% | -16.7 |
| 2017 | 26.0% | 6.3% | 38.9% | 5.3% | -12.9 |
| 2018 | -10.7% | 16.9% | -6.3% | 16.4% | -4.5 |
| 2019 | 6.9% | 14.0% | 6.3% | 14.3% | +0.6 |
| 2020 | 6.5% | 28.0% | 13.1% | 39.9% | -6.6 |
| 2021 | 43.0% | 12.5% | 35.9% | 11.4% | +7.1 |
| 2022 | 7.8% | 18.8% | 8.2% | 17.8% | -0.4 |
| 2023 | 22.6% | 14.2% | 31.3% | 10.6% | -8.7 |
| All | 118.0% | 33.0% | 222.6% | 41.2% | -104.7 |

**Benchmark 2:** PX_NIFTY50, the Nifty 50 TRI less 0.05% a year.

| Year | Run return % | Run max DD % | Benchmark return % | Benchmark max DD % | Excess return, pp |
|---|---|---|---|---|---|
| 2016 | -10.0% | 13.3% | 4.5% | 12.1% | -14.5 |
| 2017 | 26.0% | 6.3% | 30.2% | 4.1% | -4.2 |
| 2018 | -10.7% | 16.9% | 4.6% | 14.4% | -15.3 |
| 2019 | 6.9% | 14.0% | 13.4% | 10.8% | -6.5 |
| 2020 | 6.5% | 28.0% | 16.1% | 38.3% | -9.6 |
| 2021 | 43.0% | 12.5% | 25.5% | 9.9% | +17.5 |
| 2022 | 7.8% | 18.8% | 5.6% | 15.9% | +2.2 |
| 2023 | 22.6% | 14.2% | 21.2% | 7.0% | +1.4 |
| All | 118.0% | 33.0% | 201.2% | 38.3% | -83.3 |

- **2016:** the run held cash until 2016-11-01. Its -10.0% came from November and
  December. Its first holdings were Metal, Realty, PSU Bank and Auto.
- **Sell costs:** the run's last equity is after the `end_of_run` sale of 4 holdings,
  so it has paid sell costs. The benchmarks have not.

## 5. By entry year (base, trial 19)

Max DD % and Sharpe are from that year's sessions.

| Year | Trades | Win % | Avg win Rs | Avg loss Rs | Gross bps | Cost bps | Net bps | PF | Net Rs | Max DD % | Sharpe |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2016 | 5 | 40.0% | 454 | -538 | -247.1 | 44.3 | -291.4 | 0.56 | -706 | 13.3% | -0.93 |
| 2017 | 13 | 61.5% | 374 | -256 | 354.9 | 45.0 | 309.9 | 2.34 | 1,717 | 6.3% | 1.83 |
| 2018 | 10 | 50.0% | 419 | -403 | 60.7 | 44.3 | 16.4 | 1.04 | 81 | 16.9% | -0.80 |
| 2019 | 11 | 45.5% | 241 | -421 | -210.3 | 42.9 | -253.2 | 0.48 | -1,321 | 14.0% | 0.54 |
| 2020 | 11 | 54.5% | 1,861 | -763 | 1849.6 | 48.3 | 1801.3 | 2.92 | 7,348 | 28.0% | 0.44 |
| 2021 | 12 | 58.3% | 1,195 | -460 | 868.6 | 39.1 | 829.5 | 3.64 | 6,064 | 12.5% | 1.75 |
| 2022 | 12 | 41.7% | 1,096 | -407 | 377.4 | 37.2 | 340.2 | 1.92 | 2,630 | 18.8% | 0.49 |
| 2023 | 12 | 66.7% | 1,328 | -710 | 808.0 | 35.7 | 772.3 | 3.74 | 7,779 | 14.2% | 1.70 |

Trades are counted in their entry year. A trade entered in one year can be held well
into the next (section 8).

## 6. Net bps per trade and trade count, by entry year and tier

| Year | Trades (every tier) | none | base | stress1 | stress2 |
|---|---|---|---|---|---|
| 2016 | 5 | -249.6 | -291.4 | -310.9 | -330.3 |
| 2017 | 13 | 352.9 | 309.9 | 289.2 | 268.3 |
| 2018 | 10 | 58.4 | 16.4 | -3.6 | -24.1 |
| 2019 | 11 | -212.8 | -253.2 | -273.0 | -292.7 |
| 2020 | 11 | 1849.1 | 1801.3 | 1777.2 | 1753.0 |
| 2021 | 12 | 867.1 | 829.5 | 807.3 | 785.5 |
| 2022 | 12 | 375.4 | 340.2 | 318.8 | 297.6 |
| 2023 | 12 | 806.4 | 772.3 | 750.3 | 728.3 |

## 7. Turnover and costs

By year of each fill (base, trial 19; from fills.parquet):

| Year | Bought Rs | Sold Rs | Turnover x | Charges Rs | DP Rs (pre-GST) | Slippage Rs | Costs Rs | Costs % capital |
|---|---|---|---|---|---|---|---|---|
| 2016 | 23,877 | 3,912 | 0.69 | 15 | 9 | 28 | 43 | 0.2% |
| 2017 | 62,354 | 62,736 | 3.13 | 153 | 117 | 125 | 278 | 1.4% |
| 2018 | 48,951 | 48,866 | 2.45 | 118 | 90 | 98 | 215 | 1.1% |
| 2019 | 56,327 | 57,007 | 2.83 | 130 | 99 | 113 | 243 | 1.2% |
| 2020 | 49,161 | 48,869 | 2.45 | 128 | 99 | 98 | 226 | 1.1% |
| 2021 | 83,704 | 85,281 | 4.22 | 147 | 108 | 169 | 316 | 1.6% |
| 2022 | 88,554 | 88,295 | 4.42 | 148 | 108 | 177 | 325 | 1.6% |
| 2023 | 101,716 | 144,304 | 6.15 | 196 | 144 | 246 | 442 | 2.2% |

2023 includes the `end_of_run` sales. Charges total Rs 1,034. Of that, the DP charge
(Rs 9 + GST per sale day per scrip) is Rs 913: Rs 774 before GST.

Costs (charges + slippage) as % of the Rs 20,000 capital, by year of each fill and
tier:

| Year | none | base | stress1 | stress2 |
|---|---|---|---|---|
| 2016 | 0.02% | 0.21% | 0.35% | 0.49% |
| 2017 | 0.07% | 1.39% | 2.01% | 2.61% |
| 2018 | 0.06% | 1.08% | 1.57% | 2.03% |
| 2019 | 0.07% | 1.22% | 1.77% | 2.30% |
| 2020 | 0.06% | 1.13% | 1.60% | 2.05% |
| 2021 | 0.10% | 1.58% | 2.38% | 3.13% |
| 2022 | 0.11% | 1.62% | 2.43% | 3.19% |
| 2023 | 0.14% | 2.21% | 3.36% | 4.39% |
| Per year (total / 7.82) | 0.1% | 1.3% | 2.0% | 2.6% |

Costs rise over the years because the account grew under current-equity sizing.

## 8. Holding period, trades per year, time in market (base, trial 19)

**Holding period.** Sessions held counts from the buy's fill session to the sale's fill
session, both included.

| | Median | Mean | Min | Max |
|---|---|---|---|---|
| Sessions held | 44 | 78.8 | 19 | 309 |
| Calendar days | 62 | 114.9 | 28 | 456 |

Distribution of sessions held:

| Sessions held | Trades |
|---|---|
| 1-21 | 12 |
| 22-42 | 25 |
| 43-63 | 13 |
| 64-126 | 20 |
| 127-252 | 14 |
| over 252 | 2 |

**Trades per year.** 86 / 7.82 = 11.0 a year. By entry year: 5 (2016, from November),
13, 10, 11, 11, 12, 12 and 12.

**Time in market.** Positions held at each session's close, over 1,971 sessions:

| Positions held | Sessions |
|---|---|
| 4 | 1,586 |
| 3 | 81 |
| 2 | 21 |
| 1 | 62 |
| 0 | 221 |

The 221 sessions with nothing held are:

- the 202 warm-up sessions before 2016-11-01;
- 18 sessions in April 2020;
- the last session, after the `end_of_run` sale.

The average number of positions held by year was 0.7, 4.0, 3.67, 3.92, 3.06, 4.0, 3.83
and 3.98 (2016 to 2023). No buy was rejected or skipped. So every month with fewer than
4 held had fewer than 4 series ranked, meaning above their 200-session average with a
momentum value.

## 9. By exit reason (base, trial 19)

| Exit | Trades | Win % | Avg win Rs | Avg loss Rs | Gross bps | Cost bps | Net bps | PF | Net Rs |
|---|---|---|---|---|---|---|---|---|---|
| end_of_run | 4 | 100.0% | 1,979 | - | 2310.7 | 36.7 | 2274.0 | - | 7,915 |
| strategy | 82 | 51.2% | 831 | -481 | 456.4 | 42.1 | 414.3 | 1.81 | 15,676 |

The `end_of_run` trades are PX_REALTY, PX_PHARMA, PX_AUTO and PX_PSUBANK, closed at the
2023-12-29 close.

## 10. By symbol (base, trial 19), by net Rs

| Symbol | Trades | Win % | Avg win Rs | Avg loss Rs | Gross bps | Cost bps | Net bps | PF | Net Rs |
|---|---|---|---|---|---|---|---|---|---|
| PX_IT | 5 | 80.0% | 1,416 | -154 | 2418.8 | 45.8 | 2373.0 | 36.72 | 5,510 |
| PX_REALTY | 12 | 58.3% | 1,482 | -1,120 | 551.4 | 41.5 | 509.9 | 1.85 | 4,775 |
| PX_PSUBANK | 9 | 66.7% | 916 | -293 | 796.1 | 40.0 | 756.1 | 6.26 | 4,619 |
| PX_BANK | 8 | 87.5% | 365 | -441 | 505.2 | 44.0 | 461.2 | 5.79 | 2,116 |
| PX_METAL | 7 | 28.6% | 2,932 | -845 | 1278.9 | 41.2 | 1237.7 | 1.39 | 1,639 |
| PX_FMCG | 8 | 50.0% | 643 | -275 | 271.9 | 41.2 | 230.7 | 2.34 | 1,473 |
| PX_PHARMA | 4 | 50.0% | 1,118 | -433 | 715.0 | 41.4 | 673.6 | 2.58 | 1,371 |
| PX_AUTO | 9 | 55.6% | 575 | -407 | 180.3 | 40.0 | 140.3 | 1.76 | 1,243 |
| PX_ENERGY | 9 | 33.3% | 877 | -344 | 103.6 | 44.1 | 59.5 | 1.27 | 565 |
| PX_INFRA | 8 | 50.0% | 298 | -183 | 134.2 | 40.3 | 93.8 | 1.62 | 458 |
| PX_FINSERV | 7 | 28.6% | 687 | -310 | -124.1 | 42.2 | -166.2 | 0.89 | -178 |

## 11. Rejections and cap skips

None in any tier:

- no `PRICE_ABOVE_POSITION_CAP` (cap skips), `MAX_POSITIONS`, `QTY_BELOW_ONE` or
  `MAX_ORDERS_PER_DAY` rejections;
- no buy rejected for cash at the open.

## 12. Without the single best symbol (PX_IT)

PX_IT had the largest total net Rs in the base run (Rs +5,510). Neither view is a
rerun: every other trade stays as it was, including its size.

**Base trade metrics without PX_IT's 5 trades:**

- 81 trades, win 51.9%;
- net +385.2 bps and Rs +223.23 per trade;
- PF 1.95, net Rs +18,081.

**Benchmark 1 report** with `--exclude PX_IT`:

| Year | Run return % | Run max DD % | Benchmark return % | Benchmark max DD % | Excess return, pp |
|---|---|---|---|---|---|
| 2016 | -10.0% | 13.3% | 6.8% | 16.4% | -16.7 |
| 2017 | 26.0% | 6.3% | 38.9% | 5.3% | -12.9 |
| 2018 | -13.9% | 19.6% | -6.3% | 16.4% | -7.6 |
| 2019 | 4.3% | 14.5% | 6.3% | 14.3% | -2.0 |
| 2020 | -6.1% | 29.7% | 13.1% | 39.9% | -19.2 |
| 2021 | 40.9% | 14.6% | 35.9% | 11.4% | +5.0 |
| 2022 | 11.4% | 21.3% | 8.2% | 17.8% | +3.2 |
| 2023 | 26.8% | 16.7% | 31.3% | 10.6% | -4.5 |
| All | 90.4% | 38.4% | 222.6% | 41.2% | -132.2 |

As a check, final equity - capital = Rs 18,081.47, which equals the net P&L of the
other trades in trades.parquet.

## Read with the tables

- **Proxy, not ETF prices** (plan section 3). Only Bank, PSU Bank and Infra had an ETF
  through all of dev. The proxy has no tracking error, no premium or discount to NAV,
  and no spread beyond the slippage tier.
- **Unequal starts.** The benchmarks hold from the 2016-01-04 open; the run holds cash
  until 2016-11-01. This is the same warm-up as strategies 2 and 3.
- **Opening prices.** The 2016-01-04 opens were 0.1% to 3.2% above that day's closes,
  so both benchmarks lost that much on their first day.

## Reproduce

    uv run python scripts/build_etf_proxy.py
    uv run python -m nsealgo.backtest --strategy sector_rotation --period dev --cost-tier none --brokerage zero
    uv run python -m nsealgo.backtest --strategy sector_rotation --period dev --cost-tier base
    uv run python -m nsealgo.backtest --strategy sector_rotation --period dev --cost-tier stress1
    uv run python -m nsealgo.backtest --strategy sector_rotation --period dev --cost-tier stress2
    uv run python scripts/report_runs.py summary Reference=<none dir> Base=<base dir> Stress1=<stress1 dir> Stress2=<stress2 dir>
    uv run python scripts/report_runs.py detail <base dir> --all-symbols --sort net_pnl
    uv run python scripts/report_runs.py benchmark <base dir>
    uv run python scripts/report_runs.py benchmark <base dir> --exclude PX_IT

Run dirs (local, not committed):

- `research/runs/20261029-024228_sector_rotation_dev_none`
- `research/runs/20261029-024230_sector_rotation_dev_base`
- `research/runs/20261029-024231_sector_rotation_dev_stress1`
- `research/runs/20261029-024233_sector_rotation_dev_stress2`

The by-tier year tables, sessions held and time in market were computed from those
directories' parquet files and the calendar (one-off script, not in the repo).
