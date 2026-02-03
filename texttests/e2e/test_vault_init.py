from __future__ import annotations

from pathlib import Path

from substrate.vault import vault_structure


def test_vault_init_structure(vault_root: Path):
    expected = {p.resolve() for p in vault_structure(vault_root)}
    for path in expected:
        assert path.exists(), f"Missing {path}"
