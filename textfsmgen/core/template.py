"""
textfsmgen.core.template
========================

Core functionality for the TextFSM Generator.

This module provides the foundational logic for building and validating
TextFSM templates. It defines the primary classes and functions that
transform user-provided snippets into structured parsing templates,
support test execution, and integrate with configuration options.
"""

from typing import Optional

import re
from datetime import datetime
from textwrap import indent
from textfsm import TextFSM
from io import StringIO

from textfsmgen.libs import text
from textfsmgen.libs import file

from textfsmgen.core.patterns import LinePattern
from textfsmgen.libs.text import enclose_string

from textfsmgen.libs.utils import get_data_as_tabular
from textfsmgen.libs.common import decorate_text
from textfsmgen.libs import datatype

from textfsmgen.exceptions import TemplateParsedLineError
from textfsmgen.exceptions import TemplateBuilderError
from textfsmgen.exceptions import TemplateBuilderInvalidFormat

from textfsmgen.engine.category import CategoryLinesTranslator
from textfsmgen.engine.tabular import TabularTranslator

import logging
logger = logging.getLogger(__file__)


class LineParser:
    def __init__(self, txt):
        self.text = str(txt)
        self.line = ''
        self.template_op = ''
        self.ignore_case = False
        self.is_comment = False
        self.comment = ''
        self.is_kept = False
        self.kept = ''
        self.variables = list()
        self._parse()

    @property
    def is_empty(self) -> bool:
        """Check whether the line is empty."""
        return not bool(self.line.strip())

    @property
    def is_word(self) -> bool:
        """Check whether the text represents a single word."""
        return bool(re.match(r'^[A-Za-z]\w*$', self.text.strip()))

    @property
    def no_letters(self) -> bool:
        """Check whether the line contains no alphabetic characters."""
        if self.is_empty:
            return False
        return bool(re.match(r'[^a-z0-9]+$', self.line, flags=re.I))

    def statement(self) -> str:
        """Construct the template statement for the current line."""
        if self.is_empty:
            return ""
        if self.is_comment:
            return self.comment
        if self.is_kept:
            return self.kept
        if self.is_word:
            return self.text

        line_pattern = LinePattern(self.line, ignore_case=self.ignore_case)

        if line_pattern.variables:
            self.variables = line_pattern.variables[:]
            statement = line_pattern.statement
        else:
            try:
                re.compile(self.line)
                if re.search(r'\s', self.line):
                    statement = line_pattern
                else:
                    if '(' in self.line and self.line.endswith(')'):
                        statement = line_pattern if not line_pattern.endswith(')') else self.line
                    else:
                        statement = self.line
            except Exception as ex:     # noqa
                statement = line_pattern

        # Normalize case-insensitive flag placement
        statement = statement.replace('(?i)^', '^(?i)')

        # Ensure proper start anchor spacing
        spacer = '  ' if statement.startswith('^') else '  ^'
        statement = f"{spacer}{statement}"

        # Ensure proper end anchor
        if statement.endswith('$') and not statement.endswith(r'\$'):
            statement = f"{statement}$"

        # Append template operator if present
        if self.template_op:
            statement = f"{statement} -> {self.template_op}"

        return statement

    def _parse(self) -> None:
        """Parse the line and reapply formatting for template construction."""
        lst = self.text.rsplit(" -> ", 1)
        if len(lst) == 2:
            tmpl_op = lst[-1].strip()
            first, *remaining = tmpl_op.split(' ', 1)

            mapping = {'norecord': 'NoRecord', 'clearall': 'ClearAll'}
            if '.' in first:
                pat = r'(?P<lop>next|continue|error)\.' \
                      r'(?P<rop>norecord|record|clearall|clear)$'
                match = re.match(pat, first, flags=re.I)
                if match:
                    lop = match.group("lop").title()
                    rop = match.group("rop").title()
                    rop = mapping.get(rop.lower(), rop)
                    op = f"{lop}.{rop}"
                else:
                    op = first
                tmpl_op = f"{op} {''.join(remaining)}"
            else:
                pat = r'(next|continue|error|norecord|record|clearall|clear)$'
                if re.match(pat, first, flags=re.I):
                    op = first.title()
                    op = mapping.get(op.lower(), op)
                else:
                    op = first
                tmpl_op = f"{op} {''.join(remaining)}"

            self.template_op = tmpl_op.strip()
            txt = lst[0].rstrip()
        else:
            txt = self.text

        flag_pat = r"^(?P<flag>(ignore_case|comment|keep)__+ )?(?P<line>.*)"
        match = re.match(flag_pat, txt, flags=re.I)
        if not match:
            raise TemplateParsedLineError(f"Invalid format - {self.text!r}")

        value = match.group("flag") or ""
        flag = value.lower().strip().rstrip("_")
        self.ignore_case = flag == "ignore_case"
        self.is_comment = flag == "comment"
        self.is_kept = flag == "keep"
        self.line = match.group("line") or ""

        if self.is_comment:
            prefix = "  " if value.count("_") == 2 else ""
            self.comment = f"{prefix}# {self.line}"

        if self.is_kept:
            self.kept = f"  ^{self.line.strip().lstrip('^')}"


class TemplateBuilder:
    """
    Build TextFSM templates and generate associated test scripts.
    """
    logger = logger

    def __init__(
        self,
        test_data='',
        test_data_file='',
        user_data='',
        user_data_file='',
        author='',
        email='',
        company='',
        description='',
        test_script_file='',
        debug=False
    ):
        test_data_ = file.read(test_data_file) if test_data_file else test_data
        self.test_data = text.list_to_text(test_data_)

        user_data_ = file.read(user_data_file) if user_data_file else user_data
        self.user_data = text.list_to_text(user_data_)

        self.author = str(author)
        self.email = str(email)
        self.company = str(company)
        self.description = text.list_to_text(description)
        self.test_script_file = str(test_script_file)
        self.variables = []
        self.statements = []
        self.bare_template = ''
        self.template = ''
        self.template_parser = None
        self.verified_message = ''
        self.debug = debug
        self.bad_template = ''

        self.build()

    def prepare(self) -> None:
        """
        Parse user data lines and build template statements.
        """

        for line in self.user_data.splitlines():
            line = line.rstrip()

            parsed_line = LineParser(line)
            statement = parsed_line.statement()
            if statement.endswith(r'\$$'):
                statement = '{}$$'.format(statement[:-3])
            elif r'\$$ -> ' in statement:
                statement = statement.replace(r'\$$ -> ', '$$ -> ')
            statement = statement.replace(r'\$', r'\x24')

            if statement:
                self.statements.append(statement)
            else:
                if self.statements:
                    self.statements.append(statement)

            if parsed_line.variables:
                for pl_var in parsed_line.variables:
                    is_identical = False
                    for var in self.variables:
                        if pl_var.name == var.name and pl_var.pattern == var.pattern:
                            is_identical = True
                            break
                    if not is_identical:
                        self.variables.append(pl_var)

    def template_header(self) -> str:
        """Build a formatted metadata header for a generated template."""

        lines = [
            "#" * 80,
            f"# Template is generated by TextFSMGen CE",
        ]

        author = self.author or self.company
        if author:
            lines.append(f"# Created by  : {author}")
        if self.email:
            lines.append(f"# Email       : {self.email}")
        if self.company:
            lines.append(f"# Company     : {self.company}")

        lines.append(f"# Created date: {datetime.now():%Y-%m-%d}")

        if self.description:
            description = indent(self.description, "#     ").strip("# ")
            lines.append(f"# Description : {description}")

        lines.append("#" * 80)
        return "\n".join(lines)

    def reformat(self, template: str) -> str | None:    # noqa
        """
        Reformat a TextFSM template for readability.
        """
        if not template:
            return None

        lines = []
        pattern = r"[\r\n]+[a-zA-Z]\w*([\r\n]+|$)"
        start = 0
        last_match = None

        for match in re.finditer(pattern, template):
            before = match.string[start:match.start()]
            state = match.group().strip()

            if before.strip():
                for line in before.splitlines():
                    if line.strip():
                        lines.append(line)

            lines.append("")  # blank line before state
            lines.append(state)
            start = match.end()
            last_match = match

        if last_match and lines:
            after = last_match.string[last_match.end():]
            if after.strip():
                for line in after.splitlines():
                    if line.strip():
                        lines.append(line)

        return "\n".join(lines)

    def build(self) -> None:
        """
        Build a TextFSM template from user data.
        """
        self.template = ""
        self.prepare()

        if not self.variables:
            raise TemplateBuilderInvalidFormat(
                "user_data does not have any assigned variable for template."
            )

        # Build comment and template sections
        comment = self.template_header()
        variables = "\n".join(v.value for v in self.variables)
        template_def = "\n".join(self.statements)

        if not template_def.strip().startswith("Start"):
            template_def = f"Start\n{template_def}"

        bare_template = f"{variables}\n\n{template_def}"
        template = f"{comment}\n{bare_template}"

        # Reformat templates
        self.bare_template = self.reformat(bare_template)
        self.template = self.reformat(template)

        # Validate template with TextFSM
        try:
            stream = StringIO(self.template)
            self.template_parser = TextFSM(stream)
        except Exception as ex:
            error_msg = f"{type(ex).__name__}: {ex}"
            if not self.debug:
                raise TemplateBuilderError(error_msg)
            self.logger.error(error_msg)
            self.bad_template = f"# {error_msg}\n{self.template}"
            self.template = ""

    def show_debug_report(
            self,
            test_result: Optional[list[dict] | None] = None,
            expected_result: Optional[list[dict] | None] = None,
            tabular: bool = False,
    ) -> None:
        """
        Display debug report for template verification.
        """
        if not self.verified_message:
            return

        # Template
        print(decorate_text(f"{'Template:':<16}"))
        print(f"{self.template}\n")

        # Test Data
        print(decorate_text(f"{'Test Data:':<16}"))
        print(f"{self.test_data}\n")

        # Expected Result
        if expected_result is not None:
            print(decorate_text(f"{'Expected Result:':<16}"))
            print(f"{expected_result}\n")

        # Test Result
        if test_result is not None:
            print(decorate_text(f"{'Test Result:':<16}"))
            formatted_result = get_data_as_tabular(test_result) if tabular else test_result
            print(f"{formatted_result}\n")

        # Verified Message
        verified_msg = f"Verified Message: {self.verified_message}"
        print(decorate_text(verified_msg))

    def verify(self, expected_rows_count=None, expected_result=None,
               tabular=False, debug=False, ignore_space=False):
        """Verify parsed test data against expected results."""

        if not self.test_data:
            self.verified_message = 'test_data is empty.'
            if debug:
                self.show_debug_report()
            return False

        is_verified = True
        try:
            rows = self.template_parser.ParseTextToDicts(self.test_data)
            if not rows:
                self.verified_message = 'There is no record after parsed.'
                if debug:
                    self.show_debug_report()
                return False

            # Validate row count
            if expected_rows_count is not None:
                actual_count = len(rows)
                chk = expected_rows_count == actual_count
                is_verified &= chk
                self.verified_message = (
                    f"Parsed-row-count and expected-row-count are {expected_rows_count}."
                    if chk
                    else f"Parsed-row-count is {actual_count} while expected-row-count is {expected_rows_count}."
                )

            # Validate expected result
            if expected_result is not None:
                rows_to_compare = datatype.clean_list_of_dicts(rows) if ignore_space else rows
                chk = rows_to_compare == expected_result
                is_verified &= chk
                result_msg = (
                    "Parsed result and expected result are matched."
                    if chk
                    else "Parsed result and expected result are different."
                )
                self.verified_message = f"{self.verified_message}\n{result_msg}".strip()

            # Default success message
            if is_verified and not self.verified_message:
                self.verified_message = 'Parsed result has record(s).'

            # Debug output
            if debug:
                self.show_debug_report(
                    test_result=rows,
                    expected_result=expected_result,
                    tabular=tabular
                )

            return is_verified

        except Exception as ex:
            raise TemplateBuilderError(f"{type(ex).__name__}: {ex}")

    def create_test_script(self, test_script_fmt: str, error: str) -> str:
        """
        Generate a test script from the current template and test data.
        """

        if not self.test_data:
            raise TemplateBuilderError(error)

        test_script = test_script_fmt.format(
            template=enclose_string(self.template),
            test_data=enclose_string(self.test_data)
        )

        if self.test_script_file:
            file.write(self.test_script_file, test_script)
        return test_script

    def create_unittest(self):
        """
        Generate a Python unittest script for the current template and test data.
        """
        test_script_fmt = text.dedent_and_strip('''
            """Python unittest script is generated by TextFSMGen CE"""
            
            import unittest
            from textfsm import TextFSM
            from io import StringIO
            
            template = r{template}
            
            test_data = {test_data}
            
            
            class TestTemplate(unittest.TestCase):
                def test_textfsm_template(self):
                    stream = StringIO(template)
                    parser = TextFSM(stream)
                    rows = parser.ParseTextToDicts(test_data)
                    total_rows_count = len(rows)
                    self.assertGreaterEqual(total_rows_count, 0)
            
            if __name__ == '__main__':
                unittest.main()
        ''')
        error = 'Cannot create Python unittest script without test data.'
        test_script = self.create_test_script(test_script_fmt, error)
        return test_script

    def create_pytest(self):
        """
        Generate a Python pytest script for the current template and test data.
        """
        test_script_fmt = text.dedent_and_strip('''
            """Python pytest script is generated by TextFSMGen CE"""

            from textfsm import TextFSM
            from io import StringIO

            template = r{template}
            
            test_data = {test_data}


            class TestTemplate:
                def test_textfsm_template(self):
                    stream = StringIO(template)
                    parser = TextFSM(stream)
                    rows = parser.ParseTextToDicts(test_data)
                    total_rows_count = len(rows)
                    assert total_rows_count > 0
            
            if __name__ == "__main__":
                import pytest
                raise SystemExit(pytest.main(["-v", __file__]))
        ''')
        error = "Cannot create Python pytest script without test data."
        test_script = self.create_test_script(test_script_fmt, error)
        return test_script

    def create_python_test(self):
        """
        Generate a Python snippet script for the current template and test data.
        """
        test_script_fmt = text.dedent_and_strip(r'''
            """Python snippet script is generated by TextFSMGen CE"""

            from textfsm import TextFSM
            from io import StringIO

            template = r{template}

            test_data = {test_data}


            def test_textfsm_template(template_, test_data_):
                """test textfsm template via test data
                
                Parameters
                ----------
                template_ (str): a content of textfsm template.
                test_data_ (str): test data.
                """
                
                # show test data
                print("Test data:\n----------\n%s" % test_data_)
                print("\n%s\n" % ("+" * 40))
                
                # show textfsm template
                print("Template:\n---------\n%s" % template_)
                
                stream = StringIO(template_)
                parser = TextFSM(stream)
                rows = parser.ParseTextToDicts(test_data_)
                total_rows_count = len(rows)
                assert total_rows_count > 0
                
                # print parsed result
                print("\n%s\n" % ("+" * 40))
                print("Result:\n-------\n%s\n" % rows)
            
            if __name__ == "__main__":
                test_textfsm_template(template, test_data)
        ''')
        error = 'Cannot create Python snippet script without test data.'
        test_script = self.create_test_script(test_script_fmt, error)
        return test_script


class CategoryTemplateBuilder:
    def __init__(
        self,
        user_data='',
        user_data_file='',
        test_data='',
        test_data_file='',
        count=1,
        separator=":",
        starting_from=None,
        ending_at=None,
        replacing_rules=None,
        author='',
        email='',
        company='',
        description='',
        test_script_file='',
        debug=False
    ):
        self.translator = CategoryLinesTranslator(
            user_data,
            count=count,
            separator=separator,
            starting_from=starting_from,
            ending_at=ending_at,
            replacing_rules=replacing_rules,
        )

        self.template_builder_args = dict(
            user_data=user_data,
            user_data_file=user_data_file,
            test_data=test_data,
            test_data_file=test_data_file,
            author=author,
            email=email,
            company=company,
            description=description,
            test_script_file=test_script_file,
            debug=debug
        )

        self.builder = None

        if self.translator:
            snippet = self.translator.to_template_snippet()
            self.template_builder_args.update(user_data=snippet)
            self.builder = TemplateBuilder(**self.template_builder_args)

    def __bool__(self): return bool(self.translator)

    def __len__(self): return 1 if self.translator else 0

    @property
    def snippet(self):
        return self.translator.to_template_snippet() if self.translator else ""

    @property
    def template(self):
        return self.builder.template if self.builder else ""

    def verify(self, expected_rows_count=None, expected_result=None,
               tabular=False, debug=False, ignore_space=False):
        """Verify parsed test data against expected results."""

        if not self.builder:
            return False

        return self.builder.verify(
            expected_rows_count=expected_rows_count,
            expected_result=expected_result,
            tabular=tabular,
            debug=debug,
            ignore_space=ignore_space
        )

    def create_unittest(self):
        """Generate a Python unittest script for the current template and test data."""
        return self.builder.create_unittest() if self.builder else ""

    def create_pytest(self):
        """Generate a Python pytest script for the current template and test data."""
        return self.builder.create_pytest() if self.builder else ""

    def create_python_test(self):
        """Generate a Python test script for the current template and test data."""
        return self.builder.create_python_test() if self.builder else ""


class TabularTemplateBuilder:
    def __init__(
        self,
        user_data='',
        user_data_file='',
        test_data='',
        test_data_file='',
        column_divider='',
        column_count=0,
        column_widths=None,
        headers=None,
        header_rows=None,
        custom_header_text='',
        starting_from=None,
        ending_at=None,
        has_header_row=True,
        replacing_rules=None,
        author='',
        email='',
        company='',
        description='',
        test_script_file='',
        debug=False
    ):
        self.translator = TabularTranslator(
            user_data,
            column_divider=column_divider,
            column_count=column_count,
            column_widths=column_widths,
            headers=headers,
            header_rows=header_rows,
            custom_header_text=custom_header_text,
            has_header_row=has_header_row,
            starting_from=starting_from,
            ending_at=ending_at,
            replacing_rules=replacing_rules,
        )

        self.template_builder_args = dict(
            user_data=user_data,
            user_data_file=user_data_file,
            test_data=test_data,
            test_data_file=test_data_file,
            author=author,
            email=email,
            company=company,
            description=description,
            test_script_file=test_script_file,
            debug=debug
        )

        self.builder = None

        if self.translator:
            snippet = self.translator.to_template_snippet()
            self.template_builder_args.update(user_data=snippet)
            self.builder = TemplateBuilder(**self.template_builder_args)

    def __bool__(self): return bool(self.translator)

    def __len__(self): return 1 if self.translator else 0

    @property
    def snippet(self):
        return self.translator.to_template_snippet() if self.translator else ""

    @property
    def template(self):
        return self.builder.template if self.builder else ""

    def verify(self, expected_rows_count=None, expected_result=None,
               tabular=False, debug=False, ignore_space=False):
        """Verify parsed test data against expected results."""

        if not self.builder:
            return False

        return self.builder.verify(
            expected_rows_count=expected_rows_count,
            expected_result=expected_result,
            tabular=tabular,
            debug=debug,
            ignore_space=ignore_space
        )

    def create_unittest(self):
        """Generate a Python unittest script for the current template and test data."""
        return self.builder.create_unittest() if self.builder else ""

    def create_pytest(self):
        """Generate a Python pytest script for the current template and test data."""
        return self.builder.create_pytest() if self.builder else ""

    def create_python_test(self):
        """Generate a Python test script for the current template and test data."""
        return self.builder.create_python_test() if self.builder else ""


def get_textfsm_template(
    template_snippet: str,
    author: str = "",
    email: str = "",
    company: str = "",
    description: str = "",
) -> str:
    """
    Generate a TextFSM template from a snippet of user data.
    """
    builder = TemplateBuilder(
        user_data=template_snippet,
        author=author,
        email=email,
        company=company,
        description=description,
    )
    textfsm_template = builder.template
    return textfsm_template


