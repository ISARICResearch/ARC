#!/usr/bin/env python
"""
unit_conversion_classes.py: Defines classes for units and unit conversions.

This is for one-way unit conversions based on the ARC unit_conversion JSON file.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Union, Optional, List, Dict, Self

import pandas as pd
import numpy as np
import json
from jsonschema import Draft7Validator

Numeric = Union[float, int]


class ValidationError(Exception):
    pass


class SchemaValidationError(Exception):
    pass


@dataclass
class BaseUnit:
    unit_label: str
    unit_value: Optional[int]
    unit_field_name: Optional[str]


@dataclass
class BaseUnitCollection:
    units: List[BaseUnit]

    def __post_init__(self):
        attr_lists = {
            "unit_label": [unit.unit_label for unit in self.units],
            "unit_values": [
                unit.unit_value for unit in self.units if unit.unit_value is not None
            ],
            "unit_field_names": [
                unit.unit_field_name
                for unit in self.units
                if unit.unit_field_name is not None
            ],
        }
        for item in attr_lists:
            if len(set(attr_lists[item])) != len(attr_lists[item]):
                raise ValidationError(
                    f"units in {self.units} have non-unique attributes"
                )

    def get_unit_from_unit_label(self, unit_label: str) -> BaseUnit:
        return [unit for unit in self.units if unit.unit_label == unit_label][0]

    def get_unit_from_unit_value(self, unit_value: str) -> BaseUnit:
        return [unit for unit in self.units if unit.unit_value == unit_value][0]


@dataclass
class LinearConversion:
    multiplier: Numeric = 1.0
    offset: Numeric = 0.0

    def convert(self, value: Union[Numeric, pd.Series]):
        return self.multiplier * value + self.offset

    def convert_with_denominator(
        self,
        value: Union[Numeric, pd.Series],
        denominator_value: Union[Numeric, pd.Series],
    ):
        if isinstance(denominator_value, Numeric) and (
            np.isnan(denominator_value) or denominator_value == 0.0
        ):
            return np.nan

        converted_value = self.multiplier * value / denominator_value + self.offset

        if isinstance(denominator_value, pd.Series):
            converted_value.replace([np.inf, -np.inf], np.nan, inplace=True)
        return converted_value


@dataclass
class ConversionRule:
    from_unit: BaseUnit
    to_unit: BaseUnit
    conversion: Optional[LinearConversion]
    note: Optional[str] = None
    requires_denominator: bool = False
    denominator_field_name: Optional[str] = None

    @classmethod
    def from_dict(
        cls, item: Dict[str, Union[str, Numeric]], units: BaseUnitCollection
    ) -> Self:
        conversion_type = item.get("type", "none")

        conversion = None
        if conversion_type in ["linear", "linear_with_denominator"]:
            conversion = LinearConversion(
                multiplier=item["multiplier"], offset=item["offset"]
            )

        requires_denominator = conversion_type == "linear_with_denominator"
        denominator_field_name = (
            item["denominator_field_name"]
            if conversion_type == "linear_with_denominator"
            else None
        )

        conversion_rule = cls(
            from_unit=units.get_unit_from_unit_label(item["from_unit"]),
            to_unit=units.get_unit_from_unit_label(item["to_unit"]),
            conversion=conversion,
            note=item.get("note", None),
            requires_denominator=requires_denominator,
            denominator_field_name=denominator_field_name,
        )
        return conversion_rule


@dataclass
class ConversionEntry:
    field_name: str
    units_field_name: str
    units: List[BaseUnit]
    conversion_rules: List[ConversionRule]
    preferred_unit: BaseUnit

    def matches(self, other: Self, attrs: Optional[List[str]] = None) -> bool:
        if not attrs:
            attrs = list(self.__annotations__.keys())
        return all(
            hasattr(self, a) == hasattr(other, a)
            and getattr(self, a) == getattr(other, a)
            for a in attrs
        )

    def __post_init__(self):
        self._conversion_rule_registry = {
            (rule.from_unit.unit_label, rule.to_unit.unit_label): rule
            for rule in self.conversion_rules
        }

    def get_rule(self, from_unit_label: str, to_unit_label: str):
        return self._conversion_rule_registry.get(
            (from_unit_label, to_unit_label), None
        )

    @classmethod
    def from_dict(cls, item: Dict[str, Union[str, List, Dict]]) -> Self:
        units = BaseUnitCollection(
            [
                BaseUnit(
                    unit_label=unit_raw["unit_label"],
                    unit_value=unit_raw["unit_value"],
                    unit_field_name=unit_raw.get("unit_field_name", None),
                )
                for unit_raw in item["units"]
            ]
        )

        conversion_rules = [
            ConversionRule.from_dict(item=conversion_rule_raw, units=units)
            for conversion_rule_raw in item["conversion_rules"]
        ]

        conversion_entry = cls(
            field_name=item["field_name"],
            units_field_name=item["units_field_name"],
            units=units,
            conversion_rules=conversion_rules,
            preferred_unit=units.get_unit_from_unit_label(item["preferred_unit"]),
        )
        return conversion_entry


@dataclass
class ConversionRegistry:
    conversion_entries: Dict[str, ConversionEntry] = field(default_factory=dict)
    verbose: bool = False

    def load_and_validate_json(
        self, path: Union[str, Path], schema_path: Union[str, Path]
    ):
        with Path(schema_path).open("r", encoding="utf-8") as f:
            schema = json.load(f)

        Draft7Validator.check_schema(schema)

        with Path(path).open("r", encoding="utf-8") as f:
            json_data = json.load(f)

        validator = Draft7Validator(schema)
        errors = list(validator.iter_errors(json_data))

        if errors:
            messages = []
            for err in sorted(errors, key=lambda e: e.path):
                path = "/".join(map(str, err.absolute_path)) or "<root>"
                msg = f"{path}: {err.message}"

                if err.context:
                    submsgs = "; ".join(sub.message for sub in err.context)
                    msg += f" (details: {submsgs})"

                messages.append(msg)

            print(
                "Data does not validate against schema:\n"
                + "\n".join(f"- {m}" for m in messages)
            )
            raise SchemaValidationError

        field_names = [field["field_name"] for field in json_data]
        if len(set(field_names)) != len(field_names):
            raise ValidationError("JSON entries must be unique for field 'field_name'")

        return json_data

    def load_from_json(
        self,
        path: Union[str, Path],
        schema_path: Union[str, Path],
    ) -> Self:
        json_data = self.load_and_validate_json(path, schema_path)

        self.conversion_entries = {
            field["field_name"]: ConversionEntry.from_dict(field) for field in json_data
        }
        return self

    def get_rule(
        self,
        field_name: str,
        from_unit: Union[int, str],
        to_unit: Optional[Union[int, str]] = None,
        is_unit_label: bool = True,
    ) -> Optional[ConversionEntry]:
        entry = self.conversion_entries.get(field_name, None)
        if entry is not None:
            if not is_unit_label:
                from_unit = entry.units.get_unit_from_unit_value(
                    from_unit_value=from_unit
                )
                to_unit = entry.units.get_unit_from_unit_value(from_unit_value=to_unit)
            return entry.get_rule(from_unit_label=from_unit, to_unit_label=to_unit)

    def get_unit_field_name(self, field_name: str):
        entry = self.conversion_entries.get(field_name, None)
        if entry is not None:
            return entry.units_field_name


@dataclass
class UnitConverter:
    conversion_registry: ConversionRegistry
    is_unit_labels: Union[bool, Dict[str, bool]] = True
    verbose: bool = False

    def __post_init__(self):
        """Add a registry for is_unit_labels for all fields"""
        if isinstance(self.is_unit_labels, bool):
            self._is_unit_labels_registry = {
                field_name: self.is_unit_labels
                for field_name in self.conversion_registry.conversion_entries.keys()
            }

        if isinstance(self.is_unit_labels, dict):
            self._is_unit_labels_registry = {
                field_name: (
                    self.is_unit_labels[field_name]
                    if field_name not in self.is_unit_labels.keys()
                    else True
                )
                for field_name in self.conversion_registry.conversion_entries.keys()
            }

    def convert(
        self,
        field_name: str,
        value: Numeric,
        from_unit: Union[str, int],
        to_unit: Union[str, int],
        denominator_value: Optional[Numeric] = None,
    ) -> Dict[str, Union[str, Numeric]]:
        rule = self.conversion_registry.get_rule(
            field_name=field_name,
            from_unit=from_unit,
            to_unit=to_unit,
            is_unit_label=self._is_unit_labels_registry[field_name],
        )

        if not rule:
            if from_unit == to_unit:
                note = "Identity (from_unit = to_unit)"
            if from_unit != to_unit:
                note = "No match for the unit in the unit conversion registry"
            if self.verbose:
                print(note)
            return {"value": value, "unit": from_unit, "converted": False, "note": note}

        if not rule.conversion:
            return {
                "value": value,
                "unit": from_unit,
                "converted": False,
                "note": rule.note,
            }

        if rule.requires_denominator:
            if denominator_value is None:
                if self.verbose:
                    print(
                        "Conversion requires a denominator, denominator value not provided"
                    )
                return {
                    "value": value,
                    "unit": from_unit,
                    "converted": False,
                    "note": rule.note,
                }

            converted_value = rule.conversion.convert_with_denominator(
                value=value, denominator_value=denominator_value
            )

        if not rule.requires_denominator:
            converted_value = rule.conversion.convert(value=value)

        return {
            "value": converted_value,
            "unit": to_unit,
            "converted": True,
            "note": rule.note,
        }

    def convert_series(
        self,
        values: pd.Series,
        from_units: pd.Series,
        to_unit: Union[str, int],
        denominator_values: Optional[Dict[str, pd.Series]] = None,
    ):
        field_name = values.name

        if not values.index.equals(from_units.index):
            raise ValidationError(
                "pd.Series values and from_units must have same index"
            )

        converted_values = pd.Series(index=values.index, dtype=float).rename(
            values.name
        )
        to_units = pd.Series(index=values.index, dtype=from_units.dtype).rename(
            from_units.name
        )
        converted_bool = pd.Series(False, index=values.index, dtype=bool).rename(
            "converted"
        )
        notes = pd.Series(index=values.index, dtype=object).rename("notes")

        for from_unit, idx in from_units.groupby(from_units).groups.items():
            rule = self.conversion_registry.get_rule(
                field_name=field_name,
                from_unit=from_unit,
                to_unit=to_unit,
                is_unit_label=self._is_unit_labels_registry[field_name],
            )

            if rule is None:
                converted_values.loc[idx] = values.loc[idx]
                to_units.loc[idx] = from_units.loc[idx]
                notes.loc[idx] = "No conversion"
            else:
                notes.loc[idx] = rule.note
                if (
                    rule.requires_denominator
                    and denominator_values.get(from_unit, None) is None
                ):
                    raise ValidationError(
                        f"denominator_values must contain key {from_unit}"
                    )

                if rule.requires_denominator:
                    converted_values.loc[idx] = (
                        rule.conversion.convert_with_denominator(
                            value=values.loc[idx],
                            denominator_value=denominator_values[from_unit].loc[idx],
                        )
                    )
                    to_units.loc[idx] = to_unit
                    converted_bool.loc[idx] = from_units.loc[idx].eq(to_units.loc[idx])
                else:
                    converted_values.loc[idx] = rule.conversion.convert(
                        value=values.loc[idx],
                    )
                    to_units.loc[idx] = to_unit
                    converted_bool.loc[idx] = from_units.loc[idx].eq(to_units.loc[idx])

        return {
            "values": converted_values,
            "units": to_units,
            "converted": converted_bool,
            "notes": notes,
        }

    def convert_dataframe(self, dataframe: pd.DataFrame, inplace: bool = False):
        if not inplace:
            dataframe = dataframe.copy()

        entries = [
            self.conversion_registry.conversion_entries[field_name]
            for field_name in dataframe.columns
            if field_name in self.conversion_registry.conversion_entries.keys()
        ]

        kwargs_list = [
            {
                "values": dataframe[entry.field_name],
                "from_units": dataframe[entry.units_field_name],
                "to_unit": entry.preferred_unit.unit_label,
                "denominator_values": {
                    x.from_unit.unit_label: dataframe[x.denominator_field_name]
                    for x in entry.conversion_rules
                    if x is not None and x.denominator_field_name in dataframe.columns
                },
            }
            for entry in entries
            if entry.units_field_name in dataframe.columns
        ]

        for kwargs in kwargs_list:
            converted_series = self.convert_series(**kwargs)
            dataframe[converted_series["values"].name] = converted_series["values"]
            dataframe[converted_series["units"].name] = converted_series["units"]

        if not inplace:
            return dataframe


def convert_units(
    df: pd.DataFrame,
    unit_conversion_path: Union[str, Path],
    unit_conversion_schema_path: Union[str, Path],
    is_unit_labels: Union[bool, Dict[str, bool]] = True,
    inplace: bool = False,
):
    cr = ConversionRegistry().load_from_json(
        path=unit_conversion_path,
        schema_path=unit_conversion_schema_path,
    )
    uc = UnitConverter(conversion_registry=cr, is_unit_labels=is_unit_labels)
    return uc.convert_dataframe(dataframe=df, inplace=inplace)


if __name__ == "__main__":
    cr = ConversionRegistry().load_from_json(
        path="units/unit_conversion.json",
        schema_path="units/unit_conversion.schema.json",
    )

    df = pd.DataFrame(
        [[150, "cm"], [160, "cm"], [60, "in"]],
        columns=["demog_height", "demog_height_units"],
    )
    uc = UnitConverter(conversion_registry=cr, is_unit_labels=True)
    uc.convert(field_name="demog_height", value=60, from_unit="in", to_unit="cm")
    uc.convert_series(
        values=df["demog_height"], from_units=df["demog_height_units"], to_unit="cm"
    )
    uc.convert_dataframe(dataframe=df, inplace=False)

    converted_df = convert_units(
        df=df,
        unit_conversion_path="units/unit_conversion.json",
        unit_conversion_schema_path="units/unit_conversion.schema.json",
        is_unit_labels=True,
        inplace=False,
    )
