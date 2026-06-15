.. _writing-a-parser:

Writing a Custom Parser
=======================

This tutorial walks through writing an `ADTL <https://adtl.readthedocs.io/en/latest/index.html>`_
parser that transforms a clinical dataset — collected using tools other than BRIDGE & REDCap — into
the two ISARIC output tables described in :ref:`isaric-data-schema`.

The example files used throughout this tutorial live in ``docs/examples/``:

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - File
     - Description
   * - ``example_data.csv``
     - Synthetic COVID-19 source dataset (5 patients)
   * - ``example_parser.toml``
     - Worked parser mapping to the ISARIC core and long tables

Getting started
-----------------

Before going through this tutorial, first read through the `ADTL documentation <https://adtl.readthedocs.io/en/latest/index.html>`_ for full
installation and usage instructions.

Particularly, make sure you have gone through the example provided there, as it introduces several concepts also used here.

The source data
---------------

``example_data.csv`` represents a COVID-19 hospital study with five patients. A selection
of columns is shown below:

.. code-block:: text

   usubjid,studyid,siteid_final,country_iso,slider_sex,age,date_admit,date_outcome,outcome,...
   C001,COVID-STUDY,SITE-GBR-01,GBR,Male,55,2023-01-10,2023-01-17,discharge,...
   C002,COVID-STUDY,SITE-DEU-01,DEU,Female,72,2023-01-11,2023-01-28,death,...
   C003,COVID-STUDY,SITE-USA-01,USA,Male,38,2023-01-12,2023-01-19,discharge,...
   C004,COVID-STUDY,SITE-GBR-02,GBR,Female,61,2023-01-13,NA,ongoing care,...
   C005,COVID-STUDY,SITE-ESP-01,ESP,Male,48,2023-01-14,2023-01-21,transferred,...

Missing values are represented as ``NA`` throughout the source file.
Boolean fields (symptoms, comorbidities, treatments, complications) use ``TRUE`` / ``FALSE``.

The source data has several mismatches with the ISARIC schema that the parser must handle:

.. list-table::
   :header-rows: 1
   :widths: 35 30 35

   * - Source
     - ISARIC
     - How to handle
   * - ``NA`` for missing values
     - Omit the field / row
     - ``emptyFields = "NA"``
   * - ``TRUE`` / ``FALSE``
     - ``"Yes"`` / ``"No"``
     - Reusable def (``"Y/N/NK"``)
   * - ``age`` in years
     - Integer days
     - Unit conversion
   * - ``outcome`` as free text (varies by site)
     - Fixed enum string
     - Value mapping + ``ignoreMissingKey``
   * - Some fields recorded in both ``treat_*`` and ``icu_treat_*`` columns
     - Single ``attribute`` row
     - ``combinedType = "firstNonNull"``

Writing the parser
------------------

1. The ``[adtl]`` metadata block
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Every parser starts with a metadata block. The ``emptyFields`` key tells ADTL which
string in the source data represents a missing value — any field containing that string
is treated as null and will not produce an output row:

.. code-block:: toml

   [adtl]
     name        = "covid-study"
     description = "Example COVID-19 study parser"
     emptyFields = "NA"

If your dataset has blank cells/empty strings instead of a specific placeholder,
`emptyFields` does not need to be specified.

2. Reusable definitions
~~~~~~~~~~~~~~~~~~~~~~~~

Rules that appear in many places can be pulled into ``[adtl.defs]`` and referenced
with ``ref = "name"``.

**Boolean mapping** — the source uses ``TRUE`` / ``FALSE``, but the ISARIC schema
requires ``"Yes"`` / ``"No"``. A single def handles every boolean field in the dataset:

.. code-block:: toml

     [adtl.defs."Y/N/NK"]
       values = { TRUE = "Yes", FALSE = "No" }

**Named phase blocks** — In this example dataset, there are data corresponding to two of the 5 phases present in the ISARIC schema: presentation (at admission) and outcome (at discharge).

Each phase has an associated date, and this phase-date pair is consistent across all long-table rows for that phase.
Creating reusable definitions allows the phase and date to be specified once and referenced in multiple blocks, while making the ``[[long]]`` blocks self-documenting:

.. code-block:: toml

     [adtl.defs.phase_presentation]
       phase = "presentation"
       date  = { field = "date_admit" }

     [adtl.defs.phase_outcome]
       phase = "outcome"
       date  = { field = "date_outcome" }

3. Table declarations
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: toml

     [adtl.tables.core]
       kind        = "groupBy"
       groupBy     = "subjid"
       aggregation = "lastNotNull"
       schema      = "../../schemas/isaric-core.json"

     [adtl.tables.long]
       kind          = "oneToMany"
       schema        = "../../schemas/arc_1.2.2_isaric_long.schema.json"
       discriminator = "attribute"
       common = { subjid = { field = "usubjid" }, dataset_id = { field = "studyid" }, arcver = "1.2.2" }

``kind = "groupBy"`` for the core table collapses any duplicate patient rows into one,
keeping the last non-null value for each field. ``kind = "oneToMany"`` for the long
table expands each source row out into multiple output rows — one per observation.

``common`` lists fields written to every ``[[long]]`` row without having to repeat them in each block.
Here ``dataset_id`` is read from the source column ``studyid``, not hard-coded,
because it varies across datasets that share the same parser.

The ``schema`` paths are relative to the parser file (``docs/examples/``). Replace
``1.2.2`` with the ARC version you are targeting; the long schema is auto-generated
for each ARC release.

4. Core table field mappings
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: toml

   [core]
     subjid             = { field = "usubjid" }
     siteid             = { field = "siteid_final" }
     dataset_id         = { field = "studyid" }
     dataset_disease    = "COVID-19"
     demog_country_iso3 = { field = "country_iso" }
     pres_adm           = "Unknown"
     pres_date          = { field = "date_admit" }
     outco_date         = { field = "date_outcome" }

Constants (no ``field`` key) are written as literal values. ``pres_adm = "Unknown"``
is appropriate when admission status was not explicitly recorded.

**Sex mapping** — the source already uses ``"Male"`` / ``"Female"`` strings, but
an explicit ``values`` mapping is still good practice: it documents intent, rejects
unexpected values, and makes it straightforward to add ``"Other"`` later:

.. code-block:: toml

     [core.demog_sex]
       field  = "slider_sex"
       values = { Male = "Male", Female = "Female" }

**Age in days** — the source records age in years. ADTL uses the
`pint <https://pint.readthedocs.io>`_ library for unit conversion:

.. code-block:: toml

     [core.demog_age_days]
       field       = "age"
       unit        = "days"
       source_unit = "years"

**Outcome mapping** — Data can often be recorded as free-text, or with a large range of controlled terminology which varies between sites and studies.
ADTL's default behaviour is to silently drop any source value that is not explicitly mapped, if a `values` map is given.
``ignoreMissingKey = true`` suppresses this behaviour and keeps any source value not in the ``values`` map, which is essential when you cannot enumerate/do not know every string in advance.
If a value has not been mapped and is not one of enums accepted by the ISARIC schema, ADTL will flag the entry with an error to allow the user to correct the parser.
The ``[core.outco_outcome.values]`` table block syntax is used here (rather than inline
braces) because the mapping has too many entries to fit on one line:

.. code-block:: toml

     [core.outco_outcome]
       field            = "outcome"
       ignoreMissingKey = true
       [core.outco_outcome.values]
         discharge                                    = "Discharged alive"
         released                                     = "Discharged alive"
         "released with home care"                    = "Discharged alive"
         "cured (confirmed by a negative covid test)" = "Discharged alive"
         "recovery (confirmed by a negative test)"    = "Discharged alive"
         "ongoing care"                               = "Still hospitalised"
         transferred                                  = "Transfer to other facility"
         "moved to facility"                          = "Transfer to other facility"
         death                                        = "Death"

Multiple source strings can map to the same schema value (all the ``"Discharged alive"``
variants above). Patient C004's ``outcome = "ongoing care"`` maps to
``"Still hospitalised"``; their ``date_outcome`` is ``"NA"`` (null), so
``outco_date`` is left empty for that patient.

5. Long table — symptoms and comorbidities
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Boolean fields use ``ref = "Y/N/NK"`` to apply the ``TRUE`` / ``FALSE`` mapping
defined in step 2. ``ref = "phase_presentation"`` pulls in the ``phase`` and ``date``
keys from the named def. Each block also sets ``attribute_status`` using the provided
``attribute_status_fill`` function.

``attribute_status_fill`` is defined in ``schemas/isaric_transformations.py`` and is
designed for data exported from BRIDGE CRFs, where missing fields may carry
explicit status codes (``"UNK"``, ``"NI"``, ``"NASK"``, ``"NA"``). Its logic is:

- If the raw field value is one of the four pre-defined status codes, pass it through as-is.
- If the field is any other non-null value (including ``"TRUE"`` or ``"FALSE"``), return ``"VAL"``.
- If the field is null (absent or matched by ``emptyFields``), return ``None`` — which suppresses the row.

.. code-block:: toml

   [[long]]
     attribute        = "adsym_fever"
     value            = { field = "symptoms_history_of_fever", ref = "Y/N/NK" }
     attribute_status = { field = "symptoms_history_of_fever", apply = { function = "attribute_status_fill" } }
     ref              = "phase_presentation"

   [[long]]
     attribute        = "comor_hypertensi"
     value            = { field = "comorbid_hypertension", ref = "Y/N/NK" }
     attribute_status = { field = "comorbid_hypertension", apply = { function = "attribute_status_fill" } }
     ref              = "phase_presentation"

Both ``ref`` keys expand when used: ``ref = "Y/N/NK"`` fills the ``values`` map inside
``value``; ``ref = "phase_presentation"`` fills ``phase`` and ``date`` at the block
level. ADTL automatically suppresses rows where the mapped value is null — so an
``"NA"`` source field produces no output row for that patient.

The same ``attribute_status_fill`` pattern is used on every vital sign and lab block.

6. Long table — vital signs and lab values
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Numeric observations use ``value_num`` instead of ``value``, with an optional
``attribute_unit``. Vitals are assigned to the ``phase_presentation`` phase; lab
values (typically recorded at or near discharge) to ``phase_outcome``:

.. code-block:: toml

   [[long]]
     attribute      = "vital_highesttem_c"
     value_num      = { field = "vs_temp" }
     attribute_unit = "°C"
     ref            = "phase_presentation"

   [[long]]
     attribute      = "labs_crp_mgl"
     attribute_unit = "mg/L"
     value_num      = { field = "lab_crp" }
     ref            = "phase_outcome"

7. Long table — treatments with two source columns
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Some studies record treatment data separately for general ward and ICU. Using
``combinedType = "firstNonNull"`` merges two source columns into a single output
row: ADTL evaluates the fields in order and returns the first non-null result.

For non-ICU patients, ``icu_treat_*`` columns are ``"NA"`` (null after ``emptyFields``
processing), so the ward column is used. For patient C002, who was admitted to the ICU,
the ward column is ``FALSE`` but the ICU column is ``TRUE``.

The ``[long.value]`` and ``[long.attribute_status]`` table block syntax is used here
because the ``combinedType`` structure is too nested for inline braces. The
``attribute_status`` block mirrors the same field order so the status always reflects
the same source column as the selected value:

.. code-block:: toml

   [[long]]
     attribute = "medi_medtype"
     ref       = "phase_outcome"
     [long.value]
       combinedType = "firstNonNull"
       fields = [
         { field = "treat_corticosteroids",     values = { "TRUE" = "Corticosteroid" } },
         { field = "icu_treat_corticosteroids", values = { "TRUE" = "Corticosteroid" } },
       ]
     [long.attribute_status]
       combinedType = "firstNonNull"
       fields = [
         { field = "treat_corticosteroids",     apply = { function = "attribute_status_fill" } },
         { field = "icu_treat_corticosteroids", apply = { function = "attribute_status_fill" } },
       ]

8. Long table — block without a phase ref
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ICU admission block cannot use either phase ref because its observation date
(``icu_in``) is different from both ``date_admit`` and ``date_outcome``. The ``phase``
and ``date`` keys are defined inline instead:

.. code-block:: toml

   [[long]]
     attribute        = "crito_icu"
     value            = { field = "slider_icu_ever", ref = "Y/N/NK" }
     attribute_status = { field = "slider_icu_ever", apply = { function = "attribute_status_fill" } }
     phase            = "during_observation"
     date             = { field = "icu_in" }
     duration         = { field = "icu_in", apply = { function = "durationDays", params = ["$icu_out"] } }

``attribute_status_fill`` works correctly here for the same reason as in step 5:
``"TRUE"`` and ``"FALSE"`` are both non-null, non-status-code values, so both
return ``"VAL"``.

``duration`` records the ICU length of stay in days. The ``durationDays`` function
computes the number of days from ``icu_in`` to the field named in ``params``
(``$icu_out`` — the ``$`` prefix tells ADTL to look up a column in the same row).
For patients without an ICU admission, both ``icu_in`` and ``icu_out`` are ``"NA"``
(null), so ``duration`` is left empty for those rows.

9. Long table — complications
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Complications follow the same ``attribute_status_fill`` pattern as symptoms and
comorbidities. Where the ARC 1.2.2 schema has no single boolean attribute for a
condition, the source field may need to map to more than one attribute.

``comps_bacterial_pneumonia`` is an example: the schema captures pneumonia presence
via ``compl_pneum`` and etiology separately via ``compl_pneum_type``. The
``compl_pneum_type`` block only maps ``TRUE``, so it is emitted only for patients
where pneumonia was recorded — ADTL silently skips rows where the source value has
no entry in ``values``:

.. code-block:: toml

   [[long]]
     attribute        = "compl_ards"
     value            = { field = "comps_ards", ref = "Y/N/NK" }
     attribute_status = { field = "comps_ards", apply = { function = "attribute_status_fill" } }
     ref              = "phase_outcome"

   [[long]]
     attribute        = "compl_pneum"
     value            = { field = "comps_bacterial_pneumonia", ref = "Y/N/NK" }
     attribute_status = { field = "comps_bacterial_pneumonia", apply = { function = "attribute_status_fill" } }
     ref              = "phase_outcome"

   [[long]]
     attribute        = "compl_pneum_type"
     value            = { field = "comps_bacterial_pneumonia", values = { "TRUE" = "Bacterial" } }
     attribute_status = { field = "comps_bacterial_pneumonia", apply = { function = "attribute_status_fill" } }
     ref              = "phase_outcome"

Running the parser
------------------

From the repository root:

.. code-block:: bash

   adtl docs/examples/example_parser.toml docs/examples/example_data.csv

For large datasets, add ``-p`` / ``--parallel`` for a significant speed improvement:

.. code-block:: bash

   adtl docs/examples/example_parser.toml large-study-data.csv --parallel

This creates two output files in the current directory (the expected outputs for
the example dataset are included in ``docs/examples/`` for reference):

- ``covid-study-core.csv`` — one row per patient
- ``covid-study-long.csv`` — one row per observation per patient

The terminal output shows schema validation results:

.. code-block:: text

   |table          |valid  |total  |percentage_valid|
   |---------------|-------|-------|----------------|
   |core           |4      |5      |80.000000%      |
   |long           |109    |109    |100.000000%     |

One core row fails validation. Opening ``covid-study-core.csv`` shows the reason
in the ``adtl_error`` column for patient C004:

.. code-block:: text

   data must contain ['subjid', 'siteid', 'dataset_id', 'dataset_disease',
   'demog_sex', 'demog_age_days', 'demog_country_iso3', 'pres_adm',
   'pres_date', 'outco_outcome', 'outco_date'] properties

C004's ``date_outcome`` is ``"NA"`` in the source data — the patient is still
hospitalised, so no outcome date was recorded. Because ``emptyFields = "NA"``
treats this as a missing value, ADTL omits ``outco_date`` from the output row
entirely. The core schema marks ``outco_date`` as a required property, so the
row fails validation even though the data itself is correct.

This is expected behaviour for ongoing-care patients. The row is still written
to ``covid-study-core.csv`` (with ``adtl_valid = False``) so no data is lost.
In a real study you would decide at the analysis stage whether to include or
exclude such rows. The long table is unaffected because it validates each
observation row independently.

Checking a parser before a full run
-------------------------------------

Before running against a large dataset, use ``adtl check`` to validate the parser
and cross-check field names against the source data:

.. code-block:: bash

   adtl check docs/examples/example_parser.toml docs/examples/example_data.csv

This errors if any field names in the parser do not exist in the data, and warns
about fields in the data that are not mapped.

Extending the parser
--------------------

Adding more observations
~~~~~~~~~~~~~~~~~~~~~~~~~

Add a ``[[long]]`` block for each new observation type, choosing the appropriate
phase ref and value type:

.. code-block:: toml

   [[long]]
     attribute = "adsym_headache"
     value     = { field = "symptoms_headache", ref = "Y/N/NK" }
     ref       = "phase_presentation"

   [[long]]
     attribute      = "labs_astsgot"
     attribute_unit = "U/L"
     value_num      = { field = "lab_ast" }
     ref            = "phase_outcome"

Handling follow-up data
~~~~~~~~~~~~~~~~~~~~~~~~

For observations recorded at follow-up visits, add a ``phase_follow_up`` def
and reference it from the relevant blocks:

.. code-block:: toml

   [adtl.defs.phase_follow_up]
     phase = "follow_up"
     date  = { field = "date_follow_up" }

   [[long]]
     attribute = "follow_outcome"
     value     = { field = "fu_status", values = { alive = "Alive", dead = "Dead" } }
     ref       = "phase_follow_up"

Repeated observation blocks
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If the source data has multiple follow-up visits as separate columns (e.g.
``fu_fever_1`` through ``fu_fever_5``), use a ``for`` loop instead of five
identical blocks:

.. code-block:: toml

   [[long]]
     phase       = "follow_up"
     date        = { field = "fu_date_{n}" }
     attribute   = "adsym_fever"
     value       = { field = "fu_fever_{n}", ref = "Y/N/NK" }
     for.n.range = [1, 5]

Linking related observations with a UUID
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When multiple rows describe the same event (e.g. different properties of the same
medication dose), generate a shared ``event_id`` to link them:

.. code-block:: toml

   [[long]]
     attribute = "medi_medname"
     value     = { field = "drug_name" }
     event_id  = { generate = { type = "uuid5", values = ["subjid", "medi_date", "drug_name"] } }

   [[long]]
     attribute = "medi_dose"
     value_num = { field = "drug_dose_mg" }
     event_id  = { generate = { type = "uuid5", values = ["subjid", "medi_date", "drug_name"] } }

Rows with the same ``event_id`` inputs will receive the same UUID, allowing
downstream tools to join them.

Further reading
---------------

- `ADTL documentation <https://adtl.readthedocs.io/en/latest/index.html>`_ — full reference for all mapping rules, CLI options, and the Python API.
- :ref:`isaric-data-schema` — overview of the ISARIC core and long schema tables.
