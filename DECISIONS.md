# Decisions Log

## 2026-02-03
- Implemented Phase 0 utilities as a small Python package (`substrate/`) with a CLI (`python -m substrate`).
- Vault initialization creates `vault/` (Layer 1) and `raw/` (Layer 0) directories per PRD.
- Frontmatter validation is schema-driven; `schema/v0.1.json` defines a strict baseline with enums and basic patterns.
- Quarantine entries stored under `vault/_system/quarantine/<ulid>/` with `meta.json` for provenance and restoration.
- Added append-only ops log at `vault/_system/logs/ops.jsonl` with UTC timestamps for critical operations.
- Added repair commands (`repair`, `repair-tree`) to normalize canonical frontmatter and quarantine invalid files; enforced schema validation during writes.
- Added ops-log query helpers (tail, filter, since) for deterministic audits.
- Introduced pytest-based test suite under `texttests/` with a temp-vault fixture.
- Added strict frontmatter duplicate-key detection and YAML negative tests; warnings/coercions and size limits implemented.
- Set frontmatter size limit to 64 KiB (UTF-8) until the spec defines another value.
- Extended repair-tree with `--include` glob patterns and `--limit` for deterministic batch processing.
