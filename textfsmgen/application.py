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
        self.root = None

        # tkinter widgets for main layout
        self.paned_window = None
        self.frames = None
        self.textarea = None
        self.buttons = None

        self.curr_widget = None
        self.prev_widget = None

        # datastore
        self.snapshot = None

        # settings var
        self.settings = None

        # method call
        self.build_main_window()
        menu.create(self)
        self.build_main_layout()
        self.build_input_textarea()
        controls.build_action_buttons(self)
        self.build_output_textarea()

    def _init(self):
        self.frames = DotObject(
            input=None,
            buttons=None,
            output=None
        )

        self.textarea = DotObject(
            input=None,
            output=None,
        )

        self.buttons = DotObject(
            test_data=None,
            open=None,
            clear=None,
            paste=None,
            save=None,
            copy=None,

            build=None,
            result=None,
            settings=None,

            python=None,
            unittest=None,
            pytest=None,
            execute=None
        )

        self.settings = DotObject(
            test_data_btn_name=tk.StringVar(),

            # general arguments for TemplateBuilder
            author=tk.StringVar(),
            email=tk.StringVar(),
            company=tk.StringVar(),
            description=tk.StringVar(),

            # Category translator arguments
            use_category_translator_flag=tk.BooleanVar(),
            category_arg_count=tk.IntVar(),
            category_arg_separator=tk.StringVar(),
            category_arg_starting_from=tk.StringVar(),
            category_arg_ending_at=tk.StringVar(),
            category_arg_replacing_rules=tk.StringVar(),

            # Tabular Translator arguments
            use_tabular_translator_flag=tk.BooleanVar(),
            tabular_arg_has_header_row_flag=tk.BooleanVar(),
            tabular_arg_divider=tk.StringVar(),
            tabular_arg_count=tk.IntVar(),
            tabular_arg_widths=tk.StringVar(),
            tabular_arg_headers=tk.StringVar(),
            tabular_arg_header_rows=tk.StringVar(),
            tabular_arg_custom_header=tk.StringVar(),
            tabular_arg_starting_from=tk.StringVar(),
            tabular_arg_ending_at=tk.StringVar(),
            tabular_arg_replacing_rules=tk.StringVar(),

            # Test execution settings
            always_ask_flag=tk.BooleanVar(),
            delete_file_after_run_flag=tk.BooleanVar(),
            python_interpreter=tk.StringVar(),

            # Output Display Options
            test_data_flag=tk.BooleanVar(),
            template_flag=tk.BooleanVar(),
            tabular_flag=tk.BooleanVar(),
            index_flag=tk.BooleanVar()
        )

        # General arguments
        self.settings.test_data_btn_name.set("Test Data")

        # Category translator arguments
        self.settings.category_arg_count.set(1)
        self.settings.category_arg_separator.set(":")

        # Tabular Translator arguments
        self.settings.tabular_arg_has_header_row_flag.set(True)

        # Test execution settings
        self.settings.delete_file_after_run_flag.set(True)
        self.settings.always_ask_flag.set(True)

        # Output Display Options
        self.settings.tabular_flag.set(True)

        self.snapshot = DotObject(
            user_data="",
            test_data="",
            result="",
            template="",
            is_built=False,
        )

    def category_translator_enabled(self):
        """Return True if the category translator is enabled."""
        return self.settings.use_category_translator_flag.get()

    def tabular_translator_enabled(self):
        """Return True if the tabular translator is enabled."""
        return self.settings.use_tabular_translator_flag.get()

    def reset_category_translator(self):
        """Reset the category‑translator flag to False."""
        self.settings.use_category_translator_flag.set(False)

    def reset_tabular_translator(self):
        """Reset the tabular‑translator flag to False."""
        self.settings.use_tabular_translator_flag.set(False)

    def get_template_builder_args(self):
        """Return keyword arguments for initializing a TemplateBuilder."""
        return dict(
            author=self.settings.author.get(),
            email=self.settings.email.get(),
            company=self.settings.company.get(),
            description=self.settings.description.get()
        )

    def get_category_template_builder_args(self):
        """Return keyword arguments for initializing a CategoryTemplateBuilder."""
        starting_from = self.settings.category_arg_starting_from.get()
        ending_at = self.settings.category_arg_ending_at.get()

        return dict(
            count=abs(self.settings.category_arg_count.get()),
            separator=self.settings.category_arg_separator.get(),
            starting_from=starting_from if starting_from.strip() else None,
            ending_at=ending_at if ending_at.strip() else None,
            replacing_rules=self.settings.category_arg_replacing_rules.get(),
            # ----------
            author=self.settings.author.get(),
            email=self.settings.email.get(),
            company=self.settings.company.get(),
            description=self.settings.description.get()
        )

    def get_tabular_template_builder_args(self):
        """Return keyword arguments for initializing a TabularTemplateBuilder."""

        mapping = {"space": " ", "spaces": "  "}

        divider = self.settings.tabular_arg_divider.get()
        column_divider = mapping.get(divider.lower(), divider)

        column_widths = self.settings.tabular_arg_widths.get().strip()
        headers = self.settings.tabular_arg_headers.get()
        header_rows = self.settings.tabular_arg_header_rows.get()
        custom_header_text = self.settings.tabular_arg_custom_header.get()
        starting_from = self.settings.tabular_arg_starting_from.get()
        ending_at = self.settings.tabular_arg_ending_at.get()

        return dict(
            column_divider=column_divider,
            column_count=abs(self.settings.tabular_arg_count.get()),
            column_widths=column_widths if column_widths.strip() else None,
            headers=headers if headers.strip() else None,
            header_rows=header_rows if headers.strip() else None,
            custom_header_text=custom_header_text if custom_header_text.strip() else None,
            starting_from=starting_from if starting_from.strip() else None,
            ending_at=ending_at if ending_at.strip() else None,
            has_header_row=self.settings.tabular_arg_has_header_row_flag.get(),
            replacing_rules=self.settings.tabular_arg_replacing_rules.get(),
            # ----------
            author=self.settings.author.get(),
            email=self.settings.email.get(),
            company=self.settings.company.get(),
            description=self.settings.description.get()
        )

    def callback_focus(self, event):
        """Handle focus change when a new widget is selected."""

        try:
            widget = getattr(event, "widget", None)
            if widget and widget != self.curr_widget:
                self.prev_widget = self.curr_widget
                self.curr_widget = widget
        except Exception as ex:     # noqa
            print(f"... skip {getattr(event, 'widget', event)}")

    def build_main_window(self):
        self.root = tk.Tk()
        self.root.geometry('1000x750+100+100' if ui.is_macos else '900x600+100+100')
        self.root.minsize(200, 200)
        self.root.option_add('*tearOff', False)

        self.root.title('TextFSM Generator CE')
        ui.set_window_icon(self.root)
        self.root.bind("<Button-1>", lambda e: self.callback_focus(e))

        self._init()

    def build_main_layout(self) -> None:
        """Create the primary layout frames and attach them to the main paned window."""
        # Main vertical paned container

        # Create main paned window
        self.paned_window = ui.PanedWindow(self.root, orient=tk.VERTICAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        # Define frames
        self.frames.input = ui.Frame(
            self.paned_window, width=600, height=300, relief=tk.RIDGE
        )
        self.frames.buttons = ui.Frame(
            self.paned_window, width=600, height=10, relief=tk.RIDGE
        )
        self.frames.output = ui.Frame(
            self.paned_window, width=600, height=350, relief=tk.RIDGE
        )

        # Add frames to paned window with weights
        self.paned_window.add(self.frames.input, weight=3)
        self.paned_window.add(self.frames.buttons)
        self.paned_window.add(self.frames.output, weight=7)

    def build_input_textarea(self):
        """
        Construct the main input text area for the TextFSM generator GUI.
        """
        # Configure grid for resizing
        self.frames.input.rowconfigure(0, weight=1)
        self.frames.input.columnconfigure(0, weight=1)

        # Create main input text area
        self.textarea.input = ui.TextArea(
            self.frames.input, width=20, height=5, wrap='none',
            name='input_textarea',
        )
        self.textarea.input.grid(row=0, column=0, sticky='nswe')

        # Add vertical scrollbar
        vscrollbar = ttk.Scrollbar(
            self.frames.input, orient=tk.VERTICAL,
            command=self.textarea.input.yview
        )
        vscrollbar.grid(row=0, column=1, sticky='ns')

        # Add horizontal scrollbar
        hscrollbar = ttk.Scrollbar(
            self.frames.input, orient=tk.HORIZONTAL,
            command=self.textarea.input.xview
        )
        hscrollbar.grid(row=1, column=0, sticky='ew')

        # Link scrollbars to text area
        self.textarea.input.config(
            yscrollcommand=vscrollbar.set,
            xscrollcommand=hscrollbar.set
        )

    def build_output_textarea(self):
        """
        Construct the result display area for the application.
        """

        # Create result text area
        self.frames.output.rowconfigure(0, weight=1)
        self.frames.output.columnconfigure(0, weight=1)

        # Create result text area
        self.textarea.output = ui.TextArea(
            self.frames.output, width=20, height=5, wrap='none',
            state=tk.DISABLED,
            name='output_textarea'
        )
        self.textarea.output.grid(row=0, column=0, sticky='nswe')

        # Attach scrollbars
        vscrollbar = ttk.Scrollbar(
            self.frames.output, orient=tk.VERTICAL,
            command=self.textarea.output.yview
        )
        vscrollbar.grid(row=0, column=1, sticky='ns')

        hscrollbar = ttk.Scrollbar(
            self.frames.output, orient=tk.HORIZONTAL,
            command=self.textarea.output.xview
        )
        hscrollbar.grid(row=1, column=0, sticky='ew')

        # Link scrollbars to text area
        self.textarea.output.config(
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
