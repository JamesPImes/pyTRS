
"""
Functions to unpack regex matches into their intended components.
"""

import re

from .rgxlib import *


# Unpacking lot_regex, multilot_regex, and lot_with_aliquot_regex matches.

def is_multi_lot(multilots_mo) -> bool:
    """
    INTERNAL USE:
    Whether a multilot_regex (or multilot_with_aliquots_regex) match
    object found more than one lot (True) or if it is only one lot
    (False).

    WARNING: Do not pass a match object for any other regex pattern.
    """
    if multilots_mo['lotnum_rightmost'] is not None:
        return True
    elif multilots_mo['lotnum'] is not None:
        return False
    raise ValueError


# Unpacking multisec_regex.

def is_multi_sec(multisec_mo) -> bool:
    """
    INTERNAL USE:
    Whether a multisec_regex match object found more than one sec (True)
    or if it is only one sec (False).

    WARNING: Do not pass a match object for any other regex pattern.
    """
    if multisec_mo['secnum_rightmost'] is not None:
        return True
    elif multisec_mo['secnum'] is not None:
        return False
    raise ValueError
