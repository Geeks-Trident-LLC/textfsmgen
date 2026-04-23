"""
textfsmgen.ui.controls
======================

Reusable UI controls buttons for the TextFSMGen application.
""" # noqa

import re

from textfsmgen import ui
from textfsmgen.ui import (
    callback,
    settings,
    usage,
    snippet,
    builder,

)


def build_action_buttons(app) -> None:
    """Assemble all main action buttons for the application UI."""

    parent = app.frames.controls

    top = ui.Frame(parent, width=600, height=5,)
    top.pack(side="top", fill="x", padx=2, pady=2)

    sep = ui.ttk.Separator(parent, orient="horizontal")
    sep.pack(fill="x", padx=4)

    bottom = ui.Frame(parent, width=600, height=5,)
    bottom.pack(side="bottom", fill="x", padx=2, pady=2)

    build_primary_buttons(app, top)
    build_secondary_buttons(app, bottom)


def build_primary_buttons(app, parent) -> None:
    """Create the first-row action buttons for the main UI."""
    btn_width = 6 if ui.is_macos else 8
    button_lst = (
        (app.settings.test_data_btn_name, "normal", lambda: callback.toggle_test_data_mode(app),),
        ("SEPARATOR", None, None),
        ("open", "normal", lambda: callback.open_file(app)),
        ("save", "disabled", lambda: callback.save(app)),
        ("copy", "disabled", lambda: callback.copy(app)),
        ("paste", "normal", lambda: callback.paste(app)),
        ("clear", "normal", lambda: callback.clear(app)),
        ("SEPARATOR", None, None),
        ("build", "normal", lambda: callback.build(app)),
        ("result", "disabled", lambda: callback.show_result(app)),
        ("SEPARATOR", None, None),
        ("settings", "normal", lambda: settings.show_dialog(app)),
        ("help", "normal", lambda: usage.show_help(app, "app")),
    )

    for pos, options in enumerate(button_lst):
        text, state, command = options

        if text == "SEPARATOR":
            sep = ui.ttk.Separator(parent, orient="vertical")
            sep.grid(row=0, column=pos, sticky="ns", padx=(4, 2), pady=2)
            continue

        kwargs = {
            "state": state,
            "command": command,
            "width": btn_width + (2 if pos == 0 else 0),
        }
        if isinstance(text, str):
            name = text
            kwargs.update(text=text.title(), name=f"{name}_btn")
        else:
            name = "test_data"
            kwargs.update(textvariable=text, name=f"{name}_btn")

        button = ui.Button(parent, **kwargs)
        button.grid(row=0, column=pos, padx=(2, 0), pady=(2, 0))
        app.buttons.update({name: button})


def build_secondary_buttons(app, parent) -> None:
    """Create the second-row action buttons for the main UI."""

    btn_width = 6 if ui.is_macos else 8

    button_lst = (
        ("python", "disabled", lambda: callback.create_python_script(app)),
        ("unittest", "disabled", lambda: callback.create_unittest_script(app)),
        ("pytest", "disabled", lambda: callback.create_pytest_script(app)),
        ("SEPARATOR", None, None),
        ("execute", "disabled", lambda: callback.execute_test_script(app)),
        ("SEPARATOR", None, None),
        ("snippet translator", "normal", lambda: snippet.show_dialog(app)),
        ("regex builder", "normal", lambda: builder.show_dialog(app)),
        ("keyword query assistant", "disabled", lambda: None),
    )

    mapping = {
        "snippet_translator": 10,
        "regex_builder": 6,
        "keyword_query_assistant": 16,
    }

    for pos, options in enumerate(button_lst):
        text, state, command = options

        name = re.sub(r"\s+", "_", text)

        if text == "SEPARATOR":
            sep = ui.ttk.Separator(parent, orient="vertical")
            sep.grid(row=0, column=pos, sticky="ns", padx=(4, 2), pady=2)
            continue

        button = ui.Button(
            parent,
            name=f"{name}_btn",
            text=text.title(),
            state=state,
            command=command,
            width=btn_width + (2 if pos == 0 else mapping.get(name, 0)),
        )
        button.grid(row=0, column=pos, padx=(2, 0), pady=(0, 2))

        if name not in mapping:
            app.buttons.update({text: button})

