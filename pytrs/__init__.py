# Copyright (c) 2020-2022, James P. Imes, all rights reserved.

"""
pyTRS - a pure Python library for parsing Public Land Survey System
(PLSS) land descriptions (or "legal descriptions") into their component
parts, in a format that is more useful for data analysis, GIS mapping,
spreadsheets, and databases generally. It accounts for common variations
in layout, abbreviations, typos, etc. and can therefore process a range
of real-world data.

Copyright (c) 2020-2022, James P. Imes, all rights reserved.

THIS LIBRARY IS NOT TO BE USED FOR ANY UNLICENSED COMMERCIAL PURPOSES OR
FOR GENERATING OR MODIFYING LEGAL DESCRIPTIONS IN ANY LEGAL DOCUMENT!
Intended for data analysis purposes ONLY. Read license and disclaimer
prior to using for any purpose.
"""

import pytrs._constants as _constants

__version__ = _constants.__version__
__version_date__ = _constants.__version_date__
__author__ = _constants.__author__
__email__ = _constants.__email__
__license__ = _constants.__license__
__disclaimer__ = _constants.__disclaimer__
__website__ = _constants.__website__


# Import the main parsing functionality as top-level classes, vars, etc.
from pytrs.parser import (
    # Primary parsing classes and their helper classes
    PLSSDesc,   # parser.plssdesc submodule
    Tract,      # parser.tract submodule
    TRS,        # parser.trs submodule
    TractList,  # parser.container submodule
    TRSList,    # parser.container submodule
    Config,     # parser.config.config submodule
    MasterConfig,   # parser.config.master_config submodule

    # Misc. functions for examining / handling descriptions
    find_twprge,    # parser.plss_preprocess submodule
    trs_to_dict,    # parser.trs submodule

    # For grouping / sorting Tract objects
    group_tracts,   # parser.containers submodule
    sort_grouped_tracts,    # parser.containers submodule

    # A tuple of currently implemented layouts
    IMPLEMENTED_LAYOUTS,    # parser.plss_parse submodule

    # Examples of the currently implemented layouts
    IMPLEMENTED_LAYOUT_EXAMPLES     # parser.plss_parse submodule
)


# Misc. utils:

def version():
    """Return the current version and version date as a string."""
    return f'v{__version__} - {__version_date__}'


def disclaimer():
    """Print the disclaimer to console."""
    print(__disclaimer__)
