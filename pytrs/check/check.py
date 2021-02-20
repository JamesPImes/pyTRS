# Copyright (c) 2020, James P. Imes, All rights reserved.

"""
Functions for quick-checking some attributes of PLSSDesc or Tract
objects.
"""


def check_flag(target, flag, get_lines=False):
    """
    Check whether the `.w_flags` or `.e_flags`. list in `target` (a
    PLSSDesc object or a Tract object) contains the specified `flag`.
    Optionally return also a list of the lines in the text that raised
    that flag, with `get_lines=True`.

    NOTE: If `target` was passed as a type other than PLSSDesc or Tract,
    this will return None.

    :param target: A pytrs.Tract or pytrs.PLSSDesc object.
    :param flag: A string, specifying the error flag or warning flag
    that should be looked for.
    :param get_lines: A bool, specifying whether or not to also return a
    list of the lines (or context) that raised the requested `flag`.
    :return: If `get_lines=False` (the default) will return a bool. If
    `get_lines=True`, then will return a 2-tuple, composed of the bool
    and a list of the lines or context that raised the `flag`.
    """

    from pytrs.parser import PLSSDesc, Tract

    # Feed in only a PLSSDesc object or Tract object.
    if not isinstance(target, (PLSSDesc, Tract)):
        raise TypeError(
            "`target` must be either a pytrs.PLSSDesc "
            "or pytrs.Tract object"
        )

    # Get a bool, whether the flag is in either flag list
    all_flags = target.w_flags + target.e_flags
    flag_found = flag in all_flags
    if not get_lines:
        return flag_found

    all_flag_lines = target.w_flag_lines + target.e_flag_lines
    context = [
        line for flag_, line in all_flag_lines if flag_ == flag
    ]
    return flag_found, context
