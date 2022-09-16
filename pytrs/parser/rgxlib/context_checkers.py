
import re

from .sec import *
from .twprge import *


sec_twprge_in_between = re.compile(
    fr"""
    {multisec_regex.pattern}
    \s*
    (?P<between_found>
        in
        |
        of
        |
        ,
        |
        all\s*of
        |
        all\s*(with)?in
        |
        lying\s*(with)?in
        |
        that\s*lies\s*(with)?in
    )
    \s*
    {twprge_regex.pattern}
    """, re.VERBOSE | re.IGNORECASE)
