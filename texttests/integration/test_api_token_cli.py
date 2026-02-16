from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import yaml


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


def test_api_token_rotate(vault_root: Path):
    result = _run_cli(["api-token", "rotate", str(vault_root)])
    assert result.returncode == 0, result.stderr
    token1 = result.stdout.strip()
    assert token1

    result = _run_cli(["api-token", "rotate", str(vault_root)])
    assert result.returncode == 0, result.stderr
    token2 = result.stdout.strip()
    assert token2
    assert token1 != token2

    config_path = vault_root / "vault" / "_system" / "config.yaml"
    data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    assert data.get("api_token") == token2
