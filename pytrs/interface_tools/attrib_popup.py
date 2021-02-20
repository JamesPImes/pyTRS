# Copyright (c) 2020, James P. Imes, all rights reserved

"""
A GUI app for choosing pyTRS Tract attributes.
A PromptAttrib object can be used directly in a tkinter application; or
the prompt_attrib() function can be used to hold up the program while
the user makes their choices, and then continue when it returns.
"""

import tkinter as tk
from tkinter import messagebox
from tkinter.ttk import Checkbutton

def prompt_attrib(
        attribs='all', header='Desired Tract Attributes', show_ok=True,
        show_cancel=True, ok_button_text='Confirm Attributes',
        cancel_button_text='Cancel', confirm_cancel_prompt=None,
        prompt_after_ok=None):
    """
    Launch a PromptAttrib tkinter frame, for the user to choose from
    pyTRS.Tract instance attributes. Will wait for the PromptAttrib
    window to close, and then will return the chosen attribute names
    as a list of strings.

    All parameters have the same effect as they do in __init__() for a
    PromptConfig object, although not all parameters are available in
    this function.
    :param attribs:
    :param header:
    :param show_ok:
    :param show_cancel:
    :param ok_button_text:
    :param cancel_button_text:
    :param confirm_cancel_prompt:
    :param prompt_after_ok:
    :return: Returns a list of the attribute names that were chosen
    (i.e. a list of strings).
    """
    """
    Prompt the user for which attributes they would like for PLSSDesc
    and/or Tract objects.

    :param attribs: Which attributes to allow the user to select from;
        may be entered as a list, or as a string with attributes
        separated by commas (defaults to 'all')
    :param at_window: Optional; used when embedded in another tkinter
        app. This specifies the frame or window it should appear in. If
        None, will launch as a new window.
    :param main_window: If embedded in another tkinter app, this
        specifies the window whose variable it should be saved in.
        Access the compiled attribute text with
        <main_window>.getvar(name='attrib_list'). If None, will default
        to be same as `at_window`.
    :param row: Starting at which row in `at_window` should the
        checkbuttons be placed.
    :param column: In which column in `at_window` should the checkbuttons
        be placed.
    :param header: Text to be placed above the attribute options.
    :param show_ok: Show the OK button.
    :param show_cancel: Show the Cancel button.
    :param ok_button_text: Specify the text in the OK button.
    :param cancel_button_text: Specify the text in the Cancel button.
    :param exit_after_ok: Close the `at_window` after 'OK' is run.
    :param after_prompt: Text to prompt the user with after 'OK' is run.
    :param as_list: Return the attributes in a list of attribute names
        (only allowed if running as its own window.)
    :return: The compiled list of user-requested attributes, as a single
        string, separated by comma and no spaces. (May return as a list
        with `as_list=True`)
    """

    attrib_holder = {'attrib_list': ''}

    popup = PromptAttrib(
        master=None, target_config_var=None, attribs=attribs, header=header,
        show_ok=show_ok, show_cancel=show_cancel,
        prompt_after_ok=prompt_after_ok, cancel_button_text=cancel_button_text,
        ok_button_text=ok_button_text, exit_after_ok=True,
        external_target_var=attrib_holder,
        confirm_cancel_prompt=confirm_cancel_prompt)
    popup.master.mainloop()
    return attrib_holder['attrib_list']


class PromptAttrib(tk.Frame):
    """
    A tkinter frame for configuring which attributes should be
    returned from parsed PLSSDesc and/or Tract objects.
    """

    # A dict of standard Tract object attributes that can be requested by
    # the user -- keyed by attribute name, with values of a list containing
    # [0] short description, and [1] default value.
    STOCK_ATTRIBS = {
        'trs': ["TRS (Township-Range-Section joined)", 1],
        'twp': ['Township', 0],
        'rge': ['Range', 0],
        'sec': ['Section', 0],
        'desc': ['Description Block', 1],
        'pp_desc': ['Preprocessed (cleaner) description block', 0],
        'lots': ['Lots', 0],
        'qqs': ['Aliquot quarter-quarters (QQs)', 0],
        'lots_qqs': ['Lots and Aliquot quarter-quarters (QQs)', 1],
        'w_flags': ['Warning flags', 1],
        'w_flag_lines': ['Warning flag lines', 0],
        'e_flags': ['Error flags', 1],
        'e_flag_lines': ['Error flag lines', 0]
    }

    def __init__(
            self, master=None, attribs='all', target_attrib_var=None,
            header='Desired Tract Attributes', show_ok=True,
            show_cancel=True, ok_button_text='Confirm Attributes',
            cancel_button_text='Cancel', confirm_cancel_prompt=None,
            exit_after_ok=True, prompt_after_ok=None, external_target_var=None,
            **kw):
        """
        :param master: The tkinter master (same as for tkinter.Frame)
        :param target_attrib_var: A tk.StringVar to which the chosen
        attributes should be stored when the OK button is clicked.
        Stored as a single string, with attribute names separated by
        a comma and no spaces.
        :param attribs: Which attributes to allow the user to select
        from; may be passed as a list, or as a string with attributes
        separated by commas (defaults to 'all')
        :param header: Text to be placed above the attribute options.
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
        `target_attrib_var` to the string 'CANCEL' and close the window.
        :param confirm_cancel_prompt: A string to display in a
        yes/no messagebox when the Cancel button is clicked. Defaults
        to None.
        :param external_target_var: A dict with the key 'attrib_list',
        to which the chosen attributes should be set (as a list of
        strings). (Used if this PromptAttrib object is NOT being
        incorporated into a tkinter app, since a dict can exist outside
        of tkinter, whereas a tk.StringVar cannot.)
        :param kw: Kwargs to pass through to tkinter.Frame at init.
        """

        default_master = False
        if master is None:
            default_master = True
            master = tk.Tk()
            master.title('Select pyTRS Tract Attributes')

        tk.Frame.__init__(self, master, **kw)
        self.master = master
        if default_master:
            self.pack(padx=20, pady=20)

        if target_attrib_var is None:
            target_attrib_var = tk.StringVar()
        self.target_attrib_var = target_attrib_var

        if external_target_var is None:
            external_target_var = {'attrib_list': []}
        self.external_target_var = external_target_var

        self.show_ok = show_ok
        self.show_cancel = show_cancel
        self.prompt_after_ok = prompt_after_ok
        self.exit_after_ok = exit_after_ok
        self.confirm_cancel_prompt = confirm_cancel_prompt

        if attribs.lower() == 'all':
            attribs = list(PromptAttrib.STOCK_ATTRIBS.keys())

        if isinstance(attribs, str):
            attribs = attribs.replace(' ', '').split(',')

        if header is not None:
            try:
                hdr = tk.Label(self, text=header, font='"Arial Black"')
            except:
                hdr = tk.Label(self, text=header)
            hdr.grid(row=0, column=0, sticky='n')

        # Generate a new IntVar for each available attribute option, set
        # its value to the default value per STOCK_ATTRIBS, store it as
        # an instance variable, and also set it to the attrib_dict.
        # Finally, create a checkbutton for that attribute.
        # So for attribute 'qqs':
        #   -> self.QQListVar --> a tk.IntVar with initial value 0
        #   -> self.attrib_dict['qqs'] --> self.QQListVar
        #   -> <create a checkbutton for qqs>
        self.attrib_dict = dict()
        cur_row = 5
        for att in attribs:
            new_var = tk.IntVar()
            new_var.set(PromptAttrib.STOCK_ATTRIBS[att][1])
            setattr(self, att + 'Var', new_var)
            self.attrib_dict[att] = new_var
            cb = Checkbutton(
                self, text=PromptAttrib.STOCK_ATTRIBS[att][0],
                var=self.attrib_dict[att])
            cb.grid(row=cur_row, column=0, sticky='w', pady=2)
            cur_row += 1

        ctrl_frame = tk.Frame(self)
        ctrl_frame.grid(row=cur_row, column=0, padx=10, pady=10)

        if show_ok:
            ok_btn = tk.Button(
                ctrl_frame, text=ok_button_text, command=self.ok_clicked)
            ok_btn.grid(row=0, column=1, sticky='e', padx=20, pady=10)

        if show_cancel:
            cancel_btn = tk.Button(
                ctrl_frame, text=cancel_button_text,
                command=self.cancel_clicked)
            cancel_btn.grid(row=0, column=0, sticky='e', padx=20, pady=10)

    def compile_attributes(self):
        """
        Compile a list of chosen attributes (a list of strings).
        """
        chosen_attribs = []
        for att, var in self.attrib_dict.items():
            if var.get() == 1:
                chosen_attribs.append(att)
        return chosen_attribs

    def ok_clicked(self):
        selected_attribs = self.compile_attributes()
        self.target_attrib_var.set(','.join(selected_attribs))
        self.external_target_var['attrib_list'] = selected_attribs

        if self.prompt_after_ok is not None:
            messagebox.showinfo('', self.prompt_after_ok)

        if self.exit_after_ok:
            self.master.destroy()

    def cancel_clicked(self):
        confirm = True
        if self.confirm_cancel_prompt is not None:
            confirm = messagebox.askyesno(
                'Cancel?', self.confirm_cancel_prompt)
        if confirm:
            self.target_attrib_var.set('CANCEL')
            self.external_target_var['attrib_list'] = ['CANCEL']
            self.master.destroy()


if __name__ == '__main__':
    # If run on its own, won't really serve much purpose, but it will
    # pop up and show the default attributes.
    pa = PromptAttrib()
    pa.master.mainloop()
