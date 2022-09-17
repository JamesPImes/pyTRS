
"""
Class and functions for parsing PLSS descriptions that have already been
preprocessed.
"""

from .rgxlib import *
from .unpackers import (
    SecUnpacker,
    unpack_twprge,
    twprge_natural_to_short,
    is_multi_sec,
)
from .master_config import (
    MasterConfig,
)
from .plss_preprocess import (
    PLSSPreprocessor,
    find_twprge,
)
from .parser import Tract


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
        if require_colon == self.DEFAULT_COLON and layout in [TRS_DESC, S_DESC_TR]:
            # Do a second pass.
            self.findall_matching_sec(
                text, layout=layout, require_colon=self.SECOND_PASS)
        return None


class PLSSParser:
    """
    INTERNAL USE:
    A class to parse already-preprocessed text into Tract objects.
    """

    TWPRGE_START = 'TWPRGE_START'
    TWPRGE_END = 'TWPRGE_END'
    SEC_START = 'SEC_START'
    SEC_END = 'SEC_END'
    TEXT_START = 'TEXT_START'
    TEXT_END = 'TEXT_END'

    def __init__(
            self,
            text,
            layout=None,
            config=None,
            segment=False,
            clean_up=None,
            parse_qq=None,
            source=None):
        """
        INTERNAL USE:
        A class to parse already-preprocessed text into Tract objects.

        :param text: Preprocessed text to be parsed.
        :param layout:
        :param config: Config data to hand down to subordinate Tract
        objects. (Will be at least partially overridden by
        ``parse_qq=True``, if that is passed.)
        :param segment:
        :param clean_up:
        :param parse_qq: Whether to instruct subordinate Tract objects
        to parse their lots/qqs.
        :param source: Source of the PLSS description. (Optional)
        """
        # These inform subordinate Tract objects.
        self.parse_qq = parse_qq
        self.source = source
        self.orig_text = text
        if parse_qq:
            config = f"{config},parse_qq"
        self.config = config

        # These impact the parse of this PLSS description.
        self.mandate_layout = not segment and layout is not None
        preprocessor = PLSSPreprocessor(text)
        self.text = preprocessor.text
        if layout is None:
            layout = deduce_layout(text)
        self.layout = layout
        if clean_up is None:
            clean_up = True
            if layout == COPY_ALL:
                clean_up = False
        self.clean_up = clean_up

        # These are temporary data.
        self.twprge_matches = []
        self.working_twprge_list = []
        self.sec_matches = []
        self.working_sec_list = []
        self.markers_list = []
        self.markers_dict = {}
        self.tract_components = []
        self.unused_components = []
        self.blocks = [self.text]
        self.next_tract_uid = 0

        # These get populated and handed off.
        self.tracts = []
        self.w_flags = []
        self.w_flag_lines = []
        self.e_flags = []
        self.e_flag_lines = []

        # Append a warning flag for any Twp/Rges that were fixed during
        # preprocessing.
        for fixed in preprocessor.fixed_twprges:
            flag = f"fixed_twprge<{fixed}>"
            self.w_flags.append(flag)
            self.w_flag_lines.append((flag, flag))

        self.parse(segment=segment)

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
        sec_finder = SecFinder(text, layout)
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

    def reset(self):
        """
        Reset the cached matches, markers, etc.
        """
        self.twprge_matches = []
        self.working_twprge_list = []
        self.sec_matches = []
        self.working_sec_list = []
        self.markers_list = []
        self.markers_dict = {}
        self.tract_components = []
        self.unused_components = []
        return None

    def parse(self, segment=False):
        """
        Parse the text and create Tract objects. Populates the relevant
        attributes.
        :param segment: Whether to do a segmented parse (defaults to
        ``False``).
        """
        def flag_unused(unused_text):
            """
            Create a warning flag and flag line for unused text.
            """
            flag = f"unused_desc<{unused_text}>"
            self.w_flags.append(flag)
            self.w_flag_lines.append((flag, unused_text))

        def examine_unused():
            """
            Generate a warning flag for each block of unused text longer
            than a few characters, then reset the unused components.
            """
            for unused_chunk in self.unused_components:
                if len(unused_chunk) > 3:
                    flag_unused(unused_chunk)

        if segment:
            chunker = PLSSChunker(self.text, layout=self.layout)
            self.blocks = chunker.blocks
            self.unused_components.extend(chunker.unused_blocks)
            examine_unused()

        for chunk in self.blocks:
            self.reset()
            chunk_layout = self.layout
            if not self.mandate_layout:
                chunk_layout = deduce_layout(chunk)
            self.find_matches(chunk, chunk_layout)
            self.populate_markers(chunk)

            # Populate the tract data (self.tract_components).
            if chunk_layout in [DESC_STR, TR_DESC_S]:
                self._descstr_trdescs(chunk, chunk_layout)
            elif chunk_layout in [TRS_DESC, S_DESC_TR]:
                self._trsdesc_sdesctr(chunk, chunk_layout)
            else:
                self._copyall(chunk)

            # Convert the tract data into actual Tract objects.
            self.construct_tracts()
            examine_unused()

        self.hand_down_flags()

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

    def construct_tracts(self):
        """
        Convert the parsed data components in ``self.tract_components``
        into ``Tract`` objects, and append them to the ``self.tracts``
        list.
        """
        for tract_data in self.tract_components:
            desc = tract_data['desc']
            if self.clean_up:
                desc = cleanup_desc(desc)
            for sec in tract_data['sec']:
                trs = f"{tract_data['twprge']}{sec}"
                new_tract = Tract(
                    desc,
                    trs,
                    config=self.config,
                    parse_qq=self.parse_qq,
                    source=self.source,
                    orig_desc=self.orig_text,
                    orig_index=self.next_tract_uid
                )
                self.tracts.append(new_tract)
                self.next_tract_uid += 1
        return None

    def _descstr_trdescs(self, txt, layout=None):
        """
        Use the already-gathered matched Twp/Rge and Sec data to break
        the text down into tract components for the desc_STR and
        TR_desc_S layouts.
        """
        markers_list = self.markers_list
        markers = self.markers_dict

        # Note that these layouts are 'forward looking' (e.g., we don't
        # know what section a description block will belong to until
        # after we've encountered the description block), so we often
        # have to look at what marker type comes next. That's also why
        # we have to grab the first working_sec right away.
        working_sec = self.get_next_sec()

        # Default to errors for Twp/Rge.
        working_twprge = MasterConfig._ERR_TWPRGE

        if layout is None:
            layout = self.layout

        if layout == DESC_STR:
            working_twprge = self.get_next_twprge()

        final = len(markers_list) - 1
        for count, marker_pos in enumerate(markers_list):
            marker_type = markers[marker_pos]

            # These fall back to the current pos and type for the final
            # run through the loop.
            next_marker_pos = markers_list[min((count + 1, final))]
            next_marker_type = markers[next_marker_pos]

            if marker_type == self.TWPRGE_END:
                sec_err_pos = marker_pos

            if marker_type == self.TWPRGE_START:
                working_twprge = self.get_next_twprge()

            if next_marker_type == self.SEC_START:
                tract_identified = {
                    "desc": txt[marker_pos:next_marker_pos].strip(),
                    "sec": working_sec,
                    "twprge": working_twprge
                }
                self.tract_components.append(tract_identified)
                # Write back to the next SEC_END, if needed (i.e. if an
                # error tract is encountered later, don't include this
                # legit tract that we've just identified).
                sec_err_pos = markers_list[min((count + 2, len(markers_list) - count))]

            elif (next_marker_type == self.TWPRGE_START
                    and marker_type != self.SEC_END
                    and next_marker_pos - sec_err_pos > 5):
                # If (1) we found a Twp/Rge next, and (2) we aren't
                # CURRENTLY at a SEC_END, and (3) it's been more than a
                # few characters since we last created a new Tract, then
                # we're apparently dealing with a section error.
                tract_identified = {
                    "desc": txt[sec_err_pos:next_marker_pos].strip(),
                    "sec": MasterConfig._ERR_SEC,
                    "twprge": working_twprge
                }
                self.tract_components.append(tract_identified)

            elif marker_type == self.SEC_START:
                working_sec = self.get_next_sec()

            elif marker_type == self.TEXT_END:
                break

            # Capture unused text at the end of the string.
            if layout == TR_DESC_S:
                start_kinds = [self.SEC_START, self.TWPRGE_START]
                if marker_type == self.SEC_END and next_marker_type not in start_kinds:
                    new_unused = txt[marker_pos:next_marker_pos].strip()
                    self.unused_components.append(new_unused)

            # Capture unused text at the end of a section (if appropriate).
            elif layout == DESC_STR and count != final:
                enders = [self.SEC_END, self.TWPRGE_END]
                if marker_type in enders and next_marker_type != self.SEC_START:
                    new_unused = txt[marker_pos:next_marker_pos].strip()
                    self.unused_components.append(new_unused)
        return None

    def _trsdesc_sdesctr(self, txt, layout=None):
        """
        Use the already-gathered matched Twp/Rge and Sec data to break
        the text down into tract components for the TRS_desc and
        S_desc_TR layouts.
        """
        markers_list = self.markers_list
        markers = self.markers_dict
        # Default to errors for Twp/Rge and Sec.
        working_twprge = MasterConfig._ERR_TWPRGE
        working_sec = [MasterConfig._ERR_SEC]

        if layout is None:
            layout = self.layout

        if layout == S_DESC_TR:
            working_twprge = self.get_next_twprge()

        final = len(markers_list) - 1
        for count, marker_pos in enumerate(markers_list):
            marker_type = markers[marker_pos]

            # This falls back to the current pos for the final run
            # through the loop.
            next_marker_pos = markers_list[min((count + 1, final))]

            if marker_type == self.SEC_START:
                working_sec = self.get_next_sec()

            elif marker_type == self.SEC_END:
                tract_identified = {
                    "desc": txt[marker_pos:next_marker_pos].strip(),
                    "sec": working_sec,
                    "twprge": working_twprge
                }
                self.tract_components.append(tract_identified)

            elif marker_type == self.TWPRGE_START:
                working_twprge = self.get_next_twprge()

            elif marker_type == self.TWPRGE_END:
                new_unused = txt[marker_pos:next_marker_pos]
                self.unused_components.append(new_unused)
        return None

    def _copyall(self, txt):
        """
        Use the already-gathered matched Twp/Rge and Sec data, but parse
        as copy_all layout.
        """
        sec = self.get_next_sec()
        # Just the first section.
        sec = [sec[0]]
        twprge = self.get_next_twprge()
        copyall_tract = {
            'desc': txt,
            'sec': sec,
            'twprge': twprge
        }
        self.tract_components.append(copyall_tract)

    def get_next_twprge(self) -> str:
        """
        Get the next Twp/Rge in the working list. If no more, get an
        error Twp/Rge.
        """
        if self.working_twprge_list:
            return self.working_twprge_list.pop(0)
        else:
            return MasterConfig._ERR_TWPRGE

    def get_next_sec(self):
        """
        Get the next Sec list in the working list. If no more, get an
        error Sec inside a list.
        """
        if self.working_sec_list:
            return self.working_sec_list.pop(0)
        else:
            return [MasterConfig._ERR_SEC]


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
                self.unused_blocks.append(text[:start])

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
                self.unused_blocks.append(text[end:])

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
    implemented meaningful layouts (i.e. 'TRS_desc', 'desc_STR',
    'S_desc_TR', and 'TR_desc_S'), but will also consider 'copy_all' if
    an apparently flawed description is found. If specifying fewer than
    all candidates, ensure that at least one layout from
    ``IMPLEMENTED_LAYOUTS`` is in the list. (Strings not in
    ``IMPLEMENTED_LAYOUTS`` will have no effect.)

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


__all__ = [
    'PLSSParser',
    'deduce_layout',
    'find_twprge',

    # Public-facing info / examples.
    'TRS_DESC',
    'DESC_STR',
    'S_DESC_TR',
    'TR_DESC_S',
    'COPY_ALL',
    'IMPLEMENTED_LAYOUTS',
    'IMPLEMENTED_LAYOUT_EXAMPLES',
]
