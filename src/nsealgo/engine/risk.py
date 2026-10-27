"""RiskGovernor: the only code that turns strategy intents into orders.

Limits come from config/risk.yaml (MIS: intraday rules; CNC: the swing block; sizing
basis per run mode). Exits reducing a real position are always allowed, even under KILL
or a latched halt. Every rejection has a reason code, logged on `nsealgo.risk`. Runs in
backtest, paper and live alike: reads only the snapshot, calendar, config and KILL file.
"""

import logging
from collections import defaultdict
from collections.abc import Sequence
from datetime import date
from decimal import Decimal
from pathlib import Path

import pandas as pd

from nsealgo.brokers.fills import dec
from nsealgo.costs import CostConfig, fill_charges
from nsealgo.engine.config import MarginConfig, RiskConfig
from nsealgo.engine.exposure import (
    committed,
    reference_price,
    sizing_shift,
    strategy_orders_today,
    swing_slots_and_gross,
    trades_today,
)
from nsealgo.engine.portfolio import AccountSnapshot, PositionView
from nsealgo.engine.sessions import TradingCalendar, at, session_close
from nsealgo.engine.sizing import SwingSize, mis_qty, swing_qty
from nsealgo.engine.types import (
    ExitReason,
    HaltRecord,
    IntentKind,
    Order,
    OrderIntent,
    OrderRole,
    OrderType,
    Product,
    Rejection,
    RejectReason,
    Side,
)
from nsealgo.settings import Mode

logger = logging.getLogger("nsealgo.risk")
ZERO = Decimal(0)
R = RejectReason
Problem = tuple[RejectReason, str] | None


class RiskGovernor:
    def __init__(
        self,
        config: RiskConfig,
        margins: MarginConfig,
        calendar: TradingCalendar,
        costs: CostConfig,
        brokerage_preset: str,
        *,
        product: Product,
        mode: Mode = "backtest",
        kill_file: Path | None = None,
    ) -> None:
        self.config = config
        self.margins = margins
        self.calendar = calendar
        self._rates = costs.rates
        self._delivery = costs.brokerage_presets[brokerage_preset].delivery
        self.product = product
        self.halt_mode = config.halt_mode.for_mode(mode)
        self.sizing_basis = config.sizing_basis.for_mode(mode, product)
        self.kill_file = kill_file
        self.halt: HaltRecord | None = None
        self.latched = False

    # --- public API ---

    def observe(self, snap: AccountSnapshot) -> None:
        """Update the drawdown-halt state from current equity vs the running peak."""
        self.observe_equity(snap.equity, snap.peak_equity, snap.session_date, snap.now)

    def observe_equity(self, equity: Decimal, peak: Decimal, day: date, now: pd.Timestamp) -> None:
        dd = (peak - equity) / peak * 100 if peak > 0 else ZERO
        if dd < self.config.account_drawdown_halt_pct:
            return
        if self.halt is None:
            self.halt = HaltRecord(day, now, float(dd), equity, peak)
            logger.warning("drawdown %.2f%% reached at %s (%s mode)", dd, now, self.halt_mode)
        if self.halt_mode == "latch":
            self.latched = True

    def review(
        self, intent: OrderIntent, snap: AccountSnapshot, now: pd.Timestamp
    ) -> Order | Rejection:
        if intent.product is not self.product:
            return self._reject(intent, now, R.WRONG_PRODUCT, f"this run trades {self.product}")
        if intent.kind is IntentKind.EXIT:
            return self._review_exit(intent, snap, now)
        self.observe(snap)
        if self.kill_file is not None and self.kill_file.exists():
            return self._reject(intent, now, R.KILL_SWITCH, str(self.kill_file))
        if self.latched:
            return self._reject(intent, now, R.DRAWDOWN_HALT, f"since {self.halt.date}")
        if self.product is Product.MIS:
            return self._review_mis_entry(intent, snap, now)
        return self._review_swing_entry(intent, snap, now)

    def screen_groups(
        self, intents: Sequence[OrderIntent], snap: AccountSnapshot, now: pd.Timestamp
    ) -> tuple[list[OrderIntent], list[Rejection]]:
        """Drop every leg of a malformed OCO entry group (INVALID_GROUP)."""
        groups: dict[str, list[OrderIntent]] = defaultdict(list)
        for i in intents:
            if i.group_id is not None:
                groups[i.group_id].append(i)
        bad = {g: why for g, legs in groups.items() if (why := self._group_problem(g, legs, snap))}
        ok = [i for i in intents if i.group_id not in bad]
        rejected = [
            self._reject(i, now, R.INVALID_GROUP, bad[i.group_id])
            for i in intents
            if i.group_id in bad
        ]
        return ok, rejected

    def reject_group_leg(self, intent: OrderIntent, now: pd.Timestamp) -> Rejection:
        """A group is all-or-nothing: once one leg is rejected the others are too (the
        caller cancels any leg already placed)."""
        return self._reject(intent, now, R.GROUP_LEG_REJECTED, "another leg was rejected")

    def forced_exits(
        self, snap: AccountSnapshot, now: pd.Timestamp
    ) -> tuple[list[Order], list[int]]:
        """At or after flat_by: market exits for every MIS position (replacing any other
        working exit) and the ids of working orders to cancel."""
        if self.product is not Product.MIS or now.time() < self.config.flat_by:
            return [], []
        cancels = [v.order_id for v in snap.working(OrderRole.ENTRY)]
        orders = []
        for symbol, p in snap.positions.items():
            exits = snap.working(OrderRole.EXIT, symbol)
            if any(v.order.exit_reason is ExitReason.FLAT_BY for v in exits):
                continue
            cancels += [v.order_id for v in exits]
            orders.append(_market_exit(p, abs(p.qty), now, ExitReason.FLAT_BY))
        return orders, cancels

    # --- exits ---

    def _review_exit(
        self, intent: OrderIntent, snap: AccountSnapshot, now: pd.Timestamp
    ) -> Order | Rejection:
        pos = snap.positions.get(intent.symbol)
        if pos is None:
            return self._reject(intent, now, R.NO_POSITION, "nothing to exit")
        side = Side.SELL if pos.qty > 0 else Side.BUY
        qty = intent.qty if intent.qty is not None else abs(pos.qty)
        shaped = intent.order_type is OrderType.MARKET and intent.side in (None, side)
        extras = (intent.price, intent.stop_loss, intent.target, intent.group_id)
        if not shaped or any(x is not None for x in extras) or not 0 < qty <= abs(pos.qty):
            return self._reject(
                intent, now, R.INVALID_INTENT, f"exit must be market, qty 1..{abs(pos.qty)}"
            )
        if snap.working(OrderRole.EXIT, intent.symbol):
            return self._reject(intent, now, R.DUPLICATE_EXIT, "an exit is already working")
        not_before = expires = None
        if self.product is Product.CNC:
            not_before = self.calendar.next_tradeable_after(snap.session_date)
            if not_before is None:
                return self._reject(intent, now, R.NO_NEXT_SESSION, "no session to fill in")
            expires = session_close(not_before)
        return _market_exit(pos, qty, now, ExitReason.STRATEGY, not_before, expires, intent.tag)

    # --- MIS entries ---

    def _review_mis_entry(
        self, intent: OrderIntent, snap: AccountSnapshot, now: pd.Timestamp
    ) -> Order | Rejection:
        problem = self._entry_shape(intent) or self._mis_gate(intent, snap, now)
        if problem:
            return self._reject(intent, now, *problem)
        if intent.stop_loss is None or not intent.stop_loss > 0:
            return self._reject(intent, now, R.INVALID_STOP, "MIS entries need a stop_loss")
        ref = reference_price(intent, snap)
        if ref is None:
            return self._reject(intent, now, R.NO_PRICE, "no visible price")
        stop, long = dec(intent.stop_loss), intent.side is Side.BUY
        if (long and stop >= ref) or (not long and stop <= ref):
            return self._reject(intent, now, R.INVALID_STOP, f"stop {stop} vs ref {ref}", ref)
        target = dec(intent.target) if intent.target is not None else None
        if target is not None and ((long and target <= ref) or (not long and target >= ref)):
            return self._reject(intent, now, R.INVALID_INTENT, f"target {target} vs ref {ref}", ref)
        exposure, margin = committed(snap, self.margins, exclude_group=intent.group_id)
        shift = sizing_shift(snap, self.config.capital, self.sizing_basis, self.product)
        q = mis_qty(
            risk_rupees=self.config.risk_per_trade_rupees,
            ref=ref,
            stop=stop,
            remaining_exposure=self.config.max_gross_exposure_rupees - exposure,
            free_margin=snap.free_cash + shift - margin,
            margin_fraction=self.margins.mis_fraction(intent.symbol),
        )
        if q.qty < 1:
            return self._reject(intent, now, R.QTY_BELOW_ONE, str(q), ref)
        price = dec(intent.price) if intent.order_type is not OrderType.MARKET else None
        return Order(
            intent.symbol,
            Product.MIS,
            intent.side,
            q.qty,
            intent.order_type,
            OrderRole.ENTRY,
            now,
            price=price,
            ref_price=ref,
            stop_loss=stop,
            target=target,
            group_id=intent.group_id,
            rank=intent.rank,
            expires_at=at(snap.session_date, self.config.entry_end),
            tag=intent.tag,
        )

    def _mis_gate(self, intent: OrderIntent, snap: AccountSnapshot, now: pd.Timestamp) -> Problem:
        cfg = self.config
        if self.calendar.is_no_trade(snap.session_date):
            return R.NO_TRADE_SESSION, f"{snap.session_date} is no_trade"
        if now.time() < cfg.entry_start:
            return R.BEFORE_ENTRY_START, f"{now.time()} < {cfg.entry_start}"
        if now.time() > cfg.entry_end:
            return R.AFTER_ENTRY_END, f"{now.time()} > {cfg.entry_end}"
        day_pnl = snap.equity - snap.equity_at_session_start
        if day_pnl <= -cfg.max_daily_loss_rupees:
            return R.DAILY_LOSS_LIMIT, f"day P&L {day_pnl:.2f}"
        siblings = snap.working(OrderRole.ENTRY, intent.symbol)
        joining = (
            intent.group_id is not None
            and 0 < len(siblings) < 2
            and all(v.order.group_id == intent.group_id for v in siblings)
        )
        if not joining:
            filled, units = trades_today(snap)
            if filled + units >= cfg.max_trades_per_day:
                return R.MAX_TRADES_PER_DAY, f"{filled} filled + {units} working"
        if intent.symbol in snap.positions or (siblings and not joining):
            return R.POSITION_EXISTS, "one position or working entry per symbol"
        return None

    # --- swing (CNC) entries ---

    def _review_swing_entry(
        self, intent: OrderIntent, snap: AccountSnapshot, now: pd.Timestamp
    ) -> Order | Rejection:
        problem = self._swing_shape(intent) or self._swing_gate(intent, snap)
        if problem:
            return self._reject(intent, now, *problem)
        fill_day = self.calendar.next_tradeable_after(snap.session_date)
        if fill_day is None:
            return self._reject(intent, now, R.NO_NEXT_SESSION, "no session to fill in")
        price = reference_price(intent, snap)
        if price is None:
            return self._reject(intent, now, R.NO_PRICE, "no visible price")
        size = self._swing_size(snap, price)
        if size.reason is not None:
            return self._reject(intent, now, size.reason, size.detail, price)
        return Order(
            intent.symbol,
            Product.CNC,
            Side.BUY,
            size.qty,
            OrderType.MARKET,
            OrderRole.ENTRY,
            now,
            ref_price=price,
            rank=intent.rank,
            not_before=fill_day,
            expires_at=session_close(fill_day),
            tag=intent.tag,
        )

    def _swing_shape(self, intent: OrderIntent) -> Problem:
        if not self.config.swing.enabled:
            return R.SWING_DISABLED, "swing.enabled is false"
        if intent.side is Side.SELL:
            return R.SHORT_NOT_ALLOWED, "CNC cannot short"
        extras = (intent.price, intent.stop_loss, intent.target, intent.group_id, intent.qty)
        if (
            intent.side is None
            or intent.order_type is not OrderType.MARKET
            or any(x is not None for x in extras)
        ):
            return R.INVALID_INTENT, "swing entries are plain market orders for the next open"
        return None

    def _swing_gate(self, intent: OrderIntent, snap: AccountSnapshot) -> Problem:
        sw = self.config.swing
        today = strategy_orders_today(snap)
        if today >= sw.max_orders_per_day:
            return R.MAX_ORDERS_PER_DAY, f"{today} orders today"
        if intent.symbol in snap.positions or snap.working(OrderRole.ENTRY, intent.symbol):
            return R.POSITION_EXISTS, "one position or working entry per symbol"
        held, pending, _ = swing_slots_and_gross(snap)
        if held + pending >= sw.max_positions:
            return R.MAX_POSITIONS, f"{held} held + {pending} pending"
        return None

    def _swing_size(self, snap: AccountSnapshot, price: Decimal) -> SwingSize:
        shift = sizing_shift(snap, self.config.capital, self.sizing_basis, self.product)
        sw, equity = self.config.swing, snap.equity + shift
        per_slot, est = equity / sw.max_positions, ZERO
        if per_slot > 0:
            leg = fill_charges("CNC", "BUY", per_slot, self._rates, self._delivery)
            est = sw.max_positions * leg.total
        _, _, gross = swing_slots_and_gross(snap)
        return swing_qty(
            price=price,
            equity=equity,
            est_buy_charges=est,
            max_positions=sw.max_positions,
            cash_buffer_pct=sw.cash_buffer_pct,
            position_cap=equity * sw.max_position_pct / 100,
            remaining_gross=equity * sw.max_gross_exposure_pct / 100 - gross,
        )

    # --- helpers ---

    @staticmethod
    def _entry_shape(intent: OrderIntent) -> Problem:
        if intent.side is None or intent.qty is not None:
            return R.INVALID_INTENT, "entries need a side and no qty (the RiskGovernor sizes)"
        priced = intent.price is not None
        if (intent.order_type is OrderType.MARKET) == priced:
            return R.INVALID_INTENT, "STOP/LIMIT entries need a price; MARKET entries take none"
        if priced and not intent.price > 0:
            return R.INVALID_INTENT, f"bad price {intent.price}"
        return None

    def _group_problem(
        self, gid: str, legs: list[OrderIntent], snap: AccountSnapshot
    ) -> str | None:
        if self.product is not Product.MIS:
            return "OCO entry groups are MIS only"
        if len(legs) > 2:
            return f"{len(legs)} legs; at most 2"
        if any(i.kind is not IntentKind.ENTRY or i.order_type is OrderType.MARKET for i in legs):
            return "legs must be STOP or LIMIT entries"
        if len({(i.symbol, i.product) for i in legs}) != 1:
            return "legs must share symbol and product"
        if any(v.order.group_id == gid for v in snap.working(OrderRole.ENTRY)):
            return "group already working from an earlier bar"
        return None

    def _reject(
        self,
        intent: OrderIntent,
        now: pd.Timestamp,
        reason: RejectReason,
        detail: str,
        price: Decimal | None = None,
    ) -> Rejection:
        r = Rejection(
            now=now,
            symbol=intent.symbol,
            reason=reason,
            detail=detail,
            kind=intent.kind.value,
            price=float(price) if price is not None else intent.price,
            rank=intent.rank,
            group_id=intent.group_id,
        )
        logger.info("rejected %s %s %s: %s", r.kind, r.symbol, r.reason, r.detail)
        return r


def _market_exit(
    pos: PositionView,
    qty: int,
    now: pd.Timestamp,
    reason: ExitReason,
    not_before: date | None = None,
    expires: pd.Timestamp | None = None,
    tag: str = "",
) -> Order:
    side = Side.SELL if pos.qty > 0 else Side.BUY
    return Order(
        pos.symbol,
        pos.product,
        side,
        qty,
        OrderType.MARKET,
        OrderRole.EXIT,
        now,
        ref_price=pos.mark,
        exit_reason=reason,
        not_before=not_before,
        expires_at=expires,
        tag=tag,
    )
