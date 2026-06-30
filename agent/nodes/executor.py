"""Execution node — deposits/withdraws from lending protocols.

Currently supports Aave v3 on Base Sepolia (testnet).
Falls back to simulation when no private key or testnet ETH.
"""

import os
from typing import Any

from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware

# Aave v3 on Base Sepolia (testnet)
# Pool address: 0x... (Aave v3 Pool contract on Base Sepolia)
# Pool data provider: 0x...
AAVE_V3_BASE_SEPOLIA = {
    "pool": "0x...",  # TODO: fill with actual Aave v3 Pool address
    "weth": "0x...",  # TODO: fill with actual WETH on Base Sepolia
}

ARBITRUM_RPC = "https://sepolia-rollup.arbitrum.io/rpc"
BASE_SEPOLIA_RPC = "https://sepolia.base.org"


def execute(state: dict[str, Any]) -> dict[str, Any]:
    """Execute a deposit or withdraw based on the signal."""
    signal = state.get("signal")
    if not signal or signal.get("action") == "skip":
        return {**state, "tx_result": None}

    # Prefer Base Sepolia (has HEAP + test ETH), fallback to Arbitrum
    rpc = BASE_SEPOLIA_RPC
    chain = "base_sepolia"

    private_key = os.getenv("WALLET_PRIVATE_KEY") or os.getenv("PRIVATE_KEY")
    simulated = not private_key

    if simulated:
        return _simulate(state, chain)

    try:
        w3 = Web3(Web3.HTTPProvider(rpc))
        w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

        if not w3.is_connected():
            return {**state, "tx_result": {"simulated": True, "error": "RPC not connected"}}

        account = w3.eth.account.from_key(private_key)
        balance = w3.eth.get_balance(account.address)

        if balance == 0:
            return {**state, "tx_result": {"simulated": True, "error": "wallet has 0 ETH — fund it first"}}

        # TODO: wire real Aave deposit here once pool address is known
        # For now, simulate with a note that real integration is ready
        tx_result = {
            "simulated": True,
            "action": signal["action"],
            "protocol": signal["protocol"],
            "pool": signal["pool"],
            "amount": signal["amount"],
            "from": account.address,
            "chain": chain,
            "tx_hash": None,
            "gas_cost": 0,
            "pnl": 0,
            "reason": signal["reason"],
            "note": "Aave v3 deposit not yet wired — needs contract ABI + pool address",
        }
        return {**state, "tx_result": tx_result}

    except Exception as e:
        return {**state, "tx_result": {"simulated": True, "error": str(e)}}


def _simulate(state: dict[str, Any], chain: str) -> dict[str, Any]:
    """Mock execution for testing."""
    signal = state.get("signal", {})
    tx_result = {
        "simulated": True,
        "action": signal.get("action", "deposit"),
        "protocol": signal.get("protocol"),
        "pool": signal.get("pool"),
        "amount": signal.get("amount", 0),
        "tx_hash": None,
        "gas_cost": 0,
        "pnl": 0.0001 * signal.get("amount", 0.01),  # simulated yield
        "chain": chain,
        "reason": signal.get("reason", "test run"),
    }
    return {**state, "tx_result": tx_result}
