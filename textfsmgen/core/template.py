"""
textfsmgen.core
===============

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
from textfsmgen.libs.utils import Printer
from textfsmgen.libs import datatype

from textfsmgen.exceptions import TemplateParsedLineError
from textfsmgen.exceptions import TemplateBuilderError
from textfsmgen.exceptions import TemplateBuilderInvalidFormat

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

    The TemplateBuilder class constructs parsing templates from user-provided
    data and test data, and can generate unit test scripts in multiple formats
    (unittest, pytest, or generic Python). It supports metadata such as author,
    company, and description, and provides verification utilities to ensure
    template correctness.

    Attributes
    ----------
    test_data : str
        Sample test data used to validate the generated template.
    user_data : str
        Raw user input data from which the template is derived.
    namespace : str
        Reference name for the template datastore.
    author : str, optional
        Author name. Defaults to an empty string.
    email : str, optional
        Author email. Defaults to an empty string.
    company : str, optional
        Company name. Defaults to an empty string.
    description : str, optional
        Description of the template. Defaults to an empty string.
    filename : str, optional
        File name to save the generated test script. Defaults to an empty string.
    variables : list
        List of variables extracted from the template.
    statements : list
        List of template statements.
    template : str
        The generated TextFSM template string.
    template_parser : TextFSM
        Instance of the TextFSM parser for the generated template.
    verified_message : str
        Message returned after successful verification.
    debug : bool
        Flag indicating whether to enable debug mode for template validation.
    bad_template : str
        Representation of an invalid or failed template.

    Methods
    -------
    prepare() -> None
        Prepare internal structures before building the template.
    build_template_comment() -> None
        Generate template comments for documentation.
    reformat() -> None
        Reformat the template for readability and consistency.
    build() -> None
        Build the final template from user and test data.
    show_debug_info(test_result=None, expected_result=None) -> None
        Display debug information comparing test results with expectations.
    verify(expected_rows_count=None, expected_result=None, debug=False) -> bool
        Verify the generated template against expected results.
    create_unittest() -> str
        Generate a Python unittest script for the template.
    create_pytest() -> str
        Generate a Python pytest script for the template.
    create_python_test() -> str
        Generate a generic Python test script snippet.

    Raises
    ------
    TemplateBuilderError
        Raised if the generated template is invalid.
    TemplateBuilderInvalidFormat
        Raised if `user_data` has an invalid format.
    """
    logger = logger

    def __init__(
        self,
        test_data='',
        user_data='',
        namespace='',
        author='',
        email='',
        company='',
        description='',
        filename='',
        debug=False
    ):
        self.test_data = text.list_to_text(test_data)
        self.user_data = text.list_to_text(user_data)
        self.namespace = str(namespace)
        self.author = str(author)
        self.email = str(email)
        self.company = str(company)
        self.description = text.list_to_text(description)
        self.filename = str(filename)
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

        This method processes each line in `self.user_data`, converts it into a
        `LineParser` object, and generates a normalized template statement. It
        also collects unique variables encountered during parsing.

        Processing steps
        ----------------
        - Strip trailing whitespace from each line.
        - Convert the line into a `LineParser` and extract its statement.
        - Normalize statement formatting:
            * Replace escaped `\\$$` with `$$`.
            * Replace `\\$$ ->` with `$$ ->`.
            * Replace `\\$` with `\\x24`.
        - Append the statement to `self.statements` (including empty ones).
        - Add variables from the parsed line to `self.variables`, ensuring
          uniqueness by matching both `name` and `pattern`.

        Returns
        -------
        None
            The method updates `self.statements` and `self.variables` in place.

        Raises
        ------
        TemplateParsedLineError
            If a line cannot be parsed into a valid `LineParser`.
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

    def build_template_comment(self) -> str:
        """
        Build a formatted template comment block.

        This method generates a standardized comment section for a TextFSM
        template, including metadata such as author, email, company, creation
        date, and description.

        Returns
        -------
        str
            A multi-line string containing the formatted template comment.

        Notes
        -----
        - The author defaults to `self.author` if provided, otherwise falls back
          to `self.company`.
        - The description is indented for readability.
        """
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

        This method restructures a template string by ensuring that states
        (lines beginning with an identifier) are separated by blank lines
        and that surrounding content is preserved.

        Parameters
        ----------
        template : str
            The raw template string to reformat.

        Returns
        -------
        str or None
            The reformatted template string, or None if the input is empty.

        Notes
        -----
        - States are identified using the regex pattern
          ``[\\r\\n]+[a-zA-Z]\\w*([\\r\\n]+|$)``.
        - Non-empty lines before and after states are preserved.
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

        This method prepares user data, constructs template statements and
        variables, and generates a formatted TextFSM template. It also validates
        the template by attempting to parse it with `TextFSM`.

        Workflow
        --------
        1. Reset `self.template`.
        2. Call `self.prepare()` to parse user data into statements and variables.
        3. If variables exist:
            - Build a template comment block.
            - Concatenate variables and statements into a bare template.
            - Ensure the template starts with a `Start` state.
            - Reformat both bare and full template for readability.
            - Attempt to parse the template with `TextFSM`.
        4. If parsing fails:
            - Raise `TemplateBuilderError` unless debug mode is enabled.
            - In debug mode, log the error and store the invalid template in
              `self.bad_template`.
        5. If no variables are found, raise `TemplateBuilderInvalidFormat`.

        Raises
        ------
        TemplateBuilderError
            Raised if the generated template is invalid and debug mode is disabled.
        TemplateBuilderInvalidFormat
            Raised if `user_data` does not contain any variables.
        """
        self.template = ""
        self.prepare()

        if not self.variables:
            raise TemplateBuilderInvalidFormat(
                "user_data does not have any assigned variable for template."
            )

        # Build comment and template sections
        comment = self.build_template_comment()
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

    def show_debug_info(
            self,
            test_result: Optional[list[dict] | None] = None,
            expected_result: Optional[list[dict] | None] = None,
            tabular: bool = False,
    ) -> None:
        """
        Display debug information for template verification.

        This method prints the template, test data, expected results, and
        actual test results in a structured format. It is primarily used
        for debugging and validation during template development.

        Parameters
        ----------
        test_result : list of dict, optional
            The actual test results to display. If provided, results are
            shown either as raw dictionaries or in tabular format.
        expected_result : list of dict, optional
            The expected results to display. If provided, they are printed
            alongside the test results.
        tabular : bool, default=False
            If True, format `test_result` as a tabular string using
            `get_data_as_tabular`. Otherwise, display raw dictionaries.

        Returns
        -------
        None
            This method prints debug information to stdout.

        Notes
        -----
        - Output is only shown if `self.verified_message` is set.
        - Uses a fixed width for labels to align output consistently.
        """
        if not self.verified_message:
            return

        width = 76
        printer = Printer()

        # Template
        printer.print("Template:".ljust(width))
        print(f"{self.template}\n")

        # Test Data
        printer.print("Test Data:".ljust(width))
        print(f"{self.test_data}\n")

        # Expected Result
        if expected_result is not None:
            printer.print("Expected Result:".ljust(width))
            print(f"{expected_result}\n")

        # Test Result
        if test_result is not None:
            printer.print("Test Result:".ljust(width))
            formatted_result = get_data_as_tabular(
                test_result) if tabular else test_result
            print(f"{formatted_result}\n")

        # Verified Message
        verified_msg = f"Verified Message: {self.verified_message}"
        printer.print(verified_msg.ljust(width))

    def verify(self, expected_rows_count=None, expected_result=None,
               tabular=False, debug=False, ignore_space=False):
        """
        Verify parsed test data against expected results.

        This method parses `self.test_data` using the current template and
        validates the output against optional expectations such as row count
        and expected results. It updates `self.verified_message` with details
        of the verification outcome.

        Parameters
        ----------
        expected_rows_count : int, optional
            Expected number of parsed rows. If provided, the actual row count
            is compared against this value.
        expected_result : list of dict, optional
            Expected parsed result. If provided, the actual parsed rows are
            compared against this list of dictionaries.
        tabular : bool, default=False
            If True, display test results in tabular format when debug output
            is enabled.
        debug : bool, default=False
            If True, print debug information using `show_debug_info`.
        ignore_space : bool, default=False
            If True, strip leading and trailing spaces from parsed data before
            comparison.

        Returns
        -------
        bool
            True if verification succeeds, False otherwise.

        Raises
        ------
        TemplateBuilderError
            Raised if an exception occurs during parsing.
        """

        if not self.test_data:
            self.verified_message = 'test_data is empty.'
            if debug:
                self.show_debug_info()
            return False

        is_verified = True
        try:
            rows = self.template_parser.ParseTextToDicts(self.test_data)
            if not rows:
                self.verified_message = 'There is no record after parsed.'
                if debug:
                    self.show_debug_info()
                return False

            # Validate row count
            if expected_rows_count is not None:
                actual_count = len(rows)
                chk = expected_rows_count == actual_count
                is_verified &= chk
                index = int(chk)
                verified_messages = [
                    f"Parsed-row-count is {actual_count} while expected-row-count is {expected_rows_count}.",
                    f"Parsed-row-count and expected-row-count are {expected_rows_count}."
                ]
                self.verified_message = verified_messages[index]

            # Validate expected result
            if expected_result is not None:
                rows_to_compare = datatype.clean_list_of_dicts(rows) if ignore_space else rows
                chk = rows_to_compare == expected_result
                is_verified &= chk
                index = int(chk)
                result_msgs = [
                    "Parsed result and expected result are different.",
                    "Parsed result and expected result are matched."
                ]
                result_msg = result_msgs[index]
                self.verified_message = f"{self.verified_message}\n{result_msg}".strip()

            # Default success message
            if is_verified and not self.verified_message:
                self.verified_message = 'Parsed result has record(s).'

            # Debug output
            if debug:
                self.show_debug_info(
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

        This method formats a test script using the provided format string
        and the current template/test data. If no test data is available,
        a `TemplateBuilderError` is raised. Optionally, the generated script
        is written to a file if `self.filename` is set.

        Parameters
        ----------
        test_script_fmt : str
            A format string containing placeholders for `template` and `test_data`.
        error : str
            Error message to raise if `self.test_data` is missing.

        Returns
        -------
        str
            The generated test script as a string.

        Raises
        ------
        TemplateBuilderError
            If `self.test_data` is empty or missing.
        """

        if not self.test_data:
            raise TemplateBuilderError(error)

        test_script = test_script_fmt.format(
            template=enclose_string(self.template),
            test_data=enclose_string(self.test_data)
        )

        if self.filename:
            file.write(self.filename, test_script)
        return test_script

    def create_unittest(self):
        """
        Generate a Python unittest script for the current template and test data.

        This method builds a unittest script that uses `TextFSM` to parse
        `self.test_data` with the current template. The generated script
        includes a single test case that verifies parsing produces a
        non-negative number of rows.

        Returns
        -------
        str
            The generated unittest script as a string.

        Raises
        ------
        TemplateBuilderError
            Raised if `self.test_data` is missing or empty.
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
        ''')
        error = 'Cannot create Python unittest script without test data.'
        test_script = self.create_test_script(test_script_fmt, error)
        return test_script

    def create_pytest(self):
        """
        Generate a Python pytest script for the current template and test data.

        This method builds a pytest script that uses `TextFSM` to parse
        `self.test_data` with the current template. The generated script
        includes a single test case that verifies parsing produces a
        non-negative number of rows.

        Returns
        -------
        str
            The generated pytest script as a string.

        Raises
        ------
        TemplateBuilderError
            Raised if `self.test_data` is missing or empty.
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
        ''')
        error = "Cannot create Python pytest script without test data."
        test_script = self.create_test_script(test_script_fmt, error)
        return test_script

    def create_python_test(self):
        """
        Generate a Python snippet script for the current template and test data.

        This method builds a python snippet script that uses `TextFSM` to parse
        `self.test_data` with the current template. The generated script
        includes a single test case that verifies parsing produces a
        non-negative number of rows.

        Returns
        -------
        str
            The generated python snippet script as a string.

        Raises
        ------
        TemplateBuilderError
            Raised if `self.test_data` is missing or empty.
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
            
            # function call
            test_textfsm_template(template, test_data)
        ''')
        error = 'Cannot create Python snippet script without test data.'
        test_script = self.create_test_script(test_script_fmt, error)
        return test_script


def get_textfsm_template(
    template_snippet: str,
    author: str = "",
    email: str = "",
    company: str = "",
    description: str = "",
) -> str:
    """
    Generate a TextFSM template from a snippet of user data.

    This function creates a `TemplateBuilder` instance using the provided
    template snippet and optional metadata (author, email, company, description).
    It returns the generated TextFSM template as a string.

    Parameters
    ----------
    template_snippet : str
        Raw user data snippet to be converted into a TextFSM template.
    author : str, optional
        Name of the template author. Defaults to an empty string.
    email : str, optional
        Email address of the template author. Defaults to an empty string.
    company : str, optional
        Company name associated with the template. Defaults to an empty string.
    description : str, optional
        Description of the template. Defaults to an empty string.

    Returns
    -------
    str
        The generated TextFSM template.

    Raises
    ------
    TemplateBuilderError
        If the template cannot be built due to invalid input or parsing errors.
    TemplateBuilderInvalidFormat
        If the provided snippet has an invalid format.
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


