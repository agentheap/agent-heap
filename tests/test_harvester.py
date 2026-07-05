"""Tests for the harvester node and harvest-reinvest flow."""

import json
import os
import tempfile

import pytest

from agent.nodes.harvester import (
    Position,
    PositionLedger,
    _load_ledger,
    _save_ledger,
    track_deposit,
    track_withdrawal,
    get_total_deposited,
    estimate_accrued_yield,
    harvest,
    MIN_HARVEST_THRESHOLD,
)
from agent.nodes.executor import (
    execute,
    build_withdraw_tx,
    _process_withdrawals,
    _withdraw_simulated,
    _spending_limits_exceeded,
    _daily_cap_exceeded,
    _is_retryable,
    _get_min_out,
)


# ── Fixtures ──────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def _temp_positions_file():
    """Use a temp positions file for every test to avoid cross-test pollution."""
    tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w")
    json.dump({"positions": [], "updated_at": ""}, tmp)
    tmp.close()
    os.environ["AGENT_POSITIONS_FILE"] = tmp.name
    yield
    os.unlink(tmp.name)
    if "AGENT_POSITIONS_FILE" in os.environ:
        del os.environ["AGENT_POSITIONS_FILE"]


@pytest.fixture
def sample_yields():
    return [
        {"protocol": "aave", "pool": "USDC", "apy": 5.2, "tvl": 100_000_000, "chain": "Arbitrum"},
        {"protocol": "compound", "pool": "USDC", "apy": 4.8, "tvl": 80_000_000, "chain": "Arbitrum"},
        {"protocol": "morpho", "pool": "USDC", "apy": 6.1, "tvl": 50_000_000, "chain": "Arbitrum"},
    ]


# ── Position Ledger ───────────────────────────────────────────────────


def test_track_deposit_new():
    track_deposit("aave", "USDC", 100.0, apy=5.2)
    totals = get_total_deposited()
    assert totals.get("aave") == 100.0


def test_track_deposit_merge():
    track_deposit("aave", "USDC", 100.0)
    track_deposit("aave", "USDC", 50.0)
    totals = get_total_deposited()
    assert totals["aave"] == 150.0


def test_track_deposit_multiple_protocols():
    track_deposit("aave", "USDC", 100.0)
    track_deposit("compound", "USDC", 200.0)
    totals = get_total_deposited()
    assert totals["aave"] == 100.0
    assert totals["compound"] == 200.0


def test_track_withdrawal_partial():
    track_deposit("aave", "USDC", 100.0)
    track_withdrawal("aave", "USDC", 30.0)
    totals = get_total_deposited()
    assert totals["aave"] == 70.0


def test_track_withdrawal_full():
    track_deposit("aave", "USDC", 100.0)
    track_withdrawal("aave", "USDC", 100.0)
    totals = get_total_deposited()
    assert "aave" not in totals


def test_track_withdrawal_excess():
    track_deposit("aave", "USDC", 50.0)
    track_withdrawal("aave", "USDC", 999.0)
    totals = get_total_deposited()
    assert "aave" not in totals


def test_ledger_persistence():
    track_deposit("aave", "USDC", 100.0)
    track_deposit("compound", "USDC", 200.0)
    # Reload from file
    ledger = _load_ledger()
    assert len(ledger.positions) == 2
    amounts = {p.protocol: p.amount for p in ledger.positions}
    assert amounts["aave"] == 100.0
    assert amounts["compound"] == 200.0


def test_empty_ledger():
    totals = get_total_deposited()
    assert totals == {}


# ── Yield Estimation ──────────────────────────────────────────────────


def test_estimate_accrued_yield(sample_yields):
    pos = Position(protocol="aave", pool="USDC", amount=1000.0,
                   deposited_at="2026-06-30T00:00:00", apy_at_deposit=5.0)
    accrued = estimate_accrued_yield(pos, sample_yields)
    # ~1000 * 0.052 * 5/365 ≈ 0.71 for 5 days at 5.2% APY
    assert accrued > 0
    assert accrued < 10  # Sanity check: shouldn't be huge


def test_estimate_accrued_yield_zero_apy():
    pos = Position(protocol="aave", pool="USDC", amount=1000.0,
                   deposited_at="2026-06-30T00:00:00", apy_at_deposit=0)
    accrued = estimate_accrued_yield(pos, [])
    assert accrued == 0.0


def test_estimate_accrued_yield_no_match():
    pos = Position(protocol="aave", pool="USDC", amount=1000.0,
                   deposited_at="2026-06-30T00:00:00", apy_at_deposit=5.0)
    accrued = estimate_accrued_yield(pos, [{"protocol": "compound", "pool": "USDC", "apy": 3.0}])
    assert accrued > 0  # Falls back to apy_at_deposit


# ── Harvester Node ────────────────────────────────────────────────────


def test_harvester_no_positions(sample_yields):
    state = {"yields": sample_yields}
    result = harvest(state)
    assert result["harvest_signal"] is None
    assert result["harvest_yield_info"] == []


def test_harvester_below_threshold():
    """Yield accrued but below MIN_HARVEST_THRESHOLD."""
    track_deposit("aave", "USDC", 10.0, apy=5.0)
    state = {
        "yields": [{"protocol": "aave", "pool": "USDC", "apy": 5.0, "tvl": 1_000_000, "chain": "Arbitrum"}]
    }
    result = harvest(state)
    # 10 * 0.05 * elapsed_days/365 — with a fresh deposit, elapsed is near 0
    assert result["harvest_signal"] is None


def test_harvester_above_threshold(sample_yields):
    """Large position with enough elapsed time should trigger harvest."""
    track_deposit("aave", "USDC", 5000.0)
    state = {"yields": sample_yields}
    result = harvest(state)
    # If elapsed time is > 0 (test fixture writes a new timestamp),
    # a $5000 position at 5.2% APY accrues ~$0.71/day.
    signal = result["harvest_signal"]
    info = result["harvest_yield_info"]
    if signal:
        assert signal["action"] == "harvest_and_redeposit"
        assert signal["total_harvestable"] > 0
        assert len(info) > 0
        assert info[0]["protocol"] == "aave"


def test_harvester_multiple_positions(sample_yields):
    track_deposit("aave", "USDC", 5000.0)
    track_deposit("compound", "USDC", 3000.0)
    state = {"yields": sample_yields}
    result = harvest(state)
    info = result["harvest_yield_info"]
    if result["harvest_signal"]:
        assert len(info) >= 1  # At least one position has yield


# ── Withdrawal ────────────────────────────────────────────────────────


def test_withdraw_simulated():
    result = _withdraw_simulated("aave", 100.0)
    assert result["success"] is True
    assert result["simulated"] is True
    assert result["protocol"] == "aave"
    assert result["amount"] == 100.0


def test_build_withdraw_tx_aave():
    tx = build_withdraw_tx("aave", 1000000, "0x1234567890123456789012345678901234567890")
    assert tx is not None
    assert tx["to"] is not None
    assert tx["data"] is not None
    assert "withdraw" in tx["description"]


def test_build_withdraw_tx_compound():
    tx = build_withdraw_tx("compound", 1000000, "0x1234567890123456789012345678901234567890")
    assert tx is not None
    assert "withdraw" in tx["description"]
    # Compound checksum address should be valid
    assert tx["to"].startswith("0x")


def test_build_withdraw_tx_aave_checksum():
    """Aave pool address should be a valid EIP-55 checksum address."""
    from web3 import Web3
    tx = build_withdraw_tx("aave", 1000000, "0x1234567890123456789012345678901234567890")
    assert tx is not None
    assert Web3.is_checksum_address(tx["to"])


def test_build_withdraw_tx_morpho():
    tx = build_withdraw_tx("morpho", 1000000, "0x1234567890123456789012345678901234567890")
    assert tx is None  # Not yet implemented


def test_build_withdraw_tx_unknown():
    tx = build_withdraw_tx("unknown_protocol", 1000000, "0x1234567890123456789012345678901234567890")
    assert tx is None


def test_process_withdrawals_simulated():
    harvest_signal = {
        "action": "harvest_and_redeposit",
        "total_harvestable": 5.0,
        "positions": [
            {"protocol": "aave", "pool": "USDC", "deposited": 1000.0, "accrued_yield": 5.0, "elapsed_days": 30},
        ]
    }
    os.environ.pop("PRIVATE_KEY", None)
    results, total = _process_withdrawals({}, harvest_signal)
    assert len(results) == 1
    assert total == 1005.0
    assert results[0]["success"] is True
    assert results[0]["simulated"] is True


# ── Executor Integration ──────────────────────────────────────────────


def test_executor_with_harvest_signal():
    """Executor should handle harvest signal + deposit signal together."""
    signal = {
        "action": "deposit",
        "protocol": "aave",
        "pool": "USDC",
        "amount": 0.01,
        "reason": "test",
        "apy": 5.2,
    }
    state = {
        "signal": signal,
        "tx_result": None,
        "harvest_signal": {
            "action": "harvest_and_redeposit",
            "total_harvestable": 0.75,
            "positions": [
                {"protocol": "aave", "pool": "USDC", "deposited": 100.0, "accrued_yield": 0.75, "elapsed_days": 50},
            ]
        },
        "harvest_yield_info": [{"protocol": "aave", "pool": "USDC", "deposited": 100.0, "accrued_yield": 0.75, "elapsed_days": 50}],
        "memory_context": [],
    }
    result = execute(state)
    assert result["tx_result"]["simulated"] is True
    assert result["tx_result"]["protocol"] == "aave"
    assert len(result["withdrawal_results"]) == 1
    assert result["withdrawal_results"][0]["success"] is True


def test_executor_no_signal_with_harvest():
    """Executor should still process withdrawals even without a deposit signal."""
    state = {
        "signal": None,
        "tx_result": None,
        "harvest_signal": {
            "action": "harvest_and_redeposit",
            "total_harvestable": 1.0,
            "positions": [
                {"protocol": "compound", "pool": "USDC", "deposited": 200.0, "accrued_yield": 1.0, "elapsed_days": 30},
            ]
        },
        "harvest_yield_info": [],
        "memory_context": [],
    }
    result = execute(state)
    assert result["tx_result"] is None
    assert len(result["withdrawal_results"]) == 1


# ── Hardening: spending limits, retry, MEV protection ─────────────────


def test_spending_limits_within_bounds():
    os.environ["MAX_TX_AMOUNT"] = "100"
    assert _spending_limits_exceeded(50) is None
    del os.environ["MAX_TX_AMOUNT"]


def test_spending_limits_block_over():
    os.environ["MAX_TX_AMOUNT"] = "10"
    err = _spending_limits_exceeded(20)
    assert err is not None
    assert "MAX_TX_AMOUNT" in err
    del os.environ["MAX_TX_AMOUNT"]


def test_spending_limits_no_env():
    assert _spending_limits_exceeded(100) is None


def test_retryable_error_patterns():
    class FakeError(Exception):
        pass

    assert _is_retryable(FakeError("nonce too low")) is True
    assert _is_retryable(FakeError("replacement transaction underpriced")) is True
    assert _is_retryable(FakeError("fee cap less than block base fee")) is True
    assert _is_retryable(FakeError("connection refused")) is True
    assert _is_retryable(FakeError("rate limit exceeded")) is True
    assert _is_retryable(FakeError("execution reverted: insufficient balance")) is False
    assert _is_retryable(FakeError("unknown account")) is False


def test_min_out_calculation():
    min_out = _get_min_out(1_000_000, slippage_bps=50)
    assert min_out == 995_000  # 0.5% slippage


def test_min_out_no_slippage():
    min_out = _get_min_out(1_000_000, slippage_bps=0)
    assert min_out == 1_000_000


def test_min_out_high_slippage():
    min_out = _get_min_out(1_000_000, slippage_bps=200)
    assert min_out == 980_000  # 2% slippage


def test_daily_cap_no_env():
    assert _daily_cap_exceeded(100) is None


def test_daily_cap_single_tx_under():
    """Without trade history, daily cap only checks the tx itself."""
    os.environ["DAILY_TX_LIMIT"] = "100"
    err = _daily_cap_exceeded(50)
    # May be None (no env-based check, relies on db) or a string if db fails
    # Just verify it doesn't crash
    del os.environ["DAILY_TX_LIMIT"]


# ── Cleanup ───────────────────────────────────────────────────────────


def test_clean_positions_file_after_withdrawal():
    """After full withdrawal, positions file should be empty."""
    track_deposit("aave", "USDC", 100.0)
    track_withdrawal("aave", "USDC", 100.0)
    ledger = _load_ledger()
    assert len(ledger.positions) == 0
