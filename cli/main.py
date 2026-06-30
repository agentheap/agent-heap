import os
import signal
import time
from datetime import datetime, timezone
from pathlib import Path

import click
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table

from agent.graph import run_agent
from agent.memory.vector_store import AgentMemory
from chains.arbitrum import ARBITRUM_NETWORK
from db.session import get_recent_trades, get_agent_state, save_trade, set_agent_status
from wallet.generator import (
    check_balance,
    generate_wallet,
    print_funding_instructions,
)

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


@cli.group()
def wallet():
    """Wallet management commands."""
    pass


@wallet.command()
@click.option(
    "--output", "-o", default=None, help="Write wallet JSON to this file path"
)
def generate(output: str | None):
    """Generate a fresh wallet for the active Arbitrum network.

    Uses ARBITRUM_NETWORK env var (default: sepolia) to determine the target network.
    """
    network_label = "Arbitrum One mainnet" if ARBITRUM_NETWORK == "mainnet" else "Arbitrum Sepolia"
    console.print(f"[bold]Generating wallet for {network_label}...[/bold]")

    wallet = generate_wallet(output_path=output)

    console.print(f"[green]✓[/green] Wallet address: [bold]{wallet.address}[/bold]")

    if output:
        abs_path = Path(output).resolve()
        console.print(f"[green]✓[/green] Wallet saved to: [bold]{abs_path}[/bold]")
        console.print("    [yellow]⚠ Keep this file secure![/yellow]")

    print_funding_instructions(wallet)


@wallet.command()
def balance():
    """Check the balance of the configured wallet.

    Reads PRIVATE_KEY from environment and queries the current network.
    """
    result = check_balance()

    if "error" in result:
        console.print(f"[red]Error:[/red] {result['error']}")
        console.print("\n[yellow]Set PRIVATE_KEY in your environment to check balance.[/yellow]")
        return

    table = Table(title=f"Wallet Balance ({result['network']})")
    table.add_column("Asset", style="cyan")
    table.add_column("Balance", style="white")
    table.add_row("Address", result.get("address", "unknown"))
    table.add_row("ETH", f"{result['eth']:.6f}")
    console.print(table)


@wallet.command()
@click.option("--output", "-o", default=None, help="Write wallet JSON to this file path")
def new(output: str | None):
    """Alias for 'wallet generate' — create a new wallet and print funding instructions."""
    network_label = "Arbitrum One mainnet" if ARBITRUM_NETWORK == "mainnet" else "Arbitrum Sepolia"
    console.print(f"[bold]Generating wallet for {network_label}...[/bold]")

    wallet = generate_wallet(output_path=output)

    console.print(f"[green]✓[/green] Wallet address: [bold]{wallet.address}[/bold]")

    if output:
        abs_path = Path(output).resolve()
        console.print(f"[green]✓[/green] Wallet saved to: [bold]{abs_path}[/bold]")

    print_funding_instructions(wallet)


@cli.command()
def memory():
    """Show recent vector memory entries."""
    try:
        mem = AgentMemory()
        all_entries = mem.collection.get()
    except Exception:
        console.print("[red]Could not connect to Chroma vector store[/red]")
        return

    if not all_entries["ids"]:
        console.print("[yellow]No memory entries yet[/yellow]")
        return

    entries = [
        dict(m) for m in (all_entries["metadatas"] or [])
        if m is not None
    ]

    table = Table(title="Vector Memory (last 10)")
    table.add_column("#", style="dim")
    table.add_column("Action")
    table.add_column("Protocol")
    table.add_column("Pool")
    table.add_column("Amount", justify="right")
    table.add_column("Reason")
    for i, m in enumerate(entries[-10:], 1):
        table.add_row(
            str(i),
            str(m.get("action", "")),
            str(m.get("protocol", "")),
            str(m.get("pool", "")),
            str(m.get("amount", "")),
            str(m.get("reason", ""))[:50],
        )
    console.print(table)
if __name__ == "__main__":
    cli()
