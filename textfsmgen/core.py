"""
textfsmgen.core
===============

Core functionality for the TextFSM Generator.

This module provides the foundational logic for building and validating
TextFSM templates. It defines the primary classes and functions that
transform user-provided snippets into structured parsing templates,
support test execution, and integrate with configuration options.

Purpose
-------
- Parse and process user input into TextFSM templates.
- Provide template generation and validation utilities.
- Support integration with test data and configuration settings.
- Serve as the central engine for CLI and GUI workflows.

Notes
-----
- Acts as the backbone of the TextFSM Generator package.
- Designed for extensibility: additional parsing strategies or test
  frameworks can be integrated via `TemplateBuilder`.
- Errors are surfaced with descriptive messages to aid debugging.
"""

import re
from datetime import datetime
from textwrap import indent
from textfsm import TextFSM
from io import StringIO

from regexapp import LinePattern
from regexapp.core import enclose_string

from genericlib import get_data_as_tabular
from genericlib import Printer
from genericlib import MiscObject
from genericlib.text import dedent_and_strip
import genericlib.file as file

from textfsmgen.exceptions import TemplateParsedLineError
from textfsmgen.exceptions import TemplateBuilderError
from textfsmgen.exceptions import TemplateBuilderInvalidFormat

from textfsmgen.config import edition

import logging
logger = logging.getLogger(__file__)


class ParsedLine:
    """
    Represent and parse a single line into template format.

    The `ParsedLine` class encapsulates the logic for interpreting a line
    of text as part of a template definition. It supports parsing operators,
    handling comments, preserving raw text, and extracting variables.

    Attributes
    ----------
    text : str
        Raw text content associated with the line.
    line : str
        Original line data before parsing.
    template_op : str
        Template operator applied to the line.
    ignore_case : bool
        Flag indicating whether parsing should be case-insensitive.
    is_comment : bool
        True if the line is a comment, otherwise False.
    comment_text : str
        The comment text if the line is marked as a comment.
    is_kept : bool
        True if the line should be preserved as-is, otherwise False.
    kept_text : str
        The preserved text when `is_kept` is True.
    variables : list
        List of variables extracted from the line.

    Methods
    -------
    is_empty() -> bool
        Return True if the line contains no data, otherwise False.
    is_a_word() -> bool
        Return True if the text represents a single word, otherwise False.
    is_not_containing_letter() -> bool
        Return True if the line contains no alphabetic characters, otherwise False.
    build() -> None
        Construct the internal representation of the parsed line.
    get_statement() -> str
        Return the formatted statement derived from the parsed line.

    Raises
    ------
    TemplateParsedLineError
        Raised if the line cannot be parsed due to invalid format.
    """
    def __init__(self, text):
        self.text = str(text)
        self.line = ''
        self.template_op = ''
        self.ignore_case = False
        self.is_comment = False
        self.comment_text = ''
        self.is_kept = False
        self.kept_text = ''
        self.variables = list()
        self.build()

    @property
    def is_empty(self) -> bool:
        """
        Check whether the line is empty.

        This property evaluates the current line and determines if it
        contains only whitespace or no characters at all.

        Returns
        -------
        bool
            True if the line is empty or consists solely of whitespace,
            False otherwise.
        """
        return not bool(self.line.strip())

    @property
    def is_a_word(self) -> bool:
        """
        Check whether the text represents a single word.

        This property evaluates the `text` attribute and determines if it
        consists of exactly one word. A valid word is defined as starting
        with an alphabetic character and followed by zero or more
        alphanumeric or underscore characters.

        Returns
        -------
        bool
            True if the text is a single word, False otherwise.
        """
        return bool(re.match(r'^[A-Za-z]\w*$', self.text.strip()))

    @property
    def is_not_containing_letter(self) -> bool:
        """
        Check whether the line contains no alphabetic characters.

        This property evaluates the current line and determines if it
        consists entirely of non-alphanumeric characters. Empty lines
        are explicitly excluded and return False.

        Returns
        -------
        bool
            True if the line contains no alphabetic characters (only
            digits, symbols, or whitespace), False otherwise.
        """
        if self.is_empty:
            return False
        return bool(re.match(r'[^a-z0-9]+$', self.line, flags=re.I))

    def get_statement(self) -> str:
        """
        Construct the template statement for the current line.

        This method interprets the line according to its type (empty,
        comment, preserved text, single word, or regex pattern) and
        generates a formatted statement suitable for building a template.
        It applies validation, whitespace handling, and optional template
        operators.

        Returns
        -------
        str
            A formatted template statement. Returns an empty string if
            the line is empty.

        Notes
        -----
        - Empty lines return an empty string.
        - Comment lines return the associated comment text.
        - Preserved lines return the kept text as-is.
        - Single words return the raw text.
        - Regex patterns are validated and adjusted for case-insensitivity,
          anchors, and optional template operators.
        - Variables extracted from the line are stored in `self.variables`.
        """
        if self.is_empty:
            return ""

        if self.is_comment:
            return self.comment_text

        if self.is_kept:
            return self.kept_text

        if self.is_a_word:
            return self.text

        pat_obj = LinePattern(self.line, ignore_case=self.ignore_case)

        if pat_obj.variables:
            self.variables = pat_obj.variables[:]
            statement = pat_obj.statement
        else:
            try:
                re.compile(self.line)
                if re.search(r'\s', self.line):
                    statement = pat_obj
                else:
                    if '(' in self.line and self.line.endswith(')'):
                        statement = pat_obj if not pat_obj.endswith(')') else self.line
                    else:
                        statement = self.line
            except Exception as ex:     # noqa
                statement = pat_obj

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

    def build(self) -> None:
        """
        Parse the line and reapply formatting for template construction.

        This method interprets the raw `text` attribute, extracts template
        operators, and applies flags for case-insensitivity, comments, or
        preserved lines. It normalizes operator names, validates syntax,
        and prepares internal attributes (`template_op`, `line`, `comment_text`,
        `kept_text`) for later use in template generation.

        Workflow
        --------
        1. Split the text into template content and operator (if present).
        2. Normalize operator names (e.g., `norecord` → `NoRecord`,
           `clearall` → `ClearAll`).
        3. Handle compound operators (e.g., `next.norecord`, `error.clear`).
        4. Apply flags:
           - `ignore_case__` → mark line as case-insensitive.
           - `comment__`     → mark line as a comment.
           - `keep__`        → preserve line as-is.
        5. Construct `comment_text` or `kept_text` when applicable.
        6. Raise `TemplateParsedLineError` if the format is invalid.

        Attributes Set
        --------------
        template_op : str
            Normalized template operator string (if present).
        line : str
            Parsed line content without flags.
        ignore_case : bool
            True if the line should be case-insensitive.
        is_comment : bool
            True if the line is a comment.
        is_kept : bool
            True if the line should be preserved as-is.
        comment_text : str
            Formatted comment text (if applicable).
        kept_text : str
            Formatted preserved text (if applicable).

        Raises
        ------
        TemplateParsedLineError
            If the line format is invalid or cannot be parsed.
        """
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
            text = lst[0].rstrip()
        else:
            text = self.text

        pat = r"^(?P<flag>(ignore_case|comment|keep)__+ )?(?P<line>.*)"
        match = re.match(pat, text, flags=re.I)
        if match:
            value = match.group("flag") or ""
            flag = value.lower().strip().rstrip("_")
            self.ignore_case = flag == "ignore_case"
            self.is_comment = flag == "comment"
            self.is_kept = flag == "keep"
            self.line = match.group("line") or ""

            if self.is_comment:
                prefix = "  " if value.count("_") == 2 else ""
                self.comment_text = f"{prefix}# {self.line}"

            if self.is_kept:
                self.kept_text = '  ^{}'.format(self.line.strip().lstrip('^'))

        else:
            raise TemplateParsedLineError(f"Invalid format - {self.text!r}")


class TemplateBuilder:
    """Create template and test script

    Attributes
    ----------
    test_data (str): a test data.
    user_data (str): a user data.
    namespace (str): a reference name for template datastore.
    author (str): author name.  Default is empty.
    email (str): author email.  Default is empty.
    company (str): company name.  Default is empty.
    description (str): a description about template.  Default is empty.
    filename (str): a saving file name for a generated test script to file name.
    variables (list): a list of variable.
    statements (list): a list of template statement.
    template (str): a generated template.
    template_parser (TextFSM): instance of TextFSM.
    verified_message (str): a verified message.
    debug (bool): a flag to check bad template.
    bad_template (str): a bad generated template.

    Methods
    -------
    TemplateBuilder.convert_to_string(data) -> str
    prepare() -> None
    build_template_comment() -> None
    reformat() -> None
    build() -> None
    show_debug_info(test_result=None, expected_result=None) -> None
    verify(expected_rows_count=None, expected_result=None, debug=False) -> bool
    create_unittest() -> str
    create_pytest() -> str
    create_python_test() -> str

    Raises
    ------
    TemplateBuilderError: will raise exception if a created template is invalid.
    TemplateBuilderInvalidFormat: will raise exception if
            user_data has invalid format.
    """
    logger = logger

    def __init__(self, test_data='', user_data='', namespace='',
                 author='', email='', company='', description='',
                 filename='', debug=False):
        self.test_data = TemplateBuilder.convert_to_string(test_data)
        self.raw_user_data = TemplateBuilder.convert_to_string(user_data)
        self.user_data = ''
        self.namespace = str(namespace)
        self.author = str(author)
        self.email = str(email)
        self.company = str(company)
        self.description = TemplateBuilder.convert_to_string(description)
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

    @classmethod
    def convert_to_string(cls, data):
        """convert data to string

        Parameters
        ----------
        data (str, list): a data

        Returns
        -------
        str: a text
        """
        if isinstance(data, list):
            return '\n'.join(str(item) for item in data)
        else:
            return str(data)

    def prepare(self):
        """prepare data to build template"""

        pattern = r"# \S+commercial use: generated by[^\r\n]+[\r\n]+" \
                  r"# Created Date: [^\r\n]+[\r\n]+#{4,} *[\r\n]+"

        if re.match(pattern, self.raw_user_data.lstrip()):
            # excluding commercial use text in user data
            self.user_data = re.sub(pattern, "", self.raw_user_data.lstrip())
        else:
            self.user_data = self.raw_user_data

        for line in self.user_data.splitlines():
            line = line.rstrip()

            parsed_line = ParsedLine(line)
            statement = parsed_line.get_statement()
            if statement.endswith(r'\$$'):
                statement = '{}$$'.format(statement[:-3])
            elif r'\$$ -> ' in statement:
                statement = statement.replace(r'\$$ -> ', '$$ -> ')
            statement = statement.replace(r'\$', r'\x24')

            if statement:
                self.statements.append(statement)
            else:
                self.statements and self.statements.append(statement)

            if parsed_line.variables:
                for v in parsed_line.variables:
                    is_identical = False
                    for item in self.variables:
                        if v.name == item.name and v.pattern == item.pattern:
                            is_identical = True
                            break
                    not is_identical and self.variables.append(v)

    def build_template_comment(self):
        """return a template comment including created by, email, company,
        created date, and description"""

        fmt = '# Template is generated by template {} Edition'
        fmt1 = '# Created by  : {}'
        fmt2 = '# Email       : {}'
        fmt3 = '# Company     : {}'
        fmt4 = '# Created date: {:%Y-%m-%d}'
        fmt5 = '# Description : {}'

        author = self.author or self.company
        lst = ['#' * 80, fmt.format(edition)]
        author and lst.append(fmt1.format(author))
        self.email and lst.append(fmt2.format(self.email))
        self.company and lst.append(fmt3.format(self.company))
        lst.append(fmt4.format(datetime.now()))
        if self.description:
            description = indent(self.description, '#     ').strip('# ')
            lst.append(fmt5.format(description))
        lst.append('#' * 80)
        return '\n'.join(lst)

    def reformat(self, template):   # noqa
        if not template:
            return

        lst = []
        pat = r'[\r\n]+[a-zA-Z]\w*([\r\n]+|$)'
        start = 0
        m = None
        for m in re.finditer(pat, template):
            before_match = m.string[start:m.start()]
            state = m.group().strip()
            if before_match.strip():
                for line in before_match.splitlines():
                    if line.strip():
                        lst.append(line)
            lst.append('')
            lst.append(state)
            start = m.end()
        else:
            if m and lst:
                after_match = m.string[m.end():]
                if after_match.strip():
                    for line in after_match.splitlines():
                        if line.strip():
                            lst.append(line)

        reformat_template = '\n'.join(lst)
        return reformat_template

    def build(self):
        """build template

        Raises
        ------
        TemplateBuilderError: will raise exception if a created template is invalid.
        TemplateBuilderInvalidFormat: will raise exception if
                user_data has invalid format.
        """
        self.template = ''
        self.prepare()
        if self.variables:
            comment = self.build_template_comment()
            variables = '\n'.join(v.value for v in self.variables)
            template_def = '\n'.join(self.statements)
            if not template_def.strip().startswith('Start'):
                template_def = f"Start\n{template_def}"
            bare_template = f"{variables}\n\n{template_def}"
            template = f"{comment}\n{bare_template}"
            self.bare_template = self.reformat(bare_template)
            self.template = self.reformat(template)

            try:
                stream = StringIO(self.template)
                self.template_parser = TextFSM(stream)
            except Exception as ex:
                error = '{}: {}'.format(type(ex).__name__, ex)
                if not self.debug:
                    raise TemplateBuilderError(error)
                else:
                    self.logger.error(error)
                    self.bad_template = '# {}\n{}'.format(error, self.template)
                    self.template = ''
        else:
            msg = 'user_data does not have any assigned variable for template.'
            raise TemplateBuilderInvalidFormat(msg)

    def show_debug_info(self, test_result=None, expected_result=None,
                        tabular=False):
        """show debug information
        
        Parameters
        ----------
        test_result (list): a list of dictionary.
        expected_result (list): a list of dictionary.
        tabular (bool): show result in tabular format.  Default is False.
        """
        if self.verified_message:
            width = 76
            printer = Printer()
            printer.print('Template:'.ljust(width))
            print(self.template + '\n')
            printer.print('Test Data:'.ljust(width))
            print(self.test_data + '\n')
            if expected_result is not None:
                printer.print('Expected Result:'.ljust(width))
                print(f'{expected_result}\n')
            if test_result is not None:
                printer.print('Test Result:'.ljust(width))
                new_result = get_data_as_tabular(test_result) if tabular else test_result
                print(f'{new_result}\n')

            verified_msg = 'Verified Message: {}'.format(self.verified_message)
            printer.print(verified_msg.ljust(width))

    def verify(self, expected_rows_count=None, expected_result=None,
               tabular=False, debug=False, ignore_space=False):
        """verify test_data via template
        
        Parameters
        ----------
        expected_rows_count (int): total number of rows.
        expected_result (list): a list of dictionary.
        tabular (bool): show result in tabular format.  Default is False.
        debug (bool): True will show debug info.  Default is False.
        ignore_space(bool): True will strip any leading or trailing space in data.
                Default is False.

        Returns
        -------
        bool: True if it is verified, otherwise False.

        Raises
        ------
        TemplateBuilderError: show exception if there is error during parsing text.
        """
        if not self.test_data:
            self.verified_message = 'test_data is empty.'
            debug and self.show_debug_info()
            return False

        is_verified = True
        try:
            rows = self.template_parser.ParseTextToDicts(self.test_data)
            if not rows:
                self.verified_message = 'There is no record after parsed.'
                debug and self.show_debug_info()
                return False

            if expected_rows_count is not None:
                rows_count = len(rows)
                chk = expected_rows_count == rows_count
                is_verified &= chk
                if not chk:
                    fmt = 'Parsed-row-count is {} while expected-row-count is {}.'
                    self.verified_message = fmt.format(rows_count, expected_rows_count)
                else:
                    fmt = 'Parsed-row-count and expected-row-count are {}.'
                    self.verified_message = fmt.format(expected_rows_count)

            if expected_result is not None:
                rows = MiscObject.cleanup_list_of_dict(rows) if ignore_space else rows
                chk = rows == expected_result
                is_verified &= chk

                if chk:
                    msg = 'Parsed result and expected result are matched.'
                else:
                    msg = 'Parsed result and expected result are different.'

                msg = '{}\n{}'.format(self.verified_message, msg,)
                self.verified_message = msg.strip()

            if is_verified and not self.verified_message:
                self.verified_message = 'Parsed result has record(s).'

            if debug:
                self.show_debug_info(test_result=rows,
                                     expected_result=expected_result,
                                     tabular=tabular)

            return is_verified

        except Exception as ex:
            error = '{}: {}'.format(type(ex).__name__, ex)
            raise TemplateBuilderError(error)

    def create_unittest(self):
        """return a Python unittest script

        Raises
        ------
        TemplateBuilderError: raise exception if test_data is empty.
        """

        if not self.test_data:
            error = 'CANT create Python unittest script without test data.'
            raise TemplateBuilderError(error)

        fmt = dedent_and_strip("""
            {docstring}
            
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
        """)

        docstring = ('Python unittest script is generated by '
                     'template {} Edition').format(edition)
        script = fmt.format(
            docstring='"""{}"""'.format(docstring),
            template=enclose_string(self.template),
            test_data=enclose_string(self.test_data)
        )
        if self.filename:
            file.write(self.filename, script)
        return script

    def create_pytest(self):
        """return a Python pytest script

        Raises
        ------
        TemplateBuilderError: raise exception if test_data is empty.
        """

        if not self.test_data:
            error = 'CANT create Python pytest script without test data.'
            raise TemplateBuilderError(error)

        fmt = dedent_and_strip("""
            {docstring}

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
        """)

        docstring = ('Python pytest script is generated by '
                     'template {} edition').format(edition)
        script = fmt.format(
            docstring='"""{}"""'.format(docstring),
            template=enclose_string(self.template),
            test_data=enclose_string(self.test_data)
        )

        if self.filename:
            file.write(self.filename, script)
        return script

    def create_python_test(self):
        """return a Python snippet script

        Raises
        ------
        TemplateBuilderError: raise exception if test_data is empty.
        """

        if not self.test_data:
            error = 'CANT create Python snippet script without test data.'
            raise TemplateBuilderError(error)

        fmt = dedent_and_strip(r'''
            {docstring}

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

        docstring = ('Python snippet script is generated by '
                     'template {} edition').format(edition)
        script = fmt.format(
            docstring='"""{}"""'.format(docstring),
            template=enclose_string(self.template),
            test_data=enclose_string(self.test_data)
        )

        if self.filename:
            file.write(self.filename, script)
        return script


def get_textfsm_template(template_snippet, author='', email='',
                         company='', description=''):
    builder = TemplateBuilder(user_data=template_snippet, author=author,
                              email=email, company=company, description=description)
    textfsm_tmpl = builder.template
    return textfsm_tmpl


def verify(template_snippet, test_data,
           expected_rows_count=None, expected_result=None,
           ignore_space=True):
    builder = TemplateBuilder(user_data=template_snippet, test_data=test_data)
    is_verified = builder.verify(expected_rows_count=expected_rows_count,
                                 expected_result=expected_result,
                                 ignore_space=ignore_space)
    return is_verified
