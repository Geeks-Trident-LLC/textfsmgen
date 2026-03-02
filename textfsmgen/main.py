"""
textfsmgen.main
===============

Entry point for the TextFSM Generator command‑line interface (CLI).
"""

import argparse
import re
import yaml

from textfsmgen.libs.common import sys_exit
from textfsmgen.libs.common import decorate_list_of_line
from textfsmgen.libs import file

from textfsmgen.application import Application
from textfsmgen import TemplateBuilder


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
            help="Required: user-provided snippet used to generate a TextFSM template"
        )

        parser.add_argument(
            '--test-data', type=str, dest='test_data',
            default='',
            help="Provide user test data for template validation"
        )

        parser.add_argument(
            '--run-test', action='store_true', dest='test',
            help="Run validation: compare test data against the generated template"
        )

        parser.add_argument(
            '--platform', type=str,
            choices=['unittest', 'pytest', 'snippet'],
            default='',
            help="Select output format: generate a unittest, pytest, or snippet script"
        )

        parser.add_argument(
            '--config', type=str,
            default='',
            help="Specify configuration settings for the generated test script"
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
        self.kwargs = dict()

    def validate_cli_flags(self):
        """
        Validate and process command-line flags provided via argparse.

        This method ensures that required CLI options are present and properly
        formatted. It supports inline user data, file references, test data,
        and configuration settings. If validation fails, the program exits
        gracefully with an error message.

        Workflow
        --------
        1. Ensure `user_data` is provided; otherwise, print help and exit.
        2. If `user_data` or `test_data` matches the `file::filename` pattern,
           load content from the referenced file.
        3. If `config` is provided:
           - Load content from a file if specified.
           - Otherwise, normalize inline configuration text into YAML format.
           - Parse configuration into a dictionary and store in `self.kwargs`.

        Returns
        -------
        bool
            True if validation succeeds. Exits the program with `sys_exit`
            if validation fails.

        Notes
        -----
        - File references must use the format: ``file::path/to/file`` or
          ``filename::path/to/file``.
        - Configuration text is normalized before being parsed with
          `yaml.SafeLoader`.
        - Errors are reported with descriptive messages and terminate execution.
        """

        if not self.options.user_data:
            self.parser.print_help()
            sys_exit(success=False)

        pattern = r'file( *name)?:: *(?P<filename>\S*)'

        # Handle user_data
        match = re.match(pattern, self.options.user_data, re.I)
        if match:
            try:
                filename = match.group('filename')
                self.options.user_data = file.read(filename)
            except Exception as ex:
                sys_exit(success=False, msg=f"*** {type(ex).__name__}: {ex}")

        # Handle test_data
        if self.options.test_data:
            match = re.match(pattern, self.options.test_data, re.I)
            if match:
                try:
                    self.options.test_data = file.read(match.group('filename'))
                except Exception as ex:
                    sys_exit(success=False, msg=f"*** {type(ex).__name__}: {ex}")

        # Handle config
        if self.options.config:
            config = self.options.config
            match = re.match(pattern, config, re.I)
            content = ""
            if match:
                try:
                    content = file.read(match.group('filename'))
                except Exception as ex:
                    sys_exit(success=False, msg=f"*** {type(ex).__name__}: {ex}")
            else:
                # Normalize inline config text
                other_pat = r'''(?x)(
                    author|email|company|filename|
                    description|namespace|tabular): *'''
                content = re.sub(r' *: *', r': ', config)
                content = re.sub(other_pat, r'\n\1: ', content)
                content = '\n'.join(line.strip(', ') for line in content.splitlines())

            if content:
                try:
                    kwargs = yaml.load(content, Loader=yaml.SafeLoader)
                    if isinstance(kwargs, dict):
                        self.kwargs = kwargs
                    else:
                        sys_exit(success=False, msg=f"*** INVALID-CONFIG: {config}")
                except Exception as ex:
                    sys_exit(success=False, msg=f"*** LOADING-CONFIG-ERROR - {ex}")

        return True

    def build_template(self):
        """Generate a TextFSM template from user-provided data."""
        try:
            factory = TemplateBuilder(
                user_data=self.options.user_data,
                **self.kwargs
            )
            sys_exit(success=True, msg=factory.template)
        except Exception as ex:
            sys_exit(
                success=False,
                msg=f"*** {type(ex).__name__}: {ex}\n*** Failed to generate "
                    f"template from\n{self.options.user_data}"
            )

    def build_test_script(self):
        """Generate a test script based on the selected platform."""

        platform = self.options.platform.lower()
        if platform:
            method_map = dict(
                unittest='create_unittest',
                pytest='create_pytest'
            )
            method_name = method_map.get(platform, 'create_python_test')
            try:
                factory = TemplateBuilder(
                    user_data=self.options.user_data,
                    test_data=self.options.test_data,
                    **self.kwargs
                )
                test_script = getattr(factory, method_name)()
                sys_exit(success=True, msg=f"\n{test_script}\n")
            except Exception as ex:
                sys_exit(
                    success=False,
                    msg=f"*** {type(ex).__name__}: {ex}\n*** Failed to execute "
                        f"test script from\n{self.options.user_data} "
                )
        else:
            self.build_template()

    def run_test(self):
        """Execute a validation test for the generated TextFSM template."""

        if self.options.test:
            try:
                factory = TemplateBuilder(
                    user_data=self.options.user_data,
                    test_data=self.options.test_data,
                    **self.kwargs
                )
                kwargs = dict(
                    expected_rows_count=self.kwargs.get('expected_rows_count', None),
                    expected_result=self.kwargs.get('expected_result', None),
                    tabular=self.kwargs.get('tabular', False),
                    debug=True
                )
                factory.verify(**kwargs)
                sys_exit(success=True)
            except Exception as ex:
                sys_exit(
                    success=False,
                    msg=f"*** {type(ex).__name__}: {ex}\n*** Failed to run "
                        f"template test from\n{self.options.user_data}"
                )

    def run(self):
        """Execute the main CLI workflow for the TextFSM Generator application."""

        show_version(self.options)
        show_dependency(self.options)
        run_gui_application(self.options)
        self.validate_cli_flags()
        if not self.options.test_data:
            self.build_template()
        else:
            self.run_test()
            self.build_test_script()


def execute():
    """Entry point for executing the TextFSM Generator console CLI."""
    app = Cli()
    app.run()
