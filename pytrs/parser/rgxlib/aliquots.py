
import re


# A lookbehind requiring an aliquot marker or word boundary.
fwb_lkbehind = r"((?<=¼|4|½|2)|(?<=\b))"

# A lookahead requiring the start of an aliquot, or appropriate symbol
# (do not use word boundary \b, to prevent symbols like degrees -- e.g.,
#   N 2° 37'  -->  'N/2').
aqwb_lkahead = r"((?=N|S|E|W)|(?=[\s,.;])|(?=$))"

# A subpattern to match 'One Quarter', 'Quarter', or equivalent symbol.
quarter_subpattern = r"((One)?[\s\-]*Q[uarter]{3,7}|1\s*\/\s*4|¼)"

# A subpattern to match 'One Half', 'Half', or equivalent symbol.
half_subpattern = r"((One)?[\s\-]*Half|1\s*\/\s*2|½)"

# Subpaterns for each quarter or abbreviation (with no fraction).
# Note: Should not be used without some forward-looking context (e.g.,
# a fraction symbol).
ne_simple = r"(N\s{0,2}E|North?[\s\-]*East|N\.\s{0,2}E\.)"
se_simple = r"(S\s{0,2}E|South?[\s\-]*East|S\.\s{0,2}E\.)"
nw_simple = r"(N\s{0,2}W|North?[\s\-]*West|N\.\s{0,2}W\.)"
sw_simple = r"(S\s{0,2}W|South?[\s\-]*West|S\.\s{0,2}W\.)"

# Subpatterns for each direction or abbreviation (with no fraction).
n_simple = r"(N\.?|No\.?|North?)"
s_simple = r"(S\.?|So\.?|South?)"
e_simple = r"(E\.?|East)"
w_simple = r"(W\.?|West)"

# Subpatterns for each direction with short abbreviations for 'half'.
# Note: If space(s) is found between '/' and '2', then space(s) is
# REQUIRED between [aliquot] and [fraction abbrev.]
#    'N / 2' -> OK;    'N /2' -> OK;    'N/ 2'  --> Not OK.
_form = r"(({0}\/?2)|({0}\s{{1,2}}(2|\/\s{{0,2}}2)))"
n2_short = _form.format('N')
s2_short = _form.format('S')
e2_short = _form.format('E')
w2_short = _form.format('W')

# Subpatterns for each quarter with short abbreviations for 'quarter'.
# Note: If space(s) is found between '/' and '4', then space(s) is
# REQUIRED between [aliquot] and [fraction abbrev.]
#    'NE / 4' -> OK;   'NE /4' -> OK;  'NE/ 4'  --> Not OK.
_form = r"(({0}\/?4)|({0}\s{{1,2}}(4|\/\s{{0,2}}4)))"
ne_short = _form.format('NE')
nw_short = _form.format('NW')
se_short = _form.format('SE')
sw_short = _form.format('SW')

# Subpattern for cleaned up aliquot.
aliquot_simple = r"(([NESW]½)|((NE|NW|SE|SW)¼))"

# Basic aliquot regexes.

# Quarters.

ne_regex = re.compile(
    fr"""
    {fwb_lkbehind}
    (
        ({ne_simple}\s*{quarter_subpattern})
        |
        ({ne_short})
    )
    {aqwb_lkahead}
    """, re.IGNORECASE | re.VERBOSE)

se_regex = re.compile(
    fr"""
    {fwb_lkbehind}
    (
        ({se_simple}\s*{quarter_subpattern})
        |
        ({se_short})
    )
    {aqwb_lkahead}
    """, re.IGNORECASE | re.VERBOSE)

nw_regex = re.compile(
    fr"""
    {fwb_lkbehind}
    (
        ({nw_simple}\s*{quarter_subpattern})
        |
        ({nw_short})
    )
    {aqwb_lkahead}
    """, re.IGNORECASE | re.VERBOSE)

sw_regex = re.compile(
    fr"""
    {fwb_lkbehind}
    (
        ({sw_simple}\s*{quarter_subpattern})
        |
        ({sw_short})
    )
    {aqwb_lkahead}
    """, re.IGNORECASE | re.VERBOSE)

# Halves.

n2_regex = re.compile(
    fr"""
    {fwb_lkbehind}
    (
        ({n_simple}\s*{half_subpattern})
        |
        ({n2_short})
    )
    {aqwb_lkahead}
    """, re.IGNORECASE | re.VERBOSE)

s2_regex = re.compile(
    fr"""
    {fwb_lkbehind}
    (
        ({s_simple}\s*{half_subpattern})
        |
        ({s2_short})
    )
    {aqwb_lkahead}
    """, re.IGNORECASE | re.VERBOSE)

e2_regex = re.compile(
    fr"""
    {fwb_lkbehind}
    (
        ({e_simple}\s*{half_subpattern})
        |
        ({e2_short})
    )
    {aqwb_lkahead}
    """, re.IGNORECASE | re.VERBOSE)

w2_regex = re.compile(
    fr"""
    {fwb_lkbehind}
    (
        ({w_simple}\s*{half_subpattern})
        |
        ({w2_short})
    )
    {aqwb_lkahead}
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
    (?P<half_aliquot>[NESW]½)       # Which aliquot half.
    
    (
        \s*
        (?P<of_the>\s*of(\s*the)?)?    # 'of' or 'of the'
        \s*
        
        (?P<quarter_aliquot_rightmost>
            
            # Determine whichever aliquot quarter appears at the rightmost.
            
            # IMPORTANT: The following named groups ('ne_found' etc.) do
            #   NOT match ONLY on the rightmost. Figure out which group
            #   ('ne_found', etc.) matches the 'quarter_aliquot_rightmost'
            #   group, and that will be the ACTUAL rightmost named group.
            
            (?P<ne_found>{ne_simple})        
            |
            (?P<nw_found>{nw_simple})
            |
            (?P<se_found>{se_simple})
            |
            (?P<sw_found>{sw_simple})
        )
    )+      # IMPORTANT: One or more to match all.
    
    # Lookahead for apparent marker of end of the aliquot, and exclude
    # any already-cleaned halves or quarters.
    (
        $                     # End of string.
        |
        (?=[\s\.\,\;])        # End on white space, comma, etc.
        |
        (?=[NESW]½)           # End on clean half.
        |
        (?=NE¼|NW¼|SE¼|SW¼)   # End on clean quarter.
    )
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


# Will capture the aliquot component (without fraction) in 'aliquot_no_frac'
# named group. Should only be used on preprocessed aliquot blocks (e.g.,
# "E½NW¼NE¼" or "ALL"):
single_aliquot_unpacker_regex = re.compile(r"((?P<aliquot_no_frac>[NESW]{1,2}|ALL)[½¼]?)")


aliquot_unpacker_regex = re.compile(
    r'\b(([NESW]½)|((NE|NW|SE|SW)¼))+\b')