from __future__ import annotations

from pathlib import Path

from substrate.api import api_item_update, api_validate, api_daily_open, api_daily_append
from substrate.items import create_inbox_note, read_item


def test_api_validate(vault_root: Path):
    payload = {
        "frontmatter": {"schema_version": "0.1"},
        "body": "Body",
    }
    result = api_validate(
        vault_root,
        payload=payload,
        token_required=None,
        token_provided=None,
    )
    assert result["valid"] is False
    assert result["errors"]


def test_api_item_update_validate_only(vault_root: Path):
    path = create_inbox_note(vault_root, title="EditMe", body="Body")
    item = read_item(path)

    payload = {
        "path": str(path),
        "frontmatter": {"title": "Edited"},
        "body": "Body",
        "validate_only": True,
    }
    result = api_item_update(
        vault_root,
        payload=payload,
        token_required=None,
        token_provided=None,
    )
    assert result["saved"] is False
    assert result["frontmatter"]["title"] == "Edited"
    # file should remain unchanged
    reread = read_item(path)
    assert reread.frontmatter["title"] == item.frontmatter["title"]


def test_api_item_update_save(vault_root: Path):
    path = create_inbox_note(vault_root, title="EditMe", body="Body")

    payload = {
        "path": str(path),
        "frontmatter": {"title": "Edited"},
        "body": "Updated",
        "validate_only": False,
    }
    result = api_item_update(
        vault_root,
        payload=payload,
        token_required=None,
        token_provided=None,
    )
    assert result["saved"] is True
    reread = read_item(path)
    assert reread.frontmatter["title"] == "Edited"
    assert reread.body.strip() == "Updated"


def test_api_daily_open_append(vault_root: Path):
    opened = api_daily_open(
        vault_root,
        date_value="2026-02-03",
        token_required=None,
        token_provided=None,
    )
    assert opened["path"]

    appended = api_daily_append(
        vault_root,
        payload={"date": "2026-02-03", "text": "Entry"},
        token_required=None,
        token_provided=None,
    )
    assert "Entry" in appended["item"]["body"]
