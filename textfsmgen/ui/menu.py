"""
textfsmgen.ui.menu
==================

UI helpers for building the TextFSMGen menu bar.
""" # noqa

from textfsmgen import ui
from textfsmgen.ui.common import open_app_resource
from textfsmgen.ui import (
    about, snippet, callback, usage,
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
            "label": "Project Homepage",
            "command": lambda: open_app_resource("project-page")
        }),
        (help_menu, {
            "label": "Package Homepage",
            "command": lambda: open_app_resource("package-page")
        }),
        (help_menu, {
            "label": "Docs (Github Wiki)",
            "command": lambda: open_app_resource("wiki")
        }),
        (help_menu, None),
        (help_menu, {
            "label": "Using TextFSM Generator",
            "command": lambda: usage.show_help(app, "app")
        }),
        (help_menu, {
            "label": "TextFSMGen Settings Reference",
            "command": lambda: usage.show_help(app, "settings")
        }),
        (help_menu, None),
        (help_menu, {
            "label": "Using Snippet Translator",
            "command": lambda: usage.show_help(app, "snippet_translator")
        }),
        (help_menu, {
            "label": "Using Regex Builder",
            "state": "disabled",
            "command": lambda: usage.show_help(app, "regex")
        }),
        (help_menu, {
            "label": "Using Keyword Query Assistant",
            "state": "disabled",
            "command": lambda: usage.show_help(app, "query")
        }),
        (help_menu, None),
        (help_menu, {
            "label": "Report an Issue",
            "command": lambda: open_app_resource("report-issue")
        }),
        (help_menu, {
            "label": "Contact Support...",
            "command": lambda: open_app_resource("contact-support")
        }),
        (help_menu, {
            "label": "Submit Feedback...",
            "state": "disabled",
            "command": lambda: open_app_resource("submit-feedback")
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
            continue
        menu.add_separator()