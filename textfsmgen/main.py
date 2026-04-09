"""
textfsmgen.main
===============

Entry point for the TextFSM Generator command‑line interface (CLI).
"""

import argparse

from textfsmgen.libs.common import sys_exit
from textfsmgen.libs.common import decorate_list_of_line
from textfsmgen.libs import file

from textfsmgen.application import Application
from textfsmgen import TemplateBuilder
from textfsmgen import CategoryTemplateBuilder
from textfsmgen import TabularTemplateBuilder


def run_gui_application(options):
    """Launch the TextFSM Generator GUI application."""
    if not options.gui:
        return

    app = Application()
    app.run()
    sys_exit(success=True)


def show_dependency(options):
    """Display dependency information for the TextFSM Generator application."""
    if not options.dependency:
        return

    from platform import uname
    from platform import python_version
    from textfsmgen import config

    os_name = uname().system
    os_release = uname().release
    py_ver = python_version()
    lst = [
        config.main_app_text,
        f'Platform: {os_name} {os_release} - Python {py_ver}',
        '--------------------',
        'Dependencies:'
    ]

    for pkg in config.get_dependency().values():
        lst.append(f'  + Package: {pkg["package"]}')
        lst.append(f'             {pkg["url"]}')

    msg = decorate_list_of_line(lst)
    sys_exit(success=True, msg=msg)


def show_version(options):
    """Display the current version of the TextFSM Generator application."""
    if not options.version:
        return

    from textfsmgen import version
    sys_exit(success=True, msg=f"textfsmgen {version}")


class Cli:
    """
    Command‑line interface (CLI) handler for the TextFSM Generator application.
    """

    def __init__(self):
        parser = argparse.ArgumentParser(
            prog='textfsmgen',
            usage='%(prog)s [options]',
            description='%(prog)s application',
        )

        parser.add_argument(
            '--gui', action='store_true',
            help="Launch the TextFSM Template Generator GUI application"
        )

        parser.add_argument(
            '--user-data', type=str, dest='user_data',
            default='',
            help="User snippet text used to generate a TextFSM template"
        )

        parser.add_argument(
            '--user-data-file', type=str, dest='user_data_file',
            default='',
            help="Load snippet text from file to generate a TextFSM template"
        )

        parser.add_argument(
            '--test-data', type=str, dest='test_data',
            default='',
            help="Optional: test data for validating the generated template"
        )

        parser.add_argument(
            '--test-data-file', type=str, dest='test_data_file',
            default='',
            help="Optional: Load test data from file for template validation"
        )

        parser.add_argument(
            '--run-test', action='store_true', dest='tested',
            help="Run validation: compare test data against the generated template"
        )

        parser.add_argument(
            '--platform', type=str,
            choices=['unittest', 'pytest', 'snippet'],
            default='',
            help="Select output format: generate a unittest, pytest, or snippet script"
        )

        parser.add_argument(
            '--save-template', type=str, dest='template_file',
            default='',
            help="Optional: Save the generated TextFSM template to a file"
        )

        parser.add_argument(
            '--save-test-script', type=str, dest='test_script_file',
            default='',
            help="Optional: Save the generated test script to a file"
        )

        parser.add_argument(
            '--options-file', type=str, dest='options_file', default='',
            help="Optional: load a YAML file containing keyword arguments for template building and verification"
        )

        parser.add_argument(
            '--dependency', action='store_true',
            help="Display TextFSM Generator dependencies and package information"
        )

        parser.add_argument(
            '-v', '--version', action='store_true',
            help="Show the current TextFSM Generator version"
        )

        self.parser = parser
        self.options = self.parser.parse_args()
        self.template_kwargs = dict()
        self.category_template_kwargs = dict()
        self.tabular_template_kwargs = dict()
        self.category_translator_enabled = False
        self.tabular_translator_enabled = False
        self.verified_kwargs = dict()
        self.tested = False
        self.template_file = ""
        self.test_script_file = ""
        self.platform = ""

    def _update_builder_arg(self, key: str, value) -> None:
        """Update a builder keyword argument if it is supported."""
        allowed = {
            "user_data", "user_data_file", "test_data", "test_data_file",
            "author", "email", "company", "description", "debug"
        }
        if key not in allowed or not value or not str(value).strip():
            return

        if key != "debug":
            self.template_kwargs[key] = value or ""
            self.category_template_kwargs[key] = value or ""
            self.tabular_template_kwargs[key] = value or ""
            return

        # Normalize debug flag
        debug = value.strip().lower() == "true" if isinstance(value, str) else bool(value)
        self.template_kwargs[key] = debug
        self.category_template_kwargs[key] = debug
        self.tabular_template_kwargs[key] = debug

    def _update_category_template_builder_arg(self, key: str, value) -> None:
        """Update a category template builder keyword argument if it is supported."""
        if key == "use_category_translator":
            self.category_translator_enabled = (
                value.strip().lower() == "true"
                if isinstance(value, str) else bool(value)
            )
            return

        allowed = {
            "count", "separator",
            "starting_from", "ending_at",
            "replacing_rules"
        }
        if key not in allowed or not value or not str(value).strip():
            return

        self.category_template_kwargs[key] = value

    def _update_tabular_template_builder_arg(self, key: str, value) -> None:
        """Update a tabular template builder keyword argument if it is supported."""
        if key == "use_tabular_translator":
            self.tabular_translator_enabled = (
                value.strip().lower() == "true"
                if isinstance(value, str) else bool(value)
            )
            return

        allowed = {
            "column_divider", "column_count",
            "column_widths", "headers", "header_rows",
            "custom_header_text",
            "starting_from", "ending_at",
            "has_header_row", "replacing_rules"
        }

        if key == "column_divider":
            self.tabular_template_kwargs[key] = value
            return

        if key not in allowed or not value or not str(value).strip():
            return

        if key == "has_header_row":
            self.tabular_template_kwargs[key] = (
                value.strip().lower() == "true"
                if isinstance(value, str) else bool(value)
            )
            return

        self.tabular_template_kwargs[key] = value


    def _update_verify_arg(self, key: str, value) -> None:
        """Update a verification keyword argument if it is supported."""
        allowed = {
            "expected_rows_count", "expected_result",
            "tabular", "debug", "ignore_space"
        }
        if key not in allowed:
            return

        # expected_rows_count → integer or None
        if key == "expected_rows_count":
            if isinstance(value, int):
                self.verified_kwargs[key] = value
            else:
                text = str(value).strip()
                self.verified_kwargs[key] = int(text) if text.isdigit() else None
            return

        # expected_result → list of dicts with uniform dict length
        if key == "expected_result":
            if isinstance(value, list) and all(
                    isinstance(i, dict) for i in value):
                lengths = {len(d) for d in value}
                self.verified_kwargs[key] = value if len(lengths) == 1 else None
            else:
                self.verified_kwargs[key] = None
            return

        # Boolean flags: tabular, debug, ignore_space
        self.verified_kwargs[key] = (
            value.strip().lower() == "true"
            if isinstance(value, str) else bool(value)
        )

    def _update_other_option(self, key, value):
        """Update miscellaneous template options such as run mode, platform, and file paths."""
        allowed = {
            "run_test", "platform",
            "save_template", "save_test_script"
        }
        if key not in allowed:
            return

        # run_test -> boolean
        if key == "run_test":
            self.tested = (
                value.strip().lower() == "true"
                if isinstance(value, str) else bool(value)
            )
            return

        # platform -> normalized choice
        if key == "platform":
            v = str(value).strip().lower()
            self.platform = v if v in {"unittest", "pytest", "snippet"} else "snippet"
            return

        setattr(self, key, str(value))

    def apply_kwargs(self, data: dict) -> None:
        """Apply keyword arguments loaded from a YAML mapping."""
        for key, value in data.items():
            key_ = key.lower()
            self._update_builder_arg(key_, value)
            self._update_category_template_builder_arg(key_, value)
            self._update_tabular_template_builder_arg(key_, value)
            self._update_verify_arg(key_, value)
            self._update_other_option(key_, value)

    def validate_cli_flags(self):
        yaml_file = self.options.options_file
        if yaml_file:
            try:
                data = file.safe_load_yaml(yaml_file)
                if not isinstance(data, dict):
                    sys_exit(
                        success=False,
                        msg=f"*** YAML-format of {yaml_file!r} MUST be a dictionary."
                    )
                self.apply_kwargs(data)
            except Exception as ex:
                sys_exit(success=False, msg=f"*** {type(ex).__name__}: {ex}")

        pairs = (
            ("user_data", self.options.user_data),
            ("user_data_file", self.options.user_data_file),
            ("test_data", self.options.test_data),
            ("test_data_file", self.options.test_data_file),
        )
        for key, value in pairs:
            if key not in self.template_kwargs:
                self.template_kwargs[key] = value
            else:
                if value:
                    self._update_builder_arg(key, value)

        if self.template_kwargs.get("user_data") or self.template_kwargs.get("user_data_file"):
            return

        self.parser.print_help()
        sys_exit(success=False)

    def create_builder(self):
        """Instantiate TemplateBuilder and exit with an error message on failure."""
        try:
            if self.category_translator_enabled:
                kwargs = self.category_template_kwargs.copy()
                cls = CategoryTemplateBuilder
            elif self.tabular_translator_enabled:
                kwargs = self.tabular_template_kwargs.copy()
                cls = TabularTemplateBuilder
            else:
                cls = TemplateBuilder
                kwargs = self.template_kwargs.copy()

            return cls(**kwargs)
        except Exception as ex:
            sys_exit(
                success=False,
                msg=(
                    f"*** {type(ex).__name__}: {ex}\n"
                    f"*** Failed to generate template from\n{self.options.user_data}"
                ),
            )

    def save_outputs(self, tb):
        """Write generated template and test script files when available."""
        template_path = self.options.template_file or self.template_file
        script_path = self.options.test_script_file or self.test_script_file

        messages = []

        if template_path:
            file.write(template_path, tb.template)
            messages.append(f"+++ TextFSM template saved to {template_path!r}.")

        if script_path and tb.test_data:
            platform = (self.options.platform or self.platform or "snippet").lower()
            method = f"create_{platform}" if platform in ("unittest",
                                                          "pytest") else "create_python_test"
            script = getattr(tb, method)()
            file.write(script_path, script)
            messages.append(f"+++ {platform.title()} script saved to {script_path!r}.")

        if messages:
            sys_exit(success=False, msg="\n".join(messages))

    def execute_test(self, tb):
        """Run builder verification when enabled and exit on success."""
        should_run = self.options.tested or self.tested
        if not should_run:
            return

        args = {**self.verified_kwargs, "debug": True}
        tb.verify(**args)
        sys_exit(success=True)

    def display_test_script(self, tb):
        """Generate the appropriate test script and print it to stdout."""
        platform = self.options.platform.lower() or self.platform
        if not platform:
            return

        method = f"create_{platform}" if platform in ("unittest", "pytest") else "create_python_test"
        test_script = getattr(tb, method, "create_python_test")()
        sys_exit(success=True, msg=test_script)

    def run(self):
        """Execute the main CLI workflow for the TextFSM Generator application."""
        show_version(self.options)
        show_dependency(self.options)
        run_gui_application(self.options)
        self.validate_cli_flags()
        tb = self.create_builder()
        self.save_outputs(tb)   # noqa
        self.execute_test(tb)   # noqa
        self.display_test_script(tb)

        if self.category_translator_enabled or self.tabular_translator_enabled:
            msg = f"{tb.snippet}\n\n\n{tb.template}"    # noqa
        else:
            msg = tb.template   # noqa
        sys_exit(success=True, msg=msg)


def execute():
    """Entry point for executing the TextFSM Generator console CLI."""
    app = Cli()
    app.run()
