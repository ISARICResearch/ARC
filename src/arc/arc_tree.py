from __future__ import annotations


__all__ = [
    "get_tree_items",
]


# -- IMPORTS --

# -- Standard libraries --
import re
from typing import Tuple

# -- 3rd party libraries --
import pandas as pd

# -- Internal libraries --


INCLUDE_NOT_SHOW = [
    "otherl3",
    "otherl2",
    "route",
    "route2",
    "agent",
    "agent2",
    "warn",
    "warn2",
    "warn3",
    "vol",
    "txt",
    "calc",
]

ROWS_FOR_TREE = [
    "Form",
    "Sec_name",
    "vari",
    "mod",
    "Question",
    "Variable",
    "Type",
]


def get_tree_items(
    df_datadicc: pd.DataFrame, version: str, dynamic_units_conversion: bool
) -> dict:
    df_tree = _create_tree_item_dataframe(df_datadicc, dynamic_units_conversion)

    tree = {"title": version, "key": "ARC", "children": []}
    seen_forms = set()
    seen_sections = dict()

    # Build tree
    for (form, sec_name), df_sec in df_tree.groupby(
        ["Form", "Sec_name"], dropna=False, sort=False
    ):
        form_upper = str(form).upper()
        sec_name_upper = str(sec_name).upper()

        tree, seen_forms, seen_sections = _add_form_to_tree(
            tree, seen_forms, seen_sections, form_upper
        )
        tree, seen_sections = _add_section_to_tree(
            tree, seen_sections, form_upper, sec_name_upper
        )
        section_node = _find_section_node(tree, form_upper, sec_name_upper)

        df_sec = df_sec.sort_values("_row_order")
        for vari, df_variable in df_sec.groupby("vari", dropna=False, sort=False):
            # SPECIAL CASE: for unit questions, make THAT row the parent, and attach all other rows (same vari) as children.
            df_parent_of_units, df_units = _get_units_parent_units_dataframes(
                dynamic_units_conversion, df_variable
            )
            if not df_parent_of_units.empty:
                parent_title = _format_question_text(df_parent_of_units.iloc[0])
                parent_key = df_parent_of_units["Variable"].values[0]

                parent_node = {
                    "title": parent_title,
                    "key": parent_key,
                    "children": [],
                }
                section_node["children"].append(parent_node)

                # add children (units)
                for _, variable_series in df_units.iterrows():
                    parent_node["children"].append(
                        {
                            "title": _format_question_text(variable_series),
                            "key": f"{variable_series['Variable']}",
                        }
                    )

            else:
                # Fallback: your normal grouping (>=3 => group; else flat)
                n_total = int(
                    df_variable["n_in_vari_total"].iloc[0]
                    if pd.notna(df_variable["n_in_vari_total"].iloc[0])
                    else 0
                )

                if n_total >= 3:
                    parent_title = df_variable["first_question"].iloc[0]
                    parent_key = f"{form_upper}-{sec_name_upper}-VARI-{vari}-GROUP"
                    parent_node = {
                        "title": parent_title + " (Group)",
                        "key": parent_key,
                        "children": [],
                    }
                    section_node["children"].append(parent_node)

                    for _, variable_series in df_variable.iterrows():
                        parent_node["children"].append(
                            {
                                "title": _format_question_text(variable_series),
                                "key": f"{variable_series['Variable']}",
                            }
                        )
                else:
                    for _, variable_series in df_variable.iterrows():
                        section_node["children"].append(
                            {
                                "title": _format_question_text(variable_series),
                                "key": f"{variable_series['Variable']}",
                            }
                        )

    return tree


def _get_units_parent_units_dataframes(
    dynamic_units_conversion: bool, df_variable: pd.DataFrame
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    df_units = pd.DataFrame()
    if not dynamic_units_conversion:
        # E.g. demog_height_units
        df_parent_of_units = df_variable.loc[df_variable["Validation"] == "units"]
        if not df_parent_of_units.empty:
            parent_name = df_parent_of_units["Variable"].values[0]
            # Don't need the old parent name. Pass the one with _units only
            old_parent_name = re.sub("_units$", "", parent_name)
            df_units = df_variable[
                ~df_variable["Variable"].isin([parent_name, old_parent_name])
            ]
    else:
        # E.g. demog_height
        df_parent_of_units = df_variable.loc[
            df_variable["Question"].str.contains(
                "(select units)", case=False, na=False, regex=False
            )
        ]
        if not df_parent_of_units.empty:
            parent_name = df_parent_of_units["Variable"].values[0]
            df_units = df_variable[df_variable["Variable"] != parent_name]

    return df_parent_of_units.reset_index(drop=True), df_units.reset_index(drop=True)


def _create_tree_item_dataframe(
    df_datadicc: pd.DataFrame, dynamic_units_conversion: bool
) -> pd.DataFrame:
    # hide some mods
    df_for_item = df_datadicc.loc[~df_datadicc["mod"].isin(INCLUDE_NOT_SHOW)]

    # Deal with units based on ARC version
    if not dynamic_units_conversion:
        # Keep (mod = units, Validation = units), as needed for subsequent steps
        df_for_item = df_for_item.loc[
            ~((df_datadicc["mod"] == "units") & (df_datadicc["Validation"] != "units"))
        ]
        df_for_item = df_for_item[ROWS_FOR_TREE + ["Validation"]]
    else:
        df_for_item = df_for_item.loc[df_datadicc["mod"] != "units"]
        df_for_item = df_for_item[ROWS_FOR_TREE]

    # counts per (Form, Sec_name, vari)
    base_for_counts = df_for_item[["Form", "Sec_name", "vari"]].copy()
    group_counts_total = (
        base_for_counts.groupby(["Form", "Sec_name", "vari"], dropna=False)
        .size()
        .rename("n_in_vari_total")
        .reset_index()
    )

    # prep indexing and "first question"
    df_for_item = df_for_item[df_for_item["Sec_name"].notna()].copy()
    df_for_item["_row_order"] = range(len(df_for_item))
    df_idx_first = (
        df_for_item.sort_values("_row_order")
        .groupby(["Form", "Sec_name", "vari"], dropna=False, as_index=False)
        .nth(0)[["Form", "Sec_name", "vari", "Question", "Variable"]]
        .rename(columns={"Question": "first_question", "Variable": "first_variable"})
        .reset_index(drop=True)
    )

    # merge counts + first-question
    df_for_item = df_for_item.merge(
        group_counts_total, on=["Form", "Sec_name", "vari"], how="left"
    ).merge(df_idx_first, on=["Form", "Sec_name", "vari"], how="left")

    return df_for_item


def _add_form_to_tree(
    tree: dict, seen_forms: set, seen_sections: dict, form_upper: str
) -> Tuple[dict, set, dict]:
    if form_upper not in seen_forms:
        tree["children"].append(
            {
                "title": form_upper,
                "key": form_upper,
                "children": [],
            }
        )
        seen_forms.add(form_upper)
        seen_sections[form_upper] = set()
    return tree, seen_forms, seen_sections


def _add_section_to_tree(
    tree: dict, seen_sections: dict, form_upper: str, sec_name_upper: str
) -> Tuple[dict, dict]:
    if sec_name_upper not in seen_sections[form_upper]:
        for child in tree["children"]:
            if child["title"] == form_upper:
                child["children"].append(
                    {
                        "title": sec_name_upper,
                        "key": f"{form_upper}-{sec_name_upper}",
                        "children": [],
                    }
                )
                break
        seen_sections[form_upper].add(sec_name_upper)
    return tree, seen_sections


def _find_section_node(tree: dict, form_upper: str, sec_name_upper: str) -> None | dict:
    section_node = None
    for child in tree["children"]:
        if child["title"] == form_upper:
            for sec_child in child["children"]:
                if sec_child["title"] == sec_name_upper:
                    section_node = sec_child
                    break
    return section_node


def _format_question_text(row: pd.Series) -> str:
    if row["Type"] == "user_list":
        return "↳ " + row["Question"]
    elif row["Type"] == "multi_list":
        return "⇉ " + row["Question"]
    return row["Question"]
