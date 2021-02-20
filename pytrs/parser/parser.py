# Copyright (c) 2020, James P. Imes, All rights reserved.

"""
The main parsing package. Primary classes:
> PLSSDesc objects parse PLSS description text (full descriptions) into
    Tract objects (one TRS + description per Tract), stored as TractList
> Tract objects parse tract text into lots and aliquots.
> TractList objects contain a list of Tracts, and can compile that Tract
    data into broadly useful formats (i.e. into list, dict, string).
> Config objects configure parsing parameters for Tract and PLSSDesc.
> ParseBag objects handle data within / between Tract and PLSSDesc.
"""

import re
from .regexlib import (
    twprge_regex,
    twprge_broad_regex,
    sec_regex,
    multiSec_regex,
    comma_multiSec_regex,
    noNum_sec_regex,
    preproTR_noNSWE_regex,
    preproTR_noR_noNS_regex,
    preproTR_noT_noWE_regex,
    twprge_ocr_scrub_regex,
    lots_context_regex,
    TRS_unpacker_regex,
    well_regex,
    depth_regex,
    including_regex,
    less_except_regex,
    isfa_regex,
    NE_regex,
    SE_regex,
    NW_regex,
    SW_regex,
    N2_regex,
    S2_regex,
    E2_regex,
    W2_regex,
    ALL_regex,
    ALL_context_regex,
    cleanNE_regex,
    cleanSE_regex,
    cleanNW_regex,
    cleanSW_regex,
    halfPlusQ_regex,
    through_regex,
    lot_regex,
    lot_with_aliquot_regex,
    lotAcres_unpacker_regex,
    aliquot_unpacker_regex,
    single_aliquot_unpacker_regex,
    aliquot_intervener_remover_regex,
    aliquot_lot_intervener_scrubber_regex,
    pm_regex,
    twprge_pm_regex,
    sec_within_desc_regex
)

# All current layouts
TRS_DESC = "TRS_desc"
DESC_STR = "desc_STR"
S_DESC_TR = "S_desc_TR"
TR_DESC_S = "TR_desc_S"
COPY_ALL = "copy_all"

# A tuple of all currently implemented layouts:
_IMPLEMENTED_LAYOUTS = (
    TRS_DESC, DESC_STR, S_DESC_TR, TR_DESC_S, COPY_ALL
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

# For aliquot parsing.
QQ_HALVES = ('N', 'S', 'E', 'W')
QQ_QUARTERS = ('NE', 'NW', 'SE', 'SW')
QQ_SUBDIVIDE_DEFINITIONS = {
    'ALL': QQ_QUARTERS,
    'N': ('NE', 'NW'),
    'S': ('SE', 'SW'),
    'E': ('NE', 'SE'),
    'W': ('NW', 'SW'),
}
QQ_NS = ("N", "S")
QQ_EW = ("E", "W")
QQ_SAME_AXIS = {
    "N": QQ_NS,
    "S": QQ_NS,
    "E": QQ_EW,
    "W": QQ_EW
}

# Define what should replace matches of each regex that is used in the
# _scrub_aliquots() function.
QQ_SCRUBBER_DEFINITIONS = {
    NE_regex: 'NE¼',
    NW_regex: 'NW¼',
    SE_regex: 'SE¼',
    SW_regex: 'SW¼',
    N2_regex: 'N½',
    S2_regex: 'S½',
    E2_regex: 'E½',
    W2_regex: 'W½',
    cleanNE_regex: 'NE¼',
    cleanNW_regex: 'NW¼',
    cleanSE_regex: 'SE¼',
    cleanSW_regex: 'SW¼'
}

CONFIG_ERROR = TypeError(
    "config must be a str, None, or another Config object.")

DEFAULT_NS_ERROR = ValueError(
    "default_ns must be either 'n' or 's'."
)

DEFAULT_EW_ERROR = ValueError(
    "default_ew must be either 'e' or 'w'."
)


class PLSSDesc:
    """
    Each object of this class is a full PLSS description, taking the raw
    text of the original description as input, and parsing it into one
    or more pyTRS.Tract objects (each Tract containing one Twp/Rge/Sec
    combo and the corresponding description of the land within that TRS,
    optionally with lots and quarter-quarters, or QQ's, broken out --
    see pyTRS.Tract documentation for more details).

    Configure the parsing algorithm with config parameters at init,
    passed in `config=` (taking either a pyTRS.Config object or a string
    containing equivalent config parameters -- see documentation on
    pyTRS.Config objects for possible parameters).

    ____ PARSING ____
    Parse the PLSSDesc object into pyTRS.Tract objects with the
    `.parse()` method at some point after init. Alternatively, trigger
    the parse at init in one of several ways:
    -- Use init parameter `init_parse=True` (parses the PLSSDesc object
        into Tract objects, which are NOT yet parsed into lots and
        QQ's).
    -- Use init parameter `init_parse_qq=True` (parses the PLSSDesc object
        into Tract objects, which ARE then immediately parsed into lots
        and QQ's)
    -- Include string 'init_parse' and/or 'init_parse_qq' among the config
        parameters that are passed in `config=` at init.
    (NOTE: init_parse_qq entails init_parse, but not vice-versa.)

    ____ IMPORTANT INSTANCE VARIABLES AFTER PARSING ____
    .orig_desc -- The original text. (Gets set from the first positional
        argument at init.)
    .parsed_tracts -- A pyTRS.TractList object (i.e. a list) containing
        all of the pyTRS.Tract objects that were generated from parsing
        this object.
    .pp_desc -- The preprocessed description. (If the object has not yet
        been preprocessed, it will be equivalent to .orig_desc)
    .source -- (Optional) A string specifying where the description came
        from. Useful if parsing multiple descriptions and need to
        internally keep track where they came from. (Optionally specify
        at init with parameter `source=<str>`.)
    .w_flags -- a list of warning flags (strings) generated during
        preprocessing and/or parsing.
    .w_flag_lines -- a list of 2-tuples, each being a warning flag and the
        line or context from the description that caused the warning.
    .e_flags -- a list of error flags (strings) generated during
        preprocessing and/or parsing.
    .e_flag_lines -- a list of 2-tuples, each being an error flag and the
        line or context from the description that caused the error.
    .desc_is_flawed -- a bool, whether or not an apparently fatal flaw was
        discovered during parsing.
    .layout -- The user-dictated or algorithm-deduced layout of the
        description (controls how the parsing algorithm interprets the
        text).

    ____ STREAMLINED OUTPUT OF THE PARSED DATA ____
    See the notable instance variables listed in the pyTRS.Tract object
    documentation. Those variables can be compiled with these PLSSDesc
    methods:
    .quick_desc() -- Returns a string of the entire parsed description.
    .print_desc() -- Does the same thing, but prints to console.
    .tracts_to_dict() -- Compile the requested attributes for each Tract
        into a dict, and returns a list of those dicts (i.e. the list is
        equal in length to `.parsed_tracts` TractList).
    .tracts_to_list() -- Compile the requested attributes for each Tract
        into a list, and returns a nested list of those list (i.e. the
        top-level list is equal in length to `.parsed_tracts` TractList).
    .tracts_to_str() -- Compile the requested attributes for each Tract
        into a string-based table, and return a single string of all
        tables.
    .list_trs() -- Return a list of all twp/rge/sec combinations in the
        `.parsed_tracts` TractList, optionally removing duplicates.
    .print_data() -- Equivalent to `.tracts_to_dict()`, but the data
        is formatted as a table and printed to console.

    ____ OTHER NOTABLE METHODS ____
    These methods are used before or during the parse, and are typically
    called automatically:
    .deduce_layout() -- Deduces the layout of the description, if it was
        not dictated at init, or otherwise.
    ._deduce_segment_layout() -- (Static method)  Deduces the layout of a
        segment of the description.
    .preprocess() -- Attempt to scrub the original description of common
        flaws, typos, etc. into a format more consistently understood by
        the parser.
    .static_preprocess() -- (Static method)  Same as .preprocess(), but
        processes text without saving any data.
    .gen_flags() -- Scour the text for potential flag-raising issues.
    """

    def __init__(
            self, orig_desc: str, source='', layout=None, config=None,
            init_parse=None, init_parse_qq=None):
        """
        A 'raw' PLSS description of land. Will be parsed into one or
        more Tract objects, which are stored in the `.parsed_tracts`
        instance variable (a list).

        :param orig_desc: The text of the description to be parsed.
        :param source: (Optional) A string specifying where the
        description came from. (Useful if parsing multiple descriptions
        and need to internally keep track where they came from.)
        :param layout: The pyTRS layout. If not specified, will be
        deduced when initialized, and/or when parsed. See available
        options in `pyTRS.IMPLEMENTED_LAYOUTS` and examples in
        `pyTRS.IMPLEMENTED_LAYOUT_EXAMPLES`.
        :param config: Either a pyTRS.Config object, or a string of
        parameters to configure how the PLSSDesc object should be
        parsed. (See documentation on pyTRS.Config objects for optional
        config parameters.)
        :param init_parse: Whether to parse this PLSSDesc object when
        initialized.
        NOTE: If `init_parse` is specified as a kwarg at init, and also
        specified in the `config` (i.e. config='init_parse'), then the
        kwarg `init_parse=<bool>` will control.
        :param init_parse_qq: Whether to parse this PLSSDesc object and
        each resulting Tract object (into lots and QQs) when
        initialized.
        NOTE: If `init_parse_qq` is specified as a kwarg at init, and also
        specified in the `config` (i.e. config='init_parse_qq'), then the
        kwarg `init_parse_qq=<bool>` will control.
        """

        # The original input of the PLSS description:
        self.orig_desc = orig_desc

        # If something other than a string is fed in, raise a TypeError
        if not isinstance(orig_desc, str):
            raise TypeError(
                f"`orig_desc` must be of type 'string'. "
                f"Passed as type {type(orig_desc)}.")

        # The source of this PLSS description:
        self.source = source

        # The layout of this PLSS description -- Initially None, but will be
        # set to one of the values in the _IMPLEMENTED_LAYOUTS list before
        # __init__() returns -- either by kwarg `layout=`, or by
        # `set_config()`:
        self.layout = None

        # Whether the layout was specified at initialization.
        self.layout_specified = False

        # If a T&R is identified without 'North/South' specified, or without
        # 'East/West' specified, fall back on default_ns and default_ew,
        # respectively. Each will be filled in with set_config (if applicable),
        # or defaulted to 'n' and 'w' soon.
        self.default_ns = None
        self.default_ew = None

        ###############################################################
        # NOTE: the following default bools will be changed in
        # set_config(), as applicable.
        ###############################################################

        # Whether we should preprocess the text at initialization:
        self.init_preprocess = True

        # Whether we should parse the text at initialization:
        self.init_parse = False

        # Whether we should parse lots and aliquots in each Tract when created.
        # NOTE: In effect, `init_parse_qq==True` also entails
        # `self.init_parse==True` -- but NOT vice-versa
        self.init_parse_qq = False

        # Whether tract descriptions are expected to have `clean_qq` (i.e.
        # nothing but clean aliquots and lots, with no typos, exceptions,
        # metes-and-bounds, or other hindrances to the parser.)
        self.clean_qq = False

        # Whether we should require a colon between Section ## and tract
        # description (for TRS_DESC and S_DESC_TR layouts):
        self.require_colon = True

        # Whether to include any divisions of lots
        # (i.e. 'N/2 of Lot 1' -> 'N2 of L1')
        self.include_lot_divs = True

        # Whether to iron out common OCR artifacts.
        # NOTE: Currently only has effect of cleaning up T&R's during
        # `.preprocess()`.  May have more effect in a later version.
        self.ocr_scrub = False

        # Whether to segment the text during parsing (can /potentially/
        # capture descriptions with multiple layouts):
        self.segment = False

        # Attributes to control how deeply QQ's should be parsed.
        # If `.qq_depth` is set, it will override `.qq_depth_min` and
        # `.qq_depth_max`
        self.qq_depth = None
        self.qq_depth_min = 2
        self.qq_depth_max = None
        self.break_halves = False

        # Apply settings from `config=`.
        self.set_config(config)

        # If `default_ns` has not yet been specified, default to 'n'
        if self.default_ns is None:
            self.default_ns = 'n'

        # If `default_ew` has not yet been specified, default to 'w'
        if self.default_ew is None:
            self.default_ew = 'w'

        # Track fatal flaws in the parsing of this PLSS description
        self.desc_is_flawed = False
        # list of Tract objs, after parsing (TractList is a subclass of `list`)
        self.parsed_tracts = TractList()
        # list of warning flags
        self.w_flags = []
        # list of 2-tuples that caused warning flags (warning flag, text string)
        self.w_flag_lines = []
        # list of error flags
        self.e_flags = []
        # list of 2-tuples that caused error flags (error flag, text string)
        self.e_flag_lines = []
        # Track whether the preprocess has been completed
        self.preprocess_done = False

        # If init_parse_qq specified as init parameter, it will override
        # `config` parameter.
        #    ex:   config='n,w,init_parse_qq', init_parse_qq=False   ...
        #       -> Will NOT parse lots/QQs at init.
        if isinstance(init_parse_qq, bool):
            self.init_parse_qq = init_parse_qq

        # If kwarg-specified init_parse, that will override config input
        #   (similar to init_parse_qq)
        if isinstance(init_parse, bool):
            self.init_parse = init_parse

        ocr_scrub_now = False
        if self.ocr_scrub:
            ocr_scrub_now = True

        # Optionally can preprocess the desc when the object is initiated
        # (on by default).
        if self.init_preprocess or ocr_scrub_now:
            self.preprocess(commit=True, ocr_scrub=ocr_scrub_now)
        else:
            # Preprocessed descrip set to .orig_desc if preprocess is declined
            self.pp_desc = self.orig_desc

        # If layout was specified as kwarg, use that:
        if layout is not None:
            self.layout = layout
            self.layout_specified = True

        # If layout has not yet been /validly/ set by the user or
        # set_config(), deduce it:
        if self.layout not in _IMPLEMENTED_LAYOUTS:
            self.layout = self.deduce_layout(commit=True)
            self.layout_specified = False

        # Compile and store the final Config file (for passing down to
        # Tract objects)
        self.config = Config.from_parent(self)

        # Optionally can run the parse when the object is initiated
        # (off by default).
        if self.init_parse or self.init_parse_qq:
            self.parse(commit=True)

    def __str__(self):
        pt = len(self.parsed_tracts)
        return (
            "PLSSDesc ({0})\n"
            "Source: {1}\n"
            "Total Tracts: {2}\n"
            "Tracts: {3}\n"
            "Original description:\n"
            "{4}").format(
                "Unparsed" if pt == 0 else "Parsed",
                self.source,
                "n/a" if pt == 0 else pt,
                self.parsed_tracts.snapshot_inside(),
                self.orig_desc)

    def set_config(self, config):
        """
        Apply the relevant settings from a Config object to this object;
        takes either a string (i.e. config text) or a Config object.

        :param config: Either a pyTRS.Config object, or equivalent
        config parameters. (See pyTRS.Config documentation for optional
        parameters.)
        """
        if isinstance(config, str) or config is None:
            config = Config(config)
        if not isinstance(config, Config):
            raise CONFIG_ERROR

        for attrib in Config._PLSSDESC_ATTRIBUTES:
            value = getattr(config, attrib)
            if value is not None:
                setattr(self, attrib, value)
                if attrib == 'layout':
                    self.layout_specified = True

    def _unpack_pb(self, target_pb):
        """
        Unpack (append or set) the relevant attributes of the
        `target_pb` into self's attributes.

        :param target_pb: A ParseBag object containing data from
        the parse.
        """

        if not isinstance(target_pb, ParseBag):
            raise TypeError("Can only `_unpack_pb()` a pyTRS.ParseBag object.")

        if target_pb.desc_is_flawed:
            self.desc_is_flawed = True

        if len(target_pb.w_flags) > 0:
            self.w_flags.extend(target_pb.w_flags)

        if len(target_pb.e_flags) > 0:
            self.e_flags.extend(target_pb.e_flags)

        if len(target_pb.w_flag_lines) > 0:
            self.w_flag_lines.extend(target_pb.w_flag_lines)

        if len(target_pb.e_flag_lines) > 0:
            self.e_flag_lines.extend(target_pb.e_flag_lines)

        if len(target_pb.parsed_tracts) > 0:
            self.parsed_tracts.extend(target_pb.parsed_tracts)

    def parse(
            self, text=None, layout=None, clean_up=None, init_parse_qq=None,
            clean_qq=None, require_colon='default_colon', segment=None,
            commit=True, qq_depth_min=None, qq_depth_max=None, qq_depth=None,
            break_halves=None):
        """
        Parse the description. If parameter `commit=True` (defaults to
        on), the results will be stored to the various instance
        attributes (.parsed_tracts, .w_flags, .w_flag_lines, .e_flags,
        and .e_flag_lines). Returns only the TractList object containing
        the parsed Tract objects (i.e. what would be stored to
        `.parsed_tracts`).

        :param text: The text to be parsed. If not specified, defaults
        to the string currently stored in `self.pp_desc` (i.e. the
        pre-processed description).
        :param layout: The layout to be assumed. If not specified,
        defaults to whatever is in `self.layout`.
        :param clean_up: Whether to clean up common 'artefacts' from
        parsing. If not specified, defaults to False for parsing the
        'copy_all' layout, and `True` for all others.
        :param init_parse_qq: Whether to parse each resulting Tract object
        into lots and QQs when initialized. If not specified, defaults
        to whatever is specified in `self.init_parse_qq`.
        :param clean_qq: Whether to expect only clean lots and QQ's (i.e.
        no metes-and-bounds, exceptions, complicated descriptions,
        etc.). Defaults to whatever is specified in `self.clean_qq`
        (which is False, unless configured otherwise).
        :param require_colon: Whether to require a colon between the
        section number and the following description (only has an effect
        on 'TRS_desc' or 'S_desc_TR' layouts).
        If not specified, it will default to a 'two-pass' method, where
        first it will require the colon; and if no matching sections are
        found, it will do a second pass where colons are not required.
        Setting as `True` or `False` here prevent the two-pass method.
            ex: 'Section 14 NE/4'
                `require_colon=True` --> no match
                `require_colon=False` --> match (but beware false
                    positives)
                <not specified> --> no match on first pass; if no other
                            sections are identified, will be matched on
                            second pass.
        :param segment: Whether to break the text down into segments,
        with one MATCHING township/range per segment (i.e. only T&R's
        that are appropriate to the specified layout will count for the
        purposes of this parameter). This can potentially capture
        descriptions whose layout changes partway through, but can also
        cause appropriate warning/error flags to be missed. If not
        specified here, defaults to whatever is set in `self.segment`.
        :param commit: Whether to commit the results to the appropriate
        instance attributes. Defaults to `True`.
        :param qq_depth_min: (Optional, and only relevant if parsing
        Tracts into lots and QQs.) An int, specifying the minimum depth
        of the parse. If not set here, will default to settings from
        init (if any), which in turn default to 2, i.e. to
        quarter-quarters (e.g., 'N/2NE/4' -> ['NENE', 'NENE']).
        Setting to 3 would return 10-acre subdivisions (i.e. dividing
        the 'NENE' into ['NENENE', 'NWNENE', 'SENENE', 'SWNENE']), and
        so forth.
        WARNING: Higher than a few levels of depth will result in very
        slow performance.
        :param qq_depth_max: (Optional, and only relevant if parsing
        Tracts into lots and QQs.) An int, specifying the maximum depth
        of the parse. If set as 2, any subdivision smaller than
        quarter-quarter (e.g., 'NENE') would be discarded -- so, for
        example, the 'N/2NE/4NE/4' would simply become the 'NENE'. Must
        be greater than or equal to `qq_depth_min`. (Defaults to None --
        i.e. no maximum. Can also be configured at init.)
        :param qq_depth: (Optional, and only relevant if parsing Tracts
        into lots and QQs.) An int, specifying both the minimum and
        maximum depth of the parse. If specified, will override both
        `qq_depth_min` and `qq_depth_max`. (Defaults to None -- i.e. use
        qq_depth_min and optionally qq_depth_max; and can optionally be
        configured at init.)
        :param break_halves: (Optional, and only relevant if parsing
        Tracts into lots and QQs.) Whether to break halves into
        quarters, even if we're beyond the qq_depth_min. (False by
        default, but can be configured at init.)
        :return: Returns a pyTRS.TractList object (a subclass of 'list')
        of all of the resulting pyTRS.Tract objects.
        """

        # ----------------------------------------
        # Lock down parameters for this parse.

        if commit:
            # Wipe the existing parsed_tracts, if any.
            self.parsed_tracts = TractList()

        if text is None:
            text = self.pp_desc
            # Unless specified otherwise, we get the flagLists and flagLines from the
            # ORIGINAL description, rather than from the preprocessed description
            flagText = self.orig_desc
        else:
            flagText = text

        # When layout is specified at init, or when calling
        # `.parse(layout=<string>)`, we prevent _parse_segment() from deducing,
        # AS LONG AS the specified layout is among the implemented layouts.
        layout_specified = False
        if layout in _IMPLEMENTED_LAYOUTS:
            layout_specified = True
        else:
            # If not otherwise specified, pull from self attribute.
            layout = self.layout
            layout_specified = self.layout_specified
            # As a stopgap, if it's still not an acceptable layout, deduce it.
            if layout not in _IMPLEMENTED_LAYOUTS:
                layout = self.deduce_layout(commit=False)

        if init_parse_qq is None:
            init_parse_qq = self.init_parse_qq

        if clean_qq is None:
            clean_qq = self.clean_qq

        # Config object for passing down to Tract objects.
        config = self.config

        if not isinstance(segment, bool):
            segment = self.segment

        if layout == COPY_ALL:
            # If a *segment* (which will be divided up shortly) finds itself in
            # the COPY_ALL layout, that should still parse fine. But
            # segmenting the whole description would defy the point of
            # COPY_ALL layout. So prevent `segment` when the OVERALL layout
            # is COPY_ALL
            segment = False

        # For QQ parsing (if applicable)
        if break_halves is None:
            break_halves = self.break_halves
        if qq_depth is None and qq_depth_min is None and qq_depth_max is None:
            qq_depth = self.qq_depth
        if qq_depth_min is None:
            qq_depth_min = self.qq_depth_min
        if qq_depth_max is None:
            qq_depth_max = self.qq_depth_max

        # ParseBag obj for storing the data generated throughout.
        bigPB = ParseBag(parent_type='PLSSDesc')

        if len(text) == 0 or not isinstance(text, str):
            bigPB.e_flags.append('noText')
            bigPB.e_flag_lines.append(
                ('noText', '<No text was fed into the program.>'))
            return bigPB

        if not isinstance(clean_up, bool):
            if layout in [TRS_DESC, DESC_STR, S_DESC_TR, TR_DESC_S]:
                # Default `clean_up` to True only for these layouts
                clean_up = True
            else:
                clean_up = False

        # ----------------------------------------
        # If doing a segment parse, break it up into segments now
        if segment:
            # Segment text into blocks, based on T&Rs that match our
            # layout requirements
            trTextBlocks, discard_trTextBlocks = _segment_by_tr(
                text, layout=layout, twprge_first=None)

            # Append any discard text to the w_flags
            for textBlock in discard_trTextBlocks:
                bigPB.w_flags.append(f"Unused_desc_<{textBlock}>")
                bigPB.w_flag_lines.append(
                    (f"Unused_desc_<{textBlock}>", textBlock))

        else:
            # If not segmented parse, pack entire text into list, with
            # a leading empty str (to mirror the output of the
            # _segment_by_tr() function)
            trTextBlocks = [('', text)]

        # ----------------------------------------
        # Parse each segment into a separate ParseBag obj, then absorb
        # that PB into the big PB each time:
        for textBlock in trTextBlocks:
            use_layout = layout
            if segment and layout != COPY_ALL:
                # Let the segment parser deduce layout for each text_block.
                use_layout = None
            midParseBag = _parse_segment(
                textBlock[1], clean_up=clean_up, require_colon=require_colon,
                layout=use_layout, handed_down_config=config,
                init_parse_qq=init_parse_qq, clean_qq=clean_qq,
                qq_depth_min=qq_depth_min, qq_depth_max=qq_depth_max,
                qq_depth=qq_depth, break_halves=break_halves)
            bigPB.absorb(midParseBag)

        # If we've still not discovered any Tracts, run a final parse in
        # layout COPY_ALL, and include appropriate errors.
        if len(bigPB.parsed_tracts) == 0:
            bigPB.absorb(
                _parse_segment(
                    text, layout=COPY_ALL, clean_up=False, require_colon=False,
                    handed_down_config=config, init_parse_qq=init_parse_qq,
                    clean_qq=clean_qq, qq_depth_min=qq_depth_min,
                    qq_depth_max=qq_depth_max, qq_depth=qq_depth,
                    break_halves=break_halves))
            bigPB.desc_is_flawed = True

        for TractObj in bigPB.parsed_tracts:
            if TractObj.trs[:5] == 'TRerr':
                bigPB.e_flags.append('trError')
                bigPB.e_flag_lines.append(
                    ('trError', TractObj.trs + ':' + TractObj.desc))
                bigPB.desc_is_flawed = True
            if TractObj.trs[-2:] == 'or':
                bigPB.e_flags.append('secError')
                bigPB.e_flag_lines.append(
                    ('secError', TractObj.trs + ':' + TractObj.desc))
                bigPB.desc_is_flawed = True

        # Check for warning flags (and a couple error flags).
        # Note that .gen_flags() is being run on `flagText`, not `text`.
        flagParseBag = self.gen_flags(text=flagText, commit=False)
        bigPB.absorb(flagParseBag)

        # We want each Tract to have the entire PLSSDesc's warnings,
        # because a computer can't automatically tell which limitations,
        # etc. apply to which Tracts. (This is an ambiguity that often
        # exists in the data, even when humans read it.) So for robust
        # data, we apply flags from the whole PLSSDesc to each Tract.
        # It will only _unpack the flags and flaglines, because that's
        # all that is relevant to a Tract. Also apply TractNum (i.e.
        # orig_index).
        # Also, `tempPB` takes the wFlags and eFlags from the PLSSDesc
        # object that may have been generated prior to calling .parse(),
        # and they get passed down to each TractObj too.
        tempPB = ParseBag()
        tempPB.w_flags = self.w_flags
        tempPB.w_flag_lines = self.w_flag_lines
        tempPB.e_flags = self.e_flags
        tempPB.e_flag_lines = self.e_flag_lines
        TractNum = 0
        for TractObj in bigPB.parsed_tracts:

            # Unpack the flags from the PLSSDesc, held in `tempPB`.
            TractObj._unpack_pb(tempPB)

            # Unpack the flags, etc. from `bigPB`.
            TractObj._unpack_pb(bigPB)

            # And hand down the PLSSDesc object's `.source` and `.orig_desc`
            # attributes to each of the Tract objects:
            TractObj.source = self.source
            TractObj.orig_desc = self.orig_desc

            # And apply the TractNum for each Tract object:
            TractObj.orig_index = TractNum
            TractNum += 1

        if commit:
            self._unpack_pb(bigPB)

        # Return the list of identified `Tract` objects (ie. a TractList object)
        return bigPB.parsed_tracts

    @staticmethod
    def _deduce_segment_layout(text, candidates=None, deduce_by='TRS_order'):
        """
        INTERNAL USE:
        Deduce the layout of a *segment* of a description, without
        committing any results.

        :param text: The text, whose layout is to be deduced.
        :param candidates: A list of which layouts are to be considered.
        If passed as `None` (the default), it will consider all
        currently implemented meaningful layouts (i.e. 'TRS_desc',
        'desc_STR', 'S_desc_TR', and 'TR_desc_S'), but will also
        consider 'copy_all' if an apparently flawed description is
        found. If specifying fewer than all candidates, ensure that at
        least one layout from _IMPLEMENTED_LAYOUTS is in the list.
        (Strings not in _IMPLEMENTED_LAYOUTS will have no effect.)
        :param deduce_by: The preferred deduction algorithm. (Currently
        only uses 'TRS_order' -- i.e. basically, the apparent order of
        the Twp, Rge, Sec, and description block.)
        :return: Returns the algorithm's best guess at the layout (i.e.
        a string).
        """

        return PLSSDesc.deduce_layout(
            self=None, text=text, candidates=candidates, deduce_by=deduce_by,
            commit=False)

    def deduce_layout(
            self, text=None, candidates=None, deduce_by='TRS_order',
            commit=True):
        """
        Deduce the layout of the description.

        :param text: The text, whose layout is to be deduced.
        If not specified, will use whatever is stored in `self.pp_desc`,
        i.e. the preprocessed description.
        :param candidates: A list of which layouts are to be considered.
        If passed as `None` (the default), it will consider all
        currently implemented meaningful layouts (i.e. 'TRS_desc',
        'desc_STR', 'S_desc_TR', and 'TR_desc_S'), but will also
        consider 'copy_all' if an apparently flawed description is
        found. If specifying fewer than all candidates, ensure that at
        least one layout from _IMPLEMENTED_LAYOUTS is in the list.
        (Strings not in _IMPLEMENTED_LAYOUTS will have no effect.)
        :param deduce_by: The preferred deduction algorithm. (Currently
        only uses 'TRS_order' -- i.e. basically, the apparent order of
        the Twp, Rge, Sec, and description block.)
        :param commit: Whether to store the guessed layout to
        `self.layout`.
        :return: Returns the algorithm's best guess at the layout (i.e.
        a string).
        """

        if text is None:
            text = self.pp_desc

        if not isinstance(candidates, list):
            candidates = [TRS_DESC, DESC_STR, S_DESC_TR, TR_DESC_S]

        try_TRS_desc = TRS_DESC in candidates
        try_desc_STR = DESC_STR in candidates
        try_S_desc_TR = S_DESC_TR in candidates
        try_TR_desc_S = TR_DESC_S in candidates
        try_subdivision = 'subdivision' in candidates

        if deduce_by == 'demerits':
            # Not yet ready for deployment. Fall back to 'TRS_order'.
            return self.deduce_layout(
                text=text, candidates=candidates, deduce_by='TRS_order',
                commit=commit)

        else:
            # Default to 'TRS_order' (i.e. check whether a Section comes
            # before a T&R, or vice versa). Strip out whitespace for this
            # (mainly to avoid false misses in S_DESC_TR).

            # we use the noNum version of the sec_regex here
            sec_mo = noNum_sec_regex.search(text.strip())
            tr_mo = twprge_broad_regex.search(text.strip())

            if sec_mo is None:
                # If we find no Sections, best guess is it's a
                # subdivision (as long as that's an option).
                if try_subdivision:
                    layoutGuess = 'subdivision'
                    if commit:
                        self.layout = layoutGuess
                    return layoutGuess
                else:
                    # If subdivision isn't option, default to COPY_ALL,
                    # as no identifiable section is an insurmountable flaw
                    layoutGuess = COPY_ALL
                    if commit:
                        self.layout = layoutGuess
                    return layoutGuess

            if tr_mo is None:
                # If found no T&R's, default to COPY_ALL because desc is
                # likely flawed.
                layoutGuess = COPY_ALL
                if commit:
                    self.layout = layoutGuess
                return layoutGuess

            # If the first identified section comes before the first
            # identified T&R, then it's probably DESC_STR or S_DESC_TR:
            if sec_mo.start() < tr_mo.start():
                if try_S_desc_TR:
                    # This is such an unlikely layout, we give it very
                    # limited room for error. If the section comes first
                    # in the description, we should expect it VERY early
                    # in the text:
                    if sec_mo.start() <= 1:
                        layoutGuess = S_DESC_TR
                    else:
                        layoutGuess = DESC_STR
                else:
                    layoutGuess = DESC_STR
            else:
                # If T&R comes before Section, it's most likely TRS_DESC,
                # but could also be TR_DESC_S. Check how many characters
                # appear between T&R and Sec, and decide whether it's
                # TR_DESC_S or TRS_DESC, based on that.
                stringBetween = text.strip()[tr_mo.end():sec_mo.start()].strip()
                if len(stringBetween) >= 4 and try_TR_desc_S:
                    layoutGuess = TR_DESC_S
                else:
                    layoutGuess = TRS_DESC

        if commit:
            self.layout = layoutGuess

        return layoutGuess

    @staticmethod
    def static_preprocess(text, default_ns='n', default_ew='w', ocr_scrub=False):
        """
        Run the description preprocessor on text without storing any
        data / objects.

        :param text: The text (string) to be preprocessed.
        :param default_ns: How to interpret townships for which direction
        was not specified -- i.e. either 'n' or 's'. (Defaults to 'n')
        :param default_ew: How to interpret ranges for which direction
        was not specified -- i.e. either 'e' or 'w'. (Defaults to 'w')
        :param ocr_scrub: Whether to try to iron out common OCR
        'artifacts'. May cause unintended changes. (Defaults to `False`)
        :return: The preprocessed string.
        """

        dummyObj = PLSSDesc(text, config='preprocess.False')
        return dummyObj.preprocess(
            default_ns=default_ns, default_ew=default_ew, ocr_scrub=ocr_scrub,
            commit=False)

    def preprocess(
            self, text=None, default_ns=None, default_ew=None, commit=True,
            ocr_scrub=None) -> str:
        """
        Preprocess the PLSS description to iron out common kinks in
        the input data, and optionally store results to `self.pp_desc`.

        :param text: The text to be preprocessed. Defaults to what is
        stored in `self.orig_desc` (i.e. the original description).
        :param default_ns: How to interpret townships for which direction
        was not specified -- i.e. either 'n' or 's'. (Defaults to
        `self.default_ns`, which is 'n' unless otherwise specified.)
        :param default_ew: How to interpret ranges for which direction
        was not specified -- i.e. either 'e' or 'w'. (Defaults to
        `self.default_ew`, which is 'w' unless otherwise specified.)
        :param ocr_scrub: Whether to try to iron out common OCR
        'artifacts'. May cause unintended changes. (Defaults to
        `self.ocr_scrub`, which is `False` unless otherwise specified.)
        :param commit: Whether to store the resluts to `self.pp_desc`.
        (Defaults to `True`)
        :return: The preprocessed string.
        """

        # Defaults to pulling the text from the orig_desc of the object:
        if text is None:
            text = self.orig_desc

        if default_ns is None:
            default_ns = self.default_ns

        if default_ew is None:
            default_ew = self.default_ew

        if ocr_scrub is None:
            ocr_scrub = self.ocr_scrub

        # Look for T&R's in original text (for checking if we fix any
        # during preprocess, to raise a wFlag)
        cleanTR_list = find_twprge(text)

        # Run each of the prepro regexes over the text, each working on
        # the last-prepro'd version of the text. Swaps in the cleaned up
        # TR (format 'T000N-R000W') for each T&R, every time.
        ppRegexes = [
            twprge_regex, preproTR_noNSWE_regex, preproTR_noR_noNS_regex,
            preproTR_noT_noWE_regex, twprge_pm_regex
        ]
        if ocr_scrub:
            # This invites potential mis-matches, so it is not included
            # by default. Turn on with `ocr_scrub=True` kwarg, or at init
            # with `config='ocr_scrub'`.
            ppRegexes.insert(0, twprge_ocr_scrub_regex)

        for ppRegex in ppRegexes:
            i = 0
            # working preprocessed description (gets reconstructed every loop):
            w_pp_desc = ''
            while True:
                searchTextBlock = text[i:]
                ppTr_mo = ppRegex.search(searchTextBlock)

                if ppTr_mo is None:
                    # If we've found no more T&R's, append the remaining
                    # text_block and end the loop
                    w_pp_desc = w_pp_desc + searchTextBlock
                    break

                # Need some additional context to rule out 'Lots 6, 7, East'
                # as matching as "T6S-R7E" (i.e. the 'ts' in 'Lots' as being
                # picked up as 'Township'):
                if ppRegex == preproTR_noR_noNS_regex:
                    lk_back = 3  # We'll look behind this many characters
                    if lk_back > ppTr_mo.start() + i:
                        lk_back = ppTr_mo.start() + i

                    # Get a context string containing that many characters
                    # behind, plus a couple ahead. Will look for "Lot" or "Lots"
                    # (allowing for slight typo) in that string:
                    cntxt_str = text[i + ppTr_mo.start() - lk_back: i + ppTr_mo.start() + 2]
                    lot_check_mo = lots_context_regex.search(cntxt_str)
                    if lot_check_mo is not None:
                        # If we matched, then we're dealing with a false
                        # T&R match, and we need to move on.
                        w_pp_desc = w_pp_desc + searchTextBlock[:ppTr_mo.end()]
                        i = i + ppTr_mo.end()
                        continue

                cleanTR = _preprocess_twprge_mo(
                    ppTr_mo, default_ns=default_ns, default_ew=default_ew)

                # Add to the w_pp_desc all of the searchTextBlock, up to the
                # identified ppTr_mo, and add the cleanTR, with some spaces
                # around it, just to keep it cleanly delineated from
                # surrounding text
                w_pp_desc = w_pp_desc + searchTextBlock[:ppTr_mo.start()] + ' ' + cleanTR + ' '

                # Move the search index to the end of the ppTr_mo. Note
                # that ppTr_mo is indexed against the searchTextBlock,
                # so we have to add its .end() to i (which is indexed
                # against the source text)
                i = i + ppTr_mo.end()

            text = w_pp_desc

        # Clean up white space:
        text = text.strip()
        while True:
            # Scrub until text at start of loop == text at end of loop.
            text1 = text

            # Forbid consecutive spaces
            text1 = text1.replace('  ', ' ')
            # Maximum of two linebreaks in a row
            text1 = text1.replace('\n\n\n', '\n\n')
            # Remove spaces at the start of a new line
            text1 = text1.replace('\n ', '\n')
            # Remove tabs at the start of a new line
            text1 = text1.replace('\n\t', '\n')
            if text1 == text:
                break
            text = text1

        # Look for T&R's in the preprocessed text
        afterPrepro_TR_list = find_twprge(text)

        # Remove from the post-preprocess TR list each of the elements
        # in the list generated from the original text.
        for tr in cleanTR_list:
            if tr in afterPrepro_TR_list:
                afterPrepro_TR_list.remove(tr)

        if commit:
            self.pp_desc = text
            if len(afterPrepro_TR_list) > 0:
                # If any T&R's still remain in the post-pp_desc-generated
                # T&R list...
                self.w_flags.append(
                    'T&R_fixed<%s>' % '//'.join(afterPrepro_TR_list))
                # Append a tuple to the w_flag_lines list:
                self.w_flag_lines.append(
                    (f"T&R_fixed<{'//'.join(afterPrepro_TR_list)}>",
                     '//'.join(afterPrepro_TR_list)))
            self.preprocess_done = True

        return text

    def gen_flags(self, text=None, commit=False):
        """
        Return a ParseBag object containing w_flags, w_flag_lines,
        e_flags, and eFlagLine, and maybe desc_is_flawed. Each element
        in w_flag_lines or e_flag_lines is a tuple, the first element being
        the warning or error flag, and the second element being the line
        that raised the flag.  If parameter `commit=True` is passed (off
        by default), it will commit them to the PLSSDesc object's
        attributes--which is probably already done by the .parse()
        method.
        """

        if text is None:
            text = self.orig_desc

        flag_pb = ParseBag(parent_type='PLSSDesc')

        lines = text.split('\n')

        ################################################################
        # Error flags
        ################################################################

        # Preprocess the text, but only to make sure at least one T&R exists
        ppText = self.preprocess(text=text, commit=False)
        if len(find_twprge(ppText)) == 0:
            flag_pb.e_flags.append('noTR')
            flag_pb.e_flag_lines.append(
                ('noTR', 'No T&R\'s identified!'))
            flag_pb.desc_is_flawed = True

        # For everything else, we check against the orig_desc
        if len(find_sec(text)) == 0 and len(find_multisec(text)) == 0:
            flag_pb.e_flags.append('noSection')
            flag_pb.e_flag_lines.append(
                ('noSection', 'No Sections identified!'))
            flag_pb.desc_is_flawed = True

        ################################################################
        # Warning flags
        ################################################################

        # A few warning flag regexes, and the appropriate flag to
        # generate if one or more matches are found.
        wflag_regexes = [
            (isfa_regex, "isfa"),
            (less_except_regex, "except"),
            (including_regex, "including")
        ]

        def check_for_wflag(line, rgx, flag):
            if len(rgx.findall(line)) == 0:
                return
            if flag not in flag_pb.w_flags:
                flag_pb.w_flags.append(flag)
            flag_pb.w_flag_lines.append((flag, line))

        for line in lines:
            for rgx, flag in wflag_regexes:
                check_for_wflag(line, rgx, flag)

        if commit:
            self._unpack_pb(flag_pb)

        return flag_pb

    def tracts_to_dict(self, *attributes) -> list:
        """
        Compile the data for each Tract object in .parsed_tracts into a
        dict containing the requested attributes only, and return a list
        of those dicts (the returned list being equal in length to
        .parsed_tracts).

        :param attributes: The names (strings) of whichever attributes
        should be included (see documentation on `pyTRS.Tract` objects
        for the names of relevant attributes).

        :Example:

        txt = '''154N-97W
        Sec 14: NE/4
        Sec 15: Northwest Quarter, North Half South West Quarter'''
        d_obj = pyTRS.PLSSDesc(txt, init_parse_qq=True)
        d_obj.tracts_to_dict('trs', 'desc', 'qqs')

        Example returns a list of two dicts:

            [
            {'trs': '154n97w14',
            'desc': 'NE/4',
            'qqs': ['NENE', 'NWNE', 'SENE', 'SWNE']},

            {'trs': '154n97w15',
            'desc': 'Northwest Quarter, North Half South West Quarter',
            'qqs': ['NENW', 'NWNW', 'SENW', 'SWNW', 'NESW', 'NWSW']}
            ]
        """

        # This functionality is handled by TractList method.
        return self.parsed_tracts.tracts_to_dict(attributes)

    def tracts_to_list(self, *attributes) -> list:
        """
        Compile the data for each Tract object in .parsed_tracts into a
        list containing the requested attributes only, and return a
        nested list of those lists (the returned list being equal in
        length to .parsed_tracts).

        :param attributes: The names (strings) of whichever attributes
        should be included (see documentation on `pyTRS.Tract` objects
        for the names of relevant attributes).

        :Example:

        txt = '''154N-97W
        Sec 14: NE/4
        Sec 15: Northwest Quarter, North Half South West Quarter'''
        d_obj = pyTRS.PLSSDesc(txt, init_parse_qq=True)
        d_obj.tracts_to_list('trs', 'desc', 'qqs')

        Example returns a nested list:
            [
                ['154n97w14',
                'NE/4',
                ['NENE', 'NWNE', 'SENE', 'SWNE']],

                ['154n97w15',
                'Northwest Quarter, North Half South West Quarter',
                ['NENW', 'NWNW', 'SENW', 'SWNW', 'NESW', 'NWSW']]
            ]
        """

        # This functionality is handled by TractList method.
        return self.parsed_tracts.tracts_to_list(attributes)

    def tracts_to_str(self, *attributes) -> str:
        """
        Compile the data for all Tract objects in .parsed_tracts,
        containing the requested attributes only, and return a single
        string of the data.

        :param attributes: The names (strings) of whichever attributes
        should be included (see documentation on `pyTRS.Tract` objects
        for the names of relevant attributes).

        :Example:

        txt = '''154N-97W
        Sec 14: NE/4
        Sec 15: Northwest Quarter, North Half South West Quarter'''
        d_obj = pyTRS.PLSSDesc(txt, init_parse_qq=True)
        d_obj.tracts_to_str('trs', 'desc', 'qqs')

        Example returns a multi-line string that looks like this when
        printed:

            Tract #1
            trs    : 154n97w14
            desc   : NE/4
            qqs : NENE, NWNE, SENE, SWNE

            Tract #2
            trs    : 154n97w15
            desc   : Northwest Quarter, North Half South West Quarter
            qqs : NENW, NWNW, SENW, SWNW, NESW, NWSW
        """

        # This functionality is handled by TractList method.
        return self.parsed_tracts.tracts_to_str(attributes)

    def quick_desc(self, delim=': ', newline='\n') -> str:
        """
        Returns the entire .parsed_tracts list as a single string.
        :param delim: Specify what separates TRS from the desc.
        (defaults to ': ').
        :param newline: Specify what separates Tracts from one another.
        (defaults to '\n').

        :Example:

        txt = '''154N-97W
        Sec 14: NE/4
        Sec 15: Northwest Quarter, North Half South West Quarter'''
        d_obj = pyTRS.PLSSDesc(txt, init_parse_qq=True)
        d_obj.quick_desc()

        Example returns a multi-line string that looks like this when
        printed:

            154n97w14: NE/4
            154n97w15: Northwest Quarter, North Half South West Quarter
        """

        # This functionality is handled by TractList method.
        return self.parsed_tracts.quick_desc(delim=delim, newline=newline)

    def quick_desc_short(self, delim=': ', newline='\n', max_len=30) -> str:
        """
        Returns the description (`.trs` + `.desc`) of all Tract objects
        in `.parsed_tracts` as a single string, but trims every line down
        to `max_len`, if needed.
        :param delim: Specify what separates TRS from the desc.
        (defaults to ': ').
        :param newline: Specify what separates Tracts from one another.
        (defaults to '\n').
        :param max_len: Maximum length of each string inside the list.
        (Defaults to 30.)
        :return: A string of the complete description.
        """
        return self.parsed_tracts.quick_desc_short(delim, newline, max_len)

    # def extractTractData():  # method removed in v0.4.11, 8/25/2020
    # (replaced with more specific .tracts_to_dict() and .tracts_to_list())

    # def strDesc():  # method removed in v0.4.11, 8/25/2020
    # (replaced with .tracts_to_str())

    def list_trs(self, remove_duplicates=False):
        """
        Return a list all the TRS's in .parsed_tracts list. Optionally
        remove duplicates with remove_duplicates=True.
        """

        # This functionality is handled by TractList method.
        return self.parsed_tracts.list_trs(remove_duplicates=remove_duplicates)

    def print_desc(self, delim=': ', newline='\n') -> None:
        """
        Simple printing of the parsed description.

        :param delim: Specify what separates TRS from the desc.
        (defaults to ': ').
        :param newline: Specify what separates Tracts from one another.
        (defaults to '\n').
        """

        # This functionality is handled by TractList method.
        self.parsed_tracts.print_desc(delim=delim, newline=newline)

    # def genFlagList():  # method removed in v0.2.1, 5/31/2020

    def print_data(self, *attributes) -> None:
        """
        Simple printing of the arg-specified attributes for each Tract
        in the .parsed_tracts list.
        """
        print(self.tracts_to_str(attributes))
        return


class Tract:
    """
    Each object of this class is a discrete tract of land, limited to
    one Twp/Rge/Sec combination (often shorted to 'TRS' in this module)
    and the description of the land within that TRS, which optionally
    can be parsed into aliquot quarter-quarters (called QQ's) and lots.

    Configure the parsing algorithm with config parameters at init,
    passed in `config=` (taking either a pyTRS.Config object or a string
    containing equivalent config parameters -- see documentation on
    Config objects for possible parameters).

    ____ PARSING ____
    Parse the text into lots/QQs with the `.parse()` method at some
    point after init. Alternatively, trigger the parse at init in one of
    two ways:
    -- Use init parameter `init_parse_qq=True`
    -- Include 'init_parse_qq' in the config parameters that are passed in
        `config=` at init.

    ____ IMPORTANT INSTANCE VARIABLES AFTER PARSING ____
    .trs -- The Twp/Rge/Sec combo. Formatted such that Twp and Rge are
        1 to 3 digits + direction, and section is 2 digits, and
        North/South and East/West are represented with the lowercase
        first letter.
            Ex: Sec 1, T154N-R97W -> '154n97w01'
                Sec 14, T1S-R9E -> '1s9e14'
    NOTE: If there was a flawed parse where Twp/Rge and/or Sec could not
        be successfully identified, .trs may contain 'TRerr_' and/or
        'secError'.
    .twp -- The Twp portion of .trs, a string (ex: '154n')
    .rge -- The Rge portion of .trs, a string (ex: '97w')
    .twprge -- The Twp/Rge portion of .trs, a string (ex: '154n97w')
    .sec -- The Sec portion of .trs, a string (ex: '01')
    .desc -- The description block within this TRS.
    .qqs -- A list of identified QQ's (or smaller) formatted as 4
    characters (or more, if there are further divisions).
        Ex:     Northeast Quarter -> ['NENE', 'NWNE', 'NENW', 'NWNW']
        Ex:     N/2SE/4SE/4 -> ['N2SESE']
    .lots -- A list of identified lots.
        Ex:     Lot 1, North Half of Lot 2 -> ['L1', 'N2 of L2']
        NOTE: Divisions of lots can be suppressed with config parameter
            'include_lot_divs.False' (i.e. ['L1', 'L2'] in this example).
    .lots_qqs -- A joined list of identified lots and QQ's.
        Ex:     ['L1', 'N2 of L2', 'NENE', 'NWNE', 'NENW', 'NWNW']
    .lot_acres -- A dict of lot names and their apparent gross acreages,
    as stated in the original description.
        Ex:     Lots 1(38.29), 2(39.22), 3(39.78)
                    -> {'L1': '38.29', 'L2':'39.22', 'L3':'39.78'}
    .pp_desc -- The preprocessed description. (If the object has not yet
        been preprocessed, it will be equivalent to .desc)
    .source -- (Optional) A string specifying where the description came
        from. Useful if parsing multiple descriptions and need to
        internally keep track where they came from. (Optionally specify
        at init with parameter `source=<str>`.)
    .orig_desc -- The full, original text of the parent PLSSDesc object,
        if any.
    .orig_index -- An integer represeting the order in which this Tract
        object was created while parsing the parent PLSSDesc object, if
        any.
    .w_flags -- a list of warning flags (strings) generated during
        preprocessing and/or parsing.
    .w_flag_lines -- a list of 2-tuples, each being a warning flag and the
        line or context from the description that caused the warning.
    .e_flags -- a list of error flags (strings) generated during
        preprocessing and/or parsing.
    .e_flag_lines -- a list of 2-tuples, each being an error flag and the
        line or context from the description that caused the error.
    .desc_is_flawed -- a bool, whether or not an apparently fatal flaw was
        discovered during parsing of the parent PLSSDesc object, if any.
        (Tract objects themselves are agnostic to fatal flaws.)

    ____ STREAMLINED OUTPUT OF THE PARSED DATA ____
    The instance variables above can be compiled with these methods:
    .quick_desc() -- Returns a string of the TRS + description.
    .to_dict() -- Compile the requested attributes into a dict.
    .to_list() -- Compile the requested attributes into a list.
    """

    def __init__(
            self, desc='', trs='', source='', orig_desc='', orig_index=0,
            desc_is_flawed=False, config=None, init_parse_qq=None):
        """
        :param desc: The description block within this TRS. (What will
        be processed if this Tract object gets parsed into lots/QQs.)
        :param trs: Specify the TRS of the Tract. Formatted such that
        Twp and Rge are 1 to 3 digits + direction, and section is 2
        digits, and North/South and East/West are represented with the
        lowercase first letter.
            Ex: Sec 1, T154N-R97W -> '154n97w01'
                Sec 14, T1S-R9E -> '1s9e14'
        :param source: (Optional) A string specifying where the
        description came from. Useful if parsing multiple descriptions
        and need to internally keep track where they came from.
        :param orig_desc: The full, original text of the parent PLSSDesc
        object, if any.
        :param orig_index: An integer represeting the order in which this
        Tract object was created while parsing the parent PLSSDesc
        object, if any
        :param desc_is_flawed: a bool, whether or not an apparently fatal
        flaw was discovered during parsing of the parent PLSSDesc
        object, if any. (Tract objects themselves are agnostic to fatal
        flaws.)
        :param config: Either a pyTRS.Config object, or a string of
        parameters to configure how the Tract object should be parsed.
        (See documentation on pyTRS.Config objects for optional config
        parameters.)
        :param init_parse_qq: Whether to parse the `desc` into lots/QQs at
        init. (Defaults to False)
        """

        if not isinstance(trs, str) and trs is not None:
            raise TypeError("`trs` must be a string or None")

        # a string containing the TRS (Township Range and Section),
        # stored in the format 000n000w00 (or fewer digits for Twp/Rge).
        self.trs = trs

        # a string containing the description block.
        self.desc = desc

        # The order in which this TRS/Desc was identified when parsing
        # the original PLSSDesc object (if applicable)
        self.orig_index = orig_index

        # The source of this Tract.
        self.source = source

        # Original description of the full PLSS description from which
        # this Tract comes
        self.orig_desc = orig_desc

        # Whether we have parsed this Tract and committed the results
        self.parse_complete = False

        # If the TRS has been specified (i.e. is in the '000n000w00'
        # format), _unpack it into the component parts
        self.twp, self.rge, self.sec = break_trs(trs)
        if self.sec is None:
            self.sec = 'secError'
        self.twprge = self.twp + self.rge

        # Whether fatal flaws were identified during the parsing of the
        # parent PLSSDesc object, if any
        self.desc_is_flawed = desc_is_flawed
        # list of warning flags
        self.w_flags = []
        # list of 2-tuples that caused warning flags (warning flag, text string)
        self.w_flag_lines = []
        # list of error flags
        self.e_flags = []
        # list of 2-tuples that caused error flags (error flag, text string)
        self.e_flag_lines = []

        # A list of QQ's (or smaller) with no quarter fractions
        # i.e. ['NENE', 'NENW', 'N2SENW', ... ]:
        self.qqs = []

        # Attributes to control how deeply QQ's should be parsed.
        # If `.qq_depth` is set, it will override `.qq_depth_min` and
        # `.qq_depth_max`
        self.qq_depth = None
        self.qq_depth_min = 2
        self.qq_depth_max = None
        self.break_halves = False

        # A list of standard lots, ['L1', 'L2', 'N2 of L5', ...]:
        self.lots = []

        # A combined list of lots + QQs:
        self.lots_qqs = []

        # A dict of lot acreages, keyed by 'L1', 'L2', etc.
        self.lot_acres = {}

        # A bool to track whether the preprocess has been completed
        self.preprocess_done = False

        # --------------------------------------------------------------
        # Configure how the Tract should be parsed:

        # If a T&R is identified without 'North/South' specified, fall
        # back on this. Will be filled in with set_config() (if
        # applicable) or defaulted to 'n' shortly.
        # NOTE: only applicable for using .from_twprgesec()
        self.default_ns = None

        # If a T&R is identified without 'East/West' specified, fall
        # back on this. Will be filled in with set_config() (if
        # applicable) or defaulted to 'w' shortly.
        # NOTE: only applicable for using .from_twprgesec()
        self.default_ew = None

        # NOTE: `initPreproces`, `init_parse_qq`, `clean_qq`, &
        # `include_lot_divs` will be changed in set_config(), if needed.

        # Whether we should preprocess the text at initialization:
        self.init_preprocess = True

        # Whether we should parse lots and aliquots at init.
        self.init_parse_qq = False

        # Whether the user expects tract descriptions to have `clean_qq` (i.e.
        # nothing but clean aliquots and lots, with no typos, exceptions,
        # metes-and-bounds, or other hindrances to the parser.)
        self.clean_qq = False

        # Whether to include any divisions of lots
        # (i.e. 'N/2 of Lot 1' to 'N2 of L1').
        self.include_lot_divs = True

        # Whether to iron out common OCR artifacts. Defaults to `False`.
        # NOTE: Currently only has effect if Tract object is created via
        # `.from_twprgesec()`   ...  May have more effect in a later version.
        self.ocr_scrub = False

        # Apply settings from kwarg `config=`
        self.set_config(config)

        # If `default_ns` has not yet been specified, default to 'n' :
        if self.default_ns is None:
            self.default_ns = 'n'

        # If `default_ew` has not yet been specified, default to 'w' :
        if self.default_ew is None:
            self.default_ew = 'w'

        # If kwarg-specified init_parse_qq, that will override config input
        if isinstance(init_parse_qq, bool):
            self.init_parse_qq = init_parse_qq

        ################################################################
        # If config settings require calling preprocess() and parse() at
        # initialization, do it now:
        ################################################################

        if self.init_preprocess or self.clean_qq:
            self.preprocess(commit=True)
        else:
            self.pp_desc = self.desc

        if self.init_parse_qq:
            self.parse(commit=True)

    def __str__(self):
        return (
            "Tract ({0})\n"
            "{1}\n"
            "Total QQs: {2}\n"
            "Total Lots: {3}").format(
                "Parsed" if self.parse_complete else "Unparsed",
                self.quick_desc() if self.trs not in ("", None) else self.desc,
                len(self.qqs) if self.parse_complete else "n/a",
                len(self.lots) if self.parse_complete else "n/a")

    @staticmethod
    def from_twprgesec(
            desc='', twp='0', rge='0', sec='0', source='', orig_desc='',
            default_ns=None, default_ew=None, orig_index=0, desc_is_flawed=False,
            config=None, init_parse_qq=None):
        """
        Create a Tract object from separate Twp, Rge, and Sec components
        rather than joined TRS. All parameters are the same as
        __init__(), except that `trs=` is replaced with `twp=`, `rge`,
        and `sec`. (If N/S or E/W are not specified, will pull defaults
        from config parameters.)

        WARNING: This method has fewer guardrails on what gets set to
        `.twp`, `.rge`, `.sec`, and `.trs` in the resulting Tract; so it
        may be wise to preprocess those data before passing as args.

        :param twp: Township. Pass as a string (i.e. '154n'). If passed
        as an integer, the N/S will be pulled from `config` parameters,
        or defaulted to 'n' if not specified.
        :param rge: Range. Pass as a string (i.e. '97w'). If passed as
        an integer, the E/W will be pulled from `config` parameters, or
        defaulted to 'w' if not specified.
        :param sec: Section. Pass as a string or an integer (up to 2
        digits).
        """

        # Compile the `config=` data into a Config object (or use the
        # provided object, if already provided as `Config` type), so we
        # can extract `default_ns` and `default_ew`
        if isinstance(config, str) or config is None:
            config = Config(config)
        if not isinstance(config, Config):
            raise CONFIG_ERROR

        # Get our default_ns and default_ew from kwargs or config
        if default_ns is None:
            default_ns = config.default_ns
        if default_ew is None:
            default_ew = config.default_ew
        # If still not specified (i.e. neither set in kwarg, nor in config),
        # default to 'n' and 'w', respectively.
        if default_ns is None:
            default_ns = 'n'
        if default_ew is None:
            default_ew = 'w'
        # Ensure legal N/S and E/W values.
        if default_ns.lower() not in ['n', 'north', 's', 'south']:
            raise DEFAULT_NS_ERROR
        if default_ew.lower() not in ['w', 'west', 'e', 'east']:
            raise DEFAULT_EW_ERROR

        # Whether to scrub twp, rge, and sec strings for OCR artifacts
        ocr_scrub = False
        if config.ocr_scrub is not None:
            ocr_scrub = config.ocr_scrub

        # Get twp in a standardized format, if we can
        if not isinstance(twp, (int, str)):
            twp = ''
        elif isinstance(twp, int):
            twp = f'{str(twp)}{default_ns}'
        elif isinstance(twp, str):
            if twp[-1].lower() not in ['n', 's']:
                # If the final character is not 'n' or 's', apply our default_ns
                twp = twp + default_ns
            if ocr_scrub:
                # If configured so, OCR-scrub all but the final character
                twp = _ocr_scrub_alpha_to_num(twp[:-1]) + twp[-1]
            twp = twp.lower()

        # Get rge in a standardized format, if we can
        if not isinstance(rge, (int, str)):
            rge = ''
        elif isinstance(rge, int):
            rge = f'{str(rge)}{default_ew}'
        elif isinstance(rge, str):
            if rge[-1].lower() not in ['e', 'w']:
                # If the final character is not 'e' or 'w', apply our default_ew
                rge = rge + default_ew
            if ocr_scrub:
                # If configured so, OCR-scrub all but the final character
                rge = _ocr_scrub_alpha_to_num(rge[:-1]) + rge[-1]
            rge = rge.lower()

        # Get sec in a standardized format, if we can
        if not isinstance(sec, (int, str)):
            raise TypeError("`sec` must be an int or str.")
        sec = str(sec)
        try:
            sec = str(int(sec)).rjust(2, '0')
            if ocr_scrub:
                # If configured so, OCR-scrub all characters
                sec = _ocr_scrub_alpha_to_num(sec)
        except ValueError:
            pass

        # compile a TRS, and see if it matches our known format
        trs = f'{twp}{rge}{sec}'

        # Create a new Tract object and return it
        new_tract = Tract(
            desc=desc, trs=trs, source=source, orig_desc=orig_desc,
            orig_index=orig_index, desc_is_flawed=desc_is_flawed, config=config,
            init_parse_qq=init_parse_qq)
        new_tract.twp = twp
        new_tract.rge = rge
        new_tract.sec = sec
        return new_tract

    def set_config(self, config):
        """
        Apply the relevant settings from a Config object to this object;
        takes either a string (i.e. config text) or a Config object.

        :param config: Either a pyTRS.Config object, or equivalent
        config parameters. (See pyTRS.Config documentation for optional
        parameters.)
        """
        if isinstance(config, str) or config is None:
            config = Config(config)
        if not isinstance(config, Config):
            raise CONFIG_ERROR

        for attrib in Config._TRACT_ATTRIBUTES:
            value = getattr(config, attrib)
            if value is not None:
                setattr(self, attrib, value)

    def _unpack_pb(self, target_pb):
        """
        Unpack (append or set) the relevant attributes of the
        `target_pb` into self's attributes.

        :param target_pb: A ParseBag object containing data from
        the parse.
        """

        if not isinstance(target_pb, ParseBag):
            raise TypeError("Can only `_unpack_pb()` a pyTRS.ParseBag object.")

        if target_pb.desc_is_flawed:
            self.desc_is_flawed = True

        if len(target_pb.w_flags) > 0:
            self.w_flags.extend(target_pb.w_flags)

        if len(target_pb.e_flags) > 0:
            self.e_flags.extend(target_pb.e_flags)

        if len(target_pb.w_flag_lines) > 0:
            self.w_flag_lines.extend(target_pb.w_flag_lines)

        if len(target_pb.e_flag_lines) > 0:
            self.e_flag_lines.extend(target_pb.e_flag_lines)

        if target_pb.parent_type == 'Tract':
            # Only if unpacking a Tract-level ParseBag... Otherwise,
            # these attributes won't exist for that ParseBagObj.

            if len(target_pb.qqs) > 0:
                # Only append fresh (non-duplicate) QQ's, and raise a
                # flag if there are any duplicates
                dupQQs = []
                freshQQs = []
                for qq in target_pb.qqs:
                    if qq in self.qqs or qq in freshQQs:
                        dupQQs.append(qq)
                    else:
                        freshQQs.append(qq)
                self.qqs.extend(freshQQs)
                if len(dupQQs) > 0:
                    self.w_flags.append('dup_QQ')
                    self.w_flag_lines.append(
                        ('dup_QQ', f'<{self.trs}: {", ".join(dupQQs)}>'))

            if len(target_pb.lots) > 0:
                # Only append fresh (non-duplicate) Lots, and raise a
                # flag if there are any duplicates
                dupLots = []
                freshLots = []
                for lot in target_pb.lots:
                    if lot in self.lots or lot in freshLots:
                        dupLots.append(lot)
                    else:
                        freshLots.append(lot)
                self.lots.extend(freshLots)
                if len(dupLots) > 0:
                    self.w_flags.append('dup_lot')
                    self.w_flag_lines.append(
                        ('dup_lot', f'<{self.trs}: {", ".join(dupLots)}>'))

            self.lots_qqs = self.lots + self.qqs

            if len(target_pb.lot_acres) > 0:
                self.lot_acres = target_pb.lot_acres
                # TODO: Handle discrepancies, if there's already data in
                #   lot_acres.

    def parse(
            self, text=None, commit=True, clean_qq=None, include_lot_divs=None,
            preprocess=None, qq_depth_min=None, qq_depth_max=None,
            qq_depth=None, break_halves=None):
        """
        Parse the description block of this Tract into lots and QQ's.

        :param text: The text to be parsed into lots and QQ's. If not
        specified, will pull from `self.pp_desc` (i.e. the preprocessed
        description).
        :param commit: Whether to commit the results to the appropriate
        instance attributes. Defaults to `True`.
        :param clean_qq: Whether to expect only clean lots and QQ's (i.e.
        no metes-and-bounds, exceptions, complicated descriptions,
        etc.). Defaults to whatever is specified in `self.clean_qq`
        (which is False, unless configured otherwise).
        :param include_lot_divs: Whether to report divisions of lots.
        Defaults to whatever is specified in `self.include_lot_divs`
        (which is True, unless configured otherwise).
            ex:  North Half of Lot 1
                    `True` -> 'N2 of L1'
                    `False` -> 'L1'
        :param preprocess: Whether to preprocess the text before parsing
        it (if the preprocess has not already been done).
        :param qq_depth_min: An int, specifying the minimum depth of the
        parse. If not set here, will default to settings from init (if
        any), which in turn default to 2, i.e. to quarter-quarters
        (e.g., 'N/2NE/4' -> ['NENE', 'NENE']). Setting to 3 would return
        10-acre subdivisions (i.e. dividing the 'NENE' into ['NENENE',
        'NWNENE', 'SENENE', 'SWNENE']), and so forth.
        WARNING: Higher than a few levels of depth will result in very
        slow performance.
        :param qq_depth_max: (Optional) An int, specifying the maximum
        depth of the parse. If set as 2, any subdivision smaller than
        quarter-quarter (e.g., 'NENE') would be discarded -- so, for
        example, the 'N/2NE/4NE/4' would simply become the 'NENE'. Must
        be greater than or equal to `qq_depth_min`. (Defaults to None --
        i.e. no maximum. Can also be configured at init.)
        :param qq_depth: (Optional) An int, specifying both the min and
        max depth of the parse. If specified, will override both
        `qq_depth_min` and `qq_depth_max`. (Defaults to None -- i.e. use
        qq_depth_min and optionally qq_depth_max; but can also be
        configured at init.)
        :param break_halves: Whether to break halves into quarters,
        even if we're beyond the qq_depth_min. (False by default, but can
        be configured at init.)
        :return: Returns the a single list of identified lots and QQ's
        (equivalent to what would be stored in `.lots_qqs`).
        """

        # TODO: Generate a list (saved as an attribute) of slice_indexes
        #   of the `pp_desc` for the text that was incorporated into
        #   lots and QQ's vs. not.

        if text is None:
            text = self.pp_desc

        if clean_qq is None:
            clean_qq = self.clean_qq

        if include_lot_divs is None:
            include_lot_divs = self.include_lot_divs

        # If preprocess has not already been complete, and param did not
        # dictate `preprocess=False`, then we will want to run
        # preprocess(). Alternatively, if our kwarg-specified clean_qq
        # does not match self.clean_qq, we want the kwarg-specified to
        # control, so we'll run preprocess() again, with the
        # kwarg-specified `clean_qq` value:
        do_prepro = False
        if not self.preprocess_done and preprocess in [None, True]:
            do_prepro = True
        if self.clean_qq != clean_qq:
            do_prepro = True

        if do_prepro:
            text = self.preprocess(clean_qq=clean_qq, commit=False)

        # TODO : DON'T pull the QQ in "less and except the Johnston #1
        #   well in the NE/4NE/4 of Section 4, T154N-R97W" (for example)

        # TODO : DON'T pull the QQ in "To the east line of the NW/4NW/4"
        #   (for example). May need some additional context limitations.
        #   (exclude "of the said <match>"; "<match> of [the] Section..." etc.)

        ################################################################
        # General process is as follows:
        # 1) Scrub the aliquots (i.e. Convert 'Northeast Quarter of
        #       Southwest Quarter, E/2, NE4' to 'NE¼SW¼, E½, NE¼')
        # 2) Extract lot_regex matches from the text (actually uses
        #       lot_with_aliquot_regex to capture lot divisions).
        # 3) Unpack lot_regex matches into a lots.
        # 4) Extract aliquot_regex matches from the text.
        # 5) Convert the aliquot_regex matches into a qqs.
        # 6) Pack it all into a ParseBag.
        # 6a) If committing the results, self._unpack_pb() the ParseBag.
        # 7) Join the lots and qqs from the ParseBag, and return it.
        ################################################################

        # For holding the data during parsing
        plqqParseBag = ParseBag(parent_type='Tract')

        # Swap out NE/NW/SE/SW and N2/S2/E2/W2 matches for cleaner versions
        text = _scrub_aliquots(text, clean_qq=clean_qq)

        # Extract the lots from the description (and leave the rest of
        # the description for aliquot parsing).  Replace any extracted
        # lots with ';;' to prevent unintentionally combining aliquots later.
        lotTextBlocks = []
        remainingText = text
        while True:
            # We use `lot_with_aliquot_regex` instead of `lot_regex`,
            # in order to ALSO capture leading aliquots -- i.e. we want
            # to capture 'N½ of Lot 1' (even if we won't be reporting
            # lot divisions), because otherwise the 'N½' will be read as
            # <the entire N/2> of the section.
            lot_aliq_mo = lot_with_aliquot_regex.search(remainingText)
            if lot_aliq_mo is None:
                break
            else:
                lotTextBlocks.append(lot_aliq_mo.group())
                # reconstruct remainingText, injecting ';;' where the
                # match was located
                p1 = remainingText[:lot_aliq_mo.start()]
                p2 = remainingText[lot_aliq_mo.end():]
                remainingText = f"{p1};;{p2}"
        text = remainingText

        lots = []
        lotsAcresDict = {}

        for lotTextBlock in lotTextBlocks:
            # Unpack the lots in this lot_text_block (and get a ParseBag back)
            lotspb = _unpack_lots(lotTextBlock, include_lot_divs=include_lot_divs)

            # Append these identified lots:
            lots.extend(lotspb.lots)

            # Add any identified lot_acres to the dict:
            for lot in lotspb.lot_acres:
                lotsAcresDict[lot] = lotspb.lot_acres[lot]

            # And absorb any flags/flagLines:
            plqqParseBag.absorb(lotspb)

        # Get a list of all of the aliquots strings
        aliqTextBlocks = []
        remainingText = text
        while True:
            # Run this loop, pulling the next aliquot match until we run out.
            aliq_mo = aliquot_unpacker_regex.search(remainingText)
            if aliq_mo is None:
                break
            else:
                # TODO: Implement context awareness. Should not pull aliquots
                #   before "of Section ##", for example.
                aliqTextBlocks.append(aliq_mo.group())
                remainingText = remainingText[:aliq_mo.start()] + ';;' \
                                + remainingText[aliq_mo.end():]
        text = remainingText

        # And also pull out "ALL" as an aliquot if it is clear of any
        # context (e.g., pull "ALL" but not "All of the").  First, get a
        # working text string, and replace each group of whitespace with
        # a single space.
        wText = re.sub(r'\s+', ' ', text).strip()
        all_mo = ALL_regex.search(wText)
        if all_mo is not None:
            if all_mo.group(2) is None:
                # If we ONLY found "ALL", then we're good.
                aliqTextBlocks.append('ALL')
            # TODO: Make this more robust. As of now will only capture
            #  'ALL' in "Section 14: ALL", but there might be some
            #  disregardable context around "ALL" (e.g., punctuation)
            #  that could currently prevent it from being picked up.

        # --------------------------------------------------------------
        # Now that we have list of text blocks, each containing a separate
        # aliquot, parse each of them into QQ's (or smaller, if further
        # divided).
        #   ex:  ['NE¼', 'E½NE¼NW¼']
        #           -> ['NENE' , 'NWNE' , 'SENE' , 'SWNE', 'E2NENW']

        # Determine whether to use the _min and _max, or to use the
        # qq_depth -- and whether to use the arg-specified or what was
        # set in the instance attributes.
        # If qq_depth is specified as an arg, that gets top priority.
        # If qq_depth_min or qq_depth_max are specified as an arg, we
        # will NOT use the instance attribute `self.qq_depth`.
        # If none of them were set as arguments, we will use
        # `self.qq_depth` (as long as it is not None) or else fall back
        # to `self.qq_depth_min` and `self.qq_depth_max`.
        use_min_max = False
        if qq_depth_min is None:
            qq_depth_min = self.qq_depth_min
        else:
            use_min_max = True
        if qq_depth_max is None:
            qq_depth_max = self.qq_depth_max
        else:
            use_min_max = True
        if qq_depth is not None:
            qq_depth_min = qq_depth_max = qq_depth
        elif not use_min_max and self.qq_depth is not None:
            qq_depth_min = qq_depth_max = self.qq_depth

        if break_halves is None:
            break_halves = self.break_halves
        QQList = []
        for aliqTextBlock in aliqTextBlocks:
            wQQList = _unpack_aliquots(
                aliqTextBlock, qq_depth_min, qq_depth_max, qq_depth,
                break_halves)
            QQList.extend(wQQList)

        plqqParseBag.qqs = QQList
        plqqParseBag.lots = lots
        plqqParseBag.lot_acres = lotsAcresDict

        ret_lots_qqs = plqqParseBag.lots + plqqParseBag.qqs

        # Store the results, if instructed to do so.
        if commit:
            self.parse_complete = True
            self._unpack_pb(plqqParseBag)

        return ret_lots_qqs

    def preprocess(self, text=None, commit=True, clean_qq=None) -> str:
        """
        Preprocess the description text to iron out common kinks in the
        input data, and optionally store results to `self.pp_desc`.

        :param text: The text to be preprocessed. Defaults to what is
        stored in `self.desc` (i.e. the original description block).
        :param commit: Whether to store the resluts to `self.pp_desc`.
        (Defaults to `True`)
        :param clean_qq: Whether to expect only clean lots and QQ's (i.e.
        no metes-and-bounds, exceptions, complicated descriptions,
        etc.). Defaults to whatever is specified in `self.clean_qq`
        (which is False, unless configured otherwise).
        :return: The preprocessed string.
        """

        if text is None:
            text = self.desc

        if clean_qq is None:
            clean_qq = self.clean_qq

        text = _scrub_aliquots(text, clean_qq=clean_qq)

        if commit:
            self.pp_desc = text
            self.preprocess_done = True

        return text

    def to_dict(self, *attributes) -> dict:
        """
        Compile the requested attributes into a dict.

        :param attributes: The attribute names (instance variables) to
        include.
        :return: A dict, keyed by attribute.
        """

        # Unpack any lists or tuples included among attributes, and
        # ensure elements are all strings:
        attributes = _clean_attributes(attributes)

        return {att: getattr(self, att, f"{att}: n/a") for att in attributes}

    def to_list(self, *attributes) -> list:
        """
        Compile the requested attributes into a list.

        :param attributes: The attribute names (instance variables) to
        include.
        :return: A list of attribute values.
        """

        attributes = _clean_attributes(attributes)
        return [getattr(self, att, f"{att}: n/a") for att in attributes]

    def quick_desc(self, delim=': ') -> str:
        """
        Return a string of the TRS + description.

        :param delim: The string that should separate TRS from the
        description. (Defaults to ': ')
        :return: A string of the TRS + description.
        """
        return f"{self.trs}{delim}{self.desc}"

    def quick_desc_short(self, delim=': ', max_len=30) -> str:
        """
        Get the `.quick_desc()` of this Tract, but if the resulting str
        is longer than `max_len`, shorten it to that length.

        :param delim: The string that should separate TRS from the
        description. (Defaults to ': ')
        :param max_len: Maximum length of the returned string. (Defaults
        to 30.)
        :return: A string, no longer than `max_len`.
        """
        qd = self.quick_desc(delim)
        if len(qd) > max_len:
            qd = qd[:max_len - 3] + "..."
        return qd

    # def extractData():  # method removed in v0.4.11, 8/25/2020
    # (replaced with more specific .to_dict() and .to_list())

    # def outputTRSdesc():  # method removed in v0.4.11, 8/25/2020
    # (replaced with .quick_desc())

    # Aliases to prevent breaking API on calls to method names with caps
    # TODO: Deprecate these method names
    from_TwpRgeSec = from_twprgesec


class TractList(list):
    """
    A standard `list` that contains Tract objects, with added methods
    for compiling and manipulating the data in the contained Tract objs.

    ____ STREAMLINED OUTPUT OF THE PARSED DATA ____
    These methods have the same effect as in PLSSDesc objects.
    .quick_desc() -- Returns a string of the entire parsed description.
    .tracts_to_dict() -- Compile the requested attributes for each Tract
        into a dict, and returns a list of those dicts.
    .tracts_to_list() -- Compile the requested attributes for each Tract
        into a list, and returns a nested list of those list.
    .tracts_to_str() -- Compile the requested attributes for each Tract
        into a string-based table, and return a single string of all
        tables.
    .list_trs() -- Return a list of all twp/rge/sec combinations,
        optionally removing duplicates.
    """

    def __init__(self, *args, **kwargs):
        list.__init__(self, *args, **kwargs)

    def __str__(self):
        return (
            "TractList\nTotal Tracts: {0}\n"
            "Tracts: {1}").format(
                len(self), self.snapshot_inside())

    def check_illegal(self):
        """
        Ensure every element is a Tract object, or raise TypeError.
        """
        if not all(isinstance(t, Tract) for t in self):
            raise TypeError(
                'Only pyTRS.Tract objects should be appended to TractList')

    def tracts_to_dict(self, *attributes) -> list:
        """
        Compile the data for each Tract object into a dict containing
        the requested attributes only, and return a list of those dicts
        (the returned list being equal in length to this TractList
        object).

        :param attributes: The names (strings) of whichever attributes
        should be included (see documentation on `pyTRS.Tract` objects
        for the names of relevant attributes).

        :Example:

        txt = '''154N-97W
        Sec 14: NE/4
        Sec 15: Northwest Quarter, North Half South West Quarter'''
        d_obj = PLSSDesc(txt)
        tl_obj = d_obj.parse(init_parse_qq=True, commit=False)
        tl_obj.tracts_to_dict('trs', 'desc', 'qqs')

        Example returns a list of two dicts:

            [
            {'trs': '154n97w14',
            'desc': 'NE/4',
            'qqs': ['NENE', 'NWNE', 'SENE', 'SWNE']},

            {'trs': '154n97w15',
            'desc': 'Northwest Quarter, North Half South West Quarter',
            'qqs': ['NENW', 'NWNW', 'SENW', 'SWNW', 'NESW', 'NWSW']}
            ]
        """

        # Ensure all elements are legal.
        self.check_illegal()

        attributes = _clean_attributes(attributes)

        return [t.to_dict(attributes) for t in self]

    def tracts_to_list(self, *attributes) -> list:
        """
        Compile the data for each Tract object into a list containing
        the requested attributes only, and return a nested list of those
        lists (the returned list being equal in length to this TractList
        object).

        :param attributes: The names (strings) of whichever attributes
        should be included (see documentation on `pyTRS.Tract` objects
        for the names of relevant attributes).

        :Example:

        txt = '''154N-97W
        Sec 14: NE/4
        Sec 15: Northwest Quarter, North Half South West Quarter'''
        d_obj = PLSSDesc(txt)
        tl_obj = d_obj.parse(init_parse_qq=True, commit=False)
        tl_obj.tracts_to_list('trs', 'desc', 'qqs')

        Example returns a nested list:
            [
                ['154n97w14',
                'NE/4',
                ['NENE', 'NWNE', 'SENE', 'SWNE']],

                ['154n97w15',
                'Northwest Quarter, North Half South West Quarter',
                ['NENW', 'NWNW', 'SENW', 'SWNW', 'NESW', 'NWSW']]
            ]
        """

        # Ensure all elements are legal.
        self.check_illegal()

        attributes = _clean_attributes(attributes)

        return [t.to_list(attributes) for t in self]

    def tracts_to_str(self, *attributes) -> str:
        """
        Compile the data for all Tract objects, containing the requested
        attributes only, and return a single string of the data.

        :param attributes: The names (strings) of whichever attributes
        should be included (see documentation on `pyTRS.Tract` objects
        for the names of relevant attributes).

        :Example:

        txt = '''154N-97W
        Sec 14: NE/4
        Sec 15: Northwest Quarter, North Half South West Quarter'''
        d_obj = PLSSDesc(txt)
        tl_obj = d_obj.parse(init_parse_qq=True, commit=False)
        tl_obj.tracts_to_str('trs', 'desc', 'qqs')

        Example returns a multi-line string that looks like this when
        printed:

            Tract #1
            trs    : 154n97w14
            desc   : NE/4
            qqs : NENE, NWNE, SENE, SWNE

            Tract #2
            trs    : 154n97w15
            desc   : Northwest Quarter, North Half South West Quarter
            qqs : NENW, NWNW, SENW, SWNW, NESW, NWSW
        """

        # Ensure all elements are legal.
        self.check_illegal()

        attributes = _clean_attributes(attributes)

        # How far to justify the attribute names in the output str:
        longest = max([len(att) for att in attributes])

        all_tract_data = ""
        for i, t_dct in enumerate(self.tracts_to_dict(attributes), start=1):
            tract_data = f"\n\nTract #{i}"
            if i == 1:
                tract_data = f"Tract #{i}"
            for att_name, v in t_dct.items():
                # Flatten lists/tuples, but leave everything else as-is
                if isinstance(v, (list, tuple)):
                    v = ", ".join(flatten(v))
                # Justify attribute name and report its value
                tract_data = tract_data + f"\n{att_name.ljust(longest, ' ')} : {v}"

            all_tract_data = all_tract_data + tract_data

        return all_tract_data

    def quick_desc(self, delim=': ', newline='\n') -> str:
        """
        Returns the description of all Tract objects (`.trs` + `.desc`)
        as a single string.
        :param delim: Specify what separates TRS from the desc.
        (defaults to ': ').
        :param newline: Specify what separates Tracts from one another.
        (defaults to '\n').

        :Example:

        txt = '''154N-97W
        Sec 14: NE/4
        Sec 15: Northwest Quarter, North Half South West Quarter'''
        d_obj = PLSSDesc(txt)
        tl_obj = d_obj.parse(init_parse_qq=True, commit=False)
        tl_obj.quick_desc()

        Example returns a multi-line string that looks like this when
        printed:

            154n97w14: NE/4
            154n97w15: Northwest Quarter, North Half South West Quarter
        """

        # Ensure all elements are legal.
        self.check_illegal()

        dlist = [
            t.quick_desc(delim=delim) for t in self
        ]

        return newline.join(dlist)

    def quick_desc_short(self, delim=': ', newline='\n', max_len=30) -> str:
        """
        Returns the description of all Tract objects (`.trs` + `.desc`)
        as a single string, but trims every line down to `max_len`, if
        needed.
        :param delim: Specify what separates TRS from the desc.
        (defaults to ': ').
        :param newline: Specify what separates Tracts from one another.
        (defaults to '\n').
        :param max_len: Maximum length of each string inside the list.
        (Defaults to 30.)
        :return: A string of the complete description.
        """
        return newline.join(self.snapshot_inside(delim, max_len))

    def snapshot_inside(self, delim=': ', max_len=30) -> list:
        """
        Get a list of the descriptions ('.trs' + '.desc') of the Tract
        objects, shortened to `max_len` as necessary.
        :param delim: Specify what separates TRS from the desc.
        (defaults to ': ').
        :param max_len: Maximum length of each string inside the list.
        (Defaults to 30.)
        :return: A list of strings, each no longer than `max_len`.
        """
        return [t.quick_desc_short(delim, max_len) for t in self]

    def print_desc(self, delim=': ', newline='\n') -> None:
        """
        Simple printing of the parsed description.

        :param delim: Specify what separates TRS from the desc.
        (defaults to ': ').
        :param newline: Specify what separates Tracts from one another.
        (defaults to '\n').
        """

        print(self.quick_desc(delim=delim, newline=newline))

    def list_trs(self, remove_duplicates=False):
        """
        Return a list all the TRS's in this TractList. Optionally remove
        duplicates with remove_duplicates=True.
        """
        unique_trs = []
        all_trs = []
        for trs in [t.trs for t in self]:
            all_trs.append(trs)
            if trs not in unique_trs:
                unique_trs.append(trs)
        if remove_duplicates:
            return unique_trs
        return all_trs


class ParseBag:
    """
    INTERNAL USE:

    An object for temporarily holding data during various steps of
    the parsing process.
    """

    # This class only exists to serve as "luggage" between various
    # functions / methods that are called during parsing. Output data of
    # varying kinds are temporarily packed into a ParseBag. When it gets
    # back to the PLSSDesc and/or Tract object, that object will
    # ._unpack_pb() the contents of the ParseBag into its own attributes
    # -- i.e. `plssdesc_object._unpack_pb(parsebag_object)`.

    # It was designed this way because different functions process
    # different components of the PLSS description, but almost all of
    # them can generate warning flags and error flags for the user's
    # attention. For UX reasons, we want those warning/error data stored
    # in a single location (i.e. a in the `.w_flags` or `.e_flags`).
    # Tract objects also contain `.w_flags` and `.e_flags`

    # So these ParseBag objects will hold those warning/error data (and
    # the TractList, etc.) in one place until the intended endpoint is
    # reached, where it is unpacked.

    # A ParseBag object can also absorb a child ParseBag object by
    # appending (but not overwriting) its own data:
    #       `parent_pb.absorb(child_pb)`
    # This is done, for example, where `child_pb` stores Tract-level
    # parsing data (e.g., qqs, lots) -- but where warning flags
    # can also be generated that would be relevant to the higher-level
    # class PLSSDesc.

    def __init__(self, parent_type='PLSSDesc'):

        # parent_type will establish additional attributes, as necessary,
        # depending on the function or method that created the ParseBag
        self.parent_type = parent_type

        # for all types of objects:
        self.w_flags = []
        self.w_flag_lines = []
        self.e_flags = []
        self.e_flag_lines = []
        self.desc_is_flawed = False

        if parent_type == 'PLSSDesc':
            self.parsed_tracts = TractList()

        elif parent_type == 'Tract':
            self.qqs = []
            self.lots = []
            self.lot_acres = {}

        elif parent_type == 'multisec':
            # for unpacking multiSec
            self.sec_list = []

        elif parent_type == 'lot_text':
            # for unpacking text from a lot_regex match into component lots
            self.lots = []
            self.lot_acres = {}

    def absorb(self, target_pb):
        """
        Absorb (i.e. append or set) the relevant attributes of a child
        `target_pb` into the parent (i.e. self).
        """

        if not isinstance(target_pb, ParseBag):
            raise TypeError("Can only `absorb()` a pyTRS.ParseBag object.")

        # We do not absorb qqs, lots, or lot_acres, since those are not
        # relevant to a PLSSDescObj (only TractObj).

        if target_pb.desc_is_flawed:
            self.desc_is_flawed = True

        if len(target_pb.w_flags) > 0:
            self.w_flags.extend(target_pb.w_flags)

        if len(target_pb.e_flags) > 0:
            self.e_flags.extend(target_pb.e_flags)

        if len(target_pb.w_flag_lines) > 0:
            self.w_flag_lines.extend(target_pb.w_flag_lines)

        if len(target_pb.e_flag_lines) > 0:
            self.e_flag_lines.extend(target_pb.e_flag_lines)

        if target_pb.parent_type == 'PLSSDesc':
            self.parsed_tracts.extend(target_pb.parsed_tracts)


class Config:
    """
    A class to configure how PLSSDesc and Tract objects should be
    parsed.

    For a list of all parameter options, printed to console:
        `pyTRS.utils.config_parameters()`

    Or launch the Config GUI application:
        `pyTRS.utils.config_util()`

    For a guide to using Config objects general, printed to console:
        `pyTRS.utils.config_help()`

    Save Config object's set parameters to .txt file:
        `Config.save_to_file()`

    Import saved config parameters from .txt file:
        `Config.from_file()`

    All possible parameters (call `pyTRS.utils.config_parameters()` for
    definitions) -- any unspecified parameters will fall back to
    default parsing behavior:
        -- 'n'  <or>  'default_ns.n'  vs.  's'  <or>  'default_ns.s'
        -- 'e'  <or>  'default_ew.e'  vs.  'w'  <or>  'default_ew.w'
        -- 'init_parse'  vs.  'init_parse.False'
        -- 'init_parse_qq'  vs.  'init_parse_qq.False'
        -- 'init_preprocess'  vs.  'init_preprocess.False'
        -- 'clean_qq'  vs.  'clean_qq.False'
        -- 'require_colon'  vs.  'require_colon.False'
        -- 'include_lot_divs'  vs.  'include_lot_divs.False'
        -- 'ocr_scrub'  vs.  'ocr_scrub.False'
        -- 'segment'  vs.  'segment.False'
        -- 'qq_depth_min.<int>'  (defaults to 'qq_depth_min.2')
        -- 'qq_depth_max.<int>'  (defaults to 'qq_depth_max.None')
        -- 'qq_depth.<int>'  (defaults to 'qq_depth.None')
        -- 'break_halves'  vs.  'break_halves.False'
        Only one of the following may be passed -- and none of these are
        recommended:
        -- 'TRS_desc'  <or>  'layout.TRS_desc'
        -- 'desc_STR'  <or>  'layout.desc_STR'
        -- 'S_desc_TR'  <or>  'layout.S_desc_TR'
        -- 'TR_desc_S'  <or>  'layout.TR_desc_S'
        -- 'copy_all'  <or>  'layout.copy_all'
    """

    # Implemented settings that are settable via Config object:
    _CONFIG_ATTRIBUTES = (
        'default_ns',
        'default_ew',
        'init_preprocess',
        'layout',
        'init_parse',
        'init_parse_qq',
        'clean_qq',
        'require_colon',
        'include_lot_divs',
        'ocr_scrub',
        'segment',
        'qq_depth',
        'qq_depth_min',
        'qq_depth_max',
        'break_halves'
    )

    # A list of attribute names whose values should be a bool:
    _BOOL_TYPE_ATTRIBUTES = (
        'init_parse',
        'init_parse_qq',
        'clean_qq',
        'include_lot_divs',
        'init_preprocess',
        'require_colon',
        'ocr_scrub',
        'segment',
        'break_halves'
    )

    _INT_TYPE_ATTRIBUTES = (
        'qq_depth_min',
        'qq_depth_max',
        'qq_depth'
    )

    # Those attributes relevant to PLSSDesc objects:
    _PLSSDESC_ATTRIBUTES = _CONFIG_ATTRIBUTES

    # Those attributes relevant to Tract objects:
    _TRACT_ATTRIBUTES = (
        'default_ns',
        'default_ew',
        'init_preprocess',
        'init_parse_qq',
        'clean_qq',
        'include_lot_divs',
        'ocr_scrub',
        'qq_depth',
        'qq_depth_min',
        'qq_depth_max',
        'break_halves'
    )

    def __init__(self, config_text='', config_name=''):
        """
        Compile a Config object from a string `config_text=`, with
        optional kwarg `config_name=` that does not affect parsing.

        Pass config parameters as a single string, with each parameter
        separated by comma. Spaces are optional and have no effect.
            ex: 'n,s,clean_qq,include_lot_divs.False'

        All possible parameters (call `pyTRS.utils.config_parameters()`
        for definitions) -- any unspecified parameters will fall back to
        default parsing behavior:
        -- 'n'  <or>  'default_ns.n'  vs.  's'  <or>  'default_ns.s'
        -- 'e'  <or>  'default_ew.e'  vs.  'w'  <or>  'default_ew.w'
        -- 'init_parse'  vs.  'init_parse.False'
        -- 'init_parse_qq'  vs.  'init_parse_qq.False'
        -- 'init_preprocess'  vs.  'init_preprocess.False'
        -- 'clean_qq'  vs.  'clean_qq.False'
        -- 'require_colon'  vs.  'require_colon.False'
        -- 'include_lot_divs'  vs.  'include_lot_divs.False'
        -- 'ocr_scrub'  vs.  'ocr_scrub.False'
        -- 'segment'  vs.  'segment.False'
        -- 'qq_depth_min.<int>'  (defaults to 'qq_depth_min.2')
        -- 'qq_depth_max.<int>'  (defaults to 'qq_depth_max.None')
        -- 'qq_depth.<int>'  (defaults to 'qq_depth.None')
        -- 'break_halves'  vs.  'break_halves.False'
        Only one of the following may be passed -- and none of these are
        recommended:
        -- 'TRS_desc'  <or>  'layout.TRS_desc'
        -- 'desc_STR'  <or>  'layout.desc_STR'
        -- 'S_desc_TR'  <or>  'layout.S_desc_TR'
        -- 'TR_desc_S'  <or>  'layout.TR_desc_S'
        -- 'copy_all'  <or>  'layout.copy_all'
        """

        # All attributes (except config_name) are defaulted to `None`,
        # because PLSSDesc and Tract objects will use only those that
        # have been specified as other than `None`.

        if isinstance(config_text, Config):
            # If a Config object is passed as the first argument,
            # decompile its text and use that:
            config_text = config_text.decompile_to_text()
        elif config_text is None:
            config_text = ''
        elif not isinstance(config_text, str):
            raise CONFIG_ERROR
        self.config_text = config_text
        self.config_name = config_name

        # Default all other attributes to `None`:
        for attrib in Config._CONFIG_ATTRIBUTES:
            setattr(self, attrib, None)

        # Remove all spaces from config_text:
        config_text = config_text.replace(' ', '')

        # Separate config parameters with ','  or  ';'
        config_lines = re.split(r'[;,]', config_text)

        for line in config_lines:
            # Parse each 'attrib.val' pair, and commit to the configObj

            if line == '':
                continue

            if re.split(r'[\.=]', line)[0] in Config._BOOL_TYPE_ATTRIBUTES:
                # If string is the name of an attribute that will be stored
                # as a bool, default to `True` (but will be overruled in
                # _set_str_to_values() if specified otherwise):
                self._set_str_to_values(line, default_bool=True)
            elif line.lower() in ['n', 's', 'north', 'south']:
                # Specifying N/S can be done with just a string (there's
                # nothing else it can mean in config context.)
                self.default_ns = line[0].lower()
            elif line.lower() in ['e', 'w', 'east', 'west']:
                # Specifying E/W can be done with just a string (there's
                # nothing else it can mean in config context.)
                self.default_ew = line[0].lower()
            elif line in _IMPLEMENTED_LAYOUTS:
                # Specifying layout can be done with just a string
                # (there's nothing else it can mean in config context.)
                self.layout = line
            else:
                # For anything else, set it with `._set_str_to_values()`.
                self._set_str_to_values(line)

    def __str__(self):
        return self.decompile_to_text()

    def save_to_file(self, filepath):
        """
        Save this Config object to .txt file.
        """

        if filepath[-4:].lower() != '.txt':
            raise ValueError('Error: filename must be .txt file')

        file = open(filepath, 'w')

        attsToWrite = ['config_name'] + list(Config._CONFIG_ATTRIBUTES)

        file.write(f"<Contains config data for parsing PLSSDesc "
                   f"and/or Tract objects with the pyTRS library.>\n")
        file.write(f"<config_text: '{self.decompile_to_text()}'>\n")

        def attrib_text(att):
            """
            Get the output text for the attribute from `self`
            """
            if hasattr(self, att):
                text = f'{att}.{getattr(self, att)}\n'
            else:
                text = ''
            return text

        for att in attsToWrite:
            file.write(attrib_text(att))

        file.close()

    @staticmethod
    def from_file(filepath):
        """
        Compile and return a Config object from .txt file.
        """

        if filepath[-4:].lower() != '.txt':
            raise ValueError('Error: filename must be .txt file')

        with open(filepath, 'r') as file:
            config_lines = file.readlines()

        config = Config()

        for line in config_lines:
            # Ignore data stored in angle brackets
            if line[0] == '<':
                continue

            # For each line, parse the 'attrib.val' pair, and commit to
            # the config, using ._set_str_to_values()
            config._set_str_to_values(line.strip('\n'))
        return config

    @staticmethod
    def from_parent(parent, config_name='', suppress_layout=False):
        """
        Compile and return a Config object from the settings in a
        PLSSDesc object or Tract object.
        :param parent: A PLSSDesc or Tract object whose config
        parameters should be compiled into this Config object.
        :param config_name: An optional string, being the name of this
        Config object.
        :param suppress_layout: A bool, whether or not to include the
        `.layout` attribute from the parent object.
        """

        config = Config()

        config.config_name = config_name
        config.init_preprocess = parent.init_preprocess
        if isinstance(parent, PLSSDesc) and not suppress_layout:
            config.layout = parent.layout
        else:
            config.layout = None
        config.init_parse = parent.init_parse
        config.init_parse_qq = parent.init_parse_qq
        config.clean_qq = parent.clean_qq
        config.default_ns = parent.default_ns
        config.default_ew = parent.default_ew
        config.include_lot_divs = parent.include_lot_divs

        return config

    def decompile_to_text(self) -> str:
        """
        Decompile a Config object into its equivalent string.
        """

        def write_val_as_text(att, val):
            if att in Config._BOOL_TYPE_ATTRIBUTES:
                if val is None:
                    return ""
                if val:
                    # If true, Config needs to receive only the
                    # attribute name (defaults to True if specified).
                    return att
                else:
                    return f"{att}.{val}"

            elif att in ['default_ns', 'default_ew']:
                if val is not None:
                    # Only need to specify 'n' or 's' to set default_ns; and
                    # 'e' or 'w' for default_ew (i.e. not 'default_ns.n' or
                    # 'default_ew.w'), so we return only `val`, and not `att`
                    return val
                else:
                    return ''
            elif val is None:
                return ''
            else:
                return f"{att}.{val}"

        write_vals = []
        for att in Config._CONFIG_ATTRIBUTES:
            w = write_val_as_text(att, getattr(self, att))
            if w:
                # Include only non-empty strings (i.e. config params
                # that were actually set)
                write_vals.append(w)

        return ','.join(write_vals)

    def _set_str_to_values(self, attrib_val, default_bool=None):
        """
        Take in a string of an attribute/value pair (in the format
        'attribute.value' or 'attribute=value') and set the appropriate
        value of the attribute.
        """

        def str_to_value(text):
            """
            Convert string to None or bool or int, if appropriate.
            """
            if text == 'None':
                return None
            elif text == 'True':
                return True
            elif text == 'False':
                return False
            else:
                try:
                    return int(text)
                except ValueError:
                    return text

        # split attribute/value pair by '.' or '='
        #   ex: 'default_ns.n' or 'default_ns=n' -> ['default_ns', 'n']
        comps = re.split(r'[\.=]', attrib_val)

        # Track whether only one component was found in the text with `only_one`:
        #   i.e. "init_parse." --> `only_one=True`
        #   but 'init_parse.True' --> `only_one=False`
        # (Both will set `self.init_parse` to `True` in this example, since it's
        # a bool-type config parameter)
        only_one = False
        if len(comps) != 2:
            only_one = True

        def decide_bool():
            """
            If only_one, return the default bool; otherwise, return
            the user-specified value from attrib_val.
            """
            if only_one:
                return default_bool
            else:
                return str_to_value(comps[1])

        if only_one and not isinstance(default_bool, bool):
            # If only one component, and default_bool was not entered as
            # a bool, return a failure value:
            return -1

        # Write values to the respective attributes. boolTypeAttribs
        # will specifically become bools:
        if comps[0] in Config._BOOL_TYPE_ATTRIBUTES:
            # If this is a bool-type attribute, set the value with decide_bool()
            setattr(self, comps[0], decide_bool())
            return 0
        elif comps[0] in ['default_ns', 'default_ew']:
            # Only writing the first letter of comps[1], in lowercase
            #   (i.e. 'North' --> 'n' or 'West' --> 'w'):
            setattr(self, comps[0], str_to_value(comps[1][0].lower()))
            return 0
        else:
            # Otherwise, set it however it's specified.
            setattr(self, comps[0], str_to_value(comps[1]))
            return 0


########################################################################
# Tools and functions for PLSSDesc.parse()
########################################################################

def _findall_matching_tr(text, layout=None) -> ParseBag:
    """
    INTERNAL USE:

    Find T&R's that appropriately match the layout. Returns a ParseBag
    that contains an ad-hoc `.trPosList` attribute, which holds a list
    of tuples, each containing a T&R (as '000n000w' or fewer digits),
    and its start and end position in the string.
    """

    if layout not in _IMPLEMENTED_LAYOUTS:
        layout = PLSSDesc._deduce_segment_layout(text=text)

    trParseBag = ParseBag(parent_type='PLSSDesc')

    wTRList = []
    # A parsing index for text (marks where we're currently searching from):
    i = 0
    # j is the search-behind pos (indexed against the original text str):
    j = 0
    while True:
        tr_mo = twprge_regex.search(text, pos=i)

        # If there are no more T&R's in the text, end this loop.
        if tr_mo is None:
            break

        # Move the parsing index forward to the start of this next matched T&R.
        i = tr_mo.start()

        # For most layouts we want to know what comes before this matched
        # T&R to see if it is relevant for a NEW Tract, or if it's simply
        # part of the description of another Tract (i.e., we probably
        # don't want to pull the T&R or Section in "...less and except
        # the wellbore of the Johnston #1 located in the NE/4NW/4 of
        # Section 14, T154N-R97W" -- so we have to rule that out).

        # We do that by looking behind our current match for context:

        # We'll look up to this many characters behind i:
        length_to_search_behind = 15
        # ...but we only want to search back to the start of the text string:
        if length_to_search_behind > i:
            length_to_search_behind = i

        # j is the search-behind pos (indexed against the original text str):
        j = i - length_to_search_behind

        # We also need to make sure there's only one section in the string,
        # so loop until it's down to one section:
        secFound = False
        while True:
            sec_mo = sec_regex.search(text[:i], pos=j)
            if sec_mo is None:
                # If no more sections were found, move on to the next step.
                break
            else:
                # Otherwise, if we've found another sec, move the j-index
                # to the end of it
                j = sec_mo.end()
                secFound = True

        # If we've found a section before our current T&R, then we need
        # to check what's in between. For TRS_DESC and S_DESC_TR layouts,
        # we want to rule out misc. interveners:
        #       ','  'in'  'of'  'all of'  'all in'  (etc.).
        # If we have such an intervening string, then this appears to be
        # desc_STR layout -- ex. 'Section 1 of T154N-R97W'
        interveners = ['in', 'of', ',', 'all of', 'all in', 'within', 'all within']
        if secFound and text[j:i].strip() in interveners \
                and layout in [TRS_DESC, S_DESC_TR]:
            # In TRS_Desc and S_DESC_TR layouts specifically, this is
            # NOT a T&R match for a new Tract.

            # Move our parsing index to the end of the currently identified T&R.
            # NOTE: the length of this tr_mo match is indexed against the text
            # slice, so need to add it to i (which is indexed against the full
            # text) to get the 'real' index
            i = i + len(tr_mo.group())

            # and append a warning flag that we've ignored this T&R:
            ignoredTR = _compile_twprge_mo(tr_mo)
            flag = 'TR_not_pulled<%s>' % ignoredTR
            line = tr_mo.group()
            trParseBag.w_flags.append(flag)
            trParseBag.w_flag_lines.append((flag, line))
            continue

        # Otherwise, if there is NO intervener, or the layout is something
        # other than TRS_DESC or S_DESC_TR, then this IS a match and we
        # want to store it.
        else:
            wTRList.append((_compile_twprge_mo(tr_mo), i, i + len(tr_mo.group())))
            # Move the parsing index to the end of the T&R that we just matched:
            i = i + len(tr_mo.group())
            continue

    # Ad-hoc attribute (T&R/position list)
    trParseBag.trPosList = wTRList

    return trParseBag


def _segment_by_tr(text, layout=None, twprge_first=None):
    """
    INTERNAL USE:

    Break the description into segments, based on previously
    identified T&R's that match our description layout via the
    _findall_matching_tr() function. Returns a list of textBlocks AND a
    list of discarded textBlocks.

    :param layout: Which layout to use. If not specified, will deduce.
    :param twprge_first: Whether it's a layout where Twp/Rge comes first
    (i.e. 'TRS_desc' or 'TR_desc_S').
    """

    if layout not in _IMPLEMENTED_LAYOUTS:
        layout = PLSSDesc._deduce_segment_layout(text=text)

    if not isinstance(twprge_first, bool):
        if layout in [TRS_DESC, TR_DESC_S]:
            twprge_first = True
        else:
            twprge_first = False

    # Search for all T&R's that match the layout requirements.
    trMatchPB = _findall_matching_tr(text, layout=layout)

    # Pull ad-hoc `.trPosList` attribute from the ParseBag object. Do
    # not absorb the rest.
    wTRList = trMatchPB.trPosList

    if wTRList == []:
        # If no T&R's had been matched, return the text block as single
        # element in a list (what would have been `trTextBlocks`), and
        # another empty list (what would have been `discardTextBlocks`)
        return [text], []

    trStartPoints = []
    trEndPoints = []
    trList = []
    trTextBlocks = []
    discardTextBlocks = []
    for TRtuple in wTRList:
        trList.append(TRtuple[0])
        trStartPoints.append(TRtuple[1])
        trEndPoints.append(TRtuple[2])

    if twprge_first:
        for i in range(len(trStartPoints)):
            if i == 0 and trStartPoints[i] != 0:
                # If the first element is not 0 (i.e. T&R right at the
                # start), this is discard text.
                discardTextBlocks.append(text[:trStartPoints[i]])
            # Append each text_block
            new_desc = text[trStartPoints[i]:]
            if i + 1 != len(trStartPoints):
                new_desc = text[trStartPoints[i]:trStartPoints[i + 1]]
            trTextBlocks.append((trList.pop(0), _cleanup_desc(new_desc)))

    else:
        for i in range(len(trEndPoints)):
            if i + 1 == len(trEndPoints) and trEndPoints[i] != len(text):
                # If the last element is not the final character in the
                # string (i.e. T&R ends at text end), discard text
                discardTextBlocks.append(text[trEndPoints[i]:])
            # Append each text_block
            new_desc = text[:trEndPoints[i]]
            if i != 0:
                new_desc = text[trEndPoints[i - 1]:trEndPoints[i]]
            trTextBlocks.append((trList.pop(0), _cleanup_desc(new_desc)))

    return trTextBlocks, discardTextBlocks


def _findall_matching_sec(text, layout=None, require_colon='default_colon'):
    """
    INTERNAL USE:

    Pull from the text all sections and 'multi-sections' that are
    appropriate to the description layout. Returns a ParseBag object
    with ad-hoc attributes `.sec_list` and `.multiSecList`.
    :param require_colon: Same effect as in PLSSDesc.parse()`
    """

    # require_colon=True will pass over sections that are NOT followed by
    # colons, in the TRS_DESC and S_DESC_TR layouts. For this version,
    # it is defaulted to True for those layouts. However, if no
    # satisfactory section or multiSec is found during the first pass,
    # it will rerun self.parse() with require_colon='second_pass'.
    # Feeding require_colon=True as a kwarg will override allowing the
    # second pass.

    # Note: the kwarg require_colon= accepts either a string (for
    # 'default_colon' and 'second_pass') or bool. If a bool is fed in
    # (i.e. require_colon=True), a 'second_pass' will NOT be allowed.
    # require_colonBool is the actual variable that controls the relevant
    # logic throughout.
    # Note also: Future versions COULD conceivably compare the
    # first_pass and second_pass results to see which has more secErr's
    # or other types of errors, and use the less-flawed of the two...
    # But I'm not sure that would actually be better...

    # Lastly, note that `require_colonBool` has no effect on layouts
    # other than TRS_DESC and S_DESC_TR, even if set to `True`

    if isinstance(require_colon, bool):
        require_colonBool = require_colon
    elif require_colon == 'second_pass':
        require_colonBool = False
    else:
        require_colonBool = True

    secPB = ParseBag(parent_type='PLSSDesc')

    # Run through the description and find INDIVIDUAL sections or
    # LISTS of sections that match our layout.
    #   For INDIVIDUAL sections, we want "Section 5" in "T154N-R97W,
    #       Section 5: NE/4, Sections 4 and 6 - 10: ALL".
    #   For LISTS of sections (called "MultiSections" in this program),
    #       we want "Sections 4 and 6 - 10" in the above example.

    # For individual sections, save a list of tuples (wSecList), each
    # containing the section number (as '00'), and its start and end
    # position in the text.
    wSecList = []

    # For groups (lists) of sections, save a list of tuples
    # (wMultiSecList), each containing a list of the section numbers
    # (as ['01', '03, '04', '05' ...]), and the group's start and end
    # position in the text.
    wMultiSecList = []

    if layout not in _IMPLEMENTED_LAYOUTS:
        layout = PLSSDesc._deduce_segment_layout(text=text)

    def adj_secmo_end(sec_mo):
        """
        If a sec_mo or multisec_mo ends in whitespace, give the
        .end() minus 1; else return the .end()
        """
        # sec_regex and multiSec_regex can match unlimited whitespace at
        # the end, so if we don't back up 1 char, we can end up with a
        # situation where sec_end is at the same position as tr_start,
        # which can mess up the parser.
        if sec_mo.group().endswith((' ', '\n', '\t', '\r')):
            return sec_mo.end() - 1
        else:
            return sec_mo.end()

    # A parsing index for text (marks where we're currently searching from):
    i = 0
    while True:
        sec_mo = multiSec_regex.search(text, pos=i)

        if sec_mo is None:
            # There are no more sections matching our layout in the text
            break

        # Sections and multiSections can get ruled out for a few reasons.
        # We want to deduce this condition various ways, but handle ruled
        # out sections the same way. So for now, a bool:
        ruledOut = False

        # For TRS_DESC and S_DESC_TR layouts specifically, we do NOT want
        # to match sections following "of", "said", or "in" (e.g.
        # 'the NE/4 of Section 4'), because it very likely means its a
        # continuation of the same description.
        enders = (' of', ' said', ' in', ' within')
        if (layout in [TRS_DESC, S_DESC_TR]) and \
                text[:sec_mo.start()].rstrip().endswith(enders):
            ruledOut = True

        # Also for TRS_DESC and S_DESC_TR layouts, we ONLY want to match
        # sections and multi-Sections that are followed by a colon (if
        # requiredColonBool == True):
        if (require_colonBool) and (layout in [TRS_DESC, S_DESC_TR]) and \
                not (_sec_ends_with_colon(sec_mo)):
            ruledOut = True

        if ruledOut:
            # Move our index to the end of this sec_mo and move to the next pass
            # through this loop, because we don't want to include this sec_mo.
            i = sec_mo.end()

            # Create a warning flag, that we did not pull this section or
            # multiSec and move on to the next loop.
            ignoredSec = _compile_sec_mo(sec_mo)
            if isinstance(ignoredSec, list):
                flag = 'multiSec_not_pulled<%s>' % ', '.join(ignoredSec)
            else:
                flag = 'sec_not_pulled<%s>' % ignoredSec
            secPB.w_flags.append(flag)
            secPB.w_flag_lines.append((flag, sec_mo.group()))
            continue

        # Move the parsing index forward to the start of this next matched Sec
        i = sec_mo.start()

        # If we've gotten to here, then we've found a section or multiSec
        # that we want. Determine which it is, and append it to the respective
        # list:
        if _is_multisec(sec_mo):
            # If it's a multiSec, _unpack it, and append it to the wMultiSecList.
            multiSecParseBagObj = _unpack_sections(sec_mo.group())
            # Pull out the sec_list.
            unpackedMultiSec = multiSecParseBagObj.sec_list

            # First create a flag in the bigPB
            flag = 'multiSec_found<%s>' % ', '.join(unpackedMultiSec)
            secPB.w_flags.append(flag)
            secPB.w_flag_lines.append((flag, sec_mo.group()))

            # Then absorb the multiSecParseBagObj into the bigPB
            secPB.absorb(multiSecParseBagObj)

            # And finally append the tuple for this multiSec
            wMultiSecList.append((unpackedMultiSec, i, adj_secmo_end(sec_mo)))
        else:
            # Append the tuple for this individual section
            wSecList.append((_compile_sec_mo(sec_mo), i, adj_secmo_end(sec_mo)))

        # And move the parser index to the end of our current sec_mo
        i = sec_mo.end()

    # If we're in either TRS_DESC or S_DESC_TR layouts and discovered
    # neither a standalone section nor a multiSec, then rerun
    # _findall_matching_sec() under the same kwargs, except with
    # require_colon='second_pass' (which sets require_colonBool=False),
    # to see if we can capture a section after all.
    # Will return those results instead.
    do_second_pass = True
    if layout not in [TRS_DESC, S_DESC_TR]:
        do_second_pass = False
    if len(wSecList) > 0 or len(wMultiSecList) > 0:
        do_second_pass = False
    if require_colon != 'default_colon':
        do_second_pass = False
    if do_second_pass:
        pass2_PB = _findall_matching_sec(
            text, layout=layout, require_colon='second_pass')
        if len(pass2_PB.sec_list) > 0 or len(pass2_PB.multiSecList) > 0:
            pass2_PB.w_flags.append('pulled_sec_without_colon')
        return pass2_PB

    # Ad-hoc attributes for `sec_list` and `multiSecList`:
    secPB.sec_list = wSecList
    secPB.multiSecList = wMultiSecList
    return secPB


def _parse_segment(
        text_block, layout=None, clean_up=None, require_colon='default_colon',
        handed_down_config=None, init_parse_qq=False, clean_qq=None,
        qq_depth_min=None, qq_depth_max=None, qq_depth=None,
        break_halves=None):
    """
    INTERNAL USE:

    Parse a segment of text into pyTRS.Tract objects. Returns a
    pyTRS.ParseBag object.

    :param text_block: The text to be parsed.
    :param layout: The layout to be assumed. If not specified,
    will be deduced.
    :param clean_up: Whether to clean up common 'artefacts' from
    parsing. If not specified, defaults to False for parsing the
    'copy_all' layout, and `True` for all others.
    :param init_parse_qq: Whether to parse each resulting Tract object
    into lots and QQs when initialized. Defaults to False.
    :param clean_qq: Whether to expect only clean lots and QQ's (i.e.
    no metes-and-bounds, exceptions, complicated descriptions,
    etc.). Defaults to False.
    :param require_colon: Whether to require a colon between the
    section number and the following description (only has an effect
    on 'TRS_desc' or 'S_desc_TR' layouts).
    If not specified, it will default to a 'two-pass' method, where
    first it will require the colon; and if no matching sections are
    found, it will do a second pass where colons are not required.
    Setting as `True` or `False` here prevent the two-pass method.
        ex: 'Section 14 NE/4'
            `require_colon=True` --> no match
            `require_colon=False` --> match (but beware false
                positives)
            <not specified> --> no match on first pass; if no other
                        sections are identified, will be matched on
                        second pass.
    :param handed_down_config: A Config object to be passed to any Tract
    object that is created, so that they are configured identically to
    a parent PLSSDesc object (if any). Defaults to None.
    :param qq_depth_min: (Optional, and only relevant if parsing
    Tracts into lots and QQs.) An int, specifying the minimum depth
    of the parse. If not set here, will default to settings from
    init (if any), which in turn default to 2, i.e. to
    quarter-quarters (e.g., 'N/2NE/4' -> ['NENE', 'NENE']).
    Setting to 3 would return 10-acre subdivisions (i.e. dividing
    the 'NENE' into ['NENENE', 'NWNENE', 'SENENE', 'SWNENE']), and
    so forth.
    WARNING: Higher than a few levels of depth will result in very
    slow performance.
    :param qq_depth_max: (Optional, and only relevant if parsing
    Tracts into lots and QQs.) An int, specifying the maximum depth
    of the parse. If set as 2, any subdivision smaller than
    quarter-quarter (e.g., 'NENE') would be discarded -- so, for
    example, the 'N/2NE/4NE/4' would simply become the 'NENE'. Must
    be greater than or equal to `qq_depth_min`. (Defaults to None --
    i.e. no maximum. Can also be configured at init.)
    :param qq_depth: (Optional, and only relevant if parsing Tracts
    into lots and QQs.) An int, specifying both the minimum and
    maximum depth of the parse. If specified, will override both
    `qq_depth_min` and `qq_depth_max`. (Defaults to None -- i.e. use
    qq_depth_min and optionally qq_depth_max; and can optionally be
    configured at init.)
    :param break_halves: (Optional, and only relevant if parsing
    Tracts into lots and QQs.) Whether to break halves into
    quarters, even if we're beyond the qq_depth_min. (False by
    default, but can be configured at init.)
    :return: a pyTRS.ParseBag object with the parsed data.
    """

    ####################################################################
    # General explanation of how this function works:
    # 1) Lock down parameters for parse via kwargs, etc.
    # 2) If the layout was not appropriately specified, deduce it with
    #       `PLSSDesc.deduceSegment()`
    # 3) Based on the layout, pull each of the T&R's that match our
    #       layout (for segmented parse, /should/ only be one), with
    #       `_findall_matching_tr()` function.
    # 4) Based on the layout, pull each of the Sections and
    #       Multi-Sections that match our layout with
    #       `_findall_matching_sec()` function.
    # 5) Combine all of the positions of starts/ends of T&R's, Sections,
    #       and Multisections into a single dict.
    # 6) Based on layout, apply the appropriate algorithm for breaking
    #       down the text. Each algorithm decides where to break the
    #       text apart based on section location, T&R location, etc.
    #       (e.g., by definition, TR_DESC_S and DESC_STR both pull
    #       the description block from BEFORE an identified section;
    #       whereas S_DESC_TR and TRS_DESC both pull description
    #       block /after/ the section).
    # 6a) For COPY_ALL specifically, the entire text_block will be
    #       copied as the `.desc` attribute of a Tract object.
    # 7) If no Tract was created by the end of the parse (e.g., no
    #       matching T&R found, or no section/multiSec found), then it
    #       will rerun this function using COPY_ALL layout, which will
    #       result in an error flag, but will capture the text as a
    #       Tract. In that case, either the parsing algorithm can't
    #       handle an apparent edge case, or the input is flawed.
    ####################################################################

    if layout not in _IMPLEMENTED_LAYOUTS:
        layout = PLSSDesc._deduce_segment_layout(text_block)

    segParseBag = ParseBag(parent_type='PLSSDesc')

    # If `clean_qq` was specified, convert it to a string, and set it to the
    # `handed_down_config`.
    handed_down_config = Config(handed_down_config)
    if isinstance(clean_qq, bool):
        handed_down_config._set_str_to_values(f"clean_qq.{clean_qq}")
    if break_halves is not None:
        handed_down_config._set_str_to_values(
            f"break_halves.{break_halves}")
    if qq_depth_min is not None:
        handed_down_config._set_str_to_values(f"qq_depth_min.{qq_depth_min}")
    if qq_depth_max is not None:
        handed_down_config._set_str_to_values(f"qq_depth_max.{qq_depth_max}")
    if qq_depth is not None:
        handed_down_config._set_str_to_values(f"qq_depth.{qq_depth}")

    if not isinstance(clean_up, bool):
        # if clean_up has not been specified as a bool, then use these defaults:
        if layout in [TRS_DESC, DESC_STR, S_DESC_TR, TR_DESC_S]:
            clean_up = True
        else:
            clean_up = False

    def clean_as_needed(candidate_text):
        """
        Will return either `candidate_text` (a string for the .desc
        attribute of a `Tract` object that is about to be created) or the
        cleaned-up version of it, depending on the bool `clean_up`.
        """
        if clean_up:
            return _cleanup_desc(candidate_text)
        else:
            return candidate_text

    # Find matching TR's that are appropriate to our layout (should only
    # be one, due to segmentation):
    trPB = _findall_matching_tr(text_block)
    # Pull the ad-hoc `.trPosList` attribute from the ParseBag object,
    # and absorb the rest of the data into segParseBag:
    wTRList = trPB.trPosList
    segParseBag.absorb(trPB)

    # Find matching Sections and MultiSections that are appropriate to
    # our layout (could be any number):
    secPB = _findall_matching_sec(text_block, require_colon=require_colon)
    # Pull the ad-hoc `.sec_list` and `.multiSecList` attributes from the
    # ParseBag object, and absorb the rest of the data into segParseBag:
    wSecList = secPB.sec_list
    wMultiSecList = secPB.multiSecList
    segParseBag.absorb(secPB)

    ####################################################################
    # Break down the wSecList, wMultiSecList, and wTRList into the index points
    ####################################################################

    # The Tract objects will be created from these component parts
    # (first-in-first-out).
    working_tr_list = []
    working_sec_list = []
    working_multiSec_list = []

    # A dict, keyed by index (i.e. start/end point of matched objects
    # within the text) and what was found at that index:
    markersDict = {}
    # This key/val will be overwritten if we found a T&R or Section at
    # the first character
    markersDict[0] = 'text_start'
    # Add the end of the string to the markersDict (may also get overwritten)
    markersDict[len(text_block)] = 'text_end'

    for tuple in wTRList:
        working_tr_list.append(tuple[0])
        markersDict[tuple[1]] = 'tr_start'
        markersDict[tuple[2]] = 'tr_end'

    for tuple in wSecList:
        working_sec_list.append(tuple[0])
        markersDict[tuple[1]] = 'sec_start'
        markersDict[tuple[2]] = 'sec_end'

    for tuple in wMultiSecList:
        working_multiSec_list.append(tuple[0])  # A list of lists
        markersDict[tuple[1]] = 'multiSec_start'
        markersDict[tuple[2]] = 'multiSec_end'

    # If we're in either TRS_DESC or S_DESC_TR layouts and discovered
    # neither a standalone section nor a multiSec, then rerun the parse
    # under the same kwargs, except with require_colon='second_pass' (which
    # sets require_colonBool=False), to see if we can capture a section after
    # all. Will return those results instead:
    do_second_pass = True
    if layout not in [TRS_DESC, S_DESC_TR]:
        do_second_pass = False
    if len(working_sec_list) > 0 or len(working_multiSec_list) > 0:
        do_second_pass = False
    if require_colon != 'default_colon':
        do_second_pass = False
    if do_second_pass:
        replacementMidPB = _parse_segment(
            text_block=text_block, layout=layout, require_colon='second_pass',
            handed_down_config=handed_down_config, init_parse_qq=init_parse_qq)
        TRS_found = replacementMidPB.parsed_tracts[0].trs is not None
        if TRS_found:
            # If THIS time we successfully found a TRS, flag that we ran
            # it without requiring colon...
            replacementMidPB.w_flags.append('pulled_sec_without_colon')
            for trObj in replacementMidPB.parsed_tracts:
                trObj.w_flags.append('pulled_sec_without_colon')
            # TODO: Note, this may not get applied to all Tract objects
            #   in the entire .parsed_tracts TractList.
        return replacementMidPB

    # Get a list of all of the keys, then sort them, so that we're pulling
    # first-to-last (vis-a-vis the original text of this segment):
    mrkrsLst = list(markersDict.keys())
    mrkrsLst.sort()  # We sort the keys, so that we're pulling first-to-last.

    def new_tract(
            text_for_new_desc, sec='default_sec', tr='default_tr') -> Tract:
        """
        Create and return a new Tract object, using the current
        working_sec and working_tr, unless otherwise specified (e.g., for
        multiSec). Positional args filled as <desc, sec, twprge>
        """

        if sec == 'default_sec':
            sec = working_sec
        if tr == 'default_tr':
            tr = working_tr
        return Tract(
            desc=text_for_new_desc, trs=tr + sec, config=handed_down_config,
            init_parse_qq=init_parse_qq)

    def flag_unused(unused_text, context):
        """
        Create a warning flag and flagLine for unused text.
        """
        flag = f"Unused_desc_<{unused_text}>"
        segParseBag.w_flags.append(flag)
        segParseBag.w_flag_lines.append((flag, context))

    if layout in [DESC_STR, TR_DESC_S]:
        # These two layouts are handled nearly identically, except that
        # in DESC_STR the TR is popped before it's encountered, and in
        # TR_DESC_S it's popped only when encountered. So setting
        # initial TR is the only difference.

        # Defaults to a T&R error.
        working_tr = 'TRerr_'

        # For TR_DESC_S, will pop the working_tr when we encounter the
        # first TR. However, for desc_STR, need to pre-set our working_tr
        # (if one is available):
        if layout == DESC_STR and len(working_tr_list) > 0:
            working_tr = working_tr_list.pop(0)

        # Description block comes before section in this layout, so we
        # pre-set the working_sec and working_multiSec (if any are available):
        working_sec = 'secError'
        if len(working_sec_list) > 0:
            working_sec = working_sec_list.pop(0)

        working_multiSec = ['secError']
        if len(working_multiSec_list) > 0:
            working_multiSec = working_multiSec_list.pop(0)

        finalRun = False  # Will switch to True on the final loop

        # We'll check every marker to see what's at that point in the
        # text; depending on the type of marker, it will tell us how to
        # construct the next Tract object, or to pop the next section,
        # multi-Section, or T&R from the start of the respective working
        # list.

        # Track how far back we'll write to when we come across
        # secErrors in this layout:
        secErrorWriteBackToPos = 0
        for i in range(len(mrkrsLst)):

            if i == len(mrkrsLst) - 1:
                finalRun = True

            # Get this marker position and type
            markerPos = mrkrsLst[i]
            markerType = markersDict[markerPos]

            # Unless this is the last marker, get the next marker
            # position and type
            if not finalRun:
                nextMarkerPos = mrkrsLst[i + 1]
                nextMarkerType = markersDict[nextMarkerPos]
            else:
                # For the final run, default to the current marker
                # position and type
                nextMarkerPos = markerPos
                nextMarkerType = markerType

            # Unless it's the first one, get the last marker position and type
            if i != 0:
                lastMarkerPos = mrkrsLst[i - 1]
                lastMarkerType = markersDict[lastMarkerPos]
            else:
                lastMarkerPos = markerPos
                lastMarkerType = markerType

            # We don't need to handle 'text_start' in this layout.

            if markerType == 'tr_end':
                # This is included for handling secErrors in this layout.
                # Note that it does not force a continue.
                secErrorWriteBackToPos = markerPos

            if markerType == 'tr_start':  # Pull the next T&R in our list
                if len(working_tr_list) == 0:
                    # Will cause a TR error if another TRS+Desc is created:
                    working_tr = 'TRerr_'
                else:
                    working_tr = working_tr_list.pop(0)
                continue

            if nextMarkerType == 'sec_start':
                # NOTE that this algorithm is looking for the start of a
                # section at the NEXT marker!

                # Create new TractObj, compiling our current working_tr
                # and working_sec into a TRS, with the desc being the
                # text between this marker and the next.
                TractObj = new_tract(
                    clean_as_needed(
                        text_block[mrkrsLst[i]:mrkrsLst[i + 1]].strip()))
                segParseBag.parsed_tracts.append(TractObj)
                if i + 2 <= len(mrkrsLst):
                    secErrorWriteBackToPos = mrkrsLst[i + 2]
                else:
                    secErrorWriteBackToPos = mrkrsLst[i + 1]

            elif nextMarkerType == 'multiSec_start':
                # NOTE that this algorithm is looking for the start of a
                # multi-section at the NEXT marker!

                # Create a new TractObj, compiling our current working_tr
                # and each of the sections in the working_multiSec into a
                # TRS, with the desc being the text between this marker
                # and the next. Do that for EACH of the sections in the
                # working_multiSec
                for sec in working_multiSec:
                    TractObj = new_tract(
                        clean_as_needed(
                            text_block[mrkrsLst[i]:mrkrsLst[i + 1]].strip()),
                        sec)
                    segParseBag.parsed_tracts.append(TractObj)
                if i + 2 <= len(mrkrsLst):
                    secErrorWriteBackToPos = mrkrsLst[i + 2]
                else:
                    secErrorWriteBackToPos = mrkrsLst[i + 1]

            elif nextMarkerType == 'tr_start' \
                    and markerType not in ['sec_end', 'multiSec_end'] \
                    and nextMarkerPos - secErrorWriteBackToPos > 5:
                # If (1) we found a T&R next, and (2) we aren't CURRENTLY
                # at a sec_end or multiSec_end, and (3) it's been more than
                # a few characters since we last created a new Tract, then
                # we're apparently dealing with a secError, and we need to
                # make a flawed TractObj with  that secError.
                TractObj = new_tract(
                    clean_as_needed(
                        text_block[secErrorWriteBackToPos:mrkrsLst[i + 1]].strip()),
                    'secError')
                segParseBag.parsed_tracts.append(TractObj)

            elif markerType == 'sec_start':
                if len(working_sec_list) == 0:
                    # Will cause a section error if another TRS+Desc is created
                    working_sec = 'secError'
                else:
                    working_sec = working_sec_list.pop(0)

            elif markerType == 'multiSec_start':
                if len(working_multiSec_list) == 0:
                    # Will cause a section error if another TRS+Desc is created
                    working_multiSec = ['secError']
                else:
                    working_multiSec = working_multiSec_list.pop(0)

            elif markerType == 'sec_end':
                if nextMarkerType not in ['sec_start', 'tr_start', 'multiSec_start'] \
                        and markerPos != len(text_block):
                    # Whenever we come across a Section end, the next thing must
                    # be either a sec_start, multiSec_start, or tr_start.
                    # Hence the warning flag, if that's not true:
                    unusedText = text_block[mrkrsLst[i]:mrkrsLst[i + 1]].strip()
                    segParseBag.w_flags.append('Unused_desc_<%s>' % unusedText)

            elif markerType == 'text_end':
                break

            # Capture unused text at the end of the string.
            if layout == TR_DESC_S \
                    and markerType in ['sec_end', 'multiSec_end'] \
                    and not finalRun \
                    and nextMarkerType not in ['sec_start', 'tr_start', 'multiSec_start']:
                # For TR_DESC_S, whenever we come across the end of a Section or
                # multi-Section, the next thing must be either a sec_start,
                # multiSec_start, or tr_start. Hence the warning flag, if that's
                # not true:
                unusedText = text_block[mrkrsLst[i]:mrkrsLst[i + 1]].strip()
                flag_unused(unusedText, text_block[lastMarkerPos:nextMarkerPos])

            # Capture unused text at the end of a section/multiSec (if appropriate).
            if layout == DESC_STR \
                    and markerType in ['sec_end', 'multiSec_end'] \
                    and not finalRun \
                    and nextMarkerType not in ['sec_start', 'multiSec_start']:
                unusedText = text_block[markerPos:nextMarkerPos]
                if len(_cleanup_desc(unusedText)) > 3:
                    flag_unused(
                        unusedText, text_block[lastMarkerPos:nextMarkerPos])

    if layout == S_DESC_TR:
        # TODO: Can probably cut out a lot of lines of code by combining
        #   S_DESC_TR and TRS_DESC parsing, and just handling how
        #   the first T&R is popped.

        # Defaults to a T&R error if no T&R's were identified, but
        # pre-set our T&R (if one is available):
        working_tr = 'TRerr_'
        if len(working_tr_list) > 0:
            working_tr = working_tr_list.pop(0)

        # Default to a 'secError' for this layout. Will change when we
        # meet the first sec and multiSec respectively.
        working_sec = 'secError'
        working_multiSec = ['secError']

        finalRun = False

        # We'll check every marker to see what's at that point in the
        # text; depending on the type of marker, it will tell us how to
        # construct the next Tract object, or to pop the next section,
        # multi-Section, or T&R from the respective working list.
        for i in range(len(mrkrsLst)):

            if i == len(mrkrsLst) - 1:
                # Just a shorthand to not show the logic every time:
                finalRun = True

            # Get this marker position and type
            markerPos = mrkrsLst[i]
            markerType = markersDict[markerPos]

            # Unless this is the last marker, get the next marker
            # position and type
            if not finalRun:
                nextMarkerPos = mrkrsLst[i + 1]
                nextMarkerType = markersDict[nextMarkerPos]
            else:
                # For the final run, default to the current marker
                # position and type
                nextMarkerPos = markerPos
                nextMarkerType = markerType

            # Unless it's the first one, get the last marker position and type
            if i != 0:
                lastMarkerPos = mrkrsLst[i - 1]
                lastMarkerType = markersDict[lastMarkerPos]
            else:
                lastMarkerPos = markerPos
                lastMarkerType = markersDict[markerPos]

            # We don't need to handle 'text_start' in this layout.

            if markerType == 'sec_start':
                if len(working_sec_list) == 0:
                    # Will cause a section error if another TRS+Desc is created
                    working_sec = 'secError'
                else:
                    working_sec = working_sec_list.pop(0)
                #continue

            elif markerType == 'multiSec_start':
                if len(working_multiSec_list) == 0:
                    # Will cause a section error if another TRS+Desc is created
                    working_multiSec = ['secError']
                else:
                    working_multiSec = working_multiSec_list.pop(0)

            elif markerType == 'sec_end':
                # We found the start of a new desc block (betw Section's end
                # and whatever's next).

                # Create new TractObj, compiling our current working_tr
                # and working_sec into a TRS, with the desc being the text
                # between this marker and the next.
                TractObj = new_tract(
                    clean_as_needed(
                        text_block[mrkrsLst[i]:mrkrsLst[i + 1]].strip()))
                segParseBag.parsed_tracts.append(TractObj)

            elif markerType == 'multiSec_end':
                # We found start of a new desc block (betw multiSec end
                # and whatever's next).

                # Create a new TractObj, compiling our current working_tr
                # and each of the sections in the working_multiSec into a
                # TRS, with the desc being the text between this marker
                # and the next. Do that for EACH of the sections in the
                # working_multiSec.
                for sec in working_multiSec:
                    TractObj = new_tract(
                        clean_as_needed(
                            text_block[mrkrsLst[i]:mrkrsLst[i + 1]].strip()),
                        sec)
                    segParseBag.parsed_tracts.append(TractObj)

            elif markerType == 'tr_start':  # Pull the next T&R in our list
                if len(working_tr_list) == 0:
                    # Will cause a TR error if another TRS+Desc is created:
                    working_tr = 'TRerr_'
                else:
                    working_tr = working_tr_list.pop(0)

            elif markerType == 'tr_end':
                # The only effect 'tr_end' has on this layout is checking
                # for unused text.
                unusedText = text_block[markerPos:nextMarkerPos]
                if len(unusedText.strip()) > 2:
                    flag_unused(
                        unusedText, text_block[lastMarkerPos:nextMarkerPos])

    if layout == COPY_ALL:
        # A minimally-processed layout option. Basically just copies the
        # entire text as a `.desc` attribute. Can serve as a fallback if
        # deduce_layout() can't figure out what the real layout is (or
        # it's a flawed input).
        # TRS will be arbitrarily set to first T&R + Section (if either
        # is actually found).

        if len(wTRList) == 0:
            # Defaults to a T&R error if no T&R's were identified
            working_tr = 'TRerr_'
        else:
            working_tr = wTRList[0][0]

        if len(wSecList) == 0:
            working_sec = 'secError'
        else:
            working_sec = wSecList[0][0]

        # If no solo section was found, check for a multiSec we can pull from
        if len(wMultiSecList) != 0 and working_sec == 'secError':
            # Just pull the first section in the first multiSec.
            working_sec = wMultiSecList[0][0][0]

        # Append a dummy TractObj that contains the full text as its `.desc`
        # attribute. TRS is arbitrary, but will pull a TR + sec, if found.
        TractObj = new_tract(text_block)
        segParseBag.parsed_tracts.append(TractObj)

    if layout == TRS_DESC:

        # Defaults to a T&R error and Sec errors for this layout.
        working_tr = 'TRerr_'
        working_sec = 'secError'
        working_multiSec = ['secError']

        finalRun = False

        # We'll check every marker to see what's at that point in the text;
        # depending on the type of marker, it will tell us how to construct
        # the next Tract object, or to pop the next section, multi-Section,
        # or T&R from the respective working list.
        for i in range(len(mrkrsLst)):

            if i == len(mrkrsLst) - 1:
                # Just shorthand to avoid writing the logic every time.
                finalRun = True

            # Get this marker position and type
            markerPos = mrkrsLst[i]
            markerType = markersDict[markerPos]

            # Unless this is the last marker, get the next marker
            # position and type
            if not finalRun:
                nextMarkerPos = mrkrsLst[i + 1]
                nextMarkerType = markersDict[nextMarkerPos]
            else:
                # For the final run, default to the current marker
                # position and type
                nextMarkerPos = markerPos
                nextMarkerType = markerType

            # Unless it's the first one, get the last marker position and type
            if i != 0:
                lastMarkerPos = mrkrsLst[i - 1]
                lastMarkerType = markersDict[lastMarkerPos]
            else:
                lastMarkerPos = markerPos
                lastMarkerType = markerType

            if markerType == 'text_start':
                # 'text_start' does not have implications for parsing
                # TRS_DESC layout. Move on to next.
                pass

            elif markerType == 'tr_start':
                # Pull the next T&R in our list
                if lastMarkerType == 'tr_end':
                    segParseBag.e_flags.append('Unused_TR<%s>' % working_tr)
                working_tr = working_tr_list.pop(0)

            elif markerType == 'tr_end':
                # The only effect 'tr_end' has on this layout is checking
                # for unused text.
                unusedText = text_block[markerPos:nextMarkerPos]
                if len(unusedText.strip()) > 2:
                    flag_unused(
                        unusedText, text_block[lastMarkerPos:nextMarkerPos])

            elif markerType == 'sec_start':
                if len(working_sec_list) == 0:
                    # If another TRS+Desc pair is created after this point,
                    # it will result in a Section error:
                    working_sec = 'secError'
                else:
                    working_sec = working_sec_list.pop(0)

            elif markerType == 'multiSec_start':
                if len(working_multiSec_list) == 0:
                    # If another GROUP of TRS+Desc pairs is created
                    # after this point, it will result in a Section error.
                    working_multiSec = ['secError']
                else:
                    working_multiSec = working_multiSec_list.pop(0)

            elif markerType == 'sec_end':
                # Create a new TractObj, compiling our current working_tr
                # and working_sec into a TRS, with the desc being the text
                # between this marker and the next.
                TractObj = new_tract(
                    clean_as_needed(text_block[markerPos:nextMarkerPos].strip()))
                segParseBag.parsed_tracts.append(TractObj)

            elif markerType == 'multiSec_end':
                # Create a series of new TractObjs, compiling our current
                # working_tr and elements from working_multiSec into a series
                # of TRS, with the desc for EACH being the text between this
                # marker and the next.
                for sec in working_multiSec:
                    TractObj = new_tract(
                        clean_as_needed(text_block[markerPos:nextMarkerPos].strip()), sec)
                    segParseBag.parsed_tracts.append(TractObj)

            elif markerType == 'text_end':
                break

    if len(segParseBag.parsed_tracts) == 0:
        # If we identified no Tracts in this segment, re-parse using
        # COPY_ALL layout.
        replacementPB = _parse_segment(
            text_block, layout=COPY_ALL, clean_up=False, require_colon=False,
            handed_down_config=handed_down_config, init_parse_qq=init_parse_qq,
            clean_qq=clean_qq)
        return replacementPB

    return segParseBag


def _cleanup_desc(text):
    """
    INTERNAL USE:
    Clean up common 'artifacts' from parsing--especially layouts other
    than TRS_DESC. (Intended to be run only on post-parsing .desc
    attributes of Tract objects.)
    """

    # Run this loop until the input string matches the output string.
    while True:
        text1 = text
        text1 = text1.lstrip('.')
        text1 = text1.strip(',;:-–—\t\n ')
        cullList = [' the', ' all in', ' all of', ' of', ' in', ' and']
        # Check to see if text1 ends with each of the strings in the
        # cullList, and if so, slice text1 down accordingly.
        for cullString in cullList:
            cull_length = len(cullString)
            if text1.lower().endswith(cullString):
                text1 = text1[:-cull_length]
        if text1 == text:
            break
        text = text1
    return text


def find_twprge(text, default_ns='n', default_ew='w'):
    """
    Returns a list of all T&R's in the text (formatted as '000n000w',
    or with fewer digits as needed).
    """

    # search the PLSS description for all T&R's
    twprge_mo_iter = twprge_regex.finditer(text)
    tr_list = []

    # For each match, compile a clean T&R and append it.
    for twprge_mo in twprge_mo_iter:
        tr_list.append(_compile_twprge_mo(twprge_mo))
    return tr_list


def _ocr_scrub_alpha_to_num(text):
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
    text = text.replace('S', '5')
    text = text.replace('s', '5')
    text = text.replace('O', '0')
    text = text.replace('I', '1')
    text = text.replace('l', '1')
    return text


def _preprocess_twprge_mo(tr_mo, default_ns='n', default_ew='w') -> str:
    """
    INTERNAL USE:
    Take a T&R match object (tr_mo) and check for missing 'T', 'R', and
    and if N/S and E/W are filled in. Will fill in any missing elements
    (using default_ns and default_ew as necessary) and outputs a string in
    the format T000N-R000W (or fewer digits for twp & rge), which is to
    be swapped into the source text where the tr_mo was originally
    matched, in order to clean up the pp_desc.
    """

    clean_tr = _compile_twprge_mo(tr_mo, default_ns=default_ns, default_ew=default_ew)
    twp, ns, rge, ew = decompile_twprge(clean_tr)

    # Maintain the first character, if it's a whitespace:
    if tr_mo.group().startswith(('\n', '\t', ' ')):
        first = tr_mo.group()[0]
    else:
        first = ''

    twp = _ocr_scrub_alpha_to_num(twp)  # twp number
    rge = _ocr_scrub_alpha_to_num(rge)  # rge number

    # Maintain the last character, if it's a whitespace.
    if tr_mo.group().endswith(('\n', '\t', ' ')):
        last = tr_mo.group()[-1]
    else:
        last = ''

    output_ppTR = first + 'T' + twp + ns.upper() + '-R' + rge + ew.upper() + last
    return output_ppTR


def decompile_twprge(twprge) -> tuple:
    """
    Take a compiled T&R (format '000n000w', or fewer digits) and break
    it into four elements, returned as a 4-tuple:
    (Twp number, Twp direction, Rge number, Rge direction)
        NOTE: If Twp and Rge are each 'TRerr', will return
            ('TRerr', None, 'TRerr', None).
        ex: '154n97w'   -> ('154', 'n', '97', 'w')
        ex: 'TRerr'     -> ('TRerr', None, 'TRerr', None)"""
    twp, rge, _ = break_trs(twprge)
    twp_dir = None
    rge_dir = None
    if twp != 'TRerr':
        twp_dir = twp[-1]
        twp = twp[:-1]
    if rge != 'TRerr':
        rge_dir = rge[-1]
        rge = rge[:-1]

    return (twp, twp_dir, rge, rge_dir)


def _compile_twprge_mo(mo, default_ns='n', default_ew='w'):
    """
    INTERNAL USE:
    Take a match object (`mo`) of an identified T&R, and return a string
    in the format of '000n000w' (i.e. between 1 and 3 digits for
    township and for range numbers).
    """

    twpNum = mo[2]
    # Clean up any leading '0's in twpNum.
    # (Try/except is used to handle twprge_ocr_scrub_regex mo's, which
    # can contain alpha characters in `twpNum`.)
    try:
        twpNum = str(int(twpNum))
    except:
        pass

    # if mo[4] is None:
    if mo.group(3) == '':
        ns = default_ns
    else:
        ns = mo[3][0].lower()

    if len(mo.groups()) > 10:
        # Only some of the `twprge_regex` variations generate this many
        # groups. Those that do may have Rge number in groups 6 /or/ 12,
        # and range direction in group 7 /or/ 13.
        # So we handle those ones with extra if/else...
        if mo[12] is None:
            rgeNum = mo[6]
        else:
            rgeNum = mo[12]
    else:
        rgeNum = mo[6]

    # --------------------------------------
    # Clean up any leading '0's in rgeNum.
    # (Try/except is used to handle twprge_ocr_scrub_regex mo's, which
    # can contain alpha characters in `rgeNum`.)
    try:
        rgeNum = str(int(rgeNum))
    except:
        pass

    if len(mo.groups()) > 10:
        # Only some of the `twprge_regex` variations generate this many
        # groups. Those that do may have Rge number in groups 6 /or/ 12,
        # and range direction in group 7 /or/ 13.
        # So we handle those ones with extra if/else...
        if mo[13] is None:
            if mo[7] in ['', None]:
                ew = default_ew
            else:
                ew = mo[7][0].lower()
        else:
            ew = mo[13][0].lower()
    else:
        if mo[7] in ['', None]:
            ew = default_ew
        else:
            ew = mo[7][0].lower()

    return twpNum + ns + rgeNum + ew


def _compile_sec_mo(sec_mo):
    """
    INTERNAL USE
    Takes a match object (mo) of an identified multiSection, and
    returns a string in the format of '00' for individual sections and a
    list ['01', '02', ...] for multiSections
    """
    if _is_multisec(sec_mo):
        multiSecParseBagObj = _unpack_sections(sec_mo.group())
        return multiSecParseBagObj.sec_list  # Pull out the sec_list
    elif _is_singlesec(sec_mo):
        return _get_last_sec(sec_mo).rjust(2, '0')
    else:
        return


def find_sec(text):
    """
    Returns a list of all identified individual Section numbers in the
    text (formatted as '00').
    NOTE: Does not capture multi-Sections (i.e. lists of Sections).
    """

    # Search for all Section markers occurring anywhere:
    sec_mo_list = sec_regex.findall(text)
    sec_list = []
    for sec_mo in sec_mo_list:
        # This generates a clean list of every identified section,
        # formatted as 2 digits.
        newSec = sec_mo[2][-2:].rjust(2, '0')
        sec_list.append(newSec)
    return sec_list


def find_multisec(text, flat=True) -> list:
    """
    Returns a list of all identified multi-Section numbers in the
    text (formatted as '00'). Returns a flattened list by default, but
    can return a nested list (one per multiSec) with `flat=False`.
    """

    packedMultiSec_list = []
    unpackedMultiSec_list = []

    i = 0
    while True:
        multiSec_mo = multiSec_regex.search(text, pos = i)
        if multiSec_mo is None:
            break
        packedMultiSec_list.append(multiSec_mo.group())
        i = multiSec_mo.end()

    for multiSec in packedMultiSec_list:
        multiSecParseBagObj = _unpack_sections(multiSec)
        workingSecList = multiSecParseBagObj.sec_list
        if len(workingSecList) == 1:
            # skip any single-section matches
            continue
        unpackedMultiSec_list.append(workingSecList)

    if flat:
        unpackedMultiSec_list = flatten(unpackedMultiSec_list)

    return unpackedMultiSec_list


def _unpack_sections(sec_text_block):
    """
    INTERNAL USE:
    Feed in a string of a multiSec_regex match object, and return a
    ParseBag object with a .sec_list attribute containing all of the
    sections (i.e. 'Sections 2, 3, 9 - 11' will return ParseBag whose
    .sec_list contains ['02', '03', '09', '10', 11'].
    """

    # TODO: Maybe just put together a simpler algorithm. Since there's
    #   so much less possible text in a list of Sections, can probably
    #   just add from left-to-right, unlike _unpack_lots.

    multiSecParseBag = ParseBag(parent_type='multisec')

    sectionsList = []  #
    remainingSecText = sec_text_block

    # A working list of the sections. Note that this gets filled from
    # last-to-first on this working text block, but gets reversed at the end.
    wSectionsList = []
    foundThrough = False
    while True:
        secs_mo = multiSec_regex.search(remainingSecText)

        if secs_mo is None:  # we're out of section numbers.
            break

        else:
            # Pull the right-most section number (still as a string):
            secNum = _get_last_sec(secs_mo)

            if _is_singlesec(secs_mo):
                # We can skip the next loop after we've found the last section.
                remainingSecText = ''

            else:
                # If we've found >= 2 sections, we will need to loop at
                # least once more.
                remainingSecText = remainingSecText[:secs_mo.start(12)]

            # Clean up any leading '0's in secNum.
            secNum = str(int(secNum))

            # Layout section number as 2 digits, with a leading 0, if needed.
            newSec = secNum.rjust(2, '0')

            if foundThrough:
                # If we've identified a elided list (e.g., 'Sections 3 - 9')...
                prevSec = wSectionsList[-1]
                # Take the secNum identified earlier this loop:
                start_of_list = int(secNum)
                # The the previously last-identified section:
                end_of_list = int(prevSec)
                correctOrder = True
                if start_of_list >= end_of_list:
                    correctOrder = False
                    multiSecParseBag.w_flags.append('nonSequen_sec')
                    multiSecParseBag.w_flag_lines.append(
                        ('nonSequen_sec',
                         f'Sections {start_of_list} - {end_of_list}')
                    )

                ########################################################
                # `start_of_list` and `end_of_list` variable names are
                # unintuitive. Here's an explanation:
                # The 'sections' list is being filled in reverse by this
                # algorithm, starting at the end of the search string
                # and running backwards. Thus, this particular loop,
                # which is attempting to _unpack "Sections 3 - 9", will
                # be fed into the sections list as [08, 07, 06, 05, 04,
                # 03]. (09 should already be in the list from the
                # previous loop.)  'start_of_list' refers to the
                # original text (i.e. in 'Sections 3 - 9', start_of_list
                # will be 3; end_of_list will be 9).
                ########################################################

                # vars a,b&c are the bounds (a&b) and incrementation (c)
                # of the range() for the secs in the elided list:
                # If the string is correctly 'Sections 3 - 9' (for example),
                # we use the default:
                a, b, c = end_of_list - 1, start_of_list - 1, -1
                # ... but if the string is 'sections 9 - 3' (i.e. wrong),
                # we use:
                if not correctOrder:
                    a, b, c = end_of_list + 1, start_of_list + 1, 1

                for i in range(a, b, c):
                    addSec = str(i).rjust(2, '0')
                    if addSec in wSectionsList:
                        multiSecParseBag.w_flags.append(f'dup_sec<{addSec}>')
                        multiSecParseBag.w_flag_lines.append(
                            (f'dup_sec<{addSec}>', f'Section {addSec}'))
                    wSectionsList.append(addSec)
                foundThrough = False  # Reset the foundThrough.

            else:
                # Otherwise, if it's a standalone section (not the start
                #   of an elided list), we add it.
                # We check this new section to see if it's in EITHER
                #   sectionsList OR wSectionsList:
                if newSec in sectionsList or newSec in wSectionsList:
                    multiSecParseBag.w_flags.append('dup_sec')
                    multiSecParseBag.w_flag_lines.append(
                        ('dup_sec', f'Section {newSec}'))
                wSectionsList.append(newSec)

            # If we identified at least two sections, we need to check
            # if the last one is the end of an elided list:
            if _is_multisec(secs_mo):
                thru_mo = through_regex.search(secs_mo.group(6))
                # Check if we find 'through' (or equivalent symbol or
                # abbreviation) before this final section:
                if thru_mo is None:
                    foundThrough = False
                else:
                    foundThrough = True
    wSectionsList.reverse()
    multiSecParseBag.sec_list = wSectionsList

    return multiSecParseBag


########################################################################
# Tools for interpreting multiSec_regex match objects:
########################################################################

def _is_multisec(multisec_mo) -> bool:
    """
    INTERNAL USE:
    Determine whether a multiSec_regex match object is a multiSec.
    """
    return multisec_mo.group(12) is not None


def _is_singlesec(multisec_mo) -> bool:
    """
    INTERNAL USE:
    Determine whether a multiSec_regex match object is a single section.
    """
    return (multisec_mo.group(12) is None) and (multisec_mo.group(5) is not None)


def _get_last_sec(multisec_mo) -> str:
    """
    INTERNAL USE:
    Extract the right-most section in a multiSec_regex match object.
    Returns None if no match.
    """
    if _is_multisec(multisec_mo):
        return multisec_mo.group(12)
    elif _is_singlesec(multisec_mo):
        return multisec_mo.group(5)
    else:
        return None


def _is_plural_singlesec(multisec_mo) -> bool:
    """
    INTERNAL USE:
    Determine if a multiSec_regex match object is a single section
    but pluralized (ex. 'Sections 14: ...').
    """
    # Only a single section in this match...
    # But there's a plural "Sections" anyway!
    if _is_singlesec(multisec_mo) and multisec_mo.group(4) is not None:
        return multisec_mo.group(4).lower() == 's'
    else:
        return False


def _sec_ends_with_colon(multisec_mo) -> bool:
    """
    INTERNAL USE:
    Determine whether a multiSec_regex match object ends with a colon.
    """
    return multisec_mo.group(13) == ':'


########################################################################
# Tools for Tract.parse():
########################################################################

def _scrub_aliquots(text, clean_qq=False) -> str:
    """
    INTERNAL USE:
    Scrub the raw text of a Tract's description, to convert aliquot
    components into standardized abbreviations.
    """

    def scrubber(text, regex_run):
        """
        Convert the raw aliquots to cleaner components, using the
        regex fed as the second arg, and returns the scrubbed text.
        (Will only function properly with specific aliquots regexes.)
        """
        remainingText = text
        rebuilt_text = ''

        # NOTE: we do not use the `re.sub()` function because we need to
        # maintain the first character in the regex match, which provides
        # necessary context to prevent over-matching. For example, the
        # `NE_regex` must match '(\b|¼|4|½|2)' at the beginning, so that
        # we don't capture "one hundred" as "oNE¼ hundred".
        # (The clean_qq regexes do not have this requirement.)

        while True:
            mo = regex_run.search(remainingText)
            if mo is None:  # If we found no more matches like this.
                rebuilt_text = rebuilt_text + remainingText
                break
            rebuilt_text = "{0}{1}{2}".format(
                rebuilt_text,
                remainingText[:mo.start(2)],
                QQ_SCRUBBER_DEFINITIONS[regex_run]
            )
            remainingText = remainingText[mo.end():]
        return rebuilt_text

    # We'll run these scrubber regexes on the text:
    scrubber_rgxs = [
        NE_regex, NW_regex, SE_regex, SW_regex, N2_regex, S2_regex,
        E2_regex, W2_regex
    ]

    # If the user has specified that the input data is clean (i.e. no
    # metes-and-bounds tracts, etc.), then broader regexes can also be applied.
    if clean_qq:
        scrubber_rgxs.extend(
            [cleanNE_regex, cleanNW_regex, cleanSE_regex, cleanSW_regex])
    # Now run each of the regexes over the text:
    for reg_to_run in scrubber_rgxs:
        text = scrubber(text, reg_to_run)

    # And now that 'halves' have been cleaned up, we can also convert matches
    # like 'E½NE' into 'E½NE¼', using essentially the same code as in scrubber()
    remainingText = text
    rebuilt_text = ''
    while True:
        halfQ_mo = halfPlusQ_regex.search(remainingText)
        if halfQ_mo is None:  # If we found no more matches like this.
            rebuilt_text = rebuilt_text + remainingText
            break
        clean_hpQ = f'{halfQ_mo.group(3)}½{halfQ_mo.group(5)}¼'
        rebuilt_text = rebuilt_text + remainingText[:halfQ_mo.start(3)] + clean_hpQ
        remainingText = remainingText[halfQ_mo.end():]
    text = rebuilt_text

    # Clean up the remaining text, to convert "NE¼ of the NE¼" into "NE¼NE¼" and
    # "SW¼ SW¼" into "SW¼SW¼", by removing extraneous "of the" and whitespace
    # between previously identified aliquots:
    while True:
        aliqIntervener_mo = aliquot_intervener_remover_regex.search(text)
        if aliqIntervener_mo is None:
            # We're out of aliquots to clean up.
            break
        else:
            # i.e. 'N½' in example "N½ of the NE¼":
            part1 = aliqIntervener_mo.group(1)
            # i.e. 'NE¼' in example "N½ of the NE¼":
            part2 = aliqIntervener_mo.group(8)
            text = text.replace(aliqIntervener_mo.group(), part1 + part2)

    return text


def _unpack_aliquots(
        aliquot_text_block, qq_depth_min=2, qq_depth_max=None, qq_depth=None,
        break_halves=False) -> list:
    """
    INTERNAL USE:
    Convert an aliquot with fraction symbols (or 'ALL') into a list of
    clean QQs. Returns a list of QQ's (or smaller, if applicable):
        'N½SW¼NE¼' -> ['N2SWNE']
        'N½SW¼' -> ['NESW', 'NWSW']

    NOTE: Input a single aliquot_text_block (i.e. feed only 'N½SW¼NE¼',
    even if we have a larger list of ['N½SW¼NE¼', 'NW¼'] to process).

    :param aliquot_text_block: A clean string, as generated by the
    `Tract.parse()` method (e.g., 'E½NW¼NE¼' or 'ALL').
    :param qq_depth_min: An int, specifying the minimum depth of the parse.
    Defaults to 2, i.e. to quarter-quarters (e.g., 'N/2NE/4' -> ['NENE',
    'NENE']). Setting to 3 would return 10-acre subdivisions (i.e.
    dividing the 'NENE' into ['NENENE', 'NWNENE', 'SENENE', 'SWNENE']),
    and so forth.
    WARNING: Higher than a few levels of depth will result in very slow
    performance.
    :param qq_depth_max: (Optional) An int, specifying the maximum depth of
    the parse. If set as 2, any subdivision smaller than quarter-quarter
    (e.g., 'NENE') would be discarded -- so, for example, the
    'N/2NE/4NE/4' would simply become the 'NENE'. Must be greater than
    or equal to `qq_depth_min`. (Defaults to None -- i.e. no maximum.)
    :param qq_depth: (Optional) An int, specifying both the min and max
    depth of the parse. If specified, will override both `qq_depth_min`
    and `qq_depth_max`. (Defaults to None -- i.e. use qq_depth_min and
    optionally qq_depth_max.)
    :param break_halves: Whether to break halves into quarters, even
    if we're beyond the qq_depth_min. (False by default.)
    """

    if qq_depth is not None:
        qq_depth_min = qq_depth_max = qq_depth
    
    if qq_depth_max is not None and qq_depth_max < qq_depth_min:
        import warnings
        msg = (
            "If specified, `qq_depth_max` should be greater than or equal to "
            f"`qq_depth_min` (passed as {qq_depth_max} and {qq_depth_min}, "
            "respectively). Using a larger qq_depth_max than qq_depth_min may "
            "result in more QQ's being returned than actually exist in the "
            "Tract."
        )
        warnings.warn(msg)

    # ------------------------------------------------------------------
    # Get a list of the component parts of the aliquot string, and then
    # reverse it -- i.e. 'N½SW¼NE¼' becomes ['NE', 'SW', 'N']

    # Note that group(2) of a `single_aliquot_unpacker_regex` match is
    # the aliquot component without the fraction, and it is at index 1
    # in each tuple within the list returned by `.findall()`
    raw_matches = single_aliquot_unpacker_regex.findall(aliquot_text_block)

    # Unpack the list of tuples into a list of only the aliquot components
    component_list = [aq_tuple[1] for aq_tuple in raw_matches]

    # Reverse, so that the aliquot divisions are in the order of
    # largest-to-smallest.
    component_list.reverse()

    # ------------------------------------------------------------------
    # If no components found, there are no QQ's to _unpack.
    if len(component_list) == 0:
        return component_list

    # ------------------------------------------------------------------
    # Check for any consecutive halves that are on opposite axes.
    # E.g., the N/2E/2 should be converted to the NE/4, but the W/2E/2
    # should be left alone.

    component_list_clean = []
    i = 0
    while i < len(component_list):
        aq1 = component_list[i]
        if i + 1 == len(component_list):
            # Last item.
            component_list_clean.append(aq1)
            break
        aq2 = component_list[i + 1]
        if aq1 in QQ_HALVES and aq2 in QQ_HALVES and aq2 not in QQ_SAME_AXIS[aq1]:
            # e.g., the current component is 'N' and the next component is 'E';
            # those do not exist on the same axis, so we combine them into
            # the 'NE'. (And make sure the N/S direction goes before E/W.)
            new_quarter = f"{aq2}{aq1}" if aq1 in "EW" else f"{aq1}{aq2}"
            component_list_clean.append(new_quarter)
            # Skip over the next component, because we already handled it during
            # this iteration.
            i += 2
        else:
            component_list_clean.append(aq1)
            i += 1
    component_list = component_list_clean

    # ------------------------------------------------------------------
    # Convert the components into aliquot strings

    # (Remember that the component_list is ordered last-to-first
    # vis-a-vis the original aliquot string.)

    # Discard any subdivisions greater than the qq_depth_max, if it was set.
    if qq_depth_max is not None and len(component_list) > qq_depth_max:
        component_list = component_list[:qq_depth_max]

    subdivided_component_list = []
    for i, comp in enumerate(component_list, start=1):
        # Determine how deeply we need to subdivide (i.e. break down) each
        # component, such that we ultimately capture the intended qq_depth_min.

        depth = 0
        if i == qq_depth_min:
            depth = 1
        elif i == len(component_list) and len(component_list) < qq_depth_min:
            depth = qq_depth_min - i + 1
        elif comp in QQ_HALVES and (i < qq_depth_min or break_halves):
            depth = 1
        if comp in QQ_QUARTERS:
            # Quarters (by definition) are already 1 depth more broken down
            # than halves (or 'ALL'), so subtract 1 to account for that
            depth -= 1

        # Subdivide this aliquot component, as deep as needed
        new_comp = _subdivide_aliquot(comp, depth)

        # Append it to our list of components (with subdivisions arranged
        # largest-to-smallest).
        subdivided_component_list.append(new_comp)

    # subdivided_component_list is now in the format:
    #   `[['SE'], ['NW', 'SW'], ['E2']]`
    # ...for E/2W/2SE/4, parsed to a qq_depth_min of 2.

    # Convert the 1-depth nested list into the final QQ list and return.
    return _rebuild_aliquots(subdivided_component_list)


def _rebuild_aliquots(nested_aliquot_list: list):
    """
    INTERNAL USE:

    A shallow-nested (single-depth) list of aliquot components is
    returned as a flattened list of rebuilt aliquots.

    :param nested_aliquot_list: A single-depth nested list of aliquot
    components, arranged by subdivision size, largest to smallest. For
    example:  [['SE'], ['NW', 'SW'], ['E2']]  ...for 'E/2W/2SE/4',
    parsed to a qq_depth_min of 2.
    :return: A clean QQ list, in the format ['E2NWSE', 'E2SWSE'] (or
    smaller strings, if parsed to a less qq_depth_min).
    """
    qq_list = []
    while len(nested_aliquot_list) > 0:
        deepest = nested_aliquot_list.pop(-1)
        if len(nested_aliquot_list) == 0:
            # deepest is our final QQ list
            qq_list = deepest
            break
        second_deepest = nested_aliquot_list.pop(-1)
        rebuilt = []
        for shallow in second_deepest:
            rebuilt.extend(map(lambda deep: f"{deep}{shallow}", deepest))

        nested_aliquot_list.append(rebuilt)

    return qq_list


def _subdivide_aliquot(aliquot_component: str, depth: int):
    """
    INTERNAL USE:

    Subdivide an aliquot into smaller pieces, to the specified `depth`.

    Return examples:

    _subdivide_aliquot('N', 0)
    ->  ['N2']

    _subdivide_aliquot('N', 1)
    ->  ['NE', 'NW']

    _subdivide_aliquot('N', 2)
    ->  ['NENE', 'NWNE', 'SENE', 'SWNE', 'NENW', 'NWNW', 'SENW', 'SWNW']

    _subdivide_aliquot('NE', 1)
    ->  ['NENE', 'NWNE', 'SENE', 'SWNE']

    :param aliquot_component: Any element that appears in the variable
    `QQ_QUARTERS` or as a key in the `QQ_SUBDIVIDE_DEFINITIONS` dict.

    :param depth: How many times to subdivide this aliquot (i.e. halves
    or 'ALL' into quarters, or quarters into deeper quarters). More
    precisely stated, the section will be subdivided into a total number
    of pieces equal to `4^(depth - 1)` -- assuming we're parsing the
    complete section (i.e. 'ALL'). Thus, setting depth greater than 5 or
    so will probably take a long time to process.  NOTE: A depth of 0 or
    less will simply place the aliquot in a list and return it, after
    adding the half designator '2', if appropriate (i.e. 'NE' -> ['NE'],
    but 'E' -> ['E2'] ).

    :return: A list of aliquots, in the format shown above.
    """
    if depth <= 0:
        # We don't actually need to subdivide the aliquot component, so
        # just make sure it is appropriately formatted if it's a half
        # (i.e. 'N' -> 'N2'), then put it in a list and return it.
        if aliquot_component in QQ_HALVES:
            return [aliquot_component + "2"]
        return [aliquot_component]

    # Construct a nested list, which _rebuild_aliquots() requires,
    # which will process it and spit out a flat list before this function
    # returns.
    divided = [[aliquot_component]]
    for _ in range(depth):
        if divided[-1][0] in QQ_SUBDIVIDE_DEFINITIONS.keys():
            # replace halves and 'ALL' with quarters
            comp = divided.pop(-1)[0]
            divided.append(list(QQ_SUBDIVIDE_DEFINITIONS[comp]))
        else:
            divided.append(list(QQ_QUARTERS))

    # The N/2 (passed to this function as 'N') would now be parsed into
    # a format (at a depth of 2):
    #       [['NE', 'NW'], ['NE', 'NW', 'SE', 'SW']]
    # ... which gets reconstructed to:
    #       ['NENE', 'NWNE', 'SENE', 'SWNE', 'NENW', 'NWNW', 'SENW', 'SWNW']
    # ...by `_rebuild_aliquots()`

    return _rebuild_aliquots(divided)


def _unpack_lots(lot_text_block, include_lot_divs=True):
    """
    INTERNAL USE:
    Feed in a string of a lot_regex match object, and return a ParseBag
    object with .lots and .lot_acres attributes for all of the lots --

    ex:  'Lot 1(39.80), 2(30.22)'
        -> ParseBag_obj.lots --> ['L1', 'L2']
        -> ParseBag_obj.lot_acres --> {'L1' : '39.80', 'L2' : '30.22'}
    """

    lotsParseBag = ParseBag(parent_type='lot_text')

    # This will be the output list of Lot numbers [L1, L2, L5, ...]:
    lots = []

    # This will be a dict of stated gross acres for the respective lots,
    # keyed by 'L1', 'L2', etc. It only gets filled for the lots for
    # which gross acreage was specified in parentheses.
    lotsAcresDict = {}

    # A working list of the lots. Note that this gets filled from
    # last-to-first on this working text block. It will be reversed
    # before adding it to the main lots list:
    wLots = []

    # `foundThrough` will switch to True at the start of an elided list
    # (e.g., when we're at '3' in "Lots 3 - 9")
    foundThrough = False
    remainingLotsText = lot_text_block

    while True:
        lots_mo = lot_regex.search(remainingLotsText)

        if lots_mo is None:  # we're out of lot numbers.
            break

        else:
            # We still have at least one lot to _unpack.

            # Pull the right-most lot number (as a string):
            lotNum = _get_last_lot(lots_mo)

            if _is_single_lot(lots_mo):
                # Skip the next loop after we've reached the left-most lot
                remainingLotsText = ''

            else:
                # If we've found at least two lots.
                remainingLotsText = remainingLotsText[:_start_of_last_lot(lots_mo)]

            # Clean up any leading '0's in lotNum.
            lotNum = str(int(lotNum))
            if lotNum == '0':
                lotsParseBag.w_flags.append('Lot0')

            newLot = 'L' + lotNum

            if foundThrough:
                # If we've identified an elided list (e.g., 'Lots 3 - 9')
                prevLot = wLots[-1]
                # Start at lotNum identified earlier this loop:
                start_of_list = int(lotNum)
                # End at last round's lotNum (omit leading 'L'; convert to int):
                end_of_list = int(prevLot[1:])
                correctOrder = True
                if start_of_list >= end_of_list:
                    lotsParseBag.w_flags.append('nonSequen_Lots')
                    lotsParseBag.w_flag_lines.append(
                        ('nonSequen_Lots',
                         f"Lots {start_of_list} - {end_of_list}"))
                    correctOrder = False

                ########################################################
                # start_of_list and end_of_list variable names are
                # unintuitive. Here's an explanation:
                # The 'lots' list is being filled in reverse by this
                # algorithm, starting at the end of the search string
                # and running backwards. Thus, this particular loop,
                # which is attempting to _unpack "Lots 3 - 9", will be
                # fed into the lots list as [L8, L7, L6, L5, L4, L3].
                # (L9 should already be in the list from the previous
                # loop.)
                #
                # 'start_of_list' refers to the original text (i.e. in
                # 'Lots 3 - 9', start_of_list will be 3; end_of_list
                # will be 9).
                ########################################################

                # vars a,b&c are the bounds (a&b) and incrementation (c)
                # of the range() for the lots in the elided list:
                # If the string is correctly 'Lots 3 - 9' (for example),
                # we use the default:
                a, b, c = end_of_list - 1, start_of_list - 1, -1
                # ... but if the string is 'Lots 9 - 3' (i.e. wrong),
                # we use:
                if not correctOrder:
                    a, b, c = end_of_list + 1, start_of_list + 1, 1

                for i in range(a, b, c):
                    # Append each new lot in this range.
                    wLots.append('L' + str(i))
                # Reset the foundThrough.
                foundThrough = False

            else:
                # If it's a standalone lot (not the start of an elided
                # list), we append it
                wLots.append(newLot)

            # If acreage was specified for this lot, clean it up and add
            # to dict, keyed by the newLot.
            newAcres = _get_lot_acres(lots_mo)
            if newAcres is not None:
                lotsAcresDict[newLot] = newAcres

            # If we identified at least two lots, we need to check if
            # the last one is the end of an elided list, by calling
            # _thru_lot() to check for us:
            if _is_multi_lot(lots_mo):
                foundThrough = _thru_lot(lots_mo)

    # Reverse wLots, so that it's in the order it was in the original
    # description, and append it to our main list:
    wLots.reverse()
    lots.extend(wLots)

    if include_lot_divs:
        # If we want include_lot_divs, add it to the front of each parsed lot.
        leadingAliq = _get_leading_aliquot(
            lot_with_aliquot_regex.search(lot_text_block))
        leadingAliq = leadingAliq.replace('¼', '')
        leadingAliq = leadingAliq.replace('½', '2')
        if leadingAliq != '':
            if _first_lot_is_plural(lot_regex.search(lot_text_block)):
                # If the first lot is plural, we apply leadingAliq to
                # all lots in the list
                lots = [f'{leadingAliq} of {lot}' for lot in lots]
            else:
                # If the first lot is NOT plural, apply leadingAliq to
                # ONLY the first lot:
                firstLot = f'{leadingAliq} of {lots.pop(0)}'
                lots.insert(0, firstLot)
            # TODO: This needs to be a bit more robust to handle all real-world
            #   permutations.  For example: 'N/2 of Lot 1 and 2' (meaning
            #   ['N2 of L1', 'N2 of L2']) is possible -- albeit poorly formatted

    lotsParseBag.lots = lots
    lotsParseBag.lot_acres = lotsAcresDict

    return lotsParseBag


########################################################################
# Misc. tools
########################################################################

def flatten(list_or_tuple=None) -> list:
    """
    Unpack the elements in a nested list or tuple into a flattened list.
    """

    if list_or_tuple is None:
        return []

    if not isinstance(list_or_tuple, (list, tuple)):
        return [list_or_tuple]
    else:
        flattened = []
        for element in list_or_tuple:
            if not isinstance(element, (list, tuple)):
                flattened.append(element)
            else:
                flattened.extend(flatten(element))
    return flattened


def break_trs(trs: str) -> tuple:
    """
    Break down a TRS that is already in the format '000n000w00' (or
    fewer digits for twp/rge) into its component parts.
    Returns a 3-tuple containing:
    -- a str for `twp`
    -- a str for `rge`
    -- either a str or None for `sec`

        ex:  '154n97w14' -> ('154n', '97w', '14')
        ex:  '154n97w' -> ('154n', '97w', None)
        ex:  '154n97wsecError' -> ('154n', '97w', 'secError')
        ex:  'TRerr_14' -> ('TRerr', 'TRerr', '14')
        ex:  'asdf' -> ('TRerr', 'TRerr', 'secError')"""

    DEFAULT_ERRORS = ('TRerr', 'TRerr', 'secError',)

    mo = TRS_unpacker_regex.search(trs)
    if mo is None:
        return DEFAULT_ERRORS

    if mo[2] is not None:
        twp = mo[2].lower()
        rge = mo[3].lower()
    else:
        # Pull twp, rge from DEFAULT_ERRORS; discard the val for section error
        twp, rge, _ = DEFAULT_ERRORS

    # mo.group(5) may be a 2-digit numerical string (e.g., '14' from
    # '154n97w14'); or a string 'secError' (from '154n97wsecError'); or
    # None (from '154n97w')
    sec = mo[5]

    return (twp, rge, sec)


########################################################################
# Tools for interpreting lot_regex and lot_with_aliquot_regex match objects:
########################################################################

def _is_multi_lot(lots_mo) -> bool:
    """
    INTERNAL USE:
    Return a bool, whether a lot_regex match object is a multiLot.
    """
    try:
        return (lots_mo.group(11) is not None) and (lots_mo.group(19) is not None)
    except:
        return False


def _thru_lot(lots_mo) -> bool:
    """
    INTERNAL USE:
    Return a bool, whether the word 'through' (or an abbreviation)
    appears before the right-most lot in a lot_regex match object.
    """

    try:
        if _is_multi_lot(lots_mo):
            try:
                thru_mo = through_regex.search(lots_mo.group(15))
            except:
                return False
        else:
            return False

        if thru_mo is None:
            foundThrough = False
        else:
            foundThrough = True

        return foundThrough
    except:
        return False


def _is_single_lot(lots_mo) -> bool:
    """
    INTERNAL USE:
    Return a bool, whether a lot_regex match object is a single lot.
    """
    try:
        return (lots_mo.group(11) is not None) and (lots_mo.group(19) is None)
    except:
        return False


def _get_last_lot(lots_mo):
    """
    INTERNAL USE:
    Extract the right-most lot in a lot_regex match object. Returns a
    string if found; if none found, returns None.
    """
    try:
        if _is_multi_lot(lots_mo):
            return lots_mo.group(19)
        elif _is_single_lot(lots_mo):
            return lots_mo.group(11)
        else:
            return None
    except:
        return None


def _start_of_last_lot(lots_mo) -> int:
    """
    INTERNAL USE:
    Return an int of the starting position of the right-most lot in a
    lot_regex match object. Returns None if none found.
    """
    try:
        if _is_multi_lot(lots_mo):
            return lots_mo.start(19)
        elif _is_single_lot(lots_mo):
            return lots_mo.start(11)
        else:
            return None
    except:
        return None


def _get_lot_acres(lots_mo) -> str:
    """
    INTERNAL USE:
    Return the string of the lot_acres for the right-most lot, without
    parentheses. If no match, then returns None.
    """
    try:
        if _is_multi_lot(lots_mo):
            if lots_mo.group(14) is None:
                return None
            else:
                lotAcres_mo = lotAcres_unpacker_regex.search(lots_mo.group(14))

        elif _is_single_lot(lots_mo):
            if lots_mo.group(12) is None:
                return None
            else:
                lotAcres_mo = lotAcres_unpacker_regex.search(lots_mo.group(12))

        else:
            return None

        if lotAcres_mo is None:
            return None
        else:
            lotAcres_text = lotAcres_mo.group(1)

            # Swap in a period if there was a comma separating:
            lotAcres_text = lotAcres_text.replace(',', '.')
            return lotAcres_text
    except:
        return None


def _first_lot_is_plural(lots_mo) -> bool:
    """
    INTERNAL USE:
    Return a bool, whether the first instance of the word 'lot' in a
    lots_regex match object is pluralized.
    """
    try:
        return lots_mo.group(9).lower() == 'lots'
    except:
        return None


########################################################################
# Tools for interpreting lot_with_aliquot_regex match objects:
########################################################################

def _has_leading_aliquot(mo) -> bool:
    """
    INTERNAL USE:
    Return a bool, whether this lot_with_aliquot_regex match object
    has a leading aliquot. Returns None if no match found.
    """
    try:
        return mo.group(1) is None
    except:
        return None


def _get_leading_aliquot(mo) -> str:
    """
    INTERNAL USE:
    Return the string of the leading aliquot component from a
    lot_with_aliquot_regex match object. Returns None if no match.
    """
    try:
        if mo.group(2) is not None:
            return mo.group(2)
        else:
            return ''
    except:
        return None


def _get_lot_component(mo):
    """
    INTERNAL USE:
    Return the string of the entire lots component from a
    lot_with_aliquot_regex match object. Returns None if no match.
    """
    try:
        if mo.group(7) is not None:
            return mo.group(7)
        else:
            return ''
    except:
        return None


# Tools for extracting data from PLSSDesc and Tract objects

def _clean_attributes(*attributes) -> list:
    """
    INTERNAL USE:
    Ensure that each element has been entered as a string.
    Returns a flattened list of strings.
    """
    attributes = flatten(attributes)

    if len(attributes) == 0:
        return []

    cleanArgList = []
    for att in attributes:
        if not isinstance(att, str):
            raise TypeError(
                'Attributes must be specified as strings (or list of strings).')

        else:
            cleanArgList.append(att)

    return cleanArgList


########################################################################
# Output results to CSV file
########################################################################

def output_to_csv(
        filepath, to_output: list, attributes: list, include_source=True,
        resume=True, include_headers=True, unpack_lists=False):
    """
    Write the requested Tract data to a .csv file. Each Tract will be on
    its own row--with multiple rows per PLSSDesc object, as necessary.

    :param filepath: Path to the output .csv file.
    :param to_output: A list of parsed PLSSDesc, Tract, and/or TractList
    objects.
    :param attributes: A list of the Tract attributes to extract and
    write.  ex: ['trs', 'desc', 'w_flags']
    :param include_source: Whether to include the `.source` attribute of
    each written Tract object as the first column. (Defaults to True)
    :param resume: Whether to overwrite an existing file if found
    (i.e. `resume=False`) or to continue writing at the end of it
    (`resume=True`). Defaults to True.
    NOTE: If no existing file is found, this will create a new file
    regardless of `resume`.
    NOTE ALSO: If resuming a previous output, but with different
    attributes (or differently ordered) than before, the columns will be
    misaligned.
    :param include_headers: Whether to write headers. Defaults to True.
    :param unpack_lists: Whether to try to flatten and join lists, or
    simply write them as they appear. (Defaults to `False`)
    :return: None.
    """

    ACCEPTABLE_TYPES = (PLSSDesc, Tract, TractList)
    ACCEPTABLE_TYPES_PLUS = (PLSSDesc, Tract, TractList, list)

    if filepath[-4:].lower() != '.csv':
        # Attempted filename did not end in '.csv'
        raise ValueError('Error: filename must be .csv file')

    import csv, os

    # If the file already exists and we're not writing a new file, turn
    # off headers
    if os.path.isfile(filepath) and resume:
        include_headers = False

    # Default to opening in `write` mode (create new file). However...
    openMode = 'w'
    # If we don't want to create a new file, will open in `append` mode instead.
    if resume:
        openMode = 'a'

    csvFile = open(filepath, openMode, newline='')
    outputWriter = csv.writer(csvFile)

    if not isinstance(to_output, ACCEPTABLE_TYPES_PLUS):
        # If not the correct type, abort before writing any more.
        raise TypeError(
            f"to_output must be passed as one of: {ACCEPTABLE_TYPES_PLUS}; "
            f"passed as '{type(to_output)}'.")
    to_output = flatten(to_output)

    attributes = flatten(attributes)
    # Ensure the type of each attribute is a str
    attributes = [
        att if isinstance(att, str) else 'Attribute TypeError' for att in attributes
    ]
    if include_source:
        # Mandate the inclusion of attribute 'source', unless overruled
        # with `include_source=False`
        attributes.insert(0, 'source')

    if include_headers:
        # Write the attribute names as headers:
        outputWriter.writerow(attributes)

    for obj in to_output:
        if not isinstance(obj, ACCEPTABLE_TYPES):
            raise TypeError(
                f"Can only write types: {ACCEPTABLE_TYPES}; tried to write "
                f"type '{type(obj)}'.")
        elif isinstance(obj, (PLSSDesc, TractList)):
            # Note that both PLSSDesc and TractList have equivalent
            # `.tracts_to_list()` methods, so both types are handled here
            allTractData = obj.tracts_to_list(attributes)
        else:
            # i.e. `obj` is a `Tract` object.
            # Get the Tract object's attr values in a list, and nest
            # that list as the only element in allTractData list:
            allTractData = [obj.to_list(attributes)]

        for TractData in allTractData:
            dataToWrite = []
            for data in TractData:
                if isinstance(data, (list, tuple)) and unpack_lists:
                    # If this data is a list / tuple, flatten & join its
                    # elements with ',' and then append:
                    try:
                        dataToWrite.append(','.join(flatten(data)))
                    except:
                        # Cannot .join() non-string elements, so handle
                        # with try/except.
                        # TODO: Write a more robust joiner function.
                        dataToWrite.append(data)
                else:
                    # If this data is NOT a list / tuple, just append:
                    dataToWrite.append(data)
            outputWriter.writerow(dataToWrite)

    csvFile.close()


__all__ = [
    PLSSDesc,
    Tract,
    TractList,
    Config,
    IMPLEMENTED_LAYOUTS,
    IMPLEMENTED_LAYOUT_EXAMPLES,
    decompile_twprge,
    break_trs,
    find_twprge,
    find_sec,
    find_multisec,
    output_to_csv
]