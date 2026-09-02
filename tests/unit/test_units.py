import pathlib
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


@pytest.mark.high
def test_arc_units_correct_type_validation():
    """
    Variable names ending in "_units" must have Type="radio" and Validation="units",
    except the variables "demog_age_units" and "medi_units" which are special cases.
    """
    arc = pd.read_csv(
        ARC_PATH, dtype="object", usecols=["Variable", "Type", "Validation"]
    )
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
            "Variable",
        ].tolist()
        for x in field_names
    }

    unit_answers = {
        x: arc.set_index("Variable").loc[x + "_units", "Answer Options"].split("|")
        for x in field_names
    }
    unit_answers = {k: [x.strip() for x in v] for k, v in unit_answers.items()}

    condition = [
        len(unit_answers[x]) == len(unit_specific_field_names[x]) for x in field_names
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
                "Minimum",
            ]
            .astype(float)
            .min(skipna=False),
            "max_of_max": arc.loc[
                arc["Variable"].str.startswith(x + "_")
                & ~arc["Variable"].str.endswith("_units"),
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
            "Variable",
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
        units_field_names[x]
        for x in field_names
        if entries[x].units_field_name != units_field_names[x]
    ]
    if inconsistent_units_field_names:
        pytest.fail(
            f"ARC variables {inconsistent_units_field_names} does not match the entry in "
            f"conversion JSON file {UNITS_PATH}"
        )

    missing_unit_specific_field_names = [
        x
        for x in field_names
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
        usecols=["Variable", "Validation"],
    )

    units_idx = arc["Validation"] == "units"
    units_field_names = arc.loc[units_idx, "Variable"].tolist()
    field_names = [x.split("_units")[0] for x in units_field_names]

    units_field_names = dict(zip(field_names, units_field_names))
    unit_specific_field_names = {
        x: arc.loc[
            arc["Variable"].str.startswith(x + "_")
            & ~arc["Variable"].str.endswith("_units"),
            "Variable",
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
        x
        for x in field_names
        if not set(x.unit_field_name for x in entries[x].units.units).issubset(
            unit_specific_field_names[x]
        )
    ]
    if missing_unit_specific_field_names:
        pytest.fail(
            f"ARC variables {missing_unit_specific_field_names} does not include units "
            f"listed in conversion JSON file {UNITS_PATH}. Please update the JSON file."
        )


@pytest.mark.high
def test_valid_conversions_for_min_max():
    """
    Test that the min/max values for unit-specific variables align with conversion
    functions.
    """
    arc = pd.read_csv(
        ARC_PATH,
        dtype="object",
        usecols=["Variable", "Validation", "Minimum", "Maximum"],
    )

    units_idx = arc["Validation"] == "units"
    units_field_names = arc.loc[units_idx, "Variable"].tolist()
    field_names = [x.split("_units")[0] for x in units_field_names]

    units_field_names = dict(zip(field_names, units_field_names))
    arc_subset = pd.concat(
        [
            arc.loc[
                arc["Variable"].str.startswith(x + "_")
                & ~arc["Variable"].str.endswith("_units"),
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

    conversion_registry = ConversionRegistry().load_from_json(
        path=UNITS_PATH,
        schema_path=SCHEMA_PATH,
    )

    entries = conversion_registry.conversion_entries

    # Ignore fields not yet in the JSON file, these are highlighted by an earlier test
    arc_subset = arc_subset.loc[arc_subset["field_name"].isin(entries.keys())]
    field_names = arc_subset["field_name"].unique().tolist()

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
        for x in field_names
        if x in arc_subset.loc[invalid_min, "field_name"].tolist()
    ]
    invalid_max = [
        x
        for x in field_names
        if x in arc_subset.loc[invalid_max, "field_name"].tolist()
    ]
    if invalid_min + invalid_max:
        pytest.fail(
            "Min values for unit-specific variables are not consistent with "
            f"the conversion functions for {invalid_min}. Fix ARC or conversion JSON. "
            "Max values for unit-specific variables are not consistent with "
            f"the conversion functions for {invalid_max}. Fix ARC or conversion JSON."
        )
