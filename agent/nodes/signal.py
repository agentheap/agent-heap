import os
from typing import Any

from risk.position_sizing import fixed_fraction


def _get_capital() -> float:
    """Read capital from env or DB, falling back to 50.0."""
    env_val = os.getenv("CAPITAL")
    if env_val is not None:
        return float(env_val)
    try:
        from db.session import get_agent_state

        state = get_agent_state()
        if state and state.config and "capital" in state.config:
            return float(state.config["capital"])
    except Exception:
        pass
    return 50.0


def generate_signal(state: dict[str, Any]) -> dict[str, Any]:
    analysis = state.get("analysis")
    if not analysis:
        return {**state, "signal": None}

    capital = _get_capital()
    amount = fixed_fraction(capital)

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
