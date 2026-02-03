# Decisions Log

## 2026-02-03
- Implemented Phase 0 utilities as a small Python package (`substrate/`) with a CLI (`python -m substrate`).
- Vault initialization creates `vault/` (Layer 1) and `raw/` (Layer 0) directories per PRD.
- Frontmatter validation is schema-driven; `schema/v0.1.json` defines a strict baseline with enums and basic patterns.
- Quarantine entries stored under `vault/_system/quarantine/<ulid>/` with `meta.json` for provenance and restoration.
- Added append-only ops log at `vault/_system/logs/ops.jsonl` with UTC timestamps for critical operations.
- Added repair command to normalize canonical frontmatter and quarantine invalid files; enforced schema validation during writes.
