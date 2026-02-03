from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .io import parse_frontmatter, safe_read_text


@dataclass(frozen=True)
class SearchResult:
    path: Path
    title: str
    type: str
    status: str
    privacy: str
    updated: str
    snippet: str
    score: int


def _iter_markdown_files(vault_root: Path) -> Iterable[Path]:
    roots = [
        vault_root / "vault" / "inbox",
        vault_root / "vault" / "items",
        vault_root / "vault" / "daily",
    ]
    for root in roots:
        if not root.exists():
            continue
        for path in sorted(root.glob("*.md")):
            if path.is_file():
                yield path


def _make_snippet(body: str, query: str, max_len: int = 120) -> str:
    if not body:
        return ""
    lower = body.casefold()
    idx = lower.find(query)
    if idx == -1:
        return body[:max_len]
    start = max(0, idx - 30)
    end = min(len(body), idx + max_len)
    snippet = body[start:end]
    return snippet.replace("\n", " ")


def search_items(
    vault_root: Path,
    query: str,
    *,
    status: list[str] | None = None,
    privacy: list[str] | None = None,
) -> list[SearchResult]:
    if not query:
        return []
    q = query.casefold()
    results: list[SearchResult] = []

    for path in _iter_markdown_files(vault_root):
        try:
            text = safe_read_text(path)
            parsed = parse_frontmatter(text)
        except Exception:
            continue
        fm = parsed.frontmatter
        title = str(fm.get("title", ""))
        body = parsed.body or ""
        item_status = str(fm.get("status", ""))
        item_privacy = str(fm.get("privacy", ""))
        if status and item_status not in status:
            continue
        if privacy and item_privacy not in privacy:
            continue
        score = 0
        if q in title.casefold():
            score += 2
        if q in body.casefold():
            score += 1
        if score == 0:
            continue
        results.append(
            SearchResult(
                path=path,
                title=title,
                type=str(fm.get("type", "")),
                status=item_status,
                privacy=item_privacy,
                updated=str(fm.get("updated", "")),
                snippet=_make_snippet(body, q),
                score=score,
            )
        )

    results.sort(key=lambda r: (r.score, r.updated), reverse=True)
    return results
