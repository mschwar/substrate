from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Tuple

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover - dependency guard
    yaml = None

from .constants import FRONTMATTER_DELIM


class FrontmatterError(ValueError):
    pass


@dataclass(frozen=True)
class ParsedDocument:
    frontmatter: dict
    body: str


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return text


def canonicalize_path(vault_root: Path, target: Path) -> Path:
    """Return resolved absolute path within vault_root or raise."""
    vault_root = vault_root.resolve()
    target_path = (vault_root / target).resolve() if not target.is_absolute() else target.resolve()
    if os.path.commonpath([vault_root, target_path]) != str(vault_root):
        raise ValueError("Path escapes vault root")
    return target_path


def safe_read_text(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    if "\x00" in text:
        raise ValueError("NUL byte not allowed in text files")
    return normalize_text(text)


def safe_write_text(path: Path, text: str) -> None:
    text = normalize_text(text)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(prefix=path.name + ".", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as tmp:
            tmp.write(text)
        os.replace(tmp_path, path)
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def parse_frontmatter(text: str) -> ParsedDocument:
    text = normalize_text(text)
    if not text.startswith(FRONTMATTER_DELIM + "\n"):
        raise FrontmatterError("Missing YAML frontmatter delimiter")

    end_idx = text.find("\n" + FRONTMATTER_DELIM + "\n", len(FRONTMATTER_DELIM) + 1)
    if end_idx == -1:
        raise FrontmatterError("Missing closing YAML frontmatter delimiter")

    yaml_block = text[len(FRONTMATTER_DELIM) + 1 : end_idx]
    body = text[end_idx + len(FRONTMATTER_DELIM) + 2 :]

    if yaml is None:
        raise FrontmatterError("PyYAML is required to parse YAML frontmatter")

    data = yaml.safe_load(yaml_block) or {}
    if not isinstance(data, dict):
        raise FrontmatterError("Frontmatter must be a YAML mapping")

    return ParsedDocument(frontmatter=data, body=body)


def dump_frontmatter(frontmatter: dict, body: str) -> str:
    if yaml is None:
        raise FrontmatterError("PyYAML is required to dump YAML frontmatter")

    yaml_block = yaml.safe_dump(frontmatter, sort_keys=True).strip()
    return f"{FRONTMATTER_DELIM}\n{yaml_block}\n{FRONTMATTER_DELIM}\n" + normalize_text(body)
