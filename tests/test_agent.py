from agent.graph import run_agent
from agent.memory.vector_store import AgentMemory
from agent.nodes.analyzer import analyze
from agent.nodes.collector import collect_yields
from agent.nodes.executor import execute
from agent.nodes.signal import generate_signal
from agent.nodes.risk_check import check_risks, record_pnl
from agent.nodes.buyback import run_buyback
from data.defillama import get_yields
from risk.circuit_breaker import CircuitBreaker
from risk.position_sizing import kelly_fraction
from risk.slippage import estimate_slippage


def test_graph_runs():
    result = run_agent()
    assert isinstance(result, dict)


def test_collector():
    result = collect_yields({"yields": [], "errors": []})
    assert "yields" in result


def test_analyzer_selects_best(sample_yields):
    state = {"yields": sample_yields, "analysis": None}
    result = analyze(state)
    assert result["analysis"] is not None


def test_analyzer_returns_none_on_empty():
    result = analyze({"yields": [], "analysis": None})
    assert result["analysis"] is None


def test_signal_generation(sample_yields):
    best = max(sample_yields, key=lambda p: p["apy"])
    state = {"yields": sample_yields, "analysis": best, "signal": None, "risk_ok": True, "sized_amount": 0.02}
    result = generate_signal(state)
    assert result["signal"]["action"] == "deposit"
    assert result["signal"]["protocol"] == "morpho"
    assert result["signal"]["amount"] == 0.02


def test_executor():
    signal = {
        "action": "deposit",
        "protocol": "aave",
        "pool": "USDC",
        "amount": 0.01,
        "reason": "test",
    }
    state = {"signal": signal, "tx_result": None}
    result = execute(state)
    assert result["tx_result"]["simulated"] is True


def test_executor_no_signal():
    result = execute({"signal": None, "tx_result": None})
    assert result["tx_result"] is None


def test_memory():
    mem = AgentMemory(path="/tmp/test_chroma_heap")
    mem.store_decision({"action": "deposit", "protocol": "aave", "amount": 0.01})
    results = mem.query_similar("deposit aave", k=1)
    assert len(results) > 0


def test_get_yields():
    result = get_yields(["aave", "compound"])
    assert isinstance(result, list)


def test_circuit_breaker_not_tripped():
    cb = CircuitBreaker(max_daily_drawdown=0.05)
    cb.record_trade(0.01)
    assert cb.is_tripped() is False


def test_circuit_breaker_tripped():
    cb = CircuitBreaker(max_daily_drawdown=0.05)
    cb.record_trade(-0.06)
    assert cb.is_tripped() is True


def test_kelly_fraction():
    f = kelly_fraction(0.6, 1.5)
    assert 0 < f < 1


def test_slippage_estimate():
    bps, ok = estimate_slippage(
        pool_liquidity=1_000_000, trade_amount=1000, max_slippage_bps=100
    )
    assert bps > 0
    assert ok is True


def test_slippage_rejected():
    bps, ok = estimate_slippage(
        pool_liquidity=1_000, trade_amount=500, max_slippage_bps=100
    )
    assert ok is False


def test_risk_check_passes(sample_yields):
    best = max(sample_yields, key=lambda p: p["apy"])
    state = {
        "yields": sample_yields,
        "analysis": best,
        "capital": 1.0,
        "signal": {"amount": 0.01},
    }
    result = check_risks(state)
    assert result.get("risk_ok") is True
    assert result.get("sized_amount", 0) > 0


def test_risk_check_blocks_empty():
    result = check_risks({"analysis": None})
    assert result.get("risk_ok") is False


def test_buyback_with_profit():
    state = {"tx_result": {"pnl": 0.01}}
    result = run_buyback(state)
    assert result.get("buyback") is not None
    assert result["buyback"].get("amount", 0) > 0


def test_buyback_no_profit():
    state = {"tx_result": {"pnl": 0}}
    result = run_buyback(state)
    assert result.get("buyback") is not None
    assert result["buyback"].get("status") == "no_profits"
