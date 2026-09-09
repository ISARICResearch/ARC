from __future__ import annotations


__all__ = [
    "add_required_datadicc_columns",
    "add_transformed_rows",
    "get_arc_versions",
    "get_arc",
    "get_dependencies",
    "get_dynamic_units_conversion_bool",
    "get_variable_order",
]


# -- IMPORTS --

# -- Standard libraries --
from time import perf_counter

# -- 3rd party libraries --
import pandas as pd
from packaging.version import parse

# -- Internal libraries --
from arc import arc_translations
from arc.arc_api import ArcApiClient
from arc.utils import setup_logger


logger = setup_logger(__name__)

pd.options.mode.copy_on_write = True

ARC_UNIT_CHANGE_VERSION = "v1.2.1"

_ARC_VERSION_CACHE: dict[str, tuple[pd.DataFrame, list, str]] = {}


def get_arc(version: str) -> tuple[pd.DataFrame, list, str]:
    cache_start = perf_counter()
    if version in _ARC_VERSION_CACHE:
        cached_df, cached_presets, cached_commit = _ARC_VERSION_CACHE[version]
        logger.debug(
            "arc_core.get_arc cache=HIT version=%s elapsed_ms=%.3f",
            version,
            (perf_counter() - cache_start) * 1000,
        )
        return cached_df.copy(deep=True), list(cached_presets), cached_commit

    logger.info(f"version: {version}")

    fetch_start = perf_counter()
    commit_sha = ArcApiClient().get_arc_version_sha(version)
    df_datadicc = ArcApiClient().get_dataframe_arc_sha(commit_sha, version)

    try:
        df_dependencies = get_dependencies(df_datadicc)
        df_datadicc = pd.merge(
            df_datadicc, df_dependencies[["Variable", "Dependencies"]], on="Variable"
        )

        df_datadicc["Branch"] = df_datadicc.apply(
            lambda row: arc_translations.process_skip_logic(row, df_datadicc), axis=1
        )

        # Find preset columns
        preset_column_list = [col for col in df_datadicc.columns if "preset_" in col]
        preset_list = []
        # Iterate through each string in the list
        for preset_column in preset_column_list:
            parts = preset_column.split("_")[1:]
            if len(parts) > 2:
                parts[1] = " ".join(parts[1:])
                del parts[2:]
            preset_list.append(parts)

        df_datadicc["Question_english"] = df_datadicc["Question"]
        _ARC_VERSION_CACHE[version] = (
            df_datadicc.copy(deep=True),
            list(preset_list),
            commit_sha,
        )
        logger.debug(
            "arc_core.get_arc cache=MISS version=%s elapsed_ms=%.3f",
            version,
            (perf_counter() - fetch_start) * 1000,
        )
        return df_datadicc, preset_list, commit_sha
    except Exception as e:
        logger.error(e)
        raise RuntimeError("Failed to format ARC data")


def get_arc_versions() -> tuple[list, str]:
    version_list = ArcApiClient().get_arc_version_list()
    logger.info(f"version_list: {version_list}")
    return version_list, max(version_list)


def add_required_datadicc_columns(df_datadicc: pd.DataFrame) -> pd.DataFrame:
    df_datadicc[["Sec", "vari", "mod"]] = df_datadicc["Variable"].str.split(
        "_", n=2, expand=True
    )
    df_datadicc[["Sec_name", "Expla"]] = df_datadicc["Section"].str.split(
        r"[(|:]", n=1, expand=True
    )
    return df_datadicc


def get_variable_order(df_datadicc: pd.DataFrame) -> list:
    df_datadicc["Sec_vari"] = df_datadicc["Sec"] + "_" + df_datadicc["vari"]
    order = df_datadicc[["Sec_vari"]]
    order = order.drop_duplicates().reset_index()
    return list(order["Sec_vari"])


def get_dependencies(df_datadicc: pd.DataFrame) -> pd.DataFrame:
    mandatory = ["subjid"]

    df_dependencies = df_datadicc[["Variable", "Skip Logic"]]
    field_dependencies = []
    for skip_logic_str in df_dependencies["Skip Logic"]:
        cont = 0
        variable_dependencies = []
        if not isinstance(skip_logic_str, float):
            for i in skip_logic_str.split("["):
                variable = i[: i.find("]")]
                if "(" in variable:
                    variable = variable[: variable.find("(")]
                if cont != 0:
                    variable_dependencies.append(variable)
                cont += 1
        field_dependencies.append(variable_dependencies)

    df_dependencies["Dependencies"] = field_dependencies
    for variable in df_dependencies["Variable"]:
        if "other" in variable:
            if (
                len(
                    df_dependencies["Dependencies"].loc[
                        df_dependencies["Variable"] == variable.replace("other", "")
                    ]
                )
                >= 1
            ):
                df_dependencies["Dependencies"].loc[
                    df_dependencies["Variable"] == variable.replace("other", "")
                ].iloc[0].append(variable)

        if "units" in variable:
            if (
                len(
                    df_dependencies["Dependencies"].loc[
                        df_dependencies["Variable"] == variable.replace("units", "")
                    ]
                )
                >= 1
            ):
                df_dependencies["Dependencies"].loc[
                    df_dependencies["Variable"] == variable.replace("units", "")
                ].iloc[0].append(variable)

        for mandatory_variable in mandatory:
            df_dependencies["Dependencies"].loc[
                df_dependencies["Variable"] == variable
            ].iloc[0].append(mandatory_variable)

    return df_dependencies


def add_transformed_rows(
    df_selected: pd.DataFrame,
    df_selected_units: pd.DataFrame,
    variable_order: list,
) -> pd.DataFrame:
    df_output = df_selected.copy().reset_index(drop=True)

    df_selected_units["Sec_vari"] = (
        df_selected_units["Sec"] + "_" + df_selected_units["vari"]
    )
    df_selected_units = df_selected_units[df_output.columns]

    for _, row in df_selected_units.iterrows():
        variable = row["Variable"]

        if variable in df_output["Variable"].values:
            # Get the index for the matching variable in the result DataFrame
            match_index = df_output.index[df_output["Variable"] == variable].tolist()[0]
            # Update each column separately
            for col in df_output.columns:
                df_output.at[match_index, col] = row[col]

        else:
            # Identify the base variable name by splitting at the last underscore
            base_var = "_".join(variable.split("_")[:-1])

            if base_var in df_output["Variable"].values:
                # Find the index of the base variable row
                base_index = df_output.index[
                    df_output["Variable"].str.startswith(base_var)
                ].max()
                df_row = pd.DataFrame([row]).reset_index(drop=True)
                # Insert the new row immediately after the base variable row
                df_output = pd.concat(
                    [
                        df_output.iloc[: base_index + 1],
                        df_row,
                        df_output.iloc[base_index + 1 :],
                    ]
                ).reset_index(drop=True)

            else:
                # Variable to be added is not based on the base variable, use the order list
                variable_to_add = variable
                order_index = (
                    variable_order.index(variable_to_add)
                    if variable_to_add in variable_order
                    else None
                )

                if order_index is not None:
                    # Find the next existing variable in 'result' from 'order'
                    insert_before_index = None
                    for next_variable in variable_order[order_index + 1 :]:
                        if next_variable in df_output["Variable"].values:
                            insert_before_index = df_output.index[
                                df_output["Variable"] == next_variable
                            ][0]
                            break

                    # Create a DataFrame from the current row
                    df_row = pd.DataFrame([row]).reset_index(drop=True)

                    # Insert the row at the determined position or append if no next variable is found
                    if insert_before_index is not None:
                        df_output = pd.concat(
                            [
                                df_output.iloc[:insert_before_index],
                                df_row,
                                df_output.iloc[insert_before_index:],
                            ]
                        ).reset_index(drop=True)

                    else:
                        df_output = pd.concat([df_output, df_row]).reset_index(
                            drop=True
                        )

                else:
                    # If the variable is not in the order list, append it at the end (or handle as needed)
                    df_row = pd.DataFrame([row]).reset_index(drop=True)
                    df_output = pd.concat([df_output, df_row]).reset_index(drop=True)

    return df_output


def get_dynamic_units_conversion_bool(version: str) -> bool:
    if parse(version.replace("v", "")) < parse(
        ARC_UNIT_CHANGE_VERSION.replace("v", "")
    ):
        # Old versions: "Question" contains "(select units)"
        dynamic_units_conversion = True
    else:
        # New versions: "Validation" == "units"
        dynamic_units_conversion = False
    return dynamic_units_conversion
