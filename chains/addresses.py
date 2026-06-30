"""
Mainnet contract addresses for DeFi protocols on Arbitrum One (chain_id: 42161).

These are canonical addresses — double-check against official docs before using.
Sepolia testnet addresses are included for the simulated path.
"""

from __future__ import annotations

from typing import NamedTuple

from chains.arbitrum import is_mainnet


class ProtocolAddresses(NamedTuple):
    pool: str
    address_provider: str | None = None
    comet: str | None = None
    morpho: str | None = None
    bundler: str | None = None


# --- Arbitrum One Mainnet ---

# Aave V3: https://docs.aave.com/developers/deployed-contracts/v3-mainnet/arbitrum
AAVE_V3_POOL_MAINNET = "0x794a61358D6845594F94dc1DB02A252b5b4814aD"
AAVE_V3_ADDRESSES_PROVIDER_MAINNET = "0xa97684ead0e402dC232d5A977953DF7EC0B9b9a2"

# Compound III (USDC Comet): https://docs.compound.finance/#networks
COMPOUND_USDC_COMET_MAINNET = "0xA5eD225DD425849A5252b4eB2300Fb654d12bbf0"
COMPOUND_CONFIGURATOR_MAINNET = "0x316f9708bB98af7dA9c68C1C3b5e79039cEBf305"

# Morpho Blue: https://docs.morpho.org/contracts
MORPHO_BLUE_MAINNET = "0xBBBBBbbBBb9cC5e90e3b3Af64bdAF62C37EEFFCb"
MORPHO_BUNDLER_MAINNET = "0x430BEddaE5c62E0BAd3bCb7bD4b0D84d0dE09C0f"

# --- Sepolia Testnet ---

# Aave V3 Sepolia
AAVE_V3_POOL_SEPOLIA = "0x6Ae43d3271ff6888e7Fc43Fd7321a503ff738951"
AAVE_V3_ADDRESSES_PROVIDER_SEPOLIA = "0x0496275d34753A48320b581E8DcAE8C305436b42"

# USDC token addresses
USDC_MAINNET = "0xaf88d065e77c8cC2239327C5EDb3A432268e5831"  # native USDC on Arbitrum One
USDC_SEPOLIA = "0x75faf114eafb1BDbe2F0316DF893fd58CE46AA4d"  # test USDC on Sepolia


def get_protocol_addresses(protocol: str) -> dict[str, str]:
    """Return the active set of contract addresses for the given protocol.

    Args:
        protocol: Lowercase protocol name — "aave", "compound", or "morpho".

    Returns:
        A dict of role → address for the current network.
    """
    if is_mainnet():
        return _mainnet_addresses().get(protocol, {})
    return _sepolia_addresses().get(protocol, {})


def _mainnet_addresses() -> dict[str, dict[str, str]]:
    return {
        "aave": {
            "pool": AAVE_V3_POOL_MAINNET,
            "addresses_provider": AAVE_V3_ADDRESSES_PROVIDER_MAINNET,
        },
        "compound": {
            "comet": COMPOUND_USDC_COMET_MAINNET,
            "configurator": COMPOUND_CONFIGURATOR_MAINNET,
        },
        "morpho": {
            "morpho": MORPHO_BLUE_MAINNET,
            "bundler": MORPHO_BUNDLER_MAINNET,
        },
    }


def _sepolia_addresses() -> dict[str, dict[str, str]]:
    return {
        "aave": {
            "pool": AAVE_V3_POOL_SEPOLIA,
            "addresses_provider": AAVE_V3_ADDRESSES_PROVIDER_SEPOLIA,
        },
        "compound": {},
        "morpho": {},
    }


def get_usdc_address() -> str:
    """Return USDC token address for the current network."""
    return USDC_MAINNET if is_mainnet() else USDC_SEPOLIA
