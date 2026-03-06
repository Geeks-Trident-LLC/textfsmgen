"""
textfsmgen.application
======================

Main logic and user interface components for the `textfsmgen` library.

This module integrates with `tkinter` to provide a graphical interface
for building, customizing, and testing TextFSM templates. It serves as
the entry point for launching the application with GUI support, offering
tools for regex construction, template validation, and interactive
pattern testing.
"""

from textfsmgen.libs.common import ensure_tkinter_available
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

from textfsmgen.libs.utils import get_data_as_tabular
from textfsmgen.libs.generic import DotObject
from textfsmgen.libs import file

from textfsmgen import TemplateBuilder
from textfsmgen.exceptions import TemplateBuilderInvalidFormat
from textfsmgen import config

from textfsmgen import version

from textfsmgen.ui import about
from textfsmgen.ui.common import (
center_window,
show_message_dialog,
make_modal
)


__version__ = version



class UserTemplate:
    """
    Manage user-defined TextFSM templates stored in the application.
    """
    def __init__(self):
        # config.user_template_filename is
        #      /home_dir/.textfsmgen/user_templates.yaml
        self.filename = config.user_template_filename
        self.status = ''
        self.content = ''

    def is_exist(self):
        """
        Check whether the user template file exists.
        """

        node = Path(self.filename)
        return node.exists()

    def create(self, confirmed=True):
        """
        Create the user template file if it does not already exist.
        """
        if self.is_exist():
            return True

        try:
            if confirmed:
                response = show_message_dialog(
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
                        show_message_dialog(
                            title="Directory Error",
                            error="Cannot create file '{str(node)}' because "
                                  "its parent path '{str(parent)}' is a file."
                        )
                        return False
                node.touch()
                self.content = node.read_text()
                if confirmed:
                    show_message_dialog(
                        title="User Template File Created",
                        info=f"{repr(self.filename)}? created successfully."
                    )
                return True
            else:
                return False
        except Exception as ex:
            self.status = f"{type(ex).__name__}: {ex}."
            show_message_dialog(
                title="User Template File Creation Error",
                error=self.status
            )

    def read(self):
        """
        Read and return the content of the user template file.
        """
        if self.is_exist():
            self.content = file.read(self.filename)
            return self.content
        else:
            self.status = f"File '{self.filename}' does not exist."
            show_message_dialog(
                title="Error: User Template File Not Found",
                error=self.status
            )
            return ''

    def search(self, template_name):
        """
        Search for a user-defined template by name.
        """
        self.status = ''
        if self.is_exist():
            if not re.match(r'[a-z0-9]+([+._-][a-z0-9]+)*$', template_name):
                self.status = 'INVALID-TEMPLATE-NAME-FORMAT'
                show_message_dialog(
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
                show_message_dialog(
                    title="Error: Invalid User Template Format",
                    error=f"File '{self.filename}' is not in the correct format."
                )
                return ''
        else:
            title = 'User Template File Not Found'
            error = "{!r} IS NOT existed.".format(self.filename)
            self.status = error
            show_message_dialog(title=title, error=error)
            return ''

    def write(self, template_name, template):
        """
        Write or update a user-defined template in the YAML file.
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
                response = show_message_dialog(
                    title="Error: Duplicate Template Name",
                    question=f"Template name '{template_name}' already "
                             f"exists.\nDo you want to overwrite?"
                )
                if response == 'yes':
                    yaml_obj[template_name] = template
                    for name, tmpl in yaml_obj.items():
                        if tmpl.strip() == template.strip() and name != template_name:
                            show_message_dialog(
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
                        response = show_message_dialog(
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
                show_message_dialog(
                    title="Error: Writing User Template File",
                    error=self.status
                )
                return False
        else:
            return False


class Application:
    """
    Main GUI application for TextFSM template management.
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

        self._base_title = 'TextFSM Generator CE'
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
        """
        result = dict(
            test_script_file=self.filename_var.get(),
            author=self.author_var.get(),
            email=self.email_var.get(),
            company=self.company_var.get(),
            description=self.description_var.get()
        )
        return result

    def set_default_setting(self):
        """
        Reset application configuration variables to their default values.
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
        """
        text = widget.get('1.0', 'end')
        return text.rstrip("\r\n")

    @classmethod
    def clear_textarea(cls, widget):
        """
        Clear all text content from a Tkinter `Text` widget.
        """
        curr_state = widget['state']
        widget.configure(state=tk.NORMAL)
        widget.delete("1.0", "end")
        widget.configure(state=curr_state)

    def set_textarea(self, widget, data, title=''):
        """
        Set text content in a Tkinter `Text` widget and optionally update the window title.
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
        """
        widget = widget or self.root
        base_title = self._base_title
        title = '{} - {}'.format(title, base_title) if title else base_title
        widget.title(title)

    def shift_to_main_app(self):
        """
        Switch the application context from the backup app to the main app.
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
        """

        def mouse_over(event):
            """
            Handle mouse hover event for a label with a hyperlink.
            """

            if 'underline' not in event.widget.font:
                event.widget.configure(
                    font=event.widget.font + ['underline'],
                    cursor='hand2'
                )

        def mouse_out(event):
            """
            Handle mouse leave event for a label with a hyperlink.
            """
            event.widget.config(
                font=event.widget.font,
                cursor='arrow'
            )

        def mouse_press(event):
            """
            Handle mouse click event for a label with a hyperlink.
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
        """
        self.root.quit()

    def callback_open_file(self):
        """
        Handle the "File > Open" menu action.
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
        """
        self.browser.open_new_tab(config.documentation_url)

    def callback_help_view_licenses(self):
        """
        Handle the "Help > View Licenses" menu action.
        """
        self.browser.open_new_tab(config.license_url)

    def callback_help_about(self):
        """
        Handle the "Help > About" menu action.
        """

        about.show_dialog(self.root)

    def callback_preferences_settings(self):
        """
        Handle the "Preferences > Settings" menu action.
        """
        # Create modal "Settings" window
        settings = tk.Toplevel(self.root)
        self.set_title(widget=settings, title='Settings')

        width = 520 if self.is_macos else 474 if self.is_linux else 370
        height = 258 if self.is_macos else 242 if self.is_linux else 234
        center_window(self.root, settings, width, height)

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
        make_modal(settings)

    def callback_preferences_user_template(self):
        """
        Handle the "Preferences > User Template" menu action.
        """
        self.search_checkbox_var.set(False)
        self.search_checkbox.invoke()

    def build_menu(self):
        """
        Construct the main menubar for the TextFSM Generator GUI application.
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

        for menu, config_ in menu_structure:
            if config_:
                menu.add_command(**config_)
            else:
                menu.add_separator()

    def build_frame(self):
        """
        Construct the main layout frames for the TextFSM generator GUI.
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
        """

        def callback_build_btn():
            """
            Handle the 'Build' button action to generate a TextFSM template.
            """

            user_data = Application.get_textarea(self.input_textarea)
            if not user_data:
                show_message_dialog(
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
                show_message_dialog(
                    title="Invalid TextFSM Template Format",
                    error=f"{type(ex).__name__}: {ex}"
                )
            except Exception as ex:
                show_message_dialog(
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
                    response = show_message_dialog(
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
                response = show_message_dialog(
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
                show_message_dialog(
                    title="Clipboard Empty",
                    info="Cannot paste because the clipboard contains no data."
                )

        def callback_snippet_btn():
            """
            Handle the 'Snippet' button action to generate a lightweight Python test script.
            """
            # --- Validate prerequisites ---
            if self.snapshot.test_data is None:
                show_message_dialog(
                    title="Missing Test Data",
                    error=(
                        "Cannot build a Python test script without test data.\n"
                        "Please use the Open or Paste button to load test data."
                    )
                )
                return

            user_data = Application.get_textarea(self.input_textarea)
            if not user_data:
                show_message_dialog(
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
                show_message_dialog(
                    title='TextFSM Generator Error',
                    error=f"{type(ex).__name__}: {ex}"
                )

        def callback_unittest_btn():
            """
            Handle the 'Unittest' button action to generate a Python unittest script.
            """

            # --- Validate prerequisites ---
            if self.snapshot.test_data is None:
                show_message_dialog(
                    title="Missing Test Data",
                    error=(
                        "Cannot build a Python unittest script without test data.\n"
                        "Please use the Open or Paste button to load the required data."
                    )
                )
                return

            user_data = Application.get_textarea(self.input_textarea)
            if not user_data:
                show_message_dialog(
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
                show_message_dialog(
                    title='TextFSM Generator Error',
                    error=f"{type(ex).__name__}: {ex}"
                )

        def callback_pytest_btn():
            """
            Handle the 'Pytest' button action to generate a Python pytest script.
            """

            # --- Validate prerequisites ---
            if self.snapshot.test_data is None:
                show_message_dialog(
                    title="Missing Test Data",
                    error=(
                        "Cannot build a Python pytest script without test data.\n"
                        "Please use the Open or Paste button to load the required data."
                    )
                )
                return

            user_data = Application.get_textarea(self.input_textarea)
            if not user_data:
                show_message_dialog(
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
                show_message_dialog(
                    title='TextFSM Generator Error',
                    error=f"{type(ex).__name__}: {ex}"
                )

        def callback_test_data_btn():
            """
            Handle the 'Test Data' button toggle.
            """

            if self.snapshot.test_data is None:
                show_message_dialog(
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
            """

            # --- Validate prerequisites ---
            if self.snapshot.test_data is None:
                show_message_dialog(
                    title='No Test Data',
                    error=("Can NOT parse text without "
                           "test data.\nPlease use Open or Paste button "
                           "to load test data")
                )
                return

            user_data = Application.get_textarea(self.input_textarea)
            if not user_data:
                show_message_dialog(
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
                    show_message_dialog(
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
            """

            user_template = UserTemplate()

            # Ensure template file exists
            if not user_template.is_exist():
                response = show_message_dialog(
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
            """

            user_template = UserTemplate()
            if not user_template.is_exist():
                show_message_dialog(
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
                show_message_dialog(
                    title="Missing Template Name",
                    error=(
                        "Cannot retrieve template because the template name "
                        "is empty.\nPlease provide a valid template name."
                    )
                )

        def callback_app_backup_refresh_btn():
            """
            Handle the 'Backup Refresh' button action for user templates.
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
                show_message_dialog(
                    title='TextFSM Generator Error',
                    error=f"{type(ex).__name__}: {ex}"
                )

        def callback_app_backup_save_btn():
            """
            Handle the 'Backup Save' button action for user templates.
            """

            user_template = UserTemplate()
            tmpl_name = self.template_name_var.get()
            status = user_template.status

            # Validation checks
            if status in ("INVALID-TEMPLATE-FORMAT", "INVALID-TEMPLATE-NAME-FORMAT"):
                return

            elif status == 'FOUND':
                show_message_dialog(
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
        #     show_message_dialog(
        #         title='Robotframework feature',
        #         info="Robotframework button is in release 1.x and later"
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
        """
        self.root.mainloop()


def execute():
    """
    Entry point for launching the TextFSM Generator GUI.
    """
    app = Application()
    app.run()
