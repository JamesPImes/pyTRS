
``MasterConfig``
================

At the user-facing level, ``MasterConfig`` serves only to control
default behavior of ``default_ns`` and ``default_ew`` when not specified
for a particular instance of an object, or a particular call to a method
or function.

.. code-block:: python

    # These are the initial values.
    MasterConfig.default_ns = 'n'
    MasterConfig.default_ew = 'w'

    # N/S and E/W are not specified in this description, and we have not
    # configured it with `config=` parameter.
    plss = PLSSDesc('T154-R97 Sec 14: NE/4')
    plss.print_desc()

Above prints the following, having assumed ``'n'`` and ``'w'``::

    154n97w14: NE/4


.. code-block:: python

    MasterConfig.default_ns = 's'
    MasterConfig.default_ew = 'e'

    # N/S and E/W are not specified in this description, and we have not
    # configured it with `config=` parameter.
    plss = PLSSDesc('T154-R97 Sec 14: NE/4')
    plss.print_desc()

Above prints the following, now having assumed ``'s'`` and ``'e'``::

    154s97e14: NE/4


However, if configured for a given object, the master will not be used.

.. code-block:: python

    MasterConfig.default_ns = 's'
    MasterConfig.default_ew = 'e'

    # N/S and E/W are not specified in this description, and we have
    # configured only 'n' (i.e. default_ns='n'), but not default_ew.
    plss = PLSSDesc('T154-R97 Sec 14: NE/4', config='n')
    plss.print_desc()


Above prints the following, having used the configured ``'n'`` for this
``PLSSDesc`` object--but assumed ``'e'``, since that was not configured
for this particular object::

    154n97e14: NE/4



(Implemented at ``pytrs.parser.config.master_config`` but automatically
imported as a top-level class, ``pytrs.MasterConfig``.)


.. autoclass:: pytrs.MasterConfig
    :members:
