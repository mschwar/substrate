from __future__ import annotations

import argparse
import json
from pathlib import Path

from .constants import DEFAULT_SCHEMA_PATH
from .io import dump_frontmatter, parse_frontmatter, safe_read_text, safe_write_text
from .ops_log import append_ops_log, filter_ops_log, find_vault_root, tail_ops_log
from .quarantine import list_quarantine, quarantine_file, restore_quarantined
from .repair import repair_file
from .schema import SchemaError, load_schema, validate_frontmatter
from .ulid import new_ulid
from .vault import init_vault


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
    print(json.dumps({\n        \"file\": str(result.path),\n        \"action\": result.action,\n        \"errors\": result.errors,\n        \"quarantined\": result.quarantined.__dict__ if result.quarantined else None,\n    }, indent=2))\n    return 0


def cmd_ops_tail(args: argparse.Namespace) -> int:
    entries = tail_ops_log(Path(args.vault), args.limit)
    print(json.dumps([e.__dict__ for e in entries], indent=2))
    return 0


def cmd_ops_filter(args: argparse.Namespace) -> int:
    entries = filter_ops_log(Path(args.vault), args.op)
    print(json.dumps([e.__dict__ for e in entries], indent=2))
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

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
