# Agent Heap 🏗️🤖

> An autonomous AI agent for multi-chain yield optimization on Arbitrum.

**Agent Heap** is a LangGraph-powered agent that continuously scans DeFi lending protocols (Aave, Compound, Morpho) on Arbitrum, analyzes yields via LLM reasoning, and executes deposits using Kelly-criterion position sizing — all autonomously.

[![Tests](https://img.shields.io/badge/tests-14%20passing-brightgreen)](#)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](#)
[![LangGraph](https://img.shields.io/badge/LangGraph-%E2%9C%94-purple)](#)
[![License](https://img.shields.io/badge/license-MIT-green)](#)
[![Arbitrum](https://img.shields.io/badge/Arbitrum-Sepolia%20%7C%20Mainnet-blue?logo=arbitrum)](#)

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    Agent Loop                        │
│  ┌──────────┐  ┌──────────┐  ┌────────┐  ┌────────┐ │
│  │Collector │→ │ Analyzer │→ │Signaler│→ │Executor│ │
│  │(DeFiLlama)│  │(LLM/NIM) │  │(Struct)│  │(web3)  │ │
│  └──────────┘  └──────────┘  └────────┘  └────────┘ │
│       │              │              │          │      │
│       ▼              ▼              ▼          ▼      │
│  Live APYs     Risk-adjusted     Signal       Tx     │
│  from Aave,    pool ranking     generation   exec    │
│  Compound,     with Kelly       (deposit/    (sim or │
│  Morpho       sizing &         withdraw/   real)    │
│                memory context   compound)            │
└─────────────────────────────────────────────────────┘
         │                                            │
         ▼                                            ▼
┌─────────────────┐                     ┌──────────────────────┐
│  Risk Modules   │                     │  Memory & Persistence│
│  • Kelly sizing │                     │  • ChromaDB (vector) │
│  • Circuit      │                     │  • SQLite/PostgreSQL │
│    breaker      │                     │  • Decision history  │
│  • Slippage     │                     └──────────────────────┘
│    estimation   │
└─────────────────┘
```

## Features

- **Autonomous yield collection** — Fetches live APY + TVL data from DeFiLlama for Aave, Compound, and Morpho on Arbitrum
- **LLM-powered analysis** — Uses NVIDIA NIM (Mistral/Llama) to select the best risk-adjusted pool; falls back to highest APY heuristic
- **Kelly-criterion sizing** — Position sizes computed via Kelly fraction for optimal risk-adjusted returns
- **Slippage protection** — Pre-execution check: rejects trades exceeding configurable slippage threshold
- **Circuit breaker** — Daily PnL tracking; halts execution if drawdown exceeds the limit
- **Vector memory** — ChromaDB stores past decisions; the analyzer queries similar contexts to avoid repeated mistakes
- **Real or simulated execution** — Web3.py integration for Arbitrum Sepolia (testnet) and Arbitrum One (mainnet); simulates when no key is set
- **CLI agent loop** — `agent-heap start` runs the 24/7 agent loop with configurable interval, rich logging, and graceful shutdown
- **Trade history** — All decisions persisted to database for P&L tracking

## Quick Start

```bash
# Clone and install
git clone https://github.com/heapchain/agent-heap.git
cd agent-heap

# Install with uv (recommended) or pip
uv sync
# or: pip install -e .

# Set up environment
cp .env.example .env
# Edit .env: add NVIDIA_NIM_API_KEY for LLM analysis

# Run tests
uv run pytest -v

# Run the agent loop (simulated — no funds needed)
agent-heap start --interval 21600

# Check status and history
agent-heap status
agent-heap history
```

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `NVIDIA_NIM_API_KEY` | Recommended | API key for LLM-powered yield analysis (falls back to max-APY heuristic if unset) |
| `ARBITRUM_RPC` | Optional | Arbitrum RPC URL (defaults to public Sepolia endpoint) |
| `PRIVATE_KEY` | Optional | Wallet private key for real execution (omit for simulation mode) |
| `DATABASE_URL` | Optional | Database URL (defaults to `sqlite:///agent-heap.db`) |

## Test Suite

```bash
uv run pytest -v

# Expected: 14 passed, covering graph flow, data feeds,
# risk models, memory, and execution paths
```

## Risk Model Reference

| Module | Function | Purpose |
|---|---|---|
| `risk/position_sizing.py` | `kelly_fraction(win_prob, win_ratio)` | Compute optimal position size |
| `risk/circuit_breaker.py` | `is_tripped()` | Halt trading on excess drawdown |
| `risk/slippage.py` | `check_trade_allowed(trade, pool)` | Reject trades with high slippage |

## Roadmap

- [x] LangGraph agent pipeline (collect → analyze → signal → execute)
- [x] DeFiLlama yield integration (Aave, Compound, Morpho)
- [x] LLM analysis with NVIDIA NIM fallback
- [x] Risk modules (Kelly sizing, circuit breaker, slippage)
- [x] ChromaDB vector memory
- [x] CLI agent loop with trade persistence
- [ ] **Mainnet deployment** — Funded wallet on Arbitrum One
- [ ] **Auto-compound** — Rebalance between pools based on risk-adjusted yield
- [ ] **Notifications** — Telegram/Discord alerts for deposits and withdrawals
- [ ] **Multi-chain** — Base, Optimism, Polygon support

## License

MIT

---

*Built with Claude Code • Gas Town • LangGraph*
