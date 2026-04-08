import pathlib
import re
import json
import pytest
import pandas as pd
import numpy as np

from units.utils import ConversionRegistry, UnitConverter

BASE_DIR = pathlib.Path(".")
UNITS_DIR = pathlib.Path("units")
ARC_PATH = BASE_DIR / "ARC.csv"
UNITS_PATH = UNITS_DIR / "unit_conversion.json"
SCHEMA_PATH = UNITS_DIR / "unit_conversion.schema.json"

EXCEPTIONS = ["demog_age_units", "medi_units"]


# --- Fixtures ---


@pytest.fixture(scope="module")
def arc_df():
    """Load full ARC.csv with all columns needed for unit tests."""
    return pd.read_csv(
        ARC_PATH,
        dtype="object",
        usecols=[
            "Variable",
            "Type",
            "Validation",
            "Answer Options",
            "Question",
            "Minimum",
            "Maximum",
        ],
    )


@pytest.fixture(scope="module")
def conversion_registry():
    """Load the unit conversion registry from JSON."""
    return ConversionRegistry().load_from_json(
        path=UNITS_PATH,
        schema_path=SCHEMA_PATH,
    )


@pytest.fixture(scope="module")
def unit_conversion_json():
    """Load raw unit_conversion.json as dict list."""
    with open(UNITS_PATH, "r") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def unit_fields_info(arc_df):
    """
    Extract unit field information from ARC.

    Returns dict with:
        - units_field_names: list of variables with Validation='units'
        - field_names: list of base field names (without '_units' suffix)
        - units_field_names_dict: mapping from field_name to units_field_name
        - unit_specific_field_names: dict mapping field_name to list of unit-specific vars
    """
    units_idx = arc_df["Validation"] == "units"
    units_field_names = arc_df.loc[units_idx, "Variable"].tolist()
    field_names = [x.split("_units")[0] for x in units_field_names]

    unit_specific_field_names = {
        x: arc_df.loc[
            arc_df["Variable"].str.startswith(x + "_")
            & ~arc_df["Variable"].str.endswith("_units"),
            "Variable",
        ].tolist()
        for x in field_names
    }

    return {
        "units_field_names": units_field_names,
        "field_names": field_names,
        "units_field_names_dict": dict(zip(field_names, units_field_names)),
        "unit_specific_field_names": unit_specific_field_names,
    }


# --- Helper functions ---


def parse_answer_options(options_str, include_values=False):
    """
    Parse Answer Options string.

    Args:
        options_str: String like '1, cm | 2, in'
        include_values: If True, return [(1, 'cm'), (2, 'in')].
                        If False, return ['cm', 'in'].
    """
    if pd.isna(options_str) or not options_str.strip():
        return []
    result = []
    for option in options_str.split("|"):
        option = option.strip()
        if "," in option:
            value, label = option.split(",", 1)
            if include_values:
                result.append((int(value.strip()), label.strip()))
            else:
                result.append(label.strip())
    return result


# --- Tests ---


@pytest.mark.high
def test_arc_units_correct_type_validation(arc_df):
    """
    Variable names ending in "_units" must have Type="radio" and Validation="units",
    except the variables "demog_age_units" and "medi_units" which are special cases.
    """
    condition = (
        ~arc_df["Variable"].str.endswith("_units")
        | (arc_df["Type"].isin(["radio"]) & arc_df["Validation"].isin(["units"]))
        | arc_df["Variable"].isin(EXCEPTIONS)
    )
    if not condition.all():
        invalid = arc_df.loc[~condition].set_index("Variable").to_dict(orient="index")
        pytest.fail(
            """Variable names ending in "_units" must have Type="radio" and """
            f"""Validation="units".Variables: {invalid}"""
        )


@pytest.mark.high
def test_arc_units_have_numeric_variable(arc_df, unit_fields_info):
    """
    Variable names ending in "_units" must have a corresponding numeric variable
    without this suffix (e.g., labs_neutrophil for labs_neutrophil_units).
    """
    units_field_names = unit_fields_info["units_field_names"]
    field_names = unit_fields_info["field_names"]
    all_arc_variables = arc_df["Variable"].tolist()

    condition = [x in all_arc_variables for x in field_names]
    if not np.all(condition):
        invalid = [x for x, y in zip(units_field_names, condition) if not y]
        pytest.fail(
            f"Unit variables {invalid} do not have corresponding numeric variables"
        )


@pytest.mark.high
def test_arc_json_field_synchronization(unit_fields_info, conversion_registry):
    """
    Bidirectional synchronization check between ARC and unit_conversion.json:
    - All ARC fields with Validation='units' must exist in JSON as 'field_name's
    - All JSON field_name entries must exist in ARC
    - The units_field_name in JSON must match the ARC naming convention
    """
    field_names = unit_fields_info["field_names"]
    units_field_names_dict = unit_fields_info["units_field_names_dict"]
    entries = conversion_registry.conversion_entries

    # Check ARC → JSON: all ARC unit fields exist in JSON
    missing_in_json = [
        x
        for x in field_names
        if x not in entries.keys() and x + "_units" not in EXCEPTIONS
    ]
    if missing_in_json:
        pytest.fail(
            f"ARC variables {missing_in_json} need to be added to units "
            f"conversion JSON file {UNITS_PATH}"
        )

    # Check JSON → ARC: all JSON entries exist in ARC
    entries_filtered = {
        k: v for k, v in entries.items() if v.units_field_name not in EXCEPTIONS
    }
    missing_in_arc = [x for x in entries_filtered.keys() if x not in field_names]
    if missing_in_arc:
        pytest.fail(
            f"Conversion JSON file {UNITS_PATH} contains variables "
            f"{missing_in_arc} that are not in ARC."
        )

    # Check units_field_name in JSON matches ARC naming
    inconsistent_units_field_names = [
        units_field_names_dict[x]
        for x in field_names
        if x in entries and entries[x].units_field_name != units_field_names_dict[x]
    ]
    if inconsistent_units_field_names:
        pytest.fail(
            f"ARC variables {inconsistent_units_field_names} does not match the entry in "
            f"conversion JSON file {UNITS_PATH}"
        )


@pytest.mark.high
def test_unit_specific_variables_exist(arc_df, unit_fields_info, conversion_registry):
    """
    For each unit_field_name defined in unit_conversion.json, there must be a
    corresponding variable in ARC. Conversely, unit-specific variables in ARC
    (e.g., labs_neutrophil_pcnt) must be defined in the JSON.
    """
    field_names = unit_fields_info["field_names"]
    unit_specific_field_names = unit_fields_info["unit_specific_field_names"]
    unit_conversion = conversion_registry.conversion_entries
    all_arc_variables = arc_df["Variable"].tolist()

    missing_unit_vars = []
    for field_name in field_names:
        if field_name + "_units" in EXCEPTIONS:
            continue
        if field_name not in unit_conversion:
            # Caught by test_arc_json_field_synchronization
            continue

        actual_unit_vars = unit_specific_field_names[field_name]

        # Expected variables from unit_field_name in JSON (may be None for some units)
        json_units = unit_conversion[field_name].units
        expected_unit_vars = [
            u.unit_field_name for u in json_units.units if u.unit_field_name is not None
        ]

        missing = [v for v in expected_unit_vars if v not in all_arc_variables]
        extra = [v for v in actual_unit_vars if v not in expected_unit_vars]

        if missing or extra:
            missing_unit_vars.append(
                {
                    "field": field_name,
                    "missing": missing,
                    "extra": extra,
                }
            )

    if missing_unit_vars:
        msg = "Unit-specific variables in ARC.csv do not match unit_conversion.json:\n"
        for m in missing_unit_vars:
            if m["missing"]:
                msg += f"  - {m['field']}: missing variables {m['missing']}\n"
            if m["extra"]:
                msg += f"  - {m['field']}: unexpected variables {m['extra']}\n"
        pytest.fail(msg)


@pytest.mark.high
def test_arc_answer_options_match_unit_conversion_json(
    arc_df, unit_fields_info, conversion_registry
):
    """
    Answer Options for unit selection variables must match exactly with the
    unit values and labels in the unit_conversion.json file.
    """
    field_names = unit_fields_info["field_names"]
    unit_conversion = conversion_registry.conversion_entries

    arc_indexed = arc_df.set_index("Variable")
    arc_answer_options = {
        x: parse_answer_options(
            arc_indexed.loc[x + "_units", "Answer Options"], include_values=True
        )
        for x in field_names
    }

    # Check values and labels match between ARC and conversion JSON
    mismatches = []
    for field_name in field_names:
        if field_name + "_units" in EXCEPTIONS:
            continue
        if field_name not in unit_conversion:
            # This is caught by test_arc_json_field_synchronization
            continue

        arc_options = arc_answer_options[field_name]
        json_units = unit_conversion[field_name].units

        # Build expected pairs from JSON
        json_options = [(u.unit_value, u.unit_label) for u in json_units.units]

        if arc_options != json_options:
            mismatches.append(
                {
                    "field": field_name,
                    "arc_options": arc_options,
                    "json_options": json_options,
                }
            )

    if mismatches:
        msg = "Answer Options in ARC.csv do not match unit_conversion.json:\n"
        for m in mismatches:
            msg += (
                f"  - {m['field']}: ARC has {m['arc_options']} "
                f"but JSON has {m['json_options']}\n"
            )
        pytest.fail(msg)


@pytest.mark.high
def test_arc_consistent_min_max(arc_df, unit_fields_info):
    """
    Variables with multiple units must have consistent min-max values.
    """
    field_names = unit_fields_info["field_names"]

    values = [
        {
            "min": float(arc_df.set_index("Variable").loc[x, "Minimum"]),
            "max": float(arc_df.set_index("Variable").loc[x, "Maximum"]),
            "min_of_min": arc_df.loc[
                arc_df["Variable"].str.startswith(x + "_")
                & ~arc_df["Variable"].str.endswith("_units"),
                "Minimum",
            ]
            .astype(float)
            .min(skipna=False),
            "max_of_max": arc_df.loc[
                arc_df["Variable"].str.startswith(x + "_")
                & ~arc_df["Variable"].str.endswith("_units"),
                "Maximum",
            ]
            .astype(float)
            .max(skipna=False),
        }
        for x in field_names
    ]
    condition = [
        (
            x["min"] == x["min_of_min"]
            or np.isnan(x["min"])
            and np.isnan(x["min_of_min"])
        )
        and (
            x["max"] == x["max_of_max"]
            or np.isnan(x["max"])
            and np.isnan(x["max_of_max"])
        )
        for x in values
    ]
    if not np.all(condition):
        invalid = [x for x, y in zip(field_names, condition) if not y]
        pytest.fail(
            f"Minimum and maximum values for unit-related variables {invalid} "
            "are not consistent within ARC (i.e. min of min/max of max)"
        )


@pytest.mark.high
def test_valid_conversions_for_min_max(arc_df, unit_fields_info, conversion_registry):
    """
    Test that the min/max values for unit-specific variables align with conversion
    functions.
    """
    field_names = unit_fields_info["field_names"]
    entries = conversion_registry.conversion_entries

    arc_subset = pd.concat(
        [
            arc_df.loc[
                arc_df["Variable"].str.startswith(x + "_")
                & ~arc_df["Variable"].str.endswith("_units"),
                ["Variable", "Minimum", "Maximum"],
            ]
            .assign(field_name=x)
            .assign(from_unit=np.nan)
            .assign(preferred_unit=np.nan)
            for x in field_names
        ]
    )
    arc_subset[["Minimum", "Maximum"]] = arc_subset[["Minimum", "Maximum"]].astype(
        float
    )

    # Ignore fields not yet in the JSON file, these are highlighted by an earlier test
    arc_subset = arc_subset.loc[arc_subset["field_name"].isin(entries.keys())]
    field_names_filtered = arc_subset["field_name"].unique().tolist()

    def get_from_unit(x: pd.DataFrame):
        try:
            units = entries[x["field_name"]].units
            from_unit = units.get_unit_from_unit_field_name(x["Variable"]).unit_label
        except Exception:
            return np.nan
        return from_unit

    arc_subset["from_unit"] = arc_subset[["Variable", "field_name"]].apply(
        lambda x: get_from_unit(x), axis=1
    )
    arc_subset["preferred_unit"] = arc_subset["field_name"].apply(
        lambda x: entries[x].preferred_unit.unit_label
    )

    # Add additional columns for min/max values of preferred unit
    preferred = arc_subset.loc[
        arc_subset["from_unit"] == arc_subset["preferred_unit"]
    ].copy()
    preferred.rename(
        columns={"Minimum": "preferred_min", "Maximum": "preferred_max"}, inplace=True
    )
    arc_subset = pd.merge(
        arc_subset,
        preferred[["field_name", "preferred_min", "preferred_max"]],
        on="field_name",
        how="left",
    )

    unit_converter = UnitConverter(
        conversion_registry=conversion_registry, is_unit_labels=True
    )

    def convert(x: pd.DataFrame, values_column="Minimum"):
        if x["from_unit"] == x["preferred_unit"]:
            return x[values_column]
        output = unit_converter.convert(
            field_name=x["field_name"],
            value=x[values_column],
            from_unit=x["from_unit"],
            to_unit=x["preferred_unit"],
        )
        return output["value"] if output["converted"] else np.nan

    arc_subset["Minimum"] = arc_subset.apply(convert, axis=1)
    arc_subset["Maximum"] = arc_subset.apply(convert, values_column="Maximum", axis=1)

    # Don't necessarily need equality, but raise if relative difference is greater than 1%
    invalid_min = (1 - arc_subset["Minimum"] / arc_subset["preferred_min"]).abs() > 0.01
    invalid_max = (1 - arc_subset["Maximum"] / arc_subset["preferred_max"]).abs() > 0.01

    invalid_min = [
        x
        for x in field_names_filtered
        if x in arc_subset.loc[invalid_min, "field_name"].tolist()
    ]
    invalid_max = [
        x
        for x in field_names_filtered
        if x in arc_subset.loc[invalid_max, "field_name"].tolist()
    ]
    if invalid_min + invalid_max:
        pytest.fail(
            "Min values for unit-specific variables are not consistent with "
            f"the conversion functions for {invalid_min}. Fix ARC or conversion JSON. "
            "Max values for unit-specific variables are not consistent with "
            f"the conversion functions for {invalid_max}. Fix ARC or conversion JSON."
        )


@pytest.mark.high
def test_unit_labels_match_question_text(arc_df, unit_conversion_json):
    """
    Unit labels in unit_conversion.json must match the units displayed in
    the Question text (in parentheses) for each unit-specific variable in ARC.csv.

    This ensures consistency between the question text and the internal conversion
    logic.

    Example:
        For labs_neutrophil_pcnt with Question "Neutrophils (%)", the unit_label
        in unit_conversion.json must be "%" (not "percent" or "pcnt").
    """

    arc = arc_df.set_index("Variable")

    mismatches = []

    for conversion_entry in unit_conversion_json:
        if conversion_entry["units_field_name"] in EXCEPTIONS:
            continue

        for unit_option in conversion_entry.get("units", []):
            unit_label = unit_option.get("unit_label")
            unit_field_name = unit_option.get("unit_field_name")
            if unit_field_name is None:
                continue

            question = arc.loc[unit_field_name, "Question"]

            # Extract unit from parentheses at the end of the question
            # e.g., "CD4 cell count (cells/mm^3)" -> "cells/mm^3"
            match = re.search(r"\(([^)]+)\)\s*$", question)
            if not match:
                continue

            question_unit = match.group(1)

            if question_unit != unit_label:
                mismatches.append(
                    {
                        "variable": unit_field_name,
                        "question_unit": question_unit,
                        "conversion_unit": unit_label,
                        "question": question,
                    }
                )

    if mismatches:
        msg = "Unit labels in unit_conversion.json do not match Question text in ARC.csv:\n"
        for m in mismatches:
            msg += (
                f"  - {m['variable']}: Question has '{m['question_unit']}' "
                f"but conversion JSON has '{m['conversion_unit']}'\n"
            )
        pytest.fail(msg)


@pytest.mark.high
def test_question_units_match_answer_options(arc_df):
    """
    For unit-specific fields (e.g., labs_neutrophil_pcnt), the unit in the
    Question text must match one of the Answer Options in the corresponding
    unit selection field (e.g., labs_neutrophil_units).

    This is a direct ARC-only consistency check that doesn't rely the conversion registry.
    """

    arc = arc_df.set_index("Variable")

    # Get all unit selection fields
    units_fields = arc[arc["Validation"] == "units"].index.tolist()
    units_fields = [x for x in units_fields if x not in EXCEPTIONS]

    mismatches = []

    for units_field in units_fields:
        field_name = units_field.rsplit("_units", 1)[0]
        answer_options = parse_answer_options(arc.loc[units_field, "Answer Options"])

        # Find unit-specific variables (e.g., labs_neutrophil_pcnt for labs_neutrophil)
        unit_specific_vars = [
            v
            for v in arc.index
            if v.startswith(field_name + "_") and not v.endswith("_units")
        ]

        for var in unit_specific_vars:
            question = arc.loc[var, "Question"]

            # Extract unit from parentheses at the end of the question
            match = re.search(r"\(([^)]+)\)\s*$", question)
            if not match:
                continue

            question_unit = match.group(1)

            if question_unit not in answer_options:
                mismatches.append(
                    {
                        "variable": var,
                        "units_field": units_field,
                        "question_unit": question_unit,
                        "answer_options": answer_options,
                    }
                )

    if mismatches:
        msg = "Question units do not match Answer Options in unit selection field:\n"
        for m in mismatches:
            msg += (
                f"  - {m['variable']}: Question has '{m['question_unit']}' "
                f"but {m['units_field']} Answer Options are {m['answer_options']}\n"
            )
        pytest.fail(msg)
