"""Agent Heap — LangGraph state machine.

Flow:
  collector → analyzer → risk_check → signaler → executor → record_pnl → buyback
"""

from typing import Any, TypedDict

from langgraph.graph import StateGraph

from agent.nodes.collector import collect_yields
from agent.nodes.analyzer import analyze
from agent.nodes.risk_check import check_risks, record_pnl
from agent.nodes.signal import generate_signal
from agent.nodes.executor import execute
from agent.nodes.buyback import run_buyback


class AgentState(TypedDict):
    yields: list[dict[str, Any]]
    analysis: dict[str, Any] | None
    risk_ok: bool
    risk_reason: str
    sized_amount: float
    capital: float
    signal: dict[str, Any] | None
    tx_result: dict[str, Any] | None
    buyback: dict[str, Any] | None
    errors: list[str]


def run_agent(capital: float = 1.0) -> dict[str, Any]:
    """Run the agent with a given capital amount in ETH."""
    builder = StateGraph(AgentState)
    builder.add_node("collector", collect_yields)
    builder.add_node("analyzer", analyze)
    builder.add_node("risk_check", check_risks)
    builder.add_node("signaler", generate_signal)
    builder.add_node("executor", execute)
    builder.add_node("record_pnl", record_pnl)
    builder.add_node("buyback", run_buyback)

    builder.set_entry_point("collector")

    builder.add_edge("collector", "analyzer")
    builder.add_edge("analyzer", "risk_check")
    builder.add_edge("risk_check", "signaler")
    builder.add_edge("signaler", "executor")
    builder.add_edge("executor", "record_pnl")
    builder.add_edge("record_pnl", "buyback")

    graph = builder.compile()

    return graph.invoke(
        {
            "yields": [],
            "analysis": None,
            "risk_ok": True,
            "risk_reason": "",
            "sized_amount": 0.0,
            "capital": capital,
            "signal": None,
            "tx_result": None,
            "buyback": None,
            "errors": [],
        }
    )


agent_graph = run_agent
