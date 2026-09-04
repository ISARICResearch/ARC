from __future__ import annotations


__all__ = [
    "MISSING_ATTRIBUTE_STATUS_CODES",
    "STATUS_CODES",
]


# -- IMPORTS --

# -- Standard libraries --
from enum import Enum, unique

# -- 3rd party libraries --
from aenum import extend_enum

# -- Internal libraries --


@unique
class MISSING_ATTRIBUTE_STATUS_CODES(Enum):
    """An enum of constants representing missing attribute status codes."""

    # Unknown
    UNKNOWN = "UNK"

    # No information
    NO_INFORMATION = "NI"

    # Not asked
    NOT_ASKED = "NASK"

    # Not applicable
    NOT_APPLICABLE = "NA"

    @classmethod
    def asdict(cls) -> dict[str, str]:
        return {member.name: member.value for member in list(cls)}

    @classmethod
    def astuple(cls) -> tuple[str]:
        return tuple(member.value for member in list(cls))


@unique
class STATUS_CODES(Enum):
    """An enum of constants representing all status codes, including missing attribute status codes."""

    # Value [?]
    VALUE = "VAL"

    @classmethod
    def asdict(cls) -> dict[str, str]:
        return {member.name: member.value for member in list(cls)}

    @classmethod
    def astuple(cls) -> tuple[str]:
        return tuple(member.value for member in list(cls))


# A global step here to extend the status codes with the missing status codes.
for member in MISSING_ATTRIBUTE_STATUS_CODES.__members__.values():
    extend_enum(STATUS_CODES, member.name, member.value)
