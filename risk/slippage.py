from typing import Any


def estimate_slippage(
    pool_liquidity: float,
    trade_amount: float,
    max_slippage_bps: int = 100,
) -> tuple[float, bool]:
    if pool_liquidity <= 0:
        return 0, False
    slippage_bps = (trade_amount / pool_liquidity) * 10_000
    acceptable = slippage_bps <= max_slippage_bps
    return slippage_bps, acceptable


def check_trade_allowed(
    trade: dict[str, Any],
    pool_data: dict[str, Any],
    max_slippage_bps: int = 100,
) -> tuple[bool, str]:
    slippage_bps, acceptable = estimate_slippage(
        pool_data.get("tvl", 0),
        trade.get("amount", 0),
        max_slippage_bps,
    )
    if not acceptable:
        return False, f"slippage {slippage_bps:.0f} bps exceeds max {max_slippage_bps}"
    return True, "ok"
