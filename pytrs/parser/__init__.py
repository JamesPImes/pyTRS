# Copyright (c) 2020-2022, James P. Imes, All rights reserved.

"""
The main parsing package. Primary classes:
> ``PLSSDesc`` objects parse PLSS description text (full descriptions)
    into ``Tract`` objects (one Twp/Rge/Sec + description per ``Tract``),
    stored as ``TractList``.
> ``Tract`` objects parse tract text into lots and aliquots.
> ``Tract`` objects represent the land in a single, unique Twp/Rge/Sec,
    and also parse text into lots and aliquots.
> ``TRS`` objects break a Twp/Rge/Sec into its components.
> ``TractList`` objects contain a list of ``Tracts``, and can compile
    that ``Tract`` data into broadly useful formats (i.e. into list,
    dict, string), as well as custom methods for sorting, grouping, and
    filtering the ``Tract`` objects themselves.
> ``TRSList`` objects are similar to ``TractList``, but instead hold
    ``TRS`` objects.
> ``Config`` objects configure parsing parameters for ``Tract`` and
    ``PLSSDesc`` objects.
"""

from .plssdesc import PLSSDesc
from .plssdesc.plss_parse import (
    deduce_layout,
    find_twprge,
)
from .tract import Tract
from .trs import (
    TRS,
    trs_to_dict
)
from .containers import (
    TractList,
    TRSList,
    group_tracts,
    sort_grouped_tracts,
)
from .config import (
    Config,
    MasterConfig,
)
from .config import (
    # Public-facing info / examples.
    IMPLEMENTED_LAYOUTS,
    IMPLEMENTED_LAYOUT_EXAMPLES,
)
