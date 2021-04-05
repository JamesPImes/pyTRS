# Copyright (c) 2021, James P. Imes. All rights reserved.

"""
A sample script using pyTRS to inventory reports by Twp/Rge/Sec based on
their filenames.  See 'file_inventory.csv' for the sample output.

(Demonstrates pytrs.PLSSDesc and pytrs.tractwriter.TractWriter classes.)

NOTE: For the sample output, the report directory contained these files:
-- skip this file.txt
-- T153N-R97W Sec 1 N2, T154N-R97W Sec 36 S2 report 2-3-2016.docx
-- T154N-R97W Sec 14 NE, Sec 15 - 18 N2 report 12-1-2014.docx
-- T154N-R97W Sec 16 SE report 1-9-2016.docx
"""

import os
import re
from pathlib import Path
import pytrs
from pytrs.tractwriter import TractWriter

# Directory containing reports, with filenames in the format:
#   '<legal description in TRS_desc layout> Report <MM-DD-YYYY>.docx'
#   e.g., 'T154N-R97W Sec 14 NE, Sec 15 - 18 N2 Report 12-1-2014.doc'
REPORT_DIRECTORY = Path(r".\Reports")

# Regex pattern of the portion of the filename that needs to be removed.
REPORT_SURPLUS = re.compile(
    r"\s*report\s(?P<date>\d{1,2}-\d{1,2}-\d{4})", re.IGNORECASE)

# Possible file extensions that were used for reports.
DOC_TYPES = (".docx", ".doc")

# Filepath at which to write our inventory.
INVENTORY_FP = Path(r"file_inventory.csv")


def main():
    files = os.listdir(REPORT_DIRECTORY)

    # We want this data from the land descriptions.
    attributes_to_write = ['trs', 'twprge', 'sec', 'desc', 'source']

    # And we want their headers to look like this.
    custom_headers = {
        'trs': 'Twp/Rge/Sec',
        'twprge': 'Twp/Rge',
        'sec': 'Sec',
        'desc': 'Specific Lands Covered',
        'source': 'Filepath'
    }

    # Get a TractWriter for writing our Tract data to .csv file.
    # We'll use the 'source' attribute to tell us which file provided
    # each tract.
    # We'll also include the report date -- which is not a pytrs.Tract
    # attribute, so we'll have to manually add it with `plus_cols=[]`.
    writer = TractWriter(
        attributes=attributes_to_write,
        fp=INVENTORY_FP,
        mode='w',
        nice_headers=custom_headers,
        plus_cols=['Report Date']
    )

    # We know our filenames are in the TRS_desc layout, and that they
    # will not contain colons.
    config = 'TRS_desc,require_colon.False'

    files_inventoried = 0

    for file in files:
        fp = Path(file)

        # Print to console to show current status.
        print(f"Checking {fp}")

        if fp.suffix.lower() not in DOC_TYPES:
            # Skip any file or directory that is not a report filetype.
            print("Not a report.")
            continue

        # Get the filename stem (without the file extension).
        fn = fp.stem

        # Get the report date from the filename using our regex pattern.
        report_date = None
        date_mo = REPORT_SURPLUS.search(fn)
        if date_mo:
            report_date = date_mo.group("date")

        # Remove the surplus from the filename, after which `cleaned_fn`
        # should be a simple PLSS land description that we can parse.
        cleaned_fn = re.sub(REPORT_SURPLUS, "", fn)

        # Parse the PLSS description, and specify that the source of it
        # is the original filepath `fp`.
        parsed = pytrs.PLSSDesc(cleaned_fn, config=config, source=fp)

        # Write the Tract contents to the csv file (manually including
        # the report date with `plus_cols=`).
        writer.write(parsed, plus_cols=[report_date])

        files_inventoried += 1

    # TractWriter object must be manually closed.
    writer.close()

    print(f"Done. {files_inventoried} files inventoried in {INVENTORY_FP}.")
    input()


if __name__ == '__main__':
    main()
