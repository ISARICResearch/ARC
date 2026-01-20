import json
import pathlib
import pytest
import pandas as pd

BASE_DIR = pathlib.Path(".")
UNITS_DIR = pathlib.Path("units")
ARC_PATH = BASE_DIR / "ARC.csv"
DATA_PATH = UNITS_DIR / "unit_conversion.json"


def load_json(path: pathlib.Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def extract_field_names_from_json(path: pathlib.Path):
    """
    Extract field names from the unit conversions JSON:
    - field_name
    - units_field_name
    - to_unit.unit_field_name
    - unit_conversions[].from_unit.unit_field_name
    """
    return


@pytest.mark.critical
def test_fields_exist_in_arc():
    """
    Check field names listed in unit conversion file exist in ARC.
    """
    unit_conversions = load_json(DATA_PATH)
    arc = pd.read_csv(ARC_PATH, dtype="object", usecols=["Variable"])
    return
