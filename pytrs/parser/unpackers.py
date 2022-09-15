
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
    return is_multi('lot', multilots_mo)


def get_rightmost_lot(multilot_mo) -> str:
    """
    Get the rightmost lot from a lot_regex, multilot_regex, or
    multilot_with_aliquot_regex match object.
    :param multilot_mo:
    :return:
    """
    return get_rightmost('lot', multilot_mo)


# Unpacking multisec_regex.

def is_multi_sec(multisec_mo) -> bool:
    """
    INTERNAL USE:
    Whether a multisec_regex match object found more than one sec (True)
    or if it is only one sec (False).

    WARNING: Do not pass a match object for any other regex pattern.
    """
    return is_multi('sec', multisec_mo)


def get_rightmost_sec(multisec_mo) -> str:
    """
    Get the rightmost lot from a lot_regex, multilot_regex, or
    multilot_with_aliquot_regex match object.
    :param multilot_mo:
    :return:
    """
    return get_rightmost('sec', multisec_mo)


# General functions.


def is_multi(kind, mo) -> bool:
    """
    INTERNAL USE:
    Whether a multisec_regex, multilot_regex, or
    multilot_with_aliquots_regex match object found more than one sec /
    lot (True) or if it is only one sec / lot (False).

    WARNING: Do not pass a match object for any other regex pattern.

    :param kind: Either 'lot' or 'sec', depending on whether we're
    figuring out whether this is a multi-lot or a multi-sec.
    :param mo: a match object for multisec_regex, multilot_regex, or
    multilot_with_aliquots_regex.
    """
    # 'lot' will match named groups 'lotnum_rightmost' and 'lotnum' in
    # the lot-type regexes; and 'sec' will match 'secnum_rightmost' and
    # 'secnum' in sec-type regex.
    if kind not in ('lot', 'sec'):
        raise ValueError
    if mo[f'{kind}num_rightmost'] is not None:
        return True
    elif mo[f'{kind}num'] is not None:
        return False
    raise ValueError


def thru_rightmost(mo) -> bool:
    """
    INTERNAL USE:
    Whether the word 'through' (or an abbreviation) appears before the
    rightmost sec/lot in a match object for multisec_regex,
    multilot_regex, or multilot_with_aliquots_regex.

    WARNING: Do not pass a match object for any other regex pattern.
    """
    # Do NOT check 'through' named group directly, because it will match
    # if it exists, even if it is not the rightmost. But 'intervener'
    # should always be the rightmost 'through' or 'and'.

    # Assume that a regex pattern with named group 'intervener' was used.
    txt = mo['intervener']
    if txt is None:
        return False
    txt = txt.strip()
    return through_regex.search(txt) is not None


def get_rightmost(kind, mo) -> str:
    """
    INTERNAL USE:
    Whether a multisec_regex, multilot_regex, or
    multilot_with_aliquots_regex match object found more than one sec /
    lot (True) or if it is only one sec / lot (False).

    WARNING: Do not pass a match object for any other regex pattern.

    :param kind: Either 'lot' or 'sec', depending on whether we're
    figuring out whether this is a multi-lot or a multi-sec.
    :param mo: a match object for multisec_regex, multilot_regex, or
    multilot_with_aliquots_regex.
    """
    # 'lot' will match named groups 'lotnum_rightmost' and 'lotnum' in
    # the lot-type regexes; and 'sec' will match 'secnum_rightmost' and
    # 'secnum' in sec-type regex.
    if kind not in ('lot', 'sec'):
        raise ValueError
    groups = mo.groupdict()
    if f'{kind}num_rightmost' not in groups.keys():
        return mo[f'{kind}num']
    elif is_multi(kind, mo):
        return mo[f'{kind}num_rightmost']
    else:
        return mo[f'{kind}num']
