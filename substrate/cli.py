from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

from .constants import DEFAULT_SCHEMA_PATH
from .inbox import list_inbox
from .io import dump_frontmatter, parse_frontmatter, safe_read_text, safe_write_text
from .items import append_daily_note, create_inbox_note, open_daily_note, promote_inbox_item, read_item, update_frontmatter
from .ops_log import append_ops_log, filter_ops_log, filter_ops_since, find_vault_root, tail_ops_log
from .quarantine import list_quarantine, quarantine_file, restore_quarantined
from .repair import repair_file, repair_tree
from .schema import SchemaError, load_schema, validate_frontmatter
from .search import search_items
from .ulid import new_ulid
from .vault import init_vault
from .views import inbox_view, load_item_view, search_view


def _parse_csv(value: str | None) -> list[str] | None:
    if not value:
        return None
    parsed = [part.strip() for part in value.split(",")]
    cleaned = [part for part in parsed if part]
    return cleaned or None


def cmd_init(args: argparse.Namespace) -> int:
    root = Path(args.root)
    init_vault(root)
    vault_root = root.expanduser().resolve()
    append_ops_log(vault_root, "vault.init", {"root": str(vault_root)})
    print(f"Initialized vault at {vault_root}")
    return 0


def cmd_ulid(_: argparse.Namespace) -> int:
    print(new_ulid())
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    path = Path(args.file)
    text = safe_read_text(path)
    parsed = parse_frontmatter(text)
    schema_path = Path(args.schema) if args.schema else DEFAULT_SCHEMA_PATH
    try:
        schema = load_schema(schema_path)
    except SchemaError as exc:
        print(f"Schema error: {exc}")
        return 2

    errors = validate_frontmatter(parsed.frontmatter, schema)
    vault_root = find_vault_root(path)
    if vault_root is not None:
        append_ops_log(vault_root, "frontmatter.validate", {"file": str(path), "valid": not errors})
    if errors:
        print("Invalid frontmatter:")
        for err in errors:
            print(f"- {err}")
        return 1
    print("Frontmatter valid")
    return 0


def cmd_read(args: argparse.Namespace) -> int:
    path = Path(args.file)
    text = safe_read_text(path)
    vault_root = find_vault_root(path)
    if vault_root is not None:
        append_ops_log(vault_root, "file.read", {"file": str(path)})
    print(text)
    return 0


def cmd_write(args: argparse.Namespace) -> int:
    path = Path(args.file)
    if args.frontmatter:
        frontmatter = json.loads(args.frontmatter)
        schema_path = Path(args.schema) if args.schema else DEFAULT_SCHEMA_PATH
        errors = validate_frontmatter(frontmatter, load_schema(schema_path))
        if errors:
            print("Invalid frontmatter:")
            for err in errors:
                print(f"- {err}")
            return 1
        output = dump_frontmatter(frontmatter, args.body or "")
    else:
        output = args.body or ""
    safe_write_text(path, output)
    vault_root = find_vault_root(path)
    if vault_root is not None:
        append_ops_log(vault_root, "file.write", {"file": str(path)})
    print(f"Wrote {path}")
    return 0


def cmd_quarantine(args: argparse.Namespace) -> int:
    vault_root = Path(args.vault)
    entry = quarantine_file(vault_root, Path(args.file), args.reason)
    append_ops_log(vault_root, "quarantine.add", entry.__dict__)
    print(json.dumps(entry.__dict__, indent=2))
    return 0


def cmd_quarantine_list(args: argparse.Namespace) -> int:
    vault_root = Path(args.vault)
    entries = list_quarantine(vault_root)
    append_ops_log(vault_root, "quarantine.list", {"count": len(entries)})
    print(json.dumps([e.__dict__ for e in entries], indent=2))
    return 0


def cmd_quarantine_restore(args: argparse.Namespace) -> int:
    dest = Path(args.destination) if args.destination else None
    vault_root = Path(args.vault)
    restored = restore_quarantined(vault_root, args.id, dest)
    append_ops_log(vault_root, "quarantine.restore", {"id": args.id, "destination": str(restored)})
    print(f"Restored to {restored}")
    return 0


def cmd_repair(args: argparse.Namespace) -> int:
    vault_root = Path(args.vault)
    schema_path = Path(args.schema) if args.schema else DEFAULT_SCHEMA_PATH
    result = repair_file(
        vault_root=vault_root,
        file_path=Path(args.file),
        schema_path=schema_path,
        quarantine_invalid=not args.no_quarantine,
        dry_run=args.dry_run,
    )
    append_ops_log(
        vault_root,
        "file.repair",
        {
            "file": str(result.path),
            "action": result.action,
            "errors": result.errors,
            "quarantined": result.quarantined.__dict__ if result.quarantined else None,
            "dry_run": args.dry_run,
        },
    )
    print(
        json.dumps(
            {
                "file": str(result.path),
                "action": result.action,
                "errors": result.errors,
                "quarantined": result.quarantined.__dict__ if result.quarantined else None,
            },
            indent=2,
        )
    )
    return 0


def cmd_repair_tree(args: argparse.Namespace) -> int:
    vault_root = Path(args.vault)
    schema_path = Path(args.schema) if args.schema else DEFAULT_SCHEMA_PATH
    results = repair_tree(
        vault_root=vault_root,
        root=Path(args.root),
        schema_path=schema_path,
        quarantine_invalid=not args.no_quarantine,
        dry_run=args.dry_run,
        include_patterns=args.include,
        limit=args.limit,
    )
    append_ops_log(
        vault_root,
        "file.repair_tree",
        {
            "root": str(args.root),
            "count": len(results),
            "dry_run": args.dry_run,
        },
    )
    print(
        json.dumps(
            [
                {
                    "file": str(result.path),
                    "action": result.action,
                    "errors": result.errors,
                    "quarantined": result.quarantined.__dict__ if result.quarantined else None,
                }
                for result in results
            ],
            indent=2,
        )
    )
    return 0


def cmd_ops_tail(args: argparse.Namespace) -> int:
    entries = tail_ops_log(Path(args.vault), args.limit)
    print(json.dumps([e.__dict__ for e in entries], indent=2))
    return 0


def cmd_ops_filter(args: argparse.Namespace) -> int:
    entries = filter_ops_log(Path(args.vault), args.op)
    print(json.dumps([e.__dict__ for e in entries], indent=2))
    return 0


def cmd_ops_since(args: argparse.Namespace) -> int:
    entries = filter_ops_since(Path(args.vault), args.since)
    print(json.dumps([e.__dict__ for e in entries], indent=2))
    return 0


def cmd_capture(args: argparse.Namespace) -> int:
    vault_root = Path(args.vault)
    tags = args.tags.split(",") if args.tags else None
    path = create_inbox_note(
        vault_root,
        title=args.title,
        body=args.body or "",
        tags=tags,
        privacy=args.privacy,
    )
    append_ops_log(
        vault_root,
        "inbox.capture",
        {"file": str(path), "title": args.title, "tags": tags or []},
    )
    print(str(path))
    return 0


def cmd_daily_open(args: argparse.Namespace) -> int:
    vault_root = Path(args.vault)
    target_date = None
    if args.date:
        target_date = datetime.strptime(args.date, "%Y-%m-%d").date()
    path = open_daily_note(vault_root, target_date=target_date)
    append_ops_log(
        vault_root,
        "daily.open",
        {"file": str(path), "date": args.date},
    )
    print(str(path))
    return 0


def cmd_daily_append(args: argparse.Namespace) -> int:
    vault_root = Path(args.vault)
    target_date = None
    if args.date:
        target_date = datetime.strptime(args.date, "%Y-%m-%d").date()
    path = append_daily_note(vault_root, args.text, target_date=target_date)
    append_ops_log(
        vault_root,
        "daily.append",
        {"file": str(path), "date": args.date},
    )
    print(str(path))
    return 0


def cmd_frontmatter_set(args: argparse.Namespace) -> int:
    updates = json.loads(args.updates)
    try:
        item = update_frontmatter(Path(args.file), updates)
    except ValueError as exc:
        print(str(exc))
        return 1
    vault_root = find_vault_root(Path(args.file))
    if vault_root is not None:
        append_ops_log(
            vault_root,
            "frontmatter.update",
            {"file": str(item.path), "keys": list(updates.keys())},
        )
    print(json.dumps(item.frontmatter, indent=2))
    return 0


def cmd_item_show(args: argparse.Namespace) -> int:
    item = read_item(Path(args.file))
    print(json.dumps(item.frontmatter, indent=2))
    print("---")
    print(item.body)
    return 0


def cmd_item_view(args: argparse.Namespace) -> int:
    payload = load_item_view(Path(args.file))
    print(json.dumps(payload, indent=2))
    return 0


def cmd_promote(args: argparse.Namespace) -> int:
    vault_root = Path(args.vault)
    try:
        target = promote_inbox_item(vault_root, Path(args.file), target_status=args.status)
    except ValueError as exc:
        print(str(exc))
        return 1
    append_ops_log(
        vault_root,
        "inbox.promote",
        {"from": str(Path(args.file)), "to": str(target), "status": args.status},
    )
    print(str(target))
    return 0


def cmd_inbox_list(args: argparse.Namespace) -> int:
    items = list_inbox(Path(args.vault))
    print(
        json.dumps(
            [
                {
                    "path": str(item.path),
                    "title": item.title,
                    "status": item.status,
                    "privacy": item.privacy,
                    "updated": item.updated,
                }
                for item in items
            ],
            indent=2,
        )
    )
    return 0


def cmd_inbox_view(args: argparse.Namespace) -> int:
    try:
        payload = inbox_view(
            Path(args.vault),
            limit=args.limit,
            offset=args.offset,
            sort=args.sort,
            status=_parse_csv(args.status),
            privacy=_parse_csv(args.privacy),
        )
    except ValueError as exc:
        print(str(exc))
        return 1
    print(json.dumps(payload, indent=2))
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    results = search_items(
        Path(args.vault),
        args.query,
        status=_parse_csv(args.status),
        privacy=_parse_csv(args.privacy),
    )
    print(
        json.dumps(
            [
                {
                    "path": str(result.path),
                    "title": result.title,
                    "type": result.type,
                    "status": result.status,
                    "privacy": result.privacy,
                    "updated": result.updated,
                    "snippet": result.snippet,
                    "score": result.score,
                }
                for result in results
            ],
            indent=2,
        )
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="substrate")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser("init", help="Initialize vault structure")
    p_init.add_argument("root")
    p_init.set_defaults(func=cmd_init)

    p_ulid = sub.add_parser("ulid", help="Generate monotonic ULID")
    p_ulid.set_defaults(func=cmd_ulid)

    p_validate = sub.add_parser("validate", help="Validate YAML frontmatter")
    p_validate.add_argument("file")
    p_validate.add_argument("--schema")
    p_validate.set_defaults(func=cmd_validate)

    p_read = sub.add_parser("read", help="Safe read text file")
    p_read.add_argument("file")
    p_read.set_defaults(func=cmd_read)

    p_write = sub.add_parser("write", help="Safe write text file")
    p_write.add_argument("file")
    p_write.add_argument("--frontmatter", help="JSON string for frontmatter")
    p_write.add_argument("--schema", help="Schema path (JSON/YAML)")
    p_write.add_argument("--body", help="Body content")
    p_write.set_defaults(func=cmd_write)

    p_quar = sub.add_parser("quarantine", help="Quarantine a file")
    p_quar.add_argument("vault")
    p_quar.add_argument("file")
    p_quar.add_argument("reason")
    p_quar.set_defaults(func=cmd_quarantine)

    p_qlist = sub.add_parser("quarantine-list", help="List quarantine entries")
    p_qlist.add_argument("vault")
    p_qlist.set_defaults(func=cmd_quarantine_list)

    p_qrestore = sub.add_parser("quarantine-restore", help="Restore quarantined file")
    p_qrestore.add_argument("vault")
    p_qrestore.add_argument("id")
    p_qrestore.add_argument("--destination")
    p_qrestore.set_defaults(func=cmd_quarantine_restore)

    p_repair = sub.add_parser("repair", help="Normalize frontmatter or quarantine invalid files")
    p_repair.add_argument("vault")
    p_repair.add_argument("file")
    p_repair.add_argument("--schema", help="Schema path (JSON/YAML)")
    p_repair.add_argument("--dry-run", action="store_true")
    p_repair.add_argument("--no-quarantine", action="store_true")
    p_repair.set_defaults(func=cmd_repair)

    p_repair_tree = sub.add_parser("repair-tree", help="Normalize or quarantine a tree of markdown files")
    p_repair_tree.add_argument("vault")
    p_repair_tree.add_argument("root")
    p_repair_tree.add_argument("--schema", help="Schema path (JSON/YAML)")
    p_repair_tree.add_argument("--dry-run", action="store_true")
    p_repair_tree.add_argument("--no-quarantine", action="store_true")
    p_repair_tree.add_argument("--include", action="append", help="Glob pattern (repeatable)")
    p_repair_tree.add_argument("--limit", type=int, help="Max files to process")
    p_repair_tree.set_defaults(func=cmd_repair_tree)

    p_ops = sub.add_parser("ops-log", help="Query ops log")
    ops_sub = p_ops.add_subparsers(dest="ops_cmd", required=True)

    p_ops_tail = ops_sub.add_parser("tail", help="Tail ops log")
    p_ops_tail.add_argument("vault")
    p_ops_tail.add_argument("--limit", type=int, default=20)
    p_ops_tail.set_defaults(func=cmd_ops_tail)

    p_ops_filter = ops_sub.add_parser("filter", help="Filter ops log by op")
    p_ops_filter.add_argument("vault")
    p_ops_filter.add_argument("op")
    p_ops_filter.set_defaults(func=cmd_ops_filter)

    p_ops_since = ops_sub.add_parser("since", help="Filter ops log since timestamp")
    p_ops_since.add_argument("vault")
    p_ops_since.add_argument("since")
    p_ops_since.set_defaults(func=cmd_ops_since)

    p_capture = sub.add_parser("capture", help="Capture a text note to inbox")
    p_capture.add_argument("vault")
    p_capture.add_argument("--title", required=True)
    p_capture.add_argument("--body")
    p_capture.add_argument("--tags", help="Comma-separated tags")
    p_capture.add_argument("--privacy", default="private")
    p_capture.set_defaults(func=cmd_capture)

    p_daily = sub.add_parser("daily", help="Daily notes")
    daily_sub = p_daily.add_subparsers(dest="daily_cmd", required=True)

    p_daily_open = daily_sub.add_parser("open", help="Open or create daily note")
    p_daily_open.add_argument("vault")
    p_daily_open.add_argument("--date", help="YYYY-MM-DD")
    p_daily_open.set_defaults(func=cmd_daily_open)

    p_daily_append = daily_sub.add_parser("append", help="Append text to daily note")
    p_daily_append.add_argument("vault")
    p_daily_append.add_argument("text")
    p_daily_append.add_argument("--date", help="YYYY-MM-DD")
    p_daily_append.set_defaults(func=cmd_daily_append)

    p_frontmatter = sub.add_parser("frontmatter-set", help="Update frontmatter fields")
    p_frontmatter.add_argument("file")
    p_frontmatter.add_argument("updates", help="JSON dict of updates")
    p_frontmatter.set_defaults(func=cmd_frontmatter_set)

    p_item_show = sub.add_parser("item-show", help="Show frontmatter and body")
    p_item_show.add_argument("file")
    p_item_show.set_defaults(func=cmd_item_show)

    p_item_view = sub.add_parser("item-view", help="Show item JSON for UI")
    p_item_view.add_argument("file")
    p_item_view.set_defaults(func=cmd_item_view)

    p_inbox_list = sub.add_parser("inbox-list", help="List inbox items")
    p_inbox_list.add_argument("vault")
    p_inbox_list.set_defaults(func=cmd_inbox_list)

    p_inbox_view = sub.add_parser("inbox-view", help="Inbox view JSON for UI")
    p_inbox_view.add_argument("vault")
    p_inbox_view.add_argument("--limit", type=int)
    p_inbox_view.add_argument("--offset", type=int, default=0)
    p_inbox_view.add_argument("--sort", default="updated_desc")
    p_inbox_view.add_argument("--status", help="Comma-separated status filter")
    p_inbox_view.add_argument("--privacy", help="Comma-separated privacy filter")
    p_inbox_view.set_defaults(func=cmd_inbox_view)

    p_search = sub.add_parser("search", help="Search vault (basic scan)")
    p_search.add_argument("vault")
    p_search.add_argument("query")
    p_search.add_argument("--status", help="Comma-separated status filter")
    p_search.add_argument("--privacy", help="Comma-separated privacy filter")
    p_search.set_defaults(func=cmd_search)

    p_promote = sub.add_parser("promote", help="Promote inbox item to items/")
    p_promote.add_argument("vault")
    p_promote.add_argument("file")
    p_promote.add_argument("--status", default="canonical")
    p_promote.set_defaults(func=cmd_promote)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
