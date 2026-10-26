# ORB v1 (strategy 1): dev-period result

30-minute Opening Range Breakout, `orb` version 1, parameters exactly as in
`config/strategies/orb.yaml` at the commits below (not optimized):
5m bars; opening range = bars 09:15-09:40, known at 09:45; long stop-entry at
ORH x 1.0005, short at ORL x 0.9995, both in one OCO group; stop at the far side of the
range (`full`); target 2R; time exit 14:30; flat by 14:50 (RiskGovernor); filters range
width 0.25-2.5% of the open and |gap| <= 0.8% on, previous-day high/low, Nifty
direction and day-of-week off; candidates ranked by range / ATR14, narrowest first.

- Period: dev, 2016-01-01 .. 2023-12-31 (1,971 sessions). Validation and holdout were not
  touched.
- Universe: the 40 symbols of `config/universe.yaml` (not point-in-time: survivorship
  bias is built in).
- Risk (`config/risk.yaml`): capital Rs 20,000; Rs 100 risk per trade; 2 trades per day;
  Rs 60,000 gross exposure; MIS margin 25% (default for every symbol); entries
  09:45-14:00.
- Costs: statutory charges from `config/costs.yaml` on every fill, shoonya brokerage
  (lower of Rs 5 and 0.03% per order) unless stated, slippage per side by tier.
- Trials: 7 lines in `research/trials.jsonl`. Trials 1-6 ran on the code committed as
  b90fa1c (logged as fe03135 + uncommitted changes) with current-equity sizing.
  Trial 7 ran on 11ad478 (clean) with fixed-capital sizing.
- Gross bps, cost bps and net bps are means over trades of P&L / entry notional;
  cost = charges + slippage. Sharpe is daily, annualized. "Skipped groups" are OCO
  groups the RiskGovernor rejected with MAX_TRADES_PER_DAY (ranked below the day's
  first two).

## Read this first: the account drained in trials 1-6

Trials 1-6 sized from current equity, and backtests keep trading after the 15% halt
(`halt_mode.backtest: record`; the halt would have fired on 2016-05-12). Losses shrank
every later position: at the base tier equity fell to about Rs 1,570 by April 2019 and
Rs 65 by November 2020; the median position was 1 share in 2021 and 2022, with 5
trades in 2022 and none in 2023. Rupee figures, drawdowns, Sharpe and trade counts in trials 1-6 mostly
describe that drain, and the costed tiers do not cover the same trades (higher costs
drain sooner). Net bps per trade is the comparable figure. Trial 7 repeats the base
tier with fixed-capital sizing so that every year trades at full size.

Median entry notional (Rs) by year:

| Run | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 |
|---|---|---|---|---|---|---|---|---|
| Base, current equity (trial 1) | 14,956 | 15,416 | 8,789 | 1,311 | 303 | 128 | 86 | - |
| Base, fixed capital (trial 7) | 14,956 | 16,741 | 13,615 | 13,446 | 10,495 | 12,414 | 12,135 | 15,561 |

## 1. Cost tiers (trials 1-4, current-equity sizing)

| Run | Ref tier | Sizing | Trades | Win % | Avg win Rs | Avg loss Rs | Gross bps | Cost bps | Net bps | PF | Max DD Rs | Max DD % | Sharpe (daily, ann.) | Net Rs | Skipped groups |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Statutory only: zero brokerage, 0 bps (trial 2) | REFERENCE | current_equity | 3,785 | 44.7% | 100 | -81 | 3.6 | 3.5 | 0.1 | 1.01 | 6,329 | 26.1% | 0.11 | 947 | 55,304 |
| Base: shoonya, 3 bps (trial 1) |  | current_equity | 2,213 | 39.2% | 54 | -49 | 2.2 | 16.3 | -14.1 | 0.70 | 20,041 | 99.9% | -2.17 | -19,981 | 25,634 |
| Stress1: shoonya, 6 bps (trial 3) |  | current_equity | 1,701 | 37.4% | 42 | -44 | 3.0 | 22.2 | -19.2 | 0.57 | 20,036 | 100.0% | -2.75 | -19,990 | 18,914 |
| Stress2: shoonya, 10 bps (trial 4) |  | current_equity | 1,379 | 36.4% | 35 | -43 | 6.2 | 30.0 | -23.8 | 0.47 | 20,016 | 100.0% | -2.96 | -19,991 | 13,556 |

The statutory-only tier is a reference tier: no broker charges and no slippage, not a
tradeable result.

## 2. Gate A items measured so far

| Gate A item | Threshold | Value |
|---|---|---|
| Dev-period trades | >= 300 | 2,213 (trial 1); 3,785 (trial 7) |
| Net expectancy at double the modeled slippage (stress1, 6 bps) | > 0 | -19.2 bps/trade (trial 3) |
| Walk-forward OOS expectancy and profit factor | > 0 and >= 1.15 | not run |
| Parameter neighbours | >= 50% of chosen | not run |
| Deflated Sharpe | >= 0.90 | not computed |
| Holdout | net positive, once | not run |
| P(15% drawdown within 250 days) | < 10% | not computed |

## 3. Filter toggles (base tier, trials 1, 5, 6)

| Run | Ref tier | Sizing | Trades | Win % | Avg win Rs | Avg loss Rs | Gross bps | Cost bps | Net bps | PF | Max DD Rs | Max DD % | Sharpe (daily, ann.) | Net Rs | Skipped groups |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Defaults: width on, gap on, PDH/PDL off (trial 1) |  | current_equity | 2,213 | 39.2% | 54 | -49 | 2.2 | 16.3 | -14.1 | 0.70 | 20,041 | 99.9% | -2.17 | -19,981 | 25,634 |
| range_width off (trial 5) |  | current_equity | 2,239 | 39.2% | 55 | -50 | 3.2 | 16.2 | -13.1 | 0.71 | 20,041 | 99.9% | -2.16 | -19,981 | 27,346 |
| gap off (trial 6) |  | current_equity | 2,229 | 38.9% | 57 | -51 | 1.9 | 16.2 | -14.4 | 0.71 | 20,876 | 99.9% | -2.06 | -19,980 | 31,257 |

Not run, by the owner's decision: previous-day high/low confluence on, Nifty direction
on (no NIFTY index data in `data/raw`), ranking widest-first. Day-of-week stays off.

## 4. Breakdowns, base tier, current-equity sizing (trial 1)

### By year

| Year | Trades | Win % | Avg win Rs | Avg loss Rs | Gross bps | Cost bps | Net bps | PF | Net Rs | Max DD % | Sharpe |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2016 | 436 | 42.9% | 100 | -95 | 7.8 | 16.2 | -8.4 | 0.78 | -5,137 | 32.0% | -1.96 |
| 2017 | 474 | 37.6% | 85 | -86 | -1.7 | 16.1 | -17.7 | 0.59 | -10,259 | 70.2% | -4.70 |
| 2018 | 414 | 39.4% | 61 | -50 | 9.2 | 16.5 | -7.3 | 0.80 | -2,481 | 56.8% | -1.33 |
| 2019 | 406 | 37.7% | 15 | -17 | -3.4 | 16.4 | -19.8 | 0.55 | -1,885 | 89.5% | -4.39 |
| 2020 | 348 | 39.1% | 4 | -3 | 0.3 | 16.4 | -16.1 | 0.75 | -182 | 81.2% | -2.02 |
| 2021 | 130 | 38.5% | 1 | -1 | 1.3 | 16.5 | -15.2 | 0.68 | -32 | 70.6% | -2.04 |
| 2022 | 5 | 0.0% | - | -1 | -105.6 | 15.6 | -121.2 | 0.00 | -5 | 20.8% | -2.01 |

Statutory-only reference tier by year (trial 2; never short of margin, so every year
traded at full size):

| Year | Trades | Win % | Avg win Rs | Avg loss Rs | Gross bps | Cost bps | Net bps | PF | Net Rs | Max DD % | Sharpe |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2016 | 436 | 47.7% | 108 | -84 | 7.8 | 3.5 | 4.3 | 1.17 | 3,241 | 8.6% | 1.37 |
| 2017 | 481 | 43.5% | 101 | -84 | -1.1 | 3.5 | -4.6 | 0.92 | -1,741 | 11.4% | -0.70 |
| 2018 | 485 | 43.3% | 115 | -84 | 8.2 | 3.5 | 4.6 | 1.04 | 890 | 7.4% | 0.44 |
| 2019 | 482 | 44.2% | 95 | -84 | -1.2 | 3.5 | -4.7 | 0.89 | -2,515 | 14.8% | -1.00 |
| 2020 | 454 | 43.8% | 100 | -81 | 3.6 | 3.5 | 0.1 | 0.97 | -641 | 13.2% | -0.24 |
| 2021 | 482 | 45.2% | 97 | -78 | 5.7 | 3.5 | 2.2 | 1.04 | 779 | 12.2% | 0.40 |
| 2022 | 481 | 44.9% | 93 | -75 | 1.7 | 3.5 | -1.8 | 1.01 | 164 | 13.6% | 0.13 |
| 2023 | 484 | 45.2% | 94 | -75 | 4.3 | 3.5 | 0.8 | 1.04 | 771 | 16.1% | 0.41 |

### Long vs short

| Side | Trades | Win % | Avg win Rs | Avg loss Rs | Gross bps | Cost bps | Net bps | PF | Net Rs |
|---|---|---|---|---|---|---|---|---|---|
| long | 995 | 39.0% | 61 | -52 | 1.2 | 16.3 | -15.1 | 0.76 | -7,517 |
| short | 1,218 | 39.3% | 48 | -48 | 2.9 | 16.3 | -13.4 | 0.65 | -12,464 |

### By exit reason

| Exit | Trades | Win % | Avg win Rs | Avg loss Rs | Gross bps | Cost bps | Net bps | PF | Net Rs |
|---|---|---|---|---|---|---|---|---|---|
| stop | 846 | 0.0% | - | -67 | -80.4 | 16.3 | -96.8 | 0.00 | -56,385 |
| strategy | 1,068 | 53.2% | 27 | -20 | 25.9 | 16.3 | 9.6 | 1.49 | 4,943 |
| target | 299 | 100.0% | 105 | - | 151.0 | 16.3 | 134.8 | - | 31,461 |

### Symbols, ranked by net bps per trade (small samples: 13-95 trades each)

Top 5:

| Symbol | Trades | Win % | Avg win Rs | Avg loss Rs | Gross bps | Cost bps | Net bps | PF | Net Rs |
|---|---|---|---|---|---|---|---|---|---|
| HINDALCO | 33 | 54.5% | 69 | -71 | 31.5 | 16.7 | 14.9 | 1.17 | 179 |
| BAJAJ-AUTO | 20 | 60.0% | 55 | -41 | 25.5 | 16.4 | 9.2 | 2.01 | 333 |
| AXISBANK | 46 | 45.7% | 65 | -54 | 20.0 | 16.5 | 3.5 | 1.00 | -3 |
| SUNPHARMA | 58 | 44.8% | 78 | -49 | 16.6 | 16.4 | 0.2 | 1.30 | 462 |
| ADANIENT | 95 | 43.2% | 81 | -59 | 16.7 | 16.6 | 0.2 | 1.04 | 125 |

Bottom 5:

| Symbol | Trades | Win % | Avg win Rs | Avg loss Rs | Gross bps | Cost bps | Net bps | PF | Net Rs |
|---|---|---|---|---|---|---|---|---|---|
| ASIANPAINT | 13 | 23.1% | 63 | -87 | -27.5 | 16.0 | -43.5 | 0.22 | -685 |
| KOTAKBANK | 45 | 24.4% | 53 | -42 | -26.3 | 16.5 | -42.8 | 0.41 | -831 |
| TITAN | 34 | 26.5% | 50 | -72 | -20.7 | 16.5 | -37.2 | 0.25 | -1,340 |
| MARUTI | 24 | 25.0% | 61 | -75 | -20.3 | 16.3 | -36.6 | 0.27 | -980 |
| TCS | 29 | 24.1% | 58 | -75 | -20.2 | 16.1 | -36.3 | 0.24 | -1,253 |

## 5. Rerun with fixed-capital sizing (trial 7)

Same strategy version, parameters, period and base tier; every session sized off Rs
20,000 with no compounding (`sizing_basis.backtest: fixed_capital`, commit 11ad478).
Equity is the real cumulative account, so it goes below zero (final Rs -46,066). Max
DD % in the summary row is of the running peak, as logged; the by-year Max DD % is the
in-year drawdown as a percent of the Rs 20,000 capital. Daily returns for Sharpe are
P&L / capital.

| Run | Ref tier | Sizing | Trades | Win % | Avg win Rs | Avg loss Rs | Gross bps | Cost bps | Net bps | PF | Max DD Rs | Max DD % | Sharpe (daily, ann.) | Net Rs | Skipped groups |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Base, fixed capital (trial 7) |  | fixed_capital | 3,785 | 39.5% | 95 | -91 | 3.6 | 16.3 | -12.7 | 0.68 | 66,648 | 332.2% | -3.60 | -66,066 | 55,304 |

### By year

| Year | Trades | Win % | Avg win Rs | Avg loss Rs | Gross bps | Cost bps | Net bps | PF | Net Rs | Max DD % | Sharpe |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2016 | 436 | 42.9% | 100 | -95 | 7.8 | 16.2 | -8.4 | 0.78 | -5,137 | 32.1% | -2.21 |
| 2017 | 481 | 38.0% | 93 | -97 | -1.1 | 15.9 | -17.0 | 0.59 | -11,715 | 61.5% | -5.00 |
| 2018 | 485 | 38.4% | 111 | -95 | 8.2 | 16.3 | -8.1 | 0.73 | -7,721 | 40.5% | -3.38 |
| 2019 | 482 | 37.8% | 92 | -92 | -1.2 | 16.3 | -17.5 | 0.60 | -10,981 | 57.6% | -4.62 |
| 2020 | 454 | 40.7% | 93 | -90 | 3.6 | 16.5 | -12.9 | 0.71 | -7,129 | 38.3% | -3.24 |
| 2021 | 482 | 40.5% | 92 | -87 | 5.7 | 16.5 | -10.7 | 0.72 | -7,023 | 38.9% | -3.00 |
| 2022 | 481 | 39.3% | 89 | -83 | 1.7 | 16.4 | -14.7 | 0.69 | -7,542 | 38.6% | -3.34 |
| 2023 | 484 | 39.0% | 87 | -86 | 4.3 | 16.0 | -11.7 | 0.65 | -8,818 | 47.8% | -3.98 |

### Long vs short

| Side | Trades | Win % | Avg win Rs | Avg loss Rs | Gross bps | Cost bps | Net bps | PF | Net Rs |
|---|---|---|---|---|---|---|---|---|---|
| long | 1,723 | 38.8% | 95 | -93 | 2.2 | 16.3 | -14.1 | 0.65 | -34,733 |
| short | 2,062 | 40.2% | 94 | -88 | 4.7 | 16.3 | -11.5 | 0.71 | -31,332 |

### By exit reason

| Exit | Trades | Win % | Avg win Rs | Avg loss Rs | Gross bps | Cost bps | Net bps | PF | Net Rs |
|---|---|---|---|---|---|---|---|---|---|
| stop | 1,439 | 0.0% | - | -120 | -74.9 | 16.2 | -91.1 | 0.00 | -172,225 |
| strategy | 1,820 | 53.3% | 54 | -42 | 25.0 | 16.3 | 8.7 | 1.48 | 17,044 |
| target | 526 | 100.0% | 169 | - | 144.1 | 16.1 | 127.9 | - | 89,115 |

### Symbols, ranked by net bps per trade

Top 5:

| Symbol | Trades | Win % | Avg win Rs | Avg loss Rs | Gross bps | Cost bps | Net bps | PF | Net Rs |
|---|---|---|---|---|---|---|---|---|---|
| CIPLA | 95 | 42.1% | 99 | -74 | 16.5 | 16.4 | 0.1 | 0.97 | -103 |
| SUNPHARMA | 107 | 43.0% | 100 | -82 | 16.4 | 16.4 | 0.0 | 0.92 | -397 |
| DLF | 135 | 43.7% | 118 | -95 | 15.5 | 16.6 | -1.1 | 0.97 | -238 |
| DRREDDY | 111 | 46.8% | 76 | -82 | 14.9 | 16.3 | -1.4 | 0.82 | -892 |
| ADANIENT | 170 | 42.9% | 108 | -84 | 14.7 | 16.6 | -1.9 | 0.97 | -248 |

Bottom 5:

| Symbol | Trades | Win % | Avg win Rs | Avg loss Rs | Gross bps | Cost bps | Net bps | PF | Net Rs |
|---|---|---|---|---|---|---|---|---|---|
| KOTAKBANK | 96 | 28.1% | 105 | -103 | -17.4 | 16.2 | -33.6 | 0.40 | -4,262 |
| TITAN | 73 | 27.4% | 97 | -90 | -16.3 | 16.5 | -32.8 | 0.41 | -2,841 |
| TCS | 74 | 29.7% | 74 | -84 | -13.2 | 16.2 | -29.4 | 0.37 | -2,722 |
| GRASIM | 86 | 37.2% | 84 | -99 | -11.9 | 16.4 | -28.3 | 0.50 | -2,652 |
| ASIANPAINT | 43 | 32.6% | 80 | -94 | -9.7 | 16.0 | -25.7 | 0.41 | -1,596 |

## Decision

Owner's decision, 2026-10-27: base nets -14.1 bps/trade, the statutory-only reference
tier is about break-even (+0.1 bps/trade), and the filter toggles moved net by about
1 bps, so no further filters or tuning on this version.

Status: fails Gate A, parked.
