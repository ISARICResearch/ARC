from unittest import mock

import numpy as np
import pandas as pd
import pytest
from pandas._testing import assert_frame_equal

from arc import arc_translations


@mock.patch("arc.arc_translations.process_skip_logic")
@mock.patch("arc.arc_translations.ArcApiClient.get_dataframe_arc_version_language")
def test_get_arc_translation(mock_arc, mock_skip_logic):
    version = "v1.1.1"
    language = "English"
    data = {
        "Variable": [
            "subjid",
            "inclu_reason",
        ],
        "Form": [
            "presentation",
            "presentation",
        ],
        "Section": [
            np.nan,
            "INCLUSION CRITERIA",
        ],
        "Question": [
            "Participant Identification Number (PIN)",
            "Is the suspected or confirmed infection the reason for hospital admission?",
        ],
        "Answer Options": [
            np.nan,
            "1, Yes | 0, No | 99, Unknown",
        ],
        "Definition": [
            "The Participant Identification Number or PIN.",
            "Suspected infection with the pathogen of interest if the reason for the hospital admission.",
        ],
        "Completion Guideline": [
            "Write the Participant Identification Number (PIN).",
            "Indicate 'Yes' if suspected or confirmed infection with the pathogen of interest.",
        ],
    }
    df_current_datadicc = pd.DataFrame.from_dict(data)

    data_not_english = {
        "Variable": [
            "subjid",
            "inclu_reason",
        ],
        "Form": [
            "presentation_translated",
            "presentation_translated",
        ],
        "Section": [
            np.nan,
            "INCLUSION CRITERIA TRANSLATED",
        ],
        "Question": [
            "Participant Identification Number (PIN)",
            "Is the suspected or confirmed infection the reason for hospital admission (translated)?",
        ],
        "Answer Options": [
            np.nan,
            "1, Joo | 0, Ei | 99, Jattipotti",
        ],
        "Definition": [
            "Le Participant Identification Number or PIN.",
            "Suspected infection with the pathogen of interest if the reason for the hospital admission (translated).",
        ],
        "Completion Guideline": [
            "Kirjoita osallistujan tunnistenumero (PIN-koodi).",
            "Indicate 'Yes' if suspected or confirmed infection with the pathogen of interest (translated).",
        ],
    }
    df_not_english = pd.DataFrame.from_dict(data_not_english)
    branch_logic = "[Some branch logic]"

    mock_arc.side_effect = [df_current_datadicc, df_not_english]
    mock_skip_logic.return_value = branch_logic

    df_extra_columns = pd.DataFrame.from_dict(
        {
            "Question_english": [
                "Participant Identification Number (PIN)",
                "Is the suspected or confirmed infection the reason for hospital admission?",
            ],
            "Branch": [
                branch_logic,
                branch_logic,
            ],
        }
    )

    df_expected = df_not_english.join(df_extra_columns)

    df_output = arc_translations.get_arc_translation(
        language, version, df_current_datadicc
    )

    assert_frame_equal(df_output, df_expected)


@pytest.mark.parametrize(
    "skip_logic_column, variables_expected, values_expected, comparison_operators_expected, logical_operators_expected",
    [
        ("[inclu_testreason]='88'", ["inclu_testreason"], ["88"], ["="], []),
        ("[inclu_testreason]=88.0", ["inclu_testreason"], [88.0], ["="], []),
        ("[inclu_testreason]=88", ["inclu_testreason"], [88], ["="], []),
        (np.nan, [], [], [], []),
    ],
)
def test_extract_logic_components(
    skip_logic_column,
    variables_expected,
    values_expected,
    comparison_operators_expected,
    logical_operators_expected,
):
    (
        variables_output,
        values_output,
        comparison_operators_output,
        logical_operators_output,
    ) = arc_translations._extract_logic_components(skip_logic_column)

    assert variables_output == variables_expected
    assert values_output == values_expected
    assert comparison_operators_output == comparison_operators_expected
    assert logical_operators_output == logical_operators_expected


@mock.patch("arc.arc_translations._extract_logic_components")
def test_process_skip_logic(mock_extract):
    mock_extract.return_value = (
        ["inclu_testreason"],
        ["88"],
        ["="],
        [],
    )
    data_series = {
        "Skip Logic": ["[inclu_testreason]='88'"],
    }
    row = pd.Series(data_series)
    data = {
        "Variable": [
            "inclu_testreason",
        ],
        "Question": [
            "Reason why the patient was tested",
        ],
        "Answer Options": [
            " 1, Symptomatic | 2, Asymptomatic | 3, Not tested | 99, Unknown | 88, Other",
        ],
        "Skip Logic": [
            "[inclu_testreason]='88'",
        ],
    }
    df_current_datadicc = pd.DataFrame.from_dict(data)
    expected = "(Reason why the patient was tested = Other)  "
    output = arc_translations.process_skip_logic(row, df_current_datadicc)
    assert output == expected


@mock.patch("arc.arc_translations._extract_logic_components")
def test_process_skip_logic_no_answers(mock_extract):
    mock_extract.return_value = (
        ["inclu_testreason"],
        ["88"],
        ["="],
        [],
    )
    data_series = {
        "Skip Logic": ["[inclu_testreason]='88'"],
    }
    row = pd.Series(data_series)
    data = {
        "Variable": [
            "inclu_testreason",
        ],
        "Question": [
            "Reason why the patient was tested",
        ],
        "Answer Options": [
            np.nan,
        ],
        "Skip Logic": [
            "[inclu_testreason]='88'",
        ],
    }
    df_current_datadicc = pd.DataFrame.from_dict(data)
    expected = "(Reason why the patient was tested = 88)  "
    output = arc_translations.process_skip_logic(row, df_current_datadicc)
    assert output == expected


@mock.patch("arc.arc_translations._extract_logic_components")
def test_process_skip_logic_index_error(mock_extract):
    mock_extract.return_value = (
        ["inclu_testreason_index_error"],
        ["88"],
        ["="],
        [],
    )
    data_series = {
        "Skip Logic": ["[inclu_testreason]='88'"],
    }
    row = pd.Series(data_series)
    data = {
        "Variable": [
            "inclu_testreason",
        ],
        "Question": [
            "Reason why the patient was tested",
        ],
        "Answer Options": [
            np.nan,
        ],
        "Skip Logic": [
            "[inclu_testreason]='88'",
        ],
    }
    df_current_datadicc = pd.DataFrame.from_dict(data)
    expected = "Variable not found getARCTranslation"
    output = arc_translations.process_skip_logic(row, df_current_datadicc)
    assert output == expected


def test_get_translations():
    english_dict = arc_translations.get_translations("English")
    spanish_dict = arc_translations.get_translations("Spanish")
    french_dict = arc_translations.get_translations("French")
    portuguese_dict = arc_translations.get_translations("Portuguese")
    assert (
        len(english_dict)
        == len(spanish_dict)
        == len(french_dict)
        == len(portuguese_dict)
    )
    assert english_dict["select"] == "Select"


def test_get_translations_exception():
    with pytest.raises(ValueError):
        arc_translations.get_translations("Klingon")
