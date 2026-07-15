"""Tests for exceptions, secrets reader, and config param coercion."""
import pytest
from fde_intel.exceptions import AgentError, SearchError, ConfigError, SynthesisError, Location
from fde_intel.config import coerce_model_params


# ── exception tests ───────────────────────────────────────────────────────────

def test_agent_error_location():
    e = AgentError("bad json", additional_info={"raw": "..."})
    assert e.location == Location.Agent
    assert "Agent" in str(e)


def test_agent_error_user_message_not_leaking_internal():
    e = AgentError("internal debug details", additional_info={"stop_reason": "max_tokens"})
    user_msg = e.get_user_facing_message()
    assert "max_tokens" not in user_msg
    assert "internal debug" not in user_msg


def test_search_error_user_message():
    e = SearchError("connection timeout", additional_info={"provider": "tavily"})
    assert e.location == Location.Search
    # user message mentions how to fix, not internal provider detail
    user_msg = e.get_user_facing_message()
    assert "connection timeout" not in user_msg  # internal message not leaked
    assert "Search" in user_msg or "search" in user_msg.lower()


def test_config_error_message_is_user_facing():
    e = ConfigError("ANTHROPIC_API_KEY not set. Add it to .env or mount it as a secret.")
    # ConfigError user message includes the message text (with location prefix)
    user_msg = e.get_user_facing_message()
    assert "ANTHROPIC_API_KEY" in user_msg


def test_synthesis_error_str_includes_location():
    e = SynthesisError("invalid json", additional_info={"raw_text": "not json"})
    assert "Synthesis" in str(e)


def test_fde_error_additional_info_in_str():
    e = AgentError("fail", additional_info={"stop_reason": "error"})
    assert "stop_reason" in str(e)


# ── coerce_model_params tests ─────────────────────────────────────────────────

def test_coerce_max_tokens_string():
    result = coerce_model_params({"max_tokens": "1024"})
    assert result["max_tokens"] == 1024
    assert isinstance(result["max_tokens"], int)


def test_coerce_max_tokens_float_whole():
    result = coerce_model_params({"max_tokens": 512.0})
    assert result["max_tokens"] == 512
    assert isinstance(result["max_tokens"], int)


def test_coerce_temperature_int_to_float():
    result = coerce_model_params({"temperature": 1})
    assert result["temperature"] == 1.0
    assert isinstance(result["temperature"], float)


def test_coerce_temperature_string():
    result = coerce_model_params({"temperature": "0.7"})
    assert result["temperature"] == pytest.approx(0.7)
    assert isinstance(result["temperature"], float)


def test_coerce_leaves_none_untouched():
    result = coerce_model_params({"max_tokens": None, "temperature": None})
    assert result["max_tokens"] is None
    assert result["temperature"] is None


def test_coerce_leaves_bool_untouched():
    result = coerce_model_params({"max_tokens": True})
    assert result["max_tokens"] is True


def test_coerce_unknown_params_unchanged():
    result = coerce_model_params({"model": "claude-sonnet", "stream": False})
    assert result == {"model": "claude-sonnet", "stream": False}


def test_coerce_empty_dict():
    assert coerce_model_params({}) == {}
