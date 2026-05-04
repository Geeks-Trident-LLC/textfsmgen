"""
textfsmgen.application
======================

Main logic and user interface components for the `textfsmgen` library.
"""

from textfsmgen.libs.generic import DotObject
from textfsmgen import version
from textfsmgen.ui import common, controls, menu
from textfsmgen import ui

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

        # settings variable
        self.settings = None

        # tools variables
        self.tools = None

        # method call
        self.build_main_window()
        menu.create(self)
        self.build_main_layout()
        self.build_input_textarea()
        controls.build_action_buttons(self)
        self.build_output_textarea()

    def init_app_variables(self):
        self.frames = DotObject(
            # frame widget
            input=None,
            controls=None,
            output=None,
        )

        self.textarea = DotObject(
            # textarea widgets
            input=None,
            output=None,
        )

        self.buttons = DotObject(
            # button widgets
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
            execute=None,
        )

        self.settings = DotObject(
            test_data_btn_name=ui.tk.StringVar(value="Test Data"),
            # general arguments for TemplateBuilder
            author=ui.tk.StringVar(),
            email=ui.tk.StringVar(),
            company=ui.tk.StringVar(),
            description=ui.tk.StringVar(),
            # Category translator arguments
            use_category_translator_flag=ui.tk.BooleanVar(),
            category_arg_count=ui.tk.IntVar(value=1),
            category_arg_separator=ui.tk.StringVar(value=":"),
            category_arg_starting_from=ui.tk.StringVar(),
            category_arg_ending_at=ui.tk.StringVar(),
            category_arg_replacing_rules=ui.tk.StringVar(),
            # Tabular Translator arguments
            use_tabular_translator_flag=ui.tk.BooleanVar(),
            tabular_arg_has_header_row_flag=ui.tk.BooleanVar(value=True),
            tabular_arg_divider=ui.tk.StringVar(),
            tabular_arg_count=ui.tk.IntVar(),
            tabular_arg_widths=ui.tk.StringVar(),
            tabular_arg_headers=ui.tk.StringVar(),
            tabular_arg_header_rows=ui.tk.StringVar(),
            tabular_arg_custom_header=ui.tk.StringVar(),
            tabular_arg_starting_from=ui.tk.StringVar(),
            tabular_arg_ending_at=ui.tk.StringVar(),
            tabular_arg_replacing_rules=ui.tk.StringVar(),
            # Test execution settings
            always_ask_flag=ui.tk.BooleanVar(value=True),
            delete_file_after_run_flag=ui.tk.BooleanVar(value=True),
            python_interpreter=ui.tk.StringVar(),
            # Output Display Options
            test_data_flag=ui.tk.BooleanVar(),
            template_flag=ui.tk.BooleanVar(),
            tabular_flag=ui.tk.BooleanVar(value=True),
            index_flag=ui.tk.BooleanVar(),
        )

        self.snapshot = DotObject(
            user_data="",
            test_data="",
            result="",
            template="",
            is_built=False,
        )

        self.tools = DotObject(
            suggester=DotObject(
                # flag or variable
                variable_flag=ui.tk.BooleanVar(value=True),
                group_flag=ui.tk.BooleanVar(),
                generic_flag=ui.tk.BooleanVar(value=True),
                notation_flag=ui.tk.BooleanVar(),
                split_arg=ui.tk.StringVar(value="/"),
                # widget
                in_textarea=None,
                out_textarea=None,
                code_textarea=None,
                result_textarea=None,
            ),
            builder=DotObject(
                # widget
                semantic_group=None,
                outcomes_group=None,
                pattern_area=None,
                explain_area=None,
                # widget-variable
                shared_semantic_list=ui.tk.StringVar(),
                exact_quantity=ui.tk.StringVar(),
                range_min_quantity=ui.tk.StringVar(),
                range_max_quantity=ui.tk.StringVar(),
                variant_flag=ui.tk.StringVar(),
                allowed_empty_flag=ui.tk.BooleanVar(),
                var_name=ui.tk.StringVar(),
                outcomes_value=ui.tk.StringVar(),
                # data
                shared_data_list=[
                    ui.tk.StringVar(),
                    ui.tk.StringVar(),
                    ui.tk.StringVar(),
                    ui.tk.StringVar(),
                    ui.tk.StringVar(),
                    ui.tk.StringVar(),
                    ui.tk.StringVar(),
                    ui.tk.StringVar(),
                ],
                snippet_and_samples=None,
            ),
            tester=DotObject(
                # widget
                dialog=None,
                template_area=None,
                test_data_area=None,
                result_area=None,
                # shared variables
                checkbox_state_var=ui.tk.BooleanVar(),
                output_flag=ui.tk.StringVar(),
                # data
                template_text=ui.tk.StringVar(),
                test_data_text=ui.tk.StringVar(),
                result_text=ui.tk.StringVar(),
            ),
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
            description=self.settings.description.get(),
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
            description=self.settings.description.get(),
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
            custom_header_text=custom_header_text
            if custom_header_text.strip()
            else None,
            starting_from=starting_from if starting_from.strip() else None,
            ending_at=ending_at if ending_at.strip() else None,
            has_header_row=self.settings.tabular_arg_has_header_row_flag.get(),
            replacing_rules=self.settings.tabular_arg_replacing_rules.get(),
            # ----------
            author=self.settings.author.get(),
            email=self.settings.email.get(),
            company=self.settings.company.get(),
            description=self.settings.description.get(),
        )

    def callback_focus(self, event):
        """Handle focus change when a new widget is selected."""

        try:
            widget = getattr(event, "widget", None)
            if widget and widget != self.curr_widget:
                self.prev_widget = self.curr_widget
                self.curr_widget = widget
        except Exception as ex:  # noqa
            print(f"... skip {getattr(event, 'widget', event)}")

    def build_main_window(self):
        self.root = ui.tk.Tk()
        width, height = (
            (1200, 750) if ui.is_macos else (1100, 650) if ui.is_linux else (900, 600)
        )
        # self.root.geometry('1000x750+100+100' if ui.is_macos else '900x600+100+100')
        self.root.geometry(f"{width}x{height}+100+100")
        self.root.minsize(200, 200)
        self.root.option_add("*tearOff", False)

        self.root.title("TextFSM Generator CE")
        common.set_window_icon(self.root)
        self.root.bind("<Button-1>", lambda e: self.callback_focus(e))

        self.init_app_variables()

    def build_main_layout(self) -> None:
        """Create the primary layout frames and attach them to the main paned window."""
        # Main vertical paned container

        # Create main paned window
        self.paned_window = ui.PanedWindow(self.root, orient="vertical")
        self.paned_window.pack(fill="both", expand=True, padx=2, pady=2)

        # Define frames
        self.frames.input = ui.Frame(
            self.paned_window, width=600, height=300, relief="ridge"
        )
        self.frames.controls = ui.Frame(
            self.paned_window,
            width=600,
            relief="ridge",
            height=70 if ui.is_macos else 74 if ui.is_linux else 62,
        )
        self.frames.controls.pack_propagate(False)  # keep the height

        self.frames.output = ui.Frame(
            self.paned_window, width=600, height=350, relief="ridge"
        )

        # Add frames to paned window with weights
        self.paned_window.add(self.frames.input, weight=3)
        self.paned_window.add(self.frames.controls)
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
            self.frames.input,
            width=20,
            height=5,
            wrap="none",
            name="input_textarea",
        )
        self.textarea.input.grid(row=0, column=0, sticky="nswe")  # noqa

        # Add vertical scrollbar
        vscrollbar = ui.Scrollbar(
            self.frames.input, orient="vertical", command=self.textarea.input.yview
        )
        vscrollbar.grid(row=0, column=1, sticky="ns")

        # Add horizontal scrollbar
        hscrollbar = ui.Scrollbar(
            self.frames.input, orient="horizontal", command=self.textarea.input.xview
        )
        hscrollbar.grid(row=1, column=0, sticky="ew")

        # Link scrollbars to text area
        self.textarea.input.config(
            yscrollcommand=vscrollbar.set, xscrollcommand=hscrollbar.set
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
            self.frames.output,
            width=20,
            height=5,
            wrap="none",
            state="disabled",
            name="output_textarea",
            bg=ui.readonly_text_bg_color,
        )
        self.textarea.output.grid(row=0, column=0, sticky="nswe")  # noqa

        # Attach scrollbars
        vscrollbar = ui.Scrollbar(
            self.frames.output, orient="vertical", command=self.textarea.output.yview
        )
        vscrollbar.grid(row=0, column=1, sticky="ns")

        hscrollbar = ui.Scrollbar(
            self.frames.output, orient="horizontal", command=self.textarea.output.xview
        )
        hscrollbar.grid(row=1, column=0, sticky="ew")

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
