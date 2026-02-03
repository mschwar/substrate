from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import re
from datetime import datetime

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover - dependency guard
    yaml = None


class SchemaError(ValueError):
    pass


@dataclass(frozen=True)
class Schema:
    raw: dict


@dataclass(frozen=True)
class ValidationResult:
    errors: list[str]
    warnings: list[str]
    data: dict


def load_schema(path: Path) -> Schema:
    if not path.exists():
        raise SchemaError(f"Schema file not found: {path}")

    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".yml", ".yaml"}:
        if yaml is None:
            raise SchemaError("PyYAML is required to load YAML schema files")
        data = yaml.safe_load(text)
    else:
        data = json.loads(text)

    if not isinstance(data, dict):
        raise SchemaError("Schema root must be an object")

    return Schema(raw=data)


def _validate_type(value: Any, expected: str) -> bool:
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "array":
        return isinstance(value, list)
    if expected == "object":
        return isinstance(value, dict)
    return False


def validate_frontmatter(frontmatter: dict, schema: Schema) -> list[str]:
    """Validate frontmatter against a minimal JSON-schema-like spec.

    Supported keys: required, properties, type, enum, items, additionalProperties,
    pattern, minimum, maximum, minItems, format.
    Returns a list of error strings (empty if valid).
    """
    return validate_frontmatter_verbose(frontmatter, schema).errors


def validate_frontmatter_verbose(
    frontmatter: dict,
    schema: Schema,
    *,
    warn_unknown: bool = True,
    coerce: bool = False,
) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []
    spec = schema.raw
    data = dict(frontmatter) if coerce else frontmatter

    if spec.get("type") not in (None, "object"):
        errors.append("schema.type must be 'object' or omitted")
        return ValidationResult(errors=errors, warnings=warnings, data=data)

    required = spec.get("required", [])
    if not isinstance(required, list):
        errors.append("schema.required must be a list")
        return ValidationResult(errors=errors, warnings=warnings, data=data)

    for key in required:
        if key not in data:
            errors.append(f"missing required field: {key}")

    properties = spec.get("properties", {})
    if not isinstance(properties, dict):
        errors.append("schema.properties must be an object")
        return ValidationResult(errors=errors, warnings=warnings, data=data)

    additional = spec.get("additionalProperties", True)

    for key, value in data.items():
        if key not in properties:
            if warn_unknown:
                warnings.append(f"unknown field: {key}")
            if additional is False:
                errors.append(f"unknown field not allowed: {key}")
            continue

        prop = properties[key]
        if not isinstance(prop, dict):
            errors.append(f"schema.properties.{key} must be an object")
            continue

        expected_type = prop.get("type")
        if expected_type and not _validate_type(value, expected_type):
            coerced = _coerce_value(value, expected_type)
            if coerced is not None:
                warnings.append(
                    f"{key} coerced from {type(value).__name__} to {expected_type}"
                )
                if coerce:
                    data[key] = coerced
                    value = coerced
                else:
                    errors.append(f"{key} must be of type {expected_type}")
                    continue
            else:
                errors.append(f"{key} must be of type {expected_type}")
                continue

        if "enum" in prop:
            enum_vals = prop["enum"]
            if not isinstance(enum_vals, list):
                errors.append(f"schema.properties.{key}.enum must be a list")
            elif value not in enum_vals:
                errors.append(f"{key} must be one of {enum_vals}")

        if expected_type == "string" and "pattern" in prop:
            pattern = prop["pattern"]
            if isinstance(pattern, str):
                if re.match(pattern, value) is None:
                    errors.append(f"{key} does not match required pattern")
            else:
                errors.append(f"schema.properties.{key}.pattern must be a string")

        if expected_type == "string" and "format" in prop:
            fmt = prop["format"]
            if fmt == "date-time":
                try:
                    _parse_iso8601(value)
                except ValueError:
                    errors.append(f"{key} must be an ISO 8601 date-time")
            elif fmt == "ulid":
                if re.match(r"^[0-9A-HJKMNP-TV-Z]{26}$", value) is None:
                    errors.append(f"{key} must be a ULID")
            else:
                errors.append(f"{key} has unsupported format: {fmt}")

        if expected_type in ("number", "integer") and "minimum" in prop:
            minimum = prop["minimum"]
            if isinstance(minimum, (int, float)) and value < minimum:
                errors.append(f"{key} must be >= {minimum}")
            elif not isinstance(minimum, (int, float)):
                errors.append(f"schema.properties.{key}.minimum must be a number")

        if expected_type in ("number", "integer") and "maximum" in prop:
            maximum = prop["maximum"]
            if isinstance(maximum, (int, float)) and value > maximum:
                errors.append(f"{key} must be <= {maximum}")
            elif not isinstance(maximum, (int, float)):
                errors.append(f"schema.properties.{key}.maximum must be a number")

        if expected_type == "array" and "minItems" in prop:
            min_items = prop["minItems"]
            if isinstance(min_items, int) and len(value) < min_items:
                errors.append(f"{key} must have at least {min_items} items")
            elif not isinstance(min_items, int):
                errors.append(f"schema.properties.{key}.minItems must be an integer")

        if expected_type == "array" and "items" in prop:
            items = prop["items"]
            if isinstance(items, dict) and "type" in items:
                item_type = items["type"]
                for idx, item in enumerate(value):
                    if not _validate_type(item, item_type):
                        errors.append(f"{key}[{idx}] must be of type {item_type}")

    return ValidationResult(errors=errors, warnings=warnings, data=data)


def _parse_iso8601(value: str) -> datetime:
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    return datetime.fromisoformat(value)


def _coerce_value(value: Any, expected_type: str) -> Any | None:
    if expected_type == "string":
        if isinstance(value, (int, float, bool)):
            return str(value)
        return None
    if expected_type == "integer":
        if isinstance(value, bool):
            return None
        if isinstance(value, int):
            return value
        if isinstance(value, float) and value.is_integer():
            return int(value)
        if isinstance(value, str) and value.isdigit():
            return int(value)
        return None
    if expected_type == "number":
        if isinstance(value, bool):
            return None
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            try:
                return float(value)
            except ValueError:
                return None
        return None
    if expected_type == "boolean":
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            lowered = value.lower()
            if lowered in ("true", "false"):
                return lowered == "true"
        return None
    if expected_type == "array":
        if isinstance(value, tuple):
            return list(value)
        return None
    return None
