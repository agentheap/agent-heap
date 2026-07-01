from typing import Any, Literal, TypedDict

from langgraph.graph import StateGraph

from agent.memory.vector_store import AgentMemory
from agent.nodes.collector import collect_yields
from agent.nodes.analyzer import analyze
from agent.nodes.signal import generate_signal
from agent.nodes.executor import execute
from agent.nodes.buyback_node import run_buyback


class AgentState(TypedDict):
    yields: list[dict[str, Any]]
    analysis: dict[str, Any] | None
    signal: dict[str, Any] | None
    tx_result: dict[str, Any] | None
    buyback_result: dict[str, Any] | None
    errors: list[str]
    memory_context: list[dict[str, Any]]
    memory_path: str


_breaker = CircuitBreaker()


def _cb_router(state: AgentState) -> Literal["executor", "__end__"]:
    """Route to executor if circuit breaker is not tripped, otherwise skip."""
    if _breaker.is_tripped():
        return "__end__"
    return "executor"


def build_graph_graph() -> StateGraph:
    """Build the LangGraph state machine for the yield-optimization agent."""
    builder = StateGraph(AgentState)
    builder.add_node("collector", collect_yields)
    builder.add_node("analyzer", analyze)
    builder.add_node("signaler", generate_signal)
    builder.add_node("executor", execute)
    builder.add_node("buyback", run_buyback)
    builder.set_entry_point("collector")
    builder.add_edge("collector", "analyzer")
    builder.add_edge("analyzer", "signaler")
    builder.add_edge("signaler", "executor")
    builder.add_edge("executor", "buyback")
    graph = builder.compile()
    return graph.invoke(
        {
            "yields": [],
            "analysis": None,
            "signal": None,
            "tx_result": None,
            "buyback_result": None,
            "errors": [],
            "memory_context": memory_context,
            "memory_path": mem.path,
        }
    )

    # Post-execution: persist decision metadata to Chroma
    tx = result.get("tx_result")
    if tx:
        _breaker.record_trade(0.0)

    store_decision_from_result(mem, result)

    return result


def store_decision_from_result(mem: AgentMemory, result: dict[str, Any]) -> None:
    """Extract a decision from the graph result and store it in Chroma."""
    tx = result.get("tx_result")
    signal = result.get("signal")
    if not tx:
        return

    decision: dict[str, Any] = {
        "action": tx.get("action"),
        "protocol": tx.get("protocol"),
        "pool": tx.get("pool"),
        "amount": tx.get("amount"),
        "reason": signal.get("reason") if signal else None,
        "apy": signal.get("apy") if signal else None,
        "tvl": signal.get("tvl") if signal else None,
        "simulated": tx.get("simulated"),
    }

    # Add any error info if present
    errors = result.get("errors", [])
    if errors:
        decision["errors"] = errors

    mem.store_decision(decision)


agent_graph = run_agent
