import re

from textfsmgen.core.patterns import LinePattern
from textfsmgen.exceptions import TemplateParsedLineError


class LineParser:
    def __init__(self, txt):
        self.text = str(txt)
        self.line = ""
        self.template_op = ""
        self.ignore_case = False
        self.is_comment = False
        self.comment = ""
        self.is_kept = False
        self.kept = ""
        self.variables = list()
        self._parse()

    @property
    def is_empty(self) -> bool:
        """Check whether the line is empty."""
        return not bool(self.line.strip())

    @property
    def is_word(self) -> bool:
        """Check whether the text represents a single word."""
        return bool(re.match(r"^[A-Za-z]\w*$", self.text.strip()))

    @property
    def no_letters(self) -> bool:
        """Check whether the line contains no alphabetic characters."""
        if self.is_empty:
            return False
        return bool(re.match(r"[^a-z0-9]+$", self.line, flags=re.I))

    def statement(self) -> str:
        """Construct the template statement for the current line."""
        if self.is_empty:
            return ""
        if self.is_comment:
            return self.comment
        if self.is_kept:
            return self.kept
        if self.is_word:
            return self.text

        line_pattern = LinePattern(self.line, ignore_case=self.ignore_case)

        if line_pattern.variables:
            self.variables = line_pattern.variables[:]
            statement = line_pattern.statement
        else:
            try:
                re.compile(self.line)
                if re.search(r"\s", self.line):
                    statement = line_pattern
                else:
                    if "(" in self.line and self.line.endswith(")"):
                        statement = (
                            line_pattern
                            if not line_pattern.endswith(")")
                            else self.line
                        )
                    else:
                        statement = self.line
            except Exception as ex:  # noqa
                statement = line_pattern

        # Normalize case-insensitive flag placement
        statement = statement.replace("(?i)^", "^(?i)")

        # Ensure proper start anchor spacing
        spacer = "  " if statement.startswith("^") else "  ^"
        statement = f"{spacer}{statement}"

        # Ensure proper end anchor
        if statement.endswith("$") and not statement.endswith(r"\$"):
            statement = f"{statement}$"

        # Append template operator if present
        if self.template_op:
            statement = f"{statement} -> {self.template_op}"

        return statement

    def _parse(self) -> None:
        """Parse the line and reapply formatting for template construction."""
        lst = self.text.rsplit(" -> ", 1)
        if len(lst) == 2:
            tmpl_op = lst[-1].strip()
            first, *remaining = tmpl_op.split(" ", 1)

            mapping = {"norecord": "NoRecord", "clearall": "ClearAll"}
            if "." in first:
                pat = (
                    r"(?P<lop>next|continue|error)\."
                    r"(?P<rop>norecord|record|clearall|clear)$"
                )
                match = re.match(pat, first, flags=re.I)
                if match:
                    lop = match.group("lop").title()
                    rop = match.group("rop").title()
                    rop = mapping.get(rop.lower(), rop)
                    op = f"{lop}.{rop}"
                else:
                    op = first
                tmpl_op = f"{op} {''.join(remaining)}"
            else:
                pat = r"(next|continue|error|norecord|record|clearall|clear)$"
                if re.match(pat, first, flags=re.I):
                    op = first.title()
                    op = mapping.get(op.lower(), op)
                else:
                    op = first
                tmpl_op = f"{op} {''.join(remaining)}"

            self.template_op = tmpl_op.strip()
            txt = lst[0].rstrip()
        else:
            txt = self.text

        flag_pat = r"^(?P<flag>(ignore_case|comment|keep)__+ )?(?P<line>.*)"
        match = re.match(flag_pat, txt, flags=re.I)
        if not match:
            raise TemplateParsedLineError(f"Invalid format - {self.text!r}")

        value = match.group("flag") or ""
        flag = value.lower().strip().rstrip("_")
        self.ignore_case = flag == "ignore_case"
        self.is_comment = flag == "comment"
        self.is_kept = flag == "keep"
        self.line = match.group("line") or ""

        if self.is_comment:
            prefix = "  " if value.count("_") == 2 else ""
            self.comment = f"{prefix}# {self.line}"

        if self.is_kept:
            self.kept = f"  ^{self.line.strip().lstrip('^')}"
