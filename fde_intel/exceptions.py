"""Structured exceptions — internal debug info stays internal, user-facing message is clean.

Pattern adopted from SAP Concur llm-orchestration internal repo.
"""
from __future__ import annotations
from enum import StrEnum
from typing import Any
import json


class Location(StrEnum):
    Search = "Search Tool"
    Agent = "Agent"
    Orchestrator = "Orchestrator"
    Synthesis = "Synthesis"
    Config = "Configuration"


def _safe_serialize(obj: Any) -> str:
    if not obj:
        return ""
    try:
        return "\n" + json.dumps(obj, indent=2, ensure_ascii=False)
    except Exception:
        try:
            return "\n" + str(obj)
        except Exception:
            return ""


class FDEError(Exception):
    """Base for all fde-intel errors. Internal info never surfaces to user."""

    def __init__(
        self,
        message: str,
        location: Location,
        user_message: str = "",
        additional_info: Any = None,
    ):
        self.message = message
        self.location = location
        self.user_message = user_message
        self.additional_info = additional_info

    def __str__(self) -> str:
        return f"[{self.location}] {self.message}{_safe_serialize(self.additional_info)}"

    def get_user_facing_message(self) -> str:
        base = f"Error in {self.location}."
        return f"{base} {self.user_message}".strip() if self.user_message else base


class AgentError(FDEError):
    """Raised when a specialist agent fails — bad stop_reason, parse failure, etc."""

    def __init__(self, message: str, additional_info: Any = None, user_message: str = ""):
        super().__init__(
            message=message,
            location=Location.Agent,
            user_message=user_message or "Agent failed to produce a valid finding. Try again.",
            additional_info=additional_info,
        )


class SearchError(FDEError):
    """Raised when both Tavily and DuckDuckGo searches fail."""

    def __init__(self, message: str, additional_info: Any = None):
        super().__init__(
            message=message,
            location=Location.Search,
            user_message="Web search failed. Check your TAVILY_API_KEY or network connection.",
            additional_info=additional_info,
        )


class ConfigError(FDEError):
    """Raised on missing or invalid configuration."""

    def __init__(self, message: str):
        super().__init__(
            message=message,
            location=Location.Config,
            user_message=message,
        )


class SynthesisError(FDEError):
    """Raised when the synthesis/scoring step fails to return valid JSON."""

    def __init__(self, message: str, additional_info: Any = None):
        super().__init__(
            message=message,
            location=Location.Synthesis,
            user_message="Failed to synthesize findings into a briefing. Try again.",
            additional_info=additional_info,
        )
