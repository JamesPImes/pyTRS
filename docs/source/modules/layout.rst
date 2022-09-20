
``layout`` in PLSS parsing
==========================

By design, the Public Land Survey System itself does not place many
strict limitations on the syntax of Township, Range, Section, and
'description block' -- i.e., they can appear in essentially any order
(except that Township pretty much always comes before Range). Below are the different
permutations (called ``layout`` in this library) that can be handled by
pyTRS:

``'TRS_desc'``
--------------

*Twp > Rge > Sec > Descripton Block*

Examples::

    T154N-R97W, Sec 14: NE/4

::

    T1S-R7E
    Sec 9: S/2

(May appear on one ore multiple lines.)


``'TR_desc_S'``
---------------

*Twp > Rge > Description Block > Sec*

Examples::

    T154N-R97W
    NE/4 of Sec 14

::

    T1S-R7E, S/2 of Sec 9


``'desc_STR'``
--------------

*Description Block > Sec > Twp > Rge*

Examples::

    NE/4 of Sec 14, T154N-R97W

::

    S/2 of Sec 9, T1S-R7E


``'S_desc_TR'``
---------------

*Sec > Description Block > Twp > Rge*

Examples::

    Sec 14: NE/4, T154N-R97W

::

    Sec 9: S/2, T1S-R7E

*(If you're writing land descriptions like this, please stop doing that.)*


``'copy_all'``
--------------

This is a stopgap layout used by pyTRS to ensure that the text is
maintained in the event that a more meaningful layout cannot be
successfully deduced (perhaps due to an omission or unrecognizable
misspelling of section, township, or range).


Usage
^^^^^

Because the components can appear in varying order, a PLSS description
will be parsed differently, which is why the concept of ``layout``
exists in this library at all.

In general, the parsing algorithm is capable of deducing the ``layout``
of the input data. However, the ``layout`` can also be dictated by the
user via ``config=<any of the above layout options>`` parameter:

.. code-block:: python

    txt='T154N-R97W Sec 14: NE/4'
    plss = PLSSDesc(txt, config='TRS_desc')

However, doing so is not recommended unless you reliably know the
layout of your dataset and want to capture errors very strictly.


.. note::

    You can get a tuple of all currently implemented ``layout`` options
    in ``pytrs.IMPLEMENTED_LAYOUTS``. Get a string containing examples
    of each in ``pytrs.IMPLEMENTED_LAYOUT_EXAMPLES``.


Limitations
^^^^^^^^^^^

You will notice that the above ``layout`` options do not account
for descriptions where the Section is couched within the
description block itself, like so::

    T154N-R97W
    That part of the NE/4 of Section 14 lying north of the river

...or...

::

    That part of the NE/4 of Section 14 lying north of the river, in
    T154N-R97W

That's a target area for improvement in future versions.

*(These two examples would both be interpreted as follows, assuming the
parser is allowed to deduce the layout.)*

::

    154n97w14: That part of the NE/4