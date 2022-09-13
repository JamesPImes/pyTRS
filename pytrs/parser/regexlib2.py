
import re

twprge_regex = re.compile(
    r"""
    (T[ownship]{0,9})?      # The word or symbol for "Township".
    [\.\-–—,\s]*            # Deadspace between "Township" and twpnum.
    (?P<twpnum>\d{1,3})     # twpnum
    [\.\-–—,\s]*            # Deadspace between twpnum and n/s.
    (?P<ns>N[orth]{0,5}|S[outh]{0,5})   # n/s.
    [\.\-–—,;\|_~\s]*       # Deadspace between Twp and Rge.
    
    # Note: if 'R' (or 'Range') does not appear, then we DISALLOW a
    # range of singular '2'. This is to prevent over-matching "Lot 2,
    # N2 W2" as <'T2N-R2W'> (for example). Otherwise, we are lible to
    # have some aliquots break out T&R capturing, and vice-versa.
    (
    (R[ange]{0,6})?         # The word or symbol for "Range".
    [\.\-–—,\s]*            # Deadspace between "Range" and rgenum.
    (?P<rgenum>\d{2,3}|[013-9])     # rgenum
    [\.\-–—,\s]*            # Deadspace between rgenum and e/w.
    (?P<ew>(W[est]{0,3})|(E[ast]{0,3}))     # e/w.
    )
    """, re.IGNORECASE | re.VERBOSE)


# TODO: I don't think this one is needed. Use twprge_regex instead.
# twprge_broad_regex


# Preprocessing Twp/Rge regexes.

# TODO: Put this regex pattern into appropriate preprocess list.
twprge_regex_rge2 = re.compile(
    r"""
    (T[ownship]{0,9})?      # The word or symbol for "Township".
    [\.\-–—,\s]*            # Deadspace between "Township" and twpnum.
    (?P<twpnum>\d{1,3})     # twpnum
    [\.\-–—,\s]*            # Deadspace between twpnum and n/s.
    (?P<ns>N[orth]{0,5}|S[outh]{0,5})   # n/s.
    [\.\-–—,;\|_~\s]*       # Deadspace between Twp and Rge.
    
    # Unlike `twprge_regex`, allow range of singular '2', but require
    # 'R' (or 'Range') beforehand.
    (
    (R[ange]{0,6})          # The word or symbol for "Range".
    [\.\-–—,\s]*            # Deadspace between "Range" and rgenum.
    (?P<rgenum>2)           # rgenum
    [\.\-–—,\s]*            # Deadspace between rgenum and e/w.
    (?P<ew>(W[est]{0,3})|(E[ast]{0,3}))     # e/w.
    )
    """, re.IGNORECASE | re.VERBOSE)


########################################################################
# prepro regexes...
#
# Broader Twp/Rge captures for the description preprocessing algorithm.
# They're mostly the same as the normal twprge_regex, but with some
# characters being allowed outside various groupings i.e. some don't
# REQUIRE 'T', but will still match it if it's there). kwargs or config
# for default_ns='n' and default_ew='w' will fill in the township and
# range letters, as needed. Abbreviations and typos for 'Township' have
# also been locked down somewhat, to avoid excessive false matches.
########################################################################

# Require 'T' (Twp) and 'R' (Rge), but not n/s or e/w.
pp_twprge_no_nswe = re.compile(
    r"""
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
    (?P<ns>N[orth]{0,5}|S[outh]{0,5})?     # n/s (optional)
    
    [\.\-–—,;\|_~\s]+       # Deadspace between Twp and Rge.
    
    R([ange]{0,6})?         # The word or symbol for "Range" (at least "R" is required).
    [\.\-–—,\s]*            # Deadspace between "Range" and rgenum.
    (?P<rgenum>\d{1,3})     # rgenum
    [\.\-–—,\s]*            # Deadspace between rgenum and e/w.
    (?P<ew>W[est]{0,3}|E[ast]{0,3})?        # e/w (optional)
    """, re.IGNORECASE | re.VERBOSE)
