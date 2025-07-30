# ARC Special Field Types Documentation

This document provides a detailed explanation of the special field types used within the ISARIC ARC (Analysis and Research Compendium) framework to support dynamic, reusable, and semantically structured Case Report Forms (CRFs). These field types extend beyond standard REDCap functionality to enable complex logic, repeated entries, hierarchical lists, and units management.

---

## Overview: REDCap-Compatible Extensions

Most fields in ARC use standard REDCap field types such as `text`, `radio`, `checkbox`, `dropdown`, `calc`, and `notes`. However, to support enhanced functionality and automation, ARC introduces several **special field types**:

- `user_list`
- `list`
- `multi_list`
-  Blank field (`select units` in Question)

These are interpreted and transformed into REDCap-compatible fields when generating a data dictionary.

---

## 1. `user_list`

### Description
A  is a structured field type that references a predefined list of options from an external file, where the user has marked some values as *selected* or *preset_* (i.e., shown as default radio options) and others as optional extensions.
A `user_list` is a structured field type that references a predefined list of options from an external file, which the user can modify to include the pertinent options for their particular context. This links to specific functionality in [ISARIC BRIDGE](https://bridge.isaric.org/), where users can select the options they wish to include for a given question. Additionally, each version of ARC includes  pre-selected options in the form of presets, which are shown by default, while other options remain available as optional extensions.

### Example
Variable: `inclu_disease`\
List source: [Lists/inclusion/Diseases.csv](https://github.com/ISARICResearch/ARC/blob/main/Lists/inclusion/Diseases.csv)

### BRIDGE Transformation
- `radio` field with checked values as options: if the number of checked values < 15
- `dropdown` field with checked values as options: if the number of checked values  >= 15
- `dropdown` (`otherl2`) to show extended values if user selects "Other"
- `text` field (`otherl3`) to specify unlisted values

### Derived Variables
- `inclu_disease_otherl2`
- `inclu_disease_otherl3`

---

## 2. `list`

### Description
`list` is used for fields that support **multiple repeated selections** from a predefined value set. Like `user_list`, the options for `list` fields are loaded from external CSV files in the ARC GitHub repository.

### Example
Variable: `comor_unlisted`\
List source: [Lists/conditions/Comorbidities.csv](https://github.com/ISARICResearch/ARC/blob/main/Lists/conditions/Comorbidities.csv)

### Transformation
- Multiple `dropdown` entries: `0item`, `1item`, ..., `nitem`
- Each followed by:
  - `text` field for "Other" entries: `0otherl2`, etc.
  - `radio` field asking if there's an additional entry: `0addi`, etc.

### Derived Variables
- `comor_unlisted_0item`, `comor_unlisted_1item`, ...
- `comor_unlisted_0otherl2`
- `comor_unlisted_0addi`

---

## 3. `multi_list`

### Description
`multi_list` represents a multiselect list where several options can be checked simultaneously. Like `list`, its options are also loaded from external CSV files.

### Example
Variable: `demog_race`\
List source: [Lists/demographics/Race.csv](https://github.com/ISARICResearch/ARC/blob/main/Lists/demographics/Race.csv)

### Transformation
- A `checkbox` group with selected options
- If value `88` (Other) is selected:
  - Show `dropdown` with less common values (`otherl2`)
  - Show `text` field for specification (`otherl3`)

### Derived Variables
- `demog_race`: base checkbox
- `demog_race_otherl2`, `demog_race_otherl3`

---

## 4. `select units`

### Description

This is a structural pattern rather than an explicit type. It applies to clinical measurements (e.g., height, weight, temperature) that may be recorded in more than one unit (e.g., cm/in, kg/lb, °C/°F). The core variable usually includes "(select units)" in its question text and is linked to two or more variants defined with specific units tha share teh same prefix.

### Example

- Base question: `demog_height` → "Height (select units)"
- Variants:
  - `demog_height_cm`: numeric field in centimeters
  - `demog_height_in`: numeric field in inches

- Base question: `demog_weight` → "Weight (select units)"
- Variants:
  - `demog_weight_kg`: numeric field in kilograms
  - `demog_weight_lb`: numeric field in pounds

### Transformation

- A unified `text` field (e.g., `demog_height`) for the value
- A companion `radio` field (e.g., `demog_height_units`) to select which unit is used

### Derived Variables

- `demog_height`: unified height input
- `demog_height_units`: unit selector (e.g., cm/in)
- `demog_weight`: unified weight input
- `demog_weight_units`: unit selector (e.g., kg/lb)

This approach reduces redundancy, improves clarity, and ensures that unit selection is explicit and standardized.

Moreover, this design enables CRF customization in the BRIDGE tool: users can choose which unit(s) to display when configuring the form for a specific data collection setting. This allows alignment with local clinical practices (e.g., countries preferring cm/in or kg/lb) while maintaining a unified structure in the backend.

---

---

## Visual Summary

Below is a simplified flowchart of how each ARC type expands into REDCap-compatible fields:

```
user_list
  └── radio field (Selected options)
      └── dropdown (Other options)
          └── text (Specify other)

list
  └── dropdown_0item
      ├── text_0otherl2
      └── radio_0addi

multi_list
  └── checkbox (main options)
      ├── dropdown_otherl2
      └── text_otherl3

select units
  ├── text (numeric value)
  └── radio (unit selector)
```

---

## Notes
- Lists are stored in the ARC GitHub repo under `/Lists/...`
- The transformation is handled automatically during CRF export from BRIDGE
- These structures support modular, scalable, and interoperable CRFs
