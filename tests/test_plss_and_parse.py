
"""
Tests for the pytrs.parser.plssdesc module and submodules (except the
.plss_preprocess submodule, which has its own tests).
"""

import unittest


try:
    from pytrs.parser import PLSSDesc
    from pytrs.parser.plssdesc.plss_parse import PLSSParser
    from pytrs.parser import Tract
except ImportError:
    import sys
    sys.path.append('../')
    from pytrs.parser import PLSSDesc
    from pytrs.parser.plssdesc.plss_parse import PLSSParser
    from pytrs.parser import Tract
