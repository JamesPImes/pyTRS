
"""
TRS class to represent a unique Twp/Rge/Sec combination.
"""


import re

from ..rgxlib import *
from ..unpack import ocr_scrub_alpha_to_num
from ..config import (
    MasterConfig,
    DefaultNSError,
    DefaultEWError,
)

MC = MasterConfig


def compile_trs_unpacker_regex(
        twp_rgx, err_twp, undef_twp, rge_rgx, err_rge, undef_rge,
        sec_rgx, err_sec, undef_sec):
    """
    INTERNAL USE:

    Compile the constants for Twp/Rge/Sec into a regex for unpacking
    strings in the pyTRS 'TRS' format.

    :return: A re.Pattern that will match pyTRS 'TRS' strings, including
    undefined and error Twp/Rge/Sections.

    :param twp_rgx: MasterConfig._TWP_RGX
    :param err_twp: MasterConfig._ERR_TWP
    :param undef_twp: MasterConfig._UNDEF_TWP
    :param rge_rgx: MasterConfig._RGE_RGX
    :param err_rge: MasterConfig._ERR_RGE
    :param undef_rge: MasterConfig._UNDEF_RGE
    :param sec_rgx: MasterConfig._SEC_RGX
    :param err_sec: MasterConfig._ERR_SEC
    :param undef_sec: MasterConfig._UNDEF_SEC
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


class TRS:
    """
    A container for Twp/Rge/Section in the standardized format.
    Automatically breaks the Twp/Rge/Sec down into its component parts,
    which can be accessed as properties -- and which are equivalent to
    properties in ``Tract`` objects::

        .trs        -> The full Twp/Rge/Sec combination.
        .twp        -> Twp number + direction (a str or None)
        .twp_num    -> Twp number (an int or None)
        .twp_ns     -> Twp direction ('n', 's', or None)
        .ns         -> same as `.twp_ns`
        .twp_undef  -> whether the Twp was undefined. (‡)
        .rge        -> Rge number + direction (a str or None)
        .rge_num    -> Rge num (an int or None)
        .rge_ew     -> Rge direction ('e', 'w', or None)
        .ew         -> same as `.rge_ew`
        .rge_undef  -> whether the Rge was undefined. (‡)
        .sec_num    -> Sec number (an int or None)
        .sec_undef  -> whether the Sec was undefined. (‡)

    .. note::

        ‡ Note that error parses do *not* qualify as 'undefined', but
        undefined and error values are both stored as ``None``.
        ``.twp_undef``, ``.rge_undef``, and ``.sec_undef`` are included
        to differentiate between error vs. undefined, in case that
        distinction is needed.

    .. note::
        Setting ``.trs`` will cause the other properties to be
        recalculated. (Optionally set the ``.trs`` using the separate
        Twp/Rge/Sec components with the ``.set_twprgesec()`` method.)
    """

    # Regex patterns for unpacking Twp/Rge/Sec
    _TWP_RGX = r"((?P<twp_num>\d{1,3})(?P<ns>[nsNS]))"
    _RGE_RGX = r"((?P<rge_num>\d{1,3})(?P<ew>[ewEW]))"
    _SEC_RGX = r"\d{2}"

    # Based on the above, compile the regex pattern for unpacking
    # Twp/Rge/Sec in this module.
    _TRS_UNPACKER_REGEX = compile_trs_unpacker_regex(
        twp_rgx=_TWP_RGX,
        err_twp=MC._ERR_TWP,
        undef_twp=MC._UNDEF_TWP,
        rge_rgx=_RGE_RGX,
        err_rge=MC._ERR_RGE,
        undef_rge=MC._UNDEF_RGE,
        sec_rgx=_SEC_RGX,
        err_sec=MC._ERR_SEC,
        undef_sec=MC._UNDEF_SEC
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

    def __init__(self, trs: str = None):
        if trs in ['', None]:
            trs = MC._UNDEF_TRS
        self.__trs_dict = None

        # Setting `.trs` attribute populates `.__trs_dict`, from which
        # twp, rge, twprge, sec, twp_num, twp_ns, rge_num, rge_ew, and
        # sec_num can be pulled (as properties)
        self.trs = trs

    def __str__(self):
        return self.trs

    def __repr__(self):
        return f"TRS<{self.trs!r}>"

    def __eq__(self, other):
        """
        A `TRS` object is equal to another object if that object is also
        a `TRS` object with an identical `.trs` attribute.
        """
        if not isinstance(other, TRS):
            return False
        return self.trs == other.trs

    def __hash__(self):
        return hash(self.trs)

    @property
    def trs(self):
        return self.__trs_dict['trs']

    @trs.setter
    def trs(self, new_trs):
        # If we've already broken down this trs into a dict, just
        # reuse it.
        self.__trs_dict = TRS.__CACHE.get(new_trs, None)
        if not self.__trs_dict:
            self.__trs_dict = TRS._cache_trs_to_dict(new_trs)

    @property
    def twp(self):
        return self.__trs_dict['twp']

    @property
    def twp_num(self):
        return self.__trs_dict['twp_num']

    @property
    def twp_ns(self):
        return self.__trs_dict['twp_ns']

    ns = twp_ns

    @property
    def rge(self):
        return self.__trs_dict['rge']

    @property
    def rge_num(self):
        return self.__trs_dict['rge_num']

    @property
    def rge_ew(self):
        return self.__trs_dict['rge_ew']

    ew = rge_ew

    @property
    def twprge(self):
        return f"{self.__trs_dict['twp']}{self.__trs_dict['rge']}"

    def pretty_twprge(
            self, t='T', delim='-', r='R', n=None, s=None, e=None, w=None,
            undef='---X'):
        """
        Convert the Twp/Rge info into a clean str. By default, will
        return in the format 'T154N-R97W', but control the output with
        the various optional parameters.

        :param t: How "Township" should appear. (``'T'`` by default)
        :param delim: How Twp should be separated from Rge. (``'-'`` by
         default)
        :param r: How "Range" should appear. (``'R'`` by default)
        :param n: How "North" (if found) should appear.
        :param s: How "South" (if found) should appear.
        :param e: How "East" (if found) should appear.
        :param w: How "West" (if found) should appear.
        :param undef: How undefined (or error) Twp or Rge should be
         represented, including the direction. (``'---X'`` by default)
        :return: A str of the clean Twp/Rge.
        """
        twp_num = self.twp_num
        rge_num = self.rge_num
        ns = self.ns
        ew = self.ew
        if not ns:
            ns = ''
        if not ew:
            ew = ''
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
        return self.__trs_dict['sec']

    @property
    def sec_num(self):
        return self.__trs_dict['sec_num']

    @property
    def twp_undef(self):
        return self.__trs_dict['twp_undef']

    @property
    def rge_undef(self):
        return self.__trs_dict['rge_undef']

    @property
    def sec_undef(self):
        return self.__trs_dict['sec_undef']

    def is_undef(self, twp=True, rge=True, sec=True) -> bool:
        """
        Check if any component of this ``TRS`` is undefined.  (Checks
        against Twp, Rge, and Sec by default, and returns ``True`` if
        any is undefined.)

        :param twp: Check if Twp is undefined.
        :param rge: Check if Rge is undefined.
        :param sec: Check if Sec is undefined.
        :return: A bool, whether *any* of the checked values are
         undefined.
        """
        return ((twp and self.twp_undef)
                or (rge and self.rge_undef)
                or (sec and self.sec_undef))

    def is_error(self, twp=True, rge=True, sec=True) -> bool:
        """
        Check if any component of this ``TRS`` is an error.  (Checks
        against Twp, Rge, and Sec by default, and returns ``True`` if
        any is an error.)

        For this method, undefined values do *not* count as an error.

        :param twp: Check if Twp is an error.
        :param rge: Check if Rge is an error.
        :param sec: Check if Sec is an error.
        :return: A bool, whether *any* of the checked values are errors.
        """
        return ((twp and self.twp_num is None and not self.twp_undef)
                or (rge and self.rge_num is None and not self.rge_undef)
                or (sec and self.sec_num is None and not self.sec_undef))

    def set_twprgesec(
            self,
            twp,
            rge,
            sec,
            default_ns=None,
            default_ew=None,
            ocr_scrub=False):
        """
        Set the Twp/Rge/Sec of this ``TRS`` object by its component
        parts. Returns the compiled Twp/Rge/Sec string in the
        standardized format.

        :param twp: Township (a str or int).

        :param rge: Range (a str or int).

        :param sec: Section (a str or int)

        :param default_ns: (Optional) If ``twp`` wasn't specified as N
         or S, assume ``default_ns`` (pass as ``'n'`` or ``'s'``). If
         not specified, will fall back to ``MasterConfig.default_ns``
         (which is ``'n'`` unless configured otherwise).

        :param default_ew: (Optional) If ``rge`` wasn't specified as E
         or W, assume ``default_ew`` (pass as ``'e'`` or ``'w'``). If
         not specified, will fall back to ``MasterConfig.default_ew``
         (which is ``'w'`` unless configured otherwise).

        :param ocr_scrub: A bool, whether to try to scrub common OCR
         artifacts from the Twp, Rge, and Sec -- if any of them are
         passed as a str. (Defaults to whatever was set in ``.config``,
         which is ``False`` unless configured otherwise.)

        :return: The compiled Twp/Rge/Sec in the standardized format.
        """
        trs = TRS.construct_trs(
            twp, rge, sec, default_ns, default_ew, ocr_scrub)
        self.trs = trs
        return trs

    @staticmethod
    def from_twprgesec(
            twp=None,
            rge=None,
            sec=None,
            default_ns=None,
            default_ew=None,
            ocr_scrub=False):
        """
        Create a new ``TRS`` object from its Twp/Rge/Sec component
        parts.

        (If N/S or E/W are not specified, will pull defaults from
        ``default_ns`` and ``default_ew``. If not specified there, will
        default to ``MasterConfig.default_ns`` and
        ``MasterConfig.default_ns``, which are `'n'` and `'w'`,
        respectively, unless configured otherwise.)

        :param twp: Township. Pass as a string (i.e. ``'154n'``). If
         passed as an int, the N/S will be pulled from ``default_ns`` or
         ``config`` parameters, or defaulted to
         ``MasterConfig.default_ns``, which is ``'n'`` unless configured
         otherwise.

        :param rge: Range. Pass as a string (i.e. ``'97w'``). If passed
         as an int, the E/W will be pulled from ``default_ns`` or
         ``config`` parameters, or defaulted to
         ``MasterConfig.default_ns``, which is ``'n'`` unless configured
         otherwise.

        :param sec: Section. Pass as a str or an int (up to 2 digits).

        :param default_ns: How to interpret townships for which
         direction was not specified -- i.e. either ``'n'`` or ``'s'``.

        :param default_ew: How to interpret ranges for which direction
         was not specified -- i.e. either 'e' or 'w'.

        :param ocr_scrub: Whether to try to iron out common OCR
         'artifacts' from the Twp, Rge, and Sec -- if any of them are
         passed as a str. (Defaults to ``False``.)

        :return: The new ``TRS`` object.
        """
        trs = TRS.construct_trs(
            twp, rge, sec, default_ns, default_ew, ocr_scrub)
        return TRS(trs)

    @staticmethod
    def construct_trs(
            twp,
            rge,
            sec,
            default_ns=None,
            default_ew=None,
            ocr_scrub=False):
        """
        Build a Twp/Rge/Sec in the standardized format from component
        parts.

        (If N/S or E/W are not specified, will pull defaults from
        ``default_ns`` and ``default_ew``. If not specified there, will
        default to ``MasterConfig.default_ns`` and
        ``MasterConfig.default_ns``, which are `'n'` and `'w'`,
        respectively, unless configured otherwise.)

        :param twp: Township. Pass as a string (i.e. ``'154n'``). If
         passed as an int, the N/S will be pulled from ``default_ns`` or
         ``config`` parameters, or defaulted to
         ``MasterConfig.default_ns``, which is ``'n'`` unless configured
         otherwise.

        :param rge: Range. Pass as a string (i.e. ``'97w'``). If passed
         as an int, the E/W will be pulled from ``default_ns`` or
         ``config`` parameters, or defaulted to
         ``MasterConfig.default_ns``, which is ``'n'`` unless configured
         otherwise.

        :param sec: Section. Pass as a str or an int (up to 2 digits).

        :param default_ns: How to interpret townships for which
         direction was not specified -- i.e. either ``'n'`` or ``'s'``.

        :param default_ew: How to interpret ranges for which direction
         was not specified -- i.e. either 'e' or 'w'.

        :param ocr_scrub: Whether to try to iron out common OCR
         'artifacts' from the Twp, Rge, and Sec -- if any of them are
         passed as a str. (Defaults to ``False``.)

        :return: The compiled Twp/Rge/Sec in the standardized format.
        """

        if default_ns is None:
            default_ns = MasterConfig.default_ns
        if default_ew is None:
            default_ew = MasterConfig.default_ew

        # Ensure legal N/S and E/W values.
        if default_ns.lower() not in MasterConfig._LEGAL_NS:
            raise DefaultNSError(default_ns)
        if default_ew.lower() not in MasterConfig._LEGAL_EW:
            raise DefaultEWError(default_ew)

        def scrub(twp_rge_or_section, ns_ew_sec):
            """
            Scrub the `twp`, `rge`, and `sec` from input into the
            component parts. (Use ``ocr_scrub`` if appropriate.) Run
            separately for twp, rge, and section.

            :param twp_rge_or_section: A candidate `twp` or `rge`
            :param ns_ew_sec: 'ns' (if running Twp), 'ew' (if running
            Rge), or None (if running Sec)
            :return: 2-tuple: (scrubbed Twp/Rge/Sec number, direction).
            Note that direction will always be evaluated to None when
            running this for Section.
            """
            twprgesec_num = twp_rge_or_section

            # Determine whether we're running Twp, Rge, or Section.
            # Default to Twp.
            direction = default_ns
            direction_options = MC._LEGAL_NS
            if ns_ew_sec == 'ew':
                # Rge.
                direction = default_ew
                direction_options = MC._LEGAL_EW
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
                twprgesec_num = ocr_scrub_alpha_to_num(twprgesec_num)

            return twprgesec_num, direction

        twp, ns = scrub(twp, 'ns')
        rge, ew = scrub(rge, 'ew')
        sec, _ = scrub(sec, None)

        if ns is None:
            ns = default_ns
        if ew is None:
            ew = default_ew

        if twp in [None, '']:
            twp = MC._UNDEF_TWP
        try:
            twp = int(twp)
        except ValueError:
            # Str has encoded N/S data, or is an error or undefined Twp.
            pass
        if isinstance(twp, int):
            twp = f'{twp}{ns.lower()}'
        if twp != MC._UNDEF_TWP and re.search(rf"\b{TRS._TWP_RGX}\b", twp) is None:
            # Couch the pattern in '\b' to ensure we match the entire str.
            twp = MC._ERR_TWP

        if rge in [None, '']:
            rge = MC._UNDEF_RGE
        try:
            rge = int(rge)
        except ValueError:
            # Str has encoded E/W data, or is an error or undefined Rge.
            pass
        if isinstance(rge, int):
            rge = f"{rge}{ew.lower()}"
        if rge != MC._UNDEF_RGE and re.search(rf"\b{TRS._RGE_RGX}\b", rge) is None:
            rge = MC._ERR_RGE

        if sec in ('', None):
            sec = MC._UNDEF_SEC
        else:
            sec = str(sec).rjust(2, '0')
        if sec != MC._UNDEF_SEC and re.search(rf"\b{TRS._SEC_RGX}\b", sec) is None:
            sec = MC._ERR_SEC

        return f"{twp}{rge}{sec}"

    @staticmethod
    def _cache_trs_to_dict(trs) -> dict:
        """
        INTERNAL USE:
        Identical to ``TRS.trs_to_dict()``, but will also add the
        resulting dict to the ``TRS.__CACHE`` (if ``TRS._USE_CACHE`` is
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
        break it into a dict, keyed as follows::

            'trs'        -> The full Twp/Rge/Sec combination.
            'twp'        -> Twp number + direction (a str or None)
            'twp_num'    -> Twp number (an int or None)
            'twp_ns'     -> Twp direction ('n', 's', or None)
            'ns'         -> same as 'twp_ns'
            'twp_undef'  -> whether the Twp was undefined. (‡)
            'rge'        -> Rge number + direction (a str or None)
            'rge_num'    -> Rge num (an int or None)
            'rge_ew'     -> Rge direction ('e', 'w', or None)
            'ew'         -> same as 'rge_ew'
            'rge_undef'  -> whether the Rge was undefined. (‡)
            'sec_num'    -> Sec number (an int or None)
            'sec_undef'  -> whether the Sec was undefined. (‡)

        .. note::

            ‡ Note that error parses do *not* qualify as 'undefined',
            but undefined and error values are both stored as ``None``.
            ``'twp_undef'``, ``'rge_undef'``, and ``'sec_undef'`` are
            included to differentiate between error vs. undefined, in
            case that distinction is needed.

        :param trs: The Twp/Rge/Sec (in the standardized format) to be
         broken apart.
        :return: A dict with the various elements.
        """
        if isinstance(trs, TRS):
            trs = trs.trs
        dct = {
            'trs': MC._ERR_TRS,
            'twp': MC._ERR_TWP,
            'twp_num': None,
            'twp_ns': None,
            'twp_undef': False,
            'rge': MC._ERR_RGE,
            'rge_num': None,
            'rge_ew': None,
            'rge_undef': False,
            'sec': MC._ERR_SEC,
            'sec_num': None,
            'sec_undef': False
        }
        # Default empty TRS to the undefined version (as opposed to an
        # error version, which would result otherwise).
        if trs in ['', None]:
            trs = MC._UNDEF_TRS

        # Enforce lowercase to match pyTRS standard.
        trs = str(trs).lower()
        mo = TRS._TRS_UNPACKER_REGEX.search(trs)
        if not mo:
            return dct

        # Break down Twp
        if mo.group('twp_num') and mo.group('ns'):
            dct['twp'] = mo.group('twp')
            dct['twp_num'] = int(mo.group('twp_num'))
            dct['twp_ns'] = mo.group('ns')
        elif mo.group('twp') == MC._UNDEF_TWP:
            dct['twp'] = mo.group('twp')
            dct['twp_undef'] = True

        # Break down Rge
        if mo.group('rge_num') and mo.group('ew'):
            dct['rge'] = mo.group('rge')
            dct['rge_num'] = int(mo.group('rge_num'))
            dct['rge_ew'] = mo.group('ew')
        elif mo.group('rge') == MC._UNDEF_RGE:
            dct['rge'] = mo.group('rge')
            dct['rge_undef'] = True

        # Break down Sec
        sec = mo.group('sec')
        try:
            dct['sec_num'] = int(sec)
        except (ValueError, TypeError):
            if sec == MC._UNDEF_SEC:
                dct['sec_undef'] = True
            else:
                sec = MC._ERR_SEC
        finally:
            dct['sec'] = sec

        # Reconstruct TRS
        dct['trs'] = f"{dct['twp']}{dct['rge']}{dct['sec']}"

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
        Range, and/or Section have changed (``MasterConfig._ERR_TWP``,
        ``MasterConfig._UNDEF_TWP``, etc.) then the unpacker regex needs
        to be recompiled to account for these.

        Also recompiles and stores these class attributes:
            ``MasterConfig._ERR_TWPRGE``
            ``MasterConfig._ERR_TRS``
            ``MasterConfig._UNDEF_TWPRGE``
            ``MasterConfig._UNDEF_TRS``

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
        new_rgx = compile_trs_unpacker_regex(
            twp_rgx=TRS._TWP_RGX,
            err_twp=MC._ERR_TWP,
            undef_twp=MC._UNDEF_TWP,
            rge_rgx=TRS._RGE_RGX,
            err_rge=MC._ERR_RGE,
            undef_rge=MC._UNDEF_RGE,
            sec_rgx=TRS._SEC_RGX,
            err_sec=MC._ERR_SEC,
            undef_sec=MC._UNDEF_SEC)
        cls._TRS_UNPACKER_REGEX = new_rgx
        
        MC._ERR_TWPRGE = f"{MC._ERR_TWP}{MC._ERR_RGE}"
        MC._ERR_TRS = f"{MC._ERR_TWPRGE}{MC._ERR_SEC}"
        MC._UNDEF_TWPRGE = f"{MC._UNDEF_TWP}{MC._UNDEF_RGE}"
        MC._UNDEF_TRS = f"{MC._UNDEF_TWPRGE}{MC._UNDEF_SEC}"

        # Clear the cache, because the same string would not necessarily
        # result in the same output dict anymore.
        cls._clear_cache()

        return new_rgx


def trs_to_dict(trs) -> dict:
    """
    Take a compiled Twp/Rge/Sec (in the standard pyTRS format) and break
    it into a dict, keyed as follows::

        'trs'        -> The full Twp/Rge/Sec combination.
        'twp'        -> Twp number + direction (a str or None)
        'twp_num'    -> Twp number (an int or None)
        'twp_ns'     -> Twp direction ('n', 's', or None)
        'ns'         -> same as 'twp_ns'
        'twp_undef'  -> whether the Twp was undefined. (‡)
        'rge'        -> Rge number + direction (a str or None)
        'rge_num'    -> Rge num (an int or None)
        'rge_ew'     -> Rge direction ('e', 'w', or None)
        'ew'         -> same as 'rge_ew'
        'rge_undef'  -> whether the Rge was undefined. (‡)
        'sec_num'    -> Sec number (an int or None)
        'sec_undef'  -> whether the Sec was undefined. (‡)

    .. note::

        ‡ Note that error parses do *not* qualify as 'undefined',
        but undefined and error values are both stored as ``None``.
        ``'twp_undef'``, ``'rge_undef'``, and ``'sec_undef'`` are
        included to differentiate between error vs. undefined, in
        case that distinction is needed.

    :param trs: The Twp/Rge/Sec (in the standardized format) to be
     broken apart.

    :return: A dict with the various elements.
    """
    return TRS.trs_to_dict(trs)


__all__ = [
    'TRS',
    'trs_to_dict',
]
