"""
textfsmgen.ui.menu
==================

UI helpers for building the TextFSMGen menu bar.
""" # noqa

from textfsmgen import ui
from textfsmgen.ui.common import open_app_resource
from textfsmgen.ui import about, callback


def create(app) -> None:
    """Create the main application menu bar."""
    root = app.root
    menu_bar = ui.Menu(root)
    root.config(menu=menu_bar)

    file_menu = ui.Menu(menu_bar, tearoff=False)
    help_menu = ui.Menu(menu_bar, tearoff=False)

    menu_bar.add_cascade(label="File",        menu=file_menu)
    menu_bar.add_cascade(label="Help",        menu=help_menu)

    items = (
        # File
        (file_menu, {"label": "Open",           "command": lambda: callback.open_file(app)}),
        (file_menu, {"label": "Load Test Data", "command": lambda: callback.load_test_data_file(app)}),
        (file_menu, None),
        (file_menu, {"label": "Quit",           "command": app.root.destroy}),

        # Help
        (help_menu, {"label": "Documentation",  "command": lambda: open_app_resource("documentation")}),
        (help_menu, {"label": "View Licenses",  "command": lambda: open_app_resource("license_text")}),
        (help_menu, None),
        (help_menu, {"label": "About",          "command": lambda: about.show_dialog(app)}),
    )

    for menu, cfg in items:
        if cfg:
            menu.add_command(**cfg)
        else:
            menu.add_separator()