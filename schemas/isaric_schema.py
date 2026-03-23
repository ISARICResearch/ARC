"""
Auto-generates a long schema matching the ISARIC format with the latest ARC variables.

To be run via a github-action when the ARC version is updated.
"""

import pandas as pd
import json
import numpy as np
from pathlib import Path
import sys
import subprocess

from units.utils import ConversionRegistry
from schemas.codes import status_codes

# Create a ConversionRegistry instance for looking up unit values
_conversion_registry = ConversionRegistry().load_from_json(
    "units/unit_conversion.json", "units/unit_conversion.schema.json"
)


def get_enums(options):
    """Extracts the enum values from the 'Answer Options' field."""
    if pd.isna(options):
        return []
    return [
        ",".join(c.split(",")[1:]).lstrip(" ").rstrip(" ") for c in options.split("|")
    ]


def medications_dosage(arc):
    # medi_units behave differently to other units.
    # Unit should be associated with the dosage, not as it's own long table entry.
    meds_filter = arc["Variable"].isin(["medi_dose", "medi_units", "medi_units_oth"])

    rule = {
        "properties": {
            "attribute": {"const": "medi_dose"},
            "value_num": {"type": "number"},
            "attribute_unit": {"type": "string"},
            "attribute_status": {
                "type": "string",
                "enum": status_codes,
                "description": "Use to indicate missing data and the reason for missingness.",
            },
        },
        "required": ["value_num", "attribute_unit"],
    }

    return [rule], arc[~meds_filter]


def attrs_with_enums(arc, types: list[str]):
    rules = []
    arc_filter = arc["Type"].isin(types)
    arc_long_with_enums = arc[arc_filter]

    for options, group in arc_long_with_enums.groupby("Answer Options"):
        if len(group) == 1:
            name = {"const": group.Variable.iloc[0]}
        else:
            name = {"enum": group.Variable.tolist()}
        enums = get_enums(options)
        rule = {
            "properties": {
                "attribute": name,
                "value": {"type": "string", "enum": enums},
                "attribute_status": {
                    "type": "string",
                    "enum": status_codes,
                },
            },
            "required": ["value"],
        }

        rules.append(rule)

    return rules, arc[~arc_filter]


def attrs_with_lists(arc, types: list[str]):
    rules = []
    arc_filter = arc["Type"].isin(types)
    arc_long_lists = arc[arc_filter]

    for list_file, group in arc_long_lists.groupby("List"):
        if len(group) == 1:
            name = {"const": group.Variable.item()}
        else:
            name = {"enum": group.Variable.tolist()}
        rule = {
            "properties": {
                "attribute": name,
                "attribute_status": {
                    "type": "string",
                    "enum": status_codes,
                },
            },
            "required": ["value"],
        }
        file_name = (list_file + ".csv").split("_")
        path = Path(*["Lists"] + file_name)
        if not path.exists():
            raise FileNotFoundError(f"List file {list_file} does not exist.")
        list_enums = [x.strip() for x in pd.read_csv(path).iloc[:, 0].unique().tolist()]

        rule["properties"]["value"] = {"type": "string", "enum": list_enums}

        rules.append(rule)
    return rules, arc[~arc_filter]


def attrs_with_units(arc):
    rules = []
    arc_filter = arc["Variable"].str.endswith("_units")
    vars_with_units = arc[arc_filter]["Variable"].str.removesuffix("_units")
    arc_vars_to_remove = (
        vars_with_units.copy().to_list() + arc[arc_filter]["Variable"].to_list()
    )

    for var in vars_with_units:
        unit_options = arc[
            arc["Variable"].str.startswith(var + "_")
            & ~arc["Variable"].str.endswith("_units")
        ]["Variable"].to_list()
        arc_vars_to_remove += unit_options

        rs = [
            {
                "properties": {
                    "attribute": {"const": unit_var},
                    "attribute_unit": {
                        "const": _conversion_registry.get_unit_label_from_unit_field_name(
                            unit_var.rsplit("_", 1)[0], unit_var
                        )
                    },
                    "value_num": {"type": "number"},
                    "attribute_status": {
                        "type": "string",
                        "enum": status_codes,
                    },
                },
                "required": ["value_num", "attribute_unit"],
            }
            for unit_var in unit_options
        ]
        rules.extend(rs)

    return rules, arc[~arc["Variable"].isin(arc_vars_to_remove)]


def numeric_attrs(arc, types: list[str]):
    rules = []
    arc_filter = arc["Type"].isin(types)
    arc_long_numeric = arc[arc_filter]

    for min_max, group in arc_long_numeric.groupby(
        ["Minimum", "Maximum"], dropna=False
    ):
        min, max = min_max
        if len(group) == 1:
            name = {"const": group.Variable.iloc[0]}
        else:
            name = {"enum": group.Variable.tolist()}
        rule = {
            "properties": {
                "attribute": name,
                "value_num": {"type": "number"},
                "attribute_status": {
                    "type": "string",
                    "enum": status_codes,
                },
            },
            "required": ["value_num"],
        }
        if not pd.isna(min):
            rule["properties"]["value_num"]["minimum"] = float(min)
        if not pd.isna(max):
            rule["properties"]["value_num"]["maximum"] = float(max)

        rules.append(rule)
    return rules, arc[~arc_filter]


def date_attrs(arc, types: list[str]):
    rules = []
    arc_filter = arc["Type"].isin(types)
    arc_long_dates = arc[arc_filter]

    for input_type, group in arc_long_dates.groupby("Type"):
        if len(group) == 1:
            name = {"const": group.Variable.item()}
        else:
            name = {"enum": group.Variable.tolist()}
        rule = {
            "properties": {
                "attribute": name,
                "value": {
                    "type": "string",
                    "format": "date" if input_type == "date_dmy" else "date-time",
                },
                "attribute_status": {
                    "type": "string",
                    "enum": status_codes,
                },
            },
            "required": ["value"],
        }

        rules.append(rule)
    return rules, arc[~arc_filter]


def time_attrs(arc, types: list[str]):
    rules = []
    arc_filter = arc["Type"].isin(types)
    arc_long_times = arc[arc_filter]

    for _, group in arc_long_times.groupby("Type"):
        if len(group) == 1:
            name = {"const": group.Variable.item()}
        else:
            name = {"enum": group.Variable.tolist()}
        rule = {
            "properties": {
                "attribute": name,
                "value": {"type": "string", "format": "time"},
                "attribute_status": {
                    "type": "string",
                    "enum": status_codes,
                },
            },
            "required": ["value"],
        }

        rules.append(rule)
    return rules, arc[~arc_filter]


def generic_str_attrs(arc, types: list[str]):
    arc_filter = arc["Type"].isin(types)
    arc_long_other_str = arc[arc_filter]

    rule = {
        "properties": {
            "attribute": {"enum": arc_long_other_str.Variable.tolist()},
            "value": {"type": "string"},
            "attribute_status": {
                "type": "string",
                "enum": status_codes,
            },
        },
        "required": ["value"],
    }

    return [rule], arc[~arc_filter]


def generate_long_schema(version):
    arc = pd.read_csv("ARC.csv")

    with open("schemas/isaric-core.json", "r") as f:
        template_core = json.load(f)

    with open("schemas/template-isaric-long.json", "r") as f:
        template_long = json.load(f)

    # Drop the core properties from the long schema,
    # plus the 'demog_age' variables which map to `demog_age_days``
    arc_long = arc[
        ~arc.Variable.isin(
            list(template_core["properties"].keys()) + ["demog_age", "demog_age_units"]
        )
    ]
    # Don't include descriptive, file types or NaN's (unwanted as stored attributes)
    arc_long = arc_long[~(arc_long.Type.isin(["descriptive", "file", np.nan]))]

    # medications dosage, which has units field that behaves differently
    medi_unit_rule, arc_long_med_unit = medications_dosage(arc_long)

    # Generate rules for each type of attribute
    units_rules, arc_long_no_units = attrs_with_units(arc_long_med_unit)

    enum_rules, arc_no_enums = attrs_with_enums(
        arc_long_no_units, ["radio", "checkbox"]
    )

    list_rules, arc_no_lists = attrs_with_lists(
        arc_no_enums, ["list", "user_list", "multi_list"]
    )

    numeric_rules, arc_no_numbers = numeric_attrs(arc_no_lists, ["number", "calc"])

    date_rules, arc_no_dates = date_attrs(arc_no_numbers, ["date_dmy", "datetime_dmy"])

    time_rules, arc_no_times = time_attrs(arc_no_dates, ["time"])

    other_str_rules, arc_no_other_str = generic_str_attrs(
        arc_no_times, ["text", "notes"]
    )

    # Combine all rules into one list
    one_of_rules = (
        medi_unit_rule
        + units_rules
        + enum_rules
        + list_rules
        + numeric_rules
        + date_rules
        + time_rules
        + other_str_rules
    )

    # check no types have been missed
    if len(arc_no_other_str) > 0:
        raise ValueError(
            "The following rows were not processed: \n",
            arc_no_other_str,
            "Please check the ARC.csv file for any new types.",
        )

    template_long["oneOf"] = one_of_rules

    # Generate new long schema
    with open(f"schemas/arc_{version}_isaric_long.schema.json", "w") as f:
        json.dump(template_long, f, indent=4)


def main():
    if len(sys.argv) > 1:
        tag = sys.argv[1]
    else:
        tag = subprocess.check_output(["git", "describe", "--tags"], text=True).strip()
    print(f"Running schema script with tag: {tag}")
    generate_long_schema(tag)


if __name__ == "__main__":
    main()
