import unittest
from pathlib import Path

from substrate.io import FrontmatterError, dump_frontmatter, parse_frontmatter, safe_write_text


class TestIO(unittest.TestCase):
    def test_frontmatter_roundtrip(self):
        tmp_dir = Path(self._get_temp_dir())
        tmp_dir.mkdir(parents=True, exist_ok=True)
        content = dump_frontmatter({"title": "Hello"}, "Body")
        file_path = tmp_dir / "note.md"
        safe_write_text(file_path, content)

        parsed = parse_frontmatter(file_path.read_text(encoding="utf-8"))
        self.assertEqual(parsed.frontmatter["title"], "Hello")
        self.assertTrue(parsed.body.startswith("Body"))

    def test_missing_frontmatter_raises(self):
        with self.assertRaises(FrontmatterError):
            parse_frontmatter("No frontmatter")

    def _get_temp_dir(self):
        from tempfile import mkdtemp

        return mkdtemp(prefix="substrate-test-")


if __name__ == "__main__":
    unittest.main()
