"""IPO v1 reporting: per-year statistics from a simulation, the Nifty 50 TRI benchmark on a
toy series, and the first-pass checks' PASS/FAIL logic (ties fail)."""

from datetime import date, timedelta

import numpy as np
import pandas as pd
import pytest

from nsealgo.engine.ipo_sim import SimInput, draws, simulate
from nsealgo.reporting.ipo_report import benchmark_returns, first_pass_checks, summarize

CAP = 2_000_000


def _od(d: date) -> int:
    return d.toordinal()


def test_summary_attributes_pnl_to_the_sale_year_and_returns_to_the_years_start_equity():
    d1, d2 = date(2024, 6, 3), date(2025, 6, 2)
    x = SimInput(
        app=np.array([_od(d1), _od(d2)]),
        block=np.array([1_500_000, 1_500_000]),
        p=np.array([1.0, 1.0]),
        free_allot=np.array([_od(d1 + timedelta(7)), _od(d2 + timedelta(7))]),
        free_not=np.array([_od(d1 + timedelta(3)), _od(d2 + timedelta(3))]),
        pnl=np.array([200_000, -100_000]),
        pnl_year=np.array([2024, 2025]),
        count_year=np.array([2024, 2025]),
        fy=np.array([2024, 2025]),
    )
    u, keys = draws(3, 2, 5)
    s = summarize(simulate(x, CAP, u, keys), x, [2024, 2025], CAP)
    y24, y25, tot = s["years"]["2024"], s["years"]["2025"], s["overall"]
    assert y24["net_rs"]["median"] == 2_000 and y24["net_pct"]["median"] == pytest.approx(10.0)
    assert y25["net_rs"]["median"] == -1_000
    assert y25["net_pct"]["median"] == pytest.approx(-1_000 / 22_000 * 100)
    assert tot["net_rs"]["mean"] == 1_000 and tot["net_pct"]["median"] == pytest.approx(5.0)
    assert y24["applications"]["mean"] == 1 and y25["allotments"]["median"] == 1
    assert y24["p_loss"] == 0 and y25["p_loss"] == 1 and tot["p_losing_year"] == 1
    assert s["median_run"]["years_pct"]["2024"] == pytest.approx(10.0)


def test_benchmark_is_the_tri_less_the_expense_ratio_from_the_base_close():
    tri = pd.Series(
        [100.0, 105.0, 110.0, 99.0, 120.0],
        index=[
            date(2018, 12, 31),
            date(2019, 6, 28),
            date(2019, 12, 31),
            date(2020, 12, 31),
            date(2021, 3, 31),
        ],
    )
    end = date(2021, 3, 31)
    b = benchmark_returns(tri, date(2018, 12, 31), end, [2019, 2020, 2021], CAP, 0.0)
    assert b["years"]["2019"] == pytest.approx(10.0)
    assert b["years"]["2020"] == pytest.approx(-10.0)
    assert b["years"]["2021"] == pytest.approx((120 / 99 - 1) * 100)
    assert b["total_pct"] == pytest.approx(20.0) and b["value_end_rs"] == pytest.approx(24_000)
    e = benchmark_returns(tri, date(2018, 12, 31), end, [2019, 2020, 2021], CAP, 0.05)
    days = (end - date(2018, 12, 31)).days
    assert e["total_pct"] == pytest.approx((1.2 * (1 - 0.0005 / 365) ** days - 1) * 100)
    with pytest.raises(ValueError):
        benchmark_returns(tri, date(2018, 12, 28), end, [2019], CAP, 0.0)


def _summary(mean_rs: float, median_total: float, year_medians: list[float], p_loss: float):
    years = {str(2019 + i): {"net_pct": {"median": v}} for i, v in enumerate(year_medians)}
    return {
        "overall": {
            "net_rs": {"mean": mean_rs},
            "net_pct": {"median": median_total},
            "p_losing_year": p_loss,
        },
        "years": years,
    }


def test_first_pass_checks_pass_fail_and_ties():
    bench = {"total_pct": 100.0, "years": {str(y): 10.0 for y in range(2019, 2027)}}
    five = [11, 11, 11, 11, 11, 9, 9, 10]  # 5 of 8 strictly above; 2026 ties
    checks = first_pass_checks(_summary(1.0, 0, [], 0), _summary(0, 101.0, five, 0.42), bench)
    by = {c["check"]: c for c in checks}
    assert by[1]["verdict"] == "PASS" and by[2]["verdict"] == "PASS"
    assert by[2]["years_beaten"] == 5 and by[3]["verdict"] == "REPORTED"
    assert by[3]["value"] == pytest.approx(0.42)
    four = [11, 11, 11, 11, 10, 9, 9, 10]
    checks = first_pass_checks(_summary(0.0, 0, [], 0), _summary(0, 101.0, four, 0.1), bench)
    by = {c["check"]: c for c in checks}
    assert by[1]["verdict"] == "FAIL"  # a mean of exactly 0 is not > 0
    assert by[2]["verdict"] == "FAIL" and by[2]["years_beaten"] == 4
    tie = first_pass_checks(_summary(1.0, 0, [], 0), _summary(0, 100.0, five, 0.1), bench)
    assert {c["check"]: c for c in tie}[2]["verdict"] == "FAIL"  # overall tie
