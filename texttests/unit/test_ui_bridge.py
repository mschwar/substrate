from pathlib import Path


def test_bridge_exists():
    assert Path("ui/tauri/src/bridge.js").exists()
