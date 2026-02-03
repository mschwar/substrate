from __future__ import annotations

"""Phase 1 UI stub.

This is a minimal placeholder for the future Tauri-based UI. For now it provides
an explicit entry point and basic structure so we can add UI integration tests
without pulling in Tauri yet.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class UIStatus:
    mode: str
    message: str


def launch_ui_stub() -> UIStatus:
    return UIStatus(mode="stub", message="UI not yet implemented")
