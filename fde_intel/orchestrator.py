"""Orchestrator: fans out to 4 specialist agents in parallel, then synthesizes the FDE briefing."""
from __future__ import annotations
import asyncio
import json
import anthropic
from fde_intel.config import ANTHROPIC_API_KEY, CLAUDE_MODEL
from fde_intel.exceptions import SynthesisError
from fde_intel.models import AgentFinding, FDEBriefing, FDEReadinessScore
from fde_intel.agents import (
    run_tech_agent,
    run_cost_agent,
    run_risk_agent,
    run_competitor_agent,
)

_client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)


async def _synthesize(
    target: str,
    tech: AgentFinding,
    cost: AgentFinding,
    risk: AgentFinding,
    competitors: AgentFinding,
) -> dict:
    """Claude reasons over all 4 findings to produce synthesis fields."""
    prompt = (
        f"You are a senior Forward Deployed Engineer preparing a pre-call briefing on: {target}\n\n"
        f"TECH FINDINGS:\n{tech.summary}\nKey points: {tech.key_points}\n\n"
        f"COST SIGNALS:\n{cost.summary}\nKey points: {cost.key_points}\n\n"
        f"RISK FLAGS:\n{risk.summary}\nKey points: {risk.key_points}\n\n"
        f"COMPETITOR LANDSCAPE:\n{competitors.summary}\nKey points: {competitors.key_points}\n\n"
        "Based on ALL findings above, return a JSON object with exactly these fields:\n"
        "{\n"
        '  "executive_summary": "2-3 sentence briefing for a non-technical stakeholder",\n'
        '  "integration_complexity": "low|medium|high — based on tech architecture, number of integration points, and risk flags. NOT based on confidence scores.",\n'
        '  "fde_readiness_score": {\n'
        '    "score": <integer 0-100>,\n'
        '    "grade": "A|B|C|D|F",\n'
        '    "rationale": "2-3 sentences explaining the score based on tech maturity, cost clarity, risk level, and competitive position",\n'
        '    "blockers": ["hard blocker 1", ...],\n'
        '    "accelerators": ["factor that speeds deployment", ...]\n'
        "  },\n"
        '  "recommended_questions": ["question for client 1", ...]\n'
        "}\n\n"
        "Scoring guide for fde_readiness_score:\n"
        "90-100 (A): Mature tech, clear pricing, low risk, weak competition — deploy immediately\n"
        "70-89 (B): Good fit with minor gaps — proceed with caveats\n"
        "50-69 (C): Significant concerns in 1-2 areas — proceed cautiously\n"
        "30-49 (D): Major blockers present — needs deeper discovery\n"
        "0-29 (F): Not deployment-ready — critical risks or poor fit\n\n"
        "The recommended_questions should be 4-6 sharp questions to uncover deployment complexity "
        "and qualify the deal. Only return the JSON — no markdown, no explanation."
    )

    response = await _client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}],
    )
    text = response.content[0].text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise SynthesisError(
            message=f"Synthesis returned invalid JSON: {e}",
            additional_info={"raw_text": text[:300]},
        ) from e


async def run_research(target: str) -> FDEBriefing:
    """Fan out 4 agents in parallel, then synthesize into an FDEBriefing."""
    tech, cost, risk, competitors = await asyncio.gather(
        run_tech_agent(target),
        run_cost_agent(target),
        run_risk_agent(target),
        run_competitor_agent(target),
    )

    synthesis = await _synthesize(target, tech, cost, risk, competitors)

    return FDEBriefing(
        target=target,
        tech_fit=tech,
        cost_signals=cost,
        risk_flags=risk,
        competitor_landscape=competitors,
        integration_complexity=synthesis["integration_complexity"],
        fde_readiness_score=FDEReadinessScore(**synthesis["fde_readiness_score"]),
        recommended_questions=synthesis["recommended_questions"],
        executive_summary=synthesis["executive_summary"],
    )
