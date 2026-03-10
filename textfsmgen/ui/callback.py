"""
textfsmgen.ui.callback
======================

Callback functions for UI actions in TextFSMGen.
"""

import re
from io import StringIO

from pathlib import Path
from pathlib import PurePath
from textfsm import TextFSM
from pprint import pformat

from textfsmgen import ui

from textfsmgen import TemplateBuilder
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
    """
    Handle the 'Build' button action to generate a TextFSM template.
    """

    user_data = extract_text(app.textarea.input)
    if not user_data:
        show_message_dialog(
            title="Missing Input Data",
            error="Unable to build TextFSM template: no data provided."
        )
        return

    try:
        kwargs = app.get_template_args()
        factory = TemplateBuilder(user_data=user_data, **kwargs)

        # Update snapshot with generated template
        app.snapshot.update(
            user_data=user_data,
            result=factory.template,
            template=factory.template,
            swich_app_template="",  # typo preserved from original
            is_built=True,
        )

        # Enable buttons and update UI
        app.settings.test_data_btn_name.set('Test Data')
        app.buttons.save.config(state=ui.tk.NORMAL)
        app.buttons.copy.config(state=ui.tk.NORMAL)
        set_text(app.textarea.output, factory.template)

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
        kwargs = app.get_template_args()
        factory = TemplateBuilder(user_data=user_data, debug=True, **kwargs)
        content = (f"# Please fix user_data to produce "
                   f"a good template\n{factory.bad_template}")
        set_text(app.textarea.output, content)

    if app.snapshot.is_built:
        app.buttons.result.config(state=ui.tk.NORMAL)


def open_file(app):
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

        # Reset and update widgets
        app.test_data_btn.config(state=ui.tk.NORMAL)
        app.settings.test_data_btn_name.set('Test Data')
        set_text(app.textarea.output, '')
        app.snapshot.update(test_data=content)

        # Update title and input area
        set_text(app.textarea.input, content)

        # Enable actions and set focus
        app.buttons.copy.configure(state=ui.tk.NORMAL)
        app.buttons.save.configure(state=ui.tk.NORMAL)
        app.textarea.input.focus()


def load_test_data_file(app):
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


        # Reset and enable test data button
        app.test_data_btn.config(state=ui.tk.NORMAL)
        app.settings.test_data_btn_name.set('Test Data')

        # Compare loaded content with current input
        input_data = extract_text(app.textarea.input)
        result_data = extract_text(app.textarea.output)

        if content.strip() == input_data.strip() or input_data.strip() == '':
            set_text(app.textarea.input, content)
            if input_data.strip() == '':
                pattern = r'#+\s+# *Template +is +generated '
                if not re.match(pattern, result_data):
                    set_text(app.textarea.output, '')
                else:
                    app.buttons.result.configure(state=ui.tk.NORMAL)
            app.textarea.input.focus()
        else:
            set_text(app.textarea.output, content)

        # Enable actions
        app.buttons.copy.configure(state=ui.tk.NORMAL)
        app.buttons.save.configure(state=ui.tk.NORMAL)

        # Update snapshot and title
        app.snapshot.update(
            test_data=content
        )


def save(app):
    """
    Handle the 'Save As' button action for input or output text areas.
    """

    prev_widget_name = str(app.prev_widget)
    is_input_area = prev_widget_name.endswith('.input_textarea')
    widget = app.textarea.input if is_input_area else app.textarea.output
    content = extract_text(widget)

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


def clear(app):
    """
    Handle the 'Clear' button action for text widgets.
    """

    prev_widget_name = str(app.prev_widget)
    is_input_area = prev_widget_name.endswith('.input_textarea')
    # --- Input text area or other ---
    if is_input_area and app.prev_widget.tag_ranges(ui.tk.SEL):
        app.prev_widget.delete(ui.tk.SEL_FIRST, ui.tk.SEL_LAST)
    else:
        # Clear input and result areas
        clear_text(app.textarea.input)
        clear_text(app.textarea.output)

        # Disable related buttons
        disabled_buttons = [
            app.buttons.save, app.buttons.copy,
            app.test_data_btn, app.buttons.result
        ]

        for button in disabled_buttons:
            button.config(state=ui.tk.DISABLED)

        # Reset input area state
        app.textarea.input.config(state=ui.tk.NORMAL)

        # Reset snapshot attributes
        app.snapshot.update(
            user_data="",
            test_data=None,
            result="",
            template="",
            is_built=False,
        )

        # Reset UI variables
        app.settings.test_data_btn_name.set('Test Data')
        # app.root.clipboard_clear()

    app.textarea.input.focus()


def copy(app):
    """
    Handle the 'Copy' button action for text widgets.
    """

    prev_widget_name = str(app.prev_widget)
    is_input_area = prev_widget_name.endswith('.input_textarea')
    if is_input_area:
        if app.prev_widget.tag_ranges(ui.tk.SEL):
            content = app.prev_widget.selection_get()
        else:
            content = extract_text(app.textarea.input)
    else:
        content = extract_text(app.textarea.output)

    # Update UI and clipboard
    app.root.clipboard_clear()
    app.root.clipboard_append(content)
    app.root.update()


def paste(app):
    """
    Handle the 'Paste' button action for text input areas.
    """

    curr_data = extract_text(app.textarea.input)
    prev_widget_name = str(app.prev_widget)

    is_not_empty = len(curr_data.strip()) > 0
    is_input_area = prev_widget_name.endswith('.input_textarea')
    try:
        data = app.root.clipboard_get()
        if not data:
            return

        if is_input_area and is_not_empty:
            # Paste into input area with existing content
            if app.prev_widget.tag_ranges(ui.tk.SEL):
                app.prev_widget.delete(ui.tk.SEL_FIRST, ui.tk.SEL_LAST)
            index = app.prev_widget.index(ui.tk.INSERT)
            app.prev_widget.insert(ui.tk.INSERT, data)
            app.prev_widget.tag_add(ui.tk.SEL, index, f"{index}+{len(data)}c")
            app.prev_widget.focus()
        else:
            # Paste as new test data
            app.buttons.clear.invoke()
            app.test_data_btn.config(state=ui.tk.NORMAL)
            app.settings.test_data_btn_name.set('Test Data')
            set_text(app.textarea.output, '')
            app.snapshot.update(
                test_data=data,
                result=''
            )

            set_text(app.textarea.input, data)
            app.textarea.input.focus()

        # Enable actions
        app.buttons.copy.configure(state=ui.tk.NORMAL)
        app.buttons.save.configure(state=ui.tk.NORMAL)


    except Exception as ex:     # noqa
        show_message_dialog(
            title="Clipboard Empty",
            info="Cannot paste because the clipboard contains no data."
        )


def create_python_script(app):
    """
    Handle the 'Snippet' button action to generate a lightweight Python test script.
    """
    # --- Validate prerequisites ---
    if app.snapshot.test_data is None:
        show_message_dialog(
            title="Missing Test Data",
            error=(
                "Cannot build a Python test script without test data.\n"
                "Please use the Open or Paste button to load test data."
            )
        )
        return

    user_data = extract_text(app.textarea.input)
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
        kwargs = app.get_template_args()
        factory = TemplateBuilder(
            user_data=user_data,
            test_data=app.snapshot.test_data,
            **kwargs
        )
        script = factory.create_python_test()

        # Update snapshot and UI
        set_text(app.textarea.output, script)

        # Update toggle and enable actions
        app.settings.test_data_btn_name.set('Test Data')
        app.snapshot.update(result=script)
        app.buttons.save.config(state=ui.tk.NORMAL)
        app.buttons.copy.config(state=ui.tk.NORMAL)
    except Exception as ex:
        show_message_dialog(
            title='TextFSM Generator Error',
            error=f"{type(ex).__name__}: {ex}"
        )


def create_unittest_script(app):
    """
    Handle the 'Unittest' button action to generate a Python unittest script.
    """

    # --- Validate prerequisites ---
    if app.snapshot.test_data is None:
        show_message_dialog(
            title="Missing Test Data",
            error=(
                "Cannot build a Python unittest script without test data.\n"
                "Please use the Open or Paste button to load the required data."
            )
        )
        return

    user_data = extract_text(app.textarea.input)
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
        kwargs = app.get_template_args()
        factory = TemplateBuilder(
            user_data=user_data,
            test_data=app.snapshot.test_data,
            **kwargs
        )
        script = factory.create_unittest()

        # Update snapshot and UI
        set_text(app.textarea.output, script)

        # Update toggle and enable actions
        app.settings.test_data_btn_name.set('Test Data')
        app.snapshot.update(result=script)
        app.buttons.save.config(state=ui.tk.NORMAL)
        app.buttons.copy.config(state=ui.tk.NORMAL)
    except Exception as ex:
        show_message_dialog(
            title='TextFSM Generator Error',
            error=f"{type(ex).__name__}: {ex}"
        )


def create_pytest_script(app):
    """
    Handle the 'Pytest' button action to generate a Python pytest script.
    """

    # --- Validate prerequisites ---
    if app.snapshot.test_data is None:
        show_message_dialog(
            title="Missing Test Data",
            error=(
                "Cannot build a Python pytest script without test data.\n"
                "Please use the Open or Paste button to load the required data."
            )
        )
        return

    user_data = extract_text(app.textarea.input)
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
        kwargs = app.get_template_args()
        factory = TemplateBuilder(
            user_data=user_data,
            test_data=app.snapshot.test_data,
            **kwargs
        )
        script = factory.create_pytest()

        # Update snapshot and UI
        set_text(app.textarea.output, script)

        # Update toggle and enable actions
        app.settings.test_data_btn_name.set('Test Data')
        app.snapshot.update(result=script)
        app.buttons.save.config(state=ui.tk.NORMAL)
        app.buttons.copy.config(state=ui.tk.NORMAL)
    except Exception as ex:
        show_message_dialog(
            title='TextFSM Generator Error',
            error=f"{type(ex).__name__}: {ex}"
        )


def test_data_btn(app):
    """
    Handle the 'Test Data' button toggle.
    """

    if app.snapshot.test_data is None:
        show_message_dialog(
            title='No Test Data',
            error="Please use Open or Paste button to load test data"
        )
        return

    name = app.settings.test_data_btn_name.get()
    if name == 'Test Data':
        # Show test data
        app.settings.test_data_btn_name.set('Hide')
        set_text(app.textarea.output, app.snapshot.test_data)
    else:
        # Restore result view
        app.settings.test_data_btn_name.set('Test Data')
        set_text(app.textarea.output, app.snapshot.result)


def show_parsed_result(app):
    """
    Handle the 'Result' button action to parse test data with a TextFSM template.
    """

    # --- Validate prerequisites ---
    if app.snapshot.test_data is None:
        show_message_dialog(
            title='No Test Data',
            error=("Can NOT parse text without "
                   "test data.\nPlease use Open or Paste button "
                   "to load test data")
        )
        return

    user_data = extract_text(app.textarea.input)
    if not user_data:
        show_message_dialog(
            title='Empty Data',
            error="Can NOT build regex pattern without data."
        )
        return

    # --- Build or reuse template ---
    try:
        kwargs = app.get_template_args()
        factory = TemplateBuilder(user_data=user_data, **kwargs)
        app.snapshot.update(
            user_data=user_data,
            template=factory.template,
            is_built=True
        )
        template = factory.template
    except Exception as ex:
        template = app.snapshot.template.strip()
        if not template:
            show_message_dialog(
                title='TextFSM Generator Error',
                error=f"{type(ex).__name__}: {ex}"
            )
            return

    # --- Parse test data ---
    stream = StringIO(template)
    parser = TextFSM(stream)
    rows = parser.ParseTextToDicts(app.snapshot.test_data)

    # --- Construct result string ---
    result = ''
    test_data = app.snapshot.test_data
    divider_fmt = '\n\n<<{}>>\n\n{{}}'.format('=' * 20)

    result_sections = []

    if app.settings.template.get() and template:
        result_sections.append('Template')
        result += divider_fmt.format(template) if result else template

    if app.settings.test_data.get() and test_data:
        result_sections.append('Test Data')
        result += divider_fmt.format(test_data) if result else test_data

    result_sections.append('Test Result')
    if rows and app.settings.tabular.get():
        tabular_data = get_data_as_tabular(rows)
        result += divider_fmt.format \
            (tabular_data) if result else tabular_data
    else:
        pretty_data = pformat(rows)
        result += divider_fmt.format(pretty_data) if result else pretty_data

    # --- Update snapshot and UI ---
    app.settings.test_data_btn_name.set('Test Data')
    app.snapshot.update(result=result)

    set_text(app.textarea.output, result)
