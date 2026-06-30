"""Wallet setup — generates a fresh agent wallet and outputs details."""

import os
import json
from pathlib import Path

from dotenv import load_dotenv

from wallet.key_manager import KeyManager


def generate_wallet(output_path: str | None = None) -> dict:
    """Generate a fresh Ethereum wallet and optionally save to disk."""
    from eth_account import Account
    import secrets

    # Generate a random private key
    private_key = "0x" + secrets.token_hex(32)
    account = Account.from_key(private_key)

    wallet_info = {
        "address": account.address,
        "private_key": private_key,
        "network": "Arbitrum Sepolia (testnet)",
        "chain_id": 421614,
        "rpc_url": "https://sepolia-rollup.arbitrum.io/rpc",
        "notes": (
            "TESTNET WALLET — for Agent Heap testnet operations.\n"
            "Fund with testnet ETH from Arbitrum Sepolia faucet:\n"
            "  https://faucet.quicknode.com/arbitrum/sepolia\n"
            "  https://www.alchemy.com/faucets/arbitrum-sepolia\n"
            "  https://bwarelabs.com/faucets/arbitrum-sepolia\n\n"
            "Get testnet USDC on Arbitrum Sepolia via Circle faucet:\n"
            "  https://faucet.circle.com/\n"
        ),
    }

    if output_path:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(wallet_info, indent=2))
        print(f"Wallet saved to {out}")

    return wallet_info


def check_wallet_balance(rpc_url: str, address: str) -> dict:
    """Check ETH balance of a wallet on a given RPC."""
    km = KeyManager(rpc_url)
    # Use the raw Web3 instance to check balance
    from web3 import Web3
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    if not w3.is_connected():
        return {"error": f"Cannot connect to {rpc_url}"}

    balance_wei = w3.eth.get_balance(Web3.to_checksum_address(address))
    balance_eth = w3.from_wei(balance_wei, "ether")
    return {
        "address": address,
        "balance_wei": str(balance_wei),
        "balance_eth": float(balance_eth),
        "connected": True,
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Agent Heap wallet setup")
    parser.add_argument(
        "--generate",
        action="store_true",
        help="Generate a new wallet",
    )
    parser.add_argument(
        "--save",
        type=str,
        default="data/agent_wallet.json",
        help="Path to save wallet info (default: data/agent_wallet.json)",
    )
    parser.add_argument(
        "--check",
        type=str,
        help="Check balance of an address (provide address or 'saved' to load from file)",
    )
    parser.add_argument(
        "--rpc",
        type=str,
        default="https://sepolia-rollup.arbitrum.io/rpc",
        help="RPC URL to check balance against",
    )
    args = parser.parse_args()

    if args.generate:
        print("=== Generating Agent Wallet ===")
        wallet = generate_wallet(args.save)
        print(f"Address:     {wallet['address']}")
        print(f"Private Key: {wallet['private_key']}")
        print(f"Network:     {wallet['network']}")
        print()
        print("NEXT STEPS:")
        print(f"1. Fund with testnet ETH from: {wallet['rpc_url']}")
        print("   Faucets: https://faucet.quicknode.com/arbitrum/sepolia")
        print("2. Set PRIVATE_KEY in .env to this wallet's private key")
        print("3. Run with --check saved to verify funding")

    elif args.check:
        load_dotenv()
        address = args.check
        if address == "saved":
            try:
                with open(args.save) as f:
                    wallet = json.load(f)
                address = wallet["address"]
                print(f"Loaded address from {args.save}")
            except FileNotFoundError:
                print(f"Error: {args.save} not found. Generate a wallet first.")
                exit(1)

        result = check_wallet_balance(args.rpc, address)
        if "error" in result:
            print(f"Error: {result['error']}")
        else:
            print(f"Address: {result['address']}")
            print(f"Balance: {result['balance_eth']} ETH")
            print(f"Connected: {result['connected']}")

    else:
        parser.print_help()
