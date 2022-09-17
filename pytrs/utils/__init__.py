# Copyright (c) 2020, James P. Imes, all rights reserved.

"""
Misc. tools for parsing, etc.
"""


def num_to_alpha(num):
    """
    Convert a number (integer) into an alpha (1 --> 'A', 26 --> 'Z',
    27 -- > 'AA') -- from A through ZZ.
    """
    return (
        ((num - 1) // 26 > 0) * chr((num - 1) // 26 + ord('A') - 1)
        + chr((num - 1) % 26 + ord('A'))
    )


def alpha_to_num(alpha):
    """
    Convert an alpha into an integer ('A' --> 1, 'Z' --> 26,
    'AA' --> 27) -- from A through ZZ.
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


def config_help():
    """
    Print to console a guide to text parameters for config settings
    and Config objects.
    """

    t0a = (
        "~~~A guide to text-based parameters in `config=` kwarg and "
        "Config objects.~~~\n\n"
        "How PLSSDesc objects and/or Tract objects are parsed can be configured "
        "at init with kwarg "
        "`config=`, as follows:\n"
        ">>> desc1 = pytrs.PLSSDesc('T154N-R97W Sec 14: NE/4', config='n; w; "
        "parse_qq')\n"
        ">>> tr1 = pytrs.Tract('NE/4', '154n97w14', config='n, w, parse_qq')\n\n"
        "Parameters are entered together as a single string, separated by comma "
        "or semicolon. (Spaces are optional and have no effect.)"
    )

    t0b = (
        "Parameters can be entered as text into the `config=` kwarg of PLSSDesc "
        "and Tract objects, OR by initializing a Config object (which can take "
        "all of the same parameters), as follows:\n"
        ">>> nd_config = pytrs.Config('n, w, parse_qq')\n\n"
        "...and then feeding this Config object into the `config=` kwarg, as follows:\n"
        ">>> desc1 = pytrs.PLSSDesc('T154N-R97W Sec 14: NE/4', config=nd_config)\n"
        ">>> tr1 = pytrs.Tract('NE/4', '154n97w14', config=nd_config)\n\n"
    )

    t1_ = (
        "~~~CONFIG PARAMETERS~~~\n\n"
        "A list of parameters is no longer maintained as part of this function. "
        "However, a current, maintained list of all config parameters with brief "
        "explanation can be printed to console by calling "
        "`pytrs.utils.config_parameters()`. It will be called now..."
    )

    bail = False
    txt_list = [t0a, t0b, t1_]
    i = 1
    for text in txt_list:
        print(f"{'-' * 15}")
        print(text)
        if i < len(txt_list):
            print(
                f"\n<continued ({len(txt_list) - i} more)... Press `Enter` to continue; "
                f"or [Q] to quit>")
        i += 1
        if input().lower() == 'q':
            bail = True
            break
    if not bail:
        config_parameters()
    return None


def config_parameters():
    """
    Print out all config parameter options and a brief explanation.
    """

    from pytrs import IMPLEMENTED_LAYOUTS

    # How many spaces to justify parameters before explanation:
    just = 24

    # String that should be used for indenter:
    # ind = '~~ '
    ind = ''

    # String for how 'or' should be printed between equivalent parameters
    or_txt = '  <or>'

    # Repeated string for how parameters should be separated
    lb_str = ' ~~'

    # String to denote default settings
    def_str = " [**]"

    # The parameters and their explanations. The bool at the end refers to whether
    # this is a default setting.
    params = [
        (("'n'", "'default_ns.n'"), "Assume any missing N/S in a Twp should be 'n'", True),
        (("'s'", "'default_ns.s'"), "Assume any missing N/S in a Twp should be 's'", False),
        (("'w'", "'default_ew.w'"), "Assume any missing E/W in a Rge should be 'w'", True),
        (("'e'", "'default_ew.e'"), "Assume any missing E/W in a Rge should be 'e'", False),
        (("'wait_to_parse'",), "Hold off on parsing PLSSDesc object at init", False),
        (("'parse_qq'",),
            "Tract object (or PLSSDesc object's subordinate Tract objects) should parse "
            "lots/aliquots at init", False),
        (("'clean_qq'",),
         "Expect ONLY clean aliquots/lots (no metes-and-bounds, exceptions, etc.)", False),
        (("'require_colon'", "'require_colon.True'"),
            "Require a colon between Section number and its following description block "
            "(on a 'first-pass' attempt at a parse only)",
            True),
        (("'require_colon.False'",), "Do not require a colon in that position", False),
        (("'include_lot_divs'", "'include_lot_divs.True'"),
            "Report lot divisions (i.e., 'N2 of L1' for 'N/2 of Lot 1')", True),
        (("'include_lot_divs.False'",),
            "Do NOT report lot divisions (i.e. just 'L1', even if divided further)",
            False),
        (("'ocr_scrub'", "'ocr_scrub.True'"),
            "Scrub common OCR artifacts from the text (currently limited effect)", False),
        (("'ocr_scrub.False'",), "Do NOT scrub OCR artifacts from the text.", True),
        (("'segment'", "'segment.True'"),
            "Segment description before parsing into Tracts (MIGHT capture descriptions "
            "with multiple layouts).",
            False),
        (("'segment.False'",), "Do NOT segment the description before parsing.", True),
        (("'qq_depth_min.<number>'",),
            "In QQ parsing, specify the MINIMUM 'depth' to parse aliquots. 2 (the "
            "default) will parse to AT LEAST quarter-quarters (QQs).",
            True),
        (("'qq_depth_max.<number>'",),
            "In QQ parsing, specify the MAXIMUM 'depth' to parse aliquots, and "
            "discard any smaller divisions.",
            False),
        (("'qq_depth.<number>'",),
            "In QQ parsing, specify the EXACT 'depth' to parse aliquots (i.e. "
            "qq_depth_min == qq_depth_max), discarding any smaller divisions.",
            False),
        (("'break_halves'", "'break_halves.True'",),
            "In QQ parsing, break all aliquot halves into quarters, EVEN IF "
            "we're at divisions smaller than the specified `qq_depth_min`.",
            False),
        (("'break_halves.False'",),
            "In QQ parsing, leave halves as they are (but ONLY IF we're at "
            "divisions smaller than the specified `qq_depth_min`).",
            True)
    ]

    # Append each of the implemented layouts to the `params` list:
    for layout in IMPLEMENTED_LAYOUTS:
        params.append(
            ((f"'{layout}'", f"'layout.{layout}'",),
             f"do not deduce layout; instead, force '{layout}' (NOT RECOMMENDED)",
             False))

    print(f"{' ALL CONFIG PARAMETER OPTIONS '.center(just * 3, '~')}\n\n")

    for param in params:
        # Print a line divider to break up the wall of text:
        print(f"{lb_str * ((just + len(ind)) // len(lb_str)) * 3}")

        if len(param[0]) == 1:
            # If only 1 parameter (e.g., 'clean_qq') we print it on a
            # single line:
            print((
                f"{ind}{param[0][0].ljust(just, ' ')})--> "
                f"{param[1]}{def_str * param[2]}"
            ))
            continue
        # If 2 parameters, print them on separate lines, separated by or:
        for i in range(len(param[0])):
            if (i + 1) % 2 == 1:
                print(f"{ind}{param[0][i].ljust(just, ' ')})")
            else:
                print((
                    f"{ind}{or_txt.ljust(just)})--> "
                    f"{param[1]}{def_str * param[2]}"
                ))
                print(f"{ind}{param[0][i].ljust(just, ' ')})")

    print(f"{lb_str * ((just + len(ind)) // len(lb_str)) * 3}\n")
    print(
        f"Where two parameters are stated above with {or_txt.strip()}, they are "
        f"functionally equivalent to one another (i.e. either option can be used for "
        f"the same effect).\n\n"
        f"And {def_str.strip()} denotes default behavior that need not be specified in "
        f"config (usually the `.False` option for such settings is the non-default).\n\n"

        "USAGE:\n"
        "Combine desired parameters into a single string, separated by comma or "
        "semicolon, like so:\n"
        "   'default_ns.n, default_ew.w, clean_qq, include_lot_divs.False, qq_depth.2'\n"
        "(Spaces are optional and have no effect.)\n\n"
        "The string should be the first positional argument of a Config object, or the "
        "init parameter `config=` when creating PLSSDesc and/or Tract objects.")


def gen_uid(num, sub, total_sub, just=4):
    """
    Generate a unique ID string in the format:  "0001.a-d"

    :example:  ``gen_uid(1, 1, 4)`` --> "0001.a-d"
    :example:  ``gen_uid(234, 3, 11)`` --> "0234.c-k"

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
    'config_help',
    'config_parameters',
    'gen_uid',
]
