from typing import Any, TypedDict

from langgraph.graph import StateGraph

from agent.memory.vector_store import AgentMemory
from agent.nodes.collector import collect_yields
from agent.nodes.analyzer import analyze
from agent.nodes.signal import generate_signal
from agent.nodes.executor import execute


class AgentState(TypedDict):
    yields: list[dict[str, Any]]
    analysis: dict[str, Any] | None
    signal: dict[str, Any] | None
    tx_result: dict[str, Any] | None
    errors: list[str]


def run_agent() -> dict[str, Any]:
    builder = StateGraph(AgentState)
    builder.add_node("collector", collect_yields)
    builder.add_node("analyzer", analyze)
    builder.add_node("signaler", generate_signal)
    builder.add_node("executor", execute)
    builder.set_entry_point("collector")
    builder.add_edge("collector", "analyzer")
    builder.add_edge("analyzer", "signaler")
    builder.add_edge("signaler", "executor")
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
