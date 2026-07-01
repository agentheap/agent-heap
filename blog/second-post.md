---

Title: How Our Agent Chooses the Best Yield Pool
Description: The math behind Kelly-criterion position sizing and LLM-powered yield analysis in Agent Heap.
Tags: defi, yield, kelly-criterion, ai
Published: true

---

# How Our Agent Chooses the Best Yield Pool

When there are 20+ lending pools across Aave, Compound, and Morpho
on Arbitrum, which one do you deposit into? Agent Heap makes this
decision in three stages.

## Stage 1: Data Collection

Every cycle, the collector fetches live data from DeFiLlama:

```python
# Simplified — fetches 200+ pools, filters to targets
pools = defillama.get_pools()
targets = [p for p in pools if p["protocol"] in ["aave-v3", "compound-v3", "morpho-blue"]]
```

Each pool comes with APY, TVL, and chain information.

## Stage 2: LLM Analysis

The analyzer formats the pools into a prompt and sends it to an LLM.
Past decisions from ChromaDB are injected as few-shot examples:

```
You are a DeFi yield analyst. Given these lending pools, pick the
one with the best risk-adjusted yield.

Pools:
1. Aave V3 / USDC: 5.2% APY, $100M TVL on Arbitrum
2. Compound / USDC: 4.8% APY, $80M TVL on Arbitrum
3. Morpho Blue / USDC: 6.1% APY, $50M TVL on Arbitrum

Past decisions:
1. deposit on aave/usdc -- stable returns are preferable
```

The LLM considers APY, TVL (liquidity safety), and past performance
before recommending.

## Stage 3: Kelly-Criterion Sizing

Once a pool is selected, the signaler computes the optimal deposit
amount using the Kelly criterion:

```python
win_prob = min(0.99, apy / (apy + avg_apy))
win_ratio = apy / avg_apy
fraction = kelly_fraction(win_prob, win_ratio)
amount = capital * fraction
```

This ensures the agent never over-allocates to a single position.

## Why This Matters

A simple "always pick highest APY" strategy would have deposited
into risky pools with low TVL. The LLM + Kelly combination catches
trade-offs that a naive script would miss.
