# Scaffold — Project Structure

Create the project skeleton for Agent Heap.

## Files to Create

- `pyproject.toml` — Python project config with dependencies (langchain, langgraph, web3, chromadb, psycopg2, click, httpx, python-dotenv, mistralai, rich, psycopg2-binary, sqlalchemy)
- `agent/__init__.py`
- `agent/graph.py` — LangGraph definition (stub with placeholder nodes)
- `agent/nodes/__init__.py`
- `agent/nodes/collector.py` — stub
- `agent/nodes/analyzer.py` — stub
- `agent/nodes/signal.py` — stub
- `agent/nodes/executor.py` — stub
- `agent/memory/__init__.py`
- `agent/memory/vector_store.py` — ChromaDB init stub
- `chains/__init__.py`
- `chains/arbitrum.py` — Arbitrum Sepolia RPC config
- `chains/base_chain.py` — Base Sepolia RPC config
- `data/__init__.py`
- `data/coingecko.py` — stub
- `data/defillama.py` — stub
- `db/__init__.py`
- `db/schema.py` — stub
- `risk/__init__.py`
- `risk/position_sizing.py` — stub
- `risk/circuit_breaker.py` — stub
- `cli/__init__.py`
- `cli/main.py` — stub with click group
- `.env.example` — with RPC vars + NVIDIA_NIM_API_KEY
- `docker-compose.yml` — postgres + chroma services
- `Dockerfile`
- `README.md` — one-line description

## Acceptance Criteria

- [ ] `pyproject.toml` exists with all dependencies listed
- [ ] All directories above are created with `__init__.py`
- [ ] `python -m pip install -e .` succeeds (install in editable mode)
- [ ] `python -c "from agent.graph import agent_graph"` imports without error
- [ ] `python -m cli.main --help` shows help text
- [ ] `docker-compose config` validates without error
- [ ] `.env.example` has placeholders for ARBITRUM_RPC, BASE_RPC, MISTRAL_API_KEY, DATABASE_URL, PRIVATE_KEY
- [ ] Code is committed with message "scaffold: project structure"

**Output when complete:** `<promise>COMPLETE</promise>`
