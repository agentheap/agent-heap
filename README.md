# Agent Heap

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](pyproject.toml)
[![Tests](https://img.shields.io/badge/Tests-18%20passing-brightgreen.svg)](tests/)
[![Base Sepolia](https://img.shields.io/badge/Blockchain-Base%20Sepolia-0052FF.svg)](https://sepolia.basescan.org/address/0x93b4C000ec98474ECacf619bec969bd9bBbd87f7)
[![Contract](https://img.shields.io/badge/$HEAP-ERC20-8247E5.svg)](https://sepolia.basescan.org/address/0x93b4C000ec98474ECacf619bec969bd9bBbd87f7)

> **Autonomous AI agent for multi-chain yield optimization.**
>
> Collects live yields from DeFiLlama, analyzes them via LLM, executes deposits on-chain.
> Built entirely by AI agents — orchestrated by Gas Town, implemented by Claude Code.

---

## 🧠 Architecture

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ Collector │───▶│ Analyzer │───▶│Risk Check│───▶│ Signaler │───▶│ Executor │───▶│ Buyback  │
│ DeFiLlama │    │  LLM     │    │ Kelly/CB │    │  Signal  │    │  web3.py │    │  → HEAP  │
└──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘
```

A **LangGraph state machine** with 6 nodes. Each run collects, analyzes, risk-checks, signals, executes, and buybacks — fully autonomous.

---

## ✨ Features

| Module | What It Does | Status |
|--------|-------------|--------|
| **DeFiLlama Feed** | Fetches live APYs for Aave, Compound, Morpho on Arbitrum & Base | ✅ |
| **LLM Analysis** | NVIDIA NIM (Mistral-7B) picks best risk-adjusted pool | ✅ |
| **Position Sizing** | Kelly criterion + fixed-fraction capital allocation | ✅ |
| **Circuit Breaker** | Halts trading after 5% daily drawdown | ✅ |
| **Slippage Guard** | Rejects trades exceeding 100bps slippage | ✅ |
| **Vector Memory** | ChromaDB recall of past decisions for context | ✅ |
| **CLI Loop** | `agent-heap start --interval 21600` — runs forever | ✅ |
| **$HEAP Token** | ERC20 with buyback mechanism (1B supply) | ✅ |
| **Test Suite** | 18 passing tests across all modules | ✅ |

---

## 🚀 Quick Start

```bash
# Install
git clone https://github.com/heapchain/agent-heap
cd agent-heap
pip install -e .

# Configure
cp .env.example .env
# Add your WALLET_PRIVATE_KEY and RPC endpoints

# Run (single pass)
agent-heap start --interval 1

# Run (6h loop)
agent-heap start --interval 21600

# Check status
agent-heap status
agent-heap history
```

---

## 🪙 $HEAP Token

Deployed on **Base Sepolia**:

| Field | Value |
|-------|-------|
| **Contract** | [`0x93b4C0...87f7`](https://sepolia.basescan.org/address/0x93b4C000ec98474ECacf619bec969bd9bBbd87f7) |
| **Name** | Agent Heap |
| **Symbol** | $HEAP |
| **Supply** | 1,000,000,000 |
| **Standard** | ERC20 |

Deploy your own:
```bash
# Testnet (free)
agent-heap deploy --testnet

# Mainnet (needs real ETH)
npm run deploy
```

---

## 🔧 Stack

```
LangGraph    → Agent orchestration
web3.py      → Blockchain interaction
ChromaDB     → Vector memory
SQLAlchemy   → Trade persistence
Solidity     → Token contract
Click        → CLI framework
Rich         → Terminal UI
pytest       → Test framework
```

---

## 📄 License

MIT — do what you want, just don't blame us.

---

<p align="center">
  <sub>Built by agents, for agents. Generated entirely by Claude Code.</sub>
  <br>
  <sub><a href="https://github.com/heapchain">@heapchain</a> — autonomous AI agents for DeFi</sub>
</p>
