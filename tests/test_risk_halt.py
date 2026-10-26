import pytest
from pydantic import ValidationError

from nsealgo.engine.config import HaltModes
from nsealgo.engine.risk import RiskGovernor
from nsealgo.engine.sessions import TradingCalendar
from nsealgo.engine.types import Order, Product, Rejection, RejectReason, Side
from tests.data_helpers import business_days
from tests.engine_helpers import cost_config, entry, exit_, margins, pos_view, risk_config, snap, ts

DAYS = business_days("2024-01-01", 10)
LONG = entry("X", Side.BUY, stop=495.0)
MARKS = {"X": 500.0}


def governor(mode: str) -> RiskGovernor:
    return RiskGovernor(
        risk_config(),
        margins(),
        TradingCalendar(DAYS),
        cost_config(),
        "shoonya",
        product=Product.MIS,
        mode=mode,
    )


def review(gov, day_i: int, equity: str, intent=LONG, **kw):
    now = ts(DAYS[day_i], "10:00")
    return gov.review(intent, snap(now, equity=equity, peak="20000", marks=MARKS, **kw), now)


def test_record_mode_keeps_trading_and_stores_first_fire_once():
    gov = governor("backtest")
    assert gov.halt is None
    assert isinstance(review(gov, 1, "17000.01"), Order)  # 14.99995% < 15%
    assert gov.halt is None
    assert isinstance(review(gov, 2, "17000"), Order)  # exactly 15%: would fire
    assert gov.halt is not None
    assert gov.halt.date == DAYS[2]
    assert gov.halt.drawdown_pct == pytest.approx(15.0)
    assert isinstance(review(gov, 3, "16000"), Order)
    assert gov.halt.date == DAYS[2]  # first fire only
    assert not gov.latched


@pytest.mark.parametrize("mode", ["paper", "live"])
def test_latch_mode_rejects_and_stays_latched_after_recovery(mode):
    gov = governor(mode)
    r = review(gov, 2, "17000")
    assert isinstance(r, Rejection) and r.reason is RejectReason.DRAWDOWN_HALT
    r = review(gov, 3, "20000")  # equity recovered
    assert isinstance(r, Rejection) and r.reason is RejectReason.DRAWDOWN_HALT
    held = (pos_view("X", 10, "500"),)
    assert isinstance(review(gov, 3, "20000", exit_("X"), positions=held), Order)


@pytest.mark.parametrize("bad", [{"paper": "record"}, {"live": "record"}, {"backtest": "off"}])
def test_paper_and_live_must_latch(bad):
    modes = {"backtest": "record", "paper": "latch", "live": "latch"} | bad
    with pytest.raises(ValidationError):
        HaltModes(**modes)


def test_repo_config_records_in_backtest_and_latches_live():
    modes = risk_config().halt_mode
    assert (modes.backtest, modes.paper, modes.live) == ("record", "latch", "latch")


def test_observe_tracks_drawdown_between_reviews():
    # The halt state is updated from equity marks even when no entry is attempted.
    gov = governor("paper")
    gov.observe(snap(ts(DAYS[1], "11:00"), equity="16900"))
    assert gov.latched and gov.halt.date == DAYS[1]
