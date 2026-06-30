# CLI — Agent Loop

Build the Click CLI that boots the agent loop.

## Files to Create/Update

- `cli/main.py` — full Click CLI

## Commands

- `agent-heap start` — starts the agent loop:
  - Runs `run_agent()` from agent/graph.py
  - Runs on configurable interval (default: every 6 hours)
  - Logs each iteration to stdout via rich
  - Saves results to PostgreSQL
  - Continues until Ctrl+C
- `agent-heap status` — shows current agent state from PostgreSQL
- `agent-heap history` — shows last 10 trades/decisions

## Requirements

- Uses `rich` for pretty CLI output
- Interval configurable via `--interval` flag (seconds, default 21600)
- Graceful shutdown on Ctrl+C (saves state as "paused")
- `.env` file loaded via python-dotenv

## Acceptance Criteria

- [ ] `python -m cli.main start --interval 5` runs a loop every 5 seconds (testable)
- [ ] `python -m cli.main status` shows state without error
- [ ] `python -m cli.main history` shows last entries
- [ ] Ctrl+C gracefully stops and saves state
- [ ] Tests pass
- [ ] Code is committed

**Output when complete:** `<promise>COMPLETE</promise>`
