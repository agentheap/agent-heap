from typing import Any


def select_best_pool(yields: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not yields:
        return None
    return max(yields, key=lambda p: p.get("apy", 0))
