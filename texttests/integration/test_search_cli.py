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


def test_search_cli(vault_root: Path):
    result = _run_cli([
        "capture",
        str(vault_root),
        "--title",
        "Searchable",
        "--body",
        "needle text",
    ])
    assert result.returncode == 0, result.stderr

    result = _run_cli(["search", str(vault_root), "needle"])
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert any(item["title"] == "Searchable" for item in payload)


def test_search_cli_filters(vault_root: Path):
    result = _run_cli([
        "capture",
        str(vault_root),
        "--title",
        "PrivateNote",
        "--body",
        "filter text",
        "--privacy",
        "private",
    ])
    assert result.returncode == 0, result.stderr

    result = _run_cli([
        "search",
        str(vault_root),
        "filter",
        "--privacy",
        "sensitive",
    ])
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert not any(item["title"] == "PrivateNote" for item in payload)
