.. _citing-arc:

Citing ARC
==========

ARC is **published** on `GitHub <https://github.com/ISARICResearch/ARC/releases>`_ and `Zenodo <https://zenodo.org/records/21337201>`_. It has the DOI:

`10.5281/zenodo.14113727 <https://doi.org/10.5281/zenodo.14113727>`_

ARC can be **cited** as follows:

	Garcia-Gallo E, Duque-Vallejo S, Darji D, Liggins P, Murthy SR, Edinburgh T, Lunn M, Kelly S, Bourner J, Chang A, Chernyavskaya A, Carson G, Cummings M, Davtian L, de Oliveira VSB, Diaz J, Dunning J, Hashmi M, Hassan Z, Ho A, Horby P, Jackson C, Judd C, Kiseleva A, Le Prevost M, Lim WS, Mello C, Murthy S, Olliaro P, Reyes LF, Rojek A, Rylance J, Sauer L, Semple C, Sconza R, Sharin L, Siddiqui A, Uyeki T, Watson H, Wu J, Pesonel E, Munblit D, Demidova A, Merson L. ISARIC ARC (v1.5.0). *ISARIC* |year|. doi:`10.5281/zenodo.14113727 <https://doi.org/10.5281/zenodo.14113727>`_

.. _note-for-maintainers-and-contributors:

A Note For Maintainers & Contributors
-------------------------------------

Maintainers and contributors should note that the `citation file <https://github.com/ISARICResearch/ARC/blob/main/CITATION.cff>`_ should be kept up-to-date with changes in authorship. The file can be validated on the command line using the `cffconvert <https://github.com/citation-file-format/cffconvert>`_ library using the following command run from the root of the ARC repository:

.. code:: shell

   cffconvert --validate

Any reported errors should be fixed, and the file staged and committed in the normal way. Citation file validation is included in the pre-commit status checks that happen automatically in GitHub on branch and PR updates.
