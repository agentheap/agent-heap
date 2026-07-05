"""Agent Heap graph -- LangGraph state machine for yield optimization.

Pipeline: collector -> harvester -> analyzer -> signaler -> executor -> buyback

The harvester checks existing positions for accrued yield before the
analyzer picks the best pool, enabling the harvest-reinvest pattern.
"""

from typing import Any, Literal, TypedDict

from langgraph.graph import StateGraph

from agent.memory.vector_store import AgentMemory
from agent.nodes.collector import collect_yields
from agent.nodes.harvester import harvest
from agent.nodes.analyzer import analyze
from agent.nodes.signal import generate_signal
from agent.nodes.executor import execute
from agent.nodes.buyback import run_buyback
from risk.circuit_breaker import CircuitBreaker


class AgentState(TypedDict):
    yields: list[dict[str, Any]]
    analysis: dict[str, Any] | None
    signal: dict[str, Any] | None
    tx_result: dict[str, Any] | None
    buyback_result: dict[str, Any] | None
    errors: list[str]
    memory_context: list[dict[str, Any]]
    memory_path: str
    harvest_signal: dict[str, Any] | None
    harvest_yield_info: list[dict[str, Any]]
    withdrawal_results: list[dict[str, Any]]


_breaker = CircuitBreaker()


def _cb_router(state: AgentState) -> Literal["executor", "__end__"]:
    """Route to executor if circuit breaker is not tripped, otherwise skip."""
    if _breaker.is_tripped():
        return "__end__"
    return "executor"


def _build_graph(
    memory_context: list[dict[str, Any]] | None = None,
    memory_path: str = "./chroma_data",
) -> dict[str, Any]:
    """Build, compile, and invoke the LangGraph state machine.

    Returns the final state dict after a full pipeline run.
    """
    if memory_context is None:
        memory_context = []

    builder = StateGraph(AgentState)
    builder.add_node("collector", collect_yields)
    builder.add_node("harvester", harvest)
    builder.add_node("analyzer", analyze)
    builder.add_node("signaler", generate_signal)
    builder.add_node("executor", execute)
    builder.add_node("buyback", run_buyback)
    builder.set_entry_point("collector")
    builder.add_edge("collector", "harvester")
    builder.add_edge("harvester", "analyzer")
    builder.add_edge("analyzer", "signaler")
    builder.add_edge("signaler", "executor")
    builder.add_edge("executor", "buyback")

    graph = builder.compile()
    result = graph.invoke(
        {
            "yields": [],
            "analysis": None,
            "signal": None,
            "tx_result": None,
            "buyback_result": None,
            "errors": [],
            "memory_context": memory_context,
            "memory_path": memory_path,
            "harvest_signal": None,
            "harvest_yield_info": [],
            "withdrawal_results": [],
        }
    )
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

    # Include harvest info if any
    harvest_info = result.get("harvest_yield_info", [])
    if harvest_info:
        decision["harvested"] = sum(h.get("accrued_yield", 0) for h in harvest_info)

    # Add any error info if present
    errors = result.get("errors", [])
    if errors:
        decision["errors"] = errors

    mem.store_decision(decision)


def run_agent() -> dict[str, Any]:
    """Run the full agent pipeline: collect -> harvest -> analyze -> signal -> execute -> buyback.

    Loads past memory context from ChromaDB, invokes the graph,
    persists the new decision, and returns the result dict.
    """
    mem = AgentMemory()
    past = mem.query_similar("yield optimization opportunity", k=3)

    result = _build_graph(memory_context=past, memory_path=mem.path)

    # Track PnL for circuit breaker
    tx = result.get("tx_result")
    if tx:
        simulated_pnl = tx.get("simulated_pnl", 0.0)
        _breaker.record_trade(simulated_pnl)

    # Persist decision to vector memory
    store_decision_from_result(mem, result)

    return result
