from __future__ import annotations

import pytest

from substrate.constants import MAX_FRONTMATTER_BYTES
from substrate.io import FrontmatterError, dump_frontmatter, parse_frontmatter


def test_unterminated_frontmatter():
    text = "---\nkey: value\n"
    with pytest.raises(FrontmatterError):
        parse_frontmatter(text)


def test_non_mapping_frontmatter_rejected():
    text = "---\n- a\n- b\n---\nBody"
    with pytest.raises(FrontmatterError):
        parse_frontmatter(text)


def test_duplicate_keys_rejected():
    text = "---\nkey: a\nkey: b\n---\nBody"
    with pytest.raises(FrontmatterError):
        parse_frontmatter(text)


def test_canonical_dump_block_style():
    frontmatter = {"a": "1", "b": ["x", "y"]}
    text = dump_frontmatter(frontmatter, "Body")
    # Block style should not use flow mapping braces
    assert "{" not in text and "}" not in text


def test_frontmatter_size_limit():
    payload = "a" * (MAX_FRONTMATTER_BYTES + 1)
    text = "---\nkey: " + payload + "\n---\nBody"
    with pytest.raises(FrontmatterError):
        parse_frontmatter(text)
