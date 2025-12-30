"""
textfsmgen.application
======================

Main logic and user interface components for the `textfsmgen` library.

This module integrates with `tkinter` to provide a graphical interface
for building, customizing, and testing TextFSM templates. It serves as
the entry point for launching the application with GUI support, offering
tools for regex construction, template validation, and interactive
pattern testing.


Notes
-----
- If `tkinter` is not installed, the module prints a descriptive error
  message and terminates gracefully.
- This module is intended primarily for interactive use; programmatic
  access to template generation is available via `textfsmgen.__init__`.
"""

from genericlib.misc import ensure_tkinter_available
tk = ensure_tkinter_available(app_name="textfsmgen")

from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox
from tkinter.font import Font

import webbrowser
from textwrap import indent
import re
import platform
from pathlib import Path
from pathlib import PurePath
import yaml
from io import StringIO
from textfsm import TextFSM

from pprint import pformat
from genericlib import get_data_as_tabular
from genericlib import DotObject
from genericlib.exceptions import raise_exception
from genericlib.text import dedent_and_strip
import genericlib.file as file

from textfsmgen import TemplateBuilder
from textfsmgen.exceptions import TemplateBuilderInvalidFormat
from textfsmgen.config import Data

from textfsmgen import version
from textfsmgen import edition


__version__ = version
__edition__ = edition


def get_relative_center_location(parent, width, height):
    """
    Compute the coordinates for centering a child window relative to its parent.

    Parameters
    ----------
    parent : tkinter.Tk or tkinter.Toplevel
        The parent window whose geometry is used as a reference.
    width : int
        The width of the child window.
    height : int
        The height of the child window.

    Returns
    -------
    tuple of int
        (x, y) coordinates for placing the child window centered
        within the parent window.
    """
    try:
        # Geometry string format: "WxH+X+Y"
        geometry = parent.winfo_geometry()
        pw, ph, px, py = re.split("[x+]", geometry)
        parent_x_loc, parent_y_loc = int(px), int(py)
        parent_width, parent_width = int(pw), int(ph)
        x_loc = int(parent_x_loc + (parent_width - width) / 2)
        y_loc = int(parent_y_loc + (parent_width - height) / 2)
        return x_loc, y_loc
    except Exception as ex:
        raise_exception(ex)


def create_msgbox(title=None, error=None, warning=None, info=None,
                  question=None, okcancel=None, retrycancel=None,
                  yesno=None, yesnocancel=None, **options):
    """
    Display a tkinter messagebox based on the provided message type.

    Parameters
    ----------
    title : str, optional
        The title of the messagebox window.
    error : str, optional
        Error message (uses `showerror`).
    warning : str, optional
        Warning message (uses `showwarning`).
    info : str, optional
        Informational message (uses `showinfo`).
    question : str, optional
        Question message (uses `askquestion`).
    okcancel : str, optional
        OK/Cancel prompt (uses `askokcancel`).
    retrycancel : str, optional
        Retry/Cancel prompt (uses `askretrycancel`).
    yesno : str, optional
        Yes/No prompt (uses `askyesno`).
    yesnocancel : str, optional
        Yes/No/Cancel prompt (uses `askyesnocancel`).
    options : keyword arguments, optional
        Additional keyword arguments passed to the underlying messagebox function.

    Returns
    -------
    Any
        The result of the messagebox interaction:
        - "ok", "yes", "no" strings for certain dialogs
        - Boolean values for confirmation dialogs
        - None for canceled dialogs
    """
    msg_func_pairs = (      # noqa
        (error, messagebox.showerror),
        (warning, messagebox.showwarning),
        (info, messagebox.showinfo),
        (question, messagebox.askquestion),
        (okcancel, messagebox.askokcancel),
        (retrycancel, messagebox.askretrycancel),
        (yesno, messagebox.askyesno),
        (yesnocancel, messagebox.askyesnocancel),
    )

    for msg, func in msg_func_pairs:
        if msg is not None:
            return func(title=title, message=dedent_and_strip(msg), **options)

    return messagebox.showinfo(title=title, message=dedent_and_strip(info), **options)


def set_modal_dialog(dialog):
    """
    Configure a Tkinter window to behave as a modal dialog.

    A modal dialog prevents interaction with other windows in the
    application until the dialog is closed.

    Parameters
    ----------
    dialog : tkinter.Tk
        The dialog or window instance to configure as modal.

    Notes
    -----
    - `transient` ensures the dialog is always on top of its parent.
    - `wait_visibility` waits until the window is visible before grabbing focus.
    - `grab_set` directs all events to the dialog, blocking other windows.
    - `wait_window` blocks execution until the dialog is closed.
    """
    if dialog.master is not None:
        dialog.transient(dialog.master)
        dialog.wait_visibility()
        dialog.grab_set()
        dialog.wait_window()


class UserTemplate:
    """
    Manage user-defined TextFSM templates stored in the application.

    This class provides an interface for creating, reading, searching,
    and writing user templates. It encapsulates the template file path,
    its content, and status information, ensuring consistent handling
    of template persistence and retrieval.

    Attributes
    ----------
    filename : str
        Path to the user template file, e.g.,
        ``/home_dir/.geekstrident/textfsmgen/user_templates.yaml``.
    status : str
        Current status message describing the template state
        (e.g., "created", "updated", "not found").
    content : str
        Raw content of the user template file.

    Methods
    -------
    is_exist() -> bool
        Check whether the template file exists at the given path.
    create(confirmed=True) -> bool
        Create a new template file. If `confirmed` is True, overwrite
        existing files when necessary.
    read() -> str
        Read and return the content of the template file.
    search(template_name: str) -> str
        Search for a template by name and return its content.
    write(template_name: str, data: str) -> str
        Write or update a template with the given name and data.
        Returns a status message indicating the result.

    Notes
    -----
    - Templates are stored in YAML format for readability and portability.
    - This class is intended for internal use within the `textfsmgen`
      application to manage user-defined templates.
    """
    def __init__(self):
        # Data.user_template_filename is
        #      /home_dir/.geekstrident/textfsmgen/user_templates.yaml
        self.filename = Data.user_template_filename
        self.status = ''
        self.content = ''

    def is_exist(self):
        """
        Check whether the user template file exists.

        This method verifies if the file specified by `self.filename`
        is present in the filesystem.

        Returns
        -------
        bool
            True if the user template file exists, False otherwise.

        Notes
        -----
        - Typical default path:
          ``/home_dir/.geekstrident/textfsmgen/user_templates.yaml``.
        - Uses `pathlib.Path.exists()` for filesystem validation.
        """

        node = Path(self.filename)
        return node.exists()

    def create(self, confirmed=True):
        """
        Create the user template file if it does not already exist.

        This method ensures that the user template file defined by
        `self.filename` is created on disk. If the file already exists,
        the method returns immediately. When `confirmed` is True, a
        confirmation dialog is shown before creating the file.

        Parameters
        ----------
        confirmed : bool, optional
            Whether to prompt the user with a confirmation messagebox
            before creating the file. Defaults to True.

        Returns
        -------
        bool
            True if the file exists or was successfully created.
            False if creation was declined or failed.

        Notes
        -----
        - The default file path is typically:
          ``/home_dir/.geekstrident/textfsmgen/user_templates.yaml``.
        - If the parent directory does not exist, it is created.
        - If the parent path is a file instead of a directory,
          creation fails and an error messagebox is displayed.
        - On successful creation, `self.content` is updated with
          the file’s initial (empty) content.
        """
        if self.is_exist():
            return True

        try:
            if confirmed:
                response = create_msgbox(
                    title ="Create User Template File",
                    yesno=f"Would you like to create the file {repr(self.filename)}?"
                )
            else:
                response = 'yes'

            if response == 'yes':
                node = Path(self.filename)
                parent = node.parent
                if not parent.exists():
                    parent.mkdir(parents=True, exist_ok=True)
                else:
                    if parent.is_file():
                        create_msgbox(
                            title="Directory Error",
                            error="Cannot create file '{str(node)}' because "
                                  "its parent path '{str(parent)}' is a file."
                        )
                        return False
                node.touch()
                self.content = node.read_text()
                if confirmed:
                    create_msgbox(
                        title="User Template File Created",
                        info=f"{repr(self.filename)}? created successfully."
                    )
                return True
            else:
                return False
        except Exception as ex:
            self.status = f"{type(ex).__name__}: {ex}."
            create_msgbox(
                title="User Template File Creation Error",
                error=self.status
            )

    def read(self):
        """
        Read and return the content of the user template file.

        This method attempts to open and read the file specified by
        `self.filename`. If the file exists, its content is stored in
        `self.content` and returned. If the file does not exist, an
        error messagebox is displayed, `self.status` is updated with
        the error message, and an empty string is returned.

        Returns
        -------
        str
            The content of the user template file if it exists,
            otherwise an empty string.

        Notes
        -----
        - Default file path is typically:
          ``/home_dir/.geekstrident/textfsmgen/user_templates.yaml``.
        - On failure, a messagebox is shown with the title
          `"User Template File Not Found"`.
        - The error message is also stored in `self.status` for
          dia
        """
        if self.is_exist():
            self.content = file.read(self.filename)
            return self.content
        else:
            self.status = f"File '{self.filename}' does not exist."
            create_msgbox(
                title="Error: User Template File Not Found",
                error=self.status
            )
            return ''

    def search(self, template_name):
        """
        Search for a user-defined template by name.

        This method looks up a template within the user template file
        (YAML format) using the provided `template_name`. It validates
        the naming convention, loads the YAML content, and returns the
        template content if found. Status messages are updated to reflect
        the outcome of the search.

        Parameters
        ----------
        template_name : str
            The name of the template to search for. Must follow the
            naming convention: alphanumeric segments separated by
            `+`, `.`, `_`, or `-`.

        Returns
        -------
        str
            The content of the template if found. Returns an empty string
            if the template file does not exist, the name is invalid, the
            template is not found, or the file format is incorrect.

        Raises
        ------
        None
            Errors are handled internally. Message boxes are displayed
            and `self.status` is updated with diagnostic codes such as:
            - 'INVALID-TEMPLATE-NAME-FORMAT'
            - 'INVALID-TEMPLATE-FORMAT'
            - 'NOT_FOUND'
            - 'FOUND'
            - or an error message if the file is missing.

        Notes
        -----
        - Templates are stored in a YAML file, typically located at:
          ``/home_dir/.geekstrident/textfsmgen/user_templates.yaml``.
        - The method uses `yaml.SafeLoader` to ensure safe parsing.
        - `self.status` is updated after each operation to indicate
          success or failure.
        - Message boxes are shown for invalid names, missing files,
          or incorrect formats.
        """
        self.status = ''
        if self.is_exist():
            if not re.match(r'[a-z0-9]+([+._-][a-z0-9]+)*$', template_name):
                self.status = 'INVALID-TEMPLATE-NAME-FORMAT'
                create_msgbox(
                    title="Error: Invalid Template Naming Convention",
                    error="Template names must follow the convention: "
                          "alphanumeric segments separated by '+', '.', '_', or '-'."
                )
                return ''

            yaml_obj = yaml.load(self.read(), Loader=yaml.SafeLoader)

            if yaml_obj is None:
                yaml_obj = dict()

            if isinstance(yaml_obj, dict):
                if template_name in yaml_obj:
                    self.status = 'FOUND'
                    return yaml_obj.get(template_name)
                else:
                    self.status = 'NOT_FOUND'
                    return ''
            else:
                self.status = 'INVALID-TEMPLATE-FORMAT'
                create_msgbox(
                    title="Error: Invalid User Template Format",
                    error=f"File '{self.filename}' is not in the correct format."
                )
                return ''
        else:
            title = 'User Template File Not Found'
            error = "{!r} IS NOT existed.".format(self.filename)
            self.status = error
            create_msgbox(title=title, error=error)
            return ''

    def write(self, template_name, template):
        """
        Write or update a user-defined template in the YAML file.

        This method stores a template under the given `template_name`
        in the user template file (YAML format), typically located at
        ``/home_dir/.geekstrident/textfsmgen/user_templates.yaml``.
        It handles duplicate names and duplicate content by prompting
        the user for confirmation or rename decisions via message boxes.
        The YAML file is rewritten with updated content if the operation
        succeeds.

        Parameters
        ----------
        template_name : str
            The name of the template to store. Must follow the valid
            naming convention enforced by `search`.
        template : str
            The template content to be stored.

        Returns
        -------
        bool
            True if the template was successfully written or updated.
            False if the file does not exist, the user denies overwrite
            or rename, a duplicate violation occurs, or an error is
            encountered while writing.

        Status Codes
        ------------
        - 'USER_TEMPLATE_NOT_EXISTED' : File does not exist.
        - 'FOUND' / 'NOT_FOUND'       : Result of initial search.
        - 'DENIED-OVERWRITE'          : User declined overwriting a duplicate name.
        - 'DUPLICATE-NAME-AND-CONTENT-VIOLATION' : Duplicate name and content detected.
        - 'DENIED-RENAME'             : User declined renaming when duplicate content found.
        - 'INVALID-TEMPLATE-FORMAT'   : File format invalid.
        - Error message string         : Exception occurred while writing.

        Notes
        -----
        - Templates are stored in YAML with block scalar style (``|``).
        - Existing templates with identical content may be removed if
          the user agrees to rename.
        - The file is fully rewritten after modifications, preserving
          sorted template names.
        - Message boxes are used to interact with the user for overwrite
          or rename decisions.
        """
        self.status = ''
        if not self.is_exist():
            self.status = 'USER_TEMPLATE_NOT_EXISTED'
            return False

        self.search(template_name)
        if self.status == 'FOUND' or self.status == 'NOT_FOUND':
            content = self.read()
            yaml_obj = yaml.load(content, Loader=yaml.SafeLoader)
            yaml_obj = yaml_obj or dict()
            if template_name in yaml_obj:
                response = create_msgbox(
                    title="Error: Duplicate Template Name",
                    question=f"Template name '{template_name}' already "
                             f"exists.\nDo you want to overwrite?"
                )
                if response == 'yes':
                    yaml_obj[template_name] = template
                    for name, tmpl in yaml_obj.items():
                        if tmpl.strip() == template.strip() and name != template_name:
                            create_msgbox(
                                title="Error: Duplicate Template Name and Content",
                                error=(
                                    f"Template name '{template_name}' is a duplicate and "
                                    f"has identical content to '{name}'.\nCannot overwrite."
                                )
                            )
                            self.status = 'DUPLICATE-NAME-AND-CONTENT-VIOLATION'
                            return False
                else:
                    self.status = 'DENIED-OVERWRITE'
                    return False
            else:
                removed_lst = []
                for name, tmpl in yaml_obj.items():
                    if tmpl.strip() == template.strip():
                        response = create_msgbox(
                            title="Error: Duplicate Template Content",
                            question=(
                                f"Template name '{template_name}' (your template) "
                                f"has the same content as '{name}'.\n"
                                "Do you want to rename?"
                            )
                        )
                        if response == 'yes':
                            removed_lst.append(name)
                        else:
                            self.status = 'DENIED-RENAME'
                            return False

                for name in removed_lst:
                    yaml_obj.pop(name)

                yaml_obj[template_name] = template

            lst = []

            for name in sorted(yaml_obj.keys()):
                tmpl = yaml_obj.get(name)
                data = '{}: |-\n{}'.format(name, indent(tmpl, '  '))
                lst.append(data)

            try:
                self.content = '\n\n'.join(lst)
                file.write(self.filename, self.content)
                return True
            except Exception as ex:
                self.status = f"{type(ex).__name__}: {ex}"
                create_msgbox(
                    title="Error: Writing User Template File",
                    error=self.status
                )
                return False
        else:
            return False


class Application:
    """
    Main GUI application for TextFSM template management.

    The `Application` class integrates with Tkinter to provide a
    graphical interface for creating, editing, validating, and testing
    TextFSM templates. It manages the lifecycle of the GUI, including
    initialization of frames, widgets, and event handlers, while
    coordinating file operations and user interactions.

    Responsibilities
    ----------------
    - Launch and manage the Tkinter event loop.
    - Provide input/output frames for template editing and testing.
    - Handle user actions such as opening, saving, searching, and
      validating templates.
    - Display error, warning, and confirmation dialogs using
      `create_msgbox`.
    - Integrate with `UserTemplate` for reading, writing, and searching
      YAML‑based template files.
    - Support switching between regex builder and pattern builder modes.

    Notes
    -----
    - Templates are stored in YAML format under the user's home
      directory, typically at:
      ``~/.geekstrident/textfsmgen/user_templates.yaml``.
    - Error handling is performed via message boxes rather than
      exceptions, making this class suitable for interactive use.
    - For programmatic access to template generation without GUI,
      use `textfsmgen.__init__` instead.
    """

    browser = webbrowser

    def __init__(self):
        # support platform: macOS, Linux, and Window
        self.is_macos = platform.system() == 'Darwin'
        self.is_linux = platform.system() == 'Linux'
        self.is_window = platform.system() == 'Windows'

        # standardize tkinter widget for macOS, Linux, and Window operating system
        self.RadioButton = tk.Radiobutton if self.is_linux else ttk.Radiobutton
        self.CheckBox = tk.Checkbutton if self.is_linux else ttk.Checkbutton
        self.Label = ttk.Label
        self.Frame = ttk.Frame
        self.LabelFrame = ttk.LabelFrame
        self.Button = ttk.Button
        self.TextBox = ttk.Entry
        self.TextArea = tk.Text
        self.PanedWindow = ttk.PanedWindow

        self._base_title = 'TextFSM Generator {} Edition'.format(edition)
        self.root = tk.Tk()
        self.root.geometry('900x600+100+100')
        self.root.minsize(200, 200)
        self.root.option_add('*tearOff', False)

        # tkinter widgets for main layout
        self.paned_window = None
        self.text_frame = None
        self.entry_frame = None
        self.backup_frame = None
        self.result_frame = None

        self.input_textarea = None
        self.result_textarea = None

        self.open_file_btn = None
        self.clear_text_btn = None
        self.paste_text_btn = None
        self.save_as_btn = None
        self.copy_text_btn = None

        self.build_btn = None
        self.snippet_btn = None
        self.unittest_btn = None
        self.pytest_btn = None
        self.test_data_btn = None
        self.result_btn = None
        self.store_btn = None
        self.search_checkbox = None
        self.template_name_textbox = None
        self.lookup_btn = None
        self.close_lookup_btn = None
        self.close_backup_btn = None

        self.curr_widget = None
        self.prev_widget = None
        self.root.bind("<Button-1>", lambda e: self.callback_focus(e))

        # datastore

        self.snapshot = DotObject()
        self.snapshot.update(
            title="",
            stored_title="",
            user_data="",
            test_data=None,
            result="",
            template="",
            is_built=False,
            curr_app="main_app",
            switch_app_template="",
            switch_app_user_data="",
            switch_app_result_data="",
            main_input_textarea="",
            main_result_textarea="",
        )

        # variables
        self.build_btn_var = tk.StringVar()
        self.build_btn_var.set('Build')
        self.test_data_btn_var = tk.StringVar()
        self.test_data_btn_var.set('Test Data')

        # variables: arguments
        self.filename_var = tk.StringVar()
        self.author_var = tk.StringVar()
        self.email_var = tk.StringVar()
        self.company_var = tk.StringVar()
        self.template_name_var = tk.StringVar()
        self.description_var = tk.StringVar()
        self.search_checkbox_var = tk.BooleanVar()

        # variables: app
        self.test_data_checkbox_var = tk.BooleanVar()
        self.template_checkbox_var = tk.BooleanVar()
        self.tabular_checkbox_var = tk.BooleanVar()
        self.tabular_checkbox_var.set(True)

        # method call
        self.set_title()
        self.build_menu()
        self.build_frame()
        self.build_textarea()
        self.build_entry()
        self.build_result()

    def get_template_args(self):
        """
        Collect and return configuration arguments for initializing
        a `TemplateBuilder` instance.

        This method gathers values from the application's GUI variables and
        returns them as a dictionary. The resulting dictionary can be passed
        directly to the `TemplateBuilder` class to configure template metadata
        such as author, company, and description.

        Returns
        -------
        dict
            A dictionary of template arguments with the following keys:

            - filename (str): Path to the template file.
            - author (str): Author name associated with the template.
            - email (str): Author email address.
            - company (str): Company name associated with the template.
            - description (str): Short description of the template's purpose.
        """
        result = dict(
            filename=self.filename_var.get(),
            author=self.author_var.get(),
            email=self.email_var.get(),
            company=self.company_var.get(),
            description=self.description_var.get()
        )
        return result

    def set_default_setting(self):
        """
        Reset application configuration variables to their default values.

        This method restores all template‑related metadata and checkbox
        options to a consistent baseline state. It ensures that the
        application starts with a clean configuration when creating or
        editing templates.

        Notes
        -----
        - Metadata fields are reset to empty strings:
            * `filename_var`
            * `author_var`
            * `email_var`
            * `company_var`
            * `description_var`
        - Checkbox options are reset as follows:
            * `test_data_checkbox_var` → False
            * `template_checkbox_var` → False
            * `tabular_checkbox_var` → True

        Returns
        -------
        None
            This method performs side effects (variable resets) but does
            not return a value.
        """

        self.filename_var.set('')
        self.author_var.set('')
        self.email_var.set('')
        self.company_var.set('')
        self.description_var.set('')

        self.test_data_checkbox_var.set(False)
        self.template_checkbox_var.set(False)
        self.tabular_checkbox_var.set(True)

    @classmethod
    def get_textarea(cls, widget):
        """
        Retrieve and normalize text content from a Tkinter `Text` widget.

        This method extracts the full text from the given `tk.Text` widget,
        starting at position `'1.0'` through `'end'`. It trims any trailing
        newline (`\\n`), carriage return (`\\r`), or Windows-style line ending
        (`\\r\\n`) that Tkinter may append automatically, ensuring the returned
        string is clean and consistent across platforms.

        Parameters
        ----------
        widget : tk.Text
            A Tkinter `Text` widget from which to retrieve content.

        Returns
        -------
        str
            The normalized text string from the widget, with trailing line
            endings removed if present.

        Notes
        -----
        - Tkinter often appends a trailing newline when retrieving text with
          `'end'`. This method ensures that such artifacts are stripped.
        - All other content entered by the user is preserved exactly.
        """
        text = widget.get('1.0', 'end')
        return text.rstrip("\r\n")

    @classmethod
    def clear_textarea(cls, widget):
        """
        Clear all text content from a Tkinter `Text` widget.

        Temporarily sets the widget state to `NORMAL` to allow deletion,
        removes all text from the widget, and then restores its original
        state.

        Parameters
        ----------
        widget : tk.Text
            A Tkinter `Text` widget whose content will be cleared.

        Returns
        -------
        None
            This method performs a side effect (clearing text) but does
            not return a value.
        """
        curr_state = widget['state']
        widget.configure(state=tk.NORMAL)
        widget.delete("1.0", "end")
        widget.configure(state=curr_state)

    def set_textarea(self, widget, data, title=''):
        """
        Set text content in a Tkinter `Text` widget and optionally update the window title.

        This method replaces the existing content of the given `tk.Text` widget
        with the provided data. If a non-empty title is supplied, the application
        window title is updated accordingly. The widget's state is temporarily
        set to `NORMAL` to allow modifications and restored to its original
        state afterward.

        Parameters
        ----------
        widget : tk.Text
            A Tkinter `Text` widget where the content will be inserted.
        data : any
            The data to insert into the widget. Converted to a string before insertion.
        title : str, optional
            The title to set for the application window. Defaults to an empty string.
            If empty, the window title is not modified.

        Returns
        -------
        None
            This method performs side effects (widget updates and optional title change)
            but does not return a value.

        Notes
        -----
        - Existing content in the `Text` widget is cleared before inserting new data.
        - Both `data` and `title` are coerced to strings to ensure consistent behavior.
        - The widget's original state is preserved after modification.
        """
        data, title = str(data), str(title).strip()

        curr_state = widget['state']
        widget.configure(state=tk.NORMAL)

        title and self.set_title(title=title)
        widget.delete("1.0", "end")
        widget.insert(tk.INSERT, data)

        widget.configure(state=curr_state)

    def set_title(self, widget=None, title=''):
        """Set a new title for tkinter widget.

        Parameters
        ----------
        widget (tkinter): a tkinter widget.
        title (str): a title.  Default is empty.
        """
        widget = widget or self.root
        base_title = self._base_title
        title = '{} - {}'.format(title, base_title) if title else base_title
        widget.title(title)

    def shift_to_main_app(self):
        """
        Switch the application context from the backup app to the main app.

        This method updates the snapshot state to indicate the main app is
        active, restores user and result data from the backup context into
        the main input/output text areas, and reconfigures the GUI layout
        by replacing the backup frame with the entry frame. It also updates
        the stored window title in the snapshot and applies the current title
        to the root window.

        Notes
        -----
        - `snapshot.curr_app` is set to `'main_app'`.
        - `switch_app_user_data` and `switch_app_result_data` are cleared
          after being restored.
        - The backup frame is removed from the paned window and the entry
          frame is inserted.
        - The window title is normalized by removing the base title suffix
          and stored in the snapshot for later use.

        Returns
        -------
        None
            This method performs side effects (state updates and GUI changes)
            but does not return a value.
        """

        # Update snapshot to reflect active app
        self.snapshot.update(curr_app='main_app')

        # Restore user and result data from backup
        user_data = self.snapshot.switch_app_user_data
        result_data = self.snapshot.switch_app_result_data
        self.snapshot.update(
            switch_app_user_data='',
            switch_app_result_data=''
        )

        # Update text areas with restored data
        self.set_textarea(self.input_textarea, user_data)
        self.set_textarea(self.result_textarea, result_data)

        # Reconfigure GUI layout
        self.paned_window.remove(self.backup_frame)
        self.paned_window.insert(1, self.entry_frame)

        # Update and apply window title
        stored_title = self.root.title().replace(f" - {self._base_title}", "")
        self.snapshot.update(stored_title=stored_title)
        self.set_title(title=self.snapshot.title)

    def shift_to_backup_app(self):
        """
        Switch the application context from the main app to the backup app.

        This method updates the snapshot state to indicate that the backup
        app is active, reconfigures the GUI layout by replacing the entry
        frame with the backup frame, and updates the window title. The
        current title is normalized by removing the base title suffix and
        stored in the snapshot. The backup app title is then applied to
        the root window.

        Notes
        -----
        - `snapshot.curr_app` is set to `'backup_app'`.
        - The entry frame is removed from the paned window and the backup
          frame is inserted.
        - The current window title is stripped of the base title suffix
          and stored in `snapshot.title`.
        - The displayed title is set to `snapshot.stored_title` if present,
          otherwise defaults to `'Storing Template'`.

        Returns
        -------
        None
            This method performs side effects (state updates and GUI changes)
            but does not return a value.
        """
        # Update snapshot to reflect active app
        self.snapshot.update(curr_app='backup_app')

        # Reconfigure GUI layout
        self.paned_window.remove(self.entry_frame)
        self.paned_window.insert(1, self.backup_frame)

        # Normalize and store current title
        title = self.root.title().replace(f" - {self._base_title}", "")
        self.snapshot.update(title=title)

        # Apply stored or default backup title
        stored_title = self.snapshot.stored_title or 'Storing Template'
        self.set_title(title=stored_title)

    def create_custom_label(self, parent, text='', link='',
                            increased_size=0, bold=False, underline=False,
                            italic=False):
        """
        Create a customized Tkinter `Label` widget with optional styling and hyperlink behavior.

        This method generates a `Label` widget with configurable text, font
        styling, and optional hyperlink functionality. If a `link` is provided,
        the label is styled in blue and bound to mouse events for hover and
        click interactions.

        Parameters
        ----------
        parent : tkinter.Widget
            The parent widget that will contain the label.
        text : str, optional
            The text to display in the label. Defaults to an empty string.
        link : str, optional
            A hyperlink associated with the label. Defaults to an empty string.
            If provided, the label is styled and bound to open the link in a
            browser when clicked.
        increased_size : int, optional
            Amount to increase the base font size. Defaults to 0 (no change).
        bold : bool, optional
            If True, the label text is rendered in bold. Defaults to False.
        underline : bool, optional
            If True, the label text is underlined. Defaults to False.
        italic : bool, optional
            If True, the label text is italicized. Defaults to False.

        Returns
        -------
        tkinter.Label
            A fully configured `Label` widget ready to be packed or gridded
            into the parent container.

        Notes
        -----
        - Font styling is applied by combining the provided options
          (`bold`, `underline`, `italic`, `increased_size`).
        - If `link` is provided, the label is styled in blue and bound to
          mouse events for hover and click interactions.
        """

        def mouse_over(event):
            """
            Handle mouse hover event for a label with a hyperlink.
            This is an inner function defined within Application.create_custom_label.

            Parameters
            ----------
            event : tkinter.Event
                The event object containing metadata about the hover action.

            Notes
            -----
            - Adds an underline to the label font if not already present.
            - Changes the cursor to a hand pointer to indicate interactivity.
            """

            if 'underline' not in event.widget.font:
                event.widget.configure(
                    font=event.widget.font + ['underline'],
                    cursor='hand2'
                )

        def mouse_out(event):
            """
            Handle mouse leave event for a label with a hyperlink.
            This is an inner function defined within Application.create_custom_label.

            Parameters
            ----------
            event : tkinter.Event
                The event object containing metadata about the mouse leave action.

            Notes
            -----
            - Restores the label font to its original state.
            - Resets the cursor to the default arrow.
            """
            event.widget.config(
                font=event.widget.font,
                cursor='arrow'
            )

        def mouse_press(event):
            """
            Handle mouse click event for a label with a hyperlink.
            This is an inner function defined within Application.create_custom_label.

            Parameters
            ----------
            event : tkinter.Event
                The event object containing metadata about the mouse click action.

            Notes
            -----
            - Opens the associated hyperlink in a new browser tab.
            """
            self.browser.open_new_tab(event.widget.link)

        style = ttk.Style()
        style.configure("Blue.TLabel", foreground="blue")
        if link:
            label = self.Label(parent, text=text, style='Blue.TLabel')
            label.bind('<Enter>', mouse_over)
            label.bind('<Leave>', mouse_out)
            label.bind('<Button-1>', mouse_press)
        else:
            label = self.Label(parent, text=text)
        font = Font(name='TkDefaultFont', exists=True, root=label)
        font = [font.cget('family'), font.cget('size') + increased_size]
        bold and font.append('bold')
        underline and font.append('underline')
        italic and font.append('italic')
        label.configure(font=font)
        label.font = font
        label.link = link
        return label

    def callback_focus(self, event):
        """
        Handle focus change when a new widget is selected.

        This callback updates the application's current and previous widget
        references whenever the user selects a different widget. If an error
        occurs during processing, the event is skipped gracefully.

        Parameters
        ----------
        event : tkinter.Event
            The event object triggered when a widget gains focus. Contains
            metadata including the widget reference.

        Returns
        -------
        None
            This method performs side effects (updating widget references)
            but does not return a value.

        Notes
        -----
        - `self.curr_widget` is updated to the newly focused widget.
        - `self.prev_widget` stores the previously focused widget.
        - Any exceptions are caught, and a skip message is printed for
          debugging purposes.
        """

        try:
            widget = getattr(event, "widget", None)
            if widget and widget != self.curr_widget:
                self.prev_widget = self.curr_widget
                self.curr_widget = widget
        except Exception as ex:     # noqa
            print(f"... skip {getattr(event, 'widget', event)}")

    def callback_file_exit(self):
        """
        Handle the "File > Exit" menu action.

        This callback terminates the application's main event loop by
        invoking `root.quit()`. It is typically bound to the "Exit" option
        in the File menu, allowing users to close the application gracefully.

        Returns
        -------
        None
            This method performs a side effect (terminating the Tkinter
            event loop) but does not return a value.

        Notes
        -----
        - `quit()` stops the Tkinter main loop but does not immediately
          destroy the root window. If full cleanup is required, consider
          using `root.destroy()` instead.
        - This method is intended for GUI menu integration rather than
          direct programmatic use.
        """
        self.root.quit()

    def callback_open_file(self):
        """
        Handle the "File > Open" menu action.

        This callback opens a file selection dialog, reads the chosen file,
        and loads its content into the application. It also updates the
        snapshot state, resets relevant widgets, and ensures the GUI is
        ready for further user interaction.

        Workflow
        --------
        1. Display a file dialog restricted to text files (`.txt`) or all files.
        2. If a file is selected:
           - Read its content.
           - Invoke search checkbox if enabled.
           - Close backup app if currently active.
           - Reset and enable relevant buttons and text areas.
           - Update snapshot with loaded test data.
           - Update window title to reflect the opened file.
           - Insert file content into the input text area.
           - Enable copy/save actions and set focus to the input area.

        Returns
        -------
        None
            This method performs side effects (file I/O, widget updates,
            and snapshot state changes) but does not return a value.

        Notes
        -----
        - The file dialog uses `tkinter.filedialog.askopenfilename`.
        - Only `.txt` files are explicitly listed, but all files can be opened.
        - The loaded content is stored in `snapshot.test_data`.
        """

        filetypes = [
            ('Text Files', '.txt', 'TEXT'),
            ('All Files', '*'),
        ]
        filename = filedialog.askopenfilename(filetypes=filetypes)
        if filename:
            # Read file content
            content = file.read(filename)

            # Trigger search checkbox if active
            if self.search_checkbox_var.get():
                self.search_checkbox.invoke()

            # Close backup app if active
            if self.snapshot.curr_app == 'backup_app':
                self.close_backup_btn.invoke()

            # Reset and update widgets
            self.test_data_btn.config(state=tk.NORMAL)
            self.test_data_btn_var.set('Test Data')
            self.set_textarea(self.result_textarea, '')
            self.snapshot.update(test_data=content)

            # Update title and input area
            self.set_title(title=f"Open {filename} + LOAD Test Data")
            self.set_textarea(self.input_textarea, content)

            # Enable actions and set focus
            self.copy_text_btn.configure(state=tk.NORMAL)
            self.save_as_btn.configure(state=tk.NORMAL)
            self.input_textarea.focus()

    def callback_load_test_data_file(self):
        """
        Handle the "File > Load Test Data" menu action.

        This callback opens a file selection dialog, loads the chosen test
        data file, and updates the application state accordingly. It manages
        synchronization between the input and result text areas, updates
        snapshot metadata, and ensures the GUI reflects the newly loaded
        test data.

        Workflow
        --------
        1. Display a file dialog restricted to text files (`.txt`) or all files.
        2. If a file is selected:
           - Read its content.
           - Invoke search checkbox if enabled.
           - Close backup app if currently active.
           - Enable and reset relevant buttons and text areas.
           - Compare loaded content with current input:
             * If identical or input is empty:
               - Load into input area.
               - If input is empty, reset result area unless it matches
                 a generated template pattern.
               - Focus input area.
             * Otherwise, load into result area.
           - Enable copy/save actions.
           - Update snapshot with loaded test data and title.
           - Update window title to reflect the loaded file.

        Returns
        -------
        None
            This method performs side effects (file I/O, widget updates,
            and snapshot state changes) but does not return a value.

        Notes
        -----
        - The file dialog uses `tkinter.filedialog.askopenfilename`.
        - Loaded content is stored in `snapshot.test_data`.
        - A regex pattern is used to detect generated template markers
          in the result area.
        """

        filetypes = [
            ('Text Files', '.txt', 'TEXT'),
            ('All Files', '*'),
        ]
        filename = filedialog.askopenfilename(filetypes=filetypes)
        if filename:
            # Read file content
            content = file.read(filename)

            # Trigger search checkbox if active
            if self.search_checkbox_var.get():
                self.search_checkbox.invoke()

            # Close backup app if active
            if self.snapshot.curr_app == 'backup_app':
                self.close_backup_btn.invoke()

            # Reset and enable test data button
            self.test_data_btn.config(state=tk.NORMAL)
            self.test_data_btn_var.set('Test Data')

            # Compare loaded content with current input
            input_data = Application.get_textarea(self.input_textarea)
            result_data = Application.get_textarea(self.result_textarea)

            if content.strip() == input_data.strip() or input_data.strip() == '':
                self.set_textarea(self.input_textarea, content)
                if input_data.strip() == '':
                    pattern = r'#+\s+# *Template +is +generated '
                    if not re.match(pattern, result_data):
                        self.set_textarea(self.result_textarea, '')
                    else:
                        self.result_btn.configure(state=tk.NORMAL)
                self.input_textarea.focus()
            else:
                self.set_textarea(self.result_textarea, content)

            # Enable actions
            self.copy_text_btn.configure(state=tk.NORMAL)
            self.save_as_btn.configure(state=tk.NORMAL)

            # Update snapshot and title
            title = f"LOAD Test Data - {filename}"
            self.snapshot.update(
                title=title,
                test_data=content
            )
            self.set_title(title=title)

    def callback_help_documentation(self):
        """
        Handle the "Help > Getting Started" menu action.

        This callback opens the application's official documentation in a
        new browser tab. It provides users with quick access to the
        "Getting Started" guide or reference materials hosted at the URL
        defined in `Data.documentation_url`.

        Workflow
        --------
        1. Retrieve the documentation URL from `Data.documentation_url`.
        2. Open the URL in a new browser tab using the application's
           `self.browser` instance.

        Returns
        -------
        None
            This method performs a side effect (launching documentation in
            a browser) but does not return a value.

        Notes
        -----
        - Relies on `self.browser.open_new_tab` for launching the documentation.
        - The documentation URL is centralized in the `Data` class for
          maintainability and consistency.
        """
        self.browser.open_new_tab(Data.documentation_url)

    def callback_help_view_licenses(self):
        """
        Handle the "Help > View Licenses" menu action.

        This callback opens the application's license information in a new
        browser tab. It provides users with direct access to the license text
        and related legal details hosted at the URL defined in
        `Data.license_url`.

        Workflow
        --------
        1. Retrieve the license URL from `Data.license_url`.
        2. Open the URL in a new browser tab using the application's
           `self.browser` instance.

        Returns
        -------
        None
            This method performs a side effect (launching the license page in
            a browser) but does not return a value.

        Notes
        -----
        - Relies on `self.browser.open_new_tab` for launching the license page.
        - The license URL is centralized in the `Data` class for maintainability
          and consistency.
        """
        self.browser.open_new_tab(Data.license_url)

    def callback_help_about(self):
        """
        Handle the "Help > About" menu action.

        This callback creates and displays a modal "About" dialog window
        containing application metadata, repository information, dependency
        links, license text, and copyright.

        Workflow
        --------
        1. Create a modal `Toplevel` window centered relative to the root.
        2. Display application name and repository URL.
        3. List PyPI dependencies with clickable links.
        4. Show license text in a scrollable, read‑only text area.
        5. Display footer with copyright and company.
        6. Make the dialog modal to prevent interaction with the main window
           until closed.

        Returns
        -------
        None
            This method performs side effects (GUI creation and display)
            but does not return a value.

        Notes
        -----
        - Uses `create_custom_label` for styled labels and hyperlinks.
        - License text is inserted into a disabled `TextArea` with a vertical
          scrollbar.
        - The dialog is non‑resizable and centered relative to the root window.
        """

        # Create modal "About" window
        about = tk.Toplevel(self.root)
        self.set_title(widget=about, title='About')

        width, height = 460, 460
        x, y = get_relative_center_location(self.root, width, height)
        about.geometry(f'{width}x{height}+{x}+{y}')
        about.resizable(False, False)

        # Top frame and paned window
        top_frame = self.Frame(about)
        top_frame.pack(fill=tk.BOTH, expand=True)

        paned_window = self.PanedWindow(top_frame, orient=tk.VERTICAL)
        paned_window.pack(fill=tk.BOTH, expand=True, padx=8, pady=12)

        # Company and repository info
        frame = self.Frame(paned_window, width=450, height=20)
        paned_window.add(frame, weight=4)

        label = self.create_custom_label(
            frame, text=Data.main_app_text,
            increased_size=2, bold=True
        )
        label.grid(row=0, column=0, columnspan=2, sticky=tk.W)

        # URL
        cell_frame = self.Frame(frame, width=450, height=5)
        cell_frame.grid(row=1, column=0, sticky=tk.W, columnspan=2)

        url = Data.repo_url
        label = self.Label(cell_frame, text='URL:')
        label.pack(side=tk.LEFT)

        label = self.create_custom_label(cell_frame, text=url, link=url)
        label.pack(side=tk.LEFT)

        # Dependencies section
        label = self.create_custom_label(frame, text='Pypi.com Dependencies:', bold=True)
        label.grid(row=2, column=0, sticky=tk.W)

        # regex app package
        label = self.create_custom_label(
            frame, text=Data.regexapp_text,
            link=Data.regexapp_link
        )
        label.grid(row=3, column=0, padx=(20, 0), sticky=tk.W)

        # genericlib package
        label = self.create_custom_label(
            frame, text=Data.genlib_text,
            link=Data.genlib_link
        )
        label.grid(row=4, column=0, padx=(20, 0), sticky=tk.W)

        # TextFSM package
        label = self.create_custom_label(
            frame, text=Data.textfsm_text,
            link=Data.textfsm_link
        )
        label.grid(row=3, column=1, padx=(20, 0), sticky=tk.W)

        # PyYAML package
        label = self.create_custom_label(
            frame, text=Data.pyyaml_text,
            link=Data.pyyaml_link
        )
        label.grid(row=4, column=1, padx=(20, 0), pady=(0, 10), sticky=tk.W)

        # license textbox
        label_frame = self.LabelFrame(
            paned_window, height=200, width=450,
            text=Data.license_name
        )
        paned_window.add(label_frame, weight=7)

        width = 58 if self.is_macos else 51
        height = 18 if self.is_macos else 14 if self.is_linux else 15
        textbox = self.TextArea(label_frame, width=width, height=height, wrap='word')
        textbox.grid(row=0, column=0, padx=5, pady=5)

        scrollbar = ttk.Scrollbar(label_frame, orient=tk.VERTICAL, command=textbox.yview)
        scrollbar.grid(row=0, column=1, sticky='nsew')
        textbox.config(yscrollcommand=scrollbar.set)

        textbox.insert(tk.INSERT, Data.license)
        textbox.config(state=tk.DISABLED)

        # Footer - copyright
        frame = self.Frame(paned_window, width=450, height=20)
        paned_window.add(frame, weight=1)

        label = self.Label(frame, text=Data.copyright_text)
        label.pack(side=tk.LEFT, pady=(10, 10))

        label = self.create_custom_label(
            frame, text=Data.company, link=Data.company_url
        )
        label.pack(side=tk.LEFT, pady=(10, 10))

        label = self.Label(frame, text='.  All right reserved.')
        label.pack(side=tk.LEFT, pady=(10, 10))

        # Make dialog modal
        set_modal_dialog(about)

    def callback_preferences_settings(self):
        """
        Handle the "Preferences > Settings" menu action.

        This callback opens a modal "Settings" dialog window where users can
        configure application metadata (author, email, company, filename,
        description) and toggle application options (test data, template,
        tabular). It provides a centralized interface for customizing
        preferences.

        Workflow
        --------
        1. Create a modal `Toplevel` window centered relative to the root.
        2. Display input fields for metadata (author, email, company, filename, description).
        3. Provide checkboxes for application options (test data, template, tabular).
        4. Include "Default" and "OK" buttons for resetting or closing the dialog.
        5. Make the dialog modal to prevent interaction with the main window
           until closed.

        Returns
        -------
        None
            This method performs side effects (GUI creation and preference
            updates) but does not return a value.

        Notes
        -----
        - Uses `set_default_setting()` to restore default values.
        - Dialog size and padding are adjusted based on platform (macOS, Linux, Windows).
        - The dialog is non‑resizable and centered relative to the root window.
        """
        # Create modal "Settings" window
        settings = tk.Toplevel(self.root)
        self.set_title(widget=settings, title='Settings')

        width = 520 if self.is_macos else 474 if self.is_linux else 370
        height = 258 if self.is_macos else 242 if self.is_linux else 234
        x, y = get_relative_center_location(self.root, width, height)
        settings.geometry(f"{width}x{height}+{x}+{y}")
        settings.resizable(False, False)

        top_frame = self.Frame(settings)
        top_frame.pack(fill=tk.BOTH, expand=True)

        # Arguments section
        label_frame_args = self.LabelFrame(
            top_frame, height=100, width=380,
            text='Arguments'
        )
        label_frame_args.grid(row=0, column=0, padx=10, pady=(5, 0), sticky=tk.W)

        pady = 0 if self.is_macos else 1

        # Metadata fields
        fields = [
            ("Author", self.author_var, 0),
            ("Email", self.email_var, 1),
            ("Company", self.company_var, 2),
            ("Filename", self.filename_var, 4),
            ("Description", self.description_var, 5),
        ]
        for label_text, var, row in fields:
            label = self.Label(label_frame_args, text=label_text)
            label.grid(
                row=row, column=0, columnspan=2, padx=2, pady=pady,
                sticky=tk.W + tk.N
            )
            textbox = self.TextBox(label_frame_args, width=45, textvariable=var)
            textbox.grid(
                row=row, column=2, columnspan=4, padx=2,
                pady=(pady, 10) if label_text == "Description" else pady,
                sticky=tk.W
            )

        # Settings - Arguments
        label_frame_app = self.LabelFrame(top_frame, height=120, width=380, text='App')
        label_frame_app.grid(row=1, column=0, padx=10, pady=1, sticky=tk.W+tk.N)

        options = [
            ("Test Data", self.test_data_checkbox_var, 0, 0, 2),
            ("Template", self.template_checkbox_var, 0, 1, 20),
            ("Tabular", self.tabular_checkbox_var, 0, 2, 2),
        ]
        for text, var, row, col, padx in options:
            kwargs = dict(text=text, onvalue=True, offvalue=False, variable=var)
            checkbox = self.CheckBox(label_frame_app, **kwargs)
            checkbox.grid(row=row, column=col, padx=padx)

        # OK and Default buttons
        frame = self.Frame(top_frame, height=14, width=380)
        frame.grid(row=2, column=0, padx=10, pady=(10, 5), sticky=tk.E+tk.S)

        button = self.Button(
            frame, text='Default',
            command=lambda: self.set_default_setting(),
        )
        button.grid(row=0, column=6, padx=1, pady=1, sticky=tk.E)

        button = self.Button(
            frame, text='OK',
            command=lambda: settings.destroy(),
        )
        button.grid(row=0, column=7, padx=1, pady=1, sticky=tk.E)

        # Make dialog modal
        set_modal_dialog(settings)

    def callback_preferences_user_template(self):
        """
        Handle the "Preferences > User Template" menu action.

        This callback disables the search option by resetting the
        `search_checkbox_var` to `False` and programmatically invoking
        the associated checkbox action. It ensures that when the
        "User Template" preference is selected, the search mode is
        turned off and the application state is updated accordingly.

        Returns
        -------
        None
            This method performs side effects (updating widget state
            and invoking checkbox behavior) but does not return a value.

        Notes
        -----
        - `search_checkbox_var` is explicitly set to `False`.
        - `search_checkbox.invoke()` triggers the checkbox's bound
          command to apply the change in the UI and application logic.
        """
        self.search_checkbox_var.set(False)
        self.search_checkbox.invoke()

    def build_menu(self):
        """
        Construct the main menubar for the TextFSM Generator GUI application.

        This method initializes and attaches a menubar to the root window,
        organizing commands under **File**, **Preferences**, and **Help**
        categories. Each menu provides access to core functionality such as
        file operations, application preferences, and help resources.

        Workflow
        --------
        1. Create a `tk.Menu` instance and attach it to the root window.
        2. Define submenus:
           - **File**
             * Open: Launches a file dialog to load text data.
             * Load Test Data: Loads predefined test data from a file.
             * Quit: Exits the application.
           - **Preferences**
             * Settings: Opens the settings dialog.
             * User Template: Switches to user template mode.
           - **Help**
             * Documentation: Opens the "Getting Started" guide in a browser.
             * View Licenses: Opens the license information page.
             * About: Displays application metadata.
        3. Add separators between logical groups of commands for clarity.

        Returns
        -------
        None
            This method performs side effects (constructing and attaching the
            menubar) but does not return a value.

        Notes
        -----
        - The menubar is attached to `self.root` via `self.root.config(menu=...)`.
        - Each command delegates to a corresponding callback method for handling
          user actions.
        - Separators are used to visually group related commands.
        """

        menu_bar = tk.Menu(self.root)
        self.root.config(menu=menu_bar)

        file_menu = tk.Menu(menu_bar, tearoff=False)
        help_menu = tk.Menu(menu_bar, tearoff=False)
        pref_menu = tk.Menu(menu_bar, tearoff=False)

        menu_bar.add_cascade(menu=file_menu, label='File')
        menu_bar.add_cascade(menu=pref_menu, label='Preferences')
        menu_bar.add_cascade(menu=help_menu, label='Help')

        menu_structure = (
            # File menu
            (file_menu, dict(label='Open',command=self.callback_open_file)),
            (file_menu, dict(label='Load Test Data',
                             command=self.callback_load_test_data_file)),
            (file_menu, None),
            (file_menu, dict(label='Quit',command=self.callback_file_exit)),

            # Preferences menu
            (pref_menu, dict(label='Settings',
                             command=self.callback_preferences_settings)),
            (pref_menu, None),
            (pref_menu, dict(label='User Template',
                             command=self.callback_preferences_user_template)),

            # Help menu
            (help_menu, dict(label='Documentation',
                             command=self.callback_help_documentation)),
            (help_menu, dict(label='View Licenses',
                             command=self.callback_help_view_licenses)),
            (help_menu, None),
            (help_menu, dict(label='About',
                             command=self.callback_help_about)),
        )

        for menu, config in menu_structure:
            if config:
                menu.add_command(**config)
            else:
                menu.add_separator()

    def build_frame(self):
        """
        Construct the main layout frames for the TextFSM generator GUI.

        This method initializes a vertical `PanedWindow` and organizes
        the primary sections of the interface: text input, entry controls,
        backup view, and result display. Each frame is created with fixed
        dimensions and ridge borders, then added to the paned window with
        relative weights to control resizing behavior.

        Workflow
        --------
        1. Create a vertical `PanedWindow` and attach it to the root window.
        2. Define four frames:
           - **Text Frame**: Input area for test data.
           - **Entry Frame**: Controls and action buttons.
           - **Backup Frame**: Alternate view for backup app state.
           - **Result Frame**: Output area for TextFSM template results.
        3. Add frames to the `PanedWindow` with weights to manage resizing.

        Returns
        -------
        None
            This method performs side effects (constructing and attaching
            frames) but does not return a value.

        Notes
        -----
        - The `PanedWindow` is packed to expand and fill both dimensions
          with padding for spacing.
        - Frame weights determine how much space each section receives
          when resizing the window.
        """

        # Create main paned window
        self.paned_window = self.PanedWindow(self.root, orient=tk.VERTICAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        # Define frames
        self.text_frame = self.Frame(
            self.paned_window, width=600, height=300, relief=tk.RIDGE
        )
        self.entry_frame = self.Frame(
            self.paned_window, width=600, height=10, relief=tk.RIDGE
        )
        self.backup_frame = self.Frame(
            self.paned_window, width=600, height=10, relief=tk.RIDGE
        )
        self.result_frame = self.Frame(
            self.paned_window, width=600, height=350, relief=tk.RIDGE
        )

        # Add frames to paned window with weights
        self.paned_window.add(self.text_frame, weight=2)
        self.paned_window.add(self.entry_frame)
        self.paned_window.add(self.result_frame, weight=7)

    def build_textarea(self):
        """
        Construct the main input text area for the TextFSM generator GUI.

        This method creates a scrollable `TextArea` widget inside the
        `text_frame`. The widget serves as the primary input field for
        entering or editing text data used in TextFSM testing. Both vertical
        and horizontal scrollbars are attached to support navigation of
        large or unwrapped text content.

        Workflow
        --------
        1. Configure the `text_frame` grid to allow resizing.
        2. Create a `TextArea` widget with fixed dimensions and no wrapping.
        3. Place the `TextArea` in the grid at row 0, column 0, expanding
           in all directions (`nswe`).
        4. Add a vertical scrollbar linked to the `yview` of the text area.
        5. Add a horizontal scrollbar linked to the `xview` of the text area.
        6. Configure the text area to update scrollbar positions during
           scrolling.

        Returns
        -------
        None
            This method performs side effects (constructing and attaching
            widgets) but does not return a value.

        Notes
        -----
        - The `wrap='none'` option ensures text does not automatically wrap,
          making horizontal scrolling necessary for long lines.
        - Scrollbars are synchronized with the text area via `yscrollcommand`
          and `xscrollcommand`.
        """
        # Configure grid for resizing
        self.text_frame.rowconfigure(0, weight=1)
        self.text_frame.columnconfigure(0, weight=1)

        # Create main input text area
        self.input_textarea = self.TextArea(
            self.text_frame, width=20, height=5, wrap='none',
            name='main_input_textarea',
        )
        self.input_textarea.grid(row=0, column=0, sticky='nswe')

        # Add vertical scrollbar
        vscrollbar = ttk.Scrollbar(
            self.text_frame, orient=tk.VERTICAL,
            command=self.input_textarea.yview
        )
        vscrollbar.grid(row=0, column=1, sticky='ns')

        # Add horizontal scrollbar
        hscrollbar = ttk.Scrollbar(
            self.text_frame, orient=tk.HORIZONTAL,
            command=self.input_textarea.xview
        )
        hscrollbar.grid(row=1, column=0, sticky='ew')

        # Link scrollbars to text area
        self.input_textarea.config(
            yscrollcommand=vscrollbar.set,
            xscrollcommand=hscrollbar.set
        )

    def build_entry(self):
        """
        Construct the entry controls section for the TextFSM Generator GUI.

        This method builds the `entry_frame` portion of the interface, which
        contains interactive widgets such as buttons, text fields, and other
        controls used to trigger actions (e.g., opening files, running regex
        tests, saving results, or switching modes). It provides the user with
        the primary means of interacting with the application beyond text input.

        Workflow
        --------
        1. Initialize the `entry_frame` container.
        2. Populate the frame with action-oriented widgets (buttons, textboxes,
           comboboxes, etc.).
        3. Configure layout and grid options to ensure controls are aligned
           and responsive to resizing.

        Returns
        -------
        None
            This method performs side effects (constructing and attaching
            widgets) but does not return a value.

        Notes
        -----
        - The `entry_frame` is positioned between the text input area and
          the result display frame.
        - Widgets added here typically connect to callback methods such as
          `callback_file_open`, `callback_preferences_*`, or template execution
          functions.
        - Acts as the control hub for user actions in the GUI.
        """

        def callback_build_btn():
            """
            Handle the 'Build' button action to generate a TextFSM template.

            This callback validates the presence of user input before attempting
            to build a TextFSM template using `TemplateBuilder`. On success, the
            generated template is displayed in the result text area and relevant
            snapshot attributes are updated. If template generation fails due to
            invalid format or other errors, appropriate error messages are shown
            and fallback content is provided.

            Workflow
            --------
            1. Validate prerequisites:
               - If no user input is provided, show an error message and abort.
            2. Attempt to build a template using `TemplateBuilder`.
               - On success:
                 * Update snapshot with user data, template, and result.
                 * Mark template as built.
                 * Enable "Save As" and "Copy" buttons.
                 * Display template in result text area.
                 * Update snapshot and window title.
            3. On `TemplateBuilderInvalidFormat`:
               - Show error message indicating invalid template format.
            4. On other exceptions:
               - Show generic error message.
               - Attempt to build a debug template with `bad_template`.
               - Display fallback content in result text area.
               - Update snapshot and window title.
            5. If template exists, enable "Store" button.
            6. If template is built, enable "Result" button.

            Returns
            -------
            None
                This method performs side effects (UI updates, snapshot changes,
                template generation, error reporting) but does not return a value.

            Notes
            -----
            - Snapshot attributes `user_data`, `template`, `result`, and `is_built`
              are updated on success.
            - Fallback content includes a comment instructing the user to fix input
              data when template generation fails.
            """

            user_data = Application.get_textarea(self.input_textarea)
            if not user_data:
                create_msgbox(
                    title="Missing Input Data",
                    error="Unable to build TextFSM template: no data provided."
                )
                return

            try:
                kwargs = self.get_template_args()
                factory = TemplateBuilder(user_data=user_data, **kwargs)

                # Update snapshot with generated template
                self.snapshot.update(
                    user_data=user_data,
                    result=factory.template,
                    template=factory.template,
                    swich_app_template="",  # typo preserved from original
                    is_built=True,
                )

                # Enable buttons and update UI
                self.test_data_btn_var.set('Test Data')
                self.save_as_btn.config(state=tk.NORMAL)
                self.copy_text_btn.config(state=tk.NORMAL)
                self.set_textarea(self.result_textarea, factory.template)

                title = "Generating Template"
                self.snapshot.update(title=title)
                self.set_title(title=title)
            except TemplateBuilderInvalidFormat as ex:
                create_msgbox(
                    title="Invalid TextFSM Template Format",
                    error=f"{type(ex).__name__}: {ex}"
                )
            except Exception as ex:
                create_msgbox(
                    title="Template Generation Error",
                    error=f"{type(ex).__name__}: {ex}"
                )
                kwargs = self.get_template_args()
                factory = TemplateBuilder(user_data=user_data, debug=True, **kwargs)
                content = (f"# Please fix user_data to produce "
                           f"a good template\n{factory.bad_template}")
                self.set_textarea(self.result_textarea, content)

                title = "Invalid Generated Template"
                self.snapshot.update(title=title)
                self.set_title(title=title)

            # Enable additional buttons if template exists/built
            if self.snapshot.template:
                self.store_btn.config(state=tk.NORMAL)

            if self.snapshot.is_built:
                self.result_btn.config(state=tk.NORMAL)

        def callback_save_as_btn():
            """
            Handle the 'Save As' button action for input or output text areas.

            This is an inner function defined within Application.build_entry.

            This callback determines the appropriate file type and extension based
            on the content of the active widget (input or result text area). It then
            prompts the user to choose a filename and saves the content accordingly.
            Special handling is applied for Python unittest/pytest scripts to enforce
            naming conventions, and for empty content to confirm whether saving should
            proceed.

            Workflow
            --------
            1. Identify the active widget:
               - Input text area → save as plain text (.txt).
               - Result text area → inspect content:
                 * If Python unittest/pytest script → save as `.py` file.
                 * If TextFSM template → save as `.textfsm` file.
                 * Otherwise → save as plain text (.txt).
            2. Prompt user with a save dialog (`asksaveasfilename`) using appropriate
               title and file type filters.
            3. If filename is chosen:
               - Ensure correct file extension is applied.
               - For unittest/pytest scripts:
                 * Enforce naming convention `test_<filename>.py`.
                 * Prompt user to confirm renaming if convention is not followed.
               - If content is empty:
                 * Prompt user to confirm saving an empty file.
            4. Save the file if user confirms.

            Returns
            -------
            None
                This method performs side effects (file save, UI updates, message boxes)
                but does not return a value.

            Notes
            -----
            - Snapshot state is not updated here; only file saving is performed.
            - Naming convention enforcement ensures compatibility with pytest/unittest.
            - Mixed results containing multiple sections are saved as plain text.
            """

            prev_widget_name = str(self.prev_widget)
            is_input_area = prev_widget_name.endswith('.main_input_textarea')
            widget = self.input_textarea if is_input_area else self.result_textarea
            content = Application.get_textarea(widget)

            # Default settings
            is_mixed_result = '<<====================>>' in content
            test_type = ''
            is_unittest_or_pytest = False
            extension = '.txt'

            if is_input_area:
                title = 'Save Input Text'
                filetypes = [('Text Files', '*.txt'), ('All Files', '*')]
            else:
                # Detect script or template type
                pattern_script = r'"+ *(?P<text>Python +(?P<test_type>\w+) +script) '
                pattern_template = r'#+\s+# *Template +is +generated '
                match = re.match(pattern_script, content, re.I)
                if match:
                    title = 'Saving {}'.format(match.group('text')).title()
                    test_type = match.group('test_type')
                    is_unittest_or_pytest |= 'unittest' == test_type
                    is_unittest_or_pytest |= 'pytest' == test_type
                    filetypes = [('Python Files', '*.py'), ('All Files', '*')]
                    extension = '.py'
                elif re.match(pattern_template, content, re.I) and not is_mixed_result:
                    title = 'Save TextFSM Template'
                    filetypes = [('TextFSM Files', '*.textfsm'), ('All Files', '*')]
                    extension = '.textfsm'
                else:
                    title = 'Save Output Text'
                    filetypes = [('Text Files', '*.txt'), ('All Files', '*')]

            # Prompt user for filename
            filename = filedialog.asksaveasfilename(title=title, filetypes=filetypes)
            if not filename:
                return

            node = PurePath(filename)
            if not node.suffix:
                node = node.with_suffix(extension)

            # Enforce naming convention for unittest/pytest
            if is_unittest_or_pytest:
                name = node.name
                if not name.startswith('test_'):
                    new_name = 'test_{}'.format(name)
                    response = create_msgbox(
                        title='Unittest/Pytest Naming Convention',
                        yesnocancel=f"""
                            {test_type.title()} - "{name}" does not follow the required naming convention: test_<filename>.
                            Yes: Save using "{new_name}".
                            No: Save using "{name}".
                            Cancel: Do not save.
                            Would you like to proceed?
                        """
                    )
                    if response is None:    # Cancel
                        return
                    else:   # Yes → rename
                        if response:
                            node = node.with_name(new_name)
            filename = str(node)
            if not content.strip():
                response = create_msgbox(
                    title=f"{title} - Empty",
                    question=(
                        f'The content of "{filename}" is empty.\n'
                        'Do you want to save the empty file?'
                    )
                )
            else:
                response = 'yes'

            if response == 'yes':
                file.write(filename, content)

        def callback_clear_text_btn():
            """
            Handle the 'Clear' button action for text widgets.

            This is an inner function defined within Application.build_entry.

            This callback clears text content depending on the active widget:

            - If the active widget is the template name textbox:
              * Clear the selected text if a selection exists.
              * Otherwise, clear the entire template name field.
            - If the active widget is the input text area:
              * Clear the selected text if a selection exists.
              * Otherwise, clear both input and result text areas, reset related
                buttons, and update snapshot state to reflect cleared data.

            Workflow
            --------
            1. Identify the active widget by its name.
            2. If template name textbox:
               - Clear selection or reset template name variable.
               - Update snapshot and window title.
            3. If input text area:
               - Clear selection if present.
               - Otherwise, clear input/result areas, disable related buttons,
                 reset snapshot attributes, and restore defaults.
            4. Update snapshot title and window title.
            5. Return focus to the appropriate widget.

            Returns
            -------
            None
                This method performs side effects (UI updates, snapshot changes,
                text clearing) but does not return a value.

            Notes
            -----
            - Snapshot attributes `user_data`, `test_data`, `result`, `template`,
              and `is_built` are reset when clearing input and test data.
            - Clipboard clearing is commented out but can be enabled if desired.
            """

            prev_widget_name = str(self.prev_widget)
            is_tmpl_name = prev_widget_name.endswith('.main_template_name_textbox')
            is_input_area = prev_widget_name.endswith('.main_input_textarea')
            if is_tmpl_name:
                # --- Template name textbox ---
                if self.prev_widget.selection_present():
                    self.prev_widget.delete(tk.SEL_FIRST, tk.SEL_LAST)
                    title = 'Clear Selected Text'
                else:
                    self.template_name_var.set('')
                    title = 'Clear Template Name'

                self.snapshot.update(title=title)
                self.set_title(title=title)
                self.prev_widget.focus()
            else:
                # --- Input text area or other ---
                if is_input_area and self.prev_widget.tag_ranges(tk.SEL):
                    self.prev_widget.delete(tk.SEL_FIRST, tk.SEL_LAST)
                    title = 'Clear Selected Text'
                else:
                    # Clear input and result areas
                    Application.clear_textarea(self.input_textarea)
                    Application.clear_textarea(self.result_textarea)

                    # Disable related buttons
                    disabled_buttons = [
                        self.save_as_btn, self.copy_text_btn,
                        self.test_data_btn, self.result_btn, self.store_btn
                    ]

                    for button in disabled_buttons:
                        button.config(state=tk.DISABLED)

                    # Reset input area state
                    self.input_textarea.config(state=tk.NORMAL)

                    # Reset snapshot attributes
                    self.snapshot.update(
                        user_data="",
                        test_data=None,
                        result="",
                        template="",
                        is_built=False,
                    )

                    # Reset UI variables
                    self.test_data_btn_var.set('Test Data')
                    self.build_btn_var.set('Build')
                    self.template_name_var.set('')
                    self.search_checkbox_var.set(False)
                    # self.root.clipboard_clear()
                    title = 'Clear Input Text and Test Data'

                self.snapshot.update(title=title)
                self.set_title(title=title)
                self.input_textarea.focus()

        def callback_copy_text_btn():
            """
            Handle the 'Copy' button action for text widgets.

            This is an inner function defined within Application.build_entry.

            This callback determines the active widget and copies its content
            (or selected text) to the system clipboard. The window title is updated
            to reflect the copy action.

            Behavior
            --------
            - If the active widget is the template name textbox:
              * Copy the selected text if available.
              * Otherwise, copy the entire template name.
            - If the active widget is the input text area:
              * Copy the selected text if available.
              * Otherwise, copy the entire input text.
            - Otherwise (default case):
              * Copy the entire output text area content.

            Workflow
            --------
            1. Identify the active widget by its name.
            2. Retrieve the appropriate content (selection or full text).
            3. Update the window title to reflect the copy action.
            4. Clear the clipboard, append the copied content, and update the root.

            Returns
            -------
            None
                This method performs side effects (clipboard operations, UI updates)
                but does not return a value.

            Notes
            -----
            - Clipboard content replaces any existing clipboard data.
            - Snapshot title is not updated here; only the window title is set.
            """

            prev_widget_name = str(self.prev_widget)
            is_tmpl_name = prev_widget_name.endswith('.main_template_name_textbox')
            is_input_area = prev_widget_name.endswith('.main_input_textarea')
            if is_tmpl_name:
                if self.prev_widget.selection_present():
                    content = self.prev_widget.selection_get()
                    title = 'Copy Selected Text'
                else:
                    content = self.template_name_var.get()
                    title = 'Copy Template Name'
            elif is_input_area:
                if self.prev_widget.tag_ranges(tk.SEL):
                    content = self.prev_widget.selection_get()
                    title = 'Copy Selected Text'
                else:
                    content = Application.get_textarea(self.input_textarea)
                    title = 'Copy Input Text'
            else:
                content = Application.get_textarea(self.result_textarea)
                title = 'Copy Output Text'

            # Update UI and clipboard
            self.set_title(title=title)
            self.root.clipboard_clear()
            self.root.clipboard_append(content)
            self.root.update()

        def callback_paste_text_btn():
            """
            Handle the 'Paste' button action for text input areas.

            This is an inner function defined within Application.build_entry.

            This callback retrieves text from the system clipboard and pastes it
            into the appropriate widget depending on context:

            - If the active widget is the template name textbox, the clipboard
              content is inserted into the template name field.
            - If the active widget is the input text area and it already contains
              data, the clipboard content is inserted at the cursor position.
            - Otherwise, the clipboard content is treated as new test data:
              * The input text area is cleared and populated with the clipboard data.
              * The result text area is reset.
              * Snapshot attributes are updated with the new test data.

            Workflow
            --------
            1. Retrieve current data from the input text area and determine the
               active widget type (template name textbox or input area).
            2. Attempt to fetch clipboard content.
               - If clipboard is empty, abort.
            3. Depending on the active widget:
               - Template name textbox → insert clipboard text into the field.
               - Input area with existing content → insert clipboard text at cursor.
               - Otherwise → treat clipboard text as new test data and reset state.
            4. Enable "Copy" and "Save As" buttons.
            5. Update snapshot title and window title accordingly.
            6. On error, display a message box indicating clipboard is empty.

            Returns
            -------
            None
                This method performs side effects (UI updates, snapshot changes,
                error reporting) but does not return a value.

            Notes
            -----
            - Clipboard content is inserted at the current cursor position or
              replaces the current selection if one exists.
            - Snapshot attributes `test_data`, `result`, and `title` are updated
              based on the paste action.
            """

            curr_data = Application.get_textarea(self.input_textarea)
            prev_widget_name = str(self.prev_widget)

            is_not_empty = len(curr_data.strip()) > 0
            is_tmpl_name = prev_widget_name.endswith('.main_template_name_textbox')
            is_input_area = prev_widget_name.endswith('.main_input_textarea')
            try:
                data = self.root.clipboard_get()
                if not data:
                    return

                if is_tmpl_name:
                    # Paste into template name textbox
                    if self.prev_widget.selection_present():
                        self.prev_widget.delete(tk.SEL_FIRST, tk.SEL_LAST)
                    index = self.prev_widget.index(tk.INSERT)
                    self.prev_widget.insert(tk.INSERT, data)
                    self.prev_widget.selection_range(index, index + len(data))
                    self.prev_widget.focus()
                    title = "Paste into Template Name"
                elif is_input_area and is_not_empty:
                    # Paste into input area with existing content
                    if self.prev_widget.tag_ranges(tk.SEL):
                        self.prev_widget.delete(tk.SEL_FIRST, tk.SEL_LAST)
                    index = self.prev_widget.index(tk.INSERT)
                    self.prev_widget.insert(tk.INSERT, data)
                    self.prev_widget.tag_add(tk.SEL, index, f"{index}+{len(data)}c")
                    self.prev_widget.focus()
                    title = "Paste into Input Area"
                else:
                    # Paste as new test data
                    self.clear_text_btn.invoke()
                    self.test_data_btn.config(state=tk.NORMAL)
                    self.test_data_btn_var.set('Test Data')
                    self.set_textarea(self.result_textarea, '')
                    self.snapshot.update(
                        test_data=data,
                        result=''
                    )

                    title = "Paste and Load Test Data"
                    self.set_textarea(self.input_textarea, data)
                    self.input_textarea.focus()

                # Enable actions
                self.copy_text_btn.configure(state=tk.NORMAL)
                self.save_as_btn.configure(state=tk.NORMAL)

                # Update snapshot and UI
                self.snapshot.update(title=title)
                self.set_title(title=title)

            except Exception as ex:     # noqa
                create_msgbox(
                    title="Clipboard Empty",
                    info="Cannot paste because the clipboard contains no data."
                )

        def callback_snippet_btn():
            """
            Handle the 'Snippet' button action to generate a lightweight Python test script.

            This is an inner function defined within Application.build_entry.

            This callback validates the presence of test data and user input before
            attempting to build a Python snippet script using `TemplateBuilder`.
            If either prerequisite is missing, an error message is displayed. On success,
            the generated script is displayed in the result text area, the snapshot is
            updated, and relevant buttons are enabled for saving and copying.

            Workflow
            --------
            1. Validate prerequisites:
               - If no test data is loaded, show an error message and abort.
               - If no user input is provided, show an error message and abort.
            2. Attempt to build a Python snippet script using `TemplateBuilder`.
               - Pass both user data and test data along with template arguments.
               - On success, update snapshot and UI with the generated script.
               - Enable "Save As" and "Copy" buttons for further actions.
            3. On error, display a message box with the exception details.

            Returns
            -------
            None
                This method performs side effects (UI updates, snapshot changes,
                script generation, error reporting) but does not return a value.

            Notes
            -----
            - Snapshot attributes `title` and `result` are updated with the script.
            - The result text area is populated with the generated snippet script.
            - Exceptions are caught broadly to ensure user feedback, but more
              granular handling may be added for specific error types.
            """
            # --- Validate prerequisites ---
            if self.snapshot.test_data is None:
                create_msgbox(
                    title="Missing Test Data",
                    error=(
                        "Cannot build a Python test script without test data.\n"
                        "Please use the Open or Paste button to load test data."
                    )
                )
                return

            user_data = Application.get_textarea(self.input_textarea)
            if not user_data:
                create_msgbox(
                    title="Missing User Data",
                    error=(
                        "Cannot build a Python test script without data.\n"
                        "Please provide or load the required input."
                    )
                )
                return

            # --- Build snippet script ---
            try:
                kwargs = self.get_template_args()
                factory = TemplateBuilder(
                    user_data=user_data,
                    test_data=self.snapshot.test_data,
                    **kwargs
                )
                script = factory.create_python_test()

                # Update snapshot and UI
                title = "Generate Python Snippet Script"
                self.snapshot.update(title=title)
                self.set_title(title=title)
                self.set_textarea(self.result_textarea, script)

                # Update toggle and enable actions
                self.test_data_btn_var.set('Test Data')
                self.snapshot.update(result=script)
                self.save_as_btn.config(state=tk.NORMAL)
                self.copy_text_btn.config(state=tk.NORMAL)
            except Exception as ex:
                create_msgbox(
                    title='TextFSM Generator Error',
                    error=f"{type(ex).__name__}: {ex}"
                )

        def callback_unittest_btn():
            """
            Handle the 'Unittest' button action to generate a Python unittest script.

            This is an inner function defined within Application.build_entry.

            This callback validates the presence of test data and user input before
            attempting to build a unittest script using `TemplateBuilder`. If either
            prerequisite is missing, an error message is displayed. On success, the
            generated unittest script is displayed in the result text area, the snapshot
            is updated, and relevant buttons are enabled for saving and copying.

            Workflow
            --------
            1. Validate prerequisites:
               - If no test data is loaded, show an error message and abort.
               - If no user input is provided, show an error message and abort.
            2. Attempt to build a unittest script using `TemplateBuilder`.
               - Pass both user data and test data along with template arguments.
               - On success, update snapshot and UI with the generated script.
               - Enable "Save As" and "Copy" buttons for further actions.
            3. On error, display a message box with the exception details.

            Returns
            -------
            None
                This method performs side effects (UI updates, snapshot changes,
                script generation, error reporting) but does not return a value.

            Notes
            -----
            - Snapshot attributes `title` and `result` are updated with the script.
            - The result text area is populated with the generated unittest script.
            - Exceptions are caught broadly to ensure user feedback, but more
              granular handling may be added for specific error types.
            """

            # --- Validate prerequisites ---
            if self.snapshot.test_data is None:
                create_msgbox(
                    title="Missing Test Data",
                    error=(
                        "Cannot build a Python unittest script without test data.\n"
                        "Please use the Open or Paste button to load the required data."
                    )
                )
                return

            user_data = Application.get_textarea(self.input_textarea)
            if not user_data:
                create_msgbox(
                    title="Missing User Data",
                    error=(
                        "Cannot build a Python unittest script without data.\n"
                        "Please provide or load the required user data."
                    )
                )
                return

            # --- Build unittest script ---
            try:
                kwargs = self.get_template_args()
                factory = TemplateBuilder(
                    user_data=user_data,
                    test_data=self.snapshot.test_data,
                    **kwargs
                )
                script = factory.create_unittest()

                # Update snapshot and UI
                title = "Generating Python Unittest Script"
                self.snapshot.update(title=title)
                self.set_title(title=title)
                self.set_textarea(self.result_textarea, script)

                # Update toggle and enable actions
                self.test_data_btn_var.set('Test Data')
                self.snapshot.update(result=script)
                self.save_as_btn.config(state=tk.NORMAL)
                self.copy_text_btn.config(state=tk.NORMAL)
            except Exception as ex:
                create_msgbox(
                    title='TextFSM Generator Error',
                    error=f"{type(ex).__name__}: {ex}"
                )

        def callback_pytest_btn():
            """
            Handle the 'Pytest' button action to generate a Python pytest script.

            This is an inner function defined within Application.build_entry.

            This callback validates the presence of test data and user input before
            attempting to build a pytest script using `TemplateBuilder`. If either
            prerequisite is missing, an error message is displayed. On success, the
            generated pytest script is displayed in the result text area, the snapshot
            is updated, and relevant buttons are enabled for saving and copying.

            Workflow
            --------
            1. Validate prerequisites:
               - If no test data is loaded, show an error message and abort.
               - If no user input is provided, show an error message and abort.
            2. Attempt to build a pytest script using `TemplateBuilder`.
               - Pass both user data and test data along with template arguments.
               - On success, update snapshot and UI with the generated script.
               - Enable "Save As" and "Copy" buttons for further actions.
            3. On error, display a message box with the exception details.

            Returns
            -------
            None
                This method performs side effects (UI updates, snapshot changes,
                script generation, error reporting) but does not return a value.

            Notes
            -----
            - Snapshot attributes `title` and `result` are updated with the script.
            - The result text area is populated with the generated pytest script.
            - Exceptions are caught broadly to ensure user feedback, but more
              granular handling may be added for specific error types.
            """

            # --- Validate prerequisites ---
            if self.snapshot.test_data is None:
                create_msgbox(
                    title="Missing Test Data",
                    error=(
                        "Cannot build a Python pytest script without test data.\n"
                        "Please use the Open or Paste button to load the required data."
                    )
                )
                return

            user_data = Application.get_textarea(self.input_textarea)
            if not user_data:
                create_msgbox(
                    title="Missing User Data",
                    error=(
                        "Cannot build a Python pytest script without data.\n"
                        "Please provide or load the required user data."
                    )
                )
                return

            # --- Build pytest script ---
            try:
                kwargs = self.get_template_args()
                factory = TemplateBuilder(
                    user_data=user_data,
                    test_data=self.snapshot.test_data,
                    **kwargs
                )
                script = factory.create_pytest()

                # Update snapshot and UI
                title = 'Generating Python Pytest Script'
                self.snapshot.update(title=title)
                self.set_title(title=title)
                self.set_textarea(self.result_textarea, script)

                # Update toggle and enable actions
                self.test_data_btn_var.set('Test Data')
                self.snapshot.update(result=script)
                self.save_as_btn.config(state=tk.NORMAL)
                self.copy_text_btn.config(state=tk.NORMAL)
            except Exception as ex:
                create_msgbox(
                    title='TextFSM Generator Error',
                    error=f"{type(ex).__name__}: {ex}"
                )

        def callback_test_data_btn():
            """
            Handle the 'Test Data' button toggle.

            This is an inner function defined within Application.build_entry.

            This callback toggles the display of test data in the result text area.
            When the button label is "Test Data", the test data is shown and the
            button label changes to "Hide". When the label is "Hide", the result
            text area is restored to the previously stored result and the button
            label changes back to "Test Data".

            Workflow
            --------
            1. Validate that test data exists in the snapshot.
               - If not, show an error message and abort.
            2. If the button label is "Test Data":
               - Change the label to "Hide".
               - Update the snapshot title and window title to "Showing Test Data".
               - Display the test data in the result text area.
            3. If the button label is "Hide":
               - Change the label back to "Test Data".
               - Restore the window title from the snapshot.
               - Display the snapshot result in the result text area.

            Returns
            -------
            None
                This method performs side effects (UI updates, snapshot changes,
                error reporting) but does not return a value.

            Notes
            -----
            - The snapshot attributes `test_data` and `result` are used to toggle
              between views.
            - The button label (`test_data_btn_var`) acts as the toggle state.
            """

            if self.snapshot.test_data is None:
                create_msgbox(
                    title='No Test Data',
                    error="Please use Open or Paste button to load test data"
                )
                return

            name = self.test_data_btn_var.get()
            if name == 'Test Data':
                # Show test data
                self.test_data_btn_var.set('Hide')
                title = self.root.title().replace(' - ' + self._base_title, '')
                self.snapshot.update(title=title)
                self.set_title(title='Showing Test Data')
                self.set_textarea(
                    self.result_textarea,
                    self.snapshot.test_data
                )
            else:
                # Restore result view
                self.test_data_btn_var.set('Test Data')
                self.set_title(title=self.snapshot.title)
                self.set_textarea(
                    self.result_textarea,
                    self.snapshot.result
                )

        def callback_result_btn():
            """
            Handle the 'Result' button action to parse test data with a TextFSM template.

            This is an inner function defined within Application.build_entry.

            This callback validates the presence of test data and user input before
            attempting to build or reuse a regex template. It then parses the test
            data using TextFSM and displays the results in the result text area.
            Depending on user-selected options, the output may include the template,
            the test data, and the parsed results (formatted either as tabular or
            pretty-printed data).

            Workflow
            --------
            1. Validate prerequisites:
               - If no test data is loaded, show an error message.
               - If no user input is provided, show an error message.
            2. Attempt to build a template using `TemplateBuilder`.
               - On success, update snapshot with template and mark as built.
               - On failure, fall back to existing snapshot template.
               - If no template is available, show an error message.
            3. Parse the test data using TextFSM.
            4. Construct the result string:
               - Include template if `template_checkbox_var` is selected.
               - Include test data if `test_data_checkbox_var` is selected.
               - Always include parsed results:
                 * Tabular format if `tabular_checkbox_var` is selected.
                 * Otherwise, pretty-printed dictionary format.
            5. Update snapshot, window title, and result text area with the output.

            Returns
            -------
            None
                This method performs side effects (UI updates, snapshot changes,
                parsing results) but does not return a value.

            Notes
            -----
            - Templates are stripped of whitespace before comparison.
            - Output sections are separated by a formatted divider string.
            - Snapshot attributes `test_data`, `template`, and `result` are updated.
            """

            # --- Validate prerequisites ---
            if self.snapshot.test_data is None:
                create_msgbox(
                    title='No Test Data',
                    error=("Can NOT parse text without "
                           "test data.\nPlease use Open or Paste button "
                           "to load test data")
                )
                return

            user_data = Application.get_textarea(self.input_textarea)
            if not user_data:
                create_msgbox(
                    title='Empty Data',
                    error="Can NOT build regex pattern without data."
                )
                return

            # --- Build or reuse template ---
            try:
                kwargs = self.get_template_args()
                factory = TemplateBuilder(user_data=user_data, **kwargs)
                self.snapshot.update(
                    user_data=user_data,
                    template=factory.template,
                    is_built=True
                )
                template = factory.template
            except Exception as ex:
                template = self.snapshot.template.strip()
                if not template:
                    create_msgbox(
                        title='TextFSM Generator Error',
                        error=f"{type(ex).__name__}: {ex}"
                    )
                    return

            # --- Parse test data ---
            stream = StringIO(template)
            parser = TextFSM(stream)
            rows = parser.ParseTextToDicts(self.snapshot.test_data)

            # --- Construct result string ---
            result = ''
            test_data = self.snapshot.test_data
            divider_fmt = '\n\n<<{}>>\n\n{{}}'.format('=' * 20)

            result_sections = []

            if self.template_checkbox_var.get() and template:
                result_sections.append('Template')
                result += divider_fmt.format(template) if result else template

            if self.test_data_checkbox_var.get() and test_data:
                result_sections.append('Test Data')
                result += divider_fmt.format(test_data) if result else test_data

            result_sections.append('Test Result')
            if rows and self.tabular_checkbox_var.get():
                tabular_data = get_data_as_tabular(rows)
                result += divider_fmt.format(tabular_data) if result else tabular_data
            else:
                pretty_data = pformat(rows)
                result += divider_fmt.format(pretty_data) if result else pretty_data

            # --- Update snapshot and UI ---
            self.test_data_btn_var.set('Test Data')
            self.snapshot.update(result=result)

            title = 'Showing {}'.format(' + '.join(result_sections))
            self.snapshot.update(title=title)
            self.set_title(title=title)
            self.set_textarea(self.result_textarea, result)

        def callback_store_btn():
            """
            Handle the 'Store' button action for user templates.

            This is an inner function defined within Application.build_entry.

            This callback ensures that the user template file exists before
            storing the current application state. If the file does not exist,
            the user is prompted to create it. Once the file is available, the
            current input and result text areas are saved into the snapshot,
            and the application is shifted into backup mode.

            Workflow
            --------
            1. Check if the user template file exists.
               - If not, prompt the user to create it.
               - If the user declines, abort the operation.
               - If accepted, create the file without confirmation.
            2. If the file exists:
               - Retrieve input and result text from the text areas.
               - Update the snapshot with user and result data.
               - Restore the input text area with the current template.
               - Restore the result text area with the file content.
               - Shift the application into backup mode.

            Returns
            -------
            None
                This method performs side effects (UI updates, snapshot changes,
                file creation, backup mode transition) but does not return a value.

            Notes
            -----
            - The snapshot attributes `switch_app_user_data`, `switch_app_result_data`,
              and `switch_app_template` are updated to preserve state.
            - If `switch_app_template` is not available, the fallback is `snapshot.template`.
            - The backup mode transition is handled by `shift_to_backup_app`.
            """

            user_template = UserTemplate()

            # Ensure template file exists
            if not user_template.is_exist():
                response = create_msgbox(
                    title="User Template File Not Found",
                    question=(
                        f"This feature is only available when the "
                        f"file {repr(user_template.filename)} exists.\n"
                        "Would you like to create this file now?"
                    )
                )
                if response == 'no':
                    return
                else:
                    user_template.create(confirmed=False)

            if user_template.is_exist():
                # Save current input and result data into snapshot
                user_data = self.get_textarea(self.input_textarea)
                result_data = self.get_textarea(self.result_textarea)
                self.snapshot.update(
                    switch_app_user_data=user_data,
                    switch_app_result_data=result_data
                )

                # Restore text areas with template and file content
                data = self.snapshot.switch_app_template or self.snapshot.template
                self.set_textarea(self.input_textarea, data)
                self.set_textarea(self.result_textarea, user_template.read())

                # Transition to back up mode
                self.shift_to_backup_app()

        def callback_search_checkbox():
            """
            Handle the 'Search' checkbox toggle for user templates.

            This is an inner function defined within Application.build_entry.

            This callback enables or disables the template search mode depending
            on the state of `search_checkbox_var`. When enabled, it disables other
            editing buttons, shows lookup controls, and attempts to load the
            requested template. When disabled, it restores the normal editing
            state, re-enables buttons, and restores the snapshot content.

            Workflow
            --------
            1. Verify that the user template file exists.
               - If not, show an info message and reset the checkbox.
            2. If search mode is enabled:
               - Disable editing buttons and input area.
               - Show lookup and close-lookup buttons.
               - Save current input/result text to snapshot.
               - If a template name is provided, attempt to search and load it.
               - Update result area with the user template file content.
               - Update snapshot and window title to "Searching Template".
            3. If search mode is disabled:
               - Re-enable editing buttons based on snapshot state.
               - Hide lookup controls.
               - Restore input/result text areas from snapshot.
               - Re-enable copy/save buttons if content exists.
               - Restore snapshot title and update window title.

            Returns
            -------
            None
                This method performs side effects (UI updates, snapshot changes,
                error reporting) but does not return a value.

            Notes
            -----
            - Template names are stripped of whitespace before lookup.
            - Snapshot attributes such as `main_input_textarea`, `main_result_textarea`,
              `test_data`, and `is_built` are used to restore state.
            - Regex is used to detect auto-generated templates and adjust the
              "Test Data" button label accordingly.
            """

            user_template = UserTemplate()
            if not user_template.is_exist():
                create_msgbox(
                    title="User Template File Not Found",
                    info=(
                        f"This feature is only available "
                        f"when the file {repr(user_template.filename)} exists."
                    )
                )
                self.search_checkbox_var.set(False)
                return

            if self.search_checkbox_var.get():
                # --- Enable search mode ---
                disabled_buttons = [
                    self.open_file_btn, self.copy_text_btn, self.save_as_btn,
                    self.paste_text_btn, self.clear_text_btn, self.build_btn,
                    self.snippet_btn, self.unittest_btn, self.pytest_btn,
                    self.result_btn, self.test_data_btn, self.store_btn,
                ]
                for btn in disabled_buttons:
                    btn.configure(state=tk.DISABLED)

                self.input_textarea.configure(state=tk.DISABLED)
                self.lookup_btn.grid(row=0, column=2, sticky=tk.W)
                self.close_lookup_btn.grid(row=0, column=3, sticky=tk.W)
                self.template_name_textbox.focus()

                # Save current state
                input_txt = Application.get_textarea(self.input_textarea)
                result_txt = Application.get_textarea(self.result_textarea)
                self.snapshot.update(
                    main_input_textarea=input_txt,
                    main_result_textarea=result_txt
                )

                # Search template if name provided
                template_name = self.template_name_var.get().strip()
                if template_name:
                    template = user_template.search(template_name)
                    if template:
                        self.snapshot.update(
                            template=template,
                            result=template
                        )
                        self.set_textarea(self.input_textarea, template)
                else:
                    self.set_textarea(self.input_textarea, '')

                # Update result area with file content
                self.set_textarea(self.result_textarea, user_template.read())

                # Update title
                title = self.root.title().replace(' - ' + self._base_title, '')
                self.snapshot.update(title=title)
                self.set_title(title='Searching Template')
            else:
                # --- Disable search mode ---
                enabled_buttons = [
                    self.open_file_btn, self.paste_text_btn,
                    self.clear_text_btn,
                    self.build_btn, self.snippet_btn, self.unittest_btn,
                    self.pytest_btn,
                ]
                for btn in enabled_buttons:
                    btn.configure(state=tk.NORMAL)

                if self.snapshot.test_data:
                    self.result_btn.config(state=tk.NORMAL)
                    self.test_data_btn.config(state=tk.NORMAL)

                if self.snapshot.is_built:
                    self.store_btn.configure(state=tk.NORMAL)

                self.input_textarea.configure(state=tk.NORMAL)
                self.lookup_btn.grid_forget()
                self.close_lookup_btn.grid_forget()

                # Restore text areas
                input_txt = Application.get_textarea(self.input_textarea)
                pattern = r'#+\s+# *Template +is +generated '
                if re.match(pattern, input_txt):
                    self.test_data_btn_var.set('Test Data')
                    self.set_textarea(self.result_textarea, input_txt)
                else:
                    self.set_textarea(
                        self.result_textarea,
                        self.snapshot.main_result_textarea,
                    )

                self.set_textarea(
                    self.input_textarea,
                    self.snapshot.main_input_textarea,
                )

                # Re-enable copy/save if content exists
                input_txt = Application.get_textarea(self.input_textarea)
                result_txt = Application.get_textarea(self.result_textarea)

                if input_txt or result_txt:
                    self.copy_text_btn.configure(state=tk.NORMAL)
                    self.save_as_btn.configure(state=tk.NORMAL)

                # Restore title
                title_ = self.snapshot.title
                title = '' if title_ == self._base_title else title_
                self.snapshot.update(title=title)
                self.set_title(title=title) if title else self.set_title()

        def callback_lookup_btn():
            """
            Handle the 'Lookup' button action for user templates.

            This is an inner function defined within Application.build_entry.

            This callback retrieves a template by name from the `UserTemplate`
            store and updates the application state accordingly. If the template
            name is missing, an error message is displayed. If the template is
            found, the snapshot and input text area are updated with its content.
            If not found, the snapshot and input text area are updated with the
            current status message.

            Workflow
            --------
            1. Retrieve the template name from `template_name_var`.
            2. If the name is empty:
               - Show a message box indicating the missing template name.
            3. If the name is provided:
               - Instantiate `UserTemplate`.
               - Search for the template by name.
               - If found:
                 * Update snapshot with template and result.
                 * Update input text area with template content.
               - If not found:
                 * Update snapshot with status.
                 * Update input text area with status message.

            Returns
            -------
            None
                This method performs side effects (UI updates, snapshot changes,
                error reporting) but does not return a value.

            Notes
            -----
            - Template names are stripped of leading/trailing whitespace before
              lookup.
            - The `UserTemplate.status` provides diagnostic codes such as
              'FOUND', 'NOT_FOUND', or error states.
            """
            template_name = self.template_name_var.get().strip()
            if template_name:
                user_template = UserTemplate()
                template = user_template.search(template_name)
                if template:
                    # Template found
                    self.snapshot.update(
                        template=template,
                        result=template
                    )
                    self.set_textarea(self.input_textarea, template)
                else:
                    # Template not found
                    self.snapshot.update(result=user_template.status)
                    self.set_textarea(self.input_textarea, user_template.status)
            else:
                create_msgbox(
                    title="Missing Template Name",
                    error=(
                        "Cannot retrieve template because the template name "
                        "is empty.\nPlease provide a valid template name."
                    )
                )

        def callback_app_backup_refresh_btn():
            """
            Handle the 'Backup Refresh' button action for user templates.

            This is an inner function defined within Application.build_entry.

            This callback rebuilds the template using the current snapshot data
            and updates the input text area accordingly. If the refreshed template
            differs from the existing one, the application title and snapshot are
            updated to reflect the change. Any exceptions encountered during the
            refresh process are reported to the user via a message box.

            Workflow
            --------
            1. Retrieve user data from the snapshot (`switch_app_user_data`).
            2. Get the current template text from the input text area.
            3. Collect template arguments via `get_template_args`.
            4. Build a new template using `TemplateBuilder`.
            5. Update the snapshot and input text area with the new template.
            6. If the refreshed template differs from the current one:
               - Update the snapshot stored title.
               - Update the application window title.
            7. On error, display a message box with the exception details.

            Returns
            -------
            None
                This method performs side effects (UI updates, snapshot changes,
                error reporting) but does not return a value.

            Notes
            -----
            - The refreshed template is stripped of leading/trailing whitespace
              before comparison.
            - Exceptions are caught broadly to ensure user feedback, but more
              granular handling may be added for specific error types.
            """

            user_data = self.snapshot.switch_app_user_data
            try:
                # Retrieve current template text
                curr_template = Application.get_textarea(self.input_textarea).strip()

                # Build new template
                kwargs = self.get_template_args()
                factory = TemplateBuilder(user_data=user_data, **kwargs)

                # Update snapshot and input area
                new_template = factory.template
                self.snapshot.update(switch_app_template=new_template)
                self.set_textarea(self.input_textarea, new_template)

                # Update title if template changed
                if curr_template != new_template.strip():
                    title = "Template Has Been Refreshed"
                    self.snapshot.update(stored_title=title)
                    self.set_title(title=title)
            except Exception as ex:
                create_msgbox(
                    title='TextFSM Generator Error',
                    error=f"{type(ex).__name__}: {ex}"
                )

        def callback_app_backup_save_btn():
            """
            Handle the 'Backup Save' button action for user templates.

            This is an inner function defined within Application.build_entry.

            This callback validates the current template name and content before
            attempting to save it. It prevents saving when the template name or
            format is invalid, and warns the user if a duplicate template name
            already exists. If saving succeeds, the result area and application
            snapshot are updated accordingly.

            Workflow
            --------
            1. Retrieve the current template name from `template_name_var`.
            2. Check the `UserTemplate.status` for validation errors:
               - INVALID-TEMPLATE-FORMAT → abort save.
               - INVALID-TEMPLATE-NAME-FORMAT → abort save.
               - FOUND → show duplicate name warning.
            3. If valid, retrieve user input from the input text area.
            4. Attempt to save the template via `UserTemplate.write`.
            5. On success:
               - Update the result text area with the saved template.
               - Update the snapshot title.
               - Update the application window title.

            Returns
            -------
            None
                This method performs side effects (UI updates, file writes) but
                does not return a value.

            Notes
            -----
            - Duplicate template names trigger a message box with guidance.
            - Saved templates are stripped of leading/trailing whitespace before
              being written.
            """

            user_template = UserTemplate()
            tmpl_name = self.template_name_var.get()
            status = user_template.status

            # Validation checks
            if status in ("INVALID-TEMPLATE-FORMAT", "INVALID-TEMPLATE-NAME-FORMAT"):
                return

            elif status == 'FOUND':
                create_msgbox(
                    title="Duplicate Template Name",
                    info=(
                        f"The template name {repr(tmpl_name)} already exists.\n"
                        "Please choose a different name."
                    )
                )
                return

            # Attempt to save template
            user_data = self.get_textarea(self.input_textarea)
            is_saved = user_template.write(tmpl_name, user_data.strip())

            if is_saved:
                self.set_textarea(self.result_textarea, user_template.read())
                title = f"{tmpl_name} successfully saved"
                self.snapshot.update(stored_title=title)
                self.set_title(title=title)

        # def callback_rf_btn():
        #     create_msgbox(
        #         title='Robotframework feature',
        #         info="Robotframework button is available in Pro or Enterprise Edition."
        #     )

        # customize width for buttons
        btn_width = 6 if self.is_macos else 8
        # open button
        self.open_file_btn = self.Button(
            self.entry_frame, text='Open',
            name='main_open_btn',
            command=self.callback_open_file,
            width=btn_width
        )
        self.open_file_btn.grid(row=0, column=0, padx=(2, 0), pady=(2, 0))

        # Save As button
        self.save_as_btn = self.Button(
            self.entry_frame, text='Save As',
            name='main_save_as_btn',
            state=tk.DISABLED,
            command=callback_save_as_btn,
            width=btn_width
        )
        self.save_as_btn.grid(row=0, column=1, pady=(2, 0))

        # copy button
        self.copy_text_btn = self.Button(
            self.entry_frame, text='Copy',
            name='main_copy_btn',
            state=tk.DISABLED,
            command=callback_copy_text_btn,
            width=btn_width
        )
        self.copy_text_btn.grid(row=0, column=2, pady=(2, 0))

        # paste button
        self.paste_text_btn = ttk.Button(
            self.entry_frame, text='Paste',
            name='main_paste_btn',
            command=callback_paste_text_btn,
            width=btn_width
        )
        self.paste_text_btn.grid(row=0, column=3, pady=(2, 0))

        # clear button
        self.clear_text_btn = self.Button(
            self.entry_frame, text='Clear',
            name='main_clear_btn',
            command=callback_clear_text_btn,
            width=btn_width
        )
        self.clear_text_btn.grid(row=0, column=4, pady=(2, 0))

        # build button
        self.build_btn = self.Button(
            self.entry_frame,
            textvariable=self.build_btn_var,
            name='main_build_btn',
            command=callback_build_btn,
            width=btn_width
        )
        self.build_btn.grid(row=0, column=5, pady=(2, 0))

        # snippet button
        self.snippet_btn = self.Button(
            self.entry_frame, text='Snippet',
            name='main_snippet_btn',
            command=callback_snippet_btn,
            width=btn_width
        )
        self.snippet_btn.grid(row=0, column=6, pady=(2, 0))

        # unittest button
        self.unittest_btn = self.Button(
            self.entry_frame, text='Unittest',
            name='main_unittest_btn',
            command=callback_unittest_btn,
            width=btn_width
        )
        self.unittest_btn.grid(row=0, column=7, pady=(2, 0))

        # pytest button
        self.pytest_btn = self.Button(
            self.entry_frame, text='Pytest',
            name='main_pytest_btn',
            command=callback_pytest_btn,
            width=btn_width
        )
        self.pytest_btn.grid(row=0, column=8, pady=(2, 0))

        # test_data button
        self.test_data_btn = self.Button(
            self.entry_frame,
            name='main_test_data_btn',
            state=tk.DISABLED,
            command=callback_test_data_btn,
            textvariable=self.test_data_btn_var,
            width=btn_width
        )
        self.test_data_btn.grid(row=0, column=9, pady=(2, 0))

        # result button
        self.result_btn = self.Button(
            self.entry_frame, text='Result',
            name='main_result_btn',
            state=tk.DISABLED,
            command=callback_result_btn,
            width=btn_width
        )
        self.result_btn.grid(row=1, column=0, padx=(2, 0), pady=(0, 2))

        # store button
        self.store_btn = self.Button(
            self.entry_frame, text='Store',
            name='main_store_btn',
            state=tk.DISABLED,
            command=callback_store_btn,
            width=btn_width
        )
        self.store_btn.grid(row=1, column=1, pady=(0, 2))

        # frame container for checkbox and textbox
        frame = self.Frame(self.entry_frame)
        frame.grid(row=1, column=2, pady=(0, 2), columnspan=8, sticky=tk.W)

        # customize x padding for search checkbox
        x = 0 if self.is_macos else 6 if self.is_linux else 2
        # search checkbox
        self.search_checkbox = self.CheckBox(
            frame, text='search',
            name='main_search_checkbox',
            variable=self.search_checkbox_var,
            onvalue=True, offvalue=False,
            command=callback_search_checkbox
        )
        self.search_checkbox.grid(row=0, column=0, padx=(0, x), sticky=tk.W)

        # template name textbox
        self.template_name_textbox = self.TextBox(
            frame, width=46,
            name='main_template_name_textbox',
            textvariable=self.template_name_var
        )
        self.template_name_textbox.grid(row=0, column=1, sticky=tk.W)

        self.lookup_btn = self.Button(
            frame, text='Lookup',
            name='main_lookup_btn',
            command=callback_lookup_btn,
            width=btn_width
        )

        self.close_lookup_btn = self.Button(
            frame, text='Close',
            name='main_close_lookup_btn',
            command=self.search_checkbox.invoke,
            width=btn_width
        )

        # Robotframework button
        # rf_btn = self.Button(self.entry_frame, text='RF',
        #                     command=callback_rf_btn, width=4)
        # rf_btn.grid(row=0, column=10)

        # backup app
        self.Label(
            self.backup_frame, text='Author'
        ).grid(row=0, column=0, padx=(4, 1), pady=(4, 0), sticky=tk.W)

        frame = self.Frame(self.backup_frame)
        frame.grid(row=0, column=1, padx=(1, 2), pady=(4, 0), sticky=tk.W)

        # customize width for author textbox
        width = 18 if self.is_macos else 20 if self.is_linux else 28
        self.TextBox(
            frame, width=width,
            textvariable=self.author_var
        ).grid(row=0, column=0, sticky=tk.W)

        # customize x-padding for email label
        x = 6 if self.is_macos else 7 if self.is_linux else 4
        self.Label(
            frame, text='Email'
        ).grid(row=0, column=1, padx=(x, 2), sticky=tk.W)

        # customize width for email textbox
        width = 27 if self.is_macos else 32 if self.is_linux else 43
        self.TextBox(
            frame, width=width,
            textvariable=self.email_var
        ).grid(row=0, column=2, sticky=tk.W)

        # customize x-padding for company label
        x = 5 if self.is_macos else 6 if self.is_linux else 5
        self.Label(
            frame, text='Company'
        ).grid(row=0, column=3, padx=(x, 2), sticky=tk.W)

        # customize width for company textbox
        width = 18 if self.is_macos else 20 if self.is_linux else 28
        self.TextBox(
            frame, width=width,
            textvariable=self.company_var
        ).grid(row=0, column=4, sticky=tk.W)

        # custom pady for description
        pady = 0 if self.is_macos else 1
        self.Label(
            self.backup_frame, text='Description'
        ).grid(row=1, column=0, padx=(4, 1), pady=pady, sticky=tk.W)

        # custom width for description textbox
        width = 78 if self.is_macos else 88 if self.is_linux else 118
        self.TextBox(
            self.backup_frame, width=width,
            textvariable=self.description_var
        ).grid(row=1, column=1, padx=(1, 2), pady=pady, sticky=tk.W)

        self.Label(
            self.backup_frame, text='Name'
        ).grid(row=2, column=0, padx=(4, 1), pady=(0, 2), sticky=tk.W)

        frame = self.Frame(
            self.backup_frame
        )
        frame.grid(row=2, column=1, padx=(1, 2), pady=(0, 2), sticky=tk.W)

        # customize width for template name textbox
        width = 48 if self.is_macos else 50 if self.is_linux else 70
        self.TextBox(
            frame, width=width,
            textvariable=self.template_name_var
        ).pack(side=tk.LEFT)
        self.Button(
            frame, text='Refresh',
            command=callback_app_backup_refresh_btn,
            width=btn_width
        ).pack(side=tk.LEFT)
        self.Button(
            frame, text='Save',
            command=callback_app_backup_save_btn,
            width=btn_width
        ).pack(side=tk.LEFT)
        self.close_backup_btn = self.Button(
            frame, text='Close',
            command=self.shift_to_main_app,
            width=btn_width
        )
        self.close_backup_btn.pack(side=tk.LEFT)

    def build_result(self):
        """
        Construct the result display area for the application.

        This method creates a disabled, scrollable `TextArea` widget inside
        `result_frame`. The widget is intended for displaying output such as
        test results, logs, or generated scripts. Both vertical and horizontal
        scrollbars are attached to support navigation of large or unwrapped
        content.

        Workflow
        --------
        1. Configure the `result_frame` grid to allow expansion:
           - Row 0 and column 0 are weighted for resizing.
        2. Create a disabled `TextArea` widget with fixed dimensions and no wrapping.
        3. Place the `TextArea` in the grid at row 0, column 0, expanding in all
           directions (`nswe`).
        4. Add a vertical scrollbar linked to the `yview` of the text area.
        5. Add a horizontal scrollbar linked to the `xview` of the text area.
        6. Configure the text area to update scrollbar positions during scrolling.

        Returns
        -------
        None
            This method performs side effects (constructing and attaching widgets)
            but does not return a value.

        Notes
        -----
        - The `wrap='none'` option ensures text does not automatically wrap,
          making horizontal scrolling necessary for long lines.
        - The `state=tk.DISABLED` option prevents direct editing of the result
          content by the user.
        """

        # Create result text area
        self.result_frame.rowconfigure(0, weight=1)
        self.result_frame.columnconfigure(0, weight=1)

        # Create result text area
        self.result_textarea = self.TextArea(
            self.result_frame, width=20, height=5, wrap='none',
            state=tk.DISABLED,
            name='main_result_textarea'
        )
        self.result_textarea.grid(row=0, column=0, sticky='nswe')

        # Attach scrollbars
        vscrollbar = ttk.Scrollbar(
            self.result_frame, orient=tk.VERTICAL,
            command=self.result_textarea.yview
        )
        vscrollbar.grid(row=0, column=1, sticky='ns')

        hscrollbar = ttk.Scrollbar(
            self.result_frame, orient=tk.HORIZONTAL,
            command=self.result_textarea.xview
        )
        hscrollbar.grid(row=1, column=0, sticky='ew')

        # Link scrollbars to text area
        self.result_textarea.config(
            yscrollcommand=vscrollbar.set, xscrollcommand=hscrollbar.set
        )

    def run(self):
        """
        Start the TextFSM Generator GUI application.

        This method launches the Tkinter main event loop, which keeps the
        TextFSM Generator graphical user interface responsive. Once invoked,
        the application window remains active until the user closes it.

        Notes
        -----
        - This is a blocking call: execution will pause here until the GUI
          window is terminated.
        - Use this method as the final step after initializing and configuring
          the application.

        Returns
        -------
        None
            This method performs side effects (running the GUI loop) and does
            not return a value.
        """
        self.root.mainloop()


def execute():
    """
    Entry point for launching the TextFSM Generator GUI.

    This function instantiates the `Application` class and starts the
    Tkinter main event loop by invoking its `run` method. It provides
    a convenient way to initialize and display the TextFSM Generator
    graphical user interface without requiring direct interaction with
    the `Application` class.

    Notes
    -----
    - This is a blocking call: execution will pause here until the GUI
      window is closed by the user.
    - Intended to be used as the main entry point when running the
      application as a script.

    Returns
    -------
    None
        This function performs side effects (launching the GUI) and does
        not return a value.
    """
    app = Application()
    app.run()
