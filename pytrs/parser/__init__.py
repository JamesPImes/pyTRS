# Copyright (c) 2020-2021, James P. Imes, All rights reserved.

"""
The main parsing package. Primary classes:
> PLSSDesc objects parse PLSS description text (full descriptions) into
    Tract objects (one TRS + description per Tract), stored as TractList
> Tract objects parse tract text into lots and aliquots.
> TRS objects break a Twp/Rge/Sec into its components.
> TractList objects contain a list of Tracts, and can compile that Tract
    data into broadly useful formats (i.e. into list, dict, string).
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
    decompile_twprge,
    find_multisec,
    break_trs,
    trs_to_dict,

    # For outputting parsed data to csv files
    output_to_csv,

    # A tuple of currently implemented layouts
    IMPLEMENTED_LAYOUTS,

    # Examples of the currently implemented layouts
    IMPLEMENTED_LAYOUT_EXAMPLES
)
