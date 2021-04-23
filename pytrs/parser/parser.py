# Copyright (c) 2020-2021, James P. Imes, All rights reserved.

"""
The main parsing package. Primary classes:
> PLSSDesc objects parse PLSS description text (full descriptions) into
    Tract objects (one TRS + description per Tract), stored as TractList
> Tract objects represent the land in a single, unique Twp/Rge/Sec, and
    also parse text into lots and aliquots.
> TRS objects break a Twp/Rge/Sec into its components.
> TractList objects contain a list of Tracts, and can compile that Tract
    data into broadly useful formats (i.e. into list, dict, string), as
    well as custom methods for sorting, grouping, and filtering the
    Tract objects themselves.
> TRSList objects are similar to TractList, but instead hold TRS
    objects.
> Config objects configure parsing parameters for Tract and PLSSDesc.
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


_DEFAULT_COLON = 'default_colon'
_SECOND_PASS = 'second_pass'

_E_FLAG_SECERR = 'SecERROR'
_E_FLAG_TWPRGE_ERR = 'TwpRgeERROR'


def _compile_trs_unpacker_regex(
        twp_rgx, err_twp, undef_twp, rge_rgx, err_rge, undef_rge,
        sec_rgx, err_sec, undef_sec):
    """
    INTERNAL USE:

    Compile the constants for Twp/Rge/Sec into a regex for unpacking
    strings in the pyTRS 'TRS' format.

    :return: A re.Pattern that will match pyTRS 'TRS' strings, including
    undefined and error Twp/Rge/Sections.

    :param twp_rgx: TRS._TWP_RGX
    :param err_twp: TRS._ERR_TWP
    :param undef_twp: TRS._UNDEF_TWP
    :param rge_rgx: TRS._RGE_RGX
    :param err_rge: TRS._ERR_RGE
    :param undef_rge: TRS._UNDEF_RGE
    :param sec_rgx: TRS._SEC_RGX
    :param err_sec: TRS._ERR_SEC
    :param undef_sec: TRS._UNDEF_SEC
    :return: The compiled re.Pattern object.
    """
    # TODO: Check for and handle regex special chars in the various
    #  constants, in case those constants are adjusted by user.
    pattern = (
        rf"(?P<twp>{twp_rgx}"
        rf"|{err_twp}|{undef_twp})"
        rf"(?P<rge>{rge_rgx}"
        rf"|{err_rge}|{undef_rge})"
        rf"(?P<sec>{sec_rgx}"
        rf"|{err_sec}|{undef_sec})?"
    )
    rgx = re.compile(pattern, re.VERBOSE)
    return rgx


class ConfigError(TypeError):
    """
    Wrong type of object was passed to `config=` argument or when
    initializing a Config() object.
    """
    def __init__(self, obj=None):
        msg = "`config` must be a str, None, or a pytrs.Config object."
        if obj is not None:
            msg = f"{msg} Passed type {type(obj)!r}."
        super().__init__(msg)


class DefaultNSError(ValueError):
    """Illegal value for `default_ns`."""
    def __init__(self, obj=None):
        legal = "', '".join(PLSSDesc._LEGAL_NS)
        legal = f"['{legal}']"
        msg = f"`default_ns` must be one of {legal}."
        if obj is not None:
            msg = f"{msg} Passed {obj!r}."
        super().__init__(msg)


class DefaultEWError(ValueError):
    """Illegal value for `default_ew`."""
    def __init__(self, obj=None):
        legal = "', '".join(PLSSDesc._LEGAL_EW)
        legal = f"['{legal}']"
        msg = f"`default_ew` must be one of {legal}."
        if obj is not None:
            msg = f"{msg} Passed {obj!r}."
        super().__init__(msg)


class PLSSDesc:
    """
    Each object of this class is a full PLSS description, taking the raw
    text of the original description as input, and parsing it into one
    or more pytrs.Tract objects (each Tract containing one Twp/Rge/Sec
    combo and the corresponding description of the land within that TRS,
    optionally with lots and quarter-quarters, or QQ's, broken out --
    see pytrs.Tract documentation for more details).

    Configure the parsing algorithm with config parameters at init,
    passed in `config=` (taking either a pytrs.Config object or a string
    containing equivalent config parameters -- see documentation on
    pytrs.Config objects for possible parameters).

    NOTE: If direction for Township (N/S) or Range (E/W) is not provided
    in the text being parsed, it will be assumed. Specify ``default_ns``
    and ``default_ew`` for each ``PLSSDesc`` object to control how these
    should be assumed (as a ``config=`` parameter at init, or as an
    argument in the appropriate method). Alternatively, we can change
    ``PLSSDesc.MASTER_DEFAULT_NS`` and ``PLSSDesc.MASTER_DEFAULT_EW``
    (class variables) to control all unspecified ``default_ns`` and
    ``default_ew`` for (these class variables will control for both
    PLSSDesc and Tract objects). However, specifying ``default_ns`` and
    ``default_ew`` for a given object will override the master defaults
    for that particular object.
    The default settings are for North (`'n'`) and West (`'w'`).
    IMPORTANT: When specifying ``default_ns``, ``default_ew``,
    ``PLSSDesc.MASTER_DEFAULT_NS`` or ``PLSSDesc.MASTER_DEFAULT_EW``, be
    sure to use ONLY single, lower-case letters (``'n'``, ``'s'``,
    ``'e'``, and ``'w'``). Or don't worry about it, and just use
    ``PLSSDesc.NORTH``, ``PLSSDesc.SOUTH``, ``PLSSDesc.EAST``, and
    ``PLSSDesc.WEST``.

    ____ PARSING ____
    Parse the PLSSDesc object into pytrs.Tract objects with the
    `.parse()` method at some point after init. Alternatively, trigger
    the parse at init in one of several ways:
    -- Use init parameter `init_parse=True` (parses the PLSSDesc object
        into Tract objects, which are NOT yet parsed into lots and
        QQ's).
    -- Use init parameter `parse_qq=True` (parses the PLSSDesc object
        into Tract objects, which ARE then immediately parsed into lots
        and QQ's)
    -- Include string 'init_parse' and/or 'parse_qq' among the config
        parameters that are passed in `config=` at init.
    (NOTE: parse_qq entails init_parse, but not vice-versa.)

    ____ IMPORTANT INSTANCE VARIABLES AFTER PARSING ____
    These are the notable attributes of a PLSSDesc object. For the tract
    information (i.e. the data fields you might want to write to a
    spreadsheet or table), look into the attributes of Tract objects
    (which can be created by a PLSSDesc).

    .orig_desc -- The original text. (Gets set from the first positional
        argument at init.)
    .tracts -- A pytrs.TractList object (i.e. a list) containing
        all of the pytrs.Tract objects that were generated from parsing
        this object.
    .pp_desc -- The preprocessed description. (If the object has not yet
        been preprocessed, it will be equivalent to .orig_desc)
    .source -- (Optional) Any value of any type (probably a str or int)
        specifying where the description came from. Useful if parsing
        multiple descriptions and need to internally keep track where
        they came from. (Optionally specify at init with parameter
        `source=<str, int, etc.>`.)
    .w_flags -- a list of warning flags (strings) generated during
        preprocessing and/or parsing.
    .w_flag_lines -- a list of 2-tuples, each being a warning flag and the
        line or context from the description that caused the warning.
    .e_flags -- a list of error flags (strings) generated during
        preprocessing and/or parsing.
    .e_flag_lines -- a list of 2-tuples, each being an error flag and the
        line or context from the description that caused the error.
    .flags -- a combined list of Warning & Error flags.
    .flag_lines -- a combined lines of 2-tuples, for Warning & Error
        flags.
    .desc_is_flawed -- a bool, whether or not an apparently fatal flaw was
        discovered during parsing.
    .layout -- The user-dictated or algorithm-deduced layout of the
        description (controls how the parsing algorithm interprets the
        text).


    ____ STREAMLINED OUTPUT OF THE PARSED TRACT DATA ____
    See the notable instance variables listed in the pytrs.Tract object
    documentation. Those variables can be compiled with these PLSSDesc
    methods:

    .quick_desc() -- Returns a string of the entire parsed description.

    .print_desc() -- Does the same thing, but prints to console.

    .tracts_to_dict() -- Compile the requested attributes for each Tract
        into a dict, and returns a list of those dicts (i.e. the list is
        equal in length to `.tracts` TractList).

    .tracts_to_list() -- Compile the requested attributes for each Tract
        into a list, and returns a nested list of those list (i.e. the
        top-level list is equal in length to `.tracts` TractList).

    .iter_to_dict() -- Identical to `.tracts_to_dict()`, but returns a
        generator of dicts for the Tract data.

    .iter_to_list() -- Identical to `.tracts_to_list()`, but returns a
        generator of lists for the Tract data.

    .tracts_to_csv() -- Compile the requested attributes for each Tract
        and write them to a .csv file, with one row per Tract.

    .tracts_to_str() -- Compile the requested attributes for each Tract
        into a string-based table, and return a single string of all
        tables.

    .list_trs() -- Return a list of all twp/rge/sec combinations in the
        `.tracts` TractList, optionally removing duplicates.

    .print_data() -- Equivalent to `.tracts_to_dict()`, but the data
        is formatted as a table and printed to console.


    ____ SORTING / GROUPING / FILTERING TRACTS BY ATTRIBUTE VALUES ____
    These methods will sort, group, or filter the Tract objects
    contained in the ``.tracts`` attribute:

    .sort_tracts() -- Custom sorting based on the Twp/Rge/Sec or
    original creation order of each Tract. Can also take parameters from
    the built-in ``list.sort()`` method.

    .group() -- Group Tract objects into a dict of TractList objects,
    based on their shared attribute values (e.g., by Twp/Rge), and
    optionally sort them.

    .filter() -- Get a new TractList of Tract objects that match some
    condition, and optionally remove them from the original TractList.

    .filter_errors() -- Get a new TractList of Tract objects whose Twp,
    Rge, and/or Section were an error or undefined, and optionally
    remove them from the original ``.tracts``.
    """

    NORTH = 'n'
    SOUTH = 's'
    EAST = 'e'
    WEST = 'w'

    # Control all unspecified default_ns and default_ew
    MASTER_DEFAULT_NS = NORTH
    MASTER_DEFAULT_EW = WEST

    # Legal settings for N/S/E/W
    _LEGAL_NS = ('n', 's', 'N', 'S')
    _LEGAL_EW = ('e', 'w', 'E', 'W')

    def __init__(
            self,
            raw_plss: str,
            layout=None,
            config=None,
            parse_qq=None,
            source=None,
            wait_to_parse=False):
        """
        A 'raw' PLSS description of land. Will be parsed into one or
        more Tract objects, which are stored in the `.tracts`
        instance variable (a list).

        :param raw_plss: The text of the description to be parsed.
        :param layout: The pyTRS layout. If not specified, will be
        deduced when initialized, and/or when parsed. See available
        options in `pytrs.IMPLEMENTED_LAYOUTS` and examples in
        `pytrs.IMPLEMENTED_LAYOUT_EXAMPLES`.
        :param config: Either a pytrs.Config object, or a string of
        parameters to configure how the PLSSDesc object should be
        parsed. (See documentation on pytrs.Config objects for optional
        config parameters.)
        :param parse_qq: Whether to parse the Tract objects that result
        from parsing this PLSSDesc into lots and QQs.
        NOTE: If `parse_qq` is specified as a kwarg at init, and also
        specified in the `config` (i.e. config='parse_qq'), then the
        kwarg `parse_qq=<bool>` will control.
        :param source: (Optional) Essentially any value (e.g., a unique
        identifier number or document id) specifying where the
        description came from. (Useful if parsing multiple descriptions
        and need to internally keep track where they came from.)
        :param wait_to_parse: A bool, whether to wait to parse at init.
        (Defaults to ``False`` -- i.e., parse at init.)
        """

        # The original input of the PLSS description:
        self.orig_desc = raw_plss

        # If something other than a string is fed in, raise a TypeError
        if not isinstance(raw_plss, str):
            raise TypeError(
                f"`raw_plss` must be of type 'string'. "
                f"Passed as type {type(raw_plss)}.")

        # The source of this PLSS description:
        self.source = source

        # The layout of this PLSS description -- Initially None, but may
        # be set to one of the values in the _IMPLEMENTED_LAYOUTS tuple
        # before __init__() returns, if specified in `config`.
        self.layout = None

        # If a T&R is identified without 'North/South' specified, or without
        # 'East/West' specified, fall back on default_ns and default_ew,
        # respectively. Each will be filled in when `.config` is set
        # (if applicable), or defaulted to 'n' and 'w' soon.
        self.default_ns = None
        self.default_ew = None

        ###############################################################
        # NOTE: the following default bools will be changed when
        # `.config` is set, as applicable.
        ###############################################################

        # Whether we should parse the text at initialization, or wait:
        self.wait_to_parse = None

        # Whether we should parse lots and aliquots in each Tract when
        # it is created.
        self.parse_qq = False

        # Whether tract descriptions are expected to have `clean_qq` (i.e.
        # nothing but clean aliquots and lots, with no typos, exceptions,
        # metes-and-bounds, or other hindrances to the parser.)
        self.clean_qq = False

        # Whether we should require a colon between Section ## and tract
        # description (for TRS_DESC and S_DESC_TR layouts):
        self.require_colon = _DEFAULT_COLON

        # Whether to include any divisions of lots
        # (i.e. 'N/2 of Lot 1' -> 'N2 of L1')
        self.include_lot_divs = True

        # Whether to iron out common OCR artifacts.
        # NOTE: Currently only has effect of cleaning up T&R's during
        # the preprocessing.  May have more effect in a later version.
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
        self.config = config

        # list of Tract objs, after parsing (TractList is a subclass of `list`)
        self.tracts = TractList()
        # list of warning flags
        self.w_flags = []
        # list of 2-tuples that caused warning flags (warning flag, text string)
        self.w_flag_lines = []
        # list of error flags
        self.e_flags = []
        # list of 2-tuples that caused error flags (error flag, text string)
        self.e_flag_lines = []

        # If parse_qq specified as init parameter, it will override
        # `config` parameter.
        #    ex:   config='n,w,parse_qq.False', parse_qq=True   ...
        #       -> WILL set parse_qq to True.
        if parse_qq is not None:
            self.parse_qq = parse_qq

        if wait_to_parse is not None:
            self.wait_to_parse = wait_to_parse

        # Preprocessed description set to .orig_desc until parsed.
        self.pp_desc = self.orig_desc

        # If layout was specified as kwarg, use that:
        self.layout = layout
        # Track whether the layout was dictated by the user.
        self.layout_specified = False
        if self.layout is not None:
            self.layout_specified = True

        # Optionally can run the parse when the object is initialized
        # (on by default).
        if not self.wait_to_parse:
            self.parse(commit=True)
        else:
            self.preprocess(commit=True)

    def __str__(self):
        pt = len(self.tracts)
        return (
            f"PLSSDesc ({'Unparsed' if pt == 0 else 'Parsed'})\n"
            f"Source: {self.source}\n"
            f"Tracts ({'n/a' if pt == 0 else pt}): "
            f"{self.tracts.snapshot_inside()}\n"
            "Original description:\n"
            f"{self.orig_desc}")

    def __getitem__(self, item):
        """
        `PLSSDesc` are LIMITEDLY subscriptable, in that you can ACCESS
        elements (i.e. `pytrs.Tract` objects) of the `.tracts`
        (a `pytrs.TractList`), thus (where `some_plssdesc` is a parsed
        `PLSSDesc` object):
        `some_plssdesc[0]` is the same as
        `some_plssdesc.tracts[0]`

        ...and we can slice, thus:
        `some_plssdesc[:2]` is the same as
        `some_plssdesc.tracts[:2]`

        ...and we can iterate over all its Tract objects:
        `for tract in some_plssdesc: <...>` is the same as
        `for tract in some_plssdesc.tracts: <...>`

        But you CANNOT assign, pop, or insert with a `PLSSDesc`
        directly. If any of that functionality is required, work
        directly with the `.tracts` attribute. Or, get a new
        `pytrs.TractList` to work with, thus:
        `new_tractlist = some_plssdesc.parse(commit=False)`
        (`TractList` is a subclass of the built-in `list`.)
        """
        return self.tracts.__getitem__(item)

    @property
    def config(self):
        return self.__config

    @config.setter
    def config(self, new_config):
        """
        Apply the relevant settings from a Config object to this object;
        takes either a string (i.e. config text) or a Config object.

        :param new_config: Either a pytrs.Config object, or equivalent
        config parameters. (See pytrs.Config documentation for optional
        parameters.)
        """
        if isinstance(new_config, str) or new_config is None:
            new_config = Config(new_config)
        if not isinstance(new_config, Config):
            raise ConfigError(new_config)

        for attrib in Config._PLSSDESC_ATTRIBUTES:
            value = getattr(new_config, attrib)
            if value is not None:
                setattr(self, attrib, value)

        self.__config = new_config

    @property
    def flags(self):
        return self.e_flags + self.w_flags

    @property
    def flag_lines(self):
        return self.e_flag_lines + self.w_flag_lines

    @property
    def desc_is_flawed(self):
        return len(self.e_flags) > 0

    def parse(
            self,
            layout=None,
            default_ns=None,
            default_ew=None,
            clean_up=None,
            parse_qq=None,
            clean_qq=None,
            require_colon=None,
            segment=None,
            ocr_scrub=None,
            commit=True,
            qq_depth_min=None,
            qq_depth_max=None,
            qq_depth=None,
            break_halves=None):
        """
        Parse the description. If parameter ``commit=True`` (default),
        the results will be stored to the various instance
        attributes (``.tracts``, ``.w_flags``, ``.w_flag_lines``,
        ``.e_flags``, and ``.e_flag_lines``). Returns only the
        ``TractList`` object containing the parsed ``Tract`` objects
        (i.e. what would be stored to ``.tracts``).

        NOTE: Any parameters passed here will override the corresponding
        ``.config`` settings, but any unspecified parameters will defer
        to ``.config``.

        :param layout: The layout to be assumed. If not specified,
        defaults to whatever is in `self.layout`; and if not specified
        there, will be automatically deduced.
        :param default_ns: How to interpret townships for which
        direction was not specified -- i.e. either 'n' or 's'. (Defaults
        to `self.default_ns` (if configured) or to
        ``PLSSDesc.MASTER_DEFAULT_NS`` which is 'n' unless otherwise
        configured.)
        :param default_ew: How to interpret ranges for which direction
        was not specified -- i.e. either 'e' or 'w'. (Defaults to
        `self.default_ew` (if configured) or to
        ``PLSSDesc.MASTER_DEFAULT_EW`` which is 'w' unless otherwise
        configured.)
        :param clean_up: Whether to clean up common 'artefacts' from
        parsing. If not specified, defaults to False for parsing the
        'copy_all' layout, and `True` for all others.
        :param parse_qq: Whether to parse each resulting Tract object
        into lots and QQs when initialized. If not specified, defaults
        to whatever is specified in `self.parse_qq` (which is ``True``
        unless otherwise configured).
        :param clean_qq: Whether to expect only clean lots and QQ's (i.e.
        no metes-and-bounds, exceptions, complicated descriptions,
        etc.). Defaults to whatever is specified in `self.clean_qq`
        (which is False, unless configured otherwise).
        :param require_colon: Whether to require a colon between the
        section number and the following description (only has an effect
        on 'TRS_desc' or 'S_desc_TR' layouts).
        If not specified, it will default to whatever was set at init;
        and unless otherwise specified there, will default to a 'two-
        pass' method, where first it will require the colon; and if no
        matching sections are found, it will do a second pass where
        colons are not required. Setting as `True` or `False` here
        prevent the two-pass method.
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
        :param ocr_scrub: Whether to try to iron out common OCR
        'artifacts'. May cause unintended changes. (Defaults to
        `.ocr_scrub` attribute, which is `False` unless otherwise
        configured.)
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
        :return: Returns a ``pytrs.TractList`` object (a subclass of
        built-in ``list``) of all of the resulting ``pytrs.Tract``
        objects.
        """

        # --------------------------------------------------------------
        # Note that this method is actually a wrapper for initializing
        # a PLSSParser object and extracting the relevant attributes
        # from that. User-facing documentation for that class is
        # maintained here.
        # --------------------------------------------------------------

        # ----------------------------------------
        # Lock down parameters for this parse.

        if require_colon is None:
            require_colon = self.require_colon

        if not default_ns:
            default_ns = self.default_ns

        if not default_ew:
            default_ew = self.default_ew

        if ocr_scrub is None:
            ocr_scrub = self.ocr_scrub

        # NOTE: If layout was specified at init or when calling
        # `.parse(layout=<string>)`, PLSSParser._parse_segment() will be
        # prevented from from deducing it.  Leave as None to allow the
        # parser to deduce.

        if parse_qq is None:
            parse_qq = self.parse_qq

        if clean_qq is None:
            clean_qq = self.clean_qq

        # Config object for passing down to Tract objects.
        handed_down_config = self.config.decompile_to_text()

        if segment is None:
            segment = self.segment

        if layout == COPY_ALL:
            # If a *segment* (which will be divided up shortly) finds
            # itself in the COPY_ALL layout, that should still parse
            # fine. But segmenting the whole description would defy the
            # point of COPY_ALL layout. So prevent `segment` when the
            # OVERALL layout is COPY_ALL.
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

        # Parameters for `PLSSParser.parse()`.
        config_params = {
            "default_ns": default_ns,
            "default_ew": default_ew,
            "ocr_scrub": ocr_scrub,
            "clean_up": clean_up,
            "parse_qq": parse_qq,
            "clean_qq": clean_qq,
            "require_colon": require_colon,
            "segment": segment,
            "qq_depth_min": qq_depth_min,
            "qq_depth_max": qq_depth_max,
            "qq_depth": qq_depth,
            "break_halves": break_halves,
            "handed_down_config": handed_down_config,
        }

        # ----------------------------------------
        # Parse it.

        parser = PLSSParser(
            text=self.orig_desc,
            mandated_layout=layout,
            parent=self,
            **config_params
        )

        if commit:
            # Wipe the existing tracts, etc., if any.
            self.tracts = TractList()
            self.w_flags = []
            self.e_flags = []
            self.w_flag_lines = []
            self.e_flag_lines = []

            # Unpack each of the 'unpackable' attributes.
            for attribute in parser.UNPACKABLES:
                setattr(self, attribute, getattr(parser, attribute))

            # The resulting `.text` in the parser is the preprocessed
            # description.
            self.pp_desc = parser.text

        return parser.tracts

    def config_tracts(self, config):
        """
        Reconfigure all of the Tract objects in ``.tracts``
        (without reconfiguring this PLSSDesc object).

        :param config: Either a pytrs.Config object, or a string of
        parameters to configure how the Tract object should be parsed.
        (See documentation on pytrs.Config objects for optional config
        parameters.)
        :return: None
        """
        return self.tracts.config_tracts(config)

    def parse_tracts(
            self,
            config=None,
            clean_qq=None,
            include_lot_divs=None,
            qq_depth_min=None,
            qq_depth_max=None,
            qq_depth=None,
            break_halves=None):
        """
        Parse (or re-parse) all of the Tract objects in
        ``.tracts`` into lots/QQ's using the specified
        parameters. Will NOT pull from this PLSSDesc object's
        ``.config`` or other attributes, but WILL pull from each Tract
        object's own ``.config`` (unless otherwise configured here).
        Optionally reconfigure each Tract object prior to parsing into
        lots/QQs by using the ``config=`` parameter here, or other
        kwargs.  (The named kwargs will take priority over ``config``,
        if there is a conflict.)

        The parsed data will be committed to the Tract objects'
        attributes, overwriting data from a prior parse.

        :param config: (Optional) New Config parameters to apply to each
        Tract before parsing. (If there is a conflict
        :param clean_qq: Same as in ``Tract.parse()`` method.
        :param include_lot_divs: Same as in ``Tract.parse()`` method.
        :param qq_depth_min: Same as in ``Tract.parse()`` method.
        :param qq_depth_max: Same as in ``Tract.parse()`` method.
        :param qq_depth: Same as in ``Tract.parse()`` method.
        :param break_halves: Same as in ``Tract.parse()`` method.
        :return: None
        """
        return self.tracts.parse_tracts(
                config=config,
                clean_qq=clean_qq,
                include_lot_divs=include_lot_divs,
                qq_depth_min=qq_depth_min,
                qq_depth_max=qq_depth_max,
                qq_depth=qq_depth,
                break_halves=break_halves)

    def deduce_layout(self, candidates=None):
        """
        Deduce the layout of the description.

        :param candidates: A list of which layouts are to be considered.
        If passed as `None` (the default), it will consider all
        currently implemented meaningful layouts (i.e. 'TRS_desc',
        'desc_STR', 'S_desc_TR', and 'TR_desc_S'), but will also
        consider 'copy_all' if an apparently flawed description is
        found. If specifying fewer than all candidates, ensure that at
        least one layout from _IMPLEMENTED_LAYOUTS is in the list.
        (Strings not in _IMPLEMENTED_LAYOUTS will have no effect.)
        :return: Returns the algorithm's best guess at the layout (i.e.
        a string).
        """
        text = PLSSPreprocessor(self.orig_desc, ocr_scrub=self.ocr_scrub)
        return PLSSParser.deduce_layout(text, candidates=candidates)

    def preprocess(
            self, default_ns=None, default_ew=None, commit=False,
            ocr_scrub=None) -> str:
        """
        Preprocess the PLSS description to iron out common kinks in
        the input data, and optionally store the results to the
        ``.pp_desc`` attribute.

        NOTE: Regardless whether committed, the description will be
        preprocessed (again) when parsed.

        :param default_ns: How to interpret townships for which direction
        was not specified -- i.e. either 'n' or 's'. (Defaults to
        `self.default_ns`, which is 'n' unless otherwise configured.)
        :param default_ew: How to interpret ranges for which direction
        was not specified -- i.e. either 'e' or 'w'. (Defaults to
        `self.default_ew`, which is 'w' unless otherwise configured.)
        :param ocr_scrub: Whether to try to iron out common OCR
        'artifacts'. May cause unintended changes. (Defaults to
        `self.ocr_scrub`, which is `False` unless otherwise configured.)
        :param commit: Whether to store the results to ``.pp_desc``.
        (Defaults to `False`)
        :return: The preprocessed string.
        """
        # Defaults to pulling the text from the orig_desc of the object:
        text = self.orig_desc
        if default_ns is None:
            default_ns = self.default_ns
        if default_ew is None:
            default_ew = self.default_ew
        if ocr_scrub is None:
            ocr_scrub = self.ocr_scrub
        pp_desc = PLSSPreprocessor.static_preprocess(
            text, default_ns, default_ew, ocr_scrub)
        if commit:
            self.pp_desc = pp_desc
        return pp_desc

    def tracts_to_dict(self, *attributes) -> list:
        """
        Compile the data for each Tract object in .tracts into a
        dict containing the requested attributes only, and return a list
        of those dicts (the returned list being equal in length to
        .tracts).

        :param attributes: The names (strings) of whichever attributes
        should be included (see documentation on `pytrs.Tract` objects
        for the names of relevant attributes).

        :Example:

        txt = '''154N-97W
        Sec 14: NE/4
        Sec 15: Northwest Quarter, North Half South West Quarter'''
        d_obj = pytrs.PLSSDesc(txt, parse_qq=True)
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
        return self.tracts.tracts_to_dict(attributes)

    def tracts_to_list(self, *attributes) -> list:
        """
        Compile the data for each Tract object in .tracts into a
        list containing the requested attributes only, and return a
        nested list of those lists (the returned list being equal in
        length to .tracts).

        :param attributes: The names (strings) of whichever attributes
        should be included (see documentation on `pytrs.Tract` objects
        for the names of relevant attributes).

        :Example:

        txt = '''154N-97W
        Sec 14: NE/4
        Sec 15: Northwest Quarter, North Half South West Quarter'''
        d_obj = pytrs.PLSSDesc(txt, parse_qq=True)
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
        return self.tracts.tracts_to_list(attributes)

    def iter_to_dict(self, *attributes):
        """
        Identical to `.tracts_to_dict()`, but returns a generator of
        dicts, rather than a list of dicts.

        :param attributes: The names (strings) of whichever attributes
        should be included (see documentation on `pytrs.Tract` objects
        for the names of relevant attributes).

        :return: A generator of data pulled from each Tract, in the form
        of a dict.
        """
        return self.tracts.iter_to_dict(attributes)

    def iter_to_list(self, *attributes):
        """
        Identical to `.tracts_to_dict()`, but returns a generator of
        lists, rather than a list of lists.

        :param attributes: The names (strings) of whichever attributes
        should be included (see documentation on `pytrs.Tract` objects
        for the names of relevant attributes).

        :return: A generator of data pulled from each Tract, in the form
        of a list.
        """
        return self.tracts.iter_to_list(attributes)

    def tracts_to_str(self, *attributes) -> str:
        """
        Compile the data for all Tract objects in .tracts,
        containing the requested attributes only, and return a single
        string of the data.

        :param attributes: The names (strings) of whichever attributes
        should be included (see documentation on `pytrs.Tract` objects
        for the names of relevant attributes).

        :Example:

        txt = '''154N-97W
        Sec 14: NE/4
        Sec 15: Northwest Quarter, North Half South West Quarter'''
        d_obj = pytrs.PLSSDesc(txt, parse_qq=True)
        d_obj.tracts_to_str('trs', 'desc', 'qqs')

        Example returns a multi-line string that looks like this when
        printed:

            Tract 1 / 2
            trs  : 154n97w14
            desc : NE/4
            qqs  : NENE, NWNE, SENE, SWNE

            Tract 2 / 2
            trs  : 154n97w15
            desc : Northwest Quarter, North Half South West Quarter
            qqs  : NENW, NWNW, SENW, SWNW, NESW, NWSW
        """
        # This functionality is handled by TractList method.
        return self.tracts.tracts_to_str(attributes)

    def tracts_to_csv(
            self, attributes, fp, mode, nice_headers=False):
        """
        Write Tract data to a .csv file.

        :param attributes: a list of names (strings) of whichever
        attributes should be included (see documentation on
        `pytrs.Tract` objects for the names of relevant attributes).
        :param fp: The filepath of the .csv file to write to.
        :param mode: The `mode` in which to open the file we're
        writing to. Either 'w' (new file) or 'a' (continue a file).
        :param nice_headers: By default, this method will use the
        attribute names as headers. To use custom headers, pass to
        ``nice_headers=`` any of the following:
        -- a list of strings to use. (Should be equal in length to the
        list passed as ``attributes``, but will not raise an error if
        that's not the case. The resulting column headers will just be
        fewer than the actual number of columns.)
        -- a dict, keyed by attribute name, and whose values are the
        corresponding headers. (Any missing keys will use the attribute
        name.)
        -- `True` -> use the values in the ``Tract.ATTRIBUTES`` dict for
        headers. (WARNING: Any value passed that is not a list or dict
        and that evaluates to `True` will cause this behavior.)
        -- If not specified (i.e. None), will just use the attribute
        names themselves.
        :return: None
        """
        self.tracts.tracts_to_csv(
            attributes, fp, mode, nice_headers)

    def quick_desc(self, delim=': ', newline='\n') -> str:
        """
        Returns the entire .tracts list as a single string.
        :param delim: Specify what separates TRS from the desc.
        (defaults to ': ').
        :param newline: Specify what separates Tracts from one another.
        (defaults to '\n').

        :Example:

        txt = '''154N-97W
        Sec 14: NE/4
        Sec 15: Northwest Quarter, North Half South West Quarter'''
        d_obj = pytrs.PLSSDesc(txt)
        d_obj.quick_desc()

        Example returns a multi-line string that looks like this when
        printed:

            154n97w14: NE/4
            154n97w15: Northwest Quarter, North Half South West Quarter
        """
        # This functionality is handled by TractList method.
        return self.tracts.quick_desc(delim=delim, newline=newline)

    def quick_desc_short(self, delim=': ', newline='\n', max_len=30) -> str:
        """
        Returns the description (`.trs` + `.desc`) of all Tract objects
        in `.tracts` as a single string, but trims every line down
        to `max_len`, if needed.
        :param delim: Specify what separates TRS from the desc.
        (defaults to ': ').
        :param newline: Specify what separates Tracts from one another.
        (defaults to '\n').
        :param max_len: Maximum length of each string inside the list.
        (Defaults to 30.)
        :return: A string of the complete description.
        """
        return self.tracts.quick_desc_short(delim, newline, max_len)

    def list_trs(self, remove_duplicates=False):
        """
        Return a list all the TRS's in .tracts list. Optionally
        remove duplicates with remove_duplicates=True.
        """
        # This functionality is handled by TractList method.
        return self.tracts.list_trs(remove_duplicates=remove_duplicates)

    def print_desc(self, delim=': ', newline='\n') -> None:
        """
        Simple printing of the parsed description.

        :param delim: Specify what separates TRS from the desc.
        (defaults to ': ').
        :param newline: Specify what separates Tracts from one another.
        (defaults to '\n').
        """
        # This functionality is handled by TractList method.
        self.tracts.print_desc(delim=delim, newline=newline)

    def pretty_desc(self, word_sec='Sec ', justify_linebreaks=None):
        """
        Get a neatened-up description of all of the Tract objects in
        ``.tracts``. (Does not access this PLSSDesc object's
        description. Instead, compiles a cleaned-up description from the
        Tract objects.)

        Groups Tracts by Twp/Rge, but only to the extent possible while
        maintaining the current sort order.

        :param word_sec: How the word 'Section' should appear, INCLUDING
        the following white space (if any). (Defaults to ``'Sec '``).
        :param justify_linebreaks: (Optional) A string specifying how to
        justify new lines after a linebreak (e.g., ``'\t'`` for a tab).
        If not specified, will align new lines with the line above. To
        use no justification at all, pass an empty string.
        :return: a str of the compiled description.
        """
        return self.tracts.pretty_desc(word_sec, justify_linebreaks)

    def pretty_print_desc(self, word_sec='Sec ', justify_linebreaks=None):
        """
        Print a neatened-up description of all of the Tract objects in
        ``.tracts``. (Does not access this PLSSDesc object's
        description. Instead, compiles a cleaned-up description from the
        Tract objects.)

        Groups Tracts by Twp/Rge, but only to the extent possible while
        maintaining the current sort order.

        :param word_sec: How the word 'Section' should appear, INCLUDING
        the following white space (if any). (Defaults to ``'Sec '``).
        :param justify_linebreaks: (Optional) A string specifying how to
        justify new lines after a linebreak (e.g., ``'\t'`` for a tab).
        If not specified, will align new lines with the line above. To
        use no justification at all, pass an empty string.
        :return: None (prints to console).
        """
        self.tracts.pretty_print_desc(word_sec, justify_linebreaks)

    def print_data(self, *attributes) -> None:
        """
        Simple printing of the arg-specified attributes for each Tract
        in the .tracts list.
        """
        # This functionality is handled by TractList method.
        self.tracts.print_data(attributes)
        return

    def sort_tracts(self, key: str = 'i,s,r,t'):
        """
        Sort the Tract objects stored in the ``.parse_tracts``
        attributes, in-situ.

        key options:

        'i' -> 'i' -> Sort by the original order they were created.

        't' -> Sort by Township.
               'num'    --> Sort by raw number, ignoring N/S. (default)
               'ns'     --> Sort from north-to-south
               'sn'     --> Sort from south-to-north

        'r' -> Sort by Range.
               'num'    --> Sort by raw number, ignoring E/W. (default)
               'ew'     --> Sort from east-to-west **
               'we'     --> Sort from west-to-east **
                (** NOTE: These do not account for Principal Meridians.)

        's' -> Sort by Section number.

        Reverse any or all of the keys by adding '.reverse' (or '.rev')
        at the end of it.

        Use as many sort keys as you want. They will be applied in order
        from left-to-right, so place the highest 'priority' sort last.

        Construct all keys as a single string, separated by comma
        (spaces are optional). The components of each key should be
        separated by a period.

        Example keys:

            's.reverse,r.ew,t.ns'
                ->  Sort by section number (reversed, so largest-to-
                        smallest);
                    then sort by Range (east-to-west);
                    then sort by Township (north-to-south)

            'i,s,r,t'  (this is the default)
                ->  Sort by original creation order;
                    then sort by Section (smallest-to-largest);
                    then sort by Range (smallest-to-largest);
                    then sort by Township (smallest-to-largest)

            'i'
                -> Return to the original order as parsed in this
                    PLSSDesc object.

        :param key: A str, specifying which sort(s) should be done.
        :return: None. (TractList is sorted in-situ.)
        """
        # This functionality is handled by TractList method.
        self.tracts.sort_tracts(key=key)
        return None

    def group_nested(
            self, by_attribute="twprge", into=None, sort_key=None,
            sort_reverse=False):
        """
        Filter the Tract objects in the ``.tracts`` into a dict
        of TractLists, keyed by unique values of `by_attribute`. By
        default, will filter into groups of Tracts that share Twp/Rge
        (i.e. `'twprge'`).

        :param by_attribute: The str name of an attribute of Tract
        objects. (Defaults to `'twprge'`). NOTE: Must be a hashable
        type!

        :param into: (Optional) An existing dict into which to group
        the Tracts. If not specified, will create a new dict. Use this
        arg if you need to continue adding Tracts to an existing
        grouped dict.

        :param sort_key: (Optional) How to sort each grouped TractList
        in the returned dict. Use a string that works with the
        ``.sort_tracts(key=<str>)`` method (e.g., 'i, s, r.ew, t.ns') or
        a lambda function, as you would with the builtin
        ``list.sort(key=<lambda>)`` method. (Defaults to ``None``, i.e.
        not sorted.)

        May optionally pass `sort_key` as a list of sort keys, to be
        applied left-to-right. Here, you may mix and match lambdas and
        ``.sort_tracts()`` strings.

        :param sort_reverse: (Optional) Whether to reverse the sort.
        NOTE: Only has an effect if the ``sort_key`` is passed as a
        lambda -- NOT as a custom string sort key. Defaults to ``False``

        NOTE: If ``sort_key`` was passed as a list, then
        ``sort_reverse`` must be passed as EITHER a single bool that
        will apply to all of the (non-string) sorts, OR as a list or
        tuple of bools that is equal in length to ``sort_key`` (i.e. the
        values in ``sort_key`` and ``sort_reverse`` will be matched up
        one-to-one).

        :return: A dict of TractList objects, each containing the Tracts
        with matching values of the `by_attribute`.
        """
        return self.tracts.group_nested(by_attribute, into, sort_key, sort_reverse)

    def group(
            self, by_attribute="twprge", into=None, sort_key=None,
            sort_reverse=False):
        """
        Filter the Tract objects in ``.tracts`` into a dict of
        TractLists, keyed by unique values of ``by_attribute``. By
        default, will filter into groups of Tracts that share Twp/Rge
        (i.e. ``'twprge'``). Pass ``by_attribute`` as a list of
        attributes to group by multiple attributes, in which case the
        keys of the returned dict will be a tuple whose elements line up
        with the attributes listed in ``by_attribute``.

        :param by_attribute: The str name of an attribute of Tract
        objects. (Defaults to ``'twprge'``). NOTE: Attributes must be a
        hashable type!  (Optionally pass as a list of str names of
        attributes to do multiple groupings.)

        :param into: (Optional) An existing dict into which to group the
        Tracts. If not specified, will create a new dict. Use this arg if
        you need to continue adding Tracts to an existing grouped dict.

        :param sort_key: (Optional) How to sort each grouped TractList
        in the returned dict. Use a string that works with the
        ``.sort_tracts(key=<str>)`` method (e.g., 'i, s, r.ew, t.ns') or
        a lambda function, as you would with the builtin
        ``list.sort(key=<lambda>)`` method. (Defaults to ``None``, i.e.
        not sorted.)

        May optionally pass `sort_key` as a list of sort keys, to be
        applied left-to-right. Here, you may mix and match lambdas and
        ``.sort_tracts()`` strings.

        :param sort_reverse: (Optional) Whether to reverse the sort.
        NOTE: Only has an effect if the ``sort_key`` is passed as a
        lambda -- NOT as a custom string sort key. Defaults to ``False``

        NOTE: If ``sort_key`` was passed as a list, then
        ``sort_reverse`` must be passed as EITHER a single bool that
        will apply to all of the (non-string) sorts, OR as a list or
        tuple of bools that is equal in length to ``sort_key`` (i.e. the
        values in ``sort_key`` and ``sort_reverse`` will be matched up
        one-to-one).

        :return: A dict of TractList objects, each containing the Tracts
        with matching values of the ``by_attribute``.  (If
        ``by_attribute`` was passed as a list of attribute names, then
        the keys in the returned dict will be a tuple whose values
        line up with the list passed as ``by_attribute``.)
        """
        return self.tracts.group(by_attribute, into, sort_key, sort_reverse)

    # Alias to mirror `sort_tracts`.
    group_tracts = group

    def filter(self, key, drop=False):
        """
        Extract from ``.tracts`` all Tract objects that match the
        `key` (a lambda function that returns a bool or bool-like
        value when applied to each Tract object).

        Returns a new TractList of all of the selected Tract objects.

        :param key: a lambda function that returns a bool or bool-like
        value when applied to a Tract object in ``.tracts``.
        (True or True-like returned values will result in the inclusion
        of that Tract).
        :param drop: Whether to drop the matching Tracts from the
        original ``.tracts``. (Defaults to ``False``)
        :return: A new TractList of the selected Tract objects. (The
        original ``.tracts`` will still hold all other Tract
        objects, unless ``drop=True`` was passed.)
        """
        return self.tracts.filter(key, drop)

    # Alias to mirror `sort_tracts`.
    filter_tracts = filter

    def filter_errors(self, twp=True, rge=True, sec=True, undef=False, drop=False):
        """
        Extract from ``.tracts`` all Tract objects that were
        parsed with an error. Specifically extract Twp/Rge errors with
        ``twp=True`` and ``rge=True``; and get Sec errors with
        ``sec=True`` (all of which are on by default).

        Returns a new TractList of all of the selected Tract objects.

        :param twp: a bool, whether to get Twp errors. (Defaults to
        ``True``)
        :param rge: a bool, whether to get Rge errors. (Defaults to
        ``True``)
        :param sec: a bool, whether to get Sec errors. (Defaults to
        ``True``)
        :param undef: a bool, whether to get consider Twps, Rges, or
        Sections that were UNDEFINED to also be errors. (Defaults to
        ``False``)  (NOTE: Undefined Twp/Rge/Sec will never occur in a
        ``PLSSDesc`` object unless a ``Tract`` was manually appended to
        the ``.tracts`` attribute.)
        :param drop: Whether to drop the selected Tracts from the
        original ``.tracts``. (Defaults to ``False``)
        :return: A new TractList containing all of the selected Tract
        objects.
        """
        return self.tracts.filter_errors(twp, rge, sec, undef, drop)

    # Alias to mirror `sort_tracts`
    filter_error_tracts = filter_errors

    def filter_duplicates(self, method='instance', drop=False):
        """
        Find the duplicate Tracts in ``.tracts``, get a new
        TractList of those Tract objects that were duplicates, and
        optionally `drop` the duplicates from the original TractList.
        (To be clear, if there are THREE identical Tracts in the
        ``.tracts``, the returned ``TractList`` will contain only
        TWO Tracts, and the original ``.tracts`` will still have
        one.)

        Control how to assess whether `Tract` objects are duplicates by
        ONE of the following methods:

        `method='instance'` (the default) -> Whether two objects are
        actually the same instance -- i.e. literally the same object.
        (By definition, this will also apply even if one of the other
        two methods is used.)  (This should never happen in a
        ``PLSSDesc`` object, unless a Tract was manually appended to
        ``.tracts``.)

        `method='lots_qqs'`  -> Whether the `.lots_qqs` attribute
        contains the same lots/aliquots (after removing duplicates
        there).  NOTE: Lots/aliquots must have been parsed for a given
        Tract object, or it will NOT match as a duplicate with this
        parameter.
                Ex: Will match these as duplicate tracts, assuming they
                were parsed with identical `config` settings:
                    `154n97w14: Lots 1 - 3, S/2NE/4`
                    `154n97w14: Lot 3, S/2NE/4, Lots 1, 2`

        `method='desc'` -> Whether the `.trs` and `.pp_desc` (i.e.
        preprocessed description) combine to form an identical tract.
                Ex: Will match these as duplicate tracts:
                    `154n97w14: NE/4`
                    `154n97w14: Northeast Quarter`

        :param method: Specify how to assess whether Tract objects are
        duplicates (either 'instance', 'lots_qqs', or 'desc'). See above
        for example behavior of each.
        :param drop: Whether to remove the identified duplicates from
        the original list.
        :return: A new TractList.
        """
        return self.tracts.filter_duplicates(method, drop)

    # Alias to mirror `sort_tracts`
    filter_duplicate_tracts = filter_duplicates


class Tract:
    """
    Each object of this class is a discrete tract of land, limited to
    one Twp/Rge/Sec combination (often shorted to 'TRS' in this module)
    and the description of the land within that TRS, which optionally
    can be parsed into aliquot quarter-quarters (called QQ's) and lots.

    Configure the parsing algorithm with config parameters at init,
    passed in `config=` (taking either a pytrs.Config object or a string
    containing equivalent config parameters -- see documentation on
    Config objects for possible parameters).

    ____ PARSING ____
    Parse the text into lots/QQs with the `.parse()` method at some
    point after init. Alternatively, trigger the parse at init in one of
    two ways:
    -- Use init parameter `parse_qq=True`
    -- Include 'parse_qq' in the config parameters that are passed in
        `config=` at init.

    ____ IMPORTANT INSTANCE VARIABLES & PROPERTIES AFTER PARSING ____
    .trs -- The Twp/Rge/Sec combination in the standard pyTRS format.
            Ex: Sec 1, T154N-R97W -> '154n97w01'
                Sec 14, T1S-R9E -> '1s9e14'
    NOTE: If there was a flawed parse where Twp/Rge and/or Sec could not
        be successfully identified, ``.trs`` may contain 'XXXzXXXz' (for
        Twp/Rge) and/or 'XX' (for Section) -- i.e. 'XXXzXXXzXX' for the
        entire Twp/Rge/Sec. Similarly, Tract objects created without
        specifying any Twp/Rge/Sec would appear as '___z___z__'.
    NOTE ALSO: Setting a Tract object's ``.trs`` attribute at any time
        (using the standard pyTRS format, e.g., '154n97w14' or '1s9e01')
        will populate all of the corresponding properties (``.twp``,
        ``.rge``, etc.). Alternatively, when the Twp/Rge/Sec components
        have not yet been compiled into the pyTRS format, you can set it
        with the ``.set_twprgesec()`` method.
    .twp -- The Twp portion of .trs, a string (ex: '154n')
    .twp_num -- The Twp portion of .trs, as an int or None (ex: 154)
    .twp_ns -- The N/S portion of .trs, as a str or None (ex: 'n')
    .rge -- The Rge portion of .trs, a string (ex: '97w')
    .rge_num -- The Rge portion of .trs, as an int or None (ex: 97)
    .rge_ew -- The E/W portion of .trs, as a str or None (ex: 'w')
    .twprge -- The Twp/Rge portion of .trs, a string (ex: '154n97w')
    .sec -- The Sec portion of .trs, a string (ex: '01')
    .sec_num -- The Sec portion of .trs, as an int or None (ex: 1)
    .desc -- The description block within this TRS.
    .qqs -- A list of identified QQ's (or smaller) formatted as 4
    characters (or more, if there are further divisions).
        Ex:     Northeast Quarter -> ['NENE', 'NWNE', 'NENW', 'NWNW']
        Ex:     N/2SE/4SE/4 -> ['N2SESE']
    .lots -- A list of identified lots.
        Ex:     Lot 1, North Half of Lot 2 -> ['L1', 'N2 of L2']
        NOTE: Divisions of lots can be suppressed with config parameter
            'include_lot_divs.False' (i.e. ['L1', 'L2'] in this example).
    .ilots -- The identified lots as a list of integers, with any
        divisions discared.
    .lots_qqs -- A joined list of identified lots and QQ's. (Technically
        a property)
        Ex:     ['L1', 'N2 of L2', 'NENE', 'NWNE', 'NENW', 'NWNW']
    .lot_acres -- A dict of lot names and their apparent gross acreages,
    as stated in the original description.
        Ex:     Lots 1(38.29), 2(39.22), 3(39.78)
                    -> {'L1': '38.29', 'L2':'39.22', 'L3':'39.78'}
    .pp_desc -- The preprocessed description. (If the object has not yet
        been parsed, it will be equivalent to .desc)
    .source -- (Optional) Any value of any type (probably a str or int)
        specifying where the description came from. Useful if parsing
        multiple descriptions and need to internally keep track where
        they came from. (Optionally specify at init with parameter
        `source=<str, int, etc.>`.)
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
    .flags -- a combined list of warning and error flags. (Technically a
        property)
    .flag_lines -- a combined list of warning and error flag_lines.
        (Technically a property)
    .desc_is_flawed -- a bool, whether or not an apparently fatal flaw was
        discovered during parsing of the parent PLSSDesc object, if any.
        (Tract objects themselves are agnostic to fatal flaws.)

    ____ STREAMLINED OUTPUT OF THE PARSED DATA ____
    The instance variables above can be compiled with these methods:
    .quick_desc() -- Returns a string of the TRS + description.
    .to_dict() -- Compile the requested attributes into a dict.
    .to_list() -- Compile the requested attributes into a list.

    ____ SETTING TOWNSHIP / RANGE / SECTION ____
    Twp/Rge/Sec will be set automatically if a Tract is created by a
    parsed PLSSDesc. However, it can also be manually set in one of four
    ways.

    At init, in the ``trs=`` kwarg (taking the standard pyTRS format):
        Ex: ``some_tract = Tract(desc='NE/4', trs='154n97w14')

    At init, but using Twp/Rge/Sec components, using the
    ``.from_twprgesec()`` method:
        Ex:
            ```
            some_tract = Tract.from_twprgesec(
                desc='NE/4', twp=154, rge=97, sec=14, default_ns='n',
                default_ew='w')
            ```

    Once the Tract has already been created, we can set the Twp/Rge/Sec
    by assigning the ``.trs`` attribute a string value in the standard
    pyTRS format.
        Ex: ``some_tract.trs = '154n97w14'``
            ``some_tract.trs = '1s87e01'``

    Alternatively, set Twp/Rge/Sec from the uncompiled components, with
    the ``.set_twprgesec()`` method:
        Ex:
            ```
            some_tract.set_twprgesec(
                154, 97, 14, default_ns='n', default_ew='w')
            ```

    Setting Twp/Rge/Sec by any of the above methods will break down the
    Twp/Rge/Sec into various data:
            .trs        -> The full Twp/Rge/Sec combination.
            .twp        -> Twp number + direction (a str or None)
            .twp_num    -> Twp number (an int or None)
            .twp_ns     -> Twp direction ('n', 's', or None)
            .ns         -> same as `.twp_ns`
            .twp_undef  -> whether the Twp was undefined. **
            .rge        -> Rge number + direction (a str or None)
            .rge_num    -> Rge num (an int or None)
            .rge_ew     -> Rge direction ('e', 'w', or None)
            .ew         -> same as `.rge_ew`
            .rge_undef  -> whether the Rge was undefined. **
            .sec_num    -> Sec number (an int or None)
            .sec_undef  -> whether the Sec was undefined. **

    ** Note that error parses do NOT qualify as 'undefined', but
    undefined and error values are both stored as None. 'twp_undef',
    'rge_undef', and 'sec_undef' are included to differentiate between
    error vs. undefined, in case that distinction is needed.
    """

    # Tract instance variables and a "header"-like definition of each.
    # (Attributes that are technically properties are marked with **)
    ATTRIBUTES = {
        'trs': 'Twp/Rge/Sec',  # **
        'twp': 'Township',  # **
        'twp_num': 'Twp Number',  # **
        'twp_ns': 'Twp Direction',  # **
        'rge': 'Range',  # **
        'rge_num': 'Rge Number',  # **
        'rge_ew': 'Rge Direction',  # **
        'twprge': 'Twp & Rge',  # **
        'sec': 'Section',  # **
        'sec_num': 'Section Number',  # **
        'qqs': 'Aliquots',
        'lots': 'Lots',
        'ilots': 'Lot Numbers',  # **
        'lots_qqs': 'Lots & Aliquots',  # **
        'desc': 'Description',
        'orig_desc': 'Original (full) PLSS Description',
        'pp_desc': 'Cleaned-Up Description',
        'desc_is_flawed': 'Fatal Parsing Errors Identified',
        'w_flags': 'Warning Flags',
        'w_flag_lines': 'Warning Flags with Context',
        'e_flags': 'Error Flags',
        'e_flag_lines': 'Error Flags with Context',
        'flags': 'Warning & Error Flags',  # **
        'flag_lines': 'Warning & Error Flags with Context',  # **
        'lot_acres': 'Lot Acreages',
        'source': 'Source'
    }

    # A unique identifier that increments every time a Tract is created.
    __UID = 0

    def __init__(
            self,
            desc,
            trs=None,
            config=None,
            parse_qq=None,
            source=None,
            orig_desc=None,
            orig_index=0):
        """
        :param desc: The description block within this TRS. (What will
        be processed if this Tract object gets parsed into lots/QQs.)
        :param trs: Specify the TRS of the Tract. Formatted such that
        Twp and Rge are 1 to 3 digits + direction, and section is 2
        digits, and North/South and East/West are represented with the
        lowercase first letter.
            Ex: Sec 1, T154N-R97W -> '154n97w01'
                Sec 14, T1S-R9E -> '1s9e14'
        :param config: Either a pytrs.Config object, or a string of
        parameters to configure how the Tract object should be parsed.
        (See documentation on pytrs.Config objects for optional config
        parameters.)
        :param parse_qq: Whether to parse the `desc` into lots/QQs at
        init. (Defaults to False)
        :param source: (Optional) Essentially any value (e.g., a unique
        identifier number or document id) specifying where the
        description came from. (Useful if parsing multiple descriptions
        and need to internally keep track where they came from.)
        :param orig_desc: The full, original text of the parent PLSSDesc
        object, if any.
        :param orig_index: An integer representing the order in which this
        Tract object was created while parsing the parent PLSSDesc
        object, if any
        """

        if not isinstance(trs, (str, TRS)) and trs is not None:
            raise TypeError("`trs` must be a str, None, or a TRS object")

        self.__uid = Tract.__UID
        Tract.__UID += 1

        # Note that setting `.trs` populates a TRS object in the
        # protected `.__trs` attribute.
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

        # A dict of lot acreages, keyed by 'L1', 'L2', etc.
        self.lot_acres = {}

        # --------------------------------------------------------------
        # Configure how the Tract should be parsed:

        # If a T&R is identified without 'North/South' specified, fall
        # back on this. Will be filled in when `.config` is set (if
        # applicable).
        # NOTE: only applicable for using .from_twprgesec() or
        # `.set_twprgesec()`
        self.default_ns = None

        # If a T&R is identified without 'East/West' specified, fall
        # back on this. Will be filled in when `.config` is set (if
        # applicable).
        # NOTE: only applicable for using .from_twprgesec() or
        # `.set_twprgesec()`
        self.default_ew = None

        # NOTE: `parse_qq`, `clean_qq`, & `include_lot_divs` will be
        # changed when `.config` is set, if needed.

        # Whether we should parse lots and aliquots at init.
        self.parse_qq = False

        # Whether the user expects tract descriptions to have `clean_qq` (i.e.
        # nothing but clean aliquots and lots, with no typos, exceptions,
        # metes-and-bounds, or other hindrances to the parser.)
        self.clean_qq = False

        # Whether to include any divisions of lots
        # (i.e. 'N/2 of Lot 1' to 'N2 of L1').
        self.include_lot_divs = True

        # Whether to iron out common OCR artifacts. Defaults to `False`.
        # NOTE: Currently only has effect if Tract object is created via
        # `.from_twprgesec()`.  May have more effect in a later version.
        self.ocr_scrub = False

        # Apply settings from kwarg `config=`
        self.config = config

        # If kwarg-specified parse_qq, that will override config input
        if parse_qq is not None:
            self.parse_qq = parse_qq

        self.pp_desc = self.desc

        # If config settings require calling parse() at init, do it now.
        if self.parse_qq:
            self.parse(commit=True)
        else:
            self.preprocess(commit=True)

    def __str__(self):
        return (
            "Tract ({0})\n"
            "{1}\n"
            "Total Lots, QQs: {3}, {2}\n").format(
                "Parsed" if self.parse_complete else "Unparsed",
                self.quick_desc() if self.trs not in ("", None) else self.desc,
                len(self.qqs) if self.parse_complete else "n/a",
                len(self.lots) if self.parse_complete else "n/a")

    @property
    def trs(self):
        """
        Accessing the ``.trs`` property actually pulls the ``.trs``
        attribute (a str) of the protected ``TRS`` object stored in
        ``.__trs``. This contrasts with SETTING the ``.trs`` attribute,
        which populates a new ``TRS`` object in ``.__trs`` instead.
        :return:
        """
        return self.__trs.trs

    @trs.setter
    def trs(self, new_trs):
        """
        Setting the ``.trs`` attribute populates all of the associated
        properties via a pytrs.TRS objects.
        :param new_trs: A Twp/Rge/Sec in the standard pyTRS format.
        """
        if isinstance(new_trs, TRS):
            new_trs = new_trs.trs
        self.__trs = TRS(new_trs)

    def set_twprgesec(
            self, twp=None, rge=None, sec=None, default_ns=None,
            default_ew=None, ocr_scrub=None):
        """
        Set the Twp/Rge/Sec of this Tract from the component parts, and
        populate the corresponding properties for this Tract object.
        Returns the compiled Twp/Rge/Sec (in the pyTRS format).

        :param twp: Township (a str or int).
        :param rge: Range (a str or int).
        :param sec: Section (a str or int)
        :param default_ns: (Optional) If `twp` wasn't specified as N or
        S, assume `default_ns` (pass as 'n' or 's'). If not specified,
        will fall back to PLSSDesc.MASTER_DEFAULT_NS (which is 'n'
        unless configured otherwise).
        :param default_ew: (Optional) If `rge` wasn't specified as E or
        W, assume `default_ew` (pass as 'e' or 'w'). If not specified,
        will fall back to PLSSDesc.MASTER_DEFAULT_EW (which is 'w'
        unless configured otherwise).
        :param ocr_scrub: A bool, whether to try to scrub common OCR
        artifacts from the Twp, Rge, and Sec -- if any of them are
        passed as a str. (Defaults to whatever was set in ``.config``,
        which is ``False`` unless configured otherwise.)
        :return: The compiled Twp/Rge/Sec in the pyTRS format.
        """
        if not default_ns:
            default_ns = self.default_ns

        if not default_ew:
            default_ew = self.default_ew

        if ocr_scrub is None:
            ocr_scrub = self.ocr_scrub

        trs = TRS.construct_trs(
            twp, rge, sec, default_ns, default_ew, ocr_scrub)
        self.trs = trs
        return trs

    @property
    def twp(self):
        return self.__trs.twp

    @property
    def twp_num(self):
        return self.__trs.twp_num

    @property
    def twp_ns(self):
        return self.__trs.twp_ns

    ns = twp_ns

    @property
    def rge(self):
        return self.__trs.rge

    @property
    def rge_num(self):
        return self.__trs.rge_num

    @property
    def rge_ew(self):
        return self.__trs.rge_ew

    ew = rge_ew

    @property
    def twprge(self):
        return self.__trs.twprge

    def pretty_twprge(
            self, t="T", delim="-", r="R", n=None, s=None, e=None, w=None,
            undef="---X"):
        """
        Convert the Twp/Rge info into a clean str. By default, will
        return in the format 'T154N-R97W', but control the output with
        the various optional parameters.

        :param t: How "Township" should appear. ('T' by default)
        :param delim: How Twp should be separated from Rge. ('-' by
        default)
        :param r: How "Range" should appear. ("R" by default)
        :param n: How "North" (if found) should appear.
        :param s: How "South" (if found) should appear.
        :param e: How "East" (if found) should appear.
        :param w: How "West" (if found) should appear.
        :param undef: How undefined (or error) Twp or Rge should be
        represented, including the direction. ('---X' by default)
        :return: A str of the clean Twp/Rge.
        """
        return self.__trs.pretty_twprge(t, delim, r, n, s, e, w, undef)

    @property
    def sec(self):
        return self.__trs.sec

    @property
    def sec_num(self):
        return self.__trs.sec_num

    @property
    def twp_undef(self):
        return self.__trs.twp_undef

    @property
    def rge_undef(self):
        return self.__trs.rge_undef

    @property
    def sec_undef(self):
        return self.__trs.sec_undef

    @property
    def lots_qqs(self):
        """A combined list of lots + QQs."""
        return self.lots + self.qqs

    @property
    def ilots(self):
        """Lots as a list of integers, with any divisions discarded."""
        return [int(lt.split('L')[-1]) for lt in self.lots]

    @property
    def flags(self):
        return self.e_flags + self.w_flags

    @property
    def flag_lines(self):
        return self.e_flag_lines + self.w_flag_lines

    @staticmethod
    def from_twprgesec(
            desc,
            twp=None,
            rge=None,
            sec=None,
            default_ns=None,
            default_ew=None,
            config=None,
            parse_qq=None,
            source=None,
            orig_desc=None,
            orig_index=0):
        """
        Create a Tract object from separate Twp, Rge, and Sec components
        rather than joined Twp/Rge/Sec. All parameters are the same as
        __init__(), except that `trs=` is replaced with `twp=`, `rge=`,
        and `sec=`. (If N/S or E/W are not specified, will pull defaults
        from `default_ns` and `default_ew` -- or failing that, from
        `config` parameters. If not specified in any of those places,
        will default to ``PLSSDesc.MASTER_DEFAULT_NS`` and
        ``PLSSDesc.MASTER_DEFAULT_EW``, which are `'n'` and `'w'`,
        respectively, unless configured otherwise.)

        :param desc: Same as initializing a Tract object.
        :param twp: Township. Pass as a string (i.e. '154n'). If passed
        as an int, the N/S will be pulled from `default_ew` or `config`
        parameters, or defaulted to 'n' if not specified.
        :param rge: Range. Pass as a string (i.e. '97w'). If passed as
        an int, the E/W will be pulled from `default_ew` or `config`
        parameters, or defaulted to 'w' if not specified.
        :param sec: Section. Pass as a str or an int (up to 2 digits).
        :param default_ns: How to interpret townships for which direction
        was not specified -- i.e. either 'n' or 's'. (Defaults to what
        is specified in the ``config=`` parameters, if any; and if not
        there, then to ``PLSSDesc.MASTER_DEFAULT_NS``, which is 'n'
        unless otherwise specified.)
        :param default_ew: How to interpret ranges for which direction
        was not specified -- i.e. either 'e' or 'w'. (Defaults to what
        is specified in the ``config=`` parameters, if any; and if not
        there, then to ``PLSSDesc.MASTER_DEFAULT_EW``, which is 'w'
        unless otherwise specified.)
        :param source: Same as when initializing a Tract object.
        :param orig_desc: Same as when initializing a Tract object.
        :param orig_index: Same as when initializing a Tract object.
        :param config: Same as when initializing a Tract object.
        :param parse_qq: Same as when initializing a Tract object.
        :return: The new Tract object, with the ``.trs`` compiled here.
        """

        # Compile the `config=` data into a Config object (or use the
        # provided object, if already provided as `Config` type), so we
        # can extract `default_ns` and `default_ew`
        if isinstance(config, str) or config is None:
            config = Config(config)
        if not isinstance(config, Config):
            raise ConfigError(config)

        # Get our default_ns and default_ew from kwargs or config
        if default_ns is None:
            default_ns = config.default_ns
        if default_ew is None:
            default_ew = config.default_ew

        # Whether to scrub twp, rge, and sec strings for OCR artifacts
        ocr_scrub = False
        if config.ocr_scrub is not None:
            ocr_scrub = config.ocr_scrub

        # Compile the Twp/Rge/Sec into `trs`
        trs = TRS.construct_trs(
            twp, rge, sec, default_ns, default_ew, ocr_scrub=ocr_scrub)

        # Create a new Tract object and return it
        new_tract = Tract(
            desc=desc, trs=trs, source=source, orig_desc=orig_desc,
            orig_index=orig_index, config=config, parse_qq=parse_qq)
        return new_tract

    @property
    def config(self):
        return self.__config

    @config.setter
    def config(self, new_config):
        """
        Apply the relevant settings from a Config object to this object;
        takes either a string (i.e. config text) or a Config object.

        :param new_config: Either a pytrs.Config object, or equivalent
        config parameters. (See pytrs.Config documentation for optional
        parameters.)
        """
        if isinstance(new_config, str) or new_config is None:
            new_config = Config(new_config)
        if not isinstance(new_config, Config):
            raise ConfigError(new_config)

        for attrib in Config._TRACT_ATTRIBUTES:
            value = getattr(new_config, attrib)
            if value is not None:
                setattr(self, attrib, value)

        self.__config = new_config

    @property
    def desc_is_flawed(self):
        return len(self.e_flags) > 0

    def parse(
            self,
            commit=True,
            clean_qq=None,
            include_lot_divs=None,
            qq_depth_min=None,
            qq_depth_max=None,
            qq_depth=None,
            break_halves=None):
        """
        Parse the description block of this Tract into lots and QQ's.

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
        :return: Returns the a single list of identified lots and QQ's.
        """

        # --------------------------------------------------------------
        # Note that this method is actually a wrapper for initializing
        # a PLSSParser object and extracting the relevant attributes
        # from that. User-facing documentation for that class is
        # maintained here.
        # --------------------------------------------------------------

        # ----------------------------------------
        # Lock down parameters for this parse.

        if clean_qq is None:
            clean_qq = self.clean_qq

        if include_lot_divs is None:
            include_lot_divs = self.include_lot_divs

        if break_halves is None:
            break_halves = self.break_halves

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

        # ----------------------------------------
        # Parse it.

        parser = TractParser(
            text=self.desc,
            clean_qq=clean_qq,
            include_lot_divs=include_lot_divs,
            qq_depth_min=qq_depth_min,
            qq_depth_max=qq_depth_max,
            qq_depth=qq_depth,
            break_halves=break_halves,
            parent=self
        )

        # Store the results, if instructed to do so.
        if commit:
            self.parse_complete = True

            # Unpack the appropriate attributes.
            for attribute in parser.UNPACKABLES:
                setattr(self, attribute, getattr(parser, attribute))

            # Pull the preprocessed text from the parser.
            self.pp_desc = parser.text

        return parser.lots + parser.qqs

    def preprocess(self, clean_qq=None, commit=False) -> str:
        """
        Preprocess the description text to iron out common kinks in the
        input data, and optionally store the results to ``.pp_desc``
        attribute (with ``commit=True``).

        NOTE: Regardless whether committed, the description will be
        preprocessed (again) when parsed.

        :param clean_qq: Whether to expect only clean lots and QQ's
        (i.e. no metes-and-bounds, exceptions, complicated descriptions,
        etc.). Defaults to whatever is specified in `self.clean_qq`
        (which is False, unless configured otherwise).
        :param commit: Whether to store the results to ``.pp_desc``.
        (Defaults to `False`)
        :return: The preprocessed string.
        """
        text = self.desc
        if clean_qq is None:
            clean_qq = self.clean_qq
        preprocessor = TractPreprocessor(text, clean_qq=clean_qq)
        text = preprocessor.text
        if commit:
            self.pp_desc = text
        return text

    def to_dict(self, *attributes) -> dict:
        """
        Compile the requested attributes into a dict.

        :param attributes: The attribute names (instance variables) to
        include.
        :return: A dict, keyed by attribute.
        """

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

    @staticmethod
    def get_headers(attributes, nice_headers, plus_cols=None):
        """
        Get 'clean' headers for a .csv file for the ``headers``, drawing
        from ``nice_headers`` (a bool, list, or dict).

        :param attributes: a list of names (strings) of whichever
        attributes should be included (see documentation on
        `pytrs.Tract` objects for the names of relevant attributes).
        :param nice_headers: By default, this method will use the
        attribute names as headers. To use custom headers, pass to
        ``nice_headers=`` any of the following:
        -- a list of strings to use. (Should be equal in length to the
        list passed as ``attributes``, but will not raise an error if
        that's not the case. The resulting column headers will just be
        fewer than the actual number of columns.)
        -- a dict, keyed by attribute name, and whose values are the
        corresponding headers. (Any missing keys will use the attribute
        name.)
        -- `True` -> use the values in the ``Tract.ATTRIBUTES`` dict for
        headers. (WARNING: Any value passed that is not a list or dict
        and that evaluates to `True` will cause this behavior.)
        -- If not specified (i.e. None), will just use the attribute
        names themselves.
        :param plus_cols:  (Optional) a list of additional headers to
        write that are not covered by the Tract attributes.
        :return: A new list of header strings.
        """
        header_row = attributes.copy()
        if isinstance(nice_headers, dict):
            header_row = [nice_headers.get(att, att) for att in attributes]
        elif isinstance(nice_headers, list):
            header_row = nice_headers.copy()
        elif nice_headers:
            header_row = [Tract.ATTRIBUTES.get(att, att) for att in attributes]
        if plus_cols:
            header_row.extend(plus_cols)
        return header_row


class TRS:
    """
    A container for Twp/Rge/Section in the standard pyTRS format.
    Automatically breaks the TRS down into its component parts, which
    can be accessed as properties:
        .trs        -> The full Twp/Rge/Sec combination. *
        .twp        -> Twp number + direction (a str or None)
        .twp_num    -> Twp number (an int or None)
        .twp_ns     -> Twp direction ('n', 's', or None)
        .ns         -> same as `.twp_ns`
        .twp_undef  -> whether the Twp was undefined. **
        .rge        -> Rge number + direction (a str or None)
        .rge_num    -> Rge num (an int or None)
        .rge_ew     -> Rge direction ('e', 'w', or None)
        .ew         -> same as `.rge_ew`
        .rge_undef  -> whether the Rge was undefined. **
        .sec_num    -> Sec number (an int or None)
        .sec_undef  -> whether the Sec was undefined. **

    * Note that setting `.trs` will cause the other properties to be
    recalculated. (Optionally set the `.trs` using the separate
    Twp/Rge/Sec components with the `.set_twprgesec()` method.)

    ** Note that error parses do NOT qualify as 'undefined', but
    undefined and error values are both stored as None. 'twp_undef',
    'rge_undef', and 'sec_undef' are included to differentiate between
    error vs. undefined, in case that distinction is needed.
    """

    # Str representations of error Twp/Rge/Sec
    _ERR_SEC = 'XX'
    _ERR_TWP = 'XXXz'
    _ERR_RGE = _ERR_TWP
    _ERR_TWPRGE = f"{_ERR_TWP}{_ERR_RGE}"
    _ERR_TRS = f"{_ERR_TWPRGE}{_ERR_SEC}"

    # Str representations of undefined Twp/Rge/Sec
    _UNDEF_SEC = '__'
    _UNDEF_TWP = '___z'
    _UNDEF_RGE = _UNDEF_TWP
    _UNDEF_TWPRGE = f"{_UNDEF_TWP}{_UNDEF_RGE}"
    _UNDEF_TRS = f"{_UNDEF_TWPRGE}{_UNDEF_SEC}"

    _ALL_ERR = (
        _ERR_SEC,
        _ERR_TWP,
        _ERR_RGE,
        _ERR_TWPRGE,
        _ERR_TRS
    )

    _ALL_UNDEF = (
        _UNDEF_SEC,
        _UNDEF_TWP,
        _UNDEF_RGE,
        _UNDEF_TWPRGE,
        _UNDEF_TRS
    )

    _ALL_ERR_UNDEF = tuple(list(_ALL_ERR) + list(_ALL_UNDEF))

    # Regex patterns for unpacking Twp/Rge/Sec
    _TWP_RGX = r"((?P<twp_num>\d{1,3})(?P<ns>[nsNS]))"
    _RGE_RGX = r"((?P<rge_num>\d{1,3})(?P<ew>[ewEW]))"
    _SEC_RGX = r"\d{2}"

    # Based on the above, compile the regex pattern for unpacking
    # Twp/Rge/Sec in this module.
    _TRS_UNPACKER_REGEX = _compile_trs_unpacker_regex(
        twp_rgx=_TWP_RGX,
        err_twp=_ERR_TWP,
        undef_twp=_UNDEF_TWP,
        rge_rgx=_RGE_RGX,
        err_rge=_ERR_RGE,
        undef_rge=_UNDEF_RGE,
        sec_rgx=_SEC_RGX,
        err_sec=_ERR_SEC,
        undef_sec=_UNDEF_SEC
    )

    # Whether to cache Twp/Rge/Sec dicts in TRS.__CACHE. If used, it
    # will reuse the same dict for the same key in the `.__trs_dict`
    # attribute each TRS object, and not bother breaking it down again.
    # Note that the contents of a TRS object's ``.__trs_dict`` attribute
    # are only ever accessed by properties that protect them (e.g.,
    # ``Tract.twp``, ``TRS.twprge``, etc.) -- so in theory, somebody
    # would really have to want to mess things up in order to do so.
    _USE_CACHE = True
    __CACHE = {}

    def __init__(self, trs=None):
        if trs in ["", None]:
            trs = TRS._UNDEF_TRS
        self.__trs_dict = None

        # Setting `.trs` attribute populates `.__trs_dict`, from which
        # twp, rge, twprge, sec, twp_num, twp_ns, rge_num, rge_ew, and
        # sec_num can be pulled (as properties)
        self.trs = trs

    def __str__(self):
        return self.trs

    def __eq__(self, other):
        """
        A `TRS` object is equal to another object if that object is also
        a `TRS` object with an identical `.trs` attribute.
        """
        if not isinstance(other, TRS):
            return False
        return self.trs == other.trs

    @property
    def trs(self):
        return self.__trs_dict["trs"]

    @trs.setter
    def trs(self, new_trs):
        # If we've already broken down this trs into a dict, just
        # reuse it.
        self.__trs_dict = TRS.__CACHE.get(new_trs, None)
        if not self.__trs_dict:
            self.__trs_dict = TRS._cache_trs_to_dict(new_trs)

    @property
    def twp(self):
        return self.__trs_dict["twp"]

    @property
    def twp_num(self):
        return self.__trs_dict["twp_num"]

    @property
    def twp_ns(self):
        return self.__trs_dict["twp_ns"]

    ns = twp_ns

    @property
    def rge(self):
        return self.__trs_dict["rge"]

    @property
    def rge_num(self):
        return self.__trs_dict["rge_num"]

    @property
    def rge_ew(self):
        return self.__trs_dict["rge_ew"]

    ew = rge_ew

    @property
    def twprge(self):
        return f"{self.__trs_dict['twp']}{self.__trs_dict['rge']}"

    def pretty_twprge(
            self, t="T", delim="-", r="R", n=None, s=None, e=None, w=None,
            undef="---X"):
        """
        Convert the Twp/Rge info into a clean str. By default, will
        return in the format 'T154N-R97W', but control the output with
        the various optional parameters.

        :param t: How "Township" should appear. ('T' by default)
        :param delim: How Twp should be separated from Rge. ('-' by
        default)
        :param r: How "Range" should appear. ("R" by default)
        :param n: How "North" (if found) should appear.
        :param s: How "South" (if found) should appear.
        :param e: How "East" (if found) should appear.
        :param w: How "West" (if found) should appear.
        :param undef: How undefined (or error) Twp or Rge should be
        represented, including the direction. ('---X' by default)
        :return: A str of the clean Twp/Rge.
        """
        twp_num = self.twp_num
        rge_num = self.rge_num
        ns = self.ns
        ew = self.ew
        if not ns:
            ns = ""
        if not ew:
            ew = ""
        if twp_num is None:
            twp_num = undef
        if rge_num is None:
            rge_num = undef

        ns = ns.upper()
        ew = ew.upper()

        if n is not None and ns.lower().startswith('n'):
            ns = n
        if s is not None and ns.lower().startswith('s'):
            ns = s
        if e is not None and ew.lower().startswith('e'):
            ew = e
        if w is not None and ew.lower().startswith('w'):
            ew = w

        return f"{t}{twp_num}{ns}{delim}{r}{rge_num}{ew}"

    @property
    def sec(self):
        return self.__trs_dict["sec"]

    @property
    def sec_num(self):
        return self.__trs_dict["sec_num"]

    @property
    def twp_undef(self):
        return self.__trs_dict["twp_undef"]

    @property
    def rge_undef(self):
        return self.__trs_dict["rge_undef"]

    @property
    def sec_undef(self):
        return self.__trs_dict["sec_undef"]

    def set_twprgesec(
            self, twp, rge, sec, default_ns=None, default_ew=None,
            ocr_scrub=False):
        """
        Set the Twp/Rge/Sec of this TRS object by its component parts.
        Returns the compiled `trs` string after setting the various
        components to the appropriate attributes.

        :param twp: Township (a str or int).
        :param rge: Range (a str or int).
        :param sec: Section (a str or int)
        :param default_ns: (Optional) If `twp` wasn't specified as N or
        S, assume `default_ns` (pass as 'n' or 's'). If not specified,
        will fall back to PLSSDesc.MASTER_DEFAULT_NS (which is 'n'
        unless configured otherwise).
        :param default_ew: (Optional) If `rge` wasn't specified as E or
        W, assume `default_ew` (pass as 'e' or 'w'). If not specified,
        will fall back to PLSSDesc.MASTER_DEFAULT_EW (which is 'w'
        unless configured otherwise).
        :param ocr_scrub: A bool, whether to try to scrub common OCR
        artifacts from the Twp, Rge, and Sec -- if any of them are
        passed as a str. (Defaults to ``False``.)
        :return: The compiled Twp/Rge/Sec in the pyTRS format.
        """
        trs = TRS.construct_trs(
            twp, rge, sec, default_ns, default_ew, ocr_scrub)
        self.trs = trs
        return trs

    @staticmethod
    def from_twprgesec(
            twp=None, rge=None, sec=None, default_ns=None, default_ew=None,
            ocr_scrub=False):
        """
        Create and return a new TRS object by defining its Twp/Rge/Sec
        from its component parts.

        :param twp: Township (a str or int).
        :param rge: Range (a str or int).
        :param sec: Section (a str or int)
        :param default_ns: (Optional) If `twp` wasn't specified as N or
        S, assume `default_ns` (pass as 'n' or 's'). If not specified,
        will fall back to PLSSDesc.MASTER_DEFAULT_NS (which is 'n'
        unless configured otherwise).
        :param default_ew: (Optional) If `rge` wasn't specified as E or
        W, assume `default_ew` (pass as 'e' or 'w'). If not specified,
        will fall back to PLSSDesc.MASTER_DEFAULT_EW (which is 'w'
        unless configured otherwise).
        :param ocr_scrub: A bool, whether to try to scrub common OCR
        artifacts from the Twp, Rge, and Sec -- if any of them are
        passed as a str. (Defaults to ``False``.)
        :return: The new pyTRS.TRS object.
        """
        trs = TRS.construct_trs(
            twp, rge, sec, default_ns, default_ew, ocr_scrub)
        return TRS(trs)

    @staticmethod
    def construct_trs(
            twp, rge, sec, default_ns=None, default_ew=None, ocr_scrub=False):
        """
        Build a Twp/Rge/Sec in the pyTRS format from component parts.
        Get back a string of that Twp/Rge/Sec.

        :param twp: Township (a str or int -- ``'154n'`` or ``154``).
        :param rge: Range (a str or int -- ``'97w'`` or ``97``).
        :param sec: Section (a str or int -- ``'14'`` or ``14``).
        :param default_ns: (Optional) If `twp` wasn't specified as N or
        S, assume `default_ns` (pass as 'n' or 's'). If not specified,
        will fall back to PLSSDesc.MASTER_DEFAULT_NS (which is 'n'
        unless configured otherwise).
        :param default_ew: (Optional) If `rge` wasn't specified as E or
        W, assume `default_ew` (pass as 'e' or 'w'). If not specified,
        will fall back to PLSSDesc.MASTER_DEFAULT_EW (which is 'w'
        unless configured otherwise).
        :param ocr_scrub: A bool, whether to try to scrub common OCR
        artifacts from the Twp, Rge, and Sec -- if any of them are
        passed as a str. (Defaults to ``False``.)
        :return: The compiled Twp/Rge/Sec in the pyTRS format.
        """

        if default_ns is None:
            default_ns = PLSSDesc.MASTER_DEFAULT_NS
        if default_ew is None:
            default_ew = PLSSDesc.MASTER_DEFAULT_EW

        # Ensure legal N/S and E/W values.
        if default_ns.lower() not in PLSSDesc._LEGAL_NS:
            raise DefaultNSError(default_ns)
        if default_ew.lower() not in PLSSDesc._LEGAL_EW:
            raise DefaultEWError(default_ew)

        def scrub(twp_rge_or_section, ns_ew_sec):
            """
            Scrub the `twp`, `rge`, and `sec` from input into the
            component parts. (Use `ocr_scrub` if appropriate.) Run
            separately for twp, rge, and section.

            :param twp_rge_or_section: A candidate `twp` or `rge`
            :param ns_ew_sec: "ns" (if running Twp), "ew" (if running
            Rge), or None (if running Sec)
            :return: 2-tuple: (scrubbed Twp/Rge/Sec number, direction).
            Note that direction will always be evaluated to None when
            running this for Section.
            """
            twprgesec_num = twp_rge_or_section

            # Determine whether we're running Twp, Rge, or Section.
            # Default to Twp.
            direction = default_ns
            direction_options = PLSSDesc._LEGAL_NS
            if ns_ew_sec == "ew":
                # Rge.
                direction = default_ew
                direction_options = PLSSDesc._LEGAL_EW
            elif ns_ew_sec is None:
                # Sec.
                direction = None

            # If it's not a string, we don't need to ocr_scrub it.
            if not isinstance(twp_rge_or_section, str):
                return twprgesec_num, None

            if (direction is not None
                    and twp_rge_or_section.lower().endswith(direction_options)):
                # Running Twp or Rge.
                twprgesec_num = twp_rge_or_section[:-1]
                direction = twp_rge_or_section[-1].lower()

            if ocr_scrub:
                twprgesec_num = _ocr_scrub_alpha_to_num(twprgesec_num)

            return twprgesec_num, direction

        twp, ns = scrub(twp, "ns")
        rge, ew = scrub(rge, "ew")
        sec, _ = scrub(sec, None)

        if ns is None:
            ns = default_ns
        if ew is None:
            ew = default_ew

        if twp in [None, ""]:
            twp = TRS._UNDEF_TWP
        try:
            twp = int(twp)
        except ValueError:
            # Str has encoded N/S data, or is an error or undefined Twp.
            pass
        if isinstance(twp, int):
            twp = f"{twp}{ns.lower()}"
        if twp != TRS._UNDEF_TWP and re.search(rf"\b{TRS._TWP_RGX}\b", twp) is None:
            # Couch the pattern in '\b' to ensure we match the entire str.
            twp = TRS._ERR_TWP

        if rge in [None, ""]:
            rge = TRS._UNDEF_RGE
        try:
            rge = int(rge)
        except ValueError:
            # Str has encoded E/W data, or is an error or undefined Rge.
            pass
        if isinstance(rge, int):
            rge = f"{rge}{ew.lower()}"
        if rge != TRS._UNDEF_RGE and re.search(rf"\b{TRS._RGE_RGX}\b", rge) is None:
            rge = TRS._ERR_RGE

        if sec is None:
            sec = TRS._UNDEF_SEC
        else:
            sec = str(sec).rjust(2, '0')
        if sec != TRS._UNDEF_SEC and re.search(rf"\b{TRS._SEC_RGX}\b", sec) is None:
            sec = TRS._ERR_SEC

        return f"{twp}{rge}{sec}"

    @staticmethod
    def _cache_trs_to_dict(trs) -> dict:
        """
        INTERNAL USE:
        Identical to `TRS.trs_to_dict()`, but will also add the
        resulting dict to the `TRS.__CACHE` (if `TRS._USE_CACHE` is
        turned on).
        """
        # We do not add dicts to the cache when calling the public-
        # facing method, in order to avoid changes to those dicts
        # impacting TRS objects. This non-public method is only called
        # by other non-public methods.
        # Note that dicts in the cache are only ever accessed via
        # protected attributes (e.g,. ``Tract.twp``, ``TRS.twprge``,
        # etc.) -- although the cache itself could be accessed and
        # modified.
        dct = TRS.trs_to_dict(trs)
        if TRS._USE_CACHE:
            TRS.__CACHE[trs] = dct
        return dct

    @staticmethod
    def trs_to_dict(trs) -> dict:
        """
        Take a compiled Twp/Rge/Sec (in the standard pyTRS format) and
        break it into a dict, keyed as follows:
            "twp"       -> Twp number + direction (a str or None)
            "twp_num"   -> Twp number (an int or None);
            "twp_ns"    -> Twp direction ('n', 's', or None);
            "twp_undef" -> whether the Twp was undefined. **
            "rge"       -> Rge number + direction (a str or None)
            "rge_num"   -> Rge num (an int or None);
            "rge_ew"    -> Rge direction ('e', 'w', or None)
            "rge_undef" -> whether the Rge was undefined. **
            "sec_num"   -> Sec number (an int or None)
            "sec_undef" -> whether the Sec was undefined. **

        ** Note that error parses do NOT qualify as 'undefined'.
        Undefined and error values are both stored as None. 'twp_undef',
        'rge_undef', and 'sec_undef' are included to differentiate
        between error vs. undefined, in case that distinction is needed.

        :param trs: The Twp/Rge/Sec (in the pyTRS format) to be broken
        apart.
        :return: A dict with the various elements.
        """

        if isinstance(trs, TRS):
            trs = trs.trs

        dct = {
            "trs": TRS._ERR_TRS,
            "twp": TRS._ERR_TWP,
            "twp_num": None,
            "twp_ns": None,
            "twp_undef": False,
            "rge": TRS._ERR_RGE,
            "rge_num": None,
            "rge_ew": None,
            "rge_undef": False,
            "sec": TRS._ERR_SEC,
            "sec_num": None,
            "sec_undef": False
        }

        # Default empty TRS to the undefined version (as opposed to an
        # error version, which would result otherwise).
        if trs in ["", None]:
            trs = TRS._UNDEF_TRS

        mo = TRS._TRS_UNPACKER_REGEX.search(trs)
        if not mo:
            return dct

        # Break down Twp
        if mo.group("twp_num") and mo.group("ns"):
            dct["twp"] = mo.group("twp")
            dct["twp_num"] = int(mo.group("twp_num"))
            dct["twp_ns"] = mo.group("ns")
        elif mo.group("twp") == TRS._UNDEF_TWP:
            dct["twp"] = mo.group("twp")
            dct["twp_undef"] = True

        # Break down Rge
        if mo.group("rge_num") and mo.group("ew"):
            dct["rge"] = mo.group("rge")
            dct["rge_num"] = int(mo.group("rge_num"))
            dct["rge_ew"] = mo.group("ew")
        elif mo.group("rge") == TRS._UNDEF_RGE:
            dct["rge"] = mo.group("rge")
            dct["rge_undef"] = True

        # Break down Sec
        sec = mo.group("sec")
        try:
            dct["sec_num"] = int(sec)
        except (ValueError, TypeError):
            if sec == TRS._UNDEF_SEC:
                dct["sec_undef"] = True
            else:
                sec = TRS._ERR_SEC
        finally:
            dct["sec"] = sec

        # Reconstruct TRS
        dct["trs"] = f"{dct['twp']}{dct['rge']}{dct['sec']}"

        return dct

    @classmethod
    def _clear_cache(cls):
        """
        INTERNAL USE:
        Clear the ``TRS.__CACHE`` dict.
        :return:
        """
        cls.__CACHE = {}
        return None

    @classmethod
    def _recompile(cls):
        """
        EXPERIMENTAL

        If any of the class attributes for error/undefined Township,
        Range, and/or Section have changed (``TRS._ERR_TWP``,
        ``TRS._UNDEF_TWP``, etc.) then the unpacker regex needs to be
        recompiled to account for these.

        Also recompiles and stores these class attributes:
            TRS._ERR_TWPRGE
            TRS._ERR_TRS
            TRS._UNDEF_TWPRGE
            TRS._UNDEF_TRS

        WARNING: This functionality is not supported.  Many pieces of
        this module rely on these attributes.  Thus, changing them is
        liable to introduce bugs in other functionality.  However, with
        care (and some limitations), it may be possible to change the
        defaults for error/undefined Twp/Rge/Sec. (You would be well
        advised to avoid using any characters that have any special
        meaning in regex patterns, generally.)

        :return: The newly compiled re.Pattern object (which will also
        have been set to the ``TRS._TRS_UNPACKER_REGEX`` class
        attribute).
        """
        new_rgx = _compile_trs_unpacker_regex(
            twp_rgx=TRS._TWP_RGX,
            err_twp=TRS._ERR_TWP,
            undef_twp=TRS._UNDEF_TWP,
            rge_rgx=TRS._RGE_RGX,
            err_rge=TRS._ERR_RGE,
            undef_rge=TRS._UNDEF_RGE,
            sec_rgx=TRS._SEC_RGX,
            err_sec=TRS._ERR_SEC,
            undef_sec=TRS._UNDEF_SEC)
        cls._TRS_UNPACKER_REGEX = new_rgx

        cls._ERR_TWPRGE = f"{cls._ERR_TWP}{cls._ERR_RGE}"
        cls._ERR_TRS = f"{cls._ERR_TWPRGE}{cls._ERR_SEC}"
        cls._UNDEF_TWPRGE = f"{cls._UNDEF_TWP}{cls._UNDEF_RGE}"
        cls._UNDEF_TRS = f"{cls._UNDEF_TWPRGE}{cls._UNDEF_SEC}"

        # Clear the cache, because the same string would not necessarily
        # result in the same output dict anymore.
        cls._clear_cache()

        return new_rgx


class _TRSTractList(list):
    """
    INTERNAL USE:

    This class is not used directly but is subclassed as `TractList` and
    `TRSList`.

    `TRSList` holds only `TRS` objects; and `TractList` holds only
    `Tract` objects.

    Both subclasses will sort / filter / group their respective element
    types. But `TractList` has quite a bit of additional functionality
    for streamlined extraction of data from `Tract` objects.
    """

    # These will be modified in the subclasses to determine what
    # elements can be processed by each.
    _ok_individuals = ()
    _ok_iterables = ()
    _typeerror_msg = ''

    def __init__(self, iterable=()):
        """
        INTERNAL USE:
        (Initialize a `TRSList` or `TractList` directly.)

        :param iterable: Same as in `list()`
        """
        list.__init__(self, self._verify_iterable(iterable))

    @classmethod
    def _verify_iterable(cls, iterable, into=None):
        """
        INTERNAL USE:
        Type-check the contents of an iterable. Return a plain list of
        the elements in `iterable` if all are legal.
        """
        if isinstance(iterable, str):
            # A string is technically iterable, and they are acceptable
            # by a `TRSList` -- but NOT to be iterated over. If a
            # TRSList iterates over a string, each character would be
            # converted to an error `TRS` object, and nobody wants that.
            raise TypeError("type 'str' is not an acceptable iterable.")
        if into is None:
            into = []
        for elem in iterable:
            if isinstance(elem, cls._ok_individuals):
                into.append(cls._verify_individual(elem))
            elif isinstance(elem, cls):
                # Other instances of this class have already been
                # appropriately type-checked.
                into.extend(elem)
            elif isinstance(elem, cls._ok_iterables):
                for elem_deeper in elem:
                    into.append(cls._verify_individual(elem_deeper))
            else:
                raise TypeError(
                    f"{cls._typeerror_msg} Iterable contained {type(elem)!r}.")
        return into

    @classmethod
    def _verify_individual(cls, obj):
        """INTERNAL USE: Type-check a single object."""
        if not isinstance(obj, cls._ok_individuals):
            raise TypeError(
                f"{cls._typeerror_msg} Cannot accept {type(obj)!r}.")
        return cls._handle_type_specially(obj)

    @classmethod
    def _handle_type_specially(cls, obj):
        """INTERNAL USE: (For subclassing purposes.)"""
        return obj

    def __setitem__(self, index, value):
        list.__setitem__(self, index, self._verify_individual(value))

    def __getitem__(self, item):
        if isinstance(item, slice):
            return self.__class__(list.__getitem__(self, item))
        return list.__getitem__(self, item)

    def __repr__(self):
        return str(self)

    def extend(self, iterable):
        list.extend(self, self._verify_iterable(iterable))

    def append(self, obj):
        list.append(self, self._verify_individual(obj))

    def __iadd__(self, other):
        list.__iadd__(self, self._verify_iterable(other))

    def copy(self):
        return self.__class__(list.copy(self))

    def filter(self, key, drop=False):
        """
        Extract from this custom list all elements that match the `key`
        (a lambda function that returns a bool or bool-like value when
        applied to each element).

        Returns a new `TractList` of all of the selected `Tract` objects
        (or a `TRSList` of the selected `TRS` objects, if called as a
        `TRSList` method).

        :param key: a lambda function that returns a bool or bool-like
        value when applied to an element in this list. (True or
        True-like returned values will result in the inclusion of that
        element).

        :param drop: Whether to drop the matching elements from the
        original list. (Defaults to ``False``)

        :return: A new `TractList` (or `TRSList`) of the selected
        elements. (The original list will still hold all other elements,
        unless ``drop=True`` was passed.)
        """
        indexes_to_include = []
        for i, element in enumerate(self):
            if key(element):
                indexes_to_include.append(i)
        return self._new_list_from_self(indexes_to_include, drop)

    def filter_errors(self, twp=True, rge=True, sec=True, undef=False, drop=False):
        """
        Extract from this custom list all elements that were parsed
        with an error. Specifically extract Twp/Rge errors with
        ``twp=True`` and ``rge=True``; and get Sec errors with
        ``sec=True`` (all of which are on by default).

        Returns a new `TractList` (or `TRSList`, as applicable) of all
        of the selected elements.

        :param twp: a bool, whether to get Twp errors. (Defaults to
        ``True``)

        :param rge: a bool, whether to get Rge errors. (Defaults to
        ``True``)

        :param sec: a bool, whether to get Sec errors. (Defaults to
        ``True``)

        :param undef: a bool, whether to get consider Twps, Rges, or
        Sections that were UNDEFINED to also be errors. (Defaults to
        ``False``)

        :param drop: Whether to drop the selected elements from the
        original list. (Defaults to ``False``)

        :return: A new `TractList` (or `TRSList`, as applicable)
        containing all of the selected elements.
        """

        def match_by(elem, controller, var, undef_var):
            # Note: `undef_var` is the Tract/TRS attribute (or rather,
            # property) that says whether the corresponding `var` was
            # undefined. If it is False, then that means that particular
            # `var` was defined but ended up being an error.
            # For example, `match_by("twp_num", "twp_undef")`...

            bad = getattr(elem, var) is None
            if bad:
                # The `undef` parameter means cull any `None` values,
                # regardless of whether it was undefined or an error.
                # Either way, cull the var that was NOT undefined (i.e.
                # was an error.)
                bad = undef or not getattr(elem, undef_var)
            return bad and controller

        indexes_to_include = []
        for i, trs_or_tract in enumerate(self):
            if (match_by(trs_or_tract, twp, "twp_num", "twp_undef")
                    or match_by(trs_or_tract, rge, "rge_num", "rge_undef")
                    or match_by(trs_or_tract, sec, "sec_num", "sec_undef")):
                indexes_to_include.append(i)
        return self._new_list_from_self(indexes_to_include, drop)

    def filter_duplicates(self, method='default', drop=False):
        """
        Find the duplicate Tracts (or `TRS` objects) in this custom
        list, get a new custom list of the elements that were
        duplicates, and optionally `drop` the duplicates from the
        original list.

        (To be clear, if there are THREE identical Tracts in the
        ``TractList``, the returned ``TractList`` will contain only TWO
        Tracts, and the original ``TractList`` will still have one.)

        Control how to assess whether elements in the list are
        duplicates by ONE of the following methods:

        `method='instance'` -> Whether two objects are actually the same
        instance -- i.e. literally the same object. (By definition, this
        will also apply even if one of the other methods is used.)

        `method='lots_qqs'`  -> Whether the `.lots_qqs` attribute
        contains the same lots/aliquots (after removing duplicates
        there).  NOTE: Lots/aliquots must have been parsed for a given
        `Tract` object, or it will NOT match as a duplicate with this
        parameter.
                Ex: Will match these as duplicate tracts, assuming they
                were parsed with identical `config` settings:
                    `154n97w14: Lots 1 - 3, S/2NE/4`
                    `154n97w14: Lot 3, S/2NE/4, Lots 1, 2`
        NOTE: `'lots_qqs'` option has no effect when used on a `TRSList`
        object.

        `method='desc'` -> Whether the `.trs` and `.pp_desc` (i.e.
        preprocessed description) combine to form an identical tract.
                Ex: Will match these as duplicate tracts:
                    `154n97w14: NE/4`
                    `154n97w14: Northeast Quarter`
        NOTE: `'desc'` option has no effect when used on a `TRSList`
        object.

        `method='trs'` -> Unique `.trs` attributes.
        WARNING: This option is NOT recommended when calling the method
        on a `TractList` object. This is more appropriate when calling
        it on a `TRSList` object.

        `method='default'` -> Use `'instance'` if working with a
        `TractList` object, or `'trs'` if working with a `TRSList`
        object.  (This is the default behavior.)

        :param method: Specify how to assess whether `Tract` (or `TRS`)
        objects are duplicates (either 'instance', 'lots_qqs', 'desc',
        'trs', or 'default'). See above for example behavior of each.

        :param drop: Whether to remove the identified duplicates from
        the original list.

        :return: A new `TractList` (or `TRSList`, as applicable).
        """
        unique = set()
        indexes_to_include = []

        if method == 'default':
            method = 'instance'
            if isinstance(self, TRSList):
                method = 'trs'
        options = ('instance', 'lots_qqs', 'desc', 'trs')
        if method not in options:
            raise ValueError(f"`method` must be one of {options}")
        lots_qqs = method == 'lots_qqs'
        desc = method == 'desc'
        trs = method == 'trs'
        only_by_instance = not (lots_qqs or desc or trs)

        for i, element in enumerate(self):
            # Always find duplicate instances (because not all Tract
            # objects are parsed into lots/qqs).
            if element in unique:
                indexes_to_include.append(i)
            unique.add(element)
            if only_by_instance:
                continue

            to_check = element
            if lots_qqs:
                if not isinstance(element, Tract):
                    continue
                if not element.parse_complete:
                    continue
                lq = sorted(set(element.lots_qqs))
                to_check = f"{element.trs}_{lq}"
            if desc:
                if not isinstance(element, Tract):
                    continue
                to_check = f"{element.trs}_{element.pp_desc.strip()}"
            if trs:
                to_check = element.trs

            if to_check not in unique:
                unique.add(to_check)
            elif i not in indexes_to_include:
                # Use elif to avoid double-appending i (may have already
                # been added from the `instance` check).
                indexes_to_include.append(i)

        return self._new_list_from_self(indexes_to_include, drop)

    def _new_list_from_self(self, indexes: list, drop: bool):
        """
        INTERNAL USE:

        Get a new ``TractList`` (or ``TRSList``, as applicable) of the
        elements at the specified ``indexes``.  Optionally remove them
        from the original list with ``drop=True``.

        :param indexes: Indexes of the elements to include in the new
        ``TractList`` (or ``TRSList``).
        :param drop: a bool, whether to drop those elements from the
        original list.
        :return: The new `TractList` (or `TRSList`).
        """
        new_list = self.__class__()
        # Populate the new list in reverse order, in order to remove the
        # intended elements from the original list if requested.
        for i in range(len(indexes) - 1, -1, -1):
            ind = indexes[i]
            new_list.append(self[ind])
            if drop:
                self.pop(ind)
        new_list.reverse()
        return new_list

    def custom_sort(self, key='i,s,r,t', reverse=False):
        """
        Sort the elements in this `TractList` (or `TRSList`), in place.
        The standard ``list.sort(key=<lambda>, reverse=<bool>)``
        parameters can be used here. But this method has additional
        customized key options.  (Note that the parameter
        ``reverse=<bool>`` applies only to lambda sorts, and NOT to the
        custom keys detailed below.)

        Customized key options:

        'i' -> Sort by the original order the `Tract` objects were
                created.  (NOTE: 'i' sorting has no effect in `TRSList`
                objects.)

        't' -> Sort by Township.
               't.num'  --> Sort by raw number, ignoring N/S. (default)
               't.ns'   --> Sort from north-to-south
               't.sn'   --> Sort from south-to-north

        'r' -> Sort by Range.
               'r.num'  --> Sort by raw number, ignoring E/W. (default)
               'r.ew'   --> Sort from east-to-west **
               'r.we'   --> Sort from west-to-east **
        (** NOTE: These do not account for Principal Meridians.)

        's' -> Sort by Section number.

        Reverse any or all of the keys by adding '.reverse' (or '.rev')
        at the end of it.

        Use as many sort keys as you want. They will be applied in order
        from left-to-right, so place the highest 'priority' sort last.

        Twp/Rge's that are errors (i.e. `'XXXzXXXz'`) will be sorted to
        the end of the list when sorting on Twp and/or Rge (whether by
        number, north-to-south, south-to-north, east-to-west, or west-
        to-east).  Similarly, error Sections (i.e. `'XX'`) will be
        sorted to the end of the list when sorting on section.  (The
        exception is if the sort is reversed, in which case, they come
        first.)

        Construct all keys as a single string, separated by comma
        (spaces are optional). The components of each key should be
        separated by a period.

        Example keys:

            's.reverse,r.ew,t.ns'
                ->  Sort by section number (reversed, so largest-to-
                        smallest);
                    then sort by Range (east-to-west);
                    then sort by Township (north-to-south)

            'i,s,r,t'  (this is the default)
                ->  Sort by original creation order;
                    then sort by Section (smallest-to-largest);
                    then sort by Range (smallest-to-largest);
                    then sort by Township (smallest-to-largest)

        Moreover, we can conduct multiple sorts by passing ``key`` as a
        list of sort keys. We can mix and match string keys above with
        lambdas, although the ``reverse=<bool>`` will apply only to the
        lambdas.

        Optionally pass ``reverse=`` as a list of bools (i.e. a list
        equal in length to ``key=<list of sort keys>``) to use different
        ``reverse`` values for different lambdas. But then make sure
        that the lengths are equal, or it will raise an IndexError.

        :param key: A str, specifying which sort(s) should be done, and
        in which order. Alternatively, a lambda function (same as for
        the builtin ``list.sort(key=<lambda>)`` method).

        May optionally pass `sort_key` as a list of sort keys, to be
        applied left-to-right. In that case, lambdas and string keys may
        be mixed and matched.

        :param reverse: (Optional) Whether to reverse the sort.
        NOTE: This ONLY has an effect if the ``key`` is passed as a
        lambda (or a list containing lambdas). It has no effect on
        string keys (for which you would instead specify ``'.rev'``
        within the string key itself). Defaults to ``False``.

        NOTE: If ``key`` was passed as a list of keys, then ``reverse``
        must be passed as EITHER a single bool that will apply to all of
        the (non-string) sorts, OR as a list of bools that is equal in
        length to ``key`` (i.e. the values in ``key`` and ``reverse``
        will be matched up one-to-one).

        :return: None. (The original list is sorted in place.)
        """
        if not key:
            return None

        # Determine whether the sort_key was passed as a list/tuple
        # (i.e. if we're doing one sort operation or multiple).
        is_multi_key = isinstance(key, (list, tuple))
        is_multi_rev = isinstance(reverse, (list, tuple))
        if is_multi_key and not is_multi_rev:
            reverse = [reverse for _ in key]

        # If `iterable` sort_key and/or `sort_reverse`, make sure
        # the length of each matches.
        if ((is_multi_key and len(key) != len(reverse))
                or (is_multi_rev and not is_multi_key)):
            raise IndexError(
                "Mismatched length of iterable `sort_key` "
                "and `sort_reverse`")

        if is_multi_key:
            # If multiple sorts, do each.
            for sk, rv in zip(key, reverse):
                self.custom_sort(key=sk, reverse=rv)
        elif isinstance(key, str):
            # `._sort_custom` takes str-type sort keys.
            self._sort_custom(key)
        else:
            # Otherwise, assume it's a lambda. Use builtin `sort()`.
            self.sort(key=key, reverse=reverse)
        return None

    def _sort_custom(self, key: str = 'i,s,r,t'):
        """
        INTERNAL USE:

        Apply the custom str-type sort keys detailed in
        ``.custom_sort()``.

        NOTE: Documentation on the str-type sort keys is maintained in
        ``.custom_sort()``.

        :param key: A str, specifying which sort(s) should be done, and
        in which order.
        :return: None. (list is sorted in-situ.)
        """

        def get_max(var):
            """
            Get the largest value of the matching var in the of any
            element in this list. If there are no valid ints, return 0.
            """
            nums = [getattr(t, var) for t in self if getattr(t, var) is not None]
            if nums:
                return max(nums)
            return 0

        # TODO: Sort undefined Twp/Rge/Sec before error Twp/Rge/Sec.

        default_twp = get_max("twp_num") + 1
        default_rge = get_max("rge_num") + 1
        default_sec = get_max("sec_num") + 1

        assume = {
            "twp_num": default_twp,
            "rge_num": default_rge,
            "sec_num": default_sec
        }

        illegal_key_error = ValueError(f"Could not interpret sort key {key!r}.")

        # The regex pattern for a valid key component.
        pat = r"(?P<var>[itrs])(\.(?P<method>ns|sn|ew|we|num))?(\.(?P<rev>rev(erse)?))?"

        legal_methods = {
            "i": ("num", None),
            "t": ("ns", "sn", "num", None),
            "r": ("ew", "we", "num", None),
            "s": ("num", None)
        }

        def extract_safe_num(tract, var):
            val = getattr(tract, var)
            if val is None:
                val = assume[var]
            return val

        def i_sort_evaluate(list_element):
            """
            If the element is a `Tract` object, extract and return its
            internal UID. Otherwise, return 0.
            (This function exists so that the sort method works on a
            list of Tract objects as well as a list of TRS objects, the
            latter of which do not have a `._Tract__uid` attribute.)
            """
            if isinstance(list_element, Tract):
                return list_element._Tract__uid
            else:
                return 0

        sort_defs = {
            'i.num': i_sort_evaluate,
            't.num': lambda x: extract_safe_num(x, "twp_num"),
            't.ns': lambda x: n_to_s(x),
            't.sn': lambda x: n_to_s(x, reverse=True),
            'r.num': lambda x: extract_safe_num(x, "rge_num"),
            'r.we': lambda x: w_to_e(x),
            'r.ew': lambda x: w_to_e(x, reverse=True),
            's.num': lambda x: extract_safe_num(x, "sec_num")
        }

        def n_to_s(element, reverse=False):
            """
            Convert Twp number and direction to a positive or negative
            int, depending on direction. North townships are negative;
            South are positive (in order to leverage the default
            behavior of ``list.sort()`` -- i.e. smallest to largest).
            ``reverse=True`` to inverse the positive and negative.
            """
            num = element.twp_num
            ns = element.twp_ns

            multiplier = 1
            if num is None:
                num = default_twp
            if ns is None:
                multiplier = 1
            if ns == 's':
                multiplier = 1
            elif ns == 'n':
                multiplier = -1
            if reverse:
                multiplier *= -1
            if ns is None:
                # Always put _TRR_ERROR parses at the end.
                multiplier *= -1 if reverse else 1
            return multiplier * num

        def w_to_e(element, reverse=False):
            """
            Convert Rge number and direction to a positive or negative
            int, depending on direction. East townships are positive;
            West are negative (in order to leverage the default behavior
            of ``list.sort()`` -- i.e. smallest to largest).
            ``reverse=True`` to inverse the positive and negative.
            """
            num = element.rge_num
            ew = element.rge_ew

            multiplier = 1
            if num is None:
                num = default_rge
            if ew == 'e':
                multiplier = 1
            elif ew == 'w':
                multiplier = -1
            if reverse:
                multiplier *= -1
            if ew is None:
                # Always put _TRR_ERROR parses at the end.
                multiplier *= -1 if reverse else 1
            return multiplier * num

        def parse_key(k_):
            k_ = k_.lower()
            mo = re.search(pat, k_)
            if not mo:
                raise illegal_key_error
            if len(mo.group(0)) != len(k_):
                import warnings
                warnings.warn(SyntaxWarning(
                    f"Sort key {k_!r} may not have been fully interpreted. "
                    f"Check to make sure you are using the correct syntax."
                ))

            var = mo.group("var")
            method = mo.group("method")

            if method is None:
                # default to "num" for all vars.
                method = "num"
            # Whether to reverse
            rev = mo.group("rev") is not None

            # Confirm legal method for this var
            if method not in legal_methods[var]:
                raise ValueError(f"invalid sort method: {k!r}")

            var_method = f"{var}.{method}"
            return var_method, rev

        key = key.lower()
        key = re.sub(r"\s", "", key)
        key = re.sub(r"reverse", "rev", key)
        keys = key.split(',')
        for k in keys:
            sk, reverse = parse_key(k)
            self.sort(key=sort_defs[sk], reverse=reverse)

    def group_nested(
            self, by_attribute="twprge", into: dict = None,
            sort_key=None, sort_reverse=False):
        """
        Filter the elements in this list into a dict, keyed by unique
        values of ``by_attribute``, whose values are a custom list of
        the same type as the original (either a `TRSList` or
        `TractList`) of the grouped objects. By default, will filter
        into groups of Tracts (or TRS objects, if working with a
        `TRSList` object) that share Twp/Rge (i.e. ``'twprge'``).

        Pass ``by_attribute`` as a list of attributes to group by
        multiple attributes, and get a NESTED dict back. (Each
        consecutive attribute in the list will be another layer of
        nesting.)

        :param by_attribute: The str name of an attribute of `Tract` (or
        `TRS`) objects. (Defaults to ``'twprge'``). NOTE: Must be a
        hashable type!  (Optionally pass as a list of str names of
        attributes to do multiple groupings.)

        :param into: (Optional) An existing dict into which to group the
        Tracts (or `TRS` objects). If not specified, will create a new
        dict. Use this arg if you need to continue adding Tracts (or
        `TRS` objects) to an existing grouped dict.

        :param sort_key: (Optional) How to sort each grouped list in the
        returned dict. Use a string that works with the
        ``.sort_tracts(key=<str>)`` method (e.g., 'i, s, r.ew, t.ns') or
        a lambda function, as you would with the builtin
        ``list.sort(key=<lambda>)`` method. (Defaults to ``None``, i.e.
        not sorted.)

        May optionally pass `sort_key` as a list of sort keys, to be
        applied left-to-right. Here, you may mix and match lambdas and
        ``.sort_tracts()`` strings.

        :param sort_reverse: (Optional) Whether to reverse the sort.
        NOTE: Only has an effect if the ``sort_key`` is passed as a
        lambda -- NOT as a custom string sort key. Defaults to ``False``

        NOTE: If ``sort_key`` was passed as a list, then
        ``sort_reverse`` must be passed as EITHER a single bool that
        will apply to all of the (non-string) sorts, OR as a list or
        tuple of bools that is equal in length to ``sort_key`` (i.e. the
        values in ``sort_key`` and ``sort_reverse`` will be matched up
        one-to-one).

        :return: Depends on which subclass this is method called by. If
        this method is called on a ``TRSList``, will return a dict of
        `TRSList` objects, each containing the ``TRS`` objects with
        matching values of the ``by_attribute``.   If this method is
        called on a ``TractList``, will return a dict of ``TractList``
        objects containing grouped `Tract` objects instead.  (If
        ``by_attribute`` was passed as a list of attribute names, then
        this will return a nested dict, with ``TractList`` objects (or
        ``TRSList`` objects, as applicable) being the deepest values.)
        """
        # Determine whether it's a single-attribute grouping, or multiple.
        this_attribute = by_attribute
        is_multi_group = isinstance(by_attribute, list)
        if is_multi_group:
            by_attribute = by_attribute.copy()
            this_attribute = by_attribute.pop(0)
            if not by_attribute:
                # If this is the last one to run.
                is_multi_group = False

        if not is_multi_group:
            # The `._group()` method handles single-attribute groupings.
            return self._group(
                self, this_attribute, into, sort_key, sort_reverse)

        def add_to_existing_dict(dct_, into_=into):
            """
            Recursively add keys/values to the original ``into`` dict.
            """
            if into_ is None:
                return dct_
            for k_, v_ in dct_.items():
                # This will always be one of two pairs:
                #   a key/TractList (or TRSList) pair (in which case we
                #       have reached the bottom); OR
                #   a key/dict pair (in which case, we need to do
                #       another recursion)
                if isinstance(v_, self.__class__):
                    into_.setdefault(k_, self.__class__())
                    into_[k_].extend(v_)
                else:
                    into_.setdefault(k_, {})
                    add_to_existing_dict(v_, into_=into_[k_])
            return into_

        # Do a single-attribute grouping as our first pass.
        dct = self._group(self, this_attribute)

        # We have at least one more grouping to do, so recursively group
        # each current TractList/TRSList object.
        dct_2 = {}
        for k, tlist in dct.items():
            dct_2[k] = tlist.group_nested(by_attribute=by_attribute, into=None)

        # Unpack dct_2 into the existing dict (`into`), sort, and return.
        dct = add_to_existing_dict(dct_2, into)
        self.sort_grouped(dct, sort_key, sort_reverse)
        return dct

    def group(
            self, by_attribute="twprge", into: dict = None, sort_key=None,
            sort_reverse=False):
        """
        Filter the elements in this list into a dict, keyed by unique
        values of ``by_attribute``, whose values are a custom list of
        the same type as the original (either a `TRSList` or
        `TractList`) of the grouped objects. By default, will filter
        into groups of Tracts (or TRS objects, if working with a
        `TRSList` object) that share Twp/Rge (i.e. ``'twprge'``).

        Pass ``by_attribute`` as a list of attributes to group by
        multiple attributes, in which case the keys of the returned dict
        will be a tuple whose elements line up with the attributes
        listed in ``by_attribute``.

        :param by_attribute: The str name of an attribute of `Tract` (or
        `TRS`) objects. (Defaults to ``'twprge'``). NOTE: Attributes
        must be a hashable type!  (Optionally pass as a list of str
        names of attributes to do multiple groupings.)

        :param into: (Optional) An existing dict into which to group the
        Tracts (or `TRS` objects). If not specified, will create a new
        dict. Use this arg if you need to continue adding Tracts (or
        `TRS` objects) to an existing grouped dict.

        :param sort_key: (Optional) How to sort each grouped list in the
        returned dict. Use a string that works with the
        ``.sort_tracts(key=<str>)`` method (e.g., 'i, s, r.ew, t.ns') or
        a lambda function, as you would with the builtin
        ``list.sort(key=<lambda>)`` method. (Defaults to ``None``, i.e.
        not sorted.)

        May optionally pass `sort_key` as a list of sort keys, to be
        applied left-to-right. Here, you may mix and match lambdas and
        ``.sort_tracts()`` strings.

        :param sort_reverse: (Optional) Whether to reverse the sort.
        NOTE: Only has an effect if the ``sort_key`` is passed as a
        lambda -- NOT as a custom string sort key. Defaults to ``False``

        NOTE: If ``sort_key`` was passed as a list, then
        ``sort_reverse`` must be passed as EITHER a single bool that
        will apply to all of the (non-string) sorts, OR as a list or
        tuple of bools that is equal in length to ``sort_key`` (i.e. the
        values in ``sort_key`` and ``sort_reverse`` will be matched up
        one-to-one).

        :return: A dict of `TractList` (or `TRSList`) objects, each
        containing the objects with matching values of the
        ``by_attribute``.  (If ``by_attribute`` was passed as a list of
        attribute names, then the keys in the returned dict will be a
        tuple whose values line up with the list passed as
        ``by_attribute``.)
        """
        # Determine whether it's a single-attribute grouping, or multiple.
        first_attribute = by_attribute
        is_multi_group = isinstance(by_attribute, list)
        if is_multi_group:
            by_attribute = by_attribute.copy()
            first_attribute = by_attribute.pop(0)
            if not by_attribute:
                # If this is the last one to run.
                is_multi_group = False

        if not is_multi_group:
            # The `._group()` method handles single-attribute groupings.
            return self._group(
                self, first_attribute, into, sort_key, sort_reverse)

        def get_keybase(key_):
            """
            Convert tuple to list and put any other object type in a
            list.  (i.e. make mutable to add an element to the list,
            which we'll then convert back to a tuple to serve as a dict
            key.)
            """
            if isinstance(key_, tuple):
                return list(key_)
            else:
                return [key_]

        dct = self._group(self, first_attribute)
        while by_attribute:
            dct_new = {}
            grp_att = by_attribute.pop(0)
            for k1, v1 in dct.items():
                k1_base = get_keybase(k1)
                dct_2 = self._group(v1, grp_att)
                for k2, v2 in dct_2.items():
                    dct_new[tuple(k1_base + [k2])] = v2
            dct = dct_new

        # Unpack `dct` into the existing dict (`into`), if applicable.
        if isinstance(into, dict):
            for k, tl in dct.items():
                into.setdefault(k, self.__class__())
                into[k].extend(tl)
            dct = into

        # Sort and return.
        self.sort_grouped(dct, sort_key, sort_reverse)
        return dct

    @classmethod
    def _group(
            cls, trstractlist, by_attribute="twprge", into: dict = None,
            sort_key=None, sort_reverse=False):
        """
        INTERNAL USE:
        (Use the public-facing ``.group()`` method.)

        Group the elements in this custom list into a dict of custom
        lists of the same type, keyed by unique values of
        ``by_attribute``. By default, will filter into groups of objects
        that share Twp/Rge (i.e. `'twprge'`).

        :trstractlist: A `TRSList` or `TractList` to be grouped.

        :param by_attribute: Same as for ``.group()`, but MUST BE A STR
        FOR THIS METHOD!

        :param into: Same as for ``.group()``.

        :param sort_key: Same as for ``.group()``.

        :param sort_reverse:  Same as for ``.group()``.

        :return: A dict of custom list objects (each the same type as
        the passed `trstractlist`), each containing the objects with
        matching values of the `by_attribute`.  (Will NOT be a nested
        dict.)
        """
        dct = {}
        for t in trstractlist:
            val = getattr(t, by_attribute, f"{by_attribute}: n/a")
            dct.setdefault(val, cls())
            dct[val].append(t)
        if isinstance(into, dict):
            for k, tl in dct.items():
                into.setdefault(k, cls())
                into[k].extend(tl)
            dct = into
        if not sort_key:
            return dct
        for tl in dct.values():
            tl.custom_sort(key=sort_key, reverse=sort_reverse)
        return dct

    @classmethod
    def sort_grouped(cls, group_dict, sort_key, reverse=False) -> dict:
        """
        Sort the `TractList` objects (or `TRSList` objects) within a
        grouped dict.

        Returns the original ``group_dict``, but with the `TractList`
        (or `TRSList`) objects having been sorted in place.

        :param group_dict: A dict, as returned by a `TractList` or
        `TRSList` grouping method or function (e.g., ``.group()``,
        ``.group_tracts()``, or ``.group_trs()``).

        :param sort_key: How to sort the elements in the lists. (Can be
        any value acceptable to the ``.custom_sort()`` method.)

        :param reverse: (Optional) Whether to reverse lambda sorts.
        (More detail provided in the docs for ``.custom_sort()``.)

        :return: The original ``group_dict``, with the lists inside it
        having been sorted in place.
        """
        if not sort_key:
            return group_dict
        for k, v in group_dict.items():
            if isinstance(v, dict):
                cls.sort_grouped(v, sort_key, reverse)
            else:
                v.custom_sort(key=sort_key, reverse=reverse)
        return group_dict

    @classmethod
    def unpack_group(cls, group_dict: dict, sort_key=None, reverse=False):
        """
        Convert a grouped dict (or nested group dict) of ``TRSList`` or
        ``TractList`` objects into a new single ``TRSList`` or
        ``TractList`` object.

        NOTE: If ``group_dict`` contains ``TRSList`` objects, this
        method must be called as ``TRSList.unpack_group()``.
        Conversely, if ``group_dict`` contains ``TractList`` objects,
        this method must be called as ``TractList.unpack_group()``.

        :param group_dict: A dict, as returned by ``.group()`` or
        ``.group_nested()`` (or a nested dict inside what was returned
        by ``.group_nested()``).

        :param sort_key: (Optional) How to sort the elements in the
        returned list.  NOT applied to the original lists inside the
        dict.  (Can be any value acceptable to the ``.custom_sort()``
        method.)

        :param reverse: (Optional) Whether to reverse lambda sorts.
        (More detail provided in the docs for ``.custom_sort()``.)

        :return: A new `TractList` (or `TRSList`, as applicable).
        """
        tl = cls()

        def unpack(dct):
            # We place recursion within the `unpack_group()` method
            # itself to avoid creating multiple `tl` instances.
            for v_ in dct.values():
                if isinstance(v_, dict):
                    # Recursively unpack nested dicts.
                    unpack(v_)
                else:
                    # Add the elements of this list.
                    tl.extend(v_)
        unpack(group_dict)
        if sort_key:
            tl.custom_sort(sort_key, reverse)
        return tl

    @classmethod
    def _from_multiple(cls, *objects, into=None):
        """
        INTERNAL USE:

        Create a `TractList` or `TRSList` from multiple sources of
        varying types.

        :param objects: For `TractList` objects, may pass any number or
        combination of Tract, PLSSDesc, and/or TractList objects (or
        other list-like element holding any of those object types).
        For `TRSList` objects, may pass any number of `TRS` objects or
        strings in the pyTRS standardized Twp/Rge/Sec format, or
        `TRSList` objects.

        :param into: A new (unused) `TRSList` or `TractList` object.

        :return: The list originally passed as `into`, now containing
        the extracted `Tract` or `TRS` objects.
        """
        if into is None:
            into = cls()
        for obj in objects:
            if isinstance(obj, cls._ok_individuals):
                into.append(obj)
            elif isinstance(obj, cls):
                # Other instances of this class have already been
                # appropriately type-checked.
                into.extend(obj)
            elif isinstance(obj, cls._ok_iterables):
                for obj_deeper in obj:
                    into.append(obj_deeper)
            else:
                # Assume it's another list-like object.
                for obj_deeper in obj:
                    # Elements are appended in place, no need to store var.
                    cls._from_multiple(obj_deeper, into=into)
        return into

    @classmethod
    def _iter_from_multiple(cls, *objects):
        """
        INTERNAL USE:

        Create from multiple elements a generator of `Tract` objects or
        `TRS` objects.

        (Identical to `.from_multiple()`, but returns a generator of
        `Tract` objects or `TRS` objects, rather than a `TractList` or
        `TRSList`.)

        :param objects: For `TractList` objects, may pass any number or
        combination of Tract, PLSSDesc, and/or TractList objects (or
        other list-like element holding any of those object types).
        For `TRSList` objects, may pass any number of `TRS` objects or
        strings in the pyTRS standardized Twp/Rge/Sec format, or
        `TRSList` objects.

        :return: A generator of `Tract` objects (or `TRS` objects, as
        applicable).
        """
        for obj in objects:
            if isinstance(obj, cls._ok_individuals):
                yield cls._verify_individual(obj)
            elif isinstance(obj, cls):
                # Other instances of this class have already been
                # appropriately type-checked.
                yield from obj
            elif isinstance(obj, cls._ok_iterables):
                for obj_deeper in obj:
                    yield cls._verify_individual(obj_deeper)
            else:
                # Assume it's another list-like object.
                for obj_deeper in obj:
                    yield from cls._iter_from_multiple(obj_deeper)


class TractList(_TRSTractList):
    """
    A specialized ``list`` for Tract objects, with added methods for
    compiling and manipulating the data inside the contained Tract
    objects, and for sorting, grouping, and filtering the Tract objects
    themselves.

    NOTE: `TractList` and `TRSList` are subclassed from the same
    superclass and have some of the same functionality for sorting,
    grouping, and filtering.  In the docstrings for many of the methods,
    there will be references to either `TRS` or `Tract` objects, and to
    `TRSList` or `TractList` objects.  To be clear, `TRSList` objects
    hold only `TRS` objects, and `TractList` objects hold only `Tract`
    objects.

    ____ STREAMLINED OUTPUT OF THE PARSED TRACT DATA ____
    These methods have the same effect as in PLSSDesc objects.

    .quick_desc() -- Returns a string of the entire parsed description.

    .tracts_to_dict() -- Compile the requested attributes for each Tract
        into a dict, and returns a list of those dicts.

    .tracts_to_list() -- Compile the requested attributes for each Tract
        into a list, and returns a nested list of those list.

    .iter_to_dict() -- Identical to `.tracts_to_dict()`, but returns a
        generator of dicts for the Tract data.

    .iter_to_list() -- Identical to `.tracts_to_list()`, but returns a
        generator of lists for the Tract data.

    .tracts_to_csv() -- Compile the requested attributes for each Tract
        and write them to a .csv file, with one row per Tract.

    .tracts_to_str() -- Compile the requested attributes for each Tract
        into a string-based table, and return a single string of all
        tables.

    .list_trs() -- Return a list of all twp/rge/sec combinations,
        optionally removing duplicates.


    ____ SORTING / GROUPING / FILTERING TRACTS BY ATTRIBUTE VALUES ____
    .sort_tracts() -- Custom sorting based on the Twp/Rge/Sec or
    original creation order of each Tract. Can also take parameters from
    the built-in ``list.sort()`` method.

    .group() -- Group Tract objects into a dict of TractList objects,
    based on their shared attribute values (e.g., by Twp/Rge), and
    optionally sort them.

    .filter() -- Get a new TractList of Tract objects that match some
    condition, and optionally remove them from the original TractList.

    .filter_errors() -- Get a new TractList of Tract objects whose Twp,
    Rge, and/or Section were an error or undefined, and optionally
    remove them from the original TractList.
    """

    # A TractList holds only Tract objects. But Tract objects can be
    # extracted from these types and added to the list.
    _ok_individuals = (Tract,)
    _ok_iterables = (PLSSDesc,)
    _typeerror_msg = "TractList will accept only type `pytrs.Tract`."

    def __init__(self, iterable=()):
        """
        :param iterable: An iterable (or `PLSSDesc`) containing `Tract`
        objects.
        """
        _TRSTractList.__init__(self, iterable)

    def __str__(self):
        return f"TractList ({len(self)}): {self.snapshot_inside()}"

    def config_tracts(self, config):
        """
        Reconfigure all of the Tract objects in this TractList.

        :param config: Either a pytrs.Config object, or a string of
        parameters to configure how the Tract object should be parsed.
        (See documentation on pytrs.Config objects for optional config
        parameters.)
        :return: None
        """
        for tract in self:
            tract.config = config
        return None

    def parse_tracts(
            self,
            config=None,
            clean_qq=None,
            include_lot_divs=None,
            qq_depth_min=None,
            qq_depth_max=None,
            qq_depth=None,
            break_halves=None):
        """
        Parse (or re-parse) all of the Tract objects in this TractList
        into lots/QQ's using the specified parameters. Will pull parsing
        parameters from each Tract object's own ``.config`` (unless
        otherwise configured here).  Optionally reconfigure each Tract
        object prior to parsing into lots/QQs by using the ``config=``
        parameter here, or other kwargs.  (The named kwargs will take
        priority over ``config``, if there is a conflict.)

        The parsed data will be committed to the Tract objects'
        attributes, overwriting data from a prior parse.

        :param config: (Optional) New Config parameters to apply to each
        Tract before parsing.
        :param clean_qq: Same as in ``Tract.parse()`` method.
        :param include_lot_divs: Same as in ``Tract.parse()`` method.
        :param qq_depth_min: Same as in ``Tract.parse()`` method.
        :param qq_depth_max: Same as in ``Tract.parse()`` method.
        :param qq_depth: Same as in ``Tract.parse()`` method.
        :param break_halves: Same as in ``Tract.parse()`` method.
        :return: None
        """
        if config:
            self.config_tracts(config)
        for t in self:
            t.parse(
                clean_qq=clean_qq,
                include_lot_divs=include_lot_divs,
                qq_depth_min=qq_depth_min,
                qq_depth_max=qq_depth_max,
                qq_depth=qq_depth,
                break_halves=break_halves)
        return None

    sort_tracts = _TRSTractList.custom_sort
    # Aliases to mirror `sort_tracts`
    filter_tracts = _TRSTractList.filter
    filter_tracts_errors = _TRSTractList.filter_errors
    group_tracts = _TRSTractList.group

    @staticmethod
    def sort_grouped_tracts(tracts_dict, sort_key, reverse=False) -> dict:
        """
        Sort TractLists within a dict of grouped Tracts. Also works on
        a nested dict (i.e. when multiple groupings were done).

        Returns the original ``tracts_dict``, but with the TractList
        objects having been sorted in-situ.

        :param tracts_dict: A dict, as returned by a TractList grouping
        method or function (e.g., ``TractList.group()`` or
        ``group_tracts()``).
        :param sort_key: How to sort the Tracts. (Can be any value
        acceptable to the ``TractList.sort_tracts()`` method.)
        :param reverse: (Optional) Whether to reverse lambda sorts.
        (More detail provided in the docs for
        ``TractList.sort_tracts()``.)
        :return: The original ``tracts_dict``, with the TractList
        objects having been sorted in-situ.
        """
        return _TRSTractList.sort_grouped(
            group_dict=tracts_dict, sort_key=sort_key, reverse=reverse)

    def tracts_to_dict(self, *attributes) -> list:
        """
        Compile the data for each Tract object into a dict containing
        the requested attributes only, and return a list of those dicts
        (the returned list being equal in length to this TractList
        object).

        :param attributes: The names (strings) of whichever attributes
        should be included (see documentation on `pytrs.Tract` objects
        for the names of relevant attributes).

        :Example:

        txt = '''154N-97W
        Sec 14: NE/4
        Sec 15: Northwest Quarter, North Half South West Quarter'''
        d_obj = PLSSDesc(txt)
        tl_obj = d_obj.parse(parse_qq=True, commit=False)
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
        attributes = _clean_attributes(attributes)
        return [t.to_dict(attributes) for t in self]

    def tracts_to_list(self, *attributes) -> list:
        """
        Compile the data for each Tract object into a list containing
        the requested attributes only, and return a nested list of those
        lists (the returned list being equal in length to this TractList
        object).

        :param attributes: The names (strings) of whichever attributes
        should be included (see documentation on `pytrs.Tract` objects
        for the names of relevant attributes).

        :Example:

        txt = '''154N-97W
        Sec 14: NE/4
        Sec 15: Northwest Quarter, North Half South West Quarter'''
        d_obj = PLSSDesc(txt)
        tl_obj = d_obj.parse(parse_qq=True, commit=False)
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
        attributes = _clean_attributes(attributes)
        return [t.to_list(attributes) for t in self]

    def tracts_to_str(self, *attributes) -> str:
        """
        Compile the data for all Tract objects, containing the requested
        attributes only, and return a single string of the data.

        :param attributes: The names (strings) of whichever attributes
        should be included (see documentation on `pytrs.Tract` objects
        for the names of relevant attributes).

        :Example:

        txt = '''154N-97W
        Sec 14: NE/4
        Sec 15: Northwest Quarter, North Half South West Quarter'''
        d_obj = PLSSDesc(txt)
        tl_obj = d_obj.parse(parse_qq=True, commit=False)
        tl_obj.tracts_to_str('trs', 'desc', 'qqs')

        Example returns a multi-line string that looks like this when
        printed:

            Tract 1 / 2
            trs  : 154n97w14
            desc : NE/4
            qqs  : NENE, NWNE, SENE, SWNE

            Tract 2 / 2
            trs  : 154n97w15
            desc : Northwest Quarter, North Half South West Quarter
            qqs  : NENW, NWNW, SENW, SWNW, NESW, NWSW
        """
        attributes = _clean_attributes(attributes)

        # How far to justify the attribute names in the output str:
        jst = max([len(att) for att in attributes]) + 1
        # For justifying linebreaks within a value.
        jst_linebreak = f"\n{' ' * (jst + 2)}"

        total_tracts = len(self)
        all_tract_data = ""
        for i, t_dct in enumerate(self.tracts_to_dict(attributes), start=1):
            tract_data = f"\n\nTract {i} / {total_tracts}"
            if i == 1:
                tract_data = f"Tract {i} / {total_tracts}"
            for att_name, v in t_dct.items():
                # Flatten lists/tuples, but leave everything else as-is
                if isinstance(v, (list, tuple)):
                    v = ", ".join(flatten(v))
                v = str(v).replace("\n", jst_linebreak)
                # Justify attribute name and report its value
                tract_data = f"{tract_data}\n{att_name.ljust(jst, ' ')}: {v}"
            all_tract_data = f"{all_tract_data}{tract_data}"
        return all_tract_data

    def tracts_to_csv(
            self, attributes, fp, mode, nice_headers=False):
        """
        Write Tract data to a .csv file.

        :param attributes: a list of names (strings) of whichever
        attributes should be included (see documentation on
        `pytrs.Tract` objects for the names of relevant attributes).
        :param fp: The filepath of the .csv file to write to.
        :param mode: The `mode` in which to open the file we're
        writing to. Either 'w' (new file) or 'a' (continue a file).
        :param nice_headers: By default, this method will use the
        attribute names as headers. To use custom headers, pass to
        ``nice_headers=`` any of the following:
        -- a list of strings to use. (Should be equal in length to the
        list passed as ``attributes``, but will not raise an error if
        that's not the case. The resulting column headers will just be
        fewer than the actual number of columns.)
        -- a dict, keyed by attribute name, and whose values are the
        corresponding headers. (Any missing keys will use the attribute
        name.)
        -- `True` -> use the values in the ``Tract.ATTRIBUTES`` dict for
        headers. (WARNING: Any value passed that is not a list or dict
        and that evaluates to `True` will cause this behavior.)
        -- If not specified (i.e. None), will just use the attribute
        names themselves.
        :return: None
        """
        if not fp:
            raise ValueError("`fp` must be a filepath")
        from pathlib import Path
        fp = Path(fp)
        headers = True
        if fp.exists() and mode == "a":
            headers = False

        import csv
        attributes = _clean_attributes(attributes)
        header_row = Tract.get_headers(attributes, nice_headers)

        def scrub_row(data):
            """Convert lists/dicts in a row to strings."""
            scrubbed = []
            for elem in data:
                if isinstance(elem, dict):
                    elem = ','.join([f"{k}:{v}" for k, v in elem.items()])
                elif isinstance(elem, (list, tuple)):
                    elem = ', '.join(elem)
                scrubbed.append(elem)
            return scrubbed

        with open(fp, mode=mode, newline="") as file:
            writer = csv.writer(file)
            if headers:
                writer.writerow(header_row)
            for tract in self:
                row = tract.to_list(attributes)
                row = scrub_row(row)
                writer.writerow(row)
        return None

    def iter_to_dict(self, *attributes):
        """
        Identical to `.tracts_to_dict()`, but returns a generator of
        dicts, rather than a list of dicts.

        :param attributes: The names (strings) of whichever attributes
        should be included (see documentation on `pytrs.Tract` objects
        for the names of relevant attributes).

        :return: A generator of data pulled from each Tract, in the form
        of a dict.
        """
        for tract in self:
            yield tract.to_dict(attributes)

    def iter_to_list(self, *attributes):
        """
        Identical to `.tracts_to_dict()`, but returns a generator of
        lists, rather than a list of lists.

        :param attributes: The names (strings) of whichever attributes
        should be included (see documentation on `pytrs.Tract` objects
        for the names of relevant attributes).

        :return: A generator of data pulled from each Tract, in the form
        of a list.
        """
        for tract in self:
            yield tract.to_list(attributes)

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
        tl_obj = d_obj.parse(parse_qq=True, commit=False)
        tl_obj.quick_desc()

        Example returns a multi-line string that looks like this when
        printed:

            154n97w14: NE/4
            154n97w15: Northwest Quarter, North Half South West Quarter
        """
        dlist = [t.quick_desc(delim=delim) for t in self]
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

    def pretty_desc(self, word_sec="Sec ", justify_linebreaks=None):
        """
        Get a neatened-up description of all of the Tract objects in
        this TractList.

        Groups Tracts by Twp/Rge, but only to the extent possible while
        maintaining the current sort order.

        :param word_sec: How the word 'Section' should appear, INCLUDING
        the following white space (if any). (Defaults to ``'Sec '``).
        :param justify_linebreaks: (Optional) A string specifying how to
        justify new lines after a linebreak (e.g., ``'\t'`` for a tab).
        If not specified, will align new lines with the line above. To
        use no justification at all, pass an empty string.
        :return: a str of the compiled description.
        """
        jst = " " * (len(word_sec) + 4)
        if justify_linebreaks:
            jst = justify_linebreaks
        if not self:
            return None
        to_print = []
        cur_twprge = self[0].twprge
        cur_group = []
        for t in self:
            if t.twprge == cur_twprge:
                cur_group.append(t)
            else:
                to_print.append((cur_twprge, cur_group))
                cur_twprge = t.twprge
                cur_group = [t]
        # Append the final group.
        to_print.append((cur_twprge, cur_group))
        dsc = ""
        for twprge, group in to_print:
            dsc = f"{dsc}\n{TRS(twprge).pretty_twprge()}"
            for tract in group:
                dsc = f"{dsc}\n{word_sec}{tract.sec}: "
                tdesc = tract.desc.replace("\n", f"\n{jst}")
                dsc = f"{dsc}{tdesc}"
        return dsc.strip()

    def pretty_print_desc(self, word_sec="Sec ", justify_linebreaks=None):
        """
        Print a neatened-up description of all of the Tract objects in
        this TractList.

        Groups Tracts by Twp/Rge, but only to the extent possible while
        maintaining the current sort order.

        :param word_sec: How the word 'Section' should appear, INCLUDING
        the following white space (if any). (Defaults to ``'Sec '``).
        :param justify_linebreaks: (Optional) A string specifying how to
        justify new lines after a linebreak (e.g., ``'\t'`` for a tab).
        If not specified, will align new lines with the line above. To
        use no justification at all, pass an empty string.
        :return: None (prints to console).
        """
        print(self.pretty_desc(word_sec, justify_linebreaks))

    def print_data(self, *attributes) -> None:
        """
        Simple printing of the arg-specified attributes for each Tract
        in this TractList.
        """
        print(self.tracts_to_str(attributes))
        return

    def list_trs(self, remove_duplicates=False):
        """
        Return a list all the TRS's in this `TractList`. Optionally
        remove duplicates with remove_duplicates=True.
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

    @classmethod
    def from_multiple(cls, *objects):
        """
        Create a `TractList` from multiple sources, which may be any
        number and combination of `Tract`, `PLSSDesc`, and `TractList`
        objects (or other iterable holding any of those object types).

        :param objects: Any number or combination of `Tract`,
        `PLSSDesc`, and/or `TractList` objects (or other iterable
        holding any of those object types).

        :return: A new `TractList` object containing all of the
        extracted `Tract` objects.
        """
        # This is (re-)defined from the superclass only in order to have
        # an accurate docstring (and to simplify the signature).
        return cls._from_multiple(objects)

    @classmethod
    def iter_from_multiple(cls, *objects):
        """
        Create from multiple sources a generator of `Tract` objects.

        (Identical to `.from_multiple()`, but returns a generator of
        `Tract` objects, rather than a `TractList`.)

        :param objects: Any number or combination of `Tract`,
        `PLSSDesc`, and/or `TractList` objects (or other iterable
        holding any of those object types).

        :return: A generator of Tract objects.
        """
        # This is (re-)defined from the superclass only in order to have
        # an accurate docstring.
        yield from cls._iter_from_multiple(objects)


class TRSList(_TRSTractList):
    """
    A specialized ``list`` for ``TRS`` objects, with added methods for
    sorting, grouping, and filtering the ``TRS`` objects.

    NOTE: `TRSList` and `TractList` are subclassed from the same
    superclass and have some of the same functionality for sorting,
    grouping, and filtering.  In the docstrings for many of the methods,
    there will be references to either `TRS` or `Tract` objects, and to
    `TRSList` or `TractList` objects.  To be clear, `TRSList` objects
    hold only `TRS` objects, and `TractList` objects hold only `Tract`
    objects.

    ____ ADDING TWP/RGE/SEC's TO THE TRSLIST ____
    A ``TRSList`` will hold only ``TRS`` objects. However, if you try to
    add a string to it, it will first be converted to a ``TRS`` object.
    Similarly, if you try to add a ``Tract`` object, its ``.trs``
    attribute will be extracted and converted to a ``TRS`` object, which
    then gets added to the list (the original ``Tract`` itself is not).

    ``TRSList`` can also be created from a ``PLSSDesc``, ``TractList``,
    or other iterable containing ``Tract`` objects (the ``.trs``
    attribute for each ``Tract`` will be extracted and converted to a
    ``TRS`` object then added to the resulting ``TRSList``).

    These are all acceptable:
        ```
        trs_list1 = pytrs.TRSList(['154n97w14', '154n97w15'])
        trs_list2 = pytrs.TRSList([pytrs.TRS('154n97w14')])
        trs_list3 = pytrs.TRSList([tract_object_1, tract_object_2])
        trs_list4 = pytrs.TRSList(plssdesc_obj)
        ```
    (Note that the ``PLSSDesc`` object is passed directly, rather than
    inside a list.)

    To robustly create a list of ``TRS`` objects from multiple objects
    of different types, look into ``TRS.from_multiple()``.

        ```
        trs_list5 = pytrs.TRSList.from_multiple(
            '154n97w14',
            pytrs.TRS('154n97w15'),
            tract_object_1,
            some_tract_list,
            some_other_trs_list)
        ```

    ____ STREAMLINED OUTPUT OF THE TWP/RGE/SEC DATA ____
    .to_strings() -- Return a plain list of all ``TRS`` objects,
    converted to strings.

    ____ SORTING / GROUPING / FILTERING ``TRS`` BY ATTRIBUTE VALUES ____
    .sort_trs() -- Custom sorting based on the Twp/Rge/Sec. Can also
    take parameters from the built-in ``list.sort()`` method.

    .group() -- Group ``TRS`` objects into a dict of ``TRSList``
    objects, based on their shared attribute values (e.g., by Twp/Rge),
    and optionally sort them.

    .filter() -- Get a new ``TRSList`` of ``TRS`` objects that match
    some condition, and optionally remove them from the original
    ``TRSList``.

    .filter_errors() -- Get a new ``TRSList`` of ``TRS`` objects whose
    Twp, Rge, and/or Section were an error or undefined, and optionally
    remove them from the original ``TRSList``.
    """

    # A TRSList holds only TRS objects. But these types can be processed
    # into individual TRS objects, which are then added.
    _ok_individuals = (str, TRS, Tract)
    _ok_iterables = (TractList, PLSSDesc)
    _typeerror_msg = (
        "TRSList will accept only types (`str`, `pytrs.TRS`, `pytrs.Tract`)."
    )

    def __init__(self, iterable=()):
        """
        :param iterable: An iterable (or `PLSSDesc`) containing any of
        the following:
        -- `TRS` objects
        -- strings (which will be converted to `TRS` objects)
        -- `Tract` objects (from which the `TRS` will be extracted and
            added to the list)
        """
        _TRSTractList.__init__(self, iterable)

    @classmethod
    def _handle_type_specially(cls, obj):
        """
        INTERNAL USE:
        
        -- Pass `TRS` objects through.
        -- Convert encountered strings to `TRS` objects.
        -- Extract from encountered `Tract` objects the `.trs` attribute
            and convert it to `TRS` object.
        """
        if isinstance(obj, TRS):
            return obj
        if isinstance(obj, str):
            return TRS(obj)
        if isinstance(obj, Tract):
            return TRS(obj.trs)
        raise TypeError(f"{cls._typeerror_msg} Cannot accept {type(obj)}")
    
    def __str__(self):
        return f"TRSList ({len(self)}): {str([elem.trs for elem in self])}"

    def to_strings(self):
        """
        Get the Twp/Rge/Sec as a string from each element in this list.
        :return: A new (plain) list containing the Twp/Rge/Sec's as
        strings.
        """
        return [trs_obj.trs for trs_obj in self]

    def contains(self, trs, match_all=False) -> bool:
        """
        Check whether this `TRSList` contains one or more specific
        Twp/Rge/Sec.  By default, a match of ANY Twp/Rge/Sec will return
        True.  But to look for matches of ALL Twp/Rge/Sec, use
        `match_all=True`.  (Duplicates are ignored.)

        :param trs: The Twp/Rge/Section(s) to look for in this TRSList.
        May pass as a TRS object, a string in the standard pyTRS format,
        or a TRSList.  May also pass a Tract, a parsed PLSSDesc object,
        a TractList.  May also or an iterable containing any combination
        of those types. (Note: If a `Tract`, `PLSSDesc`, or `TractList`
        is passed, the `.trs` attribute in each `Tract` will be looked
        for.)

        :param match_all: If we need to check whether ALL of the
        Twp/Rge/Sections are contained in this `TRSList` (ignoring
        duplicates).  Defaults to False (i.e. a match of ANY Twp/Rge/Sec
        will be interpreted as True).

        :return: A bool, whether or not any of the Twp/Rge/Sec in `trs`
        are found in this `TRSList`.
        """
        # Convert `trs` to a TRS object (or if `trs` is an iterable,
        # convert all elements within it to `TRS` objects) and add to a
        # TRSList. Convert the resulting TRSList to a set.
        look_for = set(TRSList.from_multiple(trs).to_strings())
        contained = set(self.to_strings())
        if match_all:
            return len(look_for - contained) == 0
        return len(contained.intersection(look_for)) > 0

    sort_trs = _TRSTractList.custom_sort
    # Aliases to mirror `sort_trs`
    filter_trs = _TRSTractList.filter
    filter_trs_errors = _TRSTractList.filter_errors
    group_trs = _TRSTractList.group
    sort_grouped_trs = _TRSTractList.sort_grouped

    @classmethod
    def from_multiple(cls, *objects):
        """
        Create a `TRSList` from multiple sources.

        :param objects: May pass any number or combination of `TRS`
        objects or strings in the pyTRS standardized Twp/Rge/Sec format,
        or `TRSList` objects, or other list-like objects containing
        those object types.  (Any strings will be interpreted as
        Twp/Rge/Sec and converted to `TRS` objects.)

        :return: A `TRSList` containing the `TRS` objects.
        """
        # This is (re-)defined from the superclass only in order to have
        # an accurate docstring (and to simplify the signature).
        return cls._from_multiple(objects)

    @classmethod
    def iter_from_multiple(cls, *objects):
        """
        Create from multiple sources a generator of `TRS` objects.

        (Identical to `.from_multiple()`, but returns a generator of
        `TRS` objects, rather than a `TRSList`.)

        :param objects: May pass any number or combination of `TRS`
        objects or strings in the pyTRS standardized Twp/Rge/Sec format,
        or `TRSList` objects, or other list-like objects containing
        those object types.

        :return: A generator of `TRS` objects.
        """
        # This is (re-)defined from the superclass only in order to have
        # an accurate docstring.
        yield from cls._iter_from_multiple(objects)


class Config:
    """
    A class to configure how PLSSDesc and Tract objects should be
    parsed.

    For a list of all parameter options, printed to console:
        `pytrs.utils.config_parameters()`

    Or launch the Config GUI application:
        `pytrs.utils.config_util()`

    For a guide to using Config objects general, printed to console:
        `pytrs.utils.config_help()`

    All possible parameters (call `pytrs.utils.config_parameters()` for
    definitions) -- any unspecified parameters will fall back to
    default parsing behavior:
        -- 'n'  <or>  'default_ns.n'  vs.  's'  <or>  'default_ns.s'
        -- 'e'  <or>  'default_ew.e'  vs.  'w'  <or>  'default_ew.w'
        -- 'init_parse'  vs.  'init_parse.False'
        -- 'parse_qq'  vs.  'parse_qq.False'
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
        'layout',
        'wait_to_parse',
        'parse_qq',
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
        'wait_to_parse',
        'parse_qq',
        'clean_qq',
        'include_lot_divs',
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
        'parse_qq',
        'clean_qq',
        'include_lot_divs',
        'ocr_scrub',
        'qq_depth',
        'qq_depth_min',
        'qq_depth_max',
        'break_halves'
    )

    def __init__(self, config_text=None, config_name=''):
        """
        Compile a Config object from a string `config_text=`, with
        optional kwarg `config_name=` that does not affect parsing.

        Pass config parameters as a single string, with each parameter
        separated by comma. Spaces are optional and have no effect.
            ex: 'n,s,clean_qq,include_lot_divs.False'

        All possible parameters (call `pytrs.utils.config_parameters()`
        for definitions) -- any unspecified parameters will fall back to
        default parsing behavior:
        -- 'n'  <or>  'default_ns.n'  vs.  's'  <or>  'default_ns.s'
        -- 'e'  <or>  'default_ew.e'  vs.  'w'  <or>  'default_ew.w'
        -- 'wait_to_parse'  vs.  'wait_to_parse.False'
        -- 'parse_qq'  vs.  'parse_qq.False'
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
            raise ConfigError(config_text)
        self.config_text = config_text
        self.config_name = config_name

        # Default all other attributes to `None`:
        self.default_ns = None
        self.default_ew = None
        self.layout = None
        self.wait_to_parse = None
        self.parse_qq = None
        self.clean_qq = None
        self.require_colon = None
        self.include_lot_divs = None
        self.ocr_scrub = None
        self.segment = None
        self.qq_depth = None
        self.qq_depth_min = None
        self.qq_depth_max = None
        self.break_halves = None

        # Remove all spaces from config_text:
        config_text = config_text.replace(' ', '')

        # Separate config parameters with ','  or  ';'
        config_lines = re.split(r'[;,]', config_text)

        # Parse each 'attrib.val' pair and commit to this Config object.
        for line in config_lines:

            if line == '':
                continue

            if re.split(r'[\.=]', line)[0] in Config._BOOL_TYPE_ATTRIBUTES:
                # If string is the name of an attribute that will be stored
                # as a bool, default to `True` (but will be overruled in
                # _set_str_to_values() if specified otherwise):
                self._set_str_to_values(line, default_bool=True)
            elif line in PLSSDesc._LEGAL_NS:
                # Specifying N/S can be done with just a string (there's
                # nothing else it can mean in config context.)
                self.default_ns = line
            elif line in PLSSDesc._LEGAL_EW:
                # Specifying E/W can be done with just a string (there's
                # nothing else it can mean in config context.)
                self.default_ew = line
            elif line in _IMPLEMENTED_LAYOUTS:
                # Specifying layout can be done with just a string
                # (there's nothing else it can mean in config context.)
                self.layout = line
            else:
                # This method handles any other parameter.
                self._set_str_to_values(line)

    def __str__(self):
        return self.decompile_to_text()

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
        if isinstance(parent, PLSSDesc) and not suppress_layout:
            config.layout = parent.layout
        else:
            config.layout = None
        config.init_parse = parent.init_parse
        config.parse_qq = parent.parse_qq
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


class PLSSParser:
    """
    INTERNAL USE:

    A class to handle the heavy lifting of parsing ``PLSSDesc`` objects
    into ``Tract`` objects. Not intended for use by the end-user. (All
    functionality can be triggered by appropriate ``PLSSDesc`` methods.)

    NOTE: All parsing parameters must be locked in before initializing
    the PLSSParser. Upon initializing, the parse will be automatically
    triggered and cannot be modified.

    The ``PLSSDesc.parse()`` method is actually a wrapper for
    initializing a ``PLSSParser`` object, and for extracting the
    relevant attributes from it.
    """

    # constants for the different markers we'll use
    TEXT_START = 'text_start'
    TEXT_END = 'text_end'
    TR_START = 'tr_start'
    TR_END = 'tr_end'
    SEC_START = 'sec_start'
    SEC_END = 'sec_end'
    MULTISEC_START = 'multiSec_start'
    MULTISEC_END = 'multiSec_end'

    # Text that often comes between Section number and Twp/Rge
    SEC_TWP_INTERVENERS = (
        'in',
        'of',
        ',',
        'all of',
        'all in',
        'within',
        'all within',
        'lying within',
        'that lies within',
        'lying in'
    )

    # These attributes have corresponding attributes in PLSSDesc objects.
    UNPACKABLES = (
        "tracts",
        "w_flags",
        "e_flags",
        "w_flag_lines",
        "e_flag_lines",
        "current_layout"
    )

    def __init__(
            self,
            text,
            mandated_layout=None,
            default_ns=PLSSDesc.MASTER_DEFAULT_NS,
            default_ew=PLSSDesc.MASTER_DEFAULT_EW,
            ocr_scrub=False,
            clean_up=None,
            parse_qq=False,
            clean_qq=False,
            require_colon=_DEFAULT_COLON,
            segment=False,
            qq_depth_min=2,
            qq_depth_max=None,
            qq_depth=None,
            break_halves=False,
            handed_down_config=None,
            parent: PLSSDesc = None
    ):
        """
        NOTE: Documentation for this class is not maintained here. See
        instead ``PLSSDesc.parse()``, which essentially serves as a
        wrapper for this class.
        """
        # Initial variables to control the parse.
        self.orig_desc = text
        self.preprocessor = PLSSPreprocessor(
            text, default_ns, default_ew, ocr_scrub)
        self.text = self.preprocessor.text
        self.current_layout = None
        self.clean_up = clean_up
        self.parse_qq = parse_qq
        self.clean_qq = clean_qq
        self.require_colon = require_colon
        self.segment = segment
        self.qq_depth_min = qq_depth_min
        self.qq_depth_max = qq_depth_max
        self.qq_depth = qq_depth
        self.break_halves = break_halves
        # For handing down to generated Tract objects
        self.handed_down_config = handed_down_config
        self.mandated_layout = mandated_layout
        self.source = None

        # Generated variables / parsed data.
        self.tracts = TractList()
        self.w_flags = []
        self.e_flags = []
        self.w_flag_lines = []
        self.e_flag_lines = []

        # Pull pre-existing flags from the parent PLSSDesc, if applicable.
        if parent:
            self.w_flags = parent.w_flags.copy()
            self.e_flags = parent.e_flags.copy()
            self.w_flag_lines = parent.w_flag_lines.copy()
            self.e_flag_lines = parent.e_flag_lines.copy()
            self.source = parent.source

        # Unpack `self.preprocessor.fixed_twprges` into w_flags.
        if self.preprocessor.fixed_twprges:
            fixed = "//".join(self.preprocessor.fixed_twprges)
            self.w_flags.append(f"T&R_fixed<{fixed}>")
            self.w_flag_lines.append((f"T&R_fixed<{fixed}>", fixed))

        self.parse_cache = {}
        self.reset_cache()

        self.parse()

    def reset_cache(self):
        self.parse_cache = {
            "text_block": "",
            "markers_list": [],
            "markers_dict": {},
            "twprge_list": [],
            "sec_list": [],
            "multisec_list": [],
            "new_tract_components": [],
            "unused_text": [],
            "unused_with_context": [],
            "second_pass_match": False,
            "all_twprge_matches": [],
            "all_sec_matches": [],
            "all_multisec_matches": [],
            "w_flags_staging": [],
            "w_flag_lines_staging": []
        }

    def parse(self):
        """
        Parse the full PLSS description.

        NOTE: Documentation for this method is mostly maintained under
        ``PLSSDesc.parse()``, which essentially serves as a wrapper for
        the PLSSParser class and this method.
        """

        text = self.text
        layout = self.safe_deduce_layout(text)
        clean_up = self.clean_up
        parse_qq = self.parse_qq
        clean_qq = self.clean_qq
        require_colon = self.require_colon
        segment = self.segment
        qq_depth_min = self.qq_depth_min
        qq_depth_max = self.qq_depth_max
        qq_depth = self.qq_depth
        break_halves = self.break_halves

        self.current_layout = layout

        if layout not in _IMPLEMENTED_LAYOUTS:
            raise ValueError(f"Non-implemented layout '{layout}'")

        # Config object for passing down to Tract objects.
        config = self.handed_down_config

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

        if len(text) == 0 or not isinstance(text, str):
            self.e_flags.append('noText')
            self.e_flag_lines.append(
                ('noText', '<No text was fed into the program.>'))
            return self

        if (not isinstance(clean_up, bool)
                and layout in [TRS_DESC, DESC_STR, S_DESC_TR, TR_DESC_S]):
            # Default `clean_up` to True only for these layouts.
            clean_up = True

        # ----------------------------------------
        # If doing a segment parse, break it up into segments now
        if segment:
            # Segment text into blocks, based on T&Rs that match our
            # layout requirements
            twprge_txt_blocks, discard_txt_blox = self._segment_by_tr(
                text, layout=layout, twprge_first=None)

            # Append any discard text to the w_flags
            for txt_block in discard_txt_blox:
                self.w_flags.append(f"Unused_desc_<{txt_block}>")
                self.w_flag_lines.append(
                    (f"Unused_desc_<{txt_block}>", txt_block))

        else:
            # If not segmented parse, pack entire text into list, with
            # a leading empty str (to mirror the output of the
            # _segment_by_tr() function)
            twprge_txt_blocks = [('', text)]

        # ----------------------------------------
        # Parse each segment into Tracts.
        for txt_block in twprge_txt_blocks:
            use_layout = layout
            if segment and layout != COPY_ALL:
                # Let the segment parser deduce layout for each text_block.
                use_layout = None
            self._parse_segment(
                txt_block[1], clean_up=clean_up, require_colon=require_colon,
                layout=use_layout, handed_down_config=config, clean_qq=clean_qq,
                qq_depth_min=qq_depth_min, qq_depth_max=qq_depth_max,
                qq_depth=qq_depth, break_halves=break_halves)

        # If we've still not discovered any Tracts, run a final parse in
        # layout COPY_ALL, and include appropriate errors.
        if not self.tracts:
            self._parse_segment(
                    text, layout=COPY_ALL, clean_up=False, require_colon=False,
                    handed_down_config=config,
                    clean_qq=clean_qq, qq_depth_min=qq_depth_min,
                    qq_depth_max=qq_depth_max, qq_depth=qq_depth,
                    break_halves=break_halves)
            self.e_flags.append('unrequested_copy_all')

        for tract in self.tracts:
            if tract.trs.startswith(TRS._ERR_TWPRGE):
                self.e_flags.append(_E_FLAG_TWPRGE_ERR)
                self.e_flag_lines.append(
                    (_E_FLAG_TWPRGE_ERR, f"{tract.trs}:{tract.desc}"))
            if tract.trs.endswith(TRS._ERR_SEC):
                self.e_flags.append(_E_FLAG_SECERR)
                self.e_flag_lines.append(
                    (_E_FLAG_SECERR, f"{tract.trs}:{tract.desc}"))

        # Check for warning flags (and a couple error flags).
        # Note that .gen_flags() is being run on `flag_text`, not `text`.
        self.gen_flags()

        # We want each Tract to have the entire PLSSDesc's warnings,
        # because the program can't automatically tell which issues
        # apply to which Tracts. (This is an ambiguity that often exists
        # in the data, even when humans read it.) So for robust data, we
        # apply flags from the whole PLSSDesc to each Tract.
        # It will only unpack the flags and flag_lines, because that's
        # all that is relevant to a Tract. Also apply tract_num (i.e.
        # orig_index).
        # We also take any wFlags and eFlags from the PLSSDesc object
        # that may have been generated prior to calling .parse()
        # (inherited from `parent` when this PLSSParser was initialized)
        # and those get passed down to each Tract object too.

        w_flags = self.w_flags.copy()
        w_flag_lines = self.w_flag_lines.copy()
        e_flags = self.e_flags.copy()
        e_flag_lines = self.e_flag_lines.copy()
        tract_num = 0
        for tract in self.tracts:

            # If we wanted to parse to lots/QQ's, we do it now for all
            # generated Tracts.
            if parse_qq:
                tract.parse()

            # Swap flags.
            w_flags.extend(tract.w_flags)
            w_flag_lines.extend(tract.w_flag_lines)
            e_flags.extend(tract.e_flags)
            e_flag_lines.extend(tract.e_flag_lines)
            tract.w_flags = self.w_flags + tract.w_flags
            tract.w_flag_lines = self.w_flag_lines + tract.w_flag_lines
            tract.e_flags = self.e_flags + tract.e_flags
            tract.e_flag_lines = self.e_flag_lines + tract.e_flag_lines

            # And hand down the `.source` and `.orig_desc` attributes to
            # each of the Tract objects:
            tract.source = self.source
            tract.orig_desc = self.orig_desc

            # And apply the tract_num for each Tract object:
            tract.orig_index = tract_num
            tract_num += 1

        # Set the flags/lines back to the newly compiled lists
        self.w_flags = w_flags
        self.w_flag_lines = w_flag_lines
        self.e_flags = e_flags
        self.e_flag_lines = e_flag_lines

        # Return the list of identified `Tract` objects (ie. a TractList object)
        return self.tracts

    def safe_deduce_layout(self, text, candidates=None, override=False):
        """
        Same effect as `.deduce_layout()`, except that it will defer to
        the mandated layout, if one was specified at init. Override the
        safety with ``override=True`` (False by default) -- for example,
        if deducing the layout of a *segment* of the original text,
        rather than the entirety of the original text.

        :param text: Same as in `.deduce_layout()`
        :param candidates: Same as in `.deduce_layout()`
        :param override: A bool, whether to override the safety
        :return: The mandated_layout, if it was specified at init;
        otherwise, the algorithm-deduced layout.
        """
        layout = self.mandated_layout
        if layout is None or override:
            layout = PLSSParser.deduce_layout(text, candidates)
        return layout

    @staticmethod
    def deduce_layout(text, candidates=None):
        """
        Deduce the layout of the description.

        :param text: The text, whose layout is to be deduced.
        :param candidates: A list of which layouts are to be considered.
        If passed as `None` (the default), it will consider all
        currently implemented meaningful layouts (i.e. 'TRS_desc',
        'desc_STR', 'S_desc_TR', and 'TR_desc_S'), but will also
        consider 'copy_all' if an apparently flawed description is
        found. If specifying fewer than all candidates, ensure that at
        least one layout from _IMPLEMENTED_LAYOUTS is in the list.
        (Strings not in _IMPLEMENTED_LAYOUTS will have no effect.)
        :return: Returns the algorithm's best guess at the layout (i.e.
        a string).
        """

        if not candidates:
            candidates = [TRS_DESC, DESC_STR, S_DESC_TR, TR_DESC_S]

        try_trs_desc = TRS_DESC in candidates
        try_desc_str = DESC_STR in candidates
        try_s_desc_tr = S_DESC_TR in candidates
        try_tr_desc_s = TR_DESC_S in candidates

        # Default to COPY_ALL if we can't affirmatively deduce a better
        # option.
        layout_guess = COPY_ALL

        # Strip out whitespace for this (mainly to avoid false misses in
        # S_DESC_TR).
        text = text.strip()

        # we use the `noNum` version of the sec_regex here
        sec_mo = noNum_sec_regex.search(text)
        tr_mo = twprge_broad_regex.search(text)

        if not sec_mo or not tr_mo:
            # Default to COPY_ALL, as having no identifiable section or
            # T&R is an insurmountable flaw.
            return layout_guess

        # If the first identified section comes before the first
        # identified T&R, then it's probably DESC_STR or S_DESC_TR:
        if sec_mo.start() < tr_mo.start():
            if try_s_desc_tr:
                # This is such an unlikely layout, that we give it very
                # limited room for error. If the section comes first
                # in the description, we should expect it VERY early
                # in the text:
                if sec_mo.start() <= 1:
                    layout_guess = S_DESC_TR
                else:
                    layout_guess = DESC_STR
            elif try_desc_str:
                layout_guess = DESC_STR
        elif try_trs_desc or try_tr_desc_s:
            # If T&R comes before Section, it's most likely TRS_DESC,
            # but could also be TR_DESC_S. Check how many characters
            # appear between T&R and Sec, and decide whether it's
            # TR_DESC_S or TRS_DESC, based on that.
            string_between = text[tr_mo.end():sec_mo.start()].strip()
            if len(string_between) >= 4 and try_tr_desc_s:
                layout_guess = TR_DESC_S
            elif try_trs_desc:
                layout_guess = TRS_DESC

        return layout_guess

    def _parse_segment(
            self,
            text_block, layout=None, clean_up=None, require_colon=None,
            handed_down_config=None, clean_qq=None,
            qq_depth_min=None, qq_depth_max=None, qq_depth=None,
            break_halves=None):
        """
        INTERNAL USE:

        Parse a segment of text into pytrs.Tract objects. Stores the
        results in the appropriate attribute.

        :param text_block: The text to be parsed.
        :param layout: The layout to be assumed. If not specified,
        will be deduced.
        :param clean_up: Whether to clean up common 'artefacts' from
        parsing. If not specified, defaults to False for parsing the
        'copy_all' layout, and `True` for all others.
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
        :param handed_down_config: A ``Config`` object to be passed to
        any ``Tract`` object that is created, so that they are
        configured identically to a parent ``PLSSDesc`` object. Defaults
        to None.
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
        :return: None (stores the results to the appropriate attributes)
        """

        ####################################################################
        # General explanation of how this function works:
        # 1) Lock down parameters for parse via kwargs, etc.
        # 2) If the layout was not appropriately specified, deduce it with
        #       `PLSSParser.deduce_layout()`
        # 3) Based on the layout, pull each of the T&R's that match our
        #       layout (for segmented parse, /should/ only be one), with
        #       `_findall_matching_tr()` function.
        # 4) Based on the layout, pull each of the Sections and
        #       Multi-Sections that match our layout with
        #       `_findall_matching_sec()` method.
        # 5) Combine all of the positions of starts/ends of T&R's, Sections,
        #       and Multisections into a single dict.
        # 6) Based on layout, apply the appropriate algorithm for breaking
        #       down the text. Each algorithm decides where to break the
        #       text apart based on section location, T&R location, etc.
        #       (e.g., by definition, TR_DESC_S and DESC_STR both pull
        #       the description block from BEFORE an identified section;
        #       whereas S_DESC_TR and TRS_DESC both pull description
        #       block AFTER the section).
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
            layout = self.safe_deduce_layout(text_block, override=True)

        if require_colon is None:
            require_colon = _DEFAULT_COLON

        if require_colon != _SECOND_PASS:
            self.reset_cache()

        # If `clean_qq` was specified, convert it to a string, and set
        # it to the `handed_down_config`. (We use the setter method to
        # prevent illegal values for a given attribute.)
        handed_down_config = Config(handed_down_config)
        if isinstance(clean_qq, bool):
            handed_down_config._set_str_to_values(f"clean_qq.{clean_qq}")
        if break_halves is not None:
            handed_down_config._set_str_to_values(f"break_halves.{break_halves}")
        if qq_depth_min is not None:
            handed_down_config._set_str_to_values(f"qq_depth_min.{qq_depth_min}")
        if qq_depth_max is not None:
            handed_down_config._set_str_to_values(f"qq_depth_max.{qq_depth_max}")
        if qq_depth is not None:
            handed_down_config._set_str_to_values(f"qq_depth.{qq_depth}")

        # We want to handle parse_qq all at once in this PLSSParser,
        # so mandate that it be False for now.
        handed_down_config.parse_qq = False

        if clean_up is None:
            # If clean_up has not been specified as a bool, then use
            # these defaults.
            clean_up = False
            if layout in [TRS_DESC, DESC_STR, S_DESC_TR, TR_DESC_S]:
                clean_up = True

        def clean_as_needed(candidate_text):
            """
            Will return either `candidate_text` (a string for the .desc
            attribute of a `Tract` object that is about to be created) or the
            cleaned-up version of it, depending on the bool `clean_up`.
            """
            if clean_up:
                candidate_text = PLSSParser._cleanup_desc(candidate_text)
            return candidate_text

        def new_tract(desc, sec, twprge) -> Tract:
            """Create and return a new Tract object"""
            desc = clean_as_needed(desc)
            return Tract(
                desc=desc, trs=f"{twprge}{sec}", config=handed_down_config)

        def flag_unused(unused_text, context):
            """
            Create a warning flag and flagLine for unused text.
            """
            flag = f"Unused_desc_<{unused_text}>"
            self.w_flags.append(flag)
            self.w_flag_lines.append((flag, context))

        # Find matching twprge's that are appropriate to our layout
        # (should only be one if segmented). Store the results to the
        # parse_cache, and add the w_flags and lines to the `.w_flags`
        # and `.w_flag_lines` attributes.
        self._findall_matching_tr(
            text_block,
            stage_flags_to=self.w_flags,
            stage_flag_lines_to=self.w_flag_lines)

        # Find matching Sections and MultiSections that are appropriate
        # to our layout (could be any number). Store the results to the
        # parse_cache.
        self._findall_matching_sec(text_block, require_colon=require_colon)

        # Pull the matched twprge's, sections, and multisections from
        # the parse_cache.

        all_twprge_matches = self.parse_cache["all_twprge_matches"]
        all_sec_matches = self.parse_cache["all_sec_matches"]
        all_multisec_matches = self.parse_cache["all_multisec_matches"]

        ####################################################################
        # Break down all_sec_matches, all_multisec_matches, and
        # all_twprge_matches into the index points
        ####################################################################

        # The Tract objects will be created from these component parts
        # (first-in-first-out).
        working_twprge_list = []
        working_sec_list = []
        working_multisec_list = []

        # A dict, keyed by index (i.e. start/end point of matched objects
        # within the text) and what was found at that index:
        markers_dict = {}
        # This key/val will be overwritten if we found a T&R or Section at
        # the first character
        markers_dict[0] = PLSSParser.TEXT_START
        # Add the end of the string to the markers_dict (may also get overwritten)
        markers_dict[len(text_block)] = PLSSParser.TEXT_END

        for tup in all_twprge_matches:
            working_twprge_list.append(tup[0])
            markers_dict[tup[1]] = PLSSParser.TR_START
            markers_dict[tup[2]] = PLSSParser.TR_END

        for tup in all_sec_matches:
            working_sec_list.append(tup[0])
            markers_dict[tup[1]] = PLSSParser.SEC_START
            markers_dict[tup[2]] = PLSSParser.SEC_END

        for tup in all_multisec_matches:
            working_multisec_list.append(tup[0])  # A list of lists
            markers_dict[tup[1]] = PLSSParser.MULTISEC_START
            markers_dict[tup[2]] = PLSSParser.MULTISEC_END

        # Get a list of all of the keys, then sort them, so that we're pulling
        # first-to-last (vis-a-vis the original text of this segment):
        markers_list = list(markers_dict.keys())
        markers_list.sort()

        # Cache these for access by the parser algorithm that is
        # appropriate for the layout.
        self.parse_cache["text_block"] = text_block
        self.parse_cache["markers_list"] = markers_list
        self.parse_cache["markers_dict"] = markers_dict
        self.parse_cache["twprge_list"] = working_twprge_list
        self.parse_cache["sec_list"] = working_sec_list
        self.parse_cache["multisec_list"] = working_multisec_list

        # Based on the layout, break apart the text into the relevant
        # components for each new tract. Store the results to the
        # parse_cache.
        if layout in [DESC_STR, TR_DESC_S]:
            self._descstr_trdescs(layout=layout)
        elif layout in [TRS_DESC, S_DESC_TR]:
            self._trsdesc_sdesctr(layout=layout)
        else:
            self._copyall()

        # Pull the new components from the parse_cache.
        new_tract_components = self.parse_cache["new_tract_components"]
        unused_text = self.parse_cache["unused_text"]
        uwc = self.parse_cache["unused_with_context"]

        # Generate Tract objects from the parsed components.
        new_tracts = []
        for tract_components in new_tract_components:
            tract = new_tract(**tract_components)
            new_tracts.append(tract)

        if not new_tracts:
            # If we identified no Tracts in this segment, re-parse using
            # COPY_ALL layout.
            self._parse_segment(
                text_block, layout=COPY_ALL, clean_up=False, require_colon=False,
                handed_down_config=handed_down_config, clean_qq=clean_qq)
            return None

        # Add the new Tract objects to our TractList.
        self.tracts.extend(new_tracts)

        # Generate a flag for each block of unused text longer than a
        # few characters.
        for ut in zip(unused_text, uwc):
            if len(ut[0]) > 3:
                flag_unused(*ut)

        return None

    def _descstr_trdescs(self, layout=None):
        """
        INTERNAL USE:

        Identify the Tract components assuming the syntax of
        ``desc_STR`` or ``TR_desc_S`` layout. Stores the appropriate
        data in the ``.parse_cache``.

        :param layout: Whether we are using ``'desc_STR'`` or
        ``'TR_desc_S'``.
        :return: None.
        """
        text_block = self.parse_cache["text_block"]
        working_twprge_list = self.parse_cache["twprge_list"]
        working_sec_list = self.parse_cache["sec_list"]
        working_multisec_list = self.parse_cache["multisec_list"]
        markers_list = self.parse_cache["markers_list"]
        markers_dict = self.parse_cache["markers_dict"]

        # These two layouts are handled nearly identically, except that
        # in DESC_STR the TR is popped before it's encountered, and in
        # TR_DESC_S it's popped only when encountered. So setting
        # initial TR is the only difference.

        # Defaults to a T&R error.
        working_twprge = TRS._ERR_TWPRGE
        # For TR_DESC_S, will pop the working_twprge when we encounter the
        # first TR. However, for DESC_STR, need to preset our working_twprge
        # (if one is available):
        if layout == DESC_STR and len(working_twprge_list) > 0:
            working_twprge = working_twprge_list.pop(0)

        # Description block comes before section in these layouts, so we
        # pre-set the working_sec and working_multisec (if any are available):
        working_sec = TRS._ERR_SEC
        if len(working_sec_list) > 0:
            working_sec = working_sec_list.pop(0)

        working_multisec = [TRS._ERR_SEC]
        if len(working_multisec_list) > 0:
            working_multisec = working_multisec_list.pop(0)

        new_tract_components = []
        unused_text = []
        unused_with_context = []

        final_run = False  # Will switch to True on the final loop

        # We'll check every marker to see what's at that point in the
        # text; depending on the type of marker, it will tell us how to
        # construct the next Tract object, or to pop the next section,
        # multi-Section, or T&R from the start of the respective working
        # list.

        # Track how far back we'll write to when we come across
        # secErrors in this layout:
        sec_err_write_back_to_pos = 0
        for i in range(len(markers_list)):

            if i == len(markers_list) - 1:
                final_run = True

            # Get this marker position and type
            marker_pos = markers_list[i]
            marker_type = markers_dict[marker_pos]

            # Unless this is the last marker, get the next marker
            # position and type
            if not final_run:
                next_marker_pos = markers_list[i + 1]
                next_marker_type = markers_dict[next_marker_pos]
            else:
                # For the final run, default to the current marker
                # position and type
                next_marker_pos = marker_pos
                next_marker_type = marker_type

            # Unless it's the first one, get the last marker position and type
            if i != 0:
                prev_marker_pos = markers_list[i - 1]
                prev_marker_type = markers_dict[prev_marker_pos]
            else:
                prev_marker_pos = marker_pos
                prev_marker_type = marker_type

            # We don't need to handle TEXT_START in this layout.

            if marker_type == PLSSParser.TR_END:
                # This is included for handling secErrors in this layout.
                # Note that it does not force a continue.
                sec_err_write_back_to_pos = marker_pos

            if marker_type == PLSSParser.TR_START:  # Pull the next T&R in our list
                if len(working_twprge_list) == 0:
                    # Will cause a TR error if another TRS+Desc is created:
                    working_twprge = TRS._ERR_TWPRGE
                else:
                    working_twprge = working_twprge_list.pop(0)
                continue

            if next_marker_type == PLSSParser.SEC_START:
                # NOTE that this algorithm is looking for the start of a
                # section at the NEXT marker!

                # New tract identified, with our current working_twprge
                # and working_sec, and with the desc being the text
                # between this marker and the next.
                tract_identified = {
                    "desc": text_block[markers_list[i]:markers_list[i + 1]].strip(),
                    "sec": working_sec,
                    "twprge": working_twprge
                }
                new_tract_components.append(tract_identified)
                if i + 2 <= len(markers_list):
                    sec_err_write_back_to_pos = markers_list[i + 2]
                else:
                    sec_err_write_back_to_pos = markers_list[i + 1]

            elif next_marker_type == PLSSParser.MULTISEC_START:
                # NOTE that this algorithm is looking for the start of a
                # multi-section at the NEXT marker!

                # Use our current working_twprge and EACH of the sections in
                # the working_multisec, with the desc being the text
                # between this marker and the next.
                for sec in working_multisec:
                    tract_identified = {
                        "desc": text_block[markers_list[i]:markers_list[i + 1]].strip(),
                        "sec": sec,
                        "twprge": working_twprge
                    }
                    new_tract_components.append(tract_identified)
                if i + 2 <= len(markers_list):
                    sec_err_write_back_to_pos = markers_list[i + 2]
                else:
                    sec_err_write_back_to_pos = markers_list[i + 1]

            elif (
                    next_marker_type == PLSSParser.TR_START
                    and marker_type not in [PLSSParser.SEC_END, PLSSParser.MULTISEC_END]
                    and next_marker_pos - sec_err_write_back_to_pos > 5
            ):
                # If (1) we found a T&R next, and (2) we aren't CURRENTLY
                # at a SEC_END or MULTISEC_END, and (3) it's been more than
                # a few characters since we last created a new Tract, then
                # we're apparently dealing with a secError, and we'll need
                # to make a flawed Tract object with that secError.
                tract_identified = {
                    "desc": text_block[sec_err_write_back_to_pos:markers_list[i + 1]].strip(),
                    "sec": TRS._ERR_SEC,
                    "twprge": working_twprge
                }
                new_tract_components.append(tract_identified)

            elif marker_type == PLSSParser.SEC_START:
                if len(working_sec_list) == 0:
                    # Will cause a section error if another TRS+Desc is created
                    working_sec = TRS._ERR_SEC
                else:
                    working_sec = working_sec_list.pop(0)

            elif marker_type == PLSSParser.MULTISEC_START:
                if len(working_multisec_list) == 0:
                    # Will cause a section error if another TRS+Desc is created
                    working_multisec = [TRS._ERR_SEC]
                else:
                    working_multisec = working_multisec_list.pop(0)

            elif marker_type == PLSSParser.SEC_END:
                if (next_marker_type not in [PLSSParser.SEC_START,
                                           PLSSParser.TR_START,
                                           PLSSParser.MULTISEC_START]
                    and marker_pos != len(text_block)
                ):
                    # Whenever we come across a Section end, the next thing must
                    # be either a SEC_START, MULTISEC_START, or TR_START.
                    # We'll create a warning flag if that's not true.
                    new_unused = text_block[markers_list[i]:markers_list[i + 1]].strip()
                    unused_text.append(new_unused)
                    unused_with_context.append(new_unused)

            elif marker_type == PLSSParser.TEXT_END:
                break

            # Capture unused text at the end of the string.
            if (
                    layout == TR_DESC_S
                    and marker_type in [PLSSParser.SEC_END, PLSSParser.MULTISEC_END]
                    and not final_run
                    and next_marker_type not in [PLSSParser.SEC_START,
                                               PLSSParser.TR_START,
                                               PLSSParser.MULTISEC_START]
            ):
                # For TR_DESC_S, whenever we come across the end of a Section or
                # multi-Section, the next thing must be either a SEC_START,
                # MULTISEC_START, or TR_START. Hence the warning flag, if that's
                # not true.
                new_unused = text_block[markers_list[i]:markers_list[i + 1]].strip()
                unused_text.append(new_unused)
                unused_with_context.append(new_unused)

            # Capture unused text at the end of a section/multiSec (if appropriate).
            if (layout == DESC_STR
                    and marker_type
                        in [PLSSParser.SEC_END, PLSSParser.MULTISEC_END]
                    and not final_run
                    and next_marker_type
                        not in [PLSSParser.SEC_START, PLSSParser.MULTISEC_START]):
                unused_text.append(text_block[marker_pos:next_marker_pos])
                unused_with_context.append(text_block[prev_marker_pos:next_marker_pos])

        self.parse_cache["new_tract_components"] = new_tract_components
        self.parse_cache["unused_text"] = unused_text
        self.parse_cache["unused_with_context"] = unused_with_context

        return None

    def _trsdesc_sdesctr(self, layout=None):
        """
        INTERNAL USE:

        Identify the Tract components assuming the syntax of
        ``TRS_desc`` or ``S_desc_TR`` layout. Stores the appropriate
        data in the ``.parse_cache``.

        :param layout: Whether we are using ``'TRS_desc'`` or
        ``'S_desc_TR'``.
        :return: None.
        """
        text_block = self.parse_cache["text_block"]
        working_twprge_list = self.parse_cache["twprge_list"]
        working_sec_list = self.parse_cache["sec_list"]
        working_multisec_list = self.parse_cache["multisec_list"]
        markers_list = self.parse_cache["markers_list"]
        markers_dict = self.parse_cache["markers_dict"]

        # Default to errors for T/R and Sec.
        working_twprge = TRS._ERR_TWPRGE
        working_sec = TRS._ERR_SEC
        working_multisec = [TRS._ERR_SEC]

        if len(working_twprge_list) > 0 and layout == S_DESC_TR:
            working_twprge = working_twprge_list.pop(0)

        new_tract_components = []
        unused_text = []
        unused_with_context = []

        final_run = False

        # We'll check every marker to see what's at that point in the
        # text; depending on the type of marker, it will tell us how to
        # construct the next Tract object, or to pop the next section,
        # multi-Section, or T&R from the respective working list.
        for i in range(len(markers_list)):

            if i == len(markers_list) - 1:
                # Just a shorthand to not show the logic every time:
                final_run = True

            # Get this marker position and type
            marker_pos = markers_list[i]
            marker_type = markers_dict[marker_pos]

            # Unless this is the last marker, get the next marker
            # position and type
            if not final_run:
                next_marker_pos = markers_list[i + 1]
                next_marker_type = markers_dict[next_marker_pos]
            else:
                # For the final run, default to the current marker
                # position and type
                next_marker_pos = marker_pos
                next_marker_type = marker_type

            # Unless it's the first one, get the last marker position and type
            if i != 0:
                prev_marker_pos = markers_list[i - 1]
                prev_marker_type = markers_dict[prev_marker_pos]
            else:
                prev_marker_pos = marker_pos
                prev_marker_type = markers_dict[marker_pos]

            # We don't need to handle TEXT_START in this layout.

            if marker_type == PLSSParser.SEC_START:
                if len(working_sec_list) == 0:
                    # Will cause a section error if another TRS+Desc is created
                    working_sec = TRS._ERR_SEC
                else:
                    working_sec = working_sec_list.pop(0)

            elif marker_type == PLSSParser.MULTISEC_START:
                if len(working_multisec_list) == 0:
                    # Will cause a section error if another TRS+Desc is created
                    working_multisec = [TRS._ERR_SEC]
                else:
                    working_multisec = working_multisec_list.pop(0)

            elif marker_type == PLSSParser.SEC_END:
                # We found the start of a new desc block (betw Section's end
                # and whatever's next).

                # New tract identified, with our current working_twprge
                # and working_sec, and with the desc being the text
                # between this marker and the next.
                tract_identified = {
                    "desc": text_block[markers_list[i]:markers_list[i + 1]].strip(),
                    "sec": working_sec,
                    "twprge": working_twprge
                }
                new_tract_components.append(tract_identified)

            elif marker_type == PLSSParser.MULTISEC_END:
                # We found start of a new desc block (betw multiSec end
                # and whatever's next).

                # Use our current working_twprge and EACH of the sections in
                # the working_multisec, with the desc being the text
                # between this marker and the next.
                for sec in working_multisec:
                    tract_identified = {
                        "desc": text_block[markers_list[i]:markers_list[i + 1]].strip(),
                        "sec": sec,
                        "twprge": working_twprge
                    }
                    new_tract_components.append(tract_identified)

            elif marker_type == PLSSParser.TR_START:  # Pull the next T&R in our list
                if len(working_twprge_list) == 0:
                    # Will cause a TR error if another TRS+Desc is created:
                    working_twprge = TRS._ERR_TWPRGE
                else:
                    working_twprge = working_twprge_list.pop(0)

            elif marker_type == PLSSParser.TR_END:
                # The only effect TR_END has on this layout is checking
                # for unused text.
                new_unused = text_block[marker_pos:next_marker_pos]
                unused_text.append(new_unused)
                unused_with_context.append(new_unused)

        self.parse_cache["new_tract_components"] = new_tract_components
        self.parse_cache["unused_text"] = unused_text
        self.parse_cache["unused_with_context"] = unused_with_context

        return None

    def _copyall(self):
        """
        INTERNAL USE:

        Generate the components for a Tract, assuming the syntax of
        ``copy_all``. Stores the appropriate data in the
        ``.parse_cache``.

        :return: None.
        """
        # A minimally-processed layout option. Basically just copies the
        # entire text as a `.desc` attribute. Can serve as a fallback if
        # deduce_layout() can't figure out what the real layout is (or
        # it's a flawed input).
        # TRS will be arbitrarily set to first T&R + Section (if either
        # is actually found).

        text_block = self.parse_cache["text_block"]
        working_twprge_list = self.parse_cache["twprge_list"]
        working_sec_list = self.parse_cache["sec_list"]
        working_multisec_list = self.parse_cache["multisec_list"]

        new_tract_components = []
        unused_text = []
        unused_with_context = []

        # Defaults to a T&R error if no T&R's were identified
        working_twprge = TRS._ERR_TWPRGE
        if len(working_twprge_list) > 0:
            working_twprge = working_twprge_list.pop(0)

        working_sec = TRS._ERR_SEC
        if len(working_sec_list) > 0:
            working_sec = working_sec_list.pop(0)

        # If no solo section was found, check for a multiSec we can pull from
        if working_sec == TRS._ERR_SEC and len(working_multisec_list) > 0:
            # Just pull the first section in the first multiSec.
            working_sec = working_multisec_list.pop(0)[0]

        # For generating a dummy Tract that contains the full text as
        # its `.desc` attribute. TRS is arbitrary, but will pull a
        # TR + sec, if found.
        tract_identified = {
            "desc": text_block,
            "sec": working_sec,
            "twprge": working_twprge
        }
        new_tract_components.append(tract_identified)

        self.parse_cache["new_tract_components"] = new_tract_components
        self.parse_cache["unused_text"] = unused_text
        self.parse_cache["unused_with_context"] = unused_with_context

        return None

    def _findall_matching_sec(
            self, text, layout=None, require_colon=_DEFAULT_COLON):
        """
        INTERNAL USE:

        Pull from the text all sections and 'multi-sections' that are
        appropriate to the description layout. Stores the results in the
        ``parse_cache``.
        :param require_colon: Same effect as in PLSSParser.parse()`
        """

        # require_colon=True will pass over sections that are NOT followed by
        # colons, in the TRS_DESC and S_DESC_TR layouts. For this version,
        # it is defaulted to True for those layouts. However, if no
        # satisfactory section or multiSec is found during the first pass,
        # it will rerun with `require_colon=_SECOND_PASS`.  Feeding
        # `require_colon=True` as a kwarg will override allowing the
        # second pass.

        # Note: the kwarg `require_colon=` accepts either a string (for
        # 'default_colon' and 'second_pass') or bool. If a bool is fed in
        # (i.e. require_colon=True), a 'second_pass' will NOT be allowed.
        # `require_colon_bool` is the actual variable that controls the
        # relevant logic throughout.
        # Note also: Future versions COULD conceivably compare the
        # first_pass and second_pass results to see which has more secErr's
        # or other types of errors, and use the less-flawed of the two.
        # But I'm not sure that would actually be better.

        # Note also that `require_colon_bool` has no effect on layouts
        # other than TRS_DESC and S_DESC_TR, even if set to `True`

        # Finally, note that because multiple passes may be done, we
        # initially stage our w_flags (and flag_lines) in the parse_cache.
        # After whichever pass is the final pass, the staged flags will
        # be added to `self.w_flags`.

        if isinstance(require_colon, bool):
            require_colon_bool = require_colon
        elif require_colon == _SECOND_PASS:
            require_colon_bool = False
            # Clear any staged flags from the first pass.
            self.parse_cache["w_flags_staging"] = []
            self.parse_cache["w_flag_line_staging"] = []
        else:
            require_colon_bool = True

        # Run through the description and find INDIVIDUAL sections or
        # LISTS of sections that match our layout.
        #   For INDIVIDUAL sections, we want "Section 5" in "T154N-R97W,
        #       Section 5: NE/4, Sections 4 and 6 - 10: ALL".
        #   For LISTS of sections (called "MultiSections" in this program),
        #       we want "Sections 4 and 6 - 10" in the above example.

        # For individual sections, save a list of tuples (all_sec_matches), each
        # containing the section number (as '00'), and its start and end
        # position in the text.
        all_sec_matches = []

        # For groups (lists) of sections, save a list of tuples
        # (all_multisec_matches), each containing a list of the section numbers
        # (as ['01', '03, '04', '05' ...]), and the group's start and end
        # position in the text.
        all_multisec_matches = []

        if layout not in _IMPLEMENTED_LAYOUTS:
            layout = PLSSParser.deduce_layout(text=text)

        def adj_secmo_end(sec_mo):
            """
            If a sec_mo or multisec_mo ends in whitespace, give the
            .end() minus 1; else return the .end()
            """
            # sec_regex and multiSec_regex can match unlimited whitespace at
            # the end, so if we don't back up 1 char, we can end up with a
            # situation where SEC_END is at the same position as TR_START,
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
            ruled_out = False

            # For TRS_DESC and S_DESC_TR layouts specifically, we do NOT want
            # to match sections following "of", "said", or "in" (e.g.
            # 'the NE/4 of Section 4'), because it very likely means its a
            # continuation of the same description.
            enders = (' of', ' said', ' in', ' within')
            if (
                    layout in [TRS_DESC, S_DESC_TR]
                    and text[:sec_mo.start()].rstrip().endswith(enders)
            ):
                ruled_out = True

            # Also for TRS_DESC and S_DESC_TR layouts, we ONLY want to match
            # sections and multi-Sections that are followed by a colon (if
            # requiredColonBool == True):
            if (
                    require_colon_bool
                    and layout in [TRS_DESC, S_DESC_TR]
                    and not (PLSSParser._sec_ends_with_colon(sec_mo))
            ):
                ruled_out = True

            if ruled_out:
                # Move our index to the end of this sec_mo and move to the next pass
                # through this loop, because we don't want to include this sec_mo.
                i = sec_mo.end()

                # Create a warning flag, that we did not pull this section or
                # multiSec and move on to the next loop.
                ignored_sec = PLSSParser._compile_sec_mo(sec_mo)
                if isinstance(ignored_sec, list):
                    flag = f"multiSec_not_pulled<{', '.join(ignored_sec)}>"
                else:
                    flag = f"sec_not_pulled<{ignored_sec}>"
                self.parse_cache["w_flags_staging"].append(flag)
                self.parse_cache["w_flag_lines_staging"].append((flag, sec_mo.group()))
                continue

            # Move the parsing index forward to the start of this next matched Sec
            i = sec_mo.start()

            # If we've gotten to here, then we've found a section or multiSec
            # that we want. Determine which it is, and append it to the respective
            # list:
            if PLSSParser._is_multisec(sec_mo):
                # If it's a multiSec, unpack it, and append it to
                # all_multisec_matches.  (We stage flags to temp list so that
                # we maintain the intended order of flags: i.e. so that
                # 'multisec_found' comes before any specific issues with
                # that multisec.)
                multisec_flags_temp = []
                multisec_flag_lines_temp = []
                unpackedMultiSec = self._unpack_sections(
                    sec_mo.group(), stage_flags_to=multisec_flags_temp,
                    stage_flag_lines_to=multisec_flag_lines_temp)

                # First create an overall multisec flag.
                flag = f"multiSec_found<{', '.join(unpackedMultiSec)}>"
                self.parse_cache["w_flags_staging"].append(flag)
                self.parse_cache["w_flag_lines_staging"].append((flag, sec_mo.group()))

                # Then extend with any flags generated by _unpack_sections()
                self.parse_cache["w_flags_staging"].extend(multisec_flags_temp)
                self.parse_cache["w_flag_lines_staging"].extend(multisec_flag_lines_temp)

                # And finally append the tuple for this multiSec
                all_multisec_matches.append((unpackedMultiSec, i, adj_secmo_end(sec_mo)))
            else:
                # Append the tuple for this individual section
                all_sec_matches.append(
                    (self._compile_sec_mo(sec_mo), i, adj_secmo_end(sec_mo)))

            # And move the parser index to the end of our current sec_mo
            i = sec_mo.end()

        # If we're in either TRS_DESC or S_DESC_TR layouts and discovered
        # neither a standalone section nor a multiSec, then rerun
        # _findall_matching_sec() under the same kwargs, except with
        # require_colon=_SECOND_PASS (which sets
        # require_colon_bool=False), to see if we can capture a section after
        # all.  Will return those results instead.
        do_second_pass = True
        if layout not in [TRS_DESC, S_DESC_TR]:
            do_second_pass = False
        if all_sec_matches or all_multisec_matches:
            # If we've found at lease one sec or multisec
            do_second_pass = False
            if require_colon == _SECOND_PASS:
                all_sections = [sec_tuple[0] for sec_tuple in all_sec_matches]
                for sections in [tup[0] for tup in all_multisec_matches]:
                    all_sections.extend(sections)
                flag = f"pulled_sec_without_colon<{','.join(all_sections)}>"
                self.parse_cache["w_flags_staging"].append(flag)
                self.parse_cache["w_flag_lines_staging"].append((flag, text))
        if require_colon != _DEFAULT_COLON:
            do_second_pass = False
        if do_second_pass:
            self._findall_matching_sec(
                text, layout=layout, require_colon=_SECOND_PASS)
            return None

        # Add `sec_list` and `multiSecList` to parse_cache, and cement
        # our staged w_flags.
        self.parse_cache["all_sec_matches"] = all_sec_matches
        self.parse_cache["all_multisec_matches"] = all_multisec_matches
        self.w_flags.extend(self.parse_cache["w_flags_staging"])
        self.w_flag_lines.extend(self.parse_cache["w_flag_lines_staging"])
        return None

    @staticmethod
    def _unpack_sections(
            sec_text_block, stage_flags_to: list = None,
            stage_flag_lines_to: list = None):
        """
        INTERNAL USE:
        Feed in a string of a multiSec_regex match object, and return a
        list of all of the sections (i.e. ``Sections 2, 3, 9 - 11`` will
        return as ``['02', '03', '09', '10', 11']``).

        :param sec_text_block: A string being the entire match of the
        multiSec_regex pattern.
        :param stage_flags_to: An optional list in which to add warning
        flags (in-situ). If not specified, they will be discarded.
        :param stage_flag_lines_to: An optional list in which to add
        warning flags and flag-lines (in-situ). If not specified, they
        will be discarded.
        :return: A list of 2-digit strings, being the section numbers.
        """

        # TODO: Maybe just put together a simpler algorithm. Since there's
        #   so much less possible text in a list of Sections, can probably
        #   just add from left-to-right, unlike _unpack_lots.

        text = sec_text_block

        if stage_flags_to is None:
            stage_flags_to = []
        if stage_flag_lines_to is None:
            stage_flag_lines_to = []

        # A working list of the sections. Note that this gets filled from
        # last-to-first on this working text block, but gets reversed at the end.
        sec_list = []

        def flag_duplicates(sec_num):
            """Check for and flag duplicate sections."""
            if sec_num in sec_list:
                stage_flags_to.append(f'dup_sec<{sec_num}>')
                stage_flag_lines_to.append(
                    (f'dup_sec<{sec_num}>', f'Section {sec_num}'))

        found_through = False
        endpos = len(text)
        while True:
            secs_mo = multiSec_regex.search(text, endpos=endpos)

            if not secs_mo:
                # We're out of section numbers.
                break

            # Pull the right-most section number (still as a string):
            sec_num = PLSSParser._get_last_sec(secs_mo)

            # Assume we've found the last section and can therefore skip
            # the next loop after we've found the last section.
            endpos = 0
            if PLSSParser._is_multisec(secs_mo):
                # If multiple sections remain, we will continue our
                # search next loop.
                endpos = secs_mo.start(12)

            # Clean up any leading '0's in sec_num.
            sec_num = str(int(sec_num))

            # Format section number as 2 digits.
            new_sec = sec_num.rjust(2, '0')

            if found_through:
                # If we've identified a elided list (e.g., 'Sections 3 - 9')...
                prev_sec = sec_list[-1]
                # Take the sec_num identified earlier this loop:
                start_of_list = int(sec_num)
                # The the previously last-identified section:
                end_of_list = int(prev_sec)
                correct_order = True
                if start_of_list >= end_of_list:
                    correct_order = False
                    stage_flags_to.append('nonSequen_sec')
                    stage_flag_lines_to.append(
                        ('nonSequen_sec',
                         f'Sections {start_of_list} - {end_of_list}')
                    )

                ########################################################
                # `start_of_list` and `end_of_list` variable names are
                # unintuitive. Here's an explanation:
                # The 'sections' list is being filled in reverse by this
                # algorithm, starting at the end of the search string
                # and running backwards. Thus, this particular loop,
                # which is attempting to unpack "Sections 3 - 9", will
                # be fed into the sections list as [08, 07, 06, 05, 04,
                # 03]. (09 should already be in the list from the
                # previous loop.)  'start_of_list' refers to the
                # original text (i.e. in 'Sections 3 - 9', start_of_list
                # will be 3; end_of_list will be 9).
                ########################################################

                # vars a, b & c are the bounds (a & b) and incrementation (c)
                # of the range() for the secs in the elided list:
                # If the string is correctly 'Sections 3 - 9' (for example),
                # we use the default:
                a, b, c = end_of_list - 1, start_of_list - 1, -1
                # ... but if the string is 'sections 9 - 3' (i.e. wrong),
                # we use:
                if not correct_order:
                    a, b, c = end_of_list + 1, start_of_list + 1, 1

                for i in range(a, b, c):
                    add_sec = str(i).rjust(2, '0')
                    flag_duplicates(add_sec)
                    sec_list.append(add_sec)
                found_through = False  # reset.

            else:
                # Otherwise, if it's a standalone section (not the start
                #   of an elided list), we add it.
                # First check if this new section is in sec_list:
                flag_duplicates(new_sec)
                sec_list.append(new_sec)

            # If we identified at least two sections, we need to check
            # if the last one is the end of an elided list:
            if PLSSParser._is_multisec(secs_mo):
                thru_mo = through_regex.search(secs_mo.group(6))
                # Check if we find 'through' (or equivalent symbol or
                # abbreviation) before this final section:
                if thru_mo is None:
                    found_through = False
                else:
                    found_through = True
        sec_list.reverse()

        return sec_list

    def _findall_matching_tr(
            self, text, layout=None, cache=True, stage_flags_to: list = None,
            stage_flag_lines_to: list = None) -> list:
        """
        INTERNAL USE:

        Find T&R's that appropriately match the layout. Returns a list
        of tuples, each containing a T&R (as '000n000w' or fewer digits)
        and its start and end position in the text.
        :param text: The text in which to find matching Twp/Rge's.
        :param layout: The pyTRS layout of the text. (Will be deduced if
        not specified.)
        :param cache: Whether to store the results to ``.parse_cache``.
        (Defaults to True)
        :param stage_flags_to: An optional list in which to stage
        w_flags. If not specified, they will be discarded.
        :param stage_flag_lines_to: An optional list in which to stage
        w_flag_lines. If not specified, they will be discarded.
        """

        if stage_flags_to is None:
            stage_flags_to = []
        if stage_flag_lines_to is None:
            stage_flag_lines_to = []

        if layout is None:
            layout = self.safe_deduce_layout(text=text)

        all_twprge_matches = []
        # A parsing index for text (marks where we're currently searching from):
        i = 0
        while True:
            tr_mo = twprge_regex.search(text, pos=i)

            # If there are no more T&R's in the text, end this loop.
            if tr_mo is None:
                break

            # Move the parsing index forward to the start of this next
            # matched T&R.
            i = tr_mo.start()

            # For most layouts we want to know what comes before this matched
            # T&R to see if it is relevant for a NEW Tract, or if it's simply
            # part of the description of another Tract (i.e., we probably
            # don't want to pull the T&R or Section in "...less and except
            # the wellbore of the Johnston #1 located in the NE/4NW/4 of
            # Section 14, T154N-R97W" -- so we have to rule that out).

            # We do that by looking behind our current match for context:

            # We'll look up to this many characters behind i:
            length_to_search_behind = 25
            # ...but we only want to search back to the start of the text string:
            if length_to_search_behind > i:
                length_to_search_behind = i

            # j is the search-behind pos (indexed against the original text str):
            j = i - length_to_search_behind

            # We also need to make sure there's only one section in the string,
            # so loop until it's down to one section:
            sec_found = False
            while True:
                sec_mo = sec_regex.search(text, pos=j, endpos=i)
                if not sec_mo:
                    # If no more sections were found, move on to the next step.
                    break
                else:
                    # Otherwise, if we've found another sec, move the j-index
                    # to the end of it
                    j = sec_mo.end()
                    sec_found = True

            # If we've found a section before our current T&R, then we need
            # to check what's in between. For TRS_DESC and S_DESC_TR layouts,
            # we want to rule out misc. interveners:
            #       ','  'in'  'of'  'all of'  'all in'  (etc.).
            # If we have such an intervening string, then this appears to be
            # desc_STR layout -- ex. 'Section 1 of T154N-R97W'

            if (
                    sec_found
                    and text[j:i].strip().lower() in PLSSParser.SEC_TWP_INTERVENERS
                    and layout in [TRS_DESC, S_DESC_TR]
            ):
                # In TRS_Desc and S_DESC_TR layouts specifically, this is
                # NOT a T&R match for a new Tract.

                # Move our parsing index to the end of the currently identified T&R.
                # NOTE: the length of this tr_mo match is indexed against the text
                # slice, so need to add it to i (which is indexed against the full
                # text) to get the 'real' index
                i = i + len(tr_mo.group())

                # and append a warning flag that we've ignored this T&R:
                ignored_twprge = PLSSParser._compile_twprge_mo(tr_mo)
                flag = f'TR_not_pulled<{ignored_twprge}>'
                line = tr_mo.group()
                stage_flags_to.append(flag)
                stage_flag_lines_to.append((flag, line))
                continue

            # Otherwise, if there is NO intervener, or the layout is something
            # other than TRS_DESC or S_DESC_TR, then this IS a match and we
            # want to store it.
            else:
                twprge = PLSSParser._compile_twprge_mo(tr_mo)
                match = tr_mo.group()
                all_twprge_matches.append((twprge, i, i + len(match)))
                # Move the parsing index to the end of the T&R that we
                # just matched.
                i = i + len(tr_mo.group())
                continue

        # Store to our parse_cache.
        if cache:
            self.parse_cache["all_twprge_matches"] = all_twprge_matches

        return all_twprge_matches

    def _segment_by_tr(self, text, layout=None, twprge_first=None):
        """
        INTERNAL USE:

        Break the description into segments, based on previously
        identified T&R's that match our description layout via the
        _findall_matching_tr() function. Returns 2 lists: a list of text
        blocks AND a list of discarded text blocks.

        :param layout: Which layout to use. If not specified, will
        deduce.
        :param twprge_first: Whether it's a layout where Twp/Rge comes
        first (i.e. 'TRS_desc' or 'TR_desc_S'). If not specified, will
        deduce.
        """

        if layout not in _IMPLEMENTED_LAYOUTS:
            layout = PLSSParser.deduce_layout(text=text)

        if not isinstance(twprge_first, bool):
            if layout in [TRS_DESC, TR_DESC_S]:
                twprge_first = True
            else:
                twprge_first = False

        # Search for all T&R's that match the layout requirements. (We
        # do not store the flags, nor cache the results.)
        twprge_matches = self._findall_matching_tr(text=text, layout=layout, cache=False)

        if not twprge_matches:
            # If no T&R's had been matched, return the text block as single
            # element in a list (what would have been `twprge_text_blocks`), and
            # another empty list (what would have been `discard_text_blocks`)
            return [text], []

        start_points = []
        end_points = []
        twprge_list = []
        twprge_text_blocks = []
        discard_text_blocks = []
        for twprge_tuple in twprge_matches:
            twprge_list.append(twprge_tuple[0])
            start_points.append(twprge_tuple[1])
            end_points.append(twprge_tuple[2])

        if twprge_first:
            for i in range(len(start_points)):
                if i == 0 and start_points[i] != 0:
                    # If the first element is not 0 (i.e. T&R right at the
                    # start), this is discard text.
                    discard_text_blocks.append(text[:start_points[i]])
                # Append each text_block
                new_desc = text[start_points[i]:]
                if i + 1 != len(start_points):
                    new_desc = text[start_points[i]:start_points[i + 1]]
                twprge_text_blocks.append(
                    (twprge_list.pop(0), PLSSParser._cleanup_desc(new_desc)))

        else:
            for i in range(len(end_points)):
                if i + 1 == len(end_points) and end_points[i] != len(text):
                    # If the last element is not the final character in the
                    # string (i.e. T&R ends at text end), discard text
                    discard_text_blocks.append(text[end_points[i]:])
                # Append each text_block
                new_desc = text[:end_points[i]]
                if i != 0:
                    new_desc = text[end_points[i - 1]:end_points[i]]
                twprge_text_blocks.append(
                    (twprge_list.pop(0), PLSSParser._cleanup_desc(new_desc)))

        return twprge_text_blocks, discard_text_blocks

    @staticmethod
    def _compile_twprge_mo(mo, default_ns=None, default_ew=None, ocr_scrub=False):
        """
        INTERNAL USE:
        Take a match object (`mo`) of an identified T&R, and return a string
        in the format of '000n000w' (i.e. between 1 and 3 digits for
        township and for range numbers).
        """

        if not default_ns:
            default_ns = PLSSDesc.MASTER_DEFAULT_NS

        if not default_ew:
            default_ew = PLSSDesc.MASTER_DEFAULT_EW

        twp_num = mo[2]
        if ocr_scrub:
            twp_num = _ocr_scrub_alpha_to_num(twp_num)
        # Clean up any leading '0's in twp_num.
        # (Try/except is used to handle twprge_ocr_scrub_regex mo's, which
        # can contain alpha characters in `twp_num`.)
        try:
            twp_num = str(int(twp_num))
        except ValueError:
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
                rge_num = mo[6]
            else:
                rge_num = mo[12]
        else:
            rge_num = mo[6]

        # --------------------------------------
        # Clean up any leading '0's in rge_num.
        # (Try/except is used to handle twprge_ocr_scrub_regex mo's, which
        # can contain alpha characters in `rge_num`.)
        if ocr_scrub:
            rge_num = _ocr_scrub_alpha_to_num(rge_num)
        try:
            rge_num = str(int(rge_num))
        except ValueError:
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

        return f"{twp_num}{ns}{rge_num}{ew}"

    @staticmethod
    def _compile_sec_mo(sec_mo):
        """
        INTERNAL USE
        Takes a match object (mo) of an identified multiSection, and
        returns a string in the format of '00' for individual sections and a
        list ['01', '02', ...] for multiSections
        """
        if PLSSParser._is_multisec(sec_mo):
            return PLSSParser._unpack_sections(sec_mo.group())
        elif PLSSParser._is_singlesec(sec_mo):
            return PLSSParser._get_last_sec(sec_mo).rjust(2, '0')
        return None

    @staticmethod
    def _cleanup_desc(text):
        """
        INTERNAL USE:
        Clean up common 'artifacts' from parsing--especially layouts other
        than TRS_DESC. (Intended to be run only on post-parsing .desc
        attributes of Tract objects.)
        """
        cull_list = [' the', ' all in', ' all of', ' of', ' in', ' and']
        # Run this loop until the input str matches the output str.
        while True:
            text1 = text
            text1 = text1.lstrip('.')
            text1 = text1.strip(',;:-–—\t\n ')
            # Check to see if text1 ends with each of the strings in the
            # cull_list, and if so, slice text1 down accordingly.
            for cull_str in cull_list:
                cull_length = len(cull_str)
                if text1.lower().endswith(cull_str):
                    text1 = text1[:-cull_length]
            if text1 == text:
                break
            text = text1
        return text

    @staticmethod
    def _is_multisec(multisec_mo) -> bool:
        """
        INTERNAL USE:
        Determine whether a multiSec_regex match object is a multiSec.
        """
        return multisec_mo.group(12) is not None

    @staticmethod
    def _is_singlesec(multisec_mo) -> bool:
        """
        INTERNAL USE:
        Determine whether a multiSec_regex match object is a single section.
        """
        return multisec_mo.group(12) is None and multisec_mo.group(5) is not None

    @staticmethod
    def _get_last_sec(multisec_mo) -> (str, None):
        """
        INTERNAL USE:
        Extract the right-most section in a multiSec_regex match object.
        Returns None if no match.
        """
        if PLSSParser._is_multisec(multisec_mo):
            return multisec_mo.group(12)
        elif PLSSParser._is_singlesec(multisec_mo):
            return multisec_mo.group(5)
        return None

    @staticmethod
    def _is_plural_singlesec(multisec_mo) -> bool:
        """
        INTERNAL USE:
        Determine if a multiSec_regex match object is a single section
        but pluralized (ex. 'Sections 14: ...').
        """
        # Only a single section in this match...
        # But there's a plural "Sections" anyway!
        if (PLSSParser._is_singlesec(multisec_mo)
                and multisec_mo.group(4) is not None):
            return multisec_mo.group(4).lower() == 's'
        return False

    @staticmethod
    def _sec_ends_with_colon(multisec_mo) -> bool:
        """
        INTERNAL USE:
        Determine whether a multiSec_regex match object ends with a colon.
        """
        return multisec_mo.group(13) == ':'

    def gen_flags(self):
        """
        Generate w_flags, w_flag_lines, e_flags, and e_flag_lines. Each
        element in w_flag_lines or e_flag_lines is a tuple, the first
        element being the warning or error flag, and the second element
        being the line that raised the flag.
        """
        text = self.orig_desc
        preprocessed = self.text

        lines = text.split('\n')

        ################################################################
        # Error flags
        ################################################################

        # We use the preprocessed text only to make sure at least one
        # T&R exists
        if not find_twprge(preprocessed):
            self.e_flags.append('noTR')
            self.e_flag_lines.append(
                ('noTR', 'No T&R\'s identified!'))

        # For everything else, we check against the orig_desc
        if len(find_sec(text)) == 0 and len(find_multisec(text)) == 0:
            self.e_flags.append('noSection')
            self.e_flag_lines.append(
                ('noSection', 'No Sections identified!'))

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
            if not rgx.findall(line):
                return
            if flag not in self.w_flags:
                self.w_flags.append(flag)
            self.w_flag_lines.append((flag, line))

        for line in lines:
            for rgx, flag in wflag_regexes:
                check_for_wflag(line, rgx, flag)

        return None


class PLSSPreprocessor:
    """
    INTERNAL USE:

    A class for preprocessing text for the PLSSParser. Get the
    preprocessed text from the ``.text`` attribute, or the original text
    from the ``.orig_text`` attribute.  Get a list of Twp/Rge's that
    were fixed in the ``.fixed_twprges`` attribute.
    """

    SCRUBBER_REGEXES = (
        twprge_regex,
        preproTR_noNSWE_regex,
        preproTR_noR_noNS_regex,
        preproTR_noT_noWE_regex,
        twprge_pm_regex
    )

    # Turn this one on with `ocr_scrub=True`
    OCR_SCRUBBER = twprge_ocr_scrub_regex

    def __init__(self, text, default_ns=None, default_ew=None, ocr_scrub=False):
        """

        :param text: The text to be preprocessed.
        :param default_ns: How to interpret townships for which direction
        was not specified -- i.e. either 'n' or 's'. (Defaults to
        ``PLSSDesc.MASTER_DEFAULT_NS``, which is 'n' unless otherwise
        specified.)
        :param default_ew: How to interpret ranges for which direction
        was not specified -- i.e. either 'e' or 'w'. (Defaults to
        ``PLSSDesc.MASTER_DEFAULT_EW``, which is 'w' unless otherwise
        specified.)
        :param ocr_scrub: Whether to try to iron out common OCR
        'artifacts'. May cause unintended changes. (Defaults to `False`)
        """

        self.orig_text = text
        self.ocr_scrub = ocr_scrub

        if not default_ns:
            default_ns = PLSSDesc.MASTER_DEFAULT_NS

        if not default_ew:
            default_ew = PLSSDesc.MASTER_DEFAULT_EW

        self.default_ns = default_ns
        self.default_ew = default_ew

        # These attributes are populated by `.preprocess()`:
        self.fixed_twprges = []
        self.text = text

        self.preprocess()

    def preprocess(
            self, text=None, default_ns=None, default_ew=None,
            ocr_scrub=None) -> str:
        """
        Preprocess the PLSS description to iron out common kinks in
        the input data. Stores the results to ``.text`` attribute and
        a list of fixed Twp/Rges to ``.fixed_twprges``.

        :return: The preprocessed string.
        """

        if not text:
            text = self.text

        if not default_ns:
            default_ns = self.default_ns

        if not default_ew:
            default_ew = self.default_ew

        if ocr_scrub is None:
            ocr_scrub = self.ocr_scrub

        # Look for T&R's in original text (for checking if we fix any
        # during preprocess, to raise a wFlag)
        orig_twprge_list = find_twprge(text)

        # Run each of the prepro regexes over the text, each working on
        # the last-prepro'd version of the text. Swaps in the cleaned up
        # TR (format 'T000N-R000W') for each T&R, every time.
        pp_regexes = list(PLSSPreprocessor.SCRUBBER_REGEXES)
        if ocr_scrub:
            # This invites potential mis-matches, so it is not included
            # by default. Turn on with `ocr_scrub=True` kwarg.
            pp_regexes.insert(0, PLSSPreprocessor.OCR_SCRUBBER)

        for pp_rgx in pp_regexes:
            i = 0
            # working preprocessed description (reconstructed every loop):
            w_pp_desc = ''
            while True:
                # Note: We do this as a loop, rather than using re.sub(),
                # due to an erroneous over-matching of "Lots 6, 7, East"
                # as "T6S-R7E" in the `preproTR_noR_noNS_regex` pattern.

                tr_mo = pp_rgx.search(text, pos=i)

                if tr_mo is None:
                    # If we've found no more T&R's, append the remaining
                    # text_block and end the loop
                    w_pp_desc = f"{w_pp_desc}{text[i:]}"
                    break

                mo_start = tr_mo.start()

                # Need some additional context to rule out 'Lots 6, 7, East'
                # as matching as "T6S-R7E" (i.e. the 'ts' in 'Lots' as being
                # picked up as 'Township'):
                if pp_rgx == preproTR_noR_noNS_regex:
                    # We'll look behind this many characters:
                    lk_back = 3
                    if lk_back > tr_mo.start():
                        lk_back = tr_mo.start()

                    # Get a context string containing that many characters
                    # behind, plus a couple ahead. Will look for "Lot" or "Lots"
                    # (allowing for slight typo) in that string:
                    cntxt_str = text[mo_start - lk_back: mo_start + 2]
                    lot_check_mo = lots_context_regex.search(cntxt_str)
                    if lot_check_mo is not None:
                        # If we matched, then we're dealing with a false
                        # T&R match, and we need to move on.
                        w_pp_desc = f"{w_pp_desc}{text[i:tr_mo.end()]}"
                        i = tr_mo.end()
                        continue

                clean_twprge = PLSSPreprocessor._preprocess_twprge_mo(
                    tr_mo, default_ns=default_ns, default_ew=default_ew,
                    ocr_scrub=ocr_scrub)

                # Add to the w_pp_desc all of the text since the last
                # `i`, up to the identified tr_mo, and add the
                # clean_twprge, with some spaces around it, just to keep
                # it cleanly delineated from surrounding text.
                w_pp_desc = f"{w_pp_desc}{text[i:mo_start]} {clean_twprge} "

                # Move the search index to the end of the tr_mo.
                i = tr_mo.end()

            text = w_pp_desc

        # Clean up white space:
        text = text.strip()
        while True:
            # Scrub until text at start of loop == text at end of loop.
            text1 = text

            # Forbid consecutive spaces
            text1 = re.sub(r" +", " ", text1)
            # Convert carriage returns to linebreaks
            text1 = re.sub(r"\r", "\n", text1)
            # Maximum of two linebreaks in a row
            text1 = re.sub(r"\n{2,}", "\n\n", text1)
            # Remove spaces at the start of a new line
            text1 = re.sub(r"\n ", "\n", text1)
            # Remove tabs at the start of a new line
            text1 = re.sub(r"\n\t", "\n", text1)
            if text1 == text:
                break
            text = text1

        # Look for T&R's in the preprocessed text
        prepro_twprge_list = find_twprge(text)

        # Remove from the post-preprocess TR list each of the elements
        # in the list generated from the original text.
        for tr in orig_twprge_list:
            if tr in prepro_twprge_list:
                prepro_twprge_list.remove(tr)

        self.fixed_twprges = prepro_twprge_list
        self.text = text

        return text

    @staticmethod
    def _preprocess_twprge_mo(
            tr_mo, default_ns=None, default_ew=None, ocr_scrub=False) -> str:
        """
        INTERNAL USE:
        Take a T&R match object (tr_mo) and check for missing 'T', 'R',
        and and if N/S and E/W are filled in. Will fill in any missing
        elements (using default_ns and default_ew as necessary) and
        outputs a string in the format T000N-R000W (or fewer digits for
        twp & rge), which is to be swapped into the source text where
        the tr_mo was originally matched, in order to clean up the
        preprocessed description.
        """

        if not default_ns:
            default_ns = PLSSDesc.MASTER_DEFAULT_NS

        if not default_ew:
            default_ew = PLSSDesc.MASTER_DEFAULT_EW

        clean_tr = PLSSParser._compile_twprge_mo(
            tr_mo, default_ns=default_ns, default_ew=default_ew,
            ocr_scrub=ocr_scrub)
        twprge = TRS(clean_tr)

        # Maintain the first character, if it's a whitespace.
        first = ''
        if tr_mo.group().startswith(('\n', '\t', ' ')):
            first = tr_mo.group()[0]

        # Maintain the last character, if it's a whitespace.
        last = ''
        if tr_mo.group().endswith(('\n', '\t', ' ')):
            last = tr_mo.group()[-1]

        return f"{first}{twprge.pretty_twprge()}{last}"

    @staticmethod
    def static_preprocess(
            text, default_ns=None, default_ew=None, ocr_scrub=False):
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
        processor = PLSSPreprocessor(
            text, default_ns, default_ew, ocr_scrub=ocr_scrub)
        return processor.text


class TractPreprocessor:
    """
    INTERNAL USE:

    A class for preprocessing text for the TractParser. Get the
    preprocessed text from the ``.text`` attribute, or the original text
    from the ``.orig_text`` attribute.
    """

    # Clean aliquot abbreviations with fraction, for aliquot preprocessing.
    NE_FRAC = 'NE¼'
    NW_FRAC = 'NW¼'
    SE_FRAC = 'SE¼'
    SW_FRAC = 'SW¼'
    N2_FRAC = 'N½'
    S2_FRAC = 'S½'
    E2_FRAC = 'E½'
    W2_FRAC = 'W½'

    # Define what should replace matches of each regex that is used in the
    # TractPreprocessor._scrub_aliquots() method.
    QQ_SCRUBBER_DEFINITIONS = {
        NE_regex: NE_FRAC,
        NW_regex: NW_FRAC,
        SE_regex: SE_FRAC,
        SW_regex: SW_FRAC,
        N2_regex: N2_FRAC,
        S2_regex: S2_FRAC,
        E2_regex: E2_FRAC,
        W2_regex: W2_FRAC,
        cleanNE_regex: NE_FRAC,
        cleanNW_regex: NW_FRAC,
        cleanSE_regex: SE_FRAC,
        cleanSW_regex: SW_FRAC
    }

    SCRUBBER_REGEXES = (
        NE_regex,
        NW_regex,
        SE_regex,
        SW_regex,
        N2_regex,
        S2_regex,
        E2_regex,
        W2_regex
    )

    CLEAN_QQ_REGEXES = (
        cleanNE_regex,
        cleanNW_regex,
        cleanSE_regex,
        cleanSW_regex
    )

    def __init__(self, text, clean_qq=False):
        self.orig_text = text
        self.text = text
        self.clean_qq = clean_qq
        self.preprocess()

    def preprocess(self, text=None, clean_qq=None):
        """
        Preprocess the text, store the results to ``.text`` attribute,
        and return the results.
        :param text: The text to be preprocessed.
        :return: The preprocessed text.
        """
        if not text:
            text = self.text
        if clean_qq is None:
            clean_qq = self.clean_qq
        text = TractPreprocessor._scrub_aliquots(text, clean_qq)
        self.text = text
        return text

    @staticmethod
    def _scrub_aliquots(text, clean_qq=False) -> str:
        """
        INTERNAL USE:
        Scrub the raw text of a Tract's description, to convert aliquot
        components into standard abbreviations with fraction symbols.
        """

        def scrubber(txt, regex_run):
            """
            Convert the raw aliquots to cleaner components, using the
            regex fed as the second arg, and returns the scrubbed text.
            (Will only function properly with specific aliquots regexes.)
            """

            # The str we'll use to replace matches of this regex pattern.
            replace_with = TractPreprocessor.QQ_SCRUBBER_DEFINITIONS[regex_run]

            # NOTE: we do not use the `re.sub()` function because we need to
            # maintain the first character in the regex match, which provides
            # necessary context to prevent over-matching. For example, the
            # `NE_regex` must match '(\b|¼|4|½|2)' at the beginning, so that
            # we don't capture "one hundred" as "oNE¼ hundred".
            # (The clean_qq regexes do not have this requirement.)
            remaining_text = txt
            rebuilt_text = ''
            while True:
                rgx_mo = regex_run.search(remaining_text)
                if rgx_mo is None:  # If we found no more matches like this.
                    rebuilt_text = rebuilt_text + remaining_text
                    break
                rebuilt_text = (
                    f"{rebuilt_text}"
                    f"{remaining_text[:rgx_mo.start(2)]}"
                    f"{replace_with}"
                )
                remaining_text = remaining_text[rgx_mo.end():]
            return rebuilt_text

        # We'll run these scrubber regexes on the text:
        scrubber_rgxs = list(TractPreprocessor.SCRUBBER_REGEXES)

        # If the user has specified that the input data is clean (i.e.
        # no metes-and-bounds tracts, etc.), then broader regexes can
        # also be applied.
        if clean_qq:
            scrubber_rgxs.extend(TractPreprocessor.CLEAN_QQ_REGEXES)
        # Now run each of the regexes over the text:
        for reg_to_run in scrubber_rgxs:
            text = scrubber(text, reg_to_run)

        # And now that 'halves' have been cleaned up, we can also
        # convert matches like 'E½NE' into 'E½NE¼'. Group 3 of the
        # halfPlusQ_regex is the half (without its fraction) and Group 5
        # is the quarter (without its fraction). However, we may need to
        # do some additional scrubbing on the quarter, if it did not
        # have a fraction or the word "quarter" in the original text.
        # So we break it apart and run the clean_qq regexes on that part
        # only.
        i = 0
        while True:
            mo = halfPlusQ_regex.search(text, pos=i)
            if not mo:
                break

            # Run the clean_qq scrubber on this match, and see if
            # anything changes.
            replacement = mo.group()
            check_for_changes = replacement
            for rgx in TractPreprocessor.CLEAN_QQ_REGEXES:
                replacement = scrubber(replacement, rgx)
            if replacement == check_for_changes:
                # If clean_qq scrubbing changed nothing, we need not sub
                # anything in, so move the index to the end of this
                # match and go back to look for later matches.
                i = mo.end()
                continue

            # rebuild the text by subbing in `replacement`
            text = f"{text[:mo.start()]}{replacement}{text[mo.end():]}"

            # Continue searching from the end of that last replacement.
            i = mo.start() + len(replacement)

        # Clean up the remaining text, to convert "NE¼ of the NE¼" into
        # "NE¼NE¼" and "SW¼ SW¼" into "SW¼SW¼", by removing extraneous
        # "of the" and whitespace between previously identified
        # aliquots. Group 1 and 8 are the only parts we want to keep.
        check_for_changes = None
        while text != check_for_changes:
            check_for_changes = text
            text = re.sub(aliquot_intervener_remover_regex, r"\1\8", text)

        return text


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

    # Cardinal directions / aliquot names (without fractions).
    _N = 'N'
    _S = 'S'
    _E = 'E'
    _W = 'W'
    _NE = 'NE'
    _NW = 'NW'
    _SE = 'SE'
    _SW = 'SW'
    _ALL = 'ALL'

    # Various groupings for the aliquots / directions.
    QQ_HALVES = (_N, _S, _E, _W)
    QQ_QUARTERS = (_NE, _NW, _SE, _SW)
    QQ_SUBDIVIDE_DEFINITIONS = {
        _ALL: QQ_QUARTERS,
        _N: (_NE, _NW),
        _S: (_SE, _SW),
        _E: (_NE, _SE),
        _W: (_NW, _SW),
    }
    QQ_NS = (_N, _S)
    QQ_EW = (_E, _W)
    QQ_SAME_AXIS = {
        _N: QQ_NS,
        _S: QQ_NS,
        _E: QQ_EW,
        _W: QQ_EW
    }

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
            self.source = parent.source

        self.parse_cache = {}
        self.reset_cache()

        self.parse()

    def reset_cache(self):
        self.parse_cache = {
            "text_block": "",
            "unused_text": [],
            "unused_with_context": [],
            "w_flags_staging": [],
            "w_flag_lines_staging": []
        }

    def parse(self):
        """
        Parse the Tract description.

        NOTE: Documentation for this method is mostly maintained under
        ``Tract.parse()``, which essentially serves as a wrapper for the
        TractParser class and this method.
        """
        # TODO: Generate a list (saved as an attribute) of slice_indexes
        #   of the `text` for which portions were incorporated into lots
        #   and QQ's vs. not.

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

        ################################################################
        # General process is as follows:
        # 1) Scrub the aliquots (i.e. Convert 'Northeast Quarter of
        #       Southwest Quarter, E/2, NE4' to 'NE¼SW¼, E½, NE¼')
        # 2) Extract lot_regex matches from the text (actually uses
        #       lot_with_aliquot_regex to capture lot divisions).
        # 3) Unpack lot_regex matches into a lots.
        # 4) Extract aliquot_regex matches from the text.
        # 5) Convert the aliquot_regex matches into a qqs.
        # 6) Join the lots and qqs into a single list and return it.
        ################################################################

        # Extract the lots from the description (and leave the rest of
        # the description for aliquot parsing).  Replace any extracted
        # lots with ';;' to prevent unintentionally combining aliquots
        # later.
        lot_text_blocks = []
        remaining_text = text
        while True:
            # We use `lot_with_aliquot_regex` instead of `lot_regex`,
            # in order to ALSO capture leading aliquots -- i.e. we want
            # to capture 'N½ of Lot 1' (even if we won't be reporting
            # lot divisions), because otherwise the 'N½' will be read as
            # <the entire N/2> of the section.
            lot_aliq_mo = lot_with_aliquot_regex.search(remaining_text)
            if lot_aliq_mo is None:
                break
            else:
                lot_text_blocks.append(lot_aliq_mo.group())
                # reconstruct remaining_text, injecting ';;' where the
                # match was located
                p1 = remaining_text[:lot_aliq_mo.start()]
                p2 = remaining_text[lot_aliq_mo.end():]
                remaining_text = f"{p1};;{p2}"
        text = remaining_text

        for block in lot_text_blocks:
            # Unpack the lots in this block, and store the results
            # to the appropriate attributes
            self._unpack_lots(block, include_lot_divs=include_lot_divs)

        # Get a list of all of the aliquots strings
        aliq_text_blocks = []
        remaining_text = text
        while True:
            # Run this loop, pulling the next aliquot match until we run out.
            aliq_mo = aliquot_unpacker_regex.search(remaining_text)
            if aliq_mo is None:
                break
            else:
                # TODO: Implement context awareness. Should not pull aliquots
                #   before "of Section ##", for example.
                aliq_text_blocks.append(aliq_mo.group())
                remaining_text = remaining_text[:aliq_mo.start()] + ';;' \
                                + remaining_text[aliq_mo.end():]
        text = remaining_text

        # And also pull out "ALL" as an aliquot if it is clear of any
        # context (e.g., pull "ALL" but not "All of the").  First, get a
        # working text string, and replace each group of whitespace with
        # a single space.
        check_for_acceptable_all = re.sub(r'\s+', ' ', text).strip()
        all_mo = ALL_regex.search(check_for_acceptable_all)
        if all_mo is not None:
            if all_mo.group(2) is None:
                # If we ONLY found "ALL", then we're good.
                aliq_text_blocks.append(TractParser._ALL)
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

        if qq_depth is not None:
            qq_depth_min = qq_depth_max = qq_depth

        for aliq_text_block in aliq_text_blocks:
            # Unpack each aliq_text_block, and store its results to the
            # appropriate attribute.
            self._unpack_aliquots(
                aliq_text_block, qq_depth_min, qq_depth_max, qq_depth,
                break_halves)

        lots_qqs = self.lots + self.qqs

        self.gen_flags()

        return lots_qqs

    def _unpack_aliquots(
            self, aliquot_text_block, qq_depth_min=2, qq_depth_max=None,
            qq_depth=None, break_halves=False) -> list:
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
        # Also check for any quarters that occur before halves, and convert
        # them to halves before quarters. E.g., "SE/4W/2" -> "E/2SW/4"

        component_list = TractParser._standardize_aliquot_components(component_list)

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
            elif comp in TractParser.QQ_HALVES and (i < qq_depth_min or break_halves):
                depth = 1
            if comp in TractParser.QQ_QUARTERS:
                # Quarters (by definition) are already 1 depth more broken down
                # than halves (or 'ALL'), so subtract 1 to account for that
                depth -= 1

            # Subdivide this aliquot component, as deep as needed
            new_comp = TractParser._subdivide_aliquot(comp, depth)

            # Append it to our list of components (with subdivisions arranged
            # largest-to-smallest).
            subdivided_component_list.append(new_comp)

        # subdivided_component_list is now in the format:
        #   `[['SE'], ['NW', 'SW'], ['E2']]`
        # ...for E/2W/2SE/4, parsed to a qq_depth_min of 2.

        # Convert the 1-depth nested list into the final QQ list.
        qqs = TractParser._rebuild_aliquots(subdivided_component_list)
        self.qqs.extend(qqs)

        return qqs

    @staticmethod
    def _pass_back_halves(aliquot_components: list) -> list:
        """
        INTERNAL USE:
        Quarters that precede halves in an aliquot block are nonstandard
        but technically accurate. This function adjusts them to the
        equivalent description where the half occurs before the quarter.

        For example, ``'NE/4N/2'`` (passed here as ``['N', 'NE']``) is
        better described as the ``'N/2NE/4'``. Converted here to
        ``['NE', 'N']``.

        Similarly, the ``SE/4W/2'`` (passed here as ``['W', 'SE']``) is
        better described as the ``'E/2SW/4'``. Converted here to
        ``['SW', 'E']``.

        NOTE: This function does a single pass only!

        :param aliquot_components: A list of aliquot components without any
        fractions or numbers.
        :return: The fixed list of aliquot components.
        """
        aliquot_components.reverse()
        i = 0
        while i < len(aliquot_components) - 1:
            aq1 = aliquot_components[i]
            aq2 = aliquot_components[i + 1]

            # Looking for halves before quarters.
            if not (aq2 in TractParser.QQ_HALVES and aq1 in TractParser.QQ_QUARTERS):
                # This is OK.
                i += 1
                continue

            # Break the 'NE' into 'N' and 'E'.
            char1_ns, char2_ew = [*aq1]

            if aq2 in TractParser.QQ_NS:
                rebuilt_aq2 = f"{aq2}{char2_ew}"
                rebuilt_aq1 = char1_ns
            else:
                rebuilt_aq2 = f"{char1_ns}{aq2}"
                rebuilt_aq1 = char2_ew
            # Replace aq1 and aq2 with the rebuilt versions.
            aliquot_components[i] = rebuilt_aq1
            aliquot_components[i + 1] = rebuilt_aq2
            i += 1

        aliquot_components.reverse()
        return aliquot_components

    @staticmethod
    def _combine_consecutive_halves(aliquot_components):
        """
        INTERNAL USE:
        Check for any consecutive halves that are on opposite axes.
        E.g., the N/2E/2 should be converted to the NE/4, but the W/2E/2
        should be left alone.

        NOTE: This function does a single pass only!

        :param aliquot_components: A list of aliquot components without any
        fractions or numbers.
        :return: The fixed list of aliquot components.
        """

        aliquot_components_clean = []
        i = 0
        while i < len(aliquot_components):
            aq1 = aliquot_components[i]
            if i + 1 == len(aliquot_components):
                # Last item.
                aliquot_components_clean.append(aq1)
                break
            aq2 = aliquot_components[i + 1]
            if (aq1 in TractParser.QQ_HALVES
                    and aq2 in TractParser.QQ_HALVES
                    and aq2 not in TractParser.QQ_SAME_AXIS[aq1]):
                # e.g., the current component is 'N' and the next component is 'E';
                # those do not exist on the same axis, so we combine them into
                # the 'NE'. (And make sure the N/S direction goes before E/W.)
                new_quarter = f"{aq2}{aq1}" if aq1 in "EW" else f"{aq1}{aq2}"
                aliquot_components_clean.append(new_quarter)
                # Skip over the next component, because we already handled it during
                # this iteration.
                i += 2
            else:
                aliquot_components_clean.append(aq1)
                i += 1
        aliquot_components = aliquot_components_clean
        return aliquot_components

    @staticmethod
    def _standardize_aliquot_components(aliquot_components: list) -> list:
        """
        INTERNAL USE:
        Iron out any non-standard aliquot descriptions, such as 'cross-axes'
        halves (e.g., "W/2N/2" -> "NW/4") or quarters that occur before
        halves (e.g., "SE/4W/2" -> "W/2SE/4").

        :param aliquot_components: A list of aliquot components (already
        broken down by ``_unpack_aliquots()``).
        :return: The corrected list of aliquot components.
        """
        while True:
            # Do at least one pass, and then as many more as are needed
            # until the output matches the input.
            check_orig = aliquot_components.copy()
            aliquot_components = TractParser._pass_back_halves(aliquot_components)
            aliquot_components = TractParser._combine_consecutive_halves(aliquot_components)
            if aliquot_components == check_orig:
                break
        return aliquot_components

    @staticmethod
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

    @staticmethod
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
            if aliquot_component in TractParser.QQ_HALVES:
                return [aliquot_component + "2"]
            return [aliquot_component]

        # Construct a nested list, which _rebuild_aliquots() requires,
        # which will process it and spit out a flat list before this function
        # returns.
        divided = [[aliquot_component]]
        for _ in range(depth):
            if divided[-1][0] in TractParser.QQ_SUBDIVIDE_DEFINITIONS.keys():
                # replace halves and 'ALL' with quarters
                comp = divided.pop(-1)[0]
                divided.append(list(TractParser.QQ_SUBDIVIDE_DEFINITIONS[comp]))
            else:
                divided.append(list(TractParser.QQ_QUARTERS))

        # The N/2 (passed to this function as 'N') would now be parsed into
        # a format (at a depth of 2):
        #       [['NE', 'NW'], ['NE', 'NW', 'SE', 'SW']]
        # ... which gets reconstructed to:
        #       ['NENE', 'NWNE', 'SENE', 'SWNE', 'NENW', 'NWNW', 'SENW', 'SWNW']
        # ...by `_rebuild_aliquots()`

        return TractParser._rebuild_aliquots(divided)

    def _unpack_lots(self, lot_text_block, include_lot_divs=True):
        """
        INTERNAL USE:
        Feed in a string of a lot_regex match object, and parse them
        into formatted lot strings. Also parse lot acreages, if they
        exist in the string. Stores the results to ``.lots`` and
        ``.lot_acres`` attributes.

        ex:  ``'Lot 1(39.80), 2(30.22)'``
            -> ``.lots`` --> ``['L1', 'L2']``
            -> ``.lot_acres`` --> ``{'L1' : '39.80', 'L2' : '30.22'}``
        """

        # This will be the output list of Lot numbers [L1, L2, L5, ...]:
        lots = []

        # This will be a dict of stated gross acres for the respective lots,
        # keyed by 'L1', 'L2', etc. It only gets filled for the lots for
        # which gross acreage was specified in parentheses.
        lot_acreages = {}

        # A working list of the lots. Note that this gets filled from
        # last-to-first on this working text block. It will be reversed
        # before adding it to the main lots list:
        working_lots = []

        # `found_through` will switch to True at the start of an elided list
        # (e.g., when we're at '3' in "Lots 3 - 9")
        found_through = False
        i = len(lot_text_block)
        while True:
            lots_mo = lot_regex.search(lot_text_block, endpos=i)

            if not lots_mo:
                # We're done when we're out of lot numbers.
                break

            # Pull the right-most lot number (as a string):
            lot_num = TractParser._get_last_lot(lots_mo)

            # How far we'll search in the next loop.
            i = TractParser._start_of_last_lot(lots_mo)

            # Clean up any leading '0's in lot_num.
            lot_num = str(int(lot_num))
            if lot_num == '0':
                self.w_flags.append('Lot0')

            new_lot = f"L{lot_num}"

            if found_through:
                # If we've identified an elided list (e.g., 'Lots 3 - 9').
                prev_lot = working_lots[-1]
                # Start at lot_num identified earlier this loop.
                start_of_list = int(lot_num)
                # End at last round's lot_num (omit leading 'L'; convert to int).
                end_of_list = int(prev_lot[1:])
                correct_order = True
                if start_of_list >= end_of_list:
                    self.w_flags.append('nonSequen_Lots')
                    self.w_flag_lines.append(
                        ('nonSequen_Lots',
                         f"Lots {start_of_list} - {end_of_list}"))
                    correct_order = False

                ########################################################
                # start_of_list and end_of_list variable names are
                # unintuitive. Here's an explanation:
                # The 'lots' list is being filled in reverse by this
                # algorithm, starting at the end of the search string
                # and running backwards. Thus, this particular loop,
                # which is attempting to unpack "Lots 3 - 9", will be
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
                if not correct_order:
                    a, b, c = end_of_list + 1, start_of_list + 1, 1

                # Add each new lot in this range.
                new_lots = [f"L{i}" for i in range(a, b, c)]
                working_lots.extend(new_lots)
                found_through = False  # reset.

            else:
                # If it's a standalone lot (not the start of an elided
                # list), we append it
                working_lots.append(new_lot)

            # If acreage was specified for this lot, clean it up and add
            # to dict, keyed by the new_lot.
            new_acres = TractParser._get_lot_acres(lots_mo)
            if new_acres:
                lot_acreages[new_lot] = new_acres

            # If we identified at least two lots, we need to check if
            # the last one is the end of an elided list, by calling
            # _thru_lot() to check for us:
            if TractParser._is_multi_lot(lots_mo):
                found_through = TractParser._thru_lot(lots_mo)

        # Reverse working_lots, so that it's in the order it was in the original
        # description, and append it to our main list:
        working_lots.reverse()
        lots.extend(working_lots)

        if include_lot_divs:
            # If we want include_lot_divs, add it to the front of each parsed lot.
            leading_aliq = TractParser._get_leading_aliquot(
                lot_with_aliquot_regex.search(lot_text_block))
            leading_aliq = leading_aliq.replace('¼', '')
            leading_aliq = leading_aliq.replace('½', '2')
            if leading_aliq != '':
                if TractParser._first_lot_is_plural(lot_regex.search(lot_text_block)):
                    # If the first lot is plural, we apply leading_aliq to
                    # all lots in the list
                    lots = [f'{leading_aliq} of {lot}' for lot in lots]
                else:
                    # If the first lot is NOT plural, apply leading_aliq to
                    # ONLY the first lot:
                    firstLot = f'{leading_aliq} of {lots.pop(0)}'
                    lots.insert(0, firstLot)
                # TODO: This needs to be a bit more robust to handle all real-world
                #   permutations.  For example: 'N/2 of Lot 1 and 2' (meaning
                #   ['N2 of L1', 'N2 of L2']) is possible -- albeit poorly formatted
                #   See also, "N/2 of Lot 1 - 3"...

        self.lots.extend(lots)
        for k, v in lot_acreages.items():
            self.lot_acres[k] = v

        return None

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
            flag = "dup_lot"
            context = f"{flag}<{','.join(dup_lots)}>"
            self.w_flags.append(flag)
            self.w_flag_lines.append((flag, context))

        if dup_qqs:
            flag = "dup_qq"
            context = f"{flag}<{','.join(dup_qqs)}>"
            self.w_flags.append(flag)
            self.w_flag_lines.append((flag, context))

    ####################################################################
    # Tools for interpreting lot_regex and lot_with_aliquot_regex match
    # objects:
    ####################################################################

    @staticmethod
    def _is_multi_lot(lots_mo) -> bool:
        """
        INTERNAL USE:
        Return a bool, whether a lot_regex match object is a multiLot.
        """
        try:
            return (lots_mo.group(11) is not None) and (lots_mo.group(19) is not None)
        except (IndexError, AttributeError):
            return False

    @staticmethod
    def _thru_lot(lots_mo) -> bool:
        """
        INTERNAL USE:
        Return a bool, whether the word 'through' (or an abbreviation)
        appears before the right-most lot in a lot_regex match object.
        """

        try:
            if TractParser._is_multi_lot(lots_mo):
                thru_mo = through_regex.search(lots_mo.group(15))
            else:
                return False

            found_through = True
            if thru_mo is None:
                found_through = False

            return found_through

        except (IndexError, AttributeError):
            return False

    @staticmethod
    def _is_single_lot(lots_mo) -> bool:
        """
        INTERNAL USE:
        Return a bool, whether a lot_regex match object is a single lot.
        """
        try:
            return (lots_mo.group(11) is not None) and (lots_mo.group(19) is None)
        except (IndexError, AttributeError):
            return False

    @staticmethod
    def _get_last_lot(lots_mo):
        """
        INTERNAL USE:
        Extract the right-most lot in a lot_regex match object. Returns a
        string if found; if none found, returns None.
        """
        try:
            if TractParser._is_multi_lot(lots_mo):
                return lots_mo.group(19)
            elif TractParser._is_single_lot(lots_mo):
                return lots_mo.group(11)
            else:
                return None
        except (IndexError, AttributeError):
            return None

    @staticmethod
    def _start_of_last_lot(lots_mo):
        """
        INTERNAL USE:
        Return an int of the starting position of the right-most lot in a
        lot_regex match object. Returns None if none found.

        :return: An int for the index of the start of the right-most lot
        (or None if not found).
        """
        try:
            if TractParser._is_multi_lot(lots_mo):
                return lots_mo.start(19)
            elif TractParser._is_single_lot(lots_mo):
                return lots_mo.start(11)
            return None
        except (IndexError, AttributeError):
            return None

    @staticmethod
    def _get_lot_acres(lots_mo):
        """
        INTERNAL USE:

        :return: The string of the lot_acres for the right-most lot,
        without parentheses. If no match, then returns None.
        """
        try:
            if TractParser._is_multi_lot(lots_mo):
                if not lots_mo.group(14):
                    return None
                else:
                    lot_acres_mo = lotAcres_unpacker_regex.search(lots_mo.group(14))

            elif TractParser._is_single_lot(lots_mo):
                if not lots_mo.group(12):
                    return None
                else:
                    lot_acres_mo = lotAcres_unpacker_regex.search(lots_mo.group(12))

            else:
                return None

            if not lot_acres_mo:
                return None
            else:
                lot_acres_text = lot_acres_mo.group(1)

                # Swap in a period if there was a comma separating:
                lot_acres_text = lot_acres_text.replace(',', '.')
                return lot_acres_text
        except (IndexError, AttributeError):
            return None

    @staticmethod
    def _first_lot_is_plural(lots_mo):
        """
        INTERNAL USE:

        :return: A bool, whether the first instance of the word 'lot' in
        a lots_regex match object is pluralized. If no match or
        incorrect match object is passed, return None.
        """
        try:
            return lots_mo.group(9).lower() == 'lots'
        except (IndexError, AttributeError):
            return None

    ####################################################################
    # Tools for interpreting lot_with_aliquot_regex match objects:
    ####################################################################

    @staticmethod
    def _has_leading_aliquot(mo):
        """
        INTERNAL USE:

        :return: A bool, whether this lot_with_aliquot_regex match
        object has a leading aliquot. Returns None if no match found.
        """
        try:
            return mo.group(1) is None
        except (IndexError, AttributeError):
            return None

    @staticmethod
    def _get_leading_aliquot(mo):
        """
        INTERNAL USE:

        :return: The string of the leading aliquot component from a
        lot_with_aliquot_regex match object. Returns None if no match.
        """
        try:
            if mo.group(2) is not None:
                return mo.group(2)
            else:
                return ''
        except (IndexError, AttributeError):
            return None

    @staticmethod
    def _get_lot_component(mo):
        """
        INTERNAL USE:
        Return the string of the entire lots component from a
        lot_with_aliquot_regex match object. Returns None if no match.
        """
        try:
            if mo.group(7):
                return mo.group(7)
            else:
                return ''
        except (IndexError, AttributeError):
            return None


########################################################################
# Misc. tools
########################################################################

def find_twprge(
        text, default_ns=None, default_ew=None, preprocess=False,
        ocr_scrub=False):
    """
    Returns a list of all T&R's in the text (formatted as '000n000w',
    or with fewer digits as needed).

    :param text: The text to scour for Twp/Rge's.
    :param default_ns: If N/S is not specified for the Twp, assume this
    direction. (Defaults to 'n'.)
    :param default_ew: If E/W is not specified for the Twp, assume this
    direction. (Defaults to 'w'.)
    :param preprocess: A bool, whether to preprocess the text before
    searching for Twp/Rge's. (Defaults to `False`)
    """
    if ocr_scrub:
        preprocess = True

    if preprocess:
        text = PLSSPreprocessor(text, default_ns, default_ew, ocr_scrub).text

    # Search the PLSS description for all T&R's, and for each match,
    # compile a clean T&R
    tr_list = [
        PLSSParser._compile_twprge_mo(mo, default_ns, default_ew)
        for mo in twprge_regex.finditer(text)
    ]
    return tr_list


def trs_to_dict(trs) -> dict:
    """
    Take a compiled Twp/Rge/Sec (in the standard pyTRS format) and break
    it into a dict, keyed as follows:
        "twp"       -> Twp number + direction (a str or None)
        "twp_num"   -> Twp number (an int or None);
        "twp_ns"    -> Twp direction ('n', 's', or None);
        "twp_undef" -> whether the Twp was undefined. **
        "rge"       -> Rge number + direction (a str or None)
        "rge_num"   -> Rge num (an int or None);
        "rge_ew"    -> Rge direction ('e', 'w', or None)
        "rge_undef" -> whether the Rge was undefined. **
        "sec_num"   -> Sec number (an int or None)
        "sec_undef" -> whether the Sec was undefined. **

    ** Note that error parses do NOT qualify as 'undefined'. Undefined
    and error values are both stored as None. 'twp_undef', 'rge_undef',
    and 'sec_undef' are included to differentiate between error vs.
    undefined, in case that distinction is needed.

    :param trs: The Twp/Rge/Sec (in the pyTRS format) to be broken
    apart.
    :return: A dict with the various elements.
    """
    return TRS.trs_to_dict(trs)


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
        new_sec = sec_mo[2][-2:].rjust(2, '0')
        sec_list.append(new_sec)
    return sec_list


def find_multisec(text, flat=True) -> list:
    """
    Returns a list of all identified multi-Section numbers in the
    text (formatted as '00'). Returns a flattened list by default, but
    can return a nested list (one per multisec) with `flat=False`.
    """

    packed_multisec_list = []
    unpacked_multisec_list = []

    for ms_mo in multiSec_regex.finditer(text):
        packed_multisec_list.append(ms_mo.group())

    for multisec in packed_multisec_list:
        working_sec_list = PLSSParser._unpack_sections(multisec)
        if len(working_sec_list) == 1:
            # skip any single-section matches
            continue
        unpacked_multisec_list.append(working_sec_list)

    if flat:
        unpacked_multisec_list = flatten(unpacked_multisec_list)

    return unpacked_multisec_list


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


def group_tracts(
        to_group, by_attribute="twprge", into: dict = None,
        sort_key=None, sort_reverse=None):
    """
    Group Tract objects into a dict of TractLists, keyed by unique
    values of the specified attribute (``by_attribute``). By default,
    will filter into groups of Tracts that share Twp/Rge (i.e.
    ``'twprge'``). Pass ``by_attribute`` as a list of attributes to
    filter by multiple attributes, and get a NESTED dict back. (Each
    consecutive attribute in the list will be another layer of nesting.)

    :param to_group: The source of Tract(s) to group -- i.e., a single
    Tract, a TractList, another list-like object containing Tracts
    and/or parsed PLSSDesc objects, or a single parsed PLSSDesc object.

    :param by_attribute: The str name of an attribute of Tract
    objects. (Defaults to `'twprge'`). NOTE: Must be a hashable
    type!  (Optionally pass as a list of str names of attributes to
    do multiple groupings.)

    :param into: (Optional) An existing dict into which to filter the
    Tracts. If not specified, will create a new dict. Use this arg if
    you need to continue adding Tracts to an existing grouped dict.

    :param sort_key: (Optional) How to sort each grouped TractList
    in the returned dict. Use a string that works with the
    ``.sort_tracts(key=<str>)`` method (e.g., 'i, s, r.ew, t.ns') or
    a lambda function, as you would with the builtin
    ``list.sort(key=<lambda>)`` method. (Defaults to ``None``, i.e.
    not sorted.)

    May optionally pass `sort_key` as a list of sort keys, to be
    applied left-to-right. Here, you may mix and match lambdas and
    ``.sort_tracts()`` strings.

    :param sort_reverse: (Optional) Whether to reverse the sort.
    NOTE: Only has an effect if the ``sort_key`` is passed as a
    lambda -- NOT as a custom string sort key. Defaults to ``False``.

    NOTE: If ``sort_key`` was passed as a list, then
    ``sort_reverse`` must be passed as EITHER a single bool that
    will apply to all of the (non-string) sorts, OR as a list or
    tuple of bools that is equal in length to ``sort_key`` (i.e. the
    values in ``sort_key`` and ``sort_reverse`` will be matched up
    one-to-one).
    Filter Tract objects into a dict of TractLists, keyed by unique
    values of `by_attribute`. By default, will filter into groups of
    Tracts that share Twp/Rge (i.e. `'twprge'`).

    :return: A dict of TractList objects, each containing the Tracts
    with matching values of the ``by_attribute``.  (If ``by_attribute``
    was passed as a list of attribute names, then this will return as a
    nested dict, with TractList objects being the deepest values.)
    """
    tl = TractList.from_multiple(to_group)
    return tl.group(by_attribute, into, sort_key, sort_reverse)


def sort_grouped_tracts(tracts_dict, sort_key, reverse=False) -> dict:
    """
    Sort TractLists within a dict of grouped Tracts. Also works on a
    nested dict (i.e. when multiple groupings were done).

    Returns the original ``tracts_dict``, but with the TractList objects
    having been sorted in-situ.

    :param tracts_dict: A dict, as returned by a TractList grouping
    method or function (e.g., ``TractList.group()`` or
    ``group_tracts()``).
    :param sort_key: How to sort the Tracts. (Can be any value
    acceptable to the ``TractList.sort_tracts()`` method.)
    :param reverse: (Optional) Whether to reverse lambda sorts. (More
    detail provided in the docs for ``TractList.sort_tracts()``.)
    :return: The original ``tracts_dict``, with the TractList objects
    having been sorted in-situ.
    """
    return TractList.sort_grouped_tracts(tracts_dict, sort_key, reverse)


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


def _clean_attributes(*attributes) -> list:
    """
    INTERNAL USE:
    Ensure that each element has been entered as a string.
    Returns a flattened list of strings.
    """
    attributes = flatten(attributes)
    if len(attributes) == 0:
        return []
    clean = []
    for att in attributes:
        if not isinstance(att, str):
            raise TypeError(
                'Attributes must be specified as strings (or list of strings).')
        else:
            clean.append(att)
    return clean


__all__ = [
    PLSSDesc,
    Tract,
    TractList,
    TRS,
    TRSList,
    Config,
    IMPLEMENTED_LAYOUTS,
    IMPLEMENTED_LAYOUT_EXAMPLES,
    trs_to_dict,
    find_twprge,
    find_sec,
    find_multisec,
    group_tracts,
    sort_grouped_tracts
]
