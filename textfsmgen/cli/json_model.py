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


@dataclass
class APIParams:
    merged: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BuildResult:
    result: Dict[str, Any] = field(default_factory=dict)


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
# 8. Show section
# ------------------------------------------------------------
@dataclass
class ShowSection:
    raw: Optional[str] = None  # raw --show expression
    resolved: Optional[dict] = None  # sample/snippet/template/result/tabular


# ------------------------------------------------------------
# 9. Save section (write mode)
# ------------------------------------------------------------
@dataclass
class SaveSection:
    raw: Optional[str] = None  # raw --save expression
    files: Optional[List[dict]] = None  # [{"kind": "...", "path": "..."}]


# ------------------------------------------------------------
# 10. Save dry run section
# ------------------------------------------------------------
@dataclass
class SaveDryRunSection:
    lines: List[str] = field(default_factory=list)


# ------------------------------------------------------------
# 12. JsonState
# ------------------------------------------------------------
@dataclass
class JsonState:
    """
    Represents the high-level workflow state for JSON mode.
    - name:    current step name
    - status:  "" or "abort"
    - message: human-readable message (mainly for abort)
    - output:  human-readable output (template, result, warnings, etc.)
    """

    name: str = ""
    status: str = ""
    message: str = ""
    output: dict = field(default_factory=dict)
    exit_code: int = 0


# ------------------------------------------------------------
# 11. Top-level JSON workflow
# ------------------------------------------------------------
@dataclass
class JsonWorkflow:
    cli_options: Optional[CliOptions] = None
    api_params: Optional[APIParams] = None
    build_result: Optional[BuildResult] = None

    generated_config: Optional[GeneratedConfig] = None
    golden_test: Optional[GoldenTestSection] = None
    golden_test_dry_run: Optional[GoldenTestDryRun] = None

    debug: Optional[DebugSection] = None

    show: Optional[ShowSection] = None
    save: Optional[SaveSection] = None
    save_dry_run: Optional[SaveDryRunSection] = None

    # ⭐ NEW: your workflow state block
    state: JsonState = field(default_factory=JsonState)

    # --------------------------------------------------------
    # Serialization
    # --------------------------------------------------------
    def to_json(self) -> str:
        """
        Serialize the workflow to JSON.

        If validating=True:
            - Ensure that required fields are present
            - Raise an exception if the workflow is incomplete
        """
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
