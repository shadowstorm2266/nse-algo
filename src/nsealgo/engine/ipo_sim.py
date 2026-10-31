"""Monte Carlo simulation of IPO applications under a cash constraint (research only: IPO
applications are manual UPI and never automated, hard rule 1; no orders, so no
RiskGovernor). Rules: research/ipo_strategy_plan.md section 5.

Vectorised over runs. Amounts are integer paise and days are date ordinals, so every
comparison is exact. One application per issue per run:

- on its application day, after every release due that day, an issue is applied for if
  free cash (cash - blocked) covers its block; issues sharing a day are tried in a random
  order (one uniform per run and issue);
- it is allotted when its allotment uniform is below p;
- its block comes back on `free_allot` (with its P&L) or `free_not`, the first day the
  money is usable again;
- optional tax: on each financial year's due day, pct of that year's positive P&L of
  allotted sales is taken from cash.

The choice on a day uses only cash, blocks and the order uniforms, never p, P&L or later
issues (tests/test_ipo_sim.py checks this).
"""

from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field, fields
from datetime import date, timedelta

import numpy as np


class TradingDays:
    """NSE trading days with steps in trading days. Past the last known session,
    weekdays stand in; every such day used is kept in `extended`."""

    def __init__(self, days: Iterable[date]) -> None:
        self.days = sorted(set(days))
        if not self.days:
            raise ValueError("no trading days")
        self._set = set(self.days)
        self.extended: set[date] = set()

    def _is_day(self, d: date) -> bool:
        if d <= self.days[-1]:
            return d in self._set
        return d.weekday() < 5

    def after(self, d: date, n: int = 1) -> date:
        """The n-th trading day strictly after `d` (`d` need not be one)."""
        for _ in range(n):
            d += timedelta(days=1)
            while not self._is_day(d):
                d += timedelta(days=1)
        if d > self.days[-1]:
            self.extended.add(d)
        return d

    def before(self, d: date, n: int = 1) -> date:
        """The n-th trading day strictly before `d`."""
        for _ in range(n):
            d -= timedelta(days=1)
            while not self._is_day(d):
                if d < self.days[0]:
                    raise ValueError(f"no trading day before {d}")
                d -= timedelta(days=1)
        return d

    def on_or_after(self, d: date) -> date:
        return d if self._is_day(d) else self.after(d, 1)


@dataclass(frozen=True)
class SimInput:
    """One entry per issue, sorted by application day."""

    app: np.ndarray  # application day (date ordinal)
    block: np.ndarray  # paise blocked from the application day
    p: np.ndarray  # allotment probability
    free_allot: np.ndarray  # ordinal from which the money is usable again, if allotted
    free_not: np.ndarray  # ... if not allotted
    pnl: np.ndarray  # paise credited on free_allot when allotted
    pnl_year: np.ndarray  # calendar year of the sale (listing date)
    count_year: np.ndarray  # calendar year of the bid close
    fy: np.ndarray  # financial year (start year) of the sale

    def __post_init__(self) -> None:
        n = len(self.app)
        if any(len(getattr(self, f.name)) != n for f in fields(self)):
            raise ValueError("SimInput arrays differ in length")
        if (np.diff(self.app) < 0).any():
            raise ValueError("issues must be sorted by application day")
        if ((self.free_allot <= self.app) | (self.free_not <= self.app)).any():
            raise ValueError("money must stay blocked at least on the application day")

    def take(self, keep: np.ndarray) -> "SimInput":
        return SimInput(**{f.name: getattr(self, f.name)[keep] for f in fields(self)})


@dataclass(frozen=True)
class Tax:
    pct: float
    day: dict[int, int]  # financial year -> ordinal of the payment
    year: dict[int, int]  # financial year -> calendar year the payment counts against


@dataclass
class SimResult:
    applied: np.ndarray  # (runs, issues) bool
    allotted: np.ndarray
    skipped_blocked: np.ndarray  # free cash short, total cash enough
    skipped_capital: np.ndarray  # even total cash below the block
    final_cash: np.ndarray  # (runs,) paise, after every release and tax
    tax_paid: dict[int, np.ndarray] = field(default_factory=dict)  # year -> (runs,) paise


def draws(n_runs: int, n_issues: int, seed: int) -> tuple[np.ndarray, np.ndarray]:
    """(allotment uniforms, same-day order uniforms), each (runs, issues)."""
    rng = np.random.Generator(np.random.PCG64(seed))
    return rng.random((n_runs, n_issues)), rng.random((n_runs, n_issues))


class _State:
    def __init__(self, n_runs: int, n_issues: int, capital: int) -> None:
        self.cash = np.full(n_runs, capital, dtype=np.int64)
        self.blocked = np.zeros(n_runs, dtype=np.int64)
        shape = (n_runs, n_issues)
        self.applied = np.zeros(shape, dtype=bool)
        self.allotted = np.zeros(shape, dtype=bool)
        self.skipped_blocked = np.zeros(shape, dtype=bool)
        self.skipped_capital = np.zeros(shape, dtype=bool)
        self.tax_paid: dict[int, np.ndarray] = {}


def _events(x: SimInput, tax: Tax | None) -> list[tuple[int, int, int]]:
    """(ordinal, kind, key) sorted: kind 0 = allotted release, 1 = other release (key =
    issue), 2 = tax (key = financial year)."""
    ev = [(int(x.free_allot[i]), 0, i) for i in range(len(x.app))]
    ev += [(int(x.free_not[i]), 1, i) for i in range(len(x.app))]
    if tax is not None:
        ev += [(day, 2, fy) for fy, day in tax.day.items()]
    return sorted(ev)


def _fire(event: tuple[int, int, int], x: SimInput, st: _State, tax: Tax | None) -> None:
    _, kind, key = event
    if kind == 2:
        sold = x.fy == key
        gain = (st.allotted[:, sold].astype(np.int64) @ x.pnl[sold]).clip(min=0)
        paid = np.rint(gain * (tax.pct / 100)).astype(np.int64)
        st.cash -= paid
        year = tax.year[key]
        st.tax_paid[year] = st.tax_paid.get(year, 0) + paid
        return
    back = st.allotted[:, key] if kind == 0 else st.applied[:, key] & ~st.allotted[:, key]
    st.blocked -= x.block[key] * back
    if kind == 0:
        st.cash += x.pnl[key] * back


def _apply(idx: np.ndarray, x: SimInput, keys: np.ndarray, st: _State) -> None:
    """Applications on one day for issues `idx`, in each run's random order."""
    rows = np.arange(len(st.cash))
    free = st.cash - st.blocked
    order = idx[np.argsort(keys[:, idx], axis=1, kind="stable")]
    for pos in range(len(idx)):
        i = order[:, pos]
        b = x.block[i]
        ok = free >= b
        st.applied[rows, i] = ok
        st.skipped_blocked[rows, i] = ~ok & (st.cash >= b)
        st.skipped_capital[rows, i] = ~ok & (st.cash < b)
        free -= b * ok
        st.blocked += b * ok


def _days(app: np.ndarray) -> Iterator[tuple[int, np.ndarray]]:
    for day in np.unique(app):
        yield int(day), np.flatnonzero(app == day)


def simulate(
    x: SimInput, capital: int, u: np.ndarray, keys: np.ndarray, tax: Tax | None = None
) -> SimResult:
    """Run every path at once; `u` and `keys` come from `draws` (runs x issues)."""
    if u.shape != keys.shape or u.shape[1] != len(x.app):
        raise ValueError("draws do not match the issues")
    st = _State(u.shape[0], len(x.app), capital)
    events, k = _events(x, tax), 0
    for day, idx in _days(x.app):
        while k < len(events) and events[k][0] <= day:
            _fire(events[k], x, st, tax)
            k += 1
        _apply(idx, x, keys, st)
        st.allotted[:, idx] = st.applied[:, idx] & (u[:, idx] < x.p[idx])
    for event in events[k:]:
        _fire(event, x, st, tax)
    if st.blocked.any():
        raise AssertionError("money still blocked after every release")
    return SimResult(
        applied=st.applied,
        allotted=st.allotted,
        skipped_blocked=st.skipped_blocked,
        skipped_capital=st.skipped_capital,
        final_cash=st.cash,
        tax_paid=st.tax_paid,
    )
