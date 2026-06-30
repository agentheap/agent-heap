"""Protocol ABIs for deposit/supply functions on Arbitrum Sepolia."""

import json
import os

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


# Arbitrum Sepolia contract addresses
AAVE_V3_POOL = "0x6Ae43d3271ff6888e7Fc43Fd7321a503ff738951"
COMPOUND_COMET = "0x1b7E8Fb38e734FD41E73A94F2779982F73eF3706"
MORPHO_BLUE = "0xBBBBBbbBBb9cC5e90e3b3Af64bdAF62C37EEFFCb"
USDC_ARB_SEPOLIA = "0x75faf114eafb1BDbe2F0316DF893fd58CE46AA4d"

# Map protocol names to their contract addresses
PROTOCOL_ADDRESSES = {
    "aave": AAVE_V3_POOL,
    "compound": COMPOUND_COMET,
    "morpho": MORPHO_BLUE,
}
