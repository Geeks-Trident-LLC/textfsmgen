"""
textfsmgen.gpdiff
=================

Module for computing and representing differences between TextFSM‑generated
templates, parsed outputs, or line snippets.

This module provides utilities to:
- Compare two sets of data or parsed results.
- Highlight differences in line structure, tokenization, or normalized snippets.
- Generate human‑readable diff outputs for debugging and validation.
- Support automated testing by verifying expected vs. actual parsing results.

Notes
-----
- Differences are normalized using `TranslatedPattern` to ensure consistent
  handling of digits, numbers, and whitespace.
- Intended primarily for unit testing and debugging TextFSM template generation.
- Diff results are diagnostic only and do not modify the original inputs.

"""

import re
from typing import Tuple

from typing import List
from difflib import ndiff
from itertools import combinations

from regexapp import TextPattern
from regexapp import ElementPattern
from regexapp import LinePattern

from genericlib import STRING, PATTERN, Misc, NUMBER, INDEX
from genericlib import Text
from textfsmgen.gp import TranslatedPattern
from textfsmgen.exceptions import RuntimeException


class NDiffBaseText:
    """
    Base class for representing normalized diff text nodes.

    This class provides common functionality for handling diff lines
    in a normalized representation. It distinguishes between:
    - Common lines (unchanged, prefixed with double spaces).
    - Changed lines (added or removed, prefixed with `+ ` or `- `).

    Attributes
    ----------
    _pattern : str
        Placeholder for a normalized pattern string.
    _snippet : str
        Placeholder for a snippet representation.
    _lst : list of str
        List of text fragments associated with the current node.
    _lst_other : list of str
        List of text fragments from the "other" side of the diff.
    _is_common : bool
        Flag indicating whether the line is common (unchanged).
    _is_changed : bool
        Flag indicating whether the line is changed (added/removed).

    Notes
    -----
    - Common lines are detected by `STRING.DOUBLE_SPACES`.
    - Changed lines are detected by prefixes `- ` or `+ `.
    - Subclasses such as `NDiffCommonText` and `NDiffChangedText`
      provide specialized behavior.
    """
    def __init__(self, txt: str) -> None:
        self._pattern: str = STRING.EMPTY
        self._snippet: str = STRING.EMPTY
        self._lst: List[str] = []
        self._lst_other: List[str] = []
        self._is_common: bool = False
        self._is_changed: bool = False

        # Detect common lines
        if txt.startswith(STRING.DOUBLE_SPACES):
            self._lst.append(txt.lstrip(STRING.SPACE_CHAR))
            self._is_common = True

        # Detect changed lines
        if txt.startswith("- ") or txt.startswith("+ "):
            if txt.startswith("- "):
                self._lst.append(txt.lstrip("- "))
            if txt.startswith("+ "):
                self._lst_other.append(txt.lstrip("+ "))
            self._is_changed = True

    def __bool__(self) -> bool:
        """
        Return True if this node contains any text fragments.

        Returns
        -------
        bool
            True if either `_lst` or `_lst_other` contains fragments,
            False otherwise.
        """
        return bool(self._lst or self._lst_other)

    def __len__(self) -> int:
        """
        Return the number of text fragments stored in this node.

        Returns
        -------
        int
            Number of fragments across `_lst` and `_lst_other`.
        """
        return len(self._lst) + len(self._lst_other)

    @property
    def is_common(self) -> bool:
        """bool: Whether this node represents a common (unchanged) line."""
        return self._is_common

    @property
    def is_changed(self) -> bool:
        """bool: Whether this node represents a changed (added/removed) line."""
        return self._is_changed

    @property
    def name(self) -> str:
        """str: Name identifier for the node type (default empty)."""
        return STRING.EMPTY

    @property
    def lst(self) -> List[str]:
        """list of str: Text fragments associated with this node."""
        return self._lst

    @property
    def lst_other(self) -> List[str]:
        """list of str: Text fragments from the other side of the diff."""
        return self._lst_other

    def is_same_type(self, other: "NDiffBaseText") -> bool:
        """
        Check whether another node is of the same type.

        Parameters
        ----------
        other : NDiffBaseText
            Another diff node to compare against.

        Returns
        -------
        bool
            True if both nodes share the same `name`, False otherwise.
        """
        return bool(self.name and self.name == other.name)

    def extend(self, other: "NDiffBaseText") -> None:
        """
        Extend this node's fragments with those from another node.

        Parameters
        ----------
        other : NDiffBaseText
            Another diff node whose fragments will be merged.
        """
        if self.name and self.name == other.name:
            self._lst.extend(other.lst)
            self._lst_other.extend(other.lst_other)

    def readjust_lst(self, *lst_of_txt: str) -> None:
        """
        Replace `_lst` with a new set of text fragments.

        Parameters
        ----------
        lst_of_txt : str
            One or more text fragments to store.
        """
        if lst_of_txt:
            self._lst.clear()
            self._lst.extend(txt for txt in lst_of_txt if txt)

    def readjust_lst_other(self, *lst_of_other_txt: str) -> None:
        """
        Replace `_lst_other` with a new set of text fragments.

        Parameters
        ----------
        lst_of_other_txt : str
            One or more text fragments to store in `_lst_other`.
        """
        if lst_of_other_txt:
            self._lst_other.clear()
            self._lst_other.extend(txt for txt in lst_of_other_txt if txt)

    @classmethod
    def do_factory_create(cls, txt: str) -> "NDiffBaseText":
        """
        Factory method to create the appropriate diff node.

        Parameters
        ----------
        txt : str
            Input text line to classify.

        Returns
        -------
        NDiffBaseText
            An instance of `NDiffCommonText` if the line is common,
            otherwise an instance of `NDiffChangedText` or None.
        """
        if txt.startswith(STRING.DOUBLE_SPACES):
            return NDiffCommonText(txt)
        changed_node = NDiffChangedText(txt)
        return changed_node if changed_node else None


class NDiffCommonText(NDiffBaseText):
    """
    Diff node representing common (unchanged) text lines.

    This class extends `NDiffBaseText` to handle lines that are
    considered common in a diff (unchanged lines, typically prefixed
    with double spaces in unified diff format). It provides methods
    to generate normalized regex patterns and snippet representations
    of the stored text fragments.

    Attributes
    ----------
    _pattern : str
        Cached normalized regex pattern for the line.
    _snippet : str
        Cached snippet representation of the line.
    _lst : list of str
        Text fragments associated with the common line.
    """

    @property
    def name(self) -> str:
        """
        Identifier for this diff node type.

        Returns
        -------
        str
            `"ndiff_common_text"` if the node contains fragments,
            otherwise an empty string.
        """
        return "ndiff_common_text" if bool(self) else STRING.EMPTY

    def get_pattern(self, whitespace: str = " ") -> str:
        """
        Generate a normalized regex pattern for the common line.

        Parameters
        ----------
        whitespace : str, optional
            Replacement character for spaces in the pattern.
            Defaults to a single space.

        Returns
        -------
        str
            Normalized regex pattern string. Empty if no fragments exist.
        """
        txt = STRING.DOUBLE_SPACES.join(self.lst)
        pattern = TextPattern(txt) if txt else STRING.EMPTY
        self._pattern = pattern.replace(STRING.SPACE_CHAR, whitespace) if pattern else STRING.EMPTY
        return self._pattern

    def get_snippet(self, whitespace: str = " ") -> str:
        """
        Generate a snippet representation of the common line.

        Parameters
        ----------
        whitespace : str, optional
            Replacement character for spaces in the snippet.
            If equal to `PATTERN.WHITESPACE`, tabs are used as spacers.
            Defaults to a single space.

        Returns
        -------
        str
            Snippet string representation of the line.
        """
        is_ws = whitespace == PATTERN.WHITESPACE
        spacer = "\t " if is_ws else STRING.DOUBLE_SPACES
        snippet = spacer.join(self.lst)
        self._snippet = snippet
        return snippet


class NDiffChangedText(NDiffBaseText):
    """
    Diff node representing changed text lines.

    This class extends `NDiffBaseText` to handle lines that are
    considered changed in a diff (added or removed lines, typically
    prefixed with `+ ` or `- ` in unified diff format). It provides
    methods to generate normalized regex patterns and snippet
    representations of the stored text fragments.

    Attributes
    ----------
    _pattern : str
        Cached normalized regex pattern for the changed line.
    _snippet : str
        Cached snippet representation of the changed line.
    _lst : list of str
        Text fragments associated with the "removed" side of the diff.
    _lst_other : list of str
        Text fragments associated with the "added" side of the diff.
    """

    @property
    def name(self) -> str:
        """
        Identifier for this diff node type.

        Returns
        -------
        str
            `"ndiff_changed_text"` if the node contains fragments,
            otherwise an empty string.
        """
        return "ndiff_changed_text" if bool(self) else STRING.EMPTY

    @property
    def is_containing_empty_changed(self) -> bool:
        """
        Whether this node represents a change that may be empty.

        Returns
        -------
        bool
            True if only one side (`_lst` or `_lst_other`) contains fragments.
            False if both sides contain fragments or both are empty.
        """
        if self.lst and self.lst_other:
            return False
        elif self.lst or self.lst_other:
            return True
        return False

    def get_pattern(
        self,
        var: str = "",
        label: str | None = None,
        is_lessen: bool = False,
        is_root: bool = False,
    ) -> str:
        """
        Generate a normalized regex pattern for the changed line.

        Parameters
        ----------
        var : str, optional
            Variable name to use in the regex group.
        label : str, optional
            Label to append to the variable name.
        is_lessen : bool, optional
            Whether to use the lessened pattern from the factory.
        is_root : bool, optional
            Whether to use the root pattern from the factory.

        Returns
        -------
        str
            Regex pattern string representing the changed line.
        """
        if label:
            var = var.replace("v", f"v{label}", NUMBER.ONE)

        txt1 = STRING.DOUBLE_SPACES.join(self.lst)
        txt2 = STRING.DOUBLE_SPACES.join(self.lst_other)

        if txt1 or txt2:    # noqa
            args = [txt1, txt2] if txt1 and txt2 else [txt1] if txt1 else [txt2]
            factory = TranslatedPattern.do_factory_create(*args)
            pattern = factory.lessen_pattern if is_lessen else factory.pattern
            pattern = factory.root_pattern if is_root else pattern
        else:
            pattern = STRING.EMPTY

        if var:
            fmt = "(?P<%s>(%s)|)" if self.is_containing_empty_changed else "(?P<%s>%s)"
            pattern = fmt % (var, pattern)
        elif pattern:
            pattern = f"(({pattern})|)" if self.is_containing_empty_changed else pattern

        return pattern

    def get_snippet(
        self,
        var: str = "",
        label: str | None = None,
        is_lessen: bool = False,
        is_root: bool = False,
    ) -> str:
        """
        Generate a snippet representation of the changed line.

        Parameters
        ----------
        var : str, optional
            Variable name to use in the snippet.
        label : str, optional
            Label to append to the variable name.
        is_lessen : bool, optional
            Whether to use the lessened snippet from the factory.
        is_root : bool, optional
            Whether to use the root snippet from the factory.

        Returns
        -------
        str
            Snippet string representation of the changed line.
        """
        if label:
            var = var.replace("v", f"v{label}", NUMBER.ONE)

        txt1 = STRING.DOUBLE_SPACES.join(self.lst)
        txt2 = STRING.DOUBLE_SPACES.join(self.lst_other)

        if txt1 or txt2:
            args = [txt1, txt2] if txt1 and txt2 else [txt1] if txt1 else [txt2]
            factory = TranslatedPattern.do_factory_create(*args)
            kwargs = dict(var=var, is_lessen=is_lessen, is_root=is_root)
            self._snippet = factory.get_template_snippet(**kwargs)
            if self.is_containing_empty_changed:
                self._snippet = f"{self._snippet[:-1]}, or_empty)"

        return self._snippet


class NDiffLinePattern:
    """
    Represents a normalized diff pattern between two text lines.

    This class compares two input lines (`line_a` and `line_b`) and
    generates both a regex pattern and a snippet representation that
    describe their similarities and differences. It accounts for
    leading/trailing whitespace, identical cases, empty cases, and
    diff cases using `NDiffBaseText` nodes.

    Parameters
    ----------
    line_a : str
        First line to compare.
    line_b : str
        Second line to compare.
    whitespace : str, optional
        Regex pattern for whitespace. If not provided, inferred from
        whether either line contains whitespace.
    label : str, optional
        Label used for variable naming in generated patterns/snippets.
    is_lessen : bool, optional
        Whether to use a lessened pattern representation.
    is_root : bool, optional
        Whether to use a root pattern representation.

    Attributes
    ----------
    whitespace : str
        Regex pattern used for whitespace handling.
    label : str or None
        Label used for variable naming.
    is_lessen : bool
        Flag for lessened pattern usage.
    is_root : bool
        Flag for root pattern usage.
    is_leading : bool
        True if either line has leading whitespace.
    are_leading : bool
        True if both lines have leading whitespace.
    is_trailing : bool
        True if either line has trailing whitespace.
    are_trailing : bool
        True if both lines have trailing whitespace.
    leading_whitespace : str
        Regex fragment for leading whitespace.
    trailing_whitespace : str
        Regex fragment for trailing whitespace.
    line_a : str
        Original first line.
    line_b : str
        Original second line.
    _line_a : str
        Stripped version of `line_a`.
    _line_b : str
        Stripped version of `line_b`.
    _is_diff : bool
        Flag indicating whether the lines differ.
    _pattern : str
        Generated regex pattern.
    _snippet : str
        Generated snippet representation.

    Notes
    -----
    - Empty lines are handled specially with `analyze_and_parse_empty_case`.
    - Identical lines are normalized with `TextPattern`.
    - Differences are tokenized and represented using `NDiffBaseText` nodes.
    """

    def __init__(
        self,
        line_a: str,
        line_b: str,
        whitespace: str = None,
        label: str = None,
        is_lessen: bool = False,
        is_root: bool = False,
    ) -> None:
        self.whitespace = whitespace
        if not self.whitespace:
            is_ws = any(Misc.is_whitespace_in_line(line) for line in [line_a, line_b])
            self.whitespace = PATTERN.WHITESPACE if is_ws else PATTERN.SPACE

        self.label = label
        self.is_lessen = is_lessen
        self.is_root = is_root

        # Leading whitespace detection
        self.is_leading = Misc.is_leading_line(line_a) or Misc.is_leading_line(line_b)
        self.are_leading = Misc.is_leading_line(line_a) and Misc.is_leading_line(line_b)

        # trailing whitespace detection
        self.is_trailing = Misc.is_trailing_line(line_a) or Misc.is_trailing_line(line_b)
        self.are_trailing = Misc.is_trailing_line(line_a) and Misc.is_trailing_line(line_b)

        multi = '+' if self.are_leading else '*'
        ws = self.whitespace
        self.leading_whitespace = f'{ws}{multi}' if self.is_leading else STRING.EMPTY

        multi = '+' if self.are_trailing else '*'
        self.trailing_whitespace = f'{ws}{multi}' if self.is_trailing else STRING.EMPTY

        self.line_a = line_a
        self.line_b = line_b

        self._line_a = self.line_a.strip()
        self._line_b = self.line_b.strip()

        self._is_diff = False
        self._pattern = STRING.EMPTY
        self._snippet = STRING.EMPTY
        self.process()

    def __len__(self) -> int:
        """Return nonzero if a pattern has been generated."""
        return int(self._pattern != STRING.EMPTY)

    def __call__(self, *args, **kwargs) -> "NDiffLinePattern":
        """Create a new instance of `NDiffLinePattern` with given arguments."""
        return self.__class__(*args, **kwargs)

    @property
    def is_diff(self) -> bool:
        """bool: Whether the two lines differ."""
        return self._is_diff

    @property
    def pattern(self) -> str:
        """str: Full regex pattern including leading/trailing whitespace."""
        return f"{self.leading_whitespace}{self._pattern}{self.trailing_whitespace}"

    @property
    def snippet(self) -> str:
        """
        Snippet representation of the line comparison.

        This property generates a human‑readable snippet string that
        represents the comparison between two lines. If the lines differ,
        it includes `start()` and `end()` markers with annotated whitespace
        information. Otherwise, it returns the raw snippet.

        Returns
        -------
        str
            Snippet string representation of the line comparison.

        Notes
        -----
        - If `is_diff` is True, leading and trailing whitespace markers
          are annotated as either `"space"` or `"whitespace"`.
        - If both sides contain leading/trailing whitespace, the marker
          is pluralized (e.g., `"whitespaces"`).
        - If `is_diff` is False, the cached `_snippet` is returned directly.
        """
        if self.is_diff:
            leading_snippet = "start()"
            trailing_snippet = "end()"
            whitespace = "space"
            if self.whitespace == r"\s":
                whitespace = "whitespaces"
            if self.is_leading:
                new_ws = f"{whitespace}s" if self.are_leading else whitespace
                leading_snippet = leading_snippet.replace("()", f"({new_ws})")
            if self.is_trailing:
                new_ws = f"{whitespace}s" if self.are_trailing else whitespace
                trailing_snippet = trailing_snippet.replace("()", f"({new_ws})")
            return f"{leading_snippet} {self._snippet} {trailing_snippet}"
        return self._snippet

    # --- Analysis methods ---

    def analyze_and_parse_empty_case(self) -> bool:
        """
        Handle the case where both lines are empty and equal.

        This method checks whether the stripped versions of `line_a` and
        `line_b` are both empty and identical. If so, it generates a simple
        regex pattern and snippet representation.

        Returns
        -------
        bool
            True if both lines are empty and equal, False otherwise.

        Side Effects
        ------------
        - Sets `_pattern` to a whitespace regex if leading/trailing whitespace
          is detected.
        - Sets `_snippet` to the original `line_a`.
        """
        is_equal = self._line_a == self._line_b
        is_empty = self._line_a == STRING.EMPTY

        if is_empty and is_equal:
            if self.is_leading or self.is_trailing:
                self._pattern = f"{self.whitespace}+"
            self._snippet = self.line_a
            return True
        return False

    def analyze_and_parse_identical_case(self) -> bool:
        """
        Handle the case where both lines are identical or whitespace-equivalent.

        This method checks whether the stripped versions of `line_a` and
        `line_b` are identical. If so, it generates a regex pattern and
        snippet representation. If not strictly identical, it further checks
        whether the tokenized versions (split by whitespace) are equivalent.

        Returns
        -------
        bool
            True if both lines are identical or whitespace-equivalent,
            False otherwise.

        Side Effects
        ------------
        - Sets `_pattern` to a `TextPattern` representation of the line(s).
        - Sets `_snippet` to the original `line_a`.
        """
        if self._line_a == self._line_b:
            self._pattern = TextPattern(self._line_a)
            self._snippet = self.line_a
            return True

        lst_a = re.split(f"{self.whitespace}+", self._line_a)
        lst_b = re.split(f"{self.whitespace}+", self._line_b)
        if lst_a == lst_b:
            new_lst = [TextPattern(item) for item in lst_a]
            self._pattern = f"{self.whitespace}+".join(new_lst)
            return True
        return False

    def build_list_of_diff(self) -> List[NDiffBaseText]:
        """
        Tokenize both lines and build a list of diff nodes.

        This method compares the stripped versions of `line_a` and `line_b`
        by splitting them into tokens using whitespace patterns. It then
        applies a diff algorithm (`difflib.ndiff`) to identify additions,
        deletions, and common tokens. Each diff token is converted into an
        `NDiffBaseText` node via the factory method, and consecutive nodes
        of the same type are merged for compactness.

        Returns
        -------
        list of NDiffBaseText
            A list of diff nodes representing the differences between
            `line_a` and `line_b`.

        Notes
        -----
        - Tokens starting with `'? '` (alignment hints from `ndiff`) are ignored.
        - Consecutive nodes of the same type are merged using `extend`.
        - The resulting list is suitable for building regex patterns and
          snippet representations.
        """
        # Tokenize both lines by whitespace
        lst_a = re.split(PATTERN.WHITESPACES, self._line_a)
        lst_b = re.split(PATTERN.WHITESPACES, self._line_b)

        # Compute diff between token lists
        diff = ndiff(lst_a, lst_b)

        # Filter out alignment hints
        tokens = [item for item in diff if not item.startswith("? ")]

        result: List[NDiffBaseText] = []
        for item in tokens:
            node = NDiffBaseText.do_factory_create(item)
            if result and result[-NUMBER.ONE].is_same_type(node):
                # Merge with previous node if same type
                result[-NUMBER.ONE].extend(node)
            else:
                result.append(node)

        return result

    def build_pattern_from_diff_list(self, lst) -> str:    # noqa
        """
        Construct a regex pattern from a list of diff nodes.

        This method iterates over a list of `NDiffBaseText` nodes representing
        differences between two lines and builds a regex pattern that captures
        both unchanged and changed fragments. Changed fragments are assigned
        variable placeholders (`v0`, `v1`, etc.), while unchanged fragments
        preserve whitespace handling.

        Parameters
        ----------
        lst : list
            List of diff nodes representing tokenized differences between two lines.

        Returns
        -------
        str
            Regex pattern string representing the diff list.

        Notes
        -----
        - If only one node exists, its pattern is returned directly.
        - Changed nodes are wrapped with variable placeholders.
        - Empty changes are handled with optional whitespace groups.
        - Leading/trailing whitespace is preserved using `PATTERN.WHITESPACES`
          or `PATTERN.SPACES`.
        """
        kwargs = dict(label=self.label, is_lessen=self.is_lessen, is_root=self.is_root)

        total = len(lst)
        if total == NUMBER.ONE:
            item = lst[INDEX.ZERO]
            if item.is_changed:
                return item.get_pattern(var='v0', **kwargs)
            return item.get_pattern(whitespace=self.whitespace)

        result = []
        count = 0
        spacer = PATTERN.WHITESPACES if self.whitespace == PATTERN.WHITESPACE else PATTERN.SPACES
        for index, item in enumerate(lst):
            is_last = index == total - NUMBER.ONE
            if not is_last:
                if item.is_changed:
                    pat = item.get_pattern(var=f"v{count}", **kwargs)
                    count += 1
                    if item.is_containing_empty_changed:
                        result.extend([pat, f"({spacer})?"])
                    else:
                        result.extend([pat, spacer])
                else:
                    result.extend([item.get_pattern(whitespace=self.whitespace), spacer])
            else:
                if item.is_changed:
                    pat = item.get_pattern(var=f"v{count}", **kwargs)
                    if item.is_containing_empty_changed:
                        # Adjust previous spacer to optional
                        if result:
                            result.pop()
                        result.extend([f"({spacer})?", pat])
                    else:
                        result.append(pat)
                else:
                    result.append(item.get_pattern(whitespace=self.whitespace))
        return STRING.EMPTY.join(result)

    def build_snippet_from_diff_list(self, lst) -> str:  # noqa
        """
        Construct a snippet string from a list of diff nodes.

        Parameters
        ----------
        lst : list
            List of diff nodes representing tokenized differences
            between two lines.

        Returns
        -------
        str
            Snippet string representation of the diff list, with
            variable placeholders for changed nodes and whitespace
            preserved between fragments.
        """
        result: List[str] = []
        count = NUMBER.ZERO

        for item in lst:
            if item.is_changed:
                count += NUMBER.ONE
                kwargs = dict(
                    var=f"v{count}",
                    label=self.label,
                    is_lessen=self.is_lessen,
                    is_root=self.is_root,
                )
                snippet_ = item.get_snippet(**kwargs)   # noqa
            else:
                snippet_ = item.get_snippet(whitespace=self.whitespace) # noqa
            result.append(snippet_)

        snippet = STRING.DOUBLE_SPACES.join(result)
        return snippet

    def analyze_and_parse_diff_case(self) -> bool:
        """
        Analyze and parse the case where the two lines differ.

        Returns
        -------
        bool
            True if the lines differ and a diff pattern/snippet
            was successfully generated, False otherwise.
        """
        if self.analyze_and_parse_empty_case():
            return False
        if self.analyze_and_parse_identical_case():
            return False

        self._is_diff = True
        lst = self.build_list_of_diff()
        self._pattern = self.build_pattern_from_diff_list(lst)
        self._snippet = self.build_snippet_from_diff_list(lst)
        return True

    def process(self) -> None:
        """
        Perform full analysis of the two lines.

        This method attempts to classify the comparison into one of
        three cases:
        - Empty case: both lines are empty and equal.
        - Identical case: both lines are identical or whitespace-equivalent.
        - Diff case: lines differ and a diff pattern/snippet is generated.

        Notes
        -----
        - Sets `_pattern` and `_snippet` accordingly.
        - Updates `_is_diff` flag if differences are found.
        """
        is_empty = self.analyze_and_parse_empty_case()
        is_similar = not is_empty and self.analyze_and_parse_identical_case()
        if not is_similar:
            self.analyze_and_parse_diff_case()


class DiffLinePattern(RuntimeException):
    """
    Represents a normalized diff pattern between multiple text lines.

    This class compares two or more input lines and generates both a regex
    pattern and a snippet representation that describe their similarities
    and differences. It accounts for leading/trailing whitespace, identical
    cases, and diff cases.

    Parameters
    ----------
    line1 : str
        First line to compare.
    line2 : str
        Second line to compare.
    *other_lines : str, optional
        Additional lines to include in the comparison.
    label : str, optional
        Label used for variable naming in generated patterns/snippets.

    Attributes
    ----------
    label : str or None
        Label used for variable naming.
    raw_lines : list of str
        Original input lines.
    lines : list of str
        Processed lines after normalization.
    _is_diff : bool
        Flag indicating whether the lines differ.
    _pattern : str
        Generated regex pattern.
    _snippet : str
        Generated snippet representation.
    """

    def __init__(self, line1: str, line2: str, *other_lines: str, label: str | None = None) -> None:
        self.label = label
        self.raw_lines: List[str] = []
        self.lines: List[str] = []
        self._is_diff: bool = False
        self._pattern: str = STRING.EMPTY
        self._snippet: str = STRING.EMPTY

        self.prepare(line1, line2, *other_lines)
        self.process()

    def __len__(self) -> int:
        """
        Return nonzero if a pattern has been generated.

        Returns
        -------
        int
            1 if a pattern exists, 0 otherwise.
        """
        return int(bool(self._pattern))

    @property
    def is_diff(self) -> bool:
        """bool: Whether the input lines differ."""
        return self._is_diff

    @property
    def pattern(self) -> str:
        """
        str: Full regex pattern including leading/trailing whitespace.
        """
        return f"{self.leading_whitespace}{self._pattern}{self.trailing_whitespace}"

    @property
    def snippet(self) -> str:
        """
        Snippet representation of the line comparison.

        This property generates a human‑readable snippet string that
        represents the comparison between lines. If the lines differ,
        it includes `start()` and `end()` markers with annotated whitespace
        information. Otherwise, it returns the raw snippet.

        Returns
        -------
        str
            Snippet string representation of the line comparison.

        Notes
        -----
        - Leading and trailing whitespace markers are annotated as either
          `"space"` or `"whitespace"`.
        - If both sides contain leading/trailing whitespace, the marker
          is pluralized (e.g., `"whitespaces"`).
        - If the internal `_snippet` already contains `start()` and `end()`
          markers, they are replaced with updated whitespace annotations.
        """
        if not self.is_diff:
            return self._snippet

        leading_snippet, trailing_snippet = "start()", "end()"
        whitespace_type = "whitespace" if self.whitespace == r"\s" else "space"

        if self.is_leading:
            new_ws = f"{whitespace_type}s" if self.are_leading else whitespace_type
            leading_snippet = leading_snippet.replace("()", f"({new_ws})")

        if self.is_trailing:
            new_ws = f"{whitespace_type}s" if self.are_trailing else whitespace_type
            trailing_snippet = trailing_snippet.replace("()", f"({new_ws})")

        # Regex to detect existing start/end markers in the snippet
        pattern = r"^(start\(\w*\)) (?P<snippet>.+) (end\(\w*\))$"
        match = re.match(pattern, self._snippet)

        if match:
            snippet_body = match.group("snippet")
            return f"{leading_snippet} {snippet_body} {trailing_snippet}"

        return f"{leading_snippet} {self._snippet} {trailing_snippet}"

    @property
    def are_leading(self) -> bool:
        """
        Whether all lines have leading whitespace.

        Returns
        -------
        bool
            True if every line in `raw_lines` begins with leading whitespace,
            False otherwise.
        """
        return all(Misc.is_leading_line(line) for line in self.raw_lines)

    @property
    def are_trailing(self) -> bool:
        """
        Whether all lines have trailing whitespace.

        Returns
        -------
        bool
            True if every line in `raw_lines` ends with trailing whitespace,
            False otherwise.
        """
        return all(Misc.is_trailing_line(line) for line in self.raw_lines)

    @property
    def is_leading(self) -> bool:
        """
        Whether any line has leading whitespace.

        Returns
        -------
        bool
            True if at least one line in `raw_lines` begins with leading whitespace,
            False otherwise.
        """
        return any(Misc.is_leading_line(line) for line in self.raw_lines)

    @property
    def is_trailing(self) -> bool:
        """
        Whether any line has trailing whitespace.

        Returns
        -------
        bool
            True if at least one line in `raw_lines` ends with trailing whitespace,
            False otherwise.
        """
        return any(Misc.is_trailing_line(line) for line in self.raw_lines)

    @property
    def is_whitespace_in_line(self) -> bool:
        """
        Whether any line contains whitespace.

        Returns
        -------
        bool
            True if at least one line in `raw_lines` contains whitespace,
            False otherwise.
        """
        return any(Misc.is_whitespace_in_line(line) for line in self.raw_lines)

    @property
    def whitespace(self) -> str:
        """
        Regex pattern for whitespace handling.

        Returns
        -------
        str
            `PATTERN.WHITESPACE` if any line contains whitespace,
            otherwise `PATTERN.SPACE`.
        """
        return PATTERN.WHITESPACE if self.is_whitespace_in_line else PATTERN.SPACE

    @property
    def leading_whitespace(self) -> str:
        """
        Regex fragment for leading whitespace.

        Returns
        -------
        str
            Regex fragment representing leading whitespace.
            Uses `+` if all lines are leading, `*` otherwise.
            Empty string if no leading whitespace is present.
        """
        multi = "+" if self.are_leading else "*"
        return f"{self.whitespace}{multi}" if self.is_leading else STRING.EMPTY

    @property
    def trailing_whitespace(self) -> str:
        """
        Regex fragment for trailing whitespace.

        Returns
        -------
        str
            Regex fragment representing trailing whitespace.
            Uses `+` if all lines are trailing, `*` otherwise.
            Empty string if no trailing whitespace is present.
        """
        multi = "+" if self.are_trailing else "*"
        return f"{self.whitespace}{multi}" if self.is_trailing else STRING.EMPTY

    def reset(self) -> None:
        """
        Reset the internal state of the object.

        Side Effects
        ------------
        - Clears `lines`.
        - Resets `_pattern` to empty.
        """
        self.lines.clear()
        self._pattern = STRING.EMPTY

    def prepare(self, line1: str, line2: str, *other_lines: str) -> None:
        """
        Prepare and normalize input lines for diff analysis.

        This method trims whitespace from each provided line, filters out
        empty lines, and stores both raw and normalized versions. At least
        two non-empty lines are required to form a valid pattern.

        Parameters
        ----------
        line1 : str
            First line to compare.
        line2 : str
            Second line to compare.
        *other_lines : str, optional
            Additional lines to include in the comparison.

        Raises
        ------
        RuntimeException
            If fewer than two non-empty lines are provided.

        Side Effects
        ------------
        - Populates `self.raw_lines` with original non-empty lines.
        - Populates `self.lines` with trimmed non-empty lines.
        - Calls `reset()` before storing new lines.
        """
        lst = [line1, line2] + list(other_lines)

        raw_lines: List[str] = []
        lines: List[str] = []

        for line in lst:
            trim_line = line.strip()
            if trim_line:
                if line not in raw_lines:
                    raw_lines.append(line)
                if trim_line not in lines:
                    lines.append(trim_line)

        if len(lines) < NUMBER.TWO:
            fmt = "Cannot form pattern: fewer than two lines provided.\n%s"
            details = [f"Line 1: {line1!r}", f"Line 2: {line2!r}"]
            if other_lines:
                details.append(f"Other Lines: {other_lines!r}")
            self.raise_runtime_error(msg=fmt % STRING.NEWLINE.join(details))
        else:
            self.reset()
            self.lines.extend(lines)
            self.raw_lines.extend(raw_lines)

    def get_pattern_btw_two_lines(
        self, line_a: str, line_b: str,
        is_lessen: bool = False, is_root: bool = False
    ) -> str:
        """
        Generate a regex pattern between two lines.

        Parameters
        ----------
        line_a : str
            First line to compare.
        line_b : str
            Second line to compare.
        is_lessen : bool, optional
            Whether to use a lessened pattern representation.
        is_root : bool, optional
            Whether to use a root pattern representation.

        Returns
        -------
        str
            Regex pattern string representing the comparison.
        """
        diff_line_obj = NDiffLinePattern(
            line_a,
            line_b,
            label=self.label,
            whitespace=f"{self.whitespace}",
            is_lessen=is_lessen,
            is_root=is_root,
        )
        self._is_diff = diff_line_obj.is_diff
        return diff_line_obj.pattern

    def get_snippet_btw_two_lines(
        self, line_a: str, line_b: str,
        is_lessen: bool = False, is_root: bool = False
    ) -> str:
        """
        Generate a snippet representation between two lines.

        Parameters
        ----------
        line_a : str
            First line to compare.
        line_b : str
            Second line to compare.
        is_lessen : bool, optional
            Whether to use a lessened snippet representation.
        is_root : bool, optional
            Whether to use a root snippet representation.

        Returns
        -------
        str
            Snippet string representation of the comparison.
        """
        diff_line_obj = NDiffLinePattern(
            line_a,
            line_b,
            label=self.label,
            whitespace=f"{self.whitespace}",
            is_lessen=is_lessen,
            is_root=is_root,
        )
        return diff_line_obj.snippet

    def is_matched_all(self, pattern: str) -> bool:
        """
        Check whether all stored lines fully match a given regex pattern.

        Parameters
        ----------
        pattern : str
            Regex pattern to test against each line.

        Returns
        -------
        bool
            True if all lines match the pattern exactly, False otherwise.
        """
        for line in self.lines:
            match = re.match(pattern, line)
            if not match or match.group() != line:
                return False
        return True

    def reconstruct_pattern_and_snippet(self) -> None:
        """
        Reconstruct the regex pattern and snippet representation
        from the stored lines.

        This method iterates over all lines in `self.lines`, applies the
        current `_pattern` to extract named groups, and rebuilds a generic
        pattern that captures both fixed and variable parts of the lines.
        It then constructs a list of diff nodes (`DText` and `DChange`)
        to represent unchanged and changed fragments, respectively.

        Finally, it updates the internal `_snippet` and `_pattern` attributes
        with the reconstructed values.

        Returns
        -------
        None
            Updates internal state (`_snippet`, `_pattern`) in place.

        Side Effects
        ------------
        - Sets `self._snippet` to a string of the form:
          ``start() <snippet_body> end()``.
        - Sets `self._pattern` to a new `LinePattern` built from the snippet.

        Notes
        -----
        - Each named group from the regex match is escaped and re‑inserted
          into a generic pattern with additional capture groups.
        - Consecutive matches are merged into `DText` (unchanged) or
          `DChange` (changed) objects.
        """
        lst: List[object] = []

        for line in self.lines:
            # Match the current pattern against the line
            match = re.match(self._pattern, line)
            if not match:
                continue

            other_lst = ["(?P<c0>.*)"]
            key = ""

            # Build generic pattern with escaped values and extra captures
            for key, val in match.groupdict().items():
                val = re.escape(val)
                other_lst.append(f"(?P<{key}>{val})")
                other_lst.append(f"(?P<c{key}>.+)")
            else:
                # Replace last greedy capture with a non-greedy fallback
                if other_lst:
                    other_lst.pop()
                other_lst.append(f"(?P<c{key}>.*)")

            generic_pattern = Misc.join_string(*other_lst)
            match = re.match(generic_pattern, line)

            if lst:
                # Merge values into existing nodes
                for index, (key, val) in enumerate(match.groupdict().items()):
                    lst[index].add(val)     # noqa
            else:
                # Initialize nodes from first match
                for key, val in match.groupdict().items():
                    if key.startswith("c"):
                        lst.append(DText(val))
                    else:
                        lst.append(DChange(val, var=key))

        # Build snippet string from nodes
        snippet = "".join(item.get_snippet() for item in lst)       # noqa
        self._snippet = f"start() {snippet} end()"
        self._pattern = LinePattern(snippet)

    def process(self) -> None:
        """
        Attempt to construct a regex pattern and snippet from the stored lines.

        This method compares all pairs of lines in `self.lines` and tries
        to generate a valid pattern/snippet using three passes:

        1. **First pass**: Standard pattern generation.
        2. **Second pass**: Pattern generation with `is_lessen=True`.
        3. **Third pass**: Pattern generation with `is_root=True`.

        If a matching pattern is found that validates against all lines,
        the internal `_pattern` and `_snippet` are updated and
        `reconstruct_pattern_and_snippet()` is called. If no valid pattern
        is found after all passes, a `RuntimeException` is raised.

        Raises
        ------
        RuntimeException
            If no constructed pattern matches all lines.
        """
        lines_count = len(self.lines)
        pairs = list(combinations(range(lines_count), NUMBER.TWO))
        attempted_patterns: List[str] = []

        def try_pass(**kwargs) -> bool:
            """Helper to attempt pattern/snippet generation with given flags."""
            for i, j in pairs:
                line_a, line_b = self.lines[i], self.lines[j]
                pattern = self.get_pattern_btw_two_lines(line_a, line_b,
                                                         **kwargs)
                snippet = self.get_snippet_btw_two_lines(line_a, line_b,
                                                         **kwargs)
                attempted_patterns.append(pattern)

                if self.is_matched_all(pattern):
                    self._pattern = pattern
                    self._snippet = snippet
                    self.reconstruct_pattern_and_snippet()
                    return True
            return False

        # Try passes in order: default, lessen, root
        if try_pass():
            return
        if try_pass(is_lessen=True):
            return
        if try_pass(is_root=True):
            return

        # If all passes failed, raise error with diagnostic info
        fmt = "Failed to build a matching pattern. Attempted patterns:\n  %s"
        details = "\n  ".join(repr(item) for item in attempted_patterns)
        self.raise_runtime_error(msg=fmt % details)


class CommonDiffLinePattern(RuntimeException):
    """
    Represents a common diff pattern across multiple lines.

    This class analyzes a set of input lines to determine whether they
    share identical structure, leading/trailing whitespace, or differ.
    It provides properties for whitespace handling, pattern generation,
    and snippet representation.

    Parameters
    ----------
    *lines : str
        Input lines to be analyzed.
    label : str, optional
        Label used for variable naming in generated patterns/snippets.

    Attributes
    ----------
    raw_lines : tuple of str
        Original input lines.
    lines : list of str
        Normalized (trimmed) non-empty lines.
    label : str or None
        Label used for variable naming.
    _is_diff : bool
        Flag indicating whether the lines differ.
    _pattern : str
        Generated regex pattern.
    _snippet : str
        Generated snippet representation.
    """

    def __init__(self, *lines: str, label: str | None = None) -> None:
        self.raw_lines: Tuple[str, ...] = lines
        self.lines: List[str] = [line.strip() for line in lines if line.strip()]
        self.label: str | None = label
        self._is_diff: bool = False
        self._pattern: str = STRING.EMPTY
        self._snippet: str = STRING.EMPTY
        self.process()

    @property
    def are_leading(self) -> bool:
        """
        Whether all lines have leading whitespace.

        Returns
        -------
        bool
            True if every line in `raw_lines` begins with leading whitespace,
            False otherwise.
        """
        return all(Misc.is_leading_line(line) for line in self.raw_lines)

    @property
    def are_trailing(self) -> bool:
        """
        Whether all lines have trailing whitespace.

        Returns
        -------
        bool
            True if every line in `raw_lines` ends with trailing whitespace,
            False otherwise.
        """
        return all(Misc.is_trailing_line(line) for line in self.raw_lines)

    @property
    def is_leading(self) -> bool:
        """
        Whether any line has leading whitespace.

        Returns
        -------
        bool
            True if at least one line in `raw_lines` begins with leading whitespace,
            False otherwise.
        """
        return any(Misc.is_leading_line(line) for line in self.raw_lines)

    @property
    def is_trailing(self) -> bool:
        """
        Whether any line has trailing whitespace.

        Returns
        -------
        bool
            True if at least one line in `raw_lines` ends with trailing whitespace,
            False otherwise.
        """
        return any(Misc.is_trailing_line(line) for line in self.raw_lines)

    @property
    def is_whitespace_in_line(self) -> bool:
        """
        Whether any line contains whitespace.

        Returns
        -------
        bool
            True if at least one line in `raw_lines` contains whitespace,
            False otherwise.
        """
        return any(Misc.is_whitespace_in_line(line) for line in self.raw_lines)

    @property
    def whitespace(self) -> str:
        """
        Regex pattern for whitespace handling.

        Returns
        -------
        str
            `PATTERN.WHITESPACE` if any line contains whitespace,
            otherwise `PATTERN.SPACE`.
        """
        return PATTERN.WHITESPACE if self.is_whitespace_in_line else PATTERN.SPACE

    @property
    def leading_whitespace(self) -> str:
        """
        Regex fragment for leading whitespace.

        Returns
        -------
        str
            Regex fragment representing leading whitespace.
            Uses `+` if all lines are leading, `*` otherwise.
            Empty string if no leading whitespace is present.
        """
        multi = "+" if self.are_leading else "*"
        return f"{self.whitespace}{multi}" if self.is_leading else STRING.EMPTY

    @property
    def trailing_whitespace(self) -> str:
        """
        Regex fragment for trailing whitespace.

        Returns
        -------
        str
            Regex fragment representing trailing whitespace.
            Uses `+` if all lines are trailing, `*` otherwise.
            Empty string if no trailing whitespace is present.
        """
        multi = "+" if self.are_trailing else "*"
        return f"{self.whitespace}{multi}" if self.is_trailing else STRING.EMPTY

    @property
    def has_data(self) -> bool:
        """
        Whether the class contains any non-empty lines.

        Returns
        -------
        bool
            True if `lines` contains at least one entry, False otherwise.
        """
        return len(self.lines) > NUMBER.ZERO

    @property
    def are_identical_lines(self) -> bool:
        """
        Whether all normalized lines are identical.

        Returns
        -------
        bool
            True if all lines are identical after removing whitespace,
            False otherwise.
        """
        if not self.has_data:
            return False
        normalized = [re.sub(PATTERN.WHITESPACES, STRING.EMPTY, line) for line in self.lines]
        return len(set(normalized)) == NUMBER.ONE

    @property
    def is_diff(self) -> bool:
        """
        Whether the lines differ.

        Returns
        -------
        bool
            True if the lines differ, False otherwise.
        """
        return self._is_diff

    @property
    def pattern(self) -> str:
        """
        Regex pattern representing the lines.

        Returns
        -------
        str
            Regex pattern string.
        """
        return self._pattern

    @property
    def snippet(self) -> str:
        """
        Snippet representation of the lines.

        Returns
        -------
        str
            Snippet string representation.
        """
        return self._snippet

    def get_common_pattern(self) -> str:
        """
        Construct a common regex pattern across identical lines.

        This method analyzes all stored lines and builds a regex pattern
        that captures their shared structure. If all lines are identical,
        the pattern is built directly. Otherwise, it tokenizes each line
        into groups and generates a generalized pattern that accounts for
        whitespace differences.

        Returns
        -------
        str
            Regex pattern string representing the common structure of the lines.
            Returns an empty string if lines are not identical.
        """
        if not self.are_identical_lines:
            return STRING.EMPTY

        # Case 1: All lines are exactly identical
        if len(set(self.lines)) == NUMBER.ONE:
            pattern = TextPattern(self.lines[INDEX.ZERO])
            return f"{self.leading_whitespace}{pattern}{self.trailing_whitespace}"

        # Case 2: Lines are structurally identical but differ in whitespace
        lst_of_groups = list(
            zip(*[Text(line).do_finditer_split(r"\S+") for line in self.lines]))
        result: List[str] = []

        for grp in lst_of_groups[INDEX.ONE:-INDEX.ONE]:
            if len(set(grp)) == 1:
                result.append(TextPattern(grp[INDEX.ZERO]))
            else:
                is_space_only = re.match(r" +$", "".join(grp))
                result.append(
                    PATTERN.SPACES if is_space_only else PATTERN.WHITESPACES)

        pattern = "".join(result)
        return f"{self.leading_whitespace}{pattern}{self.trailing_whitespace}"

    def get_common_snippet(self) -> str:
        """
        Construct a common snippet across identical lines.

        This method generates a human‑readable snippet string that represents
        the common structure of the lines. If all lines are identical, the
        snippet is returned directly. Otherwise, it tokenizes each line into
        groups and builds a generalized snippet representation.

        Returns
        -------
        str
            Snippet string representation of the common structure of the lines.
            Returns an empty string if lines are not identical.
        """
        if not self.are_identical_lines:
            return STRING.EMPTY

        tbl = {
            " +": "(spaces)",
            " *": "(space)",
            r"\s+": "(whitespaces)",
            r"\s*": "(whitespace)",
            "": STRING.EMPTY,
        }

        case = tbl.get(self.leading_whitespace)
        leading_snippet = f"start({case})" if self.is_leading else STRING.EMPTY
        case = tbl.get(self.trailing_whitespace)
        trailing_snippet = f"end({case})" if self.is_trailing else STRING.EMPTY

        # Case 1: All lines are exactly identical
        if len(set(self.lines)) == NUMBER.ONE:
            snippet = self.lines[INDEX.ZERO]
            return f"{leading_snippet} {snippet} {trailing_snippet}".strip()

        # Case 2: Lines are structurally identical but differ in whitespace
        lst_of_groups = list(
            zip(*[Text(line).do_finditer_split(r"\S+") for line in self.lines]))
        result: List[str] = []

        for grp in lst_of_groups[INDEX.ONE:-INDEX.ONE]:
            if len(set(grp)) == 1:
                result.append(TextPattern(grp[INDEX.ZERO]))
            else:
                result.append(list(set(grp))[-INDEX.ONE])

        snippet = "".join(result)
        return f"{self.leading_whitespace}{snippet}{self.trailing_whitespace}"

    def process(self) -> None:
        """
        Process the stored lines to generate a pattern and snippet.

        This method determines whether the lines are identical or different
        and constructs the appropriate regex pattern and snippet. If lines
        are identical, it uses `get_common_pattern` and `get_common_snippet`.
        Otherwise, it delegates to `DiffLinePattern` for diff analysis.

        Side Effects
        ------------
        - Updates `_pattern` and `_snippet` with generated values.
        - Updates `_is_diff` flag if differences are detected.
        """
        if not self.has_data:
            return

        if self.are_identical_lines:
            self._pattern = self.get_common_pattern()
            self._snippet = self.get_common_snippet()
        else:
            node = DiffLinePattern(*self.lines, label=self.label)
            self._is_diff = node.is_diff
            self._pattern = node.pattern
            self._snippet = node.snippet

            if node.is_diff:
                tbl = {
                    " +": "spaces",
                    " *": "space",
                    r"\s+": "whitespaces",
                    r"\s*": "whitespace",
                    "": STRING.EMPTY,
                }
                case = tbl.get(self.leading_whitespace)
                leading_snippet = f"start({case})" if self.is_leading else STRING.EMPTY
                case = tbl.get(self.trailing_whitespace)
                trailing_snippet = f"end({case})" if self.is_trailing else STRING.EMPTY

                # Update pattern and snippet with whitespace context
                self._pattern = f"{self.leading_whitespace}{self._pattern}{self.trailing_whitespace}"
                if leading_snippet:
                    self._snippet = self._snippet.replace("start()",
                                                          leading_snippet)
                if trailing_snippet:
                    self._snippet = self._snippet.replace("end()",
                                                          trailing_snippet)


class DText:
    """
    Represents a diff text node for unchanged fragments.

    This class models a text fragment in a diff comparison. It stores
    the original text, tracks leading/trailing whitespace, and provides
    methods to generate regex patterns and snippet representations.

    Parameters
    ----------
    text : str
        The initial text fragment.

    Attributes
    ----------
    lst : list of str
        List of text fragments associated with this node.
    leading_lst : list of str
        Leading whitespace fragments extracted from the text.
    trailing_lst : list of str
        Trailing whitespace fragments extracted from the text.
    text : str
        Original text fragment.
    """

    def __init__(self, text: str) -> None:
        self.lst: List[str] = [text]
        self.leading_lst: List[str] = []
        self.trailing_lst: List[str] = []
        self.text: str = text

        leading = Misc.get_leading_line(text)
        if leading:
            self.leading_lst.append(leading)

        trailing = Misc.get_trailing_line(text)
        if trailing:
            if text.strip():
                self.trailing_lst.append(trailing)

    @property
    def leading(self) -> str:
        """
        Leading whitespace fragment.

        Returns
        -------
        str
            Leading whitespace string. If multiple variations exist,
            chooses the first non-empty trimmed value and appends a
            space if multi-length fragments are present.
        """
        if not self.leading_lst:
            return STRING.EMPTY

        if len(set(self.leading_lst)) == NUMBER.ONE:
            return self.leading_lst[INDEX.ZERO]

        ws = STRING.SPACE_CHAR
        for item in self.leading_lst:
            if item.strip(STRING.SPACE_CHAR):
                ws = item.strip(STRING.SPACE_CHAR)
                break
        is_multi = any(len(item) > NUMBER.ONE for item in self.leading_lst)
        return f"{ws} " if is_multi else ws

    @property
    def trailing(self) -> str:
        """
        Trailing whitespace fragment.

        Returns
        -------
        str
            Trailing whitespace string. If multiple variations exist,
            chooses the first non-empty trimmed value and appends a
            space if multi-length fragments are present.
        """
        if not self.trailing_lst:
            return STRING.EMPTY

        if len(set(self.trailing_lst)) == NUMBER.ONE:
            return self.trailing_lst[INDEX.ZERO]

        ws = STRING.SPACE_CHAR
        for item in self.trailing_lst:
            if item.strip(STRING.SPACE_CHAR):
                ws = item.strip(STRING.SPACE_CHAR)
                break
        is_multi = any(len(item) > NUMBER.ONE for item in self.trailing_lst)
        return f"{ws} " if is_multi else ws

    @property
    def first_text(self) -> str:
        """
        First text fragment.

        Returns
        -------
        str
            The first text fragment in `lst`, or empty string if none exist.
        """
        return self.lst[INDEX.ZERO] if self.lst else STRING.EMPTY

    @property
    def is_identical(self) -> bool:
        """
        Whether all text fragments are identical.

        Returns
        -------
        bool
            True if all fragments in `lst` are identical, False otherwise.
        """
        return len(set(self.lst)) == NUMBER.ONE

    @property
    def is_closed_to_identical(self) -> bool:
        """
        Whether all text fragments are identical after trimming.

        Returns
        -------
        bool
            True if all non-empty trimmed fragments are identical,
            False otherwise.
        """
        clean_lst = [item.strip() for item in self.lst if item.strip()]
        return len(set(clean_lst)) == NUMBER.ONE

    def concatenate(self, text: str) -> None:
        """
        Concatenate text to the last fragment.

        Parameters
        ----------
        text : str
            Text to append to the last fragment.
        """
        if self.lst:
            self.lst[-INDEX.ONE] = self.lst[-INDEX.ONE] + text
        else:
            self.lst.append(text)

    def add(self, text: str) -> None:
        """
        Add a new text fragment.

        Parameters
        ----------
        text : str
            Text fragment to add.
        """
        self.lst.append(text)

    def to_group(self) -> List[List[str]]:
        """
        Group text fragments by whitespace splits.

        Returns
        -------
        list of list of str
            Grouped fragments, with duplicates removed per group.
        """
        lst: List[List[str]] = []
        for line in self.lst:
            line = line.strip()
            if line:
                sub_lst = Text(line).do_finditer_split(PATTERN.WHITESPACES)
                lst.append(sub_lst)

        group = list(zip(*lst))
        return [sorted(set(sub_grp)) for sub_grp in group]

    def to_general_text(self) -> str:
        """
        Generate generalized text representation.

        Returns
        -------
        str
            Generalized text string with normalized whitespace.

        Notes:
            Will check this method later
        """
        result: List[str] = []
        group = self.to_group()     # noqa

        for sub_grp in group:
            if len(sub_grp) == NUMBER.ONE:
                result.append(sub_grp[INDEX.ZERO])
            else:
                ws = STRING.SPACE_CHAR
                for item in sub_grp:
                    if item.strip(STRING.SPACE_CHAR):
                        ws = item.strip(STRING.SPACE_CHAR)
                        break
                is_multi = any(len(item) > NUMBER.ONE for item in sub_grp)
                spacer = f"{ws} " if is_multi else ws
                result.append(spacer)

        return self.leading + STRING.EMPTY.join(result) + self.trailing

    def get_pattern(self) -> "TextPattern":
        """
        Generate regex pattern for the text node.

        Returns
        -------
        TextPattern
            Regex pattern object representing the text node.
        """
        if self.is_identical:
            return TextPattern(self.first_text)
        elif self.is_closed_to_identical:
            clean_lst = [item.strip() for item in self.lst if item.strip()]
            txt = clean_lst[INDEX.ZERO]
            return TextPattern(self.leading + txt + self.trailing)
        return TextPattern(self.to_general_text())

    def get_snippet(self) -> str:
        """
        Generate snippet representation for the text node.

        Returns
        -------
        str
            Snippet string representation of the text node.
        """
        if self.is_identical:
            return self.first_text
        elif self.is_closed_to_identical:
            clean_lst = [item.strip() for item in self.lst if item.strip()]
            txt = clean_lst[INDEX.ZERO]
            return self.leading + txt + self.trailing
        return self.to_general_text()


class DChange:
    """
    Represents a diff change node for text fragments.

    This class models a changed fragment in a diff comparison. It stores
    the original text, tracks whether the fragment can be empty, and
    provides methods to generate regex patterns and snippet
    representations.

    Parameters
    ----------
    text : str
        The initial text fragment.
    var : str
        Variable name used in snippet/pattern generation.

    Attributes
    ----------
    var : str
        Variable name for the change node.
    lst : list of str
        List of non-empty text fragments associated with this change.
    text : str
        Original text fragment.
    is_empty : bool
        Flag indicating whether the fragment is empty.
    """

    def __init__(self, text: str, var: str) -> None:
        self.var: str = var
        self.lst: List[str] = []
        self.text: str = text
        self.is_empty: bool = text.strip() == STRING.EMPTY

        if not self.is_empty:
            self.lst.append(text)

    def add(self, text: str) -> None:
        """
        Add a new text fragment to the change node.

        Parameters
        ----------
        text : str
            Text fragment to add.

        Side Effects
        ------------
        - Updates `is_empty` if the provided text is empty.
        - Appends non-empty text to `lst` if not already present.
        """
        if text.strip() == STRING.EMPTY:
            self.is_empty = True
        elif text not in self.lst:
            self.lst.append(text)

    def get_pattern(self) -> "ElementPattern":
        """
        Generate a regex pattern for the change node.

        Returns
        -------
        ElementPattern
            Regex pattern object built from the snippet.
        """
        snippet = self.get_snippet()
        return ElementPattern(snippet)

    def get_snippet(self) -> str:
        """
        Generate a snippet representation of the change node.

        Returns
        -------
        str
            Snippet string representation.
        """
        factory = TranslatedPattern.do_factory_create(*self.lst)
        snippet = factory.get_template_snippet(var=self.var)

        if self.is_empty:
            snippet = f"{snippet[:-INDEX.ONE]}, or_empty)"

        return snippet
