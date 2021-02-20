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

# Primary parsing classes
from .parser import PLSSDesc, Tract, TractList, Config

# Misc. functions for examining / handling descriptions:
from .parser import (
    find_twprge,
    find_sec,
    decompile_twprge,
    find_multisec,
    break_trs
)

# For outputting parsed data to csv files
from .parser import output_to_csv

# A current list of implemented layouts
from .parser import IMPLEMENTED_LAYOUTS
from .parser import IMPLEMENTED_LAYOUT_EXAMPLES
