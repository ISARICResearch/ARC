# -- IMPORTS --

# -- Standard libraries --
import os
from unittest.mock import patch

# -- 3rd party libraries --
import pandas as pd
import pytest

# -- Internal libraries --
from arc.arc_api import ArcApiClient


@pytest.fixture(scope="session")
def client_production():
    os.environ["ENV"] = "production"
    os.environ["GITHUB_TOKEN"] = "abc123"
    return ArcApiClient()


@pytest.fixture(scope="session")
def client_development():
    os.environ["ENV"] = "development"
    os.environ["GITHUB_TOKEN"] = "def456"
    return ArcApiClient()


@pytest.fixture()
def data_path():
    data_path = "my/test/path"
    return data_path


@pytest.fixture
def mock_language_json():
    language_json = [
        {
            "_links": {
                "self": "https://api.github.com/repos/ISARICResearch/ARC-Translations/contents/ARCH1.1.3/English?ref=main"
            },
            "name": "English",
            "path": "ARCH1.1.3/English",
        },
        {
            "_links": {
                "self": "https://api.github.com/repos/ISARICResearch/ARC-Translations/contents/ARCH1.1.3/French?ref=main"
            },
            "name": "French",
            "path": "ARCH1.1.3/French",
        },
        {
            "_links": {
                "self": "https://api.github.com/repos/ISARICResearch/ARC-Translations/contents/ARCH1.1.3/Portuguese?ref=main"
            },
            "name": "Portuguese",
            "path": "ARCH1.1.3/Portuguese",
        },
        {
            "_links": {
                "self": "https://api.github.com/repos/ISARICResearch/ARC-Translations/contents/ARCH1.1.3/Spanish?ref=main"
            },
            "name": "Spanish",
            "path": "ARCH1.1.3/Spanish",
        },
    ]
    return language_json


@pytest.fixture
def translation_dict():
    translation_dict = {
        "any_additional": "Any additional",
        "other": "Other",
        "other_agent": "other agents administered",
        "select": "Select",
        "select_additional": "Select additional",
        "specify": "Specify",
        "specify_other": "Specify other",
        "specify_other_infection": "Specify other infection",
        "units": "Units",
    }
    return translation_dict


@pytest.fixture
def mock_read_list_file():
    """Fixture that patches read_list_file and returns a configurable mock."""
    with patch("arc.draft_parser.read_list_file") as mock:
        mock.return_value = {"1": "Option A", "2": "Option B"}
        yield mock


@pytest.fixture()
def mock_list_choices():
    mock_list_choices = [
        [
            "inclu_disease",
            [
                [1, "Adenovirus", 0],
                [2, "Dengue", 0],
                [5, "Mpox", 1],
            ],
        ]
    ]
    return mock_list_choices


@pytest.fixture()
def mock_all_rows():
    dict1 = {
        "Variable": "inclu_disease",
        "Type": "some_list",
        "List": "inclusion_Diseases",
    }
    series1 = pd.Series(dict1, name=0)
    dict2 = {
        "Variable": "inclu_disease_otherl3",
        "Type": "text",
        "List": None,
    }
    series2 = pd.Series(dict2, name=0)
    mock_all_rows = [
        series1,
        series2,
    ]
    return mock_all_rows


@pytest.fixture()
def df_expected_get_list_content():
    data_expected = {
        "Variable": [
            "inclu_disease",
            "inclu_disease_otherl3",
        ],
        "Type": [
            "some_list",
            "text",
        ],
        "List": [
            "inclusion_Diseases",
            None,
        ],
    }
    df_expected = pd.DataFrame.from_dict(data_expected)
    return df_expected


@pytest.fixture()
def list_expected_get_list_content():
    list_expected = [
        [
            "inclu_disease",
            [
                [1, "Adenovirus", 0],
                [2, "Dengue", 0],
                [5, "Mpox", 1],
            ],
        ]
    ]
    return list_expected


@pytest.fixture
def df_tree_units():
    data_tree = {
        "Form": [
            "presentation",
            "presentation",
            "presentation",
            "presentation",
        ],
        "Sec_name": [
            "DEMOGRAPHICS",
            "DEMOGRAPHICS",
            "DEMOGRAPHICS",
            "DEMOGRAPHICS",
        ],
        "vari": [
            "height",
            "height",
            "height",
            "height",
        ],
        "Variable": [
            "demog_height",
            "demog_height_units",
            "demog_height_cm",
            "demog_height_in",
        ],
        "_row_order": [
            48,
            49,
            50,
            51,
        ],
    }
    df_tree = pd.DataFrame.from_dict(data_tree)
    return df_tree


@pytest.fixture
def df_tree_single():
    data_tree = {
        "Form": [
            "presentation",
        ],
        "Sec_name": [
            "INCLUSION CRITERIA",
        ],
        "vari": [
            "reason",
        ],
        "Question": [
            "Is the suspected or confirmed infection the reason for hospital admission?",
        ],
        "Variable": [
            "inclu_reason",
        ],
        "Type": [
            "radio",
        ],
        "_row_order": [
            1,
        ],
        "n_in_vari_total": [
            1,
        ],
    }
    df_tree = pd.DataFrame.from_dict(data_tree)
    return df_tree


@pytest.fixture
def df_tree_multiple():
    data_tree = {
        "Form": [
            "presentation",
            "presentation",
            "presentation",
            "presentation",
        ],
        "Sec_name": [
            "INCLUSION CRITERIA",
            "INCLUSION CRITERIA",
            "INCLUSION CRITERIA",
            "INCLUSION CRITERIA",
        ],
        "vari": [
            "testreason",
            "testreason",
            "testreason",
            "testreason",
        ],
        "Question": [
            "Reason why the patient was tested",
            "Specify other reason",
            "Specify other reason 1",
            "Specify other reason 2",
        ],
        "Variable": [
            "inclu_testreason",
            "inclu_testreason_otth",
            "inclu_testreason_otth1",
            "inclu_testreason_otth2",
        ],
        "Type": [
            "radio",
            "text",
            "text",
            "text",
        ],
        "_row_order": [
            3,
            4,
            5,
            6,
        ],
        "n_in_vari_total": [
            4,
            4,
            4,
            4,
        ],
        "first_question": [
            "Reason why the patient was tested",
            "Reason why the patient was tested",
            "Reason why the patient was tested",
            "Reason why the patient was tested",
        ],
    }
    df_tree = pd.DataFrame.from_dict(data_tree)
    return df_tree

    @pytest.fixture
    def arc_with_units(self):
        """Create a test dataframe with unit fields matching the registry."""
        return pd.DataFrame(
            {
                "Variable": [
                    "demog_height",
                    "demog_height_units",
                    "demog_height_cm",
                    "demog_height_in",
                    "other_var",
                ],
                "Form": ["presentation"] * 5,
            }
        )
