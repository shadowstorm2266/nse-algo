"""Broker interface shared by the simulator and (later) the paper/live adapters."""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol

from nsealgo.engine.types import Order, OrderView, Product


@dataclass(frozen=True, slots=True)
class BrokerPosition:
    symbol: str
    product: Product
    qty: int  # signed: + long, - short


class Broker(Protocol):
    def place(self, order: Order) -> int:
        """Submit an approved order; returns the broker's order id."""
        ...

    def cancel(self, order_id: int) -> bool:
        """Cancel a working order; False if it is no longer working."""
        ...

    def positions(self) -> Mapping[str, BrokerPosition]: ...

    def orders(self) -> tuple[OrderView, ...]:
        """Today's order book plus orders still working from earlier sessions."""
        ...
