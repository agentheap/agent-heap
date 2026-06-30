<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://img.shields.io/badge/Agent%20Heap-%F0%9F%8F%97%EF%B8%8F%F0%9F%A4%96-7c3aed?style=for-the-badge&logo=github&logoColor=white">
    <img src="https://img.shields.io/badge/Agent%20Heap-%F0%9F%8F%97%EF%B8%8F%F0%9F%A4%96-7c3aed?style=for-the-badge&logo=github&logoColor=white" alt="Agent Heap">
  </picture>
</p>

<p align="center">
  <b>Autonomous AI agent for multi-chain yield optimization on Arbitrum.</b>
</p>

<p align="center">
  <a href="https://github.com/heapchain/agent-heap/blob/master/tests/test_agent.py"><img src="https://img.shields.io/badge/tests-18%20passing-brightgreen?style=for-the-badge&logo=pytest" alt="Tests"></a>
  <a href="https://github.com/heapchain/agent-heap/blob/master/pyproject.toml"><img src="https://img.shields.io/badge/python-3.11%2B-blue?style=for-the-badge&logo=python" alt="Python"></a>
  <a href="https://github.com/heapchain/agent-heap/tree/master/agent"><img src="https://img.shields.io/badge/LangGraph-%E2%9C%94-8b5cf6?style=for-the-badge" alt="LangGraph"></a>
  <a href="https://github.com/heapchain/agent-heap/blob/master/LICENSE"><img src="https://img.shields.io/badge/license-MIT-green?style=for-the-badge" alt="MIT"></a>
  <a href="https://github.com/heapchain/agent-heap/tree/master/chains"><img src="https://img.shields.io/badge/Arbitrum-Sepolia%20%7C%20Mainnet-blue?style=for-the-badge&logo=arbitrum" alt="Arbitrum"></a>
  <a href="https://github.com/heapchain/agent-heap/tree/master/agent/nodes/analyzer.py"><img src="https://img.shields.io/badge/LLM%20agnostic-multi%20model-FF6F61?style=for-the-badge" alt="Multi-Model"></a>
</p>

**Agent Heap** is a LangGraph-powered agent that continuously monitors DeFi lending protocols (Aave, Compound, Morpho) on Arbitrum, analyzes yields via LLM reasoning, and executes deposits using Kelly-criterion position sizing — all autonomously.

It runs on Arbitrum Sepolia today and is ready for mainnet deployment.

## Features

- **Autonomous loop** — 24/7 agent cycle (collect → analyze → signal → execute) on a configurable interval
- **Live yield data** — DeFiLlama APY + TVL feeds for Aave V3, Compound, and Morpho
- **LLM analysis** — Ranks pools by risk-adjusted return with any LLM (OpenAI, Anthropic, open-source); falls back to highest-APY heuristic
- **Kelly-criterion sizing** — Computes optimal position size based on win probability and expected return
- **Circuit breaker** — Daily PnL tracking; halts execution if drawdown exceeds configurable limit
- **Slippage protection** — Rejects trades exceeding configurable slippage threshold
- **Vector memory** — ChromaDB stores past decisions; the analyzer queries similar contexts to avoid repeated mistakes
- **CLI** — `agent-heap start | status | history` with rich terminal output
- **Simulation mode** — Dry-run without a funded wallet; real execution via Web3.py

## Quick start

```bash
git clone https://github.com/heapchain/agent-heap.git
cd agent-heap
uv sync
cp .env.example .env
uv run pytest -v              # 18 tests
agent-heap start --interval 21600   # 6h agent loop
```

Environment: `LLM_API_KEY` (for AI-powered analysis), `ARBITRUM_RPC`, `PRIVATE_KEY`, `DATABASE_URL`.

See [`.env.example`](.env.example) for all options.

## Architecture

Four-node LangGraph pipeline:

```
Collector → Analyzer → Signaler → Executor
(DeFiLlama)  (LLM +     (risk      (Web3.py)
              ChromaDB)  engine)
```

- **Collector** — Fetches live APY + TVL from DeFiLlama for Aave V3, Compound, Morpho on Arbitrum
- **Analyzer** — LLM pool ranking with ChromaDB memory recall; falls back to highest-APY heuristic
- **Signaler** — Computes Kelly-criterion position size, validates slippage, checks circuit breaker
- **Executor** — Builds, simulates, and/or signs + sends transactions via Web3.py

Results persist to PostgreSQL (SQLite in dev). Decision history is vector-indexed for future context.

## Roadmap

- [x] LangGraph pipeline, data feeds, risk modules, CLI, 18 tests
- [ ] **Mainnet** — Funded wallet on Arbitrum One, live deposit
- [ ] **Auto-compound** — Rebalance between pools based on risk-adjusted yield
- [ ] **Notifications** — Telegram/Discord alerts
- [ ] **Multi-chain** — Base, Optimism, Polygon

## License

MIT
