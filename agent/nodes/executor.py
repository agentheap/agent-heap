import os
from typing import Any

from chains.arbitrum import ARBITRUM_RPC


def execute(state: dict[str, Any]) -> dict[str, Any]:
    signal = state.get("signal")
    if not signal:
        return {**state, "tx_result": None}

    private_key = os.getenv("PRIVATE_KEY")
    simulated = not private_key

    if simulated:
        tx_result = {
            "simulated": True,
            "action": signal["action"],
            "protocol": signal["protocol"],
            "pool": signal["pool"],
            "amount": signal["amount"],
            "tx_hash": None,
            "gas_cost": 0,
            "reason": signal["reason"],
        }
        return {**state, "tx_result": tx_result}

    try:
        from web3 import Web3

        w3 = Web3(Web3.HTTPProvider(ARBITRUM_RPC))
        account = w3.eth.account.from_key(private_key)
        tx_result = {
            "simulated": False,
            "action": signal["action"],
            "protocol": signal["protocol"],
            "pool": signal["pool"],
            "amount": signal["amount"],
            "from": account.address,
            "tx_hash": None,
            "gas_cost": 0,
            "reason": signal["reason"],
        }
        return {**state, "tx_result": tx_result}
    except Exception as e:
        return {**state, "tx_result": {"simulated": True, "error": str(e)}}
