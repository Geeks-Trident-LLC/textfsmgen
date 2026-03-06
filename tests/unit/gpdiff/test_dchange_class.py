"""
Unit tests for the `textfsmgen.gpdiff.DChange` class.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest tests/unit/gpdiff/test_dchange_class.py
    or
    $ python -m pytest tests/unit/gpdiff/test_dchange_class.py
"""

import pytest
from textfsmgen.engine.diff import DChange


class TestDChangeClass:
    """
    Unit tests for the DChange class.

    This suite verifies initialization, adding text fragments,
    and snippet generation for different input cases.
    """

    @pytest.mark.parametrize(
        "txt, var, exp",
        [
            # non-empty init
            ("Hello Python", "v1", ("Hello Python", "v1", False, ["Hello Python"])),

            # empty init
            ("  ", "v1", ("  ", "v1", True, [])),
            ("\t ", "v1", ("\t ", "v1", True, [])),
        ],
    )
    def test_init(self, txt, var, exp):
        """
        Test initialization of DChange.

        Parameters
        ----------
        txt : str
            Input text fragment.
        var : str
            Variable name.
        exp : tuple
            Expected values (text, var, is_empty, lst).
        """
        exp_txt, exp_var, exp_empty, exp_lst = exp
        node = DChange(txt, var)
        assert node.text == exp_txt
        assert node.var == exp_var
        assert node.is_empty is exp_empty
        assert node.lst == exp_lst

    @pytest.mark.parametrize(
        "node, add_txt, exp_empty_before, exp_empty_after, exp_in_lst",
        [
            # add valid text
            (DChange("Hello Python", "v1"), "new text", False, False, True),

            # add empty text
            (DChange("Hello Python", "v1"), "", False, True, False),
            (DChange("Hello Python", "v1"), "  ", False, True, False),
            (DChange("Hello Python", "v1"), " \t  ", False, True, False),
        ],
    )
    def test_add(self, node, add_txt, exp_empty_before, exp_empty_after, exp_in_lst):
        """
        Test adding text fragments to DChange.

        Parameters
        ----------
        node : DChange
            Instance of DChange.
        add_txt : str
            Text fragment to add.
        exp_empty_before : bool
            Expected is_empty before adding.
        exp_empty_after : bool
            Expected is_empty after adding.
        exp_in_lst : bool
            Whether the added text should appear in lst.
        """
        assert node.is_empty is exp_empty_before
        node.add(add_txt)
        assert node.is_empty is exp_empty_after
        assert (add_txt in node.lst) == exp_in_lst

    @pytest.mark.parametrize(
        "data, expect",
        [
            (("a", "case01", ["B", "z"]), "letter(var_case01)"),
            (("1", "case02", ["2", "3"]), "digit(var_case02)"),
            (("a", "case03", ["b", "1"]), "alphabet_numeric(var_case03)"),
            (("-", "case04", ["+", "*"]), "punct(var_case04)"),
            (("a", "case05", ["1", "*"]), "graph(var_case05)"),
            (("a", "case06", ["1", "\xc8"]), "non_ws(var_case06)"),

            (("abc", "case11", ["B", "xyz"]), "letters(var_case11)"),
            (("123", "case12", ["2", "123"]), "digits(var_case12)"),
            (("--", "case13", ["++", "***"]), "puncts(var_case13)"),
            (("abc", "case14", ["1", "\xc8"]), "non_wss(var_case14)"),

            (("1.1", "case21", ["2.2", "3.3"]), "number(var_case21)"),
            (("1.1", "case22", ["-2.2", "3.3"]), "mixed_number(var_case22)"),

            (("abc123", "case31", ["cde", "xyz"]), "word(var_case31)"),
            # (("var_abc", "case32", ["cde", "xyz"]), "mixed_word(var_case32)"),

            (("a1 b1", "case41", ["b1", "c1"]), "words(var_case41)"),
            (("a1", "case42", ["b1 d2", "c1"]), "words(var_case42)"),
            (("a1 b1", "case43", ["b1 d2", "x3 y3"]), "phrase(var_case43)"),

            (("a.1 b1", "case51", ["b1", "c1"]), "mixed_words(var_case51)"),
            (("a1", "case52", ["b.1 d2", "c1"]), "mixed_words(var_case52)"),
            (("a1 b2", "case53", ["b.1 d2", "1 4"]), "mixed_phrase(var_case53)"),

            (("-- ++", "v61", ["==", ".."]), "puncts_group(var_v61)"),
            (("-- ++", "v62", ["== ++", ".. ::"]), "puncts_phrase(var_v62)"),

            (("a1\xc8", "v71", ["b1 d2", "c1 123"]), "non_wss_group(var_v71)"),
            (("a1\xc8 --", "v71", ["b1 d2", "c1 123"]), "non_wss_phrase(var_v71)"),

            # add or_empty in snippet if diff change has or add empty string
            (("", "case81", ["B", "z"]), "letter(var_case81, or_empty)"),
            (("a", "case82", ["", "z"]), "letter(var_case82, or_empty)"),
        ],
    )
    def test_get_snippet(self, data, expect):
        """
        Test snippet generation for DChange.

        Parameters
        ----------
        data : tuple
            Input data (text, var, other fragments).
        expect : str
            Expected snippet string.
        """
        txt, var, other = data
        node = DChange(txt, var)
        for item in other:
            node.add(item)

        assert node.get_snippet() == expect

    @pytest.mark.parametrize(
        "data, expect",
        [
            (("a", "case01", ["B", "z"]), r"(?P<case01>[a-zA-Z])"),
            (("1", "case02", ["2", "3"]), r"(?P<case02>\d)"),
            # (("a", "case03", ["b", "1"]), "alphabet_numeric(var_case03)"),
            (("-", "case04", ["+", "*"]), r"(?P<case04>[\x21-\x2f\x3a-\x40\x5b-\x60\x7b-\x7e])"),
            (("a", "case05", ["1", "*"]), r"(?P<case05>[\x21-\x7e])"),
            (("a", "case06", ["1", "\xc8"]), r"(?P<case06>\S)"),

            (("abc", "case11", ["B", "xyz"]), r"(?P<case11>[a-zA-Z]+)"),
            (("123", "case12", ["2", "123"]), r"(?P<case12>\d+)"),
            (("--", "case13", ["++", "***"]), r"(?P<case13>[\x21-\x2f\x3a-\x40\x5b-\x60\x7b-\x7e]+)"),
            (("abc", "case14", ["1", "\xc8"]), r"(?P<case14>\S+)"),

            (("1.1", "case21", ["2.2", "3.3"]), r"(?P<case21>\d*[.]?\d+)"),
            (("1.1", "case22", ["-2.2", "3.3"]), r"(?P<case22>[+\(\[\$-]?(\d+([,:/-]\d+)*)?[.]?\d+[\]\)%a-zA-Z]*)"),

            (("abc123", "case31", ["cde", "xyz"]), r"(?P<case31>[a-zA-Z0-9_]*[a-zA-Z][a-zA-Z0-9_]*)"),
            # (("var_abc", "case32", ["cde", "xyz"]), r"(?P<case32>[\x21-\x7e]*[a-zA-Z0-9][\x21-\x7e]*)"),

            (("a1 b1", "case41", ["b1", "c1"]), r"(?P<case41>[a-zA-Z0-9_]*[a-zA-Z][a-zA-Z0-9_]*(\s+[a-zA-Z0-9_]*[a-zA-Z][a-zA-Z0-9_]*)*)"),
            (("a1", "case42", ["b1 d2", "c1"]), r"(?P<case42>[a-zA-Z0-9_]*[a-zA-Z][a-zA-Z0-9_]*(\s+[a-zA-Z0-9_]*[a-zA-Z][a-zA-Z0-9_]*)*)"),
            (("a1 b1", "case43", ["b1 d2", "x3 y3"]), r"(?P<case43>[a-zA-Z0-9_]*[a-zA-Z][a-zA-Z0-9_]*(\s+[a-zA-Z0-9_]*[a-zA-Z][a-zA-Z0-9_]*)+)"),
            #
            (("a.1 b1", "case51", ["b1", "c1"]), r"(?P<case51>[\x21-\x7e]*[a-zA-Z0-9][\x21-\x7e]*(\s+[\x21-\x7e]*[a-zA-Z0-9][\x21-\x7e]*)*)"),
            (("a1", "case52", ["b.1 d2", "c1"]), r"(?P<case52>[\x21-\x7e]*[a-zA-Z0-9][\x21-\x7e]*(\s+[\x21-\x7e]*[a-zA-Z0-9][\x21-\x7e]*)*)"),
            (("a1 b2", "case53", ["b.1 d2", "1 4"]), r"(?P<case53>[\x21-\x7e]*[a-zA-Z0-9][\x21-\x7e]*(\s+[\x21-\x7e]*[a-zA-Z0-9][\x21-\x7e]*)+)"),

            (("-- ++", "v61", ["==", ".."]), r"(?P<v61>[\x21-\x2f\x3a-\x40\x5b-\x60\x7b-\x7e]+(\s+[\x21-\x2f\x3a-\x40\x5b-\x60\x7b-\x7e]+)*)"),
            (("-- ++", "v62", ["== ++", ".. ::"]), r"(?P<v62>[\x21-\x2f\x3a-\x40\x5b-\x60\x7b-\x7e]+(\s+[\x21-\x2f\x3a-\x40\x5b-\x60\x7b-\x7e]+)+)"),

            (("a1\xc8", "v71", ["b1 d2", "c1 123"]), r"(?P<v71>\S+(\s+\S+)*)"),
            (("a1\xc8 --", "v71", ["b1 d2", "c1 123"]), r"(?P<v71>\S+(\s+\S+)+)"),

            # add or_empty in snippet if diff change has or add empty string
            (("", "case81", ["B", "z"]), "(?P<case81>([a-zA-Z])|)"),
            (("a", "case82", ["", "z"]), r"(?P<case82>([a-zA-Z])|)"),
        ],
    )
    def test_get_pattern(self, data, expect):
        """
        Test pattern generation for DChange.

        Parameters
        ----------
        data : tuple
            Input data (text, var, other fragments).
        expect : str
            Expected pattern string.
        """
        txt, var, other = data
        node = DChange(txt, var)
        for item in other:
            node.add(item)
        assert node.get_pattern() == expect
