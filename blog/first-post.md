---

Title: Building an Autonomous DeFi Yield Agent
Description: How I built an AI agent that discovers, analyzes, and executes yield strategies on Arbitrum — with LangGraph, LiteLLM, and Web3.py.
Tags: defi, ai, arbitrum, solidity, python
Published: true

---

# Building an Autonomous DeFi Yield Agent

DeFi yields move fast — faster than any human can track across Aave, Compound, and Morpho on Arbitrum. So I built **Agent Heap**: an autonomous AI agent that runs a continuous loop — collect live yields from DeFiLlama, analyze them with an LLM, and execute the best deposit opportunity.

## Architecture

The agent runs a 5-node LangGraph pipeline:

```
Collector → Analyzer → Signaler → Executor → Buyback
```

Each node is a standalone Python module. The entire system runs as a
long-lived process with heartbeat monitoring, SQLite persistence, and
ChromaDB vector memory.

### 1. Collector

Fetches real-time yield data from DeFiLlama's `/pools` endpoint.
Filters for Aave V3, Compound III, and Morpho Blue on Arbitrum.

### 2. Analyzer

Sends the pool data to an LLM (Claude, GPT-4, Gemini — over 100 models
via LiteLLM). The LLM picks the best risk-adjusted yield pool, backed
by past decision history from ChromaDB vector memory. Falls back to
highest-APY heuristic if the LLM is unavailable.

### 3. Signaler

Computes Kelly-criterion position sizing from APY data. Produces a
structured deposit signal with protocol, pool, amount, and reasoning.

### 4. Executor

The execution engine. If `PRIVATE_KEY` is set, builds and sends real
deposit transactions — ERC-20 approve, EIP-1559 fees, gas estimation
with 20% buffer. Supports Aave V3, Compound III, and Morpho Blue.
Falls back to simulation if no key is configured.

### 5. Buyback

When the agent records a profit, 10% is allocated to buy and burn
HEAP tokens — creating deflationary tokenomics for the ecosystem.

## Risk Controls

The agent doesn't just chase the highest APY. Three safety layers:

- **Circuit Breaker** — 5% daily drawdown limit. Halts if PnL drops
  too far in a 24-hour window.
- **Slippage Protection** — rejects trades exceeding 1% slippage
  relative to pool liquidity.
- **Kelly Criterion** — optimal position sizing based on win
  probability and expected return.

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Agent pipeline | LangGraph (Python) |
| LLM access | LiteLLM (100+ models) |
| EVM interaction | Web3.py |
| Vector memory | ChromaDB |
| CLI (Python) | Click + Rich |
| CLI (Go) | Cobra (static binary) |
| Database | SQLite / PostgreSQL |
| Smart contract | Solidity ^0.8.28 |
| Token deployment | Clanker SDK (Base) |

## What's Next

The agent is fully built and passing 28 tests. The immediate roadmap:

1. **Mainnet deployment** — fund the wallet, enable real deposits
2. **Auto-compound** — reinvest earned yield automatically
3. **Yield switching** — move funds when APY drops on a protocol
4. **Leverage** — deposit as collateral, borrow, re-deposit
5. **Notifications** — Telegram/Discord alerts on execution

---

*Follow along as Agent Heap evolves from simulation to
autonomous DeFi manager. Code is open-source.*
