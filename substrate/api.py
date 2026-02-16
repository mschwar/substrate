from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from datetime import datetime

from .io import canonicalize_path, dump_frontmatter, safe_write_text
from .items import (
    append_daily_note,
    create_inbox_note,
    open_daily_note,
    promote_inbox_item,
    read_item,
)
from .ops_log import append_ops_log, utc_now_iso
from .schema import load_schema, validate_frontmatter_verbose
from .status import StatusTransitionError, validate_status_transition
from .views import inbox_view, item_view, load_item_view, search_view


@dataclass(frozen=True)
class ApiError(Exception):
    message: str
    status: int = 400


def _require_token(required: str | None, provided: str | None) -> None:
    if required:
        if not provided or provided != required:
            raise ApiError("unauthorized", status=401)


def api_inbox(
    vault_root: Path,
    *,
    limit: int,
    offset: int,
    sort: str,
    status: list[str] | None,
    privacy: list[str] | None,
    token_required: str | None,
    token_provided: str | None,
) -> dict[str, Any]:
    _require_token(token_required, token_provided)
    return inbox_view(vault_root, limit=limit, offset=offset, sort=sort, status=status, privacy=privacy)


def api_item(
    vault_root: Path,
    *,
    path_value: str,
    token_required: str | None,
    token_provided: str | None,
) -> dict[str, Any]:
    _require_token(token_required, token_provided)
    if not path_value:
        raise ApiError("missing path parameter", status=400)
    try:
        path = canonicalize_path(vault_root, Path(path_value))
    except ValueError:
        raise ApiError("invalid path", status=400)
    if not path.exists():
        raise ApiError("path not found", status=404)
    return load_item_view(path)


def api_search(
    vault_root: Path,
    *,
    query: str,
    limit: int,
    offset: int,
    status: list[str] | None,
    privacy: list[str] | None,
    token_required: str | None,
    token_provided: str | None,
) -> dict[str, Any]:
    _require_token(token_required, token_provided)
    return search_view(vault_root, query, limit=limit, offset=offset, status=status, privacy=privacy)


def api_capture(
    vault_root: Path,
    *,
    payload: dict,
    token_required: str | None,
    token_provided: str | None,
) -> dict[str, Any]:
    _require_token(token_required, token_provided)
    title = str(payload.get("title", "")).strip()
    body = str(payload.get("body", ""))
    tags = payload.get("tags")
    privacy = str(payload.get("privacy", "private"))
    if tags is not None and not isinstance(tags, list):
        raise ApiError("tags must be an array", status=400)
    if not title:
        raise ApiError("title is required", status=400)
    path = create_inbox_note(
        vault_root,
        title=title,
        body=body,
        tags=tags,
        privacy=privacy,
    )
    append_ops_log(vault_root, "inbox.capture", {"file": str(path), "title": title})
    return {"path": str(path)}


def api_promote(
    vault_root: Path,
    *,
    payload: dict,
    token_required: str | None,
    token_provided: str | None,
) -> dict[str, Any]:
    _require_token(token_required, token_provided)
    path_value = str(payload.get("path", ""))
    status_value = str(payload.get("status", "canonical"))
    if not path_value:
        raise ApiError("path is required", status=400)
    try:
        path = canonicalize_path(vault_root, Path(path_value))
    except ValueError:
        raise ApiError("invalid path", status=400)
    try:
        target = promote_inbox_item(vault_root, path, target_status=status_value)
    except ValueError as exc:
        raise ApiError(str(exc), status=400)
    append_ops_log(vault_root, "inbox.promote", {"from": path_value, "to": str(target)})
    return {"path": str(target)}


def api_validate(
    vault_root: Path,
    *,
    payload: dict,
    token_required: str | None,
    token_provided: str | None,
) -> dict[str, Any]:
    _require_token(token_required, token_provided)
    frontmatter = payload.get("frontmatter")
    if not isinstance(frontmatter, dict):
        raise ApiError("frontmatter must be an object", status=400)
    from .constants import DEFAULT_SCHEMA_PATH

    schema = load_schema(DEFAULT_SCHEMA_PATH)
    result = validate_frontmatter_verbose(frontmatter, schema)
    return {"valid": len(result.errors) == 0, "errors": result.errors, "warnings": result.warnings}


def api_item_update(
    vault_root: Path,
    *,
    payload: dict,
    token_required: str | None,
    token_provided: str | None,
) -> dict[str, Any]:
    _require_token(token_required, token_provided)
    path_value = str(payload.get("path", ""))
    if not path_value:
        raise ApiError("path is required", status=400)
    try:
        path = canonicalize_path(vault_root, Path(path_value))
    except ValueError:
        raise ApiError("invalid path", status=400)
    if not path.exists():
        raise ApiError("path not found", status=404)

    item = read_item(path)
    provided_frontmatter = payload.get("frontmatter")
    if not isinstance(provided_frontmatter, dict):
        raise ApiError("frontmatter must be an object", status=400)
    body = payload.get("body", item.body)
    if not isinstance(body, str):
        raise ApiError("body must be a string", status=400)

    frontmatter = dict(item.frontmatter)
    if "status" in provided_frontmatter and "status" in frontmatter:
        try:
            validate_status_transition(str(frontmatter["status"]), str(provided_frontmatter["status"]))
        except StatusTransitionError as exc:
            raise ApiError(exc.message, status=400) from exc
    frontmatter.update(provided_frontmatter)
    frontmatter["updated"] = utc_now_iso()

    from .constants import DEFAULT_SCHEMA_PATH

    schema = load_schema(DEFAULT_SCHEMA_PATH)
    validation = validate_frontmatter_verbose(frontmatter, schema)
    validate_only = bool(payload.get("validate_only", False))
    if validation.errors:
        raise ApiError("; ".join(validation.errors), status=400)

    if validate_only:
        return {
            "path": str(path),
            "frontmatter": frontmatter,
            "body": body,
            "warnings": validation.warnings,
            "saved": False,
        }

    content = dump_frontmatter(frontmatter, body)
    safe_write_text(path, content)
    append_ops_log(vault_root, "item.update", {"file": str(path)})
    return {
        "path": str(path),
        "frontmatter": frontmatter,
        "body": body,
        "warnings": validation.warnings,
        "saved": True,
    }


def api_daily_open(
    vault_root: Path,
    *,
    date_value: str | None,
    token_required: str | None,
    token_provided: str | None,
) -> dict[str, Any]:
    _require_token(token_required, token_provided)
    target_date = None
    if date_value:
        try:
            target_date = datetime.fromisoformat(str(date_value)).date()
        except (TypeError, ValueError):
            raise ApiError("invalid date", status=400)
    path = open_daily_note(vault_root, target_date=target_date)
    append_ops_log(vault_root, "daily.open", {"file": str(path), "date": date_value})
    return {"path": str(path), "item": item_view(read_item(path))}


def api_daily_append(
    vault_root: Path,
    *,
    payload: dict,
    token_required: str | None,
    token_provided: str | None,
) -> dict[str, Any]:
    _require_token(token_required, token_provided)
    text = str(payload.get("text", ""))
    if not text:
        raise ApiError("text is required", status=400)
    date_value = payload.get("date")
    target_date = None
    if date_value:
        try:
            target_date = datetime.fromisoformat(str(date_value)).date()
        except ValueError:
            raise ApiError("invalid date", status=400)
    path = append_daily_note(vault_root, text, target_date=target_date)
    append_ops_log(vault_root, "daily.append", {"file": str(path), "date": date_value})
    return {"path": str(path), "item": item_view(read_item(path))}
