"""
textfsmgen.ui.menu
==================

UI helpers for building the TextFSMGen menu bar.
""" # noqa

from textfsmgen import ui
from textfsmgen.ui.common import open_app_resource
from textfsmgen.ui import (
    about, snippet, callback
)


def create(app) -> None:
    """Create the main application menu bar."""
    root = app.root
    menu_bar = ui.Menu(root)
    root.config(menu=menu_bar)

    file_menu = ui.Menu(menu_bar, tearoff=False)
    tools_menu = ui.Menu(menu_bar, tearoff=False)
    help_menu = ui.Menu(menu_bar, tearoff=False)

    menu_bar.add_cascade(label="File",  menu=file_menu)
    menu_bar.add_cascade(label="Tools", menu=tools_menu)
    menu_bar.add_cascade(label="Help",  menu=help_menu)

    items = (
        # File
        (file_menu, {
            "label": "Open",
            "command": lambda: callback.open_file(app)
        }),
        (file_menu, None),
        (file_menu, {
            "label": "Quit",
            "command": app.root.destroy
        }),

        # Tools
        (tools_menu, {
            "label": "Snippet Translator",
            "command": lambda: snippet.show_dialog(app)
        }),
        (tools_menu, {
            "label": "Regex Builder",
            "state": "disabled",
            "command": lambda: None
        }),
        (tools_menu, {
            "label": "Keyword Query Assistant",
            "state": "disabled",
            "command": lambda: None
        }),

        # Help
        (help_menu, {
            "label": "README",
            "command": lambda: open_app_resource("readme")
        }),
        (help_menu, {
            "label": "View Licenses",
            "command": lambda: open_app_resource("license")
        }),
        (help_menu, None),
        (help_menu, {
            "label": "About",
            "command": lambda: about.show_dialog(app)
        }),
    )

    for menu, cfg in items:
        if cfg:
            menu.add_command(**cfg)
        else:
            menu.add_separator()