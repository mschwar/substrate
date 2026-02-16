# Agent C Report & Instructions

## Report (2026-02-03)
- Added integration tests covering editor + daily endpoints in `texttests/integration/test_api_server.py`, including token enforcement and `validate_only` no-write behavior.
- Updated UI READMEs for editor + daily flows.
- Tests not yet run.

## New Instructions (append)
- Run the integration suite after endpoint changes and report any failures with exact repro steps.
- Add edge-case tests:
  - Missing `path` in `/api/item/update`.
  - Invalid date formats for `/api/daily/open` and `/api/daily/append`.
  - Invalid JSON payload handling for editor endpoints.
- If feasible, add a FastAPI-backed test path (or param) to reduce reliance on the deprecated `api_server.py`.
