"""Trading calendar and session clock helpers for the engine."""

from bisect import bisect_right
from collections.abc import Collection, Iterable, Sequence
from datetime import date, datetime, time

import pandas as pd

from nsealgo.data.calendar import IST, SESSION_OPEN

SESSION_CLOSE = time(15, 30)
TIMEFRAMES = {"1m": 1, "5m": 5, "15m": 15, "1d": None}


def at(day: date, t: time) -> pd.Timestamp:
    """Tz-aware IST timestamp for wall-clock time `t` on `day`."""
    return pd.Timestamp(datetime.combine(day, t)).tz_localize(IST)


def session_close(day: date) -> pd.Timestamp:
    return at(day, SESSION_CLOSE)


def check_on_grid(minutes: int, times: Iterable[time]) -> None:
    """Raise if any of `times` is not a bar boundary of an N-minute grid anchored at 09:15."""
    open_min = SESSION_OPEN.hour * 60 + SESSION_OPEN.minute
    off = [t for t in times if (t.hour * 60 + t.minute - open_min) % minutes or t.second]
    if off:
        names = ", ".join(t.strftime("%H:%M") for t in off)
        raise ValueError(f"{names} not on the {minutes}m bar grid; choose another timeframe")


class TradingCalendar:
    """Ordered sessions plus the no_trade set. Holds no prices.

    In a backtest it comes from the data calendar; in paper/live from the exchange
    holiday list. `next_tradeable_after` skips no_trade sessions.
    """

    def __init__(self, sessions: Sequence[date], no_trade: Collection[date] = ()) -> None:
        self.sessions: tuple[date, ...] = tuple(sorted(sessions))
        self.no_trade: frozenset[date] = frozenset(no_trade)
        unknown = self.no_trade - set(self.sessions)
        if unknown:
            raise ValueError(f"no_trade dates not in the calendar: {sorted(unknown)}")

    @classmethod
    def from_frame(cls, calendar: pd.DataFrame) -> "TradingCalendar":
        """From a frame with columns session_date and no_trade (the data calendar)."""
        days = [pd.Timestamp(d).date() for d in calendar["session_date"]]
        flags = calendar["no_trade"].astype(bool).tolist()
        return cls(days, [d for d, f in zip(days, flags, strict=True) if f])

    def is_no_trade(self, day: date) -> bool:
        return day in self.no_trade

    def next_tradeable_after(self, day: date) -> date | None:
        i = bisect_right(self.sessions, day)
        for d in self.sessions[i:]:
            if d not in self.no_trade:
                return d
        return None
