import pytest


@pytest.fixture
def sample_yields():
    return [
        {
            "protocol": "aave",
            "pool": "USDC",
            "apy": 5.2,
            "tvl": 100_000_000,
            "chain": "Arbitrum",
        },
        {
            "protocol": "compound",
            "pool": "USDC",
            "apy": 4.8,
            "tvl": 80_000_000,
            "chain": "Arbitrum",
        },
        {
            "protocol": "morpho",
            "pool": "USDC",
            "apy": 6.1,
            "tvl": 50_000_000,
            "chain": "Arbitrum",
        },
    ]


@pytest.fixture
def sample_agent_state():
    return {
        "yields": [],
        "analysis": None,
        "signal": None,
        "tx_result": None,
        "errors": [],
    }
