from typing import Any, Literal, TypedDict

from langgraph.graph import StateGraph

from agent.memory.vector_store import AgentMemory
from agent.nodes.collector import collect_yields
from agent.nodes.analyzer import analyze
from agent.nodes.signal import generate_signal
from agent.nodes.executor import execute
from risk.circuit_breaker import CircuitBreaker


class AgentState(TypedDict):
    yields: list[dict[str, Any]]
    analysis: dict[str, Any] | None
    signal: dict[str, Any] | None
    tx_result: dict[str, Any] | None
    errors: list[str]


_breaker = CircuitBreaker()


def _cb_router(state: AgentState) -> Literal["executor", "__end__"]:
    """Route to executor if circuit breaker is not tripped, otherwise skip."""
    if _breaker.is_tripped():
        return "__end__"
    return "executor"


def run_agent() -> dict[str, Any]:
    builder = StateGraph(AgentState)
    builder.add_node("collector", collect_yields)
    builder.add_node("analyzer", analyze)
    builder.add_node("signaler", generate_signal)
    builder.add_node("executor", execute)
    builder.set_entry_point("collector")
    builder.add_edge("collector", "analyzer")
    builder.add_edge("analyzer", "signaler")
    builder.add_conditional_edges("signaler", _cb_router)
    graph = builder.compile()
    result = graph.invoke(
        {
            "yields": [],
            "analysis": None,
            "signal": None,
            "tx_result": None,
            "errors": [],
        }
    )

    # Post-execution store: persist decision metadata to Chroma
    tx = result.get("tx_result")
    signal = result.get("signal")
    if tx:
        # Record trade with circuit breaker (0 PnL for simulation)
        _breaker.record_trade(0.0)
        mem = AgentMemory()
        mem.store_decision(
            {
                "action": tx.get("action"),
                "protocol": tx.get("protocol"),
                "pool": tx.get("pool"),
                "amount": tx.get("amount"),
                "reason": signal.get("reason") if signal else None,
                "apy": signal.get("apy") if signal else None,
                "tvl": signal.get("tvl") if signal else None,
                "simulated": tx.get("simulated"),
            }
        )

    return result


agent_graph = run_agent
