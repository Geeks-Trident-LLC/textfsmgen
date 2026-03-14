"""
textfsmgen.ui.settings
======================

UI components for the Settings dialog in TextFSMGen.
"""

from typing import Optional

from tkinter import filedialog

from textfsmgen import ui
from textfsmgen.ui.common import (
center_window,
make_modal,
)


def show_dialog(app):
    """Handle the "Preferences > Settings" menu action."""

    parent = app.root

    dialog = create_window(parent)

    frame = ui.Frame(dialog)
    frame.pack(fill="both", expand=True)

    add_general_arguments_fields(app, frame)

    add_category_translator_arguments(app, frame)

    add_running_test_options(app, frame)

    add_output_display_options(app, frame)

    add_ok_and_default_buttons(app, frame)

    # Make dialog modal
    make_modal(dialog)


def create_window(parent: Optional[ui.Tk | ui.Toplevel]) -> ui.Toplevel:
    """Create and center the Settings window."""
    window = ui.Toplevel(parent)
    window.title("Settings - TextFSMGen CE")

    ui.set_window_icon(window)

    width = 830 if ui.is_macos else 784 if ui.is_linux else 680
    height = 338 if ui.is_macos else 322 if ui.is_linux else 314

    center_window(parent, window, width, height)
    return window

def add_general_arguments_fields(app, parent: ui.Frame) -> None:
    """Add author, email, company, and description fields to the parent frame."""
    group = ui.LabelFrame(parent, height=100, width=780, text="General Arguments")
    group.grid(row=0, column=0, padx=10, pady=(5, 0), sticky="nw")

    pad_y = 0 if ui.is_macos else 1

    fields = [
        ("Author",  app.settings.author,    0),
        ("Email",   app.settings.email,     1),
        ("Company", app.settings.company,   2),
    ]
    for label_text, var, pos in fields:
        lbl = ui.Label(group, text=label_text)
        lbl.grid(row=0, column=pos * 2, padx=2, pady=pad_y, sticky="nw")

        entry = ui.TextBox(group, width=25, textvariable=var)
        entry.grid(row=0, column=pos * 2 + 1, padx=2, pady=pad_y, sticky="nw")

    lbl = ui.Label(group, text="Description")
    lbl.grid(row=1, column=0, columnspan=1, padx=2, pady=pad_y, sticky="nw")
    entry = ui.TextBox(group, width=96, textvariable=app.settings.description)
    entry.grid(row=1, column=1, columnspan=5, padx=2, pady=pad_y, sticky="nw")


def add_category_translator_arguments(app, parent: ui.Frame) -> None:

    group = ui.LabelFrame(parent, height=120, width=780, text="Category Translator Arguments")
    group.grid(row=1, column=0, padx=10, pady=4, sticky="nw")
    pad_y = 0 if ui.is_macos else 1

    checkbox = ui.CheckBox(group, text="Use Category Translator",
                           variable=app.settings.use_category_translator_flag,
                           onvalue=True, offvalue=False)
    checkbox.grid(row=0, column=10, sticky="se")

    lbl = ui.Label(group, text="Separator")
    lbl.grid(row=0, column=0, columnspan=1, padx=2, pady=pad_y, sticky="nw")
    entry = ui.TextBox(group, width=4, justify="center",
                       textvariable=app.settings.category_arg_separator)
    entry.grid(row=0, column=1, padx=2, pady=pad_y, sticky="nw")

    lbl = ui.Label(group, text="Count")
    lbl.grid(row=0, column=2, padx=2, pady=pad_y, sticky="se")
    entry = ui.TextBox(group, width=4, justify="center",
                       textvariable=app.settings.category_arg_count)
    entry.grid(row=0, column=3, padx=2, pady=pad_y, sticky="nw")

    lbl = ui.Label(group, text="Starting From")
    lbl.grid(row=1, column=0, columnspan=1, padx=2, pady=pad_y, sticky="nw")
    entry = ui.TextBox(group, width=94, textvariable=app.settings.category_arg_starting_from)
    entry.grid(row=1, column=1, columnspan=10, padx=2, pady=pad_y, sticky="nw")

    lbl = ui.Label(group, text="Ending At")
    lbl.grid(row=2, column=0, columnspan=1, padx=2, pady=pad_y, sticky="nw")
    entry = ui.TextBox(group, width=94, textvariable=app.settings.category_arg_ending_at)
    entry.grid(row=2, column=1, columnspan=10, padx=2, pady=pad_y, sticky="nw")



def add_running_test_options(app, parent: ui.Frame) -> None:

    def open_():
        filetypes = (('Execute Files', '.exe'), ('All Files', '*'))
        filename = filedialog.askopenfilename(filetypes=filetypes)
        if filename:
            app.settings.python_interpreter.set(filename)

    group = ui.LabelFrame(
        parent, height=120, width=780,
        text="Test Execution Settings - Prefer Python Virtual Environment"
    )
    group.grid(row=3, column=0, padx=10, pady=4, sticky="nw")

    pad_y = 0 if ui.is_macos else 1

    lbl = ui.Label(group, text="Interpreter")
    lbl.grid(row=0, column=0, columnspan=1, padx=2, pady=pad_y, sticky="nw")
    entry = ui.TextBox(group, width=88, textvariable=app.settings.python_interpreter)
    entry.grid(row=0, column=1, columnspan=5, padx=2, pady=pad_y, sticky="nw")

    button = ui.Button(group, text="...", width=3, command=open_)
    button.grid(row=0, column=6, padx=2, pady=pad_y, sticky="nw")

    settings = [
        ("Always Ask",                  app.settings.always_ask_flag, 0),
        ("Delete Temp File After Run", app.settings.delete_file_after_run_flag, 1),
    ]
    for label, var, col in settings:
        checkbox = ui.CheckBox(group, text=label, variable=var, onvalue=True, offvalue=False,)
        checkbox.grid(row=1, column=col, sticky="nw")


def add_output_display_options(app, parent: ui.Frame) -> None:
    """Add application setting checkboxes to the given parent frame."""
    group = ui.LabelFrame(parent, height=120, width=380, text="Output Display Options")
    group.grid(row=4, column=0, padx=10, pady=1, sticky="nw")

    settings = [
        ("Test Data",   app.settings.test_data_flag, 0, 0, 6),
        ("Template",    app.settings.template_flag,  0, 1, 10),
        ("Tabular",     app.settings.tabular_flag,   0, 2, 10),
    ]

    for label, var, row, col, pad in settings:
        checkbox = ui.CheckBox(group, text=label, variable=var, onvalue=True, offvalue=False,)
        checkbox.grid(row=row, column=col, padx=pad)


def add_ok_and_default_buttons(app, parent: ui.Frame) -> None:
    """Add Default and OK buttons to the given parent frame."""
    container = ui.Frame(parent, height=14, width=380)
    container.grid(row=4, column=0, padx=10, pady=(10, 5), sticky="es")

    default_btn = ui.Button(
        container,
        text="Default",
        command=lambda: reset_default_setting(app),
    )
    default_btn.grid(row=0, column=6, padx=1, pady=1, sticky="e")

    ok_btn = ui.Button(
        container,
        text="OK",
        command=lambda: parent.master.destroy(),
    )
    ok_btn.grid(row=0, column=7, padx=1, pady=1, sticky="e")


def reset_default_setting(app):
    """Reset all application metadata and checkbox settings to defaults."""

    # General Arguments
    app.settings.author.set("")
    app.settings.email.set("")
    app.settings.company.set("")
    app.settings.description.set("")

    # Category Translator Arguments
    app.settings.use_category_translator_flag.set(False)
    app.settings.category_arg_separator.set(":")
    app.settings.category_arg_count.set(0)
    app.settings.category_arg_starting_from.set("")
    app.settings.category_arg_ending_at.set("")

    # Test Execution
    app.settings.python_interpreter.set("")
    app.settings.always_ask_flag.set(True)
    app.settings.delete_file_after_run_flag.set(True)

    # Output Display Options
    app.settings.test_data_flag.set(False)
    app.settings.template_flag.set(False)
    app.settings.tabular_flag.set(True)
