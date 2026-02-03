from substrate.json_schema import validate_schema


def test_validate_schema_success():
    schema = {
        "type": "object",
        "required": ["a"],
        "properties": {"a": {"type": "string"}},
    }
    data = {"a": "ok"}
    assert validate_schema(data, schema) == []


def test_validate_schema_missing_required():
    schema = {
        "type": "object",
        "required": ["a"],
        "properties": {"a": {"type": "string"}},
    }
    data = {}
    errors = validate_schema(data, schema)
    assert errors
