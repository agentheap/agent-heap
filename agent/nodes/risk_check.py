"""Risk check node -- gates deposits through circuit breaker, slippage, and position sizing."""

from typing import Any

from risk.circuit_breaker import CircuitBreaker
from risk.position_sizing import fixed_fraction
from risk.slippage import estimate_slippage

# Singleton breaker -- persists across graph invocations
_breaker = CircuitBreaker(max_daily_drawdown=0.05)


def check_risks(state: dict[str, Any]) -> dict[str, Any]:
    """Evaluate risk checks before allowing a deposit.

    Returns updated state with:
      - risk_ok: bool -- false if any check fails
      - risk_reason: str -- why it failed
      - sized_amount: float -- Kelly/fraction-adjusted deposit size
    """
    analysis = state.get("analysis")
    capital = state.get("capital", 1.0)  # ETH available to deploy

    if not analysis:
        return {**state, "risk_ok": False, "risk_reason": "no analysis"}

    # 1. Circuit breaker -- has daily PnL gone too negative?
    if _breaker.is_tripped():
        return {
            **state,
            "risk_ok": False,
            "risk_reason": "circuit breaker tripped -- max daily drawdown exceeded",
        }

    # 2. Slippage check -- is the trade small enough vs pool TVL?
    tvl = analysis.get("tvl", 0)
    default_amount = capital * 0.02  # 2% of capital
    slippage_bps, acceptable = estimate_slippage(tvl, default_amount)

    if not acceptable:
        return {
            **state,
            "risk_ok": False,
            "risk_reason": f"slippage {slippage_bps:.0f} bps exceeds limit (TVL=${tvl:,.0f}, amt={default_amount})",
        }

    # 3. Position sizing -- Kelly / fixed fraction
    sized_amount = fixed_fraction(capital, fraction=0.02)

    return {
        **state,
        "risk_ok": True,
        "risk_reason": "ok",
        "sized_amount": sized_amount,
        "slippage_bps": slippage_bps,
    }


def record_pnl(state: dict[str, Any]) -> dict[str, Any]:
    """Record trade result into circuit breaker after execution."""
    tx = state.get("tx_result")
    if tx:
        pnl = tx.get("pnl", 0)
        _breaker.record_trade(pnl)
    return state
