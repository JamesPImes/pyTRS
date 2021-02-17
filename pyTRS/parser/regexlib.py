
"""
A library of regex patterns for pyTRS parsing.
"""

import re

# Township & Range + Section regexes...

# Should find township & ranges, formatted with up to 3 digits for twp
# and for rge ('000n000w' or '0n0w' or between).
# Note that this is somewhat more complicated than it /should/ be because a
# Range of '2' can accidentally capture as a Range number in, for example
# "N2N2, W2E2" (i.e. could match as 'T2N-R2W'). So we disallow specifically
# a singular '2' when 'R' (or the word 'Range') does not precede it.
twprge_regex = re.compile(
    r"""
    (T[ownship]{0,9})?
    [\.\-–—,\s]*
    (\d{1,3})
    [\.\-–—,\s]*
    (N[orth]{0,5}|S[outh]{0,5})
    [\.\-–—,;\|_~\s]*
    # If 'R' (or 'Range') does not appear, then we DISALLOW a range of singular '2'. This 
    # is to prevent over-matching "Lot 2, N2 W2" as <'T2N-R2W'> (for example). Otherwise, 
    # we are liable to have some aliquots break out T&R capturing, and vice-versa.
    (
    (R[ange]{0,6})?
    [\.\-–—,\s]*
    (\d{2,3}|[013-9])
    [\.\-–—,\s]*
    ((W[est]{0,3})|(E[ast]{0,3}))

    |

    (
    (R[ange]{0,6})
    [\.\-–—,\s]*
    (\d)  # This time, allow singular '2', because we specified 'R' (or 'Range') beforehand
    [\.\-–—,\s]*
    ((W[est]{0,3})|(E[ast]{0,3}))))
    """, re.IGNORECASE | re.VERBOSE)
# A singular '2' will show up as .group(12); and direction is .group(13).
# Otherwise, Range number is .group(6), and direction is .group(8)

# A more broadly-capturing regex for our standard T&R format (this one does
# not require 'T' or 'R', but also incorrectly captures "Lot 2, N2 W2" as
# 'T2N-R2W'. Should not be used for unprocessed text.)
twprge_broad_regex = re.compile(
    r"""(T[ownship]{0,9})?
    [\.\-–—,\s]*
    (\d{1,3})  # Township number
    [\.\-–—,\s]*
    (N[orth]{0,5}|S[outh]{0,5})  # Township N/S
    [\.\-–—,;\|_~\s]*
    ((R[ange]{0,6})?
    [\.\-–—,\s]*
    (\d{1,3})  # Range number
    [\.\-–—,\s]*
    ((W[est]{0,3})|(E[ast]{0,3})))  # range E/W""",
    re.IGNORECASE | re.VERBOSE)

# This should find sections formatted with up to 3 digits (e.g., '013', '009',
# etc. should be captured):
sec_regex = re.compile(
    r"""
    ((Section|Sect\.?|Sec\.?|Secion|Secton|Seciton|Sectn|Secn|§)s?  # The word "section"
    [\.\-–—\s]*
    (\d{1,3})\s*)  # Section number, between 1 and 3 digits
    """, re.IGNORECASE | re.VERBOSE)

# This should find multiple sections, formatted up to 3 digits (e.g.,
# "Sections 5, 6, 8 - 12"). Unpack with: unpack_sections()
# Note that this will also match a single section, so individual sections
# must be ruled out (i.e. individual section matches will have
# mo.group(12) != None). Can use funcs is_multisec() and is_singlesec()
# on the match objects.  This regex will also capture an optional colon
# at the end.
multiSec_regex = re.compile(
    r"""
    (
    ((Section|Sect\.?|Sec\.?|Secion|Secton|Seciton|Sectn|Secn|§)(s)?)  # i.e. "section(s)"
    \s*
    (\d{1,3})  # Section number (1 to 3 digits)
    )  # Will stop here for individual sections
    \s*
    (
    ([,;]?\s*([\.,\-\/–—]|th[rough]{3,6}\.?|thru\.?|to|[\.,;:]?\s*and|&)?)*  # 'thru' or 'and'
    \s*
    ((Section|Sect|Sec|Secion|Secton|Sectn|§)(s)?)?  # Optionally "section(s)" again
    \s*
    (\d{1,3})  # Section number (1 to 3 digits)
    )*  # Will go to here for multiSections
    \s*(:)?  # Finally, capture an optional colon at end (intervening whitespace allowed).
    """, re.IGNORECASE | re.VERBOSE)

# A multiSec regex that knows if a comma is behind:
comma_multiSec_regex = re.compile(
    r"""
    (
    ,\s*  # Looking for a comma before the multiSec. Otherwise the same as multiSec_regex
    (
    ((Section|Sect\.?|Sec\.?|Secion|Seciton|Secton|Sectn|Secn|§)(s)?)
    \s*
    (\d{1,3})
    )

    \s*
    (
    ([,;]?\s*([\.,\-\/–—]|th[rough]{3,6}\.?|thru\.?|to|[\.,;:]?\s*and|&)?)*
    \s*
    ((Section|Sect|Sec|Secion|Secton|Sectn|§)(s)?)?
    \s*
    (\d{1,3})
    )*
    )
     """, re.IGNORECASE | re.VERBOSE)

# A regex that will match 'Section' (or equivalent abbreviation / typo),
# even when there's no number:
noNum_sec_regex = re.compile(
    r'((Section|Sect\.?|Sec\.?|Secion|Seciton|Secton|Sectn|Secn|§)[\.\-–—\s]*(\d{0})\s*)',
    re.IGNORECASE)


########################################################################
# prepro regexes...
#
# Broader T&R captures for the description preprocessing algorithm.
# They're mostly the same as the normal twprge_regex, but with some
# characters being allowed outside various groupings i.e. some don't
# REQUIRE 'T', but will still match it if it's there). kwargs or config
# for defaultNS=‘n’ and defaultEW=‘w’ will fill in the township and
# range letters, as needed. Abbreviations and typos for 'Township' have
# also been locked down somewhat, to avoid excessive false matches.
########################################################################

# require T and R, but not n/s or e/w  (will need to fill in with
# kwarg-specified default):
preproTR_noNSWE_regex = re.compile(
    r"""
    T(  # Move 'T' to outside the optional match, because 'T' is required
    w\.?|
    wp\.?|
    o{0,2}w{0,2}n{0,2}s{1,2}h{1,2}i{0,2}p{0,2}|
    w{1,2}o{1,2}n{1,2}s{1,2}h{1,2}i{0,2}p{0,2}|
    o{1,2}w{1,2}n{1,2}s{1,2}h{1,2}i{0,2}p{0,2}|
    o{1,2}w{1,2}s{1,2}n{1,2}h{1,2}i{0,2}p{0,2}|
    o{1,2}w{1,2}n{1,2}h{1,2}s{1,2}i{0,2}p{0,2}|
    o{1,2}w{1,2}n{1,2}s{1,2}i{0,2}h{1,2}p{0,2}
    )?
    [\.\-–—,\s]*
    (\d{1,3})
    [\.\-–—,\s]*
    (N?[orth]{0,5}|S?[outh]{0,5})  # N/S is not required
    [\.\-–—,;\|_~\s]+
    (R([ange]{0,6})?  # 'R' is required
    [\.\-–—,\s]*
    (\d{1,3})
    [\.\-–—,\s]*
    ((W[est]{0,3})|(E[ast]{0,3}))?)  # E/W is not required
    """, re.IGNORECASE | re.VERBOSE)

# require T and w/e, but not R or n/s:
preproTR_noR_noNS_regex = re.compile(
    r"""
    T(  # Move 'T' to outside the optional match, because 'T' is required
    w\.?|
    wp\.?|
    o{0,2}w{0,2}n{0,2}s{1,2}h{1,2}i{0,2}p{0,2}|
    w{1,2}o{1,2}n{1,2}s{1,2}h{1,2}i{0,2}p{0,2}|
    o{1,2}w{1,2}n{1,2}s{1,2}h{1,2}i{0,2}p{0,2}|
    o{1,2}w{1,2}s{1,2}n{1,2}h{1,2}i{0,2}p{0,2}|
    o{1,2}w{1,2}n{1,2}h{1,2}s{1,2}i{0,2}p{0,2}|
    o{1,2}w{1,2}n{1,2}s{1,2}i{0,2}h{1,2}p{0,2}
    )?
    [\.\-–—,\s]*
    (\d{1,3})
    [\.\-–—,\s]*
    (N?[orth]{0,5}|S?[outh]{0,5})  # N/S is not required
    [\.\-–—,;\|_~\s]+
    ((R[ange]{0,6})?  # 'R' is not required
    [\.\-–—,\s]*
    (\d{1,3})
    [\.\-–—,\s]*
    ((W[est]{0,3})|(E[ast]{0,3})))  # E/W is required
    """, re.IGNORECASE | re.VERBOSE)

# require R and n/s, but not T or e/w:
preproTR_noT_noWE_regex = re.compile(
    r"""
    (  # Various Abbrevs / misspellings of Township
    T|
    Tw\.?|
    Twp\.?|
    To{0,2}w{0,2}n{0,2}s{1,2}h{1,2}i{0,2}p{0,2}|
    Tw{1,2}o{1,2}n{1,2}s{1,2}h{1,2}i{0,2}p{0,2}|
    To{1,2}w{1,2}n{1,2}s{1,2}h{1,2}i{0,2}p{0,2}|
    To{1,2}w{1,2}s{1,2}n{1,2}h{1,2}i{0,2}p{0,2}|
    To{1,2}w{1,2}n{1,2}h{1,2}s{1,2}i{0,2}p{0,2}|
    To{1,2}w{1,2}n{1,2}s{1,2}i{0,2}h{1,2}p{0,2}
    )?   # 'T' is not required.
    [\.\-–—,\s]*
    (\d{1,3})
    [\.\-–—,\s]*
    (N[orth]{0,5}|S[outh]{0,5})  # N/S is required
    [\.\-–—,;\|_~\s]+
    (R([ange]{0,6})?  # 'R' is required
    [\.\-–—,\s]*
    (\d{1,3})
    [\.\-–—,\s]*
    ((W[est]{0,3})|(E[ast]{0,3}))?)  # E/W is not required
    """, re.IGNORECASE | re.VERBOSE)

# With enough context, will capture T&R's with OCR artifacts (e.g.
# "TIS4N-R97W" instead of intended "T154N-R97W").  Gets converted to
# numerics in preprocess_tr_mo().
twprge_ocrScrub_regex = re.compile(
    r"""
    T(  # Move 'T' to outside the optional match, because 'T' is required
    w\.?|
    wp\.?|                                                 # Note that many characters are 
    [o0]{0,2}w{0,2}n{0,2}[s5]{1,2}h{1,2}[Il1]{0,2}p{0,2}|  #    interchangeable here:
    w{1,2}[o0]{1,2}n{1,2}s{1,2}h{1,2}[Il1]{0,2}p{0,2}|     #       'o' / '0', and
    [o0]{1,2}w{1,2}n{1,2}s{1,2}h{1,2}[Il1]{0,2}p{0,2}|     #       '1' / 'l' / 'I'
    [o0]{1,2}w{1,2}s{1,2}n{1,2}h{1,2}[Il1]{0,2}p{0,2}|     #       '5' / 'S'
    [o0]{1,2}w{1,2}n{1,2}h{1,2}s{1,2}[Il1]{0,2}p{0,2}|     # (These are commonly swapped 
    [o0]{1,2}w{1,2}n{1,2}s{1,2}[Il1]{0,2}h{1,2}p{0,2}      #                      by OCR)
    )?
    [\.\-–—,\s]*
    ([0-9SOIl\]\|]{1,3})  # Twp num, but capturing some OCR non-numeric letters / symbols
    [\.\-–—,\s]*
    (N[orth]{0,5}|S[outh]{0,5})  # Township N/S
    [\.\-–—,;\|_~\s]*
    # If 'R' (or 'Range') does not appear, then we DISALLOW a range of singular '2'. This 
    # is to prevent over-matching "Lot 2, N2 W2" as <'T2N-R2W'> (for example). Otherwise, 
    # we are liable to have some aliquots break out T&R capturing, and vice-versa.
    (
    (R[ange]{0,6})?
    [\.\-–—,\s]*
    # Rge num, but capturing some OCR non-numeric letters / sym (singular '2' not allowed):
    ([0-9SOIl\]\|]{2,3}|[013-9SOIl\]\|])
    [\.\-–—,\s]*
    ((W[est]{0,3})|(E[ast]{0,3}))

    |

    (
    (R[ange]{0,6})
    [\.\-–—,\s]*
    (\d)  # This time, allow singular '2', because we specified 'R' (or 'Range') beforehand 
    [\.\-–—,\s]*
    ((W[est]{0,3})|(E[ast]{0,3}))))  # range E/W""",
    re.IGNORECASE | re.VERBOSE)

# A regex for extra context around TR_noR_noNS (need to rule out "Lots"
# at the start of such a match):
lots_context_regex = re.compile(r'Lo?ts?|Lo?s?t', re.IGNORECASE)

########################################################################
# Note that twprge_regex will match between 0 and 9 characters in
# [ownship] and between 0 and 5 characters in [ange]. This was done to
# capture common typos / abbreviations of "Township" and "Range". This
# was the best trade-off of robust functionality vs. risk of false
# positives. It should return pretty good results when known PLSS
# descriptions are fed through the algorithm. However, there remains the
# possibility of false positives, especially if unvetted text is fed
# into the algorithm (i.e. if a user feeds in text that hasn't been
# pared down to a known PLSS description).
#
# The same methodology was NOT used for sections, because the section
# regex do not have nearly the same amount of context built into it.
# r'S[ection]{0,7}' would probably match way too many false positives to
# be useful.
#
# If you're working with a data set that is formatted in such a way that
# requires a broader regex, either for twprge or for section, you will
# likely need to redefine the regexes accordingly.  (Probably also true
# for the depth_regex below.)
########################################################################

# For unpacking TRS into its component parts -- break into twp, rge, sec
# with break_trs():
TRS_unpacker_regex = re.compile(
    r"""((\d{1,3}[ns])(\d{1,3}[we])|(TRerr)_?)
    ((\d{1,2})|(secError))?""", re.VERBOSE | re.IGNORECASE)


########################################################################
# These are used for warning flags:
########################################################################

# Will be used to flag possible wellbore exceptions:
well_regex = re.compile(r'(wellbore|well)', re.IGNORECASE)

# Will be used to flag possible depth limitations:
depth_regex = re.compile(r'(depth|formation|surf|down|form|top|base)', re.IGNORECASE)

# Will be used to flag 'including' language:
including_regex = re.compile(r'incl', re.IGNORECASE)

# Will be used to flag possible exceptions/limitations:
less_except_regex = re.compile(r'(less|except|limit)', re.IGNORECASE)

# Looking for 'insofar' language:
isfa_except_regex = re.compile(r'(in\s?so\s?far)', re.IGNORECASE)


########################################################################
# The next block of regexes are for parsing aliquots into QQ's and
# pulling standard Lots from PLSS descriptions:
########################################################################

# QQ regexes
NE_regex = re.compile(
    r'(\b|¼|4|½|2)(NE|Nort[h]?\s*East)\s*((One)?\s*Q[uarter]{4,7}|1\/?4|\/?4|¼)',
    re.IGNORECASE)
SE_regex = re.compile(
    r'(\b|¼|4|½|2)(SE|Sout[h]?\s*East)\s*((One)?\s*Q[uarter]{4,7}|1\/?4|\/?4|¼)',
    re.IGNORECASE)
NW_regex = re.compile(
    r'(\b|¼|4|½|2)(NW|Nort[h]?\s*West)\s*((One)?\s*Q[uarter]{4,7}|1\/?4|\/?4|¼)',
    re.IGNORECASE)
SW_regex = re.compile(
    r'(\b|¼|4|½|2)(SW|Sout[h]?\s*West)\s*((One)?\s*Q[uarter]{4,7}|1\/?4|\/?4|¼)',
    re.IGNORECASE)

N2_regex = re.compile(
    r'(\b|¼|4|½|2)(N\.?|No\.?|Nort[h]?)\s*((One)?\s*Half|1\/?2|\/?2|½)', re.IGNORECASE)
S2_regex = re.compile(
    r'(\b|¼|4|½|2)(S\.?|So\.?|Sout[h]?)\s*((One)?\s*Half|1\/?2|\/?2|½)', re.IGNORECASE)
E2_regex = re.compile(
    r'(\b|¼|4|½|2)(E\.?|East)\s*((One)?\s*Half|1\/?2|\/?2|½)', re.IGNORECASE)
W2_regex = re.compile(
    r'(\b|¼|4|½|2)(W\.?|West)\s*((One)?\s*Half|1\/?2|\/?2|½)', re.IGNORECASE)

# Find 'ALL', with options for context. Will only match 'ALL' at the beginning of a word
# boundary.
ALL_regex = re.compile(r'\b(ALL)(.{1,6})?', re.IGNORECASE)

# For culling context around "ALL":
ALL_context_regex = re.compile(r'(in+|of+|th[eatiso]{0,3}|l[ying]{0,5})', re.IGNORECASE)

# cleanQQ regexes, for parsing aliquots under cleanQQ=True conditions.
# Will match much more broadly.
cleanNE_regex = re.compile(
    r'()(NE|Nort[h]?\s*East)\s*((One)?\s*Q[uarter]{4,7}|1\/?4|\/?4|¼)?', re.IGNORECASE)
cleanSE_regex = re.compile(
    r'()(SE|Sout[h]?\s*East)\s*((One)?\s*Q[uarter]{4,7}|1\/?4|\/?4|¼)?', re.IGNORECASE)
cleanNW_regex = re.compile(
    r'()(NW|Nort[h]?\s*West)\s*((One)?\s*Q[uarter]{4,7}|1\/?4|\/?4|¼)?', re.IGNORECASE)
cleanSW_regex = re.compile(
    r'()(SW|Sout[h]?\s*West)\s*((One)?\s*Q[uarter]{4,7}|1\/?4|\/?4|¼)?', re.IGNORECASE)

# N2, S2, E2, and W2 are the same under cleanQQ conditions, since there
# still must be SOME designator that it's a 'half'.

# 'E2NE' should be enough context to interpret it as the E½NE¼. This
# regex can be applied after subbing the other 'half' regexes in for
# their cleaner counterparts, so 'E2NE' -> 'E½NE' --> 'E½NE¼'.
# Must be at word boundaries, per \b.
halfPlusQ_regex = re.compile(
    r'(\b|½)((N|E|S|W)½(\s*| of | of the )(NE|NW|SE|SW))¼?\b', re.IGNORECASE)

# For breaking down the identified lots strings:
through_regex = re.compile(r'([\-–—]|th[rough]{3,6}\.?|thru\.?|to)', re.IGNORECASE)

# Lot regex (should capture entire match, but then requires some processing
# to unpack it):
lot_regex = re.compile(
    r"""
    (((()(()))))  # Blank groups, so that the structure is identical to lot_with_aliquot_regex
    ((
    (L\.?o?t?(s?))
    \s*
    (\d{1,3})
    \s*
    (\(\d{0,3}[\.,]?\d{0,4}\))?
    )  # If just one lot, will stop here
    (
    (
    \s*
    ([\.,\-–—]|th[rough]{3,6}\.?|thru\.?|to|[\.,;:]?\s*and|&)  # 'through' or 'and'
    \s*
    ((and|\&)?\s*L\.?o?t?(s?))?  # 'and lots'
    \s*
    (\d{1,3})
    \s*
    (\(\d{0,3}[\.,]?\d{0,4}\))?  # Stated acreage, i.e. the '(43.59)' in 'Lots 5(43.59)'
    )+
    )?)
    """, re.IGNORECASE | re.VERBOSE)
# Guide to lot_regex .groups:
# group(11) is the first lot;
# group(12) is the stated acreage of the first lot.
# The following exist IF AND ONLY IF more than one lot was found:
#     group(19) is the right-most lot IF AND ONLY IF more than 1 lot was found;
#     group(15) is the connector between the last lot and the lot before it,
#         possibly with superfluous text / characters ('and' or 'through'
#         -- or equivalent symbol / abbrev)
#     group(14) ends with the stated acreage of the last lot ONLY when it occurs
#         at the end of the matched string.  Get that stated acreage with
#         lotAcres_unpacker_regex, which is baked into the get_lot_acres()
#         function.


lot_with_aliquot_regex = re.compile(
    r"""
    (((([NESW]½)|((NE|NW|SE|SW)¼))+)\ ?of\ )?  # optional leading aliquot division
    ((
    (L\.?o?t?(s?))
    \s*
    (\d{1,3})
    \s*
    (\(\d{0,3}[\.,]?\d{0,4}\))?
    )  # If just one lot, will stop here
    (
    (
    \s*
    ([\.,\-–—]|th[rough]{3,6}\.?|thru\.?|to|[\.,;:]?\s*and|&)  # 'through' or 'and'
    \s*
    ((and|\&)?\s*L\.?o?t?(s?))?  # 'and lots'
    \s*
    (\d{1,3})
    \s*
    (\(\d{0,3}[\.,]?\d{0,4}\))?  # Stated acreage, i.e. the '(43.59)' in 'Lots 5(43.59)'
    )+
    )?)
    """, re.IGNORECASE | re.VERBOSE)
# Guide to lot_with_aliquot_regex groups (using "N½N½ of Lots 1 - 3" as
# the example):
#  -- group(1) is the entire aliquot component + ' of '
#       (i.e. 'N½N½ of ' in the example);
#  -- group(2) is the entire aliquot component without the 'of'
#       (i.e. 'N½N½' in the example);
#  -- group(7) is the entire lots component
#       (i.e. 'Lots 1 - 3' in the example)

lotAcres_unpacker_regex = re.compile(r'\((\d{0,3}[\.,]?\d{0,4})\)')

########################################################################
# QQ Unpacker regexes
########################################################################
aliquot_unpacker_regex = re.compile(
    r'(([NESW]½)|((NE|NW|SE|SW)¼))*(([NESW]½)|((NE|NW|SE|SW)¼))')
# The last group is always the dominant (right-most) division (may or
# may not have the fraction attached). Everything to the left of that
# needs to be recursively processed.

# Will capture the aliquot component (without fraction) in group(2), but
# should only be used on preprocessed aliquot blocks (e.g., "E½NW¼NE¼"
# or "ALL"):
single_aliquot_unpacker_regex = re.compile(r"(([NESW]{1,2}|ALL)[½¼]?)")

# For cutting out whitespace and 'of the' or 'of' between identified
# aliquot components:
aliquot_intervener_remover_regex = re.compile(
    r"""
    (([NESW]½)|((NE|NW|SE|SW)¼))  # first aliquot component
    \s*  # any amount of whitespace (to be removed)
    (
    (\s+|of|o|f|o+f+)\s*(t+h+e+|t+e+h+|t+h+|t+)?  # 'of the' or 'of' (to be removed)
    \s*  # any amount of whitespace (to be removed)
    )
    (([NESW]½)|((NE|NW|SE|SW)¼))  # second aliquot component
    """, re.IGNORECASE | re.VERBOSE)
### group(1) is the first aliquot component
#   (i.e. 'N½' in the example "N½ of the NE¼");
### group(8) is the second aliquot component
#   (i.e. 'NE¼' in the example "N½ of the NE¼").


# For cutting out whitespace and 'of the' or 'of' between an aliquot and
# lot (for handling 'N/2 of Lot 1'):
aliquot_lot_intervener_scrubber_regex = re.compile(
    r"""
    (([NESW]½)|((NE|NW|SE|SW)¼))  # first aliquot component
    \s*  # any amount of whitespace (to be removed)
    (
    \s*(of|o+f+)\s*(t+h+e+|t+e+h+|t+h+|t+)?  # 'of the' or 'of' (to be converted to ' of ')
    \s*  # any amount of whitespace (to be removed)
    )
    (  # Lot component starts at the beginning of this line
    (L\.?o?t?(s?))
    \s*
    (\d{1,3})
    )  # The lot component ends here
    """, re.IGNORECASE | re.VERBOSE)
### group(1) is the first aliquot component
#   (i.e. 'N½' in the example "N½ of the NE¼");
### group(8) is the second aliquot component
#   (i.e. 'NE¼' in the example "N½ of the NE¼").


# Looking for the phrase (or abbreviation for) 'Principal Meridian' and
# following symbols and whitespace. Not the cleanest definition, but
# will only be used in limited places (between a twprge_regex match and
# a sec_regex match), so it need not be too tight:
pm_regex = re.compile(
    r"""(P\.?\s{0,10}M\.?|
    P{1,2}r{1,2}i{0,2}n{0,2}c{0,2}i{0,2}p{0,2}a{0,2}l{0,2}\s
    {0,10}M{1,2}e{0,2}r{0,2}i{0,2}d{0,2}i{0,2}a{0,2}n{0,2})
    \s*[:,;\.\-–—]*\s*
    """, re.IGNORECASE | re.VERBOSE)

# A twprge regex that should also capture P.M.
twprge_pm_regex = re.compile(
    r"""(T[ownship]{0,9})?
    [\.\-–—,\s]*
    (\d{1,3})  # Township number
    [\.\-–—,\s]*
    (N[orth]{0,5}|S[outh]{0,5})  # Township N/S
    [\.\-–—,;\|_~\s]*
    # If 'R' (or 'Range') does not appear, then we DISALLOW a range of singular '2'. This 
    # is to prevent over-matching "Lot 2, N2 W2" as <'T2N-R2W'> (for example). Otherwise,
    # we are liable to have some aliquots break out T&R capturing, and vice-versa.
    (
    (R[ange]{0,6})?
    [\.\-–—,\s]*
    (\d{2,3}|[013-9])
    [\.\-–—,\s]*
    ((W[est]{0,3})|(E[ast]{0,3}))

    |

    (
    (R[ange]{0,6})
    [\.\-–—,\s]*
    (\d)  # This time, allow singular '2', because we've specified 'R' (or 'Range') beforehand. 
    [\.\-–—,\s]*
    ((W[est]{0,3})|(E[ast]{0,3}))))
    (\s*[:,;\.\-–—]*\s*(o*f*)?\s*(t*h*e*|t*e*h*|h*t*e|h*e*t*)?\s*(.{0,15})\s*(P\.?\s{0,10}M\.?|
    P{1,2}r{1,2}i{0,2}n{0,2}c{0,2}i{0,2}p{0,2}a{0,2}l{0,2}\s
    {0,10}M{1,2}e{0,2}r{0,2}i{0,2}d{0,2}i{0,2}a{0,2}n{0,2}))?
    """, re.IGNORECASE | re.VERBOSE)

# When the section number(s) occur /within/ the description block (e.g.,
# 'That portion of Section 14 lying west of RR')
sec_within_desc_regex = re.compile(
    r"""
    .{3,}
    (
    (((Section|Sect|Sec|Secion|Secton|Sectn|Secn|§)(s)?)\s*(\d{1,3}))
    \s*
    (([,;]?\s*([\.,\-\/–—]|th[rough]{3,6}\.?|thru\.?|to|[\.,;:]?\s*and|&)?)*
    \s*((Section|Sect|Sec|Secion|Secton|Sectn|§)(s)?)?
    \s*(\d{1,3}))?
    .*)+
    """, re.IGNORECASE | re.VERBOSE)
