
"""
Class and functions for parsing PLSS descriptions that have already been
preprocessed.
"""

from ..rgxlib import *
from ..unpack import (
    SecUnpacker,
    unpack_twprge,
    twprge_natural_to_short,
    is_multi_sec,
)
from ..config import (
    MasterConfig,
)
from ..tract import Tract
from ..containers import TractList
from ..config import (
    TRS_DESC,
    DESC_STR,
    S_DESC_TR,
    TR_DESC_S,
    COPY_ALL,
)
from .plss_preprocess import (
    PLSSPreprocessor,
    find_twprge,
)

_E_FLAG_SECERR = 'sec_error'
_E_FLAG_TWPRGE_ERR = 'twprge_error'


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
            legit_match = True

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
                    legit_match = False

            if legit_match:
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

    SEC_COLON_CAUTIOUS = 'sec_colon_cautious'
    SECOND_PASS = 'second_pass'

    def __init__(
            self,
            txt: str,
            layout: str = None,
            require_colon=False):
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
            require_colon=False):
        """
        INTERNAL USE:

        Pull from the text all sections and 'multi-sections' that are
        appropriate to the description layout.
        :param text: The text to search for sections.
        :param layout: The layout of the description. (Will be deduced
        if not specified.)
        :param require_colon: Whether to require a colon after section
        number in ``TRS_desc`` and ``S_desc_TR`` layouts. Defaults to
        ``False``. Alternatively, pass ``True`` to require colons, or
        ``SecFinder.SEC_COLON_CAUTIOUS`` to do a two-pass method
        (as turned on with config parameter ``'sec_colon_cautious'``).
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
                    flag = f"multisec_ignored<{','.join(sec_nums)}>"
                else:
                    flag = f"sec_ignored<{sec_nums[0]}>"
                self.flags.append(flag)
                self.flag_lines.append((flag, sec_txt))
                continue

            if is_multi_sec(sec_mo):
                # Generate the appropriate flag.
                flag = f"multisec_found<{','.join(sec_nums)}>"
                self.flags.append(flag)
                self.flag_lines.append((flag, sec_txt))

            new_match(sec_mo)

        if self.matches and require_colon != self.SECOND_PASS:
            return None
        elif self.matches:
            flag = f"pulled_sec_without_colon<{','.join(sec_nums)}>"
            self.flags.append((flag, flag))
            return None
        if require_colon == self.SEC_COLON_CAUTIOUS and layout in [TRS_DESC, S_DESC_TR]:
            # Do a second pass.
            self.findall_matching_sec(
                text, layout=layout, require_colon=self.SECOND_PASS)
        return None


class PLSSParser:
    """
    INTERNAL USE:

    A class to handle the heavy lifting of parsing ``PLSSDesc`` objects
    into ``Tract`` objects. Not intended for use by the end-user. (All
    functionality can be triggered by appropriate ``PLSSDesc`` methods.)

    NOTE: All parsing parameters must be locked in before initializing
    the ``PLSSParser``. Upon initializing, the parse will be
    automatically triggered and cannot be modified.

    The ``PLSSDesc.parse()`` method is actually a wrapper for
    initializing a ``PLSSParser`` object, and for extracting the
    relevant attributes from it.
    """

    # These attributes have corresponding attributes in PLSSDesc objects.
    UNPACKABLES = (
        "tracts",
        "w_flags",
        "e_flags",
        "w_flag_lines",
        "e_flag_lines",
        "current_layout",
    )
    
    # The minimum length of a substring before it will be reported as an
    # unused description
    MIN_REPORTABLE_UNUSED_LEN = 4

    def __init__(
            self,
            text,
            layout: str = None,
            default_ns: str = MasterConfig.default_ns,
            default_ew: str = MasterConfig.default_ew,
            ocr_scrub=False,
            clean_up: bool = None,
            parse_qq=False,
            clean_qq=False,
            require_colon=False,
            segment=False,
            qq_depth_min: int = 2,
            qq_depth_max: int = None,
            qq_depth: int = None,
            break_halves=False,
            handed_down_config: str = None,
            source=None,
    ):
        """
        INTERNAL USE:
        A class to parse already-preprocessed text into Tract objects.

        NOTE: Documentation for this class is not maintained here. See
        instead ``PLSSDesc.parse()``, which essentially serves as a
        wrapper for this class.

        :param text: Preprocessed text to be parsed.
        :param layout:
        :param default_ns:
        :param default_ew:
        :param ocr_scrub:
        :param clean_up:
        :param parse_qq: Whether to instruct subordinate Tract objects
        to parse their lots/qqs.
        :param clean_qq:
        :param require_colon: See ``sec_colon_required`` and
        ``sec_colon_required`` parameters in ``PLSSDesc.parse()``
        method.  This ``require_colon`` is the culmination of those
        two parameters -- can be ``False`` (default behavior), ``True``,
        or ``SecFinder.SEC_COLON_CAUTIOUS`` (which will do a second pass
        if no section is found with a colon during the first pass).
        :param segment:
        :param qq_depth_min:
        :param qq_depth_max:
        :param qq_depth:
        :param break_halves:
        :param handed_down_config: Config data to hand down to
        subordinate Tract objects. (Will be at least partially
        overridden by ``parse_qq=True``, if that is passed.)
        :param source:
        """
        # These inform subordinate Tract objects.
        self.parse_qq = parse_qq
        self.source = None
        self.orig_text = text
        if handed_down_config is None:
            handed_down_config = ''
        if parse_qq:
            handed_down_config = f"{handed_down_config},parse_qq"
        self.handed_down_config = handed_down_config

        # These impact the parse of this PLSS description.
        self.mandate_layout = not segment and layout is not None
        preprocessor = PLSSPreprocessor(text, default_ns, default_ew, ocr_scrub)
        self.text = preprocessor.text
        if layout is None:
            layout = deduce_layout(text)
        self.layout = layout
        if clean_up is None:
            clean_up = True
            if layout == COPY_ALL:
                clean_up = False
        self.clean_up = clean_up
        self.default_ns = default_ns
        self.default_ew = default_ew
        self.ocr_scrub = ocr_scrub
        self.require_colon = require_colon
        self.sec_within = True
        # Keep track of which tracts were repaired with 'sec_within'.
        self.sec_within_indexes = []

        # These exclusively affect the parsing of subordinate Tracts.
        self.clean_qq = clean_qq
        self.qq_depth_min = qq_depth_min
        self.qq_depth_max = qq_depth_max
        self.qq_depth = qq_depth
        self.break_halves = break_halves

        # These are temporary data.
        self.tract_components = []
        self.unused_components = []
        self.blocks = [self.text]
        self.next_tract_uid = 0

        # These get populated and handed off.
        self.tracts = TractList()
        self.w_flags = []
        self.w_flag_lines = []
        self.e_flags = []
        self.e_flag_lines = []

        # Append a warning flag for any Twp/Rges that were fixed during
        # preprocessing.
        if preprocessor.fixed_twprges:
            short_versions = [
                twprge_natural_to_short(tr)
                for tr in preprocessor.fixed_twprges
            ]
            flag = f"fixed_twprge<{','.join(short_versions)}>"
            self.w_flags.append(flag)
            self.w_flag_lines.append((flag, flag))

        # Override source in parent, if specified as init parameter.
        if source is None:
            self.source = source

        self.parse(segment=segment)

    @property
    def current_layout(self):
        return self.layout

    def parse(self, segment=False):
        """
        Parse the text and create Tract objects. Populates the relevant
        attributes.
        :param segment: Whether to do a segmented parse (defaults to
        ``False``).
        """
        def flag_unused(unused_text):
            """
            Create an error flag and flag line for unused text.
            """
            flag = f"unused_desc<{unused_text}>"
            self.e_flags.append(flag)
            self.e_flag_lines.append((flag, unused_text))

        def examine_unused():
            """
            Generate a warning flag for each block of unused text longer
            than a few characters, then reset the unused components.
            """
            # Discard the integer (first element in each 2-tuple), which would
            # only be used (elsewhere) with config setting 'sec_within'.
            for _, unused_bit in self.unused_components:
                if len(unused_bit) >= self.MIN_REPORTABLE_UNUSED_LEN:
                    flag_unused(unused_bit)

        if segment:
            chunker = PLSSChunker(self.text, layout=self.layout)
            self.blocks = chunker.blocks
            self.unused_components.extend(chunker.unused_blocks)

        for chunk in self.blocks:
            chunk_layout = None
            if self.layout == COPY_ALL:
                chunk_layout = COPY_ALL
            # This automatically unpacks the relevant data into the PLSSParser's
            # attributes (tracts, flags, unused_components).
            ChunkParser(chunk, layout=chunk_layout, parent=self)

        if self.sec_within:
            # This only works if a single tract has been identified, but
            # won't cause any fatal issues if that's not the case.
            rebuild_sec_within(
                self.tract_components,
                self.unused_components,
                min_length=self.MIN_REPORTABLE_UNUSED_LEN)

        self.construct_tracts()
        examine_unused()
        self.check_sec_within_tracts()
        self.check_error_tracts()
        self.hand_down_flags()

    def check_sec_within_tracts(self):
        """
        Generated the appropriate warning flag to any sections that were
        fixed with ``'sec_within'`` config setting.
        :return: None
        """
        for i in self.sec_within_indexes:
            tract = self.tracts[i]
            flag = f"sec_within<{tract.trs}>"
            context = tract.quick_desc_short()
            self.w_flags.append(flag)
            self.w_flag_lines.append((flag, context))

    def hand_down_flags(self):
        """
        Give each subordinate Tract object the warning and error flags
        of this PLSSParser.
        """
        for tract in self.tracts:
            tract.w_flags.extend(self.w_flags)
            tract.w_flag_lines.extend(self.w_flag_lines)
            tract.e_flags.extend(self.e_flags)
            tract.e_flag_lines.extend(self.e_flag_lines)
        return None

    def check_error_tracts(self):
        """
        INTERNAL USE:

        Check if any Tract objects have error Twp/Rge/Sec, and if so,
        add an appropriate error flag.
        :return: ``None`` (flags are added to attributes).
        """
        error_found = any(tract.trs_is_error() for tract in self.tracts)
        if error_found:
            flag = _E_FLAG_TWPRGE_ERR
            self.e_flags.append(flag)
            self.e_flag_lines.append((flag, flag))
        return None

    def construct_tracts(self):
        """
        Convert the parsed data components in ``.tract_components``
        into ``Tract`` objects, and append them to the ``.tracts`` list.
        """
        new_tracts = []
        for tract_data in self.tract_components:
            desc = tract_data['desc']
            if self.clean_up:
                desc = cleanup_desc(desc)
            for sec in tract_data['sec']:
                trs = f"{tract_data['twprge']}{sec}"
                new_tract = Tract(
                    desc,
                    trs,
                    config=self.handed_down_config,
                    parse_qq=self.parse_qq,
                    source=self.source,
                    orig_desc=self.orig_text,
                    orig_index=self.next_tract_uid
                )
                self.tracts.append(new_tract)
                new_tracts.append(new_tract)
                if tract_data['sec_within']:
                    self.sec_within_indexes.append(self.next_tract_uid)
                self.next_tract_uid += 1
        return new_tracts


class PLSSChunker:
    """
    INTERNAL USE:
    A class for breaking PLSS descriptions into chunks by Twp/Rge,
    according to the specified or deduced layout of the overall
    description.

    The PLSSParser will extract the ``.blocks`` and parse each of them
    separately, and ``.unused_blocks`` will be converted by the
    PLSSParser into warning flags that such chunks were not included in
    the resulting tracts.
    """

    def __init__(self, text, layout=None):
        """
        INTERNAL USE:
        :param text: The text to be broken into chunks.
        :param layout: The layout to use. If not specified, will be
        deduced.
        """
        self.text = text
        self.layout = layout
        self.blocks = []
        # A list of 2-tuples, being (<0 or 1>, <block of unused text>).
        # 0 indicates text that came before a valid chunk; 1 indicates
        # that it came after.
        self.unused_blocks = []
        self.segment(layout=layout)

    def segment(self, layout=None):
        """
        Break the text up according to the layout (one matching Twp/Rge
        per chunk). Populates ``.blocks`` and ``.unused_block`` and
        returns None.
        :param layout:  The layout to use. If not specified, will be
        deduced.
        """
        text = self.text
        if layout is None:
            layout = deduce_layout(text)
        # Don't collect TwpRgeFinder-generated flags at this point.
        # They'll be collected during the actual parse.
        matches = TwpRgeFinder(text, layout).matches
        if not matches or layout == COPY_ALL:
            self.blocks.append(text)
            return None
        if layout in [TRS_DESC, TR_DESC_S]:
            self._segment_twprge_first(text, matches)
        else:
            self._segment_twprge_last(text, matches)
        return None

    def _segment_twprge_first(self, text, matches):
        """
        Populate ``.blocks`` and ``.unused_blocks`` according to layouts
        in which Twp/Rge occurs first (i.e. TRS_desc and TR_desc_S).
        :param text: The text that is being chunked.
        :param matches: The Twp/Rge matches generated by a TwpRgeFinder
        that was run on the text.
        :return: None
        """
        str_end = len(text)
        for i, (kind, twprge, start, end) in enumerate(matches):
            next_start = str_end
            try:
                _, _, next_start, _ = matches[i + 1]
            except IndexError:
                pass
            if i == 0 and start != 0:
                # String starts with something other than a Twp/Rge, in
                # a layout that requires Twp/Rge to occur first.
                self.unused_blocks.append((0, text[:start]))

            new_block = text[start:next_start]
            new_block = cleanup_desc(new_block)
            self.blocks.append(new_block)
        return None

    def _segment_twprge_last(self, text, matches):
        """
        Populate ``.blocks`` and ``.unused_blocks`` according to layouts
        in which Twp/Rge occurs last (i.e. S_desc_TR and desc_STR).
        :param text: The text that is being chunked.
        :param matches: The Twp/Rge matches generated by a TwpRgeFinder
        that was run on the text.
        :return: None
        """
        str_len = len(text)
        for i, (kind, twprge, start, end) in enumerate(matches):
            previous_end = 0
            if i != 0:
                _, _, _, previous_end = matches[i - 1]
            if i == len(matches) - 1 and end != str_len:
                # The last element is not the final character in the string.
                # In other words, text ends with something other than a Twp/Rge,
                # in a layout that requires Twp/Rge to occur last.
                self.unused_blocks.append((1, text[end:]))

            new_block = text[previous_end:end]
            new_block = cleanup_desc(new_block)
            self.blocks.append(new_block)
        return None


def deduce_layout(text: str, candidates: list = None):
    """
    Deduce the layout of the description.

    :param text: The text, whose layout is to be deduced. (Should be
    preprocessed before feeding into this function.)

    :param candidates: A list of which layouts are to be considered.
    If passed as ``None`` (the default), it will consider all currently
    implemented meaningful layouts (i.e. ``'TRS_desc'``, ``'desc_STR'``,
    ``'S_desc_TR'``, and ``'TR_desc_S'``), but will also consider
    ``'copy_all'`` if an apparently flawed description is found. If
    specifying fewer than all candidates, ensure that at least one
    layout from ``pytrs.IMPLEMENTED_LAYOUTS`` is in the list. (Strings
    not in ``pytrs.IMPLEMENTED_LAYOUTS`` will have no effect.)

    :return: Returns the algorithm's best guess at the layout (a
    string).
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


def cleanup_desc(text):
    """
    INTERNAL USE:

    Clean up common 'artifacts' from parsing. (Intended to be run only
    on parsed text that will make up the ``.desc`` attribute of a Tract
    object.)
    """
    cull_list = [' the', ' all in', ' all of', ' of', ' in', ' and']
    new_txt = ''
    while text != new_txt:
        new_txt = text
        text = text.lstrip('.')
        text = text.strip(',;:-–—\t\n ')
        # Check to see if text1 ends with each of the strings in the
        # cull_list, and if so, slice text1 down accordingly.
        for cull_str in cull_list:
            if text.lower().endswith(cull_str):
                cull_length = len(cull_str)
                text = text[:-cull_length]
    return text


class ChunkParser:
    """
    INTERNAL USE:

    A class to parse a chunk of text. Does most of the heavy lifting for
    the ``PLSSParser`` and automatically hands off the relevant data to
    the parent ``PLSSParser``.
    """

    TWPRGE_START = 'TWPRGE_START'
    TWPRGE_END = 'TWPRGE_END'
    SEC_START = 'SEC_START'
    SEC_END = 'SEC_END'
    TEXT_START = 'TEXT_START'
    TEXT_END = 'TEXT_END'

    def __init__(self, text, layout, parent: PLSSParser):
        self.text = text
        self.layout = layout
        self.parent = parent
        self.twprge_matches = []
        self.working_twprge_list = []
        self.sec_matches = []
        self.working_sec_list = []
        self.markers_list = []
        self.markers_dict = {}
        self.tract_components = []
        self.last_twprge_used = False
        self.last_sec_used = False
        self.working_twprge = None
        self.working_sec = None

        # Stage flags, etc. before passing them to parent PLSSParser's
        # attributes, in case we find no Tracts during a first pass and need to
        # rerun in COPY_ALL layout.
        self.w_flags = []
        self.w_flag_lines = []
        self.e_flags = []
        self.e_flag_lines = []
        self.unused_components = []

        # Parsing also hands off the relevant data to the parent.
        self.parse_safe()

    def parse_safe(self):
        """
        Parse this chunk, but protect the flag attributes of the
        ``.parent`` ``PLSSParser`` object until we know that the
        parser has created at least one ``Tract``.

        .. note::
            ``.parse_chunk()`` will create a replacement ``ChunkParser``
            in the event that no ``Tract`` is created during a first
            pass.  In the replacement, it will force the use of
            ``'COPY_ALL'`` layout to ensure a ``Tract`` is created. Then
            the replacement's flags will overwrite those in the
            attributes of this ``ChunkParser``, and finally they will be
            handed off to the parent's flag attributes.
        :return: ``None``
        """
        self.parse_chunk()
        self.gen_flags_chunk()

        parent = self.parent

        # New Tract objects are already appended to parent's `.tract` attribute.
        parent.w_flags.extend(self.w_flags)
        parent.w_flag_lines.extend(self.w_flag_lines)
        parent.e_flags.extend(self.e_flags)
        parent.e_flag_lines.extend(self.e_flag_lines)
        parent.tract_components.extend(self.tract_components)
        parent.unused_components.extend(self.unused_components)

        return None

    def parse_chunk(self):
        """
        Parse a chunk of text into tracts.
        :return: The list of new ``Tract`` objects that were generated.
        """
        chunk = self.text
        chunk_layout = self.layout
        if chunk_layout != COPY_ALL and not self.parent.mandate_layout:
            chunk_layout = deduce_layout(chunk)
        self.find_matches(chunk, chunk_layout)
        self.populate_markers(chunk)

        # If using COPY_ALL layout, use that parser method, build the single
        # tract, and return.
        if chunk_layout == COPY_ALL:
            self._parse_copyall(chunk)
            return None

        # Populate the tract data (self.tract_components).
        self._parse_meaningful(chunk, chunk_layout)

        # Put unused twprge and unused sections back into the working lists.
        if not self.last_twprge_used \
                and self.working_twprge != MasterConfig._ERR_TWPRGE:
            self.working_twprge_list.insert(0, self.working_twprge)
        if not self.last_sec_used \
                and self.working_sec != [MasterConfig._ERR_SEC]:
            self.working_sec_list.insert(0, self.working_sec)

        for twprge in self.working_twprge_list:
            flag = f"unused_twprge<{twprge}>"
            self.e_flags.append(flag)
            self.e_flag_lines.append((flag, flag))

        for seclist in self.working_sec_list:
            flag = f"unused_sec<{','.join(seclist)}>"
            self.e_flags.append(flag)
            self.e_flag_lines.append((flag, flag))

        if self.parent.sec_within:
            # Note: Only works if a single tract candidate was identified. Will
            # have no effect if more than one tract was found (but considers a
            # multi-section to correspond with a single tract).
            rebuild_sec_within(
                self.tract_components,
                self.unused_components,
                min_length=self.parent.MIN_REPORTABLE_UNUSED_LEN)

        if not self.tract_components:
            # If no tracts identified, rerun this chunk as copy_all layout.
            # And steal the staged flags, etc. from the replacement to
            # hand off to the parent PLSSParser object.
            replacement = ChunkParser(self.text, COPY_ALL, self.parent)
            replacement_attributes = (
                'w_flags', 'w_flag_lines', 'e_flags', 'e_flag_lines',
                'unused_components', 'tract_components'
            )
            for attr in replacement_attributes:
                setattr(self, attr, getattr(replacement, attr))
        return None

    def find_matches(self, text, layout):
        """
        Find matching Twp/Rge and Sec according to the specified layout.
        :param text: The text (full description or chunk) in which to
        find matches.
        :param layout: The layout to use for finding matches.
        """
        # Populate Twp/Rge matches/flags.
        twprge_finder = TwpRgeFinder(text, layout)
        self.twprge_matches = twprge_finder.matches
        self.w_flags.extend(twprge_finder.flags)
        self.w_flag_lines.extend(twprge_finder.flag_lines)
        # Populate section matches/flags.
        sec_finder = SecFinder(text, layout, self.parent.require_colon)
        self.sec_matches = sec_finder.matches
        self.w_flags.extend(sec_finder.flags)
        self.w_flag_lines.extend(sec_finder.flag_lines)
        return None

    def populate_markers(self, text):
        """
        Convert the Twp/Rge and Sec matches into the markers_list and
        markers_dict, which are examined by the parser to determine
        which section(s) goes with which Twp/Rge, and which block of
        description goes with that.

        :param text: The text (full description or chunk) in which to
        find matches.
        """
        # TEXT_START and TEXT_END may get overwritten, if the start or end
        # of a Twp/Rge or Sec was matched there.
        self.markers_dict[0] = self.TEXT_START
        self.markers_dict[len(text)] = self.TEXT_END
        for kind, val, start, end in self.sec_matches:
            self.markers_dict[start] = self.SEC_START
            self.markers_dict[end] = self.SEC_END
            self.working_sec_list.append(val)
        for kind, val, start, end in self.twprge_matches:
            self.markers_dict[start] = self.TWPRGE_START
            self.markers_dict[end] = self.TWPRGE_END
            self.working_twprge_list.append(val)
        self.markers_list = sorted(self.markers_dict.keys())
        return None

    def get_next_twprge(self):
        """
        Stage the next Twp/Rge in the working list. If no more, stage an
        error Twp/Rge. (Also return that Twp/Rge.)
        """
        # Write an error flag if the previous TwpRge was not used.
        if not self.last_twprge_used \
                and self.working_twprge not in [None, MasterConfig._ERR_TWPRGE]:
            flag = f"{_E_FLAG_TWPRGE_ERR}<{self.working_twprge}>"
            context = f"<{self.working_twprge}>"
            self.e_flags.append(flag)
            self.e_flag_lines.append((flag, context))
        self.last_twprge_used = False
        if self.working_twprge_list:
            self.working_twprge = self.working_twprge_list.pop(0)
        else:
            self.working_twprge = MasterConfig._ERR_TWPRGE
        return self.working_twprge

    def get_next_sec(self):
        """
        Stage the next Sec list in the working list. If no more, stage
        an error Sec inside a list. (Also return that list.)
        """
        # Write an error flag if the previous section was not used.
        if not self.last_sec_used \
                and self.working_sec not in [None, MasterConfig._ERR_SEC]:
            flag = f"{_E_FLAG_SECERR}<{self.working_sec}>"
            context = f"<{self.working_sec}/{self.working_twprge}>"
            self.e_flags.append(flag)
            self.e_flag_lines.append((flag, context))
        self.last_sec_used = False
        if self.working_sec_list:
            self.working_sec = self.working_sec_list.pop(0)
        else:
            self.working_sec = [MasterConfig._ERR_SEC]
        return self.working_sec

    def _parse_copyall(self, txt):
        """
        Use the already-gathered matched Twp/Rge and Sec data, but parse
        as copy_all layout.
        """
        sec = self.get_next_sec()
        # Just the first section.
        sec = [sec[0]]
        twprge = self.get_next_twprge()
        self._stage_new_tract(txt, sec, twprge)

    def _parse_meaningful(self, txt, layout):
        """
        Use the already-gathered matched Twp/Rge and Sec data to break
        the text down into tract components for all layouts except
        ``'COPY_ALL'``
        :param txt:
        :param layout:
        :return:
        """

        def prep_new_tract(desc):
            desc = cleanup_desc(desc)
            self._stage_new_tract(desc, self.working_sec, self.working_twprge)
            self.last_sec_used = True
            self.last_twprge_used = True
            # Sec can be used only once.
            self.working_sec = [MasterConfig._ERR_SEC]

        s_desc_lays = [TRS_DESC, S_DESC_TR]
        tr_first_lays = [TRS_DESC, TR_DESC_S]
        final = len(self.markers_list) - 1

        # Get working sec and/or twprge for 'forward-looking' layouts.
        if layout not in s_desc_lays:
            self.working_sec = self.get_next_sec()
        if layout not in tr_first_lays:
            self.working_twprge = self.get_next_twprge()

        for count, marker_pos in enumerate(self.markers_list):
            marker_type = self.markers_dict[marker_pos]
            next_marker_pos = self.markers_list[min((final, count + 1))]
            next_marker_type = self.markers_dict[next_marker_pos]

            if marker_type == self.TWPRGE_START:
                self.get_next_twprge()
                continue
            elif marker_type == self.SEC_START:
                self.get_next_sec()
                continue

            # Get the block of text.
            block = None
            if marker_type == self.TEXT_START:
                block = txt[marker_pos:next_marker_pos]
            elif marker_type == self.TEXT_END:
                continue
            elif marker_type in [self.TWPRGE_END, self.SEC_END]:
                block = txt[marker_pos:next_marker_pos]

            if block is None:
                continue

            if layout in s_desc_lays and marker_type == self.SEC_END:
                # These layouts mandate sec -> desc, so reaching the end of a
                # section means we've identified a new tract.
                prep_new_tract(block)
                continue

            if layout not in s_desc_lays and next_marker_type == self.SEC_START:
                # These layouts mandate desc -> sec, so looking ahead to the start
                # of a section means we've identified a new tract.
                prep_new_tract(block)
                continue

            # All other scenarios are a problem. Track how many tracts had been
            # created at the time this unused block was identified, so we can
            # tie them back together if needed.
            self.unused_components.append((len(self.tract_components), block))
        return None

    def _stage_new_tract(self, desc, sec, twprge):
        """
        Stage a newly identified tract into ``.tract_components``.

        :param desc: Description block for new ``Tract``.
        :param sec: A list of section numbers.
        :param twprge: A Twp/Rge in the standardized format.
        :return: ``None`` (appends directly to ``.tract_components``)
        """
        new = {
            'desc': desc,
            'sec': sec,
            'twprge': twprge,
            'sec_within': False,
        }
        self.tract_components.append(new)

    def gen_flags_chunk(self):
        """
        Generate warning flags and corresponding context lines.
        :return: ``None`` (results stored to ``.w_flags`` and
         ``.w_flag_lines``).
        """
        # regex pattern : (flag, (context len before, context len after))
        rgx_and_how_to_hand = {
            well_regex: ("well", (5, 25)),
            depth_regex: ("depth", (10, 20)),
            including_regex: ("including", (0, 40)),
            less_except_regex: ("less_except", (0, 40)),
            isfa_regex: ("insofar", (0, 40)),
        }
        chunk = self.text
        max_end = len(chunk)
        for rgx, how_to_handle in rgx_and_how_to_hand.items():
            flag, (left_context, right_context) = how_to_handle
            start_pos = 0
            while True:
                start_mo = rgx.search(chunk, pos=start_pos)
                if not start_mo:
                    break

                # Get context substring, searching for any additional matches
                # of this same regex; and if any additional matches are found,
                # then keep extending the context right. (To reduce redundant
                # flags.)
                end_mo = start_mo
                final_end_mo = end_mo
                while True:
                    # Continue extending context rightward until we no
                    # longer find another match of this regex pattern.
                    left_bound = end_mo.end()
                    right_bound = min((max_end, end_mo.end() + right_context))
                    end_mo = rgx.search(chunk, pos=left_bound, endpos=right_bound)
                    if not end_mo:
                        break
                    final_end_mo = end_mo
                i = max((0, start_mo.start() - left_context))
                j = min((final_end_mo.end() + right_context, max_end))
                context = chunk[i:j]
                context = context.replace('\n', ' ').strip()
                context = f"<{context}>"
                self.parent.w_flags.append(flag)
                self.parent.w_flag_lines.append((flag, context))
                # Start next search from the end of this context string.
                start_pos = j


def rebuild_sec_within(
        tract_components: list, unused_components: list, min_length: int = 4):
    """
    INTERNAL USE:

    Reattach unused block of text to the description portion of a tract
    (that has not yet been compiled to a ``Tract`` object). If
    successful, will empty the ``.unused_components`` list.

    Any tract components that get rebuilt with this function will have
    their ``'sec_within'`` value changed to ``True``, so that it can be
    flagged for the appropriate ``Tract`` object(s) created by the
    ``PLSSParser``.

    .. note::
        This only works if *exactly* one tract candidate was identified.
        It will have no effect if more than one tract was found, but
        considers a multi-section equivalent to a single tract -- i.e.
        ``'That part of Sec 1 - 3 lying within the right-of-way...'``
        would be considered a single tract for the purposes of this
        method.

    :param tract_components: A list of dicts representing tracts
     that are yet to be compiled, with keys, ``'desc'``, ``'twp'``,
     and ``'sec'`` (although only ``'desc'`` gets used in this
     function).
    :param unused_components: A list of 2-tuples, being an integer
     to indicate whether this text component should come *before*
     the description text (``0``) or *after* it (``1`` or greater).
    :param min_length: The minimum length that an unused block of
     text has to be before it gets reported.
    :return: ``None`` (Appropriate values are changed within each dict.)
    """
    if len(tract_components) != 1:
        return []
    repaired_tract = tract_components[0]
    desc = repaired_tract['desc']
    while unused_components:
        i, unused = unused_components.pop(0)
        unused = cleanup_desc(unused)
        if len(unused) >= min_length:
            if i == 0:
                # Unused description came before the captured description.
                desc = f"{unused} {desc}"
            else:
                # Unused came after the captured description.
                desc = f"{desc} {unused}"
    repaired_tract['sec_within'] = True
    repaired_tract['desc'] = desc
    return [0]


__all__ = [
    'PLSSParser',
    'SecFinder',
    'deduce_layout',
    'find_twprge',
]
