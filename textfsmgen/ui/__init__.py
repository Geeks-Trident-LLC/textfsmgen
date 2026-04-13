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

from os import path

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox      # noqa
from tkinter.font import Font       # noqa

from textfsmgen.libs.shell import is_macos_dark_mode

readonly_text_bg_color = (
    "#2a2a2a"   # subtle contrast for readonly fields in dark mode
    if is_macos_dark_mode() else
    "#f0f0f0"   # slightly stronger gray
)

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
    file_path = path.join(base_dir, "images", "icon_logo.png")

    # Load logo (PhotoImage supports .png, .gif, .ppm)
    try:
        logo = tk.PhotoImage(file=file_path)
        widget.iconphoto(False, logo)
    except Exception:   # noqa
        pass
