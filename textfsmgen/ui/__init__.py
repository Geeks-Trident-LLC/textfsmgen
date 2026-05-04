"""
textfsmgen.ui
=============

UI initialization for TextFSMGen CE.

This package exposes Tkinter/ttk widgets, shared styling constants,
and platform-aware helpers used across UI submodules such as
`ui.menu`, `ui.about`, and `ui.helper`.
"""

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import filedialog
from tkinter.font import Font

from textfsmgen.libs.shell import is_macos_dark_mode
from textfsmgen.libs import is_macos, is_windows, is_linux


# ---------------------------------------------------------------------------
# Theme colors
# ---------------------------------------------------------------------------

# Subtle contrast for readonly fields in dark mode; light gray otherwise.
readonly_text_bg_color = "#2a2a2a" if is_macos_dark_mode() else "#f0f0f0"

# macOS-style blue accent for hyperlinks; fallback to standard blue.
hyperlink_fg_color = "#4DA3FF" if is_macos_dark_mode() else "blue"


# ---------------------------------------------------------------------------
# Widget exports
# ---------------------------------------------------------------------------

Tk = tk.Tk
Toplevel = tk.Toplevel

Frame = ttk.Frame
PanedWindow = ttk.PanedWindow

LabelFrame = ttk.LabelFrame
Label = ttk.Label

Button = ttk.Button

TextBox = ttk.Entry
TextArea = tk.Text

Scrollbar = ttk.Scrollbar

RadioButton = tk.Radiobutton if is_linux else ttk.Radiobutton
CheckBox = tk.Checkbutton if is_linux else ttk.Checkbutton

Menu = tk.Menu


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

__all__ = [
    # platform flags
    "is_macos",
    "is_windows",
    "is_linux",
    # theme
    "readonly_text_bg_color",
    "hyperlink_fg_color",
    # widgets
    "Tk",
    "Toplevel",
    "Frame",
    "PanedWindow",
    "LabelFrame",
    "Label",
    "Button",
    "TextBox",
    "TextArea",
    "Scrollbar",
    "RadioButton",
    "CheckBox",
    "Menu",
    # direct Tkinter utilities
    "messagebox",
    "filedialog",
    "Font",
]
