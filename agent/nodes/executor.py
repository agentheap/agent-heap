"""Executor node that constructs and sends deposit transactions to DeFi protocols.

Supports Aave V3, Compound III, and Morpho Blue on Arbitrum Sepolia and
Arbitrum One mainnet.  Toggle via ARBITRUM_NETWORK env var.
When PRIVATE_KEY env var is set, builds and sends real transactions.
Otherwise returns a simulated result (backward compatible).
"""

import logging
import os
from typing import Any

from chains.arbitrum import (
    ARBITRUM_CHAIN_ID,
    ARBITRUM_RPC,
    is_mainnet,
)
from risk.slippage import check_trade_allowed
from agent.nodes.abi import (
    PROTOCOL_ADDRESSES,
    USDC,
    load_aave_pool_abi,
    load_compound_comet_abi,
    load_erc20_abi,
    load_morpho_blue_abi,
)

logger = logging.getLogger(__name__)

# ── Gas safety ──────────────────────────────────────────────────────
# Apply a 20 % buffer on top of the estimated gas to prevent out-of-gas
# failures on L2 where state-dependent estimates can drift.
GAS_BUFFER_MULTIPLIER = 1.2

# ── Approve thresholds ──────────────────────────────────────────────
# Re-approve only when remaining allowance drops below this factor
# of the deposit amount to save gas.
_MIN_ALLOWANCE_FACTOR = 0.5


def execute(state: dict[str, Any]) -> dict[str, Any]:
    """Main executor entry point – called by the agent graph.

    Accepts a signal (action + protocol + pool + amount) and either
    simulates or executes the corresponding deposit transaction.
    """
    signal = state.get("signal")
    if not signal:
        return {**state, "tx_result": None}

    # Slippage gate: reject trades that would exceed max slippage.
    pool_data = {"tvl": signal.get("tvl", 0)}
    if pool_data["tvl"] > 0:
        allowed, msg = check_trade_allowed(signal, pool_data)
        if not allowed:
            return {
                **state,
                "tx_result": {
                    "simulated": True,
                    "error": msg,
                    "slippage_blocked": True,
                },
            }

    private_key = os.getenv("PRIVATE_KEY")
    if not private_key:
        return _simulate(state, signal)

    return _execute_real(state, signal, private_key)


# ── Public helpers (for testing) ────────────────────────────────────


def _simulate(state: dict[str, Any], signal: dict[str, Any]) -> dict[str, Any]:
    tx_result = {
        "simulated": True,
        "action": signal["action"],
        "protocol": signal["protocol"],
        "pool": signal["pool"],
        "amount": signal["amount"],
        "tx_hash": None,
        "gas_cost": 0,
        "reason": signal.get("reason"),
    }
    return {**state, "tx_result": tx_result}


def build_deposit_tx(
    protocol: str,
    amount_wei: int,
    sender: str,
    token_address: str | None = None,
) -> dict[str, Any] | None:
    """Build a deposit transaction dict for the given protocol.

    Returns a dict with keys ``to``, ``data``, ``value`` and
    ``description``, or ``None`` if the protocol is unknown.
    """
    if protocol == "aave":
        return _build_aave_deposit(amount_wei, sender)
    if protocol == "compound":
        return _build_compound_supply(amount_wei, token_address or sender)
    if protocol == "morpho":
        return _build_morpho_deposit(amount_wei, sender)
    logger.warning("Unknown protocol '%s'", protocol)
    return None


def build_approve_tx(
    spender: str, amount_wei: int, token_address: str
) -> dict[str, Any] | None:
    """Build an ERC-20 ``approve`` transaction.

    Returns ``None`` when the asset is native ETH (no approval needed).
    """
    if _is_native_eth(token_address):
        return None
    erc20_abi = load_erc20_abi()
    contract = _w3().eth.contract(address=token_address, abi=erc20_abi)
    data = contract.encode_abi("approve", args=[spender, amount_wei])
    return {
        "to": token_address,
        "data": data,
        "value": 0,
        "description": f"approve {spender} for {amount_wei}",
    }


# ── Protocol-specific builders ──────────────────────────────────────


def _build_aave_deposit(amount_wei: int, sender: str) -> dict[str, Any]:
    pool_addr = PROTOCOL_ADDRESSES["aave"]
    abi = load_aave_pool_abi()
    contract = _w3().eth.contract(address=pool_addr, abi=abi)
    data = contract.encode_abi(
        "deposit",
        args=[
            USDC,  # asset (auto-selects mainnet or sepolia)
            amount_wei,  # amount
            sender,  # onBehalfOf
            0,  # referralCode
        ],
    )
    return {
        "to": pool_addr,
        "data": data,
        "value": 0,
        "description": f"Aave V3 deposit {amount_wei} USDC",
    }


def _build_compound_supply(
    amount_wei: int, asset_address: str
) -> dict[str, Any]:
    comet_addr = PROTOCOL_ADDRESSES["compound"]
    abi = load_compound_comet_abi()
    contract = _w3().eth.contract(address=comet_addr, abi=abi)
    data = contract.encode_abi(
        "supply",
        args=[asset_address, amount_wei],
    )
    return {
        "to": comet_addr,
        "data": data,
        "value": 0,
        "description": f"Compound III supply {amount_wei} USDC",
    }


def _build_morpho_deposit(amount_wei: int, sender: str) -> dict[str, Any]:
    """Build a Morpho Blue ``supply`` transaction.

    Uses empty ``MarketParams`` placeholders where real parameters would
    come from an on-chain lookup or config – these must be resolved
    before the transaction is executable.
    """
    morpho_addr = PROTOCOL_ADDRESSES["morpho"]
    abi = load_morpho_blue_abi()
    contract = _w3().eth.contract(address=morpho_addr, abi=abi)

    # NOTE: MarketParams would normally be fetched from a market
    # registry or config.  The values below are placeholders that
    # illustrate the shape of the struct – real on-chain calls must
    # supply the correct loanToken, collateralToken, oracle, IRM and
    # LLTV for the specific market.
    market_params = (
        USDC,  # loanToken (auto-selects mainnet or sepolia)
        "0x0000000000000000000000000000000000000000",  # collateralToken (none)
        "0x0000000000000000000000000000000000000000",  # oracle (placeholder)
        "0x0000000000000000000000000000000000000000",  # irm (placeholder)
        0,  # lltv (0 = unset)
    )
    data = contract.encode_abi(
        "supply",
        args=[
            market_params,
            amount_wei,  # assets
            0,  # shares (0 = compute from assets)
            sender,  # onBehalf
            b"",  # data
        ],
    )
    return {
        "to": morpho_addr,
        "data": data,
        "value": 0,
        "description": f"Morpho Blue supply {amount_wei} USDC",
    }


# ── Transaction execution ───────────────────────────────────────────


def _execute_real(
    state: dict[str, Any],
    signal: dict[str, Any],
    private_key: str,
) -> dict[str, Any]:
    try:
        w3 = _w3()
        account = w3.eth.account.from_key(private_key)
        sender = account.address

        protocol: str = signal["protocol"]
        action: str = signal["action"]
        amount: float = signal["amount"]
        pool: str = signal.get("pool", "USDC")
        _token_address = USDC

        if action != "deposit":
            logger.warning("Unsupported action '%s' – simulating", action)
            return _simulate(state, signal)

        # ── Balance check (ETH for gas) ──────────────────────────────
        network_label = "mainnet" if is_mainnet() else "sepolia"
        balance_wei = w3.eth.get_balance(sender)
        balance_eth = float(w3.from_wei(balance_wei, "ether"))
        min_gas_eth = 0.002 if is_mainnet() else 0.01  # ~$4-6 on mainnet vs free on testnet
        if balance_eth < min_gas_eth:
            msg = (
                f"Insufficient ETH for gas on {network_label}: "
                f"{balance_eth:.6f} ETH (need ≥ {min_gas_eth} ETH). "
                f"Fund wallet {sender} and retry."
            )
            logger.error(msg)
            return {
                **state,
                "tx_result": {
                    "simulated": True,
                    "error": msg,
                    "action": action,
                    "protocol": protocol,
                    "pool": pool,
                    "amount": amount,
                },
            }

        amount_wei = _to_wei(w3, amount, _token_address)
        protocol_addr = PROTOCOL_ADDRESSES.get(protocol)
        if not protocol_addr:
            logger.warning("Unknown protocol '%s' – simulating", protocol)
            return _simulate(state, signal)

        # ── Approve step (token assets only, not native ETH) ──────
        if not _is_native_eth(_token_address):
            approve_tx = build_approve_tx(protocol_addr, amount_wei, _token_address)
            if approve_tx:
                _send_transaction(w3, account, approve_tx)

        # ── Deposit transaction ────────────────────────────────────
        deposit_def = build_deposit_tx(protocol, amount_wei, sender, _token_address)
        if deposit_def is None:
            return _simulate(state, signal)

        tx_hash, receipt = _send_transaction(w3, account, deposit_def)

        tx_result = {
            "simulated": False,
            "action": action,
            "protocol": protocol,
            "pool": pool,
            "amount": amount,
            "from": sender,
            "tx_hash": tx_hash.hex() if tx_hash else None,
            "gas_cost": receipt.get("gasUsed", 0) if receipt else 0,
            "block_number": receipt.get("blockNumber") if receipt else None,
            "reason": signal.get("reason"),
            "network": network_label,
        }
        return {**state, "tx_result": tx_result}

    except Exception as e:
        logger.exception("Real execution failed")
        return {
            **state,
            "tx_result": {
                "simulated": True,
                "error": str(e),
                "action": signal.get("action"),
                "protocol": signal.get("protocol"),
                "pool": signal.get("pool"),
                "amount": signal.get("amount"),
            },
        }


# ── Internal helpers ────────────────────────────────────────────────


_w3_instance = None


def _w3():
    """Lazily initialised Web3 instance (singleton per session)."""
    global _w3_instance
    if _w3_instance is None:
        from web3 import Web3

        _w3_instance = Web3(Web3.HTTPProvider(ARBITRUM_RPC))
    return _w3_instance


def _to_wei(w3, amount: float, token_address: str) -> int:
    """Convert a human-readable ``amount`` to wei for the given token."""
    if _is_native_eth(token_address):
        return w3.to_wei(amount, "ether")
    erc20_abi = load_erc20_abi()
    contract = w3.eth.contract(address=token_address, abi=erc20_abi)
    decimals = contract.functions.decimals().call()
    return int(amount * 10**decimals)


def _is_native_eth(token_address: str | None) -> bool:
    return (
        token_address is None
        or token_address == "0x0000000000000000000000000000000000000000"
        or token_address.lower()
        == "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE"
    )


def _send_transaction(w3, account, tx_def: dict[str, Any]) -> tuple[Any, dict]:
    """Sign, send and wait for a transaction receipt.

    ``tx_def`` must contain ``to``, ``data``, ``value`` and an optional
    ``description`` key (used for logging).
    """
    tx = {
        "to": tx_def["to"],
        "data": tx_def["data"],
        "value": tx_def["value"],
        "chainId": ARBITRUM_CHAIN_ID,
        "from": account.address,
        "nonce": w3.eth.get_transaction_count(account.address),
    }
    # Estimate gas, then apply 20% buffer to prevent out-of-gas on L2
    try:
        estimated = w3.eth.estimate_gas(tx)
        tx["gas"] = int(estimated * GAS_BUFFER_MULTIPLIER)
        logger.info(
            "Gas: estimated=%s buffered=%s (%.0f%% margin)",
            estimated,
            tx["gas"],
            (GAS_BUFFER_MULTIPLIER - 1) * 100,
        )
    except Exception as e:
        logger.warning("Gas estimation failed (%s), using default 500_000", e)
        tx["gas"] = 500_000

    # Fetch base fee from latest block for EIP-1559
    try:
        latest = w3.eth.get_block("latest")
        base_fee = latest.get("baseFeePerGas", 10**9)
        tx["maxPriorityFeePerGas"] = w3.to_wei(1, "gwei")
        tx["maxFeePerGas"] = base_fee + tx["maxPriorityFeePerGas"]
    except Exception:
        tx["gasPrice"] = w3.to_wei(10, "gwei")

    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    logger.info(
        "Sent %s | tx_hash=%s", tx_def.get("description", "tx"), tx_hash.hex()
    )
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
    logger.info("Confirmed block=%s", receipt.get("blockNumber"))
    return tx_hash, dict(receipt)
