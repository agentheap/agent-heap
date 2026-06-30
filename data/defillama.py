from typing import Any

import httpx

DEFILLAMA_BASE = "https://yields.llama.fi"


def get_yields(protocols: list[str] | None = None) -> list[dict[str, Any]]:
    try:
        resp = httpx.get(f"{DEFILLAMA_BASE}/pools", timeout=10)
        resp.raise_for_status()
        data = resp.json()
        pools = data.get("data", [])
    except Exception:
        return []

    if not protocols:
        return pools

    protocol_prefixes = tuple(p.lower() for p in protocols)
    filtered = [
        {
            "protocol": p.get("project", ""),
            "pool": p.get("symbol", ""),
            "apy": p.get("apy", 0),
            "tvl": p.get("tvlUsd", 0),
            "chain": p.get("chain", ""),
        }
        for p in pools
        if p.get("project", "").lower().startswith(protocol_prefixes)
    ]
    return filtered
