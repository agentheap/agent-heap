"""Arbitrum chain configuration -- supports both Sepolia testnet and One mainnet.

Toggle via ARBITRUM_NETWORK env var:
  "sepolia" (default) -- Arbitrum Sepolia testnet
  "mainnet"          -- Arbitrum One mainnet
"""

import os

ARBITRUM_NETWORK = os.getenv("ARBITRUM_NETWORK", "sepolia").lower()
ARBITRUM_CHAIN_ID = 42161 if ARBITRUM_NETWORK == "mainnet" else 421614
ARBITRUM_RPC = (
    "https://arb1.arbitrum.io/rpc"
    if ARBITRUM_NETWORK == "mainnet"
    else "https://sepolia-rollup.arbitrum.io/rpc"
)


def is_mainnet() -> bool:
    """Return True when the active network is Arbitrum One mainnet."""
    return ARBITRUM_NETWORK == "mainnet"
