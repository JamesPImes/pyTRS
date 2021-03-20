# Copyright (c) 2021, James P. Imes

import csv
from pathlib import Path
from pytrs import Tract, TractList


class TractWriter:
    """
    A wrapper for csv.writer for streamlined output of Tract data.
    """
    def __init__(
            self, attributes, fp, mode="w", plus_cols=None, nice_headers=False):
        """
        A wrapper for csv.writer for streamlined output of Tract data.
        Ensures that the same attributes are written for every Tract
        processed.

        :param attributes: The Tract attributes to write for each Tract.
        :param fp: Filepath to the .csv file to write to.
        :param mode: Whether to open the file in mode 'w' or 'a'.
        Defaults to 'w'. (But if a file is closed with ``.close()`` and
        later reopened with ``.open()``, it will be reopened in 'a'
        mode.)
        :param plus_cols:  (Optional) a list of additional headers to
        write that are not covered by the Tract attributes. (If using
        this functionality, a list of the specific data to write in
        these columns will need to be included every time something is
        written.)
        :param nice_headers: a bool, whether to use the values in the
        ``Tract.ATTRIBUTES`` dict for headers. Defaults to ``False``
        (i.e. just use the attribute names themselves).
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
        header_row = self.attributes.copy()
        if self.plus_cols:
            header_row.extend(self.plus_cols)
        if self.nice_headers:
            header_row = [
                Tract.ATTRIBUTES.get(att, att) for att in header_row
            ]
        self.writer.writerow(header_row)
        return None

    def write(self, tracts, plus_cols=None):
        """
        Write the data from the ``tracts``.
        :param tracts: a Tract, a PLSSDesc object, a TractList, or an
        iterable of any combination of those object types.
        :param plus_cols: (Optional) a list of additional data to write
        for each of the written rows. (Will write the same data for
        every row written.)
        :return: The number of rows written (an int).
        """
        if not self.is_open:
            raise RuntimeError("writer is not open. Call `.open()` first.")
        tl = TractList.from_multiple(tracts)
        written = 0
        for tract in tl:
            row = tract.to_list(self.attributes)
            if plus_cols:
                row.extend(plus_cols)
            row = TractWriter.scrub_row(row)
            self.writer.writerow(row)
            written += 1
        return written

    @staticmethod
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


__all__ = [
    TractWriter
]