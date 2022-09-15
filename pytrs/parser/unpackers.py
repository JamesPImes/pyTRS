
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
    :param multilot_mo: a match object for lot_regex, multilot_regex,
    or multilot_with_aliquot_regex.
    :return:
    """
    return get_rightmost('lot', multilot_mo)


def get_rightmost_acreage(multilot_mo):
    """
    Extract the stated acreage (if any) next to the rightmost lot, and
    return it as a string.  If no acreage is found, will return None.
    :param multilot_mo: a match object for lot_regex, multilot_regex,
    or multilot_with_aliquot_regex.
    :return: The acreage as a string, or None if not found.
    """
    # Search for an acreage match from the start of the rightmost through
    # the end of the match.
    i = start_of_rightmost(multilot_mo)
    j = multilot_mo.end(0)
    acreage_mo = lot_acres_unpacker_regex.search(
        multilot_mo.string,
        pos=i,
        endpos=j)

    if acreage_mo is None:
        return None
    acreage_string = acreage_mo['acreage']
    acreage_string = acreage_string.replace('[', '')
    acreage_string = acreage_string.replace(']', '')
    acreage_string = acreage_string.replace('(', '')
    acreage_string = acreage_string.replace(')', '')
    return acreage_string


def first_lot_is_plural(multilot_mo) -> bool:
    """
    Check if the leftmost word 'Lot' is plural.
    :param multilot_mo:
    :return:
    """
    return multilot_mo['plural'] is not None


# Unpacking multisec_regex.

def is_multi_sec(multisec_mo) -> bool:
    """
    INTERNAL USE:
    Whether a multisec_regex match object found more than one sec (True)
    or if it is only one sec (False).

    WARNING: Do not pass a match object for any other regex pattern.
    :param multisec_mo: a match object for sec_regex or multisec_regex.
    """
    return is_multi('sec', multisec_mo)


def get_rightmost_sec(multisec_mo) -> str:
    """
    Get the rightmost lot from a lot_regex, multilot_regex, or
    multilot_with_aliquot_regex match object.
    :param multisec_mo: a match object for sec_regex or multisec_regex.
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
    if 'intervener' not in mo.groupdict():
        # Not a multi-<whatever> regex pattern
        return False
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

    Also returns False for 'single' matches (or where 'intervener'
    named group does not exist in the regex pattern that was used).

    WARNING: Do not pass a match object for any other regex pattern.
    """
    # Do NOT check 'through' named group directly, because it will match
    # if it exists, even if it is not the rightmost. But 'intervener'
    # should always be the rightmost 'through' or 'and'.

    # Assume that a regex pattern with named group 'intervener' was used.
    if 'intervener' not in mo.groupdict():
        # Not a multi-<whatever> regex pattern
        return False
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


def start_of_rightmost(mo):
    """
    INTERNAL USE:
    Get the start position of the rightmost 'intervener' named group
    within the match object, if found. If not found or group does not
    exist, will return the start position of the match itself.

    :param mo: a match object for multisec_regex, multilot_regex, or
    multilot_with_aliquots_regex.
    """
    if 'intervener' not in mo.groupdict():
        # Not a multi-<whatever> regex pattern
        return mo.start()
    # Assume that a regex pattern with named group 'intervener' was used.
    if mo['intervener'] is not None:
        return mo.start('intervener')
    return mo.start()
