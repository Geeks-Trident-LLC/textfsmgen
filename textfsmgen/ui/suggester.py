"""
textfsmgen.ui.snippet
=====================

UI components for the Snippet Translator dialog in TextFSMGen.
"""

from typing import Optional, Union

import re

from textfsmgen.libs.text import (
    get_list_of_lines,
)

from textfsmgen.tools.translator import SnippetSuggester
from textfsmgen.tools.translator import ScriptBuilder
from textfsmgen.tools.translator import IterateTranslator

from textfsmgen.libs.generic import Position

from textfsmgen import ui
from textfsmgen.ui import usage

from textfsmgen.ui.common import (
    show_message_dialog,
    center_window,
    make_modal,
    clear_text,
    extract_text,
    set_text, set_window_icon
)

window_width = 960 if ui.is_macos else 820 if ui.is_linux else 740
window_height = 770 if ui.is_macos else 780 if ui.is_linux else 720

def show_dialog(app):
    """Show the dialog window."""
    parent = app.root

    dialog = create_window(parent)

    paned_window = build_pane_window(dialog)

    build_input_frame(paned_window, app)
    build_controls_frame(paned_window, app)
    build_output_frame(paned_window, app)
    build_python_code_frame(paned_window, app)
    build_test_result_frame(paned_window, app)

    dialog.bind("<Button-1>", lambda e: app.callback_focus(e))

    # Make dialog modal
    make_modal(dialog)


def create_window(parent: Optional[Union[ui.Tk, ui.Toplevel]]):
    """Create and center the regex suggester window."""
    window = ui.Toplevel(parent)
    window.title("Regex Suggester - TextFSMGen CE")

    set_window_icon(window)

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


def build_input_frame(parent, app):
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
        name='suggester_input_text',
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

    app.tools.suggester.in_textarea = textarea


def build_controls_frame(parent, app):
    """Create the control button row (Clear, Copy, Paste)."""
    frame = ui.Frame(parent, width=window_width, height=10, relief="ridge", borderwidth=2)
    parent.add(frame)

    top = ui.Frame(frame, width=window_width, height=5)
    top.pack(side="top", fill="x")

    sep = ui.ttk.Separator(frame, orient="horizontal")
    sep.pack(fill="x", padx=4)

    bottom = ui.Frame(frame, width=window_width, height=5)
    bottom.pack(side="top", fill="x")

    build_top_controls(top, app)
    build_bottom_controls(bottom, app)

    return frame


def build_top_controls(parent, app):
    """Build the top control bar with action buttons and a vertical separator."""
    controls = [
        ("Suggest", lambda: perform_suggest_action(app)),
        ("Test",  lambda: perform_test_action(app)),
        ("Iterate",   lambda: perform_iterate_action(app)),
        ("Default",   lambda: reset_default(app)),

        ("SEPARATOR", None),

        ("Copy",      lambda: perform_copy_action(app)),
        ("Paste",     lambda: perform_paste_action(app)),
        ("Clear",     lambda: perform_clear_action(app)),

        ("SEPARATOR", None),

        ("Help", lambda: usage.show_help(app, "suggester")),

    ]

    btn_width = 6 if ui.is_macos else 7 if ui.is_linux else 8
    padding = dict(padx=(2, 0), pady=(2, 2))
    pos = Position(value=-1)

    for label, callback in controls:
        if label == "SEPARATOR":
            sep = ui.ttk.Separator(parent, orient="vertical")
            sep.grid(row=0, column=pos.next(), sticky="ns", padx=(4, 2), pady=2)
            continue

        name = f"{label.lower()}_btn"
        width = btn_width + 2 if label in ("Suggest", "Test") else btn_width

        btn = ui.Button(
            parent,
            text=label,
            name=name,
            width=width,
            command=callback,
        )
        btn.grid(row=0, column=pos.next(), **padding)


def build_bottom_controls(parent, app):
    """Build the bottom control bar with checkboxes, separator, and split field."""
    controls = [
        ("Variable", app.tools.suggester.variable_flag),
        ("Surrounding Notation", app.tools.suggester.notation_flag),

        ("SEPARATOR", None),

        ("Group",    app.tools.suggester.group_flag),
        ("Generic",  app.tools.suggester.generic_flag),
    ]

    padding = dict(padx=(2, 0), pady=(2, 2))
    pos = Position(value=-1)

    # Checkboxes + inline separator
    for label, var in controls:
        if label == "SEPARATOR":
            sep = ui.ttk.Separator(parent, orient="vertical")
            sep.grid(row=0, column=pos.next(), sticky="ns", padx=(4, 2), pady=2)
            continue

        chk = ui.CheckBox(
            parent,
            text=label,
            name=f"{label.lower()}_checkbox",
            variable=var,
            onvalue=True,
            offvalue=False,
        )
        chk.grid(row=0, column=pos.next(), sticky="ns", **padding)

    # Final separator before split controls
    sep = ui.ttk.Separator(parent, orient="vertical")
    sep.grid(row=0, column=pos.next(), sticky="ns", padx=(4, 2), pady=2)

    # Split label
    lbl = ui.Label(parent, text="Split")
    lbl.grid(row=0, column=pos.next(), sticky="ns", **padding)

    # Split entry
    entry = ui.TextBox(
        parent,
        width=8,
        justify="center",
        textvariable=app.tools.suggester.split_arg,
    )
    entry.grid(row=0, column=pos.next(), sticky="ns", padx=2, pady=4)


def build_output_frame(parent, app):
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
        name='translator_output_text',
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

    app.tools.suggester.out_textarea = textarea


def build_python_code_frame(parent, app):
    frame = ui.Frame(
        parent, width=window_width,
        height=int(window_height / 10) * 7,
        relief="ridge"
    )
    parent.add(frame, weight=7)

    # Configure grid for resizing
    frame.rowconfigure(0, weight=1)
    frame.columnconfigure(0, weight=1)

    textarea = ui.TextArea(
        frame, width=20, height=3, wrap='none',
        bg=ui.readonly_text_bg_color,
        name='translator_code_text',
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
    textarea.config(state="disabled")

    app.tools.suggester.code_textarea = textarea


def build_test_result_frame(parent, app):
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
        bg=ui.readonly_text_bg_color,
        name='translator_result_text',
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
    textarea.config(state="disabled")

    app.tools.suggester.result_textarea = textarea


def reset_default(app):
    """Reset all application metadata and checkbox settings to defaults."""
    app.tools.suggester.variable_flag.set(True)
    app.tools.suggester.group_flag.set(False)
    app.tools.suggester.generic_flag.set(True)
    app.tools.suggester.notation_flag.set(False)
    app.tools.suggester.split_arg.set("/")


def perform_clear_action(app):
    """Clear selected text in editable areas; warn or clear readonly ones based on last focus."""
    t = app.tools.suggester

    readonly = [
        (t.code_textarea,  "Readonly Code Window",   "Cannot clear readonly Python code window"),
        (t.result_textarea, "Readonly Result Window", "Cannot clear readonly result window"),
    ]

    prev = app.prev_widget

    if prev is t.in_textarea:
        prev.update_idletasks()
        if prev.tag_ranges(ui.tk.SEL):
            prev.delete(ui.tk.SEL_FIRST, ui.tk.SEL_LAST)
            return

        clear_text(prev)

    if prev is t.out_textarea:
        prev.update_idletasks()
        if prev.tag_ranges(ui.tk.SEL):
            prev.delete(ui.tk.SEL_FIRST, ui.tk.SEL_LAST)
            return

        # Clear output + readonly
        for widget in [t.out_textarea, t.result_textarea, t.code_textarea]:
            clear_text(widget)
        return

    if prev in (t.result_textarea, t.code_textarea):
        prev.update_idletasks()
        if prev.tag_ranges(ui.tk.SEL):
            for widget, title, info in readonly:
                if widget is prev:
                    show_message_dialog(title=title, info=info)
                    return
        # Clear readonly only
        for widget in [t.result_textarea, t.code_textarea]:
            clear_text(widget)
        return

    # 4. No idea what to clear
    show_message_dialog(
        title="Ambiguous Clear Action",
        info="Please select the specific area you want to clear.",
    )


def perform_paste_action(app):
    """Paste clipboard text into editable areas; warn on readonly ones."""
    try:
        data = app.root.clipboard_get()

        if re.fullmatch(r"\s*", data):
            show_message_dialog(
                title="Paste Action",
                info="Your clipboard contains only whitespace. "
                     "The paste action will still run, but the "
                     "result is not visually noticeable."
            )

    except Exception as ex:
        show_message_dialog(
            title="Clipboard Empty",
            info=(
                f"There is no text available to paste from the clipboard.\n"
                f"{'-' * 70}\n"
                f"{type(ex).__name__}: {ex}"
                )
        )
        return

    t = app.tools.suggester

    editable = [t.in_textarea, t.out_textarea]
    readonly = [
        (t.code_textarea, "Readonly Code Window", "Cannot paste readonly Python code window"),
        (t.result_textarea, "Readonly Result Window", "Cannot paste readonly result window"),
    ]

    prev = app.prev_widget

    for widget in editable:
        widget.update_idletasks()
        if widget is prev:

            if widget.tag_ranges(ui.tk.SEL):
                widget.delete(ui.tk.SEL_FIRST, ui.tk.SEL_LAST)
                insert_pos = widget.index(ui.tk.INSERT)
                widget.insert(ui.tk.INSERT, data)
                widget.tag_add(ui.tk.SEL, insert_pos, f"{insert_pos}+{len(data)}c")
                widget.focus()
                return
            widget.insert(ui.tk.INSERT, data)
            return

    for widget, title, info in readonly:
        widget.update_idletasks()
        if widget is prev:
            show_message_dialog(title=title, info=info)
            return

    show_message_dialog(
        title="Ambiguous Paste Action",
        info="Please select the specific area you want to paste from the clipboard.",
    )


def perform_copy_action(app):
    """Copy clipboard text into editable areas; warn on readonly ones."""

    t = app.tools.suggester
    prev = app.prev_widget

    widgets = [t.in_textarea, t.out_textarea, t.code_textarea, t.result_textarea]

    for widget in widgets:
        if widget is prev:
            widget.update_idletasks()
            content = (
                widget.selection_get()
                if widget.tag_ranges(ui.tk.SEL) else
                extract_text(widget)
            )

            if not content:
                show_message_dialog(
                    title="Copy Action",
                    warning="There is no text in the your selected area to copy.",
                )
                return

            # Update UI and clipboard
            app.root.clipboard_clear()
            app.root.clipboard_append(content)
            app.root.update()
            return

    show_message_dialog(
        title="Ambiguous Copy Action",
        info="Please select the specific area you want to copy.",
    )


def perform_suggest_action(app):
    """Perform suggesting input text using current suggester settings."""

    t = app.tools.suggester
    data = extract_text(t.in_textarea)

    if not any(get_list_of_lines(data)):
        show_message_dialog(
            title="Suggest Action- No Input",
            info="No text was found to suggest.\n"
                 "Please enter or paste content first.",
        )
        return

    translator = SnippetSuggester(
        data,
        variable_flag=t.variable_flag.get(),
        notation_flag=t.notation_flag.get(),
        group_flag=t.group_flag.get(),
        generic_flag=t.generic_flag.get(),
        split_arg=t.split_arg.get(),
    )

    clear_text(t.code_textarea)
    clear_text(t.result_textarea)

    set_text(t.out_textarea, translator.snippet)
    set_text(t.code_textarea, translator.explanation)
    set_text(t.result_textarea, translator.pattern_statement)
    t.result_textarea.config(wrap="char")


def perform_iterate_action(app):
    """Notify the user that the Iterate Snippet feature is not yet implemented."""
    t = app.tools.suggester

    raw_data = extract_text(t.in_textarea)
    snippet = extract_text(t.out_textarea)

    # --- Validate snippet ----------------------------------------------------
    if not snippet.strip():
        show_message_dialog(
            title="Iterate Snippet – No Snippet",
            info=(
                "No snippet is available to adjust.\n"
                "Please update snippet in the second text area."
            ),
        )
        return

    # --- Validate test data --------------------------------------------------
    if not get_list_of_lines(raw_data):
        show_message_dialog(
            title="Generate Script – No Test Data",
            info=(
                "No test data was found to generate a script.\n"
                "Please enter or paste content in the first text area."
            ),
        )
        return

    # --- Build script --------------------------------------------------------
    builder = IterateTranslator(
        raw_data,
        snippet,
        group_flag=t.group_flag.get(),
    )

    # --- Update UI -----------------------------------------------------------
    t.result_textarea.config(wrap="none")

    if not builder:
        clear_text(t.code_textarea)
        set_text(t.result_textarea, builder.error or builder.warning)

    set_text(t.out_textarea, builder.snippet)
    set_text(t.code_textarea, builder.script)
    set_text(t.result_textarea, builder.result)


def perform_test_action(app):
    t = app.tools.suggester

    raw_data = extract_text(t.in_textarea)
    snippet = extract_text(t.out_textarea)

    # --- Validate snippet ----------------------------------------------------
    if not snippet.strip():
        show_message_dialog(
            title="Generate Script – No Snippet",
            info=(
                "No snippet is available to generate a Python script.\n"
                "Please perform suggesting text or enter a suggested snippet in the second text area."
            ),
        )
        return

    # --- Validate test data --------------------------------------------------
    if not get_list_of_lines(raw_data):
        show_message_dialog(
            title="Generate Script and Test – No Test Data",
            info=(
                "No test data was found to generate a script.\n"
                "Please enter or paste content in the first text area."
            ),
        )
        return

    # --- Build script --------------------------------------------------------
    builder = ScriptBuilder(
        raw_data,
        snippet,
        group_flag=t.group_flag.get(),
    )

    # --- Update UI -----------------------------------------------------------
    set_text(t.code_textarea, builder.script)
    set_text(t.result_textarea, builder.result)
    t.result_textarea.config(wrap="none")
