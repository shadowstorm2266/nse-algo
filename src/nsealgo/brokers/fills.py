"""Pure fill-price rules for the simulator.

All functions return the reference price (before slippage); `slip` then moves it
against us. A stop triggers on touch and fills at the stop, or at the open when the
bar gaps through it. A limit fills only when price trades strictly through it, at
the limit, or at the open when the bar opens through it.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

import pandas as pd

from nsealgo.engine.types import ExitReason, Order, OrderType, Side

BPS = Decimal(10_000)


@dataclass(frozen=True, slots=True)
class Bar:
    symbol: str
    ts: pd.Timestamp
    session_date: date
    open: float
    high: float
    low: float
    close: float


def dec(x: float) -> Decimal:
    """Exact decimal of the price as it prints (float() first: numpy reprs differ)."""
    return Decimal(str(float(x)))


def slip(ref: Decimal, side: Side, bps: Decimal) -> Decimal:
    """Buys fill `bps` above the reference, sells below."""
    return ref * (1 + side.sign * bps / BPS)


def stop_ref(side: Side, trigger: Decimal, bar: Bar) -> Decimal | None:
    if side is Side.BUY:
        if bar.open >= trigger:
            return dec(bar.open)
        return trigger if bar.high >= trigger else None
    if bar.open <= trigger:
        return dec(bar.open)
    return trigger if bar.low <= trigger else None


def limit_ref(side: Side, limit: Decimal, bar: Bar) -> Decimal | None:
    if side is Side.BUY:
        if bar.open < limit:
            return dec(bar.open)
        return limit if bar.low < limit else None
    if bar.open > limit:
        return dec(bar.open)
    return limit if bar.high > limit else None


def entry_ref(order: Order, bar: Bar) -> Decimal | None:
    if order.order_type is OrderType.MARKET:
        return dec(bar.open)
    if order.price is None:
        raise ValueError(f"{order.order_type} order without a price")
    if order.order_type is OrderType.STOP:
        return stop_ref(order.side, order.price, bar)
    return limit_ref(order.side, order.price, bar)


def first_leg(legs: Sequence[tuple[int, Order]], bar: Bar) -> tuple[int, Decimal] | None:
    """Of the OCO legs this bar triggers, the one that fills: nearest the open first
    (a leg the open gaps through has distance 0), exact ties to the lower order id."""
    open_ = dec(bar.open)
    hits = []
    for order_id, order in legs:
        ref = entry_ref(order, bar)
        if ref is not None:
            hits.append((abs(ref - open_), order_id, ref))
    if not hits:
        return None
    _, order_id, ref = min(hits)
    return order_id, ref


def bracket_exit(
    exit_side: Side,
    stop: Decimal | None,
    target: Decimal | None,
    bar: Bar,
    check_target: bool,
) -> tuple[ExitReason, Decimal] | None:
    """Exit of a bracketed position on this bar. If the bar touches both the stop and
    the target, the stop fills. `check_target=False` on the fill bar of a stop/limit
    entry, where part of the range came before the fill."""
    if stop is not None:
        ref = stop_ref(exit_side, stop, bar)
        if ref is not None:
            return ExitReason.STOP, ref
    if check_target and target is not None:
        ref = limit_ref(exit_side, target, bar)
        if ref is not None:
            return ExitReason.TARGET, ref
    return None
