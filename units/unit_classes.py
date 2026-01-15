#!/usr/bin/env python
"""
unit_conversion_classes.py: Defines classes for units and unit conversions.
"""

from dataclasses import dataclass
from typing import Union, Optional, Callable, Literal
import numpy as np

Numeric = Union[float, int]


@dataclass
class BaseUnit:
    """
    Unit specific to a variable, e.g.
    BaseUnit(unit_label="µmol/L", unit_value=1, unit_field_name="labs_bilirubin_umoll")
    """
    unit_label: str
    unit_value: Optional[int]
    unit_field_name: Optional[str]


@dataclass
class ValueUnit:
    """Value and unit pair, e.g. height=ValueUnit(value=180, unit="cm")"""
    value: Numeric
    unit: Union[int, str]
    is_unit_label: Optional[bool] = True


@dataclass
class LinearConversion:
    multiplier: Numeric = 1.0
    offset: Numeric = 0.0

    def convert(self, value: Numeric):
        return self.multiplier * value + self.offset

    def convert_with_denominator(self, value: Numeric, denominator_value: Numeric):
        if np.isnan(denominator_value) or denominator_value == 0.0:
            return
        return self.multiplier * value / denominator_value + self.offset


@dataclass
class ConversionEntry:
    field_name: str
    units_field_name: str
    from_unit: BaseUnit
    to_unit: BaseUnit
    units_field_is_label: bool = True
    type: Literal["linear", "linear_with_denominator", "none"]
    note: Optional[str]

    def convert(self, value: Numeric, unit: Union[str, int]):
        if units_field_is_label and
