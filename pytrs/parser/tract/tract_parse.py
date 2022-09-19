
"""
Class and functions for parsing tract descriptions that have already
been preprocessed.
"""

import re

from ..rgxlib import *
from ..unpack import (
    LotUnpacker,
)
from .aliquot_parse import (
    parse_aliquot,
    _ALL
)
from .tract_preprocess import (
    TractPreprocessor,
)


class TractParser:
    """
    INTERNAL USE:

    A class to handle the heavy lifting of parsing ``Tract`` objects
    into lots and QQ's. Not intended for use by the end-user. (All
    functionality can be triggered by appropriate ``Tract`` methods.)

    NOTE: All parsing parameters must be locked in before initializing
    the ``TractParser``. Upon initializing, the parse will be
    automatically triggered and cannot be modified.

    The ``Tract.parse()`` method is actually a wrapper for initializing
    a ``TractParser`` object, and for extracting the relevant attributes
    from it.
    """

    # Attributes that can be unpacked into a Tract object.
    UNPACKABLES = (
        "lots",
        "qqs",
        "lot_acres",
        "w_flags",
        "w_flag_lines",
        "e_flags",
        "e_flag_lines",
    )

    def __init__(
            self,
            text,
            clean_qq=False,
            include_lot_divs=True,
            qq_depth_min=2,
            qq_depth_max=None,
            qq_depth=None,
            break_halves=False,
            parent=None
    ):
        """
        NOTE: Documentation for this class is not maintained here. See
        instead ``Tract.parse()``, which essentially serves as a wrapper
        for this class.
        """
        self.orig_text = text
        self.preprocessor = TractPreprocessor(text, clean_qq)
        self.text = self.preprocessor.text
        self.clean_qq = clean_qq
        self.include_lot_divs = include_lot_divs
        self.qq_depth_min = qq_depth_min
        self.qq_depth_max = qq_depth_max
        self.qq_depth = qq_depth
        self.break_halves = break_halves
        self.parent = parent

        # These attributes will be populated during the parse.
        self.lots = []
        self.qqs = []
        self.lot_acres = {}
        self.w_flags = []
        self.e_flags = []
        self.w_flag_lines = []
        self.e_flag_lines = []

        # Pull pre-existing flags from the parent Tract, if applicable.
        if parent:
            self.w_flags = parent.w_flags.copy()
            self.e_flags = parent.e_flags.copy()
            self.w_flag_lines = parent.w_flag_lines.copy()
            self.e_flag_lines = parent.e_flag_lines.copy()

        self.parse()

    def parse(self):
        """
        Parse the Tract description.

        NOTE: Documentation for this method is mostly maintained under
        ``Tract.parse()``, which essentially serves as a wrapper for the
        ``TractParser`` class and this method.
        """
        text = self.text
        include_lot_divs = self.include_lot_divs
        qq_depth_min = self.qq_depth_min
        qq_depth_max = self.qq_depth_max
        qq_depth = self.qq_depth
        break_halves = self.break_halves

        # TODO : DON'T pull the QQ in "less and except the Johnston #1
        #   well in the NE/4NE/4 of Section 4, T154N-R97W" (for example)

        # TODO : DON'T pull the QQ in "To the east line of the NW/4NW/4"
        #   (for example). May need some additional context limitations.
        #   (exclude "of the said <match>"; "<match> of [the] Section..." etc.)

        # Extract the lots from the description, so we can unpack them
        # individually (and leave the rest of the description for
        # subsequent aliquot parsing).  Replace any extracted lots with
        # ';;' to prevent unintentionally combining aliquots later.

        # lot_blocks_and_leading_aliquots will contain 2-tuples of:
        #   (<text block for lots>, <text block for leading aliquot, if any>)
        lot_blocks_and_leading_aliquots = []
        remaining_text = text
        while True:
            # We use multilot_with_aliquot_regex instead of
            # multilot_regex in order to ALSO capture leading aliquots.
            # This also prevents such leading aliquots as later being
            # interpreted as standalone aliquots. (For example,
            # 'N½ of Lot 1' should be read as a whole, and not as 'N½'
            # AND 'Lot 1' separately.
            lot_aliq_mo = multilot_with_aliquot_regex.search(remaining_text)
            if lot_aliq_mo is None:
                break
            else:
                leading_aliquot = lot_aliq_mo['aliquot']
                lot_text = lot_aliq_mo['lots']
                lot_blocks_and_leading_aliquots.append((lot_text, leading_aliquot))
                # reconstruct remaining_text, injecting ';;' where the
                # match was located
                p1 = remaining_text[:lot_aliq_mo.start()]
                p2 = remaining_text[lot_aliq_mo.end():]
                remaining_text = f"{p1};;{p2}"
        text = remaining_text

        for block, leading_aliquot in lot_blocks_and_leading_aliquots:
            # Unpack the lots in this block, and store the results
            # to the appropriate attributes
            unpacker = LotUnpacker(block)
            self.w_flags.extend(unpacker.flags)
            self.w_flag_lines.extend(unpacker.flag_lines)
            new_lots = unpacker.lot_list
            if include_lot_divs and leading_aliquot is not None:
                # Combine the aliquot(s) with the lot(s).
                leading_aliquot = leading_aliquot.replace('¼', '')
                leading_aliquot = leading_aliquot.replace('½', '2')
                for idx in range(unpacker.aliquots_through):
                    new_lots[idx] = f"{leading_aliquot} of {new_lots[idx]}"

            self.lots.extend(new_lots)
            for lot_, acres_ in unpacker.lot_acres.items():
                if lot_ in self.lot_acres:
                    flag = f"dup_lot_acreage<{lot_}({self.lot_acres[lot_]})>"
                    self.w_flags.append(flag)
                    self.w_flag_lines.append((flag, flag))
                self.lot_acres[lot_] = acres_

        # Get a list of all of the aliquots strings, so we can parse them
        # individually.
        aliquot_blocks = []
        remaining_text = text
        while True:
            # Run this loop, pulling the next aliquot match until we run out.
            aliq_mo = aliquot_unpacker_regex.search(remaining_text)
            if aliq_mo is None:
                break
            else:
                # TODO: Implement context awareness. Should not pull aliquots
                #   before "of Section ##", for example.
                aliquot_blocks.append(aliq_mo.group())
                start, end = aliq_mo.start(), aliq_mo.end()
                remaining_text = f"{remaining_text[:start]};;{remaining_text[end:]}"
        text = remaining_text

        # And also pull out "ALL" as an aliquot if it is clear of any
        # context (e.g., pull "ALL" but not "All of the").  First, get a
        # working text string, and replace each group of whitespace with
        # a single space.
        check_for_acceptable_all = re.sub(r'\s+', ' ', text).strip()
        all_mo = all_regex.search(check_for_acceptable_all)
        if all_mo is not None:
            if all_mo['context'] is None:
                # If we ONLY found 'ALL', then we're good.
                aliquot_blocks.append(_ALL)

        # Now that we have list of text blocks, each containing a separate
        # aliquot, parse each of them into QQ's (or smaller, if further
        # divided).
        #   ex:  ['NE¼', 'E½NE¼NW¼']
        #           -> ['NENE' , 'NWNE' , 'SENE' , 'SWNE', 'E2NENW']

        if qq_depth is not None:
            qq_depth_min = qq_depth_max = qq_depth
        for txt in aliquot_blocks:
            new_qqs = parse_aliquot(
                txt, qq_depth_min, qq_depth_max, qq_depth, break_halves)
            self.qqs.extend(new_qqs)

        lots_qqs = self.lots + self.qqs
        self.gen_flags()
        return lots_qqs

    def gen_flags(self):
        """
        INTERNAL USE:

        Look for duplicate lots and QQ's and store the appropriate
        flags.
        :return: None.
        """
        def find_duplicates(lst):
            last = len(lst)
            duplicates = []
            for i, elem in enumerate(lst, start=1):
                if i == last:
                    break
                if elem in lst[i:]:
                    duplicates.append(elem)
            return duplicates

        dup_lots = find_duplicates(self.lots)
        dup_qqs = find_duplicates(self.qqs)

        if dup_lots:
            flag = f"dup_lot<{','.join(dup_lots)}>"
            self.w_flags.append(flag)
            self.w_flag_lines.append((flag, flag))

        if dup_qqs:
            flag = f"dup_qq<{','.join(dup_qqs)}>"
            self.w_flags.append(flag)
            self.w_flag_lines.append((flag, flag))


__all__ = [
    'TractParser',
]
