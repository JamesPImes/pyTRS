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
    twprge_regex, twprge_broad_regex, sec_regex, multiSec_regex,
    comma_multiSec_regex, noNum_sec_regex, preproTR_noNSWE_regex,
    preproTR_noR_noNS_regex, preproTR_noT_noWE_regex, twprge_ocrScrub_regex,
    lots_context_regex, TRS_unpacker_regex, well_regex, depth_regex,
    including_regex, less_except_regex, isfa_except_regex, NE_regex, SE_regex,
    NW_regex, SW_regex, N2_regex, S2_regex, E2_regex, W2_regex, ALL_regex,
    ALL_context_regex, cleanNE_regex, cleanSE_regex, cleanNW_regex,
    cleanSW_regex, halfPlusQ_regex, through_regex, lot_regex,
    lot_with_aliquot_regex, lotAcres_unpacker_regex, aliquot_unpacker_regex,
    aliquot_intervener_remover_regex, aliquot_lot_intervener_scrubber_regex,
    pm_regex, twprge_pm_regex, sec_within_desc_regex
)


# A current list of implemented layouts:
__implementedLayouts__ = [
    'TRS_desc', 'desc_STR', 'S_desc_TR', 'TR_desc_S', 'copy_all'
]

__implementedLayoutExamples__ = (
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
    -- Use init parameter `initParse=True` (parses the PLSSDesc object
        into Tract objects, which are NOT yet parsed into lots and
        QQ's).
    -- Use init parameter `initParseQQ=True` (parses the PLSSDesc object
        into Tract objects, which ARE then immediately parsed into lots
        and QQ's)
    -- Include string 'initParse' and/or 'initParseQQ' among the config
        parameters that are passed in `config=` at init.
    (NOTE: initParseQQ entails initParse, but not vice-versa.)

    ____ IMPORTANT INSTANCE VARIABLES AFTER PARSING ____
    .origDesc -- The original text. (Gets set from the first positional
        argument at init.)
    .parsedTracts -- A pyTRS.TractList object (i.e. a list) containing
        all of the pyTRS.Tract objects that were generated from parsing
        this object.
    .ppDesc -- The preprocessed description. (If the object has not yet
        been preprocessed, it will be equivalent to .origDesc)
    .source -- (Optional) A string specifying where the description came
        from. Useful if parsing multiple descriptions and need to
        internally keep track where they came from. (Optionally specify
        at init with parameter `source=<str>`.)
    .wFlagList -- a list of warning flags (strings) generated during
        preprocessing and/or parsing.
    .wFlagLines -- a list of 2-tuples, each being a warning flag and the
        line or context from the description that caused the warning.
    .eFlagList -- a list of error flags (strings) generated during
        preprocessing and/or parsing.
    .eFlagLines -- a list of 2-tuples, each being an error flag and the
        line or context from the description that caused the error.
    .descIsFlawed -- a bool, whether or not an apparently fatal flaw was
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
        equal in length to `.parsedTracts` TractList).
    .tracts_to_list() -- Compile the requested attributes for each Tract
        into a list, and returns a nested list of those list (i.e. the
        top-level list is equal in length to `.parsedTracts` TractList).
    .tracts_to_str() -- Compile the requested attributes for each Tract
        into a string-based table, and return a single string of all
        tables.
    .list_trs() -- Return a list of all twp/rge/sec combinations in the
        `.parsedTracts` TractList, optionally removing duplicates.
    .print_data() -- Equivalent to `.tracts_to_dict()`, but the data
        is formatted as a table and printed to console.

    ____ OTHER NOTABLE METHODS ____
    These methods are used before or during the parse, and are typically
    called automatically:
    .deduce_layout() -- Deduces the layout of the description, if it was
        not dictated at init, or otherwise.
    .deduce_segment_layout() -- (Static method)  Deduces the layout of a
        segment of the description.
    .preprocess() -- Attempt to scrub the original description of common
        flaws, typos, etc. into a format more consistently understood by
        the parser.
    .static_preprocess() -- (Static method)  Same as .preprocess(), but
        processes text without saving any data.
    .gen_flags() -- Scour the text for potential flag-raising issues.
    """

    def __init__(
            self, origDesc: str, source='', layout=None, config=None,
            initParse=None, initParseQQ=None):
        """
        A 'raw' PLSS description of land. Will be parsed into one or
        more Tract objects, which are stored in the `.parsedTracts`
        instance variable (a list).

        :param origDesc: The text of the description to be parsed.
        :param source: (Optional) A string specifying where the
        description came from. (Useful if parsing multiple descriptions
        and need to internally keep track where they came from.)
        :param layout: The pyTRS layout. If not specified, will be
        deduced when initialized, and/or when parsed. See available
        options in `pyTRS.__implementedLayouts__` and examples in
        `pyTRS.__implementedLayoutExamples__`.
        :param config: Either a pyTRS.Config object, or a string of
        parameters to configure how the PLSSDesc object should be
        parsed. (See documentation on pyTRS.Config objects for optional
        config parameters.)
        :param initParse: Whether to parse this PLSSDesc object when
        initialized.
        NOTE: If `initParse` is specified as a kwarg at init, and also
        specified in the `config` (i.e. config='initParse'), then the
        kwarg `initParse=<bool>` will control.
        :param initParseQQ: Whether to parse this PLSSDesc object and
        each resulting Tract object (into lots and QQs) when
        initialized.
        NOTE: If `initParseQQ` is specified as a kwarg at init, and also
        specified in the `config` (i.e. config='initParseQQ'), then the
        kwarg `initParseQQ=<bool>` will control.
        """

        # The original input of the PLSS description:
        self.origDesc = origDesc

        # If something other than a string is fed in, raise a TypeError
        if not isinstance(origDesc, str):
            raise TypeError(
                f"`origDesc` must be of type 'string'. "
                f"Passed as type {type(origDesc)}.")

        # The source of this PLSS description:
        self.source = source

        # The layout of this PLSS description -- Initially None, but will be
        # set to one of the values in the __implementedLayouts__ list before
        # __init__() returns -- either by kwarg `layout=`, or by
        # `set_config()`:
        self.layout = None

        # Whether the layout was specified at initialization.
        self.layout_specified = False

        # If a T&R is identified without 'North/South' specified, or without
        # 'East/West' specified, fall back on defaultNS and defaultEW,
        # respectively. Each will be filled in with set_config (if applicable),
        # or defaulted to 'n' and 'w' soon.
        self.defaultNS = None
        self.defaultEW = None

        ###############################################################
        # NOTE: the following default bools will be changed in
        # set_config(), as applicable.
        ###############################################################

        # Whether we should preprocess the text at initialization:
        self.initPreprocess = True

        # Whether we should parse the text at initialization:
        self.initParse = False

        # Whether we should parse lots and aliquots in each Tract when created.
        # NOTE: In effect, `initParseQQ==True` also entails
        # `self.initParse==True` -- but NOT vice-versa
        self.initParseQQ = False

        # Whether tract descriptions are expected to have `cleanQQ` (i.e.
        # nothing but clean aliquots and lots, with no typos, exceptions,
        # metes-and-bounds, or other hindrances to the parser.)
        self.cleanQQ = False

        # Whether we should require a colon between Section ## and tract
        # description (for TRS_desc and S_desc_TR layouts):
        self.requireColon = True

        # Whether to include any divisions of lots
        # (i.e. 'N/2 of Lot 1' -> 'N2 of L1')
        self.includeLotDivs = True

        # Whether to iron out common OCR artifacts.
        # NOTE: Currently only has effect of cleaning up T&R's during
        # `.preprocess()`.  May have more effect in a later version.
        self.ocrScrub = False

        # Whether to segment the text during parsing (can /potentially/
        # capture descriptions with multiple layouts):
        self.segment = False

        # Apply settings from `config=`.
        self.set_config(config)

        # If `defaultNS` has not yet been specified, default to 'n'
        if self.defaultNS is None:
            self.defaultNS = 'n'

        # If `defaultEW` has not yet been specified, default to 'w'
        if self.defaultEW is None:
            self.defaultEW = 'w'

        # Track fatal flaws in the parsing of this PLSS description
        self.descIsFlawed = False
        # list of Tract objs, after parsing (TractList is a subclass of `list`)
        self.parsedTracts = TractList()
        # list of warning flags
        self.wFlagList = []
        # list of 2-tuples that caused warning flags (warning flag, text string)
        self.wFlagLines = []
        # list of error flags
        self.eFlagList = []
        # list of 2-tuples that caused error flags (error flag, text string)
        self.eFlagLines = []
        # Track whether the preprocess has been completed
        self.preproComplete = False

        # If initParseQQ specified as init parameter, it will override
        # `config` parameter.
        #    ex:   config='n,w,initParseQQ', initParseQQ=False   ...
        #       -> Will NOT parse lots/QQs at init.
        if isinstance(initParseQQ, bool):
            self.initParseQQ = initParseQQ

        # If kwarg-specified initParse, that will override config input
        #   (similar to initParseQQ)
        if isinstance(initParse, bool):
            self.initParse = initParse

        ocrScrubNow = False
        if self.ocrScrub:
            ocrScrubNow = True

        # Optionally can preprocess the desc when the object is initiated
        # (on by default).
        if self.initPreprocess or ocrScrubNow:
            self.preprocess(commit=True, ocrScrub=ocrScrubNow)
        else:
            # Preprocessed descrip set to .origDesc if preprocess is declined
            self.ppDesc = self.origDesc

        # If layout was specified as kwarg, use that:
        if layout is not None:
            self.layout = layout
            self.layout_specified = True

        # If layout has not yet been /validly/ set by the user or
        # set_config(), deduce it:
        if self.layout not in __implementedLayouts__:
            self.layout = self.deduce_layout(commit=True)
            self.layout_specified = False

        # Compile and store the final Config file (for passing down to
        # Tract objects)
        self.config = Config.from_parent(self)

        # Optionally can run the parse when the object is initiated
        # (off by default).
        if self.initParse or self.initParseQQ:
            self.parse(commit=True)

    def set_config(self, config):
        """
        Apply the relevant settings from a Config object to this object;
        takes either a string (i.e. config text) or a Config object.

        :param config: Either a pyTRS.Config object, or equivalent
        config parameters. (See pyTRS.Config documentation for optional
        parameters.)
        """
        if isinstance(config, str) or config is None:
            configObj = Config(config)
        elif isinstance(config, Config):
            configObj = config
        else:
            raise TypeError(
                '`config` must be either a string or pyTRS.Config object. '
                f"Passed as type {type(config)}`.")

        for attrib in Config.__PLSSDescAttribs__:
            value = getattr(configObj, attrib)
            if value is not None:
                setattr(self, attrib, value)
                if attrib == 'layout':
                    self.layout_specified = True

    def unpack(self, targetParseBagObj):
        """
        Unpack (append or set) the relevant attributes of the
        `targetParseBagObj` into self's attributes.

        :param targetParseBagObj: A ParseBag object containing data from
        the parse.
        """

        if not isinstance(targetParseBagObj, ParseBag):
            return

        if targetParseBagObj.descIsFlawed:
            self.descIsFlawed = True

        if len(targetParseBagObj.wFlagList) > 0:
            self.wFlagList.extend(targetParseBagObj.wFlagList)

        if len(targetParseBagObj.eFlagList) > 0:
            self.eFlagList.extend(targetParseBagObj.eFlagList)

        if len(targetParseBagObj.wFlagLines) > 0:
            self.wFlagLines.extend(targetParseBagObj.wFlagLines)

        if len(targetParseBagObj.eFlagLines) > 0:
            self.eFlagLines.extend(targetParseBagObj.eFlagLines)

        if len(targetParseBagObj.parsedTracts) > 0:
            self.parsedTracts.extend(targetParseBagObj.parsedTracts)

    def parse(
            self, text=None, layout=None, cleanUp=None, initParseQQ=None,
            cleanQQ=None, requireColon='default_colon', segment=None,
            commit=True):
        """
        Parse the description. If parameter `commit=True` (defaults to
        on), the results will be stored to the various instance
        attributes (.parsedTracts, .wFlagList, .wFlagLines, .eFlagList,
        and .eFlagLines). Returns only the TractList object containing
        the parsed Tract objects (i.e. what would be stored to
        `.parsedTracts`).

        :param text: The text to be parsed. If not specified, defaults
        to the string currently stored in `self.ppDesc` (i.e. the
        pre-processed description).
        :param layout: The layout to be assumed. If not specified,
        defaults to whatever is in `self.layout`.
        :param cleanUp: Whether to clean up common 'artefacts' from
        parsing. If not specified, defaults to False for parsing the
        'copy_all' layout, and `True` for all others.
        :param initParseQQ: Whether to parse each resulting Tract object
        into lots and QQs when initialized. If not specified, defaults
        to whatever is specified in `self.initParseQQ`.
        :param cleanQQ: Whether to expect only clean lots and QQ's (i.e.
        no metes-and-bounds, exceptions, complicated descriptions,
        etc.). Defaults to whatever is specified in `self.cleanQQ`
        (which is False, unless configured otherwise).
        :param requireColon: Whether to require a colon between the
        section number and the following description (only has an effect
        on 'TRS_desc' or 'S_desc_TR' layouts).
        If not specified, it will default to a 'two-pass' method, where
        first it will require the colon; and if no matching sections are
        found, it will do a second pass where colons are not required.
        Setting as `True` or `False` here prevent the two-pass method.
            ex: 'Section 14 NE/4'
                `requireColon=True` --> no match
                `requireColon=False` --> match (but beware false
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
        :return: Returns a pyTRS.TractList object (a subclass of 'list')
        of all of the resulting pyTRS.Tract objects.
        """

        # ----------------------------------------
        # Lock down parameters for this parse.

        if commit:
            # Wipe the existing parsedTracts, if any.
            self.parsedTracts = TractList()

        if text is None:
            text = self.ppDesc
            # Unless specified otherwise, we get the flagLists and flagLines from the
            # ORIGINAL description, rather than from the preprocessed description
            flagText = self.origDesc
        else:
            flagText = text

        # When layout is specified at init, or when calling
        # `.parse(layout=<string>)`, we prevent parse_segment() from deducing,
        # AS LONG AS the specified layout is among the implemented layouts.
        layout_specified = False
        if layout in __implementedLayouts__:
            layout_specified = True
        else:
            # If not otherwise specified, pull from self attribute.
            layout = self.layout
            layout_specified = self.layout_specified
            # As a stopgap, if it's still not an acceptable layout, deduce it.
            if layout not in __implementedLayouts__:
                layout = self.deduce_layout(commit=False)

        if initParseQQ is None:
            initParseQQ = self.initParseQQ

        if cleanQQ is None:
            cleanQQ = self.cleanQQ

        # Config object for passing down to Tract objects.
        config = self.config

        if not isinstance(segment, bool):
            segment = self.segment

        if layout == 'copy_all':
            # If a *segment* (which will be divided up shortly) finds itself in
            # the 'copy_all' layout, that should still parse fine. But
            # segmenting the whole description would defy the point of
            # 'copy_all' layout. So prevent `segment` when the OVERALL layout
            # is 'copy_all'
            segment = False

        # ParseBag obj for storing the data generated throughout.
        bigPB = ParseBag(parentType='PLSSDesc')

        if len(text) == 0 or not isinstance(text, str):
            bigPB.eFlagList.append('noText')
            bigPB.eFlagLines.append(
                ('noText', '<No text was fed into the program.>'))
            return bigPB

        if not isinstance(cleanUp, bool):
            if layout in ['TRS_desc', 'desc_STR', 'S_desc_TR', 'TR_desc_S']:
                # Default `cleanUp` to True only for these layouts
                cleanUp = True
            else:
                cleanUp = False

        # ----------------------------------------
        # If doing a segment parse, break it up into segments now
        if segment:
            # Segment text into blocks, based on T&Rs that match our
            # layout requirements
            trTextBlocks, discard_trTextBlocks = segment_by_tr(
                text, layout=layout, trFirst=None)

            # Append any discard text to the wFlagList
            for textBlock in discard_trTextBlocks:
                bigPB.wFlagList.append(f"Unused_desc_<{textBlock}>")
                bigPB.wFlagLines.append(
                    (f"Unused_desc_<{textBlock}>", textBlock))

        else:
            # If not segmented parse, pack entire text into list, with
            # a leading empty str (to mirror the output of the
            # segment_by_tr() function)
            trTextBlocks = [('', text)]

        # ----------------------------------------
        # Parse each segment into a separate ParseBag obj, then absorb
        # that PB into the big PB each time:
        for textBlock in trTextBlocks:
            if layout == 'copy_all':
                midParseBag = parse_segment(
                    textBlock[1], cleanUp=cleanUp, requireColon=requireColon,
                    layout='copy_all', handedDownConfig=config,
                    initParseQQ=initParseQQ, cleanQQ=cleanQQ)
            elif segment:
                # Let the segment parser deduce layout for each textBlock.
                midParseBag = parse_segment(
                    textBlock[1], cleanUp=cleanUp, requireColon=requireColon,
                    layout=None, handedDownConfig=config,
                    initParseQQ=initParseQQ, cleanQQ=cleanQQ)
            else:
                midParseBag = parse_segment(
                    textBlock[1], cleanUp=cleanUp, requireColon=requireColon,
                    layout=layout, handedDownConfig=config,
                    initParseQQ=initParseQQ, cleanQQ=cleanQQ)

            bigPB.absorb(midParseBag)

        # If we've still not discovered any Tracts, run a final parse in
        # layout `copy_all`, and include appropriate errors.
        if len(bigPB.parsedTracts) == 0:
            bigPB.absorb(
                parse_segment(
                    text, layout='copy_all', cleanUp=False, requireColon=False,
                    handedDownConfig=config, initParseQQ=initParseQQ,
                    cleanQQ=cleanQQ))
            bigPB.descIsFlawed = True

        for TractObj in bigPB.parsedTracts:
            if TractObj.trs[:5] == 'TRerr':
                bigPB.eFlagList.append('trError')
                bigPB.eFlagLines.append(
                    ('trError', TractObj.trs + ':' + TractObj.desc))
                bigPB.descIsFlawed = True
            if TractObj.trs[-2:] == 'or':
                bigPB.eFlagList.append('secError')
                bigPB.eFlagLines.append(
                    ('secError', TractObj.trs + ':' + TractObj.desc))
                bigPB.descIsFlawed = True

        # Check for warning flags (and a couple error flags).
        # Note that .gen_flags() is being run on `flagText`, not `text`.
        flagParseBag = self.gen_flags(text=flagText, commit=False)
        bigPB.absorb(flagParseBag)

        # We want each Tract to have the entire PLSSDesc's warnings,
        # because a computer can't automatically tell which limitations,
        # etc. apply to which Tracts. (This is an ambiguity that often
        # exists in the data, even when humans read it.) So for robust
        # data, we apply flags from the whole PLSSDesc to each Tract.
        # It will only unpack the flags and flaglines, because that's
        # all that is relevant to a Tract. Also apply TractNum (i.e.
        # origIndex).
        # Also, `tempPB` takes the wFlags and eFlags from the PLSSDesc
        # object that may have been generated prior to calling .parse(),
        # and they get passed down to each TractObj too.
        tempPB = ParseBag()
        tempPB.wFlagList = self.wFlagList
        tempPB.wFlagLines = self.wFlagLines
        tempPB.eFlagList = self.eFlagList
        tempPB.eFlagLines = self.eFlagLines
        TractNum = 0
        for TractObj in bigPB.parsedTracts:

            # Unpack the flags from the PLSSDesc, held in `tempPB`.
            TractObj.unpack(tempPB)

            # Unpack the flags, etc. from `bigPB`.
            TractObj.unpack(bigPB)

            # And hand down the PLSSDesc object's `.source` and `.origDesc`
            # attributes to each of the Tract objects:
            TractObj.source = self.source
            TractObj.origDesc = self.origDesc

            # And apply the TractNum for each Tract object:
            TractObj.origIndex = TractNum
            TractNum += 1

        if commit:
            self.unpack(bigPB)

        # Return the list of identified `Tract` objects (ie. a TractList object)
        return bigPB.parsedTracts

    @staticmethod
    def deduce_segment_layout(text, candidates=None, deduceBy='TRS_order'):
        """
        INTERNAL USE:
        Deduce the layout of a *segment* of a description, without
        committing any results.

        :param text: The text, whose layout is to be deduced.
        :param candidates: A list of which layouts are to be considered.
        If passed as `None` (the default), it will consider all
        currently implmented meaningful layouts (i.e. 'TRS_desc',
        'desc_STR', 'S_desc_TR', and 'TR_desc_S'), but will also
        consider 'copy_all' if an apparently flawed description is
        found. If specifying fewer than all candidates, ensure that at
        least one layout from __implementedLayouts__ is in the list.
        (Strings not in __implementedLayouts__ will have no effect.)
        :param deduceBy: The preferred deduction algorithm. (Currently
        only uses 'TRS_order' -- i.e. basically, the apparent order of
        the Twp, Rge, Sec, and description block.)
        :return: Returns the algorithm's best guess at the layout (i.e.
        a string).
        """

        return PLSSDesc.deduce_layout(
            self=None, text=text, candidates=candidates, deduceBy=deduceBy,
            commit=False)

    def deduce_layout(
            self, text=None, candidates=None, deduceBy='TRS_order',
            commit=True):
        """
        Deduce the layout of the description.

        :param text: The text, whose layout is to be deduced.
        If not specified, will use whatever is stored in `self.ppDesc`,
        i.e. the preprocessed description.
        :param candidates: A list of which layouts are to be considered.
        If passed as `None` (the default), it will consider all
        currently implmented meaningful layouts (i.e. 'TRS_desc',
        'desc_STR', 'S_desc_TR', and 'TR_desc_S'), but will also
        consider 'copy_all' if an apparently flawed description is
        found. If specifying fewer than all candidates, ensure that at
        least one layout from __implementedLayouts__ is in the list.
        (Strings not in __implementedLayouts__ will have no effect.)
        :param deduceBy: The preferred deduction algorithm. (Currently
        only uses 'TRS_order' -- i.e. basically, the apparent order of
        the Twp, Rge, Sec, and description block.)
        :param commit: Whether to store the guessed layout to
        `self.layout`.
        :return: Returns the algorithm's best guess at the layout (i.e.
        a string).
        """

        if text is None:
            text = self.ppDesc

        if not isinstance(candidates, list):
            candidates = ['TRS_desc', 'desc_STR', 'S_desc_TR', 'TR_desc_S']

        try_TRS_desc = 'TRS_desc' in candidates
        try_desc_STR = 'desc_STR' in candidates
        try_S_desc_TR = 'S_desc_TR' in candidates
        try_TR_desc_S = 'TR_desc_S' in candidates
        try_subdivision = 'subdivision' in candidates

        if deduceBy == 'demerits':
            # Not yet ready for deployment. Fall back to 'TRS_order'.
            return self.deduce_layout(
                text=text, candidates=candidates, deduceBy='TRS_order',
                commit=commit)

        else:
            # Default to 'TRS_order' (i.e. check whether a Section comes
            # before a T&R, or vice versa). Strip out whitespace for this
            # (mainly to avoid false misses in S_desc_TR).

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
                    # If subdivision isn't option, default to copy_all,
                    # as no identifiable section is an insurmountable flaw
                    layoutGuess = 'copy_all'
                    if commit:
                        self.layout = layoutGuess
                    return layoutGuess

            if tr_mo is None:
                # If found no T&R's, default to copy_all because desc is
                # likely flawed.
                layoutGuess = 'copy_all'
                if commit:
                    self.layout = layoutGuess
                return layoutGuess

            # If the first identified section comes before the first
            # identified T&R, then it's probably desc_STR or S_desc_TR:
            if sec_mo.start() < tr_mo.start():
                if try_S_desc_TR:
                    # This is such an unlikely layout, we give it very
                    # limited room for error. If the section comes first
                    # in the description, we should expect it VERY early
                    # in the text:
                    if sec_mo.start() <= 1:
                        layoutGuess = 'S_desc_TR'
                    else:
                        layoutGuess = 'desc_STR'
                else:
                    layoutGuess = 'desc_STR'
            else:
                # If T&R comes before Section, it's most likely TRS_desc,
                # but could also be TR_desc_S. Check how many characters
                # appear between T&R and Sec, and decide whether it's
                # TR_desc_S or TRS_desc, based on that.
                stringBetween = text.strip()[tr_mo.end():sec_mo.start()].strip()
                if len(stringBetween) >= 4 and try_TR_desc_S:
                    layoutGuess = 'TR_desc_S'
                else:
                    layoutGuess = 'TRS_desc'

        if commit:
            self.layout = layoutGuess

        return layoutGuess

    @staticmethod
    def static_preprocess(text, defaultNS='n', defaultEW='w', ocrScrub=False):
        """
        Run the description preprocessor on text without storing any
        data / objects.

        :param text: The text (string) to be preprocessed.
        :param defaultNS: How to interpret townships for which direction
        was not specified -- i.e. either 'n' or 's'. (Defaults to 'n')
        :param defaultEW: How to interpret ranges for which direction
        was not specified -- i.e. either 'e' or 'w'. (Defaults to 'w')
        :param ocrScrub: Whether to try to iron out common OCR
        'artifacts'. May cause unintended changes. (Defaults to `False`)
        :return: The preprocessed string.
        """

        dummyObj = PLSSDesc(text, config='preprocess.False')
        return dummyObj.preprocess(
            defaultNS=defaultNS, defaultEW=defaultEW, ocrScrub=ocrScrub,
            commit=False)

    def preprocess(
            self, text=None, defaultNS=None, defaultEW=None, commit=True,
            ocrScrub=None) -> str:
        """
        Preprocess the PLSS description to iron out common kinks in
        the input data, and optionally store results to `self.ppDesc`.

        :param text: The text to be preprocessed. Defaults to what is
        stored in `self.origDesc` (i.e. the original description).
        :param defaultNS: How to interpret townships for which direction
        was not specified -- i.e. either 'n' or 's'. (Defaults to
        `self.defaultNS`, which is 'n' unless otherwise specified.)
        :param defaultEW: How to interpret ranges for which direction
        was not specified -- i.e. either 'e' or 'w'. (Defaults to
        `self.defaultEW`, which is 'w' unless otherwise specified.)
        :param ocrScrub: Whether to try to iron out common OCR
        'artifacts'. May cause unintended changes. (Defaults to
        `self.ocrScrub`, which is `False` unless otherwise specified.)
        :param commit: Whether to store the resluts to `self.ppDesc`.
        (Defaults to `True`)
        :return: The preprocessed string.
        """

        # Defaults to pulling the text from the origDesc of the object:
        if text is None:
            text = self.origDesc

        if defaultNS is None:
            defaultNS = self.defaultNS

        if defaultEW is None:
            defaultEW = self.defaultEW

        if ocrScrub is None:
            ocrScrub = self.ocrScrub

        # Look for T&R's in original text (for checking if we fix any
        # during preprocess, to raise a wFlag)
        cleanTR_list = find_tr(text)

        # Run each of the prepro regexes over the text, each working on
        # the last-prepro'd version of the text. Swaps in the cleaned up
        # TR (format 'T000N-R000W') for each T&R, every time.
        ppRegexes = [
            twprge_regex, preproTR_noNSWE_regex, preproTR_noR_noNS_regex,
            preproTR_noT_noWE_regex, twprge_pm_regex
        ]
        if ocrScrub:
            # This invites potential mis-matches, so it is not included
            # by default. Turn on with `ocrScrub=True` kwarg, or at init
            # with `config='ocrScrub'`.
            ppRegexes.insert(0, twprge_ocrScrub_regex)

        for ppRegex in ppRegexes:
            i = 0
            # working preprocessed description (gets reconstructed every loop):
            w_ppDesc = ''
            while True:
                searchTextBlock = text[i:]
                ppTr_mo = ppRegex.search(searchTextBlock)

                if ppTr_mo is None:
                    # If we've found no more T&R's, append the remaining
                    # textBlock and end the loop
                    w_ppDesc = w_ppDesc + searchTextBlock
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
                        w_ppDesc = w_ppDesc + searchTextBlock[:ppTr_mo.end()]
                        i = i + ppTr_mo.end()
                        continue

                cleanTR = preprocess_tr_mo(
                    ppTr_mo, defaultNS=defaultNS, defaultEW=defaultEW)

                # Add to the w_ppDesc all of the searchTextBlock, up to the
                # identified ppTr_mo, and add the cleanTR, with some spaces
                # around it, just to keep it cleanly delineated from
                # surrounding text
                w_ppDesc = w_ppDesc + searchTextBlock[:ppTr_mo.start()] + ' ' + cleanTR + ' '

                # Move the search index to the end of the ppTr_mo. Note
                # that ppTr_mo is indexed against the searchTextBlock,
                # so we have to add its .end() to i (which is indexed
                # against the source text)
                i = i + ppTr_mo.end()

            text = w_ppDesc

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
        afterPrepro_TR_list = find_tr(text)

        # Remove from the post-preprocess TR list each of the elements
        # in the list generated from the original text.
        for tr in cleanTR_list:
            if tr in afterPrepro_TR_list:
                afterPrepro_TR_list.remove(tr)

        if commit:
            self.ppDesc = text
            if len(afterPrepro_TR_list) > 0:
                # If any T&R's still remain in the post-ppDesc-generated
                # T&R list...
                self.wFlagList.append(
                    'T&R_fixed<%s>' % '//'.join(afterPrepro_TR_list))
                # Append a tuple to the wFlagLines list:
                self.wFlagLines.append(
                    (f"T&R_fixed<{'//'.join(afterPrepro_TR_list)}>",
                     '//'.join(afterPrepro_TR_list)))
            self.preproComplete = True

        return text

    def gen_flags(self, text=None, commit=False):
        """
        Return a ParseBag object containing wFlagList, wFlagLines,
        eFlagList,and eFlagLine, and maybe descIsFlawed. Each element in
        wFlagLines or eFlagLines is a tuple, the first element being the
        warning or error flag, and the second element being the line
        that raised the flag.  If parameter `commit=True` is passed (off
        by default), it will commit them to the PLSSDesc object's
        attributes--which is probably already done by the .parse()
        method.
        """

        if text is None:
            text = self.origDesc

        flagParseBag = ParseBag(parentType='PLSSDesc')

        lines = text.split('\n')

        ################################################################
        # Error flags
        ################################################################

        # Preprocess the text, but only to make sure at least one T&R exists
        ppText = self.preprocess(text=text, commit=False)
        if len(find_tr(ppText)) == 0:
            flagParseBag.eFlagList.append('noTR')
            flagParseBag.eFlagLines.append(
                ('noTR', 'No T&R\'s identified!'))
            flagParseBag.descIsFlawed = True

        # For everything else, we check against the origDesc
        if len(find_sec(text)) == 0 and len(find_multisec(text)) == 0:
            flagParseBag.eFlagList.append('noSection')
            flagParseBag.eFlagLines.append(
                ('noSection', 'No Sections identified!'))
            flagParseBag.descIsFlawed = True

        ################################################################
        # Warning flags
        ################################################################

        for line in lines:

            if len(isfa_except_regex.findall(line)) > 0:
                if 'isfa' not in flagParseBag.wFlagList:
                    flagParseBag.wFlagList.append('isfa')
                flagParseBag.wFlagLines.append(('isfa', line))

            if len(less_except_regex.findall(line)) > 0:
                if 'except' not in flagParseBag.wFlagList:
                    flagParseBag.wFlagList.append('except')
                flagParseBag.wFlagLines.append(('except', line))

            if len(including_regex.findall(line)) > 0:
                if 'including' not in flagParseBag.wFlagList:
                    flagParseBag.wFlagList.append('including')
                flagParseBag.wFlagLines.append(('including', line))

        if commit:
            self.unpack(flagParseBag)

        return flagParseBag

    def tracts_to_dict(self, *attributes) -> list:
        """
        Compile the data for each Tract object in .parsedTracts into a
        dict containing the requested attributes only, and return a list
        of those dicts (the returned list being equal in length to
        .parsedTracts).

        :param attributes: The names (strings) of whichever attributes
        should be included (see documentation on `pyTRS.Tract` objects
        for the names of relevant attributes).

        :Example:

        txt = '''154N-97W
        Sec 14: NE/4
        Sec 15: Northwest Quarter, North Half South West Quarter'''
        d_obj = pyTRS.PLSSDesc(txt, initParseQQ=True)
        d_obj.tracts_to_dict('trs', 'desc', 'QQList')

        Example returns a list of two dicts:

            [
            {'trs': '154n97w14',
            'desc': 'NE/4',
            'QQList': ['NENE', 'NWNE', 'SENE', 'SWNE']},

            {'trs': '154n97w15',
            'desc': 'Northwest Quarter, North Half South West Quarter',
            'QQList': ['NENW', 'NWNW', 'SENW', 'SWNW', 'NESW', 'NWSW']}
            ]
        """

        # This functionality is handled by TractList method.
        return self.parsedTracts.tracts_to_dict(attributes)

    def tracts_to_list(self, *attributes) -> list:
        """
        Compile the data for each Tract object in .parsedTracts into a
        list containing the requested attributes only, and return a
        nested list of those lists (the returned list being equal in
        length to .parsedTracts).

        :param attributes: The names (strings) of whichever attributes
        should be included (see documentation on `pyTRS.Tract` objects
        for the names of relevant attributes).

        :Example:

        txt = '''154N-97W
        Sec 14: NE/4
        Sec 15: Northwest Quarter, North Half South West Quarter'''
        d_obj = pyTRS.PLSSDesc(txt, initParseQQ=True)
        d_obj.tracts_to_list('trs', 'desc', 'QQList')

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
        return self.parsedTracts.tracts_to_list(attributes)

    def tracts_to_str(self, *attributes) -> str:
        """
        Compile the data for all Tract objects in .parsedTracts,
        containing the requested attributes only, and return a single
        string of the data.

        :param attributes: The names (strings) of whichever attributes
        should be included (see documentation on `pyTRS.Tract` objects
        for the names of relevant attributes).

        :Example:

        txt = '''154N-97W
        Sec 14: NE/4
        Sec 15: Northwest Quarter, North Half South West Quarter'''
        d_obj = pyTRS.PLSSDesc(txt, initParseQQ=True)
        d_obj.tracts_to_str('trs', 'desc', 'QQList')

        Example returns a multi-line string that looks like this when
        printed:

            Tract #1
            trs    : 154n97w14
            desc   : NE/4
            QQList : NENE, NWNE, SENE, SWNE

            Tract #2
            trs    : 154n97w15
            desc   : Northwest Quarter, North Half South West Quarter
            QQList : NENW, NWNW, SENW, SWNW, NESW, NWSW
        """

        # This functionality is handled by TractList method.
        return self.parsedTracts.tracts_to_str(attributes)

    def quick_desc(self, delim=': ', newline='\n') -> str:
        """
        Returns the entire .parsedTracts list as a single string.
        :param delim: Specify what separates TRS from the desc.
        (defaults to ': ').
        :param newline: Specify what separates Tracts from one another.
        (defaults to '\n').

        :Example:

        txt = '''154N-97W
        Sec 14: NE/4
        Sec 15: Northwest Quarter, North Half South West Quarter'''
        d_obj = pyTRS.PLSSDesc(txt, initParseQQ=True)
        d_obj.quick_desc()

        Example returns a multi-line string that looks like this when
        printed:

            154n97w14: NE/4
            154n97w15: Northwest Quarter, North Half South West Quarter
        """

        # This functionality is handled by TractList method.
        return self.parsedTracts.quick_desc(delim=delim, newline=newline)

    # def extractTractData():  # method removed in v0.4.11, 8/25/2020
    # (replaced with more specific .tracts_to_dict() and .tracts_to_list())

    # def strDesc():  # method removed in v0.4.11, 8/25/2020
    # (replaced with .tracts_to_str())

    def list_trs(self, remove_duplicates=False):
        """
        Return a list all the TRS's in .parsedTracts list. Optionally
        remove duplicates with remove_duplicates=True.
        """

        # This functionality is handled by TractList method.
        return self.parsedTracts.list_trs(remove_duplicates=remove_duplicates)

    def print_desc(self, delim=': ', newline='\n') -> None:
        """
        Simple printing of the parsed description.

        :param delim: Specify what separates TRS from the desc.
        (defaults to ': ').
        :param newline: Specify what separates Tracts from one another.
        (defaults to '\n').
        """

        # This functionality is handled by TractList method.
        self.parsedTracts.print_desc(delim=delim, newline=newline)

    # def genFlagList():  # method removed in v0.2.1, 5/31/2020

    def print_data(self, *attributes) -> None:
        """
        Simple printing of the arg-specified attributes for each Tract
        in the .parsedTracts list.
        """
        print(self.tracts_to_str(attributes))
        return

    # def sumGrossAcres(self):  # method removed in v0.4.11, 8/25/2020

    # Aliases to prevent breaking API on calls to method names with caps
    # TODO: Deprecate these method names
    list_TRS = list_trs


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
    -- Use init parameter `initParseQQ=True`
    -- Include 'initParseQQ' in the config parameters that are passed in
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
    .QQList -- A list of identified QQ's (or smaller) formatted as 4
    characters (or more, if there are further divisions).
        Ex:     Northeast Quarter -> ['NENE', 'NWNE', 'NENW', 'NWNW']
        Ex:     N/2SE/4SE/4 -> ['N2SESE']
    .lotList -- A list of identified lots.
        Ex:     Lot 1, North Half of Lot 2 -> ['L1', 'N2 of L2']
        NOTE: Divisions of lots can be suppressed with config parameter
            'includeLotDivs.False' (i.e. ['L1', 'L2'] in this example).
    .lotQQList -- A joined list of identified lots and QQ's.
        Ex:     ['L1', 'N2 of L2', 'NENE', 'NWNE', 'NENW', 'NWNW']
    .lotAcres -- A dict of lot names and their apparent gross acreages,
    as stated in the original description.
        Ex:     Lots 1(38.29), 2(39.22), 3(39.78)
                    -> {'L1': '38.29', 'L2':'39.22', 'L3':'39.78'}
    .ppDesc -- The preprocessed description. (If the object has not yet
        been preprocessed, it will be equivalent to .desc)
    .source -- (Optional) A string specifying where the description came
        from. Useful if parsing multiple descriptions and need to
        internally keep track where they came from. (Optionally specify
        at init with parameter `source=<str>`.)
    .origDesc -- The full, original text of the parent PLSSDesc object,
        if any.
    .origIndex -- An integer represeting the order in which this Tract
        object was created while parsing the parent PLSSDesc object, if
        any.
    .wFlagList -- a list of warning flags (strings) generated during
        preprocessing and/or parsing.
    .wFlagLines -- a list of 2-tuples, each being a warning flag and the
        line or context from the description that caused the warning.
    .eFlagList -- a list of error flags (strings) generated during
        preprocessing and/or parsing.
    .eFlagLines -- a list of 2-tuples, each being an error flag and the
        line or context from the description that caused the error.
    .descIsFlawed -- a bool, whether or not an apparently fatal flaw was
        discovered during parsing of the parent PLSSDesc object, if any.
        (Tract objects themselves are agnostic to fatal flaws.)

    ____ STREAMLINED OUTPUT OF THE PARSED DATA ____
    The instance variables above can be compiled with these methods:
    .quick_desc() -- Returns a string of the TRS + description.
    .to_dict() -- Compile the requested attributes into a dict.
    .to_list() -- Compile the requested attributes into a list.
    """

    def __init__(self, desc='', trs='', source='', origDesc='', origIndex=0,
                 descIsFlawed=False, config=None, initParseQQ=None):
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
        :param origDesc: The full, original text of the parent PLSSDesc
        object, if any.
        :param origIndex: An integer represeting the order in which this
        Tract object was created while parsing the parent PLSSDesc
        object, if any
        :param descIsFlawed: a bool, whether or not an apparently fatal
        flaw was discovered during parsing of the parent PLSSDesc
        object, if any. (Tract objects themselves are agnostic to fatal
        flaws.)
        :param config: Either a pyTRS.Config object, or a string of
        parameters to configure how the Tract object should be parsed.
        (See documentation on pyTRS.Config objects for optional config
        parameters.)
        :param initParseQQ: Whether to parse the `desc` into lots/QQs at
        init. (Defaults to False)
        """

        if not isinstance(trs, str) and not trs is None:
            raise TypeError("`trs` must be a string or None")

        # a string containing the TRS (Township Range and Section),
        # stored in the format 000n000w00 (or fewer digits for Twp/Rge).
        self.trs = trs

        # a string containing the description block.
        self.desc = desc

        # The order in which this TRS/Desc was identified when parsing
        # the original PLSSDesc object (if applicable)
        self.origIndex = origIndex

        # The source of this Tract.
        self.source = source

        # Original description of the full PLSS description from which
        # this Tract comes
        self.origDesc = origDesc

        # If the TRS has been specified (i.e. is in the '000n000w00'
        # format), unpack it into the component parts
        self.twp, self.rge, self.sec = break_trs(trs)
        if self.sec is None:
            self.sec = 'secError'
        self.twprge = self.twp + self.rge

        # Whether fatal flaws were identified during the parsing of the
        # parent PLSSDesc object, if any
        self.descIsFlawed = descIsFlawed
        # list of warning flags
        self.wFlagList = []
        # list of 2-tuples that caused warning flags (warning flag, text string)
        self.wFlagLines = []
        # list of error flags
        self.eFlagList = []
        # list of 2-tuples that caused error flags (error flag, text string)
        self.eFlagLines = []

        # A list of QQ's (or smaller) with no quarter fractions
        # i.e. ['NENE', 'NENW', 'N2SENW', ... ]:
        self.QQList = []

        # A list of standard lots, ['L1', 'L2', 'N2 of L5', ...]:
        self.lotList = []

        # A combined list of lots + QQs:
        self.lotQQList = []

        # A dict of lot acreages, keyed by 'L1', 'L2', etc.
        self.lotAcres = {}

        # A bool to track whether the preprocess has been completed
        self.preproComplete = False

        #---------------------------------------------------------------
        # Configure how the Tract should be parsed:

        # If a T&R is identified without 'North/South' specified, fall
        # back on this. Will be filled in with set_config() (if
        # applicable) or defaulted to 'n' shortly.
        # NOTE: only applicable for using .from_twprgesec()
        self.defaultNS = None

        # If a T&R is identified without 'East/West' specified, fall
        # back on this. Will be filled in with set_config() (if
        # applicable) or defaulted to 'w' shortly.
        # NOTE: only applicable for using .from_twprgesec()
        self.defaultEW = None

        # NOTE: `initPreproces`, `initParseQQ`, `cleanQQ`, &
        # `includeLotDivs` will be changed in set_config(), if needed.

        # Whether we should preprocess the text at initialization:
        self.initPreprocess = True

        # Whether we should parse lots and aliquots at init.
        self.initParseQQ = False

        # Whether the user expects tract descriptions to have `cleanQQ` (i.e.
        # nothing but clean aliquots and lots, with no typos, exceptions,
        # metes-and-bounds, or other hindrances to the parser.)
        self.cleanQQ = False

        # Whether to include any divisions of lots
        # (i.e. 'N/2 of Lot 1' to 'N2 of L1').
        self.includeLotDivs = True

        # Whether to iron out common OCR artifacts. Defaults to `False`.
        # NOTE: Currently only has effect if Tract object is created via
        # `.from_twprgesec()`   ...  May have more effect in a later version.
        self.ocrScrub = False

        # Apply settings from kwarg `config=`
        self.set_config(config)

        # If `defaultNS` has not yet been specified, default to 'n' :
        if self.defaultNS is None:
            self.defaultNS = 'n'

        # If `defaultEW` has not yet been specified, default to 'w' :
        if self.defaultEW is None:
            self.defaultEW = 'w'

        # If kwarg-specified initParseQQ, that will override config input
        if isinstance(initParseQQ, bool):
            self.initParseQQ = initParseQQ

        ################################################################
        # If config settings require calling preprocess() and parse() at
        # initialization, do it now:
        ################################################################

        if self.initPreprocess or self.cleanQQ:
            self.preprocess(commit=True)
        else:
            self.ppDesc = self.desc

        if self.initParseQQ:
            self.parse(commit=True)

    @staticmethod
    def from_twprgesec(
            desc='', twp='0', rge='0', sec='0', source='', origDesc='',
            origIndex=0, descIsFlawed=False, config=None, initParseQQ=None):
        """
        Create a Tract object from separate Twp, Rge, and Sec components
        rather than joined TRS. All parameters are the same as
        __init__(), except that `trs=` are replaced with `twp=`, `rge`,
        and `sec`. (If N/S or E/W are not specified, will pull defaults
        from config parameters.)

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
        # can extract `defaultNS` and `defaultEW`
        if isinstance(config, Config):
            configObj = config
        elif isinstance(config, str):
            configObj = Config(config)
        else:
            configObj = Config(None)

        # Get our defaultNS and defaultEW from config
        defaultNS = configObj.defaultNS
        defaultEW = configObj.defaultEW
        if defaultNS is None: defaultNS = 'n'
        if defaultEW is None: defaultEW = 'w'
        if defaultNS.lower() not in ['n', 'north', 's', 'south']:
            defaultNS = 'n'
        if defaultEW.lower() not in ['w', 'west', 'e', 'east']:
            defaultEW = 'w'

        # Whether to scrub twp, rge, and sec strings for OCR artifacts
        ocrScrub = False
        if configObj.ocrScrub is not None:
            ocrScrub = configObj.ocrScrub

        # Get twp in a standardized format, if we can
        if not isinstance(twp, (int,str)):
            twp = ''
        elif isinstance(twp, int):
            twp = f'{str(twp)}{defaultNS}'
        elif isinstance(twp, str):
            if twp[-1].lower() not in ['n', 's']:
                # If the final character is not 'n' or 's', apply our defaultNS
                twp = twp + defaultNS
            if ocrScrub:
                # If configured so, OCR-scrub all but the final character
                twp = ocr_scrub_alpha_to_num(twp[:-1]) + twp[-1]
            twp = twp.lower()

        # Get rge in a standardized format, if we can
        if not isinstance(rge, (int, str)):
            rge = ''
        elif isinstance(rge, int):
            rge = f'{str(rge)}{defaultEW}'
        elif isinstance(rge, str):
            if rge[-1].lower() not in ['e', 'w']:
                # If the final character is not 'e' or 'w', apply our defaultEW
                rge = rge + defaultEW
            if ocrScrub:
                # If configured so, OCR-scrub all but the final character
                rge = ocr_scrub_alpha_to_num(rge[:-1]) + rge[-1]
            rge = rge.lower()

        # Get sec in a standardized format, if we can
        if not isinstance(sec, (int,str)):
            sec = ''
        elif isinstance(sec, int):
            sec = str(sec)
        elif isinstance(sec, str):
            try:
                sec = str(int(sec)).rjust(2, '0')
                if ocrScrub:
                    # If configured so, OCR-scrub all characters
                    sec = ocr_scrub_alpha_to_num(sec)
            except:
                pass

        # compile a TRS, and see if it matches our known format
        trs = f'{twp}{rge}{sec}'
        if TRS_unpacker_regex.search(trs) is None:
            # If not, set `trs` as an empty string
            trs = ''

        # Create a new Tract object and return it
        TractObj = Tract(
            desc=desc, trs=trs, source=source, origDesc=origDesc,
            origIndex=origIndex, descIsFlawed=descIsFlawed, config=configObj,
            initParseQQ=initParseQQ)
        TractObj.twp = twp
        TractObj.rge = rge
        TractObj.sec = sec
        return TractObj

    def set_config(self, config):
        """
        Apply the relevant settings from a Config object to this object;
        takes either a string (i.e. config text) or a Config object.

        :param config: Either a pyTRS.Config object, or equivalent
        config parameters. (See pyTRS.Config documentation for optional
        parameters.)
        """
        if isinstance(config, str) or config is None:
            configObj = Config(config)
        elif isinstance(config, Config):
            configObj = config
        else:
            raise TypeError(
                '`config` must be either a string or pyTRS.Config object. '
                f"Passed as type {type(config)}`.")

        for attrib in Config.__TractAttribs__:
            value = getattr(configObj, attrib)
            if value is not None:
                setattr(self, attrib, value)

    def unpack(self, targetParseBagObj):
        """
        Unpack (append or set) the relevant attributes of the
        `targetParseBagObj` into self's attributes.

        :param targetParseBagObj: A ParseBag object containing data from
        the parse.
        """

        if not isinstance(targetParseBagObj, ParseBag):
            return

        if targetParseBagObj.descIsFlawed:
            self.descIsFlawed = True

        if len(targetParseBagObj.wFlagList) > 0:
            self.wFlagList.extend(targetParseBagObj.wFlagList)

        if len(targetParseBagObj.eFlagList) > 0:
            self.eFlagList.extend(targetParseBagObj.eFlagList)

        if len(targetParseBagObj.wFlagLines) > 0:
            self.wFlagLines.extend(targetParseBagObj.wFlagLines)

        if len(targetParseBagObj.eFlagLines) > 0:
            self.eFlagLines.extend(targetParseBagObj.eFlagLines)

        if targetParseBagObj.parentType == 'Tract':
            # Only if unpacking a Tract-level ParseBag... Otherwise,
            # these attributes won't exist for that ParseBagObj.

            if len(targetParseBagObj.QQList) > 0:
                # Only append fresh (non-duplicate) QQ's, and raise a
                # flag if there are any duplicates
                dupQQs = []
                freshQQs = []
                for QQ in targetParseBagObj.QQList:
                    if QQ in self.QQList or QQ in freshQQs:
                        dupQQs.append(QQ)
                    else:
                        freshQQs.append(QQ)
                self.QQList.extend(freshQQs)
                if len(dupQQs) > 0:
                    self.wFlagList.append('dup_QQ')
                    self.wFlagLines.append(
                        ('dup_QQ', f'<{self.trs}: {", ".join(dupQQs)}>'))

            if len(targetParseBagObj.lotList) > 0:
                # Only append fresh (non-duplicate) Lots, and raise a
                # flag if there are any duplicates
                dupLots = []
                freshLots = []
                for lot in targetParseBagObj.lotList:
                    if lot in self.lotList or lot in freshLots:
                        dupLots.append(lot)
                    else:
                        freshLots.append(lot)
                self.lotList.extend(freshLots)
                if len(dupLots) > 0:
                    self.wFlagList.append('dup_lot')
                    self.wFlagLines.append(
                        ('dup_lot', f'<{self.trs}: {", ".join(dupLots)}>'))

            self.lotQQList = self.lotList + self.QQList

            if len(targetParseBagObj.lotAcres) > 0:
                self.lotAcres = targetParseBagObj.lotAcres
                # TODO: Handle discrepancies, if there's already data in
                #   lotAcres.

    def parse(
            self, text=None, commit=True, cleanQQ=None, includeLotDivs=None,
            preprocess=None):
        """

        :param text: The text to be parsed into lots and QQ's. If not
        specified, will pull from `self.ppDesc` (i.e. the preprocessed
        description).
        :param commit: Whether to commit the results to the appropriate
        instance attributes. Defaults to `True`.
        :param cleanQQ: Whether to expect only clean lots and QQ's (i.e.
        no metes-and-bounds, exceptions, complicated descriptions,
        etc.). Defaults to whatever is specified in `self.cleanQQ`
        (which is False, unless configured otherwise).
        :param includeLotDivs: Whether to report divisions of lots.
        Defaults to whatever is specified in `self.includeLotDivs`
        (which is True, unless configured otherwise).
            ex:  North Half of Lot 1
                    `True` -> 'N2 of L1'
                    `False` -> 'L1'
        :param preprocess: Whether to preprocess the text before parsing
        it (if the preprocess has not already been done).
        :return: Returns the a single list of identified lots and QQ's
        (equivalent to what would be stored in `.lotQQList`).
        """

        # TODO: Generate a list (saved as an attribute) of slice_indexes
        #   of the `ppDesc` for the text that was incorporated into
        #   lots and QQ's vs. not.

        if text is None:
            text = self.ppDesc

        if cleanQQ is None:
            cleanQQ = self.cleanQQ

        if includeLotDivs is None:
            includeLotDivs = self.includeLotDivs

        # If preprocess has not already been complete, and param did not
        # dictate `preprocess=False`, then we will want to run
        # preprocess(). Alternatively, if our kwarg-specified cleanQQ
        # does not match self.cleanQQ, we want the kwarg-specified to
        # control, so we'll run preprocess() again, with the
        # kwarg-specified `cleanQQ` value:
        do_prepro = False
        if not self.preproComplete and preprocess in [None, True]:
            do_prepro = True
        if self.cleanQQ != cleanQQ:
            do_prepro = True

        if do_prepro:
            text = self.preprocess(cleanQQ=cleanQQ, commit=False)

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
        # 3) Unpack lot_regex matches into a lotList.
        # 4) Extract aliquot_regex matches from the text.
        # 5) Convert the aliquot_regex matches into a QQList.
        # 6) Pack it all into a ParseBag.
        # 6a) If committing the results, self.unpack() the ParseBag.
        # 7) Join the lotList and QQList from the ParseBag, and return it.
        ################################################################

        # For holding the data during parsing
        plqqParseBag = ParseBag(parentType='Tract')

        # Swap out NE/NW/SE/SW and N2/S2/E2/W2 matches for cleaner versions
        text = scrub_aliquots(text, cleanQQ=cleanQQ)

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
            if lot_aliq_mo == None:
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
            # Unpack the lots in this lotTextBlock (and get a ParseBag back)
            lotspb = unpack_lots(lotTextBlock, includeLotDivs=includeLotDivs)

            # Append these identified lots:
            lots.extend(lotspb.lotList)

            # Add any identified lotAcres to the dict:
            for lot in lotspb.lotAcres:
                lotsAcresDict[lot] = lotspb.lotAcres[lot]

            # And absorb any flags/flagLines:
            plqqParseBag.absorb(lotspb)

        # Get a list of all of the aliquots strings
        aliqTextBlocks = []
        remainingText = text
        while True:
            # Run this loop, pulling the next aliquot match until we run out.
            aliq_mo = aliquot_unpacker_regex.search(remainingText)
            if aliq_mo == None:
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

        # Now that we have list of text blocks, each containing a separate
        # aliquot, parse each of them into QQ's (or smaller, if further
        # divided).
        #   ex:  ['NE¼', 'E½NE¼NW¼']
        #           -> ['NENE' , 'NWNE' , 'SENE' , 'SWNE', 'E2NENW']

        QQList = []
        for aliqTextBlock in aliqTextBlocks:
            wQQList = unpack_aliquots(aliqTextBlock)
            QQList.extend(wQQList)

        plqqParseBag.QQList = QQList
        plqqParseBag.lotList = lots
        plqqParseBag.lotAcres = lotsAcresDict

        retLotQQList = plqqParseBag.lotList + plqqParseBag.QQList

        # Store the results, if instructed to do so.
        if commit:
            self.unpack(plqqParseBag)

        return retLotQQList

    def preprocess(self, text=None, commit=True, cleanQQ=None) -> str:
        """
        Preprocess the description text to iron out common kinks in the
        input data, and optionally store results to `self.ppDesc`.

        :param text: The text to be preprocessed. Defaults to what is
        stored in `self.desc` (i.e. the original description block).
        :param commit: Whether to store the resluts to `self.ppDesc`.
        (Defaults to `True`)
        :param cleanQQ: Whether to expect only clean lots and QQ's (i.e.
        no metes-and-bounds, exceptions, complicated descriptions,
        etc.). Defaults to whatever is specified in `self.cleanQQ`
        (which is False, unless configured otherwise).
        :return: The preprocessed string.
        """

        if text is None:
            text = self.desc

        if cleanQQ is None:
            cleanQQ = self.cleanQQ

        text = scrub_aliquots(text, cleanQQ=cleanQQ)

        if commit:
            self.ppDesc = text
            self.preproComplete = True

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
        attributes = clean_attributes(attributes)

        def val(att):
            """
            Safely get the value of the attribute; and handle instances
            where the requested attribute does not exist for this
            object.
            """
            if hasattr(self, att):
                attVal = getattr(self, att)
            else:
                attVal = f'{att}: n/a'
            return attVal

        attDict = {}
        for attribute in attributes:
            attDict[attribute] = val(attribute)
        return attDict

    def to_list(self, *attributes) -> list:
        """
        Compile the requested attributes into a list.

        :param attributes: The attribute names (instance variables) to
        include.
        :return: A list of attribute values.
        """

        attributes = clean_attributes(attributes)
        attDict = self.to_dict(attributes)
        attList = []
        for attribute in attributes:
            attList.append(attDict[attribute])

        return attList

    def quick_desc(self, delim=': ') -> str:
        """
        Return a string of the TRS + description.

        :param delim: The string that should separate TRS from the
        description. (Defaults to ': ')
        :return: A string of the TRS + description.
        """
        return f"{self.trs}{delim}{self.desc}"

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

    @staticmethod
    def check_illegal(elem):
        """
        Ensure a list element is a Tract object, or raise TypeError.
        """
        if not isinstance(elem, Tract):
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
        tl_obj = d_obj.parse(initParseQQ=True, commit=False)
        tl_obj.tracts_to_dict('trs', 'desc', 'QQList')

        Example returns a list of two dicts:

            [
            {'trs': '154n97w14',
            'desc': 'NE/4',
            'QQList': ['NENE', 'NWNE', 'SENE', 'SWNE']},

            {'trs': '154n97w15',
            'desc': 'Northwest Quarter, North Half South West Quarter',
            'QQList': ['NENW', 'NWNW', 'SENW', 'SWNW', 'NESW', 'NWSW']}
            ]
        """

        allTractData = []

        attributes = clean_attributes(attributes)

        for tractObj in self:
            TractList.check_illegal(tractObj)
            allTractData.append(tractObj.to_dict(attributes))
        return allTractData

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
        tl_obj = d_obj.parse(initParseQQ=True, commit=False)
        tl_obj.tracts_to_list('trs', 'desc', 'QQList')

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

        allTractData = []

        attributes = clean_attributes(attributes)

        for tractObj in self:
            TractList.check_illegal(tractObj)
            allTractData.append(tractObj.to_list(attributes))
        return allTractData

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
        tl_obj = d_obj.parse(initParseQQ=True, commit=False)
        tl_obj.tracts_to_str('trs', 'desc', 'QQList')

        Example returns a multi-line string that looks like this when
        printed:

            Tract #1
            trs    : 154n97w14
            desc   : NE/4
            QQList : NENE, NWNE, SENE, SWNE

            Tract #2
            trs    : 154n97w15
            desc   : Northwest Quarter, North Half South West Quarter
            QQList : NENW, NWNW, SENW, SWNW, NESW, NWSW
        """

        attributes = clean_attributes(attributes)

        # Figure out how far to justify the attribute names in the print out:
        longest = 0
        for element in attributes:
            if len(element) > longest:
                longest = len(element)

        # Print each Tract's data
        i = 1
        outputText = ''
        for TractData in self.tracts_to_dict(attributes):
            outputText = outputText + f'\nTract #{i}\n'
            i += 1
            for key in TractData:
                if type(TractData[key]) in [list, tuple]:
                    td = ", ".join(flatten(TractData[key]))
                else:
                    td = TractData[key]
                outputText = outputText + f'{key.ljust(longest, " ")} : {td}\n'
        return outputText.strip('\n')

    def quick_desc(self, delim=': ', newline='\n') -> str:
        """
        Returns the entire .parsedTracts list as a single string.
        :param delim: Specify what separates TRS from the desc.
        (defaults to ': ').
        :param newline: Specify what separates Tracts from one another.
        (defaults to '\n').

        :Example:

        txt = '''154N-97W
        Sec 14: NE/4
        Sec 15: Northwest Quarter, North Half South West Quarter'''
        d_obj = PLSSDesc(txt)
        tl_obj = d_obj.parse(initParseQQ=True, commit=False)
        tl_obj.quick_desc()

        Example returns a multi-line string that looks like this when
        printed:

            154n97w14: NE/4
            154n97w15: Northwest Quarter, North Half South West Quarter
        """

        dlist = []
        for tractObj in self:
            TractList.check_illegal(tractObj)
            dlist.append(tractObj.quick_desc(delim=delim))

        return newline.join(dlist)

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
        all_TRS = []
        for TractObj in self:
            all_TRS.append(TractObj.trs)
        if remove_duplicates:
            all_TRS_noDup = []
            for TRS in all_TRS:
                if TRS not in all_TRS_noDup:
                    all_TRS_noDup.append(TRS)
            all_TRS = all_TRS_noDup
        return all_TRS

    # Aliases to prevent breaking API on calls to method names with caps
    # TODO: Deprecate these method names
    list_TRS = list_trs


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
    # .unpack() the contents of the ParseBag into its own attributes
    # -- i.e. PLSSDescObj.unpack(ParseBagObj).

    # It was designed this way because different functions process
    # different components of the PLSS description, but almost all of
    # them can generate warning flags and error flags for the user's
    # attention. For UX reasons, we want those warning/error data stored
    # in a single location (i.e. a PLSSDescObj.wFlagList or .eFlagList).
    # Tract objects also contain wFlagList and eFlagList.

    # So these ParseBag objects will hold those warning/error data (and
    # the TractList, etc.) in one place until the intended endpoint is
    # reached, where it is unpacked.

    # A ParseBag object can also absorb a child ParseBag object by
    # appending (but not overwriting) its own data:
    # ParseBag1.absorb(ParseBag2).  This is done, for example, where
    # ParseBag2 stores Tract-level parsing data (e.g., QQList, lotList)
    # -- but where warning flags can also be generated that would be
    # relevant to the higher-level class PLSSDesc.

    def __init__(self, parentType='PLSSDesc'):

        # parentType will establish additional attributes, as necessary,
        # depending on the function or method that created the ParseBag
        self.parentType = parentType

        # for all types of objects:
        self.wFlagList = []
        self.wFlagLines = []
        self.eFlagList = []
        self.eFlagLines = []
        self.descIsFlawed = False

        if parentType == 'PLSSDesc':
            self.parsedTracts = TractList()

        elif parentType == 'Tract':
            self.QQList = []
            self.lotList = []
            self.lotAcres = {}

        elif parentType == 'multiSec':
            # for unpacking multiSec
            self.secList = []

        elif parentType == 'lotText':
            # for unpacking text from a lot_regex match into component lots
            self.lotList = []
            self.lotAcres = {}

    def absorb(self, targetParseBagObj):
        """
        Absorb (i.e. append or set) the relevant attributes of a child
        `targetParseBagObj` into the parent (i.e. self).
        """

        if not isinstance(targetParseBagObj, ParseBag):
            return

        # We do not absorb QQList, lotList, or lotAcres, since those are not
        # relevant to a PLSSDescObj (only TractObj).

        if targetParseBagObj.descIsFlawed:
            self.descIsFlawed = True

        if len(targetParseBagObj.wFlagList) > 0:
            self.wFlagList.extend(targetParseBagObj.wFlagList)

        if len(targetParseBagObj.eFlagList) > 0:
            self.eFlagList.extend(targetParseBagObj.eFlagList)

        if len(targetParseBagObj.wFlagLines) > 0:
            self.wFlagLines.extend(targetParseBagObj.wFlagLines)

        if len(targetParseBagObj.eFlagLines) > 0:
            self.eFlagLines.extend(targetParseBagObj.eFlagLines)

        if targetParseBagObj.parentType == 'PLSSDesc':
            self.parsedTracts.extend(targetParseBagObj.parsedTracts)


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
        -- 'n'  <or>  'defaultNS.n'  vs.  's'  <or>  'defaultNS.s'
        -- 'e'  <or>  'defaultEW.e'  vs.  'w'  <or>  'defaultEW.w'
        -- 'initParse'  vs.  'initParse.False'
        -- 'initParseQQ'  vs.  'initParseQQ.False'
        -- 'initPreprocess'  vs.  'initPreprocess.False'
        -- 'cleanQQ'  vs.  'cleanQQ.False'
        -- 'requireColon'  vs.  'requireColon.False'
        -- 'includeLotDivs'  vs.  'includeLotDivs.False'
        -- 'ocrScrub'  vs.  'ocrScrub.False'
        -- 'segment'  vs.  'segment.False'
        Only one of the following may be passed -- and none of these are
        recommended:
        -- 'TRS_desc'  <or>  'layout.TRS_desc'
        -- 'desc_STR'  <or>  'layout.desc_STR'
        -- 'S_desc_TR'  <or>  'layout.S_desc_TR'
        -- 'TR_desc_S'  <or>  'layout.TR_desc_S'
        -- 'copy_all'  <or>  'layout.copy_all'
    """

    # Implemented settings that are settable via Config object:
    __ConfigAttribs__ = [
        'defaultNS', 'defaultEW', 'initPreprocess', 'layout', 'initParse',
        'initParseQQ', 'cleanQQ', 'requireColon', 'includeLotDivs', 'ocrScrub',
        'segment'
    ]

    # A list of attribute names whose values should be a bool:
    __boolTypeAttribs__ = [
        'initParse', 'initParseQQ', 'cleanQQ', 'includeLotDivs',
        'initPreprocess', 'requireColon', 'ocrScrub', 'segment'
    ]

    # Those attributes relevant to PLSSDesc objects:
    __PLSSDescAttribs__ = __ConfigAttribs__

    # Those attributes relevant to Tract objects:
    __TractAttribs__ = [
        'defaultNS', 'defaultEW', 'initPreprocess', 'initParseQQ', 'cleanQQ',
        'includeLotDivs', 'ocrScrub'
    ]

    def __init__(self, configText='', configName=''):
        """
        Compile a Config object from a string `configText=`, with
        optional kwarg `configName=` that does not affect parsing.

        Pass config parameters as a single string, with each parameter
        separated by comma. Spaces are optional and have no effect.
            ex: 'n,s,cleanQQ,includeLotDivs.False'

        All possible parameters (call `pyTRS.utils.config_parameters()`
        for definitions) -- any unspecified parameters will fall back to
        default parsing behavior:
        -- 'n'  <or>  'defaultNS.n'  vs.  's'  <or>  'defaultNS.s'
        -- 'e'  <or>  'defaultEW.e'  vs.  'w'  <or>  'defaultEW.w'
        -- 'initParse'  vs.  'initParse.False'
        -- 'initParseQQ'  vs.  'initParseQQ.False'
        -- 'initPreprocess'  vs.  'initPreprocess.False'
        -- 'cleanQQ'  vs.  'cleanQQ.False'
        -- 'requireColon'  vs.  'requireColon.False'
        -- 'includeLotDivs'  vs.  'includeLotDivs.False'
        -- 'ocrScrub'  vs.  'ocrScrub.False'
        -- 'segment'  vs.  'segment.False'
        Only one of the following may be passed -- and none of these are
        recommended:
        -- 'TRS_desc'  <or>  'layout.TRS_desc'
        -- 'desc_STR'  <or>  'layout.desc_STR'
        -- 'S_desc_TR'  <or>  'layout.S_desc_TR'
        -- 'TR_desc_S'  <or>  'layout.TR_desc_S'
        -- 'copy_all'  <or>  'layout.copy_all'
        """

        # All attributes (except configName) are defaulted to `None`,
        # because PLSSDesc and Tract objects will use only those that
        # have been specified as other than `None`.

        if isinstance(configText, Config):
            # If a Config object is passed as the first argument,
            # decompile its text and use that:
            configText = configText.decompile_to_text()
        elif configText is None:
            configText = ''
        elif not isinstance(configText, str):
            raise TypeError(
                'config must be specified as a string, None, or another '
                f"Config object. Passed as type: {type(configText)}")
        self.configText = configText
        self.configName = configName

        # Default all other attributes to `None`:
        for attrib in Config.__ConfigAttribs__:
            setattr(self, attrib, None)

        # Remove all spaces from configText:
        configText = configText.replace(' ', '')

        # Separate config commands with ','  or  ';'  or '|'
        configLines = re.split(r'[;,]', configText)

        for line in configLines:
            # Parse each 'attrib.val' pair, and commit to the configObj

            if line == '':
                continue

            if re.split(r'[\.=]', line)[0] in Config.__boolTypeAttribs__:
                # If string is the name of an attribute that will be stored
                # as a bool, default to `True` (but will be overruled in
                # set_str_to_values() if specified otherwise):
                self.set_str_to_values(line, defaultBool=True)
            elif line.lower() in ['n', 's', 'north', 'south']:
                # Specifying N/S can be done with just a string (there's
                # nothing else it can mean in config context.)
                self.defaultNS = line[0].lower()
            elif line.lower() in ['e', 'w', 'east', 'west']:
                # Specifying E/W can be done with just a string (there's
                # nothing else it can mean in config context.)
                self.defaultEW = line[0].lower()
            elif line in __implementedLayouts__:
                # Specifying layout can be done with just a string
                # (there's nothing else it can mean in config context.)
                self.layout = line
            else:
                # For anything else, set it with `.set_str_to_values()`.
                self.set_str_to_values(line)

    def save_to_file(self, filepath):
        """
        Save this Config object to .txt file.
        """

        if filepath[-4:].lower() != '.txt':
            raise ValueError('Error: filename must be .txt file')

        file = open(filepath, 'w')

        attsToWrite = ['configName'] + Config.__ConfigAttribs__

        file.write(f"<Contains config data for parsing PLSSDesc "
                   f"and/or Tract objects with the pyTRS library.>\n")
        file.write(f"<configText: '{self.decompile_to_text()}'>\n")

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
            configLines = file.readlines()

        configObj = Config()

        for line in configLines:
            # Ignore data stored in angle brackets
            if line[0] == '<':
                continue

            # For each line, parse the 'attrib.val' pair, and commit to
            # the configObj, using .set_str_to_values()
            configObj.set_str_to_values(line.strip('\n'))
        return configObj

    @staticmethod
    def from_parent(parentObj, configName='', suppress_layout=False):
        """
        Compile and return a Config object from the settings in a
        PLSSDesc object or Tract object.
        :param parentObj: A PLSSDesc or Tract object whose config
        parameters should be compiled into this Config object.
        :param configName: An optional string, being the name of this
        Config object.
        :param suppress_layout: A bool, whether or not to include the
        `.layout` attribute from the parent object.
        """

        configObj = Config()

        configObj.configName = configName
        configObj.initPreprocess = parentObj.initPreprocess
        if isinstance(parentObj, PLSSDesc) and not suppress_layout:
            configObj.layout = parentObj.layout
        else:
            configObj.layout = None
        configObj.initParse = parentObj.initParse
        configObj.initParseQQ = parentObj.initParseQQ
        configObj.cleanQQ = parentObj.cleanQQ
        configObj.defaultNS = parentObj.defaultNS
        configObj.defaultEW = parentObj.defaultEW
        configObj.includeLotDivs = parentObj.includeLotDivs

        return configObj

    def decompile_to_text(self) -> str:
        """
        Decompile a Config object into its equivalent string.
        """

        def write_val_as_text(att, val):
            if att in Config.__boolTypeAttribs__:
                if val == True:
                    # If true, Config needs to receive only the
                    # attribute name (defaults to True if specified).
                    return att
                elif val == False:
                    return f"{att}.{val}"
                else:
                    # i.e. `val is None`; in which case, we won't write
                    # the attribute name
                    return ""
            elif att in ['defaultNS', 'defaultEW']:
                if val is not None:
                    # Only need to specify 'n' or 's' to set defaultNS; and
                    # 'e' or 'w' for defaultEW (i.e. not 'defaultNS.n' or
                    # 'defaultEW.w'), so we return only `val`, and not `att`
                    return val
                else:
                    return ''
            elif val is None:
                return ''
            else:
                return f"{att}.{val}"

        writeVals = []
        for att in Config.__ConfigAttribs__:
            w = write_val_as_text(att, getattr(self, att))
            if w != '':
                # Include only non-empty strings (i.e. config params
                # that were actually set)
                writeVals.append(w)

        return ','.join(writeVals)

    def set_str_to_values(self, attrib_val, defaultBool=None):
        """
        Take in a string of an attribute/value pair (in the format
        'attribute.value' or 'attribute=value') and set the appropriate
        value of the attribute.
        """

        def str_to_value(text):
            """
            Convert string to None or bool, if appropriate.
            """
            if text == 'None':
                return None
            elif text == 'True':
                return True
            elif text == 'False':
                return False
            else:
                return text

        # split attribute/value pair by '.' or '='
        #   ex: 'defaultNS.n' or 'defaultNS=n' -> ['defaultNS', 'n']
        comps = re.split(r'[\.=]', attrib_val)

        # Track whether only one component was found in the text with `onlyOne`:
        #   i.e. "initParse." --> `onlyOne=True`
        #   but 'initParse.True' --> `onlyOne=False`
        # (Both will set `self.initParse` to `True` in this example, since it's
        # a bool-type config parameter)
        onlyOne = False
        if len(comps) != 2:
            onlyOne = True

        def decide_bool():
            """
            If onlyOne, return the default bool; otherwise, return
            the user-specified value from attrib_val.
            """
            if onlyOne:
                return defaultBool
            else:
                return str_to_value(comps[1])

        if onlyOne and not isinstance(defaultBool, bool):
            # If only one component, and defaultBool was not entered as
            # a bool, return a failure value:
            return -1

        # Write values to the respective attributes. boolTypeAttribs
        # will specifically become bools:
        if comps[0] in Config.__boolTypeAttribs__:
            # If this is a bool-type attribute, set the value with decide_bool()
            setattr(self, comps[0], decide_bool())
            return 0
        elif comps[0] in ['defaultNS', 'defaultEW']:
            # Only writing the first letter of comps[1], in lowercase
            #   (i.e. 'North' --> 'n' or 'West' --> 'w'):
            setattr(self, comps[0], str_to_value(comps[1][0].lower()))
            return 0
        else:
            # Otherwise, set it however it's specified.
            setattr(self, comps[0], str_to_value(comps[1]))
            return 0


    # def help():  # method moved to pyTRS.utils.config_help() in v0.4.11,
    #   8/25/2020

    # def parameters():
    # method moved to pyTRS.utils.config_parameters() in v0.4.11,
    #   8/25/2020


########################################################################
# Tools and functions for PLSSDesc.parse()
########################################################################

def findall_matching_tr(text, layout=None) -> ParseBag:
    """
    INTERNAL USE:

    Find T&R's that appropriately match the layout. Returns a ParseBag
    that contains an ad-hoc `.trPosList` attribute, which holds a list
    of tuples, each containing a T&R (as '000n000w' or fewer digits),
    and its start and end position in the string.
    """

    if layout not in __implementedLayouts__:
        layout = PLSSDesc.deduce_segment_layout(text=text)

    trParseBag = ParseBag(parentType='PLSSDesc')

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
        # to check what's in between. For TRS_desc and S_desc_TR layouts,
        # we want to rule out misc. interveners:
        #       ','  'in'  'of'  'all of'  'all in'  (etc.).
        # If we have such an intervening string, then this appears to be
        # desc_STR layout -- ex. 'Section 1 of T154N-R97W'
        interveners = ['in', 'of', ',', 'all of', 'all in', 'within', 'all within']
        if secFound and text[j:i].strip() in interveners \
                and layout in ['TRS_desc', 'S_desc_TR']:
            # In TRS_Desc and S_desc_TR layouts specifically, this is
            # NOT a T&R match for a new Tract.

            # Move our parsing index to the end of the currently identified T&R.
            # NOTE: the length of this tr_mo match is indexed against the text
            # slice, so need to add it to i (which is indexed against the full
            # text) to get the 'real' index
            i = i + len(tr_mo.group())

            # and append a warning flag that we've ignored this T&R:
            ignoredTR = compile_tr_mo(tr_mo)
            flag = 'TR_not_pulled<%s>' % ignoredTR
            line = tr_mo.group()
            trParseBag.wFlagList.append(flag)
            trParseBag.wFlagLines.append((flag, line))
            continue

        # Otherwise, if there is NO intervener, or the layout is something
        # other than TRS_desc or S_desc_TR, then this IS a match and we
        # want to store it.
        else:
            wTRList.append((compile_tr_mo(tr_mo), i, i + len(tr_mo.group())))
            # Move the parsing index to the end of the T&R that we just matched:
            i = i + len(tr_mo.group())
            continue

    # Ad-hoc attribute (T&R/position list)
    trParseBag.trPosList = wTRList

    return trParseBag


def segment_by_tr(text, layout=None, trFirst=None):
    """
    INTERNAL USE:

    Break the description into segments, based on previously
    identified T&R's that match our description layout via the
    findall_matching_tr() function. Returns a list of textBlocks AND a
    list of discarded textBlocks.

    :param layout: Which layout to use. If not specified, will deduce.
    :param trFirst: Whether it's a layout where TR comes first (i.e.
    'TRS_desc' or 'TR_desc_S').
    """

    if layout not in __implementedLayouts__:
        layout = PLSSDesc.deduce_segment_layout(text=text)

    if not isinstance(trFirst, bool):
        if layout in ['TRS_desc', 'TR_desc_S']:
            trFirst = True
        else:
            trFirst = False

    # Search for all T&R's that match the layout requirements.
    trMatchPB = findall_matching_tr(text, layout=layout)

    # Pull ad-hoc `.trPosList` attribute from the ParseBag object. Do not absorb the rest.
    wTRList = trMatchPB.trPosList

    if wTRList == []:
        # If no T&R's had been matched, return the text block as single element in a list
        # (what would have been `trTextBlocks`), and another empty list (what would have
        # been `discardTextBlocks`)
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

    if trFirst:
        for i in range(len(trStartPoints)):
            if i == 0 and trStartPoints[i] != 0:
                # If the first element is not 0 (i.e. T&R right at the
                # start), this is discard text.
                discardTextBlocks.append(text[:trStartPoints[i]])
            # Append each textBlock
            new_desc = text[trStartPoints[i]:]
            if i + 1 != len(trStartPoints):
                new_desc = text[trStartPoints[i]:trStartPoints[i + 1]]
            trTextBlocks.append((trList.pop(0), cleanup_desc(new_desc)))

    else:
        for i in range(len(trEndPoints)):
            if i + 1 == len(trEndPoints) and trEndPoints[i] != len(text):
                # If the last element is not the final character in the
                # string (i.e. T&R ends at text end), discard text
                discardTextBlocks.append(text[trEndPoints[i]:])
            # Append each textBlock
            new_desc = text[:trEndPoints[i]]
            if i != 0:
                new_desc = text[trEndPoints[i - 1]:trEndPoints[i]]
            trTextBlocks.append((trList.pop(0), cleanup_desc(new_desc)))

    return trTextBlocks, discardTextBlocks


def findall_matching_sec(text, layout=None, requireColon='default_colon'):
    """
    INTERNAL USE:

    Pull from the text all sections and 'multi-sections' that are
    appropriate to the description layout. Returns a ParseBag object
    with ad-hoc attributes `.secList` and `.multiSecList`.
    :param requireColon: Same effect as in PLSSDesc.parse()`
    """

    # requireColon=True will pass over sections that are NOT followed by
    # colons, in the TRS_desc and S_desc_TR layouts. For this version,
    # it is defaulted to True for those layouts. However, if no
    # satisfactory section or multiSec is found during the first pass,
    # it will rerun self.parse() with requireColon='second_pass'.
    # Feeding requireColon=True as a kwarg will override allowing the
    # second pass.

    # Note: the kwarg requireColon= accepts either a string (for
    # 'default_colon' and 'second_pass') or bool. If a bool is fed in
    # (i.e. requireColon=True), a 'second_pass' will NOT be allowed.
    # requireColonBool is the actual variable that controls the relevant
    # logic throughout.
    # Note also: Future versions COULD conceivably compare the
    # first_pass and second_pass results to see which has more secErr's
    # or other types of errors, and use the less-flawed of the two...
    # But I'm not sure that would actually be better...

    # Lastly, note that `requireColonBool` has no effect on layouts
    # other than TRS_desc and S_desc_TR, even if set to `True`

    if isinstance(requireColon, bool):
        requireColonBool = requireColon
    elif requireColon == 'second_pass':
        requireColonBool = False
    else:
        requireColonBool = True

    secPB = ParseBag(parentType='PLSSDesc')

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

    if layout not in __implementedLayouts__:
        layout = PLSSDesc.deduce_segment_layout(text=text)

    def adj_secmo_end(sec_mo):
        """
        If a sec_mo or multiSec_mo ends in whitespace, give the
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

        # For TRS_desc and S_desc_TR layouts specifically, we do NOT want
        # to match sections following "of", "said", or "in" (e.g.
        # 'the NE/4 of Section 4'), because it very likely means its a
        # continuation of the same description.
        enders = (' of', ' said', ' in', ' within')
        if (layout in ['TRS_desc', 'S_desc_TR']) and \
                text[:sec_mo.start()].rstrip().endswith(enders):
            ruledOut = True

        # Also for TRS_desc and S_desc_TR layouts, we ONLY want to match
        # sections and multi-Sections that are followed by a colon (if
        # requiredColonBool == True):
        if (requireColonBool) and (layout in ['TRS_desc', 'S_desc_TR']) and \
                not (sec_ends_with_colon(sec_mo)):
            ruledOut = True

        if ruledOut:
            # Move our index to the end of this sec_mo and move to the next pass
            # through this loop, because we don't want to include this sec_mo.
            i = sec_mo.end()

            # Create a warning flag, that we did not pull this section or
            # multiSec and move on to the next loop.
            ignoredSec = compile_sec_mo(sec_mo)
            if isinstance(ignoredSec, list):
                flag = 'multiSec_not_pulled<%s>' % ', '.join(ignoredSec)
            else:
                flag = 'sec_not_pulled<%s>' % ignoredSec
            secPB.wFlagList.append(flag)
            secPB.wFlagLines.append((flag, sec_mo.group()))
            continue

        # Move the parsing index forward to the start of this next matched Sec
        i = sec_mo.start()

        # If we've gotten to here, then we've found a section or multiSec
        # that we want. Determine which it is, and append it to the respective
        # list:
        if is_multisec(sec_mo):
            # If it's a multiSec, unpack it, and append it to the wMultiSecList.
            multiSecParseBagObj = unpack_sections(sec_mo.group())
            # Pull out the secList.
            unpackedMultiSec = multiSecParseBagObj.secList

            # First create a flag in the bigPB
            flag = 'multiSec_found<%s>' % ', '.join(unpackedMultiSec)
            secPB.wFlagList.append(flag)
            secPB.wFlagLines.append((flag, sec_mo.group()))

            # Then absorb the multiSecParseBagObj into the bigPB
            secPB.absorb(multiSecParseBagObj)

            # And finally append the tuple for this multiSec
            wMultiSecList.append((unpackedMultiSec, i, adj_secmo_end(sec_mo)))
        else:
            # Append the tuple for this individual section
            wSecList.append((compile_sec_mo(sec_mo), i, adj_secmo_end(sec_mo)))

        # And move the parser index to the end of our current sec_mo
        i = sec_mo.end()

    # If we're in either 'TRS_desc' or 'S_desc_TR' layouts and discovered
    # neither a standalone section nor a multiSec, then rerun
    # findall_matching_sec() under the same kwargs, except with
    # requireColon='second_pass' (which sets requireColonBool=False),
    # to see if we can capture a section after all.
    # Will return those results instead.
    do_second_pass = True
    if layout not in ['TRS_desc', 'S_desc_TR']:
        do_second_pass = False
    if len(wSecList) > 0 or len(wMultiSecList) > 0:
        do_second_pass = False
    if requireColon != 'default_colon':
        do_second_pass = False
    if do_second_pass:
        pass2_PB = findall_matching_sec(
            text, layout=layout, requireColon='second_pass')
        if len(pass2_PB.secList) > 0 or len(pass2_PB.multiSecList) > 0:
            pass2_PB.wFlagList.append('pulled_sec_without_colon')
        return pass2_PB

    # Ad-hoc attributes for `secList` and `multiSecList`:
    secPB.secList = wSecList
    secPB.multiSecList = wMultiSecList
    return secPB


def parse_segment(
        textBlock, layout=None, cleanUp=None, requireColon='default_colon',
        handedDownConfig=None, initParseQQ=False, cleanQQ=None):
    """
    INTERNAL USE:

    Parse a segment of text into pyTRS.Tract objects. Returns a
    pyTRS.ParseBag object.

    :param textBlock: The text to be parsed.
    :param layout: The layout to be assumed. If not specified,
    will be deduced.
    :param cleanUp: Whether to clean up common 'artefacts' from
    parsing. If not specified, defaults to False for parsing the
    'copy_all' layout, and `True` for all others.
    :param initParseQQ: Whether to parse each resulting Tract object
    into lots and QQs when initialized. Defaults to False.
    :param cleanQQ: Whether to expect only clean lots and QQ's (i.e.
    no metes-and-bounds, exceptions, complicated descriptions,
    etc.). Defaults to False.
    :param requireColon: Whether to require a colon between the
    section number and the following description (only has an effect
    on 'TRS_desc' or 'S_desc_TR' layouts).
    If not specified, it will default to a 'two-pass' method, where
    first it will require the colon; and if no matching sections are
    found, it will do a second pass where colons are not required.
    Setting as `True` or `False` here prevent the two-pass method.
        ex: 'Section 14 NE/4'
            `requireColon=True` --> no match
            `requireColon=False` --> match (but beware false
                positives)
            <not specified> --> no match on first pass; if no other
                        sections are identified, will be matched on
                        second pass.
    :param handedDownConfig: A Config object to be passed to any Tract
    object that is created, so that they are configured identically to
    a parent PLSSDesc object (if any). Defaults to None.
    :return: a pyTRS.ParseBag object with the parsed data.
    """

    ####################################################################
    # General explanation of how this function works:
    # 1) Lock down parameters for parse via kwargs, etc.
    # 2) If the layout was not appropriately specified, deduce it with
    #       `PLSSDesc.deduceSegment()`
    # 3) Based on the layout, pull each of the T&R's that match our
    #       layout (for segmented parse, /should/ only be one), with
    #       `findall_matching_tr()` function.
    # 4) Based on the layout, pull each of the Sections and
    #       Multi-Sections that match our layout with
    #       `findall_matching_sec()` function.
    # 5) Combine all of the positions of starts/ends of T&R's, Sections,
    #       and Multisections into a single dict.
    # 6) Based on layout, apply the appropriate algorithm for breaking
    #       down the text. Each algorithm decides where to break the
    #       text apart based on section location, T&R location, etc.
    #       (e.g., by definition, 'TR_desc_S' and 'desc_STR' both pull
    #       the description block from BEFORE an identified section;
    #       whereas 'S_desc_TR' and 'TRS_desc' both pull description
    #       block /after/ the section).
    # 6a) For 'copy_all' specifically, the entire textBlock will be
    #       copied as the `.desc` attribute of a Tract object.
    # 7) If no Tract was created by the end of the parse (e.g., no
    #       matching T&R found, or no section/multiSec found), then it
    #       will rerun this function using 'copy_all' layout, which will
    #       result in an error flag, but will capture the text as a
    #       Tract. In that case, either the parsing algorithm can't
    #       handle an apparent edge case, or the input is flawed.
    ####################################################################

    if layout not in __implementedLayouts__:
        layout = PLSSDesc.deduce_segment_layout(textBlock)

    segParseBag = ParseBag(parentType='PLSSDesc')

    # If `cleanQQ` was specified, convert it to a string, and set it to the
    # `handedDownConfig`.
    handedDownConfig = Config(handedDownConfig)
    if isinstance(cleanQQ, bool):
        handedDownConfig.set_str_to_values(f"cleanQQ.{cleanQQ}")

    if not isinstance(cleanUp, bool):
        # if cleanUp has not been specified as a bool, then use these defaults:
        if layout in ['TRS_desc', 'desc_STR', 'S_desc_TR', 'TR_desc_S']:
            cleanUp = True
        else:
            cleanUp = False

    def clean_as_needed(candidateText):
        """
        Will return either `candidateText` (a string for the .desc
        attribute of a `Tract` object that is about to be created) or the
        cleaned-up version of it, depending on the bool `cleanUp`.
        """
        if cleanUp:
            return cleanup_desc(candidateText)
        else:
            return candidateText

    # Find matching TR's that are appropriate to our layout (should only
    # be one, due to segmentation):
    trPB = findall_matching_tr(textBlock)
    # Pull the ad-hoc `.trPosList` attribute from the ParseBag object,
    # and absorb the rest of the data into segParseBag:
    wTRList = trPB.trPosList
    segParseBag.absorb(trPB)

    # Find matching Sections and MultiSections that are appropriate to
    # our layout (could be any number):
    secPB = findall_matching_sec(textBlock, requireColon=requireColon)
    # Pull the ad-hoc `.secList` and `.multiSecList` attributes from the
    # ParseBag object, and absorb the rest of the data into segParseBag:
    wSecList = secPB.secList
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
    markersDict[len(textBlock)] = 'text_end'

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

    # If we're in either 'TRS_desc' or 'S_desc_TR' layouts and discovered
    # neither a standalone section nor a multiSec, then rerun the parse
    # under the same kwargs, except with requireColon='second_pass' (which
    # sets requireColonBool=False), to see if we can capture a section after
    # all. Will return those results instead:
    do_second_pass = True
    if layout not in ['TRS_desc', 'S_desc_TR']:
        do_second_pass = False
    if len(working_sec_list) > 0 or len(working_multiSec_list) > 0:
        do_second_pass = False
    if requireColon != 'default_colon':
        do_second_pass = False
    if do_second_pass:
        replacementMidPB = parse_segment(
            textBlock=textBlock, layout=layout, requireColon='second_pass',
            handedDownConfig=handedDownConfig, initParseQQ=initParseQQ)
        TRS_found = replacementMidPB.parsedTracts[0].trs is not None
        if TRS_found:
            # If THIS time we successfully found a TRS, flag that we ran
            # it without requiring colon...
            replacementMidPB.wFlagList.append('pulled_sec_without_colon')
            for trObj in replacementMidPB.parsedTracts:
                trObj.wFlagList.append('pulled_sec_without_colon')
            # TODO: Note, this may not get applied to all Tract objects
            #   in the entire .parsedTracts TractList.
        return replacementMidPB

    # Get a list of all of the keys, then sort them, so that we're pulling
    # first-to-last (vis-a-vis the original text of this segment):
    mrkrsLst = list(markersDict.keys())
    mrkrsLst.sort()  # We sort the keys, so that we're pulling first-to-last.

    def new_tract(textForNewDesc, sec='default_sec', tr='default_tr') -> Tract:
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
            desc=textForNewDesc, trs=tr + sec, config=handedDownConfig,
            initParseQQ=initParseQQ)

    def flag_unused(unusedText, context):
        """
        Create a warning flag and flagLine for unused text.
        """
        segParseBag.wFlagList.append(f"Unused_desc_<{unusedText}>")
        segParseBag.wFlagLines.append((f"Unused_desc_<{unusedText}>", context))

    if layout in ['desc_STR', 'TR_desc_S']:
        # These two layouts are handled nearly identically, except that
        # in 'desc_STR' the TR is popped before it's encountered, and in
        # 'TR_desc_S' it's popped only when encountered. So setting
        # initial TR is the only difference.

        # Defaults to a T&R error.
        working_tr = 'TRerr_'

        # For TR_desc_S, will pop the working_tr when we encounter the
        # first TR. However, for desc_STR, need to pre-set our working_tr
        # (if one is available):
        if layout == 'desc_STR' and len(working_tr_list) > 0:
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
                        textBlock[mrkrsLst[i]:mrkrsLst[i + 1]].strip()))
                segParseBag.parsedTracts.append(TractObj)
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
                            textBlock[mrkrsLst[i]:mrkrsLst[i + 1]].strip()),
                        sec)
                    segParseBag.parsedTracts.append(TractObj)
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
                        textBlock[secErrorWriteBackToPos:mrkrsLst[i + 1]].strip()),
                    'secError')
                segParseBag.parsedTracts.append(TractObj)

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
                        and markerPos != len(textBlock):
                    # Whenever we come across a Section end, the next thing must
                    # be either a sec_start, multiSec_start, or tr_start.
                    # Hence the warning flag, if that's not true:
                    unusedText = textBlock[mrkrsLst[i]:mrkrsLst[i + 1]].strip()
                    segParseBag.wFlagList.append('Unused_desc_<%s>' % unusedText)

            elif markerType == 'text_end':
                break

            # Capture unused text at the end of the string.
            if layout == 'TR_desc_S' \
                    and markerType in ['sec_end', 'multiSec_end'] \
                    and not finalRun \
                    and nextMarkerType not in ['sec_start', 'tr_start', 'multiSec_start']:
                # For TR_desc_S, whenever we come across the end of a Section or
                # multi-Section, the next thing must be either a sec_start,
                # multiSec_start, or tr_start. Hence the warning flag, if that's
                # not true:
                unusedText = textBlock[mrkrsLst[i]:mrkrsLst[i + 1]].strip()
                flag_unused(unusedText, textBlock[lastMarkerPos:nextMarkerPos])

            # Capture unused text at the end of a section/multiSec (if appropriate).
            if layout == 'desc_STR' \
                    and markerType in ['sec_end', 'multiSec_end'] \
                    and not finalRun \
                    and nextMarkerType not in ['sec_start', 'multiSec_start']:
                unusedText = textBlock[markerPos:nextMarkerPos]
                if len(cleanup_desc(unusedText)) > 3:
                    flag_unused(
                        unusedText, textBlock[lastMarkerPos:nextMarkerPos])

    if layout == 'S_desc_TR':
        # TODO: Can probably cut out a lot of lines of code by combining
        #   'S_desc_TR' and 'TRS_desc' parsing, and just handling how
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
                        textBlock[mrkrsLst[i]:mrkrsLst[i + 1]].strip()))
                segParseBag.parsedTracts.append(TractObj)

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
                            textBlock[mrkrsLst[i]:mrkrsLst[i + 1]].strip()),
                        sec)
                    segParseBag.parsedTracts.append(TractObj)

            elif markerType == 'tr_start':  # Pull the next T&R in our list
                if len(working_tr_list) == 0:
                    # Will cause a TR error if another TRS+Desc is created:
                    working_tr = 'TRerr_'
                else:
                    working_tr = working_tr_list.pop(0)

            elif markerType == 'tr_end':
                # The only effect 'tr_end' has on this layout is checking
                # for unused text.
                unusedText = textBlock[markerPos:nextMarkerPos]
                if len(unusedText.strip()) > 2:
                    flag_unused(
                        unusedText, textBlock[lastMarkerPos:nextMarkerPos])

    if layout == 'copy_all':
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
        TractObj = new_tract(textBlock)
        segParseBag.parsedTracts.append(TractObj)

    if layout == 'TRS_desc':

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
                # TRS_desc layout. Move on to next.
                pass

            elif markerType == 'tr_start':
                # Pull the next T&R in our list
                if lastMarkerType == 'tr_end':
                    segParseBag.eFlagList.append('Unused_TR<%s>' % working_tr)
                working_tr = working_tr_list.pop(0)

            elif markerType == 'tr_end':
                # The only effect 'tr_end' has on this layout is checking
                # for unused text.
                unusedText = textBlock[markerPos:nextMarkerPos]
                if len(unusedText.strip()) > 2:
                    flag_unused(
                        unusedText, textBlock[lastMarkerPos:nextMarkerPos])

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
                    clean_as_needed(textBlock[markerPos:nextMarkerPos].strip()))
                segParseBag.parsedTracts.append(TractObj)

            elif markerType == 'multiSec_end':
                # Create a series of new TractObjs, compiling our current
                # working_tr and elements from working_multiSec into a series
                # of TRS, with the desc for EACH being the text between this
                # marker and the next.
                for sec in working_multiSec:
                    TractObj = new_tract(
                        clean_as_needed(textBlock[markerPos:nextMarkerPos].strip()), sec)
                    segParseBag.parsedTracts.append(TractObj)

            elif markerType == 'text_end':
                break

    if len(segParseBag.parsedTracts) == 0:
        # If we identified no Tracts in this segment, re-parse using
        # 'copy_all' layout.
        replacementPB = parse_segment(
            textBlock, layout='copy_all', cleanUp=False, requireColon=False,
            handedDownConfig=handedDownConfig, initParseQQ=initParseQQ,
            cleanQQ=cleanQQ)
        return replacementPB

    return segParseBag


def cleanup_desc(text):
    """
    INTERNAL USE:
    Clean up common 'artifacts' from parsing--especially layouts other
    than 'TRS_desc'. (Intended to be run only on post-parsing .desc
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


def find_tr(text, defaultNS='n', defaultEW='w'):
    """
    Returns a list of all T&R's in the text (formatted as '000n000w',
    or with fewer digits as needed).
    """

    # search the PLSS description for all T&R's
    twprge_mo_iter = twprge_regex.finditer(text)
    tr_list = []

    # For each match, compile a clean T&R and append it.
    for twprge_mo in twprge_mo_iter:
        tr_list.append(compile_tr_mo(twprge_mo))
    return tr_list


def ocr_scrub_alpha_to_num(text):
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


def preprocess_tr_mo(tr_mo, defaultNS='n', defaultEW='w') -> str:
    """
    INTERNAL USE:
    Take a T&R match object (tr_mo) and check for missing 'T', 'R', and
    and if N/S and E/W are filled in. Will fill in any missing elements
    (using defaultNS and defaultEW as necessary) and outputs a string in
    the format T000N-R000W (or fewer digits for twp & rge), which is to
    be swapped into the source text where the tr_mo was originally
    matched, in order to clean up the ppDesc.
    """

    clean_tr = compile_tr_mo(tr_mo, defaultNS=defaultNS, defaultEW=defaultEW)
    twp, ns, rge, ew = decompile_twprge(clean_tr)

    # Maintain the first character, if it's a whitespace:
    if tr_mo.group().startswith(('\n', '\t', ' ')):
        first = tr_mo.group()[0]
    else:
        first = ''

    twp = ocr_scrub_alpha_to_num(twp)  # twp number
    rge = ocr_scrub_alpha_to_num(rge)  # rge number

    # Maintain the last character, if it's a whitespace.
    if tr_mo.group().endswith(('\n', '\t', ' ')):
        last = tr_mo.group()[-1]
    else:
        last = ''

    output_ppTR = first + 'T' + twp + ns.upper() + '-R' + rge + ew.upper() + last
    return output_ppTR


def decompile_twprge(tr_string) -> tuple:
    """
    Take a compiled T&R (format '000n000w', or fewer digits) and break
    it into four elements, returned as a 4-tuple:
    (Twp number, Twp direction, Rge number, Rge direction)
        NOTE: If Twp and Rge are each 'TRerr', will return
            ('TRerr', None, 'TRerr', None).
        ex: '154n97w'   -> ('154', 'n', '97', 'w')
        ex: 'TRerr'     -> ('TRerr', None, 'TRerr', None)"""
    twp, rge, _ = break_trs(tr_string)
    twp_dir = None
    rge_dir = None
    if twp != 'TRerr':
        twp_dir = twp[-1]
        twp = twp[:-1]
    if rge != 'TRerr':
        rge_dir = rge[-1]
        rge = rge[:-1]

    return (twp, twp_dir, rge, rge_dir)


def compile_tr_mo(mo, defaultNS='n', defaultEW='w'):
    """
    INTERNAL USE:
    Take a match object (`mo`) of an identified T&R, and return a string
    in the format of '000n000w' (i.e. between 1 and 3 digits for
    township and for range numbers).
    """

    twpNum = mo[2]
    # Clean up any leading '0's in twpNum.
    # (Try/except is used to handle twprge_ocrScrub_regex mo's, which
    # can contain alpha characters in `twpNum`.)
    try:
        twpNum = str(int(twpNum))
    except:
        pass

    # if mo[4] is None:
    if mo.group(3) == '':
        ns = defaultNS
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

    ### Clean up any leading '0's in rgeNum.
    # (Try/except is used to handle twprge_ocrScrub_regex mo's, which
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
                ew = defaultEW
            else:
                ew = mo[7][0].lower()
        else:
            ew = mo[13][0].lower()
    else:
        if mo[7] in ['', None]:
            ew = defaultEW
        else:
            ew = mo[7][0].lower()

    return twpNum + ns + rgeNum + ew


def compile_sec_mo(sec_mo):
    """
    INTERNAL USE
    Takes a match object (mo) of an identified multiSection, and
    returns a string in the format of '00' for individual sections and a
    list ['01', '02', ...] for multiSections
    """
    if is_multisec(sec_mo):
        multiSecParseBagObj = unpack_sections(sec_mo.group())
        return multiSecParseBagObj.secList  # Pull out the secList
    elif is_singlesec(sec_mo):
        return get_last_sec(sec_mo).rjust(2, '0')
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
        multiSecParseBagObj = unpack_sections(multiSec)
        workingSecList = multiSecParseBagObj.secList
        if len(workingSecList) == 1:
            # skip any single-section matches
            continue
        unpackedMultiSec_list.append(workingSecList)

    if flat:
        unpackedMultiSec_list = flatten(unpackedMultiSec_list)

    return unpackedMultiSec_list


def unpack_sections(secTextBlock):
    """
    INTERNAL USE:
    Feed in a string of a multiSec_regex match object, and return a
    ParseBag object with a .secList attribute containing all of the
    sections (i.e. 'Sections 2, 3, 9 - 11' will return ParseBag whose
    .secList contains ['02', '03', '09', '10', 11'].
    """

    # TODO: Maybe just put together a simpler algorithm. Since there's
    #   so much less possible text in a list of Sections, can probably
    #   just add from left-to-right, unlike unpack_lots.

    multiSecParseBag = ParseBag(parentType='multiSec')

    sectionsList = []  #
    remainingSecText = secTextBlock

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
            secNum = get_last_sec(secs_mo)

            if is_singlesec(secs_mo):
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
                    multiSecParseBag.wFlagList.append('nonSequen_sec')
                    multiSecParseBag.wFlagLines.append(
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
                        multiSecParseBag.wFlagList.append(f'dup_sec<{addSec}>')
                        multiSecParseBag.wFlagLines.append(
                            (f'dup_sec<{addSec}>', f'Section {addSec}'))
                    wSectionsList.append(addSec)
                foundThrough = False  # Reset the foundThrough.

            else:
                # Otherwise, if it's a standalone section (not the start
                #   of an elided list), we add it.
                # We check this new section to see if it's in EITHER
                #   sectionsList OR wSectionsList:
                if newSec in sectionsList or newSec in wSectionsList:
                    multiSecParseBag.wFlagList.append('dup_sec')
                    multiSecParseBag.wFlagLines.append(
                        ('dup_sec', f'Section {newSec}'))
                wSectionsList.append(newSec)

            # If we identified at least two sections, we need to check
            # if the last one is the end of an elided list:
            if is_multisec(secs_mo):
                thru_mo = through_regex.search(secs_mo.group(6))
                # Check if we find 'through' (or equivalent symbol or
                # abbreviation) before this final section:
                if thru_mo is None:
                    foundThrough = False
                else:
                    foundThrough = True
    wSectionsList.reverse()
    multiSecParseBag.secList = wSectionsList

    return multiSecParseBag


########################################################################
# Tools for interpreting multiSec_regex match objects:
########################################################################

def is_multisec(multiSec_mo) -> bool:
    """
    INTERNAL USE:
    Determine whether a multiSec_regex match object is a multiSec.
    """
    return multiSec_mo.group(12) is not None


def is_singlesec(multiSec_mo) -> bool:
    """
    INTERNAL USE:
    Determine whether a multiSec_regex match object is a single section.
    """
    return (multiSec_mo.group(12) is None) and (multiSec_mo.group(5) is not None)


def get_last_sec(multiSec_mo) -> str:
    """
    INTERNAL USE:
    Extract the right-most section in a multiSec_regex match object.
    Returns None if no match.
    """
    if is_multisec(multiSec_mo):
        return multiSec_mo.group(12)
    elif is_singlesec(multiSec_mo):
        return multiSec_mo.group(5)
    else:
        return None


def is_plural_singlesec(multiSec_mo) -> bool:
    """
    INTERNAL USE:
    Determine if a multiSec_regex match object is a single section
    but pluralized (ex. 'Sections 14: ...').
    """
    # Only a single section in this match...
    # But there's a plural "Sections" anyway!
    if is_singlesec(multiSec_mo) and multiSec_mo.group(4) is not None:
        return multiSec_mo.group(4).lower() == 's'
    else:
        return False


def sec_ends_with_colon(multiSec_mo) -> bool:
    """
    INTERNAL USE:
    Determine whether a multiSec_regex match object ends with a colon.
    """
    return multiSec_mo.group(13) == ':'


########################################################################
# Tools for Tract.parse():
########################################################################

def scrub_aliquots(text, cleanQQ=False) -> str:
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

        # `rd` (i.e. regexDict) stores what should be replaced by
        # matches of the specific regex_run. (Done this way to not
        # overwrite the leading character, if any, which is technically
        # part of a match of each regex--which is part of the regexes to
        # rule out false matches.)
        rd = {
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

        remainingText = text
        rebuilt_text = ''
        while True:
            mo = regex_run.search(remainingText)
            if mo is None:  # If we found no more matches like this.
                rebuilt_text = rebuilt_text + remainingText
                break
            rebuilt_text = rebuilt_text + remainingText[:mo.start(2)] + rd[regex_run]
            remainingText = remainingText[mo.end():]
        return rebuilt_text

    # We'll run these scrubber regexes on the text:
    scrubber_rgxs = [
        NE_regex, NW_regex, SE_regex, SW_regex, N2_regex, S2_regex,
        E2_regex, W2_regex
    ]

    # If the user has specified that the input data is clean (i.e. no
    # metes-and-bounds tracts, etc.), then broader regexes can also be applied.
    if cleanQQ:
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


def unpack_aliquots(aliqTextBlock) -> list:
    """
    INTERNAL USE:
    Convert an aliquot with fraction symbols into a list of clean
    QQs. Returns a list of QQ's (or smaller, if applicable):
        'N½SW¼NE¼' -> ['N2SWNE']
        'N½SW¼' -> ['NESW', 'NWSW']

    NOTE: Input a single aliqTextBlock (i.e. feed only 'N½SW¼NE¼', even
    if we have a larger list of ['N½SW¼NE¼', 'NW¼'] to process).
    """

    # To do this, we break down an aliqTextBlock into its smaller
    # components (if any), and place them all in a nested list (each
    # deeper level of the nested list is another division of the level
    # above it). Then we call rebuild_aliquots() on that nested list to
    # rebuild the components appropriately and return a flattened list
    # of aliquots, sized QQ and smaller.

    def rebuild_aliquots(aliqNestedList) -> list:
        """A nested list of aliquot components is returned as a flattened
        list of rebuilt aliquots."""

        # The S/2S/2N/2 should be fed in as
        #       ['NE', 'NW', ['SE','SW', ['S2']]]
        #   and will return:
        #       ['S2SENE', 'S2SWNE', 'S2SENW', 'S2SENW']
        # Similarly, the E/2SW/4NE/4 can be fed in as
        #       ['NE', ['SW', ['E2']]]
        #   and will spit out
        #       ['E2SWNE']

        moveUpList = []
        if not isinstance(aliqNestedList[-1], list):
        # We've hit the final list.
            return aliqNestedList

        else:  # if there are more lists...
            if isinstance(aliqNestedList[:-1], str):
                match_to_list = [aliqNestedList[0]]
            else:
                match_to_list = aliqNestedList[:-1]
            next_list = rebuild_aliquots(aliqNestedList[-1])
            for match_to_string in match_to_list:
                for element in next_list:
                    wAliquot = element + match_to_string
                    moveUpList.append(wAliquot)
            return moveUpList

    # Get a list of the component parts of the aliquot string, in
    # reverse -- i.e. 'N½SW¼NE¼' becomes ['NE', 'SW', 'N']
    remainingAliqText = aliqTextBlock

    # list of component parts of the aliquot, from last-to-first
    # -- ex. ['NE', 'SW', 'N']
    # Note that componentList is a flat list (NOT nested).
    componentList = []

    while True:
        aliq_mo = aliquot_unpacker_regex.search(remainingAliqText)
        if aliq_mo is None:
            if remainingAliqText.lower() == 'all':
                componentList.append('ALL')
            break

        # Quick explanation of the relevant regex match object groups:
        # group(8) will be the rightmost component, so long as it is a
        # quarter (e.g. 'NE' in 'E½NE¼')  If not, group(8) it will be
        # None. In that case, the rightmost component will be a half
        # (e.g., 'E½' in 'W½E½') and will be in group(6).

        # mainAliq is intended to be the rightmost component.
        mainAliq = aliq_mo.group(8)
        if aliq_mo.group(8) is None:
            mainAliq = aliq_mo.group(6)
            # Cut off the last component to rerun the loop:
            remainingAliqText = remainingAliqText[:aliq_mo.start(6)]
        else:
            # Cut off the last component to rerun the loop:
            remainingAliqText = remainingAliqText[:aliq_mo.start(8)]
        # Cut off the half fraction from 'E½', for example:
        mainAliq = mainAliq.replace('½', '')
        componentList.append(mainAliq)

    componentList.reverse()

    # (Remember that the componentList is ordered last-to-first
    # vis-a-vis the original aliquot string.)
    numComponents = len(componentList)

    if numComponents == 1:
        # If this is the only component, we break it into QQs and call it good.

        # Could do this more elegantly, but the possible inputs are so limited,
        # that there's no reason to complicate it.
        component = componentList[0]
        if component == 'N':
            QQList = ['NENE', 'NWNE', 'SENE', 'SWNE',
                      'NENW', 'NWNW', 'SENW', 'SWNW']
        elif component == 'S':
            QQList = ['NESE', 'NWSE', 'SESE', 'SWSE',
                      'NESW', 'NWSW', 'SESW', 'SWSW']
        elif component == 'E':
            QQList = ['NENE', 'NWNE', 'SENE', 'SWNE',
                      'NESE', 'NWSE', 'SESE', 'SWSE']
        elif component == 'W':
            QQList = ['NENW', 'NWNW', 'SENW', 'SWNW',
                      'NESW', 'NWSW', 'SESW', 'SWSW']
        elif component == 'NE':
            QQList = ['NENE', 'NWNE', 'SENE', 'SWNE']
        elif component == 'NW':
            QQList = ['NENW', 'NWNW', 'SENW', 'SWNW']
        elif component == 'SE':
            QQList = ['NESE', 'NWSE', 'SESE', 'SWSE']
        elif component == 'SW':
            QQList = ['NESW', 'NWSW', 'SESW', 'SWSW']
        elif component == 'ALL':
            # NOTE: 'ALL' assumes a standard section consisting of
            # 16 QQ's and no lots. This may not be accurate for all sections.
            # TODO: wFlag stating the assumption that 'ALL' became 16 QQ's.
            QQList = ['NENE', 'NWNE', 'SENE', 'SWNE',
                      'NENW', 'NWNW', 'SENW', 'SWNW',
                      'NESE', 'NWSE', 'SESE', 'SWSE',
                      'NESW', 'NWSW', 'SESW', 'SWSW']
        else:
            # It should never get to this point, but here's a stopgap
            QQList = []
        # This is as deep as we need to go for single-component aliquot
        # strings, so return now.
        return QQList

    # But if there's more than one component, we have to convert the flat
    # componentList into a nested list (mainList), then run
    # rebuild_aliquots() on it.

    # A list, to be passed through rebuild_aliquots(), which will return QQ's:
    mainList = []
    for i in range(numComponents):
        component = componentList[i]

        # The final component -- i.e. the 'NW' from 'E2NW',
        # previously stored in ['NW', 'E']:
        if i == numComponents - 1:
            if component == 'N':
                attachList = ['NE', 'NW']
            elif component == 'S':
                attachList = ['SE', 'SW']
            elif component == 'E':
                attachList = ['NE', 'SE']
            elif component == 'W':
                attachList = ['NW', 'SW']
            else:
                attachList = [component]

        # For the second-to-last component -- i.e. the 'E' from 'E2NW',
        # previously stored in ['NW', 'E']:
        elif i == numComponents - 2:
            if component == 'N':
                attachList = ['NE', 'NW']
            elif component == 'S':
                attachList = ['SE', 'SW']
            elif component == 'E':
                attachList = ['NE', 'SE']
            elif component == 'W':
                attachList = ['NW', 'SW']
            else:
                attachList = [component]

        # For any components deeper than the second (i.e. either 'N'
        # in 'N2N2S2NE'), we can pass them through:
        else:
            if len(component) == 1:
                # If it's a half call, add a '2' to the end of it, for
                # clean appearance (i.e. so it might be 'N2N2NENW'
                # instead of 'NNNENW')
                component = component + '2'
            attachList = [component]

        moveDownList = []
        for comp in attachList:
            moveDownList.append(comp)
        if len(mainList) > 0:
            # Unless this is the first loop through, nest the mainList
            # at the end of moveDownList.
            moveDownList.append(mainList)
        # And set the mainList to the moveDownList.
        mainList = moveDownList

    # And last, convert this nested list to QQ's by calling rebuild_aliquots()
    QQList = rebuild_aliquots(mainList)
    return QQList


def unpack_lots(lotTextBlock, includeLotDivs=True):
    """
    INTERNAL USE:
    Feed in a string of a lot_regex match object, and return a ParseBag
    object with .lotList and .lotAcres attributes for all of the lots --

    ex:  'Lot 1(39.80), 2(30.22)'
        -> ParseBag_obj.lotList --> ['L1', 'L2']
        -> ParseBag_obj.lotAcres --> {'L1' : '39.80', 'L2' : '30.22'}
    """

    lotsParseBag = ParseBag(parentType='lotText')

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
    remainingLotsText = lotTextBlock

    while True:
        lots_mo = lot_regex.search(remainingLotsText)

        if lots_mo is None:  # we're out of lot numbers.
            break

        else:
            # We still have at least one lot to unpack.

            # Pull the right-most lot number (as a string):
            lotNum = get_last_lot(lots_mo)

            if is_single_lot(lots_mo):
                # Skip the next loop after we've reached the left-most lot
                remainingLotsText = ''

            else:
                # If we've found at least two lots.
                remainingLotsText = remainingLotsText[:start_of_last_lot(lots_mo)]

            # Clean up any leading '0's in lotNum.
            lotNum = str(int(lotNum))
            if lotNum == '0':
                lotsParseBag.wFlagList.append('Lot0')

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
                    lotsParseBag.wFlagList.append('nonSequen_Lots')
                    lotsParseBag.wFlagLines.append(
                        ('nonSequen_Lots',
                         f"Lots {start_of_list} - {end_of_list}"))
                    correctOrder = False

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
            newAcres = get_lot_acres(lots_mo)
            if newAcres is not None:
                lotsAcresDict[newLot] = newAcres

            # If we identified at least two lots, we need to check if
            # the last one is the end of an elided list, by calling
            # thru_lot() to check for us:
            if is_multi_lot(lots_mo):
                foundThrough = thru_lot(lots_mo)

    # Reverse wLots, so that it's in the order it was in the original
    # description, and append it to our main list:
    wLots.reverse()
    lots.extend(wLots)

    if includeLotDivs:
        # If we want includeLotDivs, add it to the front of each parsed lot.
        leadingAliq = get_leading_aliq(
            lot_with_aliquot_regex.search(lotTextBlock))
        leadingAliq = leadingAliq.replace('¼', '')
        leadingAliq = leadingAliq.replace('½', '2')
        if leadingAliq != '':
            if first_lot_is_plural(lot_regex.search(lotTextBlock)):
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

    lotsParseBag.lotList = lots
    lotsParseBag.lotAcres = lotsAcresDict

    return lotsParseBag


########################################################################
# Misc. tools
########################################################################

def flatten(listOrTuple=None) -> list:
    """
    Unpack the elements in a nested list or tuple into a flattened list.
    """

    if listOrTuple is None:
        return []

    if not isinstance(listOrTuple, (list, tuple)):
        return [listOrTuple]
    else:
        flattened = []
        for element in listOrTuple:
            if not isinstance(element, (list, tuple)):
                flattened.append(element)
            else:
                flattened.extend(flatten(element))
    return flattened


def break_trs(trs : str) -> tuple:
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

def is_multi_lot(lots_mo) -> bool:
    """
    INTERNAL USE:
    Return a bool, whether a lot_regex match object is a multiLot.
    """
    try:
        return (lots_mo.group(11) is not None) and (lots_mo.group(19) is not None)
    except:
        return False


def thru_lot(lots_mo) -> bool:
    """
    INTERNAL USE:
    Return a bool, whether the word 'through' (or an abbreviation)
    appears before the right-most lot in a lot_regex match object.
    """

    try:
        if is_multi_lot(lots_mo):
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


def is_single_lot(lots_mo) -> bool:
    """
    INTERNAL USE:
    Return a bool, whether a lot_regex match object is a single lot.
    """
    try:
        return (lots_mo.group(11) is not None) and (lots_mo.group(19) is None)
    except:
        return False


def get_last_lot(lots_mo):
    """
    INTERNAL USE:
    Extract the right-most lot in a lot_regex match object. Returns a
    string if found; if none found, returns None.
    """
    try:
        if is_multi_lot(lots_mo):
            return lots_mo.group(19)
        elif is_single_lot(lots_mo):
            return lots_mo.group(11)
        else:
            return None
    except:
        return None


def start_of_last_lot(lots_mo) -> int:
    """
    INTERNAL USE:
    Return an int of the starting position of the right-most lot in a
    lot_regex match object. Returns None if none found.
    """
    try:
        if is_multi_lot(lots_mo):
            return lots_mo.start(19)
        elif is_single_lot(lots_mo):
            return lots_mo.start(11)
        else:
            return None
    except:
        return None


def get_lot_acres(lots_mo) -> str:
    """
    INTERNAL USE:
    Return the string of the lotAcres for the right-most lot, without
    parentheses. If no match, then returns None.
    """
    try:
        if is_multi_lot(lots_mo):
            if lots_mo.group(14) is None:
                return None
            else:
                lotAcres_mo = lotAcres_unpacker_regex.search(lots_mo.group(14))

        elif is_single_lot(lots_mo):
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


def first_lot_is_plural(lots_mo) -> bool:
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

def has_leading_aliq(mo) -> bool:
    """
    INTERNAL USE:
    Return a bool, whether this lot_with_aliquot_regex match object
    has a leading aliquot. Returns None if no match found.
    """
    try:
        return mo.group(1) is None
    except:
        return None


def get_leading_aliq(mo) -> str:
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


def get_lot_component(mo):
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


### Tools for extracting data from PLSSDesc and Tract objects

def clean_attributes(*attributes) -> list:
    """
    INTERNAL USE:
    Ensure that each element has been entered as a string.
    Returns a flattened list of strings.
    """
    attributes = flatten(attributes)

    if len(attributes) == 0:
        raise Exception('Specify at least one attribute as argument.')

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
        filepath, TractDescList : list, attributes : list, includeSource=True,
        resume=True, includeHeaders=True, unpackLists=False):
    """
    Write the requested Tract data to a .csv file. Each Tract will be on
    its own row--with multiple rows per PLSSDesc object, as necessary.

    :param filepath: Path to the output .csv file.
    :param TractDescList: A list of parsed PLSSDesc, Tract, and/or
    TractList objects.
    :param attributes: A list of the Tract attributes to extract and
    write.  ex: ['trs', 'desc', 'wFlagList']
    :param includeSource: Whether to include the `.source` attribute of
    each written Tract object as the first column. (Defaults to True)
    :param resume: Whether to overwrite an existing file if found
    (i.e. `resume=False`) or to continue writing at the end of it
    (`resume=True`). Defaults to True.
    NOTE: If no existing file is found, this will create a new file
    regardless of `resume`.
    NOTE ALSO: If resuming a previous output, but with different
    attributes (or differently ordered) than before, the columns will be
    misaligned.
    :param includeHeaders: Whether to write headers. Defaults to True.
    :param unpackLists: Whether to try to flatten and join lists, or
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
        includeHeaders = False

    # Default to opening in `write` mode (create new file). However...
    openMode = 'w'
    # If we don't want to create a new file, will open in `append` mode instead.
    if resume:
        openMode = 'a'

    csvFile = open(filepath, openMode, newline='')
    outputWriter = csv.writer(csvFile)

    if not isinstance(TractDescList, ACCEPTABLE_TYPES_PLUS):
        # If not the correct type, abort before writing any more.
        raise TypeError(
            f"TractDescList must be passed as one of: {ACCEPTABLE_TYPES_PLUS}; "
            f"passed as '{type(TractDescList)}'.")
    TractDescList = flatten(TractDescList)

    attributes = flatten(attributes)
    # Ensure the type of each attribute is a str
    attributes = [
        att if isinstance(att, str) else 'Attribute TypeError' for att in attributes
    ]
    if includeSource:
        # Mandate the inclusion of attribute 'source', unless overruled
        # with `includeSource=False`
        attributes.insert(0, 'source')

    if includeHeaders:
        # Write the attribute names as headers:
        outputWriter.writerow(attributes)

    for obj in TractDescList:
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
                if isinstance(data, (list, tuple)) and unpackLists:
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
