from typing import Any, TypedDict

from langgraph.graph import StateGraph

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


def run_agent() -> dict[str, Any]:
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
        }
    )


agent_graph = run_agent
