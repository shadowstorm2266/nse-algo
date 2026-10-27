# Backtest engine

Event-driven backtester for intraday MIS (1m/5m bars) and swing CNC (daily bars).
Strategies, the RiskGovernor and the Portfolio are written to run unchanged in paper
and live mode; only the broker and the bar source differ.

    uv run python -m nsealgo.backtest --strategy NAME --period dev --cost-tier base

| Module | Role |
|---|---|
| `strategies/base.py` | `Strategy` protocol: `on_bar(ctx) -> list[OrderIntent]`, pure |
| `strategies/orb.py` | Strategy 1, 30-minute Opening Range Breakout (`config/strategies/orb.yaml`) |
| `strategies/swing_momentum.py` | Strategy 2, monthly momentum, swing CNC (`config/strategies/swing.yaml`, CLI name `swing`) |
| `engine/context.py` | `StrategyContext`: only what is visible at `now` |
| `engine/risk.py` | `RiskGovernor`: the only code that turns intents into orders |
| `engine/sizing.py`, `engine/exposure.py` | pure qty and exposure arithmetic for the RiskGovernor |
| `brokers/sim.py`, `brokers/fills.py` | `SimBroker` and its fill rules |
| `engine/portfolio.py` | Decimal ledger, positions, margin, trade records |
| `engine/backtest.py` | the event loop |
| `engine/loader.py` | DuckDB inputs, research periods, holdout lock |
| `reporting/metrics.py`, `reporting/trials.py` | metrics and the trial log |
| `reporting/breakdown.py` | by year/side/symbol, turnover and costs by fill year, cap skips |

## Strategy parameters

Every parameter of a strategy lives in `config/strategies/<name>.yaml`; strategy code
has no defaults and rejects unknown keys. `--params` is a JSON object merged over the
YAML (nested keys merge), e.g.
`--params '{"filters": {"gap": {"enabled": false}}}'`. The merged parameters go into
the trial record. Changing a YAML default is a new strategy version.

## Timing (no look-ahead)

The loop walks bar groups (all symbols' bars that start at the same time):

1. The SimBroker fills working orders against the group's bars.
2. Positions are marked to the bars' closes.
3. At `now` = the bars' `available_at`, the RiskGovernor places forced exits (MIS at
   or after `flat_by`). The strategy then gets a context of everything visible at
   `now`, and each intent goes RiskGovernor -> broker.

The context also carries `next_session`, the next date on the trading calendar
(tradeable or not; None after the last), which the exchange holiday list gives in
advance, and `next_tradeable_session`, the next one not marked no_trade. The monthly
swing strategy uses the latter to know it is on the last tradeable session of a month.

So a signal on bar T fills at bar T+1's open at the earliest. A fill inside bar T+1
becomes visible at T+1's `available_at`. Daily bars have `ts` 09:15 and `available_at`
15:30: a swing decision made after the close fills at the next session's open.
`tests/test_lookahead.py` compares full and truncated runs, and was checked against
deliberately leaky engines (bars visible one bar early, fills visible early).

## Fill rules (SimBroker)

- Slippage (bps per side, from the `--cost-tier` in `config/costs.yaml`) applies to
  **every** fill, limit fills included (hard rule 5). Buys pay up, sells receive less.
- Market orders fill at the next bar's open.
- Stops trigger on touch and fill at the stop, or at the open if the bar gaps
  through it.
- Limits fill only when price trades strictly through the limit, at the limit, or at
  the open if the bar opens through it.
- Within a bar: expiries, then market exits for all symbols, then market entries
  (that morning's sale proceeds fund buys), then resting orders per symbol.
- Bracket children (stop, target) form an OCO pair; if one bar touches both, the stop
  fills. After a market entry the children are live on the entry bar. After a
  stop/limit entry, only the stop is checked on the fill bar.
- OCO entry groups: when one leg fills the sibling is cancelled. If both trigger in
  one bar, the leg nearer the open fills (a leg the open gaps through counts as
  distance 0); an exact tie goes to the leg submitted first.
- Charges: `costs.fill_charges` per fill, each component rounded to the paisa per
  order. The DP charge applies to the first CNC sell of a scrip in each session.
- A CNC buy that cash cannot cover at the open is rejected (`INSUFFICIENT_CASH`). Cash
  (`Portfolio.cash`) is real cash: ledger minus margin used, less only unrealized losses
  on MIS positions. Delivery holdings are paid for in full, so their unrealized losses
  do not reduce it. MIS free margin (`free_cash`) still subtracts every unrealized loss.
- Session end: MIS orders are cancelled. CNC orders whose fill session has passed
  expire. An MIS position still open (no bar at or after `flat_by` for that symbol)
  is closed at the last close (`session_end_fallback`, counted in metrics). At the
  end of a run, open CNC positions close at the last close (`end_of_run`).

## RiskGovernor

An MIS run uses the intraday limits in `config/risk.yaml`; a CNC run uses the `swing:`
block. Each run trades one strategy on its own capital.

**MIS entries**, checked in this order: `KILL_SWITCH`, `DRAWDOWN_HALT` (latch mode),
`NO_TRADE_SESSION`, `BEFORE_ENTRY_START` / `AFTER_ENTRY_END`, `DAILY_LOSS_LIMIT`
(equity now minus equity at the session open), `MAX_TRADES_PER_DAY` (filled entries
plus working entry units), `POSITION_EXISTS`, `INVALID_STOP`, `NO_PRICE`,
`QTY_BELOW_ONE`.

- qty = min(floor(risk_per_trade / |ref - stop|), floor(remaining exposure / ref),
  floor(free margin / (ref x margin%))). Free margin is on the sizing basis (below).
- `ref` is the trigger or limit price for STOP/LIMIT entries and the last visible
  close for market entries.
- Margin % comes from `config/margins.yaml` (default 25%).
- Shorts are allowed for MIS only.
- At `flat_by` the RiskGovernor emits market exits for every MIS position; they fill at
  the open of the 14:50 bar.

**OCO entry groups** (MIS): two STOP/LIMIT entry legs on one symbol sharing a
`group_id`, submitted in the same call. A group counts as one trade and one
per-symbol slot, and its larger leg counts for exposure and margin. Each leg is sized
against the pool without its sibling. Groups are all-or-nothing: if a leg is
rejected, any placed sibling is cancelled (`GROUP_LEG_REJECTED`). Malformed groups get
`INVALID_GROUP`.

**Swing (CNC) entries** are market orders for the next tradeable session's open only:
no entry window, no flat_by, no per-trade rupee risk and no daily loss stop.

- Checks: `SWING_DISABLED`, `SHORT_NOT_ALLOWED`, `INVALID_INTENT` (any price, stop,
  target or group), `MAX_ORDERS_PER_DAY`, `POSITION_EXISTS`, `MAX_POSITIONS`,
  `NO_NEXT_SESSION`, `NO_PRICE`, sizing.
- Sizing: slot = equity / max_positions, and room = gross left under 100% of equity
  (held positions at marks and pending entries at their reference price; a full
  working exit frees its position). Each is reduced by the estimated buy charges on
  that amount, then (100 - `cash_buffer_pct`)% of it is spent (99%: the rest absorbs a
  normal opening gap, slippage and same-morning sell charges, so the buy is not
  rejected for cash). qty = min(slot, 30% of equity, room) / price in whole shares;
  the buffer does not reduce the 30% position cap. "Equity" here is the sizing equity
  (see the sizing basis below).
- If the buffered slot buys no share but one share fits the position cap and the room,
  the qty is 1. If one share is above 30% of equity, the stock is skipped
  (`PRICE_ABOVE_POSITION_CAP`, logged with price and rank) and review continues with
  the next rank.
- Intents are reviewed exits first, then entries by `rank`. A position with a
  working full exit frees its slot.
- Orders skip no_trade sessions: they fill at the next tradeable open.

**Sizing basis** (`sizing_basis` in `risk.yaml`, per run mode; backtests per product).
`current_equity` sizes from the account as it stands, so sizes compound; paper and
live must use it, and CNC backtests use it too (`backtest.cnc`), so swing research
sizes as paper and live would. `fixed_capital` (`backtest.mis`) sizes every session
off `capital`, so a drawdown never shrinks later trades and every year of a research
period is tested at the configured size. MIS: free margin is computed on the account
rebased to `capital` at the session open, so the session's own P&L still counts. CNC
with `fixed_capital` (configurable, not the default): decisions after the close size
off `capital` exactly, and the broker's cash check at the next open uses the same
rebased account (`Portfolio.buying_power`). Equity, the drawdown halt, the daily loss
limit and every trade record use the real, cumulative account.

**Exits** reducing a real position are always allowed (`NO_POSITION`,
`DUPLICATE_EXIT` and `INVALID_INTENT` otherwise), even under KILL or a latched halt.

**Drawdown halt**: drawdown = (peak - equity) / peak, where peak is the running maximum
of capital and session-end equity. `halt_mode.backtest: record` keeps trading and
reports `halt_would_fire_date` / `halt_would_fire_drawdown_pct`. Paper and live must
`latch`: no new entries for the rest of the run, even if equity recovers.

**KILL**: the RiskGovernor checks a `KILL` file only when given its path, as paper and
live will do. Backtests pass none, so a live kill never silently zeroes a research
run.

Every rejection is a `Rejection` with a reason code. It is logged on `nsealgo.risk` and
saved to `rejections.parquet`.

## Outputs

`research/runs/<stamp>_<strategy>_<period>_<tier>/` (git-ignored):

- `trades.parquet`: one row per exit fill (a partial exit is its own row). Columns:
  trade_id, symbol, product, side, qty, entry/exit time (start of the fill bar),
  entry/exit price, entry/exit reference price, notional, gross_pnl, slippage, costs,
  net_pnl, r_multiple, exit_reason, group_id.
  - gross is at reference prices; slippage is in rupees, both legs; costs are charges.
  - net = gross - slippage - costs.
  - R = net / (|entry - initial stop| x qty), empty without a stop.
- `equity.parquet`: one row per session (equity, ledger, unrealized, daily_pnl, ...).
- `fills.parquet`: one row per fill: order_id, symbol, product, side, qty, ts (start of
  the fill bar), session_date, price (with slippage), ref_price, value, slippage (Rs),
  charges (the order's total), dp_charge (before GST; its GST is inside charges), role,
  exit_reason, group_id.
- `rejections.parquet`, `metrics.json`.

A strategy may list `reference_symbols` (an index it reads but never trades). They are
loaded with the universe; if one has no bars, or misses sessions, in the period, the
CLI prints a WARNING, the trial record's `warnings` says so, and the strategy skips
whatever needed it.

Every run appends one line to `research/trials.jsonl` (append-only; the DSR trial
count). The line holds the git hash and dirty flag, strategy and version, params,
period, cost tier, slippage, brokerage preset, universe, metrics, warnings and the run
dir. A run
with the `zero` brokerage preset or the `none` (0 bps) slippage tier is flagged
`reference_tier: true`: a labelled reference, never a tradeable result.

`scripts/report_runs.py` prints markdown tables from run directories (`summary` for
one row per run, `detail` for one run by year, side, exit reason and symbol, plus
turnover and costs by the year of each fill, holding periods, position-cap skips and
rejections). Turnover is one-way: (bought + sold) / 2 / capital.

`report_runs.py benchmark RUN_DIR [--exclude SYM,...]` compares a run with an
equal-weight buy-and-hold of its universe (`reporting/benchmark.py`): each symbol gets
capital / n, bought in fractional shares at the first session's open with one
base-tier buy (charges of the active brokerage preset plus base slippage), held to the
period's last close, no rebalancing and no sell costs. By calendar year (in-year) and
over the whole period: return, max drawdown and the run's excess return (run minus
benchmark, percentage points). `--exclude` takes those symbols' trades out of the run:
each session's equity minus their fills' cash flows (sales add value, buys subtract
it, every fill pays its charges) and their holdings at the close; other trades are
unchanged, including sizes set off an account that held them. The benchmark is not a
strategy and not a trial; it reads daily bars from data/clean, never on or after
`holdout_start`.

## Metrics

Per round trip (partial exits summed):

- trades, win rate, average win and loss;
- net expectancy in rupees and in bps of entry notional (mean over trades);
- gross bps vs cost bps per trade, where cost is charges + slippage;
- profit factor (None with no losses);
- cost share of gross (None if gross <= 0).

From session-end equity:

- max drawdown in rupees and percent;
- Sharpe = mean / std (ddof 1) of daily returns x sqrt(252), every session counted. A
  daily return is the session's P&L over the previous session-end equity
  (`current_equity`) or over capital (`fixed_capital`, where equity can go below zero).
- Max drawdown % is of the running peak (`current_equity`) or of capital
  (`fixed_capital`).
- `sizing_basis` is recorded in `metrics.json` and in the trial record.

## Holdout lock

`--period holdout` raises `HoldoutLockedError` unless `--run-holdout` is passed. It
also refuses a second holdout run for the same strategy name and version. The loader
re-checks that no session on or after `holdout_start` is read without permission.

## Known simplifications

- No tick-size rounding of prices and no volume or liquidity cap on fills.
- MIS margin is not re-checked at fill time (it is checked at review, at the
  reference price).
- Fill time is the start of the bar in which the order filled.
- Charges are per order, not per contract note. Each leg's components are rounded
  separately.
- Universe membership is not point-in-time (see `config/universe.yaml`).
- The calendar is known in advance: `next_session` and `next_tradeable_session` in the
  context, and `no_trade` flags (outage days). Swing orders deferred past an outage day
  use that knowledge, and so would a month-end swing decision moved to the session
  before a month-end outage (none in dev); in reality the outage was only known on the
  day.
- 15m bars cannot run MIS: 14:50 is not on the 15m grid.
