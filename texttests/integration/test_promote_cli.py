from __future__ import annotations

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


def test_promote_cli(vault_root: Path):
    result = _run_cli([
        "capture",
        str(vault_root),
        "--title",
        "PromoteMe",
    ])
    assert result.returncode == 0, result.stderr
    inbox_path = Path(result.stdout.strip())
    assert inbox_path.exists()

    result = _run_cli([
        "promote",
        str(vault_root),
        str(inbox_path),
    ])
    assert result.returncode == 0, result.stderr
    target_path = Path(result.stdout.strip())
    assert target_path.exists()
    assert not inbox_path.exists()
