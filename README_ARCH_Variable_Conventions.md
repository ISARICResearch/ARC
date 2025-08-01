
# ARCH Variable Naming Conventions

This document describes the variable naming conventions used in the ARCH system, which support consistent structure, clarity, and integration with data collection and harmonization tools like ARC and BRIDGE.

---

## 1. General Naming Structure

Variable names follow a modular convention using underscores (`_`) to separate components:

```
[domain]_[topic]_[detail]
```

- `domain`: thematic area (e.g., `demog`, `inter`, `labs`)
- `topic`: clinical concept (e.g., `sex`, `suppleo2`, `glucose`)
- `detail`: optional element used to indicate format, type, or follow-up

### Example:
- `demog_occupation_oth`: Open text field specifying occupation if "Other" was selected
- `inter_nasalprongs_dur`: Duration (in days/hours) of nasal prong oxygen therapy

---

## 2. Hierarchy Depth

Variable names contain varying numbers of underscores to reflect their specificity:

| Number of Underscores | Meaning                                     |
|------------------------|---------------------------------------------|
| 1 (`a_b`)              | General field (e.g., `pres_date`)           |
| 2 (`a_b_c`)            | Component of a broader concept              |
| 3+                    | Further detail or sub-field (less common)   |

---

## 3. Common Suffixes

Below are common suffixes that reflect variable function or logic. All examples are real variables from the dataset:

| Suffix   | Description                                               | Examples                                          |
|----------|-----------------------------------------------------------|---------------------------------------------------|
| `_oth`   | Text field for specifying “Other”                         | `demog_sex_oth`, `demog_gender_oth`               |
| `_type`  | Specifies type or category of a condition                 | `comor_liverdisease_type`, `comor_tuberculos_type`|
| `_date`  | Date field                                                | `inclu_consent_date`, `readm_prev_date`           |
| `_spec`  | Specification detail for a selected category              | `expo14_typeoth_spec`, `adsym_neurologic_spec`    |
| `_dur`   | Duration of an intervention or event                      | `inter_facemask_dur`, `inter_suppleo2_dur`        |
| `_ongoing` | Indicates whether a treatment/condition is ongoing      | `inter_nasalprongs_ongoing`, `inter_facemask_ongoing` |
| `_num`   | Numerical count                                            | `lesion_head_num`, `readm_prev_num`               |
| `_site`  | Site or anatomical location                               | `adsym_skinrash_site`, `readm_prev_site`          |
| `_mgdl`  | Lab measurement in mg/dL                                  | `labs_glucose_mgdl`, `labs_bilirubin_mgdl`        |
| `_pcnt`  | Percent value                                              | `vital_fio2spo2_pcnt`, `comor_hba1c_pcnt`         |
| `_yn`    | Yes/No binary question                                    | `expo14_yn`, `test_yn`                            |

---

## 4. Section Mapping

Each variable is linked to a logical section (e.g., INCLUSION CRITERIA, DEMOGRAPHICS, INTERVENTIONS) that determines its role in the clinical case report form (CRF). This section assignment ensures that CRFs are structured clearly and reproducibly.

---

## 5. Branching Logic Patterns

Suffixes like `_oth`, `_spec`, `_ongoing`, `_dur`, and `_site` often imply **conditional visibility**, depending on the answer to a parent field:

- `expo14_yn = Yes` → show `expo14_typeoth_spec`
- `inter_suppleo2_ongoing = Yes` → may show `inter_suppleo2_dur`
- `demog_gender = Other` → show `demog_gender_oth`

These dependencies must be respected in CRF tools like BRIDGE to ensure logical flow and data consistency.


---

## 6. Variable Types

ARCH uses various variable types to capture structured, semi-structured, and free-text data. Each type implies specific data constraints and rendering logic:

| Type            | Description                                                                 |
|-----------------|-----------------------------------------------------------------------------|
| `text`          | Free-text entry, typically short answers                                    |
| `user_list`     | A list of options drawn from an external source, modifiable by the user     |
| `radio`         | Single choice from a set of predefined options                              |
| `checkbox`      | Multiple selections allowed from a list                                     |
| `list`          | Similar to `radio`, may be used for dropdown selection                      |
| `multi_list`    | Like `user_list`, but allows multiple selections                            |
| `date_dmy`      | Date field (day-month-year format)                                          |
| `datetime_dmy`  | Date and time field in DMY format                                           |
| `number`        | Numeric input, often with `Minimum`/`Maximum` constraints                   |
| `calc`          | Calculated field (derived from other variables)                             |
| `file`          | Field for file upload                                                       |
| `notes`         | Long free-text, typically for comments or additional detail                 |
| `descriptive`   | Static text or headers, not a question or input field                       |

---

## 7. Unit-Selectable Variables

Some numeric variables are associated with **"Select Units"** fields. These allow users to specify the measurement unit alongside the value.

### Common Unit Systems:

| Concept         | Example Units                    |
|-----------------|----------------------------------|
| Height          | cm, inches                       |
| Weight          | kg, pounds                       |
| Temperature     | °C, °F                           |
| Blood pressure  | mmHg                             |
| Oxygen          | %FiO₂, mmHg                      |

### Structure:
These are typically implemented as **paired fields**, for example:

- `demog_weight` → select unit (radio/dropdown)
- `demog_weight_kg`, `demog_weight_lb` → numeric input fields (conditional on unit)

Such fields allow flexibility across settings while preserving data harmonization. The recommended unit (standardized) is often **pre-selected** via presets in BRIDGE.
