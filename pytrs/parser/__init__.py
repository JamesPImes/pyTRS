# Copyright (c) 2020-2021, James P. Imes, All rights reserved.

"""
The main parsing package. Primary classes:
> PLSSDesc objects parse PLSS description text (full descriptions) into
    Tract objects (one TRS + description per Tract), stored as TractList
> Tract objects parse tract text into lots and aliquots.
> Tract objects represent the land in a single, unique Twp/Rge/Sec, and
    also parse text into lots and aliquots.
> TractList objects contain a list of Tracts, and can compile that Tract
    data into broadly useful formats (i.e. into list, dict, string), as
    well as custom methods for sorting, grouping, and filtering the
    Tract objects themselves.
> Config objects configure parsing parameters for Tract and PLSSDesc.
"""

from .parser import (
    # Primary parsing classes and their helper classes
    PLSSDesc,
    Tract,
    TractList,
    TRS,
    Config,

    # Misc. functions for examining / handling descriptions
    find_twprge,
    find_sec,
    find_multisec,
    trs_to_dict,

    # For grouping / sorting Tract objects
    group_tracts,
    sort_grouped_tracts,

    # A tuple of currently implemented layouts
    IMPLEMENTED_LAYOUTS,

    # Examples of the currently implemented layouts
    IMPLEMENTED_LAYOUT_EXAMPLES
)
