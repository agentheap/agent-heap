# Go CLI Rewrite — Agent Heap

**Status:** Draft  
**Author:** Mayor  
**Date:** 2026-07-01  
**Priority:** P1  
**Drivers:** Remove Python Click dependency, add Gas Town-style agent coordination

---

## 1. Motivation

The current CLI (`cli/main.py`) is 224 lines of Python Click with Rich formatting.
It works, but:

- Ties the CLI to the full Python stack (web3.py, LangGraph, Chroma, SQLAlchemy)
- No Gas Town features (beads, rigs, daemon patrols)
- `wallet generate` / `wallet new` are duplicate commands
- `start` loop has no heartbeat or daemon integration
- Single-file design doesn't scale

A Go rewrite using Cobra gives us a static binary, zero Python dependency at
the CLI layer, and a clean surface for Gas Town-style agent coordination.

---

## 2. Architecture

```
agent-heap/
├── cmd/
│   └── agent-heap/         # main.go — cobra root, ~30 lines
│       └── main.go
├── internal/
│   ├── cmd/                # Command implementations (one file per command)
│   │   ├── start.go        # Agent loop runner
│   │   ├── status.go       # Agent health & heartbeat
│   │   ├── history.go      # Recent decision log
│   │   ├── wallet.go       # Wallet group: generate, balance, new
│   │   ├── memory.go       # Chroma vector store queries
│   │   └── bead.go         # Gas Town bead tracking (Phase 2)
│   ├── agent/              # Agent graph bridge → Python subprocess
│   │   └── runner.go
│   ├── db/                 # SQLite persistence (CGO-free)
│   │   └── sqlite.go
│   ├── wallet/             # EVM wallet operations via go-ethereum
│   │   └── evm.go
│   ├── memory/             # Chroma REST API client
│   │   └── chroma.go
│   ├── town/               # Gas Town config: town.json, rigs.json, daemon.json
│   │   └── config.go
│   └── bead/               # Bead tracking (Dolt/JSONL client)
│       └── client.go
├── go.mod
├── go.sum
└── Makefile
```

### 2.1 Data Flow

```
┌──────────┐     ┌─────────────┐     ┌──────────────┐
│  Cobra   │────▶│  internal/  │────▶│  agent/      │
│  Root    │     │  cmd/       │     │  runner.go   │──▶ python3 -m agent.graph
└──────────┘     │             │     └──────────────┘
                 │  start.go   │     ┌──────────────┐
                 │  status.go  │────▶│  internal/db │──▶ SQLite
                 │  history.go │     └──────────────┘
                 │  wallet.go  │────▶│  internal/   │──▶ go-ethereum RPC
                 │  memory.go  │────▶│  wallet/     │
                 │  bead.go    │────▶│  internal/   │──▶ Chroma REST
                 └─────────────┘     │  memory/     │
                                     └──────────────┘
```

---

## 3. Commands

### Phase 1 — Parity (7 commands, same interface as current Python CLI)

#### `agent-heap start [--interval 21600]`

Start the agent loop. Writes heartbeat, calls Python graph as subprocess, logs
decisions to SQLite, responds to SIGINT/SIGTERM for graceful shutdown.

- Writes `.agent-heap/heartbeat` every 30s with UNIX timestamp
- On SIGINT/SIGTERM: writes "stopped" state, exits cleanly
- Calls `python3 -m agent.graph` via `os/exec` each loop iteration

Blocks: **Heartbeat written, agent state = "running"**

#### `agent-heap status`

Read agent state + heartbeat from SQLite. Prints:

| Field | Value |
|-------|-------|
| Status | running / stopped / never run |
| Last Run | ISO timestamp |
| Uptime | duration string (from heartbeat) |
| PID | process ID if running |

#### `agent-heap history [--limit 10]`

Query recent `trades` table. Prints table with columns: ID, Action, Token,
Amount, Timestamp.

#### `agent-heap wallet generate [--output path]`

Generate a fresh EVM wallet using `crypto.GenerateKey()` from go-ethereum.

- Derive address from public key
- Optionally write encrypted JSON keystore to `--output`
- Print address + funding instructions
- PRIVATE_KEY env var determines network

#### `agent-heap wallet balance`

Read `PRIVATE_KEY`, derive address, query RPC for ETH balance.

- Uses `ARBITRUM_RPC` / network config from env
- Prints: Address, ETH balance, Network

#### `agent-heap wallet new [--output path]`

Alias for `wallet generate` (preserve existing muscle memory).

#### `agent-heap memory [--last 10]`

Query Chroma vector store directly via REST API (`/api/v1/collections/{name}/get`).

- Falls back to "Could not connect" message on connection error
- Prints: #, Action, Protocol, Pool, Amount, Reason

### Phase 2 — Gas Town Features (new commands)

#### `agent-heap bead list [--status open|closed]`

List beads from the Dolt/JSONL store. Mirrors Gas Town `bd list`.

#### `agent-heap bead create <title> [--priority P2] [--body "..."]`

Create a new bead (issue).

#### `agent-heap bead close <id> [--reason "..."]`

Close a bead.

#### `agent-heap rig list`

List registered rigs from `rigs.json` / `town.json`. Show git URL, last sync,
health status.

#### `agent-heap rig health <name>`

Ping a rig's working tree and git remote. Report reachable / stale / unknown.

#### `agent-heap daemon status`

Read `daemon.json`, report which patrols are enabled and their last fire time
(from `.runtime/` or heartbeat files).

---

## 4. Key Design Decisions

| Concern | Choice | Rationale |
|---------|--------|-----------|
| **CLI framework** | `spf13/cobra` | Standard Go CLI; subcommands, flags, help |
| **Table output** | `olekukonez/tablewriter` | Familiar tabular output, like Rich Table |
| **Database** | `modernc.org/sqlite` | Same schema as Python SQLite, zero CGO |
| **EVM** | `go-ethereum` | Wallet gen, balance check, tx building |
| **Chroma bridge** | Raw HTTP to REST API | No official Go SDK; Chroma's REST is simple |
| **Agent graph bridge** | `os/exec` subprocess | LangGraph has no Go port; keeps existing graph workable |
| **Config format** | JSON (town.json, rigs.json, daemon.json) | Matches Gas Town format exactly |
| **Beads** | Dolt SQL + JSONL export | Reuse existing beads infrastructure |

---

## 5. Dependencies (go.mod)

```
require (
    github.com/spf13/cobra v1.8
    github.com/ethereum/go-ethereum v1.14
    modernc.org/sqlite v1.33
    github.com/olekukonez/tablewriter v0.0.5
)
```

---

## 6. Phase Plan

### Phase 1 — Drop-in Parity
Files: `cmd/agent-heap/main.go`, `internal/cmd/{start,status,history,wallet,memory}.go`,
`internal/db/sqlite.go`, `internal/wallet/evm.go`, `internal/memory/chroma.go`,
`internal/agent/runner.go`, `go.mod`, `Makefile`

**Acceptance:**
- `agent-heap start --interval 30` runs a loop and logs decisions
- `agent-heap status` shows running/stopped state
- `agent-heap history` shows recent trades
- `agent-heap wallet generate` creates a valid EVM wallet
- `agent-heap wallet balance` queries RPC
- `agent-heap wallet new` is an alias for generate
- `agent-heap memory` queries Chroma
- `make build` produces a static binary
- Python CLI still works (side-by-side)

### Phase 2 — Gas Town Features
Files: `internal/cmd/bead.go`, `internal/town/config.go`, `internal/bead/client.go`

**Acceptance:**
- `agent-heap bead list` shows open beads from Dolt
- `agent-heap bead create "fix something"` creates a new bead
- `agent-heap bead close <id>` closes a bead
- `agent-heap rig list` shows registered rigs
- `agent-heap daemon status` shows patrol state

### Phase 3 — Standalone Agent (future)
- Port the agent graph decision logic to Go
- Replace Python subprocess with direct LangChain/LiteLLM calls from Go
- This is a significantly larger effort and not scoped here

---

## 7. Migration

1. Write `cmd/agent-heap/main.go` + Phase 1 internals in `internal/`
2. Both CLIs coexist: Python `agent-heap` entry point still works
3. Add Phase 2 Gas Town features without touching Python at all
4. When Python CLI is no longer used, remove `[project.scripts] agent-heap` from `pyproject.toml`
5. Keep `cli/main.py` as the agent execution engine (called as subprocess)
6. Phase 3: port the graph engine to Go (if warranted)

---

## 8. Files to Touch

| File | Action |
|------|--------|
| `docs/go-cli-rewrite-spec.md` | ✅ This spec |
| `cmd/agent-heap/main.go` | Create |
| `internal/cmd/start.go` | Create |
| `internal/cmd/status.go` | Create |
| `internal/cmd/history.go` | Create |
| `internal/cmd/wallet.go` | Create |
| `internal/cmd/memory.go` | Create |
| `internal/cmd/bead.go` | Create |
| `internal/db/sqlite.go` | Create |
| `internal/wallet/evm.go` | Create |
| `internal/memory/chroma.go` | Create |
| `internal/town/config.go` | Create |
| `internal/bead/client.go` | Create |
| `internal/agent/runner.go` | Create |
| `Makefile` | Create |
| `go.mod` | Create |
| `go.sum` | Create |
| `pyproject.toml` | Remove `[project.scripts] agent-heap` (Phase 2 end) |
