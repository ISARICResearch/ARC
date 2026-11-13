from __future__ import annotations


__all__ = [
    "add_required_dictionary_columns",
    "add_transformed_rows",
    "get_arc_schema",
    "get_arc_versions",
    "get_variable_dependencies",
    "get_variable_order",
    "use_dynamic_unit_conversion",
]


# -- IMPORTS --

# -- Standard libraries --
import warnings
from time import perf_counter

# -- External libraries --
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
    """:py:class:`tuple` : Returns a triple consisting of the raw ARC schema for the given release version, the presets list and the associated commit SHA.

    .. warning::

       This method is deprecated. Use the
       :py:func:`~arc.arc_core.get_arc_schema` function instead.
    """
    warnings.warn(
        "This function is deprecated. Please use the "
        "`get_arc_schema()` function instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    return get_arc_schema(version)


def get_arc_schema(version: str) -> tuple[pd.DataFrame, list, str]:
    """:py:class:`tuple` : Returns a triple consisting of the raw ARC schema for the given release version, the presets list and the associated commit SHA.

    Parameters
    ----------
    version : str
        An ARC release version string.

    Returns
    -------
    pandas.DataFrame
        The raw ARC schema for the given commit SHA.

    Examples
    --------
    >>> from arc.arc_core import get_arc
    >>> arc_schema, presets_list, commit_sha = get_arc_schema('v1.6.1') # doctest: +SKIP
    >>> arc_schema  # doctest: +SKIP
                  Form             Section  ... Branch                                   Question_english
    0     presentation                 NaN  ...                   Participant Identification Number (PIN)
    1     presentation  INCLUSION CRITERIA  ...         Suspected or confirmed infection, condition, o...
    2     presentation  INCLUSION CRITERIA  ...         Is the suspected or confirmed infection, condi...
    3     presentation  INCLUSION CRITERIA  ...                                Case classification status
    4     presentation  INCLUSION CRITERIA  ...                                        Reason for testing
    ...            ...                 ...  ...    ...                                                ...
    1752    withdrawal          WITHDRAWAL  ...                                        Date of withdrawal
    1753    withdrawal          WITHDRAWAL  ...                                     Reason for withdrawal
    1754    withdrawal          WITHDRAWAL  ...         Did the participant withdraw from active parti...
    1755    withdrawal          WITHDRAWAL  ...         Did the participant withdraw consent to use da...
    1756    withdrawal          WITHDRAWAL  ...         Did the participant withdraw consent to use sa...
    >>> presets_list  # doctest: +SKIP
    [['ARChetype Disease CRF', 'Covid'],
     ['ARChetype Disease CRF', 'H5Nx'],
     ['ARChetype Disease CRF', 'Dengue'],
     ['ARChetype Disease CRF', 'Chikungunya'],
     ['ARChetype Disease CRF', 'Mpox'],
     ['ARChetype Disease CRF', 'Mpox Pregnancy and Paediatric'],
     ['ARChetype Syndromic CRF', 'ARI'],
     ['ARChetype Syndromic CRF', 'VHF'],
     ['ARChetype Syndromic CRF', 'Encephalitis'],
     ['ARChetype Syndromic CRF', 'Arbovirus'],
     ['Score', 'CharlsonCI'],
     ['Score', 'mSOFA'],
     ['Score', 'mSOFA Dengue'],
     ['Recommended Outcomes', 'Dengue'],
     ['Populations', 'Paediatric'],
     ['Populations', 'Pregnancy']]
    >>> commit_sha  # doctest: +SKIP
    '8b6ccdd5cad0775b8b695a77f45a5cad41dabeed'
    """
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


def get_arc_versions() -> tuple[list[str], str]:
    """:py:class:`tuple` : Returns a pair consisting of a list of all ARC release versions and a string of the most recent release version.

    .. note::

    ARC release versions are almost always linked to changes in the ARC
    schema. They are **NOT** the same as the ARC Python package
    versions.

    Returns
    -------
    tuple
        A pair consisting of a list of all ARC release versions, in descending
        chronological order, and a string of the most recent release version.

    Examples
    --------
    >>> from arc.arc_core import get_arc_versions
    >>> versions, latest = get_arc_versions()  # doctest: +SKIP
    >>> versions  # doctest: +SKIP
    ['v1.6.1',
     'v1.6.0',
     'v1.5.0',
     'v1.4.1',
     'v1.4.0',
     'v1.3.0',
     'v1.2.2',
     'v1.2.1',
     'v1.2.0',
     'v1.1.5',
     'v1.1.4',
     'v1.1.3',
     'v1.1.2',
     'v1.1.1',
     'v1.1.0',
     'v1.0.4',
     'v1.0.3',
     'v1.0.2',
     'v1.0.1',
     'v1.0.0']
     >>> latest  # doctest: +SKIP
     'v1.6.1'
    """
    version_list = ArcApiClient().get_arc_versions()
    logger.info(f"version_list: {version_list}")

    return version_list, max(version_list)


def add_required_datadicc_columns(df_datadicc: pd.DataFrame) -> pd.DataFrame:
    """:py:class:`pandas.DataFrame` : Adds additional required columns to the incoming ARC data dictionary.

    .. warning::

       This method is deprecated. Use the
       :py:func:`~arc.arc_core.add_required_dictionary_columns` function instead.
    """
    warnings.warn(
        "This function is deprecated. Please use the "
        "`add_required_dictionary_columns()` function instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    return add_required_dictionary_columns(df_datadicc)


def add_required_dictionary_columns(dictionary: pd.DataFrame) -> pd.DataFrame:
    """:py:class:`pandas.DataFrame` : Adds additional required columns to the incoming ARC data dictionary.

    .. warning::

       This function modifies the incoming dictionary. If you want to have an
       unmodified original, call this function with a (deep) copy instead.

    Parameters
    ----------
    dictionary : pandas.DataFrame
        The incoming ARC data dictionary.

    Returns
    -------
    pandas.DataFrame
        The ARC data dictionary with the additional required columns added.
    """
    dictionary[["Sec", "vari", "mod"]] = dictionary["Variable"].str.split(
        "_", n=2, expand=True
    )
    dictionary[["Sec_name", "Expla"]] = dictionary["Section"].str.split(
        r"[(|:]", n=1, expand=True
    )

    return dictionary


def get_variable_order(dictionary: pd.DataFrame) -> list[str]:
    """:py:class:`list` : Returns an (ordered) list of variables in the ARC data dictionary that has the additional required columns.

    Parameters
    ----------
    pandas.DataFrame
        The incoming ARC data dictionary with the additional required
        columns.

    Returns
    -------
    list
        An (ordered) list of variables in the ARC data dictionary.
    """
    dictionary["Sec_vari"] = dictionary["Sec"] + "_" + dictionary["vari"]
    order = dictionary[["Sec_vari"]]
    order = order.drop_duplicates().reset_index()

    return list(order["Sec_vari"])


def get_dependencies(df_datadicc: pd.DataFrame) -> pd.DataFrame:
    """
    .. warning::

       This method is deprecated. Use the
       :py:func:`~arc.arc_core.get_variable_dependencies` function instead.
    """
    warnings.warn(
        "This function is deprecated. Please use the "
        "`get_variable_dependencies()` function instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    return get_variable_dependencies(df_datadicc)


def get_variable_dependencies(dictionary: pd.DataFrame) -> pd.DataFrame:
    """:py:class:`pandas.DataFrame` : Returns a dataframe of ARC variable dependencies.

    .. warning::

       This function modifies the incoming dictionary. If you want to have an
       unmodified original, call this function with a (deep) copy instead.

    Parameters
    ----------
    pandas.DataFrame
        The incoming ARC data dictionary with the additional required
        columns.

    Returns
    -------
    pandas.DataFrame
        ARC variable dependencies.
    """
    mandatory = ["subjid"]

    df_dependencies = dictionary[["Variable", "Skip Logic"]]
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
    variable_order: list[str],
) -> pd.DataFrame:
    """:py:class:`pandas.DataFrame` : Adds variable transformation rows to an incoming dataframe of selected ARC variables.

    Parameters
    ----------
    df_selected : pandas.DataFrame
        A dataframe of selected ARC variables.

    df_selected_units : pandas.DataFrame
        A dataframe of units for the selected ARC variables.

    variable_order : list
        Variable ordering.

    Returns
    -------
    pandas.DataFrame
        The selected ARC variables with the variable transformation rows
        added.
    """
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
    """
    .. warning::

       This method is deprecated. Use the
       :py:func:`~arc.arc_core.use_dynamic_units_conversion` function instead.
    """
    warnings.warn(
        "This function is deprecated. Please use the "
        "`use_dynamic_units_conversion()` function instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    return use_dynamic_unit_conversion(version)


def use_dynamic_unit_conversion(version: str) -> bool:
    """:py:class:`bool` : Whether to use dynamic unit conversion.

    Parameters
    ----------
    version : str
        ARC release version.

    Returns
    -------
    bool
        Whether to use dynamic unit version.
    """
    if parse(version.replace("v", "")) < parse(
        ARC_UNIT_CHANGE_VERSION.replace("v", "")
    ):
        # Old versions: "Question" contains "(select units)"
        return True
    # New versions: "Validation" == "units"
    return False


if __name__ == "__main__":  # pragma: no cover
    # Doctest the module from the project root using
    #
    #     PYTHONPATH="src" python3 -m doctest -v arc/arc_core.py  # noqa : E501
    #
    import doctest

    doctest.testmod()
