"""Orchestrator: fans out to 4 specialist agents in parallel, then synthesizes the FDE briefing."""
from __future__ import annotations
import asyncio
import json
import anthropic
from fde_intel.config import ANTHROPIC_API_KEY, CLAUDE_MODEL
from fde_intel.models import AgentFinding, FDEBriefing
from fde_intel.agents import (
    run_tech_agent,
    run_cost_agent,
    run_risk_agent,
    run_competitor_agent,
)

_client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)

_COMPLEXITY_MAP = {
    ("high", "high"): "high",
    ("high", "medium"): "high",
    ("medium", "high"): "high",
    ("medium", "medium"): "medium",
    ("low", "low"): "low",
}


def _infer_complexity(tech: AgentFinding, risk: AgentFinding) -> str:
    return _COMPLEXITY_MAP.get(
        (tech.confidence, risk.confidence), "medium"
    )


async def _synthesize(
    target: str,
    tech: AgentFinding,
    cost: AgentFinding,
    risk: AgentFinding,
    competitors: AgentFinding,
) -> tuple[str, list[str]]:
    """Ask Claude to produce executive summary + recommended client questions."""
    prompt = (
        f"You are a Forward Deployed Engineer preparing for a first call with a client "
        f"considering {target}.\n\n"
        f"TECH FINDINGS: {tech.summary}\n"
        f"COST SIGNALS: {cost.summary}\n"
        f"RISK FLAGS: {risk.summary}\n"
        f"COMPETITORS: {competitors.summary}\n\n"
        "Return a JSON object with exactly two fields:\n"
        '{"executive_summary": "2-3 sentence briefing for a non-technical stakeholder", '
        '"recommended_questions": ["question1", "question2", ...]}\n\n'
        "The recommended_questions should be 4-6 sharp, specific questions an FDE should ask the "
        "client to qualify the deal and uncover deployment complexity. "
        "Only return the JSON — no markdown, no explanation."
    )
    response = await _client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    text = response.content[0].text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    data = json.loads(text)
    return data["executive_summary"], data["recommended_questions"]


async def run_research(target: str) -> FDEBriefing:
    """Fan out 4 agents in parallel, then synthesize into an FDEBriefing."""
    tech, cost, risk, competitors = await asyncio.gather(
        run_tech_agent(target),
        run_cost_agent(target),
        run_risk_agent(target),
        run_competitor_agent(target),
    )

    executive_summary, recommended_questions = await _synthesize(
        target, tech, cost, risk, competitors
    )

    return FDEBriefing(
        target=target,
        tech_fit=tech,
        cost_signals=cost,
        risk_flags=risk,
        competitor_landscape=competitors,
        integration_complexity=_infer_complexity(tech, risk),
        recommended_questions=recommended_questions,
        executive_summary=executive_summary,
    )
