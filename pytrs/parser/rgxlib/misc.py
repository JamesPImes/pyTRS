
import re

# A pattern to match the word "through" or equivalent symbol or
# abbreviation. (Embedded into other regex patterns -- not to be used on
# its own.)
through_regex = re.compile(
    r'([\-–—]|th[rough]{3,6}\.?|thru\.?|to)', re.IGNORECASE)


# A pattern to be embedded within patterns to match elided lists.
# For example, for matching multisec:  "Sections 1 - 3, and 5 - 7"
# ... or multi-lots:  "Lots 1 - 3".
intervener_regex = re.compile(
    fr"""
    (?P<intervener>
    \s*
    (
        ([\/\.,;:])
        |
        # Matches "through" or equivalent symbols as named group 'thru'.
        (?P<thru>{through_regex.pattern})
        |
        (?P<and>and|&)
    )
    \s*
    )
    """, re.IGNORECASE | re.VERBOSE)
