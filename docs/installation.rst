Installation
============

To install senaite.archive in your SENAITE instance, simply add this add-on
in your buildout configuration file as follows, and run `bin/buildout`
afterwards:

.. code-block:: ini

    [buildout]

    ...

    [instance]
    ...
    eggs =
        ...
        senaite.archive


With this configuration, buildout will download and install the latest published
release of `senaite.archive from Pypi`_.

Once buildout finishes, start the instance, login with a user with "Site
Administrator" privileges and activate the add-on:

http://localhost:8080/senaite/prefs_install_products_form

.. note:: It assumes you have a SENAITE instance listening to port 8080

.. note:: For high-demand instances, is strongly recommended to use this add-on
   together with `senaite.queue`_. senaite.archive delegates the archiving of
   records to senaite.queue when installed and active. Otherwise, the archiving
   takes place in a single transaction.


.. Links

.. _senaite.archive from Pypi: https://pypi.org/project/senaite.archive
.. _senaite.queue: https://pypi.python.org/pypi/senaite.queue