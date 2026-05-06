"""
textfsmgen.tools.__init__
=========================

High‑level utilities for generating, explaining, and suggesting TextFSMGen snippets.
"""

from .explain import SnippetExplanation
from .samples import SamplesGenerator
from .suggester import (SnippetSuggester, IterateSuggester, ScriptBuilder)
from .token import (WhitespaceSnippet, TokenSnippet, LineSnippet,
                    create_pattern_statement)

__all__ = [
    "SnippetExplanation",
    "SamplesGenerator",

    "SnippetSuggester",
    "IterateSuggester",
    "ScriptBuilder",

    "TokenSnippet",
    "WhitespaceSnippet",
    "LineSnippet",
    "create_pattern_statement"
]
