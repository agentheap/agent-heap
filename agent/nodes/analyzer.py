import os
from typing import Any

ANALYST_PROMPT = """You are a DeFi yield analyst. Given these lending pools, pick the one with the best risk-adjusted yield.

Pools:
{pools}

Respond with ONLY the pool name (symbol) and a one-sentence reason. Format: POOL: <symbol> REASON: <reason>"""


def analyze(state: dict[str, Any]) -> dict[str, Any]:
    yields = state.get("yields", [])
    if not yields:
        return {**state, "analysis": None}

    nvidia_key = os.getenv("LLM_API_KEY") or os.getenv("NVIDIA_NIM_API_KEY")

    if nvidia_key:
        try:
            return _analyze_with_nvidia(state, yields, nvidia_key)
        except Exception:
            pass

    return _analyze_fallback(state, yields)


def _analyze_with_nvidia(
    state: dict[str, Any],
    yields: list[dict[str, Any]],
    api_key: str,
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
    response = llm.invoke(ANALYST_PROMPT.format(pools=pool_lines))
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

    return _analyze_fallback(state, yields)


def _analyze_fallback(
    state: dict[str, Any], yields: list[dict[str, Any]]
) -> dict[str, Any]:
    best = max(yields, key=lambda p: p.get("apy", 0))
    return {
        **state,
        "analysis": {**best, "reason": f"highest apy at {best['apy']:.1f}%"},
    }
