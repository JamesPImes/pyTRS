# Copyright (c) 2020, James P. Imes, all rights reserved.

"""
pyTRS - a pure Python library for parsing Public Land Survey System
(PLSS) land descriptions (or "legal descriptions") into their component
parts, in a format that is more useful for data analysis, GIS mapping,
spreadsheets, and databases generally. It accounts for common variations
in layout, abbreviations, typos, etc. and can therefore process a range
of real-world data.

Copyright (c) 2020, James P. Imes, all rights reserved.

THIS LIBRARY IS NOT TO BE USED FOR ANY UNLICENSED COMMERCIAL PURPOSES OR
FOR GENERATING OR MODIFYING LEGAL DESCRIPTIONS IN ANY LEGAL DOCUMENT!
Intended for data analysis purposes ONLY. Read license and disclaimer
prior to using for any purpose.

!!! USE AT YOUR OWN RISK !!!
"""

import pyTRS._constants as _constants

__version__ = _constants.__version__
__versionDate__ = _constants.__versionDate__
__author__ = _constants.__author__
__email__ = _constants.__email__
__license__ = _constants.__license__
__disclaimer__ = _constants.__disclaimer__
__website__ = _constants.__website__

# Misc. utils:

def version():
    """Return the current version and version date as a string."""
    return f'v{__version__} - {__versionDate__}'


def disclaimer():
    """Print the disclaimer to console."""
    print(__disclaimer__)


# Primary parsing classes
from pyTRS.pyTRS import PLSSDesc, Tract, TractList, Config

# Misc. functions for examining / handling descriptions:
from pyTRS.pyTRS import find_tr, find_sec, decompile_twprge, find_multisec, break_trs

# For outputting parsed data to csv files
from pyTRS.pyTRS import output_to_csv

# A current list of implemented layouts
from pyTRS.pyTRS import __implementedLayouts__
from pyTRS.pyTRS import __implementedLayoutExamples__

# Other modules
from pyTRS import check, quick, utils, interface_tools, csv_suite