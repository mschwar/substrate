from __future__ import annotations

from pathlib import Path

# Vault directory names (Layer 1)
VAULT_DIRS = [
    "inbox",
    "daily",
    "items",
    "entities",
    "attachments",
    "exports",
    "_system",
]

# Layer 0 raw archive
RAW_DIRS = ["raw", "raw/blake3"]

FRONTMATTER_DELIM = "---"

DEFAULT_SCHEMA_PATH = Path("schema/v0.1.json")

QUARANTINE_DIR = Path("_system/quarantine")

# Frontmatter size limit in bytes (UTF-8)
MAX_FRONTMATTER_BYTES = 64 * 1024
