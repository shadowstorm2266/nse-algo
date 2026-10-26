"""Simulated broker for backtests.

`process(bars)` handles one bar group (bars that start at the same time), in order:
1. orders whose `expires_at` is before the bar expire;
2. market exits fill at the open for every symbol, then market entries, so that
   morning's sale proceeds can fund that morning's buys;
3. resting STOP/LIMIT orders per symbol: OCO entry legs (the one nearest the open
   fills, siblings are cancelled), then bracket children (stop before target).
Every fill pays `costs.fill_charges` plus slippage. The DP charge applies to the
first CNC sell of a scrip in each session. A CNC buy that free cash cannot cover is
rejected (INSUFFICIENT_CASH), as a real broker would.
"""

import logging
from collections.abc import Callable, Mapping
from dataclasses import dataclass, replace
from datetime import date
from decimal import Decimal
from types import MappingProxyType
from typing import Protocol

import pandas as pd

from nsealgo.brokers.base import BrokerPosition
from nsealgo.brokers.fills import Bar, bracket_exit, dec, first_leg, slip
from nsealgo.costs import CostBreakdown, CostConfig, fill_charges
from nsealgo.engine.types import (
    ExitReason,
    Fill,
    Order,
    OrderRole,
    OrderStatus,
    OrderType,
    OrderView,
    Product,
    Side,
)

logger = logging.getLogger("nsealgo.broker")
ZERO = Decimal(0)
EXIT_ROLES = (OrderRole.EXIT, OrderRole.STOP, OrderRole.TARGET)
CHILD_ROLES = (OrderRole.STOP, OrderRole.TARGET)
WORKING = OrderStatus.WORKING


class FundsView(Protocol):
    def free_cash(self) -> Decimal: ...


@dataclass
class _State:
    order_id: int
    order: Order
    status: OrderStatus = WORKING
    fill_bar_child: bool = False  # child of a STOP/LIMIT entry that filled on this bar


@dataclass(frozen=True, slots=True)
class BrokerEvent:
    ts: pd.Timestamp | None
    order_id: int
    symbol: str
    status: OrderStatus
    reason: str


class SimBroker:
    def __init__(
        self,
        costs: CostConfig,
        brokerage_preset: str,
        slippage_bps: Decimal,
        *,
        funds: FundsView,
        on_fill: Callable[[Fill], object],
    ) -> None:
        self._rates = costs.rates
        self._preset = costs.brokerage_presets[brokerage_preset]
        self._bps = slippage_bps
        self._funds = funds
        self._on_fill = on_fill
        self._book: dict[int, _State] = {}
        self._positions: dict[str, BrokerPosition] = {}
        self._dp_paid: set[tuple[str, date]] = set()
        self._next_id = 1
        self.events: list[BrokerEvent] = []
        self.now: pd.Timestamp | None = None

    # --- Broker protocol ---

    def place(self, order: Order) -> int:
        order_id = self._next_id
        self._next_id += 1
        self._book[order_id] = _State(order_id, order)
        return order_id

    def cancel(self, order_id: int, reason: str = "cancelled") -> bool:
        st = self._book.get(order_id)
        if st is None or st.status is not WORKING:
            return False
        self._finish(st, OrderStatus.CANCELLED, reason)
        return True

    def positions(self) -> Mapping[str, BrokerPosition]:
        return MappingProxyType(dict(self._positions))

    def orders(self) -> tuple[OrderView, ...]:
        return tuple(OrderView(s.order_id, s.order, s.status) for s in self._book.values())

    # --- simulation ---

    def active_symbols(self) -> set[str]:
        return {s.order.symbol for s in self._working()} | set(self._positions)

    def process(self, bars: Mapping[str, Bar]) -> list[Fill]:
        fills: list[Fill] = []
        if bars:
            self.now = max(b.ts for b in bars.values())
        for st in self._working():
            bar, exp = bars.get(st.order.symbol), st.order.expires_at
            if bar is not None and exp is not None and bar.ts > exp:
                self._finish(st, OrderStatus.EXPIRED, f"not filled by {exp}")
        for role in (OrderRole.EXIT, OrderRole.ENTRY):
            for st in self._working():
                o, bar = st.order, bars.get(st.order.symbol)
                is_market = o.order_type is OrderType.MARKET and o.role is role
                if is_market and bar is not None and st.status is WORKING and _eligible(o, bar):
                    self._fill(st, bar, dec(bar.open), fills)
        for symbol in sorted(bars):
            self._resting(bars[symbol], fills)
        for st in self._book.values():
            st.fill_bar_child = False
        return fills

    def end_session(self, day: date) -> None:
        """Cancel MIS orders; expire CNC orders whose fill session has passed. CNC orders
        deferred to a later session and CNC bracket children stay working."""
        for st in self._working():
            o = st.order
            if o.product is Product.MIS:
                self._finish(st, OrderStatus.CANCELLED, "session end")
            elif o.role in (OrderRole.ENTRY, OrderRole.EXIT) and (
                o.not_before is None or o.not_before <= day
            ):
                self._finish(st, OrderStatus.EXPIRED, "not filled in its session")
        self._book = {i: s for i, s in self._book.items() if s.status is WORKING}

    def force_close(
        self, symbol: str, price: float, ts: pd.Timestamp, day: date, reason: ExitReason
    ) -> Fill | None:
        """Close a position at `price` (+ slippage and charges): data-gap fallbacks and
        the end of a run. Cancels the symbol's other working orders."""
        pos = self._positions.get(symbol)
        if pos is None:
            return None
        self.now = ts
        for st in self._working(symbol):
            self._finish(st, OrderStatus.CANCELLED, f"force close: {reason}")
        side = Side.SELL if pos.qty > 0 else Side.BUY
        order = Order(
            symbol,
            pos.product,
            side,
            abs(pos.qty),
            OrderType.MARKET,
            OrderRole.EXIT,
            ts,
            ref_price=dec(price),
            exit_reason=reason,
        )
        fills: list[Fill] = []
        self._fill(
            self._book[self.place(order)],
            Bar(symbol, ts, day, price, price, price, price),
            dec(price),
            fills,
        )
        return fills[0] if fills else None

    # --- internals ---

    def _working(self, symbol: str | None = None) -> list[_State]:
        return [
            s
            for s in self._book.values()
            if s.status is WORKING and (symbol is None or s.order.symbol == symbol)
        ]

    def _resting(self, bar: Bar, fills: list[Fill]) -> None:
        legs = [
            (s.order_id, s.order)
            for s in self._working(bar.symbol)
            if s.order.role is OrderRole.ENTRY
            and s.order.order_type is not OrderType.MARKET
            and _eligible(s.order, bar)
        ]
        hit = first_leg(legs, bar) if legs else None
        if hit is not None:
            self._fill(self._book[hit[0]], bar, hit[1], fills, entry_on_bar=True)
        kids = [s for s in self._working(bar.symbol) if s.order.role in CHILD_ROLES]
        pos = self._positions.get(bar.symbol)
        if not kids or pos is None:
            return
        stop = next((s for s in kids if s.order.role is OrderRole.STOP), None)
        target = next((s for s in kids if s.order.role is OrderRole.TARGET), None)
        exit_side = Side.SELL if pos.qty > 0 else Side.BUY
        out = bracket_exit(
            exit_side,
            stop.order.price if stop else None,
            target.order.price if target else None,
            bar,
            check_target=not any(s.fill_bar_child for s in kids),
        )
        if out is not None:
            reason, ref = out
            self._fill(stop if reason is ExitReason.STOP else target, bar, ref, fills)

    def _charges(self, o: Order, value: Decimal, day: date) -> CostBreakdown:
        model = self._preset.intraday if o.product is Product.MIS else self._preset.delivery
        first_sell = (o.symbol, day) not in self._dp_paid
        dp = self._preset.dp_charge_per_scrip if _cnc_sell(o) and first_sell else ZERO
        return fill_charges(o.product, o.side, value, self._rates, model, dp)

    def _fill(
        self, st: _State, bar: Bar, ref: Decimal, fills: list[Fill], entry_on_bar: bool = False
    ) -> None:
        o = st.order
        if o.role in EXIT_ROLES and not self._reduces(o):
            self._finish(st, OrderStatus.REJECTED, "exit does not reduce a position")
            return
        price = slip(ref, o.side, self._bps)
        charges = self._charges(o, price * o.qty, bar.session_date)
        if o.product is Product.CNC and o.side is Side.BUY:
            need, have = price * o.qty + charges.total, self._funds.free_cash()
            if need > have:
                self._finish(
                    st, OrderStatus.REJECTED, f"INSUFFICIENT_CASH: need {need:.2f}, free {have:.2f}"
                )
                return
        if _cnc_sell(o):
            self._dp_paid.add((o.symbol, bar.session_date))
        st.status = OrderStatus.FILLED
        fill = Fill(
            st.order_id,
            o.symbol,
            o.product,
            o.side,
            o.qty,
            bar.ts,
            bar.session_date,
            price,
            ref,
            charges,
            o.role,
            o.exit_reason,
            o.group_id,
            o.stop_loss,
        )
        self._move_position(fill)
        self._on_fill(fill)
        fills.append(fill)
        self._after_fill(st, bar, entry_on_bar)

    def _reduces(self, o: Order) -> bool:
        pos = self._positions.get(o.symbol)
        return pos is not None and (pos.qty > 0) == (o.side is Side.SELL) and o.qty <= abs(pos.qty)

    def _move_position(self, fill: Fill) -> None:
        pos = self._positions.get(fill.symbol)
        qty = (pos.qty if pos else 0) + fill.side.sign * fill.qty
        if qty == 0:
            del self._positions[fill.symbol]
        else:
            self._positions[fill.symbol] = BrokerPosition(fill.symbol, fill.product, qty)

    def _after_fill(self, st: _State, bar: Bar, entry_on_bar: bool) -> None:
        symbol = st.order.symbol
        if st.order.role is OrderRole.ENTRY:
            for s in self._working(symbol):
                if s.order.role is OrderRole.ENTRY:
                    self._finish(s, OrderStatus.CANCELLED, f"OCO: order {st.order_id} filled")
            self._bracket(st, bar, entry_on_bar)
            return
        pos = self._positions.get(symbol)
        for s in self._working(symbol):
            if pos is None and s.order.role in EXIT_ROLES:
                self._finish(s, OrderStatus.CANCELLED, "position closed")
            elif pos is not None and s.order.role in CHILD_ROLES and s.order.qty > abs(pos.qty):
                s.order = replace(s.order, qty=abs(pos.qty))

    def _bracket(self, st: _State, bar: Bar, entry_on_bar: bool) -> None:
        o = st.order
        side = o.side.opposite()
        kids = []
        if o.stop_loss is not None:
            kids.append((OrderType.STOP, OrderRole.STOP, o.stop_loss, ExitReason.STOP))
        if o.target is not None:
            kids.append((OrderType.LIMIT, OrderRole.TARGET, o.target, ExitReason.TARGET))
        for kind, role, price, reason in kids:
            child = Order(
                o.symbol,
                o.product,
                side,
                o.qty,
                kind,
                role,
                bar.ts,
                price=price,
                ref_price=price,
                exit_reason=reason,
                parent_id=st.order_id,
            )
            self._book[self.place(child)].fill_bar_child = entry_on_bar

    def _finish(self, st: _State, status: OrderStatus, reason: str) -> None:
        st.status = status
        self.events.append(BrokerEvent(self.now, st.order_id, st.order.symbol, status, reason))
        level = logging.WARNING if status is OrderStatus.REJECTED else logging.DEBUG
        logger.log(level, "order %s %s %s: %s", st.order_id, st.order.symbol, status, reason)


def _eligible(o: Order, bar: Bar) -> bool:
    return o.not_before is None or bar.session_date >= o.not_before


def _cnc_sell(o: Order) -> bool:
    return o.product is Product.CNC and o.side is Side.SELL
