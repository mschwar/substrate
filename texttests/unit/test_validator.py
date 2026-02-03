from __future__ import annotations

from pathlib import Path

import pytest

from substrate.io import dump_frontmatter, parse_frontmatter
from substrate.schema import load_schema, validate_frontmatter


def _schema_path() -> Path:
    return Path("schema/v0.1.json")


def test_validator_valid_frontmatter():
    frontmatter = {
        "schema_version": "0.1",
        "id": "01HZX0M0M4W6W7K7Q8T2K3Q2Q4",
        "type": "note",
        "created": "2026-02-03T10:00:00+00:00",
        "updated": "2026-02-03T10:00:00+00:00",
        "status": "inbox",
        "privacy": "private",
        "tags": ["alpha", "beta"],
        "summary": "Hello",
    }
    text = dump_frontmatter(frontmatter, "Body")
    parsed = parse_frontmatter(text)
    schema = load_schema(_schema_path())
    errors = validate_frontmatter(parsed.frontmatter, schema)
    assert errors == []


def test_validator_unknown_field_rejected():
    frontmatter = {
        "schema_version": "0.1",
        "id": "01HZX0M0M4W6W7K7Q8T2K3Q2Q4",
        "type": "note",
        "created": "2026-02-03T10:00:00+00:00",
        "updated": "2026-02-03T10:00:00+00:00",
        "status": "inbox",
        "privacy": "private",
        "unknown": "nope",
    }
    text = dump_frontmatter(frontmatter, "Body")
    parsed = parse_frontmatter(text)
    schema = load_schema(_schema_path())
    errors = validate_frontmatter(parsed.frontmatter, schema)
    assert any("unknown field" in err for err in errors)


def test_validator_invalid_timestamp():
    frontmatter = {
        "schema_version": "0.1",
        "id": "01HZX0M0M4W6W7K7Q8T2K3Q2Q4",
        "type": "note",
        "created": "not-a-time",
        "updated": "2026-02-03T10:00:00+00:00",
        "status": "inbox",
        "privacy": "private",
    }
    text = dump_frontmatter(frontmatter, "Body")
    parsed = parse_frontmatter(text)
    schema = load_schema(_schema_path())
    errors = validate_frontmatter(parsed.frontmatter, schema)
    assert any("date-time" in err for err in errors)


def test_validator_ulid_format():
    frontmatter = {
        "schema_version": "0.1",
        "id": "bad-id",
        "type": "note",
        "created": "2026-02-03T10:00:00+00:00",
        "updated": "2026-02-03T10:00:00+00:00",
        "status": "inbox",
        "privacy": "private",
    }
    text = dump_frontmatter(frontmatter, "Body")
    parsed = parse_frontmatter(text)
    schema = load_schema(_schema_path())
    errors = validate_frontmatter(parsed.frontmatter, schema)
    assert any("ULID" in err for err in errors)
