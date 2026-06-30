"""Signal generation node — creates deposit/withdraw signals with risk-adjusted amounts."""

from typing import Any


def generate_signal(state: dict[str, Any]) -> dict[str, Any]:
    """Generate a trading signal from analysis + risk checks."""
    analysis = state.get("analysis")
    if not analysis:
        return {**state, "signal": None}

    # Respect risk check — if blocked, no signal
    if not state.get("risk_ok", True):
        return {
            **state,
            "signal": {
                "action": "skip",
                "reason": state.get("risk_reason", "risk check failed"),
                "amount": 0,
            },
        }

    # Use risk-sized amount, fallback to default
    amount = state.get("sized_amount", 0.01)

    signal = {
        "action": "deposit",
        "protocol": analysis.get("protocol"),
        "pool": analysis.get("pool"),
        "amount": amount,
        "apy": analysis.get("apy"),
        "tvl": analysis.get("tvl"),
        "reason": analysis.get("reason", "highest apy"),
    }
    return {**state, "signal": signal}
