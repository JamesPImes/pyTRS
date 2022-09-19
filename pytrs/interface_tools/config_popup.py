# Copyright (c) 2020-2022, James P. Imes, all rights reserved

"""
A GUI app for choosing config parameters for parsing.

A ``PromptConfig`` object can be used directly in a tkinter application;
or the ``prompt_config()`` function can be used to hold up the program
while the user makes their choices, and then continue when it returns.
"""

# Note: Pass `show_ok=True` and `exit_after_ok=True` to use
# `prompt_config()` as a 'go button' for a parsing application. It will
# wait for the user to hit 'OK', then close the window and return the
# config parameters to the program that called the function. It may be
# useful to specify the parameter `ok_button_text=<'string'>` with the
# appropriate context for how the function is incorporated into your
# program.

import tkinter as tk
from tkinter import messagebox
from tkinter.ttk import Combobox
from ..parser import (
    Config,
    MasterConfig,
    IMPLEMENTED_LAYOUTS,
    IMPLEMENTED_LAYOUT_EXAMPLES,
)


def prompt_config(
        parameters='all',
        show_ok=True,
        show_cancel=False,
        prompt_after_ok=None,
        ok_button_text='Confirm Config Parameters',
        cancel_button_text='Cancel',
        confirm_cancel_prompt=None):
    """
    Launch a PromptConfig tkinter frame, for the user to set config
    parameters. Will wait for the PromptConfig window to close, and then
    will return the config parameters as a string.

    IMPORTANT: If allowing the user to see the Cancel button, be aware
    that clicking Cancel will return the string 'CANCEL'.

    If the user exits out of the window, it will return 'EXIT'.

    All parameters have the same effect as they do in __init__() for a
    PromptAttrib object, although not all parameters are available in
    this function.
    :param parameters: Which parameters choices to expose to the user.
    :param show_ok: Whether to show the OK button.
    :param show_cancel: Whether to show the Cancel button.
    :param prompt_after_ok: (Optional) The text to display after OK is
    clicked. If None, there will be no prompt.
    :param ok_button_text: The text to show inside the OK button.
    (Defaults to 'Confirm Config Parameters'.)
    :param cancel_button_text: The text to show inside the Cancel
    button.
    :param confirm_cancel_prompt: (Optional) The text to display after
    Cancel is clicked, allowing the user to change their mind. If None,
    there will be no confirmation prompt.
    :return: A string of the user's chosen config parameters.
    """

    config_holder = {'config_text': 'EXIT'}

    popup = PromptConfig(
        master=None,
        target_var=None,
        parameters=parameters,
        show_ok=show_ok,
        show_cancel=show_cancel,
        prompt_after_ok=prompt_after_ok,
        cancel_button_text=cancel_button_text,
        ok_button_text=ok_button_text,
        exit_after_ok=True,
        external_var_dict=config_holder,
        confirm_cancel_prompt=confirm_cancel_prompt)
    popup.master.mainloop()
    return config_holder['config_text']


class PromptConfig(tk.Frame):
    """
    A tkinter frame for configuring parsing parameters (i.e. ``Config``
    objects).

    NOTE: You can customize the behavior of this class by modifying the
    class attributes before creating one:
        .ALL_PARAMETERS
        .RB_PARAMETERS
        .QQ_DEPTH_CONTROLS
        .COMBO_PARAMS
        .COMBO_WIDTH_NSEW
        .COMBO_WIDTH_OTHER
        .COMBO_VALUES
        .COMBO_LABELS
        .HELP_TEXT

    ...but depending on what gets changed, it might break the compiler
    or other functionality. So, that functionality is not officially
    supported.
    """

    # Exposing these dicts, etc. as class attributes allows for some
    # customization without requiring creating a subclass and modifying
    # __init__().

    # The options that will be populated if `attributes='all'` at init.
    ALL_PARAMETERS = list(Config._CONFIG_ATTRIBUTES)

    # Parameters that are set via radiobuttons:
    RB_PARAMS = [
        'clean_qq',
        'supress_lot_divs',
        'require_colon',
        'ocr_scrub',
        'segment',
        'init_preprocess',
        'wait_to_parse',
        'parse_qq',
        'break_halves'
    ]

    # Parameters that are set to a number and control how deeply to
    # parse QQ's.
    # NOTE: "qq_depth" should be first in this list, so that it takes
    # priority over qq_depth_min and _max when compiling the config text.
    QQ_DEPTH_CONTROLS = ['qq_depth', 'qq_depth_min', 'qq_depth_max']

    # The order that these comboboxes will appear in.
    COMBO_PARAMS = [
        'default_ns',
        'default_ew',
        'layout',
        'qq_depth_min',
        'qq_depth_max',
        'qq_depth',
    ]

    # Widths for the Comboboxes.
    COMBO_WIDTH_NSEW = 16  # default_ns / default_ew
    COMBO_WIDTH_OTHER = 25

    # Values with which to populate the comboboxes.
    COMBO_VALUES = {
        'default_ns': (
            '[default: North]',
            'North',
            'South'),
        'default_ew': (
            '[default: West]',
            'West',
            'East'),
        'layout': tuple(
            ['Deduce (RECOMMENDED)'] + list(IMPLEMENTED_LAYOUTS)),
        'qq_depth_min': (
            "[Default: 2 -> QQ's]",
            '1 (quarter sections)',
            '2 (QQs)',
            '3',
            '4',
            '5'),
        'qq_depth_max': (
            '[Default - no max]',
            '1 (quarter sections)',
            '2 (QQs)',
            '3',
            '4',
            '5'),
        'qq_depth': (
            '[Default - use min and max]',
            '1 (quarter sections)',
            '2 (QQs)',
            '3',
            '4',
            '5')
    }

    # Labels for the comboboxes.
    COMBO_LABELS = {
        'layout': "Force parsing as a particular layout?",
        'default_ns': "Default unspecified Townships to [North] or [South]?",
        'default_ew': "Default unspecified Ranges to [West] or [East]?",
        'qq_depth_min': "MINIMUM depth to parse QQs",
        'qq_depth_max': "MAXIMUM depth to parse QQs",
        'qq_depth': "EXACT depth to parse QQs (override min and max)"
    }

    # The text to show for each config parameter via its 'Help' button.
    HELP_TEXT = {
        'default_ns': (
            "If the dataset contains a Township whose N/S "
            "direction was not specified, the program will assume "
            "this specified direction. (And if not specified here, "
            "will assumed North.)"
        ),

        'default_ew': (
            "If the dataset contains a Range whose E/W direction "
            "was not specified, the program will assume this "
            "specified direction. (And if not specified here, "
            "will assumed West.)"
        ),

        'layout': (
            "If you know that the dataset is all laid out in the "
            "same format, you may get more accurate results if "
            "you force parsing according to one of these formats. "
            "However, if there are multiple layouts, or unknown "
            "layouts, it is probably wise to let the program "
            "deduce the layout for each.\n\n"
            "Below are examples of the possible layouts:\n\n"
            f"{IMPLEMENTED_LAYOUT_EXAMPLES}"
        ),

        'clean_qq': (
            "Dataset contains only clean aliquots and lots; no "
            "metes-and-bounds, exceptions, or limitations. "
            "Anything that resembles an aliquot may be captured "
            "as such. For example, 'NE' will be captured as 'NE¼'."
            "\n\nThis may allow for broader parsing of lots and "
            "QQ's, but it can also result in numerous false "
            "matches, if the dataset is not simple and clean. For "
            "example, 'Northernmost one hundred feet of the NW/4' "
            "would match as 'Northernmost oNE¼ hundred feet of "
            "the NW¼'.\n\n"
            "Default: off (`False`)"
        ),

        'suppress_lot_divs': (
            "If parsing lots, suppress report any divisions of lots. "
            "For example, if False, 'N/2 of Lot 1' would be reported "
            "as 'N2 of L1'. If this is turned on, it would be "
            "reported as 'L1'.\n\n"
            "Default: off (`False`)"
        ),

        'require_colon': (
            "Instruct a PLSSDesc object (whose layout is "
            "`TRS_desc` or `S_desc_TR`) to require a colon "
            "between the section number and the following "
            "description -- i.e. 'Section 14 NE/4' would NOT be "
            "picked up if 'require_colon' is on (`True`).  If "
            "turned off (`False`), then 'Section 14 NE/4' would "
            "be captured. However, this may result in false "
            "matches, depending on the dataset.\n\n"
            "(Note that the default parsing method is to first "
            "pass over instances that do not have a colon. If no "
            "sections are matched, it will make a second pass, "
            "this time allowing section numbers that are NOT "
            "followed by colon. If not set here, the potentially "
            "two-pass method will be used by default.)\n\n"
            "If set to on (`True`) here, that second-pass method "
            "will be prevented. If set to off (`False`) here, it "
            "will broadly capture all such instances, and the "
            "second-pass method will not be needed. (Again, "
            "beware false matches.)"
        ),

        'ocr_scrub': (
            "Attempt to iron out common OCR artifacts in a "
            "PLSSDesc object or Tract object (e.g., 'TIS4N-R97W' "
            "that should have been 'T154N-R97W'). (WARNING: may "
            "cause other issues.)\n\n"
            "Default: off (`False`)."
        ),

        'segment': (
            "While parsing, segment each description by T&R "
            "before identifying tracts, which MIGHT capture SOME "
            "descriptions whose layout changes partway through. "
            "(However, this cannot capture ALL changes in "
            "layouts.)\n\n"
            "Default: off (`False`)"
        ),

        'init_preprocess': (
            "Preprocess PLSS descriptions and Tracts upon "
            "initialization.\n\n"
            "Default: on (`True`)"
        ),

        'wait_to_parse': (
            "Wait to parse PLSS descriptions upon initialization, "
            "rather than doing it automatically.\n\n"
            "Default: off (`False` -- i.e. do parse by default)"
        ),

        'parse_qq': (
            "Parse Tracts into lots and QQ's upon initialization. "
            "(If used with a PLSS description, its resulting Tracts "
            "will be parsed into lots/QQs.)\n\n"
            "Default: off (`False`)"
        ),

        'qq_depth_min': (
            "Specify the MINIMUM 'depth' to which to parse "
            "aliquots -- i.e. 2 will result in divisions NO "
            "LARGER THAN quarter-quarters (QQs, e.g., 'NENE'); "
            "whereas 1 will result in divisions no larger than "
            "quarter sections (e.g., 'NE'). Will still include "
            "smaller divisions if they exist in the data (i.e. "
            "'E/2NE/4NE/4' would become ['E2NENE'] if this is set "
            "to 2; or ['NENENE', 'SENENE'] if set to 3).\n\n"

            "Examples (parsing the 'NE/4'):\n\n"

            "1 (quarter sections) -> 'NE'\n\n"

            "2 (QQs) -> 'NENE', 'NWNE', 'SENE', 'SWNE'\n\n"
            "3 -> 'NENENE', 'NWNENE', 'SENENE', 'SWNENE', "
            "'NENWNE', 'NWNWNE', 'SENWNE', 'SWNWNE', 'NESENE', "
            "'NWSENE', 'SESENE', 'SWSENE', 'NESWNE', 'NWSWNE', "
            "'SESWNE', 'SWSWNE'\n\n"

            "[etc.]\n\n\n"

            "Default: 2 (i.e. QQs)"
        ),

        'qq_depth_max': (
            "Specify the MAXIMUM 'depth' to which to parse "
            "aliquots -- i.e. 2 will result in divisions NO "
            "SMALLER THAN quarter-quarters (QQs, e.g., 'NENE'); "
            "whereas 1 will result in divisions no smaller than "
            "quarters (e.g., 'NE'). Will NOT include smaller"
            "divisions if they exist in the data (i.e."
            "'E/2NE/4NE/4' would become ['NENE'] if this is set "
            "to 2).\n\n"
            "NOTE: qq_depth_max should be greater than or equal to "
            "qq_depth_min.\n\n\n"

            "Examples (parsing the 'NE/4'):\n\n"

            "1 (quarter sections) -> 'NE'\n\n"

            "2 (QQs) -> 'NENE', 'NWNE', 'SENE', 'SWNE'\n\n"
            "3 -> 'NENENE', 'NWNENE', 'SENENE', 'SWNENE', "
            "'NENWNE', 'NWNWNE', 'SENWNE', 'SWNWNE', 'NESENE', "
            "'NWSENE', 'SESENE', 'SWSENE', 'NESWNE', 'NWSWNE', "
            "'SESWNE', 'SWSWNE'\n\n"

            "[etc.]\n\n\n"
            "Default: None. (Will not cull smaller aliquot "
            "divisions, unless explicitly told to do so.)"
        ),

        'qq_depth': (
            "Specify the EXACT 'depth' to which to parse "
            "aliquots -- i.e. 2 will result in exactly "
            "quarter-quarters (QQs, e.g., 'NENE'), even if smaller "
            "divisions exist in the data. This is equivalent to "
            "setting qq_depth_min equal to qq_depth_max.\n\n"
            "NOTE: Using `qq_depth` will override `qq_depth_min` "
            "and `qq_depth_max`.\n\n\n"

            "Examples (parsing the 'NE/4'):\n\n"

            "1 (quarter sections) -> 'NE'\n\n"

            "2 (QQs) -> 'NENE', 'NWNE', 'SENE', 'SWNE'\n\n"
            "3 -> 'NENENE', 'NWNENE', 'SENENE', 'SWNENE', "
            "'NENWNE', 'NWNWNE', 'SENWNE', 'SWNWNE', 'NESENE', "
            "'NWSENE', 'SESENE', 'SWSENE', 'NESWNE', 'NWSWNE', "
            "'SESWNE', 'SWSWNE'\n\n"

            "[etc.]\n\n\n"
            "Default: 2 (i.e. QQs)"
        ),

        'break_halves': (
            "Whether to break aliquot halves into quarters, EVEN IF "
            "we are beyond the `qq_depth_min`.\n\n"
            "For example, if qq_depth_min is set to 2, intending "
            "to generate QQ's, but our dataset includes the "
            "E/2W/2NE/4...\n\n"
            "...without `break_halves`, this would parse into "
            "['E2NWNE', 'E2SWNE'].\n\n"
            "...but with `break_halves` turned on, this would parse into "
            "['NENWNE', 'SENWNE', 'NESWNE', 'SESWNE'].\n\n"
            "Default: off (`False`)"
        ),
    }

    def __init__(
            self, master=None,
            target_var=None,
            parameters='all',
            show_ok=True,
            show_cancel=False,
            prompt_after_ok=None,
            exit_after_ok=True,
            external_var_dict=None,
            ok_button_text='Confirm Config Parameters',
            cancel_button_text='Cancel',
            confirm_cancel_prompt=None,
            **kw):
        """
        A tkinter Frame for setting pyTRS config parameters.
        IMPORTANT: If the Cancel button (or the OK button, if parameter
        `exit_after_ok=True` is used at init) is used, it will destroy
        `master`, and not just `self`.

        :param master: The tkinter master (same as for tkinter.Frame)
        :param target_var: A tk.StringVar to which Config data should be
        stored when the OK button is clicked.
        :param parameters: A list or string containing the parameters
        that should be available to the user. If `parameters='all'`,
        will display all possible parameters. If passed as a string,
        parameter names should be separate by a comma and no spaces.
        :param show_ok: Include the OK button.
        :param ok_button_text: A string, for custom text for the OK
        button.
        :param prompt_after_ok: A string to display in a messagebox
        after the OK button has been clicked. Defaults to None.
        :param exit_after_ok: Whether to close the window after OK 
        button is clicked. Defaults to False.
        :param cancel_button_text: A string, for custom text for the
        Cancel button.
        :param show_cancel: Include the Cancel button.
        IMPORTANT: If the Cancel button is clicked, it will set the
        `target_var` to the string 'CANCEL' and close the window.
        :param confirm_cancel_prompt: A string to display in a
        yes/no messagebox when the Cancel button is clicked. Defaults
        to None.
        :param external_var_dict: A dict with the key 'config_text',
        to which the compiled config parameters should be set. (Only
        used by `prompt_config()` -- probably ignore this parameter.)
        :param kw: Kwargs to pass through to tkinter.Frame at init.
        """
        default_master = False
        if master is None:
            default_master = True
            master = tk.Tk()
            master.title("pyTRS Config Options")
        tk.Frame.__init__(self, master, **kw)
        self.master = master
        if default_master:
            self.pack(padx=20, pady=10)
        self.default_master = default_master

        if target_var is None:
            target_var = tk.StringVar()
        self.target_var = target_var
        
        # Determine which parameters the user is allowed to set:
        if parameters is None:
            parameters = 'all'
        
        if isinstance(parameters, str):
            if parameters.lower() == 'all':
                parameters = self.ALL_PARAMETERS
            else:
                parameters = [pr.lower().strip() for pr in parameters.split(',')]

        if external_var_dict is None:
            external_var_dict = {'config_text': ''}
        self.external_var_dict = external_var_dict

        self.parameters = parameters

        self.show_ok = show_ok
        self.show_cancel = show_cancel
        self.prompt_after_ok = prompt_after_ok
        self.exit_after_ok = exit_after_ok
        self.ok_button_text = ok_button_text
        self.cancel_button_text = cancel_button_text
        self.confirm_cancel_prompt = confirm_cancel_prompt

        # A dict of the possible config variables, with nested dicts for
        # respective variable and help text (variables are set later).
        self.CONFIG_DEF = {
            param: {'help': self.HELP_TEXT[param]} for param in self.HELP_TEXT
        }

        for pr in self.COMBO_PARAMS:
            # Set the values.
            self.CONFIG_DEF[pr]['values'] = self.COMBO_VALUES[pr]
            self.CONFIG_DEF[pr]['label_txt'] = self.COMBO_LABELS[pr]

        # Define widths for comboboxes.
        for pr in self.COMBO_PARAMS + self.QQ_DEPTH_CONTROLS:
            self.CONFIG_DEF[pr]['width'] = PromptConfig.COMBO_WIDTH_OTHER
            if pr in ['default_ns', 'default_ew']:
                self.CONFIG_DEF[pr]['width'] = PromptConfig.COMBO_WIDTH_NSEW

        # --------------------------------------------------------------
        self.MAIN_ROW = 0

        # --------------------------------------------------------------
        # Parameters set via Comboboxes

        # A frame for NS, EW, and Layout comboboxes and labels
        combo_frame = tk.Frame(self)
        combo_frame.grid(row=self.MAIN_ROW, column=1, sticky='nwe')
        self.MAIN_ROW += 1
        # This dict will be keyed by attribute name, and its values will
        # be the corresponding Combobox.
        self.combos = {}
        self.COMBO_FRAME_ROW = 0

        for pr in self.COMBO_PARAMS:
            if pr not in parameters:
                continue
            self.ConfigComboGen(
                master=combo_frame,
                top_owner=self,
                attribute=pr,
                values=self.CONFIG_DEF[pr]['values'],
                label_txt=self.CONFIG_DEF[pr]['label_txt'],
                width=self.CONFIG_DEF[pr]['width']
            )

        # --------------------------------------------------------------
        # Parameters set via radiobuttons (i.e. RB_PARAMS)

        lbl = tk.Label(self, text='')
        lbl.grid(row=self.MAIN_ROW, column=1)
        self.MAIN_ROW += 1

        # Set a new tk.IntVar for each variable name --
        #   i.e. var_name 'clean_qq' -> `self.clean_qq_var`, storing a
        #   tk.IntVar; and set this tk.IntVar to the `self.CONFIG_DEF`
        #   dict for 'clean_qq' (etc.)
        for var_name in self.RB_PARAMS:
            new_var = tk.IntVar()
            setattr(self, f"{var_name}_var", new_var)
            self.CONFIG_DEF[var_name]['var'] = new_var

        for var_name in self.QQ_DEPTH_CONTROLS:
            new_var = tk.StringVar()
            setattr(self, f"{var_name}_var", new_var)
            self.CONFIG_DEF[var_name]['var'] = new_var

        # --------------------------------------------------------------
        # Generate radiobuttons for the remaining parameters
        pr = self.RadioSetter(self, writing_header=True)
        pr.grid(row=self.MAIN_ROW, column=1, sticky='w')
        self.MAIN_ROW += 1
        for cf in parameters:
            if cf not in self.RB_PARAMS:
                continue
            pr = self.RadioSetter(
                self, parameter=cf, target_var=self.CONFIG_DEF[cf]['var'])
            pr.grid(row=self.MAIN_ROW, column=1, sticky='w')

            self.MAIN_ROW += 1

        # Set defaults for all of the parameters
        self.set_defaults()

        # --------------------------------------------------------------
        # Controls

        control_frame = tk.Frame(self)
        control_frame.grid(row=self.MAIN_ROW, column=1, sticky='s')
        self.MAIN_ROW += 1
        CTRL_BTN_INNER_PADY = 5
        CTRL_BTN_INNER_PADX = 5
        CTRL_PADY = 10
        CTRL_COL_PADX = 20

        control_dict = {
            'default': {
                'text': 'Reset to Defaults',
                'function': self.set_defaults
            },
            'cancel': {
                'text': cancel_button_text,
                'function': self.cancel_clicked
            },
            'ok': {
                'text': ok_button_text,
                'function': self.ok_clicked
            }
        }

        buttons_needed = ['default']
        if show_ok:
            buttons_needed.append('ok')
        if show_ok:
            buttons_needed.append('cancel')

        ctrl_col = 0
        for btn in buttons_needed:
            button = tk.Button(
                control_frame,
                text=control_dict[btn]['text'],
                command=control_dict[btn]['function'],
                padx=CTRL_BTN_INNER_PADX,
                pady=CTRL_BTN_INNER_PADY)
            button.grid(
                column=ctrl_col,
                row=0,
                padx=CTRL_COL_PADX,
                pady=CTRL_PADY)
            ctrl_col += 1

    def set_defaults(self):
        """Set or reset all config variables to their defaults."""
        for var_name in self.RB_PARAMS:
            # Pull the tk.IntVar associated with this var_name, and set to -1
            tkintvar = getattr(self, f"{var_name}_var")
            tkintvar.set(-1)
        for combo in self.combos.values():
            combo.current(0)

    def cf_help_clicked(self, attrib):
        tk.messagebox.showinfo(attrib, self.CONFIG_DEF[attrib]['help'])

    class RadioSetter(tk.Frame):
        """
        A sub-widget for setting a config parameter with 3 radiobuttons.
        """

        RB_COL_WIDTH = 5

        def __init__(
                self,
                master=None,
                writing_header=False,
                parameter=None,
                target_var=None,
                **kw):
            tk.Frame.__init__(self, master, **kw)
            self.master = master

            if writing_header:
                # If `writing_header`, will only write these:
                rlabel_1 = tk.Label(self, text='Off', width=self.RB_COL_WIDTH)
                rlabel_2 = tk.Label(self, text='Default', width=self.RB_COL_WIDTH)
                rlabel_3 = tk.Label(self, text='On', width=self.RB_COL_WIDTH)
                rlabel_1.grid(column=1, row=0, sticky='w')
                rlabel_2.grid(column=2, row=0, sticky='w')
                rlabel_3.grid(column=3, row=0, sticky='w')
                return

            for i in range(1, 4):
                lbl = tk.Label(self, width=self.RB_COL_WIDTH)
                lbl.grid(column=i, row=0)

            cb = tk.Radiobutton(self, value=0, variable=target_var)
            cb.grid(column=1, row=0, sticky='n')
            cb = tk.Radiobutton(self, value=-1, variable=target_var)
            cb.grid(column=2, row=0, sticky='n')
            cb = tk.Radiobutton(self, value=1, variable=target_var)
            cb.grid(column=3, row=0, sticky='n')

            help_btn = tk.Button(
                self, text='?', padx=5,
                command=lambda: self.master.cf_help_clicked(parameter))
            help_btn.grid(column=4, row=0)

            lbl = tk.Label(self, text=parameter)
            lbl.grid(column=5, row=0)

    @staticmethod
    def warn_deep_depths(num):
        """
        Warn the user that parsing QQ's to depths > 5 or so might result
        in very slow computing times.
        :param num:
        :return:
        """
        msg = (
            "WARNING: Parsing QQ's to a minimum (or exact) depth greater "
            "than 5 is possible but is likely to take a long time to "
            "process.\n\n"
            f"Do you want to proceed with setting it to {num}?"
        )
        return messagebox.askokcancel("WARNING", msg)

    def compile_config_text(self):
        """
        Compile and return the config text. (Returns None if cancelled.)
        """
        param_vals = []

        if 'default_ns' in self.parameters:
            ns = self.combos['default_ns'].get().lower()
            if ns.startswith(MasterConfig._LEGAL_NS):
                param_vals.append(ns[0])

        if 'default_ew' in self.parameters:
            ew = self.combos['default_ew'].get().lower()
            if ew.startswith(MasterConfig._LEGAL_EW):
                param_vals.append(ew[0])

        if 'layout' in self.parameters:
            layout = self.combos['layout'].get()
            if layout in IMPLEMENTED_LAYOUTS:
                param_vals.append(layout)

        # Check each of the requested variables. If not default (i.e. -1),
        # then append the parameter+value.
        for param in set(self.RB_PARAMS).intersection(set(self.parameters)):
            val = self.CONFIG_DEF[param]['var'].get()
            if val != -1:
                param_vals.append(f"{param}.{bool(val)}")

        # Setting qq_depth or qq_depth_min to larger than this will
        # prompt a warning. We may want to abort after qq depth warning;
        # we'll track that with `proceed`.
        QQ_DEPTH_WARN_THRESHOLD = 6
        proceed = True
        for param in self.QQ_DEPTH_CONTROLS:
            if param not in self.parameters:
                continue
            try:
                # We only want the first part (before the first space, if any).
                val = self.combos[param].get()
                val = val.split(" ")[0]
                val = int(val)
            except ValueError:
                val = None
            if val is not None:
                param_vals.append(f"{param}.{val}")
            if (val is not None
                    and param in ["qq_depth", "qq_depth_min"]
                    and val >= QQ_DEPTH_WARN_THRESHOLD):
                proceed = self.warn_deep_depths(val)
            if param == "qq_depth" and val is not None:
                # if qq_depth was set, we don't want to pull the
                # _min and _max, so break out of the loop
                break

        # Join the list of param/vals into a string, and return it
        config_text = ','.join(param_vals)
        if not proceed:
            return None
        return config_text

    def ok_clicked(self):
        """
        Compile the config text, and set it to the target config
        variable. Show the configured prompt_after_ok message (if any),
        and destroy the window (if so configured).
        """

        config_text = self.compile_config_text()
        if config_text is None:
            return None

        # Set the target tk.StringVar to the compiled config_text
        self.target_var.set(config_text)
        self.external_var_dict['config_text'] = config_text

        if self.prompt_after_ok is not None:
            messagebox.showinfo('', self.prompt_after_ok)

        if self.exit_after_ok:
            self.master.destroy()

    def cancel_clicked(self):
        """
        Set it to the target config variable to 'CANCEL'. Show
        configured confirm_cancel_prompt message (if any),
        and destroy the window (if so configured).
        """
        confirm = True
        if self.confirm_cancel_prompt is not None:
            confirm = messagebox.askyesno('Cancel?', self.confirm_cancel_prompt)
        if confirm:
            self.target_var.set('CANCEL')
            self.external_var_dict['config_text'] = 'CANCEL'
            self.master.destroy()

    class ConfigComboGen:
        """Generate a Combobox and associated buttons / labels."""
        def __init__(
                self,
                master: tk.Frame = None,
                top_owner=None,
                attribute: str = None,
                values: tuple = None,
                label_txt: str = None,
                width: int = None,
                **kw):
            """
            :param master: The frame holding this Combobox etc.
            :param top_owner: The PromptConfig object.
            :param attribute: The name of the attribute being controlled
            by this Combobox.
            :param values: A tuple of the optional values to choose
            from.
            :param label_txt: The label next to the Combobox.
            :param width: Width of the Combobox.
            :param kw: kwargs to pass through to the Combobox.
            """

            row = top_owner.COMBO_FRAME_ROW
            top_owner.COMBO_FRAME_ROW += 1

            lbl = tk.Label(master, text=label_txt)
            help_button = tk.Button(
                master, text='?', padx=5,
                command=lambda: top_owner.cf_help_clicked(attribute))
            self.combo = Combobox(master, width=width, **kw)
            self.combo['values'] = values
            lbl.grid(column=1, row=row, sticky='e')
            help_button.grid(column=2, row=row)
            self.combo.grid(column=3, row=row, sticky='w')
            top_owner.combos[attribute] = self.combo
