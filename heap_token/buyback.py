"""HEAP token buyback engine.

When the agent accrues yield profits, the buyback loop:
  1. Checks accumulated profit against the buyback threshold
  2. Calculates HEAP tokens to buy (allocation_pct of profits)
  3. Simulates or executes the swap
  4. Burns the purchased HEAP tokens
  5. Records the buyback event
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class BuybackAction(Enum):
    HOLD = "hold"
    BUYBACK = "buyback"


@dataclass
class BuybackEvent:
    """Record of a single buyback execution."""

    profit_usd: float
    allocation_pct: float
    amount_usd: float
    tokens_purchased: float
    tokens_burned: float
    tx_hash: str | None


@dataclass
class BuybackEngine:
    """Stateful buyback engine that tracks accrued profit and triggers buybacks."""

    min_profit_usd: float = 10.0
    allocation_pct: float = 0.10
    token_price_usd: float = 0.01
    simulated: bool = True

    accrued_profit: float = 0.0
    history: list[BuybackEvent] = field(default_factory=list)

    def record_profit(self, profit_usd: float) -> BuybackAction:
        """Record a profit event and return whether a buyback should execute."""
        self.accrued_profit += profit_usd
        if self.accrued_profit >= self.min_profit_usd:
            return BuybackAction.BUYBACK
        return BuybackAction.HOLD

    def execute(self) -> dict[str, Any]:
        """Execute a buyback using accrued profits."""
        if self.accrued_profit < self.min_profit_usd:
            return {
                "action": "hold",
                "reason": f"profit ${self.accrued_profit:.2f} below threshold ${self.min_profit_usd:.2f}",
                "accrued_profit": self.accrued_profit,
            }

        amount_usd = self.accrued_profit * self.allocation_pct
        tokens_purchased = amount_usd / self.token_price_usd if self.token_price_usd > 0 else 0

        if self.simulated:
            tx_hash = None
        else:
            tx_hash = self._swap_and_burn(amount_usd, tokens_purchased)

        event = BuybackEvent(
            profit_usd=self.accrued_profit,
            allocation_pct=self.allocation_pct,
            amount_usd=amount_usd,
            tokens_purchased=tokens_purchased,
            tokens_burned=tokens_purchased,
            tx_hash=tx_hash,
        )
        self.history.append(event)
        self.accrued_profit -= amount_usd

        return {
            "action": "buyback",
            "amount_usd": round(amount_usd, 2),
            "tokens_purchased": round(tokens_purchased, 4),
            "tokens_burned": round(tokens_purchased, 4),
            "tx_hash": tx_hash,
            "remaining_profit": round(self.accrued_profit, 2),
        }

    def _swap_and_burn(self, amount_usd: float, tokens: float) -> str:
        """Execute on-chain swap → burn. Requires live wallet."""
        raise NotImplementedError(
            "Live buyback requires a funded wallet. "
            "Set simulated=True or implement _swap_and_burn."
        )

    def reset(self) -> None:
        """Reset accrued profit (e.g., after manual sweep)."""
        self.accrued_profit = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "accrued_profit": round(self.accrued_profit, 2),
            "min_profit_usd": self.min_profit_usd,
            "allocation_pct": self.allocation_pct,
            "total_buybacks": len(self.history),
            "simulated": self.simulated,
        }
