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


class FDEReadinessScore(BaseModel):
    score: int = Field(ge=0, le=100, description="0-100 FDE readiness score")
    grade: Literal["A", "B", "C", "D", "F"]
    rationale: str = Field(description="2-3 sentence explanation of the score")
    blockers: list[str] = Field(
        default_factory=list,
        description="Hard blockers that must be resolved before deployment",
    )
    accelerators: list[str] = Field(
        default_factory=list,
        description="Factors that will speed up deployment",
    )


class FDEBriefing(BaseModel):
    target: str
    tech_fit: AgentFinding
    cost_signals: AgentFinding
    risk_flags: AgentFinding
    competitor_landscape: AgentFinding
    integration_complexity: Literal["low", "medium", "high"]
    fde_readiness_score: FDEReadinessScore
    recommended_questions: list[str] = Field(
        description="Questions the FDE should ask the client on first call",
        min_length=3,
        max_length=8,
    )
    executive_summary: str
