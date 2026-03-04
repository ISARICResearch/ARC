"""
Create a template schema for transforming ARC data into the ISARIC format.
"""

import pandas as pd
import json
import numpy as np
import toml_writer as tomli_w
import warnings
import sys


def get_value_options(options, lower_case=False):
    """Creates a dictionary from the 'Answer Options' field."""
    if pd.isna(options):
        return None
    formatted_options = {
        k.strip(): v.strip()
        for part in options.split("|")
        for k, v in [part.split(",", 1)]
    }
    if lower_case:
        formatted_options = {k: v.lower() for k, v in formatted_options.items()}
    return formatted_options


def read_list_file(file):
    """
    Opens a file containing the list of options for a specific question and returns
    the values dictionary.
    """
    df = pd.read_csv(file)
    try:
        value_dict = pd.Series(df.iloc[:, 0].to_list(), index=df["Value"]).to_dict()
        return {str(k): v.rstrip(" ") for k, v in value_dict.items()}
    except KeyError as e:
        warnings.warn(f"From file '{file}': {e}")
        return "TODO: fix this"


def attrs_with_units(arc, types: list[str]):
    """
    Don't use inside `make_long_row`, so we have the full arc file
    """
    rules = []
    arc_filter = arc["Type"].isin(types)
    vars_with_units = arc[arc_filter]["Variable"]
    arc_vars_to_remove = vars_with_units.copy().to_list()

    for var in vars_with_units:
        unit_options = arc[arc["Variable"].str.startswith(var + "_")][
            "Variable"
        ].to_list()
        arc_vars_to_remove += unit_options

        for opt in unit_options:
            rule = {
                # "attribute": var,
                "attribute": opt,
                "value_num": {"field": opt},
                "attribute_unit": opt.rsplit("_", 1)[-1],
                "ref": arc[arc.Variable == var]["Form"].item(),
            }

            rules.append(rule)

    return rules, arc[~arc["Variable"].isin(arc_vars_to_remove)]


def make_long_row(arc, types, rule_func):
    arc_filter = arc["Type"].isin(types)
    filtered_arc = arc[arc_filter]

    rules = rule_func(filtered_arc)

    # return rules, arc[~arc_filter]
    return rules


def attrs_with_enums(arc):
    rules = []

    for _, row in arc.iterrows():
        rule = {
            "attribute": row["Variable"],
            "value": {
                "field": row["Variable"],
                "values": get_value_options(row["Answer Options"]),
            },
            "ref": row["Form"],
        }

        rules.append(rule)

    return rules


def attrs_with_checkboxes(arc):
    rules = []

    for _, row in arc.iterrows():
        options = get_value_options(row["Answer Options"])

        for k, v in options.items():
            rule = {
                "attribute": row["Variable"],
                "value": {
                    "field": row["Variable"] + f"___{k}",
                    "values": {"1": v},
                },
                "ref": row["Form"],
            }

            rules.append(rule)

    return rules


def attrs_with_lists(arc):
    rules = []

    for _, row in arc.iterrows():
        field_base = f"{row['Variable']}_"
        rule = {
            "attribute": row["Variable"],
            "value": {
                "field": field_base + "{n}item",
                "values": read_list_file(
                    f"Lists/{'/'.join(row['List'].split('_'))}.csv"
                ),
                "can_skip": True,
            },
            "ref": row["Form"],
            "for": {"n": {"range": [0, 4]}},
        }

        rules.append(rule)

    return rules


def attrs_with_userlists(arc):
    rules = []

    for _, row in arc.iterrows():
        rule = {
            "attribute": row["Variable"],
            "value": {
                "field": row["Variable"],
                "values": read_list_file(
                    f"Lists/{'/'.join(row['List'].split('_'))}.csv"
                ),
            },
            "ref": row["Form"],
        }

        rules.append(rule)

    return rules


def attrs_with_multilists(arc):
    rules = []

    for _, row in arc.iterrows():
        values = read_list_file(f"Lists/{'/'.join(row['List'].split('_'))}.csv")
        if not isinstance(values, dict):
            continue
        for i, v in values.items():
            rule = {
                "attribute": row["Variable"],
                "value": {
                    "field": f"{row['Variable']}___{i}",
                    "values": {"1": v},
                    "can_skip": True,
                },
                "ref": row["Form"],
            }

            rules.append(rule)

    return rules


def numeric_attrs(arc):
    rules = []

    for _, row in arc.iterrows():
        rule = {
            "attribute": row["Variable"],
            "value_num": {
                "field": row["Variable"],
            },
            "ref": row["Form"],
        }

        rules.append(rule)
    return rules


def date_attrs(arc):
    rules = []

    for _, row in arc.iterrows():
        rule = {
            "attribute": row["Variable"],
            "value": {
                "field": row["Variable"],
            },
            "ref": row["Form"],
        }

        rules.append(rule)
    return rules


def generic_str_attrs(arc):
    rules = []

    for _, row in arc.iterrows():
        rule = {
            "attribute": row["Variable"],
            "value": {
                "field": row["Variable"],
            },
            "ref": row["Form"],
        }

        rules.append(rule)
    return rules


def generate_parser(
    version: str,
    arc_path: str = "ARC.csv",
    filename: str | None = None,
    preset: str | None = None,
):
    """
    Generates a generic parser file for use with ADTL based on the current version of ARC,
    assuming a redcap data export format. The generated file will include all variables in the ARC file,
    except those of type "descriptive" or "file".
    If `preset` is provided, only includes variables where the provided `preset`
    column has a value of 1.

    If you wish to generate a file for an older version of ARC, you can specify the
    path to the appropriate ARC file with `arc_path`.

    Note that few select fields (e.g. `medi_dose`, `pres_date`, `daily_date`) are
    hard-coded, so you may need to edit it this file if the current ARC naming conventions
    are changed.

    Several fields are also marked as "TODO: FILL THIS IN", mostly in the core table.
    These are dataset-specific variables not collected in the current version of ARC,
    so the generated file should be edited to reflect the appropriate mappings for your dataset.
    """

    arc = pd.read_csv(arc_path)

    if preset is not None:
        arc = arc[arc[preset] == 1]

    with open("schemas/isaric-core.json", "r") as f:
        template_core = json.load(f)

    parser = {
        "adtl": {
            "name": "ARC-isaric",
            "description": "isaric",
            "defs": {
                "presentation": {
                    "phase": "presentation",
                    "date": {"field": "pres_date", "if": {"pres_date": {"!=": "NA"}}},
                },
                "daily": {
                    "phase": "during_observation",
                    "date": {"field": "daily_date", "if": {"daily_date": {"!=": "NA"}}},
                },
                "medication": {
                    "event_id": {
                        "generate": {
                            "type": "uuid",
                            "values": [
                                "subjid",
                                "redcap_repeat_instrument",
                                "redcap_repeat_instance",
                            ],
                        }
                    },
                    "phase": "during_observation",
                    "date": {
                        "field": "medi_medstartdate",
                        "if": {"medi_medstartdate": {"!=": "NA"}},
                    },
                    "duration": {
                        "field": "medi_numdays",
                        "if": {"medi_numdays": {"!=": "NA"}},
                    },
                },
                "pathogen_testing": {
                    "event_id": {
                        "generate": {
                            "type": "uuid",
                            "values": [
                                "subjid",
                                "redcap_repeat_instrument",
                                "redcap_repeat_instance",
                            ],
                        }
                    },
                    "phase": "during_observation",
                    "date": {
                        "field": "test_collectiondate",
                        "if": {"test_collectiondate": {"!=": "NA"}},
                    },
                },
                "photographs": {
                    "event_id": {
                        "generate": {
                            "type": "uuid",
                            "values": [
                                "subjid",
                                "redcap_repeat_instrument",
                                "redcap_repeat_instance",
                            ],
                        }
                    },
                    "phase": "during_observation",
                    "date": {"field": "photo_date", "if": {"photo_date": {"!=": "NA"}}},
                },
                "outcome": {
                    "phase": "outcome",
                    "date": {"field": "outco_date", "if": {"outco_date": {"!=": "NA"}}},
                },
                "follow_up": {
                    "phase": "follow_up",
                    "date": {
                        "field": "follow_date",
                        "if": {"follow_date": {"!=": "NA"}},
                    },
                },
                "withdrawal": {
                    "phase": "follow_up",
                    "date": {"field": "withd_date", "if": {"withd_date": {"!=": "NA"}}},
                },
            },
            "tables": {
                "core": {
                    "kind": "groupBy",
                    "groupBy": "subjid",
                    "aggregation": "lastNotNull",
                    "schema": "schemas/isaric-core.schema.json",
                },
                "long": {
                    "kind": "oneToMany",
                    "schema": f"schemas/arc_{version}_isaric_long.schema.json",
                    "discriminator": "attribute",
                    "common": {
                        "subjid": {"field": "subjid"},
                        "arcver": version,
                        "dataset_id": "TODO: FILL THIS IN",
                    },
                },
            },
        }
    }

    # Build the core table

    core_fields = list(template_core["properties"].keys())

    arc_core_vars = arc[arc.Variable.isin(core_fields)]["Variable"].tolist()

    parser["core"] = {
        k: {"field": k} if k in arc_core_vars else "TODO: FILL THIS IN"
        for k in core_fields
    }

    for var in arc_core_vars:
        if opts := get_value_options(arc[arc.Variable == var]["Answer Options"].item()):
            parser["core"][var]["values"] = opts

    # Hard-code some of the fields we know about

    parser["core"]["demog_age_days"] = {
        "field": "demog_age",
        "unit": "days",
        "source_unit": {
            "field": "demog_age_units",
            "values": get_value_options(
                arc[arc.Variable == "demog_age_units"]["Answer Options"].item(),
                lower_case=True,
            ),
        },
    }

    core_fields += ["demog_age", "demog_age_units"]

    # Hard-code the medi_dose field as it should behave differently to other '_units' fields
    unit_options = get_value_options(
        arc[arc.Variable == "medi_units"]["Answer Options"].item()
    )
    parser["long"] = [
        {
            "attribute": "medi_dose",
            "value_num": {"field": "medi_dose"},
            "attribute_unit": {
                "combinedType": "firstNonNull",
                "fields": [
                    {
                        "field": "medi_units_other",
                        "if": {
                            "medi_units": int(
                                next(
                                    (k for k, v in unit_options.items() if v == "Other")
                                )
                            )
                        },
                    },
                    {
                        "field": "medi_units",
                        "values": unit_options,
                    },
                ],
            },
            "ref": arc[arc.Variable == "medi_dose"]["Form"].item(),
        }
    ]

    hard_coded_fields = core_fields + ["medi_dose", "medi_units", "medi_units_other"]

    # setup for long schema
    # Drop the core properties from the long schema
    # Don't include descriptive or file types (unwanted as stored attributes)
    arc_long = arc[~arc.Variable.isin(core_fields)]
    arc_long = arc_long[~(arc_long.Type.isin(["descriptive", "file"]))]

    row_rules = {
        "enums": attrs_with_enums,
        "checkboxes": attrs_with_checkboxes,
        "lists": attrs_with_lists,
        "user_lists": attrs_with_userlists,
        "multi_lists": attrs_with_multilists,
        "numeric": numeric_attrs,
        "dates": date_attrs,
        "strings": generic_str_attrs,
    }

    row_types = {
        "enums": ["radio"],
        "checkboxes": ["checkbox"],
        # user_list is single-select, multi_list is ___, list is an entry point where additional single-entry columns have an '_{n}item' suffix.
        "lists": ["list"],
        "user_lists": ["user_list"],
        "multi_lists": ["multi_list"],
        "numeric": ["number", "calc"],
        "dates": ["date_dmy", "datetime_dmy", "time"],
        "strings": ["text", "notes"],
    }

    arc_remaining = arc_long[~arc_long.Variable.isin(hard_coded_fields)]
    unit_rules, arc_no_units = attrs_with_units(arc_remaining, [np.nan])
    parser["long"] += unit_rules

    for attr_type in row_rules.keys():
        rules = make_long_row(arc_no_units, row_types[attr_type], row_rules[attr_type])
        parser["long"] += rules

    # Then sort by recreating the list in the order of the ARC file

    # Make a lookup for the order
    order_index = {k: i for i, k in enumerate(arc_long["Variable"])}

    # Sort parser by looking up the dict's value in the order list
    parser["long"] = sorted(parser["long"], key=lambda d: order_index[d["attribute"]])

    # Generate new long table parser
    if filename is None:
        filename = f"global_arc_{version}_parser"

    with open(f"schemas/{filename}.toml", "wb") as f:
        tomli_w.dump(parser, f)


def main():
    tag = sys.argv[1]
    print(f"Running parser script with tag: {tag}")
    generate_parser(tag)


if __name__ == "__main__":
    main()
