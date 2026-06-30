"""Faucet guide and helper — get testnet ETH/USDC or mainnet funding for Agent Heap.

Respects the ARBITRUM_NETWORK env var ("sepolia" or "mainnet") to determine
which network to show instructions for.
"""

import json
from pathlib import Path
from web3 import Web3

from chains.arbitrum import ARBITRUM_RPC, is_mainnet


RPC_URLS = {
    "arbitrum-sepolia": "https://sepolia-rollup.arbitrum.io/rpc",
    "arbitrum-one": "https://arb1.arbitrum.io/rpc",
    "base-sepolia": "https://sepolia.base.org",
}

FAUCET_LINKS = {
    "arbitrum-sepolia": [
        ("QuickNode", "https://faucet.quicknode.com/arbitrum/sepolia"),
        ("Alchemy", "https://www.alchemy.com/faucets/arbitrum-sepolia"),
        ("Chainlink", "https://faucets.chain.link/arbitrum-sepolia"),
        ("GetBlock", "https://getblock.io/faucet/arb-sepolia/"),
        ("Bware Labs", "https://bwarelabs.com/faucets"),
    ],
    "base-sepolia": [
        ("Coinbase CDP", "https://docs.cdp.coinbase.com/faucets/docs/quickstart"),
        ("Chainlink", "https://faucets.chain.link/base-sepolia"),
        ("Alchemy", "https://www.alchemy.com/faucets/base-sepolia"),
        ("QuickNode", "https://faucet.quicknode.com/base/sepolia"),
    ],
}

USDC_FAUCETS = [
    ("Circle Testnet Faucet", "https://faucet.circle.com/"),
]

WALLET_PATH = Path("data/agent_wallet.json")


def load_wallet() -> dict | None:
    """Load the generated wallet from disk."""
    if not WALLET_PATH.exists():
        return None
    return json.loads(WALLET_PATH.read_text())


def check_balance(chain: str | None = None) -> dict:
    """Check ETH balance of the configured wallet on the configured network."""
    if chain is None:
        chain = "arbitrum-one" if is_mainnet() else "arbitrum-sepolia"
    rpc = RPC_URLS.get(chain)
    if not rpc:
        return {"error": f"Unknown chain: {chain}"}

    wallet = load_wallet()
    if not wallet:
        return {
            "error": (
                "No wallet found. Generate one first:\n"
                "  uv run python -m wallet.setup --generate   (testnet, default)\n"
                "  ARBITRUM_NETWORK=mainnet uv run python -m wallet.setup --generate   (mainnet)"
            )
        }

    w3 = Web3(Web3.HTTPProvider(rpc))
    if not w3.is_connected():
        return {"error": f"Cannot connect to {rpc}"}

    address = Web3.to_checksum_address(wallet["address"])
    balance_wei = w3.eth.get_balance(address)
    balance_eth = w3.from_wei(balance_wei, "ether")

    return {
        "chain": chain,
        "address": wallet["address"],
        "balance_eth": float(balance_eth),
        "balance_wei": str(balance_wei),
        "connected": True,
    }


def print_status():
    """Print wallet status and funding instructions for the active network."""
    wallet = load_wallet()
    if not wallet:
        print("❌ No wallet found. Generate one first:")
        print("   uv run python -m wallet.setup --generate")
        return

    print(f"╔══════════════════════════════════════════╗")
    print(f"║     Agent Heap — Wallet Status           ║")
    print(f"╚══════════════════════════════════════════╝")
    print(f"\n📋 Wallet Address: {wallet['address']}")
    print(f"   Network: {wallet.get('network', 'Unknown')}")
    print()

    if is_mainnet():
        result = check_balance("arbitrum-one")
        if "error" in result:
            print(f"  Arbitrum One: ❌ {result['error']}")
        else:
            eth = result["balance_eth"]
            icon = "✅" if eth > 0.001 else "⚠️"
            print(f"  Arbitrum One: {icon} {eth:.6f} ETH")

        print()
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("  MAINNET FUNDING INSTRUCTIONS")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"\n  ⚠️  THIS IS REAL MONEY. Be careful!")
        print()
        print(f"  To fund your wallet, send ETH and USDC to:")
        print(f"  {wallet['address']}")
        print()
        print("  1. Buy ETH on any exchange (Coinbase, Binance, Kraken)")
        print("  2. Withdraw to the Arbitrum One network (not Ethereum L1)")
        print(f"  Minimum: ~0.01 ETH for gas + USDC for deposits")
        print()
        print("  After funding, run:")
        print("    uv run python -m wallet.faucet")
    else:
        for chain_name in ["arbitrum-sepolia", "base-sepolia"]:
            result = check_balance(chain_name)
            if "error" in result:
                print(f"  {chain_name}: ❌ {result['error']}")
            else:
                eth = result["balance_eth"]
                icon = "✅" if eth > 0.001 else "⚠️"
                print(f"  {chain_name}: {icon} {eth:.6f} ETH")

        print()
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("  FUNDING INSTRUCTIONS (TESTNET)")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"\n  1. Go to any faucet below and paste your wallet address")
        print(f"     Address: {wallet['address']}")
        print()
        print("  2. Arbitrum Sepolia faucets (ETH for gas):")
        for name, url in FAUCET_LINKS["arbitrum-sepolia"]:
            print(f"     • {name}: {url}")
        print()
        print("  3. Base Sepolia faucets (ETH for gas):")
        for name, url in FAUCET_LINKS["base-sepolia"]:
            print(f"     • {name}: {url}")
        print()
        print("  4. USDC faucets:")
        for name, url in USDC_FAUCETS:
            print(f"     • {name}: {url}")
        print()
        print("  5. After funding, run this again to verify:")
        print("     uv run python -m wallet.faucet")
        print()


if __name__ == "__main__":
    print_status()
