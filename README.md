<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://img.shields.io/badge/Agent%20Heap-%F0%9F%97%BE%F0%9F%A4%96-7c3aed?style=for-the-badge&logo=github&logoColor=white">
    <img src="https://img.shields.io/badge/Agent%20Heap-%F0%9F%97%BE%F0%9F%A4%96-7c3aed?style=for-the-badge&logo=github&logoColor=white" alt="Agent Heap">
  </picture>
</p>

<p align="center">
  <b>Autonomous AI agent for multi-chain yield optimization on Arbitrum.</b>
</p>

<p align="center">
  <a href="https://github.com/agentheap/agent-heap/actions"><img src="https://img.shields.io/badge/tests-60%20passing-brightgreen?style=for-the-badge&logo=pytest" alt="Tests"></a>
  <a href="https://github.com/agentheap/agent-heap"><img src="https://img.shields.io/badge/Python-3.11%2B-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python"></a>
  <a href="https://github.com/agentheap/agent-heap"><img src="https://img.shields.io/badge/Go-1.26-00ADD8?style=for-the-badge&logo=go" alt="Go"></a>
  <a href="https://github.com/agentheap/agent-heap"><img src="https://img.shields.io/badge/LangGraph-%E2%9C%93-8b5cf6?style=for-the-badge" alt="LangGraph"></a>
  <a href="https://github.com/agentheap/agent-heap"><img src="https://img.shields.io/badge/MIT-green?style=for-the-badge" alt="MIT"></a>
  <a href="https://github.com/agentheap/agent-heap"><img src="https://img.shields.io/badge/Arbitrum-Sepolia%20%7C%20Mainnet-blue?style=for-the-badge&logo=arbitrum" alt="Arbitrum"></a>
  <a href="https://github.com/agentheap/agent-heap"><img src="https://img.shields.io/badge/LiteLLM-100%2B%20models-FF6F61?style=for-the-badge" alt="LiteLLM"></a>
</p>

**Agent Heap** is a LangGraph-powered agent that continuously monitors DeFi lending protocols (Aave, Compound, Morpho) on Arbitrum, analyzes yields via LLM reasoning, executes deposits using Kelly-criterion position sizing, and manages a HEAP token buyback loop — all autonomously.

## Features

- **Autonomous loop** — 24/7 agent cycle (collect → analyze → signal → execute → buyback)
- **Live yield data** — DeFiLlama APY + TVL for Aave V3, Compound, and Morpho
- **LLM analysis** — Supports any LLM via LiteLLM (OpenAI, Anthropic, Gemini, Groq, DeepSeek, etc.); falls back to highest-APY heuristic
- **Kelly-criterion sizing** — Optimal position size based on win probability and expected return
- **Circuit breaker** — Daily PnL tracking; halts on excess drawdown
- **Slippage protection** — Rejects trades exceeding configurable threshold
- **HEAP buyback loop** — 10% of yield profits buy and burn HEAP tokens automatically
- **Vector memory** — ChromaDB stores past decisions for context-aware ranking
- **Go CLI** — Static binary, zero Python dependency at the command layer

## CLI

```text
Usage:
  agent-heap [command]

Available Commands:
  config      Manage environment configuration (.env)
  health      Check agent service health
  history     Show recent agent decisions
  memory      Show recent vector memory entries
  run         Run a single agent decision cycle
  start       Start the agent loop
  status      Show agent state and heartbeat
  wallet      Wallet management commands
```

### Key commands

| Command | Description |
|---------|-------------|
| `agent-heap start --interval 21600` | Run the agent loop (6h interval, heartbeat every 30s) |
| `agent-heap run` | Single-shot agent cycle, full result output |
| `agent-heap status` | Agent state, uptime, wallet balance, DB size |
| `agent-heap health` | Ping RPC, ChromaDB, SQLite, LLM, wallet |
| `agent-heap history --limit 20` | Recent trades with gas costs and tx hashes |
| `agent-heap config list` | Show all env vars (secrets masked) |
| `agent-heap config set KEY VALUE` | Update `.env` file |
| `agent-heap wallet generate -o wallet.json` | Create a new EVM wallet |
| `agent-heap wallet balance` | Check ETH balance of configured wallet |
| `agent-heap memory --last 10` | Query Chroma vector store |

### Quick start

```bash
agent-heap health                          # Check everything is connected
agent-heap config set ARBITRUM_RPC <url>   # Configure RPC
agent-heap wallet generate                 # Create a wallet
agent-heap run                             # Test one agent cycle
agent-heap start                           # Go live
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Go CLI (agent-heap)                 │
│  start │ run │ status │ history │ wallet │ memory       │
│  config │ health                                        │
└──────────────────────┬──────────────────────────────────┘
                       │ python3 -m agent.graph (subprocess)
┌──────────────────────▼──────────────────────────────────┐
│              LangGraph Pipeline (Python)                 │
│  Collector → Analyzer → Signaler → Executor → Buyback   │
│  (DeFiLlama)  (LiteLLM +   (risk      (Web3.py)  (HEAP │
│                ChromaDB)   engine)               burn)  │
└─────────────────────────────────────────────────────────┘
```

### Pipeline

| Node | What it does |
|------|-------------|
| **Collector** | Fetches live APY + TVL from DeFiLlama for Aave V3, Compound, and Morpho on Arbitrum |
| **Analyzer** | LLM ranks pools by risk-adjusted yield using LiteLLM (any model); falls back to highest-APY |
| **Signaler** | Kelly-criterion position sizing + circuit breaker check + slippage estimation |
| **Executor** | Builds, simulates, signs, and sends transactions via Web3.py |
| **Buyback** | 10% of yield profits → buys + burns HEAP tokens |

## Tests

```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 Go Tests (32)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 internal/db          ■■■■■■■■■■■■■■■  8/8  ✅
 internal/wallet      ■■■■■■■■■■■■■■■  6/6  ✅
 internal/memory      ■■■■■■■■■■■■■■■  11/11 ✅
 internal/agent       ■■■■■■■■■■■■■■■  6/6  ✅
 internal/cmd         ■■■■■■■■■■■■■■■  7/7  ✅

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 Python Tests (28)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 Agent Flow           ■■■■■■■■■■■■■■■  6/6  ✅
 Risk Models          ■■■■■■■■■■■■■■■  4/4  ✅
 Data Feeds           ■■■■■■■■■■■■■■■  2/2  ✅
 Memory & CLI         ■■■■■■■■■■■■■■■  2/2  ✅
 HEAP Buyback         ■■■■■■■■■■■■■■■  10/10 ✅
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 TOTAL: 60/60 PASSING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Quick start

```bash
git clone https://github.com/agentheap/agent-heap.git
cd agent-heap
uv sync
cp .env.example .env
# Edit .env with your config, OR use the CLI:
./agent-heap config set LLM_MODEL claude-sonnet-4-20250514
./agent-heap config set ANTHROPIC_API_KEY sk-...
uv run pytest -v              # 28 Python tests
go test ./...                 # 32 Go tests
./agent-heap run              # Test one agent cycle
./agent-heap start --interval 21600   # 6h agent loop
```

Set `LLM_MODEL` (e.g. `gpt-4o`, `claude-sonnet-4`) + your provider's API key in `.env` or via `agent-heap config set`.

## Roadmap

- [x] LangGraph pipeline, data feeds, risk modules, CLI
- [x] HEAP token buyback loop
- [x] Go CLI: tests, config, health, run commands (60 tests)
- [ ] **Mainnet** — Funded wallet, live deposits on Arbitrum One
- [ ] **Auto-compound** — Rebalance between pools
- [ ] **Notifications** — Telegram/Discord alerts
- [ ] **Multi-chain** — Base, Optimism, Polygon

## Build from source

```bash
make build        # Static binary → ./agent-heap
make test         # Run all Go tests
```

## License

MIT
