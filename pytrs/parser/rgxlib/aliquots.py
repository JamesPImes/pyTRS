
import re


# A lookbehind requiring an aliquot marker or word boundary.
fwb_lkbehind = r"((?<=¼|4|½|2)|(?<=\b))"

# A subpattern to match 'One Quarter', 'Quarter', or equivalent symbol.
quarter_subpattern = r"(One)?\s*Q[uarter]{3,7}|1\/?4|\/?4|¼"


# clean_qq regexes, for parsing aliquots under clean_qq=True conditions.
# Will match much more broadly than the other aliquot regexes. (These
# will get incorporated into the non-clean regexes too.)

# N2, S2, E2, and W2 are the same under clean_qq conditions, since there
# still must be SOME designator that it's a 'half'.

ne_clean = re.compile(
    fr"(NE|Nort[h]?\s*East)\s*({quarter_subpattern})?", re.IGNORECASE)

se_clean = re.compile(
    fr"(SE|Sout[h]?\s*East)\s*({quarter_subpattern})?", re.IGNORECASE)

nw_clean = re.compile(
    fr"(NW|Nort[h]?\s*West)\s*({quarter_subpattern})?", re.IGNORECASE)

sw_clean = re.compile(
    fr"(SW|Sout[h]?\s*West)\s*({quarter_subpattern})?", re.IGNORECASE)


# Basic aliquot regexes.

# Quarters.

ne_regex = re.compile(
    fr"""
    {fwb_lkbehind}
    {ne_clean}
    """, re.IGNORECASE | re.VERBOSE)

se_regex = re.compile(
    fr"""
    {fwb_lkbehind}
    {se_clean}
    """, re.IGNORECASE | re.VERBOSE)

nw_regex = re.compile(
    fr"""
    {fwb_lkbehind}
    {nw_clean}
    """, re.IGNORECASE | re.VERBOSE)

sw_regex = re.compile(
    fr"""
    {fwb_lkbehind}
    {sw_clean}
    """, re.IGNORECASE | re.VERBOSE)

# Halves.

n2_regex = re.compile(
    fr"""
    {fwb_lkbehind}
    (N\.?|No\.?|Nort[h]?)\s*((One)?\s*Half|1\/?2|\/?2|½)
    """, re.IGNORECASE | re.VERBOSE)

s2_regex = re.compile(
    fr"""
    {fwb_lkbehind}
    (S\.?|So\.?|Sout[h]?)\s*((One)?\s*Half|1\/?2|\/?2|½)
    """, re.IGNORECASE | re.VERBOSE)

e2_regex = re.compile(
    fr"""
    {fwb_lkbehind}
    (E\.?|East)\s*((One)?\s*Half|1\/?2|\/?2|½)
    """, re.IGNORECASE | re.VERBOSE)

w2_regex = re.compile(
    fr"""
    (\b|¼|4|½|2)(W\.?|West)\s*((One)?\s*Half|1\/?2|\/?2|½)
    """, re.IGNORECASE | re.VERBOSE)


# Find 'ALL', with options for context. Will only match 'ALL' at the
# beginning of a word boundary.
all_regex = re.compile(r"\b(?P<all>ALL)(?P<context>.{1,6})?", re.IGNORECASE)


# 'E2NE' should be enough context to interpret it as the E½NE¼. This
# regex can be applied after subbing the other 'half' regexes in for
# their cleaner counterparts, so 'E2NE' -> 'E½NE' --> 'E½NE¼'.
# Must be at word boundaries, per \b.
half_plus_q_regex = re.compile(
    fr"""
    ((?<=½)|(?<=\b))                # Lookbehind of word boundary or '½' 
    (?P<half_aliquot>[NESW])½       # Which aliquot half.
    (
        \s*
        (?P<of_the>of(\s*the)?)?    # 'of' or 'of the'
        \s*
        
        (?P<quarter_aliquot_rightmost>      # Which aliquot quarter appears
            (?P<ne_found>{ne_clean})        # at the rightmost.
            |
            (?P<nw_found>{nw_clean})
            |
            (?P<se_found>{se_clean})
            |
            (?P<sw_found>{sw_clean})
        )
    )+      # IMPORTANT: One or more to match all.
    \b
    """, re.IGNORECASE | re.VERBOSE)
