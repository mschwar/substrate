from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


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


def test_inbox_view_paging(vault_root: Path):
    for idx in range(3):
        result = _run_cli(
            [
                "capture",
                str(vault_root),
                "--title",
                f"Note {idx}",
            ]
        )
        assert result.returncode == 0, result.stderr

    result = _run_cli(
        [
            "inbox-view",
            str(vault_root),
            "--limit",
            "2",
            "--offset",
            "1",
        ]
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["total"] == 3
    assert len(payload["items"]) == 2


def test_inbox_view_sorting(vault_root: Path):
    from substrate.io import dump_frontmatter, safe_write_text

    inbox_dir = vault_root / "vault" / "inbox"
    inbox_dir.mkdir(parents=True, exist_ok=True)

    items = [
        ("Alpha", "2026-02-01T10:00:00+00:00", "2026-02-01T10:00:00+00:00", "01HZX0M0M4W6W7K7Q8T2K3Q2Q4"),
        ("Zulu", "2026-02-03T10:00:00+00:00", "2026-02-03T10:00:00+00:00", "01HZX0M0M4W6W7K7Q8T2K3Q2Q5"),
        ("Beta", "2026-02-02T10:00:00+00:00", "2026-02-02T10:00:00+00:00", "01HZX0M0M4W6W7K7Q8T2K3Q2Q6"),
    ]

    for title, created, updated, uid in items:
        frontmatter = {
            "schema_version": "0.1",
            "id": uid,
            "type": "note",
            "created": created,
            "updated": updated,
            "status": "inbox",
            "privacy": "private",
            "title": title,
        }
        path = inbox_dir / f"{uid}.md"
        safe_write_text(path, dump_frontmatter(frontmatter, "Body"))

    result = _run_cli(
        [
            "inbox-view",
            str(vault_root),
            "--sort",
            "created_desc",
        ]
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    titles = [item["title"] for item in payload["items"]]
    assert titles[0] == "Zulu"

    result = _run_cli(
        [
            "inbox-view",
            str(vault_root),
            "--sort",
            "title_asc",
        ]
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    titles = [item["title"] for item in payload["items"]]
    assert titles[:3] == ["Alpha", "Beta", "Zulu"]


def test_inbox_view_filters(vault_root: Path):
    from substrate.io import dump_frontmatter, safe_write_text

    inbox_dir = vault_root / "vault" / "inbox"
    inbox_dir.mkdir(parents=True, exist_ok=True)

    items = [
        ("Private", "private", "01HZX0M0M4W6W7K7Q8T2K3Q2Q7"),
        ("Sensitive", "sensitive", "01HZX0M0M4W6W7K7Q8T2K3Q2Q8"),
    ]

    for title, privacy, uid in items:
        frontmatter = {
            "schema_version": "0.1",
            "id": uid,
            "type": "note",
            "created": "2026-02-03T10:00:00+00:00",
            "updated": "2026-02-03T10:00:00+00:00",
            "status": "inbox",
            "privacy": privacy,
            "title": title,
        }
        path = inbox_dir / f"{uid}.md"
        safe_write_text(path, dump_frontmatter(frontmatter, "Body"))

    result = _run_cli([
        "inbox-view",
        str(vault_root),
        "--privacy",
        "sensitive",
    ])
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    titles = [item["title"] for item in payload["items"]]
    assert titles == ["Sensitive"]
