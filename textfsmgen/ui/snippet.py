"""
textfsmgen.ui.snippet
=====================

UI components for the Snippet Translator dialog in TextFSMGen.
"""

from typing import Optional, Union

import re

from textfsmgen.libs.generic import Position

from textfsmgen import ui

from textfsmgen.ui.common import (
    show_message_dialog,
    center_window,
    make_modal,
    clear_text,
    extract_text,
)

window_width = 1060 if ui.is_macos else 900 if ui.is_linux else 810
window_height = 770 if ui.is_macos else 785 if ui.is_linux else 720

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


def build_input_frame(parent, app):
    frame = ui.Frame(
        parent, width=window_width,
        height=int(window_height / 20) * 2,
        relief="ridge"
    )
    parent.add(frame, weight=2)

    # Configure grid for resizing
    frame.rowconfigure(0, weight=1)
    frame.columnconfigure(0, weight=1)

    textarea = ui.TextArea(
        frame, width=20, height=3, wrap='none',
        name='translator_input_text',
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

    app.tools.translator.in_textarea = textarea


def build_controls_frame(parent, app):
    """Create the control button row (Clear, Copy, Paste)."""
    frame = ui.Frame(parent, width=window_width, height=10, relief="ridge")
    parent.add(frame)

    btn_width = 5 if ui.is_macos else 6 if ui.is_linux else 8
    pad = dict(padx=(2, 0), pady=(2, 2))

    position = Position(value=-1)

    buttons = [
        ("Translate",   lambda: "Implement later"),
        ("Iterate",     lambda: "Implement later"),
        ("Test",        lambda: "Implement later"),
        ("Default",     lambda: reset_default(app)),

        ("SEPARATOR",   ""),

        ("Copy",        lambda: copy(app)),
        ("Paste",       lambda: paste(app)),
        ("Clear",       lambda: clear(app)),
    ]

    for text_ , func in buttons:
        if text_ == "SEPARATOR":
            sep = ui.ttk.Separator(frame, orient="vertical")
            sep.grid(row=0, column=position.next(), sticky="ns", padx=(4, 2), pady=2)
            continue
        name = f"{text_.lower()}_button"
        btn = ui.Button(
            frame, text=text_, name=name,
            width=btn_width + 2 if text_ == "Translate" else btn_width,
            command=func
        )
        btn.grid(row=0, column=position.next(), **pad)

    checkboxes = [
        ("Variable",    app.tools.translator.variable_flag),
        ("Notation",    app.tools.translator.notation_flag),

        ("SEPARATOR",   ""),

        ("Group",       app.tools.translator.group_flag),
        ("Exact",       app.tools.translator.exact_flag),
    ]

    sep = ui.ttk.Separator(frame, orient="vertical")
    sep.grid(row=0, column=position.next(), sticky="ns", padx=(4, 2), pady=2)

    for text_, var_ in checkboxes:
        if text_ == "SEPARATOR":
            sep = ui.ttk.Separator(frame, orient="vertical")
            sep.grid(row=0, column=position.next(), sticky="ns", padx=(4, 2), pady=2)
            continue

        checkbox = ui.CheckBox(
            frame, text=text_, name=f"{text_.lower()}_checkbox",
            variable=var_,
            onvalue=True, offvalue=False,
        )
        checkbox.grid(row=0, column=position.next(), sticky="ns", **pad)

    sep = ui.ttk.Separator(frame, orient="vertical")
    sep.grid(row=0, column=position.next(), sticky="ns", padx=(4, 2), pady=2)

    lbl = ui.Label(frame, text="Split")
    lbl.grid(row=0, column=position.next(), sticky="ns", **pad)

    entry = ui.TextBox(
        frame, width=6, justify="center",
        textvariable=app.tools.translator.split_arg
    )
    entry.grid(row=0, column=position.next(), sticky="ns", padx=2, pady=4)

    return frame


def build_output_frame(parent, app):
    frame = ui.Frame(
        parent, width=window_width,
        height=int(window_height / 20) * 8,
        relief="ridge"
    )
    parent.add(frame, weight=8)

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

    app.tools.translator.out_textarea = textarea


def build_python_code_frame(parent, app):
    frame = ui.Frame(
        parent, width=window_width,
        height=int(window_height / 20) * 11,
        relief="ridge"
    )
    parent.add(frame, weight=11)

    # Configure grid for resizing
    frame.rowconfigure(0, weight=1)
    frame.columnconfigure(0, weight=1)

    textarea = ui.TextArea(
        frame, width=20, height=3, wrap='none',
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

    app.tools.translator.code_textarea = textarea


def build_test_result_frame(parent, app):
    frame = ui.Frame(
        parent, width=window_width,
        height=int(window_height / 20),
        relief="ridge"
    )
    parent.add(frame, weight=1)

    # Configure grid for resizing
    frame.rowconfigure(0, weight=1)
    frame.columnconfigure(0, weight=1)

    textarea = ui.TextArea(
        frame, width=20, height=3, wrap='none',
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

    app.tools.translator.result_textarea = textarea


def reset_default(app):
    """Reset all application metadata and checkbox settings to defaults."""
    app.tools.translator.variable_flag.set(True)
    app.tools.translator.group_flag.set(False)
    app.tools.translator.exact_flag.set(False)
    app.tools.translator.notation_flag.set(False)
    app.tools.translator.split_arg.set("/")


def clear(app):
    """Clear selected text in editable areas; warn or clear readonly ones based on last focus."""
    t = app.tools.translator

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


def paste(app):
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

    t = app.tools.translator

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


def copy(app):
    """Copy clipboard text into editable areas; warn on readonly ones."""

    t = app.tools.translator
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
