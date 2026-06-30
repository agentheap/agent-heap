"""$HEAP token deployment on Base.

Modes:
  --testnet    Deploy ERC20 directly on Base Sepolia (free, for testing)
  --mainnet    Deploy via Clanker SDK on Base mainnet (needs real ETH)
  --clanker    Deploy via Clanker REST API (needs API key)
"""

import os
from pathlib import Path
from typing import Any

import click
import httpx
from dotenv import load_dotenv
from rich.console import Console

load_dotenv()
console = Console()

# ── Token config ─────────────────────────────────────────────────────

HEAP_CONFIG = {
    "name": "Agent Heap",
    "symbol": "HEAP",
    "description": "Multi-chain yield optimization AI agent token.",
    "initial_supply": 1_000_000_000,  # 1B
    "decimals": 18,
    "social": {
        "website": "https://agentheap.ai",
        "twitter": "https://x.com/agentheap",
        "telegram": "https://t.me/agentheap",
    },
}

CHAIN_CONFIG = {
    "testnet": {
        "name": "Base Sepolia",
        "rpc": "https://sepolia.base.org",
        "chain_id": 84532,
        "explorer": "https://sepolia.basescan.org",
        "gas_multiplier": 1.2,
    },
    "mainnet": {
        "name": "Base",
        "rpc": "https://mainnet.base.org",
        "chain_id": 8453,
        "explorer": "https://basescan.org",
        "gas_multiplier": 1.1,
    },
}

CLANKER_API = "https://www.clanker.world/api/tokens/deploy"
SOL_PATH = Path(__file__).parent / "HEAP.sol"


# ── Direct deploy (testnet + mainnet) ────────────────────────────────

def compile_and_deploy(
    private_key: str, network: str = "testnet"
) -> dict[str, Any]:
    """Compile HEAP.sol and deploy via web3.py."""
    from web3 import Web3
    from web3.middleware import ExtraDataToPOAMiddleware

    chain = CHAIN_CONFIG[network]
    w3 = Web3(Web3.HTTPProvider(chain["rpc"]))
    w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

    if not w3.is_connected():
        return {"status": "error", "error": f"Cannot connect to {chain['name']}"}

    account = w3.eth.account.from_key(private_key)
    admin = account.address
    bal = w3.eth.get_balance(admin)
    console.print(f"  Deployer:  {admin}")
    console.print(f"  Balance:   {bal / 1e18:.6f} ETH")
    console.print(f"  Network:   {chain['name']}")
    console.print(f"  Chain ID:  {chain['chain_id']}")

    if bal == 0:
        return {"status": "error", "error": f"Wallet has 0 ETH on {chain['name']}. Get free test ETH from a faucet first."}

    if not SOL_PATH.exists():
        return {"status": "error", "error": "HEAP.sol not found at heap_token/HEAP.sol"}

    # ── Compile ───────────────────────────────────────────────────
    console.print("\n[blue]Compiling HEAP.sol...[/blue]")
    from solcx import compile_source
    compiled = compile_source(
        SOL_PATH.read_text(),
        output_values=["abi", "bin"],
        solc_version="0.8.28",
    )
    contract_id, contract_data = list(compiled.items())[0]

    abi = contract_data["abi"]
    bytecode = contract_data["bin"]

    console.print(f"  Contract:  {contract_id}")
    console.print(f"  Bytecode:  {len(bytecode)} hex chars")

    # ── Deploy ────────────────────────────────────────────────────
    console.print("\n[blue]Deploying $HEAP...[/blue]")
    Heaps = w3.eth.contract(abi=abi, bytecode=bytecode)

    fee = w3.eth.fee_history(1, "latest")
    base_fee = fee["baseFeePerGas"][-1]
    priority = w3.eth.max_priority_fee
    max_fee = int((base_fee + priority) * chain["gas_multiplier"])

    tx = Heaps.constructor(admin, True).build_transaction({
        "from": admin,
        "nonce": w3.eth.get_transaction_count(admin),
        "gas": 3_000_000,
        "maxFeePerGas": max_fee,
        "maxPriorityFeePerGas": priority,
    })

    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    console.print(f"  Tx sent:   {tx_hash.hex()}")
    console.print("  Waiting for confirmation...")

    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

    if receipt["status"] != 1:
        return {"status": "error", "error": "Transaction reverted", "tx_hash": tx_hash.hex()}

    token_address = receipt["contractAddress"]
    console.print(f"\n[green]✅ $HEAP deployed![/green]")
    console.print(f"   Address:  {token_address}")
    console.print(f"   Explorer: {chain['explorer']}/address/{token_address}")
    console.print(f"   Gas used: {receipt['gasUsed']}")

    return {
        "status": "success",
        "network": network,
        "token_address": token_address,
        "tx_hash": tx_hash.hex(),
        "admin": admin,
        "explorer_url": f"{chain['explorer']}/address/{token_address}",
    }


# ── Clanker API deploy ───────────────────────────────────────────────

def deploy_via_clanker(api_key: str, admin_address: str) -> dict[str, Any]:
    """Deploy $HEAP via Clanker's REST API."""
    body = {
        "token": {
            "name": HEAP_CONFIG["name"],
            "symbol": HEAP_CONFIG["symbol"],
            "tokenAdmin": admin_address,
            "description": HEAP_CONFIG["description"],
            "socialMediaUrls": [
                {"platform": "website", "url": HEAP_CONFIG["social"]["website"]},
                {"platform": "twitter", "url": HEAP_CONFIG["social"]["twitter"]},
                {"platform": "telegram", "url": HEAP_CONFIG["social"]["telegram"]},
            ],
            "requestKey": _make_request_key(),
        },
        "rewards": [
            {
                "recipient": admin_address,
                "admin": admin_address,
                "bps": 10_000,
                "token": "Both",
            }
        ],
    }

    console.print("[blue]Deploying $HEAP via Clanker API...[/blue]")

    try:
        resp = httpx.post(
            CLANKER_API,
            json=body,
            headers={"x-api-key": api_key, "Content-Type": "application/json"},
            timeout=60,
        )
        resp.raise_for_status()
        result = resp.json()
        console.print(f"[green]✅ Deployed![/green]")
        console.print(f"   Token: {result.get('token', {}).get('address', 'pending')}")
        console.print(f"   Tx:    {result.get('txHash', 'pending')}")
        return result
    except httpx.HTTPStatusError as e:
        console.print(f"[red]Clanker error: {e.response.status_code} — {e.response.text}[/red]")
        return {"status": "error", "error": str(e)}
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return {"status": "error", "error": str(e)}


# ── Helpers ──────────────────────────────────────────────────────────

def _make_request_key() -> str:
    import hashlib, uuid
    return hashlib.sha256(uuid.uuid4().hex.encode()).hexdigest()[:32]


# ── CLI ──────────────────────────────────────────────────────────────

@click.command()
@click.option("--testnet", is_flag=True, help="Deploy on Base Sepolia (free)")
@click.option("--mainnet", is_flag=True, help="Deploy on Base mainnet via Clanker SDK")
@click.option("--clanker", is_flag=True, help="Deploy via Clanker REST API")
@click.option("--admin", default=None, help="Admin address (for Clanker deploy)")
def deploy_heap(
    testnet: bool = False,
    mainnet: bool = False,
    clanker: bool = False,
    admin: str | None = None,
) -> dict[str, Any] | None:
    """Deploy the $HEAP token.

    Start with --testnet (free on Base Sepolia) to test everything
    before launching on mainnet.
    """
    if not any([testnet, mainnet, clanker]):
        click.echo()
        console.print("[bold]Agent Heap — $HEAP Token Deploy[/bold]")
        console.print(f"  Name:    {HEAP_CONFIG['name']}")
        console.print(f"  Symbol:  ${HEAP_CONFIG['symbol']}")
        console.print(f"  Supply:  {HEAP_CONFIG['initial_supply']:,}")
        click.echo()
        console.print("Options:")
        console.print("  1) [cyan]--testnet[/cyan]   Base Sepolia (free, for testing)")
        console.print("  2) [cyan]--mainnet[/cyan]   Base mainnet via Clanker SDK")
        console.print("  3) [cyan]--clanker[/cyan]   Base mainnet via Clanker API")
        click.echo()
        if click.confirm("Deploy on testnet (Base Sepolia)?", default=True):
            testnet = True
        elif click.confirm("Deploy on mainnet via Clanker SDK?"):
            mainnet = True
        else:
            clanker = True

    private_key = os.getenv("WALLET_PRIVATE_KEY") or os.getenv("PRIVATE_KEY")

    if testnet:
        if not private_key:
            console.print("[red]❌ WALLET_PRIVATE_KEY not set in .env[/red]")
            return None
        return compile_and_deploy(private_key, network="testnet")

    if mainnet:
        if not private_key:
            console.print("[red]❌ WALLET_PRIVATE_KEY not set in .env[/red]")
            return None
        return compile_and_deploy(private_key, network="mainnet")

    if clanker:
        api_key = os.getenv("CLANKER_API_KEY")
        if not api_key:
            console.print("[red]❌ CLANKER_API_KEY not set in .env[/red]")
            return None
        admin = admin or os.getenv("TOKEN_ADMIN")
        if not admin:
            console.print("[red]❌ --admin or TOKEN_ADMIN required[/red]")
            return None
        return deploy_via_clanker(api_key, admin)

    return None
