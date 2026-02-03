from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .constants import QUARANTINE_DIR
from .ulid import new_ulid


@dataclass(frozen=True)
class QuarantineEntry:
    id: str
    original_path: str
    reason: str
    timestamp: str


def quarantine_file(vault_root: Path, file_path: Path, reason: str) -> QuarantineEntry:
    vault_root = vault_root.expanduser().resolve()
    file_path = file_path.expanduser().resolve()

    if not file_path.exists():
        raise FileNotFoundError(str(file_path))

    qid = new_ulid()
    qdir = vault_root / "vault" / QUARANTINE_DIR / qid
    qdir.mkdir(parents=True, exist_ok=False)

    target = qdir / file_path.name
    file_path.replace(target)

    entry = QuarantineEntry(
        id=qid,
        original_path=str(file_path),
        reason=reason,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
    (qdir / "meta.json").write_text(json.dumps(entry.__dict__, indent=2), encoding="utf-8")
    return entry


def list_quarantine(vault_root: Path) -> list[QuarantineEntry]:
    vault_root = vault_root.expanduser().resolve()
    qroot = vault_root / "vault" / QUARANTINE_DIR
    if not qroot.exists():
        return []

    entries: list[QuarantineEntry] = []
    for meta in sorted(qroot.glob("*/meta.json")):
        data = json.loads(meta.read_text(encoding="utf-8"))
        entries.append(QuarantineEntry(**data))
    return entries


def restore_quarantined(vault_root: Path, qid: str, destination: Path | None = None) -> Path:
    vault_root = vault_root.expanduser().resolve()
    qdir = vault_root / "vault" / QUARANTINE_DIR / qid
    meta_path = qdir / "meta.json"
    if not meta_path.exists():
        raise FileNotFoundError(f"Quarantine entry not found: {qid}")

    data = json.loads(meta_path.read_text(encoding="utf-8"))
    original_path = Path(data["original_path"])
    dest = destination.expanduser().resolve() if destination else original_path
    dest.parent.mkdir(parents=True, exist_ok=True)

    quarantined_files = [p for p in qdir.iterdir() if p.name != "meta.json"]
    if len(quarantined_files) != 1:
        raise RuntimeError("Expected exactly one quarantined file")

    quarantined_files[0].replace(dest)
    return dest
