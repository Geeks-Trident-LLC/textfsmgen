"""
Unit tests for the `textfsmgen.libs.pattern` module.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest tests/unit/libs/pattern
    or
    $ python -m pytest tests/unit/libs/pattern
"""

space = " "
spaces = " +"
ws = r"\s"
wss = r"\s+"
whitespace = ws
whitespaces = wss

dot = "."
letter = "[a-zA-Z]"
letters = "[a-zA-Z]+"

digit = r"\d"
digits = r"\d+"

alnum = "[a-zA-Z0-9]"
alnums = f"{alnum}+"
graph = r"[\x21-\x7e]"
graphs = rf"{graph}+"

non_ws = r"\S"
non_wss = r"\S+"

punct = r"[\x21-\x2f\x3a-\x40\x5b-\x60\x7b-\x7e]"
puncts = f"{punct}+"
punctuation = punct
punctuations = puncts

number = r"\d*[.]?\d+"
mixed_number = r"[+\(\[\$-]?(\d+([,:/-]\d+)*)?[.]?\d+[\]\)%a-zA-Z]*"
word = r"[a-zA-Z0-9_]*[a-zA-Z][a-zA-Z0-9_]*"
mixed_word = r"[\x21-\x7e]*[a-zA-Z0-9][\x21-\x7e]*"

space_or_punct = r"[ \x21-\x2f\x3a-\x40\x5b-\x60\x7b-\x7e]"
letter_or_punct = r"[a-zA-Z\x21-\x2f\x3a-\x40\x5b-\x60\x7b-\x7e]"
spaces_or_puncts = rf"{space_or_punct}+"
letters_or_puncts = rf"{letter_or_punct}+"

sep = r"\s+"