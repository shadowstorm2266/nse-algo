# Strategy 3: pullback mean reversion (swing, CNC, daily bars): pre-registration

Written and committed before any backtest of this strategy. The rules and parameters
below are fixed. They are not tuned on any result. Strategy name `pullback`, version 1.
If a code bug is found after a run, the fix bumps the version and the rerun is a new
trial. Earlier trial lines stay in `research/trials.jsonl`.

## 1. Hypothesis

Take a universe stock in a long-term uptrend: its close is above its 200-session simple
average. Suppose it has just fallen sharply: its 2-session RSI is below 10. The
hypothesis is that it tends to recover part of that fall within days. If so, buying at
the next open and selling once the close is back above its 5-session average (or after
10 sessions) earns more than delivery costs and slippage.

The strategy is long-only in a universe that rose over dev. So it must also beat an
equal-weight buy-and-hold of the same 40 stocks after costs (Gate A).

## 2. Rules

Code: `src/nsealgo/strategies/pullback.py`. Parameters: `config/strategies/pullback.yaml`.

| Parameter | Value | Meaning |
|---|---|---|
| `trend_ma_sessions` | 200 | entry needs close > simple average of the last 200 closes |
| `rsi_sessions` | 2 | RSI period (Wilder) |
| `rsi_entry_below` | 10 | entry needs RSI(2) < 10 |
| `exit_ma_sessions` | 5 | exit when close > simple average of the last 5 closes |
| `max_hold_sessions` | 10 | exit after 10 sessions held |

- **Universe:** the 40 symbols of `config/universe.yaml`.
- **Decision:** after each session's close, on daily bars up to and including that close.
  Orders are market orders for the next tradeable session's open.
- **Entry candidates:** symbols with a bar on the decision day that are not held and
  have no working entry, with:
  - close > the simple average of the last 200 closes (today's included); and
  - RSI(2) < 10.
- **Rank:** lowest RSI(2) first; ties by symbol name. The strategy emits an entry for
  every candidate, with its rank.
- **Buying:** the RiskGovernor buys within the swing block of `config/risk.yaml`
  exactly as it is: at most 4 positions, equal weight, current-equity sizing, 1% cash
  buffer, 30% position cap, 100% gross cap, 8 orders a day.
  - It reviews exits first, then entries by rank.
  - A position with a working full exit frees its slot for that decision's entries.
    Sells fill before buys at the open.
  - A candidate it cannot buy is skipped and review continues with the next rank. The
    reasons are no free slot (`MAX_POSITIONS`), one share above the cap, or under one
    share.
  - A buy rejected for cash at the open leaves its slot empty until the next decision.
- **Exit:** a held position gets a market exit for the next tradeable open when, at a
  decision, either:
  - its close > the simple average of its last 5 closes (today's included); or
  - it has been held for 10 or more sessions.
- **No stop loss.**
- **One position per symbol.** A symbol sold can be bought again from the next
  decision. An exit decided at session D's close sells at the next tradeable open, and
  the decision after that session's close may buy the symbol again.

### Definitions fixed here (implementation details the rules above leave open)

- **Sessions held.** E is the session whose open filled the buy. At the decision after
  the close of session D, sessions held is the number of trading-calendar sessions from
  E to D, both included, tradeable or not. It is 1 at E's own close.
  - So with no exit signal, the stock is bought at E's open and sold at the open of the
    session after E + 9: it is held over 10 closes.
  - The count uses the calendar, not the symbol's bars. Every universe symbol has a bar
    on all 1,971 dev sessions, so the two are the same in dev.
- **no_trade sessions** (2017-07-10, 2021-02-24 and 2021-02-25 in dev).
  - No decision is made after their close. The stored 2021-02-24 close is from about
    11:40, not the real close. RSI(2) on 2021-02-25 rests mostly on that price.
  - This follows swing v2's rule for month-ends on no_trade sessions.
  - Their bars still count in the averages and the RSI. They count as sessions held.
  - An exit or entry due on one of them waits for the next tradeable session's
    decision. Orders never fill on them (existing RiskGovernor rule).
- **RSI(2), Wilder.**
  - Inputs: price changes of consecutive daily closes. Gain = max(change, 0); loss =
    max(-change, 0).
  - Seed: the simple average gain and average loss of the first 2 changes. Then
    avg = (avg x 1 + new) / 2, for gains and losses.
  - RSI = 100 x avg gain / (avg gain + avg loss). There is no RSI when both are zero.
  - It is computed on the last 100 closes (99 changes). The seed's weight after 97
    smoothing steps is 2^-97, about 6e-30. So this equals Wilder's RSI over the full
    history to floating-point precision, and the value does not depend on where the
    history starts.
- **Inequalities are strict:** close > average, RSI < 10.
- **Symbol without a bar on a decision day:** not an entry candidate. If held, the
  5-average exit is not checked that day. The 10-session exit still applies.
- **Last session.** No decision is made on a session with no tradeable session after
  it. Positions still open after the run's last session (2023-12-29) are closed at its
  close (`end_of_run`), as in the engine.

### Engine change needed (before any run, with tests)

The strategy context has no way to count calendar sessions. `StrategyContext` will get a
read-only `sessions_since(day)`: the number of trading-calendar sessions from `day` to
the decision session, both included. The calendar is the exchange's list of sessions
(known in advance); it carries no prices. Nothing else in the engine, the RiskGovernor,
`risk.yaml` or `costs.yaml` changes.

## 3. Data, period, universe

- **Period:** dev only, 2016-01-01 .. 2023-12-31, 1,971 sessions. Validation and
  holdout are not touched.
- **Warm-up:** data starts 2016-01-01. The 200-session average first exists at the
  200th session, around October 2016. The strategy holds nothing before that; the
  benchmark is invested from 2016-01-04.
- **Universe bias:** the 40 symbols are today's large caps (not point-in-time). A stock
  that fell out of the large-cap set after 2016 is missing. A pullback rule buys dips,
  and the dips in stocks that later collapsed are not in the data.
- **Prices:** split/bonus adjusted by the source. No dividends on either side of the
  benchmark comparison.

## 4. Runs (exactly four, all dev)

Trials 14-17. The DSR trial count goes from 13 to 17.

| Tier | Brokerage preset | Slippage per side | Command |
|---|---|---|---|
| none (reference, not tradeable) | zero | 0 bps | `uv run python -m nsealgo.backtest --strategy pullback --period dev --cost-tier none --brokerage zero` |
| base | shoonya | 3 bps | `uv run python -m nsealgo.backtest --strategy pullback --period dev --cost-tier base` |
| stress1 (double the modeled slippage) | shoonya | 6 bps | `uv run python -m nsealgo.backtest --strategy pullback --period dev --cost-tier stress1` |
| stress2 | shoonya | 10 bps | `uv run python -m nsealgo.backtest --strategy pullback --period dev --cost-tier stress2` |

- Every fill pays the `costs.py` charges: delivery STT 0.1% on buy and sell, stamp
  0.015% on buy, transaction charge, SEBI fee, GST, and shoonya's DP charge of Rs 9 +
  GST on each sale. Slippage per the tier is on top.
- All four run on one clean commit that contains this plan and the code.
- No parameter variants, no validation run and no holdout run.

## 5. Reported (numbers only, no verdict)

The same tables as the strategy 1 and 2 dev write-ups (`orb_v1_result.md`,
`swing_v1_result.md`):

1. **Tier summary:** one row per run: trades, win %, average win and loss, gross, cost
   and net bps per trade, profit factor, max drawdown (Rs and % of peak), Sharpe,
   net Rs, cap skips, turnover x per year, costs % of capital per year.
2. **Gate A table** (section 6).
3. **By entry year, base tier:** trade metrics, in-year max drawdown and Sharpe.
4. **Net bps per trade and trade count, by year and tier.**
5. **Turnover and costs, base tier, by year of each fill.** Bought and sold Rs, turnover,
   charges, DP, slippage, costs % of capital. Also costs % of capital by year and tier.
6. **Holding period:** sessions held (as defined above) and calendar days. Median,
   mean, max, and the distribution of sessions held.
7. **Trades per year:** run total over 1,971 / 252 years, and the count by entry year.
8. **By exit reason, base tier.** `strategy` vs `end_of_run`. Strategy exits are also
   split into "close above the 5-average" and "10 sessions held". The split is
   classified after the run from the decision-day bars; the engine does not store it.
   It counts a 5-average exit when the decision-day close is above the 5-average, even
   if the 10-session limit was also reached that day.
9. **By symbol, base tier:** every symbol traded.
10. **Rejections by reason.** `MAX_POSITIONS` counts candidates beyond the free slots.
11. **Benchmark report by year:**
    `uv run python scripts/report_runs.py benchmark <base run dir>`.
12. **Without the single best symbol.** The best symbol is the one with the largest
    total net Rs in the base run. Two views:
    - the base run's trade metrics without its trades;
    - the benchmark report with `--exclude <symbol>`.

    Neither is a rerun: every other trade stays as it was, including sizes.

## 6. Gate A items (backtest to paper)

| Gate A item | Threshold | Measured from |
|---|---|---|
| Dev-period trades (swing) | >= 100 | base run |
| Net expectancy at double the modeled slippage | > 0 | stress1 run (6 bps), net bps and Rs per trade |
| Long-only: beats equal-weight buy-and-hold of the same universe after costs | overall and in at least 5 of 8 dev years | base run, `report_runs.py benchmark` |
| Walk-forward out-of-sample net expectancy and profit factor | > 0 and >= 1.15 | not run in this round |
| Parameter neighbours keep >= 50% of the chosen setting's net expectancy | >= 50% | not run in this round (it would add trials) |
| Deflated Sharpe | >= 0.90 | not computed in this round (17 trials logged after these runs) |
| Holdout net positive, run once | > 0 | not run; only the owner can ask for it |
| P(15% drawdown within 250 trading days) at configured risk | < 10% | not computed in this round; the date the 15% halt would have fired (record mode) is reported |

The benchmark is `reporting/benchmark.py`. It holds the 40 symbols, Rs 500 each, in
fractional shares, bought at the 2016-01-04 open with one base-tier buy. It is never
rebalanced, marked at each close, with no sell costs. It is not a strategy and not a
trial.

After the four runs and the report, work stops for the owner's review.
