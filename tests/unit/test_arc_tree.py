from unittest import mock

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from arc import arc_tree


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


@mock.patch("bridge.arc.arc_tree._get_units_parent_units_dataframes")
@mock.patch("bridge.arc.arc_tree._create_tree_item_dataframe")
@mock.patch("bridge.arc.arc_core.get_dynamic_units_conversion_bool", return_value=True)
def test_get_tree_items_with_units(
    _mock_dynamic_units_bool,
    mock_df_tree,
    mock_get_units,
    df_tree_units,
):
    # I haven't mocked all the functions from arc_tree as it made it too complicated
    # So some are tested in here, e.g. _add_form_to_tree
    mock_df_tree.return_value = df_tree_units
    df_datadicc = pd.DataFrame()  # Not used
    version = "v1.1.1"  # Not used
    dynamic_units_conversion = False  # Not used
    data_parent = {
        "Variable": [
            "demog_height_units",
        ],
        "Question": [
            "Height (select units)",
        ],
        "Type": [
            "radio",
        ],
    }
    df_parent = pd.DataFrame.from_dict(data_parent)
    data_units = {
        "Variable": [
            "demog_height_cm",
            "demog_height_in",
        ],
        "Question": [
            "Height (cm)",
            "Height (in)",
        ],
        "Type": [
            "number",
            "number",
        ],
    }
    df_units = pd.DataFrame.from_dict(data_units)
    mock_get_units.return_value = [df_parent, df_units]

    expected = {
        "children": [
            {
                "children": [
                    {
                        "children": [
                            {
                                "children": [
                                    {
                                        "key": "demog_height_cm",
                                        "title": "Height (cm)",
                                    },
                                    {
                                        "key": "demog_height_in",
                                        "title": "Height (in)",
                                    },
                                ],
                                "key": "demog_height_units",
                                "title": "Height (select units)",
                            }
                        ],
                        "key": "PRESENTATION-DEMOGRAPHICS",
                        "title": "DEMOGRAPHICS",
                    }
                ],
                "key": "PRESENTATION",
                "title": "PRESENTATION",
            }
        ],
        "key": "ARC",
        "title": "v1.1.1",
    }

    output = arc_tree.get_tree_items(df_datadicc, version, dynamic_units_conversion)

    assert output == expected


@mock.patch("bridge.arc.arc_tree._get_units_parent_units_dataframes")
@mock.patch("bridge.arc.arc_tree._create_tree_item_dataframe")
@mock.patch("bridge.arc.arc_core.get_dynamic_units_conversion_bool", return_value=True)
def test_get_tree_items_with_units_remove_select_units(
    _mock_dynamic_units_bool,
    mock_df_tree,
    mock_get_units,
    df_tree_units,
):
    # I haven't mocked all the functions from arc_tree as it made it too complicated
    # So some are tested in here, e.g. _add_form_to_tree
    mock_df_tree.return_value = df_tree_units
    df_datadicc = pd.DataFrame()  # Not used
    version = "v1.1.1"  # Not used
    dynamic_units_conversion = False  # Not used
    data_parent = {
        "Variable": [
            "demog_height_units",
        ],
        "Question": [
            "Height",
        ],
        "Type": [
            "radio",
        ],
    }
    df_parent = pd.DataFrame.from_dict(data_parent)
    data_units = {
        "Variable": [
            "demog_height_cm",
            "demog_height_in",
        ],
        "Question": [
            "Height (cm)",
            "Height (in)",
        ],
        "Type": [
            "number",
            "number",
        ],
    }
    df_units = pd.DataFrame.from_dict(data_units)
    mock_get_units.return_value = [df_parent, df_units]

    expected = {
        "children": [
            {
                "children": [
                    {
                        "children": [
                            {
                                "children": [
                                    {
                                        "key": "demog_height_cm",
                                        "title": "Height (cm)",
                                    },
                                    {
                                        "key": "demog_height_in",
                                        "title": "Height (in)",
                                    },
                                ],
                                "key": "demog_height_units",
                                "title": "Height",
                            }
                        ],
                        "key": "PRESENTATION-DEMOGRAPHICS",
                        "title": "DEMOGRAPHICS",
                    }
                ],
                "key": "PRESENTATION",
                "title": "PRESENTATION",
            }
        ],
        "key": "ARC",
        "title": "v1.1.1",
    }

    output = arc_tree.get_tree_items(df_datadicc, version, dynamic_units_conversion)

    assert output == expected


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


@mock.patch(
    "bridge.arc.arc_tree._get_units_parent_units_dataframes",
    return_value=[pd.DataFrame(), pd.DataFrame()],
)
@mock.patch("bridge.arc.arc_tree._create_tree_item_dataframe")
@mock.patch("bridge.arc.arc_core.get_dynamic_units_conversion_bool", return_value=True)
def test_get_tree_items_no_units_single_var(
    _mock_dynamic_units_bool,
    mock_df_tree,
    _mock_get_units,
    df_tree_single,
):
    # I haven't mocked all the functions from arc_tree as it made it too complicated
    # So some are tested in here, e.g. _add_form_to_tree
    mock_df_tree.return_value = df_tree_single
    df_datadicc = pd.DataFrame()  # Not used
    version = "v1.1.1"  # Not used
    dynamic_units_conversion = False  # Not used

    expected = {
        "children": [
            {
                "children": [
                    {
                        "children": [
                            {
                                "key": "inclu_reason",
                                "title": "Is the suspected or confirmed infection the reason for hospital admission?",
                            }
                        ],
                        "key": "PRESENTATION-INCLUSION CRITERIA",
                        "title": "INCLUSION CRITERIA",
                    }
                ],
                "key": "PRESENTATION",
                "title": "PRESENTATION",
            }
        ],
        "key": "ARC",
        "title": "v1.1.1",
    }

    output = arc_tree.get_tree_items(df_datadicc, version, dynamic_units_conversion)

    assert output == expected


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


@mock.patch(
    "bridge.arc.arc_tree._get_units_parent_units_dataframes",
    return_value=[pd.DataFrame(), pd.DataFrame()],
)
@mock.patch("bridge.arc.arc_tree._create_tree_item_dataframe")
@mock.patch("bridge.arc.arc_core.get_dynamic_units_conversion_bool", return_value=True)
def test_get_tree_items_no_units_multiple_vars(
    _mock_dynamic_units_bool,
    mock_df_tree,
    _mock_get_units,
    df_tree_multiple,
):
    # I haven't mocked all the functions from arc_tree as it made it too complicated
    # So some are tested in here, e.g. _add_form_to_tree
    mock_df_tree.return_value = df_tree_multiple
    df_datadicc = pd.DataFrame()  # Not used
    version = "v1.1.1"  # Not used
    dynamic_units_conversion = False  # Not used

    expected = {
        "children": [
            {
                "children": [
                    {
                        "children": [
                            {
                                "children": [
                                    {
                                        "key": "inclu_testreason",
                                        "title": "Reason why "
                                        "the patient "
                                        "was tested",
                                    },
                                    {
                                        "key": "inclu_testreason_otth",
                                        "title": "Specify " "other " "reason",
                                    },
                                    {
                                        "key": "inclu_testreason_otth1",
                                        "title": "Specify " "other " "reason 1",
                                    },
                                    {
                                        "key": "inclu_testreason_otth2",
                                        "title": "Specify " "other " "reason 2",
                                    },
                                ],
                                "key": "PRESENTATION-INCLUSION "
                                "CRITERIA-VARI-testreason-GROUP",
                                "title": "Reason why the patient " "was tested (Group)",
                            }
                        ],
                        "key": "PRESENTATION-INCLUSION CRITERIA",
                        "title": "INCLUSION CRITERIA",
                    }
                ],
                "key": "PRESENTATION",
                "title": "PRESENTATION",
            }
        ],
        "key": "ARC",
        "title": "v1.1.1",
    }

    output = arc_tree.get_tree_items(df_datadicc, version, dynamic_units_conversion)

    assert output == expected


def test_get_units_parent_units_dataframes_dynamic_false():
    dynamic_units_conversion = False
    data_variable = {
        "Variable": [
            "demog_height",
            "demog_height_units",
            "demog_height_cm",
            "demog_height_in",
        ],
        "Validation": [
            "number",
            "units",
            "number",
            "number",
        ],
    }
    df_variable = pd.DataFrame.from_dict(data_variable)

    data_parent = {
        "Variable": [
            "demog_height_units",
        ],
        "Validation": [
            "units",
        ],
    }
    df_expected_parent = pd.DataFrame(data_parent)
    data_units = {
        "Variable": [
            "demog_height_cm",
            "demog_height_in",
        ],
        "Validation": [
            "number",
            "number",
        ],
    }
    df_expected_units = pd.DataFrame.from_dict(data_units)

    df_output_parent, df_output_units = arc_tree._get_units_parent_units_dataframes(
        dynamic_units_conversion, df_variable
    )

    assert_frame_equal(df_output_parent, df_expected_parent)
    assert_frame_equal(df_output_units, df_expected_units)


def test_get_units_parent_units_dataframes_dynamic_true():
    dynamic_units_conversion = True
    data_variable = {
        "Variable": [
            "demog_height",
            "demog_height_cm",
            "demog_height_in",
        ],
        "Question": [
            "Height (select units)",
            "Height (cm)",
            "Height (in)",
        ],
    }
    df_variable = pd.DataFrame.from_dict(data_variable)

    data_parent = {
        "Variable": [
            "demog_height",
        ],
        "Question": [
            "Height (select units)",
        ],
    }
    df_expected_parent = pd.DataFrame(data_parent)
    data_units = {
        "Variable": [
            "demog_height_cm",
            "demog_height_in",
        ],
        "Question": [
            "Height (cm)",
            "Height (in)",
        ],
    }
    df_expected_units = pd.DataFrame.from_dict(data_units)

    df_output_parent, df_output_units = arc_tree._get_units_parent_units_dataframes(
        dynamic_units_conversion, df_variable
    )

    assert_frame_equal(df_output_parent, df_expected_parent)
    assert_frame_equal(df_output_units, df_expected_units)


def test_format_question_text_user_list():
    row_data = {
        "Type": "user_list",
        "Question": "A question",
    }
    row = pd.Series(row_data)
    expected = "↳ A question"
    output = arc_tree._format_question_text(row)
    assert output == expected


def test_format_question_text_multi_list():
    row_data = {
        "Type": "multi_list",
        "Question": "A question",
    }
    row = pd.Series(row_data)
    expected = "⇉ A question"
    output = arc_tree._format_question_text(row)
    assert output == expected


def test_create_tree_item_dataframe_dynamic_false():
    dynamic_units_conversion = False
    data = {
        "Form": [
            "presentation",
            "presentation",
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
            "DEMOGRAPHICS",
            "MEDICATION PRIOR TO THIS ADMISSION / PRESENTATION",
        ],
        "Variable": [
            "demog_height",
            "demog_height_units",
            "demog_height_cm",
            "demog_height_in",
            "demog_weight_kg",
            "drug14_antiviral_route",
        ],
        "Type": [
            "number",
            "radio",
            "number",
            "number",
            "number",
            "checkbox",
        ],
        "Question": [
            "Height",
            "Height",
            "Height (cm)",
            "Height (in)",
            "Weight (kg)",
            "Antiviral administration route",
        ],
        "Validation": [
            "number",
            "units",
            "number",
            "number",
            "number",
            None,
        ],
        "vari": [
            "height",
            "height",
            "height",
            "height",
            "weight",
            "antiviral",
        ],
        "mod": [
            None,
            "units",
            "cm",
            "in",
            "kg",
            "route",
        ],
    }
    df_datadicc = pd.DataFrame.from_dict(data)

    data_expected = {
        "Form": [
            "presentation",
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
            "DEMOGRAPHICS",
        ],
        "vari": [
            "height",
            "height",
            "height",
            "height",
            "weight",
        ],
        "mod": [
            None,
            "units",
            "cm",
            "in",
            "kg",
        ],
        "Question": [
            "Height",
            "Height",
            "Height (cm)",
            "Height (in)",
            "Weight (kg)",
        ],
        "Variable": [
            "demog_height",
            "demog_height_units",
            "demog_height_cm",
            "demog_height_in",
            "demog_weight_kg",
        ],
        "Type": [
            "number",
            "radio",
            "number",
            "number",
            "number",
        ],
        "Validation": [
            "number",
            "units",
            "number",
            "number",
            "number",
        ],
        "_row_order": [
            0,
            1,
            2,
            3,
            4,
        ],
        "n_in_vari_total": [
            4,
            4,
            4,
            4,
            1,
        ],
        "first_question": [
            "Height",
            "Height",
            "Height",
            "Height",
            "Weight (kg)",
        ],
        "first_variable": [
            "demog_height",
            "demog_height",
            "demog_height",
            "demog_height",
            "demog_weight_kg",
        ],
    }
    df_expected = pd.DataFrame(data_expected)

    df_output = arc_tree._create_tree_item_dataframe(
        df_datadicc, dynamic_units_conversion
    )
    assert_frame_equal(df_output, df_expected)


def test_create_tree_item_dataframe_dynamic_true():
    dynamic_units_conversion = True
    data = {
        "Form": [
            "presentation",
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
            "MEDICATION PRIOR TO THIS ADMISSION / PRESENTATION",
        ],
        "Variable": [
            "demog_height",
            "demog_height_cm",
            "demog_height_in",
            "demog_weight_kg",
            "drug14_antiviral_route",
        ],
        "Type": [
            "number",
            "number",
            "number",
            "number",
            "checkbox",
        ],
        "Question": [
            "Height (select units)",
            "Height (cm)",
            "Height (in)",
            "Weight (kg)",
            "Antiviral administration route",
        ],
        "vari": [
            "height",
            "height",
            "height",
            "weight",
            "antiviral",
        ],
        "mod": [
            None,
            "cm",
            "in",
            "kg",
            "route",
        ],
    }
    df_datadicc = pd.DataFrame.from_dict(data)

    data_expected = {
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
            "weight",
        ],
        "mod": [
            None,
            "cm",
            "in",
            "kg",
        ],
        "Question": [
            "Height (select units)",
            "Height (cm)",
            "Height (in)",
            "Weight (kg)",
        ],
        "Variable": [
            "demog_height",
            "demog_height_cm",
            "demog_height_in",
            "demog_weight_kg",
        ],
        "Type": [
            "number",
            "number",
            "number",
            "number",
        ],
        "_row_order": [
            0,
            1,
            2,
            3,
        ],
        "n_in_vari_total": [
            3,
            3,
            3,
            1,
        ],
        "first_question": [
            "Height (select units)",
            "Height (select units)",
            "Height (select units)",
            "Weight (kg)",
        ],
        "first_variable": [
            "demog_height",
            "demog_height",
            "demog_height",
            "demog_weight_kg",
        ],
    }
    df_expected = pd.DataFrame(data_expected)

    df_output = arc_tree._create_tree_item_dataframe(
        df_datadicc, dynamic_units_conversion
    )
    assert_frame_equal(df_output, df_expected)
