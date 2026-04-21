"""
Unit tests for the `textfsmgen.tools.explain.SnippetExplanation` class.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest tests/unit/tools/test_token_explanation.py
    or
    $ python -m pytest tests/unit/tools/test_token_explanation.py
"""

from textfsmgen.tools.explain import SnippetExplanation
from textfsmgen.libs.text import dedent_and_strip

def test_basic():
    expected = dedent_and_strip("""
        +------------------------------------------+
        |               word(var_v1)               |
        +------------------------------------------+
        Pattern:   r"(?P<v1>[a-zA-Z0-9_]*[a-zA-Z][a-zA-Z0-9_]*)"
        Operation: match one word containing alphanumeric or underscore characters
                   with at least one alphabetic character.
        Explanation:
            lst = ['dummy', 'other_dummy']
        
        Evaluating:
            [bool(re.fullmatch(pattern, item)) for item in lst]
        
        Produces:
            [True, True]
    """)
    node = SnippetExplanation(
        "word(var_v1)",
        ["dummy", "other_dummy"]
    )
    assert node.explanation == expected


def test_with_optional():
    expected = dedent_and_strip(r"""
        +------------------------------------------+
        |       optional_mixed_words(var_v1)       |
        +------------------------------------------+
        Pattern:   r"(?P<v1>([\x21-\x7e]*[a-zA-Z0-9][\x21-\x7e]*(\s+[\x21-\x7e]*[a-zA-Z0-9][\x21-\x7e]*)*)?)"
        Operation: match zero or more mixed words containing alphanumeric or
                   punctuation characters, each with at least one alphanumeric
                   character, separated by one or more whitespace characters.
        Explanation:
            lst = ['dummy', 'today is good day.']
        
        Evaluating:
            [bool(re.fullmatch(pattern, item)) for item in lst]
        
        Produces:
            [True, True]
    """)
    node = SnippetExplanation(
        "optional_mixed_words(var_v1)",
        ["dummy", "today is good day."]
    )
    assert node.explanation == expected


def test_with_or_empty_flag():
    expected = dedent_and_strip(r"""
        +--------------------------------------------------------------+
        |           optional_non_wss_group(var_v3, or_empty)           |
        +--------------------------------------------------------------+
        Pattern:   r"(?P<v3>(\S+(\s+\S+)*)?)"
        Operation: match zero or more sequences of non‑whitespace characters, each
                   separated by one or more whitespace characters.
        Explanation:
            lst = ['dummy', '', "lst = {'a': 1}"]
        
        Evaluating:
            [bool(re.fullmatch(pattern, item)) for item in lst]
        
        Produces:
            [True, True, True]
    """)
    node = SnippetExplanation(
        "optional_non_wss_group(var_v3, or_empty)",
        ["dummy", "", "lst = {'a': 1}"],
    )
    assert node.explanation == expected


def test_failure_incorrect_list_of_data():
    expected = dedent_and_strip(r"""
        +------------------------------------------+
        |         words(var_v3, or_empty)          |
        +------------------------------------------+
        Pattern:   r"(?P<v3>([a-zA-Z0-9_]*[a-zA-Z][a-zA-Z0-9_]*(\s+[a-zA-Z0-9_]*[a-zA-Z][a-zA-Z0-9_]*)*)?)"
        Operation: match zero or more words containing alphanumeric or underscore
                   characters, each with at least one alphabetic character, separated
                   by one or more whitespace characters.
        Explanation:
            lst = ['dummy', '', 'Connection* 10:']
        
        Evaluating:
            [bool(re.fullmatch(pattern, item)) for item in lst]
        
        +------------------------------------------+
        |               Failed Match               |
        +------------------------------------------+
        Expected:
            [True, True, True]
        Received:
            [True, True, False]
    """)
    node = SnippetExplanation(
        "words(var_v3, or_empty)",
        ["dummy", "", "Connection* 10:"],
    )
    assert node.explanation == expected


def test_failure_because_of_keyword_token():
    expected = "Provided snippet is empty.  Cannot explain."
    node = SnippetExplanation(
        "",
        ["dummy", ],
    )
    assert node.explanation == expected


def test_failure_undefined_keyword():
    expected = dedent_and_strip("""
        +------------------------------------------+
        |    Undefined 'dummy_keyword(var_v0)'     |
        +------------------------------------------+
        Undefined 'dummy_keyword' keyword.  Request technical support for feature extension.
    """)
    node = SnippetExplanation(
        "dummy_keyword(var_v0)",
        ["dummy", ],
    )
    assert node.explanation == expected


def test_failure_invalid_keyword_syntax():
    expected = dedent_and_strip("""
        +------------------------------------------+
        |               word(var_v0                |
        +------------------------------------------+
        Provided snippet does not match the expected keyword format:
        
          [<quantity>_]<keyword>[_<group>]([<param>])
        
        Where:
          <quantity> — one of: optional, some, 3, one_to_three, ...
          <keyword>  — one of: word, digit, number, mixed_word, non_wss, ...
          <group>    — the literal string "group"
          <param>    — empty or a comma‑separated list of text values
        
        Examples:
          1. optional_word(var_v0)
             Matches zero or one word and captures variable "v0".
        
          2. some_words(var_v1)
             Matches at least one whitespace‑separated word and captures "v1".
        
          3. one_to_three_words(var_v2)
             Matches one to three whitespace‑separated words and captures "v2".
    """)
    node = SnippetExplanation(
        "word(var_v0",
        ["dummy", ],
    )
    assert node.explanation.strip() == expected
