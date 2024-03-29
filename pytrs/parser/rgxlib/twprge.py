
"""
Regex patterns for Twp/Rge and related preprocessing.
"""

import re

from .misc import (
    comma_wb_lookbehind,
)

twprge_regex = re.compile(
    r"""
    ((?<=[,;:])|(?<=\b))    # Word boundary or comma (or similar) lookbehind.
     
    ((T[ownship]{0,9})      # The word or symbol for "Township" (optional).
    [\.\-–—,\s]*)?          # Deadspace between "Township" and twpnum.
    (?P<twpnum>\d{1,3})     # twpnum
    [\.\-–—,\s]*            # Deadspace between twpnum and n/s.
    (?P<ns>N[orth]{0,5}|S[outh]{0,5})   # n/s.
    [\.\-–—,;\|_~\s]*       # Deadspace between Twp and Rge.
        
    ((
        # Range Version 1 (all cases EXCEPT "Range 2") --
        # Note: We DISALLOW a rgenum of singular '2'. This is to prevent
        # over-matching "Lot 2, N2 W2" as <'T2N-R2W'> (for example).
        # Otherwise, we are liable to have some aliquots break out T&R
        # capturing, and vice-versa.
        
        ((R[ange]{0,6})     # The word or symbol for "Range"  (optional).
        [\.\-–—,\s]*)?      # Deadspace between "Range" and rgenum.
        (?P<rgenum>\d{2,3}|[013-9])     # rgenum
    )
    
    |
    
    (
        # Range Version 2 (edge case "Range 2") --
        # This time, allow singular rgenum '2', because we specified 'R'
        # (or 'Range') beforehand.
        
        (R[ange]{0,6})          # The word or symbol for "Range" (required).
        [\.\-–—,\s]*            # Deadspace between "Range" and rgenum.
        (?P<rgenum_edgecase_rge2>2)    # rgenum (edge case).
    ))
    
    [\.\-–—,\s]*            # Deadspace between rgenum and e/w.
    (?P<ew>W[est]{0,3}|E[ast]{0,3})    # e/w.
    """, re.IGNORECASE | re.VERBOSE)


########################################################################
# preprocessor regexes...
#
# Broader Twp/Rge captures for the description preprocessing algorithm.
# They're mostly the same as the normal twprge_regex, but with some
# characters being allowed outside various groupings (i.e. some don't
# require 'T', but will still match it if it's there). kwargs or config
# for default_ns='n' and default_ew='w' will fill in the township and
# range letters, as needed. Abbreviations and typos for 'Township' have
# also been locked down somewhat, to avoid excessive false matches.
########################################################################

# Preprocessing Twp/Rge regexes.


# Require 'T' (Twp) and 'R' (Rge), but not n/s or e/w.
pp_twprge_no_nswe = re.compile(
    r"""
    ((?<=[,;:])|(?<=\b))    # Word boundary or comma (or similar) lookbehind.
    
    # The word or symbol for "Township". (At least "T" is required.)
    T(
    w\.?|
    wp\.?|
    o{0,2}w{0,2}n{0,2}s{1,2}h{1,2}i{0,2}p{0,2}|
    w{1,2}o{1,2}n{1,2}s{1,2}h{1,2}i{0,2}p{0,2}|
    o{1,2}w{1,2}n{1,2}s{1,2}h{1,2}i{0,2}p{0,2}|
    o{1,2}w{1,2}s{1,2}n{1,2}h{1,2}i{0,2}p{0,2}|
    o{1,2}w{1,2}n{1,2}h{1,2}s{1,2}i{0,2}p{0,2}|
    o{1,2}w{1,2}n{1,2}s{1,2}i{0,2}h{1,2}p{0,2}
    )?
    
    [\.\-–—,\s]*            # Deadspace between "Township" and twpnum.
    (?P<twpnum>\d{1,3})     # twpnum
    [\.\-–—,\s]*            # Deadspace between twpnum and n/s.
    (?P<ns>N[orth]{0,5}|S[outh]{0,5})?      # n/s (optional)
    
    [\.\-–—,;\|_~\s]+       # Deadspace between Twp and Rge.
    
    R([ange]{0,6})?         # The word or symbol for "Range" (at least "R" is required).
    [\.\-–—,\s]*            # Deadspace between "Range" and rgenum.
    (?P<rgenum>\d{1,3})     # rgenum
    [\.\-–—,\s]*            # Deadspace between rgenum and e/w.
    (?P<ew>W[est]{0,3}|E[ast]{0,3})?        # e/w (optional)
    """, re.IGNORECASE | re.VERBOSE)


# Require 'T' (Twp) and e/w, but not 'R' (Rge) or n/s.
pp_twprge_no_nsr = re.compile(
    r"""
    ((?<=[,;:])|(?<=\b))    # Word boundary or comma (or similar) lookbehind.
    
    # The word or symbol for "Township". (At least "T" is required.)
    T(
    w\.?|
    wp\.?|
    o{0,2}w{0,2}n{0,2}s{1,2}h{1,2}i{0,2}p{0,2}|
    w{1,2}o{1,2}n{1,2}s{1,2}h{1,2}i{0,2}p{0,2}|
    o{1,2}w{1,2}n{1,2}s{1,2}h{1,2}i{0,2}p{0,2}|
    o{1,2}w{1,2}s{1,2}n{1,2}h{1,2}i{0,2}p{0,2}|
    o{1,2}w{1,2}n{1,2}h{1,2}s{1,2}i{0,2}p{0,2}|
    o{1,2}w{1,2}n{1,2}s{1,2}i{0,2}h{1,2}p{0,2}
    )?
    
    [\.\-–—,\s]*            # Deadspace between "Township" and twpnum.
    (?P<twpnum>\d{1,3})     # twpnum
    [\.\-–—,\s]*            # Deadspace between twpnum and n/s.
    (?P<ns>N[orth]{0,5}|S[outh]{0,5})?      # n/s (optional)
    
    [\.\-–—,;\|_~\s]+       # Deadspace between Twp and Rge.
    
    (R[ange]{0,6})?         # The word or symbol for "Range" (optional).
    [\.\-–—,\s]*            # Deadspace between "Range" and rgenum.
    (?P<rgenum>\d{1,3})     # rgenum
    [\.\-–—,\s]*            # Deadspace between rgenum and e/w
    (?P<ew>W[est]{0,3}|E[ast]{0,3})         # e/w (required)
    """, re.IGNORECASE | re.VERBOSE)


# Require 'R' (Rge) and n/s, but not 'T' (Twp) or e/w.
pp_twprge_no_ewt = re.compile(
    r"""
    ((?<=[,;:])|(?<=\b))    # Word boundary or comma (or similar) lookbehind.
    
    # The word or symbol for "Township" (optional).
    (
    T|
    Tw\.?|
    Twp\.?|
    To{0,2}w{0,2}n{0,2}s{1,2}h{1,2}i{0,2}p{0,2}|
    Tw{1,2}o{1,2}n{1,2}s{1,2}h{1,2}i{0,2}p{0,2}|
    To{1,2}w{1,2}n{1,2}s{1,2}h{1,2}i{0,2}p{0,2}|
    To{1,2}w{1,2}s{1,2}n{1,2}h{1,2}i{0,2}p{0,2}|
    To{1,2}w{1,2}n{1,2}h{1,2}s{1,2}i{0,2}p{0,2}|
    To{1,2}w{1,2}n{1,2}s{1,2}i{0,2}h{1,2}p{0,2}
    )?
    
    [\.\-–—,\s]*            # Deadspace between "Township" and twpnum.
    (?P<twpnum>\d{1,3})     # twpnum
    [\.\-–—,\s]*            # Deadspace between twpnum and n/s
    (?P<ns>N[orth]{0,5}|S[outh]{0,5})   # n/s (required)
    
    [\.\-–—,;\|_~\s]+       # Deadspace between Twp and Rge.
    
    R([ange]{0,6})?         # The word or symbol for "Range" (at least "R" required).
    [\.\-–—,\s]*            # Deadspace between "Range" and rgenum.
    (?P<rgenum>\d{1,3})     # rgenum
    [\.\-–—,\s]*            # Deadspace between rgenum and e/w
    (?P<ew>W[est]{0,3}|E[ast]{0,3})?    # e/w (optional).
    """, re.IGNORECASE | re.VERBOSE)


# With enough context, will capture T&R's with OCR artifacts (e.g.
# "TIS4N-R97W" instead of intended "T154N-R97W").
pp_twprge_ocr_scrub = re.compile(
    r"""
    ((?<=[,;:])|(?<=\b))    # Word boundary or comma (or similar) lookbehind.
    
    # The word or symbol for "Township". (At least "T" is required.)
    T(
    w\.?|
    wp\.?|                                                 # Note that many characters are 
    [o0]{0,2}w{0,2}n{0,2}[s5]{1,2}h{1,2}[Il1]{0,2}p{0,2}|  #    interchangeable here:
    w{1,2}[o0]{1,2}n{1,2}s{1,2}h{1,2}[Il1]{0,2}p{0,2}|     #       'o' / '0', and
    [o0]{1,2}w{1,2}n{1,2}s{1,2}h{1,2}[Il1]{0,2}p{0,2}|     #       '1' / 'l' / 'I'
    [o0]{1,2}w{1,2}s{1,2}n{1,2}h{1,2}[Il1]{0,2}p{0,2}|     #       '5' / 'S'
    [o0]{1,2}w{1,2}n{1,2}h{1,2}s{1,2}[Il1]{0,2}p{0,2}|     # (These are commonly swapped 
    [o0]{1,2}w{1,2}n{1,2}s{1,2}[Il1]{0,2}h{1,2}p{0,2}      #    by OCR.)
    )?
    
    [\.\-–—,\s]*            # Deadspace between "Township" and twpnum.
    (?P<twpnum>[0-9SOIl\]\|]{1,3})      # twpnum, but capturing some OCR 
                                        # non-numeric letters / symbols.
    [\.\-–—,\s]*            # Deadspace between twpnum and n/s.
    (?P<ns>N[orth]{0,5}|S[outh]{0,5})   # n/s (required)
    
    [\.\-–—,;\|_~\s]*       # Deadspace between Twp and Rge
    
    # Note: We DISALLOW a rgenum of singular '2'. This is to prevent
    # over-matching "Lot 2, N2 W2" as <'T2N-R2W'> (for example).
    # Otherwise, we are liable to have some aliquots break out T&R
    # capturing, and vice-versa.
    
    (R[ange]{0,6})?         # The word or symbol "Range" (optional).
    [\.\-–—,\s]*            # Deadspace between "Range" and rgenum.
    
    # rgenum, but capturing some OCR non-numeric letters / symbols.
    (?P<rgenum>[0-9SOIl\]\|]{2,3}|[013-9SOIl\]\|]) # (Note that singular '2' not allowed).
    
    [\.\-–—,\s]*            # Deadspace between rgenum and e/w. 
    (?P<ew>W[est]{0,3}|E[ast]{0,3})     # e/w (required).
    """,
    re.IGNORECASE | re.VERBOSE)


# Looking for the phrase (or abbreviation for) 'Principal Meridian' and
# following symbols and whitespace. Captures some misspellings. (These
# are not tightly defined, so this pattern should not be used in wide
# contexts. It is used in `pp_twprge_pm` to scrub Principal Meridian out
# of Twp/Rge's in the preprocessor.)
pm_regex = re.compile(
    r"""
    # Abbreviated 'P.M.'
    ((P\.?\s{0,10}M\.?)
    
    # Or ...
    |
    
    # Spelled out (allowing for some misspelling).
    (P{1,2}r{1,2}i{0,2}n{0,2}c{0,2}i{0,2}p{0,2}a{0,2}l{0,2}\s
    {0,10}M{1,2}e{0,2}r{0,2}i{0,2}d{0,2}i{0,2}a{0,2}n{0,2}))
    """, re.IGNORECASE | re.VERBOSE)


# Compile a twprge regex that should also capture P.M.
pp_twprge_pm = re.compile(
    fr"""
    # Twp/Rge pattern.
    {twprge_regex.pattern}
    
    # Deadspace ...
    (\s*[:,;\.\-–—]*\s*)
    
    # of the ...
    (o*f*)?\s*(t*h*e*|t*e*h*|h*t*e|h*e*t*)?\s*
    
    # Anything, arbitrarily capped at 25 characters.
    # (Double-curly brackets to escape the f-string syntax.)
    (.{{0,25}})
    
    # Deadspace ...
    (\s*[:,;\.\-–—]*)
    
    # Principal Meridian pattern.
    {pm_regex.pattern}
    """, re.IGNORECASE | re.VERBOSE)


# Preprocessing twprge regex pattern for identifying and removing
# trailing commas and similar characters.
pp_twprge_comma_remove = re.compile(
    fr"""
    # Twp/Rge pattern.
    {twprge_regex.pattern}

    # Deadspace ...
    ([\s:,;\.\-–—]*)
    """, re.IGNORECASE | re.VERBOSE)
