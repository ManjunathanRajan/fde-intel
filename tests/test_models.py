"""Tests for models and orchestrator logic."""
import pytest
from fde_intel.models import AgentFinding, FDEBriefing
from fde_intel.orchestrator import _infer_complexity


def _make_finding(focus, confidence="medium") -> AgentFinding:
    return AgentFinding(
        focus=focus,
        summary="Test summary",
        key_points=["point one", "point two"],
        sources=["https://example.com"],
        confidence=confidence,
    )


def test_fde_briefing_valid():
    briefing = FDEBriefing(
        target="Snowflake",
        tech_fit=_make_finding("tech"),
        cost_signals=_make_finding("cost"),
        risk_flags=_make_finding("risk"),
        competitor_landscape=_make_finding("competitors"),
        integration_complexity="medium",
        recommended_questions=["Q1?", "Q2?", "Q3?"],
        executive_summary="Snowflake is a cloud data warehouse.",
    )
    assert briefing.target == "Snowflake"
    assert len(briefing.recommended_questions) == 3


def test_infer_complexity_high():
    tech = _make_finding("tech", "high")
    risk = _make_finding("risk", "high")
    assert _infer_complexity(tech, risk) == "high"


def test_infer_complexity_low():
    tech = _make_finding("tech", "low")
    risk = _make_finding("risk", "low")
    assert _infer_complexity(tech, risk) == "low"


def test_infer_complexity_default_medium():
    tech = _make_finding("tech", "low")
    risk = _make_finding("risk", "high")
    assert _infer_complexity(tech, risk) == "medium"


def test_agent_finding_requires_key_points():
    with pytest.raises(Exception):
        AgentFinding(focus="tech", summary="x", key_points=[], confidence="high")
