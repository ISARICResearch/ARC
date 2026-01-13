import pytest
import pathlib
import re
import pandas as pd

BASE_DIR = pathlib.Path(".")
ARC_PATH = BASE_DIR / "ARC.csv"
TEST_PATH = pathlib.Path(__file__)

REQUIRED_COLUMNS = [
    "Form",
    "Section",
    "Variable",
    "Type",
    "Question",
    "Answer Options",
    "Validation",
    "Minimum",
    "Maximum",
    "List",
    "Skip Logic",
    "Body System",
    "Definition",
    "Completion Guideline",
    "Standardized Term Codelist",
    "Standardized Term Code",
    "Metathesaurus",
    "Identifier",
    "Research Category",
]

# Update if new forms are added
FORM_ENUM = [
    "presentation",
    "daily",
    "medication",
    "pathogen_testing",
    "photographs",
    "outcome",
    "pregnancy",
    "neonate",
    "follow_up",
    "withdrawal",
]

# Update if new types are added
TYPE_ENUM = [
    "radio",
    "checkbox",
    "list",
    "user_list",
    "multi_list",
    "number",
    "text",
    "descriptive",
    "date_dmy",
    "datetime_dmy",
    "time",
    "calc",
    "notes",
    "file",
]

# Update if new types are added
VALIDATION_ENUM = ["number", "date_dmy", "datetime_dmy", "time"]


@pytest.mark.critical
def test_arc_required_columns_exist():
    """Check required ARC columns exist"""
    arc = pd.read_csv(ARC_PATH, nrows=0, dtype="object")
    header = list(arc.columns)
    missing = [c for c in REQUIRED_COLUMNS if c not in header]
    if missing:
        pytest.fail(f"Missing required columns: {missing}")


@pytest.mark.high
def test_arc_valid_form():
    """Only specific forms are allowed."""
    arc = pd.read_csv(ARC_PATH, dtype="object", usecols=["Variable", "Form"])
    condition = arc["Form"].isin(FORM_ENUM)
    if not condition.all():
        invalid = arc.loc[~condition, "Variable"].tolist()
        pytest.fail(
            f"ARC contains Form enum not listed in {TEST_PATH}, amend the list if needed. "
            f"Variables: {invalid}"
        )


@pytest.mark.critical
def test_arc_valid_variable_regex():
    """Check all variable names match the naming convention regex."""
    arc = pd.read_csv(ARC_PATH, dtype="object", usecols=["Variable"])
    variable_regex = re.compile(r"^[a-z][a-z0-9_]*$")
    non_match = arc["Variable"].apply(lambda x: not variable_regex.match(x))
    if non_match.any():
        invalid = arc.loc[non_match].tolist()
        pytest.fail(f"Variables do not following naming convention regex: {invalid}")


@pytest.mark.high
def test_arc_valid_type():
    """Only specific types are allowed."""
    arc = pd.read_csv(ARC_PATH, dtype="object", usecols=["Variable", "Type"])
    condition = arc["Type"].isin(TYPE_ENUM)
    if not condition.all():
        invalid = arc.loc[~condition, "Variable"].tolist()
        pytest.fail(
            f"ARC contains Type enum not listed in {TEST_PATH}, amend the list if needed. "
            f"Variables: {invalid}"
        )


@pytest.mark.medium
def test_arc_question_strip():
    """Check if Question has empty spaces at the end"""
    arc = pd.read_csv(ARC_PATH, dtype="object", usecols=["Variable", "Question"])
    condition = arc["Question"].eq(arc["Question"].str.strip())
    if not condition.all():
        invalid = arc.loc[~condition, "Variable"].tolist()
        pytest.fail(
            f"ARC contains Questions with unnecessary spaces at the beginning/end. "
            f"Variables: {invalid}"
        )


@pytest.mark.critical
def test_arc_answer_options_exist():
    """Answer options for exist where relevant (radio, checkbox, list, calc)"""
    arc = pd.read_csv(
        ARC_PATH, dtype="object", usecols=["Variable", "Type", "Answer Options"]
    )
    condition = (
        arc["Type"].isin(["radio", "checkbox", "list", "calc"])
        | arc["Answer Options"].isna()
    )
    if not condition.all():
        invalid = arc.loc[~condition, "Variable"].tolist()
        pytest.fail(
            f"Answer Options should for all (radio, checkbox, list, calc) variables "
            f"and none others. Variables: {invalid}"
        )


def is_valid_redcap_field_options(s: str) -> bool:
    if not s or not isinstance(s, str):
        return False

    options = s.split("|")

    for option in options:
        option = option.strip()

        # Must contain at least one comma
        if option.count(",") < 1:
            return False

        code, label = option.split(",", 1)
        code = code.strip()
        label = label.strip()

        # Code must be non-empty
        if not code:
            return False

        # Label must be non-empty
        if not label:
            return False

    return True


@pytest.mark.critical
def test_arc_answer_options_valid_redcap():
    """Answer options for radio/checkbox variables must be valid REDCap format"""
    arc = pd.read_csv(
        ARC_PATH, dtype="object", usecols=["Variable", "Type", "Answer Options"]
    )
    condition = ~arc["Type"].isin(["radio", "checkbox", "list"]) | arc[
        "Answer Options"
    ].apply(lambda x: is_valid_redcap_field_options(x))
    if not condition.all():
        invalid = arc.loc[~condition, "Variable"].tolist()
        pytest.fail(
            f"ARC contains Answer Options that are not valid REDCap-format. "
            f"Variables: {invalid}"
        )


@pytest.mark.high
def test_arc_valid_validation():
    """Validation must be consistent with Type."""
    arc = pd.read_csv(
        ARC_PATH, dtype="object", usecols=["Variable", "Type", "Validation"]
    )
    condition = (
        arc["Validation"].isin(VALIDATION_ENUM + ["units"]) | arc["Validation"].isna()
    )
    if not condition.all():
        invalid = arc.loc[~condition, "Variable"].tolist()
        pytest.fail(
            f"ARC contains Validation enum not listed in {TEST_PATH}, amend the list if needed. "
            f"Variables: {invalid}"
        )
    condition = (
        (arc["Validation"].isin(VALIDATION_ENUM) & arc["Type"].eq(arc["Validation"]))
        | arc["Validation"].isin(["units"])
        | arc["Validation"].isna()
    )
    if not condition.all():
        invalid = arc.loc[~condition, "Variable"].tolist()
        pytest.fail(
            f"Validation should either match Type when it exists, except for units. "
            f"Variables: {invalid}"
        )


@pytest.mark.high
def test_arc_minimum_maximum_correct_type():
    """Minimum and maximum must only exist for specific Validation (number, datetime_dmy, date_dmy, time)."""
    arc = pd.read_csv(
        ARC_PATH,
        dtype="object",
        usecols=["Variable", "Validation", "Minimum", "Maximum"],
    )
    condition = arc["Validation"].isin(VALIDATION_ENUM) | (
        arc["Minimum"].isna() & arc["Maximum"].isna()
    )
    if not condition.all():
        invalid = arc.loc[~condition, "Variable"].tolist()
        pytest.fail(
            f"ARC should not contain Maximum or Minimum for non-numeric/date variables."
            f"Variables: {invalid}"
        )


@pytest.mark.low
def test_arc_minimum_maximum_exists():
    """Minimum and maximum should exist when for specific Validation (number, datetime_dmy, date_dmy, time)."""
    arc = pd.read_csv(
        ARC_PATH,
        dtype="object",
        usecols=["Variable", "Validation", "Minimum", "Maximum"],
    )
    condition = arc["Validation"].isin(VALIDATION_ENUM) | (
        arc["Minimum"].isna() & arc["Maximum"].isna()
    )
    if not condition.all():
        invalid = arc.loc[~condition, "Variable"].tolist()
        pytest.fail(
            f"ARC has no Minimum or Maximum for numeric/date Variables: {invalid}"
        )


@pytest.mark.medium
def test_arc_definition_exists():
    """
    ARC definition should exist except for 'descriptive' Type
    or "units" Validation variables
    """
    arc = pd.read_csv(
        ARC_PATH,
        dtype="object",
        usecols=["Variable", "Type", "Validation", "Definition"],
    )
    condition = (
        arc["Type"].isin(["descriptive"])
        | arc["Validation"].isin(["units"])
        | ~arc["Definition"].isna()
    )
    if not condition.all():
        invalid = arc.loc[~condition, "Variable"].tolist()
        pytest.fail(f"ARC has no Definition for Variables: {invalid}")


@pytest.mark.medium
def test_arc_valid_preset_values():
    """Preset columns column must be NaN or 1 (not 1.0)"""
    arc = pd.read_csv(ARC_PATH, dtype="object")
    preset_columns = [c for c in arc.columns if c.startswith("preset_")]
    condition = (
        arc[preset_columns].apply(lambda x: x.isin([1]) | x.isna(), axis=0).all(axis=1)
    )
    if not condition.all():
        invalid = arc.loc[~condition, "Variable"].tolist()
        pytest.fail(f"ARC has invalid preset values for Variables: {invalid}")
