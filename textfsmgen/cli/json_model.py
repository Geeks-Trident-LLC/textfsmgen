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
    stream: Optional[str] = None
    path: Optional[str] = None
    manifest: Optional[GoldenFile] = None
    inputs: Optional[List[str]] = None
    expected_results: Optional[List[str]] = None
    expected: Optional[List[str]] = None


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
    output: Optional[str] = None
    resolved: Optional[dict] = None  # sample/snippet/template/result/tabular


# ------------------------------------------------------------
# 9. Save section (write mode)
# ------------------------------------------------------------
@dataclass
class SaveSection:
    raw: Optional[str] = None  # raw --save expression
    stream: Optional[str] = None
    files: Optional[List[dict]] = None  # [{"kind": "...", "path": "..."}]


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


@dataclass
class WorkflowMeta:
    workflow_version: str = "1.0"
    builder_version: Optional[str] = None
    timestamp: Optional[str] = None  # ISO-8601
    duration_ms: Optional[int] = None


@dataclass
class ErrorInfo:
    type: Optional[str] = None  # e.g. "validation-error", "builder-error"
    code: Optional[str] = None  # e.g. "MISSING_SAMPLE"
    fatal: bool = False
    details: Optional[str] = None


@dataclass
class ArtifactIndex:
    config: Optional[str] = None
    golden_test: Optional[str] = None
    save_files: List[str] = field(default_factory=list)
    show_outputs: List[str] = field(default_factory=list)


@dataclass
class WorkflowSteps:
    steps: List[str] = field(default_factory=list)


# ------------------------------------------------------------
# 11. Top-level JSON workflow
# ------------------------------------------------------------
@dataclass
class JsonWorkflow:
    meta: Optional[WorkflowMeta] = field(default_factory=WorkflowMeta)
    error: Optional[ErrorInfo] = None
    artifacts: Optional[ArtifactIndex] = field(default_factory=ArtifactIndex)
    steps: Optional[WorkflowSteps] = field(default_factory=WorkflowSteps)

    cli_options: Optional[CliOptions] = None
    api_params: Optional[APIParams] = None
    build_result: Optional[BuildResult] = None

    generated_config: Optional[GeneratedConfig] = None
    golden_test: Optional[GoldenTestSection] = None

    debug: Optional[DebugSection] = None

    show: Optional[ShowSection] = None
    save: Optional[SaveSection] = None

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
