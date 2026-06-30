from typing import Any


def route_to_chain(chain: str) -> dict[str, Any]:
    chains = {
        "arbitrum": {
            "rpc": "https://sepolia-rollup.arbitrum.io/rpc",
            "chain_id": 421614,
        },
        "base": {"rpc": "https://sepolia.base.org", "chain_id": 84532},
    }
    return chains.get(chain, chains["arbitrum"])
