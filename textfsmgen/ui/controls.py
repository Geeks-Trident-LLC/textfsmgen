"""
textfsmgen.ui.controls
======================

Reusable UI controls buttons for the TextFSMGen application.
"""

import tkinter as tk

from textfsmgen import ui
from textfsmgen.ui import callback

from textfsmgen.ui.common import (
Position
)


def build_action_buttons(app) -> None:
    """Assemble all main action buttons for the application UI."""
    build_primary_buttons(app)
    build_secondary_buttons(app)


def build_primary_buttons(app) -> None:
    """Create the first-row action buttons for the main UI."""
    btn_width = 6 if ui.is_macos else 8
    col = Position()

    parent = app.frames.buttons

    # Test Data
    app.test_data_btn = ui.Button(
        parent,
        name="test_data_btn",
        state=tk.DISABLED,
        textvariable=app.settings.test_data_btn_name,
        command=lambda: callback.test_data_btn(app),
        width=btn_width,
    )
    app.test_data_btn.grid(row=0, column=col.value, padx=(2, 0), pady=(2, 0))

    # Open
    app.buttons.open = ui.Button(
        parent,
        name="open_btn",
        text="Open",
        command=lambda: callback.open_file(app),
        width=btn_width,
    )
    app.buttons.open.grid(row=0, column=col.increment(), padx=(2, 0), pady=(2, 0))

    # Save As
    app.buttons.save = ui.Button(
        parent,
        name="save_btn",
        text="Save",
        state=tk.DISABLED,
        command=lambda: callback.save(app),
        width=btn_width,
    )
    app.buttons.save.grid(row=0, column=col.increment(), pady=(2, 0))

    # Copy
    app.buttons.copy = ui.Button(
        parent,
        name="copy_btn",
        text="Copy",
        state=tk.DISABLED,
        command=lambda: callback.copy(app),
        width=btn_width,
    )
    app.buttons.copy.grid(row=0, column=col.increment(), pady=(2, 0))

    # Paste
    app.buttons.paste = ui.Button(
        parent,
        name="paste_btn",
        text="Paste",
        command=lambda: callback.paste(app),
        width=btn_width,
    )
    app.buttons.paste.grid(row=0, column=col.increment(), pady=(2, 0))

    # Clear
    app.buttons.clear = ui.Button(
        parent,
        name="clear_btn",
        text="Clear",
        command=lambda: callback.clear(app),
        width=btn_width,
    )
    app.buttons.clear.grid(row=0, column=col.increment(), pady=(2, 0))

    # Build
    app.buttons.build = ui.Button(
        parent,
        name="build_btn",
        text="Build",
        command=lambda: callback.build(app),
        width=btn_width,
    )
    app.buttons.build.grid(row=0, column=col.increment(), pady=(2, 0))

    # Result
    app.buttons.result = ui.Button(
        parent,
        name="result_btn",
        text="Result",
        state=tk.DISABLED,
        command=lambda: callback.show_parsed_result(app),
        width=btn_width,
    )
    app.buttons.result.grid(row=0, column=col.increment(), pady=(2, 0))


def build_secondary_buttons(app) -> None:
    """Create the second-row action buttons for the main UI."""
    col = Position()
    btn_width = 6 if ui.is_macos else 8

    parent = app.frames.buttons

    # Snippet
    app.buttons.python = ui.Button(
        parent,
        name="python_btn",
        text="Python",
        command=lambda: callback.create_python_script(app),
        width=btn_width,
    )
    app.buttons.python.grid(row=1, column=col.value, padx=(2, 0), pady=(0, 2))

    # Unittest
    app.buttons.unittest = ui.Button(
        parent,
        name="unittest_btn",
        text="Unittest",
        command=lambda: callback.create_unittest_script(app),
        width=btn_width,
    )
    app.buttons.unittest.grid(row=1, column=col.increment(), padx=(2, 0), pady=(0, 2))

    # Pytest
    app.buttons.pytest = ui.Button(
        parent,
        name="pytest_btn",
        text="Pytest",
        command=lambda: callback.create_pytest_script(app),
        width=btn_width,
    )
    app.buttons.pytest.grid(row=1, column=col.increment(), padx=(2, 0), pady=(0, 2))
