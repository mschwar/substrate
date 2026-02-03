from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

from .inbox import InboxItem, list_inbox
from .items import Item, read_item
from .search import search_items


def item_view(item: Item) -> dict[str, Any]:
    fm = item.frontmatter
    attachments = fm.get("attachments", [])
    if not isinstance(attachments, list):
        attachments = [attachments]
    return {
        "id": fm.get("id"),
        "title": fm.get("title"),
        "type": fm.get("type"),
        "status": fm.get("status"),
        "privacy": fm.get("privacy"),
        "created": fm.get("created"),
        "updated": fm.get("updated"),
        "path": str(item.path),
        "frontmatter": fm,
        "body": item.body,
        "attachments": attachments,
        "backlinks": [],
        "provenance": {
            "sources": fm.get("sources", []),
            "observed": fm.get("observed", []),
        },
    }


def load_item_view(path: Path) -> dict[str, Any]:
    return item_view(read_item(path))


_SORT_FIELDS = {"updated", "created", "title"}


def _parse_sort(sort: str) -> tuple[str, bool]:
    if sort.endswith("_desc"):
        field = sort[: -len("_desc")]
        reverse = True
    elif sort.endswith("_asc"):
        field = sort[: -len("_asc")]
        reverse = False
    else:
        raise ValueError("sort must end with _asc or _desc")

    if field not in _SORT_FIELDS:
        raise ValueError(f"unsupported sort field: {field}")

    return field, reverse


def _sort_key(item: InboxItem, field: str) -> str:
    if field == "updated":
        return item.updated or ""
    if field == "created":
        return item.created or ""
    if field == "title":
        return (item.title or "").casefold()
    return ""


def inbox_view(
    vault_root: Path,
    *,
    limit: int | None = None,
    offset: int = 0,
    sort: str = "updated_desc",
    status: list[str] | None = None,
    privacy: list[str] | None = None,
) -> dict[str, Any]:
    items = list_inbox(vault_root)
    field, reverse = _parse_sort(sort)
    filtered: list[InboxItem] = []
    for item in items:
        if status and item.status not in status:
            continue
        if privacy and item.privacy not in privacy:
            continue
        filtered.append(item)
    items_sorted = sorted(filtered, key=lambda item: _sort_key(item, field), reverse=reverse)

    total = len(items_sorted)
    window = items_sorted[offset : offset + limit if limit is not None else None]

    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "sort": sort,
        "filters": {"status": status or [], "privacy": privacy or []},
        "items": [
            {
                "path": str(item.path),
                "title": item.title,
                "status": item.status,
                "privacy": item.privacy,
                "created": item.created,
                "updated": item.updated,
            }
            for item in window
        ],
    }


def search_view(
    vault_root: Path,
    query: str,
    *,
    limit: int | None = None,
    offset: int = 0,
    status: list[str] | None = None,
    privacy: list[str] | None = None,
) -> dict[str, Any]:
    results = search_items(vault_root, query, status=status, privacy=privacy)
    total = len(results)
    window = results[offset : offset + limit if limit is not None else None]
    return {
        "query": query,
        "total": total,
        "offset": offset,
        "limit": limit,
        "filters": {"status": status or [], "privacy": privacy or []},
        "results": [
            {
                "path": str(result.path),
                "title": result.title,
                "type": result.type,
                "status": result.status,
                "privacy": result.privacy,
                "updated": result.updated,
                "snippet": result.snippet,
            }
            for result in window
        ],
    }
