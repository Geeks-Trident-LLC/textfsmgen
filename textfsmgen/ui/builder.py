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

    build_possible_outcomes(app, paned_window, row=3)

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

    app.tools.builder.semantic_group = semantic_group

    label_groups = [
        ["anything",    "something",    "space",        "whitespace",       ],
        ["dot",         "alnum",        "graph",        "non-whitespace",   ],
        ["digit",       "number",       "mixed-number", "punctuation",      ],
        ["letter",      "word",         "mixed-word",   "",                 ],
    ]

    row_pos, col_pos = 0, 0
    for row_pos, group in enumerate(label_groups):
        for col_pos, label in enumerate(group):
            if row_pos == 0:
                semantic_group.grid_columnconfigure(col_pos, weight=1, uniform="equal")

            if not label:
                continue

            kwargs = {
                "label": label,
                "shared_var": app.tools.builder.shared_semantic_list,
            }

            checkbox = ui.TriStateCheckBox(semantic_group, **kwargs)
            checkbox.grid(row=row_pos, column=col_pos, sticky="nw")

    variant_group = ui.LabelFrame(semantic_group, text="Variant / Quantity")
    variant_group.grid(row=row_pos+1, column=0, columnspan=col_pos+1, padx=4, pady=(2, 0), sticky="nw")

    label_groups = [
        ["optional",    "optional_group",   "group",        "some", "exact"],
        ["zero_or_one", "zero_or_more",     "one_or_more",  "",     "range"],
    ]

    for row_pos, group in enumerate(label_groups):
        for col_pos, label in enumerate(group):
            if not label:
                continue

            if label in ["exact", "range"]:
                if label == "exact":
                    label = ui.Label(variant_group, text="exact qty:")
                    label.grid(row=row_pos, column=col_pos, sticky="nw", padx=(20, 2))
                    textbox = ui.TextBox(
                        variant_group, width=10, justify="center", state="readonly",
                        textvariable=app.tools.builder.exact_quantity,
                    )
                    textbox.grid(row=row_pos, column=col_pos+1, sticky="nw", padx=1, pady=(0, 2))

                    continue

                label = ui.Label(variant_group, text="qty range:")
                label.grid(row=row_pos, column=col_pos, sticky="nw", padx=(20, 2))

                textbox = ui.TextBox(
                    variant_group, width=10, justify="center", state="readonly",
                    textvariable=app.tools.builder.range_min_quantity,
                )
                textbox.grid(row=row_pos, column=col_pos+1, sticky="nw", padx=1, pady=(0, 2))
                textbox = ui.TextBox(
                    variant_group, width=10, justify="center", state="readonly",
                    textvariable=app.tools.builder.range_max_quantity,
                )
                textbox.grid(row=row_pos, column=col_pos+2, sticky="nw", padx=1, pady=(0, 2))
                continue

            checkbox = ui.CheckBox(variant_group, text=label,
                variable=app.tools.builder.variant_flag,
                onvalue=label, offvalue="", cursor="hand2",
            )
            checkbox.grid(row=row_pos, column=col_pos, sticky="nw")


def build_data_group(app, parent, row=0):
    data_group = ui.LabelFrame(parent, text="Data")
    data_group.grid(row=row, column=0, padx=4, pady=(4, 0), sticky="new")

    rows = []
    index = 0
    for row_pos in range(2):
        row = []
        for col_pos in range(4):
            if row_pos == 0:
                data_group.grid_columnconfigure(col_pos, weight=1, uniform="equal")

            textbox = ui.TextBox(
                data_group,
                textvariable=app.tools.builder.shared_data_list[index],
            )
            textbox.grid(
                row=row_pos, column=col_pos,
                sticky="nsew", padx=1, pady=(0, 2)
            )
            row.append(textbox)
            index += 1
        rows.append(row)
        data_group.grid_rowconfigure(row_pos, weight=0)


def build_controls(app, parent, row=0):
    frame = ui.Frame(parent, width=600, height=40, relief="ridge")
    frame.grid(row=row, column=0, padx=4, pady=4, sticky="new")

    labels = [
        "build", "aggregate", "SEPARATOR",
        "var_name", "allowed empty", "SEPARATOR",
        "copy", "paste", "reset", "help",
    ]

    mapping = {
        "reset": lambda: perform_reset_action(app),
        "copy": lambda : perform_copy_action(app),
        "paste": lambda : perform_paste_action(app),
        "help": lambda : perform_help_action(app),

        "build": lambda : perform_build_action(app),
        "aggregate": lambda : perform_aggregate_action(app),
    }

    btn_width = 6 if ui.is_macos else 7 if ui.is_linux else 8
    position = Position(-1)
    for label in labels:
        if label == "SEPARATOR":
            sep = ui.ttk.Separator(frame, orient="vertical")
            sep.grid(row=0, column=position.next(), sticky="ns", padx=(4, 2), pady=2)
            continue

        if label == "var_name":
            label = ui.Label(frame, text="Variable:")
            label.grid(row=0, column=position.next(), sticky="nswe", padx=(6, 2), pady=4)
            textbox = ui.TextBox(
                frame, width=14, justify="left",
                textvariable=app.tools.builder.var_name
            )
            textbox.grid(row=0, column=position.next(), sticky="nswe", pady=4)
            continue

        if label == "allowed empty":
            kwargs = {
                "text": label.title(),
                "onvalue": True, "offvalue": False,
                "variable": app.tools.builder.allowed_empty_flag,
                "cursor": "hand2",
            }

            checkbox = ui.CheckBox(frame, **kwargs)
            checkbox.grid(row=0, column=position.next(), sticky="nswe", padx=(6, 2), pady=4)
            continue

        kwargs = (
            {"state": "disabled", "width": btn_width + 3, "command": mapping.get(label)}
            if label == "aggregate" else
            {"width": btn_width, "command": mapping.get(label)}
        )
        button = ui.Button(frame, text=label.title(), **kwargs)
        button.grid(row=0, column=position.next(), sticky='nswe', padx=2, pady=4)


def build_possible_outcomes(app, parent, row=0):
    outcomes_group = ui.DynamicCheckboxGroup(parent, title="Possible Outcomes")
    outcomes_group.grid(row=row, column=0, padx=4, pady=(4, 0), sticky="new")
    app.tools.builder.possible_outcomes_group = outcomes_group


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


def perform_reset_action(app):
    """Reset all Regex Builder fields, flags, and widgets to defaults."""
    b = app.tools.builder
    empty = ""

    # Reset scalar fields
    for var in (
        b.shared_semantic_list,
        b.exact_quantity,
        b.range_min_quantity,
        b.range_max_quantity,
        b.variant_flag,
        b.var_name,
        b.possible_outcomes_value,
    ):
        var.set(empty)

    # Reset boolean flags
    b.allowed_empty_flag.set(False)

    # Reset list‑based data
    for var in b.shared_data_list:
        var.set(empty)

    # Reset widget groups
    b.possible_outcomes_group.reset()

    # Reset TriStateCheckBox widgets
    for child in b.semantic_group.winfo_children():
        if isinstance(child, ui.TriStateCheckBox):
            child.reset()


def perform_copy_action(app):
    show_message_dialog(
        title="Copy Action",
        info="The copy functionality is not implemented yet.",
    )


def perform_paste_action(app):
    show_message_dialog(
        title="Paste Action",
        info="The paste functionality is not implemented yet.",
    )


def perform_help_action(app):
    """Display the Regex Builder help panel."""
    usage.show_help(app, "regex")


def perform_build_action(app):
    label_groups = [
        "optional_mixed_word_group(var_abc_xyz, or_empty)",
        "optional_mixed_word_group(var_v2)",
        "optional_mixed_word_group(var_another_super_long_variable_that_must_stay_in_one_line)",
        "words(var_v3)",
        "optional_mixed_word_group(var_another_long_variable)"
    ]
    b = app.tools.builder
    b.possible_outcomes_group.grid(row=3, column=0, padx=4, pady=(4, 0), sticky="new")
    b.possible_outcomes_group.build(label_groups, state_var=b.possible_outcomes_value)


def perform_aggregate_action(app):
    show_message_dialog(
        title="Aggregate Action",
        info="The build functionality is not implemented yet.",
    )