
``Config``
==========

Use the settings specified below to control how ``PLSSDesc`` objects are
parsed into tracts, and/or how ``Tract`` objects are parsed into
lots/aliquots.

Feed to ``Config`` all desired config settings as a single string,
separated by comma, with spaces optional::

    # default_ns of 's'; default_ew of 'w'; and set 'clean_qq' status.
    cf_object = Config('s, w, clean_qq')

You need not work with ``Config`` objects directly. Any string you can
use to create a ``Config`` object, you can alternatively pass directly
to ``config=<str>`` parameter in the appropriate method, function, or
class:

.. code-block:: python

    cf = Config('s, w, clean_qq')

    plss = PLSSDesc(
        'T154-R97W Sec 14: NE',
        config='s, w, clean_qq',
        parse_qq=True)

    tract = Tract(
        desc='NE',
        trs='154n97w14',
        config='s, w, clean_qq',
        parse_qq=True)



All config settings and methods
-------------------------------

See below for a list of all possible ``config`` settings, and a misc.
``Config`` methods.

.. autoclass:: pytrs.Config
    :members:
