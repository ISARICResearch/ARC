.. _arc-python:

ARC Python Package
==================

ARC can also be installed and used as an importable Python package (also library) named ``arc``, provided you have a clone of the `GitHub repository <https://github.com/ISARICResearch/ARC>`_. The package source files exist in the :file:`src/arc` subfolder, relative to the root of the project.

The only system-level requirement is a minimum of Python 3.12+, although Python 3.11 should also be generally fine on most platforms.

Different methods of installation are described in more detail below.

.. _arc-python-install:

Installation
------------

This is a basic guide to installing and use ARC as a Python package. Please note that there is no public PyPI package that you can :command:`pip install` from. All the installation methods described below require a local copy of the project, which typically will be a Git clone from GitHub.

.. _arc-python-non-editable-install:

Non-Editable Installation
~~~~~~~~~~~~~~~~~~~~~~~~~

From the root of a local clone of the repository you can install the package in non-editable mode with either ``pip``:

.. code:: shell

   python3 -m pip install .

or `Astral UV <https://docs.astral.sh/uv/>`_:

.. code:: shell

   uv sync --active --verbose --all-groups --no-cache --refresh --inexact

.. note::

   ``uv`` by default installs and manages all dependencies in a hidden subfolder named ``.venv`` located in the working directory where it was installed. This may cause problems if you already have a different (e.g. pre-existing or working) environment you wish to use: in this case, either export the path to the preferred environment via the `UV_PROJECT_ENVIRONMENT <https://docs.astral.sh/uv/reference/environment/#uv_project_environment>`__ environment variable, or use the ``--active`` flag to target the active environment.

.. todo::

   TODO

.. _arc-python-editable-install:

Editable Installation
~~~~~~~~~~~~~~~~~~~~~

.. todo::

   TODO


Direct Use from Source
~~~~~~~~~~~~~~~~~~~~~~

You can also use the package source files directly, provided you install all the project dependencies - but not the project itself -  into the working environment, for example, with ``uv`` using a variant of the command above with the addition of the ``--no-install-project`` flag, e.g.:

.. code:: shell

   uv sync --active --verbose --all-groups --no-install-project --no-cache --refresh --inexact

.. todo::

   TODO
