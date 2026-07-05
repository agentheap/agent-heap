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
  <a href="https://github.com/agentheap/agent-heap/security"><img src="https://img.shields.io/badge/keystore-AES256--GCM-7c3aed?style=for-the-badge" alt="Keystore"></a>
</p>

**Agent Heap** is a LangGraph-powered agent that monitors DeFi lending protocols (Aave V3, Compound III, Morpho Blue) on Arbitrum, analyzes yields via LLM reasoning, executes deposits using Kelly-criterion position sizing, and runs a HEAP token buyback loop.

- [Features](#features)
- [CLI](#cli)
- [Security](#security)
- [Architecture](#architecture)
- [Tests](#tests)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Roadmap](#roadmap)

---

## Features

| Layer | What it does |
|-------|-------------|
| **Yield monitoring** | Live APY + TVL from DeFiLlama for Aave V3, Compound III, Morpho Blue |
| **LLM analysis** | LiteLLM ranks pools by risk-adjusted yield -- supports OpenAI, Anthropic, Gemini, Groq, DeepSeek, 100+ models. Falls back to highest-APY heuristic. |
| **Position sizing** | Kelly-criterion computes optimal deposit size from available capital |
| **Execution** | Builds and sends real deposits on Arbitrum (testnet or mainnet). ERC-20 approve, EIP-1559 gas, 20% gas buffer, receipt confirmation. |
| **Circuit breaker** | Tracks daily PnL, halts on 5% drawdown |
| **Slippage protection** | Rejects trades exceeding configurable threshold |
| **HEAP buyback** | 10% of yield profits auto-buy-and-burn HEAP tokens |
| **Vector memory** | ChromaDB stores past decisions for context-aware ranking |
| **Static binary CLI** | CGO-free Go binary (~13MB), zero Python dependency at the command layer |

See [FEATURES.md](FEATURES.md) for the full breakdown.

---

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
  security    Show security feature status
  start       Start the agent loop
  status      Show agent state and heartbeat
  wallet      Wallet management commands
```

### Quick reference

| Command | Description |
|---------|-------------|
| `agent-heap run` | Single-shot agent cycle, full result output |
| `agent-heap start --interval 21600` | Run the agent loop (6h interval) |
| `agent-heap status` | Agent state, uptime, wallet balance, DB size |
| `agent-heap health` | Ping RPC, ChromaDB, SQLite, LLM, wallet |
| `agent-heap history --limit 20` | Recent trades with gas costs and tx hashes |
| `agent-heap security` | Show which security features are enabled |
| `agent-heap config list` | Show all env vars (secrets masked) |
| `agent-heap config set KEY VALUE` | Update `.env` file |
| `agent-heap wallet balance` | Check ETH balance of configured wallet |
| `agent-heap wallet generate --encrypt --passphrase "..." --output wallet.json` | Create encrypted keystore |
| `agent-heap memory --last 10` | Query Chroma vector store |

---

## Security

Agent Heap has been hardened with three layers of transaction safety and encrypted key storage. See [SECURITY.md](SECURITY.md) for the full assessment.

| Control | Status | What it does |
|---------|--------|-------------|
| **Keystore encryption** | AES-256-GCM + scrypt | Encrypts private keys with a passphrase instead of plaintext env vars |
| **Address allowlist** | Network-aware | Only known protocol addresses (Aave, Compound, Morpho, USDC) are valid recipients -- rejects everything else |
| **Spending limits** | `MAX_TX_AMOUNT` + `DAILY_TX_LIMIT` | Caps per-transaction and daily volume |
| **Rate limiting** | `MAX_TX_PER_HOUR` | Prevents runaway loops from burning gas |
| **Circuit breaker** | 5% drawdown halt | Stops the agent when daily PnL exceeds threshold |
| **Slippage protection** | Configurable | Rejects trades with excessive price impact |

Run `agent-heap security` to see the current status of all controls.

### Keystore setup (recommended over plaintext PRIVATE_KEY)

```bash
# Generate an encrypted wallet
agent-heap wallet generate --encrypt --passphrase "your-passphrase" --output wallet.json

# Or encrypt an existing key
agent-heap wallet encrypt key.json --passphrase "your-passphrase" --output wallet.json

# Set env vars
echo "KEYSTORE_FILE=wallet.json" >> .env
echo "KEYSTORE_PASSPHRASE=your-passphrase" >> .env

# Verify
agent-heap security
```

The agent auto-detects keystore vs plaintext `PRIVATE_KEY` at runtime.

---

## Architecture

```mermaid
%%{init: {'theme': 'base', 'themeVariables': {'primaryColor': '#22808c', 'primaryTextColor': '#fff', 'primaryBorderColor': '#000', 'lineColor': '#000', 'secondaryColor': '#32b8c6', 'tertiaryColor': '#d6d5d4'}}}%%
flowchart LR
    classDef cli fill:#22808c,color:#fff,stroke:#000,stroke-width:2px,rx:8px
    classDef bridge fill:#32b8c6,color:#000,stroke:#000,stroke-width:2px,rx:8px
    classDef node fill:#22808c,color:#fff,stroke:#000,stroke-width:2px,rx:8px
    classDef ext fill:#d6d5d4,color:#000,stroke:#000,stroke-width:2px,rx:8px

    C["CLI<br/>agent-heap"] --> P["Bridge<br/>agent.graph"]
    P --> COL["Collector"] --> A["Analyzer"] --> S["Signaler"] --> E["Executor"] --> B["Buyback"]

    COL -.-> DL["DeFiLlama"]
    A -.-> LT["LiteLLM"]
    A -.-> CH["ChromaDB"]
    E -.-> RPC["Arbitrum RPC"]
    B -.-> HP["HEAP"]

    class C cli
    class P bridge
    class COL,A,S,E,B node
    class DL,LT,CH,RPC,HP ext
```

### Pipeline nodes

| Node | What it does |
|------|-------------|
| **Collector** | Fetches live APY + TVL from DeFiLlama for Aave V3, Compound III, and Morpho Blue on Arbitrum |
| **Analyzer** | LLM ranks pools by risk-adjusted yield using LiteLLM (any provider); falls back to highest-APY heuristic |
| **Signaler** | Kelly-criterion position sizing, circuit breaker check, and slippage estimation |
| **Executor** | Builds, simulates, signs, and sends deposit transactions via Web3.py |
| **Buyback** | 10% of yield profits automatically buy and burn HEAP tokens |

---

## Tests

| Language | Count | Status |
|----------|-------|--------|
| Go | 32 | Passing |
| Python | 28 | Passing |
| **Total** | **60** | **All passing** |

```bash
go test ./...          # Go tests
uv run pytest -v       # Python tests
```

---

## Quick start

```bash
# Clone
git clone https://github.com/agentheap/agent-heap.git
cd agent-heap

# Python deps
uv sync

# Build the CLI
make build

# Configure
cp .env.example .env
./agent-heap config set ARBITRUM_RPC https://sepolia-rollup.arbitrum.io/rpc
./agent-heap config set LLM_MODEL claude-sonnet-4-20250514
./agent-heap config set ANTHROPIC_API_KEY sk-...

# Generate an encrypted wallet
./agent-heap wallet generate --encrypt --passphrase "test" --output wallet.json
echo "KEYSTORE_FILE=wallet.json" >> .env
echo "KEYSTORE_PASSPHRASE=test" >> .env

# Verify setup
./agent-heap health
./agent-heap security

# Run one cycle
./agent-heap run

# Run continuously (6h interval)
./agent-heap start --interval 21600
```

---

## Configuration

All configuration is via `.env` file at the project root, managed through `agent-heap config` or direct editing.

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ARBITRUM_RPC` | Yes | -- | Arbitrum RPC endpoint |
| `PRIVATE_KEY` | Conditional | -- | Wallet private key (use keystore instead) |
| `KEYSTORE_FILE` | Conditional | -- | Path to encrypted keystore |
| `KEYSTORE_PASSPHRASE` | Conditional | -- | Keystore decryption passphrase |
| `ARBITRUM_NETWORK` | No | `sepolia` | Set to `mainnet` for Arbitrum One |
| `LLM_MODEL` | No | -- | LiteLLM model name (e.g. `claude-sonnet-4-20250514`) |
| `ANTHROPIC_API_KEY` | Conditional | -- | API key for Anthropic models |
| `OPENAI_API_KEY` | Conditional | -- | API key for OpenAI models |
| `MAX_TX_AMOUNT` | No | -- | Max USDC per transaction |
| `DAILY_TX_LIMIT` | No | -- | Max USDC per day |
| `MAX_TX_PER_HOUR` | No | -- | Max transactions per hour |
| `MAX_SLIPPAGE` | No | `0.05` | Max slippage (5%) |

`PRIVATE_KEY` is only required if no keystore is configured. At least one LLM provider API key must be set if `LLM_MODEL` is configured; if neither is set, the agent runs in highest-APY fallback mode.

---

## Build from source

```bash
make build        # Static binary → ./agent-heap (CGO_ENABLED=0)
make test         # Run all Go tests
```

---

## Roadmap

- [x] LangGraph pipeline, DeFiLlama data feeds, Kelly sizing
- [x] HEAP token buyback loop
- [x] Go CLI with 9 commands, 60 tests
- [x] Security hardening (keystore, allowlist, spending & rate limits)
- [ ] **Mainnet** -- Funded wallet, live deposits on Arbitrum One
- [ ] **Auto-compound** -- Rebalance between pools
- [ ] **Notifications** -- Telegram/Discord alerts
- [ ] **Multi-chain** -- Base, Optimism, Polygon

---

## License

MIT

Built by AI agents (Claude Code) -- not a single line authored by a human.
