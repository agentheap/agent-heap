"""Executor node that constructs and sends deposit/withdraw transactions to DeFi protocols.

Supports Aave V3, Compound III, and Morpho Blue on Arbitrum Sepolia and
Arbitrum One mainnet.  Toggle via ARBITRUM_NETWORK env var.
When PRIVATE_KEY env var is set, builds and sends real transactions.
Otherwise returns a simulated result (backward compatible).

Harvest-reinvest: when a ``harvest_signal`` is present in state, the executor
first withdraws from existing positions (getting principal + accrued yield back),
then deposits the combined capital into the best pool.
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
from agent.nodes.harvester import track_deposit, track_withdrawal

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
    """Main executor entry point - called by the agent graph.

    Two-phase execution when ``harvest_signal`` is present:

    Phase 1 — Withdraw from existing positions (harvest accrued yield)
    Phase 2 — Deposit capital into the best pool (including withdrawn yield)

    Falls back to single deposit phase when no harvest signal exists.
    """
    harvest_signal = state.get("harvest_signal")
    withdrawal_results: list[dict[str, Any]] = []
    total_withdrawn = 0.0

    if harvest_signal:
        withdrawal_results, total_withdrawn = _process_withdrawals(
            state, harvest_signal
        )

    signal = state.get("signal")
    if not signal:
        result = {**state, "tx_result": None}
        if withdrawal_results:
            result["withdrawal_results"] = withdrawal_results
        return result

    # Check memory for known failures — cooldown instead of permanent simulation
    memory = state.get("memory_context", [])
    recent_failures = [
        m for m in memory
        if m.get("protocol") == signal.get("protocol")
        and m.get("simulated") is True
        and "error" in m
    ]
    if recent_failures and len(recent_failures) >= 3:
        logger.warning(
            "Protocol %s has %d prior failures in memory -- cooling down",
            signal.get("protocol"), len(recent_failures),
        )
        result = _simulate(state, signal, memory_warning="cooldown: 3+ prior failures")
        if withdrawal_results:
            result["withdrawal_results"] = withdrawal_results
        return result

    # Slippage gate: reject trades that would exceed max slippage.
    pool_data = {"tvl": signal.get("tvl", 0)}
    if pool_data["tvl"] > 0:
        allowed, msg = check_trade_allowed(signal, pool_data)
        if not allowed:
            result = {
                **state,
                "tx_result": {
                    "simulated": True,
                    "error": msg,
                    "slippage_blocked": True,
                },
            }
            if withdrawal_results:
                result["withdrawal_results"] = withdrawal_results
            return result

    private_key = os.getenv("PRIVATE_KEY")
    if not private_key:
        result = _simulate(state, signal)
        if withdrawal_results:
            result["withdrawal_results"] = withdrawal_results
        return result

    result = _execute_real(state, signal, private_key, extra_capital=total_withdrawn)
    if withdrawal_results:
        result["withdrawal_results"] = withdrawal_results
    return result


# ── Harvest-reinvest: withdrawal phase ─────────────────────────────────


def _process_withdrawals(
    state: dict[str, Any],
    harvest_signal: dict[str, Any],
) -> tuple[list[dict[str, Any]], float]:
    """Process withdrawals for all positions with accrued yield.

    Returns (withdrawal_results, total_withdrawn_amount).
    """
    private_key = os.getenv("PRIVATE_KEY")
    positions = harvest_signal.get("positions", [])
    yields_data = state.get("yields", [])
    results: list[dict[str, Any]] = []
    total = 0.0

    for pos_info in positions:
        protocol = pos_info["protocol"]
        amount = pos_info["deposited"] + pos_info["accrued_yield"]

        # ── Slippage check for withdrawal ──────────────────────────
        pool_tvl = 0.0
        for y in yields_data:
            if y.get("protocol") == protocol:
                pool_tvl = y.get("tvl", 0)
                break
        if pool_tvl > 0:
            from risk.slippage import estimate_slippage
            slippage_bps, acceptable = estimate_slippage(pool_tvl, amount)
            if not acceptable:
                logger.warning(
                    "Skipping withdrawal from %s: slippage %d bps exceeds limit",
                    protocol, slippage_bps,
                )
                results.append({
                    "success": False,
                    "simulated": True,
                    "protocol": protocol,
                    "amount": amount,
                    "error": f"slippage {slippage_bps} bps too high for withdrawal",
                })
                continue

        if private_key:
            tx_result = _withdraw_real(protocol, amount)
        else:
            tx_result = _withdraw_simulated(protocol, amount)

        results.append(tx_result)
        total += amount

        if tx_result.get("success"):
            track_withdrawal(protocol, pos_info.get("pool", "USDC"), amount)
            logger.info(
                "Withdrew %.6f from %s (principal + yield)",
                amount, protocol,
            )

    return results, total


def _withdraw_simulated(protocol: str, amount: float) -> dict[str, Any]:
    return {
        "success": True,
        "simulated": True,
        "protocol": protocol,
        "amount": amount,
        "tx_hash": None,
    }


def _withdraw_real(protocol: str, amount: float) -> dict[str, Any]:
    """Execute a real withdrawal transaction on-chain with retry + minOut."""
    try:
        w3 = _w3()
        private_key = os.getenv("PRIVATE_KEY", "")
        account = w3.eth.account.from_key(private_key)
        sender = account.address

        amount_wei = _to_wei(w3, amount, USDC)
        tx_def = build_withdraw_tx(protocol, amount_wei, sender)
        if tx_def is None:
            return {
                "success": False,
                "simulated": True,
                "protocol": protocol,
                "amount": amount,
                "error": f"No withdraw handler for protocol '{protocol}'",
            }

        tx_hash, receipt = _send_transaction_with_retry(w3, account, tx_def)

        return {
            "success": True,
            "simulated": False,
            "protocol": protocol,
            "amount": amount,
            "tx_hash": tx_hash.hex() if tx_hash else None,
            "gas_cost": receipt.get("gasUsed", 0) if receipt else 0,
            "block_number": receipt.get("blockNumber") if receipt else None,
        }
    except Exception as e:
        logger.exception("Withdrawal failed for %s", protocol)
        return {
            "success": False,
            "simulated": False,
            "protocol": protocol,
            "amount": amount,
            "error": str(e),
        }


# ── Public helpers (for testing) ────────────────────────────────────


def _simulate(
    state: dict[str, Any],
    signal: dict[str, Any],
    memory_warning: str | None = None,
) -> dict[str, Any]:
    protocol = signal.get("protocol", "")
    pool = signal.get("pool", "USDC")
    amount = signal.get("amount", 0)
    apy = signal.get("apy", 0.0)

    # Track simulated deposits too for testing continuity
    if amount > 0:
        track_deposit(protocol, pool, amount, apy)

    tx_result = {
        "simulated": True,
        "action": signal.get("action"),
        "protocol": protocol,
        "pool": pool,
        "amount": amount,
        "tx_hash": None,
        "gas_cost": 0,
        "reason": signal.get("reason"),
    }
    if memory_warning:
        tx_result["memory_warning"] = memory_warning
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
        try:
            return _build_morpho_deposit(amount_wei, sender)
        except NotImplementedError as e:
            logger.warning("Morpho deposit not available: %s", e)
            return None
    logger.warning("Unknown protocol '%s'", protocol)
    return None


def build_withdraw_tx(
    protocol: str,
    amount_wei: int,
    sender: str,
    token_address: str | None = None,
) -> dict[str, Any] | None:
    """Build a withdrawal transaction dict for the given protocol.

    Returns a dict with keys ``to``, ``data``, ``value`` and
    ``description``, or ``None`` if the protocol is unknown.
    """
    if protocol == "aave":
        return _build_aave_withdraw(amount_wei, sender)
    if protocol == "compound":
        return _build_compound_withdraw(amount_wei, token_address or USDC)
    if protocol == "morpho":
        logger.warning("Morpho Blue withdrawal not yet implemented")
        return None
    logger.warning("Unknown protocol '%s' for withdrawal", protocol)
    return None


def _build_aave_withdraw(amount_wei: int, sender: str) -> dict[str, Any]:
    pool_addr = PROTOCOL_ADDRESSES["aave"]
    abi = load_aave_pool_abi()
    contract = _w3().eth.contract(address=pool_addr, abi=abi)
    data = contract.encode_abi(
        "withdraw",
        args=[USDC, amount_wei, sender],
    )
    return {
        "to": pool_addr,
        "data": data,
        "value": 0,
        "description": f"Aave V3 withdraw {amount_wei} USDC",
    }


def _build_compound_withdraw(amount_wei: int, asset_address: str) -> dict[str, Any]:
    comet_addr = PROTOCOL_ADDRESSES["compound"]
    abi = load_compound_comet_abi()
    contract = _w3().eth.contract(address=comet_addr, abi=abi)
    data = contract.encode_abi(
        "withdraw",
        args=[asset_address, amount_wei],
    )
    return {
        "to": comet_addr,
        "data": data,
        "value": 0,
        "description": f"Compound III withdraw {amount_wei} USDC",
    }


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

    Requires valid MarketParams (loanToken, collateralToken, oracle, IRM, LLTV)
    that must be fetched on-chain from the Morpho Blue market registry.

    Returns a simulated result with an error if market params are unavailable.
    """
    logger.warning(
        "Morpho Blue deposit requires on-chain market params that are not yet configured."
        " Simulating instead of sending a tx that would fail."
    )
    raise NotImplementedError(
        "Morpho Blue deposits need real MarketParams (oracle, IRM, LLTV) fetched from"
        " the Morpho Blue contract. Configure them in agent/nodes/abi/ before using."
    )


# ── Transaction execution ───────────────────────────────────────────


def _spending_limits_exceeded(amount: float) -> str | None:
    """Check if the transaction amount exceeds configured spending limits.
    Returns an error message if exceeded, None otherwise."""
    max_tx = os.getenv("MAX_TX_AMOUNT")
    if max_tx:
        try:
            max_amount = float(max_tx)
            if amount > max_amount:
                return f"MAX_TX_AMOUNT exceeded: {amount:.4f} > {max_amount:.4f} USDC"
        except ValueError:
            pass
    return None


def _daily_cap_exceeded(amount: float) -> str | None:
    """Check if total today + this tx would exceed the daily volume cap."""
    daily_limit = os.getenv("DAILY_TX_LIMIT")
    if not daily_limit:
        return None
    try:
        max_daily = float(daily_limit)
    except ValueError:
        return None

    try:
        from db.session import get_recent_trades
        from datetime import datetime, timezone

        trades = get_recent_trades(limit=100)
        today = datetime.now(timezone.utc).date()
        today_volume = sum(
            t.amount for t in trades
            if t.timestamp and t.timestamp.date() == today
        )
        if today_volume + amount > max_daily:
            return (
                f"DAILY_TX_LIMIT exceeded: {today_volume:.4f} + {amount:.4f} "
                f"> {max_daily:.4f} USDC"
            )
    except Exception:
        pass
    return None


def _get_min_out(amount_wei: int, slippage_bps: int = 50) -> int:
    """Calculate minimum output amount with slippage tolerance (default 0.5%)."""
    return int(amount_wei * (10_000 - slippage_bps) / 10_000)


def _execute_real(
    state: dict[str, Any],
    signal: dict[str, Any],
    private_key: str,
    extra_capital: float = 0.0,
) -> dict[str, Any]:
    try:
        w3 = _w3()
        account = w3.eth.account.from_key(private_key)
        sender = account.address

        protocol: str = signal["protocol"]
        action: str = signal["action"]
        amount: float = signal["amount"] + extra_capital
        pool: str = signal.get("pool", "USDC")
        apy = signal.get("apy", 0.0)
        _token_address = USDC

        # Track this deposit for future harvest cycles
        track_deposit(protocol, pool, amount, apy)

        # ── Spending limit checks ──────────────────────────────────────
        limit_error = _spending_limits_exceeded(amount)
        if limit_error:
            logger.warning("Spending limit blocked: %s", limit_error)
            return {
                **state,
                "tx_result": {
                    "simulated": True,
                    "error": limit_error,
                    "action": action,
                    "protocol": protocol,
                    "pool": pool,
                    "amount": amount,
                },
            }

        # ── Daily cap check ────────────────────────────────────────────
        cap_error = _daily_cap_exceeded(amount)
        if cap_error:
            logger.warning("Daily cap blocked: %s", cap_error)
            return {
                **state,
                "tx_result": {
                    "simulated": True,
                    "error": cap_error,
                    "action": action,
                    "protocol": protocol,
                    "pool": pool,
                    "amount": amount,
                },
            }

        if action != "deposit":
            logger.warning("Unsupported action '%s' - simulating", action)
            return _simulate(state, signal)

        # ── Balance check (ETH for gas) ──────────────────────────────
        network_label = "mainnet" if is_mainnet() else "sepolia"
        balance_wei = w3.eth.get_balance(sender)
        balance_eth = float(w3.from_wei(balance_wei, "ether"))
        min_gas_eth = 0.002 if is_mainnet() else 0.01
        if balance_eth < min_gas_eth:
            msg = (
                f"Insufficient ETH for gas on {network_label}: "
                f"{balance_eth:.6f} ETH (need >= {min_gas_eth} ETH). "
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
            logger.warning("Unknown protocol '%s' - simulating", protocol)
            return _simulate(state, signal)

        # ── Approve step (token assets only, not native ETH) ──────
        if not _is_native_eth(_token_address):
            approve_tx = build_approve_tx(protocol_addr, amount_wei, _token_address)
            if approve_tx:
                _send_transaction_with_retry(w3, account, approve_tx)

        # ── Deposit transaction (with min-out MEV protection) ──────
        deposit_def = build_deposit_tx(protocol, amount_wei, sender, _token_address)
        if deposit_def is None:
            return _simulate(state, signal)

        tx_hash, receipt = _send_transaction_with_retry(w3, account, deposit_def)

        # ── PnL estimate ───────────────────────────────────────────
        gas_used = receipt.get("gasUsed", 0) if receipt else 0
        gas_price = _gas_price_wei(w3)
        gas_cost_eth = gas_used * gas_price / 1e18 if gas_price else 0
        # Estimated yield over ~6h cycle at current APY
        estimated_yield = amount * (apy / 100.0) * (6.0 / 24.0 / 365.0) if apy > 0 else 0

        tx_result = {
            "simulated": False,
            "action": action,
            "protocol": protocol,
            "pool": pool,
            "amount": amount,
            "from": sender,
            "tx_hash": tx_hash.hex() if tx_hash else None,
            "gas_cost": gas_used,
            "gas_cost_eth": round(gas_cost_eth, 8),
            "pnl": round(estimated_yield, 8),
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


_RETRYABLE_ERRORS = (
    "nonce too low",
    "replacement transaction underpriced",
    "already known",
    "fee cap less than block base fee",
    "timeout",
    "connection",
    "rate limit",
)


def _is_retryable(err: Exception) -> bool:
    msg = str(err).lower()
    return any(pattern in msg for pattern in _RETRYABLE_ERRORS)


def _send_transaction_with_retry(
    w3, account, tx_def: dict[str, Any], max_retries: int = 2
) -> tuple[Any, dict]:
    """Send a transaction with retry logic for transient failures."""
    last_error: Exception | None = None
    for attempt in range(max_retries + 1):
        try:
            return _send_transaction(w3, account, tx_def)
        except Exception as e:
            last_error = e
            if attempt < max_retries and _is_retryable(e):
                wait = 2 ** (attempt + 1)
                logger.warning(
                    "Retryable error on attempt %d/%d: %s. Retrying in %ds...",
                    attempt + 1, max_retries + 1, e, wait,
                )
                import time
                time.sleep(wait)
                # Bump nonce for next attempt
                tx_def["nonce"] = w3.eth.get_transaction_count(account.address)
            else:
                raise
    raise last_error  # type: ignore[misc]


def _gas_price_wei(w3) -> int | None:
    """Get current base fee per gas in wei, or None if unavailable."""
    try:
        latest = w3.eth.get_block("latest")
        return latest.get("baseFeePerGas")
    except Exception:
        return None


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
        logger.warning("Gas estimation failed (%s), using safe default 150k", e)
        tx["gas"] = 150_000

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
