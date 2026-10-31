"""IPO v1 simulation engine (research only; applications are manual, hard rule 1): cash and
blocking conventions, same-day random choice, skip kinds, compounding, tax timing and no
look-ahead, on synthetic issues. Amounts are paise, days are date ordinals."""

from datetime import date, timedelta

import numpy as np
import pytest

from nsealgo.engine.ipo_sim import SimInput, Tax, TradingDays, draws, simulate

MON = date(2024, 1, 1)
CAP = 2_000_000  # Rs 20,000


def od(n: int) -> int:
    return (MON + timedelta(days=n)).toordinal()


def inp(*issues: dict) -> SimInput:
    def col(key: str, default=0, dtype=np.int64) -> np.ndarray:
        return np.array([i.get(key, default) for i in issues], dtype=dtype)

    return SimInput(
        app=col("app"),
        block=col("block", 1_500_000),
        p=col("p", 1.0, np.float64),
        free_allot=col("free_allot"),
        free_not=col("free_not"),
        pnl=col("pnl"),
        pnl_year=col("year", 2024),
        count_year=col("year", 2024),
        fy=col("fy", 2023),
    )


def run(x: SimInput, n_runs: int = 1, capital: int = CAP, tax: Tax | None = None, seed: int = 1):
    u, keys = draws(n_runs, len(x.app), seed)
    return simulate(x, capital, u, keys, tax)


def test_trading_days_step_over_holidays_and_extend_past_the_end():
    days = TradingDays([MON, MON + timedelta(1), MON + timedelta(3), MON + timedelta(4)])
    assert days.after(MON, 1) == MON + timedelta(1)
    assert days.after(MON + timedelta(1), 1) == MON + timedelta(3)  # Wed is a holiday
    assert days.after(MON + timedelta(2), 1) == MON + timedelta(3)  # from a non-trading day
    assert days.before(MON + timedelta(3), 1) == MON + timedelta(1)
    assert days.on_or_after(MON + timedelta(2)) == MON + timedelta(3)
    assert days.after(MON + timedelta(4), 1) == MON + timedelta(7)  # past the end: weekdays
    assert days.extended == {MON + timedelta(7)}
    with pytest.raises(ValueError):
        days.before(MON, 1)


def test_money_is_blocked_through_the_release_day_and_free_the_day_after():
    # A is not allotted; its release day is day 2, so the money is free from day 3
    a = {"app": od(0), "p": 0.0, "free_not": od(3), "free_allot": od(9)}
    b = {"app": od(2), "free_not": od(5), "free_allot": od(9)}
    c = {"app": od(3), "free_not": od(5), "free_allot": od(9)}
    r = run(inp(a, b, c))
    assert r.applied[0].tolist() == [True, False, True]
    assert r.skipped_blocked[0].tolist() == [False, True, False]
    assert not r.skipped_capital.any()


def test_an_allotted_application_returns_with_its_pnl_and_funds_two_at_once():
    win = {"app": od(0), "pnl": 500_000, "free_allot": od(6), "free_not": od(3)}
    b = {"app": od(6), "block": 1_500_000, "free_not": od(9), "free_allot": od(9), "p": 0.0}
    c = {"app": od(6), "block": 1_000_000, "free_not": od(9), "free_allot": od(9), "p": 0.0}
    r = run(inp(win, b, c))
    assert r.allotted[0].tolist() == [True, False, False]
    assert r.applied[0].tolist() == [True, True, True]  # Rs 25,000 covers 15,000 + 10,000
    assert r.final_cash[0] == CAP + 500_000


def test_issues_closing_the_same_day_are_chosen_uniformly_at_random():
    a = {"app": od(0), "p": 0.0, "free_not": od(3), "free_allot": od(3)}
    b = dict(a)
    r = run(inp(a, b), n_runs=4000)
    assert (r.applied.sum(axis=1) == 1).all()  # cash covers one of the two
    assert r.applied[:, 0].mean() == pytest.approx(0.5, abs=0.03)
    assert (r.skipped_blocked.sum(axis=1) == 1).all()


def test_a_skipped_issue_is_blocked_cash_or_capital_below_one_lot():
    big = {"app": od(0), "block": 2_500_000, "free_not": od(3), "free_allot": od(3)}
    r = run(inp(big))
    assert r.skipped_capital[0, 0] and not r.skipped_blocked[0, 0] and not r.applied[0, 0]


def test_a_withdrawn_issue_blocks_only_its_bid_window():
    gone = {"app": od(0), "p": 0.0, "pnl": 0, "free_not": od(1), "free_allot": od(1)}
    nxt = {"app": od(1), "p": 0.0, "free_not": od(4), "free_allot": od(4)}
    r = run(inp(gone, nxt))
    assert r.applied[0].tolist() == [True, True] and r.final_cash[0] == CAP


def test_allotment_frequency_follows_p():
    one = {"app": od(0), "p": 0.3, "pnl": 100, "free_not": od(3), "free_allot": od(5)}
    r = run(inp(one), n_runs=20_000)
    assert r.allotted[:, 0].mean() == pytest.approx(0.3, abs=0.01)
    assert r.final_cash.mean() == pytest.approx(CAP + 30, abs=1)


def test_tax_is_paid_on_its_due_day_in_that_year_and_never_on_a_loss():
    # FY 2023 gain of Rs 10,000 -> Rs 2,000 tax on day 10, counted in 2024; FY 2024 loses
    gain = {"app": od(0), "pnl": 1_000_000, "free_allot": od(3), "free_not": od(3), "fy": 2023}
    # needs the full Rs 30,000 on day 11: after the tax only Rs 28,000 is left
    big = {"app": od(11), "block": 2_900_000, "p": 0.0, "free_not": od(14), "free_allot": od(14)}
    loss = {"app": od(12), "pnl": -50_000, "free_allot": od(15), "free_not": od(15), "fy": 2024}
    tax = Tax(pct=20.0, day={2023: od(10), 2024: od(400)}, year={2023: 2024, 2024: 2024})
    r = run(inp(gain, big, loss), tax=tax)
    assert not r.skipped_blocked[0, 1] and r.skipped_capital[0, 1]
    assert r.tax_paid[2024][0] == 200_000
    assert r.final_cash[0] == CAP + 1_000_000 - 200_000 - 50_000
    no_tax = run(inp(gain, big, loss))
    assert no_tax.applied[0, 1] and no_tax.tax_paid == {}


def test_choices_never_depend_on_that_issue_or_later_issues_outcomes():
    rng = np.random.default_rng(7)
    n = 40
    apps = np.sort(rng.integers(0, 60, n))
    issues = [
        {
            "app": od(int(a)),
            "block": int(rng.integers(1_100_000, 1_500_001)),
            "p": float(rng.random()),
            "pnl": int(rng.integers(-300_000, 600_000)),
            "free_not": od(int(a) + 4),
            "free_allot": od(int(a) + 7),
        }
        for a in apps
    ]
    base = run(inp(*issues), n_runs=200, seed=3)
    j = 20
    changed = [dict(i) for i in issues]
    for i in changed[j:]:
        i["p"], i["pnl"] = 1.0 - i["p"], -i["pnl"]
    alt = run(inp(*changed), n_runs=200, seed=3)
    upto = np.flatnonzero(apps <= apps[j])  # every issue decided on or before issue j's day
    assert (base.applied[:, upto] == alt.applied[:, upto]).all()


def test_final_cash_is_capital_plus_allotted_pnl_less_tax():
    rng = np.random.default_rng(11)
    issues = [
        {
            "app": od(3 * k),
            "p": 0.5,
            "pnl": int(rng.integers(-200_000, 400_000)),
            "free_not": od(3 * k + 2),
            "free_allot": od(3 * k + 4),
            "fy": 2023 if k < 5 else 2024,
        }
        for k in range(10)
    ]
    tax = Tax(pct=20.0, day={2023: od(16), 2024: od(1000)}, year={2023: 2024, 2024: 2024})
    x = inp(*issues)
    r = run(x, n_runs=500, tax=tax)
    paid = sum(r.tax_paid.values())
    assert (r.final_cash == CAP + r.allotted.astype(np.int64) @ x.pnl - paid).all()


def test_draws_are_fixed_by_the_seed():
    u1, k1 = draws(5, 7, 42)
    u2, k2 = draws(5, 7, 42)
    assert u1.shape == k1.shape == (5, 7)
    assert (u1 == u2).all() and (k1 == k2).all() and not (u1 == k1).all()
