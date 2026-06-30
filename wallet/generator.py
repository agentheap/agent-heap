"""
Wallet generation and funding utilities for Agent Heap.

Generates a fresh Ethereum wallet and provides instructions for funding it
with ETH and USDC on Arbitrum One (mainnet) or Arbitrum Sepolia (testnet).
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from web3 import Web3

from chains.arbitrum import (
    ARBITRUM_CHAIN_ID,
    ARBITRUM_NETWORK,
    ARBITRUM_RPC,
    is_mainnet,
    is_sepolia,
)

# Minimum recommended funding amounts
MAINNET_MIN_ETH = 0.01      # ~$20-30 at current prices
MAINNET_MIN_USDC = 0.0      # USDC deposit is optional for first run
SEPOLIA_MIN_ETH = 0.1       # Sepolia ETH is free from faucets
SEPOLIA_MIN_USDC = 0.0

# Funding sources
MAINNET_ETH_FAUCET = "https://bridge.arbitrum.io/"
SEPOLIA_ETH_FAUCET = "https://www.alchemy.com/faucets/arbitrum-sepolia"
SEPOLIA_USDC_FAUCET = "https://faucet.circle.com/"
MAINNET_USDC_BRIDGE = "https://app.aelin.xyz/bridge"  # or any CEX/onramp


@dataclass
class GeneratedWallet:
    address: str
    private_key: str
    network: Literal["mainnet", "sepolia"]
    chain_id: int
    rpc_url: str


def generate_wallet(
    output_path: str | None = None,
) -> GeneratedWallet:
    """Generate a fresh Ethereum wallet for the active Arbitrum network.

    Args:
        output_path: Optional path to write the wallet JSON to disk.

    Returns:
        A GeneratedWallet with address, private key, and network info.

    The private key is also set as the PRIVATE_KEY env var for immediate use.
    """
    w3 = Web3()
    account = w3.eth.account.create()

    network = "mainnet" if is_mainnet() else "sepolia"

    wallet = GeneratedWallet(
        address=account.address,
        private_key=account.key.hex(),
        network=network,
        chain_id=ARBITRUM_CHAIN_ID,
        rpc_url=ARBITRUM_RPC,
    )

    # Set env var for immediate use by the agent
    os.environ["PRIVATE_KEY"] = wallet.private_key

    # Write to disk if requested
    if output_path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({
            "address": wallet.address,
            "private_key": wallet.private_key,
            "network": wallet.network,
            "chain_id": wallet.chain_id,
            "rpc_url": wallet.rpc_url,
            "created_at": __import__("datetime").datetime.now(
                __import__("datetime").timezone.utc
            ).isoformat(),
        }, indent=2))
        path.chmod(0o600)  # Only owner can read

    return wallet


def print_funding_instructions(wallet: GeneratedWallet) -> None:
    """Print human-readable funding instructions for the generated wallet."""
    if is_mainnet():
        print(f"""
╔══════════════════════════════════════════════════════════════╗
║              WALLET GENERATED — ARBITRUM ONE MAINNET        ║
╠══════════════════════════════════════════════════════════════╣
║  Address:     {wallet.address}
║  Network:     Arbitrum One (chain_id: {wallet.chain_id})
║  RPC:         {wallet.rpc_url}
║                                                              ║
║  ⚠️  YOU MUST FUND THIS WALLET BEFORE USING THE AGENT       ║
║                                                              ║
║  Minimum recommended funding:                                ║
║    • ~0.01 ETH for gas (~$25-30 at current prices)           ║
║    • Optional: USDC tokens for deposit tests                 ║
║                                                              ║
║  Ways to fund:                                               ║
║    1. Bridge ETH from Ethereum mainnet via Arbitrum Bridge   ║
║       → https://bridge.arbitrum.io/                          ║
║    2. Send ETH directly from any exchange (Coinbase, etc.)   ║
║    3. For USDC, bridge via Circle or any CEX                 ║
║                                                              ║
║  To use this wallet with the agent:                          ║
║     export PRIVATE_KEY={wallet.private_key[:10]}...{wallet.private_key[-6:]}
║     export ARBITRUM_NETWORK=mainnet                          ║
║                                                              ║
║  ⚠️  KEEP YOUR PRIVATE KEY SECURE. Never share it.          ║
║  ⚠️  This key grants full control of the wallet.            ║
╚══════════════════════════════════════════════════════════════╝
""")
    else:
        print(f"""
╔══════════════════════════════════════════════════════════════╗
║              WALLET GENERATED — ARBITRUM SEPOLIA             ║
╠══════════════════════════════════════════════════════════════╣
║  Address:     {wallet.address}
║  Network:     Arbitrum Sepolia (chain_id: {wallet.chain_id})
║  RPC:         {wallet.rpc_url}
║                                                              ║
║  Get free testnet ETH:                                       ║
║    • Alchemy Faucet: https://www.alchemy.com/faucets/arbitrum-sepolia
║    • QuickNode:      https://faucet.quicknode.com/arbitrum/sepolia
║                                                              ║
║  Get free testnet USDC:                                      ║
║    • Circle Faucet:  https://faucet.circle.com/              ║
║                                                              ║
║  To use this wallet with the agent:                          ║
║     export PRIVATE_KEY={wallet.private_key[:10]}...{wallet.private_key[-6:]}
║     export ARBITRUM_NETWORK=sepolia (default)                ║
╚══════════════════════════════════════════════════════════════╝
""")


def check_balance(rpc_url: str | None = None) -> dict:
    """Check ETH and USDC balance of the currently configured wallet.

    Reads PRIVATE_KEY from env, derives the address, and queries
    the configured Arbitrum network.

    Returns:
        dict with "eth" (in ETH) and "usdc" (human-readable) balances.
        Returns zero balances if no wallet is configured or the query fails.
    """
    private_key = os.getenv("PRIVATE_KEY")
    if not private_key:
        return {"eth": 0.0, "usdc": 0.0, "error": "No PRIVATE_KEY in environment"}

    rpc = rpc_url or ARBITRUM_RPC
    try:
        w3 = Web3(Web3.HTTPProvider(rpc))
        if not w3.is_connected():
            return {"eth": 0.0, "usdc": 0.0, "error": f"Cannot connect to {rpc}"}

        account = w3.eth.account.from_key(private_key)
        balance_wei = w3.eth.get_balance(account.address)
        eth_balance = float(w3.from_wei(balance_wei, "ether"))

        return {
            "eth": eth_balance,
            "address": account.address,
            "network": "mainnet" if is_mainnet() else "sepolia",
        }
    except Exception as e:
        return {"eth": 0.0, "usdc": 0.0, "error": str(e)}
