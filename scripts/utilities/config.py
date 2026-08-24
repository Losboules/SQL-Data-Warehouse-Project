"""Configuration helpers for Northstar Retail local scripts.

Secrets are read from environment variables or a local ``.env`` file that is ignored by Git.
Non-secret defaults live in YAML files under ``config/``.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv


class ConfigurationError(RuntimeError):
    """Raised when required configuration is absent or malformed."""


def load_environment(dotenv_path: str | Path = ".env", *, override: bool = False) -> bool:
    """Load local environment variables from ``dotenv_path`` when it exists.

    Returning ``False`` is not an error: CI and production-style environments often inject
    variables directly rather than using a file.
    """
    path = Path(dotenv_path)
    if not path.exists():
        return False
    return bool(load_dotenv(path, override=override))


def required_env(name: str) -> str:
    """Return a non-empty environment variable or raise a clear configuration error."""
    value = os.getenv(name)
    if value is None or not value.strip():
        raise ConfigurationError(
            f"Required environment variable {name!r} is missing. Copy .env.example to .env "
            "and set the value locally; never commit the .env file."
        )
    return value.strip()


def optional_env(name: str, default: str | None = None) -> str | None:
    """Return an optional environment variable after trimming whitespace."""
    value = os.getenv(name)
    if value is None:
        return default
    stripped = value.strip()
    return stripped if stripped else default


def env_bool(name: str, default: bool = False) -> bool:
    """Parse a common true/false environment value."""
    value = optional_env(name)
    if value is None:
        return default
    normalized = value.lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False
    raise ConfigurationError(f"{name!r} must be true/false, yes/no, 1/0, or on/off; got {value!r}.")


def load_yaml(path: str | Path) -> dict[str, Any]:
    """Load a YAML mapping with a helpful error when the document is not a mapping."""
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(file_path)
    payload = yaml.safe_load(file_path.read_text(encoding="utf-8"))
    if payload is None:
        return {}
    if not isinstance(payload, dict):
        raise ConfigurationError(f"Expected a YAML mapping in {file_path}, got {type(payload).__name__}.")
    return payload
