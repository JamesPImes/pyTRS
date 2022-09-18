
"""
INTERNAL USE:

Functions and classes to unpack regex matches and corresponding text
blocks into their intended components.
"""

import re

from ..rgxlib import *
from ..config import (
    DefaultEWError,
    DefaultNSError,
    MasterConfig,
)


# Unpacking lot_regex, multilot_regex, and lot_with_aliquot_regex matches,
# and lot text blocks.

class LotUnpacker:
    """A class to unpack lot text blocks."""

    def __init__(self, txt):
        self.lot_list = []
        self.lot_acres = {}
        self.flags = []
        self.flag_lines = []
        # aliquots_through is the number of lots (counting from the left)
        # to which to apply an aliquot subdivision to (i.e.include_lot_divs)
        # if such a subdivision is found before this lot text.
        # Specifically, we will add aliquots until we encounter the second
        # occurrence of the word 'Lot(s)'.
        self.aliquots_through = 1
        self.unpack_lots(txt)

    def unpack_lots(self, txt):
        """
        Unpack the text into a list of lots (``.lot_list``) and dict of
        acreages (``.lot_acres``, if any are specified in text),
        formatted as 'L#'. And populate ``.flags``, and ``.flag_lines``
        with warning data, if appropriate.
        :param txt: A chunk of text that matched a lot_regex or
        multilot_regex pattern (or similar).
        :return: None (populates the object's attributes).
        """
        # A working list of the lots. Note that this gets filled from
        # last-to-first on this working text block, but gets reversed at
        # the end.
        working_lot_list = []
        working_acreages = {}

        # Keep track of the last time we encountered the word 'Lot(s)',
        # in order to determine which lot(s) we might apply an aliquot
        # division to (if one is found). The application of aliquots
        # occurs in the TractParse class (not here), but this method
        # deduces how many lots (counting from the left) will receive
        # the aliquot.
        word_lot_encountered = 0

        found_through = False
        endpos = len(txt)
        while True:
            lot_mo = multilot_regex.search(txt, endpos=endpos)

            if lot_mo is None:
                # We're out of lot numbers.
                break

            # Pull the right-most lot number (still as a string):
            lot_num = get_rightmost_lot(lot_mo)
            lot_acreage = get_rightmost_acreage(lot_mo)

            # Assume we've found the last section and can therefore skip
            # the next loop after we've found the last section.
            endpos = 0
            if is_multi_lot(lot_mo):
                # If multiple sections remain, we will continue our
                # search next loop.
                endpos = start_of_rightmost(lot_mo)

            lot_num = int(lot_num)

            if found_through:  # during the last loop.
                # We've identified a elided list (e.g., 'Sections 3 - 9').
                previous_lot = working_lot_list[-1]
                start_of_list = lot_num
                end_of_list = previous_lot

                # Whether this elided list is in the expected order (i.e.
                # 'Sections 3 - 9' -> True; 'Sections 9 - 3' -> False).
                correct_order = start_of_list < end_of_list
                end, start, step = end_of_list - 1, start_of_list - 1, -1
                if not correct_order:
                    end, start, step = end_of_list + 1, start_of_list + 1, 1
                    flag = 'nonsequential_lots'
                    flag_line = f"{flag}<{start_of_list} - {end_of_list}>"
                    self.flags.append(flag)
                    self.flag_lines.append((flag, flag_line))

                for new_lot in range(end, start, step):
                    working_lot_list.append(new_lot)
            else:
                # A standalone section.
                working_lot_list.append(lot_num)

            if lot_mo['word_lot_rightmost'] is not None:
                word_lot_encountered = len(working_lot_list)

            if lot_acreage is not None:
                lot_name = f'L{lot_num}'
                if lot_name in self.lot_acres:
                    flag = f"dup_lot_acreage<{lot_name}({self.lot_acres[lot_name]})>"
                    self.flags.append(flag)
                    self.flag_lines.append((flag, flag))
                self.lot_acres[lot_name] = lot_acreage

            # Check for the next loop.
            found_through = thru_rightmost(lot_mo)

        working_lot_list.reverse()
        # Put into preferred format 'L#'.
        working_lot_list = [f'L{lot_num}' for lot_num in working_lot_list]
        self.lot_list.extend(working_lot_list)

        for lot, acreage in working_acreages.items():
            self.lot_acres[lot] = acreage

        # Determine how many lots (counting from the left) we can add
        # aliquot subdivision to (if any is found in the TractParser).
        self.aliquots_through = len(working_lot_list) - word_lot_encountered

        return working_lot_list


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


# Unpacking Sections / Multi-Sections textblocks and multisec_regex patterns.

class SecUnpacker:
    """A class to unpack Section and Multi-Section text blocks."""

    def __init__(self, txt):
        self.sec_list = []
        self.flags = []
        self.flag_lines = []
        self.unpack_sections(txt)

    def unpack_sections(self, txt):
        """
        Unpack the text into a list of sections (``.sec_list``),
        formatted as 2-digit strings (with leading 0 if needed). And
        populate ``.flags``, and ``.flag_lines`` with warning data, if
        appropriate.
        :param txt: A chunk of text that matched a sec_regex or
        multisec_regex pattern.
        :return: None (populates the object's attributes).
        """
        # A working list of the sections. Note that this gets filled
        # from last-to-first on this working text block, but gets
        # reversed at the end.
        working_sec_list = []

        found_through = False
        endpos = len(txt)
        while True:
            sec_mo = multisec_regex.search(txt, endpos=endpos)

            if sec_mo is None:
                # We're out of section numbers.
                break

            # Pull the right-most section number (still as a string):
            sec_num = get_rightmost_sec(sec_mo)

            # Assume we've found the last section and can therefore skip
            # the next loop after we've found the last section.
            endpos = 0
            if is_multi_sec(sec_mo):
                # If multiple sections remain, we will continue our
                # search next loop.
                endpos = start_of_rightmost(sec_mo)

            # Clean up any leading '0's in sec_num.
            sec_num = str(int(sec_num))

            # Format section number as 2 digits.
            new_sec = sec_num.rjust(2, '0')

            if found_through:  # during the last loop.
                # We've identified a elided list (e.g., 'Sections 3 - 9').
                previous_sec = working_sec_list[-1]
                start_of_list = int(sec_num)
                end_of_list = int(previous_sec)

                # Whether this elided list is in the expected order (i.e.
                # 'Sections 3 - 9' -> True; 'Sections 9 - 3' -> False).
                correct_order = start_of_list < end_of_list
                end, start, step = end_of_list - 1, start_of_list - 1, -1
                if not correct_order:
                    end, start, step = end_of_list + 1, start_of_list + 1, 1
                    flag = 'nonsequential_sections'
                    flag_line = f"{flag}<{start_of_list} - {end_of_list}>"
                    self.flags.append(flag)
                    self.flag_lines.append((flag, flag_line))

                for i in range(end, start, step):
                    add_sec = str(i).rjust(2, '0')
                    working_sec_list.append(add_sec)
            else:
                # A standalone section.
                working_sec_list.append(new_sec)

            # Check for the next loop.
            found_through = thru_rightmost(sec_mo)

        working_sec_list.reverse()
        self.sec_list.extend(working_sec_list)

        return working_sec_list


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


def twprge_natural_to_short(twprge: str) -> str:
    """
    Convert a natural Twp/Rge (e.g. 'T154N-R97W') into the standard
    abbreviation used in this library (e.g., '154n97w').
    :param twprge: A natural Twp/Rge (e.g. 'T154N-R97W')
    :return: The equivalent Twp/Rge in the standard abbreviation (e.g.,
    '154n97w').
    """
    twprge = twprge.lower()
    return re.sub(r'[rt-]', '', twprge)


def twprge_short_to_natural(twprge: str) -> str:
    """
    Convert a Twp/Rge in the standard abbreviation used in this library
    (e.g., '154n97w') into the equivalent natural Twp/Rge (e.g.
    'T154N-R97W')
    :param twprge: A Twp/Rge in the standard abbreviation (e.g.,
    '154n97w').
    :return: The equivalent natural Twp/Rge (e.g. 'T154N-R97W')
    """
    twprge = twprge.upper()
    twprge = f"T{twprge}"
    return re.sub(r'(N|S)', r'\1-R', twprge)


__all__ = [
    'LotUnpacker',
    'is_multi_lot',
    'get_rightmost_lot',
    'get_rightmost_acreage',
    'first_lot_is_plural',
    'get_leading_aliquot',
    'SecUnpacker',
    'is_multi_sec',
    'get_rightmost_sec',
    'is_multi',
    'thru_rightmost',
    'get_rightmost',
    'start_of_rightmost',
    'unpack_twprge',
    'ocr_scrub_alpha_to_num',
    'twprge_natural_to_short',
    'twprge_short_to_natural',
]
