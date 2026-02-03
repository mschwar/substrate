from __future__ import annotations

from substrate.io import FrontmatterError, dump_frontmatter, normalize_text, parse_frontmatter


def test_normalize_text_newlines():
    text = "a\r\nb\r\nc"
    assert normalize_text(text) == "a\nb\nc"


def test_parse_frontmatter_missing_delim():
    try:
        parse_frontmatter("no frontmatter")
    except FrontmatterError as exc:
        assert "Missing YAML" in str(exc)
    else:
        raise AssertionError("Expected FrontmatterError")


def test_dump_frontmatter_deterministic_keys():
    frontmatter = {"b": "2", "a": "1"}
    text = dump_frontmatter(frontmatter, "Body")
    assert text.index("a:") < text.index("b:")
