# Copyright (c) 2020, James P. Imes, all rights reserved

"""
A GUI app for choosing Config parameters for pyTRS parsing;
results can be returned as text parameters (a string) or as a compiled
pytrs.Config object.
A PromptConfig object can be used directly in a tkinter application; or
the prompt_config() function can be used to hold up the program while
the user makes their choices, and then continue when it returns.
"""

# Note: If `show_ok==True` and `exit_after_ok==True`, then the
# `prompt_config()` function can function as a 'go button' for a parsing
# application: It will wait for the user to hit 'OK', then close the
# window and return the config parameters to the program that called the
# function. It may be useful to specify the parameter
# `ok_button_text=<'string'>` with the appropriate context for how the
# function is incorporated into your program.

import tkinter as tk
from tkinter import messagebox
from tkinter.ttk import Combobox
from pytrs import parser


def prompt_config(
        parameters='all', show_ok=True, show_cancel=False,
        prompt_after_ok=None, ok_button_text='Confirm Config Parameters',
        cancel_button_text='Cancel', confirm_cancel_prompt=None):
    """
    Launch a PromptConfig tkinter frame, for the user to set config
    parameters. Will wait for the PromptConfig window to close, and then
    will return the config parameters as a string.

    IMPORTANT: If allowing the user to see the Cancel button, be aware
    that clicking Cancel will return the string 'CANCEL'.

    All parameters have the same effect as they do in __init__() for a
    PromptAttrib object, although not all parameters are available in
    this function.
    :param parameters:
    :param show_ok:
    :param show_cancel:
    :param prompt_after_ok:
    :param ok_button_text:
    :param cancel_button_text:
    :param confirm_cancel_prompt:
    :return: A string of the user's chosen config parameters.
    """

    config_holder = {'config_text': ''}

    popup = PromptConfig(
        master=None, target_config_var=None, parameters=parameters,
        show_ok=show_ok, show_cancel=show_cancel,
        prompt_after_ok=prompt_after_ok, cancel_button_text=cancel_button_text,
        ok_button_text=ok_button_text, exit_after_ok=True,
        external_target_var=config_holder,
        confirm_cancel_prompt=confirm_cancel_prompt)
    popup.master.mainloop()
    return config_holder['config_text']


class PromptConfig(tk.Frame):
    """A tkinter frame for configuring pyTRS parsing parameters (i.e.
    pytrs.Config objects)."""

    # Parameters that are set via radiobuttons:
    RB_PARAMS = [
        'clean_qq', 'include_lot_divs', 'require_colon', 'ocr_scrub', 'segment',
        'init_preprocess', 'wait_to_parse', 'parse_qq', 'break_halves'
    ]

    # Parameters that are set to a number and control how deeply to
    # parse QQ's.
    # NOTE: "qq_depth" should be first in this list, so that it takes
    # priority over qq_depth_min and _max when compiling the config text.
    QQ_DEPTH_CONTROLS = ['qq_depth', 'qq_depth_min', 'qq_depth_max']

    def __init__(
            self, master=None, target_config_var=None, parameters='all',
            show_ok=True, show_cancel=False,
            prompt_after_ok=None, exit_after_ok=True, external_target_var=None,
            ok_button_text='Confirm Config Parameters',
            cancel_button_text='Cancel', confirm_cancel_prompt=None, **kw):
        """
        A tkinter Frame for setting pyTRS config parameters.
        IMPORTANT: If the Cancel button (or the OK button, if parameter
        `exit_after_ok=True` is used at init) is used, it will destroy
        `master`, and not just `self`.

        :param master: The tkinter master (same as for tkinter.Frame)
        :param target_config_var: A tk.StringVar to which Config data
        should be stored when the OK button is clicked.
        :param parameters: A list or string containing the parameters
        that should be available to the user. If `parameters='all'`,
        will display all possible parameters. If passed as a string,
        parameter names should be separate by a comma and no spaces.
        Note: default_ns and default_ew are always on.
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
        `target_config_var` to the string 'CANCEL' and close the window.
        :param confirm_cancel_prompt: A string to display in a
        yes/no messagebox when the Cancel button is clicked. Defaults
        to None.
        :param external_target_var: A dict with the key 'config_text',
        to which the compiled config parameters should be set. (Used if
        this PromptConfig object is NOT being incorporated into a
        tkinter app, since a dict can exist outside of tkinter, whereas
        a tk.StringVar cannot.)
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

        if target_config_var is None:
            target_config_var = tk.StringVar()
        self.target_config_var = target_config_var
        
        # Determine which parameters the user is allowed to set:
        if parameters is None:
            parameters = 'all'
        
        if isinstance(parameters, str):
            if parameters.lower() == 'all':
                parameters = list(parser.Config._CONFIG_ATTRIBUTES)
            else:
                parameters = parameters.replace(' ', '').split(',')

        if external_target_var is None:
            external_target_var = {'config_text': ''}
        self.external_target_var = external_target_var

        self.parameters = parameters

        self.show_ok = show_ok
        self.show_cancel = show_cancel
        self.prompt_after_ok = prompt_after_ok
        self.exit_after_ok = exit_after_ok
        self.ok_button_text = ok_button_text
        self.cancel_button_text = cancel_button_text
        self.confirm_cancel_prompt = confirm_cancel_prompt

        # A dict of the possible config variables, with nested dicts for
        # respective variable and help text (variables are set later)
        self.CONFIG_DEF = {
            'default_ns':
                {'help': (
                    "If the dataset contains a Township whose N/S "
                    "direction was not specified, the program will assume "
                    "this specified direction. (And if not specified here, "
                    "will assumed North.)"
                )},

            'default_ew':
                {'help': (
                    "If the dataset contains a Range whose E/W direction "
                    "was not specified, the program will assume this "
                    "specified direction. (And if not specified here, "
                    "will assumed West.)"
                )},

            'layout':
                {'help': (
                    "If you know that the dataset is all laid out in the "
                    "same format, you may get more accurate results if "
                    "you force parsing according to one of these formats. "
                    "However, if there are multiple layouts, or unknown "
                    "layouts, it is probably wise to let the program "
                    "deduce the layout for each.\n\n"
                    "Below are examples of the possible layouts:\n\n"
                    f"{parser.IMPLEMENTED_LAYOUT_EXAMPLES}"
                )},

            'clean_qq':
                {'help': (
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
                )},

            'include_lot_divs':
                {'help': (
                    "If parsing lots, report any divisions of lots. For "
                    "example, if True, 'N/2 of Lot 1' would be reported "
                    "as 'N2 of L1'. If this is turned off, it would be "
                    "reported as 'L1'.\n\n"
                    "Default: on (`True`)"
                )},

            'require_colon':
                {'help': (
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
                )},

            'ocr_scrub':
                {'help': (
                    "Attempt to iron out common OCR artifacts in a "
                    "PLSSDesc object or Tract object (e.g., 'TIS4N-R97W' "
                    "that should have been 'T154N-R97W'). (WARNING: may "
                    "cause other issues.)\n\n"
                    "Default: off (`False`)."
                )},

            'segment':
                {'help': (
                    "While parsing, segment each description by T&R "
                    "before identifying tracts, which MIGHT capture SOME "
                    "descriptions whose layout changes partway through. "
                    "(However, this cannot capture ALL changes in "
                    "layouts.)\n\n"
                    "Default: off (`False`)"
                )},

            'init_preprocess':
                {'help': (
                    "Preprocess PLSS descriptions and Tracts upon "
                    "initialization.\n\n"
                    "Default: on (`True`)"
                )},

            'wait_to_parse':
                {'help': (
                    "Wait to parse PLSS descriptions upon initialization, "
                    "rather than doing it automatically.\n\n"
                    "Default: off (`False` -- i.e. do parse by default)"
                )},

            'parse_qq':
                {'help': (
                    "Parse Tracts into lots and QQ's upon initialization. "
                    "(If used with a PLSS description, its resulting Tracts "
                    "will be parsed into lots/QQs.)\n\n"
                    "Default: off (`False`)"
                )},

            'qq_depth_min':
                {
                    'help': (
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
                    'options': (
                        "[Default: 2 -> QQ's]", '1 (quarter sections)',
                        '2 (QQs)', '3', '4', '5'
                    ),
                    'default_index': 1
                 },

            'qq_depth_max':
                {
                    'help': (
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
                    'options': (
                        '[Default - no max]', '1 (quarter sections)',
                        '2 (QQs)', '3', '4', '5'),
                    'default_index': 0
                },

            'qq_depth':
                {
                    'help': (
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
                    'options': (
                        '[Default - use min and max]',
                        '1 (quarter sections)',
                        '2 (QQs)', '3', '4', '5'
                    ),
                    'default_index': 0
                },

            'break_halves':
                {'help': (
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
                )}
        }

        # --------------------------------------------------------------
        # A frame for NS, EW, and Layout comboboxes and labels
        self.combos = []
        combo_frame = tk.Frame(self)
        combo_frame.grid(row=0, column=1, sticky='nwe')

        combo_frame_row = 0

        # Prompt for default N/S
        defaultNSPrompt = tk.Label(
            combo_frame,
            text="Default unspecified Townships to [North] or [South]?")
        defaultNShbtn = tk.Button(
            combo_frame, text='?', padx=5,
            command=lambda: self.cf_help_clicked('default_ns'))
        self.defaultNScombo = Combobox(combo_frame, width=16)
        self.defaultNScombo['values'] = ('[default: North]', 'North', 'South')
        defaultNSPrompt.grid(column=1, row=combo_frame_row, sticky='e')
        defaultNShbtn.grid(column=2, row=combo_frame_row)
        self.defaultNScombo.grid(column=3, row=combo_frame_row, sticky='w')
        self.combos.append(self.defaultNScombo)
        combo_frame_row += 1

        # Prompt for default E/W
        defaultEWPrompt = tk.Label(
            combo_frame, text="Default unspecified Ranges to [West] or [East]?")
        defaultEWPrompt.grid(column=1, row=combo_frame_row, sticky='e')
        defaultEWhbtn = tk.Button(
            combo_frame, text='?', padx=5,
            command=lambda: self.cf_help_clicked('default_ew'))
        defaultEWhbtn.grid(column=2, row=combo_frame_row)
        self.defaultEWcombo = Combobox(combo_frame, width=16)
        self.defaultEWcombo['values'] = ('[default: West]', 'West', 'East')
        self.defaultEWcombo.grid(column=3, row=combo_frame_row, sticky='w')
        self.combos.append(self.defaultEWcombo)
        combo_frame_row += 1
    
        # Prompt for layout
        self.layoutcombo = Combobox(combo_frame, width=25)
        self.layoutcombo['values'] = tuple(
            ['Deduce (RECOMMENDED)'] + list(parser.IMPLEMENTED_LAYOUTS))
        self.combos.append(self.layoutcombo)
    
        if 'layout' in parameters:
            # Only put layout into GUI if it's among the requested parameters
            layoutPrompt = tk.Label(
                combo_frame, text="Force parsing as a particular layout?")
            layoutPrompt.grid(column=1, row=combo_frame_row, sticky='e')
            layouthbtn = tk.Button(
                combo_frame, text='?', padx=5,
                command=lambda: self.cf_help_clicked('layout'))
            layouthbtn.grid(column=2, row=combo_frame_row)
            self.layoutcombo.grid(column=3, row=combo_frame_row, sticky='w')
        combo_frame_row += 1

        # --------------------------------------------------------------
        # Parameters set via radiobuttons (i.e. RB_PARAMS)
        cur_row = 11

        lbl = tk.Label(self, text='')
        lbl.grid(row=cur_row, column=1)
        cur_row += 1

        # Set a new tk.IntVar for each variable name --
        #   i.e. var_name 'clean_qq' -> `self.clean_qq_var`, storing a tk.IntVar;
        #   and set this tk.IntVar to the `self.CONFIG_DEF` dict for 'clean_qq'
        #   (etc.)
        for var_name in self.RB_PARAMS:
            new_var = tk.IntVar()
            setattr(self, var_name + 'Var', new_var)
            self.CONFIG_DEF[var_name]['var'] = new_var

        for var_name in self.QQ_DEPTH_CONTROLS:
            new_var = tk.StringVar()
            setattr(self, var_name + 'Var', new_var)
            self.CONFIG_DEF[var_name]['var'] = new_var

        # Prompt for qq_depth_min
        qq_depth_minPrompt = tk.Label(
            combo_frame, text="MINIMUM depth to parse QQs")
        qq_depth_minhbtn = tk.Button(
            combo_frame, text='?', padx=5,
            command=lambda: self.cf_help_clicked('qq_depth_min'))
        self.qq_depth_mincombo = Combobox(combo_frame, width=25)
        self.qq_depth_mincombo['values'] = self.CONFIG_DEF["qq_depth_min"]["options"]
        self.combos.append(self.qq_depth_mincombo)
        self.CONFIG_DEF["qq_depth_min"]["combo"] = self.qq_depth_mincombo
        if "qq_depth_min" in self.parameters:
            qq_depth_minPrompt.grid(column=1, row=combo_frame_row, sticky='e')
            qq_depth_minhbtn.grid(column=2, row=combo_frame_row)
            self.qq_depth_mincombo.grid(column=3, row=combo_frame_row, sticky='w')
            combo_frame_row += 1

        # Prompt for qq_depth_max
        qq_depth_maxPrompt = tk.Label(
            combo_frame, text="MAXIMUM depth to parse QQs")
        qq_depth_maxhbtn = tk.Button(
            combo_frame, text='?', padx=5,
            command=lambda: self.cf_help_clicked('qq_depth_max'))
        self.qq_depth_maxcombo = Combobox(combo_frame, width=25)
        self.qq_depth_maxcombo['values'] = self.CONFIG_DEF["qq_depth_max"]["options"]
        self.combos.append(self.qq_depth_maxcombo)
        self.CONFIG_DEF["qq_depth_max"]["combo"] = self.qq_depth_maxcombo
        if "qq_depth_max" in self.parameters:
            qq_depth_maxPrompt.grid(column=1, row=combo_frame_row, sticky='e')
            qq_depth_maxhbtn.grid(column=2, row=combo_frame_row)
            self.qq_depth_maxcombo.grid(column=3, row=combo_frame_row, sticky='w')
            combo_frame_row += 1

        # Prompt for qq_depth
        qq_depthPrompt = tk.Label(
            combo_frame,
            text="EXACT depth to parse QQs (override min and max)")
        qq_depthhbtn = tk.Button(
            combo_frame, text='?', padx=5,
            command=lambda: self.cf_help_clicked('qq_depth'))
        self.qq_depthcombo = Combobox(combo_frame, width=25)
        self.qq_depthcombo['values'] = self.CONFIG_DEF["qq_depth"]["options"]
        self.combos.append(self.qq_depthcombo)
        self.CONFIG_DEF["qq_depth"]["combo"] = self.qq_depthcombo
        if "qq_depth" in self.parameters:
            qq_depthPrompt.grid(column=1, row=combo_frame_row, sticky='e')
            qq_depthhbtn.grid(column=2, row=combo_frame_row)
            self.qq_depthcombo.grid(column=3, row=combo_frame_row, sticky='w')
            combo_frame_row += 1

        # Generate radiobuttons for the remaining parameters
        pr = self.RadioSetter(self, writing_header=True)
        pr.grid(row=cur_row, column=1, sticky='w')
        cur_row += 1
        for cf in parameters:
            if cf not in self.RB_PARAMS:
                continue
            pr = self.RadioSetter(
                self, parameter=cf, target_var=self.CONFIG_DEF[cf]['var'])
            pr.grid(row=cur_row, column=1, sticky='w')

            cur_row += 1

        # Set defaults for all of the parameters
        self.set_defaults()

        # --------------------------------------------------------------
        # Controls

        control_frame = tk.Frame(self)
        control_frame.grid(row=cur_row, column=1, sticky='s')
        ctrl_col = 0
        CTRL_BTN_INNER_PADY = 5
        CTRL_BTN_INNER_PADX = 5
        CTRL_PADY = 10
        CTRL_COL_PADX = 20

        defaultButton = tk.Button(
            control_frame, text='Reset to Defaults', command=self.set_defaults,
            padx=CTRL_BTN_INNER_PADX, pady=CTRL_BTN_INNER_PADY)
        defaultButton.grid(
            column=ctrl_col, row=0, padx=CTRL_COL_PADX, pady=CTRL_PADY)
        ctrl_col += 1

        if show_cancel:
            cancelButton = tk.Button(
                control_frame, text=cancel_button_text,
                command=self.cancel_clicked,
                padx=CTRL_BTN_INNER_PADX, pady=CTRL_BTN_INNER_PADY)
            cancelButton.grid(
                column=ctrl_col, row=0, padx=CTRL_COL_PADX, pady=CTRL_PADY)
            ctrl_col += 1

        if show_ok:
            compileButton = tk.Button(
                control_frame, text=ok_button_text,
                command=self.ok_clicked,
                padx=CTRL_BTN_INNER_PADX, pady=CTRL_BTN_INNER_PADY)
            compileButton.grid(
                column=ctrl_col, row=0, padx=CTRL_COL_PADX, pady=CTRL_PADY)
            ctrl_col += 1

    def set_defaults(self):
        """Set or reset all config variables to their defaults."""
        for var_name in self.RB_PARAMS:
            # Pull the tk.IntVar associated with this var_name, and set to -1
            tkintvar = getattr(self, var_name + 'Var')
            tkintvar.set(-1)
        for combo in self.combos:
            combo.current(0)
            combo.current(0)
            combo.current(0)

    def cf_help_clicked(self, attrib):
        tk.messagebox.showinfo(attrib, self.CONFIG_DEF[attrib]['help'])

    class RadioSetter(tk.Frame):
        """
        A sub-widget for setting a config parameter with 3 radiobuttons.
        """

        RB_COL_WIDTH = 5

        def __init__(self, master=None, writing_header=False, parameter=None,
                     target_var=None, **kw):
            tk.Frame.__init__(self, master, **kw)
            self.master = master

            if writing_header:
                # If `writing_header`, will only write these:
                radLabel1 = tk.Label(self, text='Off', width=self.RB_COL_WIDTH)
                radLabel2 = tk.Label(self, text='Default', width=self.RB_COL_WIDTH)
                radLabel3 = tk.Label(self, text='On', width=self.RB_COL_WIDTH)
                radLabel1.grid(column=1, row=0, sticky='w')
                radLabel2.grid(column=2, row=0, sticky='w')
                radLabel3.grid(column=3, row=0, sticky='w')
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

    def compile_config_text(self) -> str:
        """
        Compile and return the config text.
        """
        param_vals = []
        
        ns = self.defaultNScombo.get()[0].lower()
        ew = self.defaultEWcombo.get()[0].lower()
        if ns in ['n', 's']:
            param_vals.append(ns)
        if ew in ['e', 'w']:
            param_vals.append(ew)

        # Setting qq_depth or qq_depth_min to larger than this will prompt
        # a warning.
        QQ_DEPTH_WARN_THRESHOLD = 6

        proceed = True

        if 'layout' in self.parameters:
            val = self.layoutcombo.get()
            if val in parser.IMPLEMENTED_LAYOUTS:
                param_vals.append(val)

        # Check each of the requested variables. If not default (i.e. -1),
        # then append the parameter+value.
        for param in set(self.RB_PARAMS).intersection(set(self.parameters)):
            val = self.CONFIG_DEF[param]['var'].get()
            if val != -1:
                param_vals.append(f"{param}.{bool(val)}")

        for param in [p for p in self.QQ_DEPTH_CONTROLS if p in self.parameters]:
            try:
                # We only want the first part (before the first space, if any).
                val = self.CONFIG_DEF[param]['combo'].get()
                val = val.split(" ")[0]
                val = int(val)
            except ValueError:
                val = None
            if val is not None:
                param_vals.append(f"{param}.{val}")
            if val is not None \
                    and param in ["qq_depth", "qq_depth_min"] \
                    and val >= QQ_DEPTH_WARN_THRESHOLD:
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
        self.target_config_var.set(config_text)
        self.external_target_var['config_text'] = config_text

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
            self.target_config_var.set('CANCEL')
            self.external_target_var['config_text'] = 'CANCEL'
            self.master.destroy()


if __name__ == '__main__':
    # If run on its own, won't serve much purpose, but...
    pc = PromptConfig(show_ok=True, show_cancel=True)
    pc.master.mainloop()
