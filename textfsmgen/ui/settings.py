"""
textfsmgen.ui.settings
======================

UI components for the Settings dialog in TextFSMGen.
"""

from typing import Optional

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

    add_author_email_fields(app, frame)

    add_app_setting_checkboxes(app, frame)

    add_ok_and_default_buttons(app, frame)

    # Make dialog modal
    make_modal(dialog)


def create_window(parent: Optional[ui.Tk | ui.Toplevel]) -> ui.Toplevel:
    """Create and center the Settings window."""
    window = ui.Toplevel(parent)
    window.title("Settings - TextFSMGen CE")

    ui.set_window_icon(window)

    width = 520 if ui.is_macos else 474 if ui.is_linux else 370
    height = 238 if ui.is_macos else 222 if ui.is_linux else 214

    center_window(parent, window, width, height)
    return window

def add_author_email_fields(app, parent: ui.Frame) -> None:
    """Add author, email, company, and description fields to the parent frame."""
    group = ui.LabelFrame(parent, height=100, width=380, text="Arguments")
    group.grid(row=0, column=0, padx=10, pady=(5, 0), sticky="w")

    pad_y = 0 if ui.is_macos else 1

    fields = [
        ("Author",      app.settings.author,      0),
        ("Email",       app.settings.email,       1),
        ("Company",     app.settings.company,     2),
        ("Description", app.settings.description, 3),
    ]

    for label_text, var, row in fields:
        lbl = ui.Label(group, text=label_text)
        lbl.grid(
            row=row, column=0, columnspan=2,
            padx=2, pady=pad_y,
            sticky="wn"
        )

        entry = ui.TextBox(group, width=45, textvariable=var)
        entry.grid(
            row=row, column=2, columnspan=4,
            padx=2,
            pady=(pad_y, 10) if label_text == "Description" else pad_y,
            sticky="w"
        )


def add_app_setting_checkboxes(app, parent: ui.Frame) -> None:
    """Add application setting checkboxes to the given parent frame."""
    group = ui.LabelFrame(parent, height=120, width=380, text="App")
    group.grid(row=1, column=0, padx=10, pady=1, sticky="wn")

    settings = [
        ("Test Data",   app.settings.test_data, 0, 0, 6),
        ("Template",    app.settings.template,  0, 1, 10),
        ("Tabular",     app.settings.tabular,   0, 2, 10),
        ("Confirm",     app.settings.confirm,   0, 3, 10),
    ]

    for label, var, row, col, pad in settings:
        checkbox = ui.CheckBox(
            group,
            text=label,
            variable=var,
            onvalue=True,
            offvalue=False,
        )
        checkbox.grid(row=row, column=col, padx=pad)


def add_ok_and_default_buttons(app, parent: ui.Frame) -> None:
    """Add Default and OK buttons to the given parent frame."""
    container = ui.Frame(parent, height=14, width=380)
    container.grid(row=2, column=0, padx=10, pady=(10, 5), sticky="es")

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

    for key, value in (
        ("author", ""), ("email", ""), ("company", ""), ("description", ""),
        ("test_data", False), ("template", False), ("tabular", True),
        ("confirm", True)
    ):
        node = app.settings.get(key)
        node.set(value)
