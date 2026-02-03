from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .io import parse_frontmatter, safe_read_text


@dataclass(frozen=True)
class InboxItem:
    path: Path
    title: str
    status: str
    created: str
    updated: str
    privacy: str


def list_inbox(vault_root: Path) -> list[InboxItem]:
    inbox_dir = vault_root / "vault" / "inbox"
    if not inbox_dir.exists():
        return []

    items: list[InboxItem] = []
    for path in sorted(inbox_dir.glob("*.md")):
        text = safe_read_text(path)
        parsed = parse_frontmatter(text)
        fm = parsed.frontmatter
        items.append(
            InboxItem(
                path=path,
                title=str(fm.get("title", "")),
                status=str(fm.get("status", "")),
                created=str(fm.get("created", "")),
                updated=str(fm.get("updated", "")),
                privacy=str(fm.get("privacy", "")),
            )
        )
    return items
