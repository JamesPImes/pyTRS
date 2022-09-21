# Copyright (c) 2021-2022, James P. Imes. All rights reserved.

import csv
from pathlib import Path

from ..parser import Tract, TractList
from ..utils import gen_uid


class TractWriter:
    """
    A wrapper for builtin ``csv.writer`` for streamlined output of
    ``Tract`` data. Ensures that the same attributes are written for
    every ``Tract``.
    """
    def __init__(
            self, attributes, fp, mode, plus_cols=None, nice_headers=False,
            uid: int = None):
        """
        A wrapper for ``csv.writer`` for streamlined output of ``Tract``
        data.

        :param attributes: The ``Tract`` attributes to write for each
        ``Tract``. (See documentation for ``Tract`` class for all
        important attributes.)

        :param fp: Filepath to the .csv file to write to.

        :param mode: Whether to open the file in mode ``'w'`` or
         ``'a'``. Defaults to ``'w'``. (But if a file is closed with
         ``.close()`` and later reopened with ``.open()``, it will be
         reopened in ``'a'`` mode.)

        :param plus_cols:  (Optional) a list of additional headers to
         write that are not covered by the ``Tract`` attributes. (If
         using this functionality, a list of the specific data to write
         in these columns will need to be included every time something
         is written.)

        :param nice_headers: By default, this class will use the
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

        :param plus_cols: (Optional) a list of additional headers to
         write that are not covered by the ``Tract`` attributes.

        :param uid: (Optional) The number at which to start generating
         unique identifiers. If specified, UID's will be written for
         every new row (e.g., ``'0001.a-e'``). The number component of
         the UID will be incremented every time ``.write()`` is called,
         and the letter components will encode how many rows were added
         that time (``a: 1, b: 2, c: 3, <...>, aa: 27, ab: 28, etc.``).

         For example (assuming our UID is currently at 27, and
         ``parsed_desc`` is a ``PLSSDesc`` object containing 4 ``Tract``
         objects):

             .. code-block:: python

                 some_tractwriter.write(parsed_desc)
                 # Wrote 4 rows and generated these UIDs (one for
                 # each row)...
                 # '0027.a-d',  '0027.b-d',  '0027.c-d',  and '0027.d-d'
        """
        self.attributes = attributes
        self.fp = Path(fp)
        self.file = None
        self.mode = mode
        self.writer = None
        self.nice_headers = nice_headers
        self.plus_cols = plus_cols
        write_headers = True
        if self.fp.exists() and mode == "a":
            write_headers = False
        self.open()
        self.gen_uids = uid is not None
        if not self.gen_uids:
            uid = 0
        self.uid = uid
        self.uid_just = 4
        if write_headers:
            self.write_headers()

    @property
    def is_open(self) -> bool:
        """Check if the file is open."""
        return self.file is not None

    def open(self):
        """Open the file."""
        self.file = open(self.fp, mode=self.mode, newline="")
        self.writer = csv.writer(self.file)

        # If we reopen this later, we'd want to open it in mode 'a'.
        self.mode = "a"
        return None

    def close(self):
        """Close the file."""
        self.file.close()
        self.file = None
        self.writer = None
        return None

    def write_headers(self):
        """
        Write headers.
        :return: None
        """
        header_row = Tract.get_headers(
            self.attributes, self.nice_headers, self.plus_cols)
        if self.gen_uids:
            header_row.append('UID')
        self.writer.writerow(header_row)
        return None

    def write(self, to_write, plus_cols=None):
        """
        Write the data from ``to_write`` to the csv.
        :param to_write: a ``Tract``, a ``PLSSDesc`` object, a
         ``TractList``, or an iterable containing any number and
         combination of those object types.
        :param plus_cols: (Optional) a list of additional data to write
         for each of the written rows. (Will write the same data for
         every row written.)
        :return: The number of rows written (an int).
        """
        if not self.is_open:
            raise RuntimeError("writer is not open. Call `.open()` first.")
        if to_write is None:
            self.uid += 1
            return 0
        # If we're generating UID's, we need to know how many we'll
        # write in total, so get a TractList.
        tl = TractList.from_multiple(to_write)
        total_to_write = len(tl)
        written = 0
        for tract in tl:
            row = tract.to_list(self.attributes)
            if plus_cols:
                row.extend(plus_cols)
            if self.gen_uids:
                uid = gen_uid(
                    self.uid, written + 1, total_to_write, just=self.uid_just)
                row.append(uid)
            row = TractWriter._scrub_row(row)
            self.writer.writerow(row)
            written += 1
        self.uid += 1
        return written

    @staticmethod
    def _scrub_row(data):
        """
        INTERNAL USE:
        Convert lists/dicts in a row to strings.
        """
        scrubbed = []
        for elem in data:
            if isinstance(elem, dict):
                elem = ','.join([f"{k}:{v}" for k, v in elem.items()])
            elif isinstance(elem, (list, tuple)):
                elem = ', '.join(elem)
            scrubbed.append(elem)
        return scrubbed


__all__ = [
    TractWriter
]
