"""Specialized research agents — each runs independently and returns an AgentFinding."""
from __future__ import annotations
import json
import anthropic
from fde_intel.config import ANTHROPIC_API_KEY, CLAUDE_MODEL
from fde_intel.models import AgentFinding, ResearchTask
from fde_intel.tools.search import search_web

_client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)

_TOOL_DEF = {
    "name": "search_web",
    "description": "Search the web for up-to-date information. Use targeted, specific queries.",
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "The search query"},
            "max_results": {
                "type": "integer",
                "description": "Number of results (1-10)",
                "default": 5,
            },
        },
        "required": ["query"],
    },
}

_SYSTEM_PROMPTS: dict[str, str] = {
    "tech": (
        "You are a technical evaluation specialist for enterprise software deployments. "
        "Research the technical capabilities, APIs, integrations, and architecture of the given technology. "
        "Focus on: supported integrations, API quality, scalability, deployment models (cloud/on-prem/hybrid), "
        "and what engineering effort is typically required to deploy it in an enterprise. "
        "Be precise and evidence-based. Only claim what you can verify from search results."
    ),
    "cost": (
        "You are an enterprise pricing analyst. Research the cost structure of the given technology. "
        "Focus on: pricing tiers, licensing models, per-user vs usage-based, hidden costs, "
        "typical TCO for mid-size enterprise (500-5000 employees), and any recent pricing changes. "
        "Be concrete with numbers where available."
    ),
    "risk": (
        "You are a deployment risk analyst. Research known risks, issues, and failure patterns "
        "for the given technology in enterprise deployments. "
        "Focus on: known outages, CVEs or security issues, vendor lock-in concerns, "
        "migration complexity, support quality issues, and customer complaints. "
        "Flag the most critical risks clearly."
    ),
    "competitors": (
        "You are a competitive intelligence analyst. Research the competitive landscape for the given technology. "
        "Focus on: top 3-4 alternatives, how they compare on key dimensions, "
        "which use cases each wins/loses, and recent market movements (acquisitions, funding, partnerships). "
        "Give an honest comparison that would help an enterprise make a vendor decision."
    ),
}


async def _run_agent_with_tools(task: ResearchTask) -> AgentFinding:
    """Agentic loop: Claude calls search_web tool until it has enough to answer."""
    system = _SYSTEM_PROMPTS[task.focus]
    messages: list[dict] = [
        {
            "role": "user",
            "content": (
                f"Research target: {task.topic}\n"
                f"Specific focus: {task.query}\n\n"
                "Use the search_web tool to gather information, then return a JSON object with exactly "
                "these fields:\n"
                '{"summary": "...", "key_points": ["...", "..."], "sources": ["url1", "url2"], '
                '"confidence": "high|medium|low"}\n\n'
                "Only return the JSON object — no markdown, no explanation."
            ),
        }
    ]

    while True:
        response = await _client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=2048,
            system=system,
            tools=[_TOOL_DEF],
            messages=messages,
        )

        # Append assistant turn
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            # Extract final text block
            text = next(
                (b.text for b in response.content if hasattr(b, "text")), ""
            ).strip()
            # Strip markdown code fences if present
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            data = json.loads(text)
            return AgentFinding(focus=task.focus, **data)

        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type != "tool_use":
                    continue
                results = await search_web(
                    block.input["query"],
                    block.input.get("max_results", 5),
                )
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(results),
                    }
                )
            messages.append({"role": "user", "content": tool_results})
            continue

        # Unexpected stop reason — surface it
        raise RuntimeError(f"Unexpected stop_reason: {response.stop_reason}")


async def run_tech_agent(topic: str) -> AgentFinding:
    return await _run_agent_with_tools(
        ResearchTask(topic=topic, focus="tech", query=f"{topic} technical architecture integrations API enterprise")
    )


async def run_cost_agent(topic: str) -> AgentFinding:
    return await _run_agent_with_tools(
        ResearchTask(topic=topic, focus="cost", query=f"{topic} pricing licensing cost enterprise 2025 2026")
    )


async def run_risk_agent(topic: str) -> AgentFinding:
    return await _run_agent_with_tools(
        ResearchTask(topic=topic, focus="risk", query=f"{topic} risks problems outages security issues enterprise deployment")
    )


async def run_competitor_agent(topic: str) -> AgentFinding:
    return await _run_agent_with_tools(
        ResearchTask(topic=topic, focus="competitors", query=f"{topic} alternatives competitors comparison enterprise 2025 2026")
    )
