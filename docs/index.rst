===============
senaite.archive
===============

This add-on enables records archiving for `SENAITE LIMS`_, so users with enough
privileges (Manager and LabManager) can shrink the size of the database and
improve the overall performance of the system by archiving inactive objects
that are outside of a predefined retention period in years.

`senaite.archive`_ extracts old objects from SENAITE and store them on the
server's filesystem in both human and machine readable format (XML), making
forensic audits easier. Data is stored locally thanks to `Zope's genericsetup`_,
so future recovery of records is also possible.

The types of records that can be archived are Samples (aka AnalysisRequest),
together with all the information they contain (Analyses, reports, etc.),
Batches and Worksheets.

Once installed, this add-on allows the laboratory to:

* Define the retention period of data in years
* Define the local directory where data will be stored for archiving purposes
* Archive no longer active records that are outside of the retention period
* Perform historic searches against archived records


Table of Contents:

.. toctree::
   :maxdepth: 2

   installation
   quickstart
   changelog
   license


.. Links

.. _SENAITE LIMS: https://www.senaite.com
.. _senaite.archive: https://pypi.org/senaite.archive
.. _Zope's genericsetup: https://productsgenericsetup.readthedocs.io
