from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from .constants import DEFAULT_SCHEMA_PATH
from .io import dump_frontmatter, parse_frontmatter, safe_read_text, safe_write_text
from .ops_log import utc_now_iso
from .schema import load_schema, validate_frontmatter
from .status import StatusTransitionError, validate_status_transition
from .ulid import new_ulid


@dataclass(frozen=True)
class Item:
    path: Path
    frontmatter: dict[str, Any]
    body: str


def _validate_frontmatter_or_raise(frontmatter: dict[str, Any], schema_path: Path | None = None) -> None:
    schema = load_schema(schema_path or DEFAULT_SCHEMA_PATH)
    errors = validate_frontmatter(frontmatter, schema)
    if errors:
        raise ValueError("; ".join(errors))


def _vault_inbox_dir(vault_root: Path) -> Path:
    return vault_root / "vault" / "inbox"


def _vault_items_dir(vault_root: Path) -> Path:
    return vault_root / "vault" / "items"


def _vault_daily_dir(vault_root: Path) -> Path:
    return vault_root / "vault" / "daily"


def create_inbox_note(
    vault_root: Path,
    *,
    title: str,
    body: str = "",
    tags: list[str] | None = None,
    privacy: str = "private",
) -> Path:
    now = utc_now_iso()
    item_id = new_ulid()
    frontmatter: dict[str, Any] = {
        "schema_version": "0.1",
        "id": item_id,
        "type": "note",
        "title": title,
        "created": now,
        "updated": now,
        "status": "inbox",
        "privacy": privacy,
    }
    if tags:
        frontmatter["tags"] = tags

    _validate_frontmatter_or_raise(frontmatter)

    content = dump_frontmatter(frontmatter, body)
    target = _vault_inbox_dir(vault_root) / f"{item_id}.md"
    safe_write_text(target, content)
    return target


def read_item(path: Path) -> Item:
    text = safe_read_text(path)
    parsed = parse_frontmatter(text)
    return Item(path=path, frontmatter=parsed.frontmatter, body=parsed.body)


def update_frontmatter(
    path: Path,
    updates: dict[str, Any],
    *,
    schema_path: Path | None = None,
    allow_coerce: bool = False,
) -> Item:
    item = read_item(path)
    frontmatter = dict(item.frontmatter)
    if "status" in updates and "status" in frontmatter:
        try:
            validate_status_transition(str(frontmatter["status"]), str(updates["status"]))
        except StatusTransitionError as exc:
            raise ValueError(exc.message) from exc
    frontmatter.update(updates)
    frontmatter["updated"] = utc_now_iso()
    _validate_frontmatter_or_raise(frontmatter, schema_path=schema_path)
    content = dump_frontmatter(frontmatter, item.body)
    safe_write_text(path, content)
    return Item(path=path, frontmatter=frontmatter, body=item.body)


def _today_date() -> date:
    return datetime.now(timezone.utc).date()


def _daily_filename(target_date: date) -> str:
    return f"{target_date.isoformat()}.md"


def open_daily_note(
    vault_root: Path,
    *,
    target_date: date | None = None,
) -> Path:
    target_date = target_date or _today_date()
    daily_path = _vault_daily_dir(vault_root) / _daily_filename(target_date)
    if daily_path.exists():
        # verify invariant: created date matches filename date
        item = read_item(daily_path)
        created = item.frontmatter.get("created", "")
        if not str(created).startswith(target_date.isoformat()):
            raise ValueError("Daily note created date does not match filename")
        return daily_path

    now = utc_now_iso()
    frontmatter: dict[str, Any] = {
        "schema_version": "0.1",
        "id": new_ulid(),
        "type": "daily",
        "title": target_date.isoformat(),
        "created": now,
        "updated": now,
        "status": "canonical",
        "privacy": "private",
    }
    _validate_frontmatter_or_raise(frontmatter)
    content = dump_frontmatter(frontmatter, "")
    safe_write_text(daily_path, content)
    return daily_path


def append_daily_note(
    vault_root: Path,
    text: str,
    *,
    target_date: date | None = None,
) -> Path:
    daily_path = open_daily_note(vault_root, target_date=target_date)
    item = read_item(daily_path)
    body = item.body
    if body and not body.endswith("\n"):
        body = body + "\n"
    body = body + text + "\n"
    frontmatter = dict(item.frontmatter)
    frontmatter["updated"] = utc_now_iso()
    _validate_frontmatter_or_raise(frontmatter)
    content = dump_frontmatter(frontmatter, body)
    safe_write_text(daily_path, content)
    return daily_path


def promote_inbox_item(
    vault_root: Path,
    path: Path,
    *,
    target_status: str = "canonical",
) -> Path:
    inbox_dir = _vault_inbox_dir(vault_root).resolve()
    path = path.resolve()
    if path.parent != inbox_dir:
        raise ValueError("Only inbox items can be promoted")
    item = read_item(path)
    frontmatter = dict(item.frontmatter)
    if "status" in frontmatter:
        validate_status_transition(str(frontmatter["status"]), target_status)
    frontmatter["status"] = target_status
    frontmatter["updated"] = utc_now_iso()
    _validate_frontmatter_or_raise(frontmatter)
    item_id = str(frontmatter.get("id", "")).strip()
    if not item_id:
        raise ValueError("Missing id in frontmatter")
    target = _vault_items_dir(vault_root) / f"{item_id}.md"
    if target.exists():
        raise ValueError("Target item already exists")
    content = dump_frontmatter(frontmatter, item.body)
    safe_write_text(target, content)
    path.unlink()
    return target
