from __future__ import annotations

from pathlib import Path

from .constants import RAW_DIRS, VAULT_DIRS


def init_vault(root: Path) -> None:
    root = root.expanduser().resolve()
    for rel in VAULT_DIRS:
        (root / "vault" / rel).mkdir(parents=True, exist_ok=True)
    for rel in RAW_DIRS:
        (root / rel).mkdir(parents=True, exist_ok=True)


def vault_structure(root: Path) -> list[Path]:
    root = root.expanduser().resolve()
    paths = [root / "vault" / rel for rel in VAULT_DIRS]
    paths += [root / rel for rel in RAW_DIRS]
    return paths
