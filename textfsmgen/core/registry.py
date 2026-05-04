"""
textfsmgen.core.registry
========================

Registry for keyword-to-pattern mappings used by the TextFSM generator.
"""  # noqa

import re

from textfsmgen.exceptions import PatternReferenceError, raise_exception
from textfsmgen.libs import file

from textfsmgen.libs import pattern

import logging

logger = logging.getLogger(__file__)


class PatternRegistry(dict):
    """Registry of named regex patterns loaded from system and user YAML files."""

    def __init__(self):
        super().__init__()
        self.load_system()
        self.test_result = ""
        self.violated_format = ""

    def load_system(self):
        """Load system-defined patterns."""
        for attr in dir(pattern.PATTERN):
            val = getattr(pattern.PATTERN, attr)
            if re.fullmatch("[A-Z][A-Z_]*[A-Z]", attr) and isinstance(val, str):
                self[attr.lower()] = val

    def load(self, path, warn=True):
        """Load user-defined patterns and merge them into the registry."""
        try:
            yaml_obj = file.safe_load_yaml(path)
            if not yaml_obj:
                return

            if not isinstance(yaml_obj, dict):
                msg = f"File '{path}' must have a dictionary structure."
                raise PatternReferenceError(msg)

            for key, value in yaml_obj.items():
                valid_pat = pattern.check_pattern(value)
                if not valid_pat:
                    if warn:
                        logger.warning(valid_pat)
                    continue

                if key not in self:
                    self[key] = value
                else:
                    if warn:
                        logger.warning(
                            "%r already exists; skipping update for %r.", key, value
                        )
        except Exception as ex:
            raise_exception(ex, cls=PatternReferenceError)

    def has_keyword(self, key):
        """Return True if the keyword or its resolved form exists."""
        key = str(key).lower()

        if key in self:
            return True

        resolved = pattern.resolve_keyword(key)
        return bool(resolved)

    def resolve_pattern(self, key, default=None):
        """Return the pattern for the keyword, falling back if needed."""
        key = str(key).lower()

        if key in self:
            return self[key]

        return pattern.resolve_pattern(key, default=default)


class SymbolCls(dict):
    """
    Dictionary-like container for symbol references loaded from `symbols.yaml`.
    """

    def __init__(self):
        super().__init__()
        self._update_symbols()

    def _update_symbols(self):
        symbols = {
            "alphanum": "[0-9a-zA-Z]",
            "ampersand": "&",
            "apostrophe": "'",
            "asterisk": "\\*",
            "at_sign": "@",
            "backflash": "\\\\",
            "backtick": "`",
            "bar": "\\|",
            "binary": "[01]",
            "caret": "\\^",
            "circumflex_accent": "\\^",
            "colon": ":",
            "comma": ",",
            "digit": "[0-9]",
            "dollar_sign": "\\$",
            "dot": "\\.",
            "double_quote": '\\"',
            "equal": "=",
            "equal_sign": "=",
            "exclamation_mark": "!",
            "flash": "/",
            "full_stop": "\\.",
            "grave_accent": "`",
            "greater_than": ">",
            "greater_than_sign": ">",
            "hashtag": "#",
            "hex": "[0-9a-fA-F]",
            "hexadecimal": "[0-9a-fA-F]",
            "hyphen": "-",
            "left_angle": "<",
            "left_angle_sign": "<",
            "left_curly_bracket": "\\{",
            "left_parenthesis": "\\(",
            "left_round_bracket": "\\(",
            "left_square_bracket": "\\[",
            "less_than": "<",
            "less_than_sign": "<",
            "letter": "[a-zA-Z]",
            "low_line": "_",
            "minus": "-",
            "minus_sign": "-",
            "non_space": "[^ ]",
            "non_whitespace": "\\S",
            "octal": "[0-7]",
            "percent_sign": "%",
            "period": "\\.",
            "plus_sign": "\\+",
            "pound_sign": "#",
            "question_mark": "\\?",
            "quotation_mark": '\\"',
            "right_angle": ">",
            "right_angle_sign": ">",
            "right_curly_bracket": "\\}",
            "right_parenthesis": "\\)",
            "right_round_bracket": "\\)",
            "right_square_bracket": "\\]",
            "semicolon": ";",
            "single_quote": "'",
            "space": " ",
            "star": "\\*",
            "tilde": "~",
            "underline": "_",
            "underscore": "_",
            "vertical_bar": "\\|",
            "whitespace": "\\s",
        }
        self.update(symbols)
