
``Config``
==========

You need not work with ``Config`` objects directly. Any string you can
use to create a ``Config`` object, you can alternatively pass directly
to ``config=<str>`` parameter in the appropriate method, function, or
class, such as:

.. code-block:: python

    cf = Config('clean_qq')
    plss = PLSSDesc('T154N-R97W Sec 14: NE', config='clean_qq', parse_qq=True)
    tract = Tract('NE', trs='154n97w14', config='clean_qq', parse_qq=True)

(Implemented at ``pytrs.parser.config.config`` but automatically
imported as a top-level class, ``pytrs.Config``.)


.. autoclass:: pytrs.Config
    :members:
