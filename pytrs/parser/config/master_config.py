
"""
Classes for configuring default parsing.
"""


class DefaultNSError(ValueError):
    """Illegal value for ``default_ns``."""
    def __init__(self, obj=None):
        legal = "', '".join(MasterConfig._LEGAL_NS)
        legal = f"['{legal}']"
        msg = f"`default_ns` must be one of {legal}."
        if obj is not None:
            msg = f"{msg} Passed {obj!r}."
        super().__init__(msg)


class DefaultEWError(ValueError):
    """Illegal value for ``default_ew``."""
    def __init__(self, obj=None):
        legal = "', '".join(MasterConfig._LEGAL_EW)
        legal = f"['{legal}']"
        msg = f"`default_ew` must be one of {legal}."
        if obj is not None:
            msg = f"{msg} Passed {obj!r}."
        super().__init__(msg)


class MasterConfig:
    """
    Control ``default_ns`` and ``default_ew`` across all of pytrs, when
    they are not specified for a particular instance of a class, or for
    a call to a function or method (and not otherwise configured for the
    object whose method it is).
    """

    NORTH = 'n'
    SOUTH = 's'
    EAST = 'e'
    WEST = 'w'

    # Control all unspecified default_ns and default_ew
    default_ns = NORTH
    default_ew = WEST

    # Legal settings for N/S/E/W
    _LEGAL_NS = ('n', 's', 'N', 'S')
    _LEGAL_EW = ('e', 'w', 'E', 'W')

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


__all__ = [
    'DefaultEWError',
    'DefaultNSError',
    'MasterConfig',
]
