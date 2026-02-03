from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from substrate.ops_log import append_ops_log, filter_ops_since, tail_ops_log


def test_ops_log_tail_and_since(vault_root: Path):
    append_ops_log(vault_root, "test.first", {"a": 1})
    since = datetime.now(timezone.utc).isoformat()
    append_ops_log(vault_root, "test.second", {"b": 2})

    tail = tail_ops_log(vault_root, limit=1)
    assert tail[-1].op == "test.second"

    entries = filter_ops_since(vault_root, since)
    assert any(e.op == "test.second" for e in entries)
