from textfsmgen import config

from textfsmgen.exceptions import PatternReferenceError, raise_exception
from textfsmgen.libs import file

import logging
logger = logging.getLogger(__file__)


class PatternRegistry(dict):
    """Registry of named regex patterns loaded from system and user YAML files."""

    def __init__(self):
        super().__init__()
        self.load_system()
        self.test_result = ''
        self.violated_format = ''

    def load_system(self):
        """Load system-defined patterns."""
        yaml_obj = file.safe_load_yaml(config.sys_ref_yaml_file)
        self.update(yaml_obj)

    def load_user(self, path, warn=True):
        """Load user-defined patterns and merge them into the registry."""
        try:
            yaml_obj = file.safe_load_yaml(path)
            if not yaml_obj:
                return

            if not isinstance(yaml_obj, dict):
                msg = f"File '{path}' must have a dictionary structure."
                raise PatternReferenceError(msg)

            for key, value in yaml_obj.items():
                if key not in self or key == "datetime":
                    self[key] = value
                else:
                    if warn:
                        logger.warning(
                            "%r already exists; skipping update for %r.", key, val
                        )
        except Exception as ex:
            raise_exception(ex, cls=PatternReferenceError)

    def has_conflict(self, dict_obj: dict) -> bool:
        sys_ref = file.safe_load_yaml(config.sys_ref_yaml_file)
        for name in dict_obj:
            if 'datetime' not in name and name in sys_ref:
                self.violated_format = (
                    f"Keyword '{name}' already exists in system_references.yaml."
                )
                return True
        return False

    def validate_yaml(self, content: str) -> Optional[bool | None]:
        """Validate YAML content against system-defined patterns."""
        try:
            yaml_obj = yaml.safe_load(content)
            if not yaml_obj:
                logger.warning("Skipping test: YAML content is empty or missing.")
                self.test_result = 'not_tested'
                return True

            if not isinstance(yaml_obj, dict):
                raise PatternReferenceError("YAML content must be a dictionary.")

            if self.has_conflict(yaml_obj):
                raise PatternReferenceError(self.violated_format)

            self.test_result = 'tested'
            return True
        except Exception as ex:
            raise_exception(ex, cls=PatternReferenceError)


class SymbolCls(dict):
    """
    Dictionary-like container for symbol references loaded from `symbols.yaml`.
    """

    def __init__(self):
        self._update_symbols()

    def _update_symbols(self):
        symbols = {
            'alphanum': '[0-9a-zA-Z]',
            'ampersand': '&',
            'apostrophe': "'",
            'asterisk': '\\*',
            'at_sign': '@',
            'backflash': '\\\\',
            'backtick': '`',
            'bar': '\\|',
            'binary': '[01]',
            'caret': '\\^',
            'circumflex_accent': '\\^',
            'colon': ':',
            'comma': ',',
            'digit': '[0-9]',
            'dollar_sign': '\\$',
            'dot': '\\.',
            'double_quote': '\\"',
            'equal': '=',
            'equal_sign': '=',
            'exclamation_mark': '!',
            'flash': '/',
            'full_stop': '\\.',
            'grave_accent': '`',
            'greater_than': '>',
            'greater_than_sign': '>',
            'hashtag': '#',
            'hex': '[0-9a-fA-F]',
            'hexadecimal': '[0-9a-fA-F]',
            'hyphen': '-',
            'left_angle': '<',
            'left_angle_sign': '<',
            'left_curly_bracket': '\\{',
            'left_parenthesis': '\\(',
            'left_round_bracket': '\\(',
            'left_square_bracket': '\\[',
            'less_than': '<',
            'less_than_sign': '<',
            'letter': '[a-zA-Z]',
            'low_line': '_',
            'minus': '-',
            'minus_sign': '-',
            'non_space': '[^ ]',
            'non_whitespace': '\\S',
            'octal': '[0-7]',
            'percent_sign': '%',
            'period': '\\.',
            'plus_sign': '\\+',
            'pound_sign': '#',
            'question_mark': '\\?',
            'quotation_mark': '\\"',
            'right_angle': '>',
            'right_angle_sign': '>',
            'right_curly_bracket': '\\}',
            'right_parenthesis': '\\)',
            'right_round_bracket': '\\)',
            'right_square_bracket': '\\]',
            'semicolon': ';',
            'single_quote': "'",
            'space': ' ',
            'star': '\\*',
            'tilde': '~',
            'underline': '_',
            'underscore': '_',
            'vertical_bar': '\\|',
            'whitespace': '\\s'
        }
        self.update(symbols)
