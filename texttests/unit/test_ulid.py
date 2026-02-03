from __future__ import annotations

import time

from substrate.ulid import new_ulid


def test_ulid_monotonic_same_ms():
    ts = int(time.time() * 1000)
    a = new_ulid(ts)
    b = new_ulid(ts)
    assert a < b


def test_ulid_monotonic_increasing_time():
    a = new_ulid(1)
    b = new_ulid(2)
    assert a < b
