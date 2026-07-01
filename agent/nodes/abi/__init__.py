"""Protocol ABIs for deposit/supply functions on Arbitrum.

Supports both Sepolia (testnet) and Arbitrum One (mainnet).
Toggle via ARBITRUM_NETWORK env var: "sepolia" (default) or "mainnet".
"""

import json
import os

from chains.arbitrum import is_mainnet

_ABI_DIR = os.path.dirname(os.path.abspath(__file__))


def _load_abi(name: str) -> list[dict]:
    path = os.path.join(_ABI_DIR, f"{name}.json")
    with open(path) as f:
        return json.load(f)


def load_erc20_abi() -> list[dict]:
    return _load_abi("erc20")


def load_aave_pool_abi() -> list[dict]:
    return _load_abi("aave_v3_pool")


def load_compound_comet_abi() -> list[dict]:
    return _load_abi("compound_comet")


def load_morpho_blue_abi() -> list[dict]:
    return _load_abi("morpho_blue")


# --- Arbitrum One Mainnet (chain_id: 42161) ---
AAVE_V3_POOL_MAINNET = "0x794a61358D6845594F94dc1DB02A252b5b4814aD"
COMPOUND_COMET_MAINNET = "0xA5eD225DD425849A5252b4eB2300Fb654d12bbf0"
MORPHO_BLUE_MAINNET = "0xBBBBBbbBBb9cC5e90e3b3Af64bdAF62C37EEFFCb"
USDC_MAINNET = "0xaf88d065e77c8cC2239327C5EDb3A432268e5831"

# --- Arbitrum Sepolia (testnet) ---
AAVE_V3_POOL_SEPOLIA = "0x6Ae43d3271ff6888e7Fc43Fd7321a503ff738951"
COMPOUND_COMET_SEPOLIA = "0x1b7E8Fb38e734FD41E73A94F2779982F73eF3706"
MORPHO_BLUE_SEPOLIA = "0xBBBBBbbBBb9cC5e90e3b3Af64bdAF62C37EEFFCb"
USDC_SEPOLIA = "0x75faf114eafb1BDbe2F0316DF893fd58CE46AA4d"

# --- Active addresses based on network toggle ---
AAVE_V3_POOL = AAVE_V3_POOL_MAINNET if is_mainnet() else AAVE_V3_POOL_SEPOLIA
COMPOUND_COMET = COMPOUND_COMET_MAINNET if is_mainnet() else COMPOUND_COMET_SEPOLIA
MORPHO_BLUE = MORPHO_BLUE_MAINNET if is_mainnet() else MORPHO_BLUE_SEPOLIA
USDC = USDC_MAINNET if is_mainnet() else USDC_SEPOLIA

# Map protocol names to their contract addresses
PROTOCOL_ADDRESSES = {
    "aave": AAVE_V3_POOL,
    "compound": COMPOUND_COMET,
    "morpho": MORPHO_BLUE,
}
