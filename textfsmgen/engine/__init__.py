"""
textfsmgen.engine.__init__
==========================

Initialization for the TextFSM parsing engine.
"""

from .category import (
    CategoryLineTranslator,
    CategoryLinesTranslator
)

from .common import (
    get_line_position_by,
    get_fixed_line_snippet,
    sanitize_identifier,
    apply_replacements,
    apply_fallback_replacements
)

from .doc import (
    OperationDoc,
    ExplanationDoc
)

from .line import LineData

from .tabular import (
    TabularTranslator,
    VarColumnTabularTranslator,
    ParsedTable,
)

from .translate import (
    PatternTranslator,
    DigitTranslator,
    DigitsTranslator,
    NumberTranslator,
    MixedNumberTranslator,
    LetterTranslator,
    LettersTranslator,
    AlnumTranslator,
    PunctTranslator,
    PunctsTranslator,
    PunctsGroupTranslator,
    GraphTranslator,
    WordTranslator,
    WordsTranslator,
    MixedWordTranslator,
    MixedWordsTranslator,
    NonWSTranslator,
    NonWSSTranslator,
    NonWSSGroupTranslator,
    TokenAggregator,

    validate_translator_value,
    make_translator,
)


__all__ = [
    # Category Translators
    "CategoryLineTranslator",
    "CategoryLinesTranslator",

    # Common Utilities
    "get_line_position_by",
    "get_fixed_line_snippet",
    "sanitize_identifier",
    "apply_replacements",
    "apply_fallback_replacements",

    # Documentation Helpers
    "OperationDoc",
    "ExplanationDoc",

    # Line Data
    "LineData",

    # Tabular Translators
    "TabularTranslator",
    "VarColumnTabularTranslator",
    "ParsedTable",

    # Pattern Translators
    "PatternTranslator",
    "DigitTranslator",
    "DigitsTranslator",
    "NumberTranslator",
    "MixedNumberTranslator",
    "LetterTranslator",
    "LettersTranslator",
    "AlnumTranslator",
    "PunctTranslator",
    "PunctsTranslator",
    "PunctsGroupTranslator",
    "GraphTranslator",
    "WordTranslator",
    "WordsTranslator",
    "MixedWordTranslator",
    "MixedWordsTranslator",
    "NonWSTranslator",
    "NonWSSTranslator",
    "NonWSSGroupTranslator",
    "TokenAggregator",

    # Translator Helpers
    "validate_translator_value",
    "make_translator",
]
