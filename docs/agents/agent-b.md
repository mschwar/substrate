# Agent B Report & Instructions

## Report (2026-02-03)
- Validation payloads now use `{ frontmatter, body }` and warnings are surfaced in the validation block; Save is enabled when valid, even with warnings.
- Item update sends `validate_only: false` alongside `{ path, frontmatter, body }`.
- Daily open uses `GET /api/daily/open?date=YYYY-MM-DD` and daily append sends `{ date, text }`.
- Added a warning state style in the validation panel.
- Uses `new Date().toISOString().slice(0, 10)` (UTC date) to match backend daily note behavior.
- Files touched: `ui/tauri/src/mock.js`, `ui/tauri/src/bridge.js`, `ui/tauri/src/styles.css`.

## New Instructions (append)
- Add an optional manual date input to the Daily Notes panel (YYYY-MM-DD). If provided, use it for `daily_open` and `daily_append`; if blank, fall back to the current UTC date.
- Update `docs/UI_EDITOR_V0.md` to document the manual date override behavior.
