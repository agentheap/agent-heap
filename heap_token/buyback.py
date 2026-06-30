from typing import Any


def calculate_buyback(profits: float, allocation_pct: float = 0.1) -> dict[str, Any]:
    amount = profits * allocation_pct
    return {"amount": amount, "token": "HEAP", "status": "not_implemented"}
