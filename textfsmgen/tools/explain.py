
import traceback

import re

from textfsmgen.libs.generic import StatusString
from textfsmgen.libs.text import (
    dedent_and_strip,
    decorate_text,
    enclose_string,
    wrap_text_block
)

from textfsmgen.libs.pattern import ParsedKeywordMappingName

from textfsmgen.core.patterns import LinePattern

from textfsmgen.engine.doc import TokenDoc


class SnippetExplanation:
    def __init__(self, snippet: str, test_samples):
        self._raw_snippet = str(snippet)
        self._test_samples = test_samples

        self._snippet = snippet.strip()
        self._normalized = self._raw_snippet.strip()

        self._explanation = ""
        self._ready = False

        self._keyword = ""
        self._allow_empty = False

        self._status = StatusString()
        self._parser = None

        self.explain()

    def __bool__(self): return self._ready

    def __len__(self): return 1 if self._ready else 0

    @property
    def raw_snippet(self): return self._raw_snippet

    @property
    def data(self): return self._normalized

    @property
    def status(self): return self._status

    @property
    def test_samples(self): return self._test_samples

    @property
    def explanation(self):
        return self._explanation if self else str(self._status)

    @property
    def is_ready(self): return self._ready

    def explain(self):
        """Validate, parse, and build the explanation for this snippet."""
        if not self.validate():
            return

        if not self.parse_snippet():
            return

        self.build_explanation()

    def validate(self):
        """Validate snippet and test data before attempting explanation."""
        if not self._normalized:
            self._status = StatusString(
                "Provided snippet is empty.  Cannot explain.",
                status="incomplete"
            )
            return False

        if not any(self._test_samples):
            self._status = StatusString(
                "Provided test data are empty.  Cannot explain without test data.",
                status="incomplete"
            )
            return False

        if re.search(r"\w+[(][^)]*[)]", self._raw_snippet):
            return True

        width = 40 if len(self._snippet) <= 40 else 80
        header = decorate_text(self._snippet.center(width))
        usage = dedent_and_strip(
                """
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
                """
            )
        self._status = StatusString(f"{header}\n{usage}\n", status="invalid")

        return False

    def parse_snippet(self):
        """Extract keyword and parameters from the snippet."""
        keyword, raw_params = self.data[:-1].split("(", maxsplit=1)

        parser = ParsedKeywordMappingName(keyword)

        if not parser:
            self._status = StatusString(str(parser.status), status="invalid")
            return False

        params = re.split(r"\s*,\s*", raw_params.lower())
        if "or_empty" in params:
            self._allow_empty = True

        self._parser = parser
        self._keyword = keyword

        return True

    def generate_operation_section(self) -> str:
        """Build the formatted Operation: section for this keyword."""
        doc = TokenDoc(self._keyword, or_empty=self._allow_empty)
        usage = doc.usage
        return wrap_text_block(usage, subject="Operation:")

    def generate_result_section(self) -> StatusString:
        """Evaluate the snippet's pattern against all test samples."""
        pattern = LinePattern(self._normalized)

        # Ensure the generated pattern is a valid regex
        try:
            re.compile(pattern)
        except Exception as ex:
            trace = traceback.format_exc()
            return StatusString(
                trace,
                status="error",
                reason=f"{type(ex).__name__}: {ex}",
            )

        results = [bool(re.fullmatch(pattern, sample)) for sample in
                   self._test_samples]

        if all(results):
            return StatusString(str(results), status="passed")

        expected = [True] * len(results)
        return StatusString(
            str(results),
            status="failed",
            reason=str(expected),
        )

    def build_explanation(self):
        """Assemble the full explanation block for the snippet."""
        pattern = LinePattern(self._normalized)
        width = 40 if len(self._snippet) <= 40 else 80
        header = decorate_text(self._snippet.center(width))

        lines = [
            header,
            f"Pattern:   r{enclose_string(pattern)}",
            self.generate_operation_section(),
            "Explanation:",
            f"    lst = {self._test_samples}",
            "",
            "Evaluating:",
            "    [bool(re.fullmatch(pattern, item)) for item in lst]",
            ""
        ]

        result = self.generate_result_section()

        # Successful evaluation
        if result:
            self._ready = True
            self._status = StatusString(status="complete")
            lines.append("Produces:")
            lines.append(f"    {result}")
            self._explanation = "\n".join(lines)
            return

        # Regex compilation or evaluation error
        if result.error == "error":
            error_header = decorate_text(result.reason)
            self._ready = False
            self._status = StatusString(
                f"{error_header}\n\n{result}", status="error"
            )
            return

        # Failed Match
        lines.extend([
            decorate_text("Failed Match".center(40)),
            "Expected:",
            f"    {result.reason}",
            "Received:",
            f"    {result}"
        ])
        self._status = StatusString("\n".join(lines), status="failed")
