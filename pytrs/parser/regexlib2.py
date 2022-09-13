
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


# Preprocessing Twp/Rge regexes.

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
