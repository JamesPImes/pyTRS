
pyTRS
=====

.. automodule:: pytrs


Feel free to reach out via
`my GitHub <https://github.com/JamesPImes/pyTRS//>`_
with feedback or inquiries, or to let me know if you run into any
issues.

Also visit the GitHub page for a
`quickstart guide <https://github.com/JamesPImes/pyTRS/blob/master/guides/guides/quickstart.md>`_.

Bird's-eye View
---------------

.. code-block:: python

    import pytrs

The two primary parsing classes in the library are ``PLSSDesc`` and
``Tract``, which are automatically imported as top-level classes.

The conceptual difference between these two classes is that a ``Tract``
represents land within a single specific section; whereas a ``PLSSDesc``
can represent land across any number of sections in any number of
townships (i.e. one or more tracts).

Parsing a ``PLSSDesc`` object will create one or more ``Tract`` objects.

``Tract`` objects can also be created directly, for when our dataset
already has the description blocks separated from their respective
Twp/Rge/Sec.

``Tract`` objects can also be parsed, in which case they will break down
their respective descriptions into lots and aliquot "quarter-quarters".

Top-level classes and functions
-------------------------------

These classes and functions are all imported with ``import pytrs``.


Classes for parsing:

.. toctree::
    modules/plssdesc
    modules/tract
    modules/trs


Classes for configuring the parsers:

.. toctree::
    modules/config
    modules/master_config


Classes that are containers/extractors for parsed data:

.. toctree::
    modules/tractlist
    modules/trslist


Misc functions:

.. toctree::
    modules/toplevel_functions


Information on layouts:

.. toctree::
    modules/layout


Additional modules
------------------

(These modules are *not* imported by default.)


Robust writing of parsed data to .csv files:

.. toctree::
    modules/tractwriter


Tkinter-based GUI applications for getting user config data and Tract
attributes:

.. toctree::
    modules/interface_tools


Misc. utility functions:

.. toctree::
    modules/utils

License

.. toctree::
    modules/license

Indices and tables
==================

* :ref:`genindex`
* :ref:`search`
