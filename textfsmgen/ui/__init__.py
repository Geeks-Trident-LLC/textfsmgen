"""
textfsmgen.ui
=============

This module initializes the UI package for TextFSMGen CE.

Responsibilities include:
- Exposing core Tkinter/ttk widget classes and custom UI components.
- Providing decorators and helper utilities for consistent widget creation and layout.
- Serving as the entry point for importing UI functionality across submodules
  (e.g., `ui.menu`, `ui.about`, `ui.helper`).
"""     # noqa

from typing import Any, Callable, Dict, Optional
import platform
import functools

import yaml

from os import path

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox      # noqa
from tkinter.font import Font       # noqa

from textfsmgen.libs.shell import is_macos_dark_mode

# #2a2a2a subtle contrast for readonly fields in dark mode
# #f0f0f0 slightly stronger gray
readonly_text_bg_color = "#2a2a2a" if is_macos_dark_mode() else "#f0f0f0"

# #4DA3FF blue accent => bright macOS-Style blue
hyperlink_fg_color = "#4DA3FF" if is_macos_dark_mode() else "blue"

is_macos = platform.system() == 'Darwin'    # noqa
is_linux = platform.system() == 'Linux'
is_window = platform.system() == 'Windows'

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


class TriStateCheckBox(CheckBox):
    """A three‑state checkbox that cycles: unchecked → singular → plural,
    and syncs its state into an optional shared StringVar list."""

    def __init__(self, parent, label="", shared_var=None):
        self.label = label
        self.shared_var = shared_var
        self.state_var = tk.BooleanVar(value=False)  # reflects checked/unchecked
        self.state_index = 0  # 0=off, 1=singular, 2=plural

        super().__init__(
            parent,
            text=label,
            variable=self.state_var,
            cursor="hand2"
        )

    def reset(self):
        self.configure(text=self.label)
        self.state_var.set(False)
        self.state_index = 0


class DynamicCheckboxGroup(ttk.LabelFrame):
    """A LabelFrame that stays hidden until build() populates checkboxes."""

    def __init__(self, parent, title="Options"):
        super().__init__(parent, text=title)

        # Dedicated container for dynamic widgets
        self.body = ttk.Frame(self)
        self.checkboxes = []

    @staticmethod
    def create_group_labels(items):
        max_len = max(len(item) for item in items)

        for count in [4, 3, 2]:
            if max_len * count <= 100:
                return [items[i:i+count] for i in range(0, len(items), count)]

        # breakpoint()
        rows = []
        for item in items:
            if not rows:
                rows.append([item])
                continue
            last_row = rows[-1]
            if len(last_row) == 2:
                rows.append([item])
                continue

            first_item = last_row[0]
            if len(first_item) > 50:
                rows.append([item])
                continue
            last_row.append(item)
        return rows

    def build(self, labels, state_var=None):
        """Rebuild checkboxes using smart row grouping (4→3→2 fallback).
        Rules:
          - Try groups of 4 if total length ≤ 120
          - Else try groups of 3 if total length ≤ 120
          - Else use groups of 2 (minimum)
          - If any label > 60 chars → row becomes 1 item (colspan=2)
        """

        if not labels:
            return

        state_var = state_var or tk.StringVar()

        self.body.pack(fill="x", padx=6, pady=6)

        # Destroy all dynamic widgets
        for child in self.body.winfo_children():
            child.destroy()

        grouped = self.create_group_labels(labels)
        self.checkboxes.clear()

        # Build UI rows
        for row_pos, row in enumerate(grouped):
            for col_pos, text in enumerate(row):
                chk = ttk.Checkbutton(
                    self.body, text=text,
                    onvalue=text, offvalue="",
                    variable=state_var,
                    cursor="hand2",
                )
                self.checkboxes.append(chk)
                # Long label → span 2 columns
                if len(text) > 60:
                    chk.grid(row=row_pos, column=0, columnspan=2, sticky="w", padx=2)
                else:
                    chk.grid(row=row_pos, column=col_pos, sticky="w", padx=2)

        for c in range(4):
            self.body.grid_columnconfigure(c, weight=0, uniform="")

        # 2. THEN configure columns (this is the key)
        max_cols = max(len(row) for row in grouped)
        for col in range(max_cols):
            self.body.grid_columnconfigure(col, weight=1, uniform="equal")

    def reset(self):
        # Destroy all dynamic widgets
        for child in self.body.winfo_children():
            child.destroy()

        # Hide the container frame
        self.body.pack_forget()
        self.grid_remove()


def apply_layout(func: Callable) -> Callable:
    """Decorator to apply a Tkinter geometry manager (grid, pack, place) to a widget."""
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        widget = func(*args, **kwargs)
        layout = kwargs.pop("layout", None)
        if isinstance(layout, (list, tuple)) and len(layout) == 2:
            method_name, layout_options = layout
            method_name = str(method_name).lower()
            if method_name in {"grid", "pack", "place"}:
                layout_method = getattr(widget, method_name, None)
                if callable(layout_method):
                    layout_method(**layout_options)
        return widget
    return wrapper


@apply_layout
def create_widget(
    widget_type: str,
    parent: Optional[Any] = None,
    layout: Optional[tuple] = None,  # noqa
    **options: Any
) -> Any:
    """Instantiate a Tkinter widget by type and optionally apply a layout.

    Parameters
    ----------
    widget_type : str
        The type of widget to create (e.g., 'frame', 'label', 'button').
    parent : object, optional
        The parent container for the widget. If None, the widget is created standalone.
    layout : tuple, optional
        A tuple specifying the geometry manager ('grid', 'pack', or 'place')
        and its options.
    options : dict
        Additional keyword arguments passed to the widget constructor.

    Returns
    -------
    object
        The created Tkinter widget instance.
    """
    widget_map: Dict[str, Any] = {
        "panedwindow": PanedWindow,
        "toplevel": Toplevel,
        "frame": Frame,
        "label": Label,
        "labelframe": LabelFrame,
        "button": Button,
        "textbox": TextBox,
        "textarea": TextArea,
        "scrollbar": Scrollbar,
        "radiobutton": RadioButton,
        "checkbox": CheckBox,
        "menu": Menu,
    }

    widget_class = widget_map.get(widget_type.lower())
    if widget_class is None:
        raise ValueError(f"Unsupported widget type: {widget_type}")

    return widget_class(parent, **options) if parent else widget_class(**options)


def set_window_icon(widget) -> None:
    """Set the application window icon using the bundled logo image."""
    # Directory containing the current file
    base_dir = path.dirname(path.abspath(__file__))

    # Path to the logo image
    png_path = path.join(base_dir, "images", "icon_logo.png")
    xbm_path = path.join(base_dir, "images", "icon_logo.xbm")

    # Load logo (PhotoImage supports .png, .gif, .ppm)
    try:
        if is_linux and path.exists(xbm_path):
            widget.iconbitmap(xbm_path)
        else:
            logo = tk.PhotoImage(file=png_path)
            widget.iconphoto(False, logo)
    except Exception:   # noqa
        pass
