"""
Unit tests for the `textfsmgen.gpdiff.NDiffBaseText` class.

Usage
-----
Run pytest in the project root to execute these tests:
    $ pytest tests/unit/gpdiff/test_ndiff_base_text_class.py
    or
    $ python -m pytest tests/unit/gpdiff/test_ndiff_base_text_class.py
"""

import pytest

from textfsmgen.gpdiff import NDiffBaseText


class TestNDiffBaseText:
    """
    Unit tests for the NDiffBaseText class.

    Covers initialization, extending nodes, list readjustments,
    type comparison, and factory creation.
    """

    @pytest.mark.parametrize(
        "txt, is_ready, exp_len, exp_common, exp_changed, exp_lst, exp_lst_other",
        [
            ("", False, 0, False, False, [], []),
            ("  unchanged_item", True, 1, True, False, ["unchanged_item"], []),
            ("- removed_item", True, 1, False, True, ["removed_item"], []),
            ("+ added_item", True, 1, False, True, [], ["added_item"]),
        ],
    )
    def test_init(
        self, txt, is_ready, exp_len, exp_common, exp_changed, exp_lst, exp_lst_other
    ):
        """Test initialization and basic properties of NDiffBaseText."""
        node = NDiffBaseText(txt)
        assert bool(node) == is_ready
        assert len(node) == exp_len
        assert node.is_common == exp_common
        assert node.is_changed == exp_changed
        assert node.lst == exp_lst
        assert node.lst_other == exp_lst_other

    @pytest.mark.parametrize(
        "txt, ext_txt, exp_lst, exp_lst_other",
        [
            ("  unchanged_a", "  unchanged_b", ["unchanged_a", "unchanged_b"], []),
            ("  unchanged_a", "+ added_a", ["unchanged_a"], []),
            ("  unchanged_a", "- removed_a", ["unchanged_a"], []),
            ("+ added_a", "+ added_b", [], ["added_a", "added_b"]),
            ("+ added_a", "- removed_a", ["removed_a"], ["added_a"]),
            ("+ added_a", "  unchanged_a", [], ["added_a"]),
            ("- removed_a", "- removed_b", ["removed_a", "removed_b"], []),
            ("- removed_a", "+ added_a", ["removed_a"], ["added_a"]),
            ("- removed_a", "  unchanged_a", ["removed_a"], []),
        ],
    )
    def test_extend(self, txt, ext_txt, exp_lst, exp_lst_other):
        """Test extending one node with another."""
        node = NDiffBaseText.do_factory_create(txt)
        ext_node = NDiffBaseText.do_factory_create(ext_txt)
        node.extend(ext_node)
        assert node.lst == exp_lst
        assert node.lst_other == exp_lst_other

    @pytest.mark.parametrize(
        "txt, exp_before, new_lst, exp_after",
        [
            ("  unchanged", ["unchanged"], ["line4", "", "item_b"], ["line4", "item_b"]),
            ("- removed", ["removed"], ["line4", "", "item_b"], ["line4", "item_b"]),
            ("+ added", [], ["item_a", "", "item_b"], ["item_a", "item_b"]),
        ],
    )
    def test_readjust_lst(self, txt, exp_before, new_lst, exp_after):
        """Test readjusting the primary list of text fragments."""
        node = NDiffBaseText(txt)
        assert node.lst == exp_before
        node.readjust_lst(*new_lst)
        assert node.lst == exp_after

    @pytest.mark.parametrize(
        "txt, exp_before, new_lst, exp_after",
        [
            ("  unchanged", [], ["item_a", "", "item_b"], ["item_a", "item_b"]),
            ("- removed", [], ["item_a", "", "item_b"], ["item_a", "item_b"]),
            ("+ added", ["added"], ["item_a", "", "item_b"], ["item_a", "item_b"]),
        ],
    )
    def test_readjust_lst_other(self, txt, exp_before, new_lst, exp_after):
        """Test readjusting the secondary list of text fragments."""
        node = NDiffBaseText(txt)
        assert node.lst_other == exp_before
        node.readjust_lst_other(*new_lst)
        assert node.lst_other == exp_after

    @pytest.mark.parametrize(
        "txt, other_txt, exp_same",
        [
            ("  unchanged_a", "  unchanged_b", True),
            ("  unchanged_a", "+ added_a", False),
            ("  unchanged_a", "- removed_a", False),
            ("+ added_a", "+ added_b", True),
            ("+ added_a", "- removed_a", True),
            ("+ added_a", "  unchanged_a", False),
            ("- removed_a", "- removed_b", True),
            ("- removed_a", "+ added_a", True),
            ("- removed_a", "  unchanged_a", False),
        ],
    )
    def test_is_same_type(self, txt, other_txt, exp_same):
        """Test type comparison between two nodes."""
        node = NDiffBaseText.do_factory_create(txt)
        other_node = NDiffBaseText.do_factory_create(other_txt)
        assert node.is_same_type(other_node) == exp_same

    @pytest.mark.parametrize(
        "txt, exp_class",
        [
            ("  unchanged_item", "NDiffCommonText"),
            ("+ added_item", "NDiffChangedText"),
            ("- removed_item", "NDiffChangedText"),
        ],
    )
    def test_factory_create(self, txt, exp_class):
        """Test factory creation of nodes based on input text."""
        node = NDiffBaseText.do_factory_create(txt)
        assert type(node).__name__ == exp_class
