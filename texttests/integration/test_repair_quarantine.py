from __future__ import annotations

from pathlib import Path

from substrate.io import dump_frontmatter, safe_write_text
from substrate.repair import repair_file


def test_repair_quarantines_invalid(vault_root: Path):
    bad_file = vault_root / "vault" / "items" / "bad.md"
    safe_write_text(bad_file, "no frontmatter")

    result = repair_file(vault_root, bad_file)
    assert result.action == "quarantined"
    qdir = vault_root / "vault" / "_system" / "quarantine" / result.quarantined.id
    assert qdir.exists()


def test_repair_normalizes_valid(vault_root: Path):
    good_file = vault_root / "vault" / "items" / "good.md"
    frontmatter = {
        "schema_version": "0.1",
        "id": "01HZX0M0M4W6W7K7Q8T2K3Q2Q4",
        "type": "note",
        "created": "2026-02-03T10:00:00+00:00",
        "updated": "2026-02-03T10:00:00+00:00",
        "status": "inbox",
        "privacy": "private",
        "title": "Zed",
    }
    safe_write_text(good_file, dump_frontmatter(frontmatter, "Body"))

    result = repair_file(vault_root, good_file)
    assert result.action in ("normalized", "unchanged")
