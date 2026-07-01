"""Buyback node -- runs after each agent execution cycle.

Records simulated yield profit and triggers HEAP buyback when the threshold is met.
"""

from typing import Any

from heap_token.buyback import BuybackEngine

_engine: BuybackEngine | None = None


def get_engine() -> BuybackEngine:
    global _engine
    if _engine is None:
        _engine = BuybackEngine(min_profit_usd=10.0, allocation_pct=0.10)
    return _engine


def run_buyback(state: dict[str, Any]) -> dict[str, Any]:
    """Process buyback after a yield execution cycle.

    On each cycle, records a simulated profit of $2 (testnet).
    When accrued profit >= $10, triggers HEAP buyback.
    """
    engine = get_engine()
    tx_result = state.get("tx_result")

    if tx_result is None:
        return {**state, "buyback_result": {"action": "skip", "reason": "no tx executed"}}

    profit = _estimate_profit(tx_result)
    action = engine.record_profit(profit)

    if action.value == "buyback":
        result = engine.execute()
    else:
        result = {
            "action": "hold",
            "reason": "profit below threshold",
            "accrued_profit": round(engine.accrued_profit, 2),
        }

    return {
        **state,
        "buyback_result": {
            **result,
            "profit_this_cycle": profit,
            "engine_state": engine.to_dict(),
        },
    }


def _estimate_profit(tx_result: dict[str, Any]) -> float:
    """Estimate profit from a transaction result.

    For simulation mode, returns a small fixed amount.
    For real mode, would calculate yield - gas.
    """
    if not tx_result.get("simulated", True):
        return 2.0  # placeholder for real yield calculation
    return 2.0
