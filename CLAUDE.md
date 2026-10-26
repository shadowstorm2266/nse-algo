# nse-algo

Research, paper-trading and (later) live system for NSE equity cash strategies: intraday (MIS) and swing (delivery). Starting capital ₹20,000. The bot runs unattended on a Linux VM; the owner checks it between classes via Telegram.

IMPORTANT: This code will eventually place real orders with real money. Correctness beats speed. If something is ambiguous, stop and ask instead of guessing.

## Hard rules (YOU MUST follow every one)

1. **Segments.** NSE equity cash only: intraday (MIS) and delivery (CNC) for the swing track. Never write code that trades F&O, currency or commodity.
2. **Live mode is human-only.** Default mode is `backtest`. `paper` requires `MODE=paper`. `live` requires ALL of: `MODE=live` in `.env`, a `LIVE_ARMED` file in the repo root, and `live_enabled: true` in `config/risk.yaml`. Never create `LIVE_ARMED`, never set `MODE=live`, never flip `live_enabled`, never run live mode. Only the human does these.
3. **Secrets.** Load credentials only through `src/nsealgo/settings.py` (pydantic-settings reading `.env`). Never read, print, log or commit `.env`. Keep `.env.example` current with placeholder values only.
4. **No look-ahead.** A bar is visible to a strategy only after its end time. A signal computed on bar T fills no earlier than bar T+1's open. Daily features (previous-day high/low, ATR, average volume, betas) use data strictly before the current session.
5. **Costs on every fill.** Every simulated fill pays `costs.py` charges plus slippage from `config/costs.yaml`. Never report a zero-cost result except as an explicitly labeled reference tier.
6. **Risk lives in one place.** Limits are in `config/risk.yaml`, enforced only by `src/nsealgo/engine/risk.py` (RiskGovernor). Strategies emit order intents; only the RiskGovernor turns them into orders. Do not change risk values unless the human asks in this session.
7. **No LLM in the trading loop.** Nothing under `src/` calls an LLM API. Production is deterministic Python.
8. **Holdout is locked.** Never run a backtest that touches dates on or after `holdout_start` in `config/research.yaml` unless the human types "run holdout" in this session. A holdout run is logged and happens once per strategy version.
9. **Log every research run** to `research/trials.jsonl` (git hash, strategy, params, period, cost tier, metrics). It is the trial count for the Deflated Sharpe Ratio. Append only; never edit or delete lines.
10. **Report, don't judge.** Show numbers next to the gates below. Never call a strategy "profitable", "robust" or "ready". The human decides.

## Market facts (as of Oct 2026, re-verify before going live)

- Session 09:15–15:30 IST. Stocks with F&O contracts (our intraday universe) stop continuous trading at 15:15 for the Closing Auction Session; brokers auto-square MIS in them between 15:00 and 15:10; stop-loss orders are not accepted during the auction.
- Our intraday windows: entries 09:45–14:00 IST; every MIS position flat by 14:50 IST.
- Intraday equity charges: STT 0.025% on sell; NSE transaction charge 0.00297% both legs; SEBI fee ₹10 per crore both legs; stamp duty 0.003% on buy; GST 18% on (brokerage + transaction charge + SEBI fee). Brokerage model comes from `config/costs.yaml`.
- Delivery charges: STT 0.1% on buy and on sell; stamp duty 0.015% on buy; DP charge per scrip on each sell day (broker-specific, in config); same transaction/SEBI/GST rules.
- MIS margin is per stock (VaR + ELM), not a flat 5x. Use `config/margins.yaml`, with a conservative default for unknown symbols.
- Retail API rules since 1 Apr 2026: orders only from a whitelisted static IP, daily login with 2FA, sessions end each day, stay far below 10 orders per second.

## Promotion gates

- **Gate A, backtest → paper:** ≥300 dev-period trades (≥100 for swing); net expectancy > 0 at double the modeled slippage; walk-forward out-of-sample net expectancy > 0 and profit factor ≥ 1.15; parameter neighbours keep ≥50% of the chosen setting's net expectancy; Deflated Sharpe ≥ 0.90; holdout net positive (run once); P(15% drawdown within 250 trading days) < 10% at configured risk.
- **Gate B, paper → live:** ≥30 sessions and ≥40 trades; zero unhandled exceptions in the last 10 sessions; flat by 14:50 every day; paper slippage within modeled + 2 bps per side; paper P&L inside the backtest's 5th–95th percentile band for the same trade count; crash-recovery and /kill drills passed.
- **Gate C, small live → standard risk:** ≥50 live trades; live slippage ≤ modeled; results inside the backtest band; no risk-limit breach.

## Stack and layout

- Python 3.12, uv, pandas, numpy, pyarrow, duckdb, pydantic, pydantic-settings, pyyaml, pytest, hypothesis, ruff, matplotlib.
- All timestamps are tz-aware `Asia/Kolkata`.
- `src/nsealgo/{data,engine,strategies,brokers,live,reporting}`, `config/`, `scripts/`, `research/`, `tests/`, `docs/`. `data/`, `logs/` and `state/` are gitignored.

## Commands

- `uv run pytest -q`
- `uv run ruff check . && uv run ruff format .`
- `uv run python -m nsealgo.backtest --strategy orb --period dev --cost-tier base`
- `uv run python scripts/validate_strategy.py --strategy orb`
- `uv run python -m nsealgo.live --mode paper`

## Working style

- Tests first for anything touching money, fills, time or risk. Run tests and ruff before saying a task is done.
- Functions under 50 lines, files under 400 lines, type hints everywhere.
- End every task with: what changed, which tests ran, what you are unsure about.
- When a broker API detail is uncertain, read the broker's official docs or ask. Never guess endpoint or field names.
- Git: commit straight to `main` unless the owner asks for a branch.
