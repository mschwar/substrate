from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


@dataclass(frozen=True)
class OpsEntry:
    timestamp: str
    op: str
    data: dict[str, Any]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def find_vault_root(start: Path) -> Path | None:
    path = start.expanduser().resolve()
    if path.is_file():
        path = path.parent

    for parent in [path] + list(path.parents):
        if (parent / "vault" / "_system").exists():
            return parent
        if (parent / "vault").exists() and (parent / "raw").exists():
            return parent
    return None


def append_ops_log(vault_root: Path, op: str, data: dict[str, Any]) -> None:
    vault_root = vault_root.expanduser().resolve()
    log_dir = vault_root / "vault" / "_system" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "ops.jsonl"

    entry = OpsEntry(timestamp=utc_now_iso(), op=op, data=data)
    with log_path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(entry.__dict__, ensure_ascii=True) + "\n")


def iter_ops_log(vault_root: Path) -> Iterable[OpsEntry]:
    log_path = vault_root / "vault" / "_system" / "logs" / "ops.jsonl"
    if not log_path.exists():
        return []

    entries: list[OpsEntry] = []
    with log_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            data = json.loads(line)
            entries.append(OpsEntry(**data))
    return entries


def tail_ops_log(vault_root: Path, limit: int = 20) -> list[OpsEntry]:
    entries = list(iter_ops_log(vault_root))
    return entries[-limit:]


def filter_ops_log(vault_root: Path, op: str) -> list[OpsEntry]:
    return [entry for entry in iter_ops_log(vault_root) if entry.op == op]
