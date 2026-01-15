"""
textfsmgen.gpiterative
======================

Iterative grammar pattern utilities for TextFSM template generation.

This module provides classes and functions to iteratively construct,
refine, and validate grammar patterns used in parsing tabular or
structured text. It is designed to support incremental template
building, where grammar rules evolve step by step based on input
lines, column layouts, and parsing feedback.

The iterative approach allows developers to:
- Start with baseline grammar fragments.
- Expand or adjust rules as new parsing cases are encountered.
- Validate intermediate grammars against sample text.
- Produce robust TextFSM templates that handle variations in spacing,
  dividers, and column alignment.


Notes
-----
- This module complements `textfsmgen.gp` and `textfsmgen.gpcommon`,
  focusing specifically on iterative refinement strategies.
- It is intended for advanced template authors who need fine-grained
  control over grammar evolution.
- Error handling is designed to provide diagnostic feedback for each
  refinement step, aiding debugging and template tuning.
"""

import re

from typing import List, Tuple, Optional

from textfsmgen.deps import regexapp_TextPattern as TextPattern

from textfsmgen.deps import genericlib_STRING as STRING     # noqa
from textfsmgen.deps import genericlib_PATTERN as PATTERN   # noqa
from textfsmgen.deps import genericlib_NUMBER as NUMBER     # noqa
from textfsmgen.deps import genericlib_SYMBOL as SYMBOL     # noqa

from textfsmgen.deps import genericlib_text_module as text
from textfsmgen.deps import genericlib_get_ref_pattern_by_name as get_ref_pattern_by_name

from textfsmgen.gp import TranslatedPattern
from textfsmgen.gp import LData
from textfsmgen.exceptions import RuntimeException


class SnippetElement(RuntimeException):
    """
    Represents a parsed snippet element used in template generation.

    A `SnippetElement` encapsulates a single grammar element with metadata
    about whether it is captured, kept, or empty. It provides utilities
    to parse element text, split/join sub-snippets, and generate regex
    or template representations.

    Parameters
    ----------
    element_txt : str
        Raw element text to be parsed.
    trailing : str, optional
        Trailing characters (e.g., whitespace or punctuation).

    Attributes
    ----------
    element_txt : str
        Original element text.
    trailing : str
        Trailing characters.
    name : str
        Element name.
    var_name : str
        Variable name associated with the element.
    value : str
        Value string extracted from the element.
    is_captured : bool
        Whether the element is marked as captured (`cvar`).
    is_kept : bool
        Whether the element is marked as kept (`kvar`).
    is_empty : bool
        Whether the element is marked as empty (`Cvar` or `Kvar`).
    """

    def __init__(self, element_txt: str, trailing: str = "") -> None:
        self.element_txt = element_txt
        self.trailing = trailing
        self.name = STRING.EMPTY
        self.var_name = STRING.EMPTY
        self.value = STRING.EMPTY

        self.is_captured = False
        self.is_kept = False
        self.is_empty = False

        self.parse()

    def __call__(self, *args, **kwargs) -> "SnippetElement":
        """Return a new instance of SnippetElement."""
        return self.__class__(*args, **kwargs)

    @property
    def var_index(self) -> int:
        """
        Extract numeric index from the variable name.

        Returns
        -------
        int
            Parsed index value. Returns 0 if no numeric suffix is found.
        """
        match = re.search(r"[0-9]+(_[0-9]+)?$", self.var_name)
        if match:
            matched_txt = match.group()
            if matched_txt.isdigit():
                return int(matched_txt)
            first, last = matched_txt.split(STRING.UNDERSCORE_CHAR, maxsplit=1)
            return int(first) * NUMBER.TEN + int(last)
        return NUMBER.ZERO

    def parse(self) -> None:
        """
        Parse the element text into name, variable, and value components.

        Raises
        ------
        RuntimeException
            If the element text does not match the expected pattern.
        """
        pat = (r"(?P<name>[a-zA-Z]+(_[a-zA-Z]+)*)[(] *"
               r"(?P<check>[cCkK]?var)=(?P<var_name>.+), +"
               r"value=(?P<value>.+) *[)]")
        match = re.match(pat, self.element_txt)
        if not match:
            self.raise_runtime_error(msg=f"Invalid element text\n{self.element_txt}")

        check = match.group("check")
        if check.lower() == "cvar":
            self.is_captured = True
            self.is_empty = check == "Cvar"
        elif check.lower() == "kvar":
            self.is_kept = True
            self.is_empty = check == "Kvar"

        self.name = match.group("name")
        self.var_name = match.group("var_name")
        self.value = match.group("value")

    def set_captured(self) -> None:
        """Mark element as captured (`cvar`)."""
        self.is_captured = True
        self.is_kept = False

    def set_kept(self) -> None:
        """Mark element as kept (`kvar`)."""
        self.is_captured = False
        self.is_kept = True

    def set_empty(self) -> None:
        """Mark element as empty (`Cvar` or `Kvar`)."""
        self.is_empty = True

    def split(self, splitter: str = "", ref_index: int = 0) -> List["SnippetElement"]:
        """
        Split the element value into sub-snippets.

        Parameters
        ----------
        splitter : str, optional
            Custom splitter character(s). Defaults to punctuation pattern.
        ref_index : int, optional
            Reference index for variable naming.

        Returns
        -------
        list[SnippetElement]
            List of new snippet elements created from the split value.
        """
        pat = f"[{re.escape(splitter)}]+" if splitter else PATTERN.PUNCTS
        separators = re.findall(pat, self.value)
        items = re.split(pat, self.value)

        lst: List[str] = []
        for index, item in enumerate(items):
            if index < len(items) - NUMBER.ONE:
                if item:
                    lst.append(item)
                lst.append(separators[index])
            else:
                if item:
                    lst.append(item)

        result: List[SnippetElement] = []
        for index, item in enumerate(lst):
            new_var_name = f"v{ref_index + index + 1}" if ref_index else f"{self.var_name}{index}"
            pat_obj = TranslatedPattern.do_factory_create(item)
            sub_editable_snippet = pat_obj.get_readable_snippet(var=new_var_name)
            trailing = self.trailing if index == len(lst) - NUMBER.ONE else STRING.EMPTY
            result.append(self(sub_editable_snippet, trailing=trailing))

        return result

    def join(self, *args: "SnippetElement") -> "SnippetElement":
        """
        Join this element with other snippet elements.

        Parameters
        ----------
        *args : SnippetElement
            Other snippet elements to join.

        Returns
        -------
        SnippetElement
            New combined snippet element.
        """
        if args:
            txt = f"{self.value}{self.trailing}"
            for arg in args:
                txt = f"{txt}{arg.value}{arg.trailing}"
            txt = txt.strip()
            actual_txt = txt.replace("_SYMBOL_LEFT_PARENTHESIS_", "(")
            actual_txt = actual_txt.replace("_SYMBOL_RIGHT_PARENTHESIS_", ")")
            new_pat_obj = TranslatedPattern.do_factory_create(actual_txt)
            element_txt = new_pat_obj.get_readable_snippet(var=self.var_name)
            trailing = args[-1].trailing
        else:
            element_txt = self.element_txt
            trailing = self.trailing
        return self(element_txt, trailing=trailing)

    def to_regex(self) -> str:
        """
        Convert element to a regex pattern.

        Returns
        -------
        str
            Regex string representation of the element.
        """
        if not self.is_kept and not self.is_captured:
            return TextPattern(f"{self.value}{self.trailing}")

        pat = get_ref_pattern_by_name(self.name)
        if self.is_captured:
            pat = f"(?P<{self.var_name}>({pat})|)" if self.is_empty else f"(?P<{self.var_name}>{pat})"
        elif self.is_empty:
            pat = f"(({pat})|)"

        if self.is_empty and self.trailing:
            trailing_pat = " *" if re.match(r" +$", self.trailing) else r"\s*"
            pat = f"{pat}{trailing_pat}"
        else:
            pat = pat + TextPattern(self.trailing)
        return pat

    def to_template_snippet(self) -> str:
        """
        Convert element to a template snippet string.

        Returns
        -------
        str
            Template snippet representation.
        """
        if not self.is_kept and not self.is_captured:
            return f"{self.value}{self.trailing}"

        if self.is_captured:
            tmpl_snippet = f"{self.name}(var_{self.var_name}, or_empty)" if self.is_empty else f"{self.name}(var_{self.var_name})"
        else:
            tmpl_snippet = f"{self.name}(or_empty)" if self.is_empty else f"{self.name}()"

        if self.is_empty and self.trailing:
            ws = "zero_or_spaces()" if re.match(r" +$", self.trailing) else "zero_or_whitespaces()"
            tmpl_snippet = f"{tmpl_snippet}{ws}"
        else:
            tmpl_snippet = f"{tmpl_snippet}{self.trailing}"
        return tmpl_snippet

    def to_snippet(self) -> str:
        """
        Convert element back to its snippet string form.

        Returns
        -------
        str
            Snippet string representation.
        """
        v = "var"
        if self.is_captured or self.is_kept:
            v = "cvar" if self.is_captured else "kvar"
            v = v.title() if self.is_empty else v
        snippet = f"{self.name}({v}={self.var_name}, value={self.value}){self.trailing}"
        return snippet


class EditingSnippet(LData):
    """
    Represents an editable snippet with capture, keep, and action directives.

    This class parses an editing snippet string into structured elements,
    applies actions (join/split), and manages capture/keep directives.
    It provides utilities to convert the snippet into regex or template
    representations.

    Parameters
    ----------
    editing_snippet : str
        Raw editing snippet string containing capture, keep, action, and snippet data.

    Attributes
    ----------
    data : str
        Original editing snippet string.
    capture : str
        Capture directive.
    keep : str
        Keep directive.
    action : str
        Action directive (e.g., join, split).
    raw_data : str
        Raw snippet data extracted from the input.
    snippet : str
        Normalized snippet string.
    snippet_elements : list[SnippetElement]
        Parsed snippet elements.
    largest_index : int
        Largest variable index found among snippet elements.
    is_action_applied : bool
        Whether an action directive has been applied.
    is_keep_applied : bool
        Whether a keep directive has been applied.
    is_capture_applied : bool
        Whether a capture directive has been applied.
    """

    def __init__(self, editing_snippet: str) -> None:   # noqa
        self.data = editing_snippet
        self.capture = STRING.EMPTY
        self.keep = STRING.EMPTY
        self.action = STRING.EMPTY
        self.raw_data = STRING.EMPTY
        self.snippet = STRING.EMPTY
        self.snippet_elements: List[SnippetElement] = []

        self.largest_index = 0

        self.is_action_applied = False
        self.is_keep_applied = False
        self.is_capture_applied = False

        self.process()

    def prepare(self) -> None:
        """
        Parse the editing snippet into directives and snippet elements.

        Raises
        ------
        RuntimeException
            If the input snippet does not match the expected format.
        """
        pat = (r'capture[(](?P<capture>[^\)]*)[)] '
               r'keep[(](?P<keep>[^\)]*)[)] '
               r'action[(](?P<action>[^\)]*)[)]: '
               r'(?P<snippet>.+)')
        match = re.match(pat, self.data)
        if not match:
            self.raise_runtime_error(msg=f"Invalid argument\n{self.data}")

        self.capture = match.group("capture").strip()
        self.keep = match.group("keep").strip()
        self.action = match.group("action").strip()
        self.raw_data = match.group("snippet")
        self.snippet = self.raw_data.strip()

        pat = r"\w+\([cCkK]?var=[^\)]+, value=[^\)]+\)"
        spacers = re.split(pat, self.snippet)[NUMBER.ONE:-NUMBER.ONE]   # noqa
        items = re.findall(pat, self.snippet)
        total = len(items)

        for i, snippet_txt in enumerate(items):
            trailing = spacers[i] if i < total - NUMBER.ONE else STRING.EMPTY
            node = SnippetElement(snippet_txt, trailing=trailing)
            self.largest_index = max(self.largest_index, node.var_index)
            self.snippet_elements.append(node)

    def refresh_largest_index(self) -> None:
        """Recalculate the largest variable index among snippet elements."""
        for node in self.snippet_elements:
            self.largest_index = max(self.largest_index, node.var_index)

    def find_element(self, var_name: str) -> Tuple[int, Optional[SnippetElement]]:
        """
        Find a snippet element by variable name.

        Parameters
        ----------
        var_name : str
            Variable name to search for.

        Returns
        -------
        tuple[int, SnippetElement or None]
            Index and element if found, else (-0, None).
        """
        for index, node in enumerate(self.snippet_elements):
            if node.var_name == var_name:
                return index, node
        return -NUMBER.ZERO, None

    def apply_action_join(self, action_op: str) -> bool:
        """
        Apply a join action to merge multiple snippet elements.

        Parameters
        ----------
        action_op : str
            Action operation string (e.g., "1:3-join" or "v1,v2-join").

        Returns
        -------
        bool
            True if join applied, False otherwise.

        Raises
        ------
        RuntimeException
            If the specified range or variable names are invalid.
        """
        if not re.search("[-_]join", action_op, re.I):
            return False

        var_names = []
        grp = re.split("[-_]join", action_op, re.I)[NUMBER.ZERO]
        if re.match(r"\d+:\d+$", grp):
            first, last = grp.split(STRING.COLON_CHAR, maxsplit=NUMBER.ONE)
            var_names = [f"v{i}" for i in range(int(first), int(last) + 1)]
            if not var_names:
                self.raise_runtime_error(
                    name="EditingSnippetActionJoinRTError",
                    msg=f"Invalid range ({action_op})"
                )
        elif re.match(r"\w+(,\w+)*", grp):
            var_names = [f"v{i}" if i.isdigit() else i for i in grp.split(STRING.COMMA_CHAR)]

        first_index, first_node = self.find_element(var_names[NUMBER.ZERO])
        if first_index >= NUMBER.ZERO:
            remain_nodes = []   # noqa
            for var_name in var_names[NUMBER.ONE:]:
                index, node = self.find_element(var_name)
                if index >= NUMBER.ZERO:
                    remain_nodes.append(node)

            joint_node = first_node.join(*remain_nodes)
            self.snippet_elements[first_index] = joint_node
            self.is_action_applied = True

            for removed_node in remain_nodes:
                self.snippet_elements.remove(removed_node)

            self.refresh_largest_index()
            return True

        return self.raise_runtime_error(
            name="EditingSnippetActionJoinRTError",
            msg=f"Not found index ({action_op})"
        )

    def apply_action_split(self, action_op: str) -> bool | None:
        """
        Apply a split action to divide a snippet element.

        Parameters
        ----------
        action_op : str
            Action operation string (e.g., "v1-split,," or "2_split:;").

        Returns
        -------
        bool
            True if split applied, False otherwise.

        Raises
        ------
        RuntimeException
            If the specified variable name is not found.
        """
        if not re.search("[-_]split", action_op, re.I):
            return False

        var_name, sep = re.split("[-_]split[-_]?", action_op, maxsplit=1, flags=re.I)
        sep = re.sub("_left_parenthesis_", SYMBOL.LEFT_PARENTHESIS, sep, flags=re.I)
        sep = re.sub("_right_parenthesis_", SYMBOL.RIGHT_PARENTHESIS, sep, flags=re.I)
        var_name = f"v{var_name}" if var_name.isdigit() else var_name

        index, node = self.find_element(var_name)
        if index >= NUMBER.ZERO:
            self.refresh_largest_index()
            sub_lst = node.split(splitter=sep, ref_index=self.largest_index)
            self.snippet_elements = (
                self.snippet_elements[:index] + sub_lst + self.snippet_elements[index + NUMBER.ONE:]
            )
            self.is_action_applied = True
            self.refresh_largest_index()
            return True

        return self.raise_runtime_error(
            name="EditingSnippetActionSplitRTError",
            msg=f"Not found index ({var_name})"
        )

    def apply_action(self) -> None:
        """Apply all action directives (join/split) if present."""
        if not self.action:
            return
        for action_op in re.split(",? +", self.action):
            if re.search("join|split", action_op, re.I):
                applied = self.apply_action_join(action_op)
                if not applied:
                    self.apply_action_split(action_op)

    def _parse_items(self, directive: str):     # noqa
        """
        Parse a directive string into variable names.

        Parameters
        ----------
        directive : str
            The directive string (e.g., "1:3 orEmpty", "a,b,c").

        Returns
        -------
        tuple[list[str], bool]
            A tuple containing:
            - List of variable names (e.g., ["v1", "v2", "v3"])
            - Boolean indicating whether the `orEmpty` marker was present
        """
        items = re.split(PATTERN.SPACES, directive)
        var_names, is_empty = [], False

        for item in items:
            item = item.strip(',')
            is_empty = bool(re.search(r'[_-]?or([_-]empty)?', item, flags=re.I))
            item = re.sub(r'[_-]?or([_-]empty)?', STRING.EMPTY, item, flags=re.I)

            if re.match(r'^\d+:\d+$', item):
                first, last = item.split(STRING.COLON_CHAR, maxsplit=NUMBER.ONE)
                var_names.extend([f"v{i}" for i in range(int(first), int(last) + 1)])
            elif re.match(r'^\w+(,\w+)*$', item):
                var_names.extend([f"v{i}" if i.isdigit() else i for i in item.split(',')])

        return var_names, is_empty

    def apply_keep(self):
        """
        Apply keep rules to variables defined in the keep string.

        This method parses the `self.keep` directive into variable names,
        expands ranges, and marks the corresponding elements as kept.
        If the `orEmpty` marker is present, elements are also marked empty.

        Raises
        ------
        EditingSnippetActionKeepRTError
            If a variable range is invalid or a variable cannot be found.

        Side Effects
        ------------
        - Sets `self.is_keep_applied` to True if any keep is applied.
        - Calls `node.set_kept()` and optionally `node.set_empty()` on
          matched elements.
        """
        if not self.keep:
            return

        var_names, is_empty = self._parse_items(self.keep)

        if not var_names:
            self.raise_runtime_error(
                name="EditingSnippetActionKeepRTError",
                msg=f"Invalid keep directive ({self.keep})"
            )

        for var_name in var_names:
            index, node = self.find_element(var_name)
            if index >= NUMBER.ZERO:
                node.set_kept()
                if is_empty:
                    node.set_empty()
                self.is_keep_applied = True
            else:
                self.raise_runtime_error(
                    name="EditingSnippetActionKeepRTError",
                    msg=f"Not found index ({var_name})"
                )

    def apply_capture(self):
        """
        Apply capture rules to variables defined in the capture string.

        This method parses the `self.capture` directive into variable names,
        expands ranges, and marks the corresponding elements as captured.
        If the `orEmpty` marker is present, elements are also marked empty.

        Raises
        ------
        EditingSnippetActionCaptureRTError
            If a variable range is invalid or a variable cannot be found.

        Side Effects
        ------------
        - Sets `self.is_capture_applied` to True if any capture is applied.
        - Calls `node.set_captured()` and optionally `node.set_empty()` on
          matched elements.
        """
        if not self.capture:
            return

        var_names, is_empty = self._parse_items(self.capture)

        if not var_names:
            self.raise_runtime_error(
                name="EditingSnippetActionCaptureRTError",
                msg=f"Invalid capture directive ({self.capture})"
            )

        for var_name in var_names:
            index, node = self.find_element(var_name)
            if index >= NUMBER.ZERO:
                node.set_captured()
                if is_empty:
                    node.set_empty()
                self.is_capture_applied = True
            else:
                self.raise_runtime_error(
                    name="EditingSnippetActionCaptureRTError",
                    msg=f"Not found index ({var_name})"
                )

    def process(self):
        """
        Process the snippet by applying directives.

        Steps
        -----
        1. Prepare snippet elements.
        2. If an action directive exists, apply it.
        3. Otherwise, apply capture and keep directives.
        """
        self.prepare()
        if self.action:
            self.apply_action()
        else:
            self.apply_capture()
            self.apply_keep()

    def to_snippet(self) -> str:
        """
        Convert snippet elements into a textual snippet.

        Returns
        -------
        str
            A formatted snippet string including capture, keep, and action
            directives.
        """
        new_snippet = "".join(elmt.to_snippet() for elmt in self.snippet_elements)
        new_snippet = f"{self.leading}{new_snippet}{self.trailing}"

        cval = STRING.EMPTY if self.is_capture_applied else self.capture
        kval = STRING.EMPTY if self.is_keep_applied else self.keep
        aval = STRING.EMPTY if self.is_action_applied else self.action

        return f"capture({cval}) keep({kval}) action({aval}): {new_snippet}"

    def to_regex(self) -> str:
        """
        Convert snippet elements into a regex pattern.

        Returns
        -------
        str
            A regex string representation of the snippet.
        """
        pattern = "".join(elmt.to_regex() for elmt in self.snippet_elements)
        if self.is_leading:
            pattern = f"{PATTERN.ZOSPACES}{pattern}"
        if self.is_trailing:
            pattern = f"{pattern}{PATTERN.ZOSPACES}"
        return pattern

    def to_template_snippet(self):
        """
        Convert snippet elements into a template snippet.

        Returns
        -------
        str
            A template snippet string representation.
        """
        tmpl_snippet = "".join(elmt.to_template_snippet() for elmt in self.snippet_elements)
        return f"{self.leading}{tmpl_snippet}{self.trailing}"


class IterativeLinePattern(LData):
    """
    Represents a single line pattern in an iterative parsing process.

    This class wraps a line of text and provides methods to convert it
    into snippet, regex, or template representations. It can either
    symbolize raw text into editable snippet form or process existing
    editable snippets.

    Parameters
    ----------
    line : str
        Input line of text.
    label : str, optional
        Label used to generate variable names. Non-alphanumeric characters
        are replaced with underscores.

    Attributes
    ----------
    label : str
        Normalized label string.
    _snippet : str
        Internal snippet representation of the line.
    """

    def __init__(self, line: str, label: str = "") -> None:
        super().__init__(line)
        pat = r"[\x20-\x2f\x3a-\x40\x5b-\x60\x7b-\x7e]+"
        self.label: str = re.sub(pat, "_", str(label))
        self._snippet: str = STRING.EMPTY
        self.process()

    def __len__(self) -> int:
        """
        Return 1 if the snippet is non-empty, else 0.

        Returns
        -------
        int
            1 if snippet exists, 0 otherwise.
        """
        return int(bool(self._snippet))

    def symbolize(self) -> str:
        """
        Convert raw line into an editable snippet string.

        Splits the line by whitespace, converts each token into a
        `TranslatedPattern`, and assigns variable names based on the label.

        Returns
        -------
        str
            Editable snippet string with capture/keep/action directives.
        """
        spaces = re.findall(PATTERN.WHITESPACES, self.data)
        parts: List[str] = []

        for index, item in enumerate(re.split(PATTERN.WHITESPACES, self.data)):
            node = TranslatedPattern.do_factory_create(item)
            var_name = f"v{self.label}{index}"
            parts.append(node.get_readable_snippet(var=var_name))
            if index < len(spaces):
                parts.append(spaces[index])

        snippet = "".join(parts)
        editing_snippet = f"capture() keep() action(): {self.leading}{snippet}{self.trailing}"
        return editing_snippet

    def is_line_editable_snippet(self):
        """
        Check if the line is already in editable snippet format.

        Returns
        -------
        bool
            True if line matches editable snippet pattern, False otherwise.
        """
        pat = r'capture[(][^\)]*[)] keep[(][^\)]*[)] action[(][^\)]*[)]:.+'
        return bool(re.match(pat, self.data))

    def process(self):
        """
        Process the line into a snippet representation.

        If the line is already an editable snippet, it is parsed using
        `EditingSnippet`. Otherwise, it is symbolized from raw text.
        """
        if self.is_line_editable_snippet():
            node = EditingSnippet(self.data)
            self._snippet = node.to_snippet()
        else:
            self._snippet = self.symbolize()

    def to_snippet(self):
        """
        Convert the line into a snippet string.

        Returns
        -------
        str
            Snippet representation of the line.
        """
        node = EditingSnippet(self._snippet)
        snippet = node.to_snippet()
        return snippet

    def to_regex(self):
        """
        Convert the line into a regex pattern.

        Returns
        -------
        str
            Regex pattern string.
        """
        node = EditingSnippet(self._snippet)
        pattern = node.to_regex()
        pattern = pattern.replace('_SYMBOL_LEFT_PARENTHESIS_', re.escape('('))
        pattern = pattern.replace('_SYMBOL_RIGHT_PARENTHESIS_', re.escape(')'))
        return pattern

    def to_template_snippet(self):
        """
        Convert the line into a template snippet string.

        Returns
        -------
        str
            Template snippet representation.
        """
        node = EditingSnippet(self._snippet)
        tmpl_snippet = node.to_template_snippet()
        tmpl_snippet = tmpl_snippet.replace('_SYMBOL_LEFT_PARENTHESIS_', '(')
        tmpl_snippet = tmpl_snippet.replace('_SYMBOL_RIGHT_PARENTHESIS_', ')')
        return tmpl_snippet

    def is_captured_in_regex(self) -> bool:
        """
        Check if the regex representation contains a captured variable.

        Returns
        -------
        bool
            True if regex contains a named capture group, False otherwise.
        """
        return bool(re.search(r"[(][?]P<\w+>", self.to_regex()))

    def is_captured_in_template_snippet(self):
        """
        Check if the template snippet contains a captured variable.

        Returns
        -------
        bool
            True if template snippet contains a var_ reference, False otherwise.
        """
        pat = r'\b\w+[(][^\)]* *var_\w+'
        return bool(re.search(pat, self.to_template_snippet()))


class IterativeLinesPattern(RuntimeException):
    """
    Represents an iterative pattern composed of multiple lines or snippets.

    This class wraps a sequence of lines/snippets and provides methods
    to convert them into snippet strings, regex patterns, or template
    snippets. It delegates parsing of individual data lines to
    `IterativeLinePattern`.

    Parameters
    ----------
    *lines_or_snippets : str
        Input lines or snippet strings.

    Attributes
    ----------
    lines_or_snippets : list[str]
        Normalized list of read-only lines or snippets.
    """

    def __init__(self, *lines_or_snippets: str) -> None:
        self.lines_or_snippets: List[str] = list(text.get_list_of_readonly_lines(*lines_or_snippets))

    def to_snippet(self) -> str:
        """
        Convert lines/snippets into a combined snippet string.

        Returns
        -------
        str
            Snippet representation of all lines, joined by newlines.
        """
        snippets: List[str] = []
        for index, line_or_snippet in enumerate(self.lines_or_snippets):
            if text.Line.has_data(line_or_snippet):
                label = str(index) if index > 0 else STRING.EMPTY
                node = IterativeLinePattern(line_or_snippet, label=label)
                snippets.append(node.to_snippet())
            else:
                snippets.append(line_or_snippet)
        return "\n".join(snippets)

    def to_regex(self) -> str:
        """
        Convert lines/snippets into a combined regex pattern.

        Returns
        -------
        str
            Regex pattern string. Returns an empty string if no lines exist.
        """
        patterns: List[str] = []
        for snippet in self.lines_or_snippets:
            if text.Line.has_data(snippet):
                node = IterativeLinePattern(snippet)
                patterns.append(node.to_regex())
            else:
                patterns.append(r"[ \t\v]*")

        if patterns:
            return rf"({PATTERN.CRNL})".join(patterns)
        return STRING.EMPTY

    def to_template_snippet(self) -> str:
        """
        Convert lines/snippets into a combined template snippet.

        Returns
        -------
        str
            Template snippet string.

        Raises
        ------
        RuntimeException
            If no captured variable is found in any line.
        """
        tmpl_snippets: List[str] = []
        is_captured = False

        for snippet in self.lines_or_snippets:
            if text.Line.has_data(snippet):
                node = IterativeLinePattern(snippet)
                tmpl_snippets.append(node.to_template_snippet())
                is_captured |= node.is_captured_in_template_snippet()

        if not is_captured:
            self.raise_runtime_error(
                msg="Cannot form template snippet because no captured variable is created"
            )

        return STRING.NEWLINE.join(tmpl_snippets)
