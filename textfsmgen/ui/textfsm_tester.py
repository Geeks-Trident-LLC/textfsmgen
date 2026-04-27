"""
textfsmgen.ui.builder
=====================

UI components for the Regex Translator dialog in TextFSMGen.
"""

from typing import Optional, Union
import traceback

from io import StringIO
import pprint
import json
import yaml
import re

from textfsm import TextFSM

from textfsmgen.libs.generic import Position
from textfsmgen.libs.utils import get_data_as_tabular
from textfsmgen.libs.text import decorate_text
from textfsmgen.libs.generic import StatusString
from textfsmgen.libs import file

from textfsmgen import ui
from textfsmgen.ui import usage

from textfsmgen.ui.common import (
    show_message_dialog,
    center_window,
    make_modal,
    clear_text,
    set_text,
    extract_text,
    insert_text
)

window_width = 1100 if ui.is_macos else 860 if ui.is_linux else 720
window_height = 820 if ui.is_macos else 840 if ui.is_linux else 770


def show_dialog(app):
    """Show the dialog window."""

    sync_initial_state(app)

    parent = app.root
    dialog = create_window(parent)
    app.tools.tester.dialog = dialog

    # Register cleanup callback
    dialog.protocol("WM_DELETE_WINDOW", lambda: sync_dialog_state_on_close(app))

    paned_window = ui.PanedWindow(dialog, orient="vertical")
    paned_window.pack(fill="both", expand=True, padx=2, pady=2)

    template_area = create_textarea_frame(app, paned_window, name="template_area",)
    test_data_area = create_textarea_frame(app, paned_window, name="test_data_area")
    result_area = create_textarea_frame(app, paned_window, name="result_area", readonly=True)

    control_area = build_controls_frame(app, paned_window)
    control_area.grid_propagate(False)

    paned_window.add(template_area, weight=1)
    paned_window.add(test_data_area, weight=1)
    paned_window.add(control_area)
    paned_window.add(result_area, weight=1)

    dialog.bind("<Button-1>", lambda e: app.callback_focus(e))

    # Make dialog modal
    make_modal(dialog)


def create_window(parent: Optional[Union[ui.Tk, ui.Toplevel]]):
    """Create and center the snippet translator window."""
    window = ui.Toplevel(parent)
    window.title("TextFSM Tester - TextFSMGen CE")

    ui.set_window_icon(window)

    if parent:
        center_window(
            parent, window, window_width, window_height,
            x_resizable=True, y_resizable=True
        )

    return window


def build_controls_frame(app, parent):
    frame = ui.Frame(parent, width=600, height=32 if ui.is_window else 38, relief="ridge")
    frame.grid(row=0, column=0, padx=4, pady=4, sticky="ew")

    labels = [
        "test", "tabular", "SEPARATOR",
        "sync", "open", "save", "copy", "paste", "reset", "close", "help",
    ]

    mapping = {
        "test": lambda: perform_test_action(app),
        "sync": lambda: perform_sync_action(app),
        "open": lambda: perform_open_action(app),
        "save": lambda: perform_save_action(app),
        "copy": lambda : perform_copy_action(app),
        "paste": lambda : perform_paste_action(app),
        "reset": lambda: perform_reset_action(app),
        "close": lambda: sync_dialog_state_on_close(app),
        "help": lambda : perform_help_action(app),
    }

    btn_width = 6 if ui.is_macos else 7 if ui.is_linux else 8
    position = Position(-1)
    for label in labels:
        if label == "SEPARATOR":
            sep = ui.ttk.Separator(frame, orient="vertical")
            sep.grid(row=0, column=position.next(), sticky="ns", padx=(4, 2), pady=2)
            continue

        if label == "tabular":
            checkbox = ui.TriStateCheckBox(
                frame, label=label.title(),
                state_var=app.tools.tester.checkbox_state_var,
                shared_var=app.tools.tester.output_flag,
                width=18,
            )
            checkbox.grid(row=0, column=position.next(), sticky="nswe", padx=(2, 2), pady=4)
            if ui.is_linux:
                checkbox.configure(anchor="w", justify="left")
            checkbox.configure(
                command=lambda widget=checkbox: cycle_tristate_checkbox(widget, app)    # noqa
            )
            continue

        kwargs = {"width": btn_width, "command": mapping.get(label)}
        button = ui.Button(frame, text=label.title(), **kwargs)
        button.grid(row=0, column=position.next(), sticky='nswe', padx=1, pady=4)

    return frame


def create_textarea_frame(app, parent, name, readonly=False):
    frame = ui.Frame(parent)
    frame.grid(row=0, column=0, sticky="nsew", pady=4)

    frame.columnconfigure(0, weight=1)
    frame.rowconfigure(0, weight=0)
    frame.rowconfigure(1, weight=1)

    kwargs = dict(name=name, wrap="none", relief="ridge", height=5)
    if readonly:
        kwargs["state"] = "disabled"
        kwargs["background"] = ui.readonly_text_bg_color

    if name in ("template_area", "test_data_area"):
        txt = name.replace("_area", "").replace("_", " ").title()
        txt = "TextFSM Template" if txt == "Template" else txt
        label = ui.Label(frame, text=txt)
        label.grid(row=0, column=0, sticky="nsew")

    textarea = ui.TextArea(frame, **kwargs)
    textarea.grid(row=1, column=0, sticky="nsew")

    vbar = ui.Scrollbar(frame, orient="vertical", command=textarea.yview)
    vbar.grid(row=1, column=1, sticky="ns")

    hbar = ui.Scrollbar(frame, orient="horizontal", command=textarea.xview)
    hbar.grid(row=2, column=0, sticky="ew")

    textarea.configure(yscrollcommand=vbar.set, xscrollcommand=hbar.set)

    tool = app.tools.tester

    data_var = name.replace("_area", "_text")
    content = tool.get(data_var).get()
    if content:
        set_text(textarea, content)
    tool.update({name: textarea})

    return frame


def perform_test_action(app):
    """Run a TextFSM test using the template and test data from the UI."""
    tester = app.tools.tester

    template_text = extract_text(tester.template_area).strip()
    test_data_text = extract_text(tester.test_data_area)

    if not template_text:
        show_message_dialog(
            title="Test Action - Empty Template",
            warning="Cannot run test with an empty TextFSM template."
        )
        return

    if not test_data_text:
        proceed = show_message_dialog(
            title="Test Action - Empty Test Data",
            yesno="Test data is empty. Continue anyway?"
        )
        if not proceed:
            return

    rows, success = run_textfsm_parse(template_text, test_data_text)

    if not success:
        set_text(tester.result_area, success)
        return

    render_result(rows, app)


def perform_sync_action(app):
    """Sync snapshot template and test data into the tester UI."""
    tester = app.tools.tester
    snapshot = app.snapshot

    # Clear previous result
    tester.result_text.set("")

    # Extract snapshot values
    template_text = snapshot.template
    test_data_text = snapshot.test_data

    # Update text variables
    tester.template_text.set(template_text)
    tester.test_data_text.set(test_data_text)

    # Update UI text areas
    set_text(tester.template_area, template_text)
    set_text(tester.test_data_area, test_data_text)


def perform_open_action(app):
    """Open a TextFSM file into the tester UI."""

    filetypes = [
        ("TextFSM Templates", "*.template *.textfsm *.fsm"),
        ("Text Files", "*.txt"),
        ("All Files", "*"),
    ]

    filename = ui.filedialog.askopenfilename(filetypes=filetypes)
    if not filename:
        return

    content = file.read(filename)

    if validate_textfsm_template(content):
        set_text(app.tools.tester.template_area, content)
        return
    set_text(app.tools.tester.test_data_area, content)


def perform_save_action(app):
    """Save the active editor area (template, test data, or result) to a file."""
    tool = app.tools.tester
    active = app.prev_widget

    # Validate active area
    valid_areas = (tool.template_area, tool.test_data_area, tool.result_area)
    if active not in valid_areas:
        show_message_dialog(
            title="Save Action — Ambiguous Selection",
            warning="A save target is required. Choose template, test data, or result area."
        )
        return

    # --- Template Area -----------------------------------------------------
    if active is tool.template_area:
        template_text = extract_text(tool.template_area).strip()
        if not template_text:
            show_message_dialog(
                title="Save Action — Empty Template",
                warning="Cannot save because the TextFSM template is empty."
            )
            return

        filename = ui.filedialog.asksaveasfilename(
            title="Save TextFSM Template",
            filetypes=[
                ("TextFSM Templates", "*.template *.textfsm *.fsm"),
                ("All Files", "*"),
            ],
        )
        if filename:
            file.write(filename, template_text)
        return

    # --- Test Data Area ----------------------------------------------------
    if active is tool.test_data_area:
        test_data = extract_text(tool.test_data_area)
        if not test_data:
            show_message_dialog(
                title="Save Action — Empty Test Data",
                warning="Cannot save because the test data is empty."
            )
            return

        filename = ui.filedialog.asksaveasfilename(
            title="Save Test Data",
            filetypes=[
                ("Text Files", "*.txt"),
                ("All Files", "*"),
            ],
        )
        if filename:
            file.write(filename, test_data)
        return

    # --- Result Area -------------------------------------------------------
    if active is tool.result_area:
        result_text = extract_text(tool.result_area)
        if not result_text:
            show_message_dialog(
                title="Save Action — No Test Result",
                warning="Cannot save because the test result is empty."
            )
            return

        mode = tool.output_flag.get().lower()

        if mode == "json":
            title = "Save Action — JSON Result"
            filetypes = [
                ("JSON Files", "*.json"),
                ("All Files", "*"),
            ]
        elif mode == "yaml":
            title = "Save Action — YAML Result"
            filetypes = [
                ("YAML Files", "*.yaml *.yml"),
                ("All Files", "*"),
            ]
        else:
            title = "Save Action — Text Result"
            filetypes = [
                ("Text Files", "*.txt"),
                ("All Files", "*"),
            ]

        filename = ui.filedialog.asksaveasfilename(title=title, filetypes=filetypes)
        if filename:
            file.write(filename, result_text)


def perform_copy_action(app):
    """Open a TextFSM file into the tester UI."""

    tool = app.tools.tester
    prev = app.prev_widget
    widgets = [tool.template_area, tool.test_data_area, tool.result_area]

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
        title="Copy Action — Ambiguous Selection",
        info="A copy target is required. Choose template, test data, or result area."
    )


def perform_paste_action(app):
    """Paste clipboard text into the active editable area."""
    # --- Retrieve clipboard text -------------------------------------------
    try:
        text = app.root.clipboard_get()
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

    if not text:
        show_message_dialog(
            title="Paste Action",
            info="Your clipboard contains no text. No operation performed.",
        )
        return

    # --- Determine paste target --------------------------------------------
    tool = app.tools.tester
    active = app.prev_widget
    editable_areas = (tool.template_area, tool.test_data_area)

    for area in editable_areas:
        area.update_idletasks()
        if area is active:
            insert_text(area, text)
            return

    # --- No valid target ----------------------------------------------------
    show_message_dialog(
        title="Paste Action — Ambiguous Selection",
        info="Please choose the specific editable area you want to paste."
    )


def perform_reset_action(app):
    """Reset all tester fields, flags, and text areas to empty state."""
    tester = app.tools.tester

    # Reset checkbox state
    tester.checkbox_state_var.set(False)

    # Reset text variables
    for var in (
        tester.output_flag,
        tester.template_text,
        tester.test_data_text,
        tester.result_text,
    ):
        var.set("")

    # Clear UI text widgets
    for area in (
        tester.template_area,
        tester.test_data_area,
        tester.result_area,
    ):
        clear_text(area)


def perform_help_action(app):
    """Display the help panel."""
    usage.show_help(app, "tester")


def render_result(rows, app):
    """Render parsed rows into the tester's result area."""
    tester = app.tools.tester
    output_mode = tester.output_flag.get().lower()

    # No rows returned
    if not rows:
        set_text(tester.result_area, "No records were produced by the parser.")
        return

    # Tabular modes
    if output_mode.startswith("tabular"):
        show_index = "index" in output_mode
        result = get_data_as_tabular(rows, with_index=show_index)
        set_text(tester.result_area, result)
        return

    # JSON output
    if output_mode == "json":
        result = json.dumps(rows, indent=2)
        set_text(tester.result_area, result)
        return

    # YAML output
    if output_mode == "yaml":
        result = yaml.dump(rows, indent=2)
        set_text(tester.result_area, result)
        return

    # Fallback: pretty‑printed Python structure
    set_text(tester.result_area, pprint.pformat(rows))


def run_textfsm_parse(template_text, test_data_text):
    """Parse test data using a TextFSM template and return rows + status."""
    try:
        parser = TextFSM(StringIO(template_text))
        rows = parser.ParseTextToDicts(test_data_text)
        return rows, StatusString(status="passed")

    except Exception as ex:
        header = decorate_text(f"{type(ex).__name__}: {ex}")
        traceback_text = traceback.format_exc()
        return [], StatusString(f"{header}\n{traceback_text}", status="failed")


def sync_dialog_state_on_close(app):
    """Persist dialog text areas back into tester state before closing."""
    tester = app.tools.tester

    mappings = (
        (tester.template_area, tester.template_text),
        (tester.test_data_area, tester.test_data_text),
        (tester.result_area, tester.result_text),
    )

    for widget, text_var in mappings:
        text_var.set(extract_text(widget))

    tester.dialog.destroy()


def cycle_tristate_checkbox(widget, app):
    """Advance tri‑state checkbox, update label/state, and re-run parsing."""
    tester = app.tools.tester

    # Advance through 5 states
    widget.state_index = (widget.state_index + 1) % 5

    states = (
        (False, "Tabular"),
        (True,  "Tabular"),
        (True,  "Tabular with Index"),
        (True,  "JSON"),
        (True,  "YAML"),
    )

    is_checked, label = states[widget.state_index]

    # Update UI state
    widget.state_var.set(is_checked)
    widget.configure(text=label)

    # Update shared output mode (empty when state_index == 0)
    widget.shared_var.set(label.lower() if widget.state_index else "")

    # Re-run parser and update result
    template_text = extract_text(tester.template_area)
    test_data_text = extract_text(tester.test_data_area)

    rows, status = run_textfsm_parse(template_text, test_data_text)
    if status:
        render_result(rows, app)


def sync_initial_state(app):
    """Initialize tester fields from snapshot if no existing user input."""
    tester = app.tools.tester

    # Skip if user already typed something
    if tester.template_text.get() or tester.test_data_text.get():
        return

    tester.result_text.set("")

    template_text = app.snapshot.template
    test_data_text = app.snapshot.test_data

    rows, status = run_textfsm_parse(template_text, test_data_text)
    if status:
        tester.template_text.set(template_text)
        tester.test_data_text.set(test_data_text)


def validate_textfsm_template(template):
    template = template.strip()
    if not template:
        return False

    try:
        TextFSM(StringIO(template.strip()))
        return True
    except Exception as ex:     # noqa
        checks = []

        for line in template.splitlines():
            if re.match(r"Value ", line) and not checks:
                checks.append(True)
                continue

            if re.match(r"Start ", line) and len(checks) == 1:
                checks.append(True)
                continue

            if re.match(r" {2,4}\^", line) and len(checks) == 2:
                return True

        return False



