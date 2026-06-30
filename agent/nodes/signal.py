from typing import Any


def generate_signal(state: dict[str, Any]) -> dict[str, Any]:
    analysis = state.get("analysis")
    if not analysis:
        return {**state, "signal": None}

    signal = {
        "action": "deposit",
        "protocol": analysis.get("protocol"),
        "pool": analysis.get("pool"),
        "amount": 0.01,
        "apy": analysis.get("apy"),
        "tvl": analysis.get("tvl"),
        "reason": analysis.get("reason", "highest apy"),
    }
    return {**state, "signal": signal}
