"""Tests for HEAP token buyback engine and deployment."""

from heap_token.buyback import BuybackAction, BuybackEngine, BuybackEvent
from heap_token.deploy import deploy_heap


def test_buyback_hold_below_threshold() -> None:
    """Engine holds when profit is below the minimum."""
    engine = BuybackEngine(min_profit_usd=10.0)
    action = engine.record_profit(5.0)
    assert action == BuybackAction.HOLD
    assert engine.accrued_profit == 5.0


def test_buyback_triggers_at_threshold() -> None:
    """Engine signals BUYBACK when profit meets or exceeds the threshold."""
    engine = BuybackEngine(min_profit_usd=10.0)
    engine.record_profit(10.0)
    result = engine.execute()
    assert result["action"] == "buyback"
    assert result["amount_usd"] > 0
    assert result["tokens_burned"] > 0


def test_buyback_execute_deducts_profit() -> None:
    """After a buyback, the allocation is deducted from accrued profit."""
    engine = BuybackEngine(min_profit_usd=10.0, allocation_pct=0.1)
    engine.record_profit(100.0)
    result = engine.execute()
    assert result["action"] == "buyback"
    assert result["amount_usd"] == 10.0  # 10% of 100
    assert engine.accrued_profit == 90.0  # remaining


def test_buyback_multiple_accumulate() -> None:
    """Multiple small profits accumulate and trigger one buyback."""
    engine = BuybackEngine(min_profit_usd=10.0)
    for _ in range(5):
        engine.record_profit(3.0)
    assert engine.accrued_profit == 15.0
    result = engine.execute()
    assert result["action"] == "buyback"


def test_buyback_execute_hold_when_below() -> None:
    """Execute returns hold when profit hasn't reached threshold."""
    engine = BuybackEngine(min_profit_usd=10.0)
    engine.record_profit(3.0)
    result = engine.execute()
    assert result["action"] == "hold"


def test_buyback_history_recorded() -> None:
    """Each buyback is appended to the engine history."""
    engine = BuybackEngine(min_profit_usd=5.0)
    engine.record_profit(20.0)
    engine.execute()
    engine.record_profit(30.0)
    engine.execute()
    assert len(engine.history) == 2
    assert all(isinstance(e, BuybackEvent) for e in engine.history)


def test_buyback_to_dict() -> None:
    """Engine serializes state correctly."""
    engine = BuybackEngine(min_profit_usd=10.0)
    engine.record_profit(25.0)
    state = engine.to_dict()
    assert state["accrued_profit"] == 25.0
    assert state["min_profit_usd"] == 10.0
    assert state["allocation_pct"] == 0.10
    assert state["total_buybacks"] == 0
    assert state["simulated"] is True


def test_buyback_reset() -> None:
    """Reset clears accrued profit."""
    engine = BuybackEngine(min_profit_usd=10.0)
    engine.record_profit(50.0)
    engine.reset()
    assert engine.accrued_profit == 0.0
    result = engine.execute()
    assert result["action"] == "hold"


def test_buyback_token_price_zero() -> None:
    """Engine handles token_price_usd of 0 gracefully."""
    engine = BuybackEngine(min_profit_usd=5.0, token_price_usd=0)
    engine.record_profit(100.0)
    result = engine.execute()
    assert result["action"] == "buyback"
    assert result["tokens_purchased"] == 0


def test_deploy_heap_returns_stub() -> None:
    """Deployment stub returns expected shape."""
    result = deploy_heap()
    assert result["status"] == "simulated"
    assert result["token"] == "HEAP"
    assert result["supply"] == 1_000_000
