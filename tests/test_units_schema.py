import json
import pathlib
import pytest
from jsonschema import Draft7Validator, exceptions

BASE_DIR = pathlib.Path("units")
SCHEMA_PATH = BASE_DIR / "unit_conversion.schema.json"
DATA_PATH = BASE_DIR / "unit_conversion.json"


def load_json(path: pathlib.Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def test_valid_schema():
    """
    Ensure the JSON schema is a valid Draft-07 schema.
    """
    schema = load_json(SCHEMA_PATH)

    try:
        Draft7Validator.check_schema(schema)
    except exceptions.SchemaError as e:
        pytest.fail(f"Schema is not a valid Draft-07 schema:\n{e}")


def test_valid_json_against_schema():
    """
    Ensure the conversion JSON file validates against the schema.
    """
    schema = load_json(SCHEMA_PATH)
    data = load_json(DATA_PATH)

    validator = Draft7Validator(schema)
    errors = list(validator.iter_errors(data))

    if errors:
        messages = []
        for err in sorted(errors, key=lambda e: e.path):
            path = "/".join(map(str, err.absolute_path)) or "<root>"
            msg = f"{path}: {err.message}"

            # include nested context (important for oneOf)
            if err.context:
                submsgs = "; ".join(sub.message for sub in err.context)
                msg += f" (details: {submsgs})"

            messages.append(msg)

        pytest.fail(
            "Data does not validate against schema:\n"
            + "\n".join(f"- {m}" for m in messages)
        )
