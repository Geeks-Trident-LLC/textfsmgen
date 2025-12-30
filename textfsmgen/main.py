"""
textfsmgen.main
===============

Entry point for the TextFSM Generator command‑line interface (CLI).

This module defines the main execution flow for the TextFSM Generator
application. It parses command‑line arguments, initializes application
state, and dispatches actions such as template generation, testing,
and script creation. It serves as the bridge between user input and
the core functionality provided by other modules in the package.

Purpose
-------
- Provide a CLI interface for generating and validating TextFSM templates.
- Parse and validate command‑line arguments.
- Dispatch actions to core modules (`core`, `config`, `application`).
- Handle errors gracefully and present user‑friendly messages.

Notes
-----
- This module is intended for end users interacting via CLI.
- GUI functionality is provided separately in `textfsmgen.application`.
- Errors are reported using `sys_exit` with clear diagnostic messages.
"""

import argparse
import re
import yaml

from genericlib.misc import sys_exit
from genericlib.text import decorate_list_of_line
import genericlib.file as file

from textfsmgen.application import Application
from textfsmgen import TemplateBuilder


def run_gui_application(options):
    """
    Launch the TextFSM Generator GUI application.

    This function checks whether the `--gui` option was provided via
    command‑line arguments. If enabled, it instantiates the main
    `Application` class, starts the GUI event loop, and exits the
    program gracefully upon completion.

    Parameters
    ----------
    options : argparse.Namespace
        Parsed command‑line arguments. Must include the `gui` attribute
        (boolean) to determine whether the GUI should be launched.

    Returns
    -------
    None
        This function performs side effects (launching the GUI and
        exiting the process) but does not return a value.

    Notes
    -----
    - The GUI is only launched if `options.gui` is True.
    - On successful execution, the application calls
      ``Application().run()`` and exits using ``sys_exit(success=True)``.
    - This function is typically invoked from the CLI entry point
      defined in ``textfsmgen.main``.
    """
    if options.gui:
        app = Application()
        app.run()
        sys_exit(success=True)


def show_dependency(options):
    """
    Display dependency information for the TextFSM Generator application.

    This function checks whether the `--dependency` flag was provided via
    command‑line arguments. If enabled, it collects platform details and
    application dependency metadata, formats them into a structured message,
    and exits gracefully after displaying the information.

    Parameters
    ----------
    options : argparse.Namespace
        Parsed command‑line arguments. Must include the `dependency` attribute
        (boolean) to determine whether dependency information should be shown.

    Returns
    -------
    None
        This function performs side effects (collecting metadata, formatting
        output, and exiting the process) but does not return a value.

    Notes
    -----
    - Platform information includes operating system, release, and Python version.
    - Dependency metadata is retrieved from `Data.get_dependency()` and includes
      package names, versions, and PyPI URLs.
    - Output is formatted using `decorate_list_of_line` for readability.
    - The process exits with `sys_exit(success=True)` after displaying results.
    """
    if options.dependency:
        from platform import uname
        from platform import python_version
        from textfsmgen.config import Data

        os_name = uname().system
        os_release = uname().release
        py_ver = python_version()
        lst = [
            Data.main_app_text,
            f'Platform: {os_name} {os_release} - Python {py_ver}',
            '--------------------',
            'Dependencies:'
        ]

        for pkg in Data.get_dependency().values():
            lst.append(f'  + Package: {pkg["package"]}')
            lst.append(f'             {pkg["url"]}')

        msg = decorate_list_of_line(lst)
        sys_exit(success=True, msg=msg)


def show_version(options):
    """
    Display the current version of the TextFSM Generator application.

    This function checks whether the `--version` flag was provided via
    command‑line arguments. If enabled, it retrieves the application
    version from the `textfsmgen` package and exits gracefully after
    displaying the version string.

    Parameters
    ----------
    options : argparse.Namespace
        Parsed command‑line arguments. Must include the `version` attribute
        (boolean) to determine whether the version should be shown.

    Returns
    -------
    None
        This function performs side effects (retrieving version information,
        formatting output, and exiting the process) but does not return a value.

    Notes
    -----
    - The version string is retrieved from `textfsmgen.version`.
    - Output is displayed using `sys_exit(success=True, msg=...)`.
    - This function is typically invoked from the CLI entry point in
      ``textfsmgen.main``.
    """
    if options.version:
        from textfsmgen import version
        sys_exit(success=True, msg=f"textfsmgen {version}")


class Cli:
    """
    Command‑line interface (CLI) handler for the TextFSM Generator application.

    This class encapsulates the logic for parsing command‑line arguments,
    dispatching actions, and coordinating execution of the TextFSM Generator
    in CLI mode. It provides a structured interface for end users to generate
    templates, run tests, and access application metadata directly from the
    terminal.

    Purpose
    -------
    - Define and manage CLI options for template generation and testing.
    - Parse user input via `argparse` and validate required arguments.
    - Dispatch actions to core modules (`core`, `config`, `application`).
    - Handle errors gracefully and exit with clear diagnostic messages.

    Attributes
    ----------
    parser : argparse.ArgumentParser
        Argument parser instance used to define and parse CLI options.
    options : argparse.Namespace
        Parsed command‑line arguments, including flags for template generation,
        testing, configuration, and metadata display.

    Methods
    -------
    __init__()
        Initialize the CLI parser and configure available arguments.
    parse()
        Parse command‑line arguments and store them in `options`.
    execute()
        Dispatch actions based on parsed arguments (e.g., run GUI, show version,
        display dependencies, generate templates).
    run_gui_application(options)
        Launch the GUI application if the `--gui` flag is set.
    show_dependency(options)
        Display dependency metadata when the `--dependency` flag is set.
    show_version(options)
        Display the current application version when the `--version` flag is set.

    Notes
    -----
    - The CLI is the primary entry point for terminal‑based usage.
    - GUI functionality is handled separately in `textfsmgen.application`.
    - Errors are reported using `sys_exit` with consistent formatting.
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
            '-u', '--user-data', type=str, dest='user_data',
            default='',
            help="Required: user-provided snippet used to generate a TextFSM template"
        )

        parser.add_argument(
            '-t', '--test-data', type=str, dest='test_data',
            default='',
            help="Provide user test data for template validation"
        )

        parser.add_argument(
            '-r', '--run-test', action='store_true', dest='test',
            help="Run validation: compare test data against the generated template"
        )

        parser.add_argument(
            '-p', '--platform', type=str,
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
            '-d', '--dependency', action='store_true',
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

        Parameters
        ----------
        None
            Operates on `self.options` attributes populated by argparse.

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
        """
        Generate a TextFSM template from user-provided data.

        This method attempts to construct a TextFSM template using the
        `TemplateBuilder` class. If successful, the generated template
        is returned via `sys_exit`. If an error occurs during template
        generation, the process exits gracefully with a descriptive
        error message.

        Parameters
        ----------
        None
            Operates on `self.options.user_data` and `self.kwargs` attributes.

        Returns
        -------
        None
            This function performs side effects (template generation and
            process termination) but does not return a value.

        Notes
        -----
        - Relies on `TemplateBuilder` to parse and generate the template.
        - On success, the generated template string is passed to
          `sys_exit(success=True, msg=...)`.
        - On failure, the exception type, message, and input data are
          included in the error output.
        """
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
        """
        Generate a test script based on the selected platform.

        This method constructs a test script using the `TemplateBuilder`
        class. The platform is determined from the `--platform` CLI flag
        (`unittest`, `pytest`, or `snippet`). If no platform is specified,
        a plain TextFSM template is generated instead.

        Workflow
        --------
        1. Normalize the platform string to lowercase.
        2. Map the platform to the corresponding `TemplateBuilder` method:
           - `unittest` → `create_unittest`
           - `pytest`   → `create_pytest`
           - otherwise  → `create_python_test`
        3. Attempt to generate the test script using user data and test data.
        4. Exit gracefully with the generated script or an error message.

        Parameters
        ----------
        None
            Operates on `self.options.platform`, `self.options.user_data`,
            `self.options.test_data`, and `self.kwargs`.

        Returns
        -------
        None
            This function performs side effects (script generation and
            process termination) but does not return a value.

        Notes
        -----
        - On success, the generated script is passed to
          `sys_exit(success=True, msg=...)`.
        - On failure, the exception type, message, and input data are
          included in the error output.
        - If no platform is specified, `self.build_template()` is invoked
          to generate a plain TextFSM template.
        """

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
        """
        Execute a validation test for the generated TextFSM template.

        This method runs a verification process using the `TemplateBuilder`
        class. It compares user-provided test data against the generated
        template and validates expected results. If the test succeeds, the
        process exits gracefully; otherwise, it reports the error and exits
        with failure.

        Workflow
        --------
        1. Check if the `--run-test` flag (`self.options.test`) is enabled.
        2. Instantiate `TemplateBuilder` with user data and test data.
        3. Build keyword arguments for verification:
           - `expected_rows_count` : Optional expected number of parsed rows.
           - `expected_result`     : Optional expected parsing result.
           - `tabular`             : Whether to format results in tabular form.
           - `debug`               : Always enabled for detailed output.
        4. Call `factory.verify(**kwargs)` to perform the test.
        5. Exit with success or failure depending on the outcome.

        Parameters
        ----------
        None
            Operates on `self.options.user_data`, `self.options.test_data`,
            and `self.kwargs`.

        Returns
        -------
        None
            This function performs side effects (test execution and process
            termination) but does not return a value.

        Notes
        -----
        - On success, exits with `sys_exit(success=True)`.
        - On failure, includes the exception type, message, and input data
          in the error output.
        - This method is typically invoked from the CLI entry point when
          the `--run-test` flag is set.
        """

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
        """
        Execute the main CLI workflow for the TextFSM Generator application.

        This method orchestrates the overall command-line interface (CLI)
        execution flow. It processes user-provided arguments, validates
        required flags, and dispatches actions such as displaying version
        information, showing dependencies, generating templates, running
        tests, and launching the GUI application.

        Workflow
        --------
        1. Display version information if the `--version` flag is set.
        2. Display dependency information if the `--dependency` flag is set.
        3. Validate CLI flags and required arguments.
        4. If no test data is provided:
           - Generate a TextFSM template.
        5. If test data is provided:
           - Run template verification tests.
           - Generate a test script for the selected platform.
        6. Launch the GUI application if the `--gui` flag is set.

        Parameters
        ----------
        None
            Operates on `self.options` attributes populated by argparse.

        Returns
        -------
        None
            This function performs side effects (template generation, test
            execution, GUI launch, and process termination) but does not
            return a value.

        Notes
        -----
        - Errors are reported using `sys_exit` with descriptive messages.
        - This method is the primary entry point for CLI execution.
        """

        show_version(self.options)
        show_dependency(self.options)
        self.validate_cli_flags()
        if not self.options.test_data:
            self.build_template()
        else:
            self.run_test()
            self.build_test_script()
        run_gui_application(self.options)


def execute():
    """
    Entry point for executing the TextFSM Generator console CLI.

    This function serves as the main entry point for the command-line
    interface (CLI) of the TextFSM Generator application. It instantiates
    the `Cli` class, initializes argument parsing, and dispatches actions
    based on user-provided options.

    Returns
    -------
    None
        This function performs side effects (CLI execution and process
        termination) but does not return a value.

    Notes
    -----
    - Intended to be invoked when running the application as a script
      or via `python -m textfsmgen`.
    - Delegates all CLI logic to the `Cli.run()` method.
    """
    app = Cli()
    app.run()
