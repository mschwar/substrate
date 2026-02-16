# Substrate API Contract (Phase 1)

This document defines the canonical API endpoints and payloads for Phase 1 editor flows.

## Auth
- Optional token, if configured.
- Provide via header: `X-Substrate-Token: <token>`
- Or via query param: `?token=<token>` (only for GET requests).
- If token is required and missing/invalid, return `401` with `{"error":"unauthorized"}`.

## Common Error Shape
```json
{ "error": "message" }
```

## Endpoints

### GET `/api/inbox`
Query:
- `limit` (int, default 20)
- `offset` (int, default 0)
- `sort` (string, default `updated_desc`)
- `status` (csv string optional)
- `privacy` (csv string optional)

Response: `inbox_view` payload

### GET `/api/item`
Query:
- `path` (string, required)

Response: `item_view` payload

### GET `/api/search`
Query:
- `q` (string)
- `limit` (int, default 20)
- `offset` (int, default 0)
- `status` (csv string optional)
- `privacy` (csv string optional)

Response: `search_view` payload

### POST `/api/capture`
Payload:
```json
{ "title": "...", "body": "...", "tags": ["..."], "privacy": "private" }
```

Response:
```json
{ "path": "..." }
```

### POST `/api/promote`
Payload:
```json
{ "path": "...", "status": "canonical" }
```

Response:
```json
{ "path": "..." }
```

### POST `/api/validate`
Payload:
```json
{ "frontmatter": { ... }, "body": "..." }
```

Response:
```json
{ "valid": true, "errors": [], "warnings": [] }
```

### POST `/api/item/update`
Payload:
```json
{
  "path": "...",
  "frontmatter": { ... },
  "body": "...",
  "validate_only": false
}
```

Response:
```json
{
  "path": "...",
  "frontmatter": { ... },
  "body": "...",
  "warnings": [],
  "saved": true
}
```

### GET `/api/daily/open`
Query:
- `date` (YYYY-MM-DD, optional; default today)

Response:
```json
{ "path": "...", "item": { ...item_view... } }
```

### POST `/api/daily/append`
Payload:
```json
{ "date": "YYYY-MM-DD", "text": "..." }
```

Response:
```json
{ "path": "...", "item": { ...item_view... } }
```

## Notes
- All endpoints are local-only; no cloud access.
- Input validation uses schema v0.1 where applicable.
- Canonicalization and updates must write via safe IO routines.
- All writes should append to ops log.
 - Legacy compatibility: `POST /api/daily/open` with `{ "date": "YYYY-MM-DD" }` may be supported by UI clients but is not part of the canonical contract.
