from __future__ import annotations

from pathlib import Path

from substrate.schema import load_schema, validate_frontmatter_verbose


def _schema_path() -> Path:
    return Path("schema/v0.1.json")


def test_unknown_fields_warns_and_errors():
    frontmatter = {
        "schema_version": "0.1",
        "id": "01HZX0M0M4W6W7K7Q8T2K3Q2Q4",
        "type": "note",
        "created": "2026-02-03T10:00:00+00:00",
        "updated": "2026-02-03T10:00:00+00:00",
        "status": "inbox",
        "privacy": "private",
        "unknown": "field",
    }
    result = validate_frontmatter_verbose(frontmatter, load_schema(_schema_path()))
    assert any("unknown field" in w for w in result.warnings)
    assert any("unknown field not allowed" in e for e in result.errors)


def test_type_coercions_warning_and_coerce():
    frontmatter = {
        "schema_version": "0.1",
        "id": "01HZX0M0M4W6W7K7Q8T2K3Q2Q4",
        "type": "note",
        "created": "2026-02-03T10:00:00+00:00",
        "updated": "2026-02-03T10:00:00+00:00",
        "status": "inbox",
        "privacy": "private",
        "confidence": "0.8",
    }
    result = validate_frontmatter_verbose(frontmatter, load_schema(_schema_path()), coerce=True)
    assert any("coerced" in w for w in result.warnings)
    assert result.errors == []
    assert isinstance(result.data["confidence"], float)
