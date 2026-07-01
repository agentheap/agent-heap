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
        lines.append(f"  {i}. {action} on {protocol}/{pool} -- {reason}")
    lines.append("Consider what worked before when selecting the best pool.")
    return "\n".join(lines)


def analyze(state: dict[str, Any]) -> dict[str, Any]:
    yields = state.get("yields", [])
    if not yields:
        return {**state, "analysis": None}

    memory = state.get("memory_context", [])
    memory_text = _format_memory_section(memory)

    model = os.getenv("LLM_MODEL")
    if model:
        try:
            return _analyze_with_llm(state, yields, model)
        except Exception:
            pass

    return _analyze_fallback(state, yields, memory_text)


def _analyze_with_llm(
    state: dict[str, Any],
    yields: list[dict[str, Any]],
    model: str,
) -> dict[str, Any]:
    from litellm import completion

    pool_lines = "\n".join(
        f"{p['protocol']} / {p['pool']}: {p['apy']:.1f}% APY, ${p['tvl']:,.0f} TVL on {p['chain']}"
        for p in yields[:20]
    )
    memory = state.get("memory_context", [])
    memory_text = _format_memory_section(memory)
    response = completion(
        model=model,
        messages=[{"role": "user", "content": ANALYST_PROMPT.format(pools=pool_lines, memory=memory_text)}],
        temperature=0.1,
    )
    content = response.choices[0].message.content.strip()

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

    return _analyze_fallback(state, yields, memory_text or "")


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
