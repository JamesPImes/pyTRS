
"""
Library of regex patterns used by the parser.
"""

from .twprge import *
from .sec import *
from .lots import *
from .aliquots import *
from .warnings import *
from .misc import *
from .context_checkers import *

# Remove 're' module from __all__, to avoid cluttering namespace.
__all__ = [k for k in locals().keys() if not k.startswith('__')]
__all__.remove('re')
