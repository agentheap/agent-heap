from typing import Any

from data.defillama import get_yields

TARGET_PROTOCOLS = ["aave", "compound", "morpho"]
TARGET_CHAINS = {"Arbitrum", "Arbitrum Nova", "Base"}


def collect_yields(state: dict[str, Any]) -> dict[str, Any]:
    try:
        pools = get_yields(TARGET_PROTOCOLS)
        filtered = [p for p in pools if p.get("chain") in TARGET_CHAINS]

        # Use memory context: prefer protocols with past success
        memory = state.get("memory_context", [])
        if memory:
            successful_protocols = {
                m.get("protocol")
                for m in memory
                if m.get("action") in ("deposit",)
            }
            # Sort: known-successful protocols first, then by APY
            def _sort_key(p: dict[str, Any]) -> tuple:
                pref = 0 if p.get("protocol") in successful_protocols else 1
                return (pref, -p.get("apy", 0))

            filtered.sort(key=_sort_key)

        return {**state, "yields": filtered, "errors": state.get("errors", [])}
    except Exception as e:
        return {**state, "yields": [], "errors": state.get("errors", []) + [str(e)]}
