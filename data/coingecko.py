from typing import Any

import httpx

COINGECKO_BASE = "https://api.coingecko.com/api/v3"


def get_price(token_address: str, chain: str = "arbitrum") -> float | None:
    url = f"{COINGECKO_BASE}/simple/token_price/{chain}"
    params = {"contract_addresses": token_address, "vs_currencies": "usd"}
    try:
        resp = httpx.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return data.get(token_address.lower(), {}).get("usd")
    except Exception:
        return None


def get_prices(token_addresses: list[str], chain: str = "arbitrum") -> dict[str, Any]:
    url = f"{COINGECKO_BASE}/simple/token_price/{chain}"
    params = {
        "contract_addresses": ",".join(token_addresses),
        "vs_currencies": "usd",
    }
    try:
        resp = httpx.get(url, params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return {}
