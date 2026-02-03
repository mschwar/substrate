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


def test_capture_inbox_note(vault_root: Path):
    result = _run_cli(
        [
            "capture",
            str(vault_root),
            "--title",
            "Hello",
            "--body",
            "Body",
            "--tags",
            "alpha,beta",
        ]
    )
    assert result.returncode == 0, result.stderr
    path = Path(result.stdout.strip())
    assert path.exists()

    result = _run_cli(["item-show", str(path)])
    assert result.returncode == 0, result.stderr
    assert "Hello" in result.stdout


def test_daily_open_and_append(vault_root: Path):
    result = _run_cli(["daily", "open", str(vault_root), "--date", "2026-02-03"])
    assert result.returncode == 0, result.stderr
    path = Path(result.stdout.strip())
    assert path.exists()

    result = _run_cli([
        "daily",
        "append",
        str(vault_root),
        "Entry",
        "--date",
        "2026-02-03",
    ])
    assert result.returncode == 0, result.stderr
    assert "Entry" in path.read_text(encoding="utf-8")


def test_frontmatter_set(vault_root: Path):
    result = _run_cli(
        [
            "capture",
            str(vault_root),
            "--title",
            "Initial",
        ]
    )
    assert result.returncode == 0, result.stderr
    path = Path(result.stdout.strip())

    result = _run_cli([
        "frontmatter-set",
        str(path),
        json.dumps({"title": "Updated"}),
    ])
    assert result.returncode == 0, result.stderr
    assert "Updated" in result.stdout
