"""
Functions for combining parsed QQs into simpler aliquots.
"""

from __future__ import annotations
from .tract_parse import TractParser

__all__ = [
    'simplify_aliquots',
]

_ALIQUOT_DEFS = [
    [{'NE', 'NW', 'SE', 'SW'}, ''],  # 'ALL', or the entire aliquot
    [{'NE', 'NW', 'SE', 'SW'}, 'ALL'],
    [{'NE', 'NW'}, 'N2'],
    [{'SE', 'SW'}, 'S2'],
    [{'NE', 'SE'}, 'E2'],
    [{'NW', 'SW'}, 'W2'],
    [{'N2', 'S2'}, 'ALL'],
    [{'E2', 'W2'}, 'ALL'],
]

ALL_DEFS = {
    ('N2', 'S2'),
    ('E2', 'W2'),
}

HALF_DEFS = {
    'N2': ('NE', 'NW'),
    'S2': ('SE', 'SW'),
    'E2': ('NE', 'SE'),
    'W2': ('NW', 'SW')
}

COMPATIBLE_HALVES = {
    'N2': ('N2', 'S2'),
    'S2': ('N2', 'S2'),
    'E2': ('E2', 'W2'),
    'W2': ('E2', 'W2'),
}


class AliquotNode:
    """
    INTERNAL USE:

    A 4-branching tree representation of one or more aliquot
    descriptions. Can be used to recompile / simplify QQs into larger
    aliquot parts with the ``.consolidate()`` method.

    .. note::
      This is not maintained for public-facing use, but it can be used
      for a tree representation of aliquot divisions if needed. Note,
      however, that updates and changes to the API may not be publicly
      noted.
    """

    def __init__(self, parent: AliquotNode = None, label: str = None):
        """
        :param parent: The parent node. If not specified, it is assumed
         that this is the root.
        :param label: The quarter label for this node. Should be one of
         ``('NE', 'NW', 'SE', 'SW')``, unless this is the root node.
        """
        self.parent: AliquotNode = parent
        self.label: str = label
        self.children: dict[str, AliquotNode] = {}
        self._avail_consolidations: set[tuple[str]] = set()
        self.full = False
        self._consol_substrings = []

    def __repr__(self):
        child_strings = [
            f"{lbl}{'..' if node.children else ''}"
            for lbl, node in self.children.items()
        ]
        lbl = '__'
        if self.label is not None:
            lbl = self.label
        return f"{lbl}<{'|'.join(child_strings)}>"

    def __getitem__(self, qq):
        return self.children[qq]

    def __setitem__(self, qq, v):
        self.children[qq] = v
        return None

    def get(self, qq: str, default=None):
        """
        Get the child node for the specified ``qq``. If not found, will
        return the optionally specified ``default`` instead of raising a
        ``KeyError``.
        """
        return self.children.get(qq, default)

    def _insert_aliquot_into_tree(self, qq: str):
        """
        Break apart the aliquot and register it into the tree. Does not
        accept aliquots that contain halves.
        (Call this only on the root node.)
        """
        # ['SW', 'NW', 'NE']
        decon_qq = [qq[i:i + 2] for i in range(0, len(qq), 2)]
        decon_qq.reverse()
        node = self
        i = -1
        for i, aliq in enumerate(decon_qq):
            if node.full:
                return None
            if aliq not in node.children:
                node[aliq] = AliquotNode(parent=node, label=aliq)
            node = node[aliq]
        if i >= 0:
            # If anything has been inserted, the final node is full by definition.
            # Any future subdivisions of that aliquot are already covered.
            node.full = True
        return None

    def register_aliquot(self, qq: str):
        """
        Break apart the aliquot and register it into the tree. (Call
        this only on the root node.)
        """
        # Must break any halves into quarters to use a 4-branching tree structure.
        split_qqs = []
        if '2' in qq:
            tp = TractParser(text=qq, clean_qq=True, break_halves=True)
            for split_qq in tp.qqs:
                split_qqs.append(split_qq)
        else:
            split_qqs.append(qq)
        for qq in split_qqs:
            self._insert_aliquot_into_tree(qq)

    def register_all_aliquots(self, qqs: list[str]):
        """
        Break apart all aliquots in the list of QQs and register them
        into the tree. (Call this only on the root node.)
        """
        for qq in qqs:
            self.register_aliquot(qq)

    def is_leaf(self):
        """Check if this node is a leaf."""
        return len(self.children) == 0

    def _subset_full(self, labels: list, _trim=False) -> bool:
        """
        INTERNAL USE:

        Check if the selection of children nodes are full.

        :param labels: List of any number of ``['NE', 'NW', 'SE', 'SW']``
         to determine whether those children are full.
        :param _trim: Use this ONLY for checking if ``.all_full()``. If
         used, a ``True`` result in this method will cause all children
         to be deleted from the tree.
        :return: Whether all selected children are full.
        """
        relevant_nodes = [self.children.get(lbl) for lbl in labels]
        if self.is_leaf() or self.full:
            self.full = True
            return True
        elif any(node is None for node in relevant_nodes):
            # If any nodes are present (requested or not), the requested nodes must exist.
            return False
        is_full = all(node.all_full() for node in relevant_nodes)
        if _trim and is_full:
            self.full = True
            self.children = {}
        return is_full

    def all_full(self):
        """
        Check if this node is completely full. If so, child nodes will
        be trimmed.
        """
        return self.is_leaf() or self._subset_full(labels=['NE', 'NW', 'SE', 'SW'], _trim=True)

    def trim_tree(self):
        """
        Trim away branches that contain only full nodes.
        """
        if self.is_leaf():
            return None
        full = []
        for aq_label, child in self.children.items():
            if child.all_full():
                full.append(aq_label)
            else:
                child.trim_tree()
        if len(full) == 4 and self.parent is not None:
            self.full = True
            self.children = {}
        return None

    def _calc_available_consolidations(self):
        """
        INTERNAL USE:

        Calculate possible consolidations of the existing or remaining
        nodes. For example, the ``NE, NW, SE`` (if each is a 'full'
        node) could be consolidated into ``N2`` or ``E2``.

        The results get stored to ``._avail_consolidations``. In the
        above example, it would be as follows:
        ``( (N2,), (E2,), (NE,), (NW,), (SE,) )``.
        (Note that full quarters are included as possible
        consolidations.)
        """
        # Reset any prior consolidation calculations.
        self._avail_consolidations = {}
        if self.full:
            self._avail_consolidations = {tuple(sorted(HALF_DEFS.keys()))}
            return self._avail_consolidations
        full_quarters = set()
        child_options = {}
        for aliq, child in self.children.items():
            new_options = child._calc_available_consolidations()
            if child.full:
                full_quarters.add(aliq)
            else:
                child_options[aliq] = new_options
        # Include any full quarters as options.
        options = set((q,) for q in full_quarters)
        for candidate_half, quarters in HALF_DEFS.items():
            node_pair = tuple(self.get(q) for q in quarters)
            if any(node is None for node in node_pair):
                continue
            if all(node.full for node in node_pair):
                # Entire half -- e.g., N2, S2, etc.
                new_consolidation = (candidate_half,)
                options.add(new_consolidation)
                continue
            a, b = node_pair
            for cand_consolid in a._avail_consolidations:
                direction_sample = cand_consolid[0]
                if direction_sample not in COMPATIBLE_HALVES[candidate_half]:
                    # Must keep N/S together, and E/W -- e.g., can't mix N2 with E2.
                    continue
                if cand_consolid in b._avail_consolidations:
                    new_consolidation = (candidate_half,) + cand_consolid
                    options.add(new_consolidation)
        self._avail_consolidations = options
        return options

    def consolidate(self, assume_standard=False) -> list[str]:
        """
        Consolidate the tree into maximally-sized aliquot strings (i.e.,
        the smallest possible list of aliquot strings). If equally
        optimal solutions are possible, this will prefer to generate
        halves over quarters (``['N2', ...] > ['NE', 'NW', ...]``),
        quarters over half-halves (``['NE', ...] > ['N2N2', ...]``),
        and prefer North > South > East > West.

        To assume a standard 640-acre section, use
        ``assume_standard=True``, in which case the standard 16 QQ's
        will render ``'ALL'``.

         .. warning::
            This method will destroy the tree. If the original tree is
            needed after calling this method, first ensure that you have
            created an equivalent backup.

        :param assume_standard: Whether to assume that this is a
         'standard' section -- i.e. that the ``'N2'`` + ``'S2'``
         (or ``'E2'`` + ``'W2'``) together make up ``'ALL'``.
        :return: A list of consolidated aliquot strings. Not necessarily
         sorted.
        """
        consolidated_aliquots = []
        self.trim_tree()
        self._calc_available_consolidations()
        consolidations = sorted(
            self._avail_consolidations,
            key=lambda x: _calc_aliquot_component_rank(x, prefer_short=True)
        )
        top_label = self.label
        if top_label is None:
            top_label = ''
        while consolidations:
            cur_consol = consolidations.pop(0)
            # Build aliquot string.
            output_str = f"{''.join(reversed(cur_consol))}{top_label}"
            consolidated_aliquots.append(output_str)
            # Trim away used nodes.
            self._trim_used(cur_consol)
            # Throw away consolidation options that would cause overlapping aliquots.
            _cull_consolidation_options(consolidations, latest=cur_consol)
        # Now all top-level consolidations have been executed, but it is possible that
        # top-level quarters still exist, so children are recursively consolidated, then
        # combined with the remaining top-level quarter labels.
        for child_lbl, child_node in self.children.items():
            child_node.consolidate()
            # Resulting substrings have been stored to `._consol_substrings`.
            for s in child_node._consol_substrings:
                # Build aliquot string.
                consolidated_aliquots.append(f"{s}{top_label}")
                # (Newly used nodes will have been trimmed in the recursive call
                # on the child nodes.)
        if assume_standard and tuple(sorted(consolidated_aliquots)) in ALL_DEFS:
            consolidated_aliquots = ['ALL']
        self._consol_substrings = consolidated_aliquots
        return sorted(consolidated_aliquots, key=_calc_aliquot_rank)

    def _trim_used(self, aliquot_tuple: tuple[str]):
        """
        INTERNAL USE:

        Trim away nodes that have been rendered into aliquot strings.
        :param aliquot_tuple: The latest executed aliquot description,
         represented as a tuple of aliquot strings, such as
         ``('N2', 'S2')`` for the newly consolidated ``'S2N2'``.
        """
        if not aliquot_tuple or self.is_leaf():
            self.parent.children.pop(self.label)
            return None
        cur_aliq = aliquot_tuple[0]
        quarters = HALF_DEFS.get(cur_aliq)
        if quarters is not None:
            selected_children = [self[q] for q in quarters]
        else:
            selected_children = [self[cur_aliq]]
        for child_node in selected_children:
            child_node._trim_used(aliquot_tuple[1:])
        return None


def _check_nsew_split(candidate: tuple[str]):
    """
    INTERNAL USE:

    Returns ``'NS'`` if candidate eventually splits N/S or ``'EW'`` if
    it splits E/W. Returns ``None`` if candidate is only composed of
    quarters.
    """
    if not candidate:
        return None
    i = 0
    n = len(candidate)
    while i < n:
        direction_sample = candidate[i]
        if direction_sample in ('N2', 'S2'):
            return 'NS'
        elif direction_sample in ('E2', 'W2'):
            return 'EW'
        i += 1
    return None


def _cull_consolidation_options(options: list[tuple[str]], latest: tuple[str]):
    """
    INTERNAL USE:

    Cull the list of consolidation ``options``, according to the option
    that was taken most recently (``latest``).
    :param options: A list of currently possible consolidations.
    :param: The latest executed consolidation, represented as a tuple of
     aliquot strings, such as ``('N2', 'S2')`` for the newly
     consolidated ``'S2N2'``.
    :return: The remaining ``options``. (Also modifies the original list
     of tuples that was passed as ``options``.)
    """
    pop_idxs = []
    keep_nsew = _check_nsew_split(latest)
    quarters = HALF_DEFS.get(latest[0])
    split_options = []
    if quarters is not None:
        # For example, if ('N2', 'S2') is the latest executed consolidation, it would
        # also entail ('NE', 'S2') and ('NW', 'S2'). So we need to check if either of
        # those are in the consolidation options and remove them.
        split_options = [(q,) + latest[1:] for q in quarters]
    for i, opt in enumerate(options):
        if opt in split_options:
            pop_idxs.append(i)
            continue
        # We also need to throw away any options that split on the wrong axis.
        nsew_split = _check_nsew_split(opt)
        if None not in (nsew_split, keep_nsew) and nsew_split != keep_nsew:
            pop_idxs.append(i)
    pop_idxs.reverse()
    for i in pop_idxs:
        options.pop(i)
    return options


def simplify_aliquots(qqs: list[str], assume_standard=False) -> list[str]:
    """
    INTERNAL USE:

    Take a list of QQs (of any parse depth) and combine them into a list
    of simplified aliquots. For example:
     ``['NENE', 'SENE', 'NWNW']`` -> ``['E2NE', 'NWNW']``

    Warning: This is ONLY designed to work with QQs generated by the
    ``TractParser``.

    Note: By default, this does NOT assume that the entire section is
    made up four quarters, because there exist irregular sections with
    more than 16 QQ's. The returned result of four quarters would be two
    halves (either N2 and S2, or E2 and W2), but not ``'ALL'``.

    To assume a standard 640-acre section, use ``assume_standard=True``,
    in which case the standard 16 QQ's will render ``'ALL'``.
    """
    tree = AliquotNode()
    tree.register_all_aliquots(qqs)
    tree.trim_tree()
    consolidated_aliquots = tree.consolidate(assume_standard=assume_standard)
    return consolidated_aliquots


def _calc_aliquot_component_rank(components: list[str] | tuple[str], prefer_short=False):
    """
    INTERNAL USE:

    Calculate a sorting value for a decomposed aliquot string. (Does NOT
    accept ``'ALL'``.)

    :param components: List or tuple of 2-character components of an
     aliquot description, in order of highest-to-lowest priority.
     Ex: ``'N2NWNE'`` would be passed as ``['NE', 'NW', 'N2']``.
    :param prefer_short: Give highest priority to the shortest aliquots
     (i.e., ``'SE'`` would have higher priority than ``'N2N2'``).
    """
    sort_val = 0
    if prefer_short:
        sort_val = len(components)
    for position, x in enumerate(components, start=1):
        x_val = 0
        # First char NSEW
        if x[0] == 'N':
            x_val += 0
        elif x[0] == 'S':
            x_val += 1
        elif x[0] == 'E':
            x_val += 2
        elif x[0] == 'W':
            x_val += 3
        # Second char NSEW, or half.
        if x[1] == '2':
            x_val += 10
        elif x[1] == 'N':
            x_val += 20
        elif x[1] == 'S':
            x_val += 30
        elif x[1] == 'E':
            x_val += 40
        elif x[1] == 'W':
            x_val += 50
        sort_val += x_val / (10 ** (position * 2))
    return sort_val


def _calc_aliquot_rank(aliquot: str):
    """
    INTERNAL USE:

    Calculate a sorting value for an aliquot string.

    Priority:
     - ALL > everything else.
     - North > South > East > West
     - Halves > Quarters

    :param aliquot:
    :return:
    """
    if aliquot == 'ALL':
        return float('-inf')
    # Split aliquot into 2-character pieces, and reverse them.
    components = [aliquot[i:i + 2] for i in range(0, len(aliquot), 2)]
    components.reverse()
    # Note that this uses a different ranking metric than _calc_aliquot_component_rank()
    sort_val = 0
    for position, x in enumerate(components, start=1):
        x_val = 0
        # First char NSEW
        if x[0] == 'N':
            x_val += 0
        elif x[0] == 'S':
            x_val += 10
        elif x[0] == 'E':
            x_val += 20
        elif x[0] == 'W':
            x_val += 30
        # Second char NSEW, or half.
        if x[1] == '2':
            x_val += 1
        elif x[1] == 'N':
            x_val += 2
        elif x[1] == 'S':
            x_val += 3
        elif x[1] == 'E':
            x_val += 4
        elif x[1] == 'W':
            x_val += 5
        sort_val += x_val / (10 ** (position * 2))
    return sort_val
