## ARC v1.1.3 (09 Oct 2025)

### Highlights
- Restructured **ARChetype Dengue CRF**  
- Introduced **recommended core outcomes for Dengue**  
- Separated **signs** and **symptoms** for improved consistency  

### Overview
ARC v1.1.3 delivers significant updates to support dengue research and harmonisation. The **ARChetype Dengue CRF** has been restructured, and a set of **recommended core outcomes for Dengue** has been introduced.

### Variable-Level Updates
- Restructured **Dengue ARChetype CRF**, aligning variable definitions with current WHO classification.  
- Introduced **recommended outcomes for Dengue**, enabling more standardised reporting across studies.  

## ARC v1.1.1 (02 Jul 2025)

### Overview
In ARC v1.1.1, variables in the ONSET & PRESENTATION section were updated to use the prefix pres_ instead of date_ to better reflect their meaning..

### Variable‑Level Updates
Prefix change in ONSET & PRESENTATION section: Variables previously using the date_ prefix were renamed to pres_ (e.g., date_adm, → pres_adm).

### Interoperability
Standardised term code lists have been revised to align with SNOMED‑CT, LOINC, and UMLS.

## ARC v1.1.0 (09 May 2025)

### Overview
ARC v1.1.0 delivers a substantial expansion of the data model, introduces a dedicated **Acute Respiratory Infection (ARI)** preset, and separates **signs** from **symptoms** to improve semantic clarity and analytic power.

### Column / Preset Changes
| Category | Details |
|---|---|
| **New presets / columns (1)** | `preset_ARChetype Syndromic CRF_ARI` **(new)** |
| **Renamed / (4)** | `preset_ARChetype CRF_Covid` → `preset_ARChetype Disease CRF_Covid`<br>`preset_ARChetype CRF_Dengue` → `preset_ARChetype Disease CRF_Dengue`<br>`preset_ARChetype CRF_Mpox` → `preset_ARChetype Disease CRF_Mpox`<br>`preset_ARChetype CRF_H5Nx` → `preset_ARChetype Disease CRF_H5Nx`|

### Variable‑Level Updates
- **Added variables**: 472 (e.g., `adsym_blurryvis`, `adsym_cough_type`).
- **Removed variables**: 303 (e.g., `adasses_bacsi_oth`, `adasses_lymph`).
- **Field‑type changes**: 84 variables.
- **List updates**: 652 variables.
- **Answer‑choice updates**: 68 variables.
- **Signs vs Symptoms**: Clinical **signs** are now represented by brand‑new `sign_*` variables and no longer stored in `sympt_*`, clearly separating objective observations from patient‑reported symptoms.

### Interoperability
Standardised term code lists have been revised to align with **SNOMED‑CT**, **LOINC**, and **UMLS**.

## ARC v1.0.4  (04 Mar 2025)

### Overview  
The changes in ARC v1.0.4 are designed to enhance the system’s usability and ensure a more coherent structure for data entry and analysis. Users are encouraged to review their workflows and adjust any scripts or processes to reflect the updated variable names and group structures.

### Key Updates  

**Renaming of Presets**  
   - The preset "disease" has been renamed to "ARChetype CRF" in the principal ARC CSV and in the lists.

**Updates to Answer Choices**  
   - The test_biospecimentype variable has been changed to a userlist.

---
