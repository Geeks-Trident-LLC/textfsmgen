from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List


# ------------------------------------------------------------
# 1. CLI options (raw)
# ------------------------------------------------------------
@dataclass
class CliOptions:
    raw: Dict[str, Any] = field(default_factory=dict)


# ------------------------------------------------------------
# 2. Builder section
# ------------------------------------------------------------
@dataclass
class BuilderSection:
    name: str
    params: Dict[str, Any]

    # freeform-only
    snippet: Optional[str] = None
    snippet_file: Optional[str] = None

    # common
    sample: Optional[str] = None
    sample_file: Optional[str] = None

    built: bool = False
    warning: Optional[str] = None

    # outputs
    template: Optional[str] = None
    result: Optional[Any] = None  # list or dict depending on builder


# ------------------------------------------------------------
# 3. Generated config section
# ------------------------------------------------------------
@dataclass
class GeneratedConfig:
    stream: Optional[str] = None  # "console" or "io"
    path: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None


# ------------------------------------------------------------
# 4. Golden test section (write mode)
# ------------------------------------------------------------
@dataclass
class GoldenFile:
    path: Optional[str] = None
    content: Optional[str] = None


@dataclass
class GoldenTestSection:
    path: Optional[str] = None
    manifest: Optional[GoldenFile] = None
    inputs: Optional[Dict[str, Any]] = None
    expected_results: Optional[Dict[str, Any]] = None
    expected: Optional[Dict[str, Any]] = None


# ------------------------------------------------------------
# 5. Golden test dry run section
# ------------------------------------------------------------
@dataclass
class GoldenTestDryRun:
    lines: List[str] = field(default_factory=list)


# ------------------------------------------------------------
# 6. Debug section
# ------------------------------------------------------------
@dataclass
class DebugSection:
    text: Optional[str] = None


# ------------------------------------------------------------
# 7. Status section
# ------------------------------------------------------------
@dataclass
class StatusSection:
    kind: str                 # "success" | "warning" | "error"
    message: Optional[str]
    exit_code: int


# ------------------------------------------------------------
# 8. Show section
# ------------------------------------------------------------
@dataclass
class ShowSection:
    raw: Optional[str] = None          # raw --show expression
    resolved: Optional[dict] = None    # sample/snippet/template/result/tabular


# ------------------------------------------------------------
# 9. Save section (write mode)
# ------------------------------------------------------------
@dataclass
class SaveSection:
    raw: Optional[str] = None                  # raw --save expression
    files: Optional[List[dict]] = None         # [{"kind": "...", "path": "..."}]


# ------------------------------------------------------------
# 10. Save dry run section
# ------------------------------------------------------------
@dataclass
class SaveDryRunSection:
    lines: List[str] = field(default_factory=list)


# ------------------------------------------------------------
# 11. Top-level JSON workflow
# ------------------------------------------------------------
@dataclass
class JsonWorkflow:
    cli_options: Optional[CliOptions] = None
    builder: Optional[BuilderSection] = None

    generated_config: Optional[GeneratedConfig] = None
    golden_test: Optional[GoldenTestSection] = None
    golden_test_dry_run: Optional[GoldenTestDryRun] = None

    debug: Optional[DebugSection] = None
    status: Optional[StatusSection] = None

    show: Optional[ShowSection] = None
    save: Optional[SaveSection] = None
    save_dry_run: Optional[SaveDryRunSection] = None

    # --------------------------------------------------------
    # Serialization
    # --------------------------------------------------------
    def to_json(self) -> str:
        return json.dumps(
            self._to_dict(),
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
        )

    def _to_dict(self) -> Dict[str, Any]:
        def convert(obj):
            if obj is None:
                return None
            if isinstance(obj, (str, int, float, bool)):
                return obj
            if isinstance(obj, list):
                return [convert(x) for x in obj]
            if isinstance(obj, dict):
                return {k: convert(v) for k, v in obj.items()}
            if hasattr(obj, "__dict__"):
                return {k: convert(v) for k, v in obj.__dict__.items()}
            return obj

        return convert(self)

    # --------------------------------------------------------
    # Mutators
    # --------------------------------------------------------
    def add_cli_options(self, cli_options: dict) -> None:
        self.cli_options = CliOptions(raw=cli_options)

    def add_builder(
        self,
        *,
        name: str,
        params: dict,
        snippet: str | None = None,
        snippet_file: str | None = None,
        sample: str | None = None,
        sample_file: str | None = None,
        built: bool = False,
        warning: str | None = None,
        template: str | None = None,
        result: Any = None,
    ) -> None:
        self.builder = BuilderSection(
            name=name,
            params=params,
            snippet=snippet,
            snippet_file=snippet_file,
            sample=sample,
            sample_file=sample_file,
            built=built,
            warning=warning,
            template=template,
            result=result,
        )

    def update_builder(
        self,
        *,
        name: str | None = None,
        snippet: str | None = None,
        built: bool | None = None,
        warning: str | None = None,
        template: str | None = None,
        result: Any | None = None,
    ) -> None:
        if self.builder is None:
            return

        mapping = {
            "name": name,
            "snippet": snippet,
            "built": built,
            "warning": warning,
            "template": template,
            "result": result,
        }

        for attr, val in mapping.items():
            if val is not None:
                setattr(self.builder, attr, val)

    def add_generated_config(
        self,
        *,
        stream: str,
        path: Optional[str],
        payload: dict,
    ) -> None:
        self.generated_config = GeneratedConfig(
            stream=stream,
            path=path,
            payload=payload,
        )

    def add_golden_test(
        self,
        *,
        path: str,
        manifest: dict,
        inputs: dict,
        expected_results: dict,
        expected: dict,
    ) -> None:
        self.golden_test = GoldenTestSection(
            path=path,
            manifest=GoldenFile(
                path=manifest.get("path"),
                content=manifest.get("content"),
            ),
            inputs=inputs,
            expected_results=expected_results,
            expected=expected,
        )

    def add_golden_test_dry_run(self, lines: list[str]) -> None:
        self.golden_test_dry_run = GoldenTestDryRun(lines=lines or [])

    def add_debug(self, text: str) -> None:
        self.debug = DebugSection(text=text)

    def set_status(self, *, kind: str, message: str, exit_code: int) -> None:
        self.status = StatusSection(
            kind=kind,
            message=message,
            exit_code=exit_code,
        )

    def add_save_dry_run(self, lines: list[str]) -> None:
        self.save_dry_run = SaveDryRunSection(lines=lines or [])

    def add_save(self, raw: str | None = None, files: list[dict] | None = None) -> None:
        self.save = SaveSection(raw=raw, files=files or [])

    def append_save_file(self, file: dict) -> None:
        if self.save is None:
            self.save = SaveSection(raw=None, files=[])
        if self.save.files is None:
            self.save.files = []
        self.save.files.append(file)

    def add_show(self, raw: str | None = None, resolved: dict | None = None) -> None:
        self.show = ShowSection(raw=raw, resolved=resolved or {})
