"""Account accounting from fills, in Decimal rupees.

`ledger` is capital plus realized P&L at fill prices minus every charge paid.
Equity = ledger + unrealized. Margin used is MIS |qty| x entry price x the symbol's
margin fraction plus CNC qty x entry price (cash only). Free cash = ledger + any
unrealized loss (gains are not spendable) - margin used. With the `fixed_capital`
sizing basis (research), `buying_power` - the cash the broker lets a CNC buy use - is
on an account rebased to `capital` at each session open; equity, ledger and every
trade record stay the real, cumulative account.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from types import MappingProxyType
from typing import Any

import pandas as pd

from nsealgo.brokers.fills import dec
from nsealgo.engine.config import MarginConfig, SizingBasis
from nsealgo.engine.types import ExitReason, Fill, OrderRole, OrderStatus, OrderView, Product

PAISA = Decimal("0.01")
ZERO = Decimal(0)


@dataclass
class Position:
    symbol: str
    product: Product
    qty: int  # signed: + long, - short
    avg_price: Decimal  # entry fill price, slippage included
    entry_ref: Decimal  # entry reference price, before slippage
    entry_time: pd.Timestamp
    entry_qty: int
    entry_charges: Decimal
    entry_charges_left: Decimal
    initial_stop: Decimal | None
    group_id: str | None
    trade_id: int


@dataclass(frozen=True, slots=True)
class PositionView:
    symbol: str
    product: Product
    qty: int
    avg_price: Decimal
    mark: Decimal
    entry_time: pd.Timestamp
    initial_stop: Decimal | None


@dataclass(frozen=True, slots=True)
class TradeRecord:
    trade_id: int
    symbol: str
    product: Product
    side: str  # long / short
    qty: int
    entry_time: pd.Timestamp
    exit_time: pd.Timestamp
    entry_price: Decimal
    exit_price: Decimal
    entry_ref: Decimal
    exit_ref: Decimal
    notional: Decimal
    gross_pnl: Decimal  # at reference prices
    slippage: Decimal
    costs: Decimal
    net_pnl: Decimal
    r_multiple: float | None
    exit_reason: ExitReason | None
    group_id: str | None


@dataclass(frozen=True, slots=True)
class AccountSnapshot:
    """What the RiskGovernor sees. `marks` are the last visible closes of all symbols."""

    now: pd.Timestamp
    session_date: date
    equity: Decimal
    equity_at_session_start: Decimal
    peak_equity: Decimal
    ledger: Decimal
    unrealized: Decimal
    margin_used: Decimal
    positions: Mapping[str, PositionView]
    orders: tuple[OrderView, ...]
    fills_today: tuple[Fill, ...]
    marks: Mapping[str, float]

    @property
    def free_cash(self) -> Decimal:
        return self.ledger + min(ZERO, self.unrealized) - self.margin_used

    def working(self, role: OrderRole | None = None, symbol: str | None = None) -> list[OrderView]:
        return [
            v
            for v in self.orders
            if v.status is OrderStatus.WORKING
            and (role is None or v.order.role is role)
            and (symbol is None or v.order.symbol == symbol)
        ]


class Portfolio:
    def __init__(
        self, capital: Decimal, margins: MarginConfig, sizing: SizingBasis = "current_equity"
    ) -> None:
        self.capital = capital
        self.sizing = sizing
        self.ledger = capital
        self.margins = margins
        self.positions: dict[str, Position] = {}
        self.marks: dict[str, Decimal] = {}
        self.trades: list[TradeRecord] = []
        self.fills_today: list[Fill] = []
        self.peak_equity = capital
        self.session_date: date | None = None
        self.equity_at_session_start = capital
        self._next_trade_id = 1

    def start_session(self, day: date) -> None:
        self.session_date = day
        self.fills_today = []
        self.equity_at_session_start = self.equity()

    def mark(self, symbol: str, price: float) -> None:
        if symbol in self.positions:
            self.marks[symbol] = dec(price)

    def apply_fill(self, fill: Fill) -> TradeRecord | None:
        """Book one fill. Returns the trade record when it reduces a position."""
        self.ledger -= fill.charges.total
        self.fills_today.append(fill)
        pos = self.positions.get(fill.symbol)
        if pos is None:
            self._open(fill)
            return None
        if (pos.qty > 0) == (fill.side.sign > 0):
            raise ValueError(f"{fill.symbol}: adding to an open position is not supported")
        if fill.qty > abs(pos.qty):
            raise ValueError(f"{fill.symbol}: fill of {fill.qty} exceeds position {pos.qty}")
        return self._reduce(pos, fill)

    def _open(self, fill: Fill) -> None:
        if fill.role is not OrderRole.ENTRY:
            raise ValueError(f"{fill.symbol}: {fill.role} fill without a position")
        self.positions[fill.symbol] = Position(
            symbol=fill.symbol,
            product=fill.product,
            qty=fill.side.sign * fill.qty,
            avg_price=fill.price,
            entry_ref=fill.ref_price,
            entry_time=fill.ts,
            entry_qty=fill.qty,
            entry_charges=fill.charges.total,
            entry_charges_left=fill.charges.total,
            initial_stop=fill.stop_loss,
            group_id=fill.group_id,
            trade_id=self._next_trade_id,
        )
        self._next_trade_id += 1
        self.marks[fill.symbol] = fill.price

    def _reduce(self, pos: Position, fill: Fill) -> TradeRecord:
        q, sign = fill.qty, (1 if pos.qty > 0 else -1)
        last = q == abs(pos.qty)
        share = pos.entry_charges * q / pos.entry_qty
        entry_cost = pos.entry_charges_left if last else share.quantize(PAISA, ROUND_HALF_UP)
        pos.entry_charges_left -= entry_cost
        self.ledger += (fill.price - pos.avg_price) * q * sign
        gross = (fill.ref_price - pos.entry_ref) * q * sign
        slippage = abs(pos.avg_price - pos.entry_ref) * q + fill.slippage
        costs = entry_cost + fill.charges.total
        net = gross - slippage - costs
        risk = abs(pos.avg_price - pos.initial_stop) * q if pos.initial_stop is not None else ZERO
        trade = TradeRecord(
            trade_id=pos.trade_id,
            symbol=pos.symbol,
            product=pos.product,
            side="long" if sign > 0 else "short",
            qty=q,
            entry_time=pos.entry_time,
            exit_time=fill.ts,
            entry_price=pos.avg_price,
            exit_price=fill.price,
            entry_ref=pos.entry_ref,
            exit_ref=fill.ref_price,
            notional=pos.avg_price * q,
            gross_pnl=gross,
            slippage=slippage,
            costs=costs,
            net_pnl=net,
            r_multiple=float(net / risk) if risk > 0 else None,
            exit_reason=fill.exit_reason,
            group_id=pos.group_id,
        )
        pos.qty -= sign * q
        if pos.qty == 0:
            del self.positions[pos.symbol]
            self.marks.pop(pos.symbol, None)
        self.trades.append(trade)
        return trade

    def unrealized(self) -> Decimal:
        return sum(((self.marks[s] - p.avg_price) * p.qty for s, p in self.positions.items()), ZERO)

    def _margin_fraction(self, p: Position) -> Decimal:
        return Decimal(1) if p.product is Product.CNC else self.margins.mis_fraction(p.symbol)

    def margin_used(self) -> Decimal:
        return sum(
            (abs(p.qty) * p.avg_price * self._margin_fraction(p) for p in self.positions.values()),
            ZERO,
        )

    def equity(self) -> Decimal:
        return self.ledger + self.unrealized()

    def free_cash(self) -> Decimal:
        return self.ledger + min(ZERO, self.unrealized()) - self.margin_used()

    def buying_power(self) -> Decimal:
        """Free cash for the broker's CNC cash check, on the sizing basis."""
        if self.sizing == "current_equity":
            return self.free_cash()
        return self.free_cash() + self.capital - self.equity_at_session_start

    def position_views(self) -> Mapping[str, PositionView]:
        return MappingProxyType(
            {
                s: PositionView(
                    s, p.product, p.qty, p.avg_price, self.marks[s], p.entry_time, p.initial_stop
                )
                for s, p in self.positions.items()
            }
        )

    def snapshot(
        self, now: pd.Timestamp, orders: tuple[OrderView, ...], marks: Mapping[str, float]
    ) -> AccountSnapshot:
        if self.session_date is None:
            raise RuntimeError("snapshot before start_session")
        return AccountSnapshot(
            now=now,
            session_date=self.session_date,
            equity=self.equity(),
            equity_at_session_start=self.equity_at_session_start,
            peak_equity=self.peak_equity,
            ledger=self.ledger,
            unrealized=self.unrealized(),
            margin_used=self.margin_used(),
            positions=self.position_views(),
            orders=orders,
            fills_today=tuple(self.fills_today),
            marks=marks,
        )

    def end_session(self) -> dict[str, Any]:
        """Session-end equity row; updates the running peak (capital and session-end equity)."""
        equity = self.equity()
        self.peak_equity = max(self.peak_equity, equity)
        return {
            "session_date": self.session_date,
            "equity": equity,
            "ledger": self.ledger,
            "unrealized": self.unrealized(),
            "daily_pnl": equity - self.equity_at_session_start,
            "open_positions": len(self.positions),
            "fills": len(self.fills_today),
        }
