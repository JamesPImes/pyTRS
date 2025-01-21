
"""
Regex patterns for Sections and related preprocessing and parsing.
"""

import re

from .misc import (
    through_regex,
    intervener_regex,
)

# Regex pattern for the word "Section" or equivalent symbol, allowing
# for slight misspellings.
no_num_sec_regex = re.compile(
    r"(Section|Sect\.?|Sec\.?|Secion|Seciton|Secton|Sectn|Secn|§)",
    re.IGNORECASE)

# Regex pattern to match "Section <secnum>".
sec_regex = re.compile(
    fr"""
    (
    # The word or symbol "Section" (also captures named group 'plural'
    # if final 's' is present).
    {no_num_sec_regex.pattern}
    (?P<plural>s)?
    
    [:\s*]?[\.\-–—\s]*                # Deadspace between "Section" and secnum
    
    # Note the double curly brackets to escape f-string syntax.
    (?P<secnum>\d{{1,3}})       # Section number, between 1 and 3 digits.
    )
    """, re.IGNORECASE | re.VERBOSE)


multisec_regex = re.compile(
    fr"""
    (
        # This group captures "Section" and named groups 'plural' and 'secnum'.
        {sec_regex.pattern}
    )
    (
        # What comes between sections ('through', 'and', etc.). Captures named
        # groups 'through' and 'and' for those words or equivalent symbols.
        ({intervener_regex.pattern})+   # IMPORTANT: Allow more than one intervener
                                        # to keep matching multisec to the right!

        ({no_num_sec_regex.pattern}     # The word or abbreviation "Section" (optional)
        (?P<plural_rightmost>s)?)?
        \s*
        (?P<secnum_rightmost>\d{{1,3}})  # Rightmost section number (1 to 3 digits)
    )*   # Will go to here for multi-sections
    (?P<colon>\s*:)?    # Capture an optional colon at end.
    """, re.IGNORECASE | re.VERBOSE)
