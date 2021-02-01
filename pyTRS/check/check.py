# Copyright (c) 2020, James P. Imes, All rights reserved.

"""
Functions for quick-checking some attributes of PLSSDesc or Tract
objects.
"""

def check_flag(target, flag=None, getLines=False):
    """
    Check whether the flagList in `target` (a PLSSDesc object or a Tract
    object) contains the specified flag (flag='specify string').
    Optionally returns a list of the lines in the text that raised that
    warning flag, with getLines=True.

    NOTE: If `target` was passed as a type other than PLSSDesc or Tract,
    this will return None.
    """

    from pyTRS.parser import PLSSDesc, Tract

    # Feed in only a PLSSDesc object or Tract object.
    if not isinstance(target, (PLSSDesc, Tract)):
        return None

    if not isinstance(flag, str):
        raise TypeError(
            "Error: `flag` must be type str, being the name of the flag "
            "to look for, ex: `flag='secError'`")

    # Get a bool, whether the flag is in either flagList
    all_flags = target.wFlagList + target.eFlagList
    flagFound = flag in all_flags
    if getLines:
        flagLines = []
        for lineTuple in all_flags:
            if lineTuple[0] == flag:
                flagLines.append(lineTuple[1])
        return flagFound, flagLines
    else:
        return flagFound