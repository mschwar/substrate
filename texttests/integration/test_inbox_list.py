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


def test_inbox_list(vault_root: Path):
    result = _run_cli(
        [
            "capture",
            str(vault_root),
            "--title",
            "ListMe",
        ]
    )
    assert result.returncode == 0, result.stderr

    result = _run_cli(["inbox-list", str(vault_root)])
    assert result.returncode == 0, result.stderr
    items = json.loads(result.stdout)
    assert any(item["title"] == "ListMe" for item in items)
