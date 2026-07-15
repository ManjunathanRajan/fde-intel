"""File-based secret loader — reads from mounted secret files (Kubernetes style) with env var fallback.

Locally: set ANTHROPIC_API_KEY / TAVILY_API_KEY as env vars (via .env).
In deployment: mount secrets as files under SECRETS_MOUNT_PATH.
"""
from __future__ import annotations
import os
from pathlib import Path


def _mount_path() -> Path:
    return Path(os.getenv("SECRETS_MOUNT_PATH", "/mount/secrets")).resolve()


def read_secret(secret_name: str, key: str) -> str:
    """Read from mounted secret file: <mount>/<secret_name>/<key>"""
    path = _mount_path() / secret_name / key
    if not path.exists():
        raise FileNotFoundError(f"Missing secret file: {path}")
    return path.read_text().rstrip("\r\n")


def secret_available(secret_name: str, key: str) -> bool:
    return (_mount_path() / secret_name / key).exists()


def get_secret(env_var: str, secret_name: str, key: str) -> str:
    """Return secret — env var takes priority, falls back to mounted file."""
    value = os.getenv(env_var, "")
    if value:
        return value
    if secret_available(secret_name, key):
        return read_secret(secret_name, key)
    return ""
