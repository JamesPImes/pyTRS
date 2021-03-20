# Copyright (c) 2020, James P. Imes, all rights reserved.

"""A GUI for the csv_suite of the pyTRS library."""

import tkinter as tk
from tkinter import messagebox, filedialog
from tkinter.ttk import Checkbutton

from pytrs.interface_tools import PromptConfig, PromptAttrib
from pytrs.csv_suite.pytrs_parse_csv import parse_csv
from pytrs import version as pytrs_version
from pytrs import _constants as pytrs_constants


__version__ = '0.3.1'
__versionDate__ = '9/24/2020'
__author__ = 'James P. Imes'
__email__ = 'jamesimes@gmail.com'


def version():
    return f"v{__version__} - {__versionDate__}"


class AppWindow(tk.Tk):
    
    SPLASH_INFO = (
        f"pyTRS CSV Parser {version()}\n"
        f"Built on pyTRS {pytrs_version()}.\n"
        "Copyright (c) 2020, James P. Imes, all rights reserved.\n\n"
        f"Contact: <{__email__}>\n\n"
        "A program for parsing PLSS land descriptions ('legal "
        "descriptions') in a .csv file into their component parts.\n\n"
        "Be sure to read the disclaimer prior to using this program.\n\n"
        "Read disclaimer now?"
    )

    # A dict of parsing program options -- i.e. for kwargs in `parse_csv()`.
    OUTPUT_PARAM_DICT = {
        'tract_level': [
            "Tract parsing (TRS and desc. block have already been separated)", 0
            ],
        'write_headers': ["Write headers to first row", 1],
        'include_uid': ["Generate Unique ID (UID) numbers for each parsed row", 1],
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

        # Show the start-up messagebox
        self.about()

        self.at_frame = PromptAttrib(
            self, target_attrib_var=None, show_ok=False, show_cancel=False)
        self.at_frame.grid(row=0, column=1, sticky='n', padx=5, pady=5)
    
        io_param_frame = tk.Frame(self)
        io_param_frame.grid(row=0, column=2, sticky='n', padx=5, pady=5)
    
        io_btn_frame = tk.Frame(io_param_frame)
        io_btn_frame.grid(row=10, column=1, sticky='s', padx=5, pady=5)

        # I/O parameters
        cur_row = 0
        try:
            io_lbl = tk.Label(
                io_param_frame, text="Input / Output .csv Options",
                font='"Arial Black"')
        except:
            io_lbl = tk.Label(
                io_param_frame, text="Input / Output .csv Options")
        io_lbl.grid(row=cur_row, column=1)

        about_btn = tk.Button(
            io_param_frame, text='?', padx=5, command=self.about)
        about_btn.grid(row=cur_row, column=1, sticky='e')

        cur_row += 1

        # Generate a new IntVar for each available IO option, set its
        # value to the default value per OUTPUT_PARAM_DICT, store it as
        # an instance variable, and also set it to the io_param_dict.
        # Finally, create a checkbutton for that parameter.
        # So for attribute 'tract_level':
        #   -> self.tract_levelVar --> a tk.IntVar with initial value 0
        #   -> self.io_param_dict['tract_level'] --> self.tract_levelVar
        #   -> <create a checkbutton for tract_level>
        self.io_param_dict = {}
        for param in self.OUTPUT_PARAM_DICT:
            new_var = tk.IntVar()
            new_var.set(self.OUTPUT_PARAM_DICT[param][1])
            setattr(self, param + 'Var', new_var)
            self.io_param_dict[param] = new_var
            cb = Checkbutton(
                io_param_frame, text=self.OUTPUT_PARAM_DICT[param][0],
                var=self.io_param_dict[param])
            cb.grid(row=cur_row, column=1, sticky='w', pady=2)
            cur_row += 1

        choose_file_button = tk.Button(
            io_btn_frame, text='Select File', height=2, width=10,
            command=self.choose_file_clicked)
        choose_file_button.grid(row=1, column=1, pady=10)

        desc_colPrompt = tk.Label(
            io_btn_frame, text='Column with text to parse:')
        desc_colPrompt.grid(row=4, column=1, sticky='e')
        self.desc_col_entry = tk.Entry(io_btn_frame, width=5)
        self.desc_col_entry.grid(row=4, column=2, sticky='w')

        header_rowPrompt = tk.Label(
            io_btn_frame, text='Header row (leave blank if none):')
        header_rowPrompt.grid(row=5, column=1, sticky='e')
        self.header_row_entry = tk.Entry(io_btn_frame, width=5)
        self.header_row_entry.grid(row=5, column=2, sticky='w')

        first_rowPrompt = tk.Label(io_btn_frame, text='First row to parse:')
        first_rowPrompt.grid(row=6, column=1, sticky='e')
        self.first_row_entry = tk.Entry(io_btn_frame, width=5)
        self.first_row_entry.grid(row=6, column=2, sticky='w')

        last_rowPrompt = tk.Label(
            io_btn_frame, text='Last row to parse (leave blank for all):')
        last_rowPrompt.grid(row=7, column=1, sticky='e')
        self.last_row_entry = tk.Entry(io_btn_frame, width=5)
        self.last_row_entry.grid(row=7, column=2, sticky='w')

        cf_button = tk.Button(
            io_btn_frame, text='Choose Config Parameters', height=2,
            command=self.cf_btn_clicked)
        cf_button.grid(row=20, column=1, pady=10)

        go_btn = tk.Button(
            io_btn_frame, text='Parse!', height=2, width=10, command=self.go)
        go_btn.grid(row=20, column=2, sticky='e', pady=10)

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

        # Compile the attribs
        attribs = self.at_frame.compile_attributes()

        # Compile all of the input/output parameters
        config_text = self.config_text.get()
        write_headers = bool(self.write_headersVar.get())
        unpack = bool(self.unpackVar.get())
        copy_data = bool(self.copy_dataVar.get())
        tract_level = bool(self.tract_levelVar.get())
        include_uid = bool(self.include_uidVar.get())
        include_unparsed = bool(self.include_unparsedVar.get())

        # Get desc_col; whether entered as number or alpha, convert to int.
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
        success_check = parse_csv(
            in_file=in_file, desc_col=desc_col, attribs=attribs,
            out_file=out_file, first_row=first_row, last_row=last_row,
            header_row=header_row, config=config_text,
            write_headers=write_headers, unpack=unpack,
            copy_data=copy_data, tract_level=tract_level,
            include_uid=include_uid, num_tracts=False,
            include_unparsed=include_unparsed)

        if success_check:
            if messagebox.askyesno(
                    'Success!',
                    f"File successfully parsed and saved to:\n'{out_file}'\n\n"
                    "Be sure to examine results for accuracy!\n\n"
                    "Open file now?"):
                import os
                os.startfile(out_file)

    def choose_file_clicked(self):
        in_file = filedialog.askopenfilename(
            initialdir='/',
            filetypes=[("CSV Files", "*.csv")],
            title='CSV to parse...'
        )
        self.in_file.set(in_file)
        self.title(f"pytrs CSV Parser - {in_file}")
        if in_file:
            self.deduce_desc_column(in_file)

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
        pc = PromptConfig(
            master=self.config_popup_tk, target_config_var=self.config_text,
            parameters=[
                'clean_qq', 'include_lot_divs', 'require_colon', 'ocr_scrub',
                'segment', 'layout', 'qq_depth_min', 'qq_depth_max', 'qq_depth'
            ],
            show_cancel=False, exit_after_ok=True)
        pc.pack(padx=20, pady=10)

    def deduce_desc_column(self, in_file):
        self.desc_col_entry.delete(0, 'end')
        self.first_row_entry.delete(0, 'end')
        self.header_row_entry.delete(0, 'end')

        import csv
        from pytrs.parser import find_sec, find_twprge
        csv_file = open(in_file, 'r')

        reader = csv.reader(csv_file)
        rowsToTry = 10
        colMatch = None
        rowMatch = None
        row_num = 0
        for row in reader:
            if row_num > rowsToTry:
                break
            for col_num in range(len(row)):
                text = row[col_num]
                if text is None:
                    continue

                elif len(find_sec(text)) > 0 and len(find_twprge(text)) > 0:
                    # If the cell contains > 0 sections and > 0 T&R, assume it's
                    # our first match. Add 1 to convert row/column nums from
                    # 0-indexed to 1-indexed:
                    rowMatch = row_num + 1
                    colMatch = col_num + 1

                    break
            if rowMatch:
                break
            row_num += 1

        if rowMatch:
            self.desc_col_entry.insert('end', num_to_alpha(colMatch))
            self.first_row_entry.insert('end', str(rowMatch))
            if rowMatch > 1:
                self.header_row_entry.insert('end', str(rowMatch - 1))

        csv_file.close()

    def about(self):
        confirm = messagebox.askquestion('pyTRS CSV Parser', self.SPLASH_INFO)
        if confirm == 'yes':
            messagebox.showinfo(
                'pyTRS Disclaimer', pytrs_constants.__disclaimer__)


def launch_app():
    app = AppWindow()
    app.mainloop()


def alpha_to_num(alpha):
    """Convert an alpha into an integer ('A' --> 1, 'Z' --> 26,
    'AA' --> 27) -- from A through ZZ."""
    val = 0
    if len(alpha) > 2:
        return None
    if len(alpha) == 2:
        char = alpha[0]
        val = ((ord(char.upper()) - ord('A')) + 1) * 26
    char = alpha[-1]
    val += ((ord(char.upper()) - ord('A')) + 1)
    return val


def num_to_alpha(num):
    """Convert a number (integer) into an alpha (1 --> 'A',
    26 --> 'Z', 27 -- > 'AA') -- from A through ZZ."""
    return ((num - 1) // 26 > 0) * chr((num - 1) // 26 + ord('A') - 1) \
        + chr((num - 1) % 26 + ord('A'))


if __name__ == '__main__':
    launch_app()
