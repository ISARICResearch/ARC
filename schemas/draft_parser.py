"""
Create a template schema for transforming ARC data into the ISARIC format.
"""

import pandas as pd
import json
import toml_writer as tomli_w
import warnings
import sys

from units.utils import ConversionRegistry

# Create a ConversionRegistry instance for looking up unit values
_unit_registry = ConversionRegistry().load_from_json(
    "units/unit_conversion.json", "units/unit_conversion.schema.json"
)


def if_all_not_missing(field, missing_values=["UNK", "NI", "NASK", "NA"]):
    """
    Helper function to create an 'if' condition that checks a field is not equal to any
    of the specified missing values, or empty."""
    return {"all": [{field: {"!=": opt}} for opt in missing_values + [""]]}


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


def attrs_with_units(arc):
    """
    Don't use inside `make_long_row`, so we have the full arc file
    """
    rules = []
    arc_filter = arc["Variable"].str.endswith("_units")
    vars_with_units = arc[arc_filter]["Variable"].str.removesuffix("_units")
    arc_vars_to_remove = (
        vars_with_units.copy().to_list() + arc[arc_filter]["Variable"].to_list()
    )

    for var in vars_with_units:
        unit_options = arc[arc["Variable"].str.startswith(var + "_")][
            "Variable"
        ].to_list()
        arc_vars_to_remove += unit_options
        # Remove the unit field itself from the options list
        unit_options.remove(var + "_units")

        for opt in unit_options:
            rule = {
                "attribute": opt,
                # Have to construct an if rule here as it's dependent on both there being data present,
                # *and* the unit being correct.
                "if": {
                    "all": [
                        {opt: {"!=": ""}, "can_skip": True},
                        {var: {"!=": ""}, "can_skip": True},
                        {
                            f"{var}_units": _unit_registry.get_unit_value_from_unit_field_name(
                                var, opt
                            )
                        },
                    ]
                },
                # Either a the field exists with the unit in the name, or data is present as `name, name_units` columns where
                # the being entered in this unit-specific column is dependent on the units selected.
                "value_num": {
                    "combinedType": "firstNonNull",
                    "fields": [
                        {
                            "field": opt,
                            "apply": {"function": "values_strip_missing"},
                            "can_skip": True,
                        },
                        {
                            "field": var,
                            "apply": {"function": "values_strip_missing"},
                            "can_skip": True,
                        },
                    ],
                },
                "attribute_unit": (
                    _unit_registry.get_unit_label_from_unit_field_name(var, opt)
                ),
                "attribute_status": {
                    "combinedType": "firstNonNull",
                    "fields": [
                        {
                            "field": opt,
                            "apply": {"function": "attribute_status_fill"},
                            "can_skip": True,
                        },
                        {
                            "field": var,
                            "apply": {"function": "attribute_status_fill"},
                            "can_skip": True,
                        },
                    ],
                },
                "ref": arc[arc.Variable == var]["Form"].item(),
            }

            rules.append(rule)

    return rules, arc[~arc["Variable"].isin(arc_vars_to_remove)]


def make_long_row(arc, types, rule_func):
    arc_filter = arc["Type"].isin(types)
    filtered_arc = arc[arc_filter]

    rules = rule_func(filtered_arc)

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
            "attribute_status": {
                "field": row["Variable"],
                "apply": {"function": "attribute_status_fill"},
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
                "if": if_all_not_missing(row["Variable"]),
            },
            "attribute_status": {
                "field": row["Variable"],
                "apply": {"function": "attribute_status_fill"},
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
                "if": if_all_not_missing(row["Variable"]),
            },
            "attribute_status": {
                "field": row["Variable"],
                "apply": {"function": "attribute_status_fill"},
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
                "if": if_all_not_missing(row["Variable"]),
            },
            "attribute_status": {
                "field": row["Variable"],
                "apply": {"function": "attribute_status_fill"},
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
                    "date": {
                        "field": "pres_date",
                        "if": if_all_not_missing("pres_date"),
                    },
                },
                "daily": {
                    "phase": "during_observation",
                    "date": {
                        "field": "daily_date",
                        "if": if_all_not_missing("daily_date"),
                    },
                },
                "medication": {
                    "event_id": {
                        "generate": {
                            "type": "uuid5",
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
                        "if": if_all_not_missing("medi_medstartdate"),
                    },
                    "duration": {
                        "field": "medi_numdays",
                        "if": if_all_not_missing("medi_numdays"),
                    },
                },
                "pathogen_testing": {
                    "event_id": {
                        "generate": {
                            "type": "uuid5",
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
                        "if": if_all_not_missing("test_collectiondate"),
                    },
                },
                "photographs": {
                    "event_id": {
                        "generate": {
                            "type": "uuid5",
                            "values": [
                                "subjid",
                                "redcap_repeat_instrument",
                                "redcap_repeat_instance",
                            ],
                        }
                    },
                    "phase": "during_observation",
                    "date": {
                        "field": "photo_date",
                        "if": if_all_not_missing("photo_date"),
                    },
                },
                "outcome": {
                    "phase": "outcome",
                    "date": {
                        "field": "outco_date",
                        "if": if_all_not_missing("outco_date"),
                    },
                },
                "follow_up": {
                    "phase": "follow_up",
                    "date": {
                        "field": "follow_date",
                        "if": if_all_not_missing("follow_date"),
                    },
                },
                "withdrawal": {
                    "phase": "follow_up",
                    "date": {
                        "field": "withd_date",
                        "if": if_all_not_missing("withd_date"),
                    },
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
        k: {
            "field": k,
            "if": if_all_not_missing(k),
        }
        if k in arc_core_vars
        else "TODO: FILL THIS IN"
        for k in core_fields
    }

    for var in arc_core_vars:
        if opts := get_value_options(arc[arc.Variable == var]["Answer Options"].item()):
            parser["core"][var]["values"] = opts
        elif arc[arc.Variable == var]["Type"].item() in ["user_list"]:
            # Outcome options
            parser["core"][var]["values"] = read_list_file(
                f"Lists/{'/'.join(arc[arc.Variable == var]['List'].item().split('_'))}.csv"
            )

    # Hard-code some of the fields we know about

    parser["core"]["demog_age_days"] = {
        "combinedType": "firstNonNull",
        "fields": [
            {
                "field": "demog_calcage_days",
            },
            {
                "field": "demog_age",
                "unit": "days",
                "source_unit": {
                    "field": "demog_age_units",
                    "values": get_value_options(
                        arc[arc.Variable == "demog_age_units"]["Answer Options"].item(),
                        lower_case=True,
                    ),
                },
            },
        ],
    }

    core_fields += ["demog_age", "demog_age_units", "demog_calcage_days"]

    # Hard-code the medi_dose field as it should behave differently to other '_units' fields
    unit_options = get_value_options(
        arc[arc.Variable == "medi_units"]["Answer Options"].item()
    )
    parser["long"] = [
        {
            "attribute": "medi_dose",
            "value_num": {
                "field": "medi_dose",
                "if": if_all_not_missing("medi_dose"),
            },
            "attribute_unit": {
                "combinedType": "firstNonNull",
                "fields": [
                    {
                        "field": "medi_units_oth",
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
            # "attribute_status": attribute_status_rule("medi_dose"),
            "ref": arc[arc.Variable == "medi_dose"]["Form"].item(),
        }
    ]

    hard_coded_fields = core_fields + ["medi_dose", "medi_units", "medi_units_oth"]

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
    unit_rules, arc_no_units = attrs_with_units(arc_remaining)
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
    generate_parser(
        tag,
        filename="mpox_parser_1.2.1",
        preset="preset_ARChetype Disease CRF_Mpox",
    )


if __name__ == "__main__":
    main()
