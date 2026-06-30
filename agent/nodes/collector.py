from typing import Any

from data.defillama import get_yields

TARGET_PROTOCOLS = ["aave", "compound", "morpho"]
TARGET_CHAINS = {"Arbitrum", "Arbitrum Nova"}


def collect_yields(state: dict[str, Any]) -> dict[str, Any]:
    try:
        pools = get_yields(TARGET_PROTOCOLS)
        filtered = [p for p in pools if p.get("chain") in TARGET_CHAINS]
        return {**state, "yields": filtered, "errors": state.get("errors", [])}
    except Exception as e:
        return {**state, "yields": [], "errors": state.get("errors", []) + [str(e)]}
