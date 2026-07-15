#!/usr/bin/env python3
"""CLI entry point for fde-intel."""
import asyncio
from pathlib import Path
import typer
from rich.console import Console
from fde_intel.orchestrator import run_research
from fde_intel.reporter import render_terminal, render_markdown

app = typer.Typer(help="FDE Intelligence Agent — pre-call briefings for Forward Deployed Engineers")
console = Console()


@app.command()
def research(
    target: str = typer.Argument(..., help='Technology or vendor to research, e.g. "Snowflake"'),
    output: bool = typer.Option(False, "--output", "-o", help="Save briefing as markdown to reports/output/"),
):
    """Run multi-agent research on a technology and generate an FDE briefing."""
    console.print(f"\n[bold cyan]Researching:[/bold cyan] {target}")
    console.print("[dim]Spawning 4 specialist agents in parallel...[/dim]\n")

    briefing = asyncio.run(run_research(target))
    render_terminal(briefing)

    if output:
        output_dir = Path("reports/output")
        path = render_markdown(briefing, output_dir)
        console.print(f"\n[green]Briefing saved:[/green] {path}")


if __name__ == "__main__":
    app()
