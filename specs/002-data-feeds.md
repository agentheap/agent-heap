# Data Feeds — CoinGecko + DeFiLlama

Implement data fetching from free tier APIs.

## Files to Create/Update

- `data/coingecko.py` — fetch token prices by contract address (CoinGecko free tier)
- `data/defillama.py` — fetch lending pool APYs from DeFiLlama (Aave, Compound, Morpho on Arbitrum)

## Requirements

- `coingecko.py` has `get_price(token_address: str, chain: str) -> float` — returns current USD price
- `defillama.py` has `get_yields(protocols: list[str]) -> list[dict]` — returns list of pools with: protocol, pool, apy, tvl
- Default protocols to scan: Aave, Compound, Morpho on Arbitrum
- Both modules handle API errors gracefully (return None / empty list on failure)
- Use httpx with 10s timeout
- No API key needed for free tier

## Acceptance Criteria

- [ ] `python -c "from data.coingecko import get_price; print(get_price('0x...', 'arbitrum'))"` runs without error
- [ ] `python -c "from data.defillama import get_yields; print(get_yields(['aave', 'compound']))"` runs without error
- [ ] Both functions handle network errors (try/except)
- [ ] Tests pass
- [ ] Code is committed

**Output when complete:** `<promise>COMPLETE</promise>`
