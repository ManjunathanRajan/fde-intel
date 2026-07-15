"""Shared config — env vars locally, mounted secrets in deployment."""
from __future__ import annotations
import os
from typing import Any
from dotenv import load_dotenv
from fde_intel.secrets import get_secret

load_dotenv()

ANTHROPIC_API_KEY: str = get_secret("ANTHROPIC_API_KEY", "fde-intel", "anthropic-api-key")
TAVILY_API_KEY: str = get_secret("TAVILY_API_KEY", "fde-intel", "tavily-api-key")
CLAUDE_MODEL: str = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")

# Set USE_NATIVE_SEARCH=false to fall back to Tavily/DuckDuckGo
USE_NATIVE_SEARCH: bool = os.getenv("USE_NATIVE_SEARCH", "true").lower() != "false"

MAX_SEARCH_RESULTS: int = 5
REQUEST_TIMEOUT: int = 30

_INT_PARAMS: set[str] = {"max_tokens"}
_FLOAT_PARAMS: set[str] = {"temperature", "top_p"}


def coerce_model_params(params: dict[str, Any]) -> dict[str, Any]:
    """Normalise model param types — string '10' → int 10, int 1 → float 1.0.

    Prevents provider SDK type errors when params come from CLI flags or config files.
    """
    result = dict(params)
    for key in _INT_PARAMS & result.keys():
        v = result[key]
        if v is None or isinstance(v, bool):
            continue
        if isinstance(v, float) and v.is_integer():
            result[key] = int(v)
        elif isinstance(v, str):
            result[key] = int(float(v)) if "." in v else int(v)
    for key in _FLOAT_PARAMS & result.keys():
        v = result[key]
        if v is None or isinstance(v, bool):
            continue
        result[key] = float(v)
    return result


def validate_config() -> None:
    """Fail fast on startup if required config is missing."""
    from fde_intel.exceptions import ConfigError
    if not ANTHROPIC_API_KEY:
        raise ConfigError(
            "ANTHROPIC_API_KEY not set. Add it to .env or mount it as a secret."
        )
