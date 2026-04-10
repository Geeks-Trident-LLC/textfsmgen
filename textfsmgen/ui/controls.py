"""
textfsmgen.ui.controls
======================

Reusable UI controls buttons for the TextFSMGen application.
""" # noqa

from textfsmgen import ui
from textfsmgen.ui import callback
from textfsmgen.ui import settings


def build_action_buttons(app) -> None:
    """Assemble all main action buttons for the application UI."""
    build_primary_buttons(app)
    build_secondary_buttons(app)


def build_primary_buttons(app) -> None:
    """Create the first-row action buttons for the main UI."""
    btn_width = 6 if ui.is_macos else 8
    parent = app.frames.buttons
    button_lst = (
        (app.settings.test_data_btn_name, "normal", lambda: callback.toggle_test_data_mode(app),),
        ("open", "normal", lambda: callback.open_file(app)),
        ("save", "disabled", lambda: callback.save(app)),
        ("copy", "disabled", lambda: callback.copy(app)),
        ("paste", "normal", lambda: callback.paste(app)),
        ("clear", "normal", lambda: callback.clear(app)),
        ("build", "normal", lambda: callback.build(app)),
        ("result", "disabled", lambda: callback.show_result(app)),
        ("settings", "normal", lambda: settings.show_dialog(app)),
    )

    for pos, options in enumerate(button_lst):
        text, state, command = options
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


def build_secondary_buttons(app) -> None:
    """Create the second-row action buttons for the main UI."""

    btn_width = 6 if ui.is_macos else 8
    parent = app.frames.buttons

    button_lst = (
        ("python", "disabled", lambda: callback.create_python_script(app)),
        ("unittest", "disabled", lambda: callback.create_unittest_script(app)),
        ("pytest", "disabled", lambda: callback.create_pytest_script(app)),
        ("execute", "disabled", lambda: callback.execute_test_script(app)),
    )

    for pos, options in enumerate(button_lst):
        text, state, command = options
        button = ui.Button(
            parent,
            name=f"{text}_btn",
            text=text.title(),
            state=state,
            command=command,
            width=btn_width + (2 if pos == 0 else 0),
        )
        button.grid(row=1, column=pos, padx=(2, 0), pady=(0, 2))
        app.buttons.update({text: button})