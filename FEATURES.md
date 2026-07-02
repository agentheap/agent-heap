# Agent Heap — Feature Overview

> Autonomous AI agent for multi-chain yield optimization on Arbitrum.
> Built with LangGraph, LiteLLM, Go, Python, Web3.py, and ChromaDB.

---

## Table of Contents

1. [The Agent Pipeline](#1-the-agent-pipeline)
2. [Go CLI](#2-go-cli)
3. [Wallet & EVM](#3-wallet--evm)
4. [DeFi Data Feeds](#4-defi-data-feeds)
5. [Risk Engine](#5-risk-engine)
6. [Memory & Persistence](#6-memory--persistence)
7. [HEAP Token & Buyback](#7-heap-token--buyback)
8. [Testing](#8-testing)
9. [Infrastructure](#9-infrastructure)
10. [Quick Start](#10-quick-start)

---

## 1. The Agent Pipeline

A 5-node LangGraph state machine that runs autonomously:

```
Collector → Analyzer → Signaler → Executor → Buyback
(DeFiLlama)  (LiteLLM +   (risk      (Web3.py)  (HEAP
              ChromaDB)   engine)               buy & burn)
```

| Node | What it does |
|------|-------------|
| **Collector** | Fetches live APY + TVL from DeFiLlama for Aave V3, Compound, and Morpho on Arbitrum. Filters by chain (Arbitrum, Base). Prefers protocols with past success from memory. |
| **Analyzer** | If `LLM_MODEL` is set, calls LiteLLM (any provider: OpenAI, Anthropic, Gemini, Groq, DeepSeek, Together, etc.) to pick the best risk-adjusted pool. Falls back to highest-APY heuristic if LLM is unavailable or parsing fails. |
| **Signaler** | Computes Kelly-criterion position size from available capital. Produces a deposit signal with action, protocol, pool, amount, APY, TVL, and reasoning. |
| **Executor** | If `PRIVATE_KEY` is set, builds and sends a **real transaction** on Arbitrum (Aave V3 / Compound III / Morpho Blue). Includes: ETH gas check, ERC-20 approve step, gas estimation with 20% buffer, EIP-1559 fee calculation, tx signing + broadcast + receipt confirmation. Returns simulated result if no key is set. |
| **Buyback** | Tracks accrued profit per cycle. When profit ≥ $10, triggers HEAP token buyback (simulated — real swap+burn is ready for deployment). |

**Key detail:** The entire pipeline was built by AI agents (Claude Code), not by hand. The builder and the built are the same.

---

## 2. Go CLI

A **static binary** (CGO-free, ~13MB) with zero Python dependency at the command layer.

### 9 Commands

| Command | Description |
|---------|-------------|
| **`agent-heap start --interval 21600`** | Run the agent loop. Writes heartbeat every 30s, calls Python agent graph as subprocess, responds to SIGINT/SIGTERM for graceful shutdown. |
| **`agent-heap run`** | Single-shot agent cycle. Runs the full pipeline once and prints the complete result. |
| **`agent-heap status`** | Shows agent state (running/stopped/never run), last run timestamp, uptime, wallet address + ETH balance (if configured), DB file size. |
| **`agent-heap health`** | Pings all services in a table: RPC (chain ID + latency), ChromaDB, SQLite (file size), LLM provider, Wallet (address + balance). Exits non-zero if any service fails. |
| **`agent-heap history --limit 20`** | Recent trades with ID, Action, Token, Amount, Gas Cost, Tx Hash, Timestamp. |
| **`agent-heap config list`** | Shows all env vars (secret values masked). |
| **`agent-heap config get KEY`** | Shows a single config value. |
| **`agent-heap config set KEY VALUE`** | Updates `.env` file and current environment. |
| **`agent-heap wallet generate -o wallet.json`** | Creates a fresh EVM wallet via go-ethereum `crypto.GenerateKey()`. |
| **`agent-heap wallet new`** | Alias for generate (muscle memory). |
| **`agent-heap wallet balance`** | Reads `PRIVATE_KEY` from env, queries Arbitrum RPC for ETH balance. |
| **`agent-heap memory --last 10`** | Queries Chroma vector store via REST API for past decisions. |

### Architecture

```
agent-heap
├── cmd/agent-heap/main.go
├── internal/
│   ├── cmd/           # 9 cobra commands
│   ├── agent/         # Python subprocess runner (auto-detects uv/venv)
│   ├── db/            # SQLite via modernc.org/sqlite (CGO-free)
│   ├── wallet/        # EVM via go-ethereum
│   └── memory/        # Chroma REST API client
├── Makefile
└── go.mod
```

---

## 3. Wallet & EVM

| Feature | Description |
|---------|-------------|
| **Key generation** | Generate fresh EVM wallets via `crypto.GenerateKey()` |
| **Address derivation** | From private key or public key |
| **Balance checking** | Query Arbitrum RPC for ETH balance |
| **Transaction signing** | Sign transactions with any chain ID |
| **JSON output** | Write wallet info (address, private key, network, chain ID) to JSON file |
| **Network detection** | Auto-switches between Arbitrum Sepolia (testnet) and Arbitrum One (mainnet) based on env |

---

## 4. DeFi Data Feeds

| Feed | What it provides |
|------|-----------------|
| **DeFiLlama** | Live APY + TVL for Aave V3, Compound, and Morpho on Arbitrum and Base |
| **CoinGecko** | Token prices for HEAP buyback valuation |

---

## 5. Risk Engine

| Module | What it does |
|--------|-------------|
| **Kelly Criterion** | Computes optimal position size based on win probability and expected return |
| **Circuit Breaker** | Tracks daily PnL. Halts execution when cumulative drawdown exceeds configurable threshold (default 5%) |
| **Slippage Protection** | Estimates price impact based on pool liquidity and trade size. Rejects trades exceeding max slippage threshold |
| **Risk Check** | Validates analysis results before signal generation |

---

## 6. Memory & Persistence

| Storage | What it stores |
|---------|---------------|
| **SQLite** (Go) | Trades, agent state, heartbeats — via `modernc.org/sqlite` (pure Go, no CGO) |
| **PostgreSQL** (Python) | Full schema with migrations — strategies, trades, agent_state |
| **ChromaDB** (Python) | Vector memory: past decisions stored as embeddings for similarity search |
| **ChromaDB** (Go) | REST API client: query past decisions, health check |

The agent recalls past decisions to guide future analysis — protocols that succeeded before get priority.

---

## 7. HEAP Token & Buyback

| Feature | Description |
|---------|-------------|
| **Token** | ERC-20 token on Base Sepolia (1M supply), buyback mechanism built in |
| **Buyback logic** | 10% of yield profits accumulate in a profit pool |
| **Trigger** | When accrued profit ≥ $10, triggers buy-and-burn of HEAP tokens |
| **Deployment** | Deploy script ready (stub until mainnet funding) |
| **Testing** | 10 tests covering accumulation, trigger, execution, history, reset |

---

## 8. Testing

**60 tests total — all passing.**

### Go Tests (32)

| Package | Tests | What's tested |
|---------|-------|--------------|
| `internal/db` | 8 | Init, trades CRUD, agent state lifecycle, heartbeats, path config |
| `internal/wallet` | 6 | Key generation, address derivation, 0x-prefix handling, invalid keys |
| `internal/memory` | 11 | Chroma query/parse, empty entries, error responses, health check, URL defaults |
| `internal/agent` | 6 | Output parsing, JSON deserialization, empty output, error paths, env passthrough |
| `internal/cmd` | 7 | Subcommand registration, flag defaults, format helpers |

### Python Tests (28)

| Suite | Tests | What's tested |
|-------|-------|--------------|
| Agent Flow | 6 | Graph execution, collector, analyzer, signaler, executor, memory |
| Risk Models | 4 | Kelly fraction, slippage estimate/rejection, circuit breaker trip/pass |
| Data Feeds | 2 | Yield fetching from DeFiLlama |
| Risk Check | 2 | Validates risk check passes/blocks correctly |
| Buyback | 4 | Profit accumulation, execution, history, reset |
| HEAP Token | 10 | Threshold triggers, deductions, accumulation, edge cases |

---

## 9. Infrastructure

| Asset | Details |
|-------|---------|
| **GitHub** | [github.com/agentheap/agent-heap](https://github.com/agentheap/agent-heap) |
| **CI/CD** | GitHub Actions — auto-builds on `v*` tags, uploads binaries for linux + darwin |
| **Docker** | `docker-compose.yml` with PostgreSQL + ChromaDB services |
| **Dockerfile** | Docker image for Python agent deployment |
| **Static binary** | `make build` → CGO_ENABLED=0, fully static |
| **Config** | `.env` file or `agent-heap config` CLI commands |

---

## 10. Quick Start

```bash
# Clone
git clone https://github.com/agentheap/agent-heap.git
cd agent-heap

# Setup
uv sync
cp .env.example .env

# Configure
./agent-heap config set LLM_MODEL claude-sonnet-4-20250514
./agent-heap config set ANTHROPIC_API_KEY sk-...
./agent-heap config set PRIVATE_KEY 0x...
./agent-heap config set ARBITRUM_RPC https://sepolia-rollup.arbitrum.io/rpc

# Test
uv run pytest -v              # 28 Python tests
go test ./...                 # 32 Go tests

# Run
./agent-heap health           # Check everything is connected
./agent-heap run              # One agent cycle
./agent-heap start            # Go live (24/7 loop)

# Build from source
make build                    # Static binary → ./agent-heap
```

---

**License:** MIT
**Built by:** AI agents (Claude Code) — not a single line authored by a human.
