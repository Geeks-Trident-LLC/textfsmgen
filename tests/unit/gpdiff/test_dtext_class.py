"""
Unit tests for the `textfsmgen.gpdiff.DText` class.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest tests/unit/gpdiff/test_dtext_class.py
    or
    $ python -m pytest tests/unit/gpdiff/test_dtext_class.py
"""

import pytest
from textfsmgen.engine.diff import DText


class TestDText:
    """
    Unit tests for the DText class.

    Covers initialization, adding text, concatenation,
    grouping, general text, snippet, and pattern generation.
    """

    @pytest.mark.parametrize(
        "txt, exp_lead, exp_trail, exp_first",
        [
            ("", "", "", ""),
            (" \t ", " \t ", "", " \t "),
            ("Hello Python", "", "", "Hello Python"),
            ("  Hello Python", "  ", "", "  Hello Python"),
            ("Hello Python  ", "", "  ", "Hello Python  "),
            (" \t Hello Python  ", " \t ", "  ", " \t Hello Python  "),
        ],
    )
    def test_init(self, txt, exp_lead, exp_trail, exp_first):
        """Test initialization of DText."""
        node = DText(txt)
        assert node.leading == exp_lead
        assert node.trailing == exp_trail
        assert node.first_text == exp_first

    def test_add(self):
        """Test adding text fragments."""
        node = DText("apple")
        node.add("peach")
        assert "peach" in node.lst

    def test_concatenate(self):
        """Test concatenation of text fragments."""
        node = DText("Hello")
        node.concatenate(" ")
        node.concatenate("Python")
        assert node.first_text == "Hello Python"

    @pytest.mark.parametrize(
        "txt, add_txt, exp_identical, exp_closed",
        [
            ("Hello Python", "Hello Python", True, True),
            ("Hello Python", "Hello   Python", False, False),
            ("Hello Python", "  Hello Python", False, True),
        ],
    )
    def test_identical(self, txt, add_txt, exp_identical, exp_closed):
        """Test identical and closed-to-identical checks."""
        node = DText(txt)
        node.add(add_txt)
        assert node.is_identical == exp_identical
        assert node.is_closed_to_identical == exp_closed

    @pytest.mark.parametrize(
        "txt, add_lst, exp",
        [
            ("text", [], [["text"]]),
            ("text", ["add text"], [["add", "text"]]),
            ("text", ["add \t text"], [["add", "text"]]),
            ("text", ["add text", "new text"], [["add", "new", "text"]]),
            ("add text", ["new text"], [["add", "new"], [" "], ["text"]]),
            ("add   text", ["new text"], [["add", "new"], [" ", "   "], ["text"]]),
            ("add text", ["new   text"], [["add", "new"], [" ", "   "], ["text"]]),
            ("add text", ["new text", "add a text"], [["add", "new"], [" "], ["a", "text"]]),
            ("add text", ["new    text", "add a text"], [["add", "new"], [" ", "    "], ["a", "text"]]),
        ],
    )
    def test_to_group(self, txt, add_lst, exp):
        """Test grouping of text fragments."""
        node = DText(txt)
        for a in add_lst:
            node.add(a)
        assert node.to_group() == exp

    @pytest.mark.parametrize(
        "txt, add_lst, exp",
        [
            ("text", [], "text"),
            ("text", ["add text"], "add "),
            ("add text", ["add \t text"], "add\t text"),
            ("add text", ["add    text"], "add  text"),
        ],
    )
    def test_to_general_text(self, txt, add_lst, exp):
        """Test general text generation."""
        node = DText(txt)
        for a in add_lst:
            node.add(a)
        assert node.to_general_text() == exp

    @pytest.mark.parametrize(
        "txt, exp",
        [
            ("yellow blue", "yellow blue"),
            ("yellow    blue", "yellow    blue"),
            ("yellow \t blue", "yellow \t blue"),
            ("yellow .....\tblue", "yellow .....\tblue"),
            ("yellow .....\t  blue", "yellow .....\t  blue"),
            ("yellow .....\t\tblue", "yellow .....\t\tblue"),
            (
                "test paren: word()",
                "test paren: word()"
            ),
            (
                "test nothing repeat ** invalid qualifier",
                "test nothing repeat ** invalid qualifier"
            ),
            (
                "test nothing repeat ++ invalid qualifier",
                "test nothing repeat ++ invalid qualifier"
            ),
            (
                "^(?i) testing regex escape",
                "^(?i) testing regex escape"
            ),
        ],
    )
    def test_get_snippet(self, txt, exp):
        """Test snippet generation."""
        node = DText(txt)
        assert node.get_snippet() == exp

    @pytest.mark.parametrize(
        "txt, exp",
        [
            ("yellow blue", "yellow blue"),
            ("yellow    blue", "yellow +blue"),
            ("yellow \t blue", r"yellow\s+blue"),
            ("yellow .....\tblue", r"yellow \.{2,}\sblue"),
            ("yellow .....\t  blue", r"yellow \.{2,}\s+blue"),
            ("yellow .....\t\tblue", r"yellow \.{2,}\s+blue"),
            (
                "test paren: word()",
                r"test paren: word\(\)"
            ),
            (
                "test nothing repeat ** invalid qualifier",
                r"test nothing repeat \*{2,} invalid qualifier"
            ),
            (
                "test nothing repeat ++ invalid qualifier",
                r"test nothing repeat \+{2,} invalid qualifier"
            ),
            (
                "^(?i) testing regex escape",
                r"\^\(\?i\) testing regex escape"
            ),
        ],
    )
    def test_get_pattern(self, txt, exp):
        """Test regex pattern generation."""
        node = DText(txt)
        assert node.get_pattern() == exp