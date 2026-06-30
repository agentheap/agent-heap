import os
import signal
import time
from datetime import datetime, timezone

import click
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table

from agent.graph import run_agent
from db.session import get_recent_trades, get_agent_state, save_trade, set_agent_status

load_dotenv()
console = Console()
running = True


def signal_handler(sig, frame):
    global running
    running = False
    console.print("\n[yellow]Shutting down gracefully...[/yellow]")


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


@click.group()
def cli():
    pass


@cli.command()
@click.option("--interval", default=21600, help="Loop interval in seconds")
def start(interval: int):
    """Start the agent loop."""
    global running
    console.print("[bold green]Agent Heap[/bold green] starting...")
    console.print(f"Interval: {interval}s | Ctrl+C to stop")
    set_agent_status("running")

    while running:
        try:
            result = run_agent()
            ts = datetime.now(timezone.utc).isoformat()
            console.print(f"[blue]{ts}[/blue] Agent run complete")

            tx = result.get("tx_result")
            if tx:
                console.print(
                    f"  Action: {tx['action']} | Protocol: {tx['protocol']} | Pool: {tx['pool']}"
                )
                save_trade(
                    action=tx["action"],
                    amount=tx.get("amount", 0),
                    token=tx.get("pool", "unknown"),
                    simulated_pnl=0,
                )

            for _ in range(int(interval / 0.5)):
                if not running:
                    break
                time.sleep(0.5)
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

    set_agent_status("stopped")
    console.print("[yellow]Agent stopped.[/yellow]")


@cli.command()
def status():
    """Show agent state."""
    state = get_agent_state()
    table = Table(title="Agent Heap Status")
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="white")
    table.add_row("Status", state.status if state else "never run")
    table.add_row(
        "Last Run", str(state.last_run) if state and state.last_run else "N/A"
    )
    console.print(table)


@cli.command()
def history():
    """Show recent agent decisions."""
    trades = get_recent_trades(10)
    if not trades:
        console.print("[yellow]No history yet[/yellow]")
        return
    table = Table(title="Recent Decisions")
    table.add_column("ID", style="dim")
    table.add_column("Action")
    table.add_column("Token")
    table.add_column("Amount")
    table.add_column("Timestamp")
    for t in trades:
        table.add_row(
            str(t.id),
            t.action,
            t.token,
            str(t.amount),
            str(t.timestamp) if t.timestamp else "",
        )
    console.print(table)


if __name__ == "__main__":
    cli()
