"""
Unit tests for the `textfsmgen.engine.doc` module.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest tests/unit/engine/doc
    or
    $ python -m pytest tests/unit/engine/doc
"""

def get_keywords(category: str = "singular"):
    """Return the list of keyword names for the given category."""
    keywords = {
        "singular": [
            "dot", "space", "ws", "whitespace", "digit",
            "letter", "alnum", "punct", "punctuation",
            "graph", "non_ws", "non_whitespace",
            "space_punct", "space_or_punct", "space_or_punctuation",
            "sop", "sp",
            "letter_punct", "letter_or_punct",
            "letter_or_punctuation", "lop", "lp",
        ],

        "plural": [
            "dots", "spaces", "wss", "whitespaces", "digits", "letters",
            "puncts", "punctuations", "non_wss", "non_whitespaces",
        ],

        "semantic": [
            "word", "mixed_word", "number", "mixed_number",
        ],

        "plural_semantic": [
            "words", "mixed_words",
        ],

        "group": [
            "letters_group", "digits_group", "number_group",
            "mixed_number_group", "puncts_group", "punctuations_group",
            "non_wss_group", "non_whitespaces_group",
        ],
    }

    return keywords.get(category, [])