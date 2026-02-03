from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .constants import DEFAULT_SCHEMA_PATH
from .io import FrontmatterError, dump_frontmatter, parse_frontmatter, safe_read_text, safe_write_text
from .quarantine import QuarantineEntry, quarantine_file
from .schema import load_schema, validate_frontmatter


@dataclass(frozen=True)
class RepairResult:
    path: Path
    action: str
    errors: list[str]
    quarantined: Optional[QuarantineEntry] = None


def repair_file(
    vault_root: Path,
    file_path: Path,
    schema_path: Path | None = None,
    quarantine_invalid: bool = True,
    dry_run: bool = False,
) -> RepairResult:
    schema_path = schema_path or DEFAULT_SCHEMA_PATH
    schema = load_schema(schema_path)

    try:
        text = safe_read_text(file_path)
        parsed = parse_frontmatter(text)
    except (FrontmatterError, UnicodeDecodeError, ValueError) as exc:
        errors = [str(exc)]
        if quarantine_invalid and not dry_run:
            entry = quarantine_file(vault_root, file_path, "; ".join(errors))
            return RepairResult(path=file_path, action="quarantined", errors=errors, quarantined=entry)
        return RepairResult(path=file_path, action="invalid", errors=errors)

    errors = validate_frontmatter(parsed.frontmatter, schema)
    if errors:
        if quarantine_invalid and not dry_run:
            entry = quarantine_file(vault_root, file_path, "; ".join(errors))
            return RepairResult(path=file_path, action="quarantined", errors=errors, quarantined=entry)
        return RepairResult(path=file_path, action="invalid", errors=errors)

    normalized = dump_frontmatter(parsed.frontmatter, parsed.body)
    if normalized != text:
        if not dry_run:
            safe_write_text(file_path, normalized)
        return RepairResult(path=file_path, action="normalized", errors=[])

    return RepairResult(path=file_path, action="unchanged", errors=[])
