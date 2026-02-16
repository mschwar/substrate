# UI Editor v0 (Mock)

This document describes the UI editor v0 changes in `ui/tauri/src/` and how they integrate with the Phase 1 API contract.

## Overview
- Adds an editable frontmatter form plus body editor.
- Adds validation UX with inline errors and warnings.
- Adds Save button that is blocked on validation errors.
- Adds Daily Notes controls (open today, append text).
- Adds a promotion confirmation phrase (must type `PROMOTE`).

## UI Behaviors

### Editor Form
Fields:
- Title
- Type
- Status
- Privacy
- Summary
- Tags (comma-separated)
- Confidence (0.0 - 1.0)
- Schema Version (read-only)
- ID (read-only)
- Created (read-only)
- Updated (read-only)
- Body

Behavior:
- Changes update the in-memory frontmatter/body immediately.
- The header updates live as you edit title/type/status/privacy.
- Tags are stored as an array; empty tags remove the field.
- Confidence is stored as a number when valid; empty removes the field.

### Validation UX
- Runs on a debounce after changes (400ms) and again before Save.
- Calls `POST /api/validate` with `{ frontmatter, body }`.
- Shows inline errors when invalid.
- Shows warnings when valid but warning list is non-empty.
- Save button is disabled if validation is pending or invalid.

### Save
- Calls `POST /api/item/update` with `{ path, frontmatter, body, validate_only: false }`.
- Save is blocked until validation passes.
- After save, the UI reloads the item from the returned `path` or `item.path`.

### Promote
- Promote is enabled only when:
  - The current item status is `inbox`.
  - The confirm input equals `PROMOTE`.
- Calls `POST /api/promote` with `{ path, status: "canonical" }`.

### Daily Notes
- Open Today calls `GET /api/daily/open?date=YYYY-MM-DD`.
- Append calls `POST /api/daily/append` with `{ date, text }`.
- Uses UTC date (`new Date().toISOString().slice(0, 10)`) to match backend behavior.
- After success, loads the returned `path` or `item.path`.

## Bridge Commands
`ui/tauri/src/bridge.js` now supports these `invoke` commands:
- `validate` -> `POST /api/validate`
- `item_update` -> `POST /api/item/update`
- `daily_open` -> `GET /api/daily/open?date=...`
- `daily_append` -> `POST /api/daily/append`

## Running the Mock UI
Use the UI proxy to serve the static UI and forward `/api/*` to the API server:

```bash
python3 tools/api_fastapi.py --vault /path/to/vault
python3 tools/serve_ui.py --vault /path/to/vault
```

The UI is served from `ui/tauri/src/` and will proxy API calls to the FastAPI server.

## Related Docs
- `docs/API_CONTRACT.md` for the full endpoint contract.

## Next Steps
- Completed: Linked this doc from `ui/tauri/README.md`.
