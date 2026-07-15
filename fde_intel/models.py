"""Pydantic models for agent inputs, outputs, and the final briefing."""
from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, Field


class ResearchTask(BaseModel):
    topic: str
    focus: Literal["tech", "cost", "risk", "competitors"]
    query: str


class AgentFinding(BaseModel):
    focus: Literal["tech", "cost", "risk", "competitors"]
    summary: str
    key_points: list[str] = Field(min_length=1, max_length=8)
    sources: list[str] = Field(default_factory=list)
    confidence: Literal["high", "medium", "low"] = "medium"


class FDEBriefing(BaseModel):
    target: str
    tech_fit: AgentFinding
    cost_signals: AgentFinding
    risk_flags: AgentFinding
    competitor_landscape: AgentFinding
    integration_complexity: Literal["low", "medium", "high"]
    recommended_questions: list[str] = Field(
        description="Questions the FDE should ask the client on first call",
        min_length=3,
        max_length=8,
    )
    executive_summary: str
