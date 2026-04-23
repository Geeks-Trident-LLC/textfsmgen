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
        self.base_label = label
        self.shared_var = shared_var
        self.state_var = tk.BooleanVar(value=False)  # reflects checked/unchecked
        self.state_index = 0  # 0=off, 1=singular, 2=plural

        super().__init__(
            parent,
            text=label,
            variable=self.state_var,
            command=self._cycle_state,
        )

    def _cycle_state(self):
        """Advance to the next state and update UI + shared variable."""
        self.state_index = (self.state_index + 1) % 3

        if self.state_index == 1:
            self.state_var.set(True)
            self.config(text=self.base_label)

        elif self.state_index == 2 and self.base_label not in ("anything", "something"):
            self.state_var.set(True)
            self.config(text=f"{self.base_label}s")

        else:  # back to unchecked
            self.state_var.set(False)
            self.config(text=self.base_label)

        self._sync_shared_var()

    def _sync_shared_var(self):
        """Update the shared StringVar list to reflect the current state."""
        if not isinstance(self.shared_var, tk.StringVar):
            return

        try:
            items = yaml.safe_load(self.shared_var.get()) or []
        except Exception:   # noqa
            items = []

        if not isinstance(items, list):
            items = []

        singular = self.base_label
        plural = f"{self.base_label}s"

        # Remove both forms first
        items = [x for x in items if x not in (singular, plural)]

        # Add the active form
        if self.state_index == 1:
            items.append(singular)
        elif self.state_index == 2:
            items.append(plural)
        self.shared_var.set(str(items))


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
