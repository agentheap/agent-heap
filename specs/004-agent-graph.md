# Agent Graph — LangGraph Yield Optimizer

Build the core LangGraph agent with 4 nodes and the yield optimization strategy.

## Files to Create/Update

- `agent/graph.py` — full LangGraph definition
- `agent/nodes/collector.py` — fetches yields from DeFiLlama
- `agent/nodes/analyzer.py` — Mistral LLM reasons best pool
- `agent/nodes/signal.py` — outputs structured action
- `agent/nodes/executor.py` — simulates tx via web3.py (testnet, no real funds)
- `agent/strategies/yield_optimizer.py` — strategy logic

## Graph Flow

1. `collector` → calls defillama.get_yields() for Aave/Compound/Morpho on Arbitrum
2. `analyzer` → calls NVIDIA NIM API (OpenAI-compatible, Mistral/Llama model) with prompt: "Given these pools: {pools}, which has best risk-adjusted yield? Respond with pool name and reason."
3. `signaler` → parses LLM response into structured action: `{"action": "deposit", "protocol": "aave", "pool": "...", "amount": 0.01, "reason": "..."}`
4. `executor` → builds and simulates transaction via web3.py on Arbitrum Sepolia. Logs result but doesn't send real tx (no funds yet).

## State

Define `AgentState` TypedDict with fields: yields, analysis, signal, tx_result, errors

## Acceptance Criteria

- [ ] `python -c "from agent.graph import run_agent; result = run_agent(); print(result)"` completes one full loop (simulated, no real tx)
- [ ] Each node is a separate function in its own file
- [ ] Analyzer handles NVIDIA NIM API being unavailable (falls back to simple heuristic: highest APY)
- [ ] NVIDIA_NIM_API_KEY env var is loaded and used for auth
- [ ] Executor simulates tx, doesn't require real funds
- [ ] All 4 node files import without error
- [ ] Tests pass
- [ ] Code is committed

**Output when complete:** `<promise>COMPLETE</promise>`
