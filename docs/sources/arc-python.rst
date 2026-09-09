.. _arc-python:

ARC Python Package
==================

ARC can also be installed and used as an importable Python package (also library) named ``isaric-arc``, provided you have a clone of the `GitHub repository <https://github.com/ISARICResearch/ARC>`_. The package source files exist in the :file:`src/arc` subfolder, relative to the root of the project.

The only system-level requirement is a minimum of Python 3.12+, although Python 3.11 should also be generally fine on most platforms.

Different methods of installation are described in more detail below, as well as a very basic usage guide.

.. _arc-python-install:

Installation
------------

This is a basic guide to installing and using ARC as a Python package. Please note that there is currently **no public PyPI package** that you can :command:`pip install` from. All the installation methods described below require a local copy of the GitHub project, typically via a Git clone from GitHub.

.. _arc-python-non-editable-install:

Non-Editable Installation
~~~~~~~~~~~~~~~~~~~~~~~~~

From the root of a local clone of the repository you can install the package in non-editable mode with either ``pip``:

.. code:: shell

   python3 -m pip install .

or `Astral UV <https://docs.astral.sh/uv/>`_:

.. code:: shell

   uv sync --active --verbose --all-groups --no-editable --no-cache --refresh --inexact

.. note::

   ``uv`` by default installs and manages all dependencies in a hidden subfolder named ``.venv`` located in the working directory where it was installed. This may cause problems if you already have a different (e.g. pre-existing or working) environment you wish to use: in this case, either export the path to the preferred environment via the `UV_PROJECT_ENVIRONMENT <https://docs.astral.sh/uv/reference/environment/#uv_project_environment>`__ environment variable, or use the ``--active`` flag with :command:`uv sync` to target the active environment.

This will result in a Python package named ``isaric-arc`` in the working environment, which can be imported as ``arc`` in a Python shell:

.. code:: python

   >>> import arc; arc.__version__
   '0.1.0'

Note that the displayed version is **not the ARC schema version** but the Python package version - the two are versioned separately. Also note that not all the Python modules in ``arc`` are pure libraries - some are intended to be used as command line scripts, e.g. for generating parsers for the :ref:`ISARIC data schema <isaric-data-schema>`.

.. _use-from-source:

Use from Source
~~~~~~~~~~~~~~~

You can also use the ARC package source files directly, provided you install all the project dependencies - but not the project itself -  into the working environment, for example, with ``uv``, using a variant of the command above with the addition of the ``--no-install-project`` flag, e.g.:

.. code:: shell

   uv sync --active --verbose --all-groups --no-install-project --no-cache --refresh --inexact

You can then import the ``arc`` package in a Python shell as normally, with a preliminary step to tell Python where to find the source files.

.. code:: python

   >>> import sys; sys.path.insert(0, 'src')
   >>> import arc; arc.__version__
   '0.1.0'


.. _usage:

Usage
-----

Whichever way you have decided to use the ARC package, either from a non-editable installation, or directly from source, as described above, once it is available you can import in any Python shell provided they are both part of the same environment.

The following snippet shows how the latest ARC release version can be obtained, and with it the corresponding data dictionary, ARChetype CRF presets list, and the associated commit SHA.

.. code:: python

   >>> from arc.arc_core import get_arc_versions, get_arc
   >>> latest_version = get_arc_versions()[1]
   >>> latest_version
   'v1.5.0'
   >>> arc_data_dictionary, presets_list, commit_sha = get_arc(latest_version)
   >>> arc_data_dictionary
                 Form             Section  ... Branch                                   Question_english
   0     presentation                 NaN  ...                   Participant Identification Number (PIN)
   1     presentation  INCLUSION CRITERIA  ...         Suspected or confirmed infection, condition, o...
   2     presentation  INCLUSION CRITERIA  ...         Is the suspected or confirmed infection, condi...
   3     presentation  INCLUSION CRITERIA  ...                                Case classification status
   4     presentation  INCLUSION CRITERIA  ...                                        Reason for testing
   ...            ...                 ...  ...    ...                                                ...
   1752    withdrawal          WITHDRAWAL  ...                                        Date of withdrawal
   1753    withdrawal          WITHDRAWAL  ...                                     Reason for withdrawal
   1754    withdrawal          WITHDRAWAL  ...         Did the participant withdraw from active parti...
   1755    withdrawal          WITHDRAWAL  ...         Did the participant withdraw consent to use da...
   1756    withdrawal          WITHDRAWAL  ...         Did the participant withdraw consent to use sa...
   >>>
   >>> preset_list
   [['ARChetype Disease CRF', 'Covid'],
    ['ARChetype Disease CRF', 'H5Nx'],
    ['ARChetype Disease CRF', 'Dengue'],
    ['ARChetype Disease CRF', 'Chikungunya'],
    ['ARChetype Disease CRF', 'Mpox'],
    ['ARChetype Disease CRF', 'Mpox Pregnancy and Paediatric'],
    ['ARChetype Syndromic CRF', 'ARI'],
    ['ARChetype Syndromic CRF', 'VHF'],
    ['ARChetype Syndromic CRF', 'Encephalitis'],
    ['ARChetype Syndromic CRF', 'Arbovirus'],
    ['Score', 'CharlsonCI'],
    ['Score', 'mSOFA'],
    ['Score', 'mSOFA Dengue'],
    ['Recommended Outcomes', 'Dengue'],
    ['Populations', 'Paediatric'],
    ['Populations', 'Pregnancy']]
   >>>
   >>> commit_sha
   'daa4daf97ab66edccfaac36d71c7d7c354ae9c17'

A more detailed usage will be added at some point. Refer to the `ARC package source <https://github.com/ISARICResearch/ARC/tree/main/src/arc>`_ for more details on available libraries.
