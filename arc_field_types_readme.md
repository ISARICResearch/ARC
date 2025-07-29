# ARC Special Field Types Documentation

This document provides a detailed explanation of the special field types used within the ISARIC ARC (Analysis and Research Compendium) framework to support dynamic, reusable, and semantically structured Case Report Forms (CRFs). These field types extend beyond standard REDCap functionality to enable complex logic, repeated entries, hierarchical lists, and units management.

---

## Overview: REDCap-Compatible Extensions

Most fields in ARC use standard REDCap field types such as `text`, `radio`, `checkbox`, `dropdown`, `calc`, and `notes`. However, to support enhanced functionality and automation, ARC introduces several **special field types**:

- `user_list`
- `list`
- `multi_list`
- `select units`

These are interpreted and transformed into REDCap-compatible fields when generating a data dictionary.

---

## 1. `user_list`

### Description

A `user_list` is a structured field type that references a predefined list of options from an external file, where the user has marked some values as *selected* (i.e., shown as default radio options) and others as optional extensions.

### Example

Variable: `inclu_disease`\
List source: `Lists/inclusion/Diseases.csv`

### Transformation

- `radio` field with *Selected = 1* options
- `dropdown` (`otherl2`) to show extended values if user selects "Other"
- `text` field (`otherl3`) to specify unlisted values

### Derived Variables

- `inclu_disease_otherl2`
- `inclu_disease_otherl3`

---

## 2. `list`

### Description

`list` is used for fields that support **multiple repeated selections** from a predefined value set.

### Example

Used for treatments, comorbidities, or exposures where multiple entries may apply.

### Transformation

- Multiple `dropdown` entries: `0item`, `1item`, ..., `nitem`
- Each followed by:
  - `text` field for "Other" entries: `0otherl2`, etc.
  - `radio` field asking if there's an additional entry: `0addi`, etc.

### Derived Variables

- `treat_drug_0item`, `treat_drug_1item`, ...
- `treat_drug_0otherl2`
- `treat_drug_0addi`

---

## 3. `multi_list`

### Description

`multi_list` represents a multiselect list where several options can be checked simultaneously.

### Example

Used for symptoms, diagnoses, or any scenario where multiple answers may apply.

### Transformation

- A `checkbox` group with selected options
- If value `88` (Other) is selected:
  - Show `dropdown` with less common values (`otherl2`)
  - Show `text` field for specification (`otherl3`)

### Derived Variables

- `symptoms`: base checkbox
- `symptoms_otherl2`, `symptoms_otherl3`

---

## 4. `select units`

### Description

This is a structural pattern rather than an explicit type. Fields requiring both a **value** and a **unit** are inferred from questions containing phrases like "(select units)".

### Detection

- Identified by parsing the `Question` text
- Applies to variables that appear in multiple unit-specific variants

### Transformation

- One `text` field for the value (numeric)
- One `radio` field for unit selection

### Derived Variables

- `vital_temp` (numeric input)
- `vital_temp_units` (unit selector)

---

## Naming Conventions

| Purpose                                            | Pattern                 |
| -------------------------------------------------- | ----------------------- |
| Repeated entries (`list`)                          | `<base>_0item`, `1item` |
| Additional question                                | `<base>_0addi`          |
| Other dropdown (`list`, `user_list`, `multi_list`) | `<base>_otherl2`        |
| Free-text other                                    | `<base>_otherl3`        |
| Units field (`select units`)                       | `<base>_units`          |

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
- The transformation is handled automatically during CRF export
- These structures support modular, scalable, and interoperable CRFs

