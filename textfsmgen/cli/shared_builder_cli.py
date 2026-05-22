# textfsmgen/cli/shared_builder_cli.py
import copy
import json
from pathlib import Path
from typing import Optional

import click

from textfsmgen.libs.generic import StatusString, DotDict
from textfsmgen.libs.common import emit_status
from textfsmgen.libs import shell
from textfsmgen.libs.utils import get_data_as_tabular
from textfsmgen.libs.text import render_text_block

from textfsmgen.core.builder import (
    BuildResult,
    FreeFormBuilder,
    TabularBuilder,
    CategoryBuilder,
)

from .config_cmd import get_config_template
from .json_model import JsonWorkflow


BUILDER_MAPPING = {
    "freeform": FreeFormBuilder,
    "tabular": TabularBuilder,
    "category": CategoryBuilder,
}


# ------------------------------------------------------------
# Merge helper
# ------------------------------------------------------------
def merge(cli_value, cfg, key, default=None):
    if cli_value not in (None, "", 0):
        return cli_value
    return cfg.get(key, default)


# ------------------------------------------------------------
# Config validation
# ------------------------------------------------------------


def validate_config(config_path, required_top_keys, required_param_keys):
    try:
        raw = click.open_file(config_path).read()
        data = json.loads(raw)
    except Exception as exc:
        return StatusString(
            f"Failed to load config JSON: {exc}",
            status=False,
            reason="error",
        )

    missing_top = [k for k in required_top_keys if k not in data]
    if missing_top:
        return StatusString(
            (
                f"Missing required key(s): {', '.join(missing_top)}\n"
                f"Required: {', '.join(required_top_keys)}"
            ),
            status=False,
            reason="warning",
        )

    params = data.get("params")
    if not isinstance(params, dict):
        return StatusString(
            "Config 'params' must be a dictionary",
            status=False,
            reason="warning",
        )

    missing_params = [k for k in required_param_keys if k not in params]
    if missing_params:
        return StatusString(
            (
                f"Missing required params: {', '.join(missing_params)}\n"
                f"Required: {', '.join(required_param_keys)}"
            ),
            status=False,
            reason="warning",
        )

    if "snippet" in data:
        if not data.get("snippet") and not data.get("snippet_file"):
            return StatusString(
                "Config must contain either 'snippet' or 'snippet_file'",
                status=False,
                reason="warning",
            )
    else:
        if not data.get("sample_file") and not data.get("command"):
            return StatusString(
                "Config must contain either 'sample_file' or 'command'",
                status=False,
                reason="warning",
            )

    return StatusString(data, status=True)


def get_required_top_keys(builder_name):
    """
    Return required top-level keys for each builder type.
    """
    base = [
        "builder",
        "params",
        "snippet",
        "snippet_file",
        "sample_file",
        "command",
        "show",
        "save",
        "create_config",
        "create_config_file",
        "create_golden",
        "create_golden_path",
        "json_mode",
    ]

    if builder_name == "freeform":
        # Freeform requires snippet OR snippet_file
        return base + ["snippet", "snippet_file"]

    return base


def get_required_param_keys(builder_name):
    """
    Return required param keys for each builder type.
    """
    base = ["starting_from", "ending_at", "replacing_rules"]

    if builder_name == "category":
        return ["count", "separator"] + base

    if builder_name == "tabular":
        return [
            "column_divider",
            "column_count",
            "column_widths",
            "headers",
            "header_rows",
            "custom_header_text",
            "has_header_row",
        ] + base

    return []


def validate_config_new(config_path):
    """
    Validate a config JSON file for freeform, category, or tabular builders.
    Returns StatusString.
    """
    # ------------------------------------------------------------
    # Load JSON
    # ------------------------------------------------------------
    try:
        raw = click.open_file(config_path).read()
        data = json.loads(raw)
    except Exception as exc:
        return StatusString(
            f"Failed to load config JSON: {exc}",
            status=False,
            reason="code-error",
        )

    # ------------------------------------------------------------
    # Must be a dictionary
    # ------------------------------------------------------------
    if not isinstance(data, dict):
        return StatusString(
            f"{str(config_path)} must be a dictionary-JSON format.",
            status=False,
            reason="error",
        )

    # ------------------------------------------------------------
    # Must contain builder
    # ------------------------------------------------------------
    if "builder" not in data:
        return StatusString(
            f"{str(config_path)} does not have 'builder' key",
            status=False,
            reason="error",
        )

    builder = str(data["builder"]).lower()

    if builder not in ("freeform", "category", "tabular"):
        return StatusString(
            f"Expected builder must be freeform | category | tabular, "
            f"but received {builder!r}",
            status=False,
            reason="error",
        )

    # ------------------------------------------------------------
    # Required top-level keys
    # ------------------------------------------------------------
    required_top_keys = get_required_top_keys(builder)
    missing_top = [k for k in required_top_keys if k not in data]

    if missing_top:
        return StatusString(
            (
                f"Missing required key(s): {', '.join(missing_top)}\n"
                f"Required: {', '.join(required_top_keys)}"
            ),
            status=False,
            reason="warning",
        )

    # ------------------------------------------------------------
    # Validate params
    # ------------------------------------------------------------
    params = data.get("params")
    if not isinstance(params, dict):
        return StatusString(
            "Config 'params' must be a dictionary",
            status=False,
            reason="warning",
        )

    required_param_keys = get_required_param_keys(builder)
    missing_params = [k for k in required_param_keys if k not in params]

    if missing_params:
        return StatusString(
            (
                f"Missing required params: {', '.join(missing_params)}\n"
                f"Required: {', '.join(required_param_keys)}"
            ),
            status=False,
            reason="warning",
        )

    # ------------------------------------------------------------
    # Validate snippet/sample_file/command rules
    # ------------------------------------------------------------
    if builder == "freeform":
        if not data.get("snippet") and not data.get("snippet_file"):
            return StatusString(
                "Config must contain either 'snippet' or 'snippet_file'",
                status=False,
                reason="error",
            )
    else:
        if not data.get("sample_file") and not data.get("command"):
            return StatusString(
                "Config must contain either 'sample_file' or 'command'",
                status=False,
                reason="error",
            )

    # ------------------------------------------------------------
    # Valid config
    # ------------------------------------------------------------
    return StatusString(data, status=True)


# ------------------------------------------------------------
# Sample loading
# ------------------------------------------------------------
def load_sample(sample_file, command):
    if sample_file:
        try:
            content = Path(sample_file).read_text(encoding="utf-8")
        except Exception as exc:
            return StatusString(
                f"Failed to read input-file: {exc}",
                status=False,
                reason="error",
            )
        if content.strip():
            return StatusString(content, status=True)
        return StatusString(
            "Empty data from input-file", status=False, reason="warning"
        )

    if command:
        result = shell.execute_command(command)
        if not result.is_success:
            return StatusString(result.output, status=False, reason="error")

        output = result.output or ""
        if output.strip():
            return StatusString(output, status=True)

        return StatusString(f"{command} has no output", status=False, reason="warning")

    return StatusString(
        "No sample_file or command provided", status=False, reason="warning"
    )


# ------------------------------------------------------------
# Save helpers
# ------------------------------------------------------------
def parse_save_expression(expr: str):
    """
    Parse save syntax:

        sample-out.txt,result-a.json
        dryrun(sample-out.txt,result-a.json)

    Returns:
        ("", parsed)              # normal mode
        ("dryrun", parsed)        # dry-run mode

    Where parsed is:
        [
            {"kind": "sample", "path": "out.txt"},
            {"kind": "result", "path": "a.json"},
        ]

    Raises:
        ValueError on invalid syntax.
    """
    expr = expr.strip()
    if not expr:
        raise ValueError("Empty --save expression")

    mode = ""
    inner = expr

    # Detect dryrun(...) wrapper
    if expr.startswith("dryrun(") and expr.endswith(")"):
        mode = "dryrun"
        inner = expr[len("dryrun(") : -1].strip()

    if not inner:
        raise ValueError("Empty save list inside expression")

    allowed_kinds = {"sample", "snippet", "template", "result"}

    raw_items = [x.strip() for x in inner.split(",") if x.strip()]
    if not raw_items:
        raise ValueError("No valid save items found")

    parsed = []

    for item in raw_items:
        if "-" not in item:
            raise ValueError(f"Invalid save item '{item}'. Expected <kind>-<filename>")

        kind, filename = item.split("-", 1)
        kind = kind.strip()
        filename = filename.strip()

        if kind not in allowed_kinds:
            raise ValueError(
                f"Invalid save kind '{kind}'. "
                f"Allowed kinds: {', '.join(sorted(allowed_kinds))}"
            )

        if not filename:
            raise ValueError(f"Missing filename for kind '{kind}'")

        parsed.append({"kind": kind, "path": filename})

    return mode, parsed


def _write_file(filename: str, content: str, kind: str, mode: str="") -> StatusString:
    """
    Write content to filename, or simulate writing in dry-run mode.

    Returns:
        StatusString with a kind-aware message.
    """
    is_dry_run = mode == "dryrun"

    if is_dry_run:
        return StatusString(
            f"[DRY-RUN] {kind} → {filename}",
            status=True,
            reason="info",
        )

    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)

        return StatusString(
            f"Saved {kind} → {filename}",
            status=True,
            reason="info",
        )

    except Exception as exc:
        return StatusString(
            f"Failed to save {kind} → {filename}: {exc}",
            status=False,
            reason="code-error",
        )


def save_outputs(result: BuildResult, sample: str, save_spec: str):
    """
    Save outputs using the unified syntax:
        --save=sample-out.txt,snippet-snippet.txt,template-template.textfsm,result-out.json
        --save=dryrun(sample-out.txt,result-out.json)

    Returns:
        list[dict] with per-file info:
            {"kind": "...", "path": "...", "severity": "...", "message": "..."}
    """

    # ------------------------------------------------------------
    # Internal function
    # ------------------------------------------------------------
    def append(kind_, path, status_: StatusString):
        results.append(
            {
                "kind": kind_,
                "path": path,
                "severity": status_.reason,
                "message": str(status_),
            }
        )

    # ------------------------------------------------------------

    try:
        mode, items = parse_save_expression(save_spec)
    except ValueError as exc:
        status = StatusString(str(exc), status=False, reason="error")
        return [
            {
                "kind": "parse-expression",
                "path": None,
                "severity": status.reason,
                "message": str(status),
            }
        ]

    results: list[dict] = []
    is_dry_run = mode == "dryrun"

    for entry in items:
        kind = entry["kind"]
        filename = entry["path"]

        # ------------------------------------------------------------
        # sample is always allowed
        # ------------------------------------------------------------
        if kind == "sample":
            content = sample
            status = _write_file(filename, content, kind, mode)
            append(kind, filename, status)
            continue

        # ------------------------------------------------------------
        # builder-level warning blocks snippet/template/result
        # ------------------------------------------------------------
        if result.warning:
            msg = f"Build result contains warning: {result.warning}. Cannot proceed."
            status = StatusString(
                f"[DRY-RUN] {msg}" if is_dry_run else msg,
                status=False,
                reason="error",
            )
            append("build-result", None, status)
            continue

        # ------------------------------------------------------------
        # Load content
        # ------------------------------------------------------------
        if kind in ("snippet", "template"):
            content = getattr(result, kind, None)
            if not content:
                msg = f"Builder has no '{kind}' content"
                status = StatusString(
                    f"[DRY-RUN] {msg}" if is_dry_run else msg,
                    status=False,
                    reason="warning",
                )
                append(kind, filename, status)
                continue

        elif kind == "result":
            content = result.result
            if not content:
                msg = f"No records found for '{filename}'"
                status = StatusString(
                    f"[DRY-RUN] {msg}" if is_dry_run else msg,
                    status=False,
                    reason="warning",
                )
                append(kind, filename, status)
                continue

        else:
            msg = f"Unknown save kind '{kind}'"
            status = StatusString(
                f"[DRY-RUN] {msg}" if is_dry_run else msg,
                status=False,
                reason="error",
            )
            append(f"unknown-{kind}", None, status)
            continue

        # ------------------------------------------------------------
        # Normalize content to string
        # ------------------------------------------------------------
        if not isinstance(content, str):
            content = json.dumps(content, indent=2, ensure_ascii=False)

        # ------------------------------------------------------------
        # Write or dry-run (delegated to _write_file)
        # ------------------------------------------------------------
        status = _write_file(filename, content, kind, mode)
        append(kind, filename, status)

    return results


def save_outputs_v2(api_params, builder_result):
    """
    Save outputs using the unified syntax:
        --save=sample-out.txt,snippet-snippet.txt,template-template.textfsm,result-out.json

    Returns:
        DotDict(
            status=StatusString(...),
            files=[...],
            exit_code=int,
        )
    """

    # ------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------
    def append(kind_, path, status_):
        files.append(
            {
                "kind": kind_,
                "path": path,
                "severity": status_.reason,
                "message": str(status_),
            }
        )

    def record_failure(status_):
        msg = emit_status(status_)
        failure_messages.append(msg)
        return "[FATAL]" in msg

    # ------------------------------------------------------------
    # Parse save expression
    # ------------------------------------------------------------
    try:
        _, items = parse_save_expression(api_params.save)
    except ValueError as exc:
        message = f"Parse-Expression ({type(exc).__name__}: {exc})"
        return DotDict(
            status=StatusString(message, status=False, reason="code-error"),
            files=[],
            exit_code=2,
        )

    files = []
    failure_messages = []
    fatal = False

    # ------------------------------------------------------------
    # Process each save item
    # ------------------------------------------------------------
    for entry in items:
        kind = entry["kind"]
        filename = entry["path"]

        # ------------------------------------------------------------
        # sample is always allowed
        # ------------------------------------------------------------
        if kind == "sample":
            content = api_params.sample_data
            status = _write_file(filename, content, kind)
            if not status:
                fatal |= record_failure(status)
            append(kind, filename, status)
            continue

        # ------------------------------------------------------------
        # builder-level warning blocks snippet/template/result
        # ------------------------------------------------------------
        if builder_result.warning:
            msg = f"Build result contains warning: {builder_result.warning}. Cannot proceed."
            status = StatusString(msg, status=False, reason="error")
            fatal |= record_failure(status)
            append("build-result", None, status)
            continue

        # ------------------------------------------------------------
        # Load content
        # ------------------------------------------------------------
        if kind in ("snippet", "template"):
            content = getattr(builder_result, kind, None)
            if not content:
                msg = f"Builder has no '{kind}' content"
                status = StatusString(msg, status=False, reason="warning")
                fatal |= record_failure(status)
                append(kind, filename, status)
                continue

        elif kind == "result":
            content = builder_result.result
            if not content:
                msg = f"No records found for '{filename}'"
                status = StatusString(msg, status=False, reason="warning")
                fatal |= record_failure(status)
                append(kind, filename, status)
                continue

        else:
            msg = f"Unknown save kind '{kind}'"
            status = StatusString(msg, status=False, reason="error")
            fatal |= record_failure(status)
            append(f"unknown-{kind}", None, status)
            continue

        # ------------------------------------------------------------
        # Normalize content to string
        # ------------------------------------------------------------
        if not isinstance(content, str):
            content = json.dumps(content, indent=2, ensure_ascii=False)

        # ------------------------------------------------------------
        # Write file
        # ------------------------------------------------------------
        status = _write_file(filename, content, kind)
        if not status:
            fatal |= record_failure(status)
        append(kind, filename, status)

    # ------------------------------------------------------------
    # Final result
    # ------------------------------------------------------------
    if failure_messages:
        return DotDict(
            status=StatusString("\n".join(failure_messages), status=False, reason="error"),
            files=files,
            exit_code=2 if fatal else 1,
        )

    return DotDict(
        status=StatusString(status=True),
        files=files,
        exit_code=0,
    )



# ------------------------------------------------------------
# Show outputs
# ------------------------------------------------------------
def show_outputs(result: BuildResult, sample: str, show_spec: str):
    """
    Resolve --show targets into a dict:
        {
            "sample": "...",
            "result": [...],
            "template": "...",
            "snippet": "...",
            "tabular": "..."
        }
    """
    show_spec = (show_spec or "").strip()
    cases = [x.strip() for x in show_spec.split(",") if x.strip()]

    if not cases:
        return {"template": result.template}

    resolved: dict[str, object] = {}

    for case in cases:
        if case == "sample":
            resolved["sample"] = sample
            continue

        if case in ("snippet", "template"):
            value = getattr(result, case, None)
            if not value:
                resolved[case] = f"Builder has no '{case}' content"
            else:
                resolved[case] = value
            continue

        if case == "result":
            if result.warning:
                resolved["result"] = result.warning
            else:
                resolved["result"] = result.result
            continue

        if case == "default":
            if result.warning:
                resolved["result"] = result.warning
            else:
                resolved["result"] = str(result.result)
            continue

        if case == "tabular":
            if result.warning:
                resolved["result"] = result.warning
            else:
                resolved["result"] = get_data_as_tabular(result.result)
            continue

        resolved[case] = f"Unknown show target '{case}'"

    return resolved


# ------------------------------------------------------------
# Debug printer
# ------------------------------------------------------------
def debug_print(
    snippet,
    snippet_file,
    sample_file,
    command,
    params,
    config,
    sample,
    save,
    show,
    json_workflow: Optional[JsonWorkflow] = None,
):
    lines = []
    if snippet_file:
        lines.append(f"[INFO] Loaded snippet from: {snippet_file}")
        lines.append(f"[INFO] Snippet size: {len(snippet)} characters")
    if sample:
        lines.append(f"[INFO] Loaded sample from: {sample_file or command}")
        lines.append(f"[INFO] Sample size: {len(sample)} characters")

    lines.append("=== DEBUG INFO ===")
    if snippet_file:
        lines.append(f"snippet_file   = {snippet_file}")
    lines.append(f"sample_file    = {sample_file!r}")
    lines.append(f"command        = {command!r}")
    params_txt = json.dumps(params, indent=2, ensure_ascii=False)
    lines.append(render_text_block(params_txt, subject="params         ="))
    if isinstance(config, dict):
        config_txt = json.dumps(config, indent=2, ensure_ascii=False)
        lines.append(render_text_block(config_txt, subject="config         ="))
    else:
        lines.append(f"config         = {config}")
    lines.append(f"save           = {save!r}")
    lines.append(f"show           = {show!r}")
    lines.append("==================")

    debug_txt = "\n".join(lines)
    if json_workflow:
        json_workflow.add_debug(debug_txt)
        return
    click.echo(debug_txt)


def build_debug_report(api_params):
    if not api_params.debug:
        return ""

    lines = []

    # -------------------------------------------
    # helper
    # -------------------------------------------
    def _add(label, value):
        lines.append(f"{label:<23} = {value!r}")

    header_width = 60

    # -------------------------------------------
    # High-level info
    # -------------------------------------------
    if api_params.snippet_file:
        lines.append(f"[INFO] Loaded snippet from: {api_params.snippet_file!r}")
        if api_params.snippet_data:
            lines.append(
                f"[INFO] Snippet size: {len(api_params.snippet_data)} characters"
            )

    if api_params.sample_data:
        source = api_params.sample_file or api_params.command
        lines.append(f"[INFO] Loaded sample from: {source!r}")
        lines.append(f"[INFO] Sample size: {len(api_params.sample_data)} characters")

    # -------------------------------------------
    # Debug header
    # -------------------------------------------
    lines.append("")
    lines.append(" DEBUG INFO ".center(header_width, "="))
    lines.append("")

    # -------------------------------------------
    # Builder params
    # -------------------------------------------
    lines.append(" BUILDER PARAMS ".center(header_width, "-"))

    if api_params.snippet_file:
        _add("snippet_file", api_params.snippet_file)

    _add("sample_file", api_params.sample_file)
    _add("command", api_params.command)

    # Params block (pretty JSON)
    params_json = json.dumps(api_params.params, indent=2, ensure_ascii=False)
    lines.append(render_text_block(params_json, subject=f"{'params':<23} ="))

    # -------------------------------------------
    # Execution flags
    # -------------------------------------------
    lines.append("")
    lines.append(" EXECUTION FLAGS ".center(header_width, "-"))

    _add("config", api_params.config)
    _add("save", api_params.save)
    _add("show", api_params.show)
    _add("create_config", api_params.create_config)
    _add("create_config_file", api_params.create_config_file)
    _add("create_golden_test", api_params.create_golden_test)
    _add("create_golden_test_path", api_params.create_golden_test_path)
    _add("json_mode", api_params.json_mode)

    lines.append("=" * header_width)

    return "\n".join(lines)


# ------------------------------------------------------------
# Unified workflow engine
# ------------------------------------------------------------
def run_builder_workflow(
    builder_class,
    snippet="",
    snippet_file=None,
    sample_file=None,
    command="",
    params=None,
    save="",
    show="",
    config=None,
    debug=False,
    suppressed_message=False,
    json_workflow: Optional[JsonWorkflow] = None,
):
    params = params or {}
    sample_text = ""

    if sample_file or command:
        sample_status = load_sample(sample_file, command)
        if not sample_status:
            if json_workflow:
                json_workflow.set_status(
                    kind=sample_status.reason,
                    message=str(sample_status),
                    exit_code=1,
                )
                click.echo(json_workflow.to_json(validating=True))
                raise SystemExit(1)
            emit_status(sample_status)
            return 1
        sample_text = str(sample_status)

    if debug:
        debug_print(
            snippet,
            snippet_file,
            sample_file,
            command,
            params,
            config,
            sample_text,
            save,
            show,
            json_workflow=json_workflow,
        )

    builder = builder_class()

    if json_workflow:
        json_workflow.add_builder(
            name="unknown",
            params=params,
            snippet=snippet,
            snippet_file=snippet_file,
            sample=sample_text,
            sample_file=sample_file,
        )

    builder_name = "unknown"

    if issubclass(builder_class, FreeFormBuilder):
        builder_name = "freeform"
        if snippet_file:
            builder.set_snippet_file(snippet_file)
        else:
            builder.set_snippet(snippet)
        builder.set_sample(sample_text)

    elif issubclass(builder_class, (TabularBuilder, CategoryBuilder)):
        builder_name = (
            "category" if issubclass(builder_class, CategoryBuilder) else "tabular"
        )
        builder.set_sample(sample_text, **params)
    else:
        message = (
            f"Builder {builder_class.__name__} does not support sample/snippet input"
        )
        if json_workflow:
            json_workflow.update_builder(name="unknown")
            json_workflow.set_status(
                kind="error",
                message=message,
                exit_code=1,
            )
            click.echo(json_workflow.to_json(validating=True))
            raise SystemExit(1)

        status = StatusString(message, status=False, reason="error")
        emit_status(status)
        return 1

    if json_workflow:
        json_workflow.update_builder(name=builder_name)

    try:
        builder.build()
        if json_workflow:
            json_workflow.update_builder(
                name=builder_name,
                snippet=snippet if builder_name == "freeform" else builder.snippet,
                built=bool(builder),
                warning=builder.warning,
                template=builder.template,
                result=builder.result,
            )
    except Exception as exc:
        message = f"Builder {builder_class.__name__} failed with error: {exc}"
        if json_workflow:
            json_workflow.set_status(kind="error", message=message, exit_code=1)
            click.echo(json_workflow.to_json(validating=True))
            raise SystemExit(1)

        status = StatusString(message, status=False, reason="error")
        emit_status(status)
        return 1

    result: BuildResult = builder.to_result()
    if not builder:
        message = (
            f"Cannot create builder from sample (reference: {sample_file or command!r})\n"
            "===========================================\n"
            f"{sample_text}\n"
        )
        if json_workflow:
            json_workflow.set_status(kind="warning", message=message, exit_code=1)
            click.echo(json_workflow.to_json(validating=True))
            raise SystemExit(1)
        status = StatusString(message, status=False, reason="warning")
        emit_status(status)
        return 1

    # Save
    if save:
        results = save_outputs(result, sample_text, save)

        if json_workflow:
            json_workflow.add_save(raw=save)

        exit_code = 0
        failure_message = ""
        failure_severity = ""

        for info in results:
            message = info.get("message", "")
            severity = info.get("severity") or ""
            if json_workflow:
                json_workflow.append_save_file(
                    {"kind": info["kind"], "path": info["path"]}
                )
            else:
                emit_status(message)

            if severity in ("error", "warning"):
                failure_message = message
                failure_severity = severity
                exit_code = 1

        if json_workflow:
            if exit_code == 0:
                json_workflow.set_status(
                    kind="success",
                    message="",
                    exit_code=0,
                )
            else:
                json_workflow.set_status(
                    kind=failure_severity or "error",
                    message=failure_message,
                    exit_code=exit_code,
                )

        return exit_code

    # Show
    outputs_info = show_outputs(result, sample_text, show)
    if json_workflow:
        json_workflow.add_show(raw=show, resolved=outputs_info)
        json_workflow.set_status(kind="success", message="", exit_code=0)
    else:
        if not suppressed_message:
            parts: list[str] = []
            for key, output in outputs_info.items():
                header = f"=== {key} ==="
                if isinstance(output, str):
                    parts.append(f"{header}\n{output}")
                else:
                    parts.append(
                        f"{header}\n{json.dumps(output, indent=2, ensure_ascii=False)}"
                    )
            emit_status("\n==========\n".join(parts))
    return 0


def execute_builder(api_params):
    builder_name = api_params.builder
    builder_cls = BUILDER_MAPPING[builder_name]
    builder = builder_cls()

    # -------------------------------------------
    # Set snippet/sample inputs
    # -------------------------------------------
    if builder_name == "freeform":
        builder.set_snippet(api_params.snippet_data)
        if api_params.sample_data.strip():
            builder.set_sample(api_params.sample_data)
    else:
        builder.set_sample(api_params.sample_data, **api_params.params)

    # -------------------------------------------
    # Build
    # -------------------------------------------
    try:
        builder.build()
    except Exception as exc:
        message = f"Builder {builder_cls.__name__} failed with error: {exc}"
        return DotDict(
            builder_result=None,
            status=StatusString(message, status=False, reason="code-error"),
            exit_code=2,
        )

    # Convert to result object
    result: BuildResult = builder.to_result()

    # -------------------------------------------
    # Validate result
    # -------------------------------------------
    if not builder:
        if builder_name == "freeform":
            message = (
                f"Cannot create {builder_name} builder from snippet "
                f"(reference: {api_params.snippet_file or 'snippet'!r})"
                f"\n{'-' * 60}\n"
                f"{api_params.snippet_data}"
            )
        else:
            message = (
                f"Cannot create {builder_name} builder from sample "
                f"(reference: {api_params.sample_file or api_params.command!r})"
                f"\n{'-' * 60}\n"
                f"{api_params.sample_data}\n"
            )

        return DotDict(
            builder_result=result,
            status=StatusString(message, status=False, reason="error"),
            exit_code=1,
        )

    # -------------------------------------------
    # Success
    # -------------------------------------------
    return DotDict(
        builder_result=result,
        status=StatusString(status=True),
        exit_code=0,
    )


# ------------------------------------------------------------
# Config generation / save
# ------------------------------------------------------------
def generate_or_save_config(
    builder_name,
    cfg_path="",
    params=None,
    snippet="",
    snippet_file="",
    sample_file="",
    command="",
    show="",
    save="",
    json_workflow: Optional[JsonWorkflow] = None,
):
    template = get_config_template(builder_name)
    cfg = json.loads(json.dumps(template))

    cfg["sample_file"] = sample_file
    cfg["command"] = command
    cfg["show"] = show
    cfg["save"] = save

    if params:
        cfg["params"] = params.copy()

    if "snippet" in cfg:
        cfg["snippet"] = snippet

    if "snippet_file" in cfg:
        cfg["snippet_file"] = snippet_file

    content = json.dumps(cfg, indent=2, ensure_ascii=False)

    if cfg_path:
        path = Path(cfg_path).resolve()
        parent = path.parent

        if not parent.exists():
            try:
                parent.mkdir(parents=True, exist_ok=True)
            except Exception as exc:
                message = f"[ERROR] Cannot create directory {str(parent)!r}: {exc}"
                if json_workflow:
                    json_workflow.set_status(kind="error", message=message, exit_code=1)
                    click.echo(json_workflow.to_json(validating=True))
                    raise SystemExit(1)
                print(message)
                raise SystemExit(1)

        if path.exists():
            message = f"[ERROR] Config file {str(path)!r} already exists!"
            if json_workflow:
                json_workflow.set_status(kind="error", message=message, exit_code=1)
                click.echo(json_workflow.to_json(validating=True))
                raise SystemExit(1)
            print(message)
            raise SystemExit(1)

        try:
            path.write_text(content, encoding="utf-8")
        except Exception as exc:
            message = f"[ERROR] Failed to write config file {str(path)!r}: {exc}"
            if json_workflow:
                json_workflow.set_status(kind="error", message=message, exit_code=1)
                click.echo(json_workflow.to_json(validating=True))
                raise SystemExit(1)
            print(message)
            raise SystemExit(1)

        message = f"[INFO] Config file {str(path)!r} created!"
        if json_workflow:
            json_workflow.add_generated_config(stream="io", path=str(path), payload=cfg)
            json_workflow.set_status(kind="success", message=message, exit_code=0)
            click.echo(json_workflow.to_json(validating=True))
            raise SystemExit(0)
        print(message)
        raise SystemExit(0)

    if json_workflow:
        json_workflow.add_generated_config(stream="console", path=None, payload=cfg)
        json_workflow.set_status(kind="success", message="", exit_code=0)
        click.echo(json_workflow.to_json(validating=True))
        raise SystemExit(0)

    click.echo(content)
    raise SystemExit(0)


def create_config(api_params):
    builder_name = api_params.builder

    # ------------------------------------------------------------
    # 1. Build config payload
    # ------------------------------------------------------------
    template = get_config_template(builder_name)
    cfg = json.loads(json.dumps(template))  # safe deep copy

    # Overlay resolved values
    for key in cfg:
        cfg[key] = copy.deepcopy(api_params[key])

    path = Path(api_params.create_config_file) if api_params.create_config_file else None

    generated_config = DotDict(
        stream="stream" if not api_params.create_config_file else "io",
        path=None if not api_params.create_config_file else str(path.resolve()),
        payload=cfg,
    )

    # ------------------------------------------------------------
    # 2. Stream mode (print to stdout)
    # ------------------------------------------------------------
    if not api_params.create_config_file:
        return DotDict(
            status=StatusString(status=True),
            generated_config=generated_config,
            exit_code=0,
        )

    # ------------------------------------------------------------
    # 3. File mode (write to disk)
    # ------------------------------------------------------------
    path = Path(api_params.create_config_file)
    parent = path.parent

    # Ensure parent directory exists
    if not parent.exists():
        try:
            parent.mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            return DotDict(
                status=StatusString(
                    f"Cannot create directory {str(parent)!r}: {exc}",
                    status=False,
                    reason="code-error",
                ),
                generated_config=generated_config,
                exit_code=2,
            )

    # Prevent overwriting
    if path.exists():
        return DotDict(
            status=StatusString(
                f"Config file {str(path)!r} already exists!",
                status=False,
                reason="error",
            ),
            generated_config=generated_config,
            exit_code=1,
        )

    # Write file
    try:
        content = json.dumps(cfg, indent=2, ensure_ascii=False)
        path.write_text(content, encoding="utf-8")
    except Exception as exc:
        return DotDict(
            status=StatusString(
                f"Failed to write config file {str(path)!r}: {exc}",
                status=False,
                reason="code-error",
            ),
            generated_config=generated_config,
            exit_code=2,
        )

    # Success
    return DotDict(
        status=StatusString(f"[INFO] Config file {str(path)!r} created!", status=True),
        generated_config=generated_config,
        exit_code=0,
    )


# ------------------------------------------------------------
# Golden Test: Dry-Run or Create
# ------------------------------------------------------------
def dry_run_or_create_golden_test(
    builder_class,
    builder_name,
    golden_path="",
    params=None,
    snippet="",
    snippet_file="",
    sample_file="",
    command="",
    json_workflow=None,
):
    """
    Create or preview a golden test case for the given builder.

    - If golden_path is empty:
        Perform a DRY RUN.
        Do NOT write any files.
        Show which files WOULD be created.
        Default path:
            ./tests/golden/integration/<builder>-case

    - If golden_path is provided:
        Perform ACTUAL CREATION.
        golden_path MUST be under:
            tests/golden/integration/
        Auto-create parent directories.
        Fail if files already exist.
    """

    params = params or {}

    # ------------------------------------------------------------
    # 1. Determine mode + base path
    # ------------------------------------------------------------
    if not golden_path:
        mode = "dry-run"
        case_name = f"{builder_name}-case"
        base_path = Path("tests") / "golden" / "integration" / case_name
    else:
        mode = "create"
        base_path = Path(golden_path).resolve()

        # Must be inside .../golden/integration/<case>
        if not (
            base_path.parent.name == "integration"
            and base_path.parent.parent.name == "golden"
        ):
            message = (
                f"[ERROR] Golden test path {str(base_path)!r} must be inside "
                f".../golden/integration/<case>"
            )
            if json_workflow:
                json_workflow.set_status(kind="error", message=message, exit_code=1)
                click.echo(json_workflow.to_json(validating=True))
                raise SystemExit(1)
            print(message)
            raise SystemExit(1)

    # ------------------------------------------------------------
    # 2. Load sample (required)
    # ------------------------------------------------------------
    sample_status = load_sample(sample_file, command)
    if not sample_status:
        message = "[ERROR] Golden test requires a non-empty sample."
        if json_workflow:
            json_workflow.set_status(kind="error", message=message, exit_code=1)
            click.echo(json_workflow.to_json(validating=True))
            raise SystemExit(1)

        print(message)
        raise SystemExit(1)

    sample_text = str(sample_status)

    # ------------------------------------------------------------
    # 3. Instantiate builder
    # ------------------------------------------------------------
    builder = builder_class()

    # ------------------------------------------------------------
    # 4. Apply snippet/sample depending on builder type
    # ------------------------------------------------------------
    if issubclass(builder_class, FreeFormBuilder):
        if snippet_file:
            builder.set_snippet_file(snippet_file)
        else:
            builder.set_snippet(snippet)
        builder.set_sample(sample_text)

    elif issubclass(builder_class, (TabularBuilder, CategoryBuilder)):
        builder.set_sample(sample_text, **params)

    else:
        message = f"[ERROR] Unsupported builder class: {builder_class.__name__}"
        if json_workflow:
            json_workflow.set_status("error", message, 1)
            click.echo(json_workflow.to_json(validating=True))
            raise SystemExit(1)
        print(message)
        raise SystemExit(1)

    # ------------------------------------------------------------
    # 5. Build
    # ------------------------------------------------------------
    try:
        builder.build()
    except Exception as exc:
        message = f"[ERROR] Builder failed: {exc}"
        if json_workflow:
            json_workflow.set_status(kind="error", message=message, exit_code=1)
            click.echo(json_workflow.to_json(validating=True))
            raise SystemExit(1)
        print(message)
        raise SystemExit(1)

    result: BuildResult = builder.to_result()

    # ------------------------------------------------------------
    # 6. Validate builder output
    # ------------------------------------------------------------
    if result.warning:
        message = f"[ERROR] Cannot create golden test: {result.warning}"
        if json_workflow:
            json_workflow.set_status(kind="error", message=message, exit_code=1)
            click.echo(json_workflow.to_json(validating=True))
            raise SystemExit(1)

        print(message)
        raise SystemExit(1)

    # ------------------------------------------------------------
    # 7. Prepare manifest + file paths
    # ------------------------------------------------------------
    manifest = {
        "builder": builder_name,
        "params": params,
        "meta": {
            "author": "",
            "email": "",
            "description": "",
            "notes": "",
            "schema_version": "1.0",
        },
    }

    inputs_dir = base_path / "inputs"
    expected_dir = base_path / "expected"
    expected_results_dir = base_path / "expected_results"

    files = {
        "sample": inputs_dir / "sample.txt",
        "snippet": expected_dir / "snippet.txt",
        "template": expected_dir / "textfsm.template",
        "result": expected_results_dir / "sample_result.json",
        "manifest": base_path / "manifest.json",
    }

    # ------------------------------------------------------------
    # 8. Dry-run mode
    # ------------------------------------------------------------
    if mode == "dry-run":
        lines = [f"[DRY-RUN] Golden test base path: {str(base_path)}"]
        for label, path in files.items():
            lines.append(f"[DRY-RUN] Would create: {str(path)}")

        if json_workflow:
            json_workflow.add_golden_test_dry_run(lines=lines)
            json_workflow.set_status(kind="success", message="", exit_code=0)
            click.echo(json_workflow.to_json(validating=True))
            raise SystemExit(0)

        click.echo("\n".join(lines))
        raise SystemExit(0)

    # ------------------------------------------------------------
    # 9. Actual creation mode
    # ------------------------------------------------------------
    # Create directories
    for d in (inputs_dir, expected_dir, expected_results_dir):
        d.mkdir(parents=True, exist_ok=True)

    # Prevent overwriting
    for label, path in files.items():
        if path.exists():
            message = f"[ERROR] {label} file {str(path)!r} already exists!"
            if json_workflow:
                json_workflow.set_status(kind="error", message=message, exit_code=1)
                click.echo(json_workflow.to_json(validating=True))
                raise SystemExit(1)

            print(message)
            raise SystemExit(1)

    # Write files
    files["sample"].write_text(sample_text, encoding="utf-8")
    files["snippet"].write_text(result.snippet, encoding="utf-8")
    files["template"].write_text(result.template, encoding="utf-8")
    files["result"].write_text(
        json.dumps(result.result, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    files["manifest"].write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    # ------------------------------------------------------------
    # 10. JSON mode output
    # ------------------------------------------------------------
    if json_workflow:
        json_workflow.add_golden_test(
            path=str(base_path),
            manifest={
                "path": str(files["manifest"]),
                "content": json.dumps(manifest, indent=2, ensure_ascii=False),
            },
            inputs={
                "path": str(inputs_dir),
                "files": [
                    {
                        "path": str(files["sample"]),
                        "content": sample_text,
                    }
                ],
            },
            expected_results={
                "path": str(expected_results_dir),
                "files": [
                    {
                        "path": str(files["result"]),
                        "content": json.dumps(
                            result.result, indent=2, ensure_ascii=False
                        ),
                    }
                ],
            },
            expected={
                "path": str(expected_dir),
                "files": [
                    {
                        "path": str(files["snippet"]),
                        "content": result.snippet,
                    },
                    {
                        "path": str(files["template"]),
                        "content": result.template,
                    },
                ],
            },
        )

        json_workflow.set_status(kind="success", message="", exit_code=0)
        click.echo(json_workflow.to_json(validating=True))
        raise SystemExit(0)

    # ------------------------------------------------------------
    # 11. Human mode output
    # ------------------------------------------------------------
    print(f"[INFO] Golden test created at {str(base_path)!r}")
    raise SystemExit(0)


def create_golden_test(api_params, builder_result):
    """
    Create or dry-run a golden test case based on builder output and API params.
    """

    # ------------------------------------------------------------
    # 0. Validate sample
    # ------------------------------------------------------------
    if not api_params.sample_data.strip():
        ref = api_params.sample_file or api_params.command
        return DotDict(
            status=StatusString(
                f"Cannot create Golden Test without sample (reference: {ref!r}).",
                status=False,
                reason="error",
            ),
            creation_result=None,
            output="",
            exit_code=1,
        )

    builder_name = api_params.builder

    # ------------------------------------------------------------
    # 1. Determine mode + base path
    # ------------------------------------------------------------
    if api_params.create_golden_test_path:
        mode = "create"
        base_path = Path(api_params.create_golden_test_path).resolve()

        # Must be inside .../golden/integration/<case>
        if not (
            base_path.parent.name == "integration"
            and base_path.parent.parent.name == "golden"
        ):
            return DotDict(
                status=StatusString(
                    f"Golden test path {str(base_path)!r} must be inside "
                    f".../golden/integration/<case>",
                    status=False,
                    reason="error",
                ),
                creation_result=None,
                output="",
                exit_code=1,
            )

    else:
        mode = "dry-run"
        case_name = f"{builder_name}-case"
        base_path = Path("tests") / "golden" / "integration" / case_name

    # ------------------------------------------------------------
    # 2. Prepare manifest + file layout
    # ------------------------------------------------------------
    manifest = {
        "builder": builder_name,
        "params": api_params.params,
        "meta": {
            "author": "",
            "email": "",
            "description": "",
            "notes": "",
            "schema_version": "1.0",
        },
    }

    inputs_dir = base_path / "inputs"
    expected_dir = base_path / "expected"
    expected_results_dir = base_path / "expected_results"

    files = {
        "sample": inputs_dir / "sample.txt",
        "snippet": expected_dir / "snippet.txt",
        "template": expected_dir / "textfsm.template",
        "result": expected_results_dir / "sample_result.json",
        "manifest": base_path / "manifest.json",
    }

    # ------------------------------------------------------------
    # 3. Dry-run mode
    # ------------------------------------------------------------
    if mode == "dry-run":
        lines = [f"[DRY-RUN] Golden test base path: {str(base_path)}"]
        for label, path in files.items():
            lines.append(f"[DRY-RUN] Would create: {str(path)}")

        return DotDict(
            status=StatusString(status=True),
            creation_result=None,
            output="\n".join(lines),
            exit_code=0,
        )

    # ------------------------------------------------------------
    # 4. Actual creation mode
    # ------------------------------------------------------------
    # Create directories
    for d in (inputs_dir, expected_dir, expected_results_dir):
        d.mkdir(parents=True, exist_ok=True)

    # Prevent overwriting
    for label, path in files.items():
        if path.exists():
            return DotDict(
                status=StatusString(
                    f"{label} file {str(path)!r} already exists!",
                    status=False,
                    reason="error",
                ),
                creation_result=None,
                output="",
                exit_code=1,
            )

    # ------------------------------------------------------------
    # 5. Write files
    # ------------------------------------------------------------
    lines = [f"[INFO] Golden test created at {str(base_path)!r}"]

    files["sample"].write_text(api_params.sample_data, encoding="utf-8")
    lines.append(f"  - sample   => {str(files['sample'])}")

    files["snippet"].write_text(builder_result.snippet, encoding="utf-8")
    lines.append(f"  - snippet  => {str(files['snippet'])}")

    files["template"].write_text(builder_result.template, encoding="utf-8")
    lines.append(f"  - template => {str(files['template'])}")

    files["result"].write_text(
        json.dumps(builder_result.result, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    lines.append(f"  - result   => {str(files['result'])}")

    files["manifest"].write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    lines.append(f"  - manifest => {str(files['manifest'])}")

    # ------------------------------------------------------------
    # 6. Build creation_result structure
    # ------------------------------------------------------------
    creation_result = DotDict(
        path=str(base_path),
        manifest={
            "path": str(files["manifest"]),
            "content": json.dumps(manifest, indent=2, ensure_ascii=False),
        },
        inputs={
            "path": str(inputs_dir),
            "files": [
                {
                    "path": str(files["sample"]),
                    "content": api_params.sample_data,
                }
            ],
        },
        expected_results={
            "path": str(expected_results_dir),
            "files": [
                {
                    "path": str(files["result"]),
                    "content": json.dumps(
                        builder_result.result, indent=2, ensure_ascii=False
                    ),
                }
            ],
        },
        expected={
            "path": str(expected_dir),
            "files": [
                {
                    "path": str(files["snippet"]),
                    "content": builder_result.snippet,
                },
                {
                    "path": str(files["template"]),
                    "content": builder_result.template,
                },
            ],
        },
    )

    return DotDict(
        status=StatusString(status=True),
        creation_result=creation_result,
        output="\n".join(lines),
        exit_code=0,
    )

