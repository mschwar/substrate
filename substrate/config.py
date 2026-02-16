from __future__ import annotations

from pathlib import Path
from typing import Any

import secrets

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover - dependency guard
    yaml = None

from .io import safe_read_text, safe_write_text


def config_path(vault_root: Path) -> Path:
    return vault_root / "vault" / "_system" / "config.yaml"


def load_config(vault_root: Path) -> dict[str, Any]:
    path = config_path(vault_root)
    if not path.exists():
        return {}
    if yaml is None:
        raise RuntimeError("PyYAML is required to load config")
    data = yaml.safe_load(safe_read_text(path)) or {}
    if not isinstance(data, dict):
        return {}
    return data


def save_config(vault_root: Path, config: dict[str, Any]) -> None:
    if yaml is None:
        raise RuntimeError("PyYAML is required to save config")
    text = yaml.safe_dump(config, sort_keys=True).strip() + "\n"
    safe_write_text(config_path(vault_root), text)


def load_api_token(vault_root: Path) -> str | None:
    config = load_config(vault_root)
    token = config.get("api_token")
    if isinstance(token, str) and token:
        return token
    return None


def rotate_api_token(vault_root: Path) -> str:
    token = secrets.token_urlsafe(32)
    config = load_config(vault_root)
    config["api_token"] = token
    save_config(vault_root, config)
    return token
