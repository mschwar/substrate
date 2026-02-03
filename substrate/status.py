from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


ALLOWED_STATUSES = {
    "inbox",
    "draft",
    "canonical",
    "archived",
    "tombstoned",
}

_ALLOWED_TRANSITIONS = {
    "inbox": {"inbox", "draft", "canonical", "archived", "tombstoned"},
    "draft": {"draft", "canonical", "archived", "tombstoned"},
    "canonical": {"canonical", "archived", "tombstoned"},
    "archived": {"archived", "tombstoned"},
    "tombstoned": {"tombstoned"},
}


@dataclass(frozen=True)
class StatusTransitionError(Exception):
    message: str


def validate_status_transition(old_status: str, new_status: str) -> None:
    if old_status not in ALLOWED_STATUSES:
        raise StatusTransitionError(f"unknown old status: {old_status}")
    if new_status not in ALLOWED_STATUSES:
        raise StatusTransitionError(f"unknown new status: {new_status}")
    allowed = _ALLOWED_TRANSITIONS.get(old_status, set())
    if new_status not in allowed:
        raise StatusTransitionError(f"illegal status transition: {old_status} -> {new_status}")
