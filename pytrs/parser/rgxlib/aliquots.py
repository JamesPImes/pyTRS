
import re


# A lookbehind requiring an aliquot marker or word boundary.
fwb_lkbehind = r"((?<=¼|4|½|2)|(?<=\b))"

# A subpattern to match 'One Quarter', 'Quarter', or equivalent symbol.
quarter_subpattern = r"((One)?\s*Q[uarter]{3,7}|1\/?4|\/?4|¼)"

# A subpattern to match 'One Half', 'Half', or equivalent symbol.
half_subpattern = r"((One)?\s*Half|1\/?2|\/?2|½)"

# Subpatterns for each quarter or abbreviation (with no fraction).
ne_simple = r"(NE|North?\s*East)"
se_simple = r"(SE|South?\s*East)"
nw_simple = r"(NW|North?\s*West)"
sw_simple = r"(SW|South?\s*West)"

# Subpatterns for each direction or abbreviation (with no fraction).
n_simple = r"(N\.?|No\.?|North?)"
s_simple = r"(S\.?|So\.?|South?)"
e_simple = r"(E\.?|East)"
w_simple = r"(W\.?|West)"

# Subpattern for cleaned up aliquot.
aliquot_simple = r"(([NESW]½)|((NE|NW|SE|SW)¼))"

# Basic aliquot regexes.

# Quarters.

ne_regex = re.compile(
    fr"""
    {fwb_lkbehind}
    {ne_simple}
    \s*
    {quarter_subpattern}
    """, re.IGNORECASE | re.VERBOSE)

se_regex = re.compile(
    fr"""
    {fwb_lkbehind}
    {se_simple}
    \s*
    {quarter_subpattern}
    """, re.IGNORECASE | re.VERBOSE)

nw_regex = re.compile(
    fr"""
    {fwb_lkbehind}
    {nw_simple}
    \s*
    {quarter_subpattern}
    """, re.IGNORECASE | re.VERBOSE)

sw_regex = re.compile(
    fr"""
    {fwb_lkbehind}
    {sw_simple}
    \s*
    {quarter_subpattern}
    """, re.IGNORECASE | re.VERBOSE)

# Halves.

n2_regex = re.compile(
    fr"""
    {fwb_lkbehind}
    {n_simple}
    \s*
    {half_subpattern}
    """, re.IGNORECASE | re.VERBOSE)

s2_regex = re.compile(
    fr"""
    {fwb_lkbehind}
    {s_simple}
    \s*
    {half_subpattern}
    """, re.IGNORECASE | re.VERBOSE)

e2_regex = re.compile(
    fr"""
    {fwb_lkbehind}
    {e_simple}
    \s*
    {half_subpattern}
    """, re.IGNORECASE | re.VERBOSE)

w2_regex = re.compile(
    fr"""
    {fwb_lkbehind}
    {w_simple}
    \s*
    {half_subpattern}
    """, re.IGNORECASE | re.VERBOSE)


# clean_qq regexes, for parsing aliquots under clean_qq=True conditions.
# Will match much more broadly than the other aliquot regexes.

ne_clean = re.compile(
    fr"{ne_simple}\s*({quarter_subpattern})?", re.IGNORECASE)

se_clean = re.compile(
    fr"{se_simple}\s*({quarter_subpattern})?", re.IGNORECASE)

nw_clean = re.compile(
    fr"{nw_simple}\s*({quarter_subpattern})?", re.IGNORECASE)

sw_clean = re.compile(
    fr"{sw_simple}\s*({quarter_subpattern})?", re.IGNORECASE)


# N2, S2, E2, and W2 are the same under clean_qq conditions, since there
# still must be SOME designator that it's a 'half'.


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
        
        (?P<quarter_aliquot_rightmost>
            
            # Determine whichever aliquot quarter appears at the rightmost.
            
            # IMPORTANT: The following named groups ('ne_found' etc.) do
            #   NOT match ONLY on the rightmost. Figure out which group
            #   ('ne_found', etc.) matches the 'quarter_aliquot_rightmost'
            #   group, and that will be the ACTUAL rightmost named group.
            
            (?P<ne_found>{ne_clean.pattern})        
            |
            (?P<nw_found>{nw_clean.pattern})
            |
            (?P<se_found>{se_clean.pattern})
            |
            (?P<sw_found>{sw_clean.pattern})
        )
    )+      # IMPORTANT: One or more to match all.
    \b
    """, re.IGNORECASE | re.VERBOSE)

# For cutting out whitespace and 'of the' or 'of' between identified
# aliquot components:
aliquot_intervener_remover_regex = re.compile(
    fr"""
    (?P<aliquot1>({aliquot_simple})+)  # first aliquot component
    (
        \s*     # any amount of whitespace (to be removed)
        
        # 'of the' or 'of' (to be removed)
        (\s+|of|o|f|o+f+)\s*(t+h+e+|t+e+h+|t+h+|t+)?
        
        \s*     # any amount of whitespace (to be removed)
    )
    (?P<aliquot2>{aliquot_simple})  # second aliquot component
    """, re.IGNORECASE | re.VERBOSE)
