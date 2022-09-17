
"""
Functions to parse an aliquot text block into a list of quarter-quarter
(or smaller or larger, as configured by the requested depth).
"""

from .rgxlib import *

# Cardinal directions / aliquot names (without fractions).
_N = 'N'
_S = 'S'
_E = 'E'
_W = 'W'
_NE = 'NE'
_NW = 'NW'
_SE = 'SE'
_SW = 'SW'
_ALL = 'ALL'

# Various groupings for the aliquots / directions.
QQ_HALVES = (_N, _S, _E, _W)
QQ_QUARTERS = (_NE, _NW, _SE, _SW)
QQ_SUBDIVIDE_DEFINITIONS = {
    _ALL: QQ_QUARTERS,
    _N: (_NE, _NW),
    _S: (_SE, _SW),
    _E: (_NE, _SE),
    _W: (_NW, _SW),
}
QQ_NS = (_N, _S)
QQ_EW = (_E, _W)
QQ_SAME_AXIS = {
    _N: QQ_NS,
    _S: QQ_NS,
    _E: QQ_EW,
    _W: QQ_EW
}


def parse_aliquot(
        text,
        qq_depth_min=2,
        qq_depth_max=None,
        qq_depth=None,
        break_halves=False) -> list:
    """
    INTERNAL USE:
    Convert an aliquot with fraction symbols (or 'ALL') into a list of
    clean QQs. Returns a list of QQ's (or smaller, if applicable):
        'N½SW¼NE¼' -> ['N2SWNE']
        'N½SW¼' -> ['NESW', 'NWSW']

    NOTE: Input a single text (i.e. feed only 'N½SW¼NE¼',
    even if we have a larger list of ['N½SW¼NE¼', 'NW¼'] to process).

    :param text: A clean string, as generated by the
    `Tract.parse()` method (e.g., 'E½NW¼NE¼' or 'ALL').
    :param qq_depth_min: An int, specifying the minimum depth of the
    parse.  Defaults to 2, i.e. to quarter-quarters (e.g., ``'N/2NE/4'``
    -> ``['NENE', 'NENE']``). Setting to 3 would return 10-acre
    subdivisions (i.e. dividing the ``NENE`` into ``['NENENE', 'NWNENE',
    'SENENE', 'SWNENE']``), and so forth.
    WARNING: Higher than a few levels of depth will result in very slow
    performance.
    :param qq_depth_max: (Optional) An int, specifying the maximum depth
    of the parse. If set as 2, any subdivision smaller than
    quarter-quarter (e.g., 'NENE') would be discarded -- so for example,
    the ``'N/2NE/4NE/4'`` would simply become the ``'NENE'``. Must be
    greater than or equal to ``qq_depth_min``. (Defaults to ``None`` --
    i.e. no maximum.)
    :param qq_depth: (Optional) An int, specifying both the min and max
    depth of the parse. If specified, will override both ``qq_depth_min``
    and ``qq_depth_max``. (Defaults to ``None`` -- i.e. use
    ``qq_depth_min`` and optionally ``qq_depth_max``.)
    :param break_halves: Whether to break halves into quarters, even
    if we're beyond the ``qq_depth_min``. (``False`` by default.)
    """

    if qq_depth is not None:
        qq_depth_min = qq_depth_max = qq_depth

    if qq_depth_max is not None and qq_depth_max < qq_depth_min:
        import warnings
        msg = (
            "If specified, `qq_depth_max` should be greater than or equal to "
            f"`qq_depth_min` (passed as {qq_depth_max} and {qq_depth_min}, "
            "respectively). Using a larger qq_depth_max than qq_depth_min may "
            "result in more QQ's being returned than actually exist in the "
            "Tract."
        )
        warnings.warn(msg)

    # Get a list of the component parts of the aliquot string, and then
    # reverse it -- i.e. 'N½SW¼NE¼' becomes ['NE', 'SW', 'N']
    component_list = [
        mo['aliquot_no_frac']
        for mo in single_aliquot_unpacker_regex.finditer(text)
    ]
    component_list.reverse()

    # If no components found, there are no QQ's to unpack.
    if not component_list:
        return component_list

    # Check for any consecutive halves that are on opposite axes.
    # E.g., the N/2E/2 should be converted to the NE/4, but the W/2E/2
    # should be left alone.
    # Also check for any quarters that occur before halves, and convert
    # them to halves before quarters. E.g., "SE/4W/2" -> "E/2SW/4"

    component_list = standardize_aliquot_components(component_list)

    # Convert the components into aliquot strings.
    # (Remember that the component_list is ordered last-to-first
    # vis-a-vis the original aliquot string.)

    # Discard any subdivisions greater than the qq_depth_max, if it was set.
    if qq_depth_max is not None and len(component_list) > qq_depth_max:
        component_list = component_list[:qq_depth_max]

    subdivided_component_list = []
    for i, comp in enumerate(component_list, start=1):
        # Determine how deeply we need to subdivide (i.e. break down) each
        # component, such that we ultimately capture the intended qq_depth_min.
        depth = 0
        if i == qq_depth_min:
            depth = 1
        elif i == len(component_list) and len(component_list) < qq_depth_min:
            depth = qq_depth_min - i + 1
        elif comp in QQ_HALVES and (i < qq_depth_min or break_halves):
            depth = 1
        if comp in QQ_QUARTERS:
            # Quarters (by definition) are already 1 depth more broken down
            # than halves (or 'ALL'), so subtract 1 to account for that
            depth -= 1

        # Subdivide this aliquot component, as deep as needed.
        new_comp = subdivide_aliquot(comp, depth)

        # Append it to our list of components (with subdivisions arranged
        # largest-to-smallest).
        subdivided_component_list.append(new_comp)

    # subdivided_component_list is now in the format:
    #   `[['SE'], ['NW', 'SW'], ['E2']]`
    # ...for E/2W/2SE/4, parsed to a qq_depth_min of 2.

    # Convert the 1-depth nested list into the final QQ list.
    qqs = rebuild_aliquots(subdivided_component_list)
    return qqs


def pass_back_halves(aliquot_components: list) -> list:
    """
    INTERNAL USE:
    Quarters that precede halves in an aliquot block are nonstandard
    but technically accurate. This function adjusts them to the
    equivalent description where the half occurs before the quarter.

    For example, ``'NE/4N/2'`` (passed here as ``['N', 'NE']``) is
    better described as the ``'N/2NE/4'``. Converted here to
    ``['NE', 'N']``.

    Similarly, the ``SE/4W/2'`` (passed here as ``['W', 'SE']``) is
    better described as the ``'E/2SW/4'``. Converted here to
    ``['SW', 'E']``.

    NOTE: This function does a single pass only! May need to call
    iteratively until the correct output is achieved.

    :param aliquot_components: A list of aliquot components without any
    fractions or numbers.
    :return: The fixed list of aliquot components.
    """
    aliquot_components.reverse()
    i = 0
    while i < len(aliquot_components) - 1:
        aq1 = aliquot_components[i]
        aq2 = aliquot_components[i + 1]

        # Looking for halves before quarters.
        if not (aq2 in QQ_HALVES and aq1 in QQ_QUARTERS):
            # This is OK.
            i += 1
            continue

        # Break the 'NE' into 'N' and 'E'.
        char1_ns, char2_ew = aq1

        if aq2 in QQ_NS:
            rebuilt_aq2 = f"{aq2}{char2_ew}"
            rebuilt_aq1 = char1_ns
        else:
            rebuilt_aq2 = f"{char1_ns}{aq2}"
            rebuilt_aq1 = char2_ew
        # Replace aq1 and aq2 with the rebuilt versions.
        aliquot_components[i] = rebuilt_aq1
        aliquot_components[i + 1] = rebuilt_aq2
        i += 1

    aliquot_components.reverse()
    return aliquot_components


def combine_consecutive_halves(aliquot_components):
    """
    INTERNAL USE:
    Check for any consecutive halves that are on opposite axes.
    E.g., the N/2E/2 should be converted to the NE/4, but the W/2E/2
    should be left alone.

    NOTE: This function does a single pass only! May need to call
    iteratively until the correct output is achieved.

    :param aliquot_components: A list of aliquot components without any
    fractions or numbers.
    :return: The fixed list of aliquot components.
    """
    aliquot_components_clean = []
    i = 0
    while i < len(aliquot_components):
        aq1 = aliquot_components[i]
        if i + 1 == len(aliquot_components):
            # Last item.
            aliquot_components_clean.append(aq1)
            break
        aq2 = aliquot_components[i + 1]

        # If all of these conditions are met, we need to swap.
        match_conditions = (
            aq1 in QQ_HALVES,
            aq2 in QQ_HALVES,
            aq2 not in QQ_SAME_AXIS[aq1],
        )
        if all(match_conditions):
            # For example, the current component is 'N' and the next
            # component is 'E'; those do not exist on the same axis, so
            # we combine them into the 'NE'. (And make sure the N/S
            # direction goes before E/W.)
            new_quarter = f"{aq2}{aq1}" if aq1 in "EW" else f"{aq1}{aq2}"
            aliquot_components_clean.append(new_quarter)
            # Skip over the next component, because we already handled it during
            # this iteration.
            i += 2
        else:
            aliquot_components_clean.append(aq1)
            i += 1
    aliquot_components = aliquot_components_clean
    return aliquot_components


def standardize_aliquot_components(aliquot_components: list) -> list:
    """
    INTERNAL USE:
    Iron out any non-standard aliquot descriptions, such as 'cross-axes'
    halves (e.g., 'W/2N/2' -> 'NW/4') or quarters that occur before
    halves (e.g., 'SE/4W/2' -> 'W/2SE/4').

    :param aliquot_components: A list of aliquot components (already
    broken down by ``parse_aliquot()``).
    :return: The corrected list of aliquot components.
    """
    aliquot_copy = []
    while aliquot_components != aliquot_copy:
        aliquot_copy = aliquot_components.copy()
        aliquot_components = pass_back_halves(aliquot_components)
        aliquot_components = combine_consecutive_halves(aliquot_components)
    return aliquot_components


def rebuild_aliquots(nested_aliquot_list: list):
    """
    INTERNAL USE:

    A shallow-nested (single-depth) list of aliquot components is
    returned as a flattened list of rebuilt aliquots.

    :param nested_aliquot_list: A single-depth nested list of aliquot
    components, arranged by subdivision size, largest to smallest. For
    example:  ``[['SE'], ['NW', 'SW'], ['E2']]``  ...for 'E/2W/2SE/4',
    parsed to a ``qq_depth_min`` of 2.
    :return: A clean QQ list, in the format ``['E2NWSE', 'E2SWSE']`` (or
    smaller strings, if parsed to a lesser ``qq_depth_min``).
    """
    qq_list = []
    while nested_aliquot_list:
        deepest = nested_aliquot_list.pop(-1)
        if not nested_aliquot_list:
            # No more elements.
            qq_list = deepest
            break
        second_deepest = nested_aliquot_list.pop(-1)
        rebuilt = []
        for shallow in second_deepest:
            rebuilt.extend(map(lambda deep: f"{deep}{shallow}", deepest))
        nested_aliquot_list.append(rebuilt)
    return qq_list


def subdivide_aliquot(aliquot_component: str, depth: int):
    """
    INTERNAL USE:

    Subdivide an aliquot into smaller pieces, to the specified ``depth``.

    Return examples:

    ``subdivide_aliquot('N', 0)``
    ->  ``['N2']``

    ``subdivide_aliquot('N', 1)``
    ->  ``['NE', 'NW']``

    ``subdivide_aliquot('N', 2)``
    >  ``['NENE', 'NWNE', 'SENE', 'SWNE', 'NENW', 'NWNW', 'SENW', 'SWNW']``

    ``subdivide_aliquot('NE', 1)``
    >  ``['NENE', 'NWNE', 'SENE', 'SWNE']``

    :param aliquot_component: Any element that appears in the variable
    ``QQ_QUARTERS`` or as a key in ``QQ_SUBDIVIDE_DEFINITIONS``.

    :param depth: How many times to subdivide this aliquot (i.e. halves
    or 'ALL' into quarters, or quarters into deeper quarters). More
    precisely stated, the section will be subdivided into a total number
    of pieces equal to ``4^(depth - 1)`` -- assuming we're parsing the
    complete section (i.e. 'ALL'). Thus, setting depth greater than 5 or
    so will probably take a long time to process.  NOTE: A depth of 0 or
    less will simply place the aliquot in a list and return it, after
    adding the half designator ``'2'``, if appropriate (i.e. ``'NE'``
    -> ``['NE']``; but ``'E'`` -> ``['E2']`` ).

    :return: A list of aliquots, in the format shown above.
    """
    if depth <= 0:
        # I.e. a request NOT to subdivide the aliquot. So just make sure
        # it is appropriately formatted if it's a half (i.e. 'N' -> 'N2'),
        # then put it in a list and return it.
        if aliquot_component in QQ_HALVES:
            return [aliquot_component + "2"]
        return [aliquot_component]

    # Construct a nested list, which rebuild_aliquots() requires, which
    # will process it and spit out a flat list before this function
    # returns.
    divided = [[aliquot_component]]
    for _ in range(depth):
        if divided[-1][0] in QQ_SUBDIVIDE_DEFINITIONS.keys():
            # replace halves and 'ALL' with quarters
            comp = divided.pop(-1)[0]
            divided.append(list(QQ_SUBDIVIDE_DEFINITIONS[comp]))
        else:
            divided.append(list(QQ_QUARTERS))

    # The N/2 (passed to this function as 'N') would now be parsed into
    # a format (at a depth of 2):
    #   [['NE', 'NW'], ['NE', 'NW', 'SE', 'SW']]
    # ... which gets reconstructed to:
    #   ['NENE', 'NWNE', 'SENE', 'SWNE', 'NENW', 'NWNW', 'SENW', 'SWNW']
    # ...by `rebuild_aliquots()`

    return rebuild_aliquots(divided)


__all__ = [
    'parse_aliquot',
    '_N',
    '_S',
    '_E',
    '_W',
    '_NE',
    '_NW',
    '_SE',
    '_SW',
    '_ALL',
]
