
"""
A class to represent a full PLSS land description, parse it into
``Tract`` objects, and extract or export the resulting data.
"""

from ..config import (
    Config,
    ConfigError,
    COPY_ALL,
)
from ..containers import TractList
from .plss_preprocess import (
    PLSSPreprocessor,
)
from .plss_parse import (
    PLSSParser,
    SecFinder,
    deduce_layout,
)


class PLSSDesc:
    """
    A class to represent a full PLSS land description, parse it into
    ``Tract`` objects, and extract or export the resulting data.

    Each object of this class is a full PLSS description, taking the raw
    text of the original description as input, and parsing it into one
    or more ``Tract`` objects (each ``Tract`` containing one Twp/Rge/Sec
    combo and the corresponding description of the land within that
    Twp/Rge/Sec, optionally with lots and aliquot quarter-quarters
    broken out -- see ``Tract`` documentation for more details).

    Configure the parsing algorithm with config parameters at init,
    passed in ``config=`` (taking either a ``Config`` object or a string
    containing equivalent config parameters -- see documentation on
    ``Config`` objects for possible parameters).

    *Note:* If direction for Township (N/S) or Range (E/W) is not
    provided in the text being parsed, it will be assumed. Specify
    ``default_ns`` and ``default_ew`` for each ``PLSSDesc`` object to
    control how these should be assumed (as a ``config=`` parameter at
    init, or as an argument in the appropriate method). Alternatively,
    we can change ``MasterConfig.default_ns`` and
    `MasterConfig.default_ew`` (class variables) to control ALL
    unspecified ``default_ns`` and ``default_ew`` (these class variables
    will control for both ``PLSSDesc`` and ``Tract`` objects). However,
    specifying ``default_ns`` and ``default_ew`` for a given object will
    override the master defaults for that particular object.

    The default settings are for North (``'n'``) and West (``'w'``).

    *Important:* When specifying ``default_ns``, ``default_ew``,
    ``MasterConfig.default_ns``, or ``MasterConfig.default_ew``, be
    sure to use ONLY single, lower-case letters (``'n'``, ``'s'``,
    ``'e'``, and ``'w'``). Or don't worry about it, and just set them as
    ``MasterConfig.NORTH``, ``MasterConfig.SOUTH``,
    ``MasterConfig.EAST``, or ``MasterConfig.WEST``.


    PARSING
    _______
    ``PLSSDesc`` are automatically parsed into ``Tract`` objects upon
    init. Alternatively / additionally, call the ``.parse()`` method at
    some point after init.


    IMPORTANT INSTANCE VARIABLES AFTER PARSING
    ------------------------------------------
    These are the notable attributes of a ``PLSSDesc`` object. For the
    tract information (i.e. the data fields you might want to write to a
    spreadsheet or table), look into the attributes of ``Tract`` objects
    (which can be created by a ``PLSSDesc``).

    - ``.orig_desc``
        - The original text. (Set from the first positional argument at
          init.)

    - ``.tracts``
        - a ``TractList`` object (an emulated list) containing the
          ``Tract`` objects that were generated from parsing this
          object.

    - ``.pp_desc``
        - The preprocessed description.

    - ``.source``
        - (Optional) Any value of any type (probably a ``str`` or
          ``int``) specifying where the description came from. Useful if
          parsing multiple descriptions and need to internally keep
          track where they came from. (Optionally specify at init with
          parameter ``source=<whatever>``.) Will also be inherited by
          any ``Tract`` objects created by this ``PLSSDesc``.

    - ``.w_flags``
        - a list of warning flags (strings) generated during
          preprocessing and/or parsing.

    - ``.w_flag_lines``
        - a list of 2-tuples, each being a warning flag and the line or
          context from the description that caused the warning.

    - ``.e_flags``
        - a list of error flags (strings) generated during preprocessing
          and/or parsing.

    - ``.e_flag_lines``
        - a list of 2-tuples, each being an error flag and the line or
          context from the description that caused the error.

    - ``.flags``
        - a combined list of warning and error flags.

    - ``.flag_lines``
        - a combined lines of 2-tuples, for warning and error flags.

    - ``.desc_is_flawed``
        - a bool, whether an apparently fatal flaw was discovered during
          parsing. (*Note:* If there is anything in ``.e_flags`` it will
          be considered flawed.)

    - ``.layout``
        - The user-dictated or algorithm-deduced layout of the
          description (controls how the parsing algorithm interprets the
          text).


    STREAMLINED OUTPUT OF THE PARSED TRACT DATA
    -------------------------------------------
    See the notable attributes listed in the ``Tract`` documentation.
    Those variables can be compiled with these ``PLSSDesc`` methods:

    - ``.quick_desc()``
        - Returns a string of the entire parsed description.

    - ``.print_desc()``
        - Does the same thing, but prints to console.

    - ``.tracts_to_dict()``
        - Compile the requested attributes for each ``Tract`` into a
          dict, and returns a list of those dicts (i.e. the list is
          equal in length to the ``TractList`` stored at ``.tracts``).

    - ``.tracts_to_list()``
        - Compile the requested attributes for each ``Tract`` into a
          list, and returns a nested list of those list (i.e. the
          top-level list is equal in length to the ``TractList`` stored
          at ``.tracts``).

    - ``.iter_to_dict()``
        - Identical to ``.tracts_to_dict()``, but returns a generator of
          dicts for the ``Tract`` data.

    - ``.iter_to_list()``
        - Identical to ``.tracts_to_list()``, but returns a generator of
          lists for the ``Tract`` data.

    - ``.tracts_to_csv()``
        - Compile the requested attributes for each ``Tract`` and write
          them to a .csv file, with one row per ``Tract``.
            - (See ``pytrs.tractwriter.TractWriter`` class for more
              robust writing to .csv files.)

    - ``.tracts_to_str()``
        - Compile the requested attributes for each ``Tract`` into an
          orderly string.

    - ``.print_data()``
        - Equivalent to ``.tracts_to_str()``, but the data is printed to
          console.

    - ``.list_trs()``
        - Return a list of all twp/rge/sec combinations in the
          ``TractList`` stored in ``.tracts``, optionally removing
          duplicates.


    SORTING / GROUPING / FILTERING TRACTS BY ATTRIBUTE VALUES
    ---------------------------------------------------------
    These methods will sort, group, or filter the ``Tract`` objects
    contained in the ``.tracts`` attribute:

    - ``.sort_tracts()``
        - Custom sorting based on the Twp/Rge/Sec or original creation
          order of each ``Tract``. Can also take parameters from the
          built-in ``list.sort()`` method.

    - ``.group_by()`` and ``.group_by_nested()``
        - Group ``Tract`` objects into a dict of ``TractList`` objects,
          based on their shared attribute values (e.g., by Twp/Rge), and
          optionally sort them.

    - ``.filter()``
        - Get a new ``TractList`` of those ``Tract`` objects that match
          some condition, and optionally remove them from the original
          ``TractList`` (i.e. from the ``.tracts`` attribute).

    - ``.filter_errors()``
        - Get a new ``TractList`` of those ``Tract`` objects whose Twp,
          Rge, and/or Section were an error or undefined, and optionally
          remove them from the original ``TractList`` (i.e. from the
          ``.tracts`` attribute).

    - ``.filter_duplicates()``
        - Get a new ``TractList`` of duplicate ``Tract`` objects, and
          optionally remove them from the original ``TractList`` (i.e.
          from the ``.tracts`` attribute).
    """

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
        more ``Tract`` objects, which are stored in the ``.tracts``
        attribute.

        :param raw_plss: The text of the description to be parsed.

        :param layout: The pyTRS layout. If not specified, will be
         deduced when initialized, and/or when parsed. See available
         options in ``pytrs.IMPLEMENTED_LAYOUTS`` and examples in
         ``pytrs.IMPLEMENTED_LAYOUT_EXAMPLES``.

        :param config: Either a ``Config`` object, or a string of
         parameters to configure how the ``PLSSDesc`` object should be
         parsed. (See documentation on ``Config`` objects for optional
         config parameters.)

        :param parse_qq: Whether to parse the ``Tract`` objects that
         result from parsing this ``PLSSDesc`` into lots and QQs.

         *Note:* If ``parse_qq`` is specified as a kwarg at init, and
         also specified in ``config`` (i.e. ``config='parse_qq'``), then
         the parameter ``parse_qq=<bool>`` will control.

        :param source: (Optional) Essentially any value (e.g., a unique
         identifier number, document id, or filepath) specifying where
         the description came from. (Useful if parsing multiple
         descriptions and need to internally keep track where they came
         from.)

        :param wait_to_parse: A bool, whether to wait to parse at init.
         (Defaults to ``False`` -- i.e., parse at init.)
        """
        self.orig_desc = raw_plss
        if not isinstance(raw_plss, str):
            raise TypeError(
                f"`raw_plss` must be of type 'string'. "
                f"Passed as type {type(raw_plss)}.")
        self.source = source

        # The layout of this PLSS description -- Initially None, but may
        # be set to one of the values in the IMPLEMENTED_LAYOUTS tuple
        # before __init__() returns, if specified in `config`.
        self.layout = None
        self.current_layout = None

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

        # These two attributes control whether we should require a colon
        # between Section ## and tract description (for TRS_DESC and
        # S_DESC_TR layouts only).
        self.sec_colon_cautious = None
        self.sec_colon_required = False

        # Whether to suppress any divisions of lots.
        # (i.e. 'N/2 of Lot 1' -> 'N2 of L1')
        self.suppress_lot_divs = False

        # Whether to iron out common OCR artifacts.
        self.ocr_scrub = False

        # Whether to segment the text during parsing (can /potentially/
        # capture descriptions with multiple layouts).
        self.segment = False

        # Attributes to control how deeply QQ's should be parsed.
        # If `.qq_depth` is set, it will override `.qq_depth_min` and
        # `.qq_depth_max`
        self.qq_depth = None
        self.qq_depth_min = 2
        self.qq_depth_max = None
        self.break_halves = False

        # Apply settings from `config=`, overwriting the above values,
        # if specified by user.
        self.config = config

        # list of Tract objs after parsing.
        self.tracts = TractList()
        # Warning flags.
        self.w_flags = []
        # list of 2-tuples that caused warning flags (warning flag, text string)
        self.w_flag_lines = []
        # Error flags.
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

        if not self.wait_to_parse:
            self.parse(commit=True)
        else:
            self.preprocess(commit=True)

    @property
    def require_colon(self):
        """
        Check values of ``.sec_colon_required`` and
        ``.sec_colon_cautious`` to determine whether to require_colon
        after section number (i.e. determine the value to pass to
        ``require_colon=`` in the ``PLSSParser``).

        :return: ``True``, ``False``, or
         ``SecFinder.SEC_COLON_CAUTIOUS``.

         (The ``PLSSParser`` will know what to do with these values.)
        """
        required = self.sec_colon_required
        if self.sec_colon_cautious and not self.sec_colon_required:
            required = SecFinder.SEC_COLON_CAUTIOUS
        return required

    def __str__(self):
        return self.orig_desc

    def __repr__(self):
        dsc = self.orig_desc
        if len(dsc) > 30:
            dsc = f"{dsc[:27]}..."
        return f"PLSSDesc({len(self.tracts)})<{dsc!r}>".replace("\n", r"\n")

    def __getitem__(self, item):
        """
        ``PLSSDesc`` are LIMITEDLY subscriptable, in that you can ACCESS
        elements (i.e. ``Tract`` objects) of the ``.tracts``
        (a ``TractList``). Therefore::

            some_plssdesc[0]
            # is the same as...
            some_plssdesc.tracts[0]

        ...and we can slice, thus::

            some_plssdesc[:2]
            # is the same as...
            some_plssdesc.tracts[:2]

        ...and we can iterate over all its ``Tract`` objects::

            for tract in some_plssdesc:
                pass
            # is the same as...
            for tract in some_plssdesc.tracts:
                pass

        But you *cannot* assign, pop, or insert with a ``PLSSDesc``
        directly. If any of that functionality is required, work
        directly with the ``.tracts`` attribute (a ``TractList`` object)
        or get a new ``TractList`` to work with by re-parsing the
        ``PLSSDesc``, thus::

            new_tractlist = some_plssdesc.parse(commit=False)
        """
        return self.tracts.__getitem__(item)

    @property
    def config(self):
        return self.__config

    @config.setter
    def config(self, new_config):
        """
        Apply the relevant settings from a ``Config`` object to this
        object; takes either a string (i.e. config text) or a ``Config``
        object.

        :param new_config: Either a ``Config`` object, or equivalent
         config parameters. (See ``Config`` documentation for optional
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
            sec_colon_cautious=None,
            sec_colon_required=None,
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
        ``.e_flags``, and ``.e_flag_lines``).

        Returns only the ``TractList`` object containing the parsed
        ``Tract`` objects (i.e. what would be stored to ``.tracts`),
        regardless of ``commit=``.

        *Note:* Any parameters passed here will override the
        corresponding ``.config`` settings, but any unspecified
        parameters will defer to ``.config``.

        :param layout: The layout to be assumed. If not specified,
         defaults to whatever is in ``.layout`` attribute; and if not
         specified there, will be automatically deduced.

        :param default_ns: How to interpret townships for which
         direction was not specified -- i.e. either ``'n'`` or ``'s'``.
         (Defaults to ``.default_ns`` attribute (if configured) or to
         ``MasterConfig.default_ns`` which is ``'n'`` unless otherwise
         configured.)

        :param default_ew: How to interpret ranges for which direction
         was not specified -- i.e. either ``'e'`` or ``'w'``. (Defaults
         to ``.default_ew`` attribute (if configured) or to
         ``MasterConfig.default_ew`` which is ``'w'`` unless otherwise
         configured.)

        :param clean_up: Whether to clean up common 'artifacts' from
         parsing. If not specified, defaults to ``False`` for parsing
         the ``'copy_all'`` layout, and ``True`` for all others.

        :param parse_qq: Whether to parse each resulting ``Tract``
         into lots and QQs when initialized. If not specified, defaults
         to whatever is specified in ``.parse_qq`` attribute (``False``
         unless otherwise configured).

        :param clean_qq: Whether to expect only clean lots and QQ's
         (i.e. no metes-and-bounds, exceptions, complicated
         descriptions, etc.). Defaults to whatever is specified in
         ``.clean_qq`` attribute (``False``, unless configured
         otherwise).

        :param sec_colon_cautious: See ``see_colon_required`` parameter.

        :param sec_colon_required: Use ``sec_colon_cautious`` or
         ``sec_colon_required`` to determine whether to require a colon
         between the section number and the following description (only
         has an effect on ``'TRS_desc'`` or ``'S_desc_TR'`` layouts). If
         ``sec_colon_required`` is ``True``, then ``sec_colon_cautious``
         will have no effect.

         If neither is specified, it will default to whatever was set at
         init; and unless otherwise specified there, will default to
         ``False`` (i.e. require no colon).

         If ``sec_colon_cautious=True`` (and ``sec_colon_required`` is
         ``False`` or ``None``), it will use a 'two-pass' method, where
         first it will require the colon; and if no matching sections
         are found, it will do a second pass where colons are not
         required.

            Example::

                parsing 'T154N-R97W Section 14 NE/4'...

                [default, neither specified] --> match (but beware false
                            positives)
                ``sec_colon_required=True`` --> no match
                ``sec_colon_cautious=True`` (and ``sec_colon_required``
                    not specified) --> no match on first pass; if no
                            other sections are identified, will be
                            matched on second pass.

        :param segment: Whether to break the text down into segments,
         with one MATCHING township/range per segment (i.e. only
         Twp/Rges that are appropriate to the specified layout will
         count for the purposes of this parameter). This can potentially
         capture descriptions whose layout changes partway through, but
         can also cause appropriate warning/error flags to be missed. If
         not specified here, defaults to whatever is set in ``.segment``
         attribute.

        :param ocr_scrub: Whether to try to iron out common OCR
         'artifacts'. May cause unintended changes. (Defaults to
         ``.ocr_scrub`` attribute, which is ``False`` unless otherwise
         configured.)

        :param commit: Whether to commit the results to the appropriate
         instance attributes. Defaults to ``True``.

        :param qq_depth_min: (Optional, and only relevant if parsing
         Tracts into lots and QQs.) An int, specifying the minimum depth
         of the parse. If not set here, will default to settings from
         init (if any), which in turn default to 2, i.e. to
         quarter-quarters (e.g., 'N/2NE/4' -> ``['NENE', 'NENE']``).
         Setting to 3 would return 10-acre subdivisions (i.e. dividing
         the 'NENE' into ``['NENENE', 'NWNENE', 'SENENE', 'SWNENE']``),
         and so forth.

         *Warning:* Higher than a few levels of depth will result in
         very slow performance.

        :param qq_depth_max: (Optional, and only relevant if parsing
         Tracts into lots and QQs.) An int, specifying the maximum depth
         of the parse. If set as 2, any subdivision smaller than
         quarter-quarter (e.g., 'NENE') would be discarded -- so, for
         example, the 'N/2NE/4NE/4' would simply become the ``'NENE'``.
         Must be greater than or equal to ``qq_depth_min``. (Defaults to
         ``None`` -- i.e. no maximum.)

        :param qq_depth: (Optional, and only relevant if parsing Tracts
         into lots and QQs.) An int, specifying both the minimum and
         maximum depth of the parse. If specified, will override both
         ``qq_depth_min`` and ``qq_depth_max``. (Defaults to `None` --
         i.e. use ``qq_depth_min`` and optionally ``qq_depth_max``.)

        :param break_halves: (Optional, and only relevant if parsing
         Tracts into lots and QQs.) Whether to break halves into
         quarters, even if we're beyond the ``qq_depth_min``. (``False``
         by default.)

        :return: Returns a ``TractList`` object containing the
         resulting ``Tract`` objects. (That same ``TractList`` will be
         stored to ``.tracts`` if ``commit=True``.
        """

        # --------------------------------------------------------------
        # Note that this method is actually a wrapper for initializing
        # a PLSSParser object and extracting the relevant attributes
        # from that. User-facing documentation for that class is
        # maintained here.
        # --------------------------------------------------------------

        # ----------------------------------------
        # Lock down parameters for this parse.

        require_colon = self.require_colon
        if sec_colon_required is not None:
            require_colon = self.sec_colon_required
        elif sec_colon_cautious:
            require_colon = SecFinder.SEC_COLON_CAUTIOUS

        if not default_ns:
            default_ns = self.default_ns

        if not default_ew:
            default_ew = self.default_ew

        if ocr_scrub is None:
            ocr_scrub = self.ocr_scrub

        # NOTE: If layout was specified at init or when calling
        # `.parse(layout=<string>)`, PLSSParser.parse_chunk() will be
        # prevented from deducing it.  Leave as None to allow the parser
        # to deduce.

        if parse_qq is None:
            parse_qq = self.parse_qq

        if clean_qq is None:
            clean_qq = self.clean_qq

        # Config object for passing down to Tract objects.
        handed_down_config = self.config.decompile_to_text()

        if segment is None:
            segment = self.segment

        if layout == COPY_ALL:
            # Segmenting the whole description would defy the point of
            # the COPY_ALL layout, so prevent it.
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
            # require_colon is the culmination of sec_colon_required and
            # sec_colon_cautious. The PLSSParser takes one of three
            # values (True, False, or SecFinder.SEC_COLON_CAUTIOUS).
            "require_colon": require_colon,

            "segment": segment,
            "qq_depth_min": qq_depth_min,
            "qq_depth_max": qq_depth_max,
            "qq_depth": qq_depth,
            "break_halves": break_halves,
            "handed_down_config": handed_down_config,
        }

        parser = PLSSParser(
            text=self.orig_desc,
            layout=layout,
            source=self.source,
            **config_params
        )
        tracts = parser.tracts  # a TractList object
        if commit:
            # Wipe the existing tracts, etc., if any.
            self.w_flags = []
            self.e_flags = []
            self.w_flag_lines = []
            self.e_flag_lines = []

            # Unpack each of the 'unpackable' attributes.
            for attribute in parser.UNPACKABLES:
                setattr(self, attribute, getattr(parser, attribute))
            self.tracts = tracts
            # The resulting `.text` in the parser is the preprocessed
            # description.
            self.pp_desc = parser.text

        return tracts

    def config_tracts(self, config):
        """
        Reconfigure all ``Tract`` objects in ``.tracts`` attribute
        (without reconfiguring this ``PLSSDesc`` object).

        *Note:* Will *not* trigger the ``Tract`` objects to be
        (re)parsed, even if ``'parse_qq'`` is included in the new
        config.

        :param config: Either a ``Config`` object, or a string of
         parameters to configure how the ``Tract`` objects should be
         parsed.  (See documentation on ``Config`` objects for optional
         config parameters.)

        :return: None
        """
        return self.tracts.config_tracts(config)

    def parse_tracts(
            self,
            config=None,
            clean_qq=None,
            suppress_lot_divs=None,
            qq_depth_min=None,
            qq_depth_max=None,
            qq_depth=None,
            break_halves=None):
        """
        Parse (or re-parse) all ``Tract`` objects in ``.tracts``
        attribute into lots/QQ's using the specified parameters.
        Will NOT pull from this ``PLSSDesc`` object's ``.config`` or
        other attributes, but WILL pull from each ``Tract`` object's own
        ``.config`` (unless otherwise configured here).

        Optionally reconfigure each ``Tract`` object prior to parsing
        into lots/QQs by using the ``config=`` parameter here, or other
        parameters.  (The keyword parameters here will take priority
        over ``config``, if there is a conflict.)

        The parsed data will be committed to the ``Tract`` objects'
        attributes, overwriting data from a prior parse.

        :param config: (Optional) New config parameters to apply to each
         ``Tract`` before parsing.
        :param clean_qq: Same as in ``Tract.parse()`` method.
        :param suppress_lot_divs: Same as in ``Tract.parse()`` method.
        :param qq_depth_min: Same as in ``Tract.parse()`` method.
        :param qq_depth_max: Same as in ``Tract.parse()`` method.
        :param qq_depth: Same as in ``Tract.parse()`` method.
        :param break_halves: Same as in ``Tract.parse()`` method.
        :return: None
        """
        return self.tracts.parse_tracts(
                config=config,
                clean_qq=clean_qq,
                suppress_lot_divs=suppress_lot_divs,
                qq_depth_min=qq_depth_min,
                qq_depth_max=qq_depth_max,
                qq_depth=qq_depth,
                break_halves=break_halves)

    def deduce_layout(self, candidates=None):
        """
        Deduce the layout of the description.

        :param candidates: A list of which layouts are to be considered.
         If passed as ``None`` (the default), it will consider all
         currently implemented meaningful layouts (i.e. ``'TRS_desc'``,
         ``'desc_STR'``, ``'S_desc_TR'``, and ``'TR_desc_S'``), but will
         also consider ``'copy_all'`` if an apparently flawed
         description is found. If specifying fewer than all candidates,
         ensure that at least one layout from
         ``pytrs.IMPLEMENTED_LAYOUTS`` is in the list. (Strings not in
         ``pytrs.IMPLEMENTED_LAYOUTS`` will have no effect.)
        :return: Returns the algorithm's best guess at the layout (a
         string).
        """
        preprocessor = PLSSPreprocessor(self.orig_desc, ocr_scrub=self.ocr_scrub)
        return deduce_layout(preprocessor.text, candidates=candidates)

    def preprocess(
            self,
            default_ns=None,
            default_ew=None,
            commit=False,
            ocr_scrub=None) -> str:
        """
        Preprocess the PLSS description to iron out common kinks in
        the input data, and optionally store the results to the
        ``.pp_desc`` attribute (*not* committed by default).

        *Note:* Regardless whether committed, the description will be
        preprocessed (again) when parsed.

        :param default_ns: How to interpret townships for which
         direction was not specified -- i.e. either ``'n'`` or ``'s'``.
         (Defaults to ``.default_ns`` attribute (if configured) or to
         ``MasterConfig.default_ns`` which is ``'n'`` unless otherwise
         configured.)
        :param default_ew: How to interpret ranges for which direction
         was not specified -- i.e. either ``'e'`` or ``'w'``. (Defaults
         to ``.default_ew`` attribute (if configured) or to
         ``MasterConfig.default_ew`` which is ``'w'`` unless otherwise
         configured.)
        :param ocr_scrub: Whether to try to iron out common OCR
         'artifacts'. May cause unintended changes. (Defaults to
         ``.ocr_scrub`` attribute, which is ``False`` unless otherwise
         configured.)
        :param commit: Whether to store the results to ``.pp_desc``.
         (Defaults to ``False``)
        :return: The preprocessed string.
        """
        text = self.orig_desc
        if default_ns is None:
            default_ns = self.default_ns
        if default_ew is None:
            default_ew = self.default_ew
        if ocr_scrub is None:
            ocr_scrub = self.ocr_scrub
        preprocessor = PLSSPreprocessor(text, default_ns, default_ew, ocr_scrub)
        pp_desc = preprocessor.text
        if commit:
            self.pp_desc = pp_desc
        return pp_desc

    def tracts_to_dict(self, *attributes) -> list:
        """
        Compile the data for each ``Tract`` object in ``.tracts`` into a
        dict containing the requested attributes only, and return a list
        of those dicts (the returned list being equal in length to
        ``.tracts``).

        Example:

        .. code-block:: python

            txt = '''154N-97W
            Sec 14: NE/4
            Sec 15: Northwest Quarter, North Half South West Quarter'''
            d_obj = PLSSDesc(txt, parse_qq=True)
            tract_data = d_obj.tracts_to_dict('trs', 'desc', 'qqs')


        Example returns a list of two dicts::

            [
            {'trs': '154n97w14',
            'desc': 'NE/4',
            'qqs': ['NENE', 'NWNE', 'SENE', 'SWNE']},

            {'trs': '154n97w15',
            'desc': 'Northwest Quarter, North Half South West Quarter',
            'qqs': ['NENW', 'NWNW', 'SENW', 'SWNW', 'NESW', 'NWSW']}
            ]

        :param attributes: The names (strings) of whichever attributes
         should be included (see documentation on ``Tract`` objects
         for the names of relevant attributes).

        :return: List of dicts, containing the requested data for each
         ``Tract``.
        """
        # This functionality is handled by TractList method.
        return self.tracts.tracts_to_dict(attributes)

    def tracts_to_list(self, *attributes) -> list:
        """
        Compile the data for each ``Tract`` object in the ``.tracts``
        attribute into a list containing the requested attributes only,
        and return a nested list of those lists (the returned list being
        equal in length to ``.tracts``).

        Example:

        .. code-block:: python

            txt = '''154N-97W
            Sec 14: NE/4
            Sec 15: Northwest Quarter, North Half South West Quarter'''
            d_obj = pytrs.PLSSDesc(txt, parse_qq=True)
            d_obj.tracts_to_list('trs', 'desc', 'qqs')

        Example returns a nested list::

            [
                ['154n97w14',
                'NE/4',
                ['NENE', 'NWNE', 'SENE', 'SWNE']],

                ['154n97w15',
                'Northwest Quarter, North Half South West Quarter',
                ['NENW', 'NWNW', 'SENW', 'SWNW', 'NESW', 'NWSW']]
            ]

        :param attributes: The names (strings) of whichever attributes
         should be included (see documentation on ``Tract`` objects
         for the names of relevant attributes).

        :return: List of lists, containing the requested data for each
         ``Tract``.
        """
        # This functionality is handled by TractList method.
        return self.tracts.tracts_to_list(attributes)

    def iter_to_dict(self, *attributes):
        """
        Identical to ``.tracts_to_dict()``, but returns a generator of
        dicts, rather than a list of dicts.

        :param attributes: The names (strings) of whichever attributes
         should be included (see documentation on ``Tract`` objects
         for the names of relevant attributes).

        :return: A generator of data pulled from each ``Tract``, in the
         form of a dict.
        """
        return self.tracts.iter_to_dict(attributes)

    def iter_to_list(self, *attributes):
        """
        Identical to ``.tracts_to_list()``, but returns a generator of
        lists, rather than a list of lists.

        :param attributes: The names (strings) of whichever attributes
         should be included (see documentation on ``Tract`` objects for
         the names of relevant attributes).

        :return: A generator of data pulled from each ``Tract``, in the
         form of a list.
        """
        return self.tracts.iter_to_list(attributes)

    def tracts_to_str(self, *attributes) -> str:
        """
        Compile the data for all ``Tract`` objects in ``.tracts`` into
        an orderly string, containing the requested attributes only, and
        return a single string of the data.

        Example:

        .. code-block:: python

            txt = '''154N-97W
            Sec 14: NE/4
            Sec 15: Northwest Quarter, North Half South West Quarter'''
            d_obj = pytrs.PLSSDesc(txt, parse_qq=True)
            d_obj.tracts_to_str('trs', 'desc', 'qqs')

        Example returns a multi-line string that looks like this when
        printed::

            Tract 1 / 2
            trs  : 154n97w14
            desc : NE/4
            qqs  : NENE, NWNE, SENE, SWNE

            Tract 2 / 2
            trs  : 154n97w15
            desc : Northwest Quarter, North Half South West Quarter
            qqs  : NENW, NWNW, SENW, SWNW, NESW, NWSW

        :param attributes: The names (strings) of whichever attributes
         should be included (see documentation on ``Tract`` objects
         for the names of relevant attributes).

        :return: An orderly string containing the requested data for
         each ``Tract``.
        """
        # This functionality is handled by TractList method.
        return self.tracts.tracts_to_str(attributes)

    def tracts_to_csv(
            self, attributes, fp, mode, nice_headers=False):
        """
        Write all ``Tract`` data to a .csv file (one row per ``Tract``).

        (Note: See ``pytrs.tractwriter.TractWriter`` class for more
        robust writing to .csv files.)

        :param attributes: a list of names (strings) of whichever
         attributes should be included (see documentation on
         ``Tract`` objects for the names of relevant attributes).

        :param fp: The filepath of the .csv file to write to.

        :param mode: The ``mode`` in which to open the file we're
         writing to. Either ``'w'`` (new file) or ``'a'`` (continue a
         file).

        :param nice_headers: By default, this method will use the
         attribute names as headers. To use custom headers, pass to
         ``nice_headers=`` any of the following:

         - a list of strings to use. (Should be equal in length to the
           list passed as ``attributes``, but will not raise an error
           if that's not the case. The resulting column headers will
           just be fewer than the actual number of columns.)

         - a dict, keyed by attribute name, and whose values are the
           corresponding headers. (Any missing keys will use the
           attribute name.)

         - ``True`` -- use the values in the ``Tract.ATTRIBUTES`` dict
           for headers. (WARNING: Any value passed that is not a list or
           dict and that evaluates to ``True`` will cause this
           behavior.)

         - If not specified (i.e. ``None`` or ``False``), will just use
           the attribute names themselves (default).

        :return: None
        """
        self.tracts.tracts_to_csv(
            attributes, fp, mode, nice_headers)

    def quick_desc(self, delim=': ', newline='\n') -> str:
        # Note r-string, to escape '\n' character.
        r"""
        Returns the full description of all ``Tract`` objects in the
        ``.tracts`` attribute as a single, orderly string.

        Example:

        .. code-block:: python

            txt = '''154N-97W
            Sec 14: NE/4
            Sec 15: Northwest Quarter, North Half South West Quarter'''
            d_obj = pytrs.PLSSDesc(txt)
            d_obj.quick_desc()

        Example returns a multi-line string that looks like this when
        printed::

            154n97w14: NE/4
            154n97w15: Northwest Quarter, North Half South West Quarter


        :param delim: Specify what separates Twp/Rge/Sec from the
         corresponding description block (i.e. what comes between
         ``.trs`` and ``.desc``).  (Defaults to ``': '``).

        :param newline: Specify what separates each ``Tract`` from one
         another.  (Defaults to ``'\n'``).

        :return: A string of the complete description.
        """
        # This functionality is handled by TractList method.
        return self.tracts.quick_desc(delim=delim, newline=newline)

    def quick_desc_short(self, delim=': ', newline='\n', max_len=30) -> str:
        # Note r-string, to escape '\n' character.
        r"""
        Get the full description of all ``Tract`` objects in the
        ``.tracts`` attribute as a single, orderly string -- but caps
        every line at a length of ``max_len``.

        :param delim: Specify what separates Twp/Rge/Sec from the
         corresponding description block (i.e. what comes between
         ``.trs`` and ``.desc``).  (Defaults to ``': '``).

        :param newline: Specify what separates each ``Tract`` from one
         another.  (Defaults to ``'\n'``).

        :param max_len: Maximum length of each line.
         (Defaults to 30.)

        :return: A string of the complete description (with each line
         potentially trimmed).
        """
        return self.tracts.quick_desc_short(delim, newline, max_len)

    def list_trs(self, remove_duplicates=False):
        """
        Get a list all Twp/Rge/Sections in all ``Tract`` objects in the
        ``.tracts`` attribute.  Optionally remove duplicates from the
        returned list with ``remove_duplicates=True``. (Duplicates are
        NOT removed from the original.)

        The original order is maintained in the returned list.

        *Note:* Each Twp/Rge/Sec in the resulting list is a string, and
        NOT a ``TRS`` object. If ``TRS`` objects are required, cast
        the resulting list as a ``TRSList`` -- i.e.
        ``TRSList(some_plssdesc.list_trs())``.

        :param remove_duplicates: Whether to remove duplicate
         Twp/Rge/Sec from the resulting list. (They are not removed in
         the original.)  Defaults to ``False``.

        :returns: A standard list, containing string representations of
         the Twp/Rge/Sections.
        """
        # This functionality is handled by TractList method.
        return self.tracts.list_trs(remove_duplicates=remove_duplicates)

    def print_desc(self, delim=': ', newline='\n') -> None:
        # Note r-string, to escape '\n' character.
        r"""
        Simple printing of the parsed description.

        :param delim: Specify what separates Twp/Rge/Sec from the
         corresponding description block (i.e. what comes between
         ``.trs`` and ``.desc``).  (Defaults to ``': '``).

        :param newline: Specify what separates each ``Tract`` from one
         another.  (Defaults to ``'\n'``).
        """
        # This functionality is handled by TractList method.
        self.tracts.print_desc(delim=delim, newline=newline)

    def pretty_desc(self, word_sec='Sec ', justify_linebreaks=None):
        # Note r-string, to escape '\t' character.
        r"""
        Get a neatened-up description of all ``Tract`` objects in the
        ``.tracts`` attribute. (Does not directly access the description
        of this ``PLSSDesc``. Instead, compiles a cleaned-up description
        from the ``Tract`` objects.)

        Groups Tracts by Twp/Rge, but only to the extent possible while
        maintaining the current sort order.

        :param word_sec: How the word 'Section' should appear, INCLUDING
         the following white space (if any). (Defaults to ``'Sec '``).

        :param justify_linebreaks: (Optional) A string specifying how to
         justify new lines after a linebreak -- e.g., ``'\t'`` (a tab).
         If not specified, will align new lines with the line above
         (i.e. as determined by ``word_sec``). To use no justification
         at all, pass an empty string.

         Note: Only linebreaks WITHIN a given ``Tract`` will be
         justified -- i.e. the start of each ``Tract`` will be
         left-aligned.

        :return: a str of the compiled description.
        """
        return self.tracts.pretty_desc(word_sec, justify_linebreaks)

    def pretty_print_desc(self, word_sec='Sec ', justify_linebreaks=None):
        # Note r-string, to escape '\t' character.
        r"""
        Print a neatened-up description of all ``Tract`` objects in the
        ``.tracts`` attribute. (Does not directly access the description
        of this ``PLSSDesc``. Instead, compiles a cleaned-up description
        from the ``Tract`` objects.)

        Groups Tracts by Twp/Rge, but only to the extent possible while
        maintaining the current sort order.

        :param word_sec: How the word 'Section' should appear, INCLUDING
         the following white space (if any). (Defaults to ``'Sec '``).

        :param justify_linebreaks: (Optional) A string specifying how to
         justify new lines after a linebreak -- e.g., ``'\t'`` (a tab).
         If not specified, will align new lines with the line above
         (i.e. as determined by ``word_sec``). To use no justification
         at all, pass an empty string.

         Note: Only linebreaks WITHIN a given ``Tract`` will be
         justified -- i.e. the start of each ``Tract`` will be
         left-aligned.

        :return: None (prints to console).
        """
        self.tracts.pretty_print_desc(word_sec, justify_linebreaks)

    def print_data(self, *attributes) -> None:
        """
        Simple printing of the arg-specified attributes for each
        ``Tract`` in the ``.tracts`` attribute.
        """
        # This functionality is handled by TractList method.
        self.tracts.print_data(attributes)
        return

    def sort_tracts(self, key: str = 'i,s,r,t', reverse=False):
        """
        Sort the ``Tract`` objects stored in the ``.tracts`` attribute.

        The standard ``list.sort(key=<lambda>, reverse=<bool>)`` keyword
        arguments can be used here, but this method has additional
        customized key options.  (Note that the keyword argument
        ``reverse=<bool>`` applies only to lambda sorts, and NOT to the
        custom keys detailed below.)

        Customized key options:

        - ``'i'`` -- Sort tracts by the order in which they were
          created.
            - *Note:* ``'i'`` sorting has no effect on a ``TRSList``.

        - ``'t'`` -- Sort by Township, such as:
            - ``'t.num'`` -- Sort by raw number, ignoring N/S. (†)
            - ``'t.ns'`` -- Sort from north-to-south
            - ``'t.sn'`` -- Sort from south-to-north

        - ``'r'`` -- Sort by Range, such as:
            - ``'r.num'`` -- Sort by raw number, ignoring E/W. (†)
            - ``'r.ew'`` -- Sort from east-to-west (‡)
            - ``'r.we'`` -- Sort from west-to-east (‡)

        - ``'s'`` -- Sort by Section number.

        *(†) Denotes default behavior of sub-key.*

        *(‡) Note: These do not account for Principal Meridians.*

        Reverse any of the keys by adding ``'.reverse'`` (or ``'.rev'``)
        at the end of each desired key(s) to be reversed.

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

        Example keys::

            's.reverse,r.ew,t.ns'
                ->  Sort by section number (reversed, so largest-to-
                        smallest);
                ->  then sort by Range (east-to-west);
                ->  then sort by Township (north-to-south)

            'i,s,r,t'  (this is the default)
                ->  Sort by original creation order;
                ->  then sort by Section (smallest-to-largest);
                ->  then sort by Range (smallest-to-largest);
                ->  then sort by Township (smallest-to-largest)

            'i'
                -> Return to the original order as parsed in this
                    PLSSDesc object.

        Example::

            some_plssdesc.sort_tracts(key='s.reverse,r.ew,t.ns')

        (See also ``TractList.custom_sort()`` and
        ``TRSList.custom_sort()`` for a fuller write-up on sorting.

        :param key: A string specifying which sort(s) should be done.

        :return: None
        """
        # This functionality is handled by TractList method.
        self.tracts.sort_tracts(key=key, reverse=reverse)
        return None

    def group_by_nested(
            self, attribute='twprge', into=None, sort_key=None,
            sort_reverse=False):
        """
        Group the ``Tract`` objects in the ``.tracts`` attribute into a
        dict of ``TractList`` objects, keyed by unique values of the
        ``attribute`` (being any ``Tract`` attribute(s) whose value is
        hashable). By default, will filter into groups of Tracts that
        share Twp/Rge (i.e. ``attribute='twprge'``).

        Pass ``attribute`` as a *list* of attributes to group by
        multiple attributes, in which case the returned dict will be a
        NESTED dict of dicts (one level per attribute), the deepest
        level of which will be the ``TractList`` objects.

        *Note:* This method is similar to ``.group_by()``, except for
        how it handles grouping by multiple attributes.  Specifically,
        this method returns a nested dict when grouping by multiple
        attributes - whereas ``.group_by()`` will return a single-level
        dict whose keys will be tuples of each group's matching
        attributes.

        :param attribute: The str name of an attribute of ``Tract``
         objects. (Defaults to ``'twprge'``). NOTE: Must be a hashable
         type!  (Optionally pass as a list of multiple attribute names
         to do multiple groupings.)

        :param into: (Optional) An existing dict into which to group
         the ``Tract`` objects. If not specified, will create a new
         dict. Use this arg if you need to continue adding to an
         existing grouped dict.

        :param sort_key: (Optional) How to sort each grouped
         ``TractList`` in the returned dict. Use a string that works
         with the ``.sort_tracts(key=<str>)`` method (e.g.,
         ``'i, s, r.ew, t.ns'``) or a lambda function, as you would with
         the builtin ``list.sort(key=<lambda>)`` method. (Defaults to
         ``None``, i.e. not sorted.)

         May optionally pass ``sort_key`` as a list of sort keys, to be
         applied left-to-right. Here, you may mix and match lambdas and
         ``.sort_tracts()`` strings.  (See documentation on
         ``TractList.custom_sort()``.)

        :param sort_reverse: (Optional) Whether to reverse the sort.

         *Note:* Only has an effect if the ``sort_key`` is passed as a
         lambda -- NOT as a custom string sort key. Defaults to
         ``False``.

         *Note also:* If ``sort_key`` was passed as a list, then
         ``sort_reverse`` must be passed as EITHER a single bool that
         will apply to all (non-string) sorts, OR as a list or tuple of
         bools that is equal in length to ``sort_key`` (i.e. the values
         in ``sort_key`` and ``sort_reverse`` will be matched up
         one-to-one).

         (Again, see documentation on ``TractList.custom_sort()``.)

        :return: A dict of ``TractList`` objects, each containing those
         ``Tract`` object with matching values of the ``attribute``.
         If multiple attributes were included in ``attribute``, this
         will return a nested dict of dicts (one level per attribute),
         the deepest elements of which will be the ``TractList``
         objects.
        """
        return self.tracts.group_by_nested(
            attribute, into, sort_key, sort_reverse)

    def group_by(
            self, attribute="twprge", into=None, sort_key=None,
            sort_reverse=False):
        """
        Group the ``Tract`` objects in the ``.tracts`` attribute into a
        dict of ``TractList`` objects, keyed by unique values of the
        ``attribute`` (being any ``Tract`` attribute(s) whose value is
        hashable). By default, will filter into groups of Tracts that
        share Twp/Rge (i.e. ``attribute='twprge'``).

        Pass ``attribute`` as a *list* of attributes to group by
        multiple attributes, in which case the keys of the returned dict
        will be tuples of each group's matching attributes.

        *Note:* This method is similar to ``.group_by_nested()``, except
        for how it handles grouping by multiple attributes.
        Specifically, this method returns a single-level dict
        whose keys will be tuples of each group's attributes when
        grouping by multiple attributes - whereas ``.group_by_nested()``
        returns a nested dict (one level per grouping attribute).

        :param attribute: The str name of an attribute of ``Tract``
         objects. (Defaults to ``'twprge'``). *Note:* Must be a hashable
         type!  (Optionally pass as a list of multiple attribute names
         to do multiple groupings.)

        :param into: (Optional) An existing dict into which to group
         the ``Tract`` objects. If not specified, will create a new
         dict. Use this arg if you need to continue adding to an
         existing grouped dict.

        :param sort_key: (Optional) How to sort each grouped
         ``TractList`` in the returned dict. Use a string that works
         with the ``.sort_tracts(key=<str>)`` method (e.g.,
         ``'i, s, r.ew, t.ns'``) or a lambda function, as you would with
         the builtin ``list.sort(key=<lambda>)`` method. (Defaults to
         ``None``, i.e. not sorted.)

        May optionally pass ``sort_key`` as a list of sort keys, to be
        applied left-to-right. Here, you may mix and match lambdas and
        ``.sort_tracts()`` strings.  (See documentation on
        ``TractList.custom_sort()``.)

        :param sort_reverse: (Optional) Whether to reverse the sort.
         NOTE: Only has an effect if the ``sort_key`` is passed as a
         lambda -- NOT as a custom string sort key. Defaults to
         ``False``.

         NOTE: If ``sort_key`` was passed as a list, then
         ``sort_reverse`` must be passed as EITHER a single bool that
         will apply to all (non-string) sorts, OR as a list or tuple of
         bools that is equal in length to ``sort_key`` (i.e. the values
         in ``sort_key`` and ``sort_reverse`` will be matched up
         one-to-one).

         (Again, see documentation on ``TractList.custom_sort()``.)

        :return: A dict of ``TractList`` objects, each containing those
         ``Tract`` object with matching values of the ``attribute``. If
         ``attribute`` was passed as a list of attribute names, then the
         keys in the returned dict will be a tuple whose values line up
         with the list passed as ``attribute``.)
        """
        return self.tracts.group_by(attribute, into, sort_key, sort_reverse)

    # Alias to mirror `sort_tracts`.
    group_tracts_by = group_by

    def filter(self, key, drop=False):
        """
        Extract from ``.tracts`` all ``Tract`` objects that match the
        ``key`` (a lambda or other function that returns a bool or
        bool-like value when applied to each ``Tract`` object).

        Returns a new ``TractList`` of the selected ``Tract`` objects.

        :param key: a lambda or other function that returns a bool or
         bool-like value when applied to a ``Tract`` object in the
         ``.tracts`` attribute.  (Note: ``True`` or ``True``-like
         returned values will result in the inclusion of that ``Tract``).

        :param drop: Whether to drop the matching Tracts from the
         original ``.tracts``. (Defaults to ``False``)

        :return: A new ``TractList`` of the selected ``Tract`` objects.
         (The original ``.tracts`` will still hold all other ``Tract``
         objects, unless ``drop=True`` was passed.)
        """
        return self.tracts.filter(key, drop)

    # Alias to mirror `sort_tracts`.
    filter_tracts = filter

    def filter_errors(self, twp=True, rge=True, sec=True, undef=False, drop=False):
        """
        Extract from ``.tracts`` all ``Tract`` objects that were
        parsed with an error. Specifically extract Twp/Rge errors with
        ``twp=True`` and ``rge=True``; and get Section errors with
        ``sec=True`` (all of which are on by default).

        Returns a new ``TractList`` of the selected ``Tract`` objects.

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

        :param drop: Whether to drop the selected ``Tract`` objects from
         the original ``.tracts`` attribute. (Defaults to ``False``)

        :return: A new ``TractList`` containing the selected ``Tract``
         objects.
        """
        return self.tracts.filter_errors(twp, rge, sec, undef, drop)

    # Alias to mirror `sort_tracts`
    filter_error_tracts = filter_errors

    def filter_duplicates(self, method='instance', drop=False):
        """
        Find the duplicate ``Tract`` objects in ``.tracts``, get a new
        ``TractList`` of those duplicates, and optionally ``drop``
        them from the original ``.tracts`` attribute.

        To be clear, if there are three identical ``Tract`` objects in
        the ``.tracts``, the returned ``TractList`` will contain only
        two of them, and the original ``.tracts`` will still have one,
        being the first one.

        Control how to assess whether elements in the list are
        duplicates by passing one of the following values to ``method``:

        - ``method='instance'`` *(the default)*
            - Whether two objects are actually the same instance -- i.e.
              literally the same object. By definition, this will also
              apply even if one of the other two methods is used. (This
              should never happen in a ``PLSSDesc`` object, unless a
              ``Tract`` was manually appended to its ``.tracts``
              attribute.)

        - ``method='lots_qqs'``
            - Whether the ``.trs`` matches *and* ``.lots_qqs`` attribute
              contains the same lots/aliquots (after removing
              duplicates).  *Note:* Lots and aliquots must have been
              parsed for a given ``Tract`` object, or it will not match
              as a duplicate with this parameter.
                - Ex: Will match these as duplicate tracts, assuming
                  they were parsed with identical ``config`` settings::

                      154n97w14: Lots 1 - 3, S/2NE/4
                      154n97w14: Lot 3, S/2NE/4, Lots 1, 2

        - ``method='desc'``
            - Whether the ``.trs`` and ``.pp_desc`` (i.e. preprocessed
              description) combine to form an identical tract.
                - Ex: Will match these as duplicate tracts::

                        154n97w14: NE/4
                        154n97w14: Northeast Quarter

        :param method: Specify how to assess whether ``Tract`` objects
         are duplicates (either ``'instance'``, ``'lots_qqs'``, or
         ``'desc'``). See above for example behavior of each.

        :param drop: Whether to remove the identified duplicates from
         the original list.

        :return: A new ``TractList``.
        """
        return self.tracts.filter_duplicates(method, drop)

    # Alias to mirror `sort_tracts`
    filter_duplicate_tracts = filter_duplicates


__all__ = [
    'PLSSDesc',
]
