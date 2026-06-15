.. _isaric-data-schema:

ISARIC Data Schema
==================

Beyond providing the question bank that drives `BRIDGE <https://bridge.isaric.org>`_ CRF generation, ARC defines the **ISARIC data schema** — the standardized output format used across the ISARIC data ecosystem, including `DataHub <https://isaric.org/>`_ and other tools. Any dataset converted into this schema can be pooled and analysed alongside other ISARIC studies without additional harmonization work.

The schema follows an `entity-attribute-value <https://en.wikipedia.org/wiki/Entity%E2%80%93attribute%E2%80%93value_model>`_ design: a fixed **core** table holds the small set of fields expected for every patient, while a flexible **long** table holds all other observations as (attribute, value) pairs.

All date fields are strings in ISO 8601 format. A full datetime (``YYYY-MM-DDThh:mm:ss``), full date (``YYYY-MM-DD``), year-month (``YYYY-MM``), or year-only (``YYYY``) are all valid. All other fields are strings unless the type is stated otherwise.

Schema overview
---------------

**Core table** (wide format)
  One row per patient. Captures fixed, patient-level fields: identifiers,
  demographics, admission, and outcome. The core schema is considered stable;
  only additions are permitted, and only for fields expected to be present
  for most patients. Sparse indicator data (symptoms, comorbidities, etc.)
  belongs in the long table.

  Required fields:

  .. list-table::
     :header-rows: 1
     :widths: 25 15 60

     * - Field
       - Type
       - Description
     * - ``subjid``
       - string
       - Patient Identification Number (PIN). Note that ``subjid`` identifies
         an *encounter*, not necessarily a unique patient across all encounters.
     * - ``siteid``
       - string
       - Site that collected the data.
     * - ``dataset_id``
       - string
       - Dataset identifier.
     * - ``dataset_disease``
       - string
       - Primary disease/syndrome for the dataset (e.g. ``"COVID-19"``).
         The same value applies to every patient in a dataset.
     * - ``demog_sex``
       - enum
       - ``"Male"``, ``"Female"``, ``"Other"``, ``"Not specified/Unknown"``
     * - ``demog_age_days``
       - integer ≥ 0
       - Age in days.
     * - ``demog_country_iso3``
       - string
       - ISO 3166-1 alpha-3 country code (e.g. ``"GBR"``).
     * - ``pres_adm``
       - enum
       - ``"Yes"``, ``"No"``, ``"Unknown"``
     * - ``pres_date``
       - date
       - Most recent presentation/admission date at this facility.
     * - ``outco_outcome``
       - enum
       - One of: ``"Discharged alive"``, ``"Still hospitalised"``,
         ``"Transfer to other facility"``, ``"Death"``,
         ``"Palliative care"``, ``"Discharged against medical advice"``,
         ``"Alive not admitted"``, ``"Hospitalized"``
     * - ``outco_date``
       - date
       - Outcome date.

**Long table** (long format)
  One row per observation per patient. Covers all ARC variables not included
  in the core table — symptoms, vital signs, lab results, medications, imaging,
  and more — using ARC variable names as the ``attribute`` field.

  Required fields:

  .. list-table::
     :header-rows: 1
     :widths: 25 75

     * - Field
       - Description
     * - ``subjid``
       - Patient PIN (links back to core).
     * - ``dataset_id``
       - Dataset identifier.
     * - ``phase``
       - Healthcare encounter phase when the event occurred. One of
         ``"presentation"``, ``"pre_observation"``, ``"during_observation"``,
         ``"follow_up"``, ``"outcome"``.
     * - ``attribute``
       - ARC variable name for the observation (e.g. ``"adsym_fever"``,
         ``"vital_rr"``). Where an attribute with the same or substantially
         similar semantics exists in ARC, that name **must** be used.
     * - ``attribute_status``
       - Data collection status. ``"VAL"`` — value collected and present in
         ``value``/``value_num``; ``"UNK"`` — unknown; ``"NI"`` — no
         information; ``"NASK"`` — not asked; ``"NA"`` — not applicable.

  Optional fields:

  .. list-table::
     :header-rows: 1
     :widths: 25 75

     * - Field
       - Description
     * - ``value``
       - String/categorical value. Y/N/NK attributes should be stored here
         as strings (``"Yes"``/``"No"``/``"Unknown"``) to allow future
         extension with additional codes.
     * - ``value_num``
       - Numeric value (float). Used for measurements such as temperature,
         blood pressure, or heart rate.
     * - ``date``
       - Date of the observation.
     * - ``duration``
       - Duration of the event in days (integer).
     * - ``attribute_unit``
       - Unit of the recorded value. Omit if the attribute has no unit.
     * - ``arcver``
       - ARC version that the attribute belongs to. Omit if the attribute
         is not present in any ARC version.
     * - ``event_id``
       - ID linking attributes that belong to a single event (e.g. the name,
         dosage, and route of a single medication administration).
     * - ``reldate_adm``
       - Relative day since admission (integer).

  Each row must have either ``value`` or ``value_num`` (not both) populated.

  At the analysis stage, the subset of long-table rows with attributes that
  appear only once per patient can be pivoted into wide format and merged with
  the core table for easier access.

The phases in the long table correspond to the :ref:`data capture schema <data-capture-schema>` that ARC is structured around.

Schema files
------------

The JSON schema files that formally define and validate these two tables live in the ``schemas/`` directory:

- ``schemas/isaric-core.json`` — validates the core (wide) table.
- ``schemas/arc_{version}_isaric_long.schema.json`` — validates the long (narrow) table. This file is auto-generated from the current ARC variable list by ``schemas/isaric_schema.py`` each time a new ARC version is released.

Converting data to the ISARIC schema
-------------------------------------

The tool used to transform source datasets into the ISARIC schema is
`ADTL <https://adtl.readthedocs.io/en/latest/index.html>`_ (Another Data
Transformation Language). ADTL reads a TOML **parser file** which describes
how each field in the source data maps to the ISARIC schema, then writes
the two output tables.

There are two paths for generating a parser, depending on how the source
data was collected:

Data collected via BRIDGE / REDCap
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If data was collected using a CRF built with `BRIDGE <https://bridge.isaric.org>`_,
the REDCap export already uses ARC variable names. A parser for this data can
be **auto-generated** from the ARC file using ``schemas/draft_parser.py``:

.. code-block:: bash

   python schemas/draft_parser.py

This produces a file ``schemas/global_arc_{version}_parser.toml`` that covers
all ARC variables and handles the REDCap checkbox/radio/list field encoding
conventions. For a study that uses a defined preset, pass the preset name:

.. code-block:: bash

   python schemas/draft_parser.py --preset "preset_ARChetype Disease CRF_Covid"

The generated file will contain ``TODO: FILL THIS IN`` markers for
dataset-specific fields (such as ``dataset_id`` and ``dataset_disease``)
that cannot be inferred automatically, and must be filled in before it can be used.

Once edited, the parser can be used to convert the REDCap export into the ISARIC schema:

.. code-block:: bash

   adtl parse <your parser file> <your-data-file.csv> --include-transform schemas/isaric-transformations.py

Note that the ``--include-transform`` option is required as a source for the ISARIC-specific
transformations used in the auto-generated parser.

Data collected using other tools
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If data was **not** collected via a BRIDGE CRF, you will need to write a
custom parser. The parser is a TOML file that maps your source column
names and data formats to the ISARIC schema fields.

A worked example covering a COVID-19 study is available in
``docs/examples/``. See :ref:`writing-a-parser` for a full walkthrough.

Further reading
---------------

- `ADTL documentation <https://adtl.readthedocs.io/en/latest/index.html>`_ — full reference for the parser format and CLI.
- :ref:`writing-a-parser` — step-by-step tutorial for writing a custom parser.
- :ref:`data-capture-schema` — the clinical schema that defines the observation phases.
