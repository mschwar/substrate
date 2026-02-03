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
- Began Phase 1 with inbox capture, daily notes, and frontmatter editing via CLI; daily notes default to UTC until vault timezone config exists.
- Added inbox listing CLI (`inbox-list`) and a minimal UI stub entry point for Phase 1 scaffolding.
- Added item JSON view payload (`item-view`) and status transition enforcement.
- Added placeholder `ui/` and `ui/tauri/` directories for future Tauri scaffolding.
- Added inbox JSON view payload (`inbox-view`) with paging and sorting options.
- Added a static UI mock under `ui/tauri/src/` and a `tools/serve_ui.py` dev server helper.
- UI mock now fetches live inbox/item JSON via local API endpoints in `tools/serve_ui.py`.
- Added UI capture and search endpoints plus JSON schemas for view payloads.
- Added minimal JSON schema validator for view payloads in tests.
- Added basic search CLI command and UI search/capture wiring.
- Added inbox/search filter support (status/privacy) and promote flow from inbox to items.
- Added a JS invoke bridge for future Tauri command wiring.
- Added Tauri command registry stubs under `ui/tauri/src-tauri/src/`.
- Added a standalone Python API server (`tools/api_server.py`) and Tauri bridge shim (`tools/tauri_bridge.py`).
