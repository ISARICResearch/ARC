import pytest
import pathlib
import pandas as pd

BASE_DIR = pathlib.Path(".")
ARC_PATH = BASE_DIR / "ARC.csv"
TEST_PATH = pathlib.Path(__file__)
LIST_FILES = [x for x in pathlib.Path("Lists").rglob("*") if x.is_file()]

REQUIRED_COLUMNS = [
    "Selected",
    "Value"
]


@pytest.mark.critical
def test_arc_list_file_exist():
    """Check if Question has empty spaces at the end"""
    arc = pd.read_csv(ARC_PATH, dtype="object", usecols=["Variable", "List"])
    relative_list_files = [x.relative_to(pathlib.Path("Lists")) for x in LIST_FILES]
    list_enum = [str(x.parent) + "_" + x.stem for x in relative_list_files]

    condition = arc['List'].isin(list_enum) | arc['List'].isna()
    if not condition.all():
        invalid = arc.loc[~condition, "Variable"].tolist()
        pytest.fail(
            f"ARC contains List with no matching CSV file in Lists/. "
            f"Variables: {invalid}"
        )


@pytest.mark.high
@pytest.mark.parametrize("file", LIST_FILES)
def test_list_csv_loads(file):
    """Check loads correctly with no encoding"""
    try:
        pd.read_csv(file, dtype="object")
    except UnicodeDecodeError as e:
        pytest.fail(
            f"{str(file)} failed to load without specifying encoding "
            f"(file is not UTF-8 clean): {e}"
        )
    except Exception as e:
        pytest.fail(
            f"{str(file)} failed to load for an unexpected reason: {e}"
        )


@pytest.mark.high
@pytest.mark.parametrize("file", LIST_FILES)
def test_list_required_columns_exist(file):
    """Check required columns exist"""
    header = pd.read_csv(file, nrows=0, dtype="object").columns
    missing = [c for c in REQUIRED_COLUMNS if c not in header]
    if missing:
        pytest.fail(f"{str(file)} missing required columns: {missing}")


@pytest.mark.medium
@pytest.mark.parametrize("file", LIST_FILES)
def test_list_valid_selected_values(file):
    """Selected column must be NaN or 1 (not 1.0)"""
    df = pd.read_csv(file, dtype="object", usecols=["Selected"])
    condition = df["Selected"].isin([1]) | df["Selected"].isna()
    if not condition.all():
        invalid_index = df.loc[~condition].index.tolist()
        pytest.fail(f"{str(file)} has invalid Selected value for index: {invalid_index}")


@pytest.mark.medium
@pytest.mark.parametrize("file", LIST_FILES)
def test_list_valid_preset_values(file):
    """Preset columns column must be NaN or 1 (not 1.0)"""
    df = pd.read_csv(file, dtype="object")
    preset_columns = [c for c in df.columns if c.startswith("preset_")]
    condition = df[preset_columns].apply(lambda x: x.isin([1]) | x.isna(), axis=0).all(axis=1)
    if not condition.all():
        invalid_index = df.loc[~condition].index.tolist()
        pytest.fail(f"{str(file)} has invalid preset values for index: {invalid_index}")


@pytest.mark.high
@pytest.mark.parametrize("file", LIST_FILES)
def test_list_matches_arc_presets(file):
    """Check if the Lists file has the same presets as ARC"""
    arc = pd.read_csv(ARC_PATH, nrows=0, dtype="object")
    arc_header = list(arc.columns)
    arc_presets = [c for c in arc_header if c.startswith("preset_")]

    header = pd.read_csv(file, nrows=0).columns
    presets = [c for c in header if c.startswith("preset_")]

    presets_not_in_arc = [x for x in presets if x not in arc_presets]
    if presets_not_in_arc:
        pytest.fail(
            f"{str(file)} contains preset columns not in ARC: {presets_not_in_arc}"
        )
