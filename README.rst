Records archiving for SENAITE LIMS
==================================

.. image:: https://img.shields.io/pypi/v/senaite.archive.svg?style=flat-square
    :target: https://pypi.python.org/pypi/senaite.archive

.. image:: https://img.shields.io/travis/com/senaite/senaite.archive/1.3.x.svg?style=flat-square
    :target: https://travis-ci.com/senaite/senaite.archive

.. image:: https://readthedocs.org/projects/pip/badge/
    :target: https://senaitearchive.readthedocs.org

.. image:: https://img.shields.io/github/issues-pr/senaite/senaite.archive.svg?style=flat-square
    :target: https://github.com/senaite/senaite.archive/pulls

.. image:: https://img.shields.io/github/issues/senaite/senaite.archive.svg?style=flat-square
    :target: https://github.com/senaite/senaite.archive/issues

.. image:: https://img.shields.io/badge/Made%20for%20SENAITE-%E2%AC%A1-lightgrey.svg
   :target: https://www.senaite.com


About
-----

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

Documentation
-------------

* https://senaitearchive.readthedocs.io

Feedback and support
--------------------

* `Community site`_
* `Gitter channel`_
* `Users list`_

License
-------

**SENAITE.ARCHIVE** Copyright (C) 2021 RIDING BYTES & NARALABS

This program is free software; you can redistribute it and/or modify it under
the terms of the `GNU General Public License version 2`_ as published by the
Free Software Foundation.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.


.. Links

.. _SENAITE LIMS: https://www.senaite.com
.. _Community site: https://community.senaite.org/
.. _Gitter channel: https://gitter.im/senaite/Lobby
.. _Users list: https://sourceforge.net/projects/senaite/lists/senaite-users
.. _GNU General Public License version 2: https://github.com/senaite/senaite.archive/blob/master/LICENSE
.. _senaite.archive: https://pypi.org/senaite.archive
.. _Zope's genericsetup: https://productsgenericsetup.readthedocs.io

