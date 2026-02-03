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


def test_status_transition_rejected(vault_root: Path):
    result = _run_cli([
        "capture",
        str(vault_root),
        "--title",
        "Status",
    ])
    assert result.returncode == 0, result.stderr
    path = result.stdout.strip()

    result = _run_cli([
        "frontmatter-set",
        path,
        json.dumps({"status": "tombstoned"}),
    ])
    assert result.returncode == 0, result.stderr

    result = _run_cli([
        "frontmatter-set",
        path,
        json.dumps({"status": "canonical"}),
    ])
    assert result.returncode != 0
    assert "illegal status transition" in (result.stderr + result.stdout)
