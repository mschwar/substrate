from __future__ import annotations

from typing import Any


def validate_schema(data: Any, schema: dict, path: str = "$") -> list[str]:
    errors: list[str] = []

    expected = schema.get("type")
    if expected is not None:
        if not _type_matches(data, expected):
            errors.append(f"{path}: expected {expected}")
            return errors

    if "enum" in schema:
        if data not in schema["enum"]:
            errors.append(f"{path}: value not in enum")
            return errors

    if expected == "object" or (isinstance(expected, list) and "object" in expected):
        if isinstance(data, dict):
            required = schema.get("required", [])
            for key in required:
                if key not in data:
                    errors.append(f"{path}: missing required '{key}'")

            properties = schema.get("properties", {})
            additional = schema.get("additionalProperties", True)
            for key, value in data.items():
                if key in properties:
                    errors.extend(validate_schema(value, properties[key], f"{path}.{key}"))
                elif additional is False:
                    errors.append(f"{path}: unexpected property '{key}'")
        return errors

    if expected == "array" or (isinstance(expected, list) and "array" in expected):
        if isinstance(data, list):
            items = schema.get("items")
            if isinstance(items, dict):
                for idx, item in enumerate(data):
                    errors.extend(validate_schema(item, items, f"{path}[{idx}]"))
        return errors

    return errors


def _type_matches(value: Any, expected: Any) -> bool:
    if isinstance(expected, list):
        return any(_type_matches(value, item) for item in expected)
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
    if expected == "null":
        return value is None
    return False
