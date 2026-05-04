"""
textfsmgen.ui.builder
=====================

UI components for the Regex Translator dialog in TextFSMGen.
"""
from typing import Optional, Union

import re

from textfsmgen.engine.translate import make_translator
from textfsmgen.libs.datatype import trim_empty_edges, trim_blank_edges, add_if_absent
from textfsmgen.tools.explain import SnippetExplanation
from textfsmgen.tools.samples import SamplesGenerator

from textfsmgen.core.patterns import ElementPattern

from textfsmgen.libs.text import enclose_string
from textfsmgen.libs.generic import Position

from textfsmgen import ui
from textfsmgen.ui import usage, common
import yaml

from textfsmgen.ui.common import (
    show_message_dialog,
    center_window,
    make_modal,
    clear_text,
    set_text,
    extract_text,
)

window_width = 1020 if ui.is_macos else 820 if ui.is_linux else 740
window_height = 770 if ui.is_macos else 780 if ui.is_linux else 720

def show_dialog(app):
    """Show the dialog window."""
    b = app.tools.builder
    parent = app.root

    dialog = create_window(parent)

    # Register cleanup callback
    dialog.protocol("WM_DELETE_WINDOW", lambda: on_dialog_close(app, dialog))

    paned_window = build_pane_window(dialog)

    b.semantic_group = build_semantic_group(app, paned_window, row=0)

    build_data_group(app, paned_window, row=1)

    build_controls(app, paned_window, row=2)

    b.outcomes_group = build_possible_outcomes(app, paned_window, row=3)

    b.pattern_area = create_textarea(paned_window, row=4, name="pattern_area", height_rows=2)
    b.explain_area = create_textarea(paned_window, row=5, name="explain_area", height_rows=10)
    dialog.bind("<Button-1>", lambda e: app.callback_focus(e))

    # Make dialog modal
    make_modal(dialog)


def create_window(parent: Optional[Union[ui.Tk, ui.Toplevel]]):
    """Create and center the snippet translator window."""
    window = ui.Toplevel(parent)
    window.title("Regex Builder - TextFSMGen CE")

    common.set_window_icon(window)

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
    semantic_group.grid(row=row, column=0, padx=4, pady=(4, 0), sticky="ew")

    label_groups = [
        ["anything",    "something",    "space",        "whitespace",       ],
        ["dot",         "alnum",        "graph",        "non_whitespace",   ],
        ["digit",       "number",       "mixed_number", "punctuation",      ],
        ["letter",      "word",         "mixed_word",   "",                 ],
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

            checkbox = common.TriStateCheckBox(semantic_group, **kwargs)
            checkbox.grid(row=row_pos, column=col_pos, sticky="w")
            checkbox.configure(command=lambda c=checkbox: on_click_tristate_checkbox(c, app))

    variant_group = ui.LabelFrame(semantic_group, text="Variant / Quantity")
    variant_group.grid(row=row_pos+1, column=0, columnspan=col_pos+1, padx=4, pady=(2, 0), sticky="w")

    label_groups = [
        ["optional",    "optional_group",   "group",        "optional_items",   "items",    "exact"],
        ["zero_or_one", "zero_or_more",     "one_or_more",  "some",             "",         "range"],
    ]

    for row_pos, group in enumerate(label_groups):
        for col_pos, label in enumerate(group):
            if not label:
                continue

            if label in ["exact", "range"]:
                if label == "exact":
                    label = ui.Label(variant_group, text="exact qty:")
                    label.grid(row=row_pos, column=col_pos, sticky="w", padx=(20, 2))
                    textbox = ui.TextBox(
                        variant_group, width=10, justify="center",
                        textvariable=app.tools.builder.exact_quantity,
                    )
                    textbox.grid(row=row_pos, column=col_pos+1, sticky="w", padx=1, pady=(0, 2))

                    continue

                label = ui.Label(variant_group, text="qty range:")
                label.grid(row=row_pos, column=col_pos, sticky="w", padx=(20, 2))

                textbox = ui.TextBox(
                    variant_group, width=10, justify="center",
                    textvariable=app.tools.builder.range_min_quantity,
                )
                textbox.grid(row=row_pos, column=col_pos+1, sticky="w", padx=1, pady=(0, 2))
                textbox = ui.TextBox(
                    variant_group, width=10, justify="center",
                    textvariable=app.tools.builder.range_max_quantity,
                )
                textbox.grid(row=row_pos, column=col_pos+2, sticky="w", padx=1, pady=(0, 2))
                continue

            checkbox = ui.CheckBox(variant_group, text=label,
                variable=app.tools.builder.variant_flag,
                onvalue=label, offvalue="", cursor="hand2",
                command=lambda: on_click_for_refresh(app)
            )
            checkbox.grid(row=row_pos, column=col_pos, sticky="w")

    return semantic_group


def build_data_group(app, parent, row=0):
    data_group = ui.LabelFrame(parent, text="Data")
    data_group.grid(row=row, column=0, padx=4, pady=(4, 0), sticky="ew")

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

    return data_group


def build_controls(app, parent, row=0):
    frame = ui.Frame(parent, width=600, height=40, relief="ridge")
    frame.grid(row=row, column=0, padx=4, pady=4, sticky="ew")

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
                "command": lambda: on_click_for_refresh(app)
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

    return frame


def build_possible_outcomes(app, parent, row=0):    # noqa
    outcomes_group = common.DynamicCheckboxGroup(
        parent, title="Possible Outcomes",
    )
    outcomes_group.grid(row=row, column=0, padx=4, pady=(4, 0), sticky="ew")
    return outcomes_group


def create_textarea(parent, row, name, height_rows):
    frame = ui.Frame(parent, relief="ridge")
    frame.grid(row=row, column=0, sticky="nsew", pady=4)

    frame.columnconfigure(0, weight=1)
    frame.rowconfigure(0, weight=1)

    textarea = ui.TextArea(
        frame,
        wrap="none",
        state="disabled",
        background=ui.readonly_text_bg_color,
        height=height_rows,   # rows of text
        name=name
    )
    textarea.grid(row=0, column=0, sticky="nsew")

    vbar = ui.Scrollbar(frame, orient="vertical", command=textarea.yview)
    vbar.grid(row=0, column=1, sticky="ns")

    hbar = ui.Scrollbar(frame, orient="horizontal", command=textarea.xview)
    hbar.grid(row=1, column=0, sticky="ew")

    textarea.configure(
        yscrollcommand=vbar.set,
        xscrollcommand=hbar.set
    )

    return textarea


def on_dialog_close(app, dialog):
    """Cleanup when dialog closes."""
    perform_reset_action(app)
    dialog.destroy()


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
        b.outcomes_value,
    ):
        var.set(empty)

    # Reset boolean flags
    b.allowed_empty_flag.set(False)

    # Reset list‑based data
    for var in b.shared_data_list:
        var.set(empty)

    # Reset widget groups
    b.outcomes_group.reset()

    # Reset TriStateCheckBox widgets
    for child in b.semantic_group.winfo_children():
        if isinstance(child, common.TriStateCheckBox):
            child.reset()

    clear_text(b.pattern_area)
    clear_text(b.explain_area)


def perform_copy_action(app):
    """Copy clipboard text into editable areas; warn on readonly ones."""

    b = app.tools.builder
    prev = app.prev_widget
    widgets = [b.pattern_area, b.explain_area]

    for widget in widgets:
        if widget is prev:
            widget.update_idletasks()
            content = widget.selection_get() if widget.tag_ranges("sel") else extract_text(widget)

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
        info=(
            "Please choose the specific area you want to copy.\n\n"
            "The Copy feature only works for two areas:\n"
            "  • Pattern area — displays the generated Python pattern code\n"
            "  • Explanation area — displays the explanation for the pattern and snippet\n\n"
            "For all other fields, please copy manually using Ctrl+C."
        ),
    )


def perform_paste_action(app):
    """Paste clipboard text into the appropriate target, with clear error handling."""
    try:
        data = app.root.clipboard_get()
    except Exception as ex:
        show_message_dialog(
            title="Clipboard Empty",
            info=(
                "There is no text available to paste from the clipboard.\n"
                + "-" * 70 + "\n"
                f"{type(ex).__name__}: {ex}"
            ),
        )
        return

    if not data:
        show_message_dialog(
            title="Paste Action",
            info="Your clipboard contains no text. No operation performed.",
        )
        return

    prev = app.prev_widget
    if isinstance(prev, ui.TextBox):
        prev.delete(0, "end")
        prev.insert(0, data)
        return

    show_message_dialog(
        title="Ambiguous Paste Action",
        info="Please choose the specific textbox you want to paste."
    )


def perform_help_action(app):
    """Display the Regex Builder help panel."""
    usage.show_help(app, "regex")


def perform_build_action(app):
    """Build possible outcome snippets from semantic and data inputs."""
    b = app.tools.builder

    # Build parameter list
    params = []
    var_name = b.var_name.get()
    if var_name:
        params.append(f"var_{var_name}")
    if b.allowed_empty_flag.get():
        params.append("or_empty")
    params_txt = ", ".join(params)

    # Quantity + variant inputs
    variant = b.variant_flag.get()
    qty_exact = b.exact_quantity.get().strip()
    qty_min = b.range_min_quantity.get().strip()
    qty_max = b.range_max_quantity.get().strip()

    snippets = []

    # Data-group snippet
    data_snippet, samples = derive_snippet_from_data(app)
    if data_snippet:
        snippets.append(data_snippet)
        b.snippet_and_samples = [data_snippet, samples]

    # Semantic list
    semantic_text = b.shared_semantic_list.get()

    # Nothing selected and no data → warn
    if not semantic_text and not snippets or semantic_text == "[]":
        # Reset widget groups
        b.outcomes_group.reset()

        clear_text(b.pattern_area)
        clear_text(b.explain_area)

        if not semantic_text:
            show_message_dialog(
                title="Missing Semantic Selection or Data",
                warning=(
                    "No semantic items are selected and no data is provided.\n"
                    "Please choose a semantic item or enter data in the Data Group."
                ),
            )
        return

    # Build semantic-based snippets
    if semantic_text:
        for semantic in yaml.safe_load(semantic_text):

            # Special-case semantics
            if semantic in ("anything", "something"):
                snippets.append(f"{semantic}({params_txt})")

                continue

            # Variant handling
            if variant:
                if variant == "optional_group":
                    add_if_absent(f"optional_{semantic}_group({params_txt})", snippets)
                elif variant == "group":
                    add_if_absent(f"{semantic}_group({params_txt})", snippets)
                elif variant == "optional_items":
                    add_if_absent(f"optional_{semantic}_items({params_txt})", snippets)
                elif variant == "items":
                    add_if_absent(f"{semantic}_items({params_txt})", snippets)
                else:
                    add_if_absent(f"{variant}_{semantic}({params_txt})", snippets)
                continue

            # Exact quantity
            if qty_exact:
                add_if_absent(f"{qty_exact}_{semantic}({params_txt})", snippets)
                continue

            # Range quantity
            if qty_min or qty_max:
                if qty_min and not qty_max:
                    qty_max = "n"
                if not qty_min and qty_max:
                    qty_min = "0"
                add_if_absent(f"{qty_min}_to_{qty_max}_{semantic}({params_txt})", snippets)
                continue

            # Default
            add_if_absent(f"{semantic}({params_txt})", snippets)

    # Display results
    b.outcomes_group.grid(row=3, column=0, padx=4, pady=(4, 0), sticky="ew")
    b.outcomes_group.build(snippets, state_var=b.outcomes_value)

    for checkbox in b.outcomes_group.checkboxes:
        checkbox.configure(command=lambda: on_click_outcome_checkbox(app))

    if b.outcomes_group.checkboxes:
        first_checkbox = b.outcomes_group.checkboxes[0]
        first_checkbox.invoke()
        if not b.outcomes_value.get():
            first_checkbox.invoke()


def perform_aggregate_action(app):  # noqa
    show_message_dialog(
        title="Aggregate Action",
        info="The build functionality is not implemented yet.",
    )


def derive_snippet_from_data(app):
    """Build a keyword snippet from the Data Group inputs."""
    b = app.tools.builder
    var_name = b.var_name.get()

    params = []
    if var_name:
        params.append(f"var_{var_name}")

    # Raw items from UI
    items = [var.get() for var in b.shared_data_list]

    # Non-empty (after stripping) items
    cleaned = [s.strip() for s in items if s.strip()]

    # Case 1: actual data values exist
    if cleaned:
        # Detect internal empties (after trimming edges)
        inner = trim_blank_edges(items)
        if any(s.strip() == "" for s in inner):
            params.append("or_empty")

        params_txt = ", ".join(params)
        translator = make_translator(*cleaned, multiple=False)
        snippet = translator.to_snippet()
        return snippet.replace("()", f"({params_txt})"), inner

    # Case 2: no meaningful values, but some raw entries exist
    if any(items):
        inner = trim_empty_edges(items)
        if any(bool(s) for s in inner):
            params.append("or_empty")

        params_txt = ", ".join(params)

        # Detect whitespace vs non-whitespace
        has_non_space = any(re.match(r"[^ \r\n]", s) for s in items if s)
        base = "whitespaces" if has_non_space else "spaces"

        return f"{base}({params_txt})", inner

    # Case 3: nothing at all
    return "", ""


def on_click_outcome_checkbox(app):
    """Render pattern and explanation for the selected outcome snippet."""
    b = app.tools.builder
    snippet = b.outcomes_value.get()

    if not snippet:
        clear_text(b.pattern_area)
        clear_text(b.explain_area)
        return

    # Build explanation node
    if b.snippet_and_samples and snippet in b.snippet_and_samples:
        samples = b.snippet_and_samples[-1]
        node = SnippetExplanation(snippet, test_samples=samples)
    else:
        samples_gen = SamplesGenerator(snippet)
        if not samples_gen:
            clear_text(b.pattern_area)
            msg = (
                "TextFSMGen cannot generate sample data for:\n"
                f"    {snippet}\n"
                "Please submit a bug report for this case.\n"
            )
            set_text(b.explain_area, msg)
            return
        samples = samples_gen.generate()
        node = SnippetExplanation(snippet, test_samples=samples)

    # Build pattern
    pattern = ElementPattern(snippet)

    # Update UI
    set_text(b.pattern_area, f"pattern = r{enclose_string(pattern)}")
    set_text(b.explain_area, node.explanation)


def on_click_tristate_checkbox(widget, app):
    """Advance widget.state_index and update UI + shared state."""
    is_special = widget.label in ("anything", "something")

    # Determine next state count (2-state or 3-state)
    max_state = 1 if is_special else 2
    widget.state_index = (widget.state_index + 1) % (max_state + 1)

    # Update UI text + BooleanVar
    if widget.state_index == 0:
        widget.state_var.set(False)
        widget.config(text=widget.label)

    elif widget.state_index == 1:
        widget.state_var.set(True)
        widget.config(text=widget.label)

    else:  # state_index == 2 (plural form)
        widget.state_var.set(True)
        widget.config(text=f"{widget.label}s")

    sync_shared_var(widget)
    perform_build_action(app)


def sync_shared_var(widget):
    """Update the shared StringVar list to reflect the current state."""
    try:
        items = yaml.safe_load(widget.shared_var.get()) or []
    except Exception:   # noqa
        items = []

    singular = widget.label
    plural = f"{widget.label}s"
    # Remove both forms first
    items = [x for x in items if x not in (singular, plural)]

    # Add the active form
    if widget.state_index == 1:
        items.insert(0, singular)
    elif widget.state_index == 2:
        items.insert(0, plural)

    widget.shared_var.set(str(items))


def on_click_for_refresh(app):
    """Trigger a rebuild only when the shared semantic list is non‑empty."""
    txt = app.tools.builder.shared_semantic_list.get()

    # Normalize empty or placeholder values
    if not txt or txt.strip() in ("[]", ""):
        return

    perform_build_action(app)
