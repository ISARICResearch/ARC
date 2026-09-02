# -- IMPORTS --

# -- Standard libraries --

# -- 3rd party libraries --
import pytest

# -- Internal libraries --
from arc.isaric_transformations import (
    attribute_status_fill,
    values_strip_missing,
)


@pytest.mark.high
@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("UNK", "UNK"),
        ("NI", "NI"),
        ("NASK", "NASK"),
        ("NA", "NA"),
        ("something else", "VAL"),
    ],
)
def test_attribute_status_fill(value, expected):
    assert attribute_status_fill(value) == expected


@pytest.mark.critical
@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("UNK", None),
        ("NI", None),
        ("NASK", None),
        ("NA", None),
        ("something else", "something else"),
    ],
)
def test_values_strip_missing(value, expected):
    assert values_strip_missing(value) == expected
