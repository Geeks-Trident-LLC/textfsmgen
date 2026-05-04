"""
textfsmgen.ui.common
====================

Utility functions for constructing and managing Tkinter UI components
in the TextFSMGen GUI application.
"""
import functools
import re
from os import path
from typing import Any, Optional, Tuple, Dict, Callable
from typing import Union

import webbrowser

from tkinter import ttk
import tkinter as tk

import textfsmgen.config as config
from textfsmgen import ui
from textfsmgen.libs import is_linux

from textfsmgen.libs.utils import split_by_matches


class RewriteSync:
    """Track and validate whether user text and rewritten text are in sync."""

    def __init__(self, app=None):
        self.initial_input = ""
        self.initial_output = ""
        self.is_application_app = is_application_app(app)
        if self.is_application_app:
            self.initial_input = extract_text(app.self.textarea.input)
            self.initial_output = extract_text(app.self.textarea.output)

    def __bool__(self):
        return self.is_application_app

    def is_synced(self, app) -> bool:
        """Return True if both input and output match the stored originals."""

        if not is_application_app(app) or not self:
            return False

        current_in = extract_text(app.self.textarea.input)
        current_out = extract_text(app.self.textarea.output)

        return (
            bool(current_in.strip())
            and bool(current_out.strip())
            and current_in == self.initial_input
            and current_out == self.initial_output
        )

    def is_outdated(self, app) -> bool:
        """Return True if input changed but output still matches the old rewrite."""
        if not is_application_app(app) or not self:
            return False

        current_in = extract_text(app.self.textarea.input)
        current_out = extract_text(app.self.textarea.output)

        return (
            bool(current_in.strip())
            and current_in != self.initial_input
            and current_out == self.initial_output
        )

    def is_unrewritten(self, app) -> bool:
        """Return True if user input exists but no rewritten text is present."""
        if not is_application_app(app) or not self:
            return False

        current_in = extract_text(app.self.textarea.input).strip()
        current_out = extract_text(app.self.textarea.output).strip()
        return bool(current_in) and not current_out

    def is_input_empty(self, app) -> bool:
        """Return True if user input is empty."""
        if not is_application_app(app) or not self:
            return False
        return len(extract_text(app.self.textarea.input).strip()) == 0


def is_application_app(app):    # noqa
    return type(app).__name__ == "Application"


def get_center_coordinates(
        parent: tk.Tk, child_width: int, child_height: int
) -> Tuple[int, int]:
    """Calculate coordinates to center a child window within its parent."""
    geometry = parent.winfo_geometry()  # format: "WxH+X+Y"
    size, x_str, y_str = geometry.split("+")
    parent_x, parent_y = int(x_str), int(y_str)
    parent_w, parent_h = map(int, size.split("x"))

    x = parent_x + (parent_w - child_width) // 2
    y = parent_y + (parent_h - child_height) // 2
    return x, y


def center_window(parent, window, width: int, height: int, x_resizable: bool = False, y_resizable: bool = False) -> None:
    """Center a Tkinter window relative to its parent."""
    x, y = get_center_coordinates(parent, width, height)
    window.geometry(f"{width}x{height}+{x}+{y}")
    window.resizable(x_resizable, y_resizable)


def make_modal(dialog: Union[tk.Toplevel, tk.Tk]) -> None:
    """Configure a Tkinter window to behave as a modal dialog."""

    parent = dialog.master
    if parent is not None:
        dialog.transient(parent)    # noqa

    dialog.wait_visibility()
    dialog.grab_set()
    dialog.wait_window()


def show_message_dialog(    # noqa
    title: Optional[str] = None,
    error: Optional[str] = None,
    warning: Optional[str] = None,
    info: Optional[str] = None,
    question: Optional[str] = None,
    okcancel: Optional[str] = None,
    retrycancel: Optional[str] = None,
    yesno: Optional[str] = None,
    yesnocancel: Optional[str] = None,
    **options
) -> Any:
    """Display a tkinter message dialog based on the provided message type."""
    mapping = {
        error: ui.messagebox.showerror,
        warning: ui.messagebox.showwarning,
        info: ui.messagebox.showinfo,
        question: ui.messagebox.askquestion,
        okcancel: ui.messagebox.askokcancel,
        retrycancel: ui.messagebox.askretrycancel,
        yesno: ui.messagebox.askyesno,
        yesnocancel: ui.messagebox.askyesnocancel,
    }

    for message, func in mapping.items():
        if message:
            return func(title=title, message=message, **options)

    # Default fallback: show info dialog
    return ui.messagebox.showinfo(title=title, message=info or "", **options)


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
def create_styled_label(
    parent: tk.Widget,
    text: str = "",
    link: str = "",
    options: dict = None,
    increased_size: int = 0,
    bold: bool = False,
    underline: bool = False,
    italic: bool = False,
    layout: Optional[Tuple[str, Dict[str, Any]]] = None     # noqa
) -> ttk.Label:
    """Create a styled Tkinter label with optional hyperlink behavior."""

    def mouse_over(event):
        if "underline" not in event.widget.font:
            event.widget.configure(
                font=event.widget.font + ["underline"],
                cursor="hand2"
            )

    def mouse_out(event):
        event.widget.config(font=event.widget.font, cursor="arrow")

    def mouse_press(event):
        webbrowser.open_new_tab(event.widget.link)

    options = options if isinstance(options, dict) else {}

    if link:
        style = ttk.Style()
        style.configure("Blue.TLabel", foreground=ui.hyperlink_fg_color)
        label = ui.Label(parent, text=text, style="Blue.TLabel", **options)
        label.bind("<Enter>", mouse_over)
        label.bind("<Leave>", mouse_out)
        label.bind("<Button-1>", mouse_press)
    else:
        label = ui.Label(parent, text=text, **options)

    font = ui.Font(name="TkDefaultFont", exists=True, root=label)
    font_spec = [font.cget("family"), font.cget("size") + increased_size]
    if bold:
        font_spec.append("bold")
    if underline:
        font_spec.append("underline")
    if italic:
        font_spec.append("italic")

    label.configure(font=font_spec)
    label.font = font_spec
    label.link = link

    return label


def open_app_resource(resource: str) -> None:
    """Open a specified application resource in a web browser."""
    url = config.urls.get(resource, "")
    if url:
        webbrowser.open_new_tab(str(url))


def extract_text(widget) -> str:    # noqa
    """Return textarea content without the trailing newline added by Tkinter."""
    if not isinstance(widget, ui.TextArea):
        return ""
    text = widget.get("1.0", "end")
    last_two = text[-2:]
    return text[:-2] if last_two == "\r\n" else text[:-1]


def clear_text(widget) -> None:
    """Clear all text from a Tkinter Text widget while preserving its state."""
    if not isinstance(widget, ui.TextArea):
        return
    original_state = widget["state"]
    widget.configure(state="normal")
    widget.delete("1.0", "end")
    widget.configure(state=original_state)


def set_text(widget, text: str) -> None:
    """Replace all text in a Tkinter Text widget while preserving its state."""
    if not isinstance(widget, ui.TextArea):
        return

    original_state = widget["state"]
    widget.configure(state="normal")

    widget.delete("1.0", "end")
    widget.insert("1.0", text)

    widget.configure(state=original_state)


def insert_text(widget, text: str) -> None:
    """Insert text in a Tkinter Text widget while preserving its state."""
    if not isinstance(widget, ui.TextArea):
        return

    original_state = widget["state"]
    widget.configure(state="normal")

    if widget.tag_ranges(ui.tk.SEL):
        widget.delete(ui.tk.SEL_FIRST, ui.tk.SEL_LAST)
        insert_pos = widget.index(ui.tk.INSERT)
        widget.insert(ui.tk.INSERT, text)
        widget.tag_add(ui.tk.SEL, insert_pos, f"{insert_pos}+{len(text)}c")
        widget.configure(state=original_state)
        widget.focus()
        return

    widget.insert(ui.tk.INSERT, text)
    widget.configure(state=original_state)


def render_formatted_text(widget, text: str) -> None:
    """Render text with <bold>...</bold> markup into a Tkinter Text widget."""
    if not isinstance(widget, ui.TextArea):
        return

    original_state = widget["state"]
    widget.configure(state="normal")
    widget.delete("1.0", "end")

    # Bold font tag
    bold_font = ui.Font(widget, widget.cget("font"))
    bold_font.configure(weight="bold")
    widget.tag_configure("bold", font=bold_font)
    widget.tag_configure("bold_red", font=bold_font, foreground="red")
    widget.tag_configure("bold_green", font=bold_font, foreground="green")
    widget.tag_configure("bold_blue", font=bold_font, foreground="blue")
    widget.tag_configure("bold_yellow", font=bold_font, foreground="yellow")
    widget.tag_configure("bold_brown", font=bold_font, foreground="brown")
    widget.tag_configure("bold_orange", font=bold_font, foreground="orange")

    pattern = r"<(?P<tag>bold(_\w+)?|link)>(?P<inner>[^<]+)</(bold(_\w+)?|link)>"

    for item in split_by_matches(text, pattern):
        match = re.match(pattern, item)
        if match:
            tag = match.group("tag")
            inner_text = match.group("inner")
            if tag == "link":
                subject, url = inner_text.split(" ---- ")
                start_pos = widget.index("end-1c")
                widget.insert("end", subject)
                end_pos = widget.index("end-1c")

                add_hyperlink(widget, url, start_pos, end_pos)
            else:
                widget.insert("end", inner_text, tag)
        else:
            widget.insert("end", item)

    widget.configure(state=original_state)


def add_hyperlink(text_widget, url, start, end):
    """Make the text between start and end clickable as a hyperlink."""
    tag = f"link_{start.replace('.', '_')}"
    text_widget.tag_add(tag, start, end)

    # Style
    text_widget.tag_config(tag, foreground=ui.hyperlink_fg_color, underline=True)

    # Hover cursor
    text_widget.tag_bind(tag, "<Enter>", lambda e: text_widget.config(cursor="hand2"))
    text_widget.tag_bind(tag, "<Leave>", lambda e: text_widget.config(cursor=""))

    # Click action
    text_widget.tag_bind(tag, "<Button-1>", lambda e: webbrowser.open_new_tab(url))


class TriStateCheckBox(ui.CheckBox):
    """A three‑state checkbox that cycles: unchecked → singular → plural,
    and syncs its state into an optional shared StringVar list."""

    def __init__(self, parent, label="", state_var=None, shared_var=None, **kwargs):
        self.label = label
        self.shared_var = shared_var
        self.state_var = tk.BooleanVar() if state_var is None else state_var
        self.state_index = 0

        kwargs.pop("text", None)
        kwargs.pop("variable", None)
        kwargs.pop("cursor", None)

        super().__init__(
            parent,
            text=label,
            variable=self.state_var,
            cursor="hand2",
            **kwargs
        )

    def reset(self):
        self.configure(text=self.label)
        self.state_var.set(False)
        self.state_index = 0


class DynamicCheckboxGroup(ui.LabelFrame):
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
        "panedwindow": ui.PanedWindow,
        "toplevel": ui.Toplevel,
        "frame": ui.Frame,
        "label": ui.Label,
        "labelframe": ui.LabelFrame,
        "button": ui.Button,
        "textbox": ui.TextBox,
        "textarea": ui.TextArea,
        "scrollbar": ui.Scrollbar,
        "radiobutton": ui.RadioButton,
        "checkbox": ui.CheckBox,
        "menu": ui.Menu,
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
