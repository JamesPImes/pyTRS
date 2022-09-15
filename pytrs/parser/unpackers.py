
"""
Functions to unpack regex matches into their intended components.
"""

import re

from .rgxlib import *
from .config import (
    DefaultEWError,
    DefaultNSError,
    MasterConfig,
)


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


# Tools for interpreting lot_with_aliquot_regex match objects:

def get_leading_aliquot(mo):
    """
    INTERNAL USE:

    :return: The string of the leading aliquot component from a
    multilot_with_aliquot_regex match object. Returns empty string if
    that group was not found in the match.
    """
    groups = mo.groupdict()
    aliquot = groups.get('aliquot', '')
    if aliquot is None:
        return ''
    return aliquot


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


# For unpacking Twp/Rge regex matches.

def unpack_twprge(
        twprge_mo,
        default_ns=None,
        default_ew=None,
        ocr_scrub=False) -> str:
    """
    INTERNAL USE:

    Take a match object of a twprge_regex pattern, and return a
    string in the format of 'T000N-R000W' (or fewer 0's, as applicable).
    """

    if default_ns is None:
        default_ns = MasterConfig.default_ns
    if default_ns not in MasterConfig._LEGAL_NS:
        raise DefaultNSError

    if default_ew is None:
        default_ew = MasterConfig.default_ew
    if default_ew not in MasterConfig._LEGAL_EW:
        raise DefaultEWError

    groups = twprge_mo.groupdict()

    twp_num = groups['twpnum']
    if ocr_scrub:
        twp_num = ocr_scrub_alpha_to_num(twp_num)
    # Clean up any leading '0's in twp_num.
    # (Try/except is used to handle twprge_ocr_scrub_regex mo's,
    # which can contain alpha characters in `twp_num`.)
    try:
        twp_num = str(int(twp_num))
    except ValueError:
        pass

    ns = default_ns
    if groups['ns'] is not None:
        ns = groups['ns'][0]
    ns = ns.upper()

    rge_num = groups['rgenum']
    if rge_num is None:
        # Weird edge case for "Range 2 [East/West]", because it
        # alone requires "Range" be specified before the number, to
        # avoid over-matching "Lot 2, N2 W2" as <'T2N-R2W'> (for
        # example).
        rge_num = groups['rgenum_edgecase_rge2']
    # Clean up any leading '0's in rge_num.
    # (Try/except is used to handle twprge_ocr_scrub_regex mo's,
    # which can contain alpha characters in `rge_num`.)
    if ocr_scrub:
        rge_num = ocr_scrub_alpha_to_num(rge_num)
    try:
        rge_num = str(int(rge_num))
    except ValueError:
        pass

    ew = default_ew
    if groups['ew'] is not None:
        ew = groups['ew'][0]
    ew = ew.upper()

    return f"T{twp_num}{ns}-R{rge_num}{ew}"


def ocr_scrub_alpha_to_num(txt):
    """
    INTERNAL USE:
    Convert non-numeric characters that are commonly mis-recognized
    by OCR to their apparently intended numeric counterpart.
    USE JUDICIOUSLY!
    """

    # This should only be used on strings whose characters MUST be
    # numeric values (e.g., the '#' here: "T###N-R###W" -- i.e. only on
    # a couple .group() components of the match object).
    # Must use a ton of context not to over-compensate!
    txt = txt.replace('S', '5')
    txt = txt.replace('s', '5')
    txt = txt.replace('O', '0')
    txt = txt.replace('I', '1')
    txt = txt.replace('l', '1')
    txt = txt.replace('L', '1')
    return txt
