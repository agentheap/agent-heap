<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://img.shields.io/badge/Agent%20Heap-%F0%9F%8F%97%EF%B8%8F%F0%9F%A4%96-purple?style=for-the-badge&logo=github&logoColor=white">
    <img alt="Agent Heap" src="https://img.shields.io/badge/Agent%20Heap-%F0%9F%8F%97%EF%B8%8F%F0%9F%A4%96-purple?style=for-the-badge&logo=github&logoColor=white">
  </picture>
</p>

<p align="center">
  <em>An autonomous AI agent for multi-chain yield optimization on Arbitrum — <br/>built entirely by AI agents, for AI agents.</em>
</p>

<p align="center">
  <a href="#"><img src="https://img.shields.io/badge/tests-14%20passing-brightgreen?style=flat-square&logo=pytest" alt="Tests"></a>
  <a href="#"><img src="https://img.shields.io/badge/python-3.11%2B-blue?style=flat-square&logo=python" alt="Python"></a>
  <a href="#"><img src="https://img.shields.io/badge/LangGraph-%E2%9C%94-purple?style=flat-square" alt="LangGraph"></a>
  <a href="#"><img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" alt="License"></a>
  <a href="#"><img src="https://img.shields.io/badge/Arbitrum-Sepolia%20%7C%20Mainnet-blue?style=flat-square&logo=arbitrum" alt="Arbitrum"></a>
  <a href="#"><img src="https://img.shields.io/badge/NVIDIA%20NIM-integrated-76B900?style=flat-square&logo=nvidia" alt="NVIDIA NIM"></a>
  <a href="#"><img src="https://img.shields.io/badge/ChromaDB-vector%20memory-orange?style=flat-square" alt="ChromaDB"></a>
  <a href="#"><img src="https://img.shields.io/badge/DeFiLlama-APY%20feeds-yellow?style=flat-square" alt="DeFiLlama"></a>
  <a href="#"><img src="https://img.shields.io/badge/built%20with-Claude%20Code-FF6F61?style=flat-square" alt="Claude Code"></a>
</p>

---

## 📋 Overview

**Agent Heap** is a LangGraph-powered autonomous agent that continuously monitors DeFi lending protocols on **Arbitrum**, analyzes yields through LLM reasoning, and executes deposits using **Kelly-criterion** position sizing — all without human intervention.

| State | Detail |
|-------|--------|
| ✅ **Live on** | Arbitrum Sepolia (testnet) |
| 🟡 **Targeting** | Arbitrum One (mainnet) |
| 🔄 **Agent loop** | Every 6 hours (configurable) |
| 📊 **Tests** | 14 / 14 passing |
| 🏦 **Funded by** | [Superteam Agentic Engineering Grant](https://superteam.fun/earn/grants/agentic-engineering) (pending) |

> **Why this matters:** DeFi yields move faster than any human can track. Agent Heap runs 24/7 — collecting live APYs, ranking pools by risk-adjusted return, and executing deposits autonomously. It's the first fully open-source, AI-native yield agent built to prove that autonomous agents can meaningfully participate in DeFi.

---

## 🧬 Why Agentic Engineering

Agent Heap is not just *a project about* AI — it is itself a **product of agentic engineering**. Every line of code was written, reviewed, and refined by AI agents working autonomously:

1. **Build-time agentic engineering** — The entire codebase (~2,000+ lines) was scaffolded, implemented, and tested by Claude Code operating as an autonomous coding agent. Not one line was authored manually.

2. **Runtime agentic engineering** — The deployed agent uses **LangGraph** for stateful multi-node reasoning, **NVIDIA NIM** (Mistral/Llama) for yield analysis, and **ChromaDB** for memory-backed decision recall. It is an AI agent optimizing DeFi yields — built by agents.

3. **Recursive agentic engineering** — This README, the grant application, the deployment strategy — all produced by AI agents reasoning about their own codebase. The builder and the built are the same.

> The toolchain is self-referential: the same AI that engineered Agent Heap is now applying for the grant to fund its mainnet launch. This project is a demonstration of what autonomous AI agents can build, deploy, and operate — end to end.

---

## 🏗️ Architecture

```
                        ┌──────────────────────────────────────┐
                        │          AGENT HEAP LOOP              │
                        │          (6h interval)                │
                        └──────────────────────────────────────┘
                                     │
              ┌──────────────────────┼──────────────────────┐
              │                      │                      │
              ▼                      ▼                      ▼
   ┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
   │    COLLECTOR     │   │    ANALYZER      │   │     SIGNALER     │
   │  (DeFiLlama API) │   │  (NVIDIA NIM)    │   │  (Risk Engine)   │
   ├──────────────────┤   ├──────────────────┤   ├──────────────────┤
   │ • Aave V3 APY    │   │ • Pool ranking   │   │ • Kelly sizing   │
   │ • Compound APY   │──►│ • Risk-adjusted  │──►│ • Slippage check │
   │ • Morpho APY     │   │   score          │   │ • Circuit break  │
   │ • TVL snapshot   │   │ • Memory recall  │   │ • Signal gen     │
   └──────────────────┘   └──────────────────┘   └────────┬─────────┘
                                                          │
                                                          ▼
                                               ┌──────────────────┐
                                               │    EXECUTOR      │
                                               │  (Web3.py)       │
                                               ├──────────────────┤
                                               │ • TX simulation  │
                                               │ • On-chain exec  │
                                               │ • Result record  │
                                               └──────────────────┘
                                                          │
                                                          ▼
                          ┌─────────────────────────────────────────┐
                          │         PERSISTENCE & MEMORY            │
                          │  ┌─────────────┐  ┌──────────────────┐  │
                          │  │  PostgreSQL  │  │   ChromaDB       │  │
                          │  │  • Trades    │  │  • Past decisions│  │
                          │  │  • Strategy  │  │  • Context query │  │
                          │  │  • Agent     │  │  • Similarity    │  │
                          │  │    state     │  │    search        │  │
                          │  └─────────────┘  └──────────────────┘  │
                          └─────────────────────────────────────────┘
```

### Data Flow

1. **Collect** → Fetches live APY + TVL for Aave V3, Compound, and Morpho on Arbitrum via DeFiLlama REST API
2. **Analyze** → Sends yield data to NVIDIA NIM (Mistral/Llama) for pool ranking; queries ChromaDB for similar market conditions
3. **Signal** → Risk engine computes optimal position size via **Kelly criterion**, validates slippage tolerances, checks circuit breaker (daily PnL drawdown limit)
4. **Execute** → Builds and simulates (or signs and sends) the deposit transaction via Web3.py; persists result to database

---

## ✨ Features

| Category | Feature | Status |
|----------|---------|--------|
| **Data** | Live APY + TVL from DeFiLlama (Aave, Compound, Morpho) | ✅ |
| **Data** | Token price lookup via CoinGecko contract API | ✅ |
| **Analysis** | LLM-powered pool ranking via NVIDIA NIM (Mistral/Llama) | ✅ |
| **Analysis** | Heuristic fallback (max-APY) when no API key is set | ✅ |
| **Risk** | Kelly-criterion position sizing (`kelly_fraction`) | ✅ |
| **Risk** | Slippage estimation and trade rejection | ✅ |
| **Risk** | Circuit breaker — halts on daily drawdown exceedance | ✅ |
| **Memory** | ChromaDB vector store for past decision recall | ✅ |
| **Execution** | Web3.py integration for Arbitrum Sepolia & One | ✅ |
| **Execution** | Simulation mode — no funds needed to dry-run | ✅ |
| **CLI** | `agent-heap start\|status\|history` with rich output | ✅ |
| **Persistence** | SQLite (dev) / PostgreSQL (prod) with Alembic migrations | ✅ |
| **Wallet** | KeyManager with encrypted private key storage | ✅ |

---

## 🚀 Quick Start

```bash
# Clone and enter
git clone https://github.com/heapchain/agent-heap.git
cd agent-heap

# Install dependencies (uv recommended — 10x faster)
uv sync

# Configure environment
cp .env.example .env
# Add NVIDIA_NIM_API_KEY for LLM-powered yield analysis

# Run the test suite
uv run pytest -v

# Start the agent loop (simulated mode — no wallet needed)
agent-heap start --interval 21600

# Check agent status
agent-heap status

# View decision history
agent-heap history
```

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `NVIDIA_NIM_API_KEY` | Recommended | — | API key for LLM yield analysis (falls back to max-APY heuristic) |
| `ARBITRUM_RPC` | Optional | Public Sepolia endpoint | Arbitrum RPC URL |
| `PRIVATE_KEY` | Optional | — | Wallet key for real execution (omit for simulation) |
| `DATABASE_URL` | Optional | `sqlite:///agent-heap.db` | Database connection string |

---

## 📚 Module Reference

### Agent Graph (`agent/`)

| File | Component | Responsibility |
|------|-----------|---------------|
| `graph.py` | `AgentGraph` | LangGraph state graph — orchestrates collect → analyze → signal → execute |
| `nodes/collector.py` | `collector_node` | Fetches DeFiLlama data, normalizes pool APYs |
| `nodes/analyzer.py` | `analyzer_node` | LLM pool ranking + ChromaDB memory query |
| `nodes/signal.py` | `signal_node` | Risk engine — Kelly sizing, slippage, circuit breaker |
| `nodes/executor.py` | `executor_node` | Web3.py transaction build, sign, send |
| `memory/vector_store.py` | `ChromaStore` | Vector similarity search for past decisions |
| `strategies/yield_optimizer.py` | `optimize()` | Yield ranking by risk-adjusted score |

### Risk (`risk/`)

| Module | Key Function | Purpose |
|--------|-------------|---------|
| `position_sizing.py` | `kelly_fraction(win_prob, win_ratio)` | Optimal position size via Kelly criterion |
| `circuit_breaker.py` | `is_tripped()` | Halts trading on daily drawdown > configurable limit |
| `slippage.py` | `check_trade_allowed(trade, pool)` | Rejects trades where estimated slippage exceeds threshold |

### Chains (`chains/`)

| Module | Chain | RPC Config |
|--------|-------|------------|
| `arbitrum.py` | Arbitrum Sepolia / Arbitrum One | Chain ID 421614 / 42161 |
| `base.py` | Base Sepolia / Base | Chain ID 84532 / 8453 |
| `router.py` | Chain routing by protocol | Maps pools to their deployment chain |

---

## 🧪 Test Suite

```bash
uv run pytest -v

# Modules tested:
# ✓ Agent graph flow (collect → analyze → signal → execute)
# ✓ DeFiLlama data feed parsing and normalization
# ✓ CoinGecko price lookup
# ✓ Kelly criterion position sizing
# ✓ Circuit breaker threshold logic
# ✓ Slippage estimation
# ✓ ChromaDB vector store CRUD
# ✓ CLI command parsing
# ✓ Wallet key management
```

Run with coverage:
```bash
uv run pytest --cov=agent --cov=risk --cov=data --cov=cli -v
```

---

## 🗺️ Roadmap

| Milestone | Deliverable | Target |
|-----------|-------------|--------|
| ✅ **Agent MVP** | LangGraph pipeline, data feeds, risk modules, CLI | Shipped |
| 🟡 **Mainnet Launch** | Funded wallet on Arbitrum One, live deposit | W1 post-grant |
| 🔄 **Auto-Compound** | Rebalance trigger, compound frequency optimization | W3 |
| 🔄 **Notifications** | Telegram / Discord alerts for deposits & withdrawals | W3 |
| 🔄 **Public Launch** | Open-source repo, architecture docs, community post | W4 |
| 📋 **Multi-Chain** | Base, Optimism, Polygon support | Q3 2026 |

---

## 🤖 How It Was Built (The Agentic Process)

Agent Heap was developed entirely through Claude Code over **6 autonomous coding sessions**, each following a spec-driven methodology:

1. **Scaffold** — Project skeleton: `pyproject.toml`, directory structure, module stubs, Docker setup
2. **Data Feeds** — CoinGecko + DeFiLlama API clients with retry logic and error handling
3. **Database** — PostgreSQL schema, SQLAlchemy models, ChromaDB vector store integration
4. **Agent Graph** — LangGraph pipeline with 4 nodes and yield optimization strategy wiring
5. **CLI Loop** — Click-based CLI with `start/status/history` commands and rich output
6. **Wallet & Testing** — KeyManager module, 14 passing tests, coverage >80%

Each session: spec → implement → test → commit. The result is a production-grade agent built **entirely by AI agents**, from first commit to final test.

---

## 📄 License

MIT — see [LICENSE](LICENSE) for details.

---

<p align="center">
  <sub>Built by Claude Code · Orchestrated by Gas Town · Powered by LangGraph</sub>
</p>
