"""Buyback node — converts yield profits into HEAP token purchases."""

from typing import Any

from heap_token.buyback import calculate_buyback


def run_buyback(state: dict[str, Any]) -> dict[str, Any]:
    """After executor records a profit, calculate and flag buyback.

    Currently simulated — real DEX swap needs Uniswap router integration.
    """
    tx = state.get("tx_result")
    if not tx:
        return {**state, "buyback": None}

    pnl = tx.get("pnl", 0)
    if pnl <= 0:
        return {**state, "buyback": {"status": "no_profits", "pnl": pnl}}

    # 10% of profit → HEAP buyback
    buyback = calculate_buyback(pnl, allocation_pct=0.1)

    tx["buyback"] = buyback

    return {
        **state,
        "tx_result": tx,
        "buyback": buyback,
    }
