
"""
Regex patterns for Sections and related preprocessing and parsing.
"""

import re

sec_regex = re.compile(
    r"""
    # The word or symbol "Section".
    ((Section|Sect\.?|Sec\.?|Secion|Secton|Seciton|Sectn|Secn|§)
    (?P<plural>s)?              # Plural 's' (optional).
    
    [\.\-–—\s]*                 # Deadspace between "Section" and secnum
    
    (?P<secnum>\d{1,3})\s*)     # Section number, between 1 and 3 digits
    """, re.IGNORECASE | re.VERBOSE)
