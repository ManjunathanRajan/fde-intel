"""Render an FDEBriefing to terminal and optionally to a markdown file."""
from __future__ import annotations
import json
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box
from fde_intel.models import FDEBriefing

console = Console()

_COMPLEXITY_COLOR = {"low": "green", "medium": "yellow", "high": "red"}
_CONFIDENCE_COLOR = {"high": "green", "medium": "yellow", "low": "red"}


def render_terminal(briefing: FDEBriefing) -> None:
    console.print()
    console.print(
        Panel(
            f"[bold cyan]FDE Intelligence Briefing[/bold cyan]\n[white]{briefing.target}[/white]",
            box=box.DOUBLE,
        )
    )

    console.print(
        Panel(briefing.executive_summary, title="Executive Summary", border_style="cyan")
    )

    complexity_color = _COMPLEXITY_COLOR[briefing.integration_complexity]
    console.print(
        f"\n[bold]Integration Complexity:[/bold] "
        f"[{complexity_color}]{briefing.integration_complexity.upper()}[/{complexity_color}]"
    )

    for finding in [
        briefing.tech_fit,
        briefing.cost_signals,
        briefing.risk_flags,
        briefing.competitor_landscape,
    ]:
        title_map = {
            "tech": "Technical Fit",
            "cost": "Cost Signals",
            "risk": "Risk Flags",
            "competitors": "Competitor Landscape",
        }
        conf_color = _CONFIDENCE_COLOR[finding.confidence]
        title = (
            f"{title_map[finding.focus]}  "
            f"[{conf_color}](confidence: {finding.confidence})[/{conf_color}]"
        )
        points = "\n".join(f"• {p}" for p in finding.key_points)
        console.print(Panel(f"{finding.summary}\n\n{points}", title=title, border_style="blue"))

    console.print(Panel(
        "\n".join(f"[yellow]{i+1}.[/yellow] {q}" for i, q in enumerate(briefing.recommended_questions)),
        title="Recommended Client Questions",
        border_style="green",
    ))


def render_markdown(briefing: FDEBriefing, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    slug = briefing.target.lower().replace(" ", "_")
    path = output_dir / f"{slug}_briefing.md"

    lines = [
        f"# FDE Intelligence Briefing: {briefing.target}",
        "",
        f"**Integration Complexity:** {briefing.integration_complexity.upper()}",
        "",
        "## Executive Summary",
        "",
        briefing.executive_summary,
        "",
    ]

    section_titles = {
        "tech": "Technical Fit",
        "cost": "Cost Signals",
        "risk": "Risk Flags",
        "competitors": "Competitor Landscape",
    }
    for finding in [
        briefing.tech_fit,
        briefing.cost_signals,
        briefing.risk_flags,
        briefing.competitor_landscape,
    ]:
        lines += [
            f"## {section_titles[finding.focus]}",
            f"_Confidence: {finding.confidence}_",
            "",
            finding.summary,
            "",
        ]
        for point in finding.key_points:
            lines.append(f"- {point}")
        if finding.sources:
            lines += ["", "**Sources:**"]
            for src in finding.sources:
                lines.append(f"- {src}")
        lines.append("")

    lines += [
        "## Recommended Client Questions",
        "",
    ]
    for i, q in enumerate(briefing.recommended_questions, 1):
        lines.append(f"{i}. {q}")

    path.write_text("\n".join(lines), encoding="utf-8")
    return path
