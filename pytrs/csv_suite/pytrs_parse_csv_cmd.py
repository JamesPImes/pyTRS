# Copyright (c) 2020, James P. Imes, all rights reserved.

"""
A command-line interface for the the `parse_csv()` function, to parse
PLSS descriptions or tracts in a .csv file.
"""

# To use, specify the input .csv file (with arg `-i` or `--input_csv`),
# and which column contains the PLSS descriptions to be parsed (indexed
# from 1), and various optional args.
# If the output filepath is not specified, it will default to
# '<input filepath>_pytrs_parsed_<timestamp>.csv'.

# Usage: py pytrs_parse_csv_cmd.py -i 'read_from.csv' -o 'write_to.csv'
#           --desc_column 5 --config n,w,segment

# 'pytrs_parse_csv_cmd.py --help' at command line for all possible args.

import argparse
from pytrs.csv_suite.pytrs_parse_csv import parse_csv


if __name__ == '__main__':
    # Define command-line args.
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-i', '--input_csv', type=str, help='path to input .csv file', required=True)
    parser.add_argument('-o', '--output_csv', type=str, help='path to new output .csv file')
    parser.add_argument(
        '-dc', '--desc_column', type=int,
        help='The number of the column (indexed from 1) containing PLSS descriptions',
        required=True)
    parser.add_argument(
        '-a', '--attribs', type=str,
        help="Tract attributes that should be included in output "
             "(separate by comma: `-a trs,desc`)")
    parser.add_argument(
        '-fr', '--first_row', type=int, default=1,
        help="Which row to start at (indexed from 1)")

    # A negative `last_row` means parse all rows will be parsed:
    parser.add_argument(
        '-lr', '--last_row', type=int, default=-1,
        help="Which row to stop after (indexed from 1)")

    # A negative `header_row` means there are no headers in the input (or that headers
    # won't be handled as such):
    parser.add_argument(
        '-hr', '--header_row', type=int, default=-1,
        help="Which row contains headers (indexed from 1)")

    parser.add_argument(
        '-lc', '--layout_column', type=int,
        help="The number of the column (indexed from 1) containing the layout for each "
             "description (requires the user to prep input .csv to specify the layout for "
             "each row)")
    parser.add_argument(
        '-cc', '--config_column', type=int,
        help="The number of the column (indexed from 1) containing the config parameters for "
             "each description (requires the user to prep input .csv to specify config "
             "parameters for each row)")
    parser.add_argument(
        '-cf', '--config', type=str, help="config parameters to use for all rows")
    parser.add_argument(
        '-cd', '--copy_data', action='store_true',
        help="Copy existing data to any newly inserted rows")
    parser.add_argument(
        '-to', '--tracts_only', action='store_true',
        help="Tracts have already been separated from TRS in input .csv; now only parsing "
             "lots and QQ's")

    parser.add_argument(
        '-sh', '--suppress_headers', action='store_true',
        help="Do NOT write headers in the output .csv file")
    parser.add_argument(
        '-r', '--resume', action='store_true',
        help="Resume writing to an existing output .csv file")
    parser.add_argument(
        '-u', '--unpack', action='store_true',
        help="unpack any Tract data stored as a list when writing to output .csv file")
    parser.add_argument(
        '-uid', '--include_uid', action='store_true',
        help="Generate unique identifier number (UID) for each description parsed")
    parser.add_argument(
        '-iu', '--include_unparsed', action='store_true',
        help="Also write the unparsed rows (i.e. copy them) to the output .csv file")
    parser.add_argument(
        '-nt', '--number_tracts', action='store_true',
        help="Generate a separate .csv file that states how many rows were written for "
             "each description")
    parser.add_argument(
        '-launch', '--launch', action='store_true',
        help="Launch the output .csv file after writing")

    # Get raw args from command line into variables.
    args = vars(parser.parse_args())

    # `parse_csv()` is capable of creating a default output filepath. It has also been
    # implemented here to allow us to optionally launch the file after parsed.
    out_filepath = args['output_csv']

    if out_filepath is None:
        from datetime import datetime

        t = datetime.now()
        timestamp = f"{t.year}{str(t.month).rjust(2, '0')}{str(t.day).rjust(2, '0')}_" \
                    f"{str(t.hour).rjust(2, '0')}{str(t.minute).rjust(2, '0')}" \
                    f"{str(t.second).rjust(2, '0')}"
        out_filepath = f"{args['input_csv'][:-4]}_pytrs_parsed_{timestamp}.csv"

    success_check = parse_csv(
        in_file=args['input_csv'], desc_col=args['desc_column'], first_row=args['first_row'],
        last_row=args['last_row'], header_row=args['header_row'], attribs=args['attribs'],
        out_file=out_filepath, config_col=args['config_column'], config=args['config'],
        layout_col=args['layout_column'], resume=args['resume'], unpack=args['unpack'],
        copy_data=args['copy_data'], tract_level=args['tracts_only'],
        include_uid=args['include_uid'], write_headers=not args['suppress_headers'],
        include_unparsed=args['include_unparsed'], num_tracts=args['number_tracts'])

    if args['launch'] and success_check == 0:
        import os
        os.startfile(out_filepath)
