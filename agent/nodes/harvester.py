"""Harvester node — tracks deposits, estimates accrued yield, produces withdrawal signals.

The harvester runs before the collector in the LangGraph pipeline. It:

1. Reads tracked positions from a local JSON ledger
2. Fetches current yields to estimate accrued interest since deposit
3. If accrued yield > MIN_HARVEST_THRESHOLD, emits a withdrawal signal
4. The withdrawn yield becomes available for re-deposit in the current cycle

This implements the harvest-reinvest pattern: yield is claimed, then the
analyzer/signaler/executor pipeline deposits it back into the best pool.
"""

import json
import logging
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

MIN_HARVEST_THRESHOLD = float(os.getenv("MIN_HARVEST_THRESHOLD", "0.50"))  # $0.50


def _positions_path() -> str:
    """Return the positions file path, evaluating env var at call time."""
    return os.getenv("AGENT_POSITIONS_FILE", "./.agent_positions.json")


@dataclass
class Position:
    protocol: str
    pool: str
    amount: float
    deposited_at: str  # ISO 8601
    apy_at_deposit: float = 0.0

    def elapsed_days(self) -> float:
        deposited = datetime.fromisoformat(self.deposited_at)
        elapsed = datetime.now(timezone.utc) - deposited.replace(tzinfo=timezone.utc)
        return elapsed.total_seconds() / 86400


@dataclass
class PositionLedger:
    positions: list[Position] = field(default_factory=list)
    updated_at: str = ""


def _load_ledger() -> PositionLedger:
    try:
        with open(_positions_path()) as f:
            data = json.load(f)
        return PositionLedger(
            positions=[Position(**p) for p in data.get("positions", [])],
            updated_at=data.get("updated_at", ""),
        )
    except (FileNotFoundError, json.JSONDecodeError):
        return PositionLedger()


def _save_ledger(ledger: PositionLedger) -> None:
    data = {
        "positions": [asdict(p) for p in ledger.positions],
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    with open(_positions_path(), "w") as f:
        json.dump(data, f, indent=2)


def track_deposit(protocol: str, pool: str, amount: float, apy: float = 0.0) -> None:
    """Record a new deposit in the position ledger."""
    ledger = _load_ledger()
    # Merge with existing position for the same protocol+pool
    existing = [p for p in ledger.positions if p.protocol == protocol and p.pool == pool]
    if existing:
        existing[0].amount += amount
        existing[0].deposited_at = datetime.now(timezone.utc).isoformat()
        existing[0].apy_at_deposit = apy if apy else existing[0].apy_at_deposit
    else:
        ledger.positions.append(Position(
            protocol=protocol,
            pool=pool,
            amount=amount,
            deposited_at=datetime.now(timezone.utc).isoformat(),
            apy_at_deposit=apy,
        ))
    _save_ledger(ledger)


def track_withdrawal(protocol: str, pool: str, amount: float) -> None:
    """Reduce tracked position after a withdrawal."""
    ledger = _load_ledger()
    existing = [p for p in ledger.positions if p.protocol == protocol and p.pool == pool]
    if existing:
        existing[0].amount = max(0.0, existing[0].amount - amount)
        existing[0].deposited_at = datetime.now(timezone.utc).isoformat()
        if existing[0].amount <= 0:
            ledger.positions = [p for p in ledger.positions if not (p.protocol == protocol and p.pool == pool)]
    _save_ledger(ledger)


def get_total_deposited() -> dict[str, float]:
    """Return total deposited amount per protocol."""
    ledger = _load_ledger()
    totals: dict[str, float] = {}
    for p in ledger.positions:
        totals[p.protocol] = totals.get(p.protocol, 0) + p.amount
    return totals


# ── Harvester node ──────────────────────────────────────────────────────

def estimate_accrued_yield(
    position: Position,
    current_yields: list[dict[str, Any]],
) -> float:
    """Estimate yield accrued since deposit using current APY as a proxy."""
    current_apy = 0.0
    for y in current_yields:
        if y.get("protocol") == position.protocol and y.get("pool") == position.pool:
            current_apy = y.get("apy", 0.0)
            break

    if current_apy <= 0:
        current_apy = position.apy_at_deposit or current_apy

    elapsed_days = position.elapsed_days()
    # Simple linear APY: amount * (apy/100) * (days/365)
    accrued = position.amount * (current_apy / 100.0) * (elapsed_days / 365.0)
    return max(0.0, accrued)


def harvest(state: dict[str, Any]) -> dict[str, Any]:
    """Harvester node — check positions for accrued yield, produce harvest plan.

    Returns state with:
      - harvest_signal: dict with harvestable amounts per protocol, or None
      - harvest_yield_info: list of estimated yields per position

    The executor will use harvest_signal to trigger withdrawals before
    the normal deposit flow.
    """
    ledger = _load_ledger()
    yields_data = state.get("yields", [])

    if not ledger.positions:
        return {**state, "harvest_signal": None, "harvest_yield_info": []}

    harvest_info = []
    total_harvestable = 0.0

    for pos in ledger.positions:
        accrued = estimate_accrued_yield(pos, yields_data)
        if accrued > 0:
            harvest_info.append({
                "protocol": pos.protocol,
                "pool": pos.pool,
                "deposited": pos.amount,
                "accrued_yield": round(accrued, 6),
                "elapsed_days": round(pos.elapsed_days(), 2),
            })
            total_harvestable += accrued

    if total_harvestable >= MIN_HARVEST_THRESHOLD:
        harvest_signal = {
            "action": "harvest_and_redeposit",
            "total_harvestable": round(total_harvestable, 6),
            "positions": harvest_info,
        }
        logger.info(
            "Harvest signal: %.6f USDC accrued across %d position(s)",
            total_harvestable,
            len(harvest_info),
        )
    else:
        harvest_signal = None
        if harvest_info:
            logger.info(
                "Yield accrued but below threshold: %.6f USDC (min: %.2f)",
                total_harvestable,
                MIN_HARVEST_THRESHOLD,
            )

    return {
        **state,
        "harvest_signal": harvest_signal,
        "harvest_yield_info": harvest_info,
    }
