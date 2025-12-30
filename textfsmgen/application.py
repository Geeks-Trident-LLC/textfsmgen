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
import genericlib.file as file

from textfsmgen import TemplateBuilder
from textfsmgen.exceptions import TemplateBuilderInvalidFormat
from textfsmgen.core import save_file
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
            return func(title=title, message=msg, **options)

    return messagebox.showinfo(title=title, message=info, **options)


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
                        title = "Error: Duplicate Template Content"
                        question = (
                            f"Template name '{template_name}' (your template) has the same content as '{name}'.\n"
                            "Do you want to rename?"
                        )
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

        self._base_title = 'Template {}'.format(edition)
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
        self.snapshot.update(title='')
        self.snapshot.update(stored_title='')
        self.snapshot.update(user_data='')
        self.snapshot.update(test_data=None)
        self.snapshot.update(result='')
        self.snapshot.update(template='')
        self.snapshot.update(is_built=False)
        self.snapshot.update(curr_app='main_app')
        self.snapshot.update(switch_app_template='')
        self.snapshot.update(switch_app_user_data='')
        self.snapshot.update(switch_app_result_data='')
        self.snapshot.update(main_input_textarea='')
        self.snapshot.update(main_result_textarea='')

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
        """return arguments of TemplateBuilder class"""
        result = dict(
            filename=self.filename_var.get(),
            author=self.author_var.get(),
            email=self.email_var.get(),
            company=self.company_var.get(),
            description=self.description_var.get()
        )
        return result

    def set_default_setting(self):
        """reset to default setting"""
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
        """Get data from TextArea widget

        Parameters
        ----------
        widget (tk.Text): a tk.Text widget

        Returns
        -------
        str: a text from TextArea widget
        """
        text = widget.get('1.0', 'end')
        last_char = text[-1]
        last_two_chars = text[-2:]
        if last_char == '\r' or last_char == '\n':
            return text[:-1]
        elif last_two_chars == '\r\n':
            return text[:-2]
        else:
            return text

    @classmethod
    def clear_textarea(cls, widget):
        """clear data for TextArea widget

        Parameters
        ----------
        widget (tk.Text): a tk.Text widget
        """
        curr_state = widget['state']
        widget.configure(state=tk.NORMAL)
        widget.delete("1.0", "end")
        widget.configure(state=curr_state)

    def set_textarea(self, widget, data, title=''):
        """set data for TextArea widget

        Parameters
        ----------
        widget (tk.Text): a tk.Text widget
        data (any): a data
        title (str): a title of window
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
        """Switch from backup app to main app"""
        self.snapshot.update(curr_app='main_app')
        user_data = self.snapshot.switch_app_user_data      # noqa
        result_data = self.snapshot.switch_app_result_data  # noqa
        self.snapshot.update(switch_app_user_data='')
        self.snapshot.update(switch_app_result_data='')
        self.set_textarea(self.input_textarea, user_data)
        self.set_textarea(self.result_textarea, result_data)
        self.paned_window.remove(self.backup_frame)
        self.paned_window.insert(1, self.entry_frame)

        stored_title = self.root.title().replace(' - ' + self._base_title, '')
        self.snapshot.update(stored_title=stored_title)
        self.set_title(title=self.snapshot.title)   # noqa

    def shift_to_backup_app(self):
        """Switch from main app to back up app"""
        self.snapshot.update(curr_app='backup_app')
        self.paned_window.remove(self.entry_frame)
        self.paned_window.insert(1, self.backup_frame)

        title = self.root.title().replace(' - ' + self._base_title, '')
        self.snapshot.update(title=title)
        stored_title = self.snapshot.stored_title or 'Storing Template'     # noqa
        self.set_title(title=stored_title)

    def create_custom_label(self, parent, text='', link='',
                            increased_size=0, bold=False, underline=False,
                            italic=False):
        """create custom label

        Parameters
        ----------
        parent (tkinter): a parent of widget.
        text (str): a text of widget.
        link (str): a label hyperlink.
        increased_size (int): increased size for font.
        bold (bool): True will set bold font.
        underline (bool): True will set to underline font.
        italic (bool): True will set to italic font.

        Returns
        -------
        tkinter.Label: a label widget.
        """

        def mouse_over(event):
            if 'underline' not in event.widget.font:
                event.widget.configure(
                    font=event.widget.font + ['underline'],
                    cursor='hand2'
                )

        def mouse_out(event):
            event.widget.config(
                font=event.widget.font,
                cursor='arrow'
            )

        def mouse_press(event):
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
        """Callback for widget selection"""
        try:
            widget = event.widget
            if widget and widget != self.curr_widget:
                self.prev_widget = self.curr_widget
                self.curr_widget = widget
        except Exception as ex:     # noqa
            print('... skip {}'.format(getattr(event, 'widget', event)))

    def callback_file_exit(self):
        """Callback for Menu File > Exit."""
        self.root.quit()

    def callback_open_file(self):
        """Callback for Menu File > Open."""
        filetypes = [
            ('Text Files', '.txt', 'TEXT'),
            ('All Files', '*'),
        ]
        filename = filedialog.askopenfilename(filetypes=filetypes)
        if filename:
            with open(filename) as stream:
                if self.search_checkbox_var.get():
                    self.search_checkbox.invoke()

                if self.snapshot.curr_app == 'backup_app':  # noqa
                    self.close_backup_btn.invoke()

                content = stream.read()
                self.test_data_btn.config(state=tk.NORMAL)
                self.test_data_btn_var.set('Test Data')
                self.set_textarea(self.result_textarea, '')
                self.snapshot.update(test_data=content)
                title = 'Open {} + LOAD Test Data'.format(filename)
                self.set_title(title=title)
                self.set_textarea(self.input_textarea, content)
                self.copy_text_btn.configure(state=tk.NORMAL)
                self.save_as_btn.configure(state=tk.NORMAL)
                self.input_textarea.focus()

    def callback_load_td_file(self):
        """Callback for Menu File > Load Test Data."""
        filetypes = [
            ('Text Files', '.txt', 'TEXT'),
            ('All Files', '*'),
        ]
        filename = filedialog.askopenfilename(filetypes=filetypes)
        if filename:
            with open(filename) as stream:
                if self.search_checkbox_var.get():
                    self.search_checkbox.invoke()

                if self.snapshot.curr_app == 'backup_app':  # noqa
                    self.close_backup_btn.invoke()

                content = stream.read()
                self.test_data_btn.config(state=tk.NORMAL)
                self.test_data_btn_var.set('Test Data')

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

                self.copy_text_btn.configure(state=tk.NORMAL)
                self.save_as_btn.configure(state=tk.NORMAL)
                self.snapshot.update(test_data=content)
                title = 'LOAD Test Data - {}'.format(filename)
                self.snapshot.update(title=title)
                self.set_title(title=title)

    def callback_help_documentation(self):
        """Callback for Menu Help > Getting Started."""
        self.browser.open_new_tab(Data.documentation_url)

    def callback_help_view_licenses(self):
        """Callback for Menu Help > View Licenses."""
        self.browser.open_new_tab(Data.license_url)

    def callback_help_about(self):
        """Callback for Menu Help > About"""

        about = tk.Toplevel(self.root)
        self.set_title(widget=about, title='About')
        width, height = 460, 460
        x, y = get_relative_center_location(self.root, width, height)
        about.geometry('{}x{}+{}+{}'.format(width, height, x, y))
        about.resizable(False, False)

        top_frame = self.Frame(about)
        top_frame.pack(fill=tk.BOTH, expand=True)

        paned_window = self.PanedWindow(top_frame, orient=tk.VERTICAL)
        paned_window.pack(fill=tk.BOTH, expand=True, padx=8, pady=12)

        # company
        frame = self.Frame(paned_window, width=450, height=20)
        paned_window.add(frame, weight=4)

        self.create_custom_label(
            frame, text=Data.main_app_text,
            increased_size=2, bold=True
        ).grid(row=0, column=0, columnspan=2, sticky=tk.W)

        # URL
        cell_frame = self.Frame(frame, width=450, height=5)
        cell_frame.grid(row=1, column=0, sticky=tk.W, columnspan=2)

        url = Data.repo_url
        self.Label(cell_frame, text='URL:').pack(side=tk.LEFT)

        self.create_custom_label(
            cell_frame, text=url, link=url
        ).pack(side=tk.LEFT)

        # dependencies
        self.create_custom_label(
            frame, text='Pypi.com Dependencies:', bold=True
        ).grid(row=2, column=0, sticky=tk.W)

        # regex app package
        self.create_custom_label(
            frame, text=Data.gtregexapp_text,
            link=Data.gtregexapp_link
        ).grid(row=3, column=0, padx=(20, 0), sticky=tk.W)

        # genericlib package
        self.create_custom_label(
            frame, text=Data.gtgenlib_text,
            link=Data.gtgenlib_link
        ).grid(row=4, column=0, padx=(20, 0), sticky=tk.W)

        # TextFSM package
        self.create_custom_label(
            frame, text=Data.textfsm_text,
            link=Data.textfsm_link
        ).grid(row=3, column=1, padx=(20, 0), sticky=tk.W)

        # PyYAML package
        self.create_custom_label(
            frame, text=Data.pyyaml_text,
            link=Data.pyyaml_link
        ).grid(row=4, column=1, padx=(20, 0), pady=(0, 10), sticky=tk.W)

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

        # footer - copyright
        frame = self.Frame(paned_window, width=450, height=20)
        paned_window.add(frame, weight=1)

        self.Label(frame, text=Data.copyright_text).pack(side=tk.LEFT, pady=(10, 10))

        self.create_custom_label(
            frame, text=Data.company, link=Data.company_url
        ).pack(side=tk.LEFT, pady=(10, 10))

        self.Label(frame, text='.  All right reserved.').pack(side=tk.LEFT, pady=(10, 10))

        set_modal_dialog(about)

    def callback_preferences_settings(self):
        """Callback for Menu Preferences > Settings"""

        settings = tk.Toplevel(self.root)
        self.set_title(widget=settings, title='Settings')
        width = 520 if self.is_macos else 474 if self.is_linux else 370
        height = 258 if self.is_macos else 242 if self.is_linux else 234
        x, y = get_relative_center_location(self.root, width, height)
        settings.geometry('{}x{}+{}+{}'.format(width, height, x, y))
        settings.resizable(False, False)

        top_frame = self.Frame(settings)
        top_frame.pack(fill=tk.BOTH, expand=True)

        # Settings - Arguments
        label_frame_args = self.LabelFrame(
            top_frame, height=100, width=380,
            text='Arguments'
        )
        label_frame_args.grid(row=0, column=0, padx=10, pady=(5, 0), sticky=tk.W)

        pady = 0 if self.is_macos else 1

        self.Label(
            label_frame_args, text='Author'
        ).grid(row=0, column=0, columnspan=2, padx=2, pady=pady, sticky=tk.W+tk.N)
        self.TextBox(
            label_frame_args, width=45,
            textvariable=self.author_var
        ).grid(row=0, column=2, columnspan=4, padx=2, pady=pady, sticky=tk.W)

        self.Label(
            label_frame_args, text='Email'
        ).grid(row=1, column=0, columnspan=2, padx=2, pady=pady, sticky=tk.W+tk.N)
        self.TextBox(
            label_frame_args, width=45,
            textvariable=self.email_var
        ).grid(row=1, column=2, columnspan=4, padx=2, pady=pady, sticky=tk.W)

        self.Label(
            label_frame_args, text='Company'
        ).grid(row=2, column=0, columnspan=2, padx=2, pady=pady, sticky=tk.W+tk.N)
        self.TextBox(
            label_frame_args, width=45,
            textvariable=self.company_var
        ).grid(row=2, column=2, columnspan=4, padx=2, pady=pady, sticky=tk.W)

        self.Label(
            label_frame_args, text='Filename'
        ).grid(row=4, column=0, columnspan=2, padx=2, pady=pady, sticky=tk.W+tk.N)
        self.TextBox(
            label_frame_args, width=45,
            textvariable=self.filename_var
        ).grid(row=4, column=2, columnspan=4, padx=2, pady=pady, sticky=tk.W)

        self.Label(
            label_frame_args, text='Description'
        ).grid(row=5, column=0, columnspan=2, padx=2, pady=pady, sticky=tk.W+tk.N)
        self.TextBox(
            label_frame_args, width=45,
            textvariable=self.description_var
        ).grid(row=5, column=2, columnspan=4, padx=2, pady=(pady, 10), sticky=tk.W)

        # Settings - Arguments
        label_frame_app = self.LabelFrame(
            top_frame, height=120, width=380,
            text='App'
        )
        label_frame_app.grid(row=1, column=0, padx=10, pady=1, sticky=tk.W+tk.N)

        self.CheckBox(
            label_frame_app, text='Test Data',
            onvalue=True, offvalue=False,
            variable=self.test_data_checkbox_var
        ).grid(row=0, column=0, padx=2)

        self.CheckBox(
            label_frame_app, text='Template',
            onvalue=True, offvalue=False,
            variable=self.template_checkbox_var
        ).grid(row=0, column=1, padx=20)

        self.CheckBox(
            label_frame_app, text='Tabular',
            onvalue=True, offvalue=False,
            variable=self.tabular_checkbox_var
        ).grid(row=0, column=2, padx=2)

        # OK and Default buttons
        frame = self.Frame(
            top_frame, height=14, width=380
        )
        frame.grid(row=2, column=0, padx=10, pady=(10, 5), sticky=tk.E+tk.S)

        self.Button(
            frame, text='Default',
            command=lambda: self.set_default_setting(),
        ).grid(row=0, column=6, padx=1, pady=1, sticky=tk.E)

        self.Button(
            frame, text='OK',
            command=lambda: settings.destroy(),
        ).grid(row=0, column=7, padx=1, pady=1, sticky=tk.E)

        set_modal_dialog(settings)

    def callback_preferences_user_template(self):
        """Callback for Menu Preferences > User Template"""
        self.search_checkbox_var.set(False)
        self.search_checkbox.invoke()

    def build_menu(self):
        """Build menubar for Regex GUI."""
        menu_bar = tk.Menu(self.root)
        self.root.config(menu=menu_bar)
        file = tk.Menu(menu_bar)
        preferences = tk.Menu(menu_bar)
        help_ = tk.Menu(menu_bar)

        menu_bar.add_cascade(menu=file, label='File')
        menu_bar.add_cascade(menu=preferences, label='Preferences')
        menu_bar.add_cascade(menu=help_, label='Help')

        file.add_command(label='Open', command=lambda: self.callback_open_file())
        file.add_command(label='Load Test Data', command=lambda: self.callback_load_td_file())
        file.add_separator()
        file.add_command(label='Quit', command=lambda: self.callback_file_exit())

        preferences.add_command(
            label='Settings',
            command=lambda: self.callback_preferences_settings()
        )
        preferences.add_separator()
        preferences.add_command(
            label='User Template',
            command=lambda: self.callback_preferences_user_template()
        )

        help_.add_command(label='Documentation',
                          command=lambda: self.callback_help_documentation())
        help_.add_command(label='View Licenses',
                          command=lambda: self.callback_help_view_licenses())
        help_.add_separator()
        help_.add_command(label='About', command=lambda: self.callback_help_about())

    def build_frame(self):
        """Build layout for regex GUI."""
        self.paned_window = self.PanedWindow(self.root, orient=tk.VERTICAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

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
        self.paned_window.add(self.text_frame, weight=2)
        self.paned_window.add(self.entry_frame)
        self.paned_window.add(self.result_frame, weight=7)

    def build_textarea(self):
        """Build input text for regex GUI."""

        self.text_frame.rowconfigure(0, weight=1)
        self.text_frame.columnconfigure(0, weight=1)
        self.input_textarea = self.TextArea(
            self.text_frame, width=20, height=5, wrap='none',
            name='main_input_textarea',
        )
        self.input_textarea.grid(row=0, column=0, sticky='nswe')
        vscrollbar = ttk.Scrollbar(
            self.text_frame, orient=tk.VERTICAL, command=self.input_textarea.yview
        )
        vscrollbar.grid(row=0, column=1, sticky='ns')
        hscrollbar = ttk.Scrollbar(
            self.text_frame, orient=tk.HORIZONTAL, command=self.input_textarea.xview
        )
        hscrollbar.grid(row=1, column=0, sticky='ew')
        self.input_textarea.config(
            yscrollcommand=vscrollbar.set, xscrollcommand=hscrollbar.set
        )

    def build_entry(self):
        """Build input entry for regex GUI."""

        def callback_build_btn():
            user_data = Application.get_textarea(self.input_textarea)
            if not user_data:
                create_msgbox(
                    title='Empty Data',
                    error="Can NOT build regex pattern without data."
                )
                return

            try:
                kwargs = self.get_template_args()
                factory = TemplateBuilder(user_data=user_data, **kwargs)
                self.snapshot.update(user_data=user_data)
                self.snapshot.update(result=factory.template)
                self.snapshot.update(template=factory.template)
                self.snapshot.update(swich_app_template='')
                self.snapshot.update(is_built=True)
                self.test_data_btn_var.set('Test Data')
                self.save_as_btn.config(state=tk.NORMAL)
                self.copy_text_btn.config(state=tk.NORMAL)
                self.set_textarea(self.result_textarea, factory.template)

                title = 'Building Template'
                self.snapshot.update(title=title)
                self.set_title(title=title)
            except TemplateBuilderInvalidFormat as ex:
                error = '{}: {}'.format(type(ex).__name__, ex)
                create_msgbox(title='RegexApp Error', error=error)
            except Exception as ex:
                error = '{}: {}'.format(type(ex).__name__, ex)
                create_msgbox(title='RegexApp Error', error=error)
                kwargs = self.get_template_args()
                factory = TemplateBuilder(user_data=user_data, debug=True, **kwargs)
                fmt = '# Please fix user_data to produce a good template\n{}'
                content = fmt.format(factory.bad_template)
                self.set_textarea(self.result_textarea, content)
                title = 'Bad Generated Template'
                self.snapshot.update(title=title)
                self.set_title(title=title)

            if self.snapshot.template:  # noqa
                self.store_btn.config(state=tk.NORMAL)

            if self.snapshot.is_built:  # noqa
                self.result_btn.config(state=tk.NORMAL)

        def callback_save_as_btn():
            prev_widget_name = str(self.prev_widget)
            is_input_area = prev_widget_name.endswith('.main_input_textarea')
            widget = self.input_textarea if is_input_area else self.result_textarea
            content = Application.get_textarea(widget)

            is_mixed_result = '<<====================>>' in content
            test_type = ''
            is_unittest_or_pytest = False
            extension = '.txt'
            if is_input_area:
                title = 'Saving Input Text'
                filetypes = [('Text Files', '*.txt'), ('All Files', '*')]
            else:
                pattern1 = r'"+ *(?P<text>Python +(?P<test_type>\w+) +script) '
                pattern2 = r'#+\s+# *Template +is +generated '
                match = re.match(pattern1, content, re.I)
                if match:
                    title = 'Saving {}'.format(match.group('text')).title()
                    test_type = match.group('test_type')
                    is_unittest_or_pytest |= 'unittest' == test_type
                    is_unittest_or_pytest |= 'pytest' == test_type
                    filetypes = [('Python Files', '*.py'), ('All Files', '*')]
                    extension = '.py'
                elif re.match(pattern2, content, re.I) and not is_mixed_result:
                    title = 'Saving TextFSM Template'
                    filetypes = [('TextFSM Files', '*.textfsm'), ('All Files', '*')]
                    extension = '.textfsm'
                else:
                    title = 'Saving Output Text'
                    filetypes = [('Text Files', '*.txt'), ('All Files', '*')]

            filename = filedialog.asksaveasfilename(title=title, filetypes=filetypes)
            if filename:
                node = PurePath(filename)
                if not node.suffix:
                    node = node.with_suffix(extension)

                if is_unittest_or_pytest:
                    name = node.name
                    if not name.startswith('test_'):
                        new_name = 'test_{}'.format(name)
                        msg_title = 'Unittest/Pytest Naming Convention'
                        yesnocancel = '\n'.join([
                            ('{} - "{}" file does not begin '
                             'with test_<filename>.'
                             ).format(test_type.title(), name),
                            'Yes: save as "{}" file name.'.format(new_name),
                            'No: save as "{}" file name.'.format(name),
                            'Cancel: do not save.',
                            'Do you want to save?'
                        ])
                        response = create_msgbox(title=msg_title, yesnocancel=yesnocancel)
                        if response is None:
                            return
                        else:
                            if response:
                                node = node.with_name(new_name)
                filename = str(node)
                if not content.strip():
                    fmt = ('The content of {} is empty.\n'
                           'Do you want save the empty file?')
                    question = fmt.format(filename)
                    title = '{} - {}'.format(title, 'Empty')
                    response = create_msgbox(question=question, title=title)
                else:
                    response = 'yes'

                if response == 'yes':
                    save_file(filename, content)

        def callback_clear_text_btn():
            prev_widget_name = str(self.prev_widget)
            is_tmpl_name = prev_widget_name.endswith('.main_template_name_textbox')
            is_input_area = prev_widget_name.endswith('.main_input_textarea')
            if is_tmpl_name:
                if self.prev_widget.selection_present():
                    self.prev_widget.delete(tk.SEL_FIRST, tk.SEL_LAST)
                    title = 'Clearing Selected Text'
                else:
                    self.template_name_var.set('')
                    title = 'Clearing Template Name'

                self.snapshot.update(title=title)
                self.set_title(title=title)
                self.prev_widget.focus()
            else:
                if is_input_area and self.prev_widget.tag_ranges(tk.SEL):
                    self.prev_widget.delete(tk.SEL_FIRST, tk.SEL_LAST)
                    title = 'Clearing Selected Text'
                else:
                    Application.clear_textarea(self.input_textarea)
                    Application.clear_textarea(self.result_textarea)
                    self.save_as_btn.config(state=tk.DISABLED)
                    self.copy_text_btn.config(state=tk.DISABLED)
                    self.test_data_btn.config(state=tk.DISABLED)
                    self.result_btn.config(state=tk.DISABLED)
                    self.store_btn.config(state=tk.DISABLED)
                    self.input_textarea.config(state=tk.NORMAL)

                    self.snapshot.update(user_data='')
                    self.snapshot.update(test_data=None)
                    self.snapshot.update(result='')
                    self.snapshot.update(template='')
                    self.snapshot.update(is_built=False)

                    self.test_data_btn_var.set('Test Data')
                    self.build_btn_var.set('Build')
                    self.template_name_var.set('')
                    self.search_checkbox_var.set(False)
                    # self.root.clipboard_clear()
                    title = 'Clearing Input Text + Test Data'

                self.snapshot.update(title=title)
                self.set_title(title=title)
                self.input_textarea.focus()

        def callback_copy_text_btn():
            prev_widget_name = str(self.prev_widget)
            is_tmpl_name = prev_widget_name.endswith('.main_template_name_textbox')
            is_input_area = prev_widget_name.endswith('.main_input_textarea')
            if is_tmpl_name:
                if self.prev_widget.selection_present():
                    content = self.prev_widget.selection_get()
                    title = 'Copying Selected Text'
                else:
                    content = self.template_name_var.get()
                    title = 'Copied Template Name'
            elif is_input_area:
                if self.prev_widget.tag_ranges(tk.SEL):
                    content = self.prev_widget.selection_get()
                    title = 'Copying Selected Text'
                else:
                    content = Application.get_textarea(self.input_textarea)
                    title = 'Copying Input Text'
            else:
                content = Application.get_textarea(self.result_textarea)
                title = 'Copying Output Text'

            self.set_title(title=title)
            self.root.clipboard_clear()
            self.root.clipboard_append(content)
            self.root.update()

        def callback_paste_text_btn():
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
                    if self.prev_widget.selection_present():
                        self.prev_widget.delete(tk.SEL_FIRST, tk.SEL_LAST)
                    index = self.prev_widget.index(tk.INSERT)
                    self.prev_widget.insert(tk.INSERT, data)
                    self.prev_widget.selection_range(index, index + len(data))
                    self.prev_widget.focus()
                    title = 'PASTE On Template Name'
                elif is_input_area and is_not_empty:
                    if self.prev_widget.tag_ranges(tk.SEL):
                        self.prev_widget.delete(tk.SEL_FIRST, tk.SEL_LAST)
                    index = self.prev_widget.index(tk.INSERT)
                    self.prev_widget.insert(tk.INSERT, data)
                    self.prev_widget.tag_add(
                        tk.SEL, index, '{}+{}c'.format(index, len(data))
                    )
                    self.prev_widget.focus()
                    title = 'PASTE On Input Area'
                else:
                    self.clear_text_btn.invoke()
                    self.test_data_btn.config(state=tk.NORMAL)
                    self.test_data_btn_var.set('Test Data')
                    self.set_textarea(self.result_textarea, '')
                    self.snapshot.update(test_data=data)
                    self.snapshot.update(result='')

                    title = 'PASTE + LOAD Test Data'
                    self.set_textarea(self.input_textarea, data)
                    self.input_textarea.focus()

                self.copy_text_btn.configure(state=tk.NORMAL)
                self.save_as_btn.configure(state=tk.NORMAL)

                self.snapshot.update(title=title)
                self.set_title(title=title)

            except Exception as ex:  # noqa
                create_msgbox(
                    title='Empty Clipboard',
                    info='CAN NOT paste because there is no data in pasteboard.'
                )

        def callback_snippet_btn():
            if self.snapshot.test_data is None:  # noqa
                create_msgbox(
                    title='No Test Data',
                    error=("Can NOT build Python test script without "
                           "test data.\nPlease use Open or Paste button "
                           "to load test data")
                )
                return

            user_data = Application.get_textarea(self.input_textarea)
            if not user_data:
                create_msgbox(
                    title='Empty Data',
                    error="Can NOT build Python test script without data."
                )
                return

            try:
                kwargs = self.get_template_args()
                factory = TemplateBuilder(
                    user_data=user_data,
                    test_data=self.snapshot.test_data,  # noqa
                    **kwargs
                )
                script = factory.create_python_test()
                title = 'Building Python Snippet Script'
                self.snapshot.update(title=title)
                self.set_title(title=title)
                self.set_textarea(self.result_textarea, script)
                self.test_data_btn_var.set('Test Data')
                self.snapshot.update(result=script)
                self.save_as_btn.config(state=tk.NORMAL)
                self.copy_text_btn.config(state=tk.NORMAL)
            except Exception as ex:
                error = '{}: {}'.format(type(ex).__name__, ex)
                create_msgbox(title='RegexApp Error', error=error)

        def callback_unittest_btn():
            if self.snapshot.test_data is None:  # noqa
                create_msgbox(
                    title='No Test Data',
                    error=("Can NOT build Python Unittest script without "
                           "test data.\nPlease use Open or Paste button "
                           "to load test data")
                )
                return

            user_data = Application.get_textarea(self.input_textarea)
            if not user_data:
                create_msgbox(
                    title='Empty Data',
                    error="Can NOT build Python Unittest script without data."
                )
                return

            try:
                kwargs = self.get_template_args()
                factory = TemplateBuilder(
                    user_data=user_data,
                    test_data=self.snapshot.test_data,  # noqa
                    **kwargs
                )
                script = factory.create_unittest()
                title = 'Building Python Unittest Script'
                self.snapshot.update(title=title)
                self.set_title(title=title)
                self.set_textarea(self.result_textarea, script)
                self.test_data_btn_var.set('Test Data')
                self.snapshot.update(result=script)
                self.save_as_btn.config(state=tk.NORMAL)
                self.copy_text_btn.config(state=tk.NORMAL)
            except Exception as ex:
                error = '{}: {}'.format(type(ex).__name__, ex)
                create_msgbox(title='RegexApp Error', error=error)

        def callback_pytest_btn():
            if self.snapshot.test_data is None:  # noqa
                create_msgbox(
                    title='No Test Data',
                    error=("Can NOT build Python Pytest script without "
                           "test data.\nPlease use Open or Paste button "
                           "to load test data")
                )
                return

            user_data = Application.get_textarea(self.input_textarea)
            if not user_data:
                create_msgbox(
                    title='Empty Data',
                    error="Can NOT build Python Pytest script without data."
                )
                return

            try:
                kwargs = self.get_template_args()
                factory = TemplateBuilder(
                    user_data=user_data,
                    test_data=self.snapshot.test_data,  # noqa
                    **kwargs
                )
                script = factory.create_pytest()
                title = 'Building Python Pytest Script'
                self.snapshot.update(title=title)
                self.set_title(title=title)
                self.set_textarea(self.result_textarea, script)
                self.test_data_btn_var.set('Test Data')
                self.snapshot.update(result=script)
                self.save_as_btn.config(state=tk.NORMAL)
                self.copy_text_btn.config(state=tk.NORMAL)
            except Exception as ex:
                error = '{}: {}'.format(type(ex).__name__, ex)
                create_msgbox(title='RegexApp Error', error=error)

        def callback_test_data_btn():
            if self.snapshot.test_data is None:  # noqa
                create_msgbox(
                    title='No Test Data',
                    error="Please use Open or Paste button to load test data"
                )
                return

            name = self.test_data_btn_var.get()
            if name == 'Test Data':
                self.test_data_btn_var.set('Hide')
                title = self.root.title().replace(' - ' + self._base_title, '')
                self.snapshot.update(title=title)
                self.set_title(title='Showing Test Data')
                self.set_textarea(
                    self.result_textarea,
                    self.snapshot.test_data  # noqa
                )
            else:
                self.test_data_btn_var.set('Test Data')
                self.set_title(title=self.snapshot.title)   # noqa
                self.set_textarea(
                    self.result_textarea,
                    self.snapshot.result  # noqa
                )

        def callback_result_btn():
            if self.snapshot.test_data is None:  # noqa
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

            try:
                kwargs = self.get_template_args()
                factory = TemplateBuilder(user_data=user_data, **kwargs)
                self.snapshot.update(user_data=user_data)
                self.snapshot.update(template=factory.template)
                self.snapshot.update(is_built=True)
                template = factory.template
            except Exception as ex:
                template = self.snapshot.template.strip()   # noqa
                if not template:
                    error = '{}: {}'.format(type(ex).__name__, ex)
                    create_msgbox(title='RegexApp Error', error=error)
                    return

            stream = StringIO(template)
            parser = TextFSM(stream)
            rows = parser.ParseTextToDicts(self.snapshot.test_data)  # noqa

            result = ''
            test_data = self.snapshot.test_data  # noqa
            fmt = '\n\n<<{}>>\n\n{{}}'.format('=' * 20)

            lst = []

            if self.template_checkbox_var.get() and template:
                lst.append('Template')
                result += fmt.format(template) if result else template

            if self.test_data_checkbox_var.get() and test_data:  # noqa
                lst.append('Test Data')
                result += fmt.format(test_data) if result else test_data

            lst.append('Test Result')
            if rows and self.tabular_checkbox_var.get():
                tabular_data = get_data_as_tabular(rows)
                result += fmt.format(tabular_data) if result else tabular_data
            else:
                pretty_data = pformat(rows)
                result += fmt.format(pretty_data) if result else pretty_data

            self.test_data_btn_var.set('Test Data')
            self.snapshot.update(result=result)

            title = 'Showing {}'.format(' + '.join(lst))
            self.snapshot.update(title=title)
            self.set_title(title=title)
            self.set_textarea(self.result_textarea, result)

        def callback_store_btn():
            user_template = UserTemplate()
            if not user_template.is_exist():
                title = 'User Template File Not Found'
                fmt = ('The feature is only available when {!r} is existed.\n'
                       'Do you want to create this file?')
                question = fmt.format(user_template.filename)
                response = create_msgbox(title=title, question=question)
                if response == 'no':
                    return
                else:
                    user_template.create(confirmed=False)

            if user_template.is_exist():
                user_data = self.get_textarea(self.input_textarea)
                result_data = self.get_textarea(self.result_textarea)
                self.snapshot.update(switch_app_user_data=user_data)
                self.snapshot.update(switch_app_result_data=result_data)

                data = self.snapshot.switch_app_template or self.snapshot.template  # noqa
                self.set_textarea(self.input_textarea, data)
                self.set_textarea(self.result_textarea, user_template.read())
                self.shift_to_backup_app()

        def callback_search_checkbox():
            user_template = UserTemplate()
            if not user_template.is_exist():
                title = 'User Template File Not Found'
                fmt = 'The feature is only available when {!r} is existed.'
                info = fmt.format(user_template.filename)
                create_msgbox(title=title, info=info)
                self.search_checkbox_var.set(False)
                return

            if self.search_checkbox_var.get():
                self.open_file_btn.configure(state=tk.DISABLED)
                self.copy_text_btn.configure(state=tk.DISABLED)
                self.save_as_btn.configure(state=tk.DISABLED)
                self.paste_text_btn.configure(state=tk.DISABLED)
                self.clear_text_btn.configure(state=tk.DISABLED)
                self.build_btn.configure(state=tk.DISABLED)
                self.snippet_btn.configure(state=tk.DISABLED)
                self.unittest_btn.configure(state=tk.DISABLED)
                self.pytest_btn.configure(state=tk.DISABLED)
                self.result_btn.config(state=tk.DISABLED)
                self.test_data_btn.config(state=tk.DISABLED)
                self.store_btn.configure(state=tk.DISABLED)

                self.input_textarea.configure(state=tk.DISABLED)
                self.lookup_btn.grid(row=0, column=2, sticky=tk.W)
                self.close_lookup_btn.grid(row=0, column=3, sticky=tk.W)
                self.template_name_textbox.focus()

                input_txt = Application.get_textarea(self.input_textarea)
                result_txt = Application.get_textarea(self.result_textarea)
                self.snapshot.update(main_input_textarea=input_txt)
                self.snapshot.update(main_result_textarea=result_txt)

                template_name = self.template_name_var.get().strip()
                if template_name:
                    template = user_template.search(template_name)
                    if template:
                        self.snapshot.update(template=template)
                        self.snapshot.update(result=template)
                        self.set_textarea(self.input_textarea, template)
                else:
                    self.set_textarea(self.input_textarea, '')

                self.set_textarea(self.result_textarea, user_template.read())

                title = self.root.title().replace(' - ' + self._base_title, '')
                self.snapshot.update(title=title)
                self.set_title(title='Searching Template')
            else:
                self.open_file_btn.configure(state=tk.NORMAL)
                # self.copy_text_btn.configure(state=tk.NORMAL)
                # self.save_as_btn.configure(state=tk.NORMAL)
                self.paste_text_btn.configure(state=tk.NORMAL)
                self.clear_text_btn.configure(state=tk.NORMAL)
                self.build_btn.configure(state=tk.NORMAL)
                self.snippet_btn.configure(state=tk.NORMAL)
                self.unittest_btn.configure(state=tk.NORMAL)
                self.pytest_btn.configure(state=tk.NORMAL)

                if self.snapshot.test_data:     # noqa
                    self.result_btn.config(state=tk.NORMAL)
                    self.test_data_btn.config(state=tk.NORMAL)

                if self.snapshot.is_built:      # noqa
                    self.store_btn.configure(state=tk.NORMAL)

                self.input_textarea.configure(state=tk.NORMAL)
                self.lookup_btn.grid_forget()
                self.close_lookup_btn.grid_forget()

                input_txt = Application.get_textarea(self.input_textarea)
                pattern = r'#+\s+# *Template +is +generated '
                if re.match(pattern, input_txt):
                    self.test_data_btn_var.set('Test Data')
                    self.set_textarea(self.result_textarea, input_txt)
                else:
                    self.set_textarea(
                        self.result_textarea,
                        self.snapshot.main_result_textarea,     # noqa
                    )

                self.set_textarea(
                    self.input_textarea,
                    self.snapshot.main_input_textarea,  # noqa
                )

                input_txt = Application.get_textarea(self.input_textarea)
                result_txt = Application.get_textarea(self.result_textarea)

                if input_txt or result_txt:
                    self.copy_text_btn.configure(state=tk.NORMAL)
                    self.save_as_btn.configure(state=tk.NORMAL)

                title_ = self.snapshot.title    # noqa
                title = '' if title_ == self._base_title else title_
                self.snapshot.update(title=title)
                self.set_title(title=title) if title else self.set_title()

        def callback_lookup_btn():
            template_name = self.template_name_var.get().strip()
            if template_name:
                user_template = UserTemplate()
                template = user_template.search(template_name)
                if template:
                    self.snapshot.update(template=template)
                    self.snapshot.update(result=template)
                    self.set_textarea(self.input_textarea, template)
                else:
                    self.snapshot.update(result=user_template.status)
                    self.set_textarea(self.input_textarea, user_template.status)
            else:
                title = 'Empty Template Name'
                error = 'CANT retrieve template with empty template name.'
                create_msgbox(title=title, error=error)

        def callback_app_backup_refresh_btn():
            user_data = self.snapshot.switch_app_user_data      # noqa
            try:
                curr_template = Application.get_textarea(self.input_textarea).strip()
                kwargs = self.get_template_args()
                factory = TemplateBuilder(user_data=user_data, **kwargs)
                self.snapshot.update(switch_app_template=factory.template)
                self.set_textarea(self.input_textarea, factory.template)
                if curr_template != factory.template.strip():
                    title = 'Template Is Refreshed'
                    self.snapshot.update(stored_title=title)
                    self.set_title(title=title)
            except Exception as ex:
                error = '{}: {}'.format(type(ex).__name__, ex)
                create_msgbox(title='RegexApp Error', error=error)

        def callback_app_backup_save_btn():
            user_template = UserTemplate()
            tmpl_name = self.template_name_var.get()
            status = user_template.status
            is_invalid_format = status == 'INVALID-TEMPLATE-FORMAT'
            is_invalid_name = status == 'INVALID-TEMPLATE-NAME-FORMAT'

            if is_invalid_name or is_invalid_format:
                return
            elif status == 'FOUND':
                title = 'Duplicate Template Name'
                fmt = ('{!r} template name is already existed.  '
                       'Please use different name.')
                info = fmt.format(tmpl_name)
                create_msgbox(title=title, info=info)
                return

            user_data = self.get_textarea(self.input_textarea)
            is_saved = user_template.write(tmpl_name, user_data.strip())

            if is_saved:
                self.set_textarea(self.result_textarea, user_template.read())
                title = '{} Is Saved'.format(tmpl_name)
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
        """Build result text"""
        self.result_frame.rowconfigure(0, weight=1)
        self.result_frame.columnconfigure(0, weight=1)
        self.result_textarea = self.TextArea(
            self.result_frame, width=20, height=5, wrap='none',
            state=tk.DISABLED,
            name='main_result_textarea'
        )
        self.result_textarea.grid(row=0, column=0, sticky='nswe')
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
        self.result_textarea.config(
            yscrollcommand=vscrollbar.set, xscrollcommand=hscrollbar.set
        )

    def run(self):
        """Launch template GUI."""
        self.root.mainloop()


def execute():
    """Launch template GUI."""
    app = Application()
    app.run()
