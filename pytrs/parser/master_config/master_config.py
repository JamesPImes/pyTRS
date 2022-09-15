
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
    they are
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


__all__ = [
    'DefaultEWError',
    'DefaultNSError',
    'MasterConfig',
]
