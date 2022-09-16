
from .rgxlib import *
from .unpackers import (
    unpack_twprge,
    twprge_natural_to_short,
)
from .master_config import (
    DefaultEWError,
    DefaultNSError,
    MasterConfig,
)
from .plss_preprocess import (
    PLSSPreprocessor,
    find_twprge,
)


# All current layouts
TRS_DESC = "TRS_desc"
DESC_STR = "desc_STR"
S_DESC_TR = "S_desc_TR"
TR_DESC_S = "TR_desc_S"
COPY_ALL = "copy_all"

# A tuple of all currently implemented layouts:
_IMPLEMENTED_LAYOUTS = (
    TRS_DESC,
    DESC_STR,
    S_DESC_TR,
    TR_DESC_S,
    COPY_ALL,
)

# The same tuple as a public-facing var
IMPLEMENTED_LAYOUTS = _IMPLEMENTED_LAYOUTS

IMPLEMENTED_LAYOUT_EXAMPLES = (
    "'TRS_desc'\n"
    "T154N-R97W\nSection 14: NE/4\n\n"
    "'desc_STR'\n"
    "NE/4 of Section 14, T154N-R97W\n\n"
    "'S_desc_TR'\n"
    "Section 14: NE/4, T154N-R97W\n\n"
    "'TR_desc_S'\n"
    "T154N-R97W\nNE/4 of Section 14\n\n"
    "'copy_all'\n"
    "Note: <copy_all> means that the entire text will be copied as the "
    "description, regardless of what the actual layout is."
)

_E_FLAG_SECERR = 'SecERROR'
_E_FLAG_TWPRGE_ERR = 'TwpRgeERROR'


class TwpRgeFinder:
    """
    INTERNAL USE:

    A class to find Twp/Rge's that appropriately match the specified
    layout.
    """
    def __init__(self, txt: str, layout: str = None):
        self.txt = txt
        self.matches = []
        self.layout = layout
        self.flags = []
        self.flag_lines = []
        self.findall_matching_twprge(txt, layout)

    def findall_matching_twprge(self, txt, layout):
        """
        INTERNAL USE:

        Find Twp/Rge's that appropriately match the specified layout.

        :param txt: The text in which to find matching Twp/Rge's.
        :param layout: The layout of the text. (Will be deduced if not
        specified.)
        """
        if layout is None:
            layout = deduce_layout(text=txt)

        def new_match(mo):
            """
            Extract the abbreviated Twp/Rge, and the start/end positions
            of the match. Append to the list of matches as a 3-tuple.
            """
            twprge = unpack_twprge(mo)
            twprge = twprge_natural_to_short(twprge)
            new = (twprge, mo.start(0), mo.end(0))
            self.matches.append(new)
            return new

        j = 0
        for twprge_mo in twprge_regex.finditer(txt):
            # For these layouts, all Twp/Rge count as matches.
            if layout in (DESC_STR, TR_DESC_S, COPY_ALL):
                new_match(twprge_mo)
                continue

            # For TRS_DESC and S_DESC_TR, we have to rule out false matches.
            is_match = True

            # Get the rightmost sec_mo to the left of this twprge.
            i = twprge_mo.start(0)
            sec_mo = None
            for sec_mo in multisec_regex.finditer(txt, pos=j, endpos=i):
                j = sec_mo.start(0)

            if sec_mo is not None:
                substring = txt[sec_mo.start(0):twprge_mo.end(0)]
                # If there's a match on this regex pattern, this is not
                # a match.
                # (E.g., "...that part of Section 4 of T154N-R97W...")
                if sec_twprge_in_between.search(substring) is not None:
                    is_match = False

            if is_match:
                new_match(twprge_mo)
            else:
                ignored_twprge = unpack_twprge(twprge_mo)
                ignored_twprge = twprge_natural_to_short(ignored_twprge)
                flag = f'twprge_ignored<{ignored_twprge}>'
                # Context for the exclusion (but do not index beyond
                # left of string.)
                left_bound = max((0, i - 20))
                line = txt[left_bound:twprge_mo.end(0)]
                self.flags.append(flag)
                self.flag_lines.append(line)

        return None


def deduce_layout(text: str, candidates: list = None):
    """
    Deduce the layout of the description.

    :param text: The text, whose layout is to be deduced. (Should be
    preprocessed before feeding into this function.)

    :param candidates: A list of which layouts are to be considered.
    If passed as ``None`` (the default), it will consider all currently
    implemented meaningful layouts (i.e. 'TRS_desc', 'desc_STR',
    'S_desc_TR', and 'TR_desc_S'), but will also consider 'copy_all' if
    an apparently flawed description is found. If specifying fewer than
    all candidates, ensure that at least one layout from
    IMPLEMENTED_LAYOUTS is in the list. (Strings not in
    IMPLEMENTED_LAYOUTS will have no effect.)

    :return: Returns the algorithm's best guess at the layout (i.e.
    a string).
    """

    if candidates is None:
        candidates = [TRS_DESC, DESC_STR, S_DESC_TR, TR_DESC_S]

    try_trs_desc = TRS_DESC in candidates
    try_desc_str = DESC_STR in candidates
    try_s_desc_tr = S_DESC_TR in candidates
    try_tr_desc_s = TR_DESC_S in candidates

    # Default to COPY_ALL if we can't affirmatively deduce a better option.
    layout_guess = COPY_ALL

    text = text.strip()

    # No need to capture section number. Just want to check position in
    # relation to Twp/Rge.
    sec_mo = no_num_sec_regex.search(text)
    twprge_mo = twprge_regex.search(text)

    if not sec_mo or not twprge_mo:
        # Default to COPY_ALL, as having no identifiable section or
        # Twp/Rge is an insurmountable flaw.
        return COPY_ALL

    # If the first identified section comes before the first identified
    # Twp/Rge, then it's probably DESC_STR or S_DESC_TR.
    if sec_mo.start() < twprge_mo.start():
        if try_desc_str:
            layout_guess = DESC_STR
        if try_s_desc_tr and sec_mo.start() <= 1:
            # This is such an unlikely layout, that we give it very
            # limited room for error. If the section comes first in the
            # description, we should expect it VERY early in the text.
            layout_guess = S_DESC_TR
        return layout_guess

    if try_tr_desc_s:
        # Check how many characters appear between Twp/Rge and Sec, and
        # decide whether it's TR_DESC_S or TRS_DESC, based on that.
        string_between = text[twprge_mo.end():sec_mo.start()].strip()
        if len(string_between) >= 4:
            return TR_DESC_S

    if try_trs_desc:
        return TRS_DESC

    return layout_guess
