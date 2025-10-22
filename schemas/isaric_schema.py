"""
Auto-generates a long schema matching the ISARIC format with the latest ARC variables.

To be run via a github-action when the ARC version is updated.
"""

import pandas as pd
import json
import numpy as np
from pathlib import Path
import sys


def get_enums(options):
    """Extracts the enum values from the 'Answer Options' field."""
    if pd.isna(options):
        return []
    return [
        ",".join(c.split(",")[1:]).lstrip(" ").rstrip(" ") for c in options.split("|")
    ]


def attrs_with_enums(arc, types: list[str]):
    rules = []
    arc_filter = arc["Type"].isin(types)
    arc_long_with_enums = arc[arc_filter]

    for options, group in arc_long_with_enums.groupby("Answer Options"):
        if len(group) == 1:
            name = {"const": group.Variable.iloc[0]}
        else:
            name = {"enum": group.Variable.tolist()}
        rule = {
            "properties": {"attribute": name},
            "required": ["value"],
        }
        rule["properties"]["value"] = {"type": "string"}
        enums = get_enums(options)
        if set(enums) == {"Yes", "No"}:
            rule["properties"]["value_bool"] = {"type": "boolean"}
        else:
            rule["properties"]["value"]["enum"] = enums

        rules.append(rule)

    return rules, arc[~arc_filter]


def attrs_with_lists(arc, types: list[str]):
    rules = []
    arc_filter = arc["Type"].isin(types)
    arc_long_lists = arc[arc_filter]

    for list_file, group in arc_long_lists.groupby("List"):
        if len(group) == 1:
            name = {"const": group.Variable.iloc[0]}
        else:
            name = {"enum": group.Variable.tolist()}
        rule = {
            "properties": {"attribute": name},
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


# Currently not used
# def attrs_with_units(arc, types: list[str]):
#     rules = []
#     arc_filter = arc["Type"].isin(types)
#     vars_with_units = arc[arc_filter]["Variable"]
#     arc_vars_to_remove = vars_with_units.copy().to_list()

#     for var in vars_with_units:
#         unit_options = arc[arc["Variable"].str.startswith(var + "_")][
#             "Variable"
#         ].to_list()
#         arc_vars_to_remove += unit_options

#         units = [u.removeprefix(var + "_") for u in unit_options]

#         rule = {
#             "properties": {
#                 "attribute": {"const": var},
#                 "attribute_unit": {"enum": units},
#                 "value_num": {"type": "number"},
#             },
#             "required": ["value_num", "attribute_unit"],
#         }

#         rules.append(rule)

#     return rules, arc[~arc["Variable"].isin(arc_vars_to_remove)]


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
            "properties": {"attribute": name},
            "required": ["value_num"],
        }
        rule["properties"]["value_num"] = {"type": "number"}
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
            name = {"const": group.Variable.iloc[0]}
        else:
            name = {"enum": group.Variable.tolist()}
        rule = {
            "properties": {"attribute": name},
            "required": ["value"],
        }
        if input_type == "date_dmy":
            rule["properties"]["value"] = {"type": "string", "format": "date"}
        elif input_type == "datetime_dmy":
            rule["properties"]["value"] = {"type": "string", "format": "date-time"}

        rules.append(rule)
    return rules, arc[~arc_filter]


def generic_str_attrs(arc, types: list[str]):
    arc_filter = arc["Type"].isin(types)
    arc_long_other_str = arc[arc_filter]

    rule = {"properties": {"attribute": {"enum": arc_long_other_str.Variable.tolist()}}}
    rule["properties"]["value"] = {"type": "string"}
    rule["required"] = ["value"]

    return [rule], arc[~arc_filter]


def generate_long_schema(version):
    arc = pd.read_csv("ARC.csv")

    with open("schemas/isaric-core.json", "r") as f:
        template_core = json.load(f)

    with open("schemas/template-isaric-long.json", "r") as f:
        template_long = json.load(f)

    # Drop the core properties from the long schema
    # Don't include descriptive, file types or NaN's (unwanted as stored attributes)
    arc_long = arc[~arc.Variable.isin(template_core["properties"].keys())]
    arc_long = arc_long[~(arc_long.Type.isin(["descriptive", "file", np.nan]))]

    # Generate rules for each type of attribute
    enum_rules, arc_no_enums = attrs_with_enums(arc_long, ["radio", "checkbox"])

    list_rules, arc_no_lists = attrs_with_lists(
        arc_no_enums, ["list", "user_list", "multi_list"]
    )

    numeric_rules, arc_no_numbers = numeric_attrs(arc_no_lists, ["number", "calc"])

    date_rules, arc_no_dates = date_attrs(arc_no_numbers, ["date_dmy", "datetime_dmy"])

    other_str_rules, arc_no_other_str = generic_str_attrs(
        arc_no_dates, ["text", "notes"]
    )

    # Combine all rules into one list
    one_of_rules = (
        enum_rules + list_rules + numeric_rules + date_rules + other_str_rules
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
    tag = sys.argv[1]
    print(f"Running script with tag: {tag}")
    generate_long_schema(tag)


if __name__ == "__main__":
    main()
