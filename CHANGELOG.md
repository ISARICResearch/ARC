## ARC v1.1.0 (09 May 2025)

### Overview
ARC v1.1.0 delivers a substantial expansion of the data model, introduces a dedicated **Acute Respiratory Infection (ARI)** preset, and separates **signs** from **symptoms** to improve semantic clarity and analytic power.

### Column / Preset Changes
| Category | Details |
|---|---|
| **New presets / columns (1)** | `preset_ARChetype Syndromic CRF_ARI` **(new)** |
| **Renamed / (4)** | `preset_ARChetype CRF_Covid` → `preset_ARChetype Disease CRF_Covid`<br>`preset_ARChetype CRF_Dengue` → `preset_ARChetype Disease CRF_Dengue`<br>`preset_ARChetype CRF_Mpox` → `preset_ARChetype Disease CRF_Mpox`<br>`preset_ARChetype CRF_H5Nx` → `preset_ARChetype Disease CRF_H5Nx`|

### Variable‑Level Updates
- **Added variables**: 472 (e.g., `adsym_blurryvis`, `adsym_cough_type`).
- **Removed variables**: 303 (e.g., `adasses_bacsi_oth`, `adasses_lymph`).
- **Field‑type changes**: 84 variables.
- **List updates**: 652 variables.
- **Answer‑choice updates**: 68 variables.
- **Signs vs Symptoms**: Clinical **signs** are now represented by brand‑new `sign_*` variables and no longer stored in `sympt_*`, clearly separating objective observations from patient‑reported symptoms.

### Interoperability
Standardised term code lists have been revised to align with **SNOMED‑CT**, **LOINC**, and **UMLS**.

---
