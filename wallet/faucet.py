"""Faucet guide and helper — get testnet ETH/USDC for Agent Heap."""

import json
from pathlib import Path
from web3 import Web3


RPC_URLS = {
    "arbitrum-sepolia": "https://sepolia-rollup.arbitrum.io/rpc",
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


def check_balance(chain: str = "arbitrum-sepolia") -> dict:
    """Check ETH balance on a given chain."""
    rpc = RPC_URLS.get(chain)
    if not rpc:
        return {"error": f"Unknown chain: {chain}"}

    wallet = load_wallet()
    if not wallet:
        return {"error": "No wallet found. Generate one first: python -m wallet.setup --generate"}

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
    """Print wallet status across all supported chains."""
    wallet = load_wallet()
    if not wallet:
        print("❌ No wallet found. Generate one first:")
        print("   uv run python -m wallet.setup --generate")
        return

    print(f"╔══════════════════════════════════════════╗")
    print(f"║     Agent Heap — Wallet Status           ║")
    print(f"╚══════════════════════════════════════════╝")
    print(f"\n📋 Wallet Address: {wallet['address']}")
    print(f"   Network: {wallet.get('network', 'Arbitrum Sepolia (testnet)')}")
    print()

    for chain in ["arbitrum-sepolia", "base-sepolia"]:
        result = check_balance(chain)
        if "error" in result:
            print(f"  {chain}: ❌ {result['error']}")
        else:
            eth = result["balance_eth"]
            icon = "✅" if eth > 0.001 else "⚠️"
            print(f"  {chain}: {icon} {eth:.6f} ETH")

    print()
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("  FUNDING INSTRUCTIONS")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("\n  1. Go to any faucet below and paste your wallet address")
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
