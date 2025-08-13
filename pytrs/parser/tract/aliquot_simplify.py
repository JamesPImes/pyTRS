"""
Functions for combining parsed QQs into simpler aliquots.
"""

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
    def __init__(self, parent=None, label: str = None):
        self.parent: AliquotNode = parent
        self.label: str = label
        self.children: dict[str, AliquotNode] = {}
        self.avail_consolidations: set[tuple[str]] = set()
        self.full = False
        self._rendered = False

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

    def get(self, qq, default=None):
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
        return self.is_leaf() or self._subset_full(labels=['NE', 'NW', 'SE', 'SW'], _trim=True)

    def all_rendered(self):
        if self._rendered:
            return True
        child_check = [child.all_rendered() for lbl, child in self.children.items()]
        check = all(child_check)
        if check:
            self._rendered = True
        return check

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
        # labels = ['NE', 'NW']  for 'N2'
        if self.full:
            self.avail_consolidations = {tuple(HALF_DEFS.keys())}
            return self.avail_consolidations
        full_quarters = set()
        child_options = {}
        for aliq, child in self.children.items():
            new_options = child._calc_available_consolidations()
            if child.full:
                full_quarters.add(aliq)
            else:
                child_options[aliq] = new_options

        half_options = set()
        for candidate_half, quarters in HALF_DEFS.items():
            node_pair = [self.get(q) for q in quarters]
            if any(node is None for node in node_pair):
                continue
            if all(node.full for node in node_pair):
                # Entire half -- e.g., N2, S2, etc.
                half_options.add((candidate_half,))
                continue
            a, b = node_pair
            for cand_consolid in a.avail_consolidations:
                direction_sample = cand_consolid[0]
                if direction_sample not in COMPATIBLE_HALVES[candidate_half]:
                    # Must keep N/S together, and E/W -- e.g., can't mix N2 with E2.
                    continue
                if cand_consolid in b.avail_consolidations:
                    new_consolidation = (candidate_half,) + cand_consolid
                    half_options.add(new_consolidation)
        self.avail_consolidations = half_options
        return self.avail_consolidations


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

    Note also: This will not combine aliquots across quarter-boundaries.
    That is, N2NE + N2NW will not combine into N2N2. This is an area for
    future improvements.
    """

    # First breaks down the list of aliquot strings into a tree (stored as a dict).
    # Then uses DFS to recursively recompile them into the fewest possible aliquots.

    def combine_aliquot_components(available_components: set, final=False) -> set:
        """
        Helper function to merge all possible aliquot sub-components.
        Ex: ``('NE', 'NW', 'SE')`` -> ``('N2', 'SE')``
        :param available_components: A set of aliquot components that
         are available to be combined.
        :param final: Whether this is the final pass.
        """
        combined_components = set()
        for cand_components, cand_aliq in _ALIQUOT_DEFS:
            if not assume_standard and cand_aliq == 'ALL':
                continue
            if cand_aliq == '' and final:
                continue
            if cand_components <= available_components:
                # All necessary components in the candidate aliquot are found
                # in the actual components, so combine.
                combined_components.add(cand_aliq)
                # Take the newly used components out of future consideration.
                available_components.difference_update(cand_components)
        # Add any stragglers back to the set of rebuilt components.
        combined_components.update(available_components)
        return combined_components

    def compile_aliquot_tree(aq_tree: dict):
        """
        Helper function to compile the aliquot tree back into aliquot strings.
        """
        # Recompile the aliquots with recursive DFS algorithm.
        # TODO (future improvement): Combine N2NE + N2NW --> N2N2 (etc.)
        aliquots_recompiled = set()
        for aliq, children in aq_tree.items():
            subcomponents = compile_aliquot_tree(children)
            if len(subcomponents) == 0:
                aliquots_recompiled.add(aliq)
                continue
            rebuilt_components = combine_aliquot_components(subcomponents)
            for comp in rebuilt_components:
                aliquots_recompiled.add(f"{comp}{aliq}")
        return aliquots_recompiled

    # Must break any halves into quarters to use a 4-branching tree structure.
    qqs = qqs.copy()
    split_qqs = []
    while qqs:
        qq = qqs.pop()
        if '2' not in qq:
            split_qqs.append(qq)
            continue
        tp = TractParser(text=qq, clean_qq=True, break_halves=True)
        for split_qq in tp.qqs:
            split_qqs.append(split_qq)

    aliquot_tree = {}
    for qq in split_qqs:
        # Deconstruct QQ string into 2-character segments.
        #   'NENWSW' -> ['SW', 'NW', 'NE']
        #   Eventual resulting tree structure -> {'SW': {'NW': {'NE': {}}}}
        decon_qq = [qq[i:i + 2] for i in range(0, len(qq), 2)]
        decon_qq.reverse()
        node = aliquot_tree
        for i, component in enumerate(decon_qq):
            node.setdefault(component, {})
            node = node[component]
    reconstruc_aliqs = compile_aliquot_tree(aliquot_tree)
    # One final combination.
    reconstruc_aliqs = combine_aliquot_components(reconstruc_aliqs, final=True)
    aliquots = sorted(reconstruc_aliqs, key=_aliquot_rank)
    return aliquots


def _aliquot_rank(aliquot: str):
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
    decon_aliq = [aliquot[i:i + 2] for i in range(0, len(aliquot), 2)]
    decon_aliq.reverse()
    sort_val = 0
    for position, x in enumerate(decon_aliq, start=1):
        x_val = 0
        # First char NSEW
        if x[0] == 'S':
            x_val += 10
        elif x[0] == 'E':
            x_val += 20
        elif x[0] == 'W':
            x_val += 30
        # Second char NSEW, or half.
        if x[1] == '2':
            x_val += 0
        elif x[1] == 'N':
            x_val += 1
        elif x[1] == 'S':
            x_val += 2
        elif x[1] == 'E':
            x_val += 3
        elif x[1] == 'W':
            x_val += 4
        sort_val += x_val / (10 ** (position * 2))
    return sort_val
