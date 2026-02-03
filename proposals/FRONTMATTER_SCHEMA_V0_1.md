# Frontmatter Schema v0.1 (Proposal)

## Goals
- Enforce a minimal, stable contract for canonical items.
- Keep schema strict (no unknown keys) while leaving room to expand.
- Align with MVP scope and PRD privacy/status requirements.

## Required Fields
- `schema_version` (string, enum: `"0.1"`)
- `id` (string, ULID)
- `type` (string, enum)
- `created` (string, ISO 8601)
- `updated` (string, ISO 8601)
- `status` (string, enum)
- `privacy` (string, enum)

## Optional Fields
- `title` (string)
- `summary` (string)
- `tags` (array of string)
- `entities` (array of string; entity ids)
- `attachments` (array of string; attachment ids)
- `sources` (array; provenance list)
- `observed` (array; competing metadata claims)
- `confidence` (number; 0-1)

## Enums
- `type`: `note`, `document`, `photo`, `audio`, `web_clip`, `daily`, `entity`, `attachment`, `export`, `import_stub`
- `status`: `inbox`, `draft`, `canonical`, `archived`, `tombstoned`
- `privacy`: `public`, `private`, `sensitive`

## JSON Schema Draft

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "schema_version",
    "id",
    "type",
    "created",
    "updated",
    "status",
    "privacy"
  ],
  "properties": {
    "schema_version": {
      "type": "string",
      "enum": ["0.1"]
    },
    "id": { "type": "string" },
    "type": {
      "type": "string",
      "enum": [
        "note",
        "document",
        "photo",
        "audio",
        "web_clip",
        "daily",
        "entity",
        "attachment",
        "export",
        "import_stub"
      ]
    },
    "title": { "type": "string" },
    "created": { "type": "string" },
    "updated": { "type": "string" },
    "status": {
      "type": "string",
      "enum": [
        "inbox",
        "draft",
        "canonical",
        "archived",
        "tombstoned"
      ]
    },
    "privacy": {
      "type": "string",
      "enum": [
        "public",
        "private",
        "sensitive"
      ]
    },
    "tags": {
      "type": "array",
      "items": { "type": "string" }
    },
    "entities": {
      "type": "array",
      "items": { "type": "string" }
    },
    "attachments": {
      "type": "array",
      "items": { "type": "string" }
    },
    "sources": { "type": "array" },
    "observed": { "type": "array" },
    "confidence": { "type": "number" },
    "summary": { "type": "string" }
  }
}
```

## Notes / Open Questions
- Should `title` be required for non-daily notes?
- Should `status` default to `inbox` for new items?
- Do we want a dedicated `provenance` object instead of `sources`?
- Should `confidence` be constrained to `0..1`?
- Do we need `timezone` on individual items or just in `_system/config.yaml`?
