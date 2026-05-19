# textfsmgen/cli/shared_builder_cli.py

import json
from pathlib import Path
from typing import Optional

import click

from textfsmgen.libs.generic import StatusString
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


# ------------------------------------------------------------
# Sample loading
# ------------------------------------------------------------
def load_sample(sample_file, cmd):
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

    if cmd:
        result = shell.execute_command(cmd)
        if not result.is_success:
            return StatusString(result.output, status=False, reason="error")

        output = result.output or ""
        if output.strip():
            return StatusString(output, status=True)

        return StatusString(f"{cmd} has no output", status=False, reason="warning")

    return StatusString(
        "No sample_file or cmd provided", status=False, reason="warning"
    )


# ------------------------------------------------------------
# Save helpers
# ------------------------------------------------------------
def parse_save_expression(expr: str):
    """
    Parse the unified save syntax:
        sample-out.txt,snippet-a.txt,template-b.textfsm,result-c.json

    Returns:
        [
            {"kind": "sample", "path": "out.txt"},
            {"kind": "snippet", "path": "a.txt"},
            {"kind": "template", "path": "b.textfsm"},
            {"kind": "result", "path": "c.json"}
        ]

    Raises:
        ValueError on invalid syntax.
    """
    expr = expr.strip()
    if not expr:
        raise ValueError("Empty --save expression")

    items = [x.strip() for x in expr.split(",") if x.strip()]
    parsed = []

    for item in items:
        if "-" not in item:
            raise ValueError(
                f"Invalid save format: '{item}'. Expected: <kind>-<filename>"
            )

        kind, filename = item.split("-", 1)
        kind = kind.strip()
        filename = filename.strip()

        if kind not in ("sample", "snippet", "template", "result"):
            raise ValueError(f"Unknown save kind '{kind}'")

        if not filename:
            raise ValueError(f"Missing filename for kind '{kind}'")

        parsed.append({"kind": kind, "path": filename})

    return parsed


def _write_file(filename: str, content: str) -> StatusString:
    try:
        Path(filename).write_text(content, encoding="utf-8")
        return StatusString(f"Successfully saved {filename}", status=True)
    except Exception as exc:
        return StatusString(
            f"Failed to save {filename}: {exc}", status=False, reason="error"
        )


def dry_run_save(result: BuildResult, sample: str, save_spec: str):
    """
    Dry-run version of save_outputs().

    Returns:
        list[str] of human-style dry-run messages:
            "[DRY-RUN] Would write out.txt"
            "[DRY-RUN] Would NOT write out.txt: Builder has no 'template' content"
    """
    try:
        items = parse_save_expression(save_spec)
    except ValueError as exc:
        return [f"[DRY-RUN] {exc}"]

    lines: list[str] = []

    for entry in items:
        kind = entry["kind"]
        filename = entry["path"]

        if kind == "sample":
            lines.append(f"[DRY-RUN] Would write {filename}")
            continue

        if result.warning:
            lines.append(f"[DRY-RUN] Would NOT write {filename}: {result.warning}")
            continue

        if kind in ("snippet", "template"):
            content = getattr(result, kind, None)
            if not content:
                msg = f"Builder has no '{kind}' content"
                lines.append(f"[DRY-RUN] Would NOT write {filename}: {msg}")
                continue

        elif kind == "result":
            content = result.result
            if not content:
                msg = f"No records found for {filename}"
                lines.append(f"[DRY-RUN] Would NOT write {filename}: {msg}")
                continue

        else:
            msg = f"Unknown save kind '{kind}'"
            lines.append(f"[DRY-RUN] Would NOT write {filename}: {msg}")
            continue

        lines.append(f"[DRY-RUN] Would write {filename}")

    return lines


def save_outputs(result: BuildResult, sample: str, save_spec: str):
    """
    Save outputs using the unified syntax:
        --save=sample-out.txt,snippet-snippet.txt,template-template.textfsm,result-out.json

    Returns:
        list[dict] with per-file info:
            {"kind": "...", "path": "...", "severity": "...", "message": "..."}
    """
    try:
        items = parse_save_expression(save_spec)
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

    for entry in items:
        kind = entry["kind"]
        filename = entry["path"]

        # sample is always allowed
        if kind == "sample":
            content = sample
            status = _write_file(filename, content)
            results.append(
                {
                    "kind": kind,
                    "path": filename,
                    "severity": status.reason,
                    "message": str(status),
                }
            )
            continue

        # builder-level warning blocks snippet/template/result
        if result.warning:
            status = StatusString(result.warning, status=False, reason="error")
            results.append(
                {
                    "kind": "build-result",
                    "path": None,
                    "severity": status.reason,
                    "message": str(status),
                }
            )
            continue

        # load content
        if kind in ("snippet", "template"):
            content = getattr(result, kind, None)
            if not content:
                msg = f"Builder has no '{kind}' content"
                status = StatusString(msg, status=False, reason="warning")
                results.append(
                    {
                        "kind": kind,
                        "path": filename,
                        "severity": status.reason,
                        "message": str(status),
                    }
                )
                continue

        elif kind == "result":
            content = result.result
            if not content:
                msg = f"No records found for {filename}"
                status = StatusString(msg, status=False, reason="warning")
                results.append(
                    {
                        "kind": kind,
                        "path": filename,
                        "severity": status.reason,
                        "message": str(status),
                    }
                )
                continue

        else:
            msg = f"Unknown save kind '{kind}'"
            status = StatusString(msg, status=False, reason="error")
            results.append(
                {
                    "kind": f"unknown-{kind}",
                    "path": None,
                    "severity": status.reason,
                    "message": str(status),
                }
            )
            continue

        # normalize content to string
        if not isinstance(content, str):
            content = json.dumps(content, indent=2, ensure_ascii=False)

        # write file
        status = _write_file(filename, content)
        results.append(
            {
                "kind": kind,
                "path": filename,
                "severity": status.reason,
                "message": str(status),
            }
        )

    return results


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
    cmd,
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
        lines.append(f"[INFO] Loaded sample from: {sample_file or cmd}")
        lines.append(f"[INFO] Sample size: {len(sample)} characters")

    lines.append("=== DEBUG INFO ===")
    if snippet_file:
        lines.append(f"snippet_file   = {snippet_file}")
    lines.append(f"sample_file    = {sample_file!r}")
    lines.append(f"command        = {cmd!r}")
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


# ------------------------------------------------------------
# Unified workflow engine
# ------------------------------------------------------------
def run_builder_workflow(
    builder_class,
    snippet="",
    snippet_file=None,
    sample_file=None,
    cmd="",
    params=None,
    save="",
    show="",
    config=None,
    debug=False,
    dry_run=False,
    suppressed_message=False,
    json_workflow: Optional[JsonWorkflow] = None,
):
    params = params or {}
    sample_text = ""

    if sample_file or cmd:
        sample_status = load_sample(sample_file, cmd)
        if not sample_status:
            if json_workflow:
                json_workflow.set_status(
                    kind=sample_status.reason,
                    message=str(sample_status),
                    exit_code=1,
                )
                click.echo(json_workflow.to_json())
                raise SystemExit(1)
            emit_status(sample_status)
            return 1
        sample_text = str(sample_status)

    if debug:
        debug_print(
            snippet,
            snippet_file,
            sample_file,
            cmd,
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
            click.echo(json_workflow.to_json())
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
            click.echo(json_workflow.to_json())
            raise SystemExit(1)

        status = StatusString(message, status=False, reason="error")
        emit_status(status)
        return 1

    result: BuildResult = builder.to_result()
    if not builder:
        message = (
            f"Cannot create builder from sample (reference: {sample_file or cmd!r})\n"
            "===========================================\n"
            f"{sample_text}\n"
        )
        if json_workflow:
            json_workflow.set_status(kind="warning", message=message, exit_code=1)
            click.echo(json_workflow.to_json())
            raise SystemExit(1)
        status = StatusString(message, status=False, reason="warning")
        emit_status(status)
        return 1

    # Save
    if save:
        if dry_run:
            lines = dry_run_save(result, sample_text, save)
            if json_workflow:
                json_workflow.add_save_dry_run(lines=lines)
                json_workflow.set_status(kind="success", message="", exit_code=0)
                click.echo(json_workflow.to_json())
                return 0
            print("\n".join(lines))
            return 0

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
        click.echo(json_workflow.to_json())
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
                    json_workflow.set_status(
                        kind="error", message=message, exit_code=1
                    )
                    click.echo(json_workflow.to_json())
                    raise SystemExit(1)
                print(message)
                raise SystemExit(1)

        if path.exists():
            message = f"[ERROR] Config file {str(path)!r} already exists!"
            if json_workflow:
                json_workflow.set_status(
                    kind="error", message=message, exit_code=1
                )
                click.echo(json_workflow.to_json())
                raise SystemExit(1)
            print(message)
            raise SystemExit(1)

        try:
            path.write_text(content, encoding="utf-8")
        except Exception as exc:
            message = f"[ERROR] Failed to write config file {str(path)!r}: {exc}"
            if json_workflow:
                json_workflow.set_status(
                    kind="error", message=message, exit_code=1
                )
                click.echo(json_workflow.to_json())
                raise SystemExit(1)
            print(message)
            raise SystemExit(1)

        message = f"[INFO] Config file {str(path)!r} created!"
        if json_workflow:
            json_workflow.add_generated_config(
                stream="io", path=str(path), payload=cfg
            )
            json_workflow.set_status(
                kind="success", message=message, exit_code=0
            )
            click.echo(json_workflow.to_json())
            raise SystemExit(0)
        print(message)
        raise SystemExit(0)

    if json_workflow:
        json_workflow.add_generated_config(
            stream="console", path=None, payload=cfg
        )
        json_workflow.set_status(kind="success", message="", exit_code=0)
        click.echo(json_workflow.to_json())
        raise SystemExit(0)

    click.echo(content)
    raise SystemExit(0)


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
    json_workflow=None
):
    """
    Create or preview a golden test case for the given builder.

    - If golden_path is empty:
        Perform a DRY RUN.
        Do NOT write any files.
        Show which files WOULD be created.
        Assume default path:
            ./tests/golden/integration/<case>

    - If golden_path is provided:
        Perform ACTUAL CREATION.
        golden_path MUST be under:
            tests/golden/integration/
        Auto-create parent directories.
        Fail if files already exist.
    """
    params = params or {}

    # ------------------------------------------------------------
    # 1. Determine mode
    # ------------------------------------------------------------
    if not golden_path:
        mode = "dry-run"
        case_name = f"{builder_name}-case"
        base_path = Path("tests") / "golden" / "integration" / case_name
    else:
        mode = "create"
        base_path = Path(golden_path).resolve()

        # Enforce directory structure only
        if not (
            base_path.parent.name == "integration"
            and base_path.parent.parent.name == "golden"
        ):
            message = (
                f"[ERROR] Golden test path {str(base_path)!r} must "
                f"be inside .../golden/integration/<case>"
            )
            if json_workflow:
                json_workflow.set_status(kind="error", message=message, exit_code=1)
                click.echo(json_workflow.to_json())
                raise SystemExit(1)

            print(message)
            raise SystemExit(1)

    # ------------------------------------------------------------
    # 2. Load sample (required)
    # ------------------------------------------------------------
    sample = None
    if sample_file or command:
        sample = load_sample(sample_file, command)

    if not sample or not sample.strip():
        message = "[ERROR] Golden test requires a non-empty sample."
        if json_workflow:
            json_workflow.set_status(kind="error", message=message, exit_code=1)
            click.echo(json_workflow.to_json())
            raise SystemExit(1)

        print(message)
        raise SystemExit(1)

    # ------------------------------------------------------------
    # 3. Instantiate builder
    # ------------------------------------------------------------
    builder = builder_class()

    # ------------------------------------------------------------
    # 4. Apply snippet/sample depending on builder type
    # ------------------------------------------------------------
    # Apply sample/snippet depending on builder type
    if issubclass(builder_class, FreeFormBuilder):
        if snippet_file:
            builder.set_snippet_file(snippet_file)
        else:
            builder.set_snippet(snippet)
        builder.set_sample(sample)

    elif issubclass(builder_class, (TabularBuilder, CategoryBuilder)):
        builder.set_sample(sample, **params)

    else:
        message = f"[ERROR] Unsupported builder class: {builder_class!r}"
        if json_workflow:
            json_workflow.set_status(kind="error", message=message, exit_code=1)
            click.echo(json_workflow.to_json())
            raise SystemExit(1)

        print(message)
        raise SystemExit(1)

    # ------------------------------------------------------------
    # 5. Build and get result
    # ------------------------------------------------------------
    builder.build()
    result: BuildResult = builder.to_result()

    # ------------------------------------------------------------
    # 6. Validate builder output
    # ------------------------------------------------------------
    if result.warning:
        message = f"[ERROR] Cannot create golden test: {result.warning}"
        if json_workflow:
            json_workflow.set_status(kind="error", message=message, exit_code=1)
            click.echo(json_workflow.to_json())
            raise SystemExit(1)

        print(message)
        raise SystemExit(1)

    # ------------------------------------------------------------
    # 7. Prepare manifest content
    # ------------------------------------------------------------
    manifest = {
        "builder": builder_name,
        "params": params,
        "saved": True,
        "meta": {
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
            click.echo(json_workflow.to_json())
            raise SystemExit(0)

        click.echo("\n".join(lines))
        raise SystemExit(0)

    # ------------------------------------------------------------
    # 9. Actual creation mode
    # ------------------------------------------------------------
    # Create directories
    for d in (inputs_dir, expected_dir, expected_results_dir):
        d.mkdir(parents=True, exist_ok=True)

    # Prevent overwriting existing files
    for label, path in files.items():
        if path.exists():
            message = f"[ERROR] {label} file {str(path)!r} already exists!"
            if json_workflow:
                json_workflow.set_status(kind="error", message=message, exit_code=1)
                click.echo(json_workflow.to_json())
                raise SystemExit(1)

            print(message)
            raise SystemExit(1)

    # Write files
    files["sample"].write_text(sample, encoding="utf-8")
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

    if json_workflow:
        json_workflow.add_golden_test(
            path=str(base_path),
            manifest={
                "path": str(files.get("manifest")),
                "content": json.dumps(manifest, indent=2, ensure_ascii=False)
            },
            inputs={
                "path": str(inputs_dir),
                "files": [
                    {
                        "path": str(files.get("inputs")),
                        "content": sample
                    }
                ]
            },
            expected_results={
                "path": str(expected_results_dir),
                "files": [
                    {
                        "path": str(files.get("expected_results")),
                        "content": json.dumps(result.result, indent=2, ensure_ascii=False)
                    }
                ]
            },
            expected={
                "path": str(expected_dir),
                "files": [
                    {
                        "path": str(files.get("snippet")),
                        "content": result.snippet
                    },
                    {
                        "path": str(files.get("template")),
                        "content": result.template
                    }
                ]

            }

        )

        json_workflow.set_status(kind="success", message="", exit_code=0)
        click.echo(json_workflow.to_json())
        raise SystemExit(0)

    print(f"[INFO] Golden test created at {str(base_path)!r}")
    raise SystemExit(0)
