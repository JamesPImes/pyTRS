
"""
Regex patterns for Sections and related preprocessing and parsing.
"""

import re

# Regex pattern for the word "Section" or equivalent symbol, allowing
# for slight misspellings, and capturing optional plural 's'.
no_num_sec_regex = re.compile(
    r"((Section|Sect\.?|Sec\.?|Secion|Seciton|Secton|Sectn|Secn|§)(?P<plural>s)?)",
    re.IGNORECASE)

# Regex pattern to match "Section <secnum>".
sec_regex = re.compile(
    fr"""
    (
    # The word or symbol "Section" (also captures named group 'plural'
    # if final 's' is present).
    {no_num_sec_regex.pattern}
    
    [\.\-–—\s]*                 # Deadspace between "Section" and secnum
    
    # Note the double curly brackets to escape f-string syntax.
    (?P<secnum>\d{{1,3}})       # Section number, between 1 and 3 digits.
    \s*                         # Trailing whitespace.
    )
    """, re.IGNORECASE | re.VERBOSE)
