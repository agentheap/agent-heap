"""Chain routing — returns chain config based on ARBITRUM_NETWORK env toggle."""

from __future__ import annotations

from typing import Any

from chains.arbitrum import (
    ARBITRUM_CHAIN_ID,
    ARBITRUM_RPC,
    MAINNET_CHAIN_ID,
    MAINNET_RPC,
    SEPOLIA_CHAIN_ID,
    SEPOLIA_RPC,
)


def route_to_chain(chain: str) -> dict[str, Any]:
    chains = {
        "arbitrum": {
            "rpc": ARBITRUM_RPC,
            "chain_id": ARBITRUM_CHAIN_ID,
        },
        "arbitrum_sepolia": {
            "rpc": SEPOLIA_RPC,
            "chain_id": SEPOLIA_CHAIN_ID,
        },
        "arbitrum_mainnet": {
            "rpc": MAINNET_RPC,
            "chain_id": MAINNET_CHAIN_ID,
        },
    }
    return chains.get(chain, chains["arbitrum"])


def get_all_chain_configs() -> dict[str, dict[str, Any]]:
    """Return all available chain configs for reference."""
    return {
        "arbitrum_sepolia": {
            "rpc": SEPOLIA_RPC,
            "chain_id": SEPOLIA_CHAIN_ID,
            "network": "sepolia",
        },
        "arbitrum_mainnet": {
            "rpc": MAINNET_RPC,
            "chain_id": MAINNET_CHAIN_ID,
            "network": "mainnet",
        },
    }
