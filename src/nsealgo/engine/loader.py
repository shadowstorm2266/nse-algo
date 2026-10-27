"""Backtest inputs from data/clean (DuckDB views), with the holdout lock.

Intraday bars load one calendar year at a time; daily bars are aggregated from 1m
bars (ts 09:15, available_at 15:30). Nothing on or after `holdout_start` is read
unless the caller passes `allow_holdout=True`.
"""

from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import duckdb
import pandas as pd
import yaml
from pydantic import BaseModel, ConfigDict, model_validator

from nsealgo.data.calendar import IST
from nsealgo.engine.market import BAR_COLS, MarketData
from nsealgo.settings import REPO_ROOT

RESEARCH_CONFIG_PATH = REPO_ROOT / "config" / "research.yaml"
UNIVERSE_PATH = REPO_ROOT / "config" / "universe.yaml"
OPEN_OFFSET = pd.Timedelta(hours=9, minutes=15)
CLOSE_OFFSET = pd.Timedelta(hours=15, minutes=30)


class HoldoutLockedError(RuntimeError):
    """A run would touch dates on or after holdout_start without explicit permission."""


class ResearchConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    dev_start: date
    dev_end: date
    validation_start: date
    validation_end: date
    holdout_start: date
    holdout_end: date

    @model_validator(mode="after")
    def _ordered(self) -> "ResearchConfig":
        days = [
            self.dev_start,
            self.dev_end,
            self.validation_start,
            self.validation_end,
            self.holdout_start,
            self.holdout_end,
        ]
        if days != sorted(days) or self.validation_end >= self.holdout_start:
            raise ValueError("research periods must be ordered dev < validation < holdout")
        return self


@dataclass(frozen=True)
class Period:
    label: str
    start: date
    end: date
    holdout: bool


def load_research_config(path: Path = RESEARCH_CONFIG_PATH) -> ResearchConfig:
    with path.open(encoding="utf-8") as fh:
        return ResearchConfig.model_validate(yaml.safe_load(fh))


def load_universe(path: Path = UNIVERSE_PATH) -> list[str]:
    with path.open(encoding="utf-8") as fh:
        return list(yaml.safe_load(fh)["symbols"])


def resolve_period(label: str, cfg: ResearchConfig, *, allow_holdout: bool) -> Period:
    spans = {
        "dev": (cfg.dev_start, cfg.dev_end),
        "validation": (cfg.validation_start, cfg.validation_end),
        "holdout": (cfg.holdout_start, cfg.holdout_end),
    }
    if label not in spans:
        raise ValueError(f"unknown period {label!r}; use one of {sorted(spans)}")
    start, end = spans[label]
    holdout = end >= cfg.holdout_start
    if holdout and not allow_holdout:
        raise HoldoutLockedError(
            f"period {label!r} reaches {end}, on or after holdout_start {cfg.holdout_start}; "
            "only the human may run it (--run-holdout)"
        )
    return Period(label, start, end, holdout)


def check_holdout(end: date, cfg: ResearchConfig, allow_holdout: bool) -> None:
    if end >= cfg.holdout_start and not allow_holdout:
        raise HoldoutLockedError(f"refusing to read data on or after {cfg.holdout_start}")


def _in_list(symbols: Sequence[str]) -> str:
    quoted = ", ".join("'" + s.replace("'", "''") + "'" for s in symbols)
    return f"({quoted})"


def load_calendar(con: duckdb.DuckDBPyConnection, start: date, end: date) -> pd.DataFrame:
    return con.execute(
        "SELECT session_date, no_trade FROM calendar WHERE session_date BETWEEN ? AND ? "
        "ORDER BY session_date",
        [start, end],
    ).df()


def session_counts(
    con: duckdb.DuckDBPyConnection,
    symbols: Sequence[str],
    period: tuple[date, date],
    *,
    research: ResearchConfig,
    allow_holdout: bool,
) -> dict[str, int]:
    """Sessions with bars per symbol in the inclusive `period` (0 for symbols without data)."""
    start, end = period
    check_holdout(end, research, allow_holdout)
    if not symbols:
        return {}
    rows = con.execute(
        "SELECT symbol, count(DISTINCT session_date) FROM bars_1m "
        f"WHERE symbol IN {_in_list(symbols)} AND session_date BETWEEN ? AND ? GROUP BY symbol",
        [start, end],
    ).fetchall()
    found = {s: int(n) for s, n in rows}
    return {s: found.get(s, 0) for s in symbols}


def lookback_start(con: duckdb.DuckDBPyConnection, start: date, sessions: int) -> date:
    """The session `sessions` sessions before `start` (or `start` itself for 0)."""
    if sessions <= 0:
        return start
    rows = con.execute(
        "SELECT session_date FROM calendar WHERE session_date < ? "
        "ORDER BY session_date DESC LIMIT ?",
        [start, sessions],
    ).fetchall()
    return pd.Timestamp(rows[-1][0]).date() if rows else start


def load_bars(
    con: duckdb.DuckDBPyConnection, timeframe: str, symbols: Sequence[str], start: date, end: date
) -> pd.DataFrame:
    where = f"symbol IN {_in_list(symbols)} AND session_date BETWEEN ? AND ?"
    if timeframe != "1d":
        cols = ", ".join(BAR_COLS)
        return con.execute(
            f"SELECT {cols} FROM bars_{timeframe} WHERE {where} ORDER BY symbol, ts", [start, end]
        ).df()
    df = con.execute(
        "SELECT symbol, session_date, arg_min(open, ts) AS open, max(high) AS high, "
        "min(low) AS low, arg_max(close, ts) AS close, sum(volume) AS volume "
        f"FROM bars_1m WHERE {where} GROUP BY symbol, session_date ORDER BY symbol, session_date",
        [start, end],
    ).df()
    midnight = pd.to_datetime(df["session_date"]).dt.tz_localize(IST)
    df["ts"] = midnight + OPEN_OFFSET
    df["available_at"] = midnight + CLOSE_OFFSET
    return df[BAR_COLS]


def load_features(
    con: duckdb.DuckDBPyConnection, symbols: Sequence[str], start: date, end: date
) -> pd.DataFrame:
    return con.execute(
        f"SELECT * FROM daily_features WHERE symbol IN {_in_list(symbols)} "
        "AND session_date BETWEEN ? AND ?",
        [start, end],
    ).df()


def market_chunks(
    con: duckdb.DuckDBPyConnection,
    timeframe: str,
    symbols: Sequence[str],
    sessions: Sequence[date],
    *,
    lookback_sessions: int,
    research: ResearchConfig,
    allow_holdout: bool,
) -> Iterator[MarketData]:
    """MarketData for the run sessions: one chunk per year intraday, one chunk for daily."""
    if not sessions:
        return
    check_holdout(max(sessions), research, allow_holdout)
    if timeframe == "1d":
        first = lookback_start(con, min(sessions), lookback_sessions)
        bars = load_bars(con, timeframe, symbols, first, max(sessions))
        feats = load_features(con, symbols, min(sessions), max(sessions))
        yield MarketData(timeframe, bars, sessions, feats)
        return
    for year in sorted({d.year for d in sessions}):
        days = [d for d in sessions if d.year == year]
        bars = load_bars(con, timeframe, symbols, days[0], days[-1])
        feats = load_features(con, symbols, days[0], days[-1])
        yield MarketData(timeframe, bars, days, feats)
