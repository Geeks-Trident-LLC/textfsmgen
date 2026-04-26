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

from textfsmgen.core.patterns import LinePattern

from textfsmgen.libs.text import enclose_string
from textfsmgen.libs.generic import Position

from textfsmgen import ui
from textfsmgen.ui import usage
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

    paned_window = build_pane_window(dialog)

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


def build_pane_window(parent):
    paned_window = ui.PanedWindow(parent, orient="vertical")
    paned_window.pack(fill="both", expand=True, padx=2, pady=2)

    # row-0: Allow horizontal expansion, prevent vertical expansion
    paned_window.grid_columnconfigure(0, weight=1)
    paned_window.grid_rowconfigure(0, weight=1)

    # row-1: Allow horizontal expansion, prevent vertical expansion
    paned_window.grid_columnconfigure(0, weight=1)
    paned_window.grid_rowconfigure(1, weight=1)

    # row-2: Allow horizontal expansion, prevent vertical expansion
    paned_window.grid_columnconfigure(0, weight=1)
    paned_window.grid_rowconfigure(2, weight=0)

    # row-3: Allow horizontal expansion, prevent vertical expansion
    paned_window.grid_columnconfigure(0, weight=1)
    paned_window.grid_rowconfigure(3, weight=1)


    return paned_window
