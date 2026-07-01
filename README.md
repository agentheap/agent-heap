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
  <a href="https://github.com/agentheap/agent-heap/actions"><img src="https://img.shields.io/badge/tests-24%20passing-brightgreen?style=for-the-badge&logo=pytest" alt="Tests"></a>
  <a href="https://github.com/agentheap/agent-heap"><img src="https://img.shields.io/badge/Python-3.11%2B-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python"></a>
  <a href="https://github.com/agentheap/agent-heap"><img src="https://img.shields.io/badge/LangGraph-✓-8b5cf6?style=for-the-badge" alt="LangGraph"></a>
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
- **CLI** — `agent-heap start | status | history` with rich terminal output

## Quick start

```bash
git clone https://github.com/agentheap/agent-heap.git
cd agent-heap
uv sync
cp .env.example .env
uv run pytest -v              # 24 tests
agent-heap start --interval 21600   # 6h agent loop
```

Set `LLM_MODEL` (e.g. `gpt-4o`, `claude-sonnet-4`) + your provider's API key in `.env`.

## Architecture

```
Collector → Analyzer → Signaler → Executor → Buyback
(DeFiLlama)  (LLM +     (risk      (Web3.py)  (HEAP token
              ChromaDB)  engine)               buy & burn)
```

## Tests

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 Agent Flow       ■■■■■■■■■■■■■■■  6/6  ✅
 Risk Models      ■■■■■■■■■■■■■■■  4/4  ✅
 Data Feeds       ■■■■■■■■■■■■■■■  2/2  ✅
 Memory & CLI     ■■■■■■■■■■■■■■■  2/2  ✅
 HEAP Buyback     ■■■■■■■■■■■■■■■  10/10 ✅
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 TOTAL: 24/24 PASSING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Roadmap

- [x] LangGraph pipeline, data feeds, risk modules, CLI
- [x] HEAP token buyback loop (24 tests)
- [ ] **Mainnet** — Funded wallet, live deposits on Arbitrum One
- [ ] **Auto-compound** — Rebalance between pools
- [ ] **Notifications** — Telegram/Discord alerts
- [ ] **Multi-chain** — Base, Optimism, Polygon

## License

MIT
