import pytest
import pathlib
import pandas as pd

BASE_DIR = pathlib.Path(".")
ARC_PATH = BASE_DIR / "ARC.csv"
TEST_PATH = pathlib.Path(__file__)
LIST_FILES = [x for x in pathlib.Path("Lists").rglob("*") if x.is_file()]

REQUIRED_COLUMNS = ["Selected", "Value"]
LIST_FILES_WITH_ARCHETYPE_PRESETS = [
    pathlib.Path("Lists/outcome/Diseases.csv"),
    pathlib.Path("Lists/inclusion/Diseases.csv"),
    pathlib.Path("Lists/pathogens/All.csv"),
]


@pytest.mark.critical
def test_arc_list_missing():
    """Check if an ARC list entry refers to an existing Lists file"""
    arc = pd.read_csv(ARC_PATH, dtype="object", usecols=["Variable", "List"])
    relative_list_files = [x.relative_to(pathlib.Path("Lists")) for x in LIST_FILES]
    list_enum = [str(x.parent) + "_" + x.stem for x in relative_list_files]

    condition = arc["List"].isin(list_enum) | arc["List"].isna()
    if not condition.all():
        invalid = arc.loc[~condition, "Variable"].tolist()
        pytest.fail(
            f"ARC contains List with no matching CSV file in Lists/. "
            f"Variables: {invalid}"
        )


@pytest.mark.high
def test_list_file_used_in_arc():
    """Check if a Lists file is used in ARC. If not, should be removed"""
    arc = pd.read_csv(ARC_PATH, dtype="object", usecols=["Variable", "List"])
    relative_list_files = [x.relative_to(pathlib.Path("Lists")) for x in LIST_FILES]
    list_enum = [str(x.parent) + "_" + x.stem for x in relative_list_files]

    unused_list = [x for x in list_enum if x not in arc["List"].unique().tolist()]
    if unused_list:
        pytest.fail(f"ARC contains unused Lists CSV file. Variables: {unused_list}")


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
        pytest.fail(f"{str(file)} failed to load for an unexpected reason: {e}")


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
def test_arc_strip(file):
    """Check if each required column has empty spaces at the beginning/end"""
    df = pd.read_csv(file, dtype="object")
    condition = df.eq(df.apply(lambda x: x.str.strip())) | df.isna()
    if not condition.all().all():
        invalid_index = df.loc[~condition.all(axis=1)].index.tolist()
        pytest.fail(
            f"{str(file)} has unnecessary spaces at the beginning/end "
            f"for at least one column, index: {invalid_index}"
        )


@pytest.mark.medium
@pytest.mark.parametrize("file", LIST_FILES)
def test_list_valid_selected_values(file):
    """Selected column must be NaN or 1 (not 1.0)"""
    df = pd.read_csv(file, dtype="object", usecols=["Selected"])
    condition = df["Selected"].isin(["1"]) | df["Selected"].isna()
    if not condition.all().all():
        invalid_index = df.loc[~condition].index.tolist()
        pytest.fail(
            f"{str(file)} has invalid Selected value for index: {invalid_index}"
        )


@pytest.mark.medium
@pytest.mark.parametrize("file", LIST_FILES)
def test_list_valid_preset_values(file):
    """Preset columns column must be NaN or 1 (not 1.0)"""
    df = pd.read_csv(file, dtype="object")
    preset_columns = [c for c in df.columns if c.startswith("preset_")]
    condition = (
        df[preset_columns].apply(lambda x: x.isin(["1"]) | x.isna(), axis=0).all(axis=1)
    )
    if not condition.all():
        invalid_index = df.loc[~condition].index.tolist()
        pytest.fail(f"{str(file)} has invalid preset values for index: {invalid_index}")


@pytest.mark.medium
@pytest.mark.parametrize("file", LIST_FILES)
def test_too_many_presets(file):
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


@pytest.mark.high
@pytest.mark.parametrize("file", LIST_FILES_WITH_ARCHETYPE_PRESETS)
def test_missing_presets(file):
    """Check if the Lists file has ARC presets for specific Lists"""
    arc = pd.read_csv(ARC_PATH, nrows=0, dtype="object")
    arc_header = list(arc.columns)
    arc_presets = [c for c in arc_header if c.startswith("preset_ARChetype")]

    header = pd.read_csv(file, nrows=0).columns
    presets = [c for c in header if c.startswith("preset_ARChetype")]

    arc_presets_not_in_list = [x for x in arc_presets if x not in presets]
    if arc_presets_not_in_list:
        pytest.fail(f"{str(file)} missing presets in ARC: {arc_presets_not_in_list}")
