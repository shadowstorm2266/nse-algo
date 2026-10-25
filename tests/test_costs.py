from dataclasses import astuple
from decimal import Decimal

import pytest
from hypothesis import given
from hypothesis import strategies as st

from nsealgo.costs import (
    BrokerageModel,
    CostConfig,
    delivery_round_trip,
    intraday_round_trip,
    load_cost_config,
)
from nsealgo.settings import REPO_ROOT

D = Decimal


@pytest.fixture(scope="module")
def cfg() -> CostConfig:
    return load_cost_config(REPO_ROOT / "config" / "costs.yaml")


@pytest.mark.parametrize(
    ("preset", "expected"),
    [("zero", D("17.62")), ("shoonya", D("29.42")), ("dhan", D("53.02"))],
)
def test_intraday_50k_round_trip_to_the_paisa(cfg, preset, expected):
    cb = intraday_round_trip(50_000, 50_000, cfg.rates, cfg.brokerage_presets[preset])
    assert cb.total == expected


def test_intraday_50k_components_dhan(cfg):
    cb = intraday_round_trip(50_000, 50_000, cfg.rates, cfg.brokerage_presets["dhan"])
    assert cb.brokerage == D("30.00")  # min(20, 15) per leg
    assert cb.stt == D("12.50")
    assert cb.transaction_charge == D("2.97")
    assert cb.sebi_fee == D("0.10")
    assert cb.stamp_duty == D("1.50")
    assert cb.gst == D("5.95")  # 18% of 33.07
    assert cb.dp_charge == D("0.00")


def test_intraday_unequal_legs(cfg):
    cb = intraday_round_trip(50_000, 51_000, cfg.rates, cfg.brokerage_presets["zero"])
    assert cb.stt == D("12.75")
    assert cb.transaction_charge == D("3.00")  # 2.9997
    assert cb.sebi_fee == D("0.10")  # 0.101
    assert cb.stamp_duty == D("1.50")
    assert cb.gst == D("0.56")  # 18% of 3.1007 = 0.558126
    assert cb.total == D("17.91")


def test_delivery_50k_round_trip(cfg):
    cb = delivery_round_trip(50_000, 50_000, cfg.rates, cfg.brokerage_presets["zero"], 20)
    assert cb.stt == D("100.00")
    assert cb.stamp_duty == D("7.50")
    assert cb.transaction_charge == D("2.97")
    assert cb.sebi_fee == D("0.10")
    assert cb.gst == D("0.55")
    assert cb.dp_charge == D("20.00")
    assert cb.total == D("131.12")


def test_brokerage_models():
    assert BrokerageModel("zero").per_order(D(10**6)) == 0
    assert BrokerageModel("flat", flat_rupees=D(20)).per_order(D(100)) == D(20)
    fop = BrokerageModel("flat_or_pct", flat_rupees=D(20), pct=D("0.03"))
    assert fop.per_order(D(10_000)) == D(3)  # 0.03% lower
    assert fop.per_order(D(100_000)) == D(20)  # flat lower


@pytest.mark.parametrize(("buy", "sell"), [(0, 100), (100, 0), (-5, 100)])
def test_non_positive_values_rejected(cfg, buy, sell):
    with pytest.raises(ValueError):
        intraday_round_trip(buy, sell, cfg.rates, cfg.brokerage)


def test_config_presets_and_slippage(cfg):
    assert set(cfg.brokerage_presets) == {"zero", "shoonya", "dhan"}
    assert cfg.slippage_bps_per_side == {"base": D(3), "stress1": D(6), "stress2": D(10)}


values = st.decimals(min_value=D("1"), max_value=D("10000000"), places=2)


@given(buy=values, sell=values, preset=st.sampled_from(["zero", "shoonya", "dhan"]))
def test_total_is_sum_and_components_non_negative(cfg, buy, sell, preset):
    for cb in (
        intraday_round_trip(buy, sell, cfg.rates, cfg.brokerage_presets[preset]),
        delivery_round_trip(buy, sell, cfg.rates, cfg.brokerage_presets[preset], 20),
    ):
        parts = astuple(cb)[:-1]
        assert all(p >= 0 for p in parts)
        assert cb.total == sum(parts)
        # Below ~Rs 100 a leg, paisa rounding can legitimately make every component 0.
        if min(buy, sell) >= 100:
            assert cb.total > 0


@given(buy=values, sell=values)
def test_delivery_costs_more_than_intraday(cfg, buy, sell):
    b = cfg.brokerage_presets["shoonya"]
    assert (
        delivery_round_trip(buy, sell, cfg.rates, b, 0).total
        >= intraday_round_trip(buy, sell, cfg.rates, b).total
    )
