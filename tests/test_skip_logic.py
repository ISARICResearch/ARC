"""
This should handle skip logic in ARC at the time of writing (ARC v1.2.1).
It cannot do the following:
- RHS 'value' is a second field e.g. [demog_weight] = [infa_brtwei].
- REDCap smart variables e.g. datediff
"""

import pathlib
import pytest
import pandas as pd
import re
from typing import List, Dict, Union, Optional
from pathlib import Path

Numeric = Union[float, int]

BASE_DIR = pathlib.Path(".")
ARC_PATH = BASE_DIR / "ARC.csv"
LIST_FILES = [x for x in pathlib.Path("Lists").rglob("*") if x.is_file()]

PRESET_COLUMNS = [
    x for x in pd.read_csv(ARC_PATH, nrows=0).columns if x.startswith("preset_")
]
CHOICE_TYPES = ["radio", "user_list", "checkbox", "multi_list", "dropdown", "list"]

EVENT_NAMES = ["daily_arm_1", "initial_assessment_arm_1"]

EXCEPTIONS_SUFFIX_LIST = ["_otherl2"]  # Add to this as needed
EXCEPTIONS_SUFFIX = r"|".join(EXCEPTIONS_SUFFIX_LIST)

REDCAP_PATTERN = re.compile(
    r"""
    (?:\[([a-z0-9_]+)\]\s*)?                            # optional event: [event_name] (Group 1)
    \[                                                  # start of field
      ([a-z0-9_]+)                                      # field name (Group 2)
      (?:\((\d+)\))?                                    # possible checkbox value (Group 3)
    \]                                                  # end of field
    \s*                                                 # optional whitespace
    (<=|>=|<>|=|<|>|contains|CONTAINS|in|IN|matches)    # operator (Group 4)
    \s*                                                 # optional whitespace
    (?:                                                 # value alternatives (one will match)
      '([^']*)'                                         # single-quoted string -> 'sq' (Group 5)
     |([+-]?[0-9]+(?:\.[0-9]+)?)                        # number (int or decimal) -> 'number' (Group 6)
     |(\S+)                                             # fallback non-space token -> 'token' (Group 7)
    )
""",
    re.VERBOSE,
)


def extract(skip_logic: str) -> List[Dict[str, Union[str, Numeric]]]:
    results = []
    for m in REDCAP_PATTERN.finditer(skip_logic):
        event = m.group(1) or None
        field = m.group(2)
        checkbox = m.group(3) or None
        operator = m.group(4)

        # pick the first non-None value group
        value = next(
            g
            for g in (
                m.group(5),
                m.group(6),
                m.group(7),
            )
            if g is not None
        )

        results.append(
            {
                "redcap_event": event,
                "skip_logic_field": field,
                "checkbox_value": checkbox,
                "operator": operator,
                "value": value,
            }
        )
    return results


def extract_from_arc(arc: pd.DataFrame) -> pd.DataFrame:
    """
    Extract skip logic from ARC into a dataframe of components.
    """
    nested_results = []
    for idx in arc["Skip Logic"].dropna().index:
        extracted = extract(arc.loc[idx, "Skip Logic"])
        extracted_with_field_name = [
            {**x, "field_name": arc.loc[idx, "Variable"]} for x in extracted
        ]
        nested_results.append(extracted_with_field_name)
    results = [x for result in nested_results for x in result]
    return pd.DataFrame.from_dict(results)


def get_answer_options_from_list(
    file: Union[Path, str], label_column: Optional[str] = None
):
    df = pd.read_csv(file, dtype="object")
    if not label_column:
        label_column = df.columns[0]
    return " | ".join(df["Value"] + ", " + df[label_column])


def get_codes_from_answer_options(s: str) -> str:
    if not s or not isinstance(s, str):
        return []

    options = s.split("|")
    codes = []

    for option in options:
        option = option.strip()

        # Must contain at least one comma
        if option.count(",") < 1:
            return

        code, label = option.split(",", 1)
        code = code.strip()

        # Code must be non-empty
        if not code:
            return []

        codes.append(code)

    return codes


@pytest.mark.critical
def test_valid_regex():
    """
    Test if the skip logic entries match the above regex (won't fix all typos)."""
    arc = pd.read_csv(ARC_PATH, dtype="object", usecols=["Variable", "Skip Logic"])
    arc_skip_logic = extract_from_arc(arc)

    # If invalid skip logic string, extract returns empty list,
    # so field doesn't exist in arc_skip_logic
    condition = arc["Skip Logic"].isna() | arc["Variable"].isin(
        arc_skip_logic["field_name"]
    )
    if not condition.all():
        invalid = invalid = arc_skip_logic.loc[
            ~condition, ["Variable", "Skip Logic"]
        ].to_dict(orient="records")
        pytest.fail(
            "Skip logic isn't valid regex (change the regex pattern if needed)"
            f": {invalid}"
        )


@pytest.mark.high
def test_events():
    """Check that fields mentioned in the skip logic exist"""
    arc = pd.read_csv(ARC_PATH, dtype="object", usecols=["Variable", "Skip Logic"])
    arc_skip_logic = extract_from_arc(arc)

    condition = (
        arc_skip_logic["redcap_event"].isin(EVENT_NAMES)
        | arc_skip_logic["redcap_event"].isna()
    )
    if not condition.all():
        invalid = invalid = arc_skip_logic.loc[
            ~condition, ["field_name", "redcap_event"]
        ].to_dict(orient="records")
        pytest.fail(f"Skip logic includes variable not in ARC: {invalid}")


@pytest.mark.high
def test_fields_exist():
    """Check that fields mentioned in the skip logic exist"""
    arc = pd.read_csv(ARC_PATH, dtype="object", usecols=["Variable", "Skip Logic"])
    arc_skip_logic = extract_from_arc(arc)

    condition = arc_skip_logic["skip_logic_field"].isin(
        arc["Variable"]
    ) | arc_skip_logic["skip_logic_field"].str.endswith(EXCEPTIONS_SUFFIX)
    if not condition.all():
        invalid = invalid = arc_skip_logic.loc[
            ~condition, ["field_name", "skip_logic_field"]
        ].to_dict(orient="records")
        pytest.fail(f"Skip logic includes variable not in ARC: {invalid}")


@pytest.mark.high
def test_checkboxes():
    """Check that fields mentioned in the skip logic exist"""
    arc = pd.read_csv(
        ARC_PATH, dtype="object", usecols=["Variable", "Type", "Skip Logic"]
    )
    arc_skip_logic = extract_from_arc(arc)

    idx = arc_skip_logic["skip_logic_field"].str.endswith(EXCEPTIONS_SUFFIX)
    arc_skip_logic.loc[idx, "skip_logic_field"] = arc_skip_logic.loc[
        idx, "skip_logic_field"
    ].apply(lambda x: x.split(EXCEPTIONS_SUFFIX)[0])

    checkbox_idx = arc["Type"].isin(["checkbox", "multi_list"])
    condition = (
        arc_skip_logic["checkbox_value"].isna()
        & arc_skip_logic["skip_logic_field"].isin(arc.loc[~checkbox_idx, "Variable"])
    ) | (
        arc_skip_logic["checkbox_value"].notna()
        & arc_skip_logic["skip_logic_field"].isin(arc.loc[checkbox_idx, "Variable"])
    )
    if not condition.all():
        invalid = arc_skip_logic.loc[
            ~condition, ["field_name", "skip_logic_field"]
        ].to_dict(orient="records")
        pytest.fail(f"Skip logic incorrectly uses checkbox variable: {invalid}")


@pytest.mark.medium
@pytest.mark.parametrize("preset_column", PRESET_COLUMNS)
def test_fields_exist_presets(preset_column):
    """Check that fields mentioned in the skip logic exist"""
    arc = pd.read_csv(
        ARC_PATH, dtype="object", usecols=["Variable", "Skip Logic", preset_column]
    )
    arc = arc.loc[arc[preset_column].isin(["1"])]
    arc_skip_logic = extract_from_arc(arc)

    condition = arc_skip_logic["skip_logic_field"].isin(
        arc["Variable"]
    ) | arc_skip_logic["skip_logic_field"].str.endswith(EXCEPTIONS_SUFFIX)
    if not condition.all():
        invalid = invalid = arc_skip_logic.loc[
            ~condition, ["field_name", "skip_logic_field"]
        ].to_dict(orient="records")
        pytest.fail(f"Skip logic includes variable not in ARC: {invalid}")


@pytest.mark.high
def test_values_exist():
    """Check that values in the skip logic exist as answer options"""
    arc = pd.read_csv(
        ARC_PATH,
        dtype="object",
        usecols=["Variable", "Type", "Skip Logic", "Answer Options", "List"],
    )

    relative_list_files = [x.relative_to(pathlib.Path("Lists")) for x in LIST_FILES]
    list_enum = [str(x.parent) + "_" + x.stem for x in relative_list_files]
    list_answer_options = {
        x: get_answer_options_from_list(pathlib.Path("Lists") / y)
        for x, y in zip(list_enum, relative_list_files)
    }
    arc.loc[arc["List"].notna(), "Answer Options"] = (
        arc.loc[arc["List"].notna(), "List"].map(list_answer_options)
    ) + " | 88, Other"

    arc_skip_logic = extract_from_arc(arc)

    # If a checkbox, we want to use checkbox_value instead
    arc_skip_logic.loc[arc_skip_logic["checkbox_value"].notna(), "value"] = (
        arc_skip_logic.loc[arc_skip_logic["checkbox_value"].notna(), "checkbox_value"]
    )

    idx = arc_skip_logic["skip_logic_field"].str.endswith(EXCEPTIONS_SUFFIX)
    arc_skip_logic.loc[idx, "skip_logic_field"] = arc_skip_logic.loc[
        idx, "skip_logic_field"
    ].apply(lambda x: x.split(EXCEPTIONS_SUFFIX)[0])

    # Add the answer option string
    arc_skip_logic = pd.merge(
        arc_skip_logic,
        arc[["Variable", "Answer Options", "Type", "List"]].rename(
            columns={"Variable": "skip_logic_field"},
        ),
        on="skip_logic_field",
        how="left",
    )

    condition = ~arc_skip_logic["Type"].isin(CHOICE_TYPES) | arc_skip_logic.apply(
        lambda x: x["value"] in get_codes_from_answer_options(x["Answer Options"]),
        axis=1,
    )
    if not condition.all():
        invalid = invalid = arc_skip_logic.loc[
            ~condition,
            ["field_name", "skip_logic_field", "List", "Answer Options", "value"],
        ].to_dict(orient="records")
        pytest.fail(f"Skip logic values not in ARC or in relevant List: {invalid}")
