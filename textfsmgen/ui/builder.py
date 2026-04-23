"""
textfsmgen.ui.builder
=====================

UI components for the Regex Translator dialog in TextFSMGen.
"""
from typing import Optional, Union

import re

from textfsmgen.libs.text import (
    get_list_of_lines,
)

from textfsmgen.libs.generic import Position

from textfsmgen import ui
from textfsmgen.ui import usage

from textfsmgen.ui.common import (
    show_message_dialog,
    center_window,
    make_modal,
    clear_text,
    extract_text,
    set_text
)

window_width = 960 if ui.is_macos else 820 if ui.is_linux else 740
window_height = 770 if ui.is_macos else 780 if ui.is_linux else 720

def show_dialog(app):
    """Show the dialog window."""
    parent = app.root

    dialog = create_window(parent)

    paned_window = build_pane_window(dialog)

    build_semantic_group(app, paned_window, row=0)

    build_data_group(app, paned_window, row=1)

    build_controls(app, paned_window, row=2)

    create_textarea(paned_window, row=4, name="pattern_area", height_rows=2)
    create_textarea(paned_window, row=5, name="explanation_area", height_rows=10)

    dialog.bind("<Button-1>", lambda e: app.callback_focus(e))

    # Make dialog modal
    make_modal(dialog)


def create_window(parent: Optional[Union[ui.Tk, ui.Toplevel]]):
    """Create and center the snippet translator window."""
    window = ui.Toplevel(parent)
    window.title("Regex Builder - TextFSMGen CE")

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

    # row-0: Allow horizontal expansion, prevent vertical expansion
    paned_window.grid_columnconfigure(0, weight=1)
    paned_window.grid_rowconfigure(0, weight=0)

    # row-1: Allow horizontal expansion, prevent vertical expansion
    paned_window.grid_columnconfigure(0, weight=1)
    paned_window.grid_rowconfigure(1, weight=0)

    # row-2: Allow horizontal expansion, prevent vertical expansion
    paned_window.grid_columnconfigure(0, weight=1)
    paned_window.grid_rowconfigure(2, weight=0)

    # row-3: Allow horizontal expansion, prevent vertical expansion
    paned_window.grid_columnconfigure(0, weight=1)
    paned_window.grid_rowconfigure(3, weight=0)

    # row-4: Allow horizontal and vertical expansion
    paned_window.grid_columnconfigure(0, weight=1)
    paned_window.grid_rowconfigure(4, weight=1)

    # row-5: Allow horizontal and vertical expansion
    paned_window.grid_columnconfigure(0, weight=1)
    paned_window.grid_rowconfigure(5, weight=9)

    return paned_window


def build_semantic_group(app, parent, row=0):

    semantic_group = ui.LabelFrame(parent, text="Semantic")
    semantic_group.grid(row=row, column=0, padx=4, pady=(4, 0), sticky="new")

    label_groups = [
        ["anything",    "something",    "space",    "whitespace",       ],
        ["dot",         "alnum",        "graph",    "non-whitespace",   ],
        ["digit",       "number",       "",         "punctuation",      ],
        ["letter",      "word",         "words",    "",                 ],
    ]

    row, col = 0, 0
    for row, group in enumerate(label_groups):
        for col, label in enumerate(group):
            if not label:
                continue
            kwargs = {
                "text": label,
                "onvalue": True, "offvalue": False,
                "variable": app.settings.tabular_arg_has_header_row_flag,
            }
            if col < len(group) - 1:
                kwargs["width"] = 26

            checkbox = ui.CheckBox(semantic_group, **kwargs)
            checkbox.grid(row=row, column=col, sticky="nw")

    variant_group = ui.LabelFrame(semantic_group, text="Variant / Quantity")
    variant_group.grid(row=row+1, column=0, columnspan=col+1, padx=4, pady=(2, 0), sticky="nw")

    label_groups = [
        ["optional",    "some",         "group",        "exact"],
        ["zero_or_one", "zero_or_more", "one_or_more",  "range"],
    ]

    for row, group in enumerate(label_groups):
        for col, label in enumerate(group):
            if not label:
                continue

            if label in ["exact", "range"]:
                if label == "exact":
                    label = ui.Label(variant_group, text="Exact Qty:")
                    label.grid(row=row, column=col, sticky="nw")
                    textbox = ui.TextBox(variant_group, width=10, justify="center",)
                    textbox.grid(row=row, column=col+1, sticky="nw", padx=1, pady=(0, 2))

                    continue

                label = ui.Label(variant_group, text="Qty Range:")
                label.grid(row=row, column=col, sticky="nw")

                textbox = ui.TextBox(variant_group, width=10, justify="center",)
                textbox.grid(row=row, column=col+1, sticky="nw", padx=1, pady=(0, 2))
                textbox = ui.TextBox(variant_group, width=10, justify="center",)
                textbox.grid(row=row, column=col+2, sticky="nw", padx=1, pady=(0, 2))
                continue

            checkbox = ui.CheckBox(variant_group, text=label,
                           variable=app.settings.tabular_arg_has_header_row_flag,
                           width=16,
                           onvalue=True, offvalue=False)
            checkbox.grid(row=row, column=col, sticky="nw")


def build_data_group(app, parent, row=0):
    data_group = ui.LabelFrame(parent, text="Data")
    data_group.grid(row=row, column=0, padx=4, pady=(4, 0), sticky="new")

    rows = []

    for row_pos in range(2):
        row = []
        for col_pos in range(4):
            if row_pos == 0:
                data_group.grid_columnconfigure(col_pos, weight=1, uniform="equal")

            textbox = ui.TextBox(data_group)
            textbox.grid(row=row_pos, column=col_pos, sticky="nsew", padx=1, pady=(0, 2))
            row.append(textbox)
        rows.append(row)
        data_group.grid_rowconfigure(row_pos, weight=0)


def build_controls(app, parent, row=0):
    frame = ui.Frame(parent, width=600, height=40, relief="ridge")
    frame.grid(row=row, column=0, padx=4, pady=4, sticky="new")

    button = ui.Button(frame, text="Build")
    button.grid(row=0, column=0, sticky='nswe', padx=2, pady=4)

    button = ui.Button(frame, text="Aggregate", state="disabled")
    button.grid(row=0, column=1, sticky='nswe', padx=2, pady=4)


    result_group = ui.LabelFrame(parent, text="All Possible Outcomes")
    result_group.grid(row=3, column=0, padx=4, pady=(4, 0), sticky="new")

    label_groups = [
        ["optional_mixed_word_group(var_this_is_very_long_variable)", "optional_mixed_word_group(var_another_long_variable)",],
        ["words(var_v3)", "words(var_v4)"],
    ]

    for row_pos, group in enumerate(label_groups):
        for col_pos, label in enumerate(group):
            if not label:
                continue
            kwargs = {
                "text": label,
                "onvalue": True, "offvalue": False,
                "variable": app.settings.tabular_arg_has_header_row_flag,
            }

            checkbox = ui.CheckBox(result_group, **kwargs)
            checkbox.grid(row=row_pos, column=col_pos, sticky="nw")


def create_textarea(parent, row, name, height_rows):
    frame = ui.Frame(parent, relief="ridge")
    frame.grid(row=row, column=0, sticky="nsew", pady=4)

    frame.columnconfigure(0, weight=1)
    frame.rowconfigure(0, weight=1)

    text = ui.TextArea(
        frame,
        wrap="none",
        state="disabled",
        foreground=ui.readonly_text_bg_color,
        height=height_rows,   # rows of text
        name=name
    )
    text.grid(row=0, column=0, sticky="nsew")

    vbar = ui.Scrollbar(frame, orient="vertical", command=text.yview)
    vbar.grid(row=0, column=1, sticky="ns")

    hbar = ui.Scrollbar(frame, orient="horizontal", command=text.xview)
    hbar.grid(row=1, column=0, sticky="ew")

    text.configure(
        yscrollcommand=vbar.set,
        xscrollcommand=hbar.set
    )

    return text
