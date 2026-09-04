from unittest import mock

import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from arc import arc_core


@pytest.mark.all
def test_add_required_datadicc_columns():
    data = {
        "Section": [
            "INCLUSION CRITERIA",
            "CO-MORBIDITIES AND RISK FACTORS: Existing prior to this current illness and is ongoing",
        ],
        "Variable": [
            "inclu_disease",
            "comor_chrcardiac_chf",
        ],
    }
    df_datadicc = pd.DataFrame.from_dict(data)
    df_new_columns = pd.DataFrame.from_dict(
        {
            "Sec": [
                "inclu",
                "comor",
            ],
            "vari": [
                "disease",
                "chrcardiac",
            ],
            "mod": [
                None,
                "chf",
            ],
            "Sec_name": [
                "INCLUSION CRITERIA",
                "CO-MORBIDITIES AND RISK FACTORS",
            ],
            "Expla": [
                None,
                " Existing prior to this current illness and is ongoing",
            ],
        }
    )
    df_expected = df_datadicc.join(df_new_columns)
    df_output = arc_core.add_required_datadicc_columns(df_datadicc)
    assert_frame_equal(df_output, df_expected)


@pytest.mark.all
@mock.patch("bridge.arc.arc_core.logger")
@mock.patch("bridge.arc.arc_core.ArcApiClient.get_arc_version_list")
def test_get_arc_versions(mock_get_versions, _mock_logger):
    version_list = ["v1.0.0", "v1.1.0", "v1.1.1", "v1.1.2", "v1.1.3"]
    mock_get_versions.return_value = version_list

    (version_list_output, latest_version_output) = arc_core.get_arc_versions()

    assert version_list_output == version_list
    assert latest_version_output == "v1.1.3"


@pytest.mark.all
def test_get_variable_order():
    data = {
        "Sec": [
            "inclu",
            "inclu",
            "comor",
            "adsym",
        ],
        "vari": [
            "disease",
            "case",
            "chrcardiac",
            "resp",
        ],
    }
    df_current_datadicc = pd.DataFrame.from_dict(data)
    list_expected = [
        "inclu_disease",
        "inclu_case",
        "comor_chrcardiac",
        "adsym_resp",
    ]
    list_output = arc_core.get_variable_order(df_current_datadicc)
    assert list_output == list_expected


@pytest.mark.all
@mock.patch("bridge.arc.arc_core.logger")
@mock.patch("bridge.arc.arc_core.get_dependencies")
@mock.patch("bridge.arc.arc_core.ArcApiClient.get_dataframe_arc_sha")
@mock.patch("bridge.arc.arc_core.ArcApiClient.get_arc_version_sha")
def test_get_arc(mock_sha, mock_arc, mock_dependencies, _mock_logger):
    sha_str = "sha123"
    mock_sha.return_value = sha_str

    data = {
        "Variable": [
            "subjid",
            "inclu_disease",
            "inclu_testreason_otth",
        ],
        "Question": [
            "Question for subjid",
            "Question for inclu_disease",
            "Question for inclu_testreason_otth",
        ],
        "preset_ARChetype Disease CRF_Covid Adding_Some_Extra_Stuff": [
            1,
            1,
            0,
        ],
        "preset_ARChetype Disease CRF_Dengue": [
            0,
            1,
            0,
        ],
    }
    df_datadicc = pd.DataFrame.from_dict(data)
    mock_arc.return_value = df_datadicc

    data_dependencies = {
        "Variable": [
            "subjid",
            "inclu_disease",
            "inclu_testreason_otth",
        ],
        "Dependencies": [
            "[[subjid]]",
            "[subjid]",
            "[inclu_testreason, subjid]",
        ],
    }
    df_dependencies = pd.DataFrame.from_dict(data_dependencies)
    mock_dependencies.return_value = df_dependencies

    data_expected = {
        "Variable": [
            "subjid",
            "inclu_disease",
            "inclu_testreason_otth",
        ],
        "Question": [
            "Question for subjid",
            "Question for inclu_disease",
            "Question for inclu_testreason_otth",
        ],
        "preset_ARChetype Disease CRF_Covid Adding_Some_Extra_Stuff": [
            1,
            1,
            0,
        ],
        "preset_ARChetype Disease CRF_Dengue": [
            0,
            1,
            0,
        ],
        "Dependencies": [
            "[[subjid]]",
            "[subjid]",
            "[inclu_testreason, subjid]",
        ],
        "Branch": [
            "",
            "",
            "",
        ],
        "Question_english": [
            "Question for subjid",
            "Question for inclu_disease",
            "Question for inclu_testreason_otth",
        ],
    }
    df_expected = pd.DataFrame.from_dict(data_expected)
    preset_expected = [
        ["ARChetype Disease CRF", "Covid Adding Some Extra Stuff"],
        ["ARChetype Disease CRF", "Dengue"],
    ]

    version = "v1.1.1"
    (df_output, preset_output, commit_output) = arc_core.get_arc(version)

    assert_frame_equal(df_output, df_expected)
    assert preset_output == preset_expected
    assert commit_output == sha_str


@pytest.mark.all
def test_get_dependencies():
    data = {
        "Variable": [
            "subjid",
            "inclu_consent_date",
            "readm_prev_site",
            "treat_an",
            "treat_another",
            "medi_something",
            "medi_somethingunits",
        ],
        "Skip Logic": [
            np.nan,
            "[inclu_consent]='1'",
            "[readm_prev] = '1' or [readm_prev]='2' or [readm_prev]='3'",
            "[treat_dailydata]='1'",
            "[treat_dailydata]='1'",
            "[medi_treat()]='1'",
            "[medi_treat()]='1'",
        ],
    }
    df_datadicc = pd.DataFrame.from_dict(data)

    data_expected = {
        "Variable": [
            "subjid",
            "inclu_consent_date",
            "readm_prev_site",
            "treat_an",
            "treat_another",
            "medi_something",
            "medi_somethingunits",
        ],
        "Skip Logic": [
            np.nan,
            "[inclu_consent]='1'",
            "[readm_prev] = '1' or [readm_prev]='2' or [readm_prev]='3'",
            "[treat_dailydata]='1'",
            "[treat_dailydata]='1'",
            "[medi_treat()]='1'",
            "[medi_treat()]='1'",
        ],
        "Dependencies": [
            ["subjid"],
            ["inclu_consent", "subjid"],
            ["readm_prev", "readm_prev", "readm_prev", "subjid"],
            ["treat_dailydata", "subjid", "treat_another"],
            ["treat_dailydata", "subjid"],
            ["medi_treat", "subjid", "medi_somethingunits"],
            ["medi_treat", "subjid"],
        ],
    }
    df_expected = pd.DataFrame.from_dict(data_expected)
    df_output = arc_core.get_dependencies(df_datadicc)
    assert_frame_equal(df_output, df_expected)


@pytest.mark.all
def test_add_transformed_rows():
    data = {
        "Variable": [
            "demog_height",
            "comor_unlisted",
        ],
    }
    df_selected_variables = pd.DataFrame.from_dict(data)
    data = {
        "Variable": [
            "demog_height",
            "comor_unlisted",
            "comor_unlisted_0item",
            "test_var_0item",
        ],
        "Sec": [
            "demog",
            "comor",
            "comor",
            "test",
        ],
        "vari": [
            "height",
            "unlisted",
            "unlisted",
            "var",
        ],
    }
    df_arc_var_units_selected = pd.DataFrame.from_dict(data)

    variable_order = [
        "demog_height",
        "test_var_0item",
        "comor_unlisted",
    ]

    data_expected = {
        "Variable": [
            "demog_height",
            "test_var_0item",
            "comor_unlisted",
            "comor_unlisted_0item",
        ],
    }
    df_expected = pd.DataFrame.from_dict(data_expected)

    df_output = arc_core.add_transformed_rows(
        df_selected_variables, df_arc_var_units_selected, variable_order
    )

    assert_frame_equal(df_output, df_expected)


@pytest.mark.all
@pytest.mark.parametrize(
    "version, expected_output",
    [
        ("v1.1.5", True),
        ("v1.2.0", True),
        ("v1.2.1", False),
        ("v1.2.2", False),
        ("v1.3.5", False),
    ],
)
def test_get_dynamic_units_conversion_bool(version, expected_output):
    output = arc_core.get_dynamic_units_conversion_bool(version)
    assert output == expected_output
