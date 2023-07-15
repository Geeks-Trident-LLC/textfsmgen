"""Module containing the logic for template builder."""

import re
from datetime import datetime
from textwrap import indent
from textfsm import TextFSM
from io import StringIO
from textwrap import dedent

from regexpro import LinePattern
from regexpro.core import enclose_string

from genericlib import get_data_as_tabular
from genericlib import Printer
from genericlib import MiscObject

from templatepro.exceptions import TemplateParsedLineError
from templatepro.exceptions import TemplateBuilderError
from templatepro.exceptions import TemplateBuilderInvalidFormat
from templatepro.exceptions import NoUserTemplateSnippetError
from templatepro.exceptions import NoTestDataError

from templatepro.config import edition
from templatepro.config import version

import logging
logger = logging.getLogger(__file__)


def save_file(filename, content):
    """Save data to file

    Parameters
    ----------
    filename (str): a file name
    content (str): a file content
    """
    filename = str(filename).strip()
    if filename:
        with open(filename, 'w') as stream:
            stream.write(content)


class ParsedLine:
    """Parse line to template format

    Attributes
    ----------
    text (str): a data.
    line (str): a line data.
    template_op (str): template operator.
    ignore_case (bool): a case-insensitive flag.
    is_comment (bool): an indicator for comment.
    comment_str (str): a comment text.
    is_kept (bool): an indicator to keep AS-IS.
    kept_str (str): a kept text.
    variables (list): a list of variables.

    Properties
    ----------
    is_empty (bool): True if a line does not have data, otherwise False.
    is_a_word (bool): True if text is a single word, otherwise False.
    is_not_containing_letter (bool): True if line is not containing any letter,
            otherwise, False.

    Methods
    -------
    build() -> None
    get_statement() -> str

    Raises
    -------
    TemplateParsedLineError: raise exception if there is invalid format for parsing.
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
    def is_empty(self):
        """return True if a line is empty"""
        return not bool(self.line.strip())

    @property
    def is_a_word(self):
        """return True if text is a single word"""
        return bool(re.match(r'[a-z]\w+$', self.text.rstrip(), re.I))

    @property
    def is_not_containing_letter(self):
        """return True if a line doesn't contain any alphanum"""
        if self.is_empty:
            return False

        return bool(re.match(r'[^a-z0-9]+$', self.line, re.I))

    def get_statement(self):
        """return a statement for building template

        Returns
        -------
        str: a statement for template
        """
        if self.is_empty:
            return ''

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

        statement = statement.replace('(?i)^', '^(?i)')
        spacer = '  ' if statement.startswith('^') else '  ^'
        statement = '{}{}'.format(spacer, statement)
        if statement.endswith('$') and not statement.endswith(r'\$'):
            statement = '{}$'.format(statement)
        if self.template_op:
            statement = '{} -> {}'.format(statement, self.template_op)
        return statement

    def build(self):
        """parse line to reapply for building template"""
        lst = self.text.rsplit(' -> ', 1)
        if len(lst) == 2:
            tmpl_op = lst[-1].strip()
            first, *remaining = tmpl_op.split(' ', 1)

            tbl = {'norecord': 'NoRecord', 'clearall': 'ClearAll'}
            if '.' in first:
                pat = r'(?P<lop>next|continue|error)\.' \
                      r'(?P<rop>norecord|record|clearall|clear)$'
                match = re.match(pat, first, re.I)
                if match:
                    lop = match.group('lop').title()
                    rop = match.group('rop').title()
                    rop = tbl.get(rop.lower(), rop)
                    op = '{}.{}'.format(lop, rop)
                else:
                    op = first
                tmpl_op = '{} {}'.format(op, ''.join(remaining))
            else:
                pat = r'(next|continue|error|norecord|record|clearall|clear)$'
                if re.match(pat, first, re.I):
                    op = first.title()
                    op = tbl.get(op.lower(), op)
                else:
                    op = first
                tmpl_op = '{} {}'.format(op, ''.join(remaining))

            self.template_op = tmpl_op.strip()
            text = lst[0].rstrip()
        else:
            text = self.text

        pat = r'^(?P<flag>(ignore_case|comment|keep)__+ )?(?P<line>.*)'
        match = re.match(pat, text, re.I)
        if match:
            value = match.group('flag') or ''
            flag = value.lower().strip().rstrip('_')
            self.ignore_case = flag == 'ignore_case'
            self.is_comment = flag == 'comment'
            self.is_kept = flag == 'keep'
            self.line = match.group('line') or ''

            if self.is_comment:
                prefix = '  ' if value.count('_') == 2 else ''
                self.comment_text = '{}# {}'.format(prefix, self.line)

            if self.is_kept:
                self.kept_text = '  ^{}'.format(self.line.strip().lstrip('^'))

        else:
            error = 'Invalid format - {!r}'.format(self.text)
            raise TemplateParsedLineError(error)


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
    other_options (dict): other options for Pro or Enterprise edition.
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
                 filename='', debug=False,
                 **other_options):
        self.test_data = TemplateBuilder.convert_to_string(test_data)
        self.user_data = TemplateBuilder.convert_to_string(user_data)
        self.namespace = str(namespace)
        self.author = str(author)
        self.email = str(email)
        self.company = str(company)
        self.description = TemplateBuilder.convert_to_string(description)
        self.filename = str(filename)
        self.other_options = other_options
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

        fmt = """
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
        """
        fmt = dedent(fmt).strip()

        docstring = ('Python unittest script is generated by '
                     'template {} Edition').format(edition)
        script = fmt.format(
            docstring='"""{}"""'.format(docstring),
            template=enclose_string(self.template),
            test_data=enclose_string(self.test_data)
        )

        save_file(self.filename, script)
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

        fmt = """
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
        """

        fmt = dedent(fmt).strip()

        docstring = ('Python pytest script is generated by '
                     'template {} edition').format(edition)
        script = fmt.format(
            docstring='"""{}"""'.format(docstring),
            template=enclose_string(self.template),
            test_data=enclose_string(self.test_data)
        )

        save_file(self.filename, script)
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

        fmt = r'''
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
        '''

        fmt = dedent(fmt).strip()

        docstring = ('Python snippet script is generated by '
                     'template {} edition').format(edition)
        script = fmt.format(
            docstring='"""{}"""'.format(docstring),
            template=enclose_string(self.template),
            test_data=enclose_string(self.test_data)
        )

        save_file(self.filename, script)
        return script


class NonCommercialUseCls:
    def __init__(self, user_data, is_line=False, is_multi_test_data=False, is_tabular=False):
        self.user_data = str(user_data)
        self.is_line = is_line
        self.is_multi_test_data = is_multi_test_data
        self.is_tabular = is_tabular
        self.factory = None
        self.process()
        self.comment = (f"# Non-commercial use: generated by TemplateApp v{version} "
                        f"(geekstrident.com)\n"
                        f"# Created Date: {datetime.now():%Y-%m-%d %H:%M}\n"
                        "################################")

    def process(self):
        if not self.user_data.strip():
            raise NoUserTemplateSnippetError("Please provide valid user data.")
        self.factory = TemplateBuilder(user_data=self.user_data)

    def get_generated_template(self):
        template = f"{self.comment}\n{self.factory.bare_template}"
        return template

    def get_code_snippet(self):
        func = self.get_snippet_v2 if self.is_multi_test_data else self.get_snippet_v1
        code_snippet = func()
        return code_snippet

    def get_snippet_v1(self):
        script = dedent("""
            from textfsm import TextFSM
            from io import StringIO

            def test_generated_template(template, test_data):
              parser = TextFSM(StringIO(template))
              rows = parser.ParseTextToDicts(test_data)
              total_rows_count = len(rows)
              if total_rows_count:
                print('Total-rows-count: %s' % total_rows_count)
                print(rows)
              else:
                print('??? Generated template failed to parse test data ???')

            template = '''...'''    # replace actual template in ellipsis
            test_data = '''...'''   # replace actual data in ellipsis
            test_generated_template(template, test_data)
            ################################""").strip()
        code_snippet = f"{self.comment}\n{script}"
        return code_snippet

    def get_snippet_v2(self):
        script = dedent("""
            from textfsm import TextFSM
            from io import StringIO

            def test_generated_template(template, test_data):
              split_pat = r'(?i)\\r?\\n? *<<separator>> *\\r?\\n?'
              blocks = re.split(split_pat, test_data)
              for i, block in enumerate(blocks, 1):
                parser = TextFSM(StringIO(template))
                rows = parser.ParseTextToDicts(block)
                total_rows_count = len(rows)
                print('##### block #%s #####' % i)
                if total_rows_count:
                  print('Total-rows-count: %s' % total_rows_count)
                  print(rows)
                else:
                  print('??? Generated template failed to parse data-block #%s ???' % i)

            template = '''...'''    # replace actual template in ellipsis
            test_data = '''...'''   # replace actual data in ellipsis
            test_generated_template(template, test_data)
            ################################""").strip()
        code_snippet = f"{self.comment}\n{script}"
        return code_snippet

    def get_test_result(self, test_data):
        test_data = str(test_data)
        if not test_data:
            raise NoTestDataError("Please provide valid test data.")
        func = self.get_tresult_v2 if self.is_multi_test_data else self.get_tresult_v1
        test_result = func(test_data)
        return test_result

    def get_tresult_v1(self, test_data):
        template = self.get_generated_template()
        parser = TextFSM(StringIO(template))
        rows = parser.ParseTextToDicts(test_data)
        total_rows_count = len(rows)
        if total_rows_count:
            result = get_data_as_tabular(rows) if self.is_tabular else rows
            stream = StringIO()
            print(f"Total-rows-count: {total_rows_count}", file=stream)
            print(result, file=stream)
            stream.seek(0)
            test_result = stream.read()
            return test_result
        else:
            return "??? Generated template failed to parse test data ???"

    def get_tresult_v2(self, test_data):
        template = self.get_generated_template()
        split_pat = r"(?i)\r?\n? *<<separator>> *\r?\n?"
        blocks = re.split(split_pat, test_data)
        stream = StringIO()
        for i, block in enumerate(blocks, 1):
            parser = TextFSM(StringIO(template))
            rows = parser.ParseTextToDicts(block)
            total_rows_count = len(rows)
            print(f"##### block #{i} #####", file=stream)
            if not total_rows_count:
                print(f"??? Generated template failed to parse data-block #{i} ???", file=stream)
                continue

            result = get_data_as_tabular(rows) if self.is_tabular else rows
            print(f"Total-rows-count: {total_rows_count}\n{result}", file=stream)

        stream.seek(0)
        test_result = stream.read()
        return test_result
