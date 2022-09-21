
"""
Customized containers for ``Tract`` and ``TRS`` objects, along with
helper functions for grouping (or ungrouping) and sorting.
"""

import re

from ...utils import flatten
from ...utils import _confirm_list_of_strings as clean_attributes
from ..tract import Tract
from ..trs import TRS


class _TRSTractList:
    """
    INTERNAL USE:

    This class is not used directly but is subclassed as ``TractList``
    and ``TRSList``.

    ``TRSList`` holds only ``TRS`` objects; and ``TractList`` holds only
    ``Tract`` objects.

    Both subclasses will sort / filter / group their respective element
    types. But ``TractList`` has quite a bit of additional functionality
    for streamlined extraction of data from ``Tract`` objects.
    """

    # These will be modified in the subclasses to determine what
    # elements can be processed by each.
    _ok_individuals = ()
    _ok_iterables = ()
    _typeerror_msg = ''

    def __init__(self, iterable=()):
        """
        INTERNAL USE:
        (Initialize a ``TRSList`` or ``TractList`` directly.)

        :param iterable: Same as in ``list()``
        """
        self._elements = self._verify_iterable(iterable)

    @classmethod
    def _verify_iterable(cls, iterable, into=None):
        """
        INTERNAL USE:
        Type-check the contents of an iterable. Return a plain list of
        the elements in ``iterable`` if all are legal.
        """
        if isinstance(iterable, str):
            # A string is technically iterable, and they are acceptable
            # by a `TRSList` -- but NOT to be iterated over. If a
            # TRSList iterates over a string, each character would be
            # converted to an error `TRS` object, and nobody wants that.
            raise TypeError("type 'str' is not an acceptable iterable.")
        if into is None:
            into = []
        if isinstance(iterable, cls):
            into.extend(iterable)
            return into
        for elem in iterable:
            if isinstance(elem, cls._ok_individuals):
                into.append(cls._verify_individual(elem))
        return into

    @classmethod
    def _verify_individual(cls, obj):
        """INTERNAL USE: Type-check a single object."""
        if not isinstance(obj, cls._ok_individuals):
            raise TypeError(
                f"{cls._typeerror_msg} Cannot accept {type(obj)!r}.")
        return cls._handle_type_specially(obj)

    @classmethod
    def _handle_type_specially(cls, obj):
        """INTERNAL USE: (For subclassing purposes.)"""
        return obj

    def __setitem__(self, index, value):
        self._verify_individual(value)
        self._elements[index] = value

    def __getitem__(self, item):
        return self._elements[item]

    def __contains__(self, o):
        return self._elements.__contains__(o)

    def __len__(self):
        return self._elements.__len__()

    def __iter__(self):
        return iter(self._elements)

    def __reversed__(self):
        return self._elements.__reversed__()

    def __repr__(self):
        return str(self)

    def extend(self, iterable):
        self._elements.extend(self._verify_iterable(iterable))

    def append(self, obj):
        self._elements.append(self._verify_individual(obj))

    def __iadd__(self, other):
        self._elements = self._elements + self._verify_iterable(other)
        return self

    def __add__(self, value):
        return self.__class__(self._elements + self._verify_iterable(value))

    def __imul__(self, n):
        self._elements = self._elements * n
        return self

    def __mul__(self, n):
        return self.__class__(self._elements * n)

    def __eq__(self, other):
        """
        Will only compare equality between objects of the same type,
        even if the other object is a list of the same ``Tract`` or
        ``TRS`` objects.
        """
        if not isinstance(other, self.__class__):
            return False
        return self._elements == other._elements

    def insert(self, i, obj):
        return self._elements.insert(i, self._verify_individual(obj))

    def pop(self, n=-1):
        return self._elements.pop(n)

    def copy(self):
        return self.__class__(self._elements.copy())

    def sort(self, key=None, reverse=False):
        if key is None:
            return self.custom_sort(reverse=reverse)
        return self._elements.sort(key=key, reverse=reverse)

    def to_standard_list(self):
        """
        Get the elements of this container in a standard built-in list.

        :return: A standard list containing the same elements.
        """
        return self._elements.copy()

    def filter(self, key, drop=False):
        """
        Extract from this custom list all elements that match the
        ``key`` (a lambda or other function that returns a bool or
        bool-like value when applied to each element).

        Returns a new `TractList` of the selected ``Tract`` objects
        (or a ``TRSList`` of the selected ``TRS`` objects, if called as
        a ``TRSList`` method).

        :param key: a lambda or other function that returns a bool or
         bool-like value when applied to an element in this list. (Note:
         ``True`` or ``True``-like returned values will result in the
         inclusion of that element).

        :param drop: Whether to drop the matching elements from the
         original list. (Defaults to ``False``)

        :return: A new ``TractList`` (or ``TRSList``, if applicable) of
         the selected elements. (The original list will still hold all
         other elements, unless ``drop=True`` was passed.)
        """
        indexes_to_include = []
        for i, element in enumerate(self):
            if key(element):
                indexes_to_include.append(i)
        return self._new_list_from_self(indexes_to_include, drop)

    def filter_errors(self, twp=True, rge=True, sec=True, undef=False, drop=False):
        """
        Extract from this custom list all elements that were parsed
        with an error. Specifically extract Twp/Rge errors with
        ``twp=True`` and ``rge=True``; and get Section errors with
        ``sec=True`` (all of which are on by default).

        Returns a new ``TractList`` (or ``TRSList``, as applicable) of
        the selected elements.

        :param twp: a bool, whether to get Twp errors. (Defaults to
         ``True``)

        :param rge: a bool, whether to get Rge errors. (Defaults to
         ``True``)

        :param sec: a bool, whether to get Sec errors. (Defaults to
         ``True``)

        :param undef: a bool, whether to get consider Twps, Rges, or
         Sections that were UNDEFINED to also be errors. (Defaults to
         ``False``)

        :param drop: Whether to drop the selected elements from the
         original list. (Defaults to ``False``)

        :return: A new ``TractList`` (or ``TRSList``, as applicable)
         containing the selected elements.
        """
        indexes_to_include = []
        for i, element in enumerate(self):
            trs = TRS(element.trs)
            if ((undef and trs.is_undef(twp, rge, sec))
                    or trs.is_error(twp, rge, sec)):
                indexes_to_include.append(i)
        return self._new_list_from_self(indexes_to_include, drop)

    def filter_duplicates(self, method='default', drop=False):
        """
        Find the duplicate ``Tract`` (or ``TRS`` objects) in this custom
        list, get a new custom list of the elements that were
        duplicates, and optionally ``drop`` the duplicates from the
        original list.

        To be clear, if there are three identical elements in the list,
        the returned ``TractList`` (or ``TRSList``, as applicable) will
        contain only two of them, and the original will still have one,
        being the first one.

        Control how to assess duplicates by passing one of the following
        values to ``method=``:

        - ``method='instance'``
            - Whether two objects are actually the same instance -- i.e.
              literally the same object. By definition, this will also
              apply even if one of the other two methods is used.

        - ``method='lots_qqs'``
            - Whether the ``.trs`` matches *and* ``.lots_qqs`` attribute
              contains the same lots/aliquots (after removing
              duplicates).  *Note:* Lots and aliquots must have been
              parsed for a given ``Tract`` object, or it will not match
              as a duplicate with this parameter.
                - Ex: Will match these as duplicate tracts, assuming
                  they were parsed with identical ``config`` settings::

                      154n97w14: Lots 1 - 3, S/2NE/4
                      154n97w14: Lot 3, S/2NE/4, Lots 1, 2
                - *Note:* Has no effect when used on a ``TRSList``,
                  because it does not contain ``Tract`` objects.

        - ``method='desc'``
            - Whether the ``.trs`` and ``.pp_desc`` (i.e. preprocessed
              description) combine to form an identical tract.
                - Ex: Will match these as duplicate tracts::

                        154n97w14: NE/4
                        154n97w14: Northeast Quarter

                - *Note:* This *does* work on a ``TRSList``, but matches
                  matches only on ``.trs`` attribute (equivalent to
                  ``method='trs'``).

        - ``method='trs'``
            - Duplicate ``.trs`` attributes.
                - *Warning:* This option is NOT recommended when calling
                  the method on a ``TractList`` object. This is more
                  appropriate when calling it on a ``TRSList`` object.

        - ``method='default'``
            - Use ``'instance'`` if working with a ``TractList`` object
            - Use ``'trs'`` if working with a ``TRSList`` object.

        :param method: Specify how to assess whether ``Tract`` objects
         (or ``TRS``, as applicable) objects are duplicates (either
         ``'instance'``, ``'lots_qqs'``, ``'desc'``, ``'trs'``, or
         ``'default'``).  See above for example behavior of each.

        :param drop: Whether to remove the identified duplicates from
         the original list.

        :return: A new ``TractList`` (or ``TRSList``, as applicable).
        """
        unique = set()
        indexes_to_include = []

        if method == 'default':
            method = 'instance'
            if isinstance(self, TRSList):
                method = 'trs'
        options = ('instance', 'lots_qqs', 'desc', 'trs')
        if method not in options:
            raise ValueError(f"`method` must be one of {options}")
        lots_qqs = method == 'lots_qqs'
        desc = method == 'desc'
        trs = method == 'trs'
        only_by_instance = not (lots_qqs or desc or trs)

        for i, element in enumerate(self):
            # Always find duplicate instances (because not all Tract
            # objects are parsed into lots/qqs).
            if element in unique:
                indexes_to_include.append(i)
            unique.add(element)
            if only_by_instance:
                continue

            to_check = element
            if lots_qqs:
                if not isinstance(element, Tract):
                    continue
                if not element.parse_complete:
                    continue
                lq = sorted(set(element.lots_qqs))
                to_check = f"{element.trs}_{lq}"
            if desc:
                if isinstance(element, Tract):
                    # TractList
                    to_check = f"{element.trs}_{element.pp_desc.strip()}"
                elif isinstance(element, TRS):
                    # TRS (uses only .trs attribute)
                    to_check = element.trs
            if trs:
                to_check = element.trs

            if to_check not in unique:
                unique.add(to_check)
            elif i not in indexes_to_include:
                # Use elif to avoid double-appending i (may have already
                # been added from the `instance` check).
                indexes_to_include.append(i)

        return self._new_list_from_self(indexes_to_include, drop)

    def _new_list_from_self(self, indexes: list, drop: bool):
        """
        INTERNAL USE:

        Get a new ``TractList`` (or ``TRSList``, as applicable) of the
        elements at the specified ``indexes``.  Optionally remove them
        from the original list with ``drop=True``.

        :param indexes: Indexes of the elements to include in the new
         ``TractList`` (or ``TRSList``).
        :param drop: a bool, whether to drop those elements from the
         original list.
        :return: The new ``TractList`` (or ``TRSList``).
        """
        new_list = self.__class__()
        # Populate the new list in reverse order, in order to remove the
        # intended elements from the original list if requested.
        for i in range(len(indexes) - 1, -1, -1):
            ind = indexes[i]
            new_list.append(self[ind])
            if drop:
                self.pop(ind)
        new_list.reverse()
        return new_list

    def reverse(self):
        self._elements.reverse()

    def custom_sort(self, key='i,s,r,t', reverse=False):
        """
        Sort the elements in this ``TractList`` (or ``TRSList``).

        The standard ``list.sort(key=<lambda>, reverse=<bool>)``
        parameters can be used here, but this method has additional
        customized key options.

        .. note::
            The *parameter* ``reverse=<bool>`` applies only to lambda
            sorts, and NOT to the custom keys detailed below.  To
            reverse the custom sort keys, use the ``'.rev'`` encoding
            discussed below.

        Customized key options:

        - ``'i'`` -- Sort tracts by the order in which they were
          created. (*Note:* ``'i'`` sorting has no effect on a
          ``TRSList``.)

        - ``'t'`` -- Sort by Township, such as:
            - ``'t.num'`` -- Sort by raw number, ignoring N/S. (†)
            - ``'t.ns'`` -- Sort from north-to-south
            - ``'t.sn'`` -- Sort from south-to-north

        - ``'r'`` -- Sort by Range, such as:
            - ``'r.num'`` -- Sort by raw number, ignoring E/W. (†)
            - ``'r.ew'`` -- Sort from east-to-west (‡)
            - ``'r.we'`` -- Sort from west-to-east (‡)

        *(†) Denotes default behavior of sub-key.*

        *(‡) Note: These do not account for Principal Meridians.*

        - ``'s'`` -- Sort by Section number.

        Reverse any of the keys by adding ``'.reverse'`` (or ``'.rev'``)
        at the end of each desired key(s) to be reversed.

        Use as many sort keys as you want. They will be applied in order
        from left-to-right, so place the highest 'priority' sort last.

        Twp/Rge's that are errors (i.e. ``'XXXzXXXz'``) will be sorted
        to the end of the list when sorting on Twp and/or Rge (whether
        by number, north-to-south, south-to-north, east-to-west, or
        west- to-east).  Similarly, error Sections (i.e. ``'XX'``) will
        be sorted to the end of the list when sorting on section.  (The
        exception is if the sort is reversed, in which case, they come
        first.)

        Construct all keys as a single string, separated by comma
        (spaces are optional). The components of each key should be
        separated by a period.

        Example keys::

            's.reverse,r.ew,t.ns'
                ->  Sort by section number (reversed, so largest-to-
                        smallest);
                ->  then sort by Range (east-to-west);
                ->  then sort by Township (north-to-south)

            'i,s,r,t'  (this is the default)
                ->  Sort by original creation order;
                ->  then sort by Section (smallest-to-largest);
                ->  then sort by Range (smallest-to-largest);
                ->  then sort by Township (smallest-to-largest)

        Example use of key::

            tractlist_or_trslist.custom_sort(key='s.reverse,r.ew,t.ns')

        Moreover, we can conduct multiple sorts by passing ``key`` as a
        list of sort keys. We can mix and match string keys above with
        lambdas, although the ``reverse=<bool>`` will apply only to the
        lambdas.

        Optionally pass ``reverse=`` as a list of bools (i.e. a list
        equal in length to ``key=<list of sort keys>``) to use different
        ``reverse`` values for different lambdas. But then make sure
        that the lengths are equal, or it will raise an ``IndexError``.

        :param key: A str, specifying which sort(s) should be done, and
         in which order. Alternatively, a lambda function (same as for
         the builtin ``list.sort(key=<lambda>)`` method).

         May optionally pass ``sort_key`` as a list of sort keys, to be
         applied left-to-right. In that case, lambdas and string keys
         may be mixed and matched.

        :param reverse: (Optional) Whether to reverse the sort.

         *Note:* This *only* has an effect if the ``key`` is passed as a
         lambda (or a list containing lambdas). It has no effect on
         string keys (for which you would instead specify ``'.rev'``
         within the string ``key`` itself). Defaults to ``False``.

         *Note also:* If ``key`` was passed as a list of keys, then
         ``reverse`` must be passed as EITHER a single bool that will
         apply to all (non-string) sorts, OR as a list of bools that is
         equal in length to ``key`` (i.e. the values in ``key`` and
         ``reverse`` will be matched up one-to-one).

        :return: None
        """
        if not key:
            return None

        # Determine whether the sort_key was passed as a list/tuple
        # (i.e. if we're doing one sort operation or multiple).
        is_multi_key = isinstance(key, (list, tuple))
        is_multi_rev = isinstance(reverse, (list, tuple))
        if is_multi_key and not is_multi_rev:
            reverse = [reverse for _ in key]

        # If `iterable` sort_key and/or `sort_reverse`, make sure
        # the length of each matches.
        if ((is_multi_key and len(key) != len(reverse))
                or (is_multi_rev and not is_multi_key)):
            raise IndexError(
                "Mismatched length of iterable `sort_key` "
                "and `sort_reverse`")

        if is_multi_key:
            # If multiple sorts, do each.
            for sk, rv in zip(key, reverse):
                self.custom_sort(key=sk, reverse=rv)
        elif isinstance(key, str):
            # `._sort_custom` takes str-type sort keys.
            self._sort_custom(key)
        else:
            # Otherwise, assume it's a lambda. Use builtin `sort()`.
            self.sort(key=key, reverse=reverse)
        return None

    def _sort_custom(self, key: str = 'i,s,r,t'):
        """
        INTERNAL USE:

        Apply the custom str-type sort keys detailed in
        ``.custom_sort()``.

        *Note:* Documentation on the str-type sort keys is maintained in
        ``.custom_sort()``.

        :param key: A str, specifying which sort(s) should be done, and
         in which order.

        :return: None
        """

        def get_max(var):
            """
            Get the largest value of the matching var in the of any
            element in this list. If there are no valid ints, return 0.
            """
            nums = [getattr(t, var) for t in self if getattr(t, var) is not None]
            if nums:
                return max(nums)
            return 0

        # TODO: Sort undefined Twp/Rge/Sec before error Twp/Rge/Sec.

        default_twp = get_max("twp_num") + 1
        default_rge = get_max("rge_num") + 1
        default_sec = get_max("sec_num") + 1

        assume = {
            "twp_num": default_twp,
            "rge_num": default_rge,
            "sec_num": default_sec
        }

        illegal_key_error = ValueError(f"Could not interpret sort key {key!r}.")

        # The regex pattern for a valid key component.
        pat = r"(?P<var>[itrs])(\.(?P<method>ns|sn|ew|we|num))?(\.(?P<rev>rev(erse)?))?"

        legal_methods = {
            "i": ("num", None),
            "t": ("ns", "sn", "num", None),
            "r": ("ew", "we", "num", None),
            "s": ("num", None)
        }

        def extract_safe_num(tract, var):
            val = getattr(tract, var)
            if val is None:
                val = assume[var]
            return val

        def i_sort_evaluate(list_element):
            """
            If the element is a ``Tract`` object, extract and return its
            internal UID. Otherwise, return 0.

            (This function exists so that the sort method works on a
            list of ``Tract`` objects as well as a list of ``TRS``
            objects, the latter of which do not have a ``._Tract__uid``
            attribute.)
            """
            if isinstance(list_element, Tract):
                return list_element._Tract__uid
            else:
                return 0

        sort_defs = {
            'i.num': i_sort_evaluate,
            't.num': lambda x: extract_safe_num(x, "twp_num"),
            't.ns': lambda x: n_to_s(x),
            't.sn': lambda x: n_to_s(x, reverse=True),
            'r.num': lambda x: extract_safe_num(x, "rge_num"),
            'r.we': lambda x: w_to_e(x),
            'r.ew': lambda x: w_to_e(x, reverse=True),
            's.num': lambda x: extract_safe_num(x, "sec_num")
        }

        def n_to_s(element, reverse=False):
            """
            Convert Twp number and direction to a positive or negative
            int, depending on direction. North townships are negative;
            South are positive (in order to leverage the default
            behavior of ``list.sort()`` -- i.e. smallest to largest).
            ``reverse=True`` to inverse the positive and negative.
            """
            num = element.twp_num
            ns = element.twp_ns

            multiplier = 1
            if num is None:
                num = default_twp
            if ns is None:
                multiplier = 1
            if ns == 's':
                multiplier = 1
            elif ns == 'n':
                multiplier = -1
            if reverse:
                multiplier *= -1
            if ns is None:
                # Always put _TRR_ERROR parses at the end.
                multiplier *= -1 if reverse else 1
            return multiplier * num

        def w_to_e(element, reverse=False):
            """
            Convert Rge number and direction to a positive or negative
            int, depending on direction. East townships are positive;
            West are negative (in order to leverage the default behavior
            of ``list.sort()`` -- i.e. smallest to largest).
            ``reverse=True`` to inverse the positive and negative.
            """
            num = element.rge_num
            ew = element.rge_ew

            multiplier = 1
            if num is None:
                num = default_rge
            if ew == 'e':
                multiplier = 1
            elif ew == 'w':
                multiplier = -1
            if reverse:
                multiplier *= -1
            if ew is None:
                # Always put _TRR_ERROR parses at the end.
                multiplier *= -1 if reverse else 1
            return multiplier * num

        def parse_key(k_):
            k_ = k_.lower()
            mo = re.search(pat, k_)
            if not mo:
                raise illegal_key_error
            if len(mo.group(0)) != len(k_):
                import warnings
                warnings.warn(SyntaxWarning(
                    f"Sort key {k_!r} may not have been fully interpreted. "
                    f"Check to make sure you are using the correct syntax."
                ))

            var = mo.group("var")
            method = mo.group("method")

            if method is None:
                # default to "num" for all vars.
                method = "num"
            # Whether to reverse
            rev = mo.group("rev") is not None

            # Confirm legal method for this var
            if method not in legal_methods[var]:
                raise ValueError(f"invalid sort method: {k!r}")

            var_method = f"{var}.{method}"
            return var_method, rev

        key = key.lower()
        key = re.sub(r"\s", "", key)
        key = re.sub(r"reverse", "rev", key)
        keys = key.split(',')
        for k in keys:
            sk, reverse = parse_key(k)
            self.sort(key=sort_defs[sk], reverse=reverse)

    def group_by_nested(
            self,
            attribute="twprge",
            into: dict = None,
            sort_key=None,
            sort_reverse=False):
        """
        Group the elements in this list into a dict, keyed by unique
        values of ``attribute``.  By default, will form groups that
        share Twp/Rge (i.e. ``attribute='twprge'``).

        Pass ``attribute`` as a *list* of attributes to group by
        multiple attributes, in which case the keys of the returned dict
        will be tuples of each group's matching attributes.

        *Note:* This method is similar to ``.group_by_nested()``, except
        for how it handles grouping by multiple attributes.
        Specifically, this method returns a single-level dict
        whose keys will be tuples of each group's attributes when
        grouping by multiple attributes - whereas ``.group_by_nested()``
        returns a nested dict (one level per grouping attribute).

        :param attribute: The str name of an attribute of ``Tract``
         objects (or ``TRS`` objects, if working with a ``TRSList``
         object). (Defaults to ``'twprge'``). NOTE: Must be a hashable
         type!  (Optionally pass as a list of multiple attribute names
         to do multiple groupings.)

        :param into: (Optional) An existing dict into which to group
         the elements. If not specified, will create a new dict. Use
         this arg if you need to continue adding to an existing grouped
         dict.

        :param sort_key: (Optional) How to sort each grouped
         ``TractList`` (or ``TRSList``, as applicable) in the returned
         dict. Use a string that works with the
         ``.custom_sort(key=<str>)`` method (e.g.,
         ``'i, s, r.ew, t.ns'``) or a lambda function, as you would with
         the builtin ``list.sort(key=<lambda>)`` method. (Defaults to
         ``None``, i.e. not sorted.)

         May optionally pass ``sort_key`` as a list of sort keys, to be
         applied left-to-right. Here, you may mix and match lambdas and
         ``.sort_tracts()`` strings.  (See documentation on
         ``TractList.custom_sort()``.)

        :param sort_reverse: (Optional) Whether to reverse the sort.
         Defaults to ``False``.

         *Note:* Only has an effect if the ``sort_key`` is passed as a
         lambda -- *not* as a custom string sort key.

         *Note also:* If ``sort_key`` was passed as a list, then
         ``sort_reverse`` must be passed as EITHER a single bool that
         will apply to all (non-string) sorts, OR as a list or tuple of
         bools that is equal in length to ``sort_key`` (i.e. the values
         in ``sort_key`` and ``sort_reverse`` will be matched up
         one-to-one).

         (Again, see documentation on ``TractList.custom_sort()``.)

        :return: A dict of ``TractList`` objects (or ``TRSList``
         objects, as applicable) each containing those elements with
         matching values of the ``attribute``. If ``attribute`` was
         passed as a list of attribute names, then the keys in the
         returned dict will be a tuple whose values line up with the
         list passed as ``attribute``.)
        """
        # Determine whether it's a single-attribute grouping, or multiple.
        this_attribute = attribute
        is_multi_group = isinstance(attribute, list)
        if is_multi_group:
            attribute = attribute.copy()
            this_attribute = attribute.pop(0)
            if not attribute:
                # If this is the last one to run.
                is_multi_group = False

        if not is_multi_group:
            # The `._group()` method handles single-attribute groupings.
            return self._group(
                self, this_attribute, into, sort_key, sort_reverse)

        def add_to_existing_dict(dct_, into_=into):
            """
            Recursively add keys/values to the original ``into`` dict.
            """
            if into_ is None:
                return dct_
            for k_, v_ in dct_.items():
                # This will always be one of two pairs:
                #   a key/TractList (or TRSList) pair (in which case we
                #       have reached the bottom); OR
                #   a key/dict pair (in which case, we need to do
                #       another recursion)
                if isinstance(v_, self.__class__):
                    into_.setdefault(k_, self.__class__())
                    into_[k_].extend(v_)
                else:
                    into_.setdefault(k_, {})
                    add_to_existing_dict(v_, into_=into_[k_])
            return into_

        # Do a single-attribute grouping as our first pass.
        dct = self._group(self, this_attribute)

        # We have at least one more grouping to do, so recursively group
        # each current TractList/TRSList object.
        dct_2 = {}
        for k, tlist in dct.items():
            dct_2[k] = tlist.group_nested(attribute=attribute, into=None)

        # Unpack dct_2 into the existing dict (`into`), sort, and return.
        dct = add_to_existing_dict(dct_2, into)
        self.sort_grouped(dct, sort_key, sort_reverse)
        return dct

    def group_by(
            self, attribute="twprge", into: dict = None, sort_key=None,
            sort_reverse=False):
        """
        Group the elements in this list into a dict, keyed by unique
        values of ``attribute``.  By default, will form groups that
        share Twp/Rge (i.e. ``attribute='twprge'``).

        Pass ``attribute`` as a *list* of attributes to group by
        multiple attributes, in which case the keys of the returned dict
        will be tuples of each group's matching attributes.

        *Note:* This method is similar to ``.group_by_nested()``, except
        for how it handles grouping by multiple attributes.
        Specifically, this method returns a single-level dict
        whose keys will be tuples of each group's attributes when
        grouping by multiple attributes - whereas ``.group_by_nested()``
        returns a nested dict (one level per grouping attribute).

        :param attribute: The str name of an attribute of ``Tract``
         objects (or ``TRS`` objects, if working with a ``TRSList``
         object). (Defaults to ``'twprge'``). NOTE: Must be a hashable
         type!  (Optionally pass as a list of multiple attribute names
         to do multiple groupings.)

        :param into: (Optional) An existing dict into which to group
         the elements. If not specified, will create a new dict. Use
         this arg if you need to continue adding to an existing grouped
         dict.

        :param sort_key: (Optional) How to sort each grouped
         ``TractList`` (or ``TRSList``, as applicable) in the returned
         dict. Use a string that works with the
         ``.custom_sort(key=<str>)`` method (e.g.,
         ``'i, s, r.ew, t.ns'``) or a lambda function, as you would with
         the builtin ``list.sort(key=<lambda>)`` method. (Defaults to
         ``None``, i.e. not sorted.)

         May optionally pass ``sort_key`` as a list of sort keys, to be
         applied left-to-right. Here, you may mix and match lambdas and
         ``.sort_tracts()`` strings.  (See documentation on
         ``TractList.custom_sort()``.)

        :param sort_reverse: (Optional) Whether to reverse the sort.

         *Note:* Only has an effect if the ``sort_key`` is passed as a
         lambda -- NOT as a custom string sort key. Defaults to ``False``

         *Note also:* If ``sort_key`` was passed as a list, then
         ``sort_reverse`` must be passed as EITHER a single bool that
         will apply to all (non-string) sorts, OR as a list or tuple of
         bools that is equal in length to ``sort_key`` (i.e. the values
         in ``sort_key`` and ``sort_reverse`` will be matched up
         one-to-one).

         (Again, see documentation on ``TractList.custom_sort()``.)

        :return: A dict of ``TractList`` objects (or ``TRSList``
         objects, as applicable) each containing those elements with
         matching values of the ``attribute``. If ``attribute`` was
         passed as a list of attribute names, then the keys in the
         returned dict will be a tuple whose values line up with the
         list passed as ``attribute``.)
        """
        # Determine whether it's a single-attribute grouping, or multiple.
        first_attribute = attribute
        is_multi_group = isinstance(attribute, list)
        if is_multi_group:
            attribute = attribute.copy()
            first_attribute = attribute.pop(0)
            if not attribute:
                # If this is the last one to run.
                is_multi_group = False

        if not is_multi_group:
            # The `._group()` method handles single-attribute groupings.
            return self._group(
                self, first_attribute, into, sort_key, sort_reverse)

        def get_keybase(key_):
            """
            Convert tuple to list and put any other object type in a
            list.  (i.e. make mutable to add an element to the list,
            which we'll then convert back to a tuple to serve as a dict
            key.)
            """
            if isinstance(key_, tuple):
                return list(key_)
            else:
                return [key_]

        dct = self._group(self, first_attribute)
        while attribute:
            dct_new = {}
            grp_att = attribute.pop(0)
            for k1, v1 in dct.items():
                k1_base = get_keybase(k1)
                dct_2 = self._group(v1, grp_att)
                for k2, v2 in dct_2.items():
                    dct_new[tuple(k1_base + [k2])] = v2
            dct = dct_new

        # Unpack `dct` into the existing dict (`into`), if applicable.
        if isinstance(into, dict):
            for k, tl in dct.items():
                into.setdefault(k, self.__class__())
                into[k].extend(tl)
            dct = into

        # Sort and return.
        self.sort_grouped(dct, sort_key, sort_reverse)
        return dct

    @classmethod
    def _group(
            cls, trstractlist, attribute="twprge", into: dict = None,
            sort_key=None, sort_reverse=False):
        """
        INTERNAL USE:
        (Users should use the public ``.group_by()`` method instead.)

        Group the elements in this custom list into a dict of custom
        lists of the same type, keyed by unique values of ``attribute``.
        By default, will form groups that share Twp/Rge (i.e.
        ``attribute='twprge'``).

        :trstractlist: A ``TRSList`` or ``TractList`` to be grouped.

        :param attribute: Same as for ``.group_by()`, but MUST BE A STR
         FOR THIS METHOD!

        :param into: Same as for ``.group_by()``.

        :param sort_key: Same as for ``.group_by()``.

        :param sort_reverse:  Same as for ``.group_by()``.

        :return: A dict of custom list objects (each the same type as
         the passed ``trstractlist``), each containing the objects with
         matching values of the `attribute`.  (Will NOT be a nested
         dict.)
        """
        dct = {}
        for t in trstractlist:
            val = getattr(t, attribute, f"{attribute}: n/a")
            dct.setdefault(val, cls())
            dct[val].append(t)
        if isinstance(into, dict):
            for k, tl in dct.items():
                into.setdefault(k, cls())
                into[k].extend(tl)
            dct = into
        if not sort_key:
            return dct
        for tl in dct.values():
            tl.custom_sort(key=sort_key, reverse=sort_reverse)
        return dct

    @classmethod
    def sort_grouped(cls, group_dict, sort_key, reverse=False) -> dict:
        """
        Sort the ``TractList`` objects (or ``TRSList`` objects) within a
        grouped dict (or nested grouped dict).

        Returns the original ``group_dict``, but with the ``TractList``
        (or ``TRSList``) objects having been sorted.

        :param group_dict: A dict, as returned by a ``TractList`` or
         ``TRSList`` grouping method or function (e.g., ``.group_by()``,
         ``.group_tracts_by()``, or ``.group_trs_by()``), whether nested
         or single-level.

        :param sort_key: How to sort the elements in the lists. (Can be
         any value acceptable to the ``.custom_sort()`` method.)

        :param reverse: (Optional) Whether to reverse lambda sorts.
         (More detail provided in the docs for ``.custom_sort()``.)

        :return: The original ``group_dict``, with the lists inside it
         having been sorted in place.
        """
        if not sort_key:
            return group_dict
        for k, v in group_dict.items():
            if isinstance(v, dict):
                cls.sort_grouped(v, sort_key, reverse)
            else:
                v.custom_sort(key=sort_key, reverse=reverse)
        return group_dict

    @classmethod
    def unpack_group(cls, group_dict: dict, sort_key=None, reverse=False):
        """
        Convert a grouped dict (or nested group dict) of ``TRSList`` or
        ``TractList`` objects into a new single ``TRSList`` or
        ``TractList`` object.

        *Note:* If ``group_dict`` contains ``TRSList`` objects, this
        method must be called as ``TRSList.unpack_group()``. Conversely,
        if ``group_dict`` contains ``TractList`` objects, this method
        must be called as ``TractList.unpack_group()``.

        :param group_dict: A dict, as returned by ``.group()`` or
         ``.group_nested()`` (or a nested dict inside what was returned
         by ``.group_nested()``).

        :param sort_key: (Optional) How to sort the elements in the
         returned list.  NOT applied to the original lists inside the
         dict.  (Can be any value acceptable to the ``.custom_sort()``
         method.)

        :param reverse: (Optional) Whether to reverse lambda sorts.
         (More detail provided in the docs for ``.custom_sort()``.)

        :return: A new ``TractList`` (or ``TRSList``, as applicable).
        """
        tl = cls()

        def unpack(dct):
            # Do the recursion within the `.unpack_group()` method
            # itself to leverage the scope of the `tl` we created.
            for v_ in dct.values():
                if isinstance(v_, dict):
                    # Recursively unpack nested dicts.
                    unpack(v_)
                else:
                    # Add the elements of this list.
                    tl.extend(v_)
        unpack(group_dict)
        if sort_key:
            tl.custom_sort(sort_key, reverse)
        return tl

    @classmethod
    def _from_multiple(cls, *objects, into=None):
        """
        INTERNAL USE:

        Create a ``TractList`` or ``TRSList`` from multiple sources of
        varying types.

        :param objects: For `TractList` objects, may pass any number or
         combination of ``Tract``, ``PLSSDesc``, and/or ``TractList``
         objects (or other iterable container holding any of those
         object types).

         For ``TRSList`` objects, may pass any number of ``TRS`` objects
         or strings in the pyTRS standardized Twp/Rge/Sec format, or
         ``TRSList`` objects.

        :param into: A new (unused) ``TRSList`` or ``TractList`` object.

        :return: The list originally passed as ``into``, now containing
         the extracted ``Tract`` or ``TRS`` objects.
        """
        if into is None:
            into = cls()
        for obj in objects:
            if isinstance(obj, cls._ok_individuals):
                into.append(obj)
            elif isinstance(obj, cls):
                # Other instances of this class have already been
                # appropriately type-checked.
                into.extend(obj)
            elif isinstance(obj, cls._ok_iterables):
                for obj_deeper in obj:
                    into.append(obj_deeper)
            else:
                # Assume it's another list-like object.
                for obj_deeper in obj:
                    # Elements are appended in place, no need to store var.
                    cls._from_multiple(obj_deeper, into=into)
        return into


class TractList(_TRSTractList):
    """
    An emulation of the builtin ``list``, specialized for ``Tract``
    objects, with added methods for sorting, grouping, and filtering the
    ``Tract`` objects.

    *Note:* ``TractList`` and ``TRSList`` are subclassed from the same
    superclass and have some of the same functionality for sorting,
    grouping, and filtering.  In the docstrings for many of the methods,
    there will be references to either ``Tract`` or ``TRS`` objects, and
    to ``TractList`` or ``TRSList`` objects.  To be clear, ``TractList``
    objects hold only ``Tract`` objects, and ``TRSList`` objects hold
    only ``TRS`` objects.


    **STREAMLINED OUTPUT OF THE PARSED TRACT DATA**

    These methods have essentially the same effect as in ``PLSSDesc``
    objects.

    - ``.quick_desc()``
        - Returns a string of the entire parsed description.

    - ``.print_desc()``
        - Does the same thing, but prints to console.

    - ``.tracts_to_dict()``
        - Compile the requested attributes for each ``Tract`` into a
          dict, and returns a list of those dicts (i.e. the list is
          equal in length to the ``TractList``).

    - ``.tracts_to_list()``
        - Compile the requested attributes for each ``Tract`` into a
          list, and returns a nested list of those list (i.e. the
          top-level list is equal in length to the ``TractList``).

    - ``.iter_to_dict()``
        - Identical to ``.tracts_to_dict()``, but returns a generator of
          dicts for the ``Tract`` data.

    - ``.iter_to_list()``
        - Identical to ``.tracts_to_list()``, but returns a generator of
          lists for the ``Tract`` data.

    - ``.tracts_to_csv()``
        - Compile the requested attributes for each ``Tract`` and write
          them to a .csv file, with one row per ``Tract``.  (See
          ``pytrs.tractwriter.TractWriter`` class for more robust
          writing to .csv files.)

    - ``.tracts_to_str()``
        - Compile the requested attributes for each ``Tract`` into an
          orderly string.

    - ``.print_data()``
        - Equivalent to ``.tracts_to_str()``, but the data is printed to
          console.

    - ``.list_trs()``
        - Return a list of all twp/rge/sec combinations in the
          ``TractList``, optionally removing duplicates.


    **SORTING / GROUPING / FILTERING TRACTS BY ATTRIBUTE VALUES**

    - ``.custom_sort()``
        - Custom sorting based on the Twp/Rge/Sec or original creation
          order of each ``Tract``. Can also take parameters from the
          built-in ``list.sort()`` method.

    - ``.group_by()``
        - Group ``Tract`` objects into a dict of ``TractList`` objects,
          based on their shared attribute values (e.g., by Twp/Rge), and
          optionally sort them.

    - ``.filter()``
        - Get a new ``TractList`` of ``Tract`` objects that match some
          condition, and optionally remove them from the original
          ``TractList``.

    - ``.filter_errors()``
        - Get a new TractList of Tract objects whose Twp, Rge, and/or
          Section were an error or undefined, and optionally remove them
          from the original ``TractList``.
    """

    # A TractList holds only Tract objects. But Tract objects can be
    # extracted from these types and added to the list.
    _ok_individuals = (Tract,)
    _ok_iterables = tuple()
    _typeerror_msg = "TractList will accept only type `pytrs.Tract`."

    def __init__(self, iterable=()):
        """
        :param iterable: An iterable (or `PLSSDesc`) containing `Tract`
         objects.
        """
        _TRSTractList.__init__(self, iterable)

    def __str__(self):
        return str(self.snapshot_inside()).replace('\n', r'\n')

    def __repr__(self):
        return f"TractList({len(self)})<{str(self)}>"

    def config_tracts(self, config):
        """
        Reconfigure all ``Tract`` objects in this ``TractList``.

        NOTE: Will NOT trigger the ``Tract`` objects to be (re)parsed,
        even if ``'parse_qq'`` is included in the new config.

        :param config: Either a ``Config`` object, or a string of
         parameters to configure how the ``Tract`` objects should be
         parsed.  (See documentation on ``Config`` objects for optional
         config parameters.)
        """
        for tract in self:
            tract.config = config
        return None

    def parse_tracts(
            self,
            config=None,
            clean_qq=None,
            suppress_lot_divs=None,
            qq_depth_min=None,
            qq_depth_max=None,
            qq_depth=None,
            break_halves=None):
        """
        Parse (or re-parse) all ``Tract`` objects in this ``TractList``
        into lots/QQ's using the specified parameters. Will pull parsing
        parameters from each ``Tract`` object's own ``.config`` (unless
        otherwise configured here).

        Optionally reconfigure each ``Tract`` object prior to parsing
        into lots/QQs by using the ``config=`` parameter here, or other
        parameters.  (The keyword parameters here will take priority
        over ``config``, if there is a conflict.)

        The parsed data will be committed to the ``Tract`` objects'
        attributes, overwriting data from a prior parse.

        :param config: (Optional) New config parameters to apply to each
         ``Tract`` before parsing.
        :param clean_qq: Same as in ``Tract.parse()`` method.
        :param suppress_lot_divs: Same as in ``Tract.parse()`` method.
        :param qq_depth_min: Same as in ``Tract.parse()`` method.
        :param qq_depth_max: Same as in ``Tract.parse()`` method.
        :param qq_depth: Same as in ``Tract.parse()`` method.
        :param break_halves: Same as in ``Tract.parse()`` method.
        :return: None
        """
        if config:
            self.config_tracts(config)
        for t in self:
            t.parse(
                clean_qq=clean_qq,
                suppress_lot_divs=suppress_lot_divs,
                qq_depth_min=qq_depth_min,
                qq_depth_max=qq_depth_max,
                qq_depth=qq_depth,
                break_halves=break_halves)
        return None

    @staticmethod
    def sort_grouped_tracts(tracts_dict, sort_key, reverse=False) -> dict:
        """
        Sort ``TractList`` objects within a dict of grouped tracts. Also
        works on a nested dict (i.e. when multiple groupings were done).

        Returns the original ``tracts_dict``, but with the ``TractList``
        objects having been sorted.

        :param tracts_dict: A dict, as returned by a TractList grouping
         method or function (e.g., ``TractList.group_by()`` or
         ``group_tracts()``).

        :param sort_key: How to sort the Tracts. (Can be any value
         acceptable to the ``TractList.sort_tracts()`` method.)

        :param reverse: (Optional) Whether to reverse lambda sorts.
         (More detail provided in the docs for
         ``TractList.sort_tracts()``.)

        :return: The original ``tracts_dict``, with the TractList
         objects having been sorted in-situ.
        """
        return _TRSTractList.sort_grouped(
            group_dict=tracts_dict, sort_key=sort_key, reverse=reverse)

    def tracts_to_dict(self, *attributes) -> list:
        """
        Compile the data for each ``Tract`` object into a dict
        containing the requested attributes only, and return a list of
        those dicts (the returned list being equal in length to this
        ``TractList`` object).

        Example:

        .. code-block:: python

            txt = '''154N-97W
            Sec 14: NE/4
            Sec 15: Northwest Quarter, North Half South West Quarter'''
            d_obj = PLSSDesc(txt)
            tl_obj = TractList(d_obj)
            tl_obj.tracts_to_dict('trs', 'desc', 'qqs')

        Example returns a list of two dicts::

            [
            {'trs': '154n97w14',
            'desc': 'NE/4',
            'qqs': ['NENE', 'NWNE', 'SENE', 'SWNE']},

            {'trs': '154n97w15',
            'desc': 'Northwest Quarter, North Half South West Quarter',
            'qqs': ['NENW', 'NWNW', 'SENW', 'SWNW', 'NESW', 'NWSW']}
            ]

        :param attributes: The names (strings) of whichever attributes
         should be included (see documentation on ``Tract`` objects
         for the names of relevant attributes).
        :return: List of dicts, containing the requested data for each
         ``Tract``.
        """
        attributes = clean_attributes(attributes)
        return [t.to_dict(attributes) for t in self]

    def tracts_to_list(self, *attributes) -> list:
        """
        Compile the data for each ``Tract`` object into a list
        containing the requested attributes only, and return a nested
        list of those lists (the returned list being equal in length to
        this ``TractList`` object).

        Example:

        .. code-block:: python

            txt = '''154N-97W
            Sec 14: NE/4
            Sec 15: Northwest Quarter, North Half South West Quarter'''
            d_obj = PLSSDesc(txt)
            tl_obj = TractList(d_obj)
            tl_obj.tracts_to_list('trs', 'desc', 'qqs')

        Example returns a nested list::

            [
                ['154n97w14',
                'NE/4',
                ['NENE', 'NWNE', 'SENE', 'SWNE']],

                ['154n97w15',
                'Northwest Quarter, North Half South West Quarter',
                ['NENW', 'NWNW', 'SENW', 'SWNW', 'NESW', 'NWSW']]
            ]

        :param attributes: The names (strings) of whichever attributes
         should be included (see documentation on ``Tract`` objects
         for the names of relevant attributes).

        :return: List of lists, containing the requested data for each
         ``Tract``.
        """
        attributes = clean_attributes(attributes)
        return [t.to_list(attributes) for t in self]

    def tracts_to_str(self, *attributes) -> str:
        """
        Compile the data for all ``Tract`` objects into an orderly
        string, containing the requested attributes only, and return a
        single string of the data.

        Example:

        .. code-block:: python

            txt = '''154N-97W
            Sec 14: NE/4
            Sec 15: Northwest Quarter, North Half South West Quarter'''
            d_obj = PLSSDesc(txt)
            tl_obj = TractList(d_obj)
            tl_obj.tracts_to_str('trs', 'desc', 'qqs')

        Example returns a multi-line string that looks like this when
        printed::

            Tract 1 / 2
            trs  : 154n97w14
            desc : NE/4
            qqs  : NENE, NWNE, SENE, SWNE

            Tract 2 / 2
            trs  : 154n97w15
            desc : Northwest Quarter, North Half South West Quarter
            qqs  : NENW, NWNW, SENW, SWNW, NESW, NWSW

        :param attributes: The names (strings) of whichever attributes
         should be included (see documentation on ``Tract`` objects
         for the names of relevant attributes).

        :return: An orderly string containing the requested data for
         each ``Tract``.
        """
        attributes = clean_attributes(attributes)

        # How far to justify the attribute names in the output str:
        jst = max([len(att) for att in attributes]) + 1
        # For justifying linebreaks within a value.
        jst_linebreak = f"\n{' ' * (jst + 2)}"

        total_tracts = len(self)
        all_tract_data = ""
        for i, t_dct in enumerate(self.tracts_to_dict(attributes), start=1):
            tract_data = f"\n\nTract {i} / {total_tracts}"
            if i == 1:
                tract_data = f"Tract {i} / {total_tracts}"
            for att_name, v in t_dct.items():
                # Flatten lists/tuples, but leave everything else as-is
                if isinstance(v, (list, tuple)):
                    v = ", ".join(flatten(v))
                v = str(v).replace("\n", jst_linebreak)
                # Justify attribute name and report its value
                tract_data = f"{tract_data}\n{att_name.ljust(jst, ' ')}: {v}"
            all_tract_data = f"{all_tract_data}{tract_data}"
        return all_tract_data

    def tracts_to_csv(
            self, attributes, fp, mode, nice_headers=False):
        """
        Write all ``Tract`` data to a .csv file (one row per ``Tract``).

        (Note: See ``pytrs.tractwriter.TractWriter`` class for more
        robust writing to .csv files.)

        :param attributes: a list of names (strings) of whichever
         attributes should be included (see documentation on
         ``Tract`` objects for the names of relevant attributes).

        :param fp: The filepath of the .csv file to write to.

        :param mode: The ``mode`` in which to open the file we're
         writing to. Either ``'w'`` (new file) or ``'a'`` (continue a
         file).

        :param nice_headers: By default, this method will use the
         attribute names as headers. To use custom headers, pass to
         ``nice_headers=`` any of the following:

         - a list of strings to use. (Should be equal in length to the
           list passed as ``attributes``, but will not raise an error
           if that's not the case. The resulting column headers will
           just be fewer than the actual number of columns.)

         - a dict, keyed by attribute name, and whose values are the
           corresponding headers. (Any missing keys will use the
           attribute name.)

         - ``True`` -- use the values in the ``Tract.ATTRIBUTES`` dict
           for headers. (WARNING: Any value passed that is not a list or
           dict and that evaluates to ``True`` will cause this
           behavior.)

         - If not specified (i.e. ``None`` or ``False``), will just use
           the attribute names themselves (default).

        :return: None
        """
        if not fp:
            raise ValueError("`fp` must be a filepath")
        from pathlib import Path
        fp = Path(fp)
        headers = True
        if fp.exists() and mode == "a":
            headers = False

        import csv
        attributes = clean_attributes(attributes)
        header_row = Tract.get_headers(attributes, nice_headers)

        def scrub_row(data):
            """Convert lists/dicts in a row to strings."""
            scrubbed = []
            for elem in data:
                if isinstance(elem, dict):
                    elem = ','.join([f"{k}:{v}" for k, v in elem.items()])
                elif isinstance(elem, (list, tuple)):
                    elem = ', '.join(elem)
                scrubbed.append(elem)
            return scrubbed

        with open(fp, mode=mode, newline="") as file:
            writer = csv.writer(file)
            if headers:
                writer.writerow(header_row)
            for tract in self:
                row = tract.to_list(attributes)
                row = scrub_row(row)
                writer.writerow(row)
        return None

    def iter_to_dict(self, *attributes):
        """
        Identical to ``.tracts_to_dict()``, but returns a generator of
        dicts, rather than a list of dicts.

        :param attributes: The names (strings) of whichever attributes
         should be included (see documentation on ``Tract`` objects for
         the names of relevant attributes).

        :return: A generator of data pulled from each ``Tract``, in the
         form of a dict.
        """
        for tract in self:
            yield tract.to_dict(attributes)

    def iter_to_list(self, *attributes):
        """
        Identical to ``.tracts_to_list()``, but returns a generator of
        lists, rather than a list of lists.

        :param attributes: The names (strings) of whichever attributes
         should be included (see documentation on ``Tract`` objects for
         the names of relevant attributes).

        :return: A generator of data pulled from each ``Tract``, in the
         form of a list.
        """
        for tract in self:
            yield tract.to_list(attributes)

    def quick_desc(self, delim=': ', newline='\n') -> str:
        # Note r-string, to escape '\n' character.
        r"""
        Returns the full description of all ``Tract`` objects as a
        single, orderly string.

        Example:

        .. code-block:: python

            txt = '''154N-97W
            Sec 14: NE/4
            Sec 15: Northwest Quarter, North Half South West Quarter'''
            d_obj = PLSSDesc(txt)
            tl_obj = TractList(d_obj)
            tl_obj.quick_desc()

        Example returns a multi-line string that looks like this when
        printed::

            154n97w14: NE/4
            154n97w15: Northwest Quarter, North Half South West Quarter

        :param delim: Specify what separates Twp/Rge/Sec from the
         corresponding description block (i.e. what comes between
         ``.trs`` and ``.desc``).  (Defaults to ``': '``).

        :param newline: Specify what separates each ``Tract`` from one
         another.  (Defaults to ``'\n'``).

        :return: A string of the complete description.
        """
        dlist = [t.quick_desc(delim=delim) for t in self]
        return newline.join(dlist)

    def quick_desc_short(self, delim=': ', newline='\n', max_len=30) -> str:
        # Note r-string, to escape '\n' character.
        r"""
        Returns the full description of all ``Tract`` objects as a
        single, orderly string -- but caps every line at a length of
        ``max_len``.

        :param delim: Specify what separates Twp/Rge/Sec from the
         corresponding description block (i.e. what comes between
         ``.trs`` and ``.desc``).  (Defaults to ``': '``).

        :param newline: Specify what separates each ``Tract`` from one
         another.  (Defaults to ``'\n'``).

        :param max_len: Maximum length of each line. (Defaults to 30.)

        :return: A string of the complete description (with each line
         potentially trimmed).
        """
        return newline.join(self.snapshot_inside(delim, max_len))

    def snapshot_inside(self, delim=': ', max_len=30) -> list:
        r"""
        Get a list of the full description of each ``Tract`` object as a
        single, orderly string -- but caps every line at a length of
        ``max_len``.

        :param delim: Specify what separates Twp/Rge/Sec from the
         corresponding description block (i.e. what comes between
         ``.trs`` and ``.desc``).  (Defaults to ``': '``).

        :param max_len: Maximum length of each line. (Defaults to 30.)

        :return: A list of strings, each no longer than ``max_len``.
        """
        return [t.quick_desc_short(delim, max_len) for t in self]

    def print_desc(self, delim=': ', newline='\n') -> None:
        # Note r-string, to escape '\n' character.
        r"""
        Simple printing of the parsed description.

        :param delim: Specify what separates Twp/Rge/Sec from the
         corresponding description block (i.e. what comes between
         ``.trs`` and ``.desc``).  (Defaults to ``': '``).

        :param newline: Specify what separates each ``Tract`` from one
         another.  (Defaults to ``'\n'``).
        """
        print(self.quick_desc(delim=delim, newline=newline))

    def pretty_desc(self, word_sec="Sec ", justify_linebreaks=None):
        # Note r-string, to escape '\t' character.
        r"""
        Get a neatened-up description of all ``Tract`` objects in this
        ``TractList``.

        Groups Tracts by Twp/Rge, but only to the extent possible while
        maintaining the current sort order.

        :param word_sec: How the word 'Section' should appear, INCLUDING
         the following white space (if any). (Defaults to ``'Sec '``).

        :param justify_linebreaks: (Optional) A string specifying how to
         justify new lines after a linebreak -- e.g., ``'\t'`` (a tab).
         If not specified, will align new lines with the line above
         (i.e. as determined by ``word_sec``). To use no justification
         at all, pass an empty string.

         *Note:* Only linebreaks *within* a given ``Tract`` will be
         justified -- i.e. the start of each ``Tract`` will be
         left-aligned.

        :return: a str of the compiled description.
        """
        jst = " " * (len(word_sec) + 4)
        if justify_linebreaks is not None:
            jst = justify_linebreaks
        if not self:
            return None
        to_print = []
        cur_twprge = self[0].twprge
        cur_group = []
        for t in self:
            if t.twprge == cur_twprge:
                cur_group.append(t)
            else:
                to_print.append((cur_twprge, cur_group))
                cur_twprge = t.twprge
                cur_group = [t]
        # Append the final group.
        to_print.append((cur_twprge, cur_group))
        dsc = ""
        for twprge, group in to_print:
            dsc = f"{dsc}\n{TRS(twprge).pretty_twprge()}"
            for tract in group:
                dsc = f"{dsc}\n{word_sec}{tract.sec}: "
                tdesc = tract.desc.replace("\n", f"\n{jst}")
                dsc = f"{dsc}{tdesc}"
        return dsc.strip()

    def pretty_print_desc(self, word_sec="Sec ", justify_linebreaks=None):
        # Note r-string, to escape '\t' character.
        r"""
        Print a neatened-up description of all ``Tract`` objects in this
        ``TractList``.

        Groups Tracts by Twp/Rge, but only to the extent possible while
        maintaining the current sort order.

        :param word_sec: How the word 'Section' should appear, INCLUDING
         the following white space (if any). (Defaults to ``'Sec '``).

        :param justify_linebreaks: (Optional) A string specifying how to
         justify new lines after a linebreak -- e.g., ``'\t'`` (a tab).
         If not specified, will align new lines with the line above
         (i.e. as determined by ``word_sec``). To use no justification
         at all, pass an empty string.

         *Note:* Only linebreaks *within* a given ``Tract`` will be
         justified -- i.e. the start of each ``Tract`` will be
         left-aligned.

        :return: None (prints to console).
        """
        print(self.pretty_desc(word_sec, justify_linebreaks))

    def print_data(self, *attributes) -> None:
        """
        Simple printing of the arg-specified attributes for each
        ``Tract`` in this ``TractList``.
        """
        print(self.tracts_to_str(attributes))
        return

    def list_trs(self, remove_duplicates=False):
        """
        Get a list all Twp/Rge/Sections in all ``Tract`` objects.
        Optionally remove duplicates from the returned list with
        ``remove_duplicates=True``. (Duplicates are NOT removed from the
        original.)

        The original order is maintained in the returned list.

        *Note:* Each Twp/Rge/Sec in the resulting list is a string, and
        *not* a ``TRS`` object. If ``TRS`` objects are required, cast
        the resulting list as a ``TRSList``:

        .. code-block:: python

            TRSList(some_tractlist.list_trs())

        :param remove_duplicates: Whether to remove duplicate
         Twp/Rge/Sec from the resulting list. (They are not removed in
         the original.)  Defaults to ``False``.
        """
        unique_trs = []
        all_trs = []
        for trs in [t.trs for t in self]:
            all_trs.append(trs)
            if trs not in unique_trs:
                unique_trs.append(trs)
        if remove_duplicates:
            return unique_trs
        return all_trs

    @classmethod
    def from_multiple(cls, *objects):
        """
        Create a ``TractList`` from multiple sources, which may be any
        number and combination of ``Tract``, ``PLSSDesc``, and
        ``TractList`` objects (or other iterable holding any of those
        object types).

        :param objects: Any number or combination of ``Tract``,
         ``PLSSDesc``, and/or ``TractList`` objects (or other iterable
         holding any of those object types).

        :return: A new ``TractList`` object containing the extracted
         ``Tract`` objects.
        """
        # This is (re-)defined from the superclass only in order to have
        # an accurate docstring (and to simplify the signature).
        return cls._from_multiple(objects)


class TRSList(_TRSTractList):
    """
    An emulation of the builtin ``list``, specialized for ``TRS``
    objects, with added methods for sorting, grouping, and filtering the
    ``TRS`` objects.

    *Note:* ``TRSList`` and ``TractList`` are subclassed from the same
    superclass and have some of the same functionality for sorting,
    grouping, and filtering.  In the docstrings for many of the methods,
    there will be references to either ``TRS`` or ``Tract`` objects, and
    to ``TRSList`` or ``TractList`` objects.  To be clear, ``TRSList``
    objects hold only ``TRS`` objects, and ``TractList`` objects hold
    only ``Tract`` objects.

    ADDING TWP/RGE/SEC's TO THE TRSLIST
    -----------------------------------
    A ``TRSList`` will hold only ``TRS`` objects. However, if you try to
    add a string to it, it will first be converted to a ``TRS`` object.
    Similarly, if you try to add a ``Tract`` object, its ``.trs``
    attribute will be extracted and converted to a ``TRS`` object, which
    then gets added to the list (the original ``Tract`` itself is not).

    ``TRSList`` can also be created from a ``PLSSDesc``, ``TractList``,
    or other iterable containing ``Tract`` objects (the ``.trs``
    attribute for each ``Tract`` will be extracted and converted to a
    ``TRS`` object then added to the resulting ``TRSList``).

    These are all acceptable:

    .. code-block:: python

        trs_list1 = pytrs.TRSList(['154n97w14', '154n97w15'])
        trs_list2 = pytrs.TRSList([pytrs.TRS('154n97w14')])
        trs_list3 = pytrs.TRSList([tract_object_1, tract_object_2])
        trs_list4 = pytrs.TRSList(plssdesc_obj)

    (Note that the ``PLSSDesc`` object is passed directly, rather than
    inside a list, because ``PLSSDesc`` are iterable.)

    To robustly create a list of ``TRS`` objects from multiple objects
    of different types, look into ``TRS.from_multiple()``:

    .. code-block:: python

        trs_list5 = pytrs.TRSList.from_multiple(
            '154n97w14',
            pytrs.TRS('154n97w15'),
            tract_object_1,
            some_tract_list,
            some_other_trs_list)


    STREAMLINED OUTPUT OF THE TWP/RGE/SEC DATA
    ------------------------------------------
    - ``.to_strings()``
        - Return a plain list of all ``TRS`` objects, converted to
          strings.


    SORTING / GROUPING / FILTERING ``TRS`` BY ATTRIBUTE VALUES
    ----------------------------------------------------------
    - ``.sort_trs()``
        - Custom sorting based on the Twp/Rge/Sec. Can also take
          parameters from the built-in ``list.sort()`` method.

    - ``.group_by()``
        - Group ``TRS`` objects into a dict of ``TRSList`` objects,
          based on their shared attribute values (e.g., by Twp/Rge),
          and optionally sort them.

    - ``.filter()``
        - Get a new ``TRSList`` of ``TRS`` objects that match some
          condition, and optionally remove them from the original
          ``TRSList``.

    - ``.filter_errors()``
        - Get a new ``TRSList`` of ``TRS`` objects whose Twp, Rge, and/or
          Section were an error or undefined, and optionally remove them
          from the original ``TRSList``.
    """

    # A TRSList holds only TRS objects. But these types can be processed
    # into individual TRS objects, which are then added.
    _ok_individuals = (str, TRS, Tract)
    _ok_iterables = (TractList,)
    _typeerror_msg = (
        "TRSList will accept only types ('str', 'TRS', 'Tract')."
    )

    def __init__(self, iterable=()):
        """
        Create new ``TRSList``, containing the elements in ``iterable``.

        :param iterable: An iterable (or ``PLSSDesc``) containing any of
         the following:
        - `TRS` objects
        - strings (which will be converted to `TRS` objects)
        - `Tract` objects (from which the `TRS` will be extracted and
          added to the list)
        """
        _TRSTractList.__init__(self, iterable)

    @classmethod
    def _handle_type_specially(cls, obj):
        """
        INTERNAL USE:

        - Pass `TRS` objects through.
        - Convert encountered strings to ``TRS`` objects.
        - Extract from encountered ``Tract`` objects the ``.trs``
          attribute and convert it to `TRS` object.
        """
        if isinstance(obj, TRS):
            return obj
        if isinstance(obj, str):
            return TRS(obj)
        if isinstance(obj, Tract):
            return TRS(obj.trs)
        raise TypeError(f"{cls._typeerror_msg} Cannot accept {type(obj)}")

    def __str__(self):
        return str([elem.trs for elem in self])

    def __repr__(self):
        return f"TRSList({len(self)})<{str(self)}>"

    def to_strings(self):
        """
        Get the Twp/Rge/Sec as a string from each element in this list.

        :return: A new (plain) list containing the Twp/Rge/Sec's as
         strings.
        """
        return [trs_obj.trs for trs_obj in self]

    def contains(self, trs, match_all=False) -> bool:
        """
        Check whether this ``TRSList`` contains one or more specific
        Twp/Rge/Sec.  By default, a match of *any* Twp/Rge/Sec will
        return ``True``. But to look for matches of *all* Twp/Rge/Sec,
        use ``match_all=True``. (Duplicates are ignored.)

        :param trs: The Twp/Rge/Section(s) to look for in this TRSList.
         May pass as a ``TRS`` object, a string in the standard pyTRS
         format, or a ``TRSList``.  May also pass a ``Tract``, a parsed
         ``PLSSDesc`` object, or a ``TractList`` -- or an iterable
         container holding any combination of those types.

         *Note:* If a ``Tract``, ``PLSSDesc``, or ``TractList``
         is encountered, the ``.trs`` attribute in each ``Tract`` will
         be added instead.

        :param match_all: If we need to check whether *all* of the
         Twp/Rge/Sections are contained in this ``TRSList`` (ignoring
         duplicates).  Defaults to ``False`` (i.e. a match of *any*
         Twp/Rge/Sec will be interpreted as ``True``).

        :return: A bool, whether or not any of the Twp/Rge/Sec in
         ``trs`` are found in this `TRSList`.
        """
        # Convert `trs` to a TRS object (or if `trs` is an iterable,
        # convert all elements within it to `TRS` objects) and add to a
        # TRSList. Convert the resulting TRSList to a set.
        look_for = set(TRSList.from_multiple(trs).to_strings())
        contained = set(self.to_strings())
        if match_all:
            return len(look_for - contained) == 0
        return len(contained.intersection(look_for)) > 0

    @classmethod
    def from_multiple(cls, *objects):
        """
        Create a ``TRSList`` from multiple sources.

        :param objects: May pass any number or combination of ``TRS``
         objects or strings in the pyTRS standardized Twp/Rge/Sec
         format, or ``TRSList`` objects, or other list-like objects
         containing those object types.  (Any strings will be
         interpreted as Twp/Rge/Sec and converted to ``TRS`` objects.)

        :return: A ``TRSList`` containing the ``TRS`` objects.
        """
        # This is (re-)defined from the superclass only in order to have
        # an accurate docstring (and to simplify the signature).
        return cls._from_multiple(objects)


def group_tracts_by(
        to_group,
        attribute="twprge",
        into: dict = None,
        sort_key=None,
        sort_reverse=None):
    """
    (See documentation on ``TractList.group_by()`` method.)

    Instead of a method on a ``TractList`` object, this function takes
    an additional first positional argument ``to_group``, being an
    iterable container of ``Tract`` objects, ``PLSSDesc`` objects,
    and/or ``TractList`` objects.

    :return: A dict of ``TractList`` objects each containing those
     tracts with matching values of the ``attribute``. If ``attribute``
     was passed as a *list* of attribute names, then the keys in the
     returned dict will be a tuple whose values line up with the list
     passed as ``attribute``.)
    """
    tl = TractList.from_multiple(to_group)
    return tl.group(attribute, into, sort_key, sort_reverse)


def sort_grouped_tracts(group_dict, sort_key, reverse=False) -> dict:
    """
    (See documentation on ``TractList.sort_grouped_tracts()`` method.)

    :return: The original ``group_dict``, with the ``TractList``
     objects having been sorted.
    """
    return TractList.sort_grouped_tracts(group_dict, sort_key, reverse)


__all__ = [
    'TractList',
    'TRSList',
    'group_tracts_by',
    'sort_grouped_tracts',
]
