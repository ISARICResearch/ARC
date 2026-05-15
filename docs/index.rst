.. ARC documentation master file, created by
   sphinx-quickstart on Thu Apr 30 13:31:01 2026.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

ARC documentation
=================

.. image:: _static/arc-logo.png
   :height: 252.017
   :width:  304

`ARC <https://github.com/ISARICResearch/ARC>`_ (Analysis and Research Compendium) is a comprehensive library of questions developed by `ISARIC <https://isaric.org/>`_ that can be used to rapidly build standardised Case Report Forms (CRF) for disease outbreaks. It covers a wide range of patient-related information, including demographics, comorbidities, signs and symptoms, medications, outcomes, and more. Each question in ARC has specific guidelines and relevant parameters, such as definitions, answer options, units, minimum and maximum limits, data types, skip logic, and more.

ARC is designed to serve as a resource for researchers and healthcare professionals involved in the study of outbreaks and emerging public health threats. Here's what you need to know:

- **Machine-Readable**: ARC is provided in CSV format, making it easy for automated systems to read and process the data.

- **Open Access**: ARC is made openly available for the research community. While contributions are limited to authorized individuals, the document can be freely accessed and utilized by others.

- **Version Control**: We continue to improve ARC by adding new questions and implementing structural changes. We maintain a comprehensive `history of changes <https://github.com/ISARICResearch/ARC/commits/main/>`_ made to ARC using GitHub's version control. This ensures document integrity, traceability of changes, and seamless collaboration among researchers. Previous ARC versions may be accessed via this repository’s `releases <https://github.com/ISARICResearch/ARC/releases>`_. Additional questions can be added to future ARC versions by contacting us at: :email:`data@isaric.org`.

- **Integration with the Clinical Epidemiology Platform**: ARC is integrated into `BRIDGE <https://github.com/ISARICResearch/BRIDGE>`_, our software tool for CRF generation.

ARC is licensed under the `Open Source Initiative (OSI) <https://opensource.org>`_-compliant `MIT license <https://opensource.org/license/mit>`_.

.. image:: _static/osi-badge-light.svg
   :height: 200px
   :width:  200px
   :target: https://opensource.org/license/mit

Key elements of ARC, including the schema itself, can be explored in more detail below from the linked pages.

.. toctree::
   :maxdepth: 1
   :caption: Table of Contents:

   sources/arc-schema
   sources/variable-naming
   sources/special-field-types
   sources/lists/lists
   sources/data-capture-schema
   sources/archetype-crfs-and-templates
   sources/arc-latest
   sources/using-arc
   sources/contributors
