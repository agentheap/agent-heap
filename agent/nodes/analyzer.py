import os
from typing import Any

from agent.memory.vector_store import AgentMemory

ANALYST_PROMPT = """You are a DeFi yield analyst. Given these lending pools, pick the one with the best risk-adjusted yield.

Pools:
{pools}

{memory}

Respond with ONLY the pool name (symbol) and a one-sentence reason. Format: POOL: <symbol> REASON: <reason>"""


def _format_memory_section(memory_entries: list[dict[str, Any]]) -> str:
    if not memory_entries:
        return ""
    lines = ["Past decisions (similar outcomes from recent runs):"]
    for i, entry in enumerate(memory_entries, 1):
        action = entry.get("action", "?")
        protocol = entry.get("protocol", "?")
        pool = entry.get("pool", "?")
        reason = entry.get("reason", "?")
        lines.append(f"  {i}. {action} on {protocol}/{pool} — {reason}")
    lines.append("Consider what worked before when selecting the best pool.")
    return "\n".join(lines)


def analyze(state: dict[str, Any]) -> dict[str, Any]:
    yields = state.get("yields", [])
    if not yields:
        return {**state, "analysis": None}

    # Use memory context injected via state; fall back to live Chroma query
    memory_entries: list[dict[str, Any]] = state.get("memory_context", [])
    if not memory_entries:
        try:
            mem = AgentMemory(path=state.get("memory_path"))
            pool_names = [p.get("pool", "") for p in yields[:5]]
            query = (
                f"yield optimization {' '.join(pool_names)}"
                if pool_names
                else "yield optimization"
            )
            memory_entries = mem.query_similar(query, k=3)
        except Exception:
            memory_entries = []

    memory_text = _format_memory_section(memory_entries)

    nvidia_key = os.getenv("NVIDIA_NIM_API_KEY")

    if nvidia_key:
        try:
            return _analyze_with_nvidia(state, yields, nvidia_key, memory_text)
        except Exception:
            pass

    return _analyze_fallback(state, yields, memory_text)


def _analyze_with_nvidia(
    state: dict[str, Any],
    yields: list[dict[str, Any]],
    api_key: str,
    memory_text: str,
) -> dict[str, Any]:
    from langchain_nvidia_ai_endpoints import ChatNVIDIA

    llm = ChatNVIDIA(
        model="mistralai/mistral-7b-instruct-v0.3",
        api_key=api_key,
        temperature=0.1,
    )
    pool_lines = "\n".join(
        f"{p['protocol']} / {p['pool']}: {p['apy']:.1f}% APY, ${p['tvl']:,.0f} TVL on {p['chain']}"
        for p in yields[:20]
    )
    response = llm.invoke(ANALYST_PROMPT.format(pools=pool_lines, memory=memory_text))
    content = response.content.strip()

    pool_name = None
    reason = content
    for line in content.split("\n"):
        if line.upper().startswith("POOL:"):
            pool_name = line.split(":", 1)[1].strip()
        if line.upper().startswith("REASON:"):
            reason = line.split(":", 1)[1].strip()

    if pool_name:
        matched = [p for p in yields if p["pool"].lower() == pool_name.lower()]
        if matched:
            return {**state, "analysis": {**matched[0], "reason": reason}}

    return _analyze_fallback(state, yields, memory_text)


def _analyze_fallback(
    state: dict[str, Any],
    yields: list[dict[str, Any]],
    memory_text: str = "",
) -> dict[str, Any]:
    best = max(yields, key=lambda p: p.get("apy", 0))
    return {
        **state,
        "analysis": {**best, "reason": f"highest apy at {best['apy']:.1f}%"},
    }
