"""Trading cost model for NSE equity cash: intraday (MIS) and delivery (CNC).

Pure functions on Decimal rupees. Each component is computed exactly and then
rounded to the paisa (half-up); `total` is the sum of the rounded components.
Slippage is not a charge here: it is applied to fill prices by the simulator
using `CostConfig.slippage_bps_per_side`.
"""

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import Any, Literal

import yaml

PAISA = Decimal("0.01")
HUNDRED = Decimal(100)
CRORE = Decimal(10_000_000)

BrokerageKind = Literal["zero", "flat_or_pct", "flat"]
Number = Decimal | int | float | str


def _dec(x: Number) -> Decimal:
    # str() first so floats like 0.00297 become the decimal they look like.
    return x if isinstance(x, Decimal) else Decimal(str(x))


def _paisa(x: Decimal) -> Decimal:
    return x.quantize(PAISA, rounding=ROUND_HALF_UP)


def _pct(value: Decimal, pct: Decimal) -> Decimal:
    return value * pct / HUNDRED


@dataclass(frozen=True)
class BrokerageModel:
    """Per-order brokerage. Amounts in rupees, `pct` in percent."""

    kind: BrokerageKind
    flat_rupees: Decimal = Decimal(0)
    pct: Decimal = Decimal(0)

    def per_order(self, order_value: Decimal) -> Decimal:
        if self.kind == "zero":
            return Decimal(0)
        if self.kind == "flat":
            return self.flat_rupees
        if self.kind == "flat_or_pct":
            return min(self.flat_rupees, _pct(order_value, self.pct))
        raise ValueError(f"unknown brokerage model {self.kind!r}")


@dataclass(frozen=True)
class StatutoryRates:
    """Statutory rates; every `*_pct` field is in percent."""

    transaction_charge_pct: Decimal
    sebi_fee_per_crore: Decimal
    gst_pct: Decimal
    intraday_stt_sell_pct: Decimal
    intraday_stamp_buy_pct: Decimal
    delivery_stt_buy_pct: Decimal
    delivery_stt_sell_pct: Decimal
    delivery_stamp_buy_pct: Decimal


@dataclass(frozen=True)
class CostBreakdown:
    """Round-trip charges in rupees, each rounded to the paisa."""

    brokerage: Decimal
    stt: Decimal
    transaction_charge: Decimal
    sebi_fee: Decimal
    stamp_duty: Decimal
    gst: Decimal
    dp_charge: Decimal
    total: Decimal


@dataclass(frozen=True)
class CostConfig:
    rates: StatutoryRates
    brokerage_presets: dict[str, BrokerageModel]
    active_brokerage: str
    dp_charge_per_scrip: Decimal
    slippage_bps_per_side: dict[str, Decimal]

    @property
    def brokerage(self) -> BrokerageModel:
        return self.brokerage_presets[self.active_brokerage]


def _validate_values(buy_value: Decimal, sell_value: Decimal) -> None:
    if buy_value <= 0 or sell_value <= 0:
        raise ValueError(f"order values must be positive, got buy={buy_value} sell={sell_value}")


def _build(
    *,
    brokerage: Decimal,
    stt: Decimal,
    turnover: Decimal,
    stamp: Decimal,
    dp_charge: Decimal,
    rates: StatutoryRates,
) -> CostBreakdown:
    txn = _pct(turnover, rates.transaction_charge_pct)
    sebi = turnover * rates.sebi_fee_per_crore / CRORE
    gst = _pct(brokerage + txn + sebi, rates.gst_pct)
    parts = [_paisa(p) for p in (brokerage, stt, txn, sebi, stamp, gst, dp_charge)]
    return CostBreakdown(*parts, total=sum(parts, Decimal(0)))


def intraday_round_trip(
    buy_value: Number, sell_value: Number, rates: StatutoryRates, brokerage: BrokerageModel
) -> CostBreakdown:
    """Charges for one MIS buy order and one MIS sell order of the given rupee values."""
    buy, sell = _dec(buy_value), _dec(sell_value)
    _validate_values(buy, sell)
    return _build(
        brokerage=brokerage.per_order(buy) + brokerage.per_order(sell),
        stt=_pct(sell, rates.intraday_stt_sell_pct),
        turnover=buy + sell,
        stamp=_pct(buy, rates.intraday_stamp_buy_pct),
        dp_charge=Decimal(0),
        rates=rates,
    )


def delivery_round_trip(
    buy_value: Number,
    sell_value: Number,
    rates: StatutoryRates,
    brokerage: BrokerageModel,
    dp_charge_per_scrip: Number,
) -> CostBreakdown:
    """Charges for one CNC buy and one CNC sell of a single scrip (one DP charge).

    The DP charge is taken as billed (GST-inclusive) and is not added to the GST base.
    """
    buy, sell = _dec(buy_value), _dec(sell_value)
    _validate_values(buy, sell)
    return _build(
        brokerage=brokerage.per_order(buy) + brokerage.per_order(sell),
        stt=_pct(buy, rates.delivery_stt_buy_pct) + _pct(sell, rates.delivery_stt_sell_pct),
        turnover=buy + sell,
        stamp=_pct(buy, rates.delivery_stamp_buy_pct),
        dp_charge=_dec(dp_charge_per_scrip),
        rates=rates,
    )


def _parse_brokerage(raw: dict[str, Any]) -> BrokerageModel:
    kind = raw["model"]
    if kind not in ("zero", "flat_or_pct", "flat"):
        raise ValueError(f"unknown brokerage model {kind!r}")
    if kind == "zero":
        return BrokerageModel("zero")
    pct = _dec(raw["pct"]) if kind == "flat_or_pct" else Decimal(0)
    return BrokerageModel(kind, flat_rupees=_dec(raw["flat_rupees"]), pct=pct)


def load_cost_config(path: Path) -> CostConfig:
    """Parse config/costs.yaml. Missing keys raise KeyError rather than defaulting."""
    with path.open(encoding="utf-8") as fh:
        raw = yaml.safe_load(fh)
    st = raw["statutory"]
    rates = StatutoryRates(
        transaction_charge_pct=_dec(st["transaction_charge_pct"]),
        sebi_fee_per_crore=_dec(st["sebi_fee_per_crore"]),
        gst_pct=_dec(st["gst_pct"]),
        intraday_stt_sell_pct=_dec(st["intraday"]["stt_sell_pct"]),
        intraday_stamp_buy_pct=_dec(st["intraday"]["stamp_buy_pct"]),
        delivery_stt_buy_pct=_dec(st["delivery"]["stt_buy_pct"]),
        delivery_stt_sell_pct=_dec(st["delivery"]["stt_sell_pct"]),
        delivery_stamp_buy_pct=_dec(st["delivery"]["stamp_buy_pct"]),
    )
    presets = {name: _parse_brokerage(p) for name, p in raw["brokerage"]["presets"].items()}
    active = raw["brokerage"]["active"]
    if active not in presets:
        raise ValueError(f"active brokerage preset {active!r} not in presets")
    return CostConfig(
        rates=rates,
        brokerage_presets=presets,
        active_brokerage=active,
        dp_charge_per_scrip=_dec(raw["dp_charge_per_scrip_rupees"]),
        slippage_bps_per_side={k: _dec(v) for k, v in raw["slippage_bps_per_side"].items()},
    )
