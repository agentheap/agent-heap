# Security Overview — Agent Heap

> Honest assessment of the security posture of this project.
> Last updated: 2026-07-02

---

## Current Security State: **Improved — Still Not Production Ready**

Agent Heap has been hardened with keystore encryption, spending limits, address allowlisting, and rate limiting. It has **not** been professionally audited. Use with caution and only with funds you're willing to lose.

---

## Key Risks

### 1. Private Key Management — HIGH → ✅ MITIGATED

```
Current: KEYSTORE_FILE + KEYSTORE_PASSPHRASE (encrypted) OR PRIVATE_KEY (plaintext fallback)
```

**Fix:** Private keys can now be encrypted with AES-256-GCM using a scrypt-derived key from a passphrase.
- `agent-heap wallet generate --encrypt --passphrase "..." --output wallet.json` — creates encrypted keystore
- `agent-heap wallet encrypt key.json --passphrase "..." --output wallet.json` — encrypt existing key
- `agent-heap security` — shows if keystore is active
- The agent auto-detects keystore vs plaintext at runtime

**Still missing:**
- Hardware wallet support (Ledger, Trezor)
- Multi-sig for withdrawal addresses
- Key sharding or threshold signing

### 2. Transaction Signing — HIGH → ✅ MITIGATED

**Fix:** Three layers of protection now exist:
- **Address allowlist** — only known protocol addresses (Aave, Compound, Morpho, USDC) are valid recipients. Rejects transactions to unknown addresses.
- **Spending limits** — `MAX_TX_AMOUNT` caps per-transaction amount, `DAILY_TX_LIMIT` caps daily volume. Both checked in Go CLI before execution.
- **Rate limiting** — `MAX_TX_PER_HOUR` prevents runaway loops from burning gas.
- `agent-heap run` and `agent-heap start` check all limits before executing.

**Still missing:**
- Transaction simulation via eth_call before signing
- Human-in-the-loop approval for large amounts

### 3. LLM Prompt Injection — MEDIUM

**The problem:** The analyzer node sends yield data to an LLM and trusts the LLM's output. If yield data is manipulated or the LLM provider is compromised, the agent could be told to send funds to a malicious address.

**Realistically:** This is a known attack surface for all LLM-based agents. Current mitigations are minimal (hardcoded protocol addresses).

### 4. Circuit Breaker — MEDIUM

**Current:** The circuit breaker tracks daily PnL and halts on 5% drawdown. This works for market losses but would NOT stop:
- An attacker draining the wallet directly
- A manipulated LLM sending funds to a wrong address
- Gas waste on failed transactions

### 5. Dependencies — MEDIUM

The project depends on:
- `go-ethereum` (Go) — battle-tested, well-audited
- `modernc.org/sqlite` (Go) — pure Go SQLite, no CGO
- `web3.py` (Python) — mature library
- `chromadb` (Python) — vector database, smaller security surface
- Various LLM SDKs via LiteLLM

The risk is the supply chain: compromised PyPI/npm packages could inject malicious code.

### 6. Gas Management — LOW-MEDIUM

**Current:** Gas estimation with 20% buffer, EIP-1559 fee calculation. This prevents most out-of-gas failures but does not protect against:
- Gas price manipulation on L2
- MEV attacks on deposits

### 7. No Access Controls — MEDIUM

Anyone who can run the binary has full control. There are no:
- User roles
- API keys for the CLI
- Audit log of CLI commands
- Rate limiting on the agent loop

---

## What IS in place

| Control | What it does |
|---------|-------------|
| **Circuit breaker** | Halts on 5% daily drawdown |
| **Slippage protection** | Rejects trades exceeding configurable threshold |
| **Gas estimation buffer** | 20% margin prevents OOG failures |
| **Static binary** | No runtime dependency injection via Python at CLI layer |
| **Env isolation** | `.env` in `.gitignore` — won't be accidentally committed |
| **Graceful shutdown** | SIGINT/SIGTERM handler stops the loop cleanly |
| **Address derivation validation** | Invalid private keys are rejected before use |

---

## Recommendations Before Using With Real Funds

### Minimum (before any real money)

- [ ] Use a **dedicated wallet** with only the gas + USDC you're willing to lose
- [ ] Never use a main wallet, exchange deposit address, or wallet with significant funds
- [ ] Run on testnet first (Arbitrum Sepolia) for at least 1 week
- [ ] Review all protocol addresses in `agent/nodes/abi/__init__.py` before mainnet
- [ ] Set up monitoring — know immediately if the agent sends an unexpected transaction

### Strongly recommended

- [ ] Add **spending limits** to the executor (max per tx, max per day)
- [ ] **Allowlist** protocol addresses in the executor — reject any tx to an unknown address
- [ ] Encrypt `PRIVATE_KEY` with a passphrase (geth keystore format)
- [ ] Add a **human-in-the-loop** for transactions above a threshold
- [ ] Rate-limit the agent loop (max N transactions per hour)

### If this were production

- [ ] Professional third-party security audit
- [ ] Hardware wallet support (Ledger via EIP-712)
- [ ] Multi-sig withdrawal (Safe.global)
- [ ] Formal verification of protocol interactions
- [ ] Bug bounty program
- [ ] Insurance for deposited funds

---

## Amounts That Would Be Reasonable

| Stage | Max at risk | Rationale |
|-------|------------|-----------|
| **Testnet** | $0 (faucet ETH) | No real money |
| **Experimental** | $50–$100 | Amount you'd accept losing entirely |
| **Personal use** | $500–$1,000 | After spending limits + address allowlist added |
| **Production** | $10,000+ | After audit, multi-sig, hardware wallet |

---

## Reporting a Security Issue

This project does not currently have a security contact or disclosure policy.
If you find a vulnerability, please open a GitHub issue for now.

---

## Summary

| Aspect | Rating | Notes |
|--------|--------|-------|
| Private key storage | ✅ Encrypted | AES-256-GCM with scrypt key derivation |
| Transaction safety | ✅ Limited | Spending limits + address allowlist + rate limiting |
| LLM manipulation | ⚠️ Partial | Protocol addresses hardcoded |
| Circuit breaker | ✅ Working | PnL tracking, 5% halt threshold |
| Slippage | ✅ Working | Configurable max slippage |
| Dependency risk | ⚠️ Moderate | Standard supply chain risk |
| Access control | ❌ None | Anyone with the binary has full control |
| Audit | ❌ None | No professional security review |

**Bottom line:** Significantly hardened. Safe for personal use with small amounts.
**Not safe** for institutional funds without a professional audit, multi-sig, and hardware wallet support.
