"""
textfsmgen.ui.callback
======================

Callback functions for UI actions in TextFSMGen.
"""

import re
from io import StringIO

from textfsm import TextFSM
from pprint import pformat

from textfsmgen.core import testing
from textfsmgen import ui

from textfsmgen import TemplateBuilder
from textfsmgen import CategoryTemplateBuilder
from textfsmgen import TabularTemplateBuilder

from textfsmgen.exceptions import TemplateBuilderInvalidFormat
from textfsmgen.libs import file
from textfsmgen.libs.utils import get_data_as_tabular
from textfsmgen.ui.common import (
    extract_text,
    show_message_dialog,
    set_text,
    clear_text
)

from tkinter import filedialog


def build(app):
    """Handle the 'Build' button action to generate a TextFSM template."""

    activate_user_data_mode(app)
    user_data = extract_text(app.textarea.input)
    if not user_data:
        show_message_dialog(
            title="Missing Input Data",
            error="Cannot build a TextFSM template because "
                  "no input data was provided."
        )
        return

    app.snapshot.update(user_data=user_data)

    try:
        if app.category_translator_enabled():   # noqa
            cls = CategoryTemplateBuilder
            kwargs = app.get_category_template_builder_args()
        elif app.tabular_translator_enabled():
            cls = TabularTemplateBuilder
            kwargs = app.get_tabular_template_builder_args()
        else:
            cls = TemplateBuilder
            kwargs = app.get_template_builder_args()

        builder = cls(user_data=user_data, **kwargs)

        # Update snapshot with generated template
        app.snapshot.update(
            result=builder.template,
            template=builder.template,
            is_built=bool(builder)
        )

        app.settings.test_data_btn_name.set('Test Data')

        if app.category_translator_enabled() or app.tabular_translator_enabled():
            app.reset_category_translator()
            app.reset_tabular_translator()
            if isinstance(builder, (TabularTemplateBuilder, CategoryTemplateBuilder)):
                app.snapshot.update(user_data=builder.snippet)
                set_text(app.textarea.input, builder.snippet)

        # Enable buttons and update UI
        enable_buttons(app, save=True, copy=True, result=True)  # noqa
        if app.snapshot.test_data:
            enable_buttons(
                app, test_data=True, python=True,
                unittest=True, pytest=True, execute=True
            )
        set_text(app.textarea.output, app.snapshot.template)
        app.textarea.output.focus()

    except TemplateBuilderInvalidFormat as ex:
        show_message_dialog(
            title="Invalid TextFSM Template Format",
            error=f"Your snippet needs correction to produce a valid template.\n\n"
                  f"{type(ex).__name__}: {ex}"
        )
        return
    except Exception as ex:
        if not validate_count_fields(app):
            return

        show_message_dialog(
            title="Template Generation Error",
            error=f"Your snippet needs correction to produce a valid template.\n\n"
                  f"{type(ex).__name__}: {ex}"
        )
        return


def show_test_data(app):
    """Handle the 'Test Data' button toggle."""     # noqa

    btn_name = app.settings.test_data_btn_name.get()
    if btn_name == 'Hide':
        # Show user snippet
        app.settings.test_data_btn_name.set('Test Data')
        app.snapshot.test_data = extract_text(app.textarea.input)
        set_text(app.textarea.input, app.snapshot.user_data)
    else:
        # Show test data
        app.settings.test_data_btn_name.set('Hide')
        app.snapshot.user_data = extract_text(app.textarea.input)
        set_text(app.textarea.input, app.snapshot.test_data)


def open_file(app):
    """Handle the "File > Open" menu action."""

    filetypes = (('Text Files', '.txt'), ('All Files', '*'))
    filename = filedialog.askopenfilename(filetypes=filetypes)
    if filename:    # noqa
        # Read file content
        content = file.read(filename)

        activate_user_data_mode(app)

        # Reset and update widgets
        set_text(app.textarea.output, '')
        app.snapshot.update(user_data=content)
        app.snapshot.update(test_data=content)

        # Update title and input area
        set_text(app.textarea.input, content)

        # Enable actions
        enable_buttons(app, test_data=True, copy=True, save=True)

        # Disable actions
        disable_buttons(app, python=True, unittest=True, pytest=True, execute=True)

        # set focus
        app.textarea.input.focus()


def load_test_data_file(app):
    """Handle the "File > Load Test Data" menu action."""

    filetypes = (('Text Files', '.txt'), ('All Files', '*'))
    filename = filedialog.askopenfilename(filetypes=filetypes)
    if not filename:    # noqa
        return

    content = file.read(filename)
    app.snapshot.update(test_data=content)

    # Reset and enable test data button
    enable_buttons(app, test_data=True, save=True, copy=True)
    if app.snapshot.is_built:
        enable_buttons(app, result=True, python=True, unittest=True, pytest=True, execute=True)

    btn_name = app.settings.test_data_btn_name.get()
    if btn_name == "Hide":
        set_text(app.textarea.input, content)
        return

    app.settings.test_data_btn_name.set('Hide')
    input_data = extract_text(app.textarea.input)
    app.snapshot.update(user_data=input_data)
    set_text(app.textarea.input, content)


def save(app):  # noqa
    """Save content from the active input or output textarea based on its type."""
    activate_user_data_mode(app, use_test_data=False)

    focus = app.root.focus_get()

    saving_input, saving_output = False, False
    input_text  = extract_text(app.textarea.input)
    output_text = extract_text(app.textarea.output)

    if focus is not app.textarea.input or focus is not app.textarea.output:
        response = show_message_dialog(
            title="Save Options",
            yesnocancel=(
                "Choose how you want to save the text:\n"
                "  Y - Save text of the input window.\n"
                "  N - Save text of the output window.\n"
                "  C - Do not save."
            ),
        )
        if response is None:
            return

        saving_input = response is True
        saving_output = response is False

    # --- Save user snippet (input area) ---
    if saving_input or focus is app.textarea.input:
        if not input_text.strip():
            show_message_dialog(
                title="Save Options",
                warning="There is no input text to save."
            )
            return

        filename = filedialog.asksaveasfilename(
            title="Save User Snippet",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*")]
        )
        if filename:
            file.write(filename, input_text)
        return

    # --- Save generated Python test script (output area) ---
    if saving_output or focus is app.textarea.output:

        if not output_text.strip():
            show_message_dialog(
                title="Save Options",
                warning="There is no output text to save."
            )
            return

        script_header = r'"""Python (?P<kind>\w+) script is generated by TextFSMGen CE"""'
        match = re.match(script_header, output_text)

        if match:
            kind = match.group("kind")
            kind = kind if kind in {"pytest", "unittest"} else "test"

            filename = filedialog.asksaveasfilename(
                title=f"Save Python {kind.title()} Script",
                filetypes=[("Python File", "*.py"), ("All Files", "*")]
            )
            if filename:
                file.write(filename, output_text)
            return

        # --- Save TextFSM template ---
        template_header = r"#+\n# Template is generated by TextFSMGen CE"
        if re.match(template_header, output_text):
            filename = filedialog.asksaveasfilename(
                title="Save TextFSM Template",
                filetypes=[("TextFSM Files", "*.textfsm"), ("All Files", "*")]
            )
            if filename:
                file.write(filename, output_text)
            return

    # --- Fallback: show instructions ---
    show_message_dialog(
        title="Save File Instructions",
        info=(
            "How to save a TextFSM template or test script:\n"
            "  • Click 'Build' to generate the template\n"
            "  • Or click 'Python' / 'Unittest' / 'Pytest' to generate a test script\n"
            "  • Click the input or output window containing the text you want to save\n"
            "  • Click 'Save' to write the file to disk"
        )
    )


def clear(app):
    """
    Handle the 'Clear' button action for text widgets.
    """

    focus = app.root.focus_get()

    prev_widget_name = str(app.prev_widget)
    is_input_area = prev_widget_name.endswith('.input_textarea')
    # --- Input text area or other ---
    if (
        (is_input_area and app.textarea.input.tag_ranges(ui.tk.SEL)) or
        (focus is app.textarea.input and focus.tag_ranges(ui.tk.SEL))
    ):
        app.textarea.input.delete(ui.tk.SEL_FIRST, ui.tk.SEL_LAST)
        app.textarea.input.focus()
        return

    # Clear input and result areas
    clear_text(app.textarea.input)
    clear_text(app.textarea.output)

    # enable buttons
    enable_buttons(app, open=True, paste=True, clear=True, build=True)

    # Disable related buttons
    disable_buttons(
        app, test_data=True, save=True, copy=True,
        result=True, python=True, unittest=True,
        pytest=True, execute=True
    )

    # Reset input area state
    app.textarea.input.config(state="normal")

    # Reset snapshot attributes
    app.snapshot.update(
        user_data="",
        test_data="",
        result="",
        template="",
        is_built=False,
    )

    # Reset UI variables
    app.settings.test_data_btn_name.set('Test Data')
    # app.root.clipboard_clear()

    app.textarea.input.focus()


def copy(app):
    """Handle the 'Copy' button action for text widgets."""

    # Helper: get selected text or full widget text
    def get_content(widget):
        if widget.tag_ranges(ui.tk.SEL):
            return widget.selection_get()
        return extract_text(widget)

    focus = app.root.focus_get()

    prev_widget_name = str(app.prev_widget)
    is_input_area = prev_widget_name.endswith('.input_textarea')
    is_output_area = prev_widget_name.endswith('.output_textarea')
    if is_input_area or focus is app.textarea.input:
        content = get_content(app.textarea.input)
        if not content.strip():
            show_message_dialog(
                title="Copy Options",
                warning="There is no text in the input window to copy.",
            )
            return

    elif is_output_area or focus is app.textarea.output:
        content = get_content(app.textarea.output)
        if not content.strip():
            show_message_dialog(
                title="Copy Options",
                warning="There is no text in the output window to copy.",
            )
            return
    else:
        in_text = extract_text(app.textarea.input)
        out_text = extract_text(app.textarea.output)
        if in_text.strip() and out_text.strip():
            response = show_message_dialog(
                title="Copy Options",
                yesnocancel=(
                    "Choose what you want to copy:\n"
                    "  Y - Copy text from the input window text.\n"
                    "  N - Copy text from the output window text.\n"
                    "  C - Do not copy."
                ),
            )
            if response is None:
                return
            content = in_text if response else out_text
        elif in_text.strip():
            content = in_text
        elif out_text.strip():
            content = out_text
        else:
            show_message_dialog(
                title="Copy Options",
                warning="There is no text available in either window to copy.",
            )
            return

    # Update UI and clipboard
    app.root.clipboard_clear()
    app.root.clipboard_append(content)
    app.root.update()


def paste(app) -> None:
    """Paste clipboard text into the input area and update snapshot state."""
    current_text = extract_text(app.textarea.input)
    widget_name = str(app.prev_widget)

    has_content = bool(current_text.strip())
    is_input_area = widget_name.endswith(".input_textarea")

    try:
        data = app.root.clipboard_get()
    except Exception as ex:
        show_message_dialog(
            title="Clipboard Empty",
            info=(f"There is no text available to paste from the clipboard.\n"
                  f"{'-' * 70}\n"
                  f"{type(ex).__name__}: {ex}"
            )
        )
        return

    if not data:
        return

    if not is_input_area:
        enable_buttons(app, test_data=True, save=True, copy=True)
        response = show_message_dialog(
            title="Paste Options",
            yesnocancel=(
                "Choose how you want to paste the text:\n"
                "  Y - Clear existing content and paste clipboard text.\n"
                "  N - Paste clipboard text without clearing.\n"
                "  C - Do not paste."
            ),
        )
        if response is None:
            return

        # app.snapshot.update(user_data=data, test_data=data)
        if response:
            activate_user_data_mode(app)
            app.buttons.get("clear").invoke()
            app.snapshot.update(user_data=data, test_data=data)
        else:
            btn_name = app.settings.test_data_btn_name.get()
            if btn_name == "Test Data":
                app.snapshot.update(test_data=data)
            else:
                app.snapshot.update(user_data=data)

        set_text(app.textarea.input, data)
        enable_buttons(app, test_data=True, save=True, copy=True)
        app.settings.test_data_btn_name.set('Test Data')
        app.textarea.input.focus()
        return

    btn_name = app.settings.test_data_btn_name.get()

    if has_content:
        # Paste into existing input area content
        if app.textarea.input.tag_ranges(ui.tk.SEL):
            app.textarea.input.delete(ui.tk.SEL_FIRST, ui.tk.SEL_LAST)

        insert_pos = app.textarea.input.index(ui.tk.INSERT)
        app.textarea.input.insert(ui.tk.INSERT, data)
        app.textarea.input.tag_add(ui.tk.SEL, insert_pos, f"{insert_pos}+{len(data)}c")
        app.textarea.input.focus()

        updated = extract_text(app.textarea.input)
        if btn_name == "Test Data":
            app.snapshot.update(user_data=updated)
        else:
            app.snapshot.update(test_data=updated)

    else:
        # Paste as new test data
        if app.snapshot.user_data or app.snapshot.test_data:
            if btn_name == "Test Data":
                app.snapshot.update(user_data=data)
            else:
                app.snapshot.update(test_data=data)
        else:
            app.snapshot.update(user_data=data, test_data=data)

        set_text(app.textarea.input, data)
        enable_buttons(app, test_data=True, save=True, copy=True)
        app.textarea.input.focus()


def create_python_script(app):
    """
    Handle the 'Snippet' button action to generate a lightweight Python test script.
    """
    # --- Validate prerequisites ---
    if not validate_prerequisites(app, kind="python"):
        return

    # --- Build snippet script ---
    try:    # noqa
        user_data = extract_text(app.textarea.input)
        if app.category_translator_enabled():
            cls = CategoryTemplateBuilder
            kwargs = app.get_category_template_builder_args()
        elif app.tabular_translator_enabled():
            cls = TabularTemplateBuilder
            kwargs = app.get_tabular_template_builder_args()
        else:
            cls = TemplateBuilder
            kwargs = app.get_template_builder_args()

        builder = cls(
            user_data=user_data,
            test_data=app.snapshot.test_data,
            **kwargs
        )
        script = builder.create_python_test()

        if app.category_translator_enabled() or app.tabular_translator_enabled():
            app.reset_category_translator()
            app.reset_tabular_translator()
            set_text(app.textarea.input, app.snapshot.user_data)
            if isinstance(builder, (TabularTemplateBuilder, CategoryTemplateBuilder)):
                app.snapshot.update(user_data=builder.snippet)

        # Update snapshot and UI
        set_text(app.textarea.output, script)
        app.textarea.output.focus()

    except Exception as ex:
        if not validate_count_fields(app):
            return

        show_message_dialog(
            title='TextFSM Generator Error',
            error=f"{type(ex).__name__}: {ex}"
        )


def create_unittest_script(app):
    """
    Handle the 'Unittest' button action to generate a Python unittest script.
    """
    # --- Validate prerequisites ---
    if not validate_prerequisites(app, kind="unittest"):
        return

    # --- Build unittest script ---
    try:
        user_data = extract_text(app.textarea.input)    # noqa
        if app.category_translator_enabled():
            cls = CategoryTemplateBuilder
            kwargs = app.get_category_template_builder_args()
        elif app.tabular_translator_enabled():
            cls = TabularTemplateBuilder
            kwargs = app.get_tabular_template_builder_args()
        else:
            cls = TemplateBuilder
            kwargs = app.get_template_builder_args()

        builder = cls(
            user_data=user_data,
            test_data=app.snapshot.test_data,
            **kwargs
        )
        script = builder.create_unittest()

        if app.category_translator_enabled() or app.tabular_translator_enabled():   # noqa
            app.reset_category_translator()
            app.reset_tabular_translator()
            set_text(app.textarea.input, app.snapshot.user_data)
            if isinstance(builder, (TabularTemplateBuilder, CategoryTemplateBuilder)):
                app.snapshot.update(user_data=builder.snippet)

        # Update snapshot and UI
        set_text(app.textarea.output, script)
        app.textarea.output.focus()

    except Exception as ex:
        if not validate_count_fields(app):
            return

        show_message_dialog(
            title='TextFSM Generator Error',
            error=f"{type(ex).__name__}: {ex}"
        )


def create_pytest_script(app):
    """Handle the 'Pytest' button action to generate a Python pytest script."""

    # --- Validate prerequisites ---
    if not validate_prerequisites(app, kind="pytest"):
        return

    # --- Build pytest script ---
    try:    # noqa
        user_data = extract_text(app.textarea.input)
        if app.category_translator_enabled():
            cls = CategoryTemplateBuilder
            kwargs = app.get_category_template_builder_args()
        elif app.tabular_translator_enabled():
            cls = TabularTemplateBuilder
            kwargs = app.get_tabular_template_builder_args()
        else:
            cls = TemplateBuilder
            kwargs = app.get_template_builder_args()

        builder = cls(
            user_data=user_data,
            test_data=app.snapshot.test_data,
            **kwargs
        )
        script = builder.create_python_test()

        if app.category_translator_enabled() or app.tabular_translator_enabled():
            app.reset_category_translator()
            app.reset_tabular_translator()
            set_text(app.textarea.input, app.snapshot.user_data)
            if isinstance(builder, (TabularTemplateBuilder, CategoryTemplateBuilder)):
                app.snapshot.update(user_data=builder.snippet)

        # Update snapshot and UI
        set_text(app.textarea.output, script)
        app.textarea.output.focus()

    except Exception as ex:
        if not validate_count_fields(app):
            return

        show_message_dialog(
            title='TextFSM Generator Error',
            error=f"{type(ex).__name__}: {ex}"
        )


def execute_test_script(app):

    if not notify_test_execution(app):  # noqa
        return

    # --- Validate prerequisites ---
    if not validate_prerequisites(app, kind="result"):
        return

    if not validate_python_interpreter(app):
        return

    out_text = extract_text(app.textarea.output)
    python_interpreter = app.settings.python_interpreter.get()

    pattern = r'"""Python (?P<kind>\w+) script is generated by TextFSMGen CE"""'
    match = re.match(pattern, out_text)

    if match:
        result = testing.execute_test_script(python_interpreter, content=out_text)
        set_text(app.textarea.output, str(result))
        return

    response = show_message_dialog(
        title="Execution Test Script Options",
        yesnocancel=(
            "Choose how you want to execute the test:\n"
            "  Y - Run pytest\n"
            "  N - Run unittest\n"
            "  C - Run python test\n\n"
            "-------------------------------\n"
            "Note: To execute a test script without this prompt:\n"
            "  • Click 'Python', 'Unittest', or 'Pytest' to generate the script\n"
            "  • Click 'Execute' to run the test\n"
        ),
    )

    btn_name = "pytest" if response else "python" if response is None else "unittest"
    app.buttons.get(btn_name).invoke()
    test_script = extract_text(app.textarea.output)
    result = testing.execute_test_script(
        python_interpreter,
        content=test_script,
        deleted=app.settings.delete_file_after_run_flag.get()
    )
    set_text(app.textarea.output, str(result))


def show_result(app):
    """
    Handle the 'Result' button action to parse test data with a TextFSM template.
    """
    # --- Validate prerequisites ---
    if not validate_prerequisites(app, kind="result"):
        return

    # --- Build or reuse template ---
    try:
        user_data = extract_text(app.textarea.input)    # noqa
        if app.category_translator_enabled():
            cls = CategoryTemplateBuilder
            kwargs = app.get_category_template_builder_args()
        elif app.tabular_translator_enabled():
            cls = TabularTemplateBuilder
            kwargs = app.get_tabular_template_builder_args()
        else:
            cls = TemplateBuilder
            kwargs = app.get_template_builder_args()

        builder = cls(user_data=user_data, **kwargs)
        app.snapshot.update(template=builder.template, is_built=bool(builder))

        if app.category_translator_enabled() or app.tabular_translator_enabled():   # noqa
            app.reset_category_translator()
            app.reset_tabular_translator()
            set_text(app.textarea.input, app.snapshot.user_data)
            if isinstance(builder, (TabularTemplateBuilder, CategoryTemplateBuilder)):
                app.snapshot.update(user_data=builder.snippet)

        template = builder.template
    except Exception as ex:
        if not validate_count_fields(app):
            return

        template = app.snapshot.template.strip()
        if not template:
            show_message_dialog(
                title='TextFSM Generator Error',
                error=f"{type(ex).__name__}: {ex}"
            )
            return

    # --- Parse test data ---
    stream = StringIO(template)     # noqa
    parser = TextFSM(stream)
    rows = parser.ParseTextToDicts(app.snapshot.test_data)

    if not rows:
        show_message_dialog(
            title="Incorrect TextFSM Template or Test Data",
            error=(
                "The parsed result is empty. This may indicate "
                "an incorrect TextFSM template or invalid test data."
            ),
        )
        return

    # --- Construct result string ---
    test_data = app.snapshot.test_data
    result_sections = []

    if app.settings.template_flag.get() and template:
        result_sections.append(template)
        result_sections.append("\n<<====================>>\n")

    if app.settings.test_data_flag.get() and test_data:
        result_sections.append(test_data)
        result_sections.append("\n<<====================>>\n")

    if app.settings.tabular_flag.get():
        with_index = app.settings.index_flag.get()
        result_sections.append(get_data_as_tabular(rows, with_index=with_index))
    else:
        pretty_data = pformat(rows)
        result_sections.append(pretty_data)

    set_text(app.textarea.output, "\n".join(result_sections))


def disable_buttons(app, **states) -> None:     # noqa
    """Disable selected UI buttons based on keyword flags."""
    for name, flag in states.items():
        button = app.buttons.get(name)
        if flag and isinstance(button, ui.Button):
            button.config(state="disabled")


def enable_buttons(app, **states) -> None:
    """Enable selected UI buttons based on keyword flags."""
    for name, flag in states.items():
        button = app.buttons.get(name)
        if flag and isinstance(button, ui.Button):
            button.config(state="normal")


def has_user_data(app, title="Missing User Data", msg=""):
    """Validate that user data exists; show guidance dialog if missing."""
    if not app.snapshot.user_data:
        show_message_dialog(
            title=title,
            error=(
                f"{msg}\n\n" if msg else ""
                "How to add user data:\n"
                "  Option 1: File > Open\n"
                "  Option 2: Click the 'Open' button to load data from a file\n"
                "  Option 3:\n"
                "    • If you see a 'Test Data' button, you are already in 'User Data' mode\n"
                "    • Otherwise, click the 'Hide' button to switch to 'User Data' mode\n"
                "    • Enter text manually or use the Paste button"
            )
        )
        return False
    return True


def has_test_data(app, title="Missing Test Data", msg=""):
    """Validate that test data exists; show guidance dialog if missing."""
    if not app.snapshot.test_data:
        show_message_dialog(
            title=title,
            error=(
                f"{msg}\n\n" if msg else ""
                "How to add test data:\n"
                "  Option 1: File > Load Test Data\n"
                "  Option 2:\n"
                "    • If you see a 'Hide' button, you are already in 'Test Data' mode\n"
                "    • Otherwise, click the 'Test Data' button to switch to 'Test Data' mode\n"
                "    • Enter text manually or use the Paste button"
            )
        )
        return False
    return True


def activate_user_data_mode(app, use_test_data=True):
    """Switch to 'User Data' mode and sync snapshot/user data state."""
    current_label = app.settings.test_data_btn_name.get()
    translators_on = app.category_translator_enabled() or app.tabular_translator_enabled()
    if current_label == "Test Data":
        if translators_on and app.snapshot.test_data and use_test_data:
            set_text(app.textarea.input, app.snapshot.test_data)
        return

    user_input = extract_text(app.textarea.input)
    app.snapshot.update(test_data=user_input)

    set_text(app.textarea.input, app.snapshot.user_data)
    app.settings.test_data_btn_name.set("Test Data")

    if translators_on and app.snapshot.test_data and use_test_data:
        set_text(app.textarea.input, app.snapshot.test_data)


def notify_test_execution(app):
    """Notify test execution."""
    always_ask_flag = app.settings.always_ask_flag.get()
    if not always_ask_flag:
        return True

    response = show_message_dialog(
        title="Test Execution",
        yesno=(
            "Running the test requires saving the script to a temporary file.\n"
            "By default, the file will be automatically deleted after execution.\n\n"
            "Do you want to continue?\n\n\n\n"
            "Note: 'Deleted File After Run' is unchecked in Settings, the "
            "temporary file will be preserved.\n\n"
            "========================================\n"
            f"Temporary Directory: {testing.get_temp_dir()}\n"
            "========================================"
        )
    )
    return response

def validate_prerequisites(app, kind):
    """Validate required test and user data before building scripts or templates."""
    messages = {
        "python":  "Cannot build a Python test script without %s data.",
        "unittest": "Cannot build a Python unittest script without %s data.",
        "pytest":   "Cannot build a Python pytest script without %s data.",
        "result":   "Cannot build a TextFSM template and parse test data without %s data.",
        "execute": "Cannot execute a generated test script without %s data.",
    }

    template = messages.get(kind)
    if not template:
        return False

    activate_user_data_mode(app)

    for name, func in (("user", has_user_data), ("test", has_test_data)):
        if not func(app, msg=template % name):
            return False

    return True


def validate_python_interpreter(app):
    """Validate that Python interpreter exists; show guidance dialog if missing."""
    python_interpreter = app.settings.python_interpreter.get()
    if not python_interpreter:
        show_message_dialog(
            title="Missing Python Interpreter",
            error=(
                "Test execution cannot proceed without a configured Python interpreter.\n\n"
                "Please click the 'Settings' button and select a Python interpreter."
            ),
        )
        return False

    ok = testing.validate_python_executable(python_interpreter)
    if not ok:
        show_message_dialog(
            title="Invalid Python Interpreter",
            error=(
                "The selected file is not a valid Python interpreter.\n\n"
                "Please choose a correct Python interpreter and try again."
            ),
        )
        return False

    return True


def validate_count_fields(app):
    """Validate category and tabular count fields; show an error dialog if invalid."""
    try:
        category_count = app.settings.category_arg_count.get()
        tabular_count = app.settings.tabular_arg_count.get()
        return True
    except Exception as ex:
        # Identify which field failed based on which value was successfully retrieved
        field = "Category" if "category_count" not in locals() else "Tabular"
        show_message_dialog(
            title=f"Invalid Count Entry - {field} Template Translator",
            error=(
                f"Count field of must be integers.\n"
                f"Please enter a correct count in Settings - {field}.\n"
                "----------------------------------------------------------------\n"
                f"{type(ex).__name__}: {ex}"
            ),
        )
        return False
