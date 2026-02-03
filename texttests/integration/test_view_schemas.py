from __future__ import annotations

import json
from pathlib import Path

from substrate.items import create_inbox_note
from substrate.json_schema import validate_schema
from substrate.views import inbox_view, load_item_view, search_view


def _load_schema(name: str) -> dict:
    path = Path("schema/views") / name
    return json.loads(path.read_text(encoding="utf-8"))


def test_item_view_schema(vault_root: Path):
    path = create_inbox_note(vault_root, title="Schema Item", body="Body")
    payload = load_item_view(path)
    errors = validate_schema(payload, _load_schema("item_view.json"))
    assert errors == []


def test_inbox_view_schema(vault_root: Path):
    create_inbox_note(vault_root, title="Schema Inbox", body="Body")
    payload = inbox_view(vault_root, limit=10)
    errors = validate_schema(payload, _load_schema("inbox_view.json"))
    assert errors == []


def test_search_view_schema(vault_root: Path):
    create_inbox_note(vault_root, title="FindMe", body="needle in haystack")
    payload = search_view(vault_root, "needle", limit=10)
    errors = validate_schema(payload, _load_schema("search_view.json"))
    assert errors == []
    assert payload["total"] >= 1
