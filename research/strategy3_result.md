# Strategy 3, pullback mean reversion v1: dev-period result

Pre-registered in `research/strategy3_plan.md` (43785c4), committed and pushed before
any run. Rules, parameters and definitions are exactly as there.

Run facts:

- **Code:** `pullback` version 1 at dda3993. All four runs on that commit, clean tree, no
  run warnings.
- **Trials:** 14 (none), 15 (base), 16 (stress1), 17 (stress2). The DSR trial count is
  now 17: 7 ORB, 6 swing, 4 pullback.
- **Period:** dev, 2016-01-01 .. 2023-12-31, 1,971 sessions (7.82 years of 252).
  Validation and holdout were not touched.
- **Warm-up:** the first entry was filled on 2016-10-27, once the 200-session average
  existed.
- **Universe:** the 40 symbols of `config/universe.yaml`: today's large caps, not
  point-in-time.
- **Risk:** the swing block of `config/risk.yaml`, unchanged.
  - Sizing off current equity, as in paper and live. The first slot was Rs 4,944.
  - 4 positions, 1% cash buffer, 30% position cap, 100% gross cap.
- **Costs:** delivery statutory charges on every fill, shoonya (zero brokerage, DP
  Rs 9 + GST = Rs 10.62 per sale), plus slippage per tier. The reference tier uses the
  `zero` preset (no DP) and 0 bps.
- **Definitions:** as in `swing_v1_result.md`.
  - Bps are means over trades of P&L / entry notional; cost = charges + slippage.
  - Max DD % is of the running peak. Sharpe uses daily returns over the previous
    equity.
  - Turnover (one-way) and "costs % capital" are over the Rs 20,000 starting capital.

## 1. Cost tiers (trials 14-17)

| Run | Trades | Win % | Avg win Rs | Avg loss Rs | Gross bps | Cost bps | Net bps | PF | Max DD Rs | Max DD % | Sharpe (daily, ann.) | Net Rs | Final equity Rs | Cap skips | Turnover x/yr | Costs % cap/yr |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Reference: zero brokerage, 0 bps (trial 14), REFERENCE | 1,040 | 62.6% | 75 | -141 | 14.6 | 22.2 | -7.6 | 0.89 | 10,643 | 46.1% | -0.21 | -5,790 | 14,210 | 70 | 26.87 | 6.0% |
| Base: shoonya, 3 bps (trial 15) | 1,021 | 53.5% | 51 | -89 | 22.2 | 73.9 | -51.7 | 0.66 | 14,957 | 72.9% | -1.02 | -14,292 | 5,708 | 226 | 18.83 | 12.2% |
| Stress1: shoonya, 6 bps (trial 16) | 1,015 | 51.2% | 49 | -82 | 22.6 | 83.1 | -60.5 | 0.63 | 15,800 | 77.0% | -1.19 | -15,207 | 4,793 | 255 | 17.91 | 13.0% |
| Stress2: shoonya, 10 bps (trial 17) | 994 | 47.3% | 45 | -72 | 23.7 | 99.1 | -75.4 | 0.56 | 16,995 | 82.9% | -1.41 | -16,466 | 3,534 | 384 | 16.04 | 13.5% |

- The reference tier is not a tradeable result.
- **Net per trade:** Rs -5.57 (reference), -14.00 (base), -14.98 (stress1) and -16.57
  (stress2).
- **Trades per year:** 133.0, 130.5, 129.8 and 127.1. Base by entry year is in
  section 4.
- **Exits:** every exit was a strategy exit, except one `end_of_run` close in each
  stress tier.
- **Base P&L split:** gross P&L at reference prices was Rs +4,855, costs were
  Rs 19,147 and net was Rs -14,292.
- **Why tiers trade differently:** gross bps and trade counts differ between tiers
  because the account sizes differ, which changes position caps, skips and later
  holdings.

## 2. Gate A items

| Gate A item | Threshold | Value |
|---|---|---|
| Dev-period trades (swing) | >= 100 | 1,021 (base, trial 15) |
| Net expectancy at double the modeled slippage (stress1, 6 bps) | > 0 | -60.5 bps/trade, Rs -14.98/trade (trial 16) |
| Long-only: beats equal-weight buy-and-hold of the universe after costs | overall and in at least 5 of 8 dev years | -417.0 pp overall; ahead in 0 of 8 years (section 8) |
| Walk-forward OOS expectancy and profit factor | > 0 and >= 1.15 | not run |
| Parameter neighbours | >= 50% of chosen | not run |
| Deflated Sharpe | >= 0.90 | not computed (17 trials logged) |
| Holdout | net positive, once | not run |
| P(15% drawdown within 250 days) | < 10% | not computed. The 15% account-drawdown halt would have fired on 2016-11-15 in all four runs (record mode), the 12th session counting the first entry's fill session (2016-10-27). |

## 3. Read this before the tables

**The account shrank, and costs per trade grew with it.** Sizing is off current
equity, so slots fell with the account. The DP charge is a fixed Rs 10.62 per sale.

| Entry year | Base trades | Median entry notional Rs | DP + GST as bps of that | Base cost bps | Base equity at year end Rs |
|---|---|---|---|---|---|
| 2016 | 27 | 4,411 | 24 | 52.5 | 17,776 |
| 2017 | 169 | 4,378 | 24 | 54.0 | 17,733 |
| 2018 | 144 | 3,915 | 27 | 56.1 | 16,832 |
| 2019 | 145 | 3,687 | 29 | 59.1 | 15,420 |
| 2020 | 115 | 2,401 | 44 | 71.4 | 11,020 |
| 2021 | 174 | 2,368 | 45 | 77.4 | 9,733 |
| 2022 | 103 | 1,736 | 61 | 92.6 | 6,992 |
| 2023 | 144 | 1,254 | 85 | 118.3 | 5,708 |

The reference tier pays no DP charge and no slippage. Its cost is 22.1-22.3 bps per
trade in every year.

**Position-cap skips grew too.** The 30% cap is of current equity. As the account fell,
one share of higher-priced stocks went above it.

- Base skipped 226 candidates at 184 decisions; the reference tier skipped 70.
- Base skips by symbol: MARUTI 53, BAJAJ-AUTO 35, ULTRACEMCO 24, HINDUNILVR 24,
  ASIANPAINT 17, TCS 16, HEROMOTOCO 13, TITAN 13, EICHERMOT 11, ADANIENT 11, LT 6,
  GRASIM 3.
- Review then moved to the next rank, so another candidate took the slot. The full list
  is in `report_runs.py detail`.

**Exit split, base (classified after the run, as the plan defines):**

| Exit | Trades | Win % | Avg win Rs | Avg loss Rs | Gross bps | Cost bps | Net bps | PF | Net Rs | Mean sessions held |
|---|---|---|---|---|---|---|---|---|---|---|
| Close above the 5-session average | 989 | 55.2% | 51 | -68 | 59.4 | 74.2 | -14.8 | 0.92 | -2,344 | 3.6 |
| 10 sessions held | 32 | 0.0% | - | -373 | -1129.1 | 64.2 | -1193.3 | 0.00 | -11,947 | 10.0 |

- All 32 time exits lost. Together they are 84% of the base net loss.
- The three largest losses were March 2020 entries: ICICIBANK (2020-03-09), BAJFINANCE
  and TITAN (both 2020-03-11). They lost Rs 1,276, Rs 1,270 and Rs 814.
- There is no stop loss, by rule.

| Entry year | 5-average exits | Net Rs | 10-session exits | Net Rs |
|---|---|---|---|---|
| 2016 | 27 | -2,193 | 0 | 0 |
| 2017 | 165 | +1,388 | 4 | -1,572 |
| 2018 | 138 | +1,612 | 6 | -2,398 |
| 2019 | 139 | +152 | 6 | -1,568 |
| 2020 | 110 | -739 | 5 | -3,661 |
| 2021 | 169 | +160 | 5 | -1,447 |
| 2022 | 98 | -1,502 | 5 | -1,240 |
| 2023 | 143 | -1,221 | 1 | -62 |

**`MAX_POSITIONS` rejections** are candidates beyond the free slots: 1,826 in base. The
strategy emits every candidate and the RiskGovernor buys in rank order.

**Survivorship.** The universe is today's large caps. A dip-buying rule never meets the
dips of stocks that later collapsed, because those stocks are not in the data.

## 4. By year

Base tier, by entry year (Max DD % and Sharpe from that calendar year's sessions):

| Year | Trades | Win % | Avg win Rs | Avg loss Rs | Gross bps | Cost bps | Net bps | PF | Net Rs | Max DD % | Sharpe |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2016 | 27 | 40.7% | 134 | -229 | -127.6 | 52.5 | -180.1 | 0.40 | -2,193 | 15.7% | -0.94 |
| 2017 | 169 | 62.1% | 64 | -108 | 52.4 | 54.0 | -1.5 | 0.97 | -184 | 12.6% | 0.04 |
| 2018 | 144 | 63.2% | 70 | -135 | 47.3 | 56.1 | -8.8 | 0.89 | -787 | 12.7% | -0.30 |
| 2019 | 145 | 53.8% | 52 | -82 | 31.1 | 59.1 | -28.0 | 0.74 | -1,417 | 12.0% | -0.75 |
| 2020 | 115 | 60.9% | 48 | -172 | -28.7 | 71.4 | -100.0 | 0.43 | -4,400 | 40.4% | -1.27 |
| 2021 | 174 | 53.4% | 41 | -63 | 47.5 | 77.4 | -29.9 | 0.75 | -1,287 | 16.7% | -0.69 |
| 2022 | 103 | 41.7% | 34 | -70 | -54.2 | 92.6 | -146.8 | 0.35 | -2,742 | 29.4% | -2.47 |
| 2023 | 144 | 38.2% | 14 | -23 | 45.1 | 118.3 | -73.2 | 0.37 | -1,283 | 21.0% | -2.68 |

Net bps per trade / trades, by entry year and tier:

| Year | Reference | Base | Stress1 | Stress2 |
|---|---|---|---|---|
| 2016 | -149.7 / 27 | -180.1 / 27 | -186.0 / 27 | -193.9 / 27 |
| 2017 | 30.2 / 169 | -1.5 / 169 | -7.9 / 169 | -16.5 / 169 |
| 2018 | 25.1 / 144 | -8.8 / 144 | -15.7 / 144 | -27.1 / 144 |
| 2019 | 8.9 / 145 | -28.0 / 145 | -35.6 / 145 | -47.4 / 145 |
| 2020 | -62.2 / 115 | -100.0 / 115 | -102.2 / 116 | -117.9 / 111 |
| 2021 | 15.0 / 172 | -29.9 / 174 | -39.6 / 173 | -49.8 / 170 |
| 2022 | -61.6 / 117 | -146.8 / 103 | -159.0 / 102 | -191.5 / 100 |
| 2023 | -13.6 / 151 | -73.2 / 144 | -91.1 / 139 | -120.9 / 128 |

### Turnover and costs, base tier, by year of each fill

| Year | Bought Rs | Sold Rs | Turnover x | Charges Rs | DP Rs (pre-GST) | Slippage Rs | Costs Rs | Costs % capital | Average equity Rs | Costs % average equity |
|---|---|---|---|---|---|---|---|---|---|---|
| 2016 | 118,872 | 108,887 | 5.69 | 519 | 225 | 68 | 587 | 2.9% | 19,713 | 3.0% |
| 2017 | 710,385 | 709,256 | 35.49 | 3,360 | 1,512 | 426 | 3,786 | 18.9% | 18,318 | 20.7% |
| 2018 | 553,878 | 564,704 | 27.96 | 2,791 | 1,314 | 336 | 3,127 | 15.6% | 16,770 | 18.6% |
| 2019 | 514,504 | 519,579 | 25.85 | 2,698 | 1,314 | 310 | 3,008 | 15.0% | 16,030 | 18.8% |
| 2020 | 295,357 | 292,832 | 14.70 | 1,874 | 1,035 | 176 | 2,051 | 10.3% | 11,069 | 18.5% |
| 2021 | 392,925 | 394,359 | 19.68 | 2,721 | 1,566 | 236 | 2,957 | 14.8% | 10,563 | 28.0% |
| 2022 | 178,148 | 175,806 | 8.85 | 1,477 | 918 | 106 | 1,583 | 7.9% | 8,149 | 19.4% |
| 2023 | 179,221 | 180,955 | 9.00 | 1,940 | 1,305 | 108 | 2,048 | 10.2% | 6,097 | 33.6% |

- Charges include STT, stamp, exchange and SEBI fees, GST and the DP charge.
- Average equity is the mean session-end equity of that year. That column was added
  because the account fell to under a third of capital.

Costs (charges + slippage) as % of the Rs 20,000 capital, by year and tier:

| Year | Reference | Base | Stress1 | Stress2 |
|---|---|---|---|---|
| 2016 | 1.3% | 2.9% | 3.3% | 3.7% |
| 2017 | 8.6% | 18.9% | 20.9% | 23.4% |
| 2018 | 7.5% | 15.6% | 17.0% | 18.2% |
| 2019 | 8.1% | 15.0% | 16.1% | 17.1% |
| 2020 | 4.6% | 10.3% | 10.8% | 10.7% |
| 2021 | 7.3% | 14.8% | 15.5% | 15.5% |
| 2022 | 4.5% | 7.9% | 8.1% | 7.9% |
| 2023 | 4.9% | 10.2% | 10.1% | 9.2% |

## 5. Holding period (base)

- **Sessions held, as defined in the plan:** median 3, mean 3.84, max 11. Calendar
  days: median 5.0, mean 5.6, max 18.
- **The one 11-session hold:** EICHERMOT, bought 2021-02-12. It reached 10 sessions on
  2021-02-25, a no_trade session, so the exit was decided on 2021-02-26.

| Sessions held | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Trades | 161 | 202 | 202 | 146 | 88 | 64 | 51 | 33 | 21 | 52 | 1 |

21 of the 52 ten-session holds were 5-average exits on their tenth close; 31 were 10-session exits.

## 6. By symbol (base, trial 15)

All 40 symbols were traded, ranked by net bps per trade:

| Symbol | Trades | Win % | Avg win Rs | Avg loss Rs | Gross bps | Cost bps | Net bps | PF | Net Rs |
|---|---|---|---|---|---|---|---|---|---|
| ULTRACEMCO | 10 | 70.0% | 53 | -59 | 106.0 | 54.0 | 52.1 | 2.11 | 196 |
| SUNPHARMA | 27 | 51.9% | 61 | -28 | 123.6 | 91.3 | 32.3 | 2.36 | 494 |
| HINDALCO | 20 | 75.0% | 83 | -224 | 88.4 | 68.8 | 19.6 | 1.11 | 124 |
| TCS | 29 | 69.0% | 34 | -58 | 80.6 | 65.8 | 14.8 | 1.28 | 147 |
| POWERGRID | 31 | 64.5% | 42 | -55 | 75.2 | 69.4 | 5.8 | 1.36 | 221 |
| BAJAJ-AUTO | 15 | 46.7% | 39 | -34 | 65.9 | 64.7 | 1.2 | 1.00 | -1 |
| ADANIPORTS | 24 | 58.3% | 65 | -80 | 84.2 | 84.4 | -0.2 | 1.13 | 105 |
| JSWSTEEL | 29 | 62.1% | 72 | -99 | 68.5 | 71.9 | -3.4 | 1.19 | 206 |
| ASIANPAINT | 25 | 64.0% | 47 | -97 | 57.1 | 60.9 | -3.8 | 0.87 | -117 |
| HINDUNILVR | 29 | 51.7% | 31 | -28 | 63.3 | 67.2 | -4.0 | 1.17 | 67 |
| CIPLA | 31 | 54.8% | 51 | -79 | 75.8 | 81.0 | -5.2 | 0.78 | -241 |
| LT | 22 | 54.5% | 45 | -59 | 63.5 | 70.2 | -6.7 | 0.91 | -53 |
| RELIANCE | 47 | 59.6% | 44 | -71 | 68.5 | 75.4 | -6.9 | 0.90 | -129 |
| TECHM | 31 | 71.0% | 53 | -87 | 73.8 | 80.9 | -7.2 | 1.49 | 382 |
| BHARTIARTL | 39 | 46.2% | 51 | -57 | 68.3 | 79.7 | -11.5 | 0.76 | -289 |
| ITC | 24 | 45.8% | 52 | -54 | 52.2 | 71.8 | -19.6 | 0.82 | -123 |
| KOTAKBANK | 28 | 50.0% | 35 | -55 | 31.3 | 67.0 | -35.7 | 0.63 | -286 |
| BPCL | 28 | 53.6% | 70 | -89 | 32.9 | 70.3 | -37.4 | 0.91 | -100 |
| SBIN | 27 | 51.9% | 56 | -82 | 34.8 | 72.3 | -37.5 | 0.74 | -272 |
| ONGC | 24 | 54.2% | 39 | -64 | 35.0 | 76.0 | -41.0 | 0.71 | -203 |
| HDFCBANK | 28 | 42.9% | 30 | -38 | 32.8 | 80.5 | -47.7 | 0.59 | -253 |
| NTPC | 29 | 51.7% | 35 | -68 | 18.9 | 70.3 | -51.4 | 0.56 | -423 |
| AXISBANK | 24 | 41.7% | 18 | -34 | 40.7 | 93.2 | -52.5 | 0.38 | -297 |
| DRREDDY | 27 | 44.4% | 40 | -57 | 21.7 | 78.3 | -56.6 | 0.55 | -384 |
| ICICIBANK | 37 | 56.8% | 79 | -123 | 13.7 | 76.3 | -62.5 | 0.84 | -311 |
| TATASTEEL | 23 | 52.2% | 62 | -104 | 2.1 | 70.0 | -68.0 | 0.65 | -404 |
| INFY | 23 | 47.8% | 47 | -54 | 4.2 | 76.9 | -72.7 | 0.79 | -140 |
| WIPRO | 23 | 56.5% | 63 | -121 | -9.5 | 64.9 | -74.4 | 0.68 | -390 |
| INDUSINDBK | 22 | 40.9% | 43 | -61 | 0.5 | 77.3 | -76.7 | 0.49 | -403 |
| EICHERMOT | 25 | 56.0% | 50 | -119 | -5.8 | 71.2 | -77.0 | 0.54 | -606 |
| GRASIM | 23 | 43.5% | 35 | -71 | -12.6 | 78.5 | -91.1 | 0.38 | -575 |
| HCLTECH | 30 | 43.3% | 33 | -58 | -13.4 | 80.6 | -93.9 | 0.43 | -559 |
| BAJAJFINSV | 29 | 51.7% | 43 | -114 | -29.9 | 69.1 | -99.0 | 0.40 | -953 |
| TITAN | 30 | 66.7% | 51 | -172 | -34.1 | 68.4 | -102.5 | 0.60 | -696 |
| HEROMOTOCO | 15 | 53.3% | 56 | -140 | -54.4 | 62.8 | -117.1 | 0.46 | -529 |
| COALINDIA | 20 | 30.0% | 61 | -87 | -65.3 | 78.8 | -144.1 | 0.30 | -856 |
| BAJFINANCE | 33 | 57.6% | 60 | -236 | -116.4 | 74.3 | -190.7 | 0.35 | -2,162 |
| DLF | 18 | 38.9% | 43 | -194 | -155.2 | 72.8 | -228.0 | 0.14 | -1,837 |
| ADANIENT | 21 | 42.9% | 123 | -281 | -217.0 | 69.0 | -285.9 | 0.33 | -2,270 |
| MARUTI | 1 | 0.0% | - | -374 | -659.5 | 47.4 | -706.9 | 0.00 | -374 |

## 7. Rejections by reason

| Reason | Reference | Base | Stress1 | Stress2 |
|---|---|---|---|---|
| `MAX_POSITIONS` (candidates beyond the free slots) | 1,918 | 1,826 | 1,816 | 1,728 |
| `PRICE_ABOVE_POSITION_CAP` | 70 | 226 | 255 | 384 |
| `QTY_BELOW_ONE` | 0 | 2 | 4 | 3 |
| `INSUFFICIENT_CASH` (at the open) | 0 | 0 | 0 | 0 |

## 8. Base (trial 15) vs equal-weight buy-and-hold

The benchmark is `reporting/benchmark.py`, as in `swing_v1_result.md` section 7.

- It holds the 40 symbols, Rs 500 each, in fractional shares.
- They are bought at the 2016-01-04 open with one base-tier buy each, and held to the
  2023-12-29 close.
- It is never rebalanced and pays no sell costs.
- The strategy held nothing before 2016-10-27.

| Year | Pullback return % | Pullback max DD % | Benchmark return % | Benchmark max DD % | Excess return, pp |
|---|---|---|---|---|---|
| 2016 | -11.1% | 15.7% | 10.5% | 12.3% | -21.7 |
| 2017 | -0.2% | 12.6% | 45.0% | 5.8% | -45.2 |
| 2018 | -5.1% | 12.7% | -0.3% | 15.4% | -4.8 |
| 2019 | -8.4% | 12.0% | 14.3% | 13.6% | -22.7 |
| 2020 | -28.5% | 40.4% | 21.2% | 40.6% | -49.8 |
| 2021 | -11.7% | 16.7% | 52.2% | 10.7% | -63.9 |
| 2022 | -28.2% | 29.4% | 18.4% | 18.0% | -46.6 |
| 2023 | -18.4% | 21.0% | 11.5% | 23.2% | -29.9 |
| All, 2016-2023 | -71.5% | 72.9% | 345.6% | 40.6% | -417.0 |

Final equity: pullback Rs 5,708, benchmark Rs 89,114.

## 9. Without the single best symbol

SUNPHARMA has the largest total net in the base run: Rs +494 over 27 trades. TECHM is
next at Rs +382. Its trades are taken out; nothing is rerun, and every other trade is
unchanged, including sizes.

| Base run | Trades | Win % | Avg win Rs | Avg loss Rs | Gross bps | Cost bps | Net bps | Net Rs per trade | PF | Net Rs |
|---|---|---|---|---|---|---|---|---|---|---|
| All trades | 1,021 | 53.5% | 51 | -89 | 22.2 | 73.9 | -51.7 | -14.00 | 0.66 | -14,292 |
| Without SUNPHARMA | 994 | 53.5% | 51 | -91 | 19.4 | 73.4 | -54.0 | -14.88 | 0.65 | -14,786 |

Benchmark comparison without SUNPHARMA's trades. The method is the same as swing
section 7: its fills' cash flows and holdings are taken out of each session's equity.

| Year | Pullback ex-SUNPHARMA return % | Max DD % | Benchmark return % | Excess return, pp |
|---|---|---|---|---|
| 2016 | -11.1% | 15.7% | 10.5% | -21.7 |
| 2017 | -0.2% | 12.6% | 45.0% | -45.2 |
| 2018 | -8.0% | 15.7% | -0.3% | -7.8 |
| 2019 | -8.3% | 12.4% | 14.3% | -22.7 |
| 2020 | -30.0% | 41.2% | 21.2% | -51.3 |
| 2021 | -12.6% | 17.9% | 52.2% | -64.9 |
| 2022 | -29.3% | 30.6% | 18.4% | -47.7 |
| 2023 | -19.3% | 22.1% | 11.5% | -30.8 |
| All, 2016-2023 | -73.9% | 75.3% | 345.6% | -419.5 |

The benchmark keeps SUNPHARMA. Check: final equity minus capital = Rs -14,785.74 = the
net P&L of the other trades in `trades.parquet`.

## Reproduce

Run directories (gitignored):

- `research/runs/20261028-160302_pullback_dev_none`
- `research/runs/20261028-160321_pullback_dev_base`
- `research/runs/20261028-160339_pullback_dev_stress1`
- `research/runs/20261028-160358_pullback_dev_stress2`

Commands:

- `uv run python scripts/report_runs.py summary LABEL=RUN_DIR ...` for section 1.
- `uv run python scripts/report_runs.py detail <run> --all-symbols` for sections 4, 6
  and 7.
- `uv run python scripts/report_runs.py benchmark <base run> --exclude SUNPHARMA` for
  sections 8 and 9.

Some numbers come from a one-off analysis of the base run's `trades.parquet`,
`fills.parquet` and `equity.parquet` with dev daily bars. That script is not in the
repo. The figures are:

- sessions held;
- the exit split;
- trades per year;
- notional by year;
- costs as % of average equity;
- the without-SUNPHARMA trade row.

The exit split is computed this way:

1. The decision day is the last tradeable session before the exit fill.
2. Sessions held runs from the buy's fill session to the decision day on the calendar.
3. An exit is a 5-average exit if the decision-day close is above its 5-session
   average. Otherwise it is a 10-session exit.

No time exit had fewer than 10 sessions held. No 5-average exit had more than 10.
