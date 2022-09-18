
"""
A class to represent a Twp/Rge/Sec combination, with its corresponding
description block, and to parse that description block into lots and
aliquot Quarter-Quarters ("QQs").
"""

from ...utils import (
    _confirm_list_of_strings as clean_attributes,
)
from ..config import (
    Config,
    ConfigError,
)
from ..trs import TRS
from .tract_preprocess import TractPreprocessor
from .tract_parse import TractParser


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
        return self.quick_desc()

    def __repr__(self):
        return (
            f"Tract({'' if self.parse_complete else 'un'}parsed)"
            f"<{self.quick_desc_short(max_len=20)!r}>"
        ).replace('\n', r'\n')

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

    def trs_is_undef(self, twp=True, rge=True, sec=True):
        """
        Check if any component of this Tract's Twp/Rge/Sec is undefined.
        (Checks against Twp, Rge, and Sec by default, and returns True
        if any is undefined.)

        :param twp: Check if Twp is undefined.
        :param rge: Check if Rge is undefined.
        :param sec: Check if Sec is undefined.
        :return: A bool, whether ANY of the checked values are
        undefined.
        """
        return self.__trs.is_undef(twp, rge, sec)

    def trs_is_error(self, twp=True, rge=True, sec=True):
        """
        Check if any component of this Tract's Twp/Rge/Sec is an error.
        (Checks against Twp, Rge, and Sec by default, and returns True
        if any is an error.)

        :param twp: Check if Twp is an error.
        :param rge: Check if Rge is an error.
        :param sec: Check if Sec is an error.
        :return: A bool, whether ANY of the checked values are errors.
        """
        return self.__trs.is_error(twp, rge, sec)

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

        attributes = clean_attributes(attributes)
        return {att: getattr(self, att, f"{att}: n/a") for att in attributes}

    def to_list(self, *attributes) -> list:
        """
        Compile the requested attributes into a list.

        :param attributes: The attribute names (instance variables) to
        include.
        :return: A list of attribute values.
        """

        attributes = clean_attributes(attributes)
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
        and that evaluates to ``True`` will cause this behavior.)
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


__all__ = [
    'Tract'
]