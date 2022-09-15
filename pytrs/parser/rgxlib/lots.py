
import re

from .misc import (
    intervener_regex,
)

# A regex for extra context around pp_twprge_no_nsr preprocessing
# (need to rule out "Lots" at the start of such a match):
lots_context_regex = re.compile(r"Lo?ts?|Lo?s?t", re.IGNORECASE)

# Capture acreage in the format (12.345678) or [12.345678].
acreage_subpattern = re.compile(
    r"""
    (
        \(\d{0,3}\.?\d{0,6}\)   # Enclosed with parentheses.
        |
        \[\d{0,3}\.?\d{0,6}\]   # Enclosed with square brackets.
    )
    """, re.IGNORECASE | re.VERBOSE)

lot_regex = re.compile(
    fr"""
    (
        (L\.?o?t?)                  # The word or abbreviation "Lot"
        (?P<plural>s)?              # Plural 's' (optional).
        \s*
        (?P<lotnum>\d{{1,3}})       # lotnum
        \s*
        (?P<acreage>{acreage_subpattern.pattern})?  # Acreage (optional).
    )
    """, re.IGNORECASE | re.VERBOSE
)

# Lot regex (should capture entire match, but then requires some processing
# to unpack it):
multilot_regex = re.compile(
    fr"""
    (
        # This group captures "Lot" and named groups 'plural', 'lotnum',
        # and 'acreage' -- for the leftmost lot.
        {lot_regex.pattern}
    )
    
    \s*
    
    (
        # What comes between lots ('through', 'and', etc.). Captures named
        # groups 'through' and 'and' for those words or equivalent symbols.
        ({intervener_regex.pattern})+   # IMPORTANT: Allow more than one intervener
                                        # to keep matching multilots to the right!
        \s*
        ((L\.?o?t?)                  # The word or abbreviation "Lot" (optional on the right).
        (?P<plural_rightmost>s)?)?   # Plural 's' (optional).
        \s*
        (?P<lotnum_rightmost>\d{{1,3}})     # lotnum (rightmost)
        \s*
        (?P<acreage_rightmost>{acreage_subpattern.pattern})?  # Acreage (optional).
    )*
    """, re.IGNORECASE | re.VERBOSE)


# A pattern to match divided lots (e.g., 'N½N½ of Lots 1 - 3'). To be
# used only AFTER aliquots have been preprocessed into standard
# abbreviations with fractions.
lot_with_aliquot_regex = re.compile(
    fr"""
    (?P<aliquot>(([NESW]½)|((NE|NW|SE|SW)¼))+)  # leading aliquot division (optional)
    \s*
    (of)?                           # "of" (optional)
    \s*
    
    # The usual multi-lot pattern with the same named groups.
    {multilot_regex.pattern}
    """, re.IGNORECASE | re.VERBOSE)
