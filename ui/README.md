# UI Placeholder

This folder will house the desktop UI. MVP prefers Tauri, but Phase 1 only
requires a stub so we can wire flows incrementally.

Phase 1 editor + daily flows (API-backed):
- Editor validates frontmatter/body via `POST /api/validate` before save.
- Editor saves via `POST /api/item/update` (supports `validate_only`).
- Daily journal open via `GET /api/daily/open` (auto-create if missing).
- Daily journal append via `POST /api/daily/append`.
