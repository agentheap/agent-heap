# Database — PostgreSQL Schema + ChromaDB

Set up persistence layer.

## Files to Create/Update

- `db/schema.py` — SQLAlchemy models
- `db/migrations/001_initial.sql` — raw SQL for initial schema
- `agent/memory/vector_store.py` — ChromaDB wrapper

## PostgreSQL Schema

- `strategies` table: id, name, protocol, pool, chain, created_at
- `trades` table: id, strategy_id, action (deposit/withdraw/rebalance), amount, token, tx_hash, gas_cost, simulated_pnl, timestamp
- `agent_state` table: id, status (running/paused/stopped), last_run, config JSON

## ChromaDB

- Collection `agent_memory` with documents representing past decisions
- `store_decision(decision: dict)` — embeds and stores
- `query_similar(context: str, k: int=3) -> list[dict]` — retrieves similar past decisions

## Acceptance Criteria

- [ ] `python -c "from db.schema import Base; print(Base.metadata.tables.keys())"` lists strategies, trades, agent_state
- [ ] `python -c "from agent.memory.vector_store import AgentMemory; m = AgentMemory(); m.store_decision({'action': 'test'}); print(m.query_similar('test', 1))"` works
- [ ] Migration SQL file exists and is valid SQLite-compatible
- [ ] Tests pass
- [ ] Code is committed

**Output when complete:** `<promise>COMPLETE</promise>`
