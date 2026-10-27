# Swing momentum v1 (strategy 2): dev-period result

Monthly momentum on daily bars, delivery (CNC) only, `swing` version 1, parameters
exactly as in `config/strategies/swing.yaml` at c6a7edf (not optimized):

- Decision after the close of the last session of each month M, on data up to that
  close. Orders are market orders for the next tradeable session's open.
- Momentum = close at the end of month M-1 over the close at the end of month M-7,
  minus 1 (6 months, skipping the latest month). A month's end close is the symbol's
  last close in that month.
- Ranked: symbols with a bar on the decision day and a close strictly above their
  200-session simple average. Target: the top 4.
- Holdings still in the top 4 are kept as they are (`resize_holdings: false`). Only
  dropouts are sold and only newcomers are bought. A newcomer the RiskGovernor skips
  leaves its slot in cash until the next rebalance; the next-ranked stock does not
  take it.
- Market filter off (no NIFTY 50 bars in `data/clean` anyway).

Run facts:

- **Period:** dev, 2016-01-01 .. 2023-12-31 (1,971 sessions). Validation and holdout were
  not touched.
- **Rebalances:** data starts 2016-01-01, so the 200-session average first exists in
  October 2016. That makes 86 month-end decisions, 2016-10-28 .. 2023-11-30, and 77 of
  them led to at least one fill. 2023-12-29 is the period's last session (no next
  session), so there is no rebalance on it. The 4 positions open then are closed at its
  close (`end_of_run`).
- **Universe:** the 40 symbols of `config/universe.yaml`. **They are today's 40 large
  caps, so survivorship bias flatters momentum results.**
  - The raw dataset only holds stocks that are large caps today, and the 40 were picked
    from those by 2016 turnover.
  - Stocks that were large in 2016 and later collapsed or left the large-cap set are
    missing. For example, YES Bank, a Nifty 50 stock that rallied into 2018 and then
    lost most of its value, is not in the data.
  - A momentum rule buys recent winners, and the winners that later collapsed are
    exactly the stocks the data leaves out.
  - ADANIENT, the source of most of this run's P&L (section 3), is in the data because
    it is a large cap today.
- **Risk** (`config/risk.yaml`, swing block):
  - capital Rs 20,000, sized off fixed capital (`sizing_basis.backtest: fixed_capital`);
  - 4 positions, slot = (capital - estimated buy charges) / 4 = Rs 4,994.06;
  - 30% position cap (Rs 6,000) and 100% gross cap (Rs 20,000), both of the sizing
    equity (Rs 20,000 here);
  - 8 orders a day.
- **Costs** (`config/costs.yaml`, on every fill):
  - delivery statutory charges: STT 0.1% on buy and on sell, stamp 0.015% on buy,
    transaction charge, SEBI fee, GST;
  - shoonya delivery brokerage (zero) and a DP charge of Rs 9 + GST on every sale, unless
    stated;
  - slippage per side by tier.
- **Trials:** lines 8-11 of `research/trials.jsonl`, all on c6a7edf (clean tree), no run
  warnings. The DSR trial count is now 11 (7 ORB, 4 swing).
- **Definitions:**
  - Gross, cost and net bps are means over trades of P&L / entry notional;
    cost = charges + slippage.
  - Sharpe is daily, annualized, on P&L / capital.
  - Max DD % is of the Rs 20,000 capital.
  - Turnover is one-way: (rupees bought + sold) / 2 / capital.

## 1. Cost tiers (trials 8-11)

| Run | Ref tier | Sizing | Trades | Win % | Avg win Rs | Avg loss Rs | Gross bps | Cost bps | Net bps | PF | Max DD Rs | Max DD % | Sharpe (daily, ann.) | Net Rs | Cap skips | Turnover x/yr | Costs % cap/yr |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Statutory only: zero brokerage, 0 bps (trial 9) | REFERENCE | fixed_capital | 134 | 51.5% | 758 | -433 | 396.5 | 22.6 | 373.8 | 1.86 | 9,431 | 47.2% | 0.61 | 24,211 | 4 | 3.86 | 0.9% |
| Base: shoonya, 3 bps (trial 8) |  | fixed_capital | 133 | 51.1% | 756 | -456 | 391.3 | 55.7 | 335.6 | 1.73 | 9,886 | 49.4% | 0.55 | 21,761 | 4 | 3.86 | 2.0% |
| Stress1: shoonya, 6 bps (trial 10) |  | fixed_capital | 132 | 50.8% | 762 | -459 | 391.1 | 61.8 | 329.3 | 1.71 | 10,034 | 50.2% | 0.53 | 21,233 | 4 | 3.83 | 2.2% |
| Stress2: shoonya, 10 bps (trial 11) |  | fixed_capital | 132 | 50.8% | 758 | -462 | 390.9 | 70.0 | 321.0 | 1.69 | 10,231 | 51.2% | 0.52 | 20,754 | 4 | 3.83 | 2.5% |

The statutory-only tier is a reference tier: no broker charges and no slippage, not a
tradeable result.

- "Per year" in the last two columns is the run total over 1,971 / 252 = 7.8 years. The
  strategy only held stocks from 2016-11-01, so the by-year table in section 4 is the
  better guide.
- Trade counts differ slightly between tiers because buys rejected for cash at the open
  differ (section 3), which changes later holdings.

## 2. Gate A items measured so far

| Gate A item | Threshold | Value |
|---|---|---|
| Dev-period trades (swing) | >= 100 | 133 (base): 129 strategy exits + 4 end-of-run closes |
| Net expectancy at double the modeled slippage (stress1, 6 bps) | > 0 | +329.3 bps/trade, Rs +160.9/trade (trial 10) |
| Walk-forward OOS expectancy and profit factor | > 0 and >= 1.15 | not run |
| Parameter neighbours | >= 50% of chosen | not run |
| Deflated Sharpe | >= 0.90 | not computed (11 trials logged) |
| Holdout | net positive, once | not run |
| P(15% drawdown within 250 days) | < 10% | not computed. The 15% account-drawdown halt would have fired on 2018-03-06 (base; 2018-03-07 reference). Paper and live latch, so they would stop new entries then. |

## 3. Read this before the tables

**Concentration.** Base net is Rs 21,761 over the period.

| Base tier | Net Rs |
|---|---|
| All 133 trades | 21,761 |
| Excluding ADANIENT (6 trades) | 8,410 |
| Excluding trades entered in 2020 (16 trades) | 3,280 |
| Excluding the 5 largest winning trades | -2,757 |

- One trade, ADANIENT bought 2020-11-02 (15 shares at Rs 329) and sold 2021-11-01 at
  Rs 1,392, nets Rs 15,905. That is 73% of the run's net.
- Per-trade net is very spread out: mean +335.6 bps, median +17.3 bps, standard
  deviation 3,170 bps, standard error of the mean 275 bps (n = 133).
- The worst drawdown ran from a Rs 23,897 peak on 2017-09-14 to Rs 14,012 on 2020-03-23
  (Rs 9,886; 49.4% of capital, 41.4% of that peak).

**Fixed-capital sizing and `resize_holdings: false` together blocked new buys in 2021.**

- Research sizes off a fixed Rs 20,000, and the 100% gross cap counts held positions at
  market value.
- As ADANIENT (bought 2020-11-02 for about Rs 4,900) grew towards and then past
  Rs 20,000, the gross room shrank.
  - Newcomers were bought smaller: DLF for Rs 1,835 in March 2021, ADANIPORTS for
    Rs 2,855 and SBIN as 1 share in April.
  - Or they were rejected: 16 of the 19 `QTY_BELOW_ONE` rejections in base fall between
    2021-02-26 and 2021-09-30, with gross room from Rs 95 down to Rs -3,049.
- From 2021-06-01 to 2021-10-29 (105 sessions) the book held ADANIENT alone. The real
  account was then about Rs 40,000.
- Paper and live size off current equity, so they would have kept buying newcomers, with
  ADANIENT at roughly half of a Rs 40,000 account. The 30% position cap is checked only
  at entry.
- So this backtest under-invests after a large winner, compared with how paper and live
  would size. Whether that is the wanted research behaviour is the owner's call; nothing
  was changed.

**Buys rejected for cash at the open.**

- Base had 7 newcomer buys (8 in stress1/2, 5 in the reference) rejected by the broker
  with `INSUFFICIENT_CASH`; each slot stayed in cash until the next rebalance.
- They are sized at the decision-day close. At the next open, the gap, slippage and buy
  charges can exceed the cash left after the earlier buys of the same morning. The cash
  shortfalls ranged from Re 0.05 (DLF, 2018-05-02) to Rs 163 (BAJFINANCE, 2017-07-03).
- The 1-share rule adds to this: MARUTI at about Rs 5,270 is above the Rs 4,994 slot.
- This is RiskGovernor/broker behaviour, not a strategy rule.

**Position-cap skips (one share above 30% of capital, Rs 6,000).** 4 of the 86
rebalances skipped a stock, the same 4 in every tier. The slot stayed in cash.

| Decision | Symbol | Price Rs | Rank |
|---|---|---|---|
| 2017-10-31 | MARUTI | 8,220 | 4 |
| 2022-03-31 | MARUTI | 7,563 | 4 |
| 2023-04-28 | ULTRACEMCO | 7,540 | 1 |
| 2023-06-30 | ULTRACEMCO | 8,289 | 4 |

Two more rebalances left out a top-4 stock that was under the cap but cost more than the
gross room left: MARUTI on 2016-10-28 (Rs 5,875, rank 4) and 2017-01-31 (Rs 5,900,
rank 3). These are `QTY_BELOW_ONE`, not the 30% cap. The one remaining `QTY_BELOW_ONE`
outside 2021 is EICHERMOT on 2022-09-30 (Rs 3,665 against Rs 1,671 of gross room).

Base rejections by reason: `QTY_BELOW_ONE` 19, `INSUFFICIENT_CASH` 7,
`PRICE_ABOVE_POSITION_CAP` 4.

## 4. By year

Base tier, by entry year (Max DD % and Sharpe from that calendar year's sessions). The
ADANIENT trade above is a 2020 entry held into November 2021.

| Year | Trades | Win % | Avg win Rs | Avg loss Rs | Gross bps | Cost bps | Net bps | PF | Net Rs | Max DD % | Sharpe |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2016 | 3 | 33.3% | 1,439 | -674 | 107.3 | 50.0 | 57.3 | 1.07 | 91 | 12.5% | -0.95 |
| 2017 | 19 | 52.6% | 382 | -255 | 223.7 | 50.6 | 173.1 | 1.67 | 1,526 | 12.7% | 1.11 |
| 2018 | 22 | 40.9% | 412 | -493 | -186.3 | 51.0 | -237.3 | 0.58 | -2,696 | 29.5% | -1.11 |
| 2019 | 20 | 60.0% | 434 | -643 | 45.5 | 51.3 | -5.8 | 1.01 | 69 | 23.7% | 0.58 |
| 2020 | 16 | 62.5% | 2,319 | -785 | 2409.7 | 58.6 | 2351.1 | 4.92 | 18,480 | 46.3% | 0.42 |
| 2021 | 14 | 42.9% | 575 | -459 | 47.2 | 74.4 | -27.2 | 0.94 | -222 | 31.5% | 1.68 |
| 2022 | 15 | 53.3% | 625 | -450 | 326.6 | 58.6 | 268.0 | 1.59 | 1,854 | 26.7% | 0.41 |
| 2023 | 24 | 50.0% | 466 | -245 | 272.9 | 53.7 | 219.1 | 1.91 | 2,658 | 20.0% | 0.31 |

Net bps per trade / trades, by entry year and tier:

| Year | Reference | Base | Stress1 | Stress2 |
|---|---|---|---|---|
| 2016 | 84.9 / 3 | 57.3 / 3 | 51.2 / 3 | 43.2 / 3 |
| 2017 | 201.3 / 19 | 173.1 / 19 | 156.8 / 18 | 148.7 / 18 |
| 2018 | -225.6 / 23 | -237.3 / 22 | -243.2 / 22 | -251.0 / 22 |
| 2019 | 23.3 / 20 | -5.8 / 20 | -11.8 / 20 | -19.8 / 20 |
| 2020 | 2385.8 / 16 | 2351.1 / 16 | 2343.7 / 16 | 2333.8 / 16 |
| 2021 | 142.2 / 14 | -27.2 / 14 | -33.2 / 14 | -41.2 / 14 |
| 2022 | 304.2 / 15 | 268.0 / 15 | 261.9 / 15 | 253.6 / 15 |
| 2023 | 250.5 / 24 | 219.1 / 24 | 213.0 / 24 | 204.8 / 24 |

2021 differs between the reference and base tiers by more than costs: base's extra
cash rejection (TATASTEEL, 2021-06-01) changed which stocks were held.

### Turnover and costs, base tier, by year of each fill

| Year | Bought Rs | Sold Rs | Turnover x | Charges Rs | DP Rs (pre-GST) | Slippage Rs | Costs Rs | Costs % capital |
|---|---|---|---|---|---|---|---|---|
| 2016 | 14,751 | 0 | 0.37 | 18 | 0 | 4 | 22 | 0.1% |
| 2017 | 91,814 | 90,561 | 4.56 | 394 | 162 | 55 | 449 | 2.2% |
| 2018 | 102,483 | 98,545 | 5.03 | 457 | 198 | 60 | 518 | 2.6% |
| 2019 | 92,848 | 96,929 | 4.74 | 423 | 180 | 57 | 480 | 2.4% |
| 2020 | 66,664 | 65,512 | 3.30 | 317 | 144 | 40 | 357 | 1.8% |
| 2021 | 55,039 | 74,476 | 3.24 | 291 | 126 | 39 | 330 | 1.6% |
| 2022 | 62,734 | 64,014 | 3.17 | 300 | 135 | 38 | 338 | 1.7% |
| 2023 | 104,991 | 125,800 | 5.77 | 552 | 252 | 69 | 621 | 3.1% |

Charges include STT, stamp, exchange and SEBI fees, GST and the DP charge. 2023 includes
the four end-of-run sales on 2023-12-29.

Costs (charges + slippage) as % of capital, by year and tier:

| Year | Reference | Base | Stress1 | Stress2 |
|---|---|---|---|---|
| 2016 | 0.1% | 0.1% | 0.1% | 0.2% |
| 2017 | 1.0% | 2.2% | 2.4% | 2.7% |
| 2018 | 1.2% | 2.6% | 2.9% | 3.3% |
| 2019 | 1.1% | 2.4% | 2.7% | 3.1% |
| 2020 | 0.7% | 1.8% | 2.0% | 2.2% |
| 2021 | 0.7% | 1.6% | 1.8% | 2.1% |
| 2022 | 0.7% | 1.7% | 1.9% | 2.1% |
| 2023 | 1.3% | 3.1% | 3.5% | 3.9% |

Holding period (base): median 59 calendar days, mean 71.5, max 364.

## 5. By exit reason and by symbol (base tier, trial 8)

| Exit | Trades | Win % | Avg win Rs | Avg loss Rs | Gross bps | Cost bps | Net bps | PF | Net Rs |
|---|---|---|---|---|---|---|---|---|---|
| end_of_run | 4 | 100.0% | 1,073 | - | 2261.3 | 58.4 | 2202.9 | - | 4,293 |
| strategy | 129 | 49.6% | 736 | -456 | 333.4 | 55.6 | 277.7 | 1.59 | 17,468 |

All 37 symbols traded, ranked by net bps per trade (1-9 trades each; 3 of the 40 were
never held: GRASIM, HDFCBANK, MARUTI):

| Symbol | Trades | Win % | Avg win Rs | Avg loss Rs | Gross bps | Cost bps | Net bps | PF | Net Rs |
|---|---|---|---|---|---|---|---|---|---|
| ADANIENT | 6 | 50.0% | 5,835 | -1,385 | 4608.6 | 56.2 | 4552.4 | 4.21 | 13,351 |
| DRREDDY | 3 | 66.7% | 1,449 | -65 | 1939.9 | 52.9 | 1887.0 | 44.26 | 2,833 |
| NTPC | 2 | 100.0% | 828 | - | 1719.8 | 52.1 | 1667.7 | - | 1,655 |
| ITC | 3 | 66.7% | 814 | -91 | 1115.0 | 51.6 | 1063.4 | 17.94 | 1,537 |
| CIPLA | 3 | 100.0% | 362 | - | 1098.7 | 61.7 | 1037.0 | - | 1,085 |
| COALINDIA | 4 | 50.0% | 1,038 | -34 | 1052.1 | 55.3 | 996.8 | 30.94 | 2,010 |
| ADANIPORTS | 4 | 75.0% | 533 | -272 | 819.2 | 54.8 | 764.4 | 5.89 | 1,328 |
| TECHM | 3 | 66.7% | 737 | -465 | 783.0 | 52.8 | 730.2 | 3.17 | 1,009 |
| ICICIBANK | 4 | 75.0% | 511 | -167 | 744.7 | 50.9 | 693.8 | 9.17 | 1,367 |
| INDUSINDBK | 4 | 75.0% | 357 | -91 | 737.3 | 71.8 | 665.5 | 11.80 | 979 |
| HCLTECH | 2 | 50.0% | 451 | -76 | 654.3 | 57.5 | 596.8 | 5.96 | 376 |
| INFY | 3 | 66.7% | 449 | -120 | 604.3 | 51.4 | 552.8 | 7.49 | 778 |
| WIPRO | 3 | 66.7% | 378 | -89 | 505.1 | 50.4 | 454.7 | 8.47 | 668 |
| KOTAKBANK | 2 | 50.0% | 606 | -204 | 463.0 | 50.7 | 412.3 | 2.97 | 401 |
| TCS | 2 | 50.0% | 631 | -438 | 455.2 | 56.0 | 399.1 | 1.44 | 193 |
| BHARTIARTL | 4 | 75.0% | 478 | -699 | 432.4 | 50.7 | 381.8 | 2.05 | 736 |
| TATASTEEL | 4 | 50.0% | 1,032 | -647 | 431.7 | 50.0 | 381.6 | 1.60 | 770 |
| TITAN | 6 | 66.7% | 364 | -262 | 374.9 | 52.9 | 322.1 | 2.77 | 930 |
| RELIANCE | 6 | 66.7% | 303 | -86 | 373.9 | 56.8 | 317.1 | 7.08 | 1,042 |
| SUNPHARMA | 2 | 50.0% | 334 | -248 | 265.5 | 56.4 | 209.1 | 1.34 | 85 |
| LT | 3 | 66.7% | 150 | -336 | 113.9 | 56.2 | 57.7 | 0.89 | -35 |
| BAJAJ-AUTO | 1 | 100.0% | 11 | - | 77.1 | 52.0 | 25.1 | - | 11 |
| JSWSTEEL | 7 | 42.9% | 500 | -387 | 65.5 | 51.5 | 14.0 | 0.97 | -50 |
| ASIANPAINT | 3 | 66.7% | 39 | -262 | -80.6 | 56.5 | -137.1 | 0.30 | -183 |
| HEROMOTOCO | 1 | 0.0% | - | -63 | -146.8 | 63.6 | -210.3 | 0.00 | -63 |
| AXISBANK | 3 | 33.3% | 533 | -390 | -169.9 | 52.5 | -222.3 | 0.68 | -247 |
| ONGC | 3 | 33.3% | 164 | -289 | -223.9 | 49.2 | -273.1 | 0.28 | -414 |
| HINDUNILVR | 5 | 40.0% | 158 | -353 | -295.5 | 56.4 | -351.8 | 0.30 | -743 |
| DLF | 6 | 33.3% | 1,207 | -725 | -335.6 | 55.4 | -391.0 | 0.83 | -488 |
| HINDALCO | 6 | 16.7% | 1,439 | -498 | -353.6 | 50.0 | -403.6 | 0.58 | -1,052 |
| BAJAJFINSV | 7 | 28.6% | 371 | -423 | -409.0 | 50.6 | -459.6 | 0.35 | -1,374 |
| ULTRACEMCO | 1 | 0.0% | - | -234 | -439.6 | 49.8 | -489.5 | 0.00 | -234 |
| SBIN | 3 | 33.3% | 47 | -596 | -353.7 | 142.6 | -496.3 | 0.04 | -1,146 |
| POWERGRID | 1 | 0.0% | - | -346 | -669.1 | 49.4 | -718.4 | 0.00 | -346 |
| BAJFINANCE | 9 | 44.4% | 376 | -931 | -749.2 | 50.3 | -799.6 | 0.32 | -3,150 |
| BPCL | 3 | 0.0% | - | -391 | -811.9 | 49.6 | -861.5 | 0.00 | -1,174 |
| EICHERMOT | 1 | 0.0% | - | -683 | -1703.1 | 53.2 | -1756.4 | 0.00 | -683 |

SBIN's cost bps (142.6) is high because one SBIN position was 1 share (Rs 368, bought
2021-04-01 with little gross room left), where the Rs 9 + GST DP charge is a large share
of the notional.

Reproduce the tables with `scripts/report_runs.py summary` and
`scripts/report_runs.py detail <run dir> --all-symbols` on the run directories of
trials 8-11.

Status: no decision recorded. The owner decides.
