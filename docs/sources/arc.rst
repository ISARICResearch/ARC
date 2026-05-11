.. _arc-schema:

==========
ARC Schema
==========

The ARC schema is made available as a machine-readable `CSV <https://github.com/ISARICResearch/ARC/blob/main/ARC.csv>`_ (also shown at the **bottom of this page**) of clinical and research questions. This file provides the standardized structure that ensures interoperability across studies and outbreak contexts.

Each row in the CSV represents a **variable** used in the Case Report Forms (CRFs). Variables include metadata that ensures **clarity, interoperability, and reusability** across contexts. For more details on variable naming conventions see :ref:`this <arc-variable-naming>`, and for details on the variable data types see :ref:`this <arc-field-types>`.

For every variable, the following fields are included:

- **Variable**: Unique variable name identifier used in the dataset (e.g., ``comor_hypertensi``).
- **Form**: The CRF form where the variable appears (e.g., *Presentation*, *Daily*, *Outcome*, …).
- **Section**: Subdivision within the form that groups related questions (e.g., *Co-morbidities and Risk Factors*,…).
- **Type**: Format of the response field (e.g., ``radio``, ``checkbox``, ``text``, ``date``).
- **Question**: Human-readable text shown to the data collector (e.g., *Hypertension*).
- **Answer Options**: Permissible responses to the question. These may reference predefined lists in ``/lists`` (e.g.,
  ``1, Yes | 0, No | 99, Unknown``).
- **Validation**: Input rules for the response, such as numeric range or pattern restrictions.
- **Minimum / Maximum**: Boundaries for numeric input when applicable.
- **List**: Links to option lists in ``/lists``.
- **Skip Logic**: Rules defining when the variable should be displayed, depending on other responses.
- **Body System**: Physiological system the variable belongs to (e.g., *Cardiovascular*).
- **Definition**: Description of the concept being captured, often linked to clinical definitions.
- **Completion Guideline**: Instruction text for data collectors to standardize responses.
- **Standardized Term Codelist**: Reference ontology or terminology
  system used for harmonization (e.g., *SNOMED*).
- **Standardized Term Code**: The specific code(s) from the ontology (e.g., ``38341003, Hypertensive disorder, systemic arterial (disorder)``).
- **Templates / Presets**: Links to where the variable is used in disease-specific CRFs (*COVID, Dengue, Mpox, H5Nx, ARI*) or risk scores (*Charlson CI, mSOFA*).

The CSV serves not only as a **question bank**, but also as a **metadata dictionary** that enables:

- Harmonized clinical data collection.
- Mapping to standard vocabularies.
- Adaptation for different diseases and study contexts.

.. literalinclude:: ../../ARC.csv
   :encoding: latin-1
   :language: csv
   :lineno-start: 1
   :emphasize-lines: 1

