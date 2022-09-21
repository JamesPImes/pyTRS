
``TRS``
=======

Standardized TRS format
^^^^^^^^^^^^^^^^^^^^^^^

The pyTRS library uses a standardized format to represent Twp/Rge/Sec.

+------------+------------------------------------------------------------+-------------+
| Component  | Format                                                     | Example     |
+============+============================================================+=============+
| Twp        | Up to three digits, plus ``'n'`` or ``'s'`` for direction  | ``'154n'``  |
+------------+------------------------------------------------------------+-------------+
| Rge        | Up to three digits, plus ``'e'`` or ``'w'`` for direction  | ``'97w'``   |
+------------+------------------------------------------------------------+-------------+
| Sec        | Exactly 2 digits, with leading "0" if needed               | ``'01'``    |
+------------+------------------------------------------------------------+-------------+


These are combined to form the trs in a standardized format:

- ``Section 14 of T154N-R97W`` becomes ``'154n97w14'``
- ``Section 1 of T7S-R9E becomes`` ``'7s9e01'``


Undefined Twp/Rge/Sec
^^^^^^^^^^^^^^^^^^^^^

When a ``Tract`` or ``TRS`` object is created without specifying
Twp/Rge/Sec, its ``.trs`` is set to the undefined value
``'___z___z__'``, i.e.:

+------------+-------------+
| Component  | Format      |
+============+=============+
| Twp        | ``'___z'``  |
+------------+-------------+
| Rge        | ``'___z'``  |
+------------+-------------+
| Sec        | ``'__'``    |
+------------+-------------+


Error Twp/Rge/Sec
^^^^^^^^^^^^^^^^^

When a ``Tract`` or ``TRS`` object is created and its Twp/Rge/Sec
couldn't be deciphered (or when a ``PLSSDesc`` couldn't parse a
Twp/Rge/Sec that made sense), the ``.trs`` is set to the error value
``'XXXzXXXzXX'``, i.e.:

+------------+-------------+
| Component  | Format      |
+============+=============+
| Twp        | ``'XXXz'``  |
+------------+-------------+
| Rge        | ``'XXXz'``  |
+------------+-------------+
| Sec        | ``'XX'``    |
+------------+-------------+


``TRS`` class attributes and methods
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


.. autoclass:: pytrs.TRS
    :members:
