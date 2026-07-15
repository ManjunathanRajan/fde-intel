"""Tests covering models, orchestration logic, agentic loop, and search fallback."""
from __future__ import annotations
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fde_intel.models import AgentFinding, FDEBriefing, FDEReadinessScore


# ── helpers ──────────────────────────────────────────────────────────────────

def _make_finding(focus, confidence="medium") -> AgentFinding:
    return AgentFinding(
        focus=focus,
        summary="Test summary",
        key_points=["point one", "point two"],
        sources=["https://example.com"],
        confidence=confidence,
    )


def _make_briefing() -> FDEBriefing:
    return FDEBriefing(
        target="Snowflake",
        tech_fit=_make_finding("tech", "high"),
        cost_signals=_make_finding("cost", "medium"),
        risk_flags=_make_finding("risk", "low"),
        competitor_landscape=_make_finding("competitors", "medium"),
        integration_complexity="medium",
        fde_readiness_score=FDEReadinessScore(
            score=78,
            grade="B",
            rationale="Mature platform with clear pricing and manageable risks.",
            blockers=["Existing Redshift contracts must expire first"],
            accelerators=["Strong Snowflake ecosystem in client's industry"],
        ),
        recommended_questions=["Q1?", "Q2?", "Q3?"],
        executive_summary="Snowflake is a mature cloud data warehouse.",
    )


# ── model tests ───────────────────────────────────────────────────────────────

def test_fde_briefing_valid():
    briefing = _make_briefing()
    assert briefing.target == "Snowflake"
    assert briefing.fde_readiness_score.grade == "B"
    assert briefing.fde_readiness_score.score == 78
    assert len(briefing.recommended_questions) == 3


def test_fde_readiness_score_bounds():
    with pytest.raises(Exception):
        FDEReadinessScore(score=101, grade="A", rationale="too high")
    with pytest.raises(Exception):
        FDEReadinessScore(score=-1, grade="F", rationale="negative")


def test_agent_finding_requires_key_points():
    with pytest.raises(Exception):
        AgentFinding(focus="tech", summary="x", key_points=[], confidence="high")


def test_agent_finding_caps_key_points():
    with pytest.raises(Exception):
        AgentFinding(
            focus="tech",
            summary="x",
            key_points=[f"point {i}" for i in range(9)],
        )


# ── agentic loop tests ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_agent_loop_end_turn_on_first_response():
    """Agent returns result immediately when Claude responds with end_turn."""
    finding_json = json.dumps({
        "summary": "Snowflake is a cloud data warehouse.",
        "key_points": ["Supports multi-cloud", "Consumption-based pricing"],
        "sources": ["https://snowflake.com"],
        "confidence": "high",
    })

    mock_text_block = MagicMock()
    mock_text_block.text = finding_json
    mock_text_block.type = "text"

    mock_response = MagicMock()
    mock_response.stop_reason = "end_turn"
    mock_response.content = [mock_text_block]

    mock_create = AsyncMock(return_value=mock_response)

    with patch("fde_intel.agents._client") as mock_client:
        mock_client.messages.create = mock_create
        with patch("fde_intel.agents.search_web", new_callable=AsyncMock):
            from fde_intel.agents import run_tech_agent
            result = await run_tech_agent("Snowflake")

    assert result.focus == "tech"
    assert result.confidence == "high"
    assert "Snowflake" in result.summary
    mock_create.assert_called_once()


@pytest.mark.asyncio
async def test_agent_loop_tool_use_then_end_turn():
    """Agent calls search tool once, then returns result on second Claude call."""
    finding_json = json.dumps({
        "summary": "Snowflake pricing is consumption-based.",
        "key_points": ["Credits per second", "Storage separate"],
        "sources": ["https://snowflake.com/pricing"],
        "confidence": "medium",
    })

    # First response: tool_use
    mock_tool_block = MagicMock()
    mock_tool_block.type = "tool_use"
    mock_tool_block.id = "tool_123"
    mock_tool_block.input = {"query": "Snowflake pricing enterprise", "max_results": 5}

    mock_response_tool = MagicMock()
    mock_response_tool.stop_reason = "tool_use"
    mock_response_tool.content = [mock_tool_block]

    # Second response: end_turn
    mock_text_block = MagicMock()
    mock_text_block.text = finding_json
    mock_text_block.type = "text"

    mock_response_final = MagicMock()
    mock_response_final.stop_reason = "end_turn"
    mock_response_final.content = [mock_text_block]

    mock_create = AsyncMock(side_effect=[mock_response_tool, mock_response_final])
    mock_search = AsyncMock(return_value=[{"title": "Pricing", "url": "https://snowflake.com/pricing", "content": "Credits..."}])

    with patch("fde_intel.agents._client") as mock_client:
        mock_client.messages.create = mock_create
        with patch("fde_intel.agents.search_web", mock_search):
            from fde_intel.agents import run_cost_agent
            result = await run_cost_agent("Snowflake")

    assert result.focus == "cost"
    assert mock_create.call_count == 2
    mock_search.assert_called_once_with("Snowflake pricing enterprise", 5)


@pytest.mark.asyncio
async def test_agent_loop_raises_on_unexpected_stop_reason():
    mock_response = MagicMock()
    mock_response.stop_reason = "max_tokens"
    mock_response.content = []

    with patch("fde_intel.agents._client") as mock_client:
        mock_client.messages.create = AsyncMock(return_value=mock_response)
        from fde_intel.agents import run_risk_agent
        from fde_intel.exceptions import AgentError
        with pytest.raises(AgentError):
            await run_risk_agent("Snowflake")


# ── orchestrator tests ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_orchestrator_fans_out_all_agents():
    """run_research calls all 4 specialist agents."""
    findings = {
        "tech": _make_finding("tech"),
        "cost": _make_finding("cost"),
        "risk": _make_finding("risk"),
        "competitors": _make_finding("competitors"),
    }
    synthesis = {
        "executive_summary": "Snowflake is production-ready.",
        "integration_complexity": "medium",
        "fde_readiness_score": {
            "score": 80,
            "grade": "B",
            "rationale": "Good fit.",
            "blockers": [],
            "accelerators": ["Strong community"],
        },
        "recommended_questions": ["Q1?", "Q2?", "Q3?"],
    }

    with patch("fde_intel.orchestrator.run_tech_agent", AsyncMock(return_value=findings["tech"])), \
         patch("fde_intel.orchestrator.run_cost_agent", AsyncMock(return_value=findings["cost"])), \
         patch("fde_intel.orchestrator.run_risk_agent", AsyncMock(return_value=findings["risk"])), \
         patch("fde_intel.orchestrator.run_competitor_agent", AsyncMock(return_value=findings["competitors"])), \
         patch("fde_intel.orchestrator._synthesize", AsyncMock(return_value=synthesis)):
        from fde_intel.orchestrator import run_research
        briefing = await run_research("Snowflake")

    assert briefing.target == "Snowflake"
    assert briefing.integration_complexity == "medium"
    assert briefing.fde_readiness_score.score == 80
    assert briefing.fde_readiness_score.grade == "B"


# ── search fallback tests ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_search_uses_tavily_when_key_set():
    with patch("fde_intel.tools.search.TAVILY_API_KEY", "fake-key"), \
         patch("fde_intel.tools.search._search_tavily", new_callable=AsyncMock) as mock_tavily, \
         patch("fde_intel.tools.search._search_duckduckgo", new_callable=AsyncMock) as mock_ddg:
        mock_tavily.return_value = [{"title": "T", "url": "u", "content": "c"}]
        from fde_intel.tools.search import search_web
        results = await search_web("test query")

    mock_tavily.assert_called_once()
    mock_ddg.assert_not_called()
    assert results[0]["title"] == "T"


@pytest.mark.asyncio
async def test_search_falls_back_to_duckduckgo_when_no_key():
    with patch("fde_intel.tools.search.TAVILY_API_KEY", ""), \
         patch("fde_intel.tools.search._search_tavily", new_callable=AsyncMock) as mock_tavily, \
         patch("fde_intel.tools.search._search_duckduckgo", new_callable=AsyncMock) as mock_ddg:
        mock_ddg.return_value = [{"title": "D", "url": "u", "content": "c"}]
        from fde_intel.tools.search import search_web
        results = await search_web("test query")

    mock_ddg.assert_called_once()
    mock_tavily.assert_not_called()
    assert results[0]["title"] == "D"
