
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

# A pattern ot be embedded within other patterns to check if "of the"
# appears between target groups.
of_the_regex = re.compile(
    r"(\s+|of|o|f|o+f+)\s*(t+h+e+|t+e+h+|t+h+|t+)?", re.IGNORECASE
)

# Lookbehind subpattern for comma (or similar) or word boundary.
comma_wb_lookbehind = r"((?<=[,;:])|(?<=\b))"
