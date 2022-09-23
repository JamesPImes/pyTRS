
``layout`` in PLSS parsing
==========================

By design, the Public Land Survey System itself does not place many
strict limitations on the syntax of Township, Range, Section, and
'description block' -- i.e., they can appear in essentially any order
(except that Township pretty much always comes before Range).


``layout`` options
------------------
Below are the different permutations (called ``layout`` in this library)
that can be handled by pyTRS:


``'TRS_desc'``
~~~~~~~~~~~~~~

*Twp > Rge > Sec > Descripton Block*

Examples::

    T154N-R97W, Sec 14: NE/4

::

    T1S-R7E
    Sec 9: S/2

(May appear on one ore multiple lines.)


``'TR_desc_S'``
~~~~~~~~~~~~~~~

*Twp > Rge > Description Block > Sec*

Examples::

    T154N-R97W
    NE/4 of Sec 14

::

    T1S-R7E, S/2 of Sec 9


``'desc_STR'``
~~~~~~~~~~~~~~

*Description Block > Sec > Twp > Rge*

Examples::

    NE/4 of Sec 14, T154N-R97W

::

    S/2 of Sec 9, T1S-R7E


``'S_desc_TR'``
~~~~~~~~~~~~~~~

*Sec > Description Block > Twp > Rge*

Examples::

    Sec 14: NE/4, T154N-R97W

::

    Sec 9: S/2, T1S-R7E

*(If you're writing land descriptions like this, please stop doing that.)*


``'copy_all'``
~~~~~~~~~~~~~~

This is a stopgap layout used by pyTRS to ensure that the text is
maintained in the event that a more meaningful layout cannot be
successfully deduced (perhaps due to an omission or unrecognizable
misspelling of section, township, or range).


Usage
-----

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
-----------

You will notice that the above ``layout`` options do not account
for descriptions where the Section is couched within the
description block itself, like so::

    T154N-R97W
    That part of Section 14 lying north of the river

...or...

::

    That part of Section 14 lying north of the river, in T154N-R97W

...or...

::

    That part of Section 14, T154N-R97W, lying north of the river

By default, each of these would be parsed into the following ``Tract``,
assuming parser is allowed to deduce the ``layout``::

    154n97w14: That part of Section 14

...and would generate an error flag of
``'unused_desc<lying north of the river>'`` (with slight variations
depending on the ``layout``).


``'sec_within'`` config setting
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

As of ``v2.1.0``, these descriptions can now be parsed by using the
``'sec_within'`` config setting, **but only** where *exactly* one tract
was identified in the text.

That said, the parser considers a multi-section to be equivalent to a
single tract for the purpose of this setting:

.. code-block:: python

    txt = 'That part of Sections 13 - 15, T154N-R97W lying north of the river'
    parsed = pytrs.PLSSDesc(txt, config='sec_within')
    parsed.pretty_print_desc()

The above prints this to console::

    T154N-R97W
    Sec 13: That part lying north of the river
    Sec 14: That part lying north of the river
    Sec 15: That part lying north of the river

Expanding this capability to multiple (unique) tracts per PLSS
description is a target area for improvement in future versions.

Combining ``'sec_within'`` and ``'segment'`` config settings *might*
allow or capture multiple tracts, but still only one tract per Twp/Rge.

.. code-block:: python

    txt = """T153N-R97W
    Sec 1: S/2N/2
    T154N-R97W
    That part of Sec 13 - 15 lying north of the river"""
    parsed = PLSSDesc(txt, config='segment, sec_within')
    parsed.pretty_print_desc()

The above prints this to console::

    T153N-R97W
    Sec 01: S/2N/2
    T154N-R97W
    Sec 13: That part lying north of the river
    Sec 14: That part lying north of the river
    Sec 15: That part lying north of the river