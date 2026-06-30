"""
Arbitrum chain configuration.

Supports both Sepolia testnet and Arbitrum One mainnet.
Toggle via ARBITRUM_NETWORK env var: "sepolia" (default) or "mainnet"
"""

import os
from typing import Literal

# --- Sepolia (testnet) config ---
SEPOLIA_RPC = "https://sepolia-rollup.arbitrum.io/rpc"
SEPOLIA_CHAIN_ID = 421614

# --- Arbitrum One (mainnet) config ---
MAINNET_RPC = "https://arb1.arbitrum.io/rpc"
MAINNET_CHAIN_ID = 42161

# --- Active config based on env toggle ---
ARBITRUM_NETWORK: Literal["sepolia", "mainnet"] = os.getenv("ARBITRUM_NETWORK", "sepolia")  # type: ignore[assignment]

if ARBITRUM_NETWORK not in ("sepolia", "mainnet"):
    raise ValueError(
        f"Invalid ARBITRUM_NETWORK={ARBITRUM_NETWORK!r}. Must be 'sepolia' or 'mainnet'."
    )

ARBITRUM_RPC = MAINNET_RPC if ARBITRUM_NETWORK == "mainnet" else SEPOLIA_RPC
ARBITRUM_CHAIN_ID = MAINNET_CHAIN_ID if ARBITRUM_NETWORK == "mainnet" else SEPOLIA_CHAIN_ID


def is_mainnet() -> bool:
    return ARBITRUM_NETWORK == "mainnet"


def is_sepolia() -> bool:
    return ARBITRUM_NETWORK == "sepolia"
