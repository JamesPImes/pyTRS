# Copyright (c) 2020-2022, James P. Imes, all rights reserved.

"""
Misc. tools for parsing, etc.
"""


def num_to_alpha(num):
    """
    Convert a number (integer) into an alpha (``1`` --> ``'A'``,
    ``'26'`` --> ``'Z'``, ``27`` -- > ``'AA'``) -- from ``A`` through
    ``ZZ``.
    """
    return (
        ((num - 1) // 26 > 0) * chr((num - 1) // 26 + ord('A') - 1)
        + chr((num - 1) % 26 + ord('A'))
    )


def alpha_to_num(alpha):
    """
    Convert an alpha into an integer (``'A'`` --> `1`,
    ``'Z'`` --> ``26``, ``'AA'`` --> ``27``) -- from ``A`` through
    ``ZZ``.
    """
    val = 0
    if len(alpha) > 2:
        return None
    if len(alpha) == 2:
        char = alpha[0]
        val = ((ord(char.upper()) - ord('A')) + 1) * 26
    char = alpha[-1]
    val += ((ord(char.upper()) - ord('A')) + 1)
    return val


def flatten(list_or_tuple):
    """
    Flatten a list or tuple into a 1-dimensional copy of the same type.
    """
    cast_result_as = type(list_or_tuple)
    while any((isinstance(e, (list, tuple)) for e in list_or_tuple)):
        unpacked = []
        for element in list_or_tuple:
            if isinstance(element, (list, tuple)):
                unpacked.extend(element)
            else:
                unpacked.append(element)
        list_or_tuple = unpacked
    return cast_result_as(list_or_tuple)


def gen_uid(num, sub, total_sub, just=4):
    """
    Generate a unique ID string in the format:  ``'0001.a-d'``

    :example:  ``gen_uid(1, 1, 4)`` --> ``'0001.a-d'``
    :example:  ``gen_uid(234, 3, 11)`` --> ``'0234.c-k'``

    :param num: The number to appear left of the period.
    :param sub: An int, indicating which entry this is for ``num``.
    :param total_sub: An int, being how many total entries there will be
     for this ``num``.
    :param just: How many places to justify (defaults to 4).
    :return: The UID string.
    """
    return (
        f"{str(num).rjust(just, '0')}"
        f".{num_to_alpha(sub).lower()}"
        f"-{num_to_alpha(total_sub).lower()}"
    )


def _confirm_list_of_strings(*attributes) -> list:
    """
    INTERNAL USE:
    Ensure that each element has been entered as a string.
    Returns a flattened list of strings.
    """
    attributes = flatten(attributes)
    if len(attributes) == 0:
        return []
    if not all((isinstance(att, str) for att in attributes)):
        raise TypeError('Must pass list of strings.')
    return attributes


__all__ = [
    'num_to_alpha',
    'alpha_to_num',
    'flatten',
    'gen_uid',
]
