"""Shared config loaded from environment."""
import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
TAVILY_API_KEY: str = os.getenv("TAVILY_API_KEY", "")
CLAUDE_MODEL: str = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5-20251001")

MAX_SEARCH_RESULTS: int = 5
REQUEST_TIMEOUT: int = 30

MAX_SEARCH_RESULTS: int = 5
REQUEST_TIMEOUT: int = 30
