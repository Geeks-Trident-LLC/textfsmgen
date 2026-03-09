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

    parent = app.buttons_frame

    # Test Data
    app.test_data_btn = ui.Button(
        parent,
        name="main_test_data_btn",
        state=tk.DISABLED,
        textvariable=app.test_data_btn_var,
        command=lambda: callback.test_data_btn(app),
        width=btn_width,
    )
    app.test_data_btn.grid(row=0, column=col.value, padx=(2, 0), pady=(2, 0))

    # Open
    app.open_file_btn = ui.Button(
        parent,
        name="main_open_btn",
        text="Open",
        command=lambda: callback.open_file(app),
        width=btn_width,
    )
    app.open_file_btn.grid(row=0, column=col.increment(), padx=(2, 0), pady=(2, 0))

    # Save As
    app.save_as_btn = ui.Button(
        parent,
        name="main_save_as_btn",
        text="Save As",
        state=tk.DISABLED,
        command=lambda: callback.save_as_btn(app),
        width=btn_width,
    )
    app.save_as_btn.grid(row=0, column=col.increment(), pady=(2, 0))

    # Copy
    app.copy_text_btn = ui.Button(
        parent,
        name="main_copy_btn",
        text="Copy",
        state=tk.DISABLED,
        command=lambda: callback.copy_text_btn(app),
        width=btn_width,
    )
    app.copy_text_btn.grid(row=0, column=col.increment(), pady=(2, 0))

    # Paste
    app.paste_text_btn = ui.Button(
        parent,
        name="main_paste_btn",
        text="Paste",
        command=lambda: callback.paste_text_btn(app),
        width=btn_width,
    )
    app.paste_text_btn.grid(row=0, column=col.increment(), pady=(2, 0))

    # Clear
    app.clear_text_btn = ui.Button(
        parent,
        name="main_clear_btn",
        text="Clear",
        command=lambda: callback.clear_text_btn(app),
        width=btn_width,
    )
    app.clear_text_btn.grid(row=0, column=col.increment(), pady=(2, 0))

    # Build
    app.build_btn = ui.Button(
        parent,
        name="main_build_btn",
        textvariable=app.build_btn_var,
        command=lambda: callback.build_btn(app),
        width=btn_width,
    )
    app.build_btn.grid(row=0, column=col.increment(), pady=(2, 0))

    # Result
    app.result_btn = ui.Button(
        parent,
        name="main_result_btn",
        text="Result",
        state=tk.DISABLED,
        command=lambda: callback.result_btn(app),
        width=btn_width,
    )
    app.result_btn.grid(row=0, column=col.increment(), pady=(2, 0))


def build_secondary_buttons(app) -> None:
    """Create the second-row action buttons for the main UI."""
    col = Position()
    btn_width = 6 if ui.is_macos else 8

    parent = app.buttons_frame

    # Snippet
    app.snippet_btn = ui.Button(
        parent,
        name="main_snippet_btn",
        text="Snippet",
        command=lambda: callback.snippet_btn(app),
        width=btn_width,
    )
    app.snippet_btn.grid(row=1, column=col.value, padx=(2, 0), pady=(0, 2))

    # Unittest
    app.unittest_btn = ui.Button(
        parent,
        name="main_unittest_btn",
        text="Unittest",
        command=lambda: callback.unittest_btn(app),
        width=btn_width,
    )
    app.unittest_btn.grid(row=1, column=col.increment(), padx=(2, 0), pady=(0, 2))

    # Pytest
    app.pytest_btn = ui.Button(
        parent,
        name="main_pytest_btn",
        text="Pytest",
        command=lambda: callback.pytest_btn(app),
        width=btn_width,
    )
    app.pytest_btn.grid(row=1, column=col.increment(), padx=(2, 0), pady=(0, 2))
