from typing import Optional, List
from io import StringIO
import re
from dataclasses import dataclass

from textfsm import TextFSM

from textfsmgen import LineParser
from textfsmgen.libs import text, file
from textfsmgen.exceptions import raise_runtime_error

from textfsmgen.engine.category import CategoryLinesTranslator
from textfsmgen.engine.tabular import TabularTranslator


@dataclass
class BuildResult:
    snippet: str
    template: str
    result: List[dict]
    warning: Optional[str] = None


class BuilderBase:
    """
    Common base for all builders.

    Contract:
    - .sample: Optional[str]
    - .snippet: str
    - .template: str
    - .result: List[dict]
    - .warning: Optional[str]
    """

    def __init__(self) -> None:
        self.sample: Optional[str] = None
        self.snippet: str = ""
        self.template: str = ""
        self.result: List[dict] = []
        self.warning: Optional[str] = None

    def __bool__(self) -> bool:
        return bool(self.template)

    def set_sample(self, sample: str, **params) -> None:  # pragma: no cover (interface)
        raise NotImplementedError

    def build(self) -> None:  # pragma: no cover (interface)
        raise NotImplementedError


class FreeFormBuilder(BuilderBase):
    """
    Build a TextFSM template from free‑form snippet text.
    """

    def __init__(self) -> None:
        super().__init__()
        self.variables: List = []
        self.statements: List[str] = []
        self.bare_template: str = ""

    def __repr__(self):
        return (
            f"<FreeFormBuilder snippet={bool(self.snippet)} "
            f"template={bool(self.template)} result={len(self.result)} "
            f"warning={bool(self.warning)}>"
        )

    # ------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------

    def set_snippet(self, snippet: str) -> None:
        self.snippet = text.list_to_text(snippet)
        self._reset_core()

    def set_snippet_file(self, path: str) -> None:
        self.snippet = text.list_to_text(file.read(path))
        self._reset_core()

    def set_sample(self, sample: str) -> None:  # noqa
        # IMPORTANT: do NOT overwrite snippet
        self.sample = text.list_to_text(sample)

    def set_sample_file(self, path: str) -> None:
        self.sample = text.list_to_text(file.read(path))

    def build(self) -> None:
        # Do not clear sample here; only reset internal template state
        self._reset_core()
        self._prepare()

        if not self.variables:
            self.warning = (
                "Snippet does not contain any variable definitions.\n"
                "A valid snippet must include at least one variable, e.g.:\n"
                "  + 'San Jose, CA' → no variables\n"
                "  + 'words(var_city), word(var_state)' → contains variables"
            )
            return

        variables = "\n".join(v.value for v in self.variables)
        template_def = "\n".join(self.statements)

        if not template_def.strip().startswith("Start"):
            template_def = "Start\n" + template_def

        bare = variables + "\n\n" + template_def

        self.bare_template = self._reformat(bare)
        self.template = self.bare_template

        # FreeFormBuilder does not raise on validation
        self.validate(raise_on_error=False)

    def validate(self, raise_on_error: bool = False) -> None:
        """
        Validate that the template can parse the sample.
        FreeFormBuilder never raises; Category/Tabular may.
        """
        self.result = []
        self.warning = None

        try:
            stream = StringIO(self.template)
            parser = TextFSM(stream)

            if self.sample is None:
                self.warning = (
                    "No sample was provided. The generated template was not tested "
                    "against any input data."
                )
                return

            if not self.sample.strip():
                self.warning = (
                    "The provided sample is empty. The generated template could not be "
                    "validated against empty input."
                )
                return

            parsed = parser.ParseTextToDicts(self.sample)

            if not parsed:
                self.warning = (
                    "The generated template did not match any records in the provided "
                    "sample. This usually means the snippet does not describe the "
                    "structure of the sample."
                )
                return

            self.result = parsed

        except Exception as ex:
            self.warning = (
                f"Failed to parse the sample using the generated template: {ex}. "
                "This usually indicates that the snippet does not match the sample format."
            )
            if raise_on_error:
                raise_runtime_error(obj="TemplateBuilderError", msg=self.warning)

    # ------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------

    def _reset_core(self) -> None:
        self.variables = []
        self.statements = []
        self.bare_template = ""
        self.template = ""
        self.result = []
        self.warning = None

    def _prepare(self) -> None:
        for line in self.snippet.splitlines():
            line = line.rstrip()

            parsed = LineParser(line)
            stmt = parsed.statement()

            if stmt.endswith(r"\$$"):
                stmt = stmt[:-3] + "$$"
            elif r"\$$ -> " in stmt:
                stmt = stmt.replace(r"\$$ -> ", "$$ -> ")
            stmt = stmt.replace(r"\$", r"\x24")

            if stmt:
                self.statements.append(stmt)
            else:
                if self.statements:
                    self.statements.append(stmt)

            for pl_var in parsed.variables:
                exists = any(
                    v.name == pl_var.name and v.pattern == pl_var.pattern
                    for v in self.variables
                )
                if not exists:
                    self.variables.append(pl_var)

    def _reformat(self, template: str) -> str:
        if not template:
            return ""

        lines = []
        pattern = r"[\r\n]+[A-Za-z]\w*([\r\n]+|$)"
        start = 0
        last = None

        for match in re.finditer(pattern, template):
            before = match.string[start : match.start()]
            state = match.group().strip()

            if before.strip():
                for line in before.splitlines():
                    if line.strip():
                        lines.append(line)

            lines.append("")
            lines.append(state)
            start = match.end()
            last = match

        if last and lines:
            after = last.string[last.end() :]
            if after.strip():
                for line in after.splitlines():
                    if line.strip():
                        lines.append(line)

        return "\n".join(lines)

    # ------------------------------------------------------------
    # BuildResult
    # ------------------------------------------------------------

    def to_result(self) -> BuildResult:
        return BuildResult(
            snippet=self.snippet,
            template=self.template,
            result=self.result,
            warning=self.warning,
        )


class CategoryBuilder(BuilderBase):
    def __init__(self) -> None:
        super().__init__()
        self.count: int = 1
        self.separator: str = ":"
        self.starting_from: Optional[str] = None
        self.ending_at: Optional[str] = None
        self.replacing_rules: Optional[str] = None

    def __repr__(self):
        return (
            f"<CategoryBuilder snippet={bool(self.snippet)} "
            f"template={bool(self.template)} "
            f"result={len(self.result)} warning={bool(self.warning)}>"
        )

    def set_sample(
        self,
        sample: str,
        count: int = 1,
        separator: str = ":",
        starting_from: Optional[str] = None,
        ending_at: Optional[str] = None,
        replacing_rules: Optional[str] = None,
    ) -> None:
        self.sample = text.list_to_text(sample)
        self._set_params(count, separator, starting_from, ending_at, replacing_rules)
        self._reset_core()

    def set_sample_file(
        self,
        sample_file: str,
        count: int = 1,
        separator: str = ":",
        starting_from: Optional[str] = None,
        ending_at: Optional[str] = None,
        replacing_rules: Optional[str] = None,
    ) -> None:
        self.sample = text.list_to_text(file.read(sample_file))
        self._set_params(count, separator, starting_from, ending_at, replacing_rules)
        self._reset_core()

    def build(self) -> None:
        translator = CategoryLinesTranslator(
            self.sample or "",
            count=self.count,
            separator=self.separator,
            starting_from=self.starting_from,
            ending_at=self.ending_at,
            replacing_rules=self.replacing_rules,
        )

        self.snippet = translator.to_template_snippet()

        freeform_builder = FreeFormBuilder()
        freeform_builder.set_snippet(self.snippet)
        freeform_builder.set_sample(self.sample or "")
        freeform_builder.build()

        # Strict validation
        freeform_builder.validate(raise_on_error=True)

        self.template = freeform_builder.template
        self.result = freeform_builder.result

    def to_result(self) -> BuildResult:
        return BuildResult(
            snippet=self.snippet,
            template=self.template,
            result=self.result,
            warning=self.warning,
        )

    # ------------------------------------------------------------

    def _set_params(
        self,
        count: int,
        separator: str,
        starting_from: Optional[str],
        ending_at: Optional[str],
        replacing_rules: Optional[str],
    ) -> None:
        self.count = count
        self.separator = separator
        self.starting_from = starting_from
        self.ending_at = ending_at
        self.replacing_rules = replacing_rules

    def _reset_core(self) -> None:
        self.snippet = ""
        self.template = ""
        self.result = []
        self.warning = None


class TabularBuilder(BuilderBase):
    def __init__(self) -> None:
        super().__init__()

        self.column_divider: str = ""
        self.column_count: int = 0
        self.column_widths: Optional[str] = None
        self.headers: Optional[str] = None
        self.header_rows: Optional[str] = None
        self.custom_header_text: str = ""
        self.starting_from: Optional[str] = None
        self.ending_at: Optional[str] = None
        self.has_header_row: bool = True
        self.replacing_rules: Optional[str] = None

    def __repr__(self):
        return (
            f"<TabularBuilder snippet={bool(self.snippet)} "
            f"template={bool(self.template)} "
            f"result={len(self.result)} warning={bool(self.warning)}>"
        )

    def set_sample(
        self,
        sample: str,
        column_divider: str = "",
        column_count: int = 0,
        column_widths: Optional[str] = None,
        headers: Optional[str] = None,
        header_rows: Optional[str] = None,
        custom_header_text: str = "",
        starting_from: Optional[str] = None,
        ending_at: Optional[str] = None,
        has_header_row: bool = True,
        replacing_rules: Optional[str] = None,
    ) -> None:
        self.sample = text.list_to_text(sample)
        self._set_params(
            column_divider,
            column_count,
            column_widths,
            headers,
            header_rows,
            custom_header_text,
            starting_from,
            ending_at,
            has_header_row,
            replacing_rules,
        )
        self._reset_core()

    def set_sample_file(
        self,
        sample_file: str,
        column_divider: str = "",
        column_count: int = 0,
        column_widths: Optional[str] = None,
        headers: Optional[str] = None,
        header_rows: Optional[str] = None,
        custom_header_text: str = "",
        starting_from: Optional[str] = None,
        ending_at: Optional[str] = None,
        has_header_row: bool = True,
        replacing_rules: Optional[str] = None,
    ) -> None:
        sample = file.read(sample_file)
        self.sample = text.list_to_text(sample)
        self._set_params(
            column_divider,
            column_count,
            column_widths,
            headers,
            header_rows,
            custom_header_text,
            starting_from,
            ending_at,
            has_header_row,
            replacing_rules,
        )
        self._reset_core()

    def build(self) -> None:
        translator = TabularTranslator(
            self.sample or "",
            column_divider=self.column_divider,
            column_count=self.column_count,
            column_widths=self.column_widths,
            headers=self.headers,
            header_rows=self.header_rows,
            custom_header_text=self.custom_header_text,
            starting_from=self.starting_from,
            ending_at=self.ending_at,
            has_header_row=self.has_header_row,
            replacing_rules=self.replacing_rules,
        )

        self.snippet = translator.to_snippet()

        freeform_builder = FreeFormBuilder()
        freeform_builder.set_snippet(self.snippet)
        freeform_builder.set_sample(self.sample or "")
        freeform_builder.build()

        # Strict validation
        freeform_builder.validate(raise_on_error=True)

        self.template = freeform_builder.template
        self.result = freeform_builder.result or []

    def to_result(self) -> BuildResult:
        return BuildResult(
            snippet=self.snippet,
            template=self.template,
            result=self.result,
            warning=self.warning,
        )

    # ------------------------------------------------------------

    def _set_params(
        self,
        column_divider: str,
        column_count: int,
        column_widths: Optional[str],
        headers: Optional[str],
        header_rows: Optional[str],
        custom_header_text: str,
        starting_from: Optional[str],
        ending_at: Optional[str],
        has_header_row: bool,
        replacing_rules: Optional[str],
    ) -> None:
        self.column_divider = column_divider
        self.column_count = column_count
        self.column_widths = column_widths
        self.headers = headers
        self.header_rows = header_rows
        self.custom_header_text = custom_header_text
        self.starting_from = starting_from
        self.ending_at = ending_at
        self.has_header_row = has_header_row
        self.replacing_rules = replacing_rules

    def _reset_core(self) -> None:
        self.snippet = ""
        self.template = ""
        self.result = []
        self.warning = None
