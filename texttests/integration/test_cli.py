from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from substrate.io import dump_frontmatter, safe_write_text


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _run_cli(args: list[str]) -> subprocess.CompletedProcess[str]:
    root = _repo_root()
    env = os.environ.copy()
    env["PYTHONPATH"] = str(root)
    return subprocess.run(
        [sys.executable, "-m", "substrate", *args],
        cwd=str(root),
        env=env,
        text=True,
        capture_output=True,
    )


def test_cli_write_validate_opslog(vault_root: Path):
    file_path = vault_root / "vault" / "items" / "cli.md"
    frontmatter = {
        "schema_version": "0.1",
        "id": "01HZX0M0M4W6W7K7Q8T2K3Q2Q4",
        "type": "note",
        "created": "2026-02-03T10:00:00+00:00",
        "updated": "2026-02-03T10:00:00+00:00",
        "status": "inbox",
        "privacy": "private",
    }
    result = _run_cli(
        [
            "write",
            str(file_path),
            "--frontmatter",
            json.dumps(frontmatter),
            "--body",
            "Body",
        ]
    )
    assert result.returncode == 0, result.stderr
    assert "Wrote" in result.stdout

    result = _run_cli(["validate", str(file_path)])
    assert result.returncode == 0, result.stderr
    assert "Frontmatter valid" in result.stdout

    result = _run_cli(["ops-log", "tail", str(vault_root), "--limit", "10"])
    assert result.returncode == 0, result.stderr
    entries = json.loads(result.stdout)
    assert any(entry["op"] == "file.write" for entry in entries)


def test_cli_repair_tree(vault_root: Path):
    items_root = vault_root / "vault" / "items"
    good_file = items_root / "good.md"
    bad_file = items_root / "bad.md"

    good_frontmatter = {
        "schema_version": "0.1",
        "id": "01HZX0M0M4W6W7K7Q8T2K3Q2Q4",
        "type": "note",
        "created": "2026-02-03T10:00:00+00:00",
        "updated": "2026-02-03T10:00:00+00:00",
        "status": "inbox",
        "privacy": "private",
    }

    items_root.mkdir(parents=True, exist_ok=True)
    safe_write_text(good_file, dump_frontmatter(good_frontmatter, "Body"))
    bad_file.write_text("no frontmatter", encoding="utf-8")

    result = _run_cli(["repair-tree", str(vault_root), str(items_root)])
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    actions = {entry["file"]: entry["action"] for entry in payload}
    assert str(bad_file) in actions
    assert actions[str(bad_file)] == "quarantined"


def test_cli_repair_dry_run_no_quarantine(vault_root: Path):
    bad_file = vault_root / "vault" / "items" / "bad_dry.md"
    bad_file.write_text("no frontmatter", encoding="utf-8")
    result = _run_cli(["repair", str(vault_root), str(bad_file), "--dry-run"])
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["action"] == "invalid"
    qroot = vault_root / "vault" / "_system" / "quarantine"
    assert not qroot.exists() or not any(qroot.iterdir())


def test_cli_ops_log_since(vault_root: Path):
    file_path = vault_root / "vault" / "items" / "since.md"
    frontmatter = {
        "schema_version": "0.1",
        "id": "01HZX0M0M4W6W7K7Q8T2K3Q2Q4",
        "type": "note",
        "created": "2026-02-03T10:00:00+00:00",
        "updated": "2026-02-03T10:00:00+00:00",
        "status": "inbox",
        "privacy": "private",
    }
    result = _run_cli(
        [
            "write",
            str(file_path),
            "--frontmatter",
            json.dumps(frontmatter),
            "--body",
            "Body",
        ]
    )
    assert result.returncode == 0, result.stderr
    # filter since epoch; should include file.write
    result = _run_cli(["ops-log", "since", str(vault_root), "1970-01-01T00:00:00+00:00"])
    assert result.returncode == 0, result.stderr
    entries = json.loads(result.stdout)
    assert any(entry["op"] == "file.write" for entry in entries)
