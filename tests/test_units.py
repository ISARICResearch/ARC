import pathlib
import pytest
import pandas as pd
import numpy as np

from units.utils import ConversionRegistry

BASE_DIR = pathlib.Path(".")
UNITS_DIR = pathlib.Path("units")
ARC_PATH = BASE_DIR / "ARC.csv"
UNITS_PATH = UNITS_DIR / "unit_conversion.json"
SCHEMA_PATH = UNITS_DIR / "unit_conversion.schema.json"

EXCEPTIONS = ["demog_age_units", "medi_units"]


@pytest.mark.high
def test_arc_units_correct_type_validation():
    """
    Variable names ending in "_units" must have Type="radio" and Validation="units",
    except the variables "demog_age_units" and "medi_units" which are special cases.
    """
    arc = pd.read_csv(ARC_PATH, dtype="object", usecols=["Variable", "Type", "Validation"])
    condition = (
        ~arc["Variable"].str.endswith("_units")
        | (arc["Type"].isin(["radio"]) & arc["Validation"].isin(["units"]))
        | arc["Variable"].isin(EXCEPTIONS)
    )
    if not condition.all():
        invalid = arc.loc[~condition].set_index("Variable").to_dict(orient="index")
        pytest.fail(
            """Variable names ending in "_units" must have Type="radio" and """
            f"""Validation="units".Variables: {invalid}"""
        )


@pytest.mark.high
def test_arc_numeric_variables_exist():
    """
    Variable names ending in "_units" must have be related to numeric variable
    without this suffix, plus the same number of unit-specific numeric variables
    as in the Answer Options. This doesn't check that the unit-specific variables
    actually match the Answer Options though.
    """
    arc = pd.read_csv(
        ARC_PATH,
        dtype="object",
        usecols=["Variable", "Validation", "Answer Options"],
    )

    units_idx = arc["Validation"] == "units"
    units_field_names = arc.loc[units_idx, "Variable"].tolist()
    field_names = [x.split("_units")[0] for x in units_field_names]

    condition = [x in arc["Variable"].tolist() for x in field_names]
    if not np.all(condition):
        invalid = [x for x, y in zip(units_field_names, condition) if not y]
        pytest.fail(
            f"Unit variables {invalid} do not have corresponding numeric variables"
        )

    unit_specific_field_names = {
        x: arc.loc[
            arc["Variable"].str.startswith(x + "_")
            & ~arc["Variable"].str.endswith("_units"),
            "Variable"
        ].tolist()
        for x in field_names
    }

    unit_answers = {
        x: arc.set_index("Variable").loc[x + "_units", "Answer Options"].split("|")
        for x in field_names
    }
    unit_answers = {k: [x.strip() for x in v] for k, v in unit_answers.items()}

    condition = [
        len(unit_answers[x]) == len(unit_specific_field_names[x])
        for x in field_names
    ]
    if not np.all(condition):
        invalid = [x for x, y in zip(field_names, condition) if not y]
        pytest.fail(
            "The number of Answer Options for the radio units variable does not "
            f"match the number of unit-specific ARC variables. Variables: {invalid}"
        )


@pytest.mark.high
def test_arc_consistent_min_max():
    """
    Variables with multiple units must have consistent min-max values.
    """
    arc = pd.read_csv(
        ARC_PATH,
        dtype="object",
        usecols=["Variable", "Validation", "Minimum", "Maximum"],
    )

    units_idx = arc["Validation"] == "units"
    units_field_names = arc.loc[units_idx, "Variable"].tolist()
    field_names = [x.split("_units")[0] for x in units_field_names]

    values = [
        {
            "min": float(arc.set_index("Variable").loc[x, "Minimum"]),
            "max": float(arc.set_index("Variable").loc[x, "Maximum"]),
            "min_of_min": arc.loc[
                    arc["Variable"].str.startswith(x + "_")
                    & ~arc["Variable"].str.endswith("_units"),
                    "Minimum"
                ].astype(float).min(skipna=False),
            "max_of_max": arc.loc[
                   arc["Variable"].str.startswith(x + "_")
                   & ~arc["Variable"].str.endswith("_units"),
                   "Maximum"
               ].astype(float).max(skipna=False),
        }
        for x in field_names
    ]
    condition = [
        (x["min"] == x["min_of_min"] or np.isnan(x["min"]) and np.isnan(x["min_of_min"]))
        and (x["max"] == x["max_of_max"] or np.isnan(x["max"]) and np.isnan(x["max_of_max"]))
        for x in values
    ]
    if not np.all(condition):
        invalid = [x for x, y in zip(field_names, condition) if not y]
        pytest.fail(
            f"Minimum and maximum values for unit-related variables {invalid} "
            "are not consistent within ARC (i.e. min of min/max of max)"
        )


@pytest.mark.high
def test_fields_in_arc_exist_in_conversions():
    arc = pd.read_csv(
        ARC_PATH,
        dtype="object",
        usecols=["Variable", "Validation", "Answer Options"],
    )

    units_idx = arc["Validation"] == "units"
    units_field_names = arc.loc[units_idx, "Variable"].tolist()
    field_names = [x.split("_units")[0] for x in units_field_names]

    units_field_names = dict(zip(field_names, units_field_names))
    unit_specific_field_names = {
        x: arc.loc[
            arc["Variable"].str.startswith(x + "_")
            & ~arc["Variable"].str.endswith("_units"),
            "Variable"
        ].tolist()
        for x in field_names
    }

    conversion_registry = ConversionRegistry().load_from_json(
        path=UNITS_PATH,
        schema_path=SCHEMA_PATH,
    )
    entries = conversion_registry.conversion_entries

    missing_field_names = [x for x in field_names if x not in entries.keys()]
    if missing_field_names:
        pytest.fail(
            f"ARC variables {missing_field_names} need to be added to units "
            f"conversion JSON file {UNITS_PATH}"
        )

    inconsistent_units_field_names = [
        units_field_names[x] for x in field_names
        if entries[x].units_field_name != units_field_names[x]
    ]
    if inconsistent_units_field_names:
        pytest.fail(
            f"ARC variables {inconsistent_units_field_names} does not match the entry in "
            f"conversion JSON file {UNITS_PATH}"
        )

    missing_unit_specific_field_names = [
        x for x in field_names
        if not set(unit_specific_field_names[x]).issubset(
            x.unit_field_name for x in entries[x].units.units
        )
    ]
    if missing_unit_specific_field_names:
        pytest.fail(
            f"ARC variables {missing_unit_specific_field_names} have units not listed in "
            f"conversion JSON file {UNITS_PATH}. Please update the JSON file."
        )


@pytest.mark.medium
def test_fields_in_conversions_exist_in_arc():
    arc = pd.read_csv(
        ARC_PATH,
        dtype="object",
        usecols=["Variable", "Validation", "Answer Options"],
    )

    units_idx = arc["Validation"] == "units"
    units_field_names = arc.loc[units_idx, "Variable"].tolist()
    field_names = [x.split("_units")[0] for x in units_field_names]

    units_field_names = dict(zip(field_names, units_field_names))
    unit_specific_field_names = {
        x: arc.loc[
            arc["Variable"].str.startswith(x + "_")
            & ~arc["Variable"].str.endswith("_units"),
            "Variable"
        ].tolist()
        for x in field_names
    }

    conversion_registry = ConversionRegistry().load_from_json(
        path=UNITS_PATH,
        schema_path=SCHEMA_PATH,
    )
    entries = conversion_registry.conversion_entries
    entries = {k: v for k, v in entries.items() if v.units_field_name not in EXCEPTIONS}

    missing_field_names = [x for x in entries.keys() if x not in field_names]
    if missing_field_names:
        pytest.fail(
            f"Conversion JSON file {UNITS_PATH} contains variables "
            f"{missing_field_names} that are not in ARC."
        )

    missing_unit_specific_field_names = [
        x for x in field_names
        if not set(x.unit_field_name for x in entries[x].units.units).issubset(
            unit_specific_field_names[x]
        )
    ]
    if missing_unit_specific_field_names:
        pytest.fail(
            f"ARC variables {missing_unit_specific_field_names} does not include units "
            f"listed in conversion JSON file {UNITS_PATH}. Please update the JSON file."
        )
