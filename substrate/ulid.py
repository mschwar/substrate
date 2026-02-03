from __future__ import annotations

import os
import threading
import time

# Crockford's Base32 alphabet
_ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"

_lock = threading.Lock()
_last_time_ms = 0
_last_random = bytearray(10)


def _encode_base32(value: int, length: int) -> str:
    chars = []
    for _ in range(length):
        value, idx = divmod(value, 32)
        chars.append(_ALPHABET[idx])
    return "".join(reversed(chars))


def _bytes_to_base32(b: bytes) -> str:
    # 80 bits -> 16 chars
    value = int.from_bytes(b, "big")
    return _encode_base32(value, 16)


def new_ulid(timestamp_ms: int | None = None) -> str:
    """Generate a monotonic ULID string.

    If multiple ULIDs are generated within the same millisecond, the random
    component is incremented to ensure monotonicity.
    """
    global _last_time_ms, _last_random

    if timestamp_ms is None:
        timestamp_ms = int(time.time() * 1000)

    if not (0 <= timestamp_ms < 2**48):
        raise ValueError("timestamp_ms out of range for ULID")

    with _lock:
        if timestamp_ms > _last_time_ms:
            _last_time_ms = timestamp_ms
            _last_random = bytearray(os.urandom(10))
        else:
            # Same millisecond: increment random (80-bit) big-endian
            carry = 1
            for i in range(9, -1, -1):
                if carry == 0:
                    break
                new_val = (_last_random[i] + carry) & 0xFF
                carry = 1 if new_val == 0 else 0
                _last_random[i] = new_val

    time_part = _encode_base32(timestamp_ms, 10)
    rand_part = _bytes_to_base32(bytes(_last_random))
    return time_part + rand_part
