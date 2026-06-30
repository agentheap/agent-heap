import os
from typing import Any

from risk.position_sizing import kelly_fraction


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


def _compute_kelly_amount(
    apy: float,
    yields: list[dict[str, Any]],
    capital: float,
) -> float:
    """Derive win probability and ratio from APY data, then compute Kelly fraction."""
    if not yields or capital <= 0:
        return capital * 0.02

    avg_apy = sum(p["apy"] for p in yields) / len(yields)
    if avg_apy <= 0:
        return capital * 0.02

    win_prob = min(0.99, max(0.01, apy / (apy + avg_apy)))
    win_ratio = apy / avg_apy
    f = kelly_fraction(win_prob, win_ratio)
    return capital * f


def generate_signal(state: dict[str, Any]) -> dict[str, Any]:
    analysis = state.get("analysis")
    if not analysis:
        return {**state, "signal": None}

    capital = _get_capital()
    amount = _compute_kelly_amount(
        apy=analysis.get("apy", 0),
        yields=state.get("yields", []),
        capital=capital,
    )

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
