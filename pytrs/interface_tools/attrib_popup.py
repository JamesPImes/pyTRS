# Copyright (c) 2020-2021, James P. Imes, all rights reserved

"""
A GUI app for choosing pytrs.Tract attributes.
A PromptAttrib object can be used directly in a tkinter application; or
the prompt_attrib() function can be used to hold up the program while
the user makes their choices, and then continue when it returns.
"""

import tkinter as tk
from tkinter import messagebox
from tkinter.ttk import Checkbutton
from pytrs import Tract


def prompt_attrib(
        attributes='standard',
        header='Desired Tract Attributes',
        show_ok=True,
        show_cancel=True,
        ok_button_text='Confirm Attributes',
        cancel_button_text='Cancel',
        confirm_cancel_prompt=None,
        prompt_after_ok=None):
    """
    Launch a PromptAttrib tkinter frame, for the user to choose from
    pytrs.Tract attributes. Will wait for the PromptAttrib window to
    close, and then will return the chosen attribute names as a list of
    strings.

    If the user hits the Cancel button, it will return as `['CANCEL']`.
    If the user exits the window, it will return as `['EXIT']`.

    All parameters have the same effect as they do in __init__() for a
    PromptAttrib object, although not all parameters are available in
    this function.

    :param attributes: Which attributes to allow the user to select
    from; may be passed as a list, or as a string with attributes
    separated by commas (defaults to 'standard')
    :param header: Text to be placed above the attribute options.
    :param show_ok: Include the OK button.
    :param ok_button_text: A string, for custom text for the OK
    button.
    :param prompt_after_ok: A string to display in a messagebox
    after the OK button has been clicked. Defaults to None.
    :param cancel_button_text: A string, for custom text for the
    Cancel button.
    :param show_cancel: Include the Cancel button.
    IMPORTANT: If the Cancel button is clicked, it will set the
    `target_var` to the string 'CANCEL' and close the window.
    :param confirm_cancel_prompt: A string to display in a
    yes/no messagebox when the Cancel button is clicked. Defaults
    to None.
    :return: Returns a list of the attribute names that were chosen
    (i.e. a list of strings).
    """

    attrib_holder = {'attrib_list': ['EXIT']}

    popup = PromptAttrib(
        master=None,
        target_var=None,
        attributes=attributes,
        header=header,
        show_ok=show_ok,
        show_cancel=show_cancel,
        prompt_after_ok=prompt_after_ok,
        cancel_button_text=cancel_button_text,
        ok_button_text=ok_button_text,
        exit_after_ok=True,
        external_var_dict=attrib_holder,
        confirm_cancel_prompt=confirm_cancel_prompt)
    popup.master.mainloop()
    return attrib_holder['attrib_list']


class PromptAttrib(tk.Frame):
    """
    A tkinter frame for configuring which attributes should be
    returned from parsed PLSSDesc and/or Tract objects.
    """

    # These will be options in the prompt.
    STANDARD_OPTIONS = [
        'trs',
        'twp',
        'rge',
        'twprge',
        'sec',
        'desc',
        'pp_desc',
        'lots',
        'qqs',
        'lots_qqs',
        'w_flags',
        'w_flag_lines',
        'e_flags',
        'e_flag_lines',
        'flags',
        'flag_lines',
    ]

    # These attributes will be turned on by default.
    DEFAULT_ON = [
        'trs',
        'desc',
        'lots',
        'qqs',
        'flags'
    ]

    # Construct a dict of standard Tract object attributes that can be
    # requested by the user -- keyed by attribute name, with values of a
    # list containing [0] short description, and [1] default value.
    # Use the 'header-like' values from the Tract.ATTRIBUTES dict as the
    # short description.
    STANDARD_ATTRIBUTES = {
        att: [Tract.ATTRIBUTES[att], 0] for att in STANDARD_OPTIONS
    }

    # And one for ALL of the attributes. (Turned on with `attributes='all'`)
    ALL_ATTRIBUTES = {
        att: [val, 0] for att, val in Tract.ATTRIBUTES.items()
    }

    # Turn on these attributes by default.
    for att in DEFAULT_ON:
        STANDARD_ATTRIBUTES[att][1] = 1
        ALL_ATTRIBUTES[att][1] = 1

    def __init__(
            self,
            master=None,
            attributes='standard',
            target_var=None,
            header='Desired Tract Attributes',
            show_ok=True,
            show_cancel=True,
            ok_button_text='Confirm Attributes',
            cancel_button_text='Cancel',
            confirm_cancel_prompt=None,
            exit_after_ok=True,
            prompt_after_ok=None,
            external_var_dict=None,
            **kw):
        """
        :param master: The tkinter master (same as for tkinter.Frame)
        :param target_var: A tk.StringVar to which the chosen
        attributes should be stored when the OK button is clicked.
        Stored as a single string, with attribute names separated by
        a comma and no spaces.
        :param attributes: Which attributes to allow the user to select
        from; may be passed as a list, or as a string with attributes
        separated by commas (defaults to 'standard')
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
        `target_var` to the string 'CANCEL' and close the window.
        :param confirm_cancel_prompt: A string to display in a
        yes/no messagebox when the Cancel button is clicked. Defaults
        to None.
        :param external_var_dict: A dict with the key 'attrib_list',
        to which the chosen attributes should be set (as a list of
        strings). (Only used by `prompt_attrib()` -- probably ignore
        this parameter.)
        :param kw: Kwargs to pass through to tkinter.Frame at init.
        """

        default_master = False
        if not master:
            default_master = True
            master = tk.Tk()
            master.title('Select pyTRS Tract Attributes')

        tk.Frame.__init__(self, master, **kw)
        self.master = master
        if default_master:
            self.pack(padx=20, pady=20)

        if not target_var:
            target_var = tk.StringVar()
        self.target_var = target_var

        if not external_var_dict:
            external_var_dict = {'attrib_list': []}
        self.external_var_dict = external_var_dict

        self.show_ok = show_ok
        self.show_cancel = show_cancel
        self.prompt_after_ok = prompt_after_ok
        self.exit_after_ok = exit_after_ok
        self.confirm_cancel_prompt = confirm_cancel_prompt

        if isinstance(attributes, str):
            if attributes.lower() == 'standard':
                attributes = PromptAttrib.STANDARD_OPTIONS
            elif attributes.lower() == 'all':
                attributes = PromptAttrib.ALL_ATTRIBUTES.keys()
            else:
                attributes = [at.lower().strip() for at in attributes.split(',')]

        if header:
            hdr = tk.Label(self, text=str(header), font='"Arial Black"')
            hdr.grid(row=0, column=0, sticky='n')

        # Generate a new IntVar for each available attribute option, set
        # its value to the default value per STANDARD_ATTRIBUTES, store
        # it as an instance variable, and also set it to the attrib_dict.
        # Finally, create a checkbutton for that attribute.
        # So for attribute 'qqs':
        #   -> self.qqs_var --> a tk.IntVar with initial value 0
        #   -> self.attrib_dict['qqs'] --> self.qqs_var
        #   -> <create a checkbutton for qqs>
        self.attrib_dict = dict()
        cur_row = 5
        for att in attributes:
            new_var = tk.IntVar()
            new_var.set(PromptAttrib.ALL_ATTRIBUTES[att][1])
            setattr(self, f"{att}_var", new_var)
            self.attrib_dict[att] = new_var
            cb = Checkbutton(
                self, text=PromptAttrib.ALL_ATTRIBUTES[att][0],
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
        self.target_var.set(','.join(selected_attribs))
        self.external_var_dict['attrib_list'] = selected_attribs

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
            self.target_var.set('CANCEL')
            self.external_var_dict['attrib_list'] = ['CANCEL']
            self.master.destroy()


if __name__ == '__main__':
    # If run on its own, won't really serve much purpose, but it will
    # pop up and show the default attributes.
    pa = PromptAttrib()
    pa.master.mainloop()
