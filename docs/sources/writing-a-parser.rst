.. _writing-a-parser:

Writing a Custom Parser
=======================

This tutorial walks through converting a clinical dataset into the two ISARIC
output tables described in :ref:`isaric-data-schema`. The conversion tool is
`ADTL <https://adtl.readthedocs.io/en/latest/index.html>`_ (Another Data
Transformation Language), which reads a TOML **parser file** that you will write to
describe how your source columns map to the schema.

Install ADTL and read through its introductory documentation before continuing:

.. code-block:: bash

   pip install adtl

The example files used throughout this tutorial live in ``docs/examples/``:

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - File
     - Description
   * - ``example_data.csv``
     - Synthetic COVID-19 source dataset (5 patients)
   * - ``example_parser.toml``
     - Completed parser — the end result of this tutorial
   * - ``covid-study-core.csv``
     - Expected core table output
   * - ``covid-study-long.csv``
     - Expected long table output

.. _what-you-build:

What you are building
---------------------

Running ADTL with the ``example_parser.toml`` file and synthetic data produces two CSV files.
The **core table** has one row per patient, with fixed demographic and outcome columns:

.. code-block:: text

   subjid  dataset_id    demog_sex  demog_age_days  demog_country_iso3  outco_outcome       outco_date
   C001    COVID-STUDY   Male       20088           GBR                 Discharged alive    2023-01-17
   C002    COVID-STUDY   Female     26298           DEU                 Death               2023-01-28
   ...

The **long table** has one row per *observation* per patient. Instead of one
column per variable, it uses a single ``attribute`` column to name the
observation, and ``value`` or ``value_num`` to hold its value:

.. code-block:: text

   subjid  attribute          value   value_num  phase         date        attribute_status
   C001    adsym_fever        Yes              presentation  2023-01-10  VAL
   C001    vital_highesttem_c          38.1      presentation  2023-01-10  VAL
   C001    comor_hypertensi   Yes              presentation  2023-01-10  VAL
   ...

Every row in the long table also carries an ``attribute_status``: ``VAL``
- a value was recorded; ``UNK`` - unknown; ``NI`` - no
information; ``NASK`` - not asked; ``NA`` - not applicable. This matters
for pooled analyses because a missing row could mean "not asked" or
"asked but unknown" — the status distinguishes between them.

The parser file is what tells ADTL how to turn your source columns into this
structure. The rest of this tutorial builds it up step by step.

Depending on how closely your dataset resembles one generated using a BRIDGE CRF & REDCap, you may wish to start
with the auto-generated parser produced by the `draft_parser.py` script in the ``schemas/`` directory, and edit that file rather than writing one from scratch.
Running ``adtl check`` with the auto-generated parser and your source data will show you which
fields are missing; however, it won't look at the mapping so you should check the output data carefully
to make sure it has been transformed correctly.

.. _step-1-find-data-target:

Step 1: Find where your data goes
----------------------------------

Before writing any mapping rules, work out where each of your source columns
belongs in the ISARIC schema. There are two questions to answer for each field:

**Core or long?**

The core table is for fields that apply once per patient: identifiers,
demographics, admission details, and the final outcome. Everything else —
symptoms, vital signs, lab results, treatments, complications — goes in the
long table. The core table is deliberately short, so finding the fields in your dataset
which correspond to the core table variables should not take long; you can find the fields
in :ref:`isaric-data-schema`.

Everything else goes in the long table, with the variable name specified in the ``attribute`` column.

**What is the ISARIC attribute name?**

The long table uses ARC variable names in the ``attribute`` column. To find
the right name for your field, search ``ARC.csv`` for a matching concept. For
example, if your dataset has a column called ``comorbid_hypertension``, search
for "hypertension".

This returns ``comor_hypertensi`` — the ARC variable name to use as the
``attribute`` value in your parser.

The full ARC variable list, with descriptions and answer options, is in
``ARC.csv`` at the root of this repository.

.. note::

   Sometimes there is no single ARC attribute that matches your source field
   exactly. A source column called ``comps_bacterial_pneumonia`` (a yes/no
   field) does not map to a single ARC attribute — instead, it maps to
   ``compl_pneum`` (was pneumonia present?) and separately to ``compl_pneum_type``
   (type of pneumonia). The :ref:`complications section <complications-section>`
   below shows how to handle this.

   If there is no good match for your field, you should contact the ISARIC team about how best to proceed.

.. _the-source-data:

The source data
---------------

``example_data.csv`` represents a COVID-19 hospital study with five patients.
A selection of columns is shown below:

.. code-block:: text

   usubjid,studyid,siteid_final,country_iso,slider_sex,age,date_admit,date_outcome,outcome,...
   C001,COVID-STUDY,SITE-GBR-01,GBR,Male,55,2023-01-10,2023-01-17,discharge,...
   C002,COVID-STUDY,SITE-DEU-01,DEU,Female,72,2023-01-11,2023-01-28,death,...
   C003,COVID-STUDY,SITE-USA-01,USA,Male,38,2023-01-12,2023-01-19,discharge,...
   C004,COVID-STUDY,SITE-GBR-02,GBR,Female,61,2023-01-13,NA,ongoing care,...
   C005,COVID-STUDY,SITE-ESP-01,ESP,Male,48,2023-01-14,2023-01-21,transferred,...

Missing values are represented as ``NA`` throughout. Boolean fields use
``TRUE`` / ``FALSE``.

Comparing the source columns to the ISARIC schema reveals several things that
need handling:

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
     - Reusable value mapping
   * - ``age`` in years
     - ``demog_age_days`` in days
     - Unit conversion
   * - ``outcome`` as free text
     - Fixed set of allowed strings
     - Value mapping + ``ignoreMissingKey``
   * - Treatments in both ``treat_*`` and ``icu_treat_*`` columns
     - Single ``attribute`` row
     - ``combinedType = "firstNonNull"``

.. _step-2-setup-parser-file:

Step 2: Set up the parser file
-------------------------------

Create a new file (e.g. ``my-study-parser.toml``) and start with the metadata
block. The ``name`` value determines the output filenames:

.. code-block:: toml

   [adtl]
     name        = "covid-study"
     description = "Example COVID-19 study parser"
     emptyFields = "NA"

``emptyFields`` tells ADTL which string in your source data represents a
missing value. Any field containing that string will be treated as absent —
no output row will be produced. If your data uses blank cells instead of a
placeholder, omit this line.

Next, declare the two output tables. These lines tell ADTL what kind of table
each is and where to find the schema file it should validate against:

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

``kind = "groupBy"`` collapses any duplicate source rows for the same patient
into one output row, keeping the last non-null value for each field.
``kind = "oneToMany"`` expands each source row into multiple output rows —
one per ``[[long]]`` block that produces a non-null value.

The ``common`` setting lists fields that should appear on every long table row.
Putting ``subjid`` and ``dataset_id`` here means you do not have to repeat
them in every observation block.

Replace ``1.2.2`` with the ARC version you are targeting. The schema paths are
relative to the parser file.

.. _step-3-map-core:

Step 3: Map the core table
---------------------------

The ``[core]`` section maps your source columns to the core table fields. The
simplest case is a direct column-to-field mapping:

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

``subjid = { field = "usubjid" }`` means: take the value from the source column
named ``usubjid`` (referred to as the ``field``) and write it to the ``subjid`` column in the core table.

Values without a ``field`` key are written as-is for every patient.
``dataset_disease = "COVID-19"`` and ``pres_adm = "Unknown"`` are examples:
the disease is the same for all patients in this dataset, and admission status
was not explicitly collected.

**When the values need translating**

The core schema requires ``demog_sex`` to be ``"Male"`` or ``"Female"``,
exactly. The source data happens to use the same strings — but an explicit
``values`` mapping is still good practice because it documents the intent,
rejects unexpected values like ``"M"`` or ``"F"``, and makes it easy to add
``"Other"`` later if needed:

.. code-block:: toml

   [core.demog_sex]
     field  = "slider_sex"
     values = { Male = "Male", Female = "Female" }

**When the units are different**

The schema requires ``demog_age_days`` as an integer number of days, but the
source records age in years. ADTL handles unit conversion automatically, when you specify
the ``source_unit`` (the units your data was collected in) and the target ``unit`` (what the ISARIC schema requires):

.. code-block:: toml

   [core.demog_age_days]
     field       = "age"
     unit        = "days"
     source_unit = "years"

.. note:: On TOML syntax

   The above TOML code-block is equivalent to

   .. code-block:: toml

      [core]
        demog_age_days = { field = "age", unit = "days", source_unit = "years" }

  Which format you choose is largely dependent on personal preference and readability.
  If, like in the example below, there are many sub-keys for a single field, the sub-table
  format is often easier to read as it doesn't disappear off the edge of the screen.

  If using an IDE such as VSCode to edit your parser, there are auto-formatters available such as
  `Even Better TOML <https://marketplace.visualstudio.com/items?itemName=tamasfe.even-better-toml>`_ which
  will automatically format your parser file for you and highlight any syntax errors.

**When the outcome is recorded as free text**

Clinical outcome can be recorded in many ways across different sites — ``"discharge"``,
``"released"``, ``"cured (confirmed by a negative covid test)"`` — but the
ISARIC schema only accepts a fixed set of strings. A ``values`` map converts
each source string to the correct schema value.

By default, if a source value is not found in the ``values`` map, ADTL silently ignores it.
Setting ``ignoreMissingKey = true`` changes this: unmapped
values pass through unchanged, and ADTL will flag them at validation time if
they are not valid schema values. This is useful when you cannot know in advance
every possible free-text string a site might enter:

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

Multiple source strings can map to the same schema value. The sub-table
syntax (``[core.outco_outcome.values]``) is used here instead of inline braces
because the mapping is too long to fit on one line.

.. _step-4-map-long:

Step 4: Map the long table
---------------------------

Each observation type gets its own ``[[long]]`` block. The minimum each block needs is
an ``attribute`` name, a value source, a phase and an ``attribute_status``.

.. _reuse-definitions:

**Reusing phase and date across many blocks**

Most observations belong to one of two healthcare encounter phases in this dataset: presentation
(at admission) or outcome (at discharge). Rather than writing the phase and
date on every single block, define them once as reusable references:

.. code-block:: toml

   [adtl.defs.phase_presentation]
     phase = "presentation"
     date  = { field = "date_admit" }

   [adtl.defs.phase_outcome]
     phase = "outcome"
     date  = { field = "date_outcome" }

Any ``[[long]]`` block can then include e.g. ``ref = "phase_presentation"`` to
inherit both ``phase`` and ``date`` from the definition.

.. _string-bool-observations:

**String and boolean observations (symptoms, comorbidities)**

In this example dataset, boolean fields — where the source value is ``TRUE`` or
``FALSE`` — are common. These need two things: a mapping from ``TRUE``/``FALSE`` to ``"Yes"``/``"No"``, and an
``attribute_status`` to record whether the data was actually collected.

Define the value mapping once as a reusable def:

.. code-block:: toml

   [adtl.defs."Y/N/NK"]
     values = { TRUE = "Yes", FALSE = "No" }

Then reference it in each observation block:

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

``ref = "Y/N/NK"`` expands the ``values`` map inside the ``value`` field.
``ref = "phase_presentation"`` expands into ``phase`` and ``date`` at the
block level. ADTL applies these substitutions before producing output.

The ``attribute_status_fill`` function is defined in ``schemas/isaric_transformations.py``
(not built into ADTL itself). It determines the status code from the raw source value:

- A null value (absent, or matched by ``emptyFields``) → row is suppressed entirely
- A pre-defined status code (``UNK``, ``NI``, ``NASK``, ``NA``) → passed through as-is
- Any other non-null value (including ``TRUE`` or ``FALSE``) → ``VAL``

This same pattern — ``ref = "Y/N/NK"`` for the value, ``attribute_status_fill``
for the status — applies to every boolean field: symptoms, comorbidities,
treatments, and complications.

.. _numeric-observation:

**Numeric observations (vital signs, lab values)**

For numeric measurements, use ``value_num`` instead of ``value``, and add
``attribute_unit`` to record the unit:

.. code-block:: toml

   [[long]]
     attribute        = "vital_highesttem_c"
     value_num        = { field = "vs_temp" }
     attribute_unit   = "°C"
     attribute_status = { field = "vs_temp", apply = { function = "attribute_status_fill" } }
     ref              = "phase_presentation"

   [[long]]
     attribute        = "labs_crp_mgl"
     attribute_unit   = "mg/L"
     value_num        = { field = "lab_crp" }
     attribute_status = { field = "lab_crp", apply = { function = "attribute_status_fill" } }
     ref              = "phase_outcome"

Vital signs are assigned to the ``phase_presentation`` phase; lab values to ``phase_outcome``.
This may differ for you, depending on the timing of your measurements. Adjust the ``ref`` accordingly.

.. _two-sources-section:

**When the same data is in two source columns**

Some studies record treatments separately for general ward and ICU patients.
Rather than producing two rows for the same attribute, ``combinedType = "firstNonNull"``
merges them: ADTL evaluates the list of fields in order and uses the first
non-null result.

For non-ICU patients, the ``icu_treat_*`` column is ``"NA"`` (null), so the
ward column is used. For patient C002 (who was in the ICU), the ward column is
``FALSE`` but the ICU column is ``TRUE`` — so the ICU value takes effect.

The ``[long.attribute_status]`` block
mirrors the same field order so the status always reflects the same source
column as the selected value:

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

.. _own-date-section:

**When an observation has its own date**

The ICU admission block cannot use the presentation or outcome phase refs,
because its date (``icu_in``) is different from both ``date_admit`` and
``date_outcome``. Define the phase and date inline instead:

.. code-block:: toml

   [[long]]
     attribute        = "crito_icu"
     value            = { field = "slider_icu_ever", ref = "Y/N/NK" }
     attribute_status = { field = "slider_icu_ever", apply = { function = "attribute_status_fill" } }
     phase            = "during_observation"
     date             = { field = "icu_in" }
     duration         = { field = "icu_in", apply = { function = "durationDays", params = ["$icu_out"] } }

The ``duration`` field records the ICU length of stay in days. ``durationDays``
computes the number of days between the value of ``icu_in`` and the column
named in ``params`` (``$icu_out`` — the ``$`` prefix means "look up this
column in the same source row"). For patients without an ICU admission,
both columns are ``"NA"`` (null), so ``duration`` is left empty.

ADTL ships with a number of built-in functions similar to `durationDays`,
which can be found in the `ADTL documentation <https://adtl.readthedocs.io/en/latest/api/transformations.html>`_.

.. _complications-section:

**When one source field maps to multiple attributes**

Sometimes a single yes/no source column corresponds to more than one ARC
attribute. The source column ``comps_bacterial_pneumonia`` is an example: the
ARC 1.2.2 schema does not have a single attribute for "bacterial pneumonia as
a complication". Instead, it separates the concept into two attributes:
``compl_pneum`` (was pneumonia present?) and ``compl_pneum_type`` (what was
the etiology?).

Write two ``[[long]]`` blocks from the same source column. For
``compl_pneum_type``, only map ``TRUE`` — ADTL silently skips rows where the
source value has no entry in the ``values`` map, so patients where
``comps_bacterial_pneumonia = FALSE`` will not get a ``compl_pneum_type`` row:

.. code-block:: toml

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

.. _step-5-run-and-check:

Step 5: Run the parser and check the output
--------------------------------------------

Before running against a full dataset, use ``adtl check`` to catch problems
early. This validates that all field names in the parser exist in your data,
and warns about source columns that are not mapped:

.. code-block:: bash

   adtl check docs/examples/example_parser.toml docs/examples/example_data.csv

Once you are happy, run the parser to produce the output files:

.. code-block:: bash

   adtl parse docs/examples/example_parser.toml docs/examples/example_data.csv

This creates two files in the current directory — ``covid-study-core.csv`` and
``covid-study-long.csv`` — and prints a validation summary:

.. code-block:: text

   |table          |valid  |total  |percentage_valid|
   |---------------|-------|-------|----------------|
   |core           |4      |5      |80.000000%      |
   |long           |109    |109    |100.000000%     |

.. _understanding-errors:

**Understanding validation errors**

A row that fails validation is still written to the output file, with
``adtl_valid = False`` and an explanation in the ``adtl_error`` column. No
data is lost. In this example, patient C004 fails:

.. code-block:: text

   data must contain ['subjid', 'siteid', 'dataset_id', 'dataset_disease',
   'demog_sex', 'demog_age_days', 'demog_country_iso3', 'pres_adm',
   'pres_date', 'outco_outcome', 'outco_date'] properties

C004's ``date_outcome`` is ``"NA"`` — the patient is still hospitalised, so no
outcome date was recorded. Because ``emptyFields = "NA"``, ADTL omits
``outco_date`` from the output row entirely. The core schema marks
``outco_date`` as required, so the row fails validation even though the data
itself is correct.

This is expected for ongoing-care patients. At the analysis stage you would
decide whether to include or exclude such rows. The long table is unaffected
because it validates each observation row independently.

For large datasets, add ``--parallel`` for a significant speed improvement:

.. code-block:: bash

   adtl parse docs/examples/example_parser.toml large-study-data.csv --parallel

Going further
-------------

The patterns above cover the most common cases. Below are a few more that
appear in real-world datasets.

.. _repeated-columns:

**Repeated columns**

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

This will expand out into 5 blocks when run, and will create a long table row for each
follow-up visit that has a non-null value.

.. _event-id:

**Linking related observations**

Some ARC forms — medications and pathogen testing, for example — can have
multiple entries per patient per day. A patient might receive two different
medications on the same date, so the date alone is not enough to tell those
entries apart in the long table. Related observations in the long table ( e.g. the name, dose, and
route of a single medication) need to be linked by a shared ``event_id``.

ADTL can generate this ID automatically using the ``generate`` key. It
produces a UUID5, which is deterministic: the same inputs always produce
the same ID. The fields listed in ``values`` are combined to generate the ID,
so they must together uniquely identify the event. In the example below,
``subjid`` + ``medi_date`` + ``drug_name`` is sufficient — two different
medications given to the same patient on the same day will have different
names, giving each its own ID:

.. code-block:: toml

   [[long]]
     attribute = "medi_medname"
     value     = { field = "drug_name" }
     event_id  = { generate = { type = "uuid5", values = ["subjid", "medi_date", "drug_name"] } }

   [[long]]
     attribute = "medi_dose"
     value_num = { field = "drug_dose_mg" }
     event_id  = { generate = { type = "uuid5", values = ["subjid", "medi_date", "drug_name"] } }

Good practise would be to create a reusable definition for, e.g., all medication-related blocks,
so that the same event ID generation logic is applied consistently across all related observations.

That might look something like this:

.. code-block:: toml

   [adtl.defs.medication]
     phase    = "during_observation"
     date     = { field = "medi_date" }
     duration = { field = "medi_numdays" }

     [adtl.defs.medication.event_id]
       generate = { type = "uuid5", values = ["subjid", "medi_date", "drug_name"] }

   [[long]]
     ref       = "medication"
     attribute = "medi_medname"
     value     = { field = "drug_name" }

   [[long]]
     ref       = "medication"
     attribute = "medi_dose"
     value_num = { field = "drug_dose_mg" }

Further reading
---------------

- `ADTL documentation <https://adtl.readthedocs.io/en/latest/index.html>`_ — full reference for all mapping rules, CLI options, and the Python API.
- :ref:`isaric-data-schema` — overview of the ISARIC core and long schema tables.
