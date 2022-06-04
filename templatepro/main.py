"""Module containing the logic for the templatepro entry-points."""

import sys
import argparse
import re
import yaml

from templatepro.application import Application
from templatepro import TemplateBuilder


def run_gui_application(options):
    """Run templatepro GUI application.

    Parameters
    ----------
    options (argparse.Namespace): argparse.Namespace instance.

    Returns
    -------
    None: will invoke ``templatepro.Application().run()`` and ``sys.exit(0)``
    if end user requests `--gui`
    """
    if options.gui:
        app = Application()
        app.run()
        sys.exit(0)


def show_dependency(options):
    if options.dependency:
        from platform import uname, python_version
        from templatepro.config import Data
        lst = [
            Data.main_app_text,
            'Platform: {0.system} {0.release} - Python {1}'.format(
                uname(), python_version()
            ),
            '--------------------',
            'Dependencies:'
        ]

        for pkg in Data.get_dependency().values():
            lst.append('  + Package: {0[package]}'.format(pkg))
            lst.append('             {0[url]}'.format(pkg))

        width = max(len(item) for item in lst)
        txt = '\n'.join('| {1:{0}} |'.format(width, item) for item in lst)
        print('+-{0}-+\n{1}\n+-{0}-+'.format(width * '-', txt))
        sys.exit(0)


class Cli:
    """templatepro console CLI application."""

    def __init__(self):
        parser = argparse.ArgumentParser(
            prog='templatepro',
            usage='%(prog)s [options]',
            description='%(prog)s application',
        )

        parser.add_argument(
            '--gui', action='store_true',
            help='launch a template GUI application'
        )

        parser.add_argument(
            '-u', '--user-data', type=str, dest='user_data',
            default='',
            help='Required flag: user snippet for template generation.'
        )

        parser.add_argument(
            '-t', '--test-data', type=str, dest='test_data',
            default='',
            help='User test data.'
        )

        parser.add_argument(
            '-r', '--run-test', action='store_true', dest='test',
            help='To perform test between test data vs generated template.'
        )

        parser.add_argument(
            '-p', '--platform', type=str, choices=['unittest', 'pytest', 'snippet'],
            default='',
            help='A generated script choice for unittest or pytest test framework.'
        )

        parser.add_argument(
            '--config', type=str,
            default='',
            help='Config settings for generated test script.'
        )

        parser.add_argument(
            '-d', '--dependency', action='store_true',
            help='Show TemplatePro dependent package(s).'
        )

        self.parser = parser
        self.options = self.parser.parse_args()
        self.kwargs = dict()

    def validate_cli_flags(self):
        """Validate argparse `options`.

        Returns
        -------
        bool: show ``self.parser.print_help()`` and call ``sys.exit(1)`` if
        user_data flag is empty, otherwise, return True
        """

        if not self.options.user_data:
            self.parser.print_help()
            sys.exit(1)

        pattern = r'file( *name)?:: *(?P<filename>\S*)'
        m = re.match(pattern, self.options.user_data, re.I)
        if m:
            try:
                with open(m.group('filename')) as stream:
                    self.options.user_data = stream.read()
            except Exception as ex:
                failure = '*** {}: {}'.format(type(ex).__name__, ex)
                print(failure)
                sys.exit(1)

        if self.options.test_data:
            m = re.match(pattern, self.options.test_data, re.I)
            if m:
                try:
                    with open(m.group('filename')) as stream:
                        self.options.test_data = stream.read()
                except Exception as ex:
                    failure = '*** {}: {}'.format(type(ex).__name__, ex)
                    print(failure)
                    sys.exit(1)

        if self.options.config:
            config = self.options.config
            m = re.match(pattern, config, re.I)
            if m:
                try:
                    with open(m.group('filename')) as stream:
                        content = stream.read()
                except Exception as ex:
                    failure = '*** {}: {}'.format(type(ex).__name__, ex)
                    print(failure)
                    sys.exit(1)
            else:
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
                        failure = '*** INVALID-CONFIG: {}'.format(config)
                        print(failure)
                        sys.exit(1)
                except Exception as ex:
                    failure = '*** LOADING-CONFIG-ERROR - {}'.format(ex)
                    print(failure)
                    sys.exit(1)

        return True

    def build_template(self):
        """Build template"""
        try:
            factory = TemplateBuilder(
                user_data=self.options.user_data,
                **self.kwargs
            )
            print(factory.template)
            sys.exit(0)
        except Exception as ex:
            fmt = '*** {}: {}\n*** Failed to generate template from\n{}'
            print(fmt.format(type(ex).__name__, ex, self.options.user_data))
            sys.exit(1)

    def build_test_script(self):
        """Build test script"""
        platform = self.options.platform.lower()
        if platform:
            tbl = dict(unittest='create_unittest', pytest='create_pytest')
            method_name = tbl.get(platform, 'create_python_test')
            try:
                factory = TemplateBuilder(
                    user_data=self.options.user_data,
                    test_data=self.options.test_data,
                    **self.kwargs
                )
                test_script = getattr(factory, method_name)()
                print('\n{}\n'.format(test_script))
                sys.exit(0)
            except Exception as ex:
                fmt = '*** {}: {}\n*** Failed to test script from\n{}'
                print(fmt.format(type(ex).__name__, ex, self.options.user_data))
                sys.exit(1)
        else:
            self.build_template()

    def run_test(self):
        """Run test"""
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
                sys.exit(0)
            except Exception as ex:
                fmt = '*** {}: {}\n*** Failed to run template test from\n{}'
                print(fmt.format(type(ex).__name__, ex, self.options.user_data))
                sys.exit(1)

    def run(self):
        """Take CLI arguments, parse it, and process."""
        show_dependency(self.options)
        self.validate_cli_flags()
        if not self.options.test_data:
            self.build_template()
        else:
            self.run_test()
            self.build_test_script()
        run_gui_application(self.options)


def execute():
    """Execute template console CLI."""
    app = Cli()
    app.run()
