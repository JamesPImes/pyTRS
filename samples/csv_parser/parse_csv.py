# Copyright (c) 2020-2021, James P. Imes, all rights reserved.

"""
A GUI application to parse PLSS descriptions in a .csv file, and write
the parsed results at the end of each row, inserting rows as necessary
such that there is one Tract per row. Saves to a new .csv file.

(Demonstrates PromptConfig and PromptAttrib classes in the
pytrs.interface_tools package.)
"""

import csv
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, filedialog
from tkinter.ttk import Checkbutton

import pytrs
import pytrs.interface_tools
from pytrs.utils import gen_uid, alpha_to_num, num_to_alpha, flatten


__version__ = '0.4.0'
__version_date__ = '4/11/2021'
__author__ = 'James P. Imes'
__email__ = 'jamesimes@gmail.com'


def parse_csv(
        in_file,
        desc_col: int,
        first_row=1,
        last_row=-1,
        header_row=-1,
        attributes=None,
        out_file=None,
        config_col=None,
        config=None,
        layout_col=None,
        write_headers=True,
        unpack=False,
        copy_data=False,
        tract_level=False,
        include_uid=False,
        include_unparsed=True):
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
    :param attributes: Which pytrs.Tract attributes to write to the csv.
    Pass as a list of strings, or as a single string with attribute
    names separated by comma. (If not specified, will default to basic
    data for each description.)
    :param out_file: Filepath to the .csv to write to. (If not
    specified, will default to a variation of the input filename, with a
    timestamp.)
    :param config_col: (Optional) Column in the .csv file containing the
    pyTRS config parameters to use for parsing that row.
    :param config: (Optional) Standard pyTRS config parameters to be
    used for every description, entered as a string with parameters
    separated by comma, or as a pytrs.Config object.
    NOTE: If `config_col` is specified, then `config=` will be ignored
    (assuming the `config_col` actually contains data).
    :param layout_col: (Optional) Column in the .csv file containing the
    pyTRS layout name to use for that row. (If not specified, will use
    `config=` parameters or `config_col`; and if not specified there,
    will deduce it when parsed.)
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
    :return: Returns the filepath of the output file.
    """

    in_file = Path(in_file)
    if out_file:
        out_file = Path(out_file)

    if out_file is None:
        from datetime import datetime
        t = datetime.now()
        ts = f"{t:%Y%m%d%H%M%S}"
        out_file = in_file.with_name(
            f"{in_file.stem}_pytrs_parsed_{ts}{in_file.suffix}")

    # Ensure input and output filepaths lead to .csv files.
    if in_file.suffix.lower() != '.csv' or out_file.suffix.lower() != '.csv':
        raise ValueError("input and output filepaths must end in '.csv'")

    if desc_col < 1:
        raise ValueError(
            f"Integer for column must be equal to or greater than 1. "
            f"~~desc_col={desc_col}")

    for param in [first_row, last_row, header_row]:
        if not isinstance(param, int):
            raise TypeError("Rows must be specified as integers.")

    if first_row <= header_row:
        raise ValueError(
            f"first_row must be greater than header_row. "
            f"~~first_row={first_row}, header_row={header_row}")

    # Whether we should stop after a certain number of rows
    end_early = False
    if last_row > 0:
        end_early = True

    if attributes in [None, '']:
        attributes = ('trs', 'desc')
        if tract_level:
            attributes = ('pp_desc', 'lots', 'qqs')
    elif isinstance(attributes, str):
        # Split attribute string into list of Tract attribute names:
        attributes = attributes.replace(' ', '').split(',')

    read_file = open(in_file)
    reader = csv.reader(read_file)

    write_file = open(out_file, mode='w', newline='')
    writer = csv.writer(write_file)

    print(f"Parsing descriptions in '{in_file}'...")

    # Number of rows encountered AFTER the header (identical to row_num
    # if no header in original) -- for UID purposes.
    parse_num = 0

    for row_num, row in enumerate(reader):
        row_num += 1

        if write_headers:
            if row_num == header_row:
                writer.writerow(row + ['parse_UID'] * include_uid + attributes)
                write_headers = False
                continue
            elif row_num == first_row and header_row < 1:
                # In this scenario, write headers just above first-parsed row.
                writer.writerow(
                    ['' for _ in row] + ['parse_UID'] * include_uid + attributes)
                write_headers = False
                # Do not continue yet, because we still need to parse
                # and write results.

        if (include_unparsed
                and ((row_num < first_row) or (row_num > last_row and end_early))):
            writer.writerow(row)
            continue

        elif row_num < first_row:
            continue

        elif row_num > last_row and end_early:
            break

        parse_num += 1

        # config_col, layout_col, and desc_col are 1-indexed, but are
        # used to access elements in 0-indexed list, so we subtract 1
        # from each here.

        # Get `config` parameters either from the .csv, or from
        # `config=` (preference given to config_col).
        try:
            config = row[config_col - 1]
        except TypeError:
            pass
        if config is None:
            config = ''

        # If user has specified a column for layout, add that layout to
        # the end of the `config` string.
        try:
            config = f"{config},{row[layout_col - 1]}"
        except TypeError:
            pass

        # Get text of description from row.
        desc_text = ''
        try:
            desc_text = row[desc_col - 1]
        except IndexError:
            pass

        # Parse the description.
        if tract_level:
            t = pytrs.Tract(desc=desc_text, config=config, parse_qq=True)
            # Manually put data into a nested list, to mirror the output
            # of `PLSSDesc.tracts_to_list()`.
            all_tract_data = [t.to_list(attributes)]
        else:
            d = pytrs.PLSSDesc(desc_text, config=config, parse_qq=True)
            all_tract_data = d.tracts_to_list(attributes)

        total_tracts = len(all_tract_data)

        for new_row_num, data in enumerate(all_tract_data, start=1):
            if new_row_num == 1 or copy_data:
                # Copy the original row data
                to_write = row.copy()
            else:
                # Blank data for inserted rows, if copy_data was not requested.
                to_write = ['' for _ in row]

            if include_uid:
                # Generate UID in the format '0032.a-j':
                uid = gen_uid(
                    num=parse_num, sub=new_row_num, total_sub=total_tracts)
                to_write.append(uid)

            try:
                # Add the parsed Tract Data
                for val in data:
                    if isinstance(val, (list, tuple)) and unpack:
                        # If requested, `unpack` and join lists/tuples
                        # before writing:
                        to_write.append(', '.join(flatten(val)))
                    else:
                        to_write.append(val)
            except IndexError:
                # If no data for this Tract (e.g., no tracts identified
                # in the PLSSDesc object), fill with dummy data.
                to_write.extend([f"{attrib}: n/a" for attrib in attributes])

            writer.writerow(to_write)

    print(
        f"Done. Results written to '{out_file}'. "
        f"Be sure to examine results for fidelity."
    )
    return out_file


class ParserAppWindow(tk.Tk):
    """
    A GUI application for parsing PLSS descriptions in a .csv file.
    """

    SPLASH_INFO = (
        f"pyTRS CSV Parser v{__version__} - {__version_date__}\n"
        f"Built on pyTRS {pytrs.version()}.\n"
        "Copyright (c) 2020-2021, James P. Imes, all rights reserved.\n\n"
        f"Contact: <{__email__}>\n\n"
        "A program for parsing PLSS land descriptions ('legal "
        "descriptions') in a .csv file into their component parts.\n\n"
        "Be sure to read the disclaimer prior to using this program.\n\n"
        "Read disclaimer now?"
    )

    # A dict of parsing program options -- i.e. parameters in
    # `parse_csv()`. The integers control whether each option is checked
    # on or off by default.
    OUTPUT_PARAM_DICT = {
        'tract_level': ["Tract parsing (TRS and desc. block are already separate)", 0],
        'write_headers': ["Write headers", 1],
        'include_uid': ["Generate Unique ID (UID) for each parsed row", 1],
        'copy_data': ["Copy existing data into newly inserted rows", 0],
        'include_unparsed': ["Also include any unparsed rows", 1],
        'unpack': ["Unpack lists", 1]
    }

    def __init__(self):
        tk.Tk.__init__(self)
        self.title('pyTRS CSV Parser')

        self.config_text = tk.StringVar()
        self.config_text.set('')

        # What will be a PromptConfig window.
        self.config_popup_tk = None

        self.in_file = tk.StringVar()
        self.in_file.set('')

        # Show the start-up messagebox.
        self.about()

        self.at_frame = pytrs.interface_tools.PromptAttrib(
            self, target_var=None, show_ok=False, show_cancel=False)
        self.at_frame.grid(row=0, column=1, sticky='n', padx=5, pady=5)

        # Frame for I/O options.
        io_param_frame = tk.Frame(self)
        io_param_frame.grid(row=0, column=2, sticky='n', padx=5, pady=5)

        io_cur_row = 0
        io_lbl = tk.Label(
            io_param_frame, text="Input / Output .csv Options",
            font='"Arial Black"')
        io_lbl.grid(row=io_cur_row, column=1)
        io_cur_row += 1

        # Generate a new IntVar for each available IO option, set its
        # value to the default value per OUTPUT_PARAM_DICT, store it as
        # an instance variable, and also set it to the io_param_dict.
        # Finally, create a checkbutton for that parameter.
        # So for attribute 'tract_level':
        #   -> self.tract_level_var --> a tk.IntVar with initial value 0
        #   -> self.io_param_dict['tract_level'] --> self.tract_level_var
        #   -> <create a checkbutton for tract_level>
        self.io_param_dict = {}
        for param in self.OUTPUT_PARAM_DICT:
            new_var = tk.IntVar()
            new_var.set(self.OUTPUT_PARAM_DICT[param][1])
            setattr(self, param + '_var', new_var)
            self.io_param_dict[param] = new_var
            cb = Checkbutton(
                io_param_frame, text=self.OUTPUT_PARAM_DICT[param][0],
                var=self.io_param_dict[param])
            cb.grid(row=io_cur_row, column=1, sticky='w', pady=2)
            io_cur_row += 1

        # Frame for I/O buttons.
        io_btn_frame = tk.Frame(io_param_frame)
        io_btn_frame.grid(row=io_cur_row, column=1, sticky='s', padx=5, pady=5)
        io_cur_row += 1

        io_btn_cur_row = 0

        choose_file_button = tk.Button(
            io_btn_frame, text='Select File', height=2, width=10,
            command=self.choose_file_clicked)
        choose_file_button.grid(row=io_btn_cur_row, column=1, pady=10)
        io_btn_cur_row += 1

        desc_col_prompt = tk.Label(
            io_btn_frame, text='Column with text to parse:')
        desc_col_prompt.grid(row=io_btn_cur_row, column=1, sticky='e')
        self.desc_col_entry = tk.Entry(io_btn_frame, width=5)
        self.desc_col_entry.grid(row=io_btn_cur_row, column=2, sticky='w')
        io_btn_cur_row += 1

        header_row_prompt = tk.Label(
            io_btn_frame, text='Header row (leave blank if none):')
        header_row_prompt.grid(row=io_btn_cur_row, column=1, sticky='e')
        self.header_row_entry = tk.Entry(io_btn_frame, width=5)
        self.header_row_entry.grid(row=io_btn_cur_row, column=2, sticky='w')
        io_btn_cur_row += 1

        first_row_prompt = tk.Label(io_btn_frame, text='First row to parse:')
        first_row_prompt.grid(row=io_btn_cur_row, column=1, sticky='e')
        self.first_row_entry = tk.Entry(io_btn_frame, width=5)
        self.first_row_entry.grid(row=io_btn_cur_row, column=2, sticky='w')
        io_btn_cur_row += 1

        last_row_prompt = tk.Label(
            io_btn_frame, text='Last row to parse (leave blank for all):')
        last_row_prompt.grid(row=io_btn_cur_row, column=1, sticky='e')
        self.last_row_entry = tk.Entry(io_btn_frame, width=5)
        self.last_row_entry.grid(row=io_btn_cur_row, column=2, sticky='w')
        io_btn_cur_row += 1

        cf_button = tk.Button(
            io_btn_frame, text='Choose Config Parameters', height=2,
            command=self.cf_btn_clicked)
        cf_button.grid(row=io_btn_cur_row, column=1, pady=10)

        go_btn = tk.Button(
            io_btn_frame, text='Parse!', height=2, width=10, command=self.go)
        go_btn.grid(row=io_btn_cur_row, column=2, sticky='e', pady=10)
        io_btn_cur_row += 1

        about_btn = tk.Button(
            io_btn_frame, text='?', padx=8, pady=2, command=self.about)
        about_btn.grid(row=io_btn_cur_row, column=2, pady=10, sticky='e')
        io_btn_cur_row += 1

    def go(self):
        """
        Pull the variables from all over, prompt for save-to filepath,
        and run it.
        """
        in_file = self.in_file.get()

        # Ensure `in_file` points to a .csv file.
        if not in_file.lower().endswith('csv'):
            messagebox.showerror(
                'Error', "Choose an input file with '.csv' extension")
            return

        # Prompt for save-to filepath, with default filename modified
        # from in_file.
        def_file_name = f"{in_file.split('/')[-1][:-4]}_pytrs_parsed.csv"
        out_file = filedialog.asksaveasfilename(
            initialdir=in_file, initialfile=def_file_name,
            filetypes=[("CSV Files", "*.csv")], title='Save to...')
        # Ensure `out_file` points to a .csv file.
        if out_file == '':
            return

        elif not out_file.lower().endswith('csv'):
            messagebox.showerror(
                'Error', "Choose a filename with '.csv' extension")
            return

        # Compile the attributes using the PromptAttrib method.
        attributes = self.at_frame.compile_attributes()

        # Compile all of the input/output parameters.
        config_text = self.config_text.get()
        write_headers = bool(self.write_headers_var.get())
        unpack = bool(self.unpack_var.get())
        copy_data = bool(self.copy_data_var.get())
        tract_level = bool(self.tract_level_var.get())
        include_uid = bool(self.include_uid_var.get())
        include_unparsed = bool(self.include_unparsed_var.get())

        # Get desc_col and convert to int.
        desc_col = self.desc_col_entry.get()
        if not desc_col:
            messagebox.showerror(
                'Error!',
                'Fill in the column containing descriptions to be parsed.')
            return
        elif desc_col.isalpha() and len(desc_col) <= 2:
            desc_col = int(alpha_to_num(desc_col))
        elif desc_col.isnumeric() and len(desc_col) <= 2:
            desc_col = int(desc_col)
        if not isinstance(desc_col, int):
            messagebox.showerror(
                'Error!',
                'Specify the column containing descriptions as either the '
                'number of the column (indexed to 1), or as the letter of '
                'the column as used in standard spreadsheet software '
                '(A, B, ..., Z, AA, AB, etc.).\n\n'
                '(May be up to two characters long, whether entered as a '
                'number or as letters.)'
            )

        first_row = self.first_row_entry.get()
        if not first_row:
            messagebox.showerror(
                'Error!',
                'Specify the first row containing descriptions to be parsed.')
            return
        try:
            first_row = int(first_row)
        except (TypeError, ValueError):
            messagebox.showerror(
                'Error!',
                'Enter a number for the first row containing descriptions to '
                'be parsed.')
            return

        last_row = self.last_row_entry.get()
        if last_row:
            try:
                last_row = int(last_row)
            except (TypeError, ValueError):
                messagebox.showerror(
                    'Error!',
                    'If you only want to parse some rows, enter a number for '
                    'the last row containing descriptions to be parsed.')
                return
        else:
            last_row = -1

        header_row = self.header_row_entry.get()
        if header_row:
            try:
                header_row = int(header_row)
            except (TypeError, ValueError):
                messagebox.showerror(
                    'Error!',
                    'To specify the row containing headers in the input '
                    '.csv file, enter a number for that row.')
                return
        else:
            header_row = None

        # Run the parser
        try:
            parse_csv(
                in_file=in_file,
                desc_col=desc_col,
                attributes=attributes,
                out_file=out_file,
                first_row=first_row,
                last_row=last_row,
                header_row=header_row,
                config=config_text,
                write_headers=write_headers,
                unpack=unpack,
                copy_data=copy_data,
                tract_level=tract_level,
                include_uid=include_uid,
                include_unparsed=include_unparsed)
        except BaseException as error:
            messagebox.showerror(
                'Error!',
                'Unhandled error occurred.\n\n'
                f"{error}"
            )
            raise error

        if messagebox.askyesno(
                'Success!',
                f"File successfully parsed and saved to:\n'{out_file}'\n\n"
                "Be sure to examine results for accuracy!\n\n"
                "Open file now?"):
            import os
            os.startfile(out_file)

    def choose_file_clicked(self):
        """
        Prompt user with file selection; and then deduce which
        rows/columns we need to parse.
        """
        in_file = filedialog.askopenfilename(
            filetypes=[("CSV Files", "*.csv")],
            title='CSV to parse...'
        )
        self.in_file.set(in_file)
        self.title(f"pyTRS CSV Parser - {in_file}")
        if in_file:
            self.deduce_desc_column(in_file)
        return None

    def cf_btn_clicked(self):
        """
        Config button was clicked; launch popup window to get Config
        parameters from user (results are stored in StringVar
        `self.config_text`).
        """
        try:
            self.config_popup_tk.destroy()
        except AttributeError:
            pass

        self.config_popup_tk = tk.Toplevel()
        self.config_popup_tk.title('Set pyTRS Config Parameters')
        pc = pytrs.interface_tools.PromptConfig(
            master=self.config_popup_tk,
            target_var=self.config_text,
            parameters=[
                'clean_qq',
                'include_lot_divs',
                'require_colon',
                'ocr_scrub',
                'segment',
                'layout',
                'qq_depth_min',
                'qq_depth_max',
                'qq_depth'
            ],
            show_cancel=False,
            exit_after_ok=True)
        pc.pack(padx=20, pady=10)
        return None

    def deduce_desc_column(self, in_file):
        """
        Attempt to deduce which column contains descriptions, and the
        first row and header row. If successful, will populate the
        appropriate I/O fields.
        """
        # Zero-out prior data in these fields.
        self.desc_col_entry.delete(0, 'end')
        self.first_row_entry.delete(0, 'end')
        self.header_row_entry.delete(0, 'end')

        csv_file = open(in_file, 'r')
        reader = csv.reader(csv_file)
        rows_to_try = 10
        col_match = None
        row_match = None
        for row_num, row in enumerate(reader):
            if row_num >= rows_to_try:
                break
            for col_num, txt in enumerate(row):
                if not isinstance(txt, str):
                    continue
                elif len(pytrs.find_sec(txt)) > 0 and len(pytrs.find_twprge(txt)) > 0:
                    # If the cell contains at least one section and one Twp/Rge,
                    # assume it's our first match. Add 1 to convert row/column
                    # nums from 0-indexed to 1-indexed.
                    row_match = row_num + 1
                    col_match = col_num + 1
                    break
            if row_match:
                break

        if row_match:
            self.desc_col_entry.insert('end', num_to_alpha(col_match))
            self.first_row_entry.insert('end', str(row_match))
            if row_match > 1:
                self.header_row_entry.insert('end', str(row_match - 1))

        csv_file.close()
        return None

    def about(self):
        confirm = messagebox.askquestion('pyTRS CSV Parser', self.SPLASH_INFO)
        if confirm == 'yes':
            messagebox.showinfo(
                'pyTRS Disclaimer', pytrs.__disclaimer__)
        return None


def launch_app():
    app = ParserAppWindow()
    app.mainloop()


if __name__ == '__main__':
    launch_app()
