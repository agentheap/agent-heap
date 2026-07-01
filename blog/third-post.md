---

Title: From Zero to Mainnet: Deploying Agent Heap
Description: What it takes to go from passing tests to managing real funds on Arbitrum One.
Tags: deployment, arbitrum, devops
Published: true

---

# From Zero to Mainnet: Deploying Agent Heap

After 28 tests, 14 modules, and countless iterations, Agent Heap
is ready for mainnet. Here's what the deployment pipeline looks like.

## Testnet First

The agent runs on Arbitrum Sepolia, interacting with deployed
testnet contracts. This validates the full pipeline:
- Wallet connection and transaction signing
- Aave/Compound/Morpho protocol interactions
- ChromaDB memory persistence
- Buyback calculations

## Mainnet Checklist

1. **Funded wallet** — ETH for gas + USDC for deposits
2. **PRIVATE_KEY configured** — environment variable
3. **LLM provider key** — API access for yield analysis
4. **Circuit breaker calibrated** — mainnet limits differ
5. **Slippage thresholds** — tighter on mainnet

## The Agent Loop

Once deployed, the agent runs continuously:

```
while True:
    sleep(interval)
    yields = collect()         # DeFiLlama
    best = analyze(yields)     # LLM
    amount = size(best)        # Kelly criterion
    tx = execute(best, amount) # Web3.py
    record(tx)                 # SQLite + ChromaDB
```

## Security Considerations

- Private key never leaves the environment
- Circuit breaker halts on excess drawdown
- Slippage gate prevents unfavorable trades
- All transactions are standard DeFi operations
- No special permissions — agent uses a standard wallet

## Cost Breakdown

Deploying to Arbitrum One:

| Item | Cost |
|------|------|
| Gas per deposit | ~$0.02-0.10 |
| Approve tx | ~$0.01-0.05 |
| Weekly gas (daily deposits) | ~$0.20-0.50 |
| LLM API calls | ~$0.01-0.05 per analysis |
| **Monthly operating** | **~$5-15** |

The economics work if the deposited capital is large enough for
yield returns to exceed operational costs.
