# Copyright (c) 2020, James P. Imes, all rights reserved.

"""
A program to parse PLSS descriptions in a .csv file, and write the
parsed results at the end of each row, inserting rows as necessary such
that there is one Tract per row; saves to a new .csv file.
Built on the pyTRS library.
"""


def parse_csv(
        in_file: str, desc_col: int, first_row=1, last_row=-1, header_row=-1,
        attribs=None, out_file=None, config_col=None, config=None,
        layout_col=None, resume=False, write_headers=True, unpack=False,
        copy_data=False, tract_level=False, include_uid=False,
        include_unparsed=True, num_tracts=False):
    """
    Parse the PLSS descriptions in a .csv file, and write the results
    in new columns at the end, inserting rows as necessary for one
    parsed Tract per row; save to new .csv file.
    NOTE: Columns/Rows are indexed to 1 (not 0).

    :param in_file: Filepath to the .csv to read from.
    :param desc_col: Integer, specifying which column to read from for
    the PLSS descriptions to parse. (Indexed from 1, rather than 0.)
    :param first_row: An integer, specifying the row containing the
    first description to parse. (Indexed from 1, rather than 0.)
    :param last_row: An integer, specifying the row after which to stop
    parsing. If not specified, will parse all rows. (Indexed from 1,
    rather than 0.)
    :param header_row: An integer specifying the row in the input file
    containing headers, if any. (Indexed from 1, rather than 0.)
    :param attribs: Which pyTRS.Tract attributes (instance variables) to
    write to the csv. Pass as a list of strings, or as a single string
    with attribute names separated by comma.
    For 'tract-level' parsing (i.e. only parsing tracts into Lots/QQ's)
    :param out_file: Filepath to the .csv to write to.
    :param config_col: Column in the .csv file containing the pyTRS
    config parameters to use for parsing that row.
    :param config: Standard pyTRS config parameters to be used for every
    description, entered as a string with parameters separated by comma,
    or as a pyTRS.Config object.
    NOTE: In the event of conflict between parameters in config and in
    config_col, config_col will control.
    :param layout_col: (Optional) Column in the .csv file containing the
    pyTRS layout name to use for that row. (If not specified, will use
    `config` parameters; and if not specified there, will deduce it when
    parsed.)
    :param resume: Whether to overwrite (i.e. `resume=False`) an
    existing file if found at the filepath specified at `out_file`, or
    to continue writing at the end of it (`resume=True`). Defaults to
    True.
    NOTE: If no existing file is found, this will create a new file
    regardless of `resume`.
    NOTE ALSO: If resuming a previous output, but with different
    attributes (or differently ordered) than before, the columns will be
    misaligned.
    :param write_headers: Whether to write headers. Defaults to True.
    :param unpack: Whether to try to flatten and join lists, or
    simply write them as they appear. (Defaults to `False`)
    :param copy_data: Copy the the unparsed data for every new row (i.e.
    whether to copy the data OTHER than the parsed descriptions, or to
    just leave it in the original row). Defaults to False.
    :param tract_level: If the .csv already has lands broken into one
    Twp/Rge/Sec combo (TRS) per row, specify `tract_level=True` to parse
    the text into lots and QQs only. Defaults to False.
    :param include_uid: Include a unique identifier number for each row
    in the format '0000-a.g' (where the digits refer to the row in the
    original .csv, and the letters refer to how many rows were written
    by the csv parser). Defaults to False.
    :param include_unparsed: Copy rows that were not parsed.
    :param num_tracts: INTERNAL USE. Write a separate .csv file with
    each row containing the number of how many rows were written for the
    corresponding row in the main .csv. (Probably don't use it.)
    :return: Returns 0 on success.
    """

    from pyTRS.parser import PLSSDesc, Tract
    import os, csv
    from pyTRS.utils import flatten, alpha_to_num, num_to_alpha

    if out_file is None:
        from datetime import datetime
        t = datetime.now()
        timestamp = (
            f"{t.year}{str(t.month).rjust(2, '0')}{str(t.day).rjust(2, '0')}"
            f"_{str(t.hour).rjust(2, '0')}{str(t.minute).rjust(2, '0')}"
            f"{str(t.second).rjust(2, '0')}"
        )
        out_file = f"{in_file[:-4]}_pyTRS_parsed_{timestamp}.csv"

    # Ensure input and output filepaths lead to .csv files.
    if not (in_file.lower().endswith('.csv') and out_file.lower().endswith('.csv')):
        raise ValueError("Error: input and output filepath must end in '.csv'")

    if desc_col < 1:
        raise ValueError(
            f"Error: Integer for column must be equal to or greater than 1. "
            f"~~desc_col={desc_col}")

    if header_row is not None:
        if not first_row > header_row:
            raise ValueError(
                f"Error: first_row must be greater than header_row. "
                f"~~first_row={first_row}, header_row={header_row}")

    if attribs in [None, '']:
        # If not specified, set default attribs, which are different for
        # `tract_level` than otherwise.
        attribs = 'trs,desc'
        if tract_level:
            attribs = 'pp_desc,lots,qqs'

    if isinstance(attribs, str):
        # Split attribute string into list of Tract attribute names:
        attribs = attribs.replace(' ', '').split(',')

    read_file = open(in_file)
    reader = csv.reader(read_file)

    # If the file already exists and we're not writing a new file, turn
    # off headers
    if os.path.isfile(out_file) and resume:
        write_headers = False

    # Default to opening in `write` mode (create new file). However...
    openMode = 'w'
    if resume:
        # If we don't want to create a new file, will open in `append`
        # mode instead.
        openMode = 'a'

    write_file = open(out_file, openMode, newline='')
    writer = csv.writer(write_file)

    # If a .csv of number of rows has been requested, create and open
    # that .csv file, using the same openMode as for `writer`
    if num_tracts:
        num_out_file = f"{out_file[:-4]}_numTracts.csv"
        num_write_file = open(num_out_file, openMode, newline='')
        num_writer = csv.writer(num_write_file)
        if not resume and write_headers:
            num_writer.writerow(['Rows_written_in_output'])

    # Whether we should stop after a certain number of rows
    end_early = False
    if last_row > 0:
        end_early = True

    print(f"Parsing descriptions in '{in_file}'...")
    # Which row we're on (vis-a-vis the original .csv):
    cur_row = 0
    # Number of rows encountered /after/ the header (identical to
    # cur_row if no header in original). For UID:
    parse_num = 0
    for row in reader:
        cur_row += 1

        if write_headers:
            if cur_row == header_row:
                writer.writerow(row + ['parse_UID'] * include_uid + attribs)
                write_headers = False
                continue
            elif cur_row == first_row and (header_row is None or header_row < 1):
                # In this scenario, write headers just above first-parsed row
                writer.writerow(
                    ['' for _ in row] + ['parse_UID'] * include_uid + attribs)
                write_headers = False
                # Do not continue yet, because we still need to parse
                # and write results.

        if include_unparsed \
                and ((cur_row < first_row) or (cur_row > last_row and end_early)):
            writer.writerow(row)
            continue

        elif cur_row < first_row:
            continue

        elif cur_row > last_row and end_early:
            break

        parse_num += 1

        # Note: config_col, layout_col, and desc_col are 1-indexed, but
        # are used to access elements in 0-indexed list, so we subtract
        # 1 from each here:

        # Get `config` parameters either from the .csv, or from the
        # kwarg `config` (preference given to config_col)
        try:
            config = row[config_col-1]
        except:
            pass
        if config is None:
            config = ''

        # If user has specified a column for layout, add that layout to
        # the end of the `config` string.
        try:
            config = f"{config},{row[layout_col-1]}"
        except:
            pass

        # Get text of description from row.
        try:
            desc_text = row[desc_col-1]
        except IndexError:
            print(
                f"Warning: Could not access PLSS description at row {cur_row}, "
                f"column {desc_col}.")
            desc_text = ''

        # Parse the description.
        if tract_level:
            # If we're parsing lots/QQ's in an already-parsed Tract (or
            # equivalent), do it, and pack the attributes into a nested list:
            t = Tract(desc=desc_text, trs='', config=config, init_parse_qq=True)
            all_Tract_data = [t.to_list(attribs)]
        else:
            # Otherwise, parsing a full PLSS description, and the
            # `.tracts_to_list()` method outputs an already-nested list:
            d = PLSSDesc(desc_text, config=config, init_parse_qq=True)
            all_Tract_data = d.tracts_to_list(attribs)

        # We will write a row for each Tract object, but if none were found,
        # we want to write a minimum of 1 row.
        num_rows_to_write = len(all_Tract_data)
        if num_rows_to_write == 0:
            num_rows_to_write = 1

        for i in range(num_rows_to_write):
            if i == 0 or copy_data:
                # Copy the original row data
                to_write = row.copy()
            else:
                # Blank data for inserted rows, if `copy_data` was not requested
                to_write = ['' for _ in row]

            if include_uid:
                # Generate UID in the format '0032.a-j':
                uid = (
                    f"{str(parse_num).rjust(4, '0')}"
                    f".{num_to_alpha(i + 1).lower()}"
                    f"-{num_to_alpha(num_rows_to_write).lower()}"
                )
                to_write.append(uid)

            try:
                # Add the parsed Tract Data
                for val in all_Tract_data[i]:
                    if isinstance(val, (list, tuple)) and unpack:
                        # If requested, `unpack` and join lists/tuples
                        # before writing:
                        to_write.append(', '.join(flatten(val)))
                    else:
                        to_write.append(val)
            except:
                # If no data for this Tract (e.g., no tracts identified
                # in the PLSSDesc object), fill with dummy data.
                to_write.extend([f"{attrib}: n/a" for attrib in attribs])

            writer.writerow(to_write)

        # Write number of tracts to separate csv if requested with
        # `num_tracts=True`:
        if num_tracts:
            num_writer.writerow([num_rows_to_write])

    print(
        f"Done. Results written to '{out_file}'. "
        f"Be sure to examine results for fidelity."
    )
    return 0
