
from .rgxlib import *
from .unpackers import (
    SecUnpacker,
    unpack_twprge,
    twprge_natural_to_short,
    is_multi_sec,
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
            of the match. Append to the list of matches as a 4-tuple,
            whose first element is 'TWPRGE'.
            """
            twprge = unpack_twprge(mo)
            twprge = twprge_natural_to_short(twprge)
            new = ('TWPRGE', twprge, mo.start(0), mo.end(0))
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


class SecFinder:
    """
    INTERNAL USE:

    A class to find Sections that appropriately match the specified
    layout.
    """

    DEFAULT_COLON = 'default_colon'
    SECOND_PASS = 'second_pass'

    def __init__(
            self,
            txt: str,
            layout: str = None,
            require_colon = DEFAULT_COLON):
        self.txt = txt
        self.matches = []
        self.layout = layout
        self.flags = []
        self.flag_lines = []
        self.findall_matching_sec(txt, layout, require_colon)

    def findall_matching_sec(
            self,
            text: str,
            layout: str = None,
            require_colon=DEFAULT_COLON):
        """
        INTERNAL USE:

        Pull from the text all sections and 'multi-sections' that are
        appropriate to the description layout.
        :param text: The text to search for sections.
        :param layout: The layout of the description. (Will be deduced
        if not specified.)
        :param require_colon: Same effect as in ``PLSSParser.parse()``
        """

        def new_match(mo):
            """
            Extract the list of section numbers, and the start/end
            positions of the match. Append to the list of matches as a
            4-tuple, whose first element is 'SEC'.
            :param mo:
            :return:
            """
            unpacker = SecUnpacker(mo.group(0))
            self.flags.extend(unpacker.flags)
            self.flag_lines.extend(unpacker.flag_lines)
            new = ('SEC', unpacker.sec_list, mo.start(0), mo.end(0))
            self.matches.append(new)

        if layout is None:
            layout = deduce_layout(text=text)

        # require_colon=True will pass over sections that are NOT
        # followed by colons in the TRS_DESC and S_DESC_TR layouts only.
        # It is defaulted to (sort-of) True for those layouts, but if no
        # satisfactory section or multi-section is found during the
        # first pass, it will rerun with `require_colon=SECOND_PASS`.
        # Feeding `require_colon=True` as a kwarg will override allowing
        # the second pass.

        if isinstance(require_colon, bool):
            need_colon = require_colon
        elif require_colon == self.SECOND_PASS:
            need_colon = False
            # Clear any staged flags from the first pass.
            self.flags = []
            self.flag_lines = []
        else:
            need_colon = True
        if layout not in [TRS_DESC, S_DESC_TR]:
            # need_colon has no effect on other description layouts.
            need_colon = False

        for sec_mo in multisec_regex.finditer(text):
            # Sections and multi-sections can get ruled out for a few reasons.
            legit_match = True
            sec_txt = sec_mo.group(0)
            sec_nums = SecUnpacker(sec_txt).sec_list

            # For TRS_DESC and S_DESC_TR layouts specifically, we do NOT
            # want to match sections following "of", "said", or "in"
            # (e.g. 'the NE/4 of Section 4'), because it very likely
            # means it's a continuation of the same description.
            illegal = (' of', ' said', ' in', ' within')
            illegal_word_prior = text[:sec_mo.start()].rstrip().endswith(illegal)
            if layout in [TRS_DESC, S_DESC_TR] and illegal_word_prior:
                legit_match = False

            # Also for TRS_DESC and S_DESC_TR layouts, we ONLY want to
            # match sections and multi-Sections that are followed by a
            # colon (if need_colon is True).
            if need_colon and sec_mo['colon'] is None:
                legit_match = False

            if not legit_match:
                # Create a warning flag that we did not pull this
                # (multi)section and move on to the next loop.
                if len(sec_nums) > 1:
                    flag = f"multisec_ignored<{', '.join(sec_nums)}>"
                else:
                    flag = f"sec_ignored<{sec_nums[0]}>"
                self.flags.append(flag)
                self.flag_lines.append((flag, sec_txt))
                continue

            if is_multi_sec(sec_mo):
                # Generate the appropriate flag.
                flag = f"multisec_found<{', '.join(sec_nums)}"
                self.flags.extend(flag)
                self.flags.extend((flag, sec_txt))

            new_match(sec_mo)

        if self.matches and require_colon != self.SECOND_PASS:
            return None
        elif self.matches:
            flag = f"pulled_sec_without_colon<{','.join(sec_nums)}>"
            self.flags.append((flag, flag))
            return None
        if require_colon == self.DEFAULT_COLON and layout in [TRS_DESC, S_DESC_TR]:
            # Do a second pass.
            self.findall_matching_sec(
                text, layout=layout, require_colon=self.SECOND_PASS)
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
