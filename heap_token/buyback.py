"""$HEAP buyback logic — agent profits auto-buy HEAP tokens."""

from typing import Any


def calculate_buyback(profits: float, allocation_pct: float = 0.1) -> dict[str, Any]:
    """Calculate how much HEAP to buy back from agent profits."""
    if profits <= 0:
        return {"amount": 0, "token": "HEAP", "status": "no_profits"}

    amount = profits * allocation_pct

    return {
        "amount": amount,
        "token": "HEAP",
        "status": "ready",
        "allocation_pct": allocation_pct,
        "note": f"Allocating {allocation_pct*100:.0f}% of ${profits:.2f} profit to HEAP buyback",
    }


def execute_buyback(
    buyback_amount_eth: float,
    token_address: str,
    private_key: str | None = None,
) -> dict[str, Any]:
    """Execute a HEAP buyback via DEX swap on Base.

    Stub — needs Uniswap v3/v4 integration.
    """
    if not private_key:
        return {
            "status": "simulated",
            "amount_eth": buyback_amount_eth,
            "token_address": token_address,
            "note": "Simulated buyback — pass PRIVATE_KEY for real execution",
        }

    return {
        "status": "not_implemented",
        "amount_eth": buyback_amount_eth,
        "token_address": token_address,
        "message": "Real DEX swap not yet wired — needs Uniswap router + ABI",
    }
