"""
Unit tests for schema draft parser functions.
"""

import adtl
import pytest
import pandas as pd
from unittest.mock import patch

from schemas.draft_parser import (
    if_all_not_missing,
    get_value_options,
    read_list_file,
    attrs_with_units,
    attrs_with_enums,
    attrs_with_checkboxes,
    attrs_with_lists,
    attrs_with_userlists,
    attrs_with_multilists,
    numeric_attrs,
    generic_str_attrs,
    form_definitions,
    generate_parser,
    missing_codes,
)


@pytest.fixture
def mock_read_list_file():
    """Fixture that patches read_list_file and returns a configurable mock."""
    with patch("schemas.draft_parser.read_list_file") as mock:
        mock.return_value = {"1": "Option A", "2": "Option B"}
        yield mock


class TestIfAllNotMissing:
    """Tests for the if_all_not_missing helper function."""

    def test_default_missing_values(self):
        """Check default missing values are used."""
        result = if_all_not_missing("test_field")
        expected = {
            "all": [
                {"test_field": {"!=": "UNK"}},
                {"test_field": {"!=": "NI"}},
                {"test_field": {"!=": "NASK"}},
                {"test_field": {"!=": "NA"}},
                {"test_field": {"!=": ""}},
            ]
        }
        assert result == expected

    def test_custom_missing_values(self):
        """Check custom missing values work."""
        result = if_all_not_missing("my_field", missing_values=["UNKNOWN", "NULL"])
        expected = {
            "all": [
                {"my_field": {"!=": "UNKNOWN"}},
                {"my_field": {"!=": "NULL"}},
                {"my_field": {"!=": ""}},
            ]
        }
        assert result == expected

    def test_empty_missing_values(self):
        """Check empty missing values still includes empty string check."""
        result = if_all_not_missing("field", missing_values=[])
        expected = {"all": [{"field": {"!=": ""}}]}
        assert result == expected


class TestGetValueOptions:
    """Tests for the get_value_options function."""

    def test_returns_none_for_nan(self):
        """Check NaN input returns None."""
        assert get_value_options(pd.NA) is None

    def test_parses_simple_options(self):
        """Check simple pipe-separated options are parsed correctly."""
        options = "1, Yes|2, No"
        result = get_value_options(options)
        assert result == {"1": "Yes", "2": "No"}

    def test_parses_options_with_spaces(self):
        """Check options with extra spaces are trimmed."""
        options = " 1 , Yes | 2 , No "
        result = get_value_options(options)
        assert result == {"1": "Yes", "2": "No"}

    def test_parses_options_with_commas_in_values(self):
        """Check options with commas in values are handled correctly."""
        options = "1, Yes, definitely|2, No, never"
        result = get_value_options(options)
        assert result == {"1": "Yes, definitely", "2": "No, never"}

    def test_lower_case_option(self):
        """Check lower_case parameter converts values to lowercase."""
        options = "1, Yes|2, No"
        result = get_value_options(options, lower_case=True)
        assert result == {"1": "yes", "2": "no"}


class TestReadListFile:
    """Tests for the read_list_file function."""

    def test_read_existing_list_file(self):
        """Check reading an existing list file returns a dictionary."""
        result = read_list_file("conditions_Symptoms")
        assert isinstance(result, dict)
        assert len(result) > 0

    def test_read_with_selected_filter(self):
        """Check selected=True filters to selected rows only."""
        result_all = read_list_file("conditions_Symptoms")
        result_selected = read_list_file("conditions_Symptoms", selected=True)
        # Selected should be a subset
        assert len(result_selected) <= len(result_all)


class TestAttrsWithUnits:
    """Tests for the attrs_with_units function."""

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

    def test_returns_tuple_of_rules_and_dataframe(self, arc_with_units):
        """Check attrs_with_units returns a tuple of (rules, filtered_df)."""
        rules, filtered_arc = attrs_with_units(arc_with_units)

        assert isinstance(rules, list)
        assert isinstance(filtered_arc, pd.DataFrame)

    def test_filters_out_unit_related_variables(self, arc_with_units):
        """Check unit-related variables are removed from the returned dataframe."""
        _, filtered_arc = attrs_with_units(arc_with_units)

        # Only 'other_var' should remain
        assert len(filtered_arc) == 1
        assert filtered_arc["Variable"].item() == "other_var"

    def test_creates_rule_per_unit_option(self, arc_with_units):
        """Check a rule is created for each unit-specific field."""
        rules, _ = attrs_with_units(arc_with_units)

        # Should create 2 rules (one for cm, one for in)
        assert len(rules) == 2
        attributes = [r["attribute"] for r in rules]
        assert "demog_height_cm" in attributes
        assert "demog_height_in" in attributes

    def test_rule_structure(self, arc_with_units):
        """Check the structure of generated unit rules."""
        rules, _ = attrs_with_units(arc_with_units)

        assert len(rules) >= 1
        rule = rules[0]

        # only one of demog_height_cm or demog_height will be present,
        # whichever is there must be non-null
        assert rule == {
            "attribute": "demog_height_cm",
            "if": {
                "all": [
                    {"demog_height_cm": {"!=": ""}, "can_skip": True},
                    {"demog_height": {"!=": ""}, "can_skip": True},
                    {"demog_height_units": 1},
                ]
            },
            "value_num": {
                "combinedType": "firstNonNull",
                "fields": [
                    {
                        "field": "demog_height_cm",
                        "apply": {"function": "values_strip_missing"},
                        "can_skip": True,
                    },
                    {
                        "field": "demog_height",
                        "apply": {"function": "values_strip_missing"},
                        "can_skip": True,
                    },
                ],
            },
            "attribute_unit": "cm",
            "attribute_status": {
                "combinedType": "firstNonNull",
                "fields": [
                    {
                        "field": "demog_height_cm",
                        "apply": {"function": "attribute_status_fill"},
                        "can_skip": True,
                    },
                    {
                        "field": "demog_height",
                        "apply": {"function": "attribute_status_fill"},
                        "can_skip": True,
                    },
                ],
            },
            "ref": "presentation",
        }

    def test_no_rules_when_no_unit_fields(self):
        """Check no rules are created when there are no unit fields."""
        arc = pd.DataFrame(
            {
                "Variable": ["name", "age", "status"],
                "Form": ["presentation", "presentation", "presentation"],
            }
        )
        rules, filtered_arc = attrs_with_units(arc)

        assert len(rules) == 0
        assert len(filtered_arc) == 3


class TestAttrsWithEnums:
    """Tests for the attrs_with_enums function."""

    def test_creates_rules_for_each_row(self):
        """Check a rule is created for each row in the dataframe."""
        arc = pd.DataFrame(
            {
                "Variable": ["var1", "var2"],
                "Answer Options": ["1, Yes|2, No", "1, Male|2, Female"],
                "Form": ["presentation", "presentation"],
            }
        )
        rules = attrs_with_enums(arc)
        assert len(rules) == 2

    def test_rule_structure(self):
        """Check the structure of generated rules."""
        arc = pd.DataFrame(
            {
                "Variable": ["test_var"],
                "Answer Options": ["1, Yes|2, No"],
                "Form": ["daily"],
            }
        )
        rules = attrs_with_enums(arc)
        assert len(rules) == 1

        assert rules[0] == {
            "attribute": "test_var",
            "value": {"field": "test_var", "values": {"1": "Yes", "2": "No"}},
            "attribute_status": {
                "field": "test_var",
                "apply": {"function": "attribute_status_fill"},
            },
            "ref": "daily",
        }


class TestAttrsWithCheckboxes:
    """Tests for the attrs_with_checkboxes function."""

    arc = pd.DataFrame(
        {
            "Variable": ["diagnosis_type"],
            "Answer Options": ["1, Clinical|2, Lab|3, Radiological"],
            "Form": ["outcome"],
        }
    )

    def test_creates_rule_per_option(self):
        """Check a rule is created for each checkbox option."""
        rules = attrs_with_checkboxes(self.arc)
        # 3 value rules + 4 missing code rules
        assert len(rules) == 3 + len(missing_codes)

    def test_field_naming_convention(self):
        """Check checkbox fields use the ___option naming convention."""
        rules = attrs_with_checkboxes(self.arc)
        # Check the value rules have correct field names
        value_rules = [r for r in rules if "value" in r]
        fields = [r["value"]["field"] for r in value_rules]
        assert "diagnosis_type___1" in fields
        assert "diagnosis_type___2" in fields

    def test_rule_structure(self):
        """Check checkbox fields use the ___option naming convention."""
        rules = attrs_with_checkboxes(self.arc)
        assert rules[0] == {
            "attribute": "diagnosis_type",
            "value": {"field": "diagnosis_type___1", "values": {"1": "Clinical"}},
            "attribute_status": "VAL",
            "ref": "outcome",
        }


class TestNumericAttrs:
    """Tests for the numeric_attrs function."""

    def test_creates_numeric_rules(self):
        """Check numeric rules are created with value_num field."""
        arc = pd.DataFrame(
            {
                "Variable": ["height", "weight"],
                "Form": ["presentation", "presentation"],
            }
        )
        rules = numeric_attrs(arc)
        assert len(rules) == 2
        for rule in rules:
            assert "value_num" in rule
            assert "attribute_status" in rule

    def test_numeric_rule_structure(self):
        """Check the structure of numeric rules."""
        arc = pd.DataFrame(
            {
                "Variable": ["nborn_hospdur"],
                "Form": ["neonate"],
            }
        )
        rules = numeric_attrs(arc)
        assert rules[0] == {
            "attribute": "nborn_hospdur",
            "value_num": {
                "field": "nborn_hospdur",
                "if": {
                    "all": [
                        {"nborn_hospdur": {"!=": "UNK"}},
                        {"nborn_hospdur": {"!=": "NI"}},
                        {"nborn_hospdur": {"!=": "NASK"}},
                        {"nborn_hospdur": {"!=": "NA"}},
                        {"nborn_hospdur": {"!=": ""}},
                    ]
                },
            },
            "attribute_status": {
                "field": "nborn_hospdur",
                "apply": {"function": "attribute_status_fill"},
            },
            "ref": "neonate",
        }


class TestGenericStrAttrs:
    """Tests for the generic_str_attrs function."""

    arc = pd.DataFrame(
        {
            "Variable": ["pres_consultdate", "withd_date"],
            "Form": ["presentation", "withdrawal"],
        }
    )

    def test_creates_string_rules(self):
        """Check string rules are created with value field."""
        rules = generic_str_attrs(self.arc)
        assert len(rules) == 2
        for rule in rules:
            assert "value" in rule
            assert "attribute_status" in rule

    def test_string_rule_structure(self):
        """Check the structure of string rules."""
        rules = generic_str_attrs(self.arc)
        rule = rules[0]
        assert rule == {
            "attribute": "pres_consultdate",
            "value": {
                "field": "pres_consultdate",
                "if": {
                    "all": [
                        {"pres_consultdate": {"!=": "UNK"}},
                        {"pres_consultdate": {"!=": "NI"}},
                        {"pres_consultdate": {"!=": "NASK"}},
                        {"pres_consultdate": {"!=": "NA"}},
                        {"pres_consultdate": {"!=": ""}},
                    ]
                },
            },
            "attribute_status": {
                "field": "pres_consultdate",
                "apply": {"function": "attribute_status_fill"},
            },
            "ref": "presentation",
        }


class TestFormDefinitions:
    """Tests for the form_definitions function."""

    def test_returns_dict(self):
        """Check form_definitions returns a dictionary."""
        result = form_definitions()
        assert isinstance(result, dict)

    def test_expected_forms_present(self):
        """Check expected form names are present."""
        result = form_definitions()

        arc = pd.read_csv("ARC.csv")
        expected_forms = arc["Form"].unique().tolist()

        for form in expected_forms:
            assert form in result, f"Missing form: {form}"

    def test_forms_have_phase(self):
        """Check all forms have a phase defined."""
        result = form_definitions()
        for form_name, form_def in result.items():
            assert "phase" in form_def, f"Form {form_name} missing 'phase'"

    def test_forms_have_date(self):
        """Check all forms have a date field defined."""
        result = form_definitions()
        for form_name, form_def in result.items():
            assert "date" in form_def, f"Form {form_name} missing 'date'"


class TestAttrsWithLists:
    """Tests for the attrs_with_lists function."""

    def test_creates_rules_with_for_loop(self, mock_read_list_file):
        """Check list rules use the 'for' construct for iteration."""
        arc = pd.DataFrame(
            {
                "Variable": ["comorbidities"],
                "List": "conditions_Comorbidities",
                "Form": ["presentation"],
            }
        )
        rules = attrs_with_lists(arc)
        # Should create 2 rules per variable (item and otherl2)
        assert len(rules) == 2
        assert rules == [
            {
                "attribute": "comorbidities",
                "value": {
                    "field": "comorbidities_{n}item",
                    "values": {"1": "Option A", "2": "Option B"},
                    "can_skip": True,
                },
                "attribute_status": {
                    "field": "comorbidities_{n}item",
                    "apply": {"function": "attribute_status_fill"},
                },
                "ref": "presentation",
                "for": {"n": {"range": [0, 4]}},
            },
            {
                "attribute": "comorbidities",
                "value": {
                    "field": "comorbidities_{n}otherl2",
                    "values": {"1": "Option A", "2": "Option B"},
                    "can_skip": True,
                },
                "attribute_status": {
                    "field": "comorbidities_{n}otherl2",
                    "apply": {"function": "attribute_status_fill"},
                },
                "ref": "presentation",
                "for": {"n": {"range": [0, 4]}},
            },
        ]


class TestAttrsWithUserlists:
    """Tests for the attrs_with_userlists function."""

    def test_creates_three_rules_per_variable(self, mock_read_list_file):
        """Check userlist creates 3 rules: main, otherl2, and otherl3."""
        arc = pd.DataFrame(
            {
                "Variable": ["test_userlist"],
                "List": "test_list",
                "Form": ["presentation"],
            }
        )
        rules = attrs_with_userlists(arc)
        # Should create 3 rules per variable (main, otherl2, otherl3)
        assert len(rules) == 3

    def test_rule_field_names(self, mock_read_list_file):
        """Check field names follow userlist naming convention."""
        mock_read_list_file.return_value = {"1": "Option A"}
        arc = pd.DataFrame(
            {
                "Variable": ["outcome_type"],
                "List": "outcome_list",
                "Form": ["outcome"],
            }
        )
        rules = attrs_with_userlists(arc)
        fields = [r["value"]["field"] for r in rules]
        assert "outcome_type" in fields
        assert "outcome_type_otherl2" in fields
        assert "outcome_type_otherl3" in fields

    def test_otherl3_has_can_skip(self, mock_read_list_file):
        """Check otherl2 and otherl3 rules have can_skip set."""
        mock_read_list_file.return_value = {"1": "Option A"}
        arc = pd.DataFrame(
            {
                "Variable": ["var"],
                "List": "list",
                "Form": ["presentation"],
            }
        )
        rules = attrs_with_userlists(arc)
        other_rules = [r for r in rules if "otherl" in r["value"]["field"]]
        for rule in other_rules:
            assert rule["value"].get("can_skip") is True


class TestAttrsWithMultilists:
    """Tests for the attrs_with_multilists function."""

    def test_creates_rules_for_each_list_item(self, mock_read_list_file):
        """Check multilist creates a rule for each list item."""
        mock_read_list_file.return_value = {"1": "Item A", "2": "Item B", "3": "Item C"}
        arc = pd.DataFrame(
            {
                "Variable": ["test_multilist"],
                "List": "test_list",
                "Form": ["presentation"],
            }
        )
        rules = attrs_with_multilists(arc)
        # 3 value rules + 4 missing codes + 2 other rules
        assert len(rules) == 9

        value_rules = [
            r for r in rules if "value" in r and r.get("attribute_status") == "VAL"
        ]
        assert len(value_rules) == 3


class TestParserGeneration:
    """
    Integration test for parser full parser generation. Checks the format against ADTL's
    specification
    """

    def test_parser_format(self, tmp_path):
        file = tmp_path / "test_parser"
        generate_parser("test", filename=file)
        adtl.validate_specification(f"{file}.toml")
