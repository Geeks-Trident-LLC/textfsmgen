"""
textfsmgen.application
======================

Main logic and user interface components for the `textfsmgen` library.
"""

from textfsmgen.libs.common import ensure_tkinter_available
tk = ensure_tkinter_available(app_name="textfsmgen")

from tkinter import ttk

from textfsmgen.libs.generic import DotObject

from textfsmgen import version

from textfsmgen import ui
from textfsmgen.ui import menu
from textfsmgen.ui import controls

__version__ = version


class Application:
    """
    Main GUI application for TextFSM template management.
    """

    def __init__(self):
        # standardize tkinter widget for macOS, Linux, and Window operating system
        self.Frame = ttk.Frame
        self.TextArea = tk.Text
        self.PanedWindow = ttk.PanedWindow

        self.root = tk.Tk()
        self.root.geometry('900x600+100+100')
        self.root.minsize(200, 200)
        self.root.option_add('*tearOff', False)

        self.root.title('TextFSM Generator CE')
        ui.set_window_icon(self.root)

        # tkinter widgets for main layout
        self.paned_window = None
        self.input_frame = None
        self.buttons_frame = None
        self.backup_frame = None
        self.output_frame = None

        self.input_textarea = None
        self.output_textarea = None

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

        # settings var
        self.settings = DotObject(
            author=tk.StringVar(),
            email=tk.StringVar(),
            company=tk.StringVar(),
            description=tk.StringVar(),
            test_data=tk.BooleanVar(),
            template=tk.BooleanVar(),
            tabular=tk.BooleanVar(),
            confirm=tk.BooleanVar(),
        )
        self.settings.tabular.set(True)
        self.settings.confirm.set(True)

        # method call
        menu.create(self)
        self.build_frame()
        self.build_textarea()
        controls.build_action_buttons(self)
        self.build_result()

    def get_template_args(self):
        return dict(
            author=self.settings.author.get(),
            email=self.settings.email.get(),
            company=self.settings.company.get(),
            description=self.settings.description.get()
        )

    def shift_to_backup_app(self):
        """
        Switch the application context from the main app to the backup app.
        """
        # Update snapshot to reflect active app
        self.snapshot.update(curr_app='backup_app')

        # Reconfigure GUI layout
        self.paned_window.remove(self.buttons_frame)
        self.paned_window.insert(1, self.backup_frame)

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

    def build_frame(self):
        """
        Construct the main layout frames for the TextFSM generator GUI.
        """

        # Create main paned window
        self.paned_window = self.PanedWindow(self.root, orient=tk.VERTICAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        # Define frames
        self.input_frame = self.Frame(
            self.paned_window, width=600, height=300, relief=tk.RIDGE
        )
        self.buttons_frame = self.Frame(
            self.paned_window, width=600, height=10, relief=tk.RIDGE
        )
        self.backup_frame = self.Frame(
            self.paned_window, width=600, height=10, relief=tk.RIDGE
        )
        self.output_frame = self.Frame(
            self.paned_window, width=600, height=350, relief=tk.RIDGE
        )

        # Add frames to paned window with weights
        self.paned_window.add(self.input_frame, weight=2)
        self.paned_window.add(self.buttons_frame)
        self.paned_window.add(self.output_frame, weight=7)

    def build_textarea(self):
        """
        Construct the main input text area for the TextFSM generator GUI.
        """
        # Configure grid for resizing
        self.input_frame.rowconfigure(0, weight=1)
        self.input_frame.columnconfigure(0, weight=1)

        # Create main input text area
        self.input_textarea = self.TextArea(
            self.input_frame, width=20, height=5, wrap='none',
            name='main_input_textarea',
        )
        self.input_textarea.grid(row=0, column=0, sticky='nswe')

        # Add vertical scrollbar
        vscrollbar = ttk.Scrollbar(
            self.input_frame, orient=tk.VERTICAL,
            command=self.input_textarea.yview
        )
        vscrollbar.grid(row=0, column=1, sticky='ns')

        # Add horizontal scrollbar
        hscrollbar = ttk.Scrollbar(
            self.input_frame, orient=tk.HORIZONTAL,
            command=self.input_textarea.xview
        )
        hscrollbar.grid(row=1, column=0, sticky='ew')

        # Link scrollbars to text area
        self.input_textarea.config(
            yscrollcommand=vscrollbar.set,
            xscrollcommand=hscrollbar.set
        )

    def build_result(self):
        """
        Construct the result display area for the application.
        """

        # Create result text area
        self.output_frame.rowconfigure(0, weight=1)
        self.output_frame.columnconfigure(0, weight=1)

        # Create result text area
        self.output_textarea = self.TextArea(
            self.output_frame, width=20, height=5, wrap='none',
            state=tk.DISABLED,
            name='main_result_textarea'
        )
        self.output_textarea.grid(row=0, column=0, sticky='nswe')

        # Attach scrollbars
        vscrollbar = ttk.Scrollbar(
            self.output_frame, orient=tk.VERTICAL,
            command=self.output_textarea.yview
        )
        vscrollbar.grid(row=0, column=1, sticky='ns')

        hscrollbar = ttk.Scrollbar(
            self.output_frame, orient=tk.HORIZONTAL,
            command=self.output_textarea.xview
        )
        hscrollbar.grid(row=1, column=0, sticky='ew')

        # Link scrollbars to text area
        self.output_textarea.config(
            yscrollcommand=vscrollbar.set, xscrollcommand=hscrollbar.set
        )

    def run(self):
        """Start the TextFSM Generator GUI application."""
        self.root.mainloop()


def execute():
    """
    Entry point for launching the TextFSM Generator GUI.
    """
    app = Application()
    app.run()
