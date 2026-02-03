from __future__ import annotations

from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from substrate.vault import init_vault


@pytest.fixture()
def vault_root(tmp_path: Path) -> Path:
    root = tmp_path / "vault_root"
    init_vault(root)
    return root
