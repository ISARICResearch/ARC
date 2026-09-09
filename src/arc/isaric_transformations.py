from __future__ import annotations


__all__ = [
    "attribute_status_fill",
    "values_strip_missing",
]


# -- IMPORTS --

# -- Standard libraries --

# -- 3rd party libraries --

# -- Internal libraries --
from arc.codes import (
    MISSING_ATTRIBUTE_STATUS_CODES,
    STATUS_CODES,
)


def attribute_status_fill(field: str) -> str | None:
    """:py:class:`str` or :py:class:`NoneType` : Infer attribute status if it is missing.

    Parameters
    ----------
    field : str
        Attribute status field.

    Returns
    -------
    str or None
        The original status field if it is one of the values:

        * ``'UNK'`` - unknown
        * ``'NI'`` - no information
        * ``'NASK'`` - not asked
        * ``'NA'`` - not applicable

        or ``'VAL'`` if it is non-null but different from the above, otherwise
        ``None``.

    Examples
    --------
    >>> attribute_status_fill("UNK")
    'UNK'
    >>> attribute_status_fill("NI")
    'NI'
    >>> attribute_status_fill("NASK")
    'NASK'
    >>> attribute_status_fill("NA")
    'NA'
    >>> attribute_status_fill("XYZ")
    'VAL'
    >>> attribute_status_fill(None)
    >>>
    """  # noqa : E501
    if field is None:
        return None

    match field:
        case (
            MISSING_ATTRIBUTE_STATUS_CODES.UNKNOWN.value
            | MISSING_ATTRIBUTE_STATUS_CODES.NO_INFORMATION.value
            | MISSING_ATTRIBUTE_STATUS_CODES.NOT_ASKED.value
            | MISSING_ATTRIBUTE_STATUS_CODES.NOT_APPLICABLE.value
        ):
            return field
        case _:
            return STATUS_CODES.VALUE.value


def values_strip_missing(field: str) -> str | None:
    """:py:class:`str` or :py:class:`NoneType` : Strip missing attribute status field.

    Parameters
    ----------
    field : str
        Attribute status field.

    Returns
    -------
    str or None
        Null if it is one of the values:

        * ``'UNK'`` - unknown
        * ``'NI'`` - no information
        * ``'NASK'`` - not asked
        * ``'NA'`` - not applicable

        and ``None`` otherwise.

    Examples
    --------
    >>> values_strip_missing("UNK")
    >>>
    >>> values_strip_missing("NI")
    >>>
    >>> values_strip_missing("NASK")
    >>>
    >>> values_strip_missing("NA")
    >>>
    >>> values_strip_missing("XYZ")
    'XYZ'
    >>> values_strip_missing(None)
    >>>
    """  # noqa : E501

    match field:
        case (
            MISSING_ATTRIBUTE_STATUS_CODES.UNKNOWN.value
            | MISSING_ATTRIBUTE_STATUS_CODES.NO_INFORMATION.value
            | MISSING_ATTRIBUTE_STATUS_CODES.NOT_ASKED.value
            | MISSING_ATTRIBUTE_STATUS_CODES.NOT_APPLICABLE.value
        ):
            return None
        case _:
            return field


if __name__ == "__main__":  # pragma: no cover
    # Doctest the module from the project root using
    #
    #     python3 -m doctest -v src/isaricanalytics/isaric_transformations.py  # noqa : E501
    #
    import doctest

    doctest.testmod()
