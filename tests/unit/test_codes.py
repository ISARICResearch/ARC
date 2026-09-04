# -- IMPORTS --

# -- Standard libraries --

# -- 3rd party libraries --
import pytest

# -- Internal libraries --
from arc.codes import (
    MISSING_ATTRIBUTE_STATUS_CODES,
    STATUS_CODES,
)


@pytest.mark.all
@pytest.mark.high
def test_missing_attribute_status_codes():
    assert MISSING_ATTRIBUTE_STATUS_CODES.UNKNOWN.value == "UNK"
    assert MISSING_ATTRIBUTE_STATUS_CODES.NO_INFORMATION.value == "NI"
    assert MISSING_ATTRIBUTE_STATUS_CODES.NOT_ASKED.value == "NASK"
    assert MISSING_ATTRIBUTE_STATUS_CODES.NOT_APPLICABLE.value == "NA"


@pytest.mark.all
@pytest.mark.high
def test_status_codes():
    assert STATUS_CODES.UNKNOWN.value == "UNK"
    assert STATUS_CODES.NO_INFORMATION.value == "NI"
    assert STATUS_CODES.NOT_ASKED.value == "NASK"
    assert STATUS_CODES.NOT_APPLICABLE.value == "NA"
    assert STATUS_CODES.VALUE.value == "VAL"
