"""
textfsmgen.ui.snippet
=====================

UI components for the Snippet Translator dialog in TextFSMGen.
"""

from typing import Optional, Union

from textfsmgen.libs.generic import Position

from textfsmgen import ui
from textfsmgen.ui.common import (
    center_window,
    make_modal,
)

window_width = 982 if ui.is_macos else 880 if ui.is_linux else 760
window_height = 770 if ui.is_macos else 785 if ui.is_linux else 720

def show_dialog(app):
    """Show the dialog window."""
    parent = app.root

    dialog = create_window(parent)

    paned_window = build_pane_window(dialog)

    build_input_frame(paned_window)
    build_controls_frame(paned_window, app)
    build_output_frame(paned_window)
    build_python_code_frame(paned_window)
    build_test_result_frame(paned_window)

    # Make dialog modal
    make_modal(dialog)


def create_window(parent: Optional[Union[ui.Tk, ui.Toplevel]]):
    """Create and center the snippet translator window."""
    window = ui.Toplevel(parent)
    window.title("Snippet Translator - TextFSMGen CE")

    ui.set_window_icon(window)

    if parent:
        center_window(
            parent, window, window_width, window_height,
            x_resizable=True, y_resizable=True
        )

    return window


def build_pane_window(parent):
    paned_window = ui.PanedWindow(parent, orient="vertical")
    paned_window.pack(fill="both", expand=True, padx=2, pady=2)
    return paned_window


def build_input_frame(parent):
    frame = ui.Frame(
        parent, width=window_width,
        height=int(window_height / 5),
        relief="ridge"
    )
    parent.add(frame, weight=2)

    # Configure grid for resizing
    frame.rowconfigure(0, weight=1)
    frame.columnconfigure(0, weight=1)

    textarea = ui.TextArea(
        frame, width=20, height=3, wrap='none',
        name='input_text',
    )

    textarea.grid(row=0, column=0, sticky='nswe')  # noqa

    # Add vertical scrollbar
    vscrollbar = ui.Scrollbar(
        frame, orient="vertical",
        command=textarea.yview
    )
    vscrollbar.grid(row=0, column=1, sticky='ns')

    # Add horizontal scrollbar
    hscrollbar = ui.Scrollbar(
        frame, orient="horizontal",
        command=textarea.xview
    )
    hscrollbar.grid(row=1, column=0, sticky='ew')

    # Link scrollbars to text area
    textarea.config(
        yscrollcommand=vscrollbar.set,
        xscrollcommand=hscrollbar.set
    )


def build_controls_frame(parent, app):
    """Create the control button row (Clear, Copy, Paste)."""
    frame = ui.Frame(parent, width=window_width, height=10, relief="ridge")
    parent.add(frame)

    btn_width = 6 if ui.is_macos else 8
    pad = dict(padx=(2, 0), pady=(2, 2))

    position = Position(value=-1)

    buttons = [
        ("Translate", lambda: "Implement later"),
        ("Test", lambda: "Implement later"),
        ("Reset", lambda: reset_default(app)),
        ("Copy", lambda: "Implement later"),
        ("Paste", lambda: "Implement later")
    ]

    for text_ , func in buttons:
        name = f"{text_.lower()}_button"
        btn = ui.Button(frame, text=text_, name=name, width=btn_width, command=func)
        btn.grid(row=0, column=position.next(), **pad)

    checkboxes = [
        ("Variable",    app.tools.translator.variable_flag),
        ("Group",       app.tools.translator.group_flag),
        ("Exact",       app.tools.translator.exact_flag),
        ("Notation",    app.tools.translator.notation_flag),
        ("Split",       app.tools.translator.split_flag),
    ]

    for text_, var_ in checkboxes:
        checkbox = ui.CheckBox(
            frame, text=text_, name=f"{text_.lower()}_checkbox",
            variable=var_,
            onvalue=True, offvalue=False,
        )
        checkbox.grid(row=0, column=position.next(), sticky="ns", **pad)
    return frame


def build_output_frame(parent):
    frame = ui.Frame(
        parent, width=window_width,
        height=int(window_height / 5),
        relief="ridge"
    )
    parent.add(frame, weight=2)

    # Configure grid for resizing
    frame.rowconfigure(0, weight=1)
    frame.columnconfigure(0, weight=1)

    textarea = ui.TextArea(
        frame, width=20, height=3, wrap='none',
        name='output_text',
    )

    textarea.grid(row=0, column=0, sticky='nswe')  # noqa

    # Add vertical scrollbar
    vscrollbar = ui.Scrollbar(
        frame, orient="vertical",
        command=textarea.yview
    )
    vscrollbar.grid(row=0, column=1, sticky='ns')

    # Add horizontal scrollbar
    hscrollbar = ui.Scrollbar(
        frame, orient="horizontal",
        command=textarea.xview
    )
    hscrollbar.grid(row=1, column=0, sticky='ew')

    # Link scrollbars to text area
    textarea.config(
        yscrollcommand=vscrollbar.set,
        xscrollcommand=hscrollbar.set
    )


def build_python_code_frame(parent):
    frame = ui.Frame(
        parent, width=window_width,
        height=int(window_height / 2),
        relief="ridge"
    )
    parent.add(frame, weight=5)

    # Configure grid for resizing
    frame.rowconfigure(0, weight=1)
    frame.columnconfigure(0, weight=1)

    textarea = ui.TextArea(
        frame, width=20, height=3, wrap='none',
        name='python_code_text',
    )

    textarea.grid(row=0, column=0, sticky='nswe')  # noqa

    # Add vertical scrollbar
    vscrollbar = ui.Scrollbar(
        frame, orient="vertical",
        command=textarea.yview
    )
    vscrollbar.grid(row=0, column=1, sticky='ns')

    # Add horizontal scrollbar
    hscrollbar = ui.Scrollbar(
        frame, orient="horizontal",
        command=textarea.xview
    )
    hscrollbar.grid(row=1, column=0, sticky='ew')

    # Link scrollbars to text area
    textarea.config(
        yscrollcommand=vscrollbar.set,
        xscrollcommand=hscrollbar.set
    )


def build_test_result_frame(parent):
    frame = ui.Frame(
        parent, width=window_width,
        height=int(window_height / 10),
        relief="ridge"
    )
    parent.add(frame, weight=1)

    # Configure grid for resizing
    frame.rowconfigure(0, weight=1)
    frame.columnconfigure(0, weight=1)

    textarea = ui.TextArea(
        frame, width=20, height=3, wrap='none',
        name='result_text',
    )

    textarea.grid(row=0, column=0, sticky='nswe')  # noqa

    # Add vertical scrollbar
    vscrollbar = ui.Scrollbar(
        frame, orient="vertical",
        command=textarea.yview
    )
    vscrollbar.grid(row=0, column=1, sticky='ns')

    # Add horizontal scrollbar
    hscrollbar = ui.Scrollbar(
        frame, orient="horizontal",
        command=textarea.xview
    )
    hscrollbar.grid(row=1, column=0, sticky='ew')

    # Link scrollbars to text area
    textarea.config(
        yscrollcommand=vscrollbar.set,
        xscrollcommand=hscrollbar.set
    )


def reset_default(app):
    """Reset all application metadata and checkbox settings to defaults."""

    app.tools.translator.variable_flag.set(True)
    app.tools.translator.group_flag.set(False)
    app.tools.translator.exact_flag.set(False)
    app.tools.translator.notation_flag.set(False)
    app.tools.translator.split_flag.set(False)