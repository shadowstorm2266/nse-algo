"""Build data/clean from data/raw: clean, QA, resample, calendar, features.

Per symbol (`process_symbol`): normalize, drop rows with a price <= 0 (each drop
is logged as an event), flag suspect prints and other anomalies, write 1m/5m/15m.
Then (`finish`): calendar, per-symbol quality summary, daily features and RVOL
profiles.
"""

from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from nsealgo.data.calendar import (
    BARS_PER_SESSION,
    build_calendar,
    classify_short_sessions,
)
from nsealgo.data.config import DataConfig
from nsealgo.data.features import daily_bars, daily_features, rvol_profile
from nsealgo.data.quality import (
    EVENT_COLS,
    bad_print_mask,
    event,
    nonpositive_mask,
    ohlc_inconsistent_mask,
    out_of_line_days,
    overnight_moves,
)
from nsealgo.data.raw import Normalized, normalize, read_raw
from nsealgo.data.resample import resample_bars, with_available_at
from nsealgo.data.store import write_bars, write_symbol_table


@dataclass
class SymbolResult:
    symbol: str
    daily: pd.DataFrame
    raw_session_bars: pd.DataFrame
    events: list[dict[str, Any]] = field(default_factory=list)
    stats: dict[str, Any] = field(default_factory=dict)


def _drop_nonpositive(bars: pd.DataFrame, res: SymbolResult) -> pd.DataFrame:
    mask = nonpositive_mask(bars)
    for r in bars[mask].itertuples():
        detail = f"o={r.open} h={r.high} l={r.low} c={r.close} v={r.volume}"
        res.events.append(
            event(res.symbol, r.session_date, "nonpositive_price", "dropped_row", detail, r.ts)
        )
    res.stats["nonpositive_rows_dropped"] = int(mask.sum())
    return bars[~mask]


def _flag_suspect_prints(bars: pd.DataFrame, cfg: DataConfig, res: SymbolResult) -> None:
    # Flag only: the heuristic also fires on real crashes and circuit-halt days
    # (e.g. 2020-03-13), so it must not remove data. The human reviews the list.
    q = cfg.quality
    bad = bad_print_mask(bars, q.bad_print_max_dev, q.bad_print_lookaround)
    for day, rows in bars[bad].groupby("session_date"):
        r = rows.iloc[0]
        detail = (
            f"{len(rows)} suspect bar(s); first o={r.open} h={r.high} l={r.low} c={r.close}; "
            f"day has {(bars['session_date'] == day).sum()} bars"
        )
        res.events.append(event(res.symbol, day, "suspect_print", "flagged", detail, r.ts))
    res.stats["suspect_print_days"] = bars.loc[bad, "session_date"].nunique()


def _log_counts(norm: Normalized, res: SymbolResult) -> None:
    for kind, df in (("out_of_session", norm.out_of_session), ("off_grid_ts", norm.off_grid)):
        for r in df.itertuples():
            res.events.append(
                event(res.symbol, r.session_date, kind, "dropped_rows", str(r.n_rows))
            )
        res.stats[f"{kind}_rows_dropped"] = int(df["n_rows"].sum())


def _flag(bars: pd.DataFrame, daily: pd.DataFrame, cfg: DataConfig, res: SymbolResult) -> None:
    q, sym = cfg.quality, res.symbol
    ohlc = ohlc_inconsistent_mask(bars)
    for r in bars[ohlc].itertuples():
        detail = f"o={r.open} h={r.high} l={r.low} c={r.close}"
        res.events.append(event(sym, r.session_date, "ohlc_inconsistent", "flagged", detail, r.ts))
    moves = overnight_moves(daily, q.overnight_move_flag)
    for r in moves.itertuples():
        detail = f"prev_close={r.prev_close} open={r.open} move={r.move:+.1%}"
        res.events.append(event(sym, r.session_date, "overnight_move", "flagged", detail))
    lines = out_of_line_days(
        daily, q.out_of_line_window_sessions, q.out_of_line_low, q.out_of_line_high
    )
    for r in lines.itertuples():
        detail = f"close={r.close} centered_median={r.ref:.2f} ratio={r.ratio:.2f}"
        res.events.append(event(sym, r.session_date, "out_of_line_day", "flagged", detail))
    res.stats |= {
        "duplicate_ts": 0,  # normalize() raises on any duplicate
        "zero_volume_bars": int(bars["volume"].eq(0).sum()),
        "ohlc_inconsistent": int(ohlc.sum()),
        "overnight_moves_gt_threshold": len(moves),
        "out_of_line_days": len(lines),
    }


def process_symbol(cfg: DataConfig, symbol: str) -> SymbolResult:
    """Clean one symbol, write its 1m/5m/15m bars, return daily bars, events and stats."""
    raw = read_raw(cfg.raw_dir, symbol)
    norm = normalize(raw, symbol, cfg.clean_start, cfg.clean_end, cfg.excluded())
    res = SymbolResult(symbol, pd.DataFrame(), norm.raw_session_bars.assign(symbol=symbol), [], {})
    _log_counts(norm, res)
    bars = _drop_nonpositive(norm.bars, res).reset_index(drop=True)
    _flag_suspect_prints(bars, cfg, res)
    res.daily = daily_bars(bars)
    _flag(bars, res.daily, cfg, res)
    write_bars(with_available_at(bars, 1), cfg.clean_dir, "1m")
    for minutes in (5, 15):
        write_bars(resample_bars(bars, minutes), cfg.clean_dir, f"{minutes}m")
    return res


def quality_row(res: SymbolResult, calendar: pd.DataFrame) -> dict[str, Any]:
    expected_per_day = calendar["max_bars"].where(calendar["no_trade"], BARS_PER_SESSION)
    expected = int(expected_per_day.sum())
    bars = int(res.daily["n_bars"].sum())
    return {
        "symbol": res.symbol,
        "first_session": res.daily["session_date"].min(),
        "last_session": res.daily["session_date"].max(),
        "sessions": len(res.daily),
        "calendar_sessions": len(calendar),
        "bars": bars,
        "expected_bars": expected,
        "missing_minutes_pct": round(100 * (1 - bars / expected), 4),
        **res.stats,
        "zero_volume_pct": round(100 * res.stats["zero_volume_bars"] / bars, 4),
    }


def finish(
    results: list[SymbolResult], cfg: DataConfig, holidays: set[Any]
) -> dict[str, pd.DataFrame]:
    """Calendar, quality tables and per-symbol features (written to data/clean/daily)."""
    daily = pd.concat([r.daily for r in results], ignore_index=True)
    calendar = build_calendar(daily[["symbol", "session_date", "n_bars"]], cfg.no_trade(), holidays)
    raw_counts = pd.concat([r.raw_session_bars for r in results], ignore_index=True)
    short = classify_short_sessions(
        raw_counts, cfg.excluded(), cfg.no_trade(), cfg.quality.short_session_bars
    )
    sessions = list(calendar["session_date"])
    complete = list(calendar.loc[~calendar["no_trade"], "session_date"])
    for r in results:
        feats = daily_features(
            r.daily, sessions, cfg.feature_warmup_sessions, cfg.atr_period, cfg.avg_window_sessions
        )
        write_symbol_table(feats, cfg.clean_dir, "features")
        b5 = pd.read_parquet(
            cfg.clean_dir / "5m" / f"symbol={r.symbol}", columns=["ts", "session_date", "volume"]
        )
        rv = rvol_profile(b5.assign(symbol=r.symbol), complete, cfg.avg_window_sessions)
        write_symbol_table(rv, cfg.clean_dir, "rvol")
    events = [e for r in results for e in r.events]
    return {
        "calendar": calendar,
        "short_sessions": short,
        "quality": pd.DataFrame([quality_row(r, calendar) for r in results]),
        "events": pd.DataFrame(events, columns=EVENT_COLS),
        "daily": daily,
    }
