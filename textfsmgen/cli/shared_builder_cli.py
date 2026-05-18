# textfsmgen/cli/shared_builder_cli.py

import json
from pathlib import Path
import click
from textfsmgen.libs.generic import StatusString
from textfsmgen.libs.common import emit_status
from textfsmgen.libs import shell
from textfsmgen.libs.utils import get_data_as_tabular
from textfsmgen.libs.text import render_text_block

from textfsmgen.core.builder import BuildResult


# ------------------------------------------------------------
# Merge helper
# ------------------------------------------------------------
def merge(cli_value, cfg, key, default=None):
    if cli_value not in (None, "", 0):
        return cli_value
    return cfg.get(key, default)


# ------------------------------------------------------------
# Config validation (parameterized)
# ------------------------------------------------------------
def validate_config(config_path, required_top_keys, required_param_keys):
    """
    Validate a JSON config file.

    Parameters:
        config_path (str): Path to JSON config file.
        required_top_keys (list[str]): Required top-level keys.
        required_param_keys (list[str]): Required keys inside "params".

    Returns:
        StatusString: success or failure with message and reason.
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
            reason="error",
        )

    # ------------------------------------------------------------
    # Validate top-level keys
    # ------------------------------------------------------------
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
    # Validate params block
    # ------------------------------------------------------------
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

    # ------------------------------------------------------------
    # Validate sample_file or command
    # ------------------------------------------------------------
    if not data.get("sample_file") and not data.get("command"):
        return StatusString(
            "Config must contain either 'sample_file' or 'command'",
            status=False,
            reason="warning",
        )

    # ------------------------------------------------------------
    # Valid config
    # ------------------------------------------------------------
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
# Dry-run save
# ------------------------------------------------------------
def dry_run_save(result: BuildResult, sample, save_spec):
    try:
        parsed_items = parse_save_expression(save_spec)
    except ValueError as exc:
        if save_spec.strip().startswith("json("):
            return [json.dumps({"status": "error", "error": str(exc)}, indent=2)]
        return [f"[DRY-RUN] {exc}"]

    wrapper = parsed_items[0][0]  # "json" or None

    json_items = []
    lines = []
    global_reason = None  # "warning" or "error"
    content = None

    for _, kind, filename in parsed_items:
        # ------------------------------------------------------------
        # sample is always allowed
        # ------------------------------------------------------------
        if kind == "sample":
            if wrapper == "json":
                json_items.append(
                    {
                        "kind": "sample",
                        "filename": filename,
                        "status": "ok",
                        "content": sample,
                    }
                )
            else:
                lines.append(f"[DRY-RUN] Would write {filename}:\n{sample}\n")
            continue

        # ------------------------------------------------------------
        # Builder-level warning
        # ------------------------------------------------------------
        if result.warning:
            msg = result.warning
            if wrapper == "json":
                json_items.append(
                    {
                        "kind": kind,
                        "filename": filename,
                        "status": "error",
                        "reason": msg,
                    }
                )
            else:
                lines.append(f"[DRY-RUN] Would NOT write {filename}: {msg}")
            global_reason = "error"
            continue

        # ------------------------------------------------------------
        # Load content
        # ------------------------------------------------------------
        if kind in ("snippet", "template"):
            content = getattr(result, kind, None)
            if not content:
                msg = f"Builder has no '{kind}' content"
                if wrapper == "json":
                    json_items.append(
                        {
                            "kind": kind,
                            "filename": filename,
                            "status": "error",
                            "reason": msg,
                        }
                    )
                else:
                    lines.append(f"[DRY-RUN] Would NOT write {filename}: {msg}")
                global_reason = "error"
                continue

        elif kind == "result":
            content = result.result
            if not content:
                msg = f"No records found for {filename}"
                if wrapper == "json":
                    json_items.append(
                        {
                            "kind": kind,
                            "filename": filename,
                            "status": "warning",
                            "reason": msg,
                        }
                    )
                else:
                    lines.append(f"[DRY-RUN] Would NOT write {filename}: {msg}")
                global_reason = "warning"
                continue

        # ------------------------------------------------------------
        # JSON mode
        # ------------------------------------------------------------
        if wrapper == "json":
            json_items.append(
                {
                    "kind": kind,
                    "filename": filename,
                    "status": "ok",
                    "content": content,
                }
            )
            continue

        # ------------------------------------------------------------
        # Plain mode
        # ------------------------------------------------------------
        lines.append(f"[DRY-RUN] Would write {filename}:\n{content}\n")

    # ------------------------------------------------------------
    # Final output
    # ------------------------------------------------------------
    if wrapper == "json":
        return [
            json.dumps(
                {"status": global_reason or "ok", "items": json_items},
                indent=2,
                ensure_ascii=False,
            )
        ]

    return lines


# ------------------------------------------------------------
# Save outputs
# ------------------------------------------------------------
def save_outputs(result: BuildResult, sample, save_spec):
    try:
        parsed_items = parse_save_expression(save_spec)
    except ValueError as exc:
        if save_spec.strip().startswith("json("):
            return {"status": "error", "error": str(exc)}
        return [StatusString(str(exc), status=False, reason="error")]

    wrapper = parsed_items[0][0]  # "json" or None

    json_results = {}
    results = []
    global_reason = None  # "warning" or "error"
    content = None

    for _, kind, filename in parsed_items:
        # ------------------------------------------------------------
        # sample is always allowed, regardless of warnings
        # ------------------------------------------------------------
        if kind == "sample":
            content = sample
            if wrapper == "json":
                try:
                    json_content = json.dumps(
                        {"sample": content}, indent=2, ensure_ascii=False
                    )
                    _write_file(filename, json_content)
                    json_results[kind] = {"status": "ok", "filename": filename}
                except Exception as exc:
                    json_results[kind] = {
                        "status": "error",
                        "filename": filename,
                        "reason": str(exc),
                    }
                continue

            # plain mode
            results.append(_write_file(filename, content))
            continue

        # ------------------------------------------------------------
        # Handle builder-level warning
        # ------------------------------------------------------------
        if result.warning:
            if wrapper == "json":
                json_results[kind] = {
                    "status": "error",
                    "filename": filename,
                    "reason": result.warning,
                }
            else:
                results.append(
                    StatusString(result.warning, status=False, reason="error")
                )
            global_reason = "error"
            continue

        # ------------------------------------------------------------
        # Load content
        # ------------------------------------------------------------
        if kind in ("snippet", "template"):
            content = getattr(result, kind, None)
            if not content:
                msg = f"Builder has no '{kind}' content"
                if wrapper == "json":
                    json_results[kind] = {
                        "status": "error",
                        "filename": filename,
                        "reason": msg,
                    }
                else:
                    results.append(StatusString(msg, status=False, reason="warning"))
                global_reason = "warning"
                continue

        elif kind == "result":
            content = result.result
            if not content:
                msg = f"No records found for {filename}"
                if wrapper == "json":
                    json_results[kind] = {
                        "status": "warning",
                        "filename": filename,
                        "reason": msg,
                    }
                else:
                    results.append(StatusString(msg, status=False, reason="warning"))
                global_reason = "warning"
                continue

        # ------------------------------------------------------------
        # JSON mode
        # ------------------------------------------------------------
        if wrapper == "json":
            try:
                json_content = json.dumps({kind: content}, indent=2, ensure_ascii=False)
                _write_file(filename, json_content)
                json_results[kind] = {"status": "ok", "filename": filename}
            except Exception as exc:
                json_results[kind] = {
                    "status": "error",
                    "filename": filename,
                    "reason": str(exc),
                }
                global_reason = "error"
            continue

        # ------------------------------------------------------------
        # Plain mode
        # ------------------------------------------------------------
        results.append(_write_file(filename, content))

    # ------------------------------------------------------------
    # Final return
    # ------------------------------------------------------------
    if wrapper == "json":
        json_results["status"] = "ok" if global_reason is None else global_reason
        return json_results

    return results


def _write_file(filename, content):
    try:
        Path(filename).write_text(content, encoding="utf-8")
        return StatusString(f"Successfully saved {filename}", status=True)
    except Exception as exc:
        return StatusString(
            f"Failed to save {filename}: {exc}", status=False, reason="error"
        )


def parse_save_expression(expr: str):
    expr = expr.strip()

    # Case 1: json(...)
    if expr.startswith("json(") and expr.endswith(")"):
        inner = expr[5:-1].strip()
        items = [i.strip() for i in inner.split(",") if i.strip()]
        wrapper = "json"
    else:
        # Case 2: plain
        items = [i.strip() for i in expr.split(",") if i.strip()]
        wrapper = None

    parsed = []
    for item in items:
        if "-" not in item:
            raise ValueError(
                f"Invalid save format: {item}\n"
                "Expected: kind-filename or json(kind-filename)"
            )

        kind, filename = item.split("-", 1)
        kind = kind.strip()
        filename = filename.strip()

        if kind not in ("snippet", "template", "result"):
            raise ValueError(f"Unknown save kind: {kind}")

        parsed.append((wrapper, kind, filename))

    return parsed


def show_outputs(result: BuildResult, sample, show_spec):
    show_spec = show_spec.strip()
    is_json = show_spec.startswith("json(") and show_spec.endswith(")")

    if is_json:
        inner = show_spec[len("json(") : -1].strip()
        cases = [x.strip() for x in inner.split(",") if x.strip()]
    else:
        cases = [x.strip() for x in show_spec.split(",") if x.strip()]

    parts = {} if is_json else []
    reason = None  # "warning" or "error"

    def add(container, item, name):
        if is_json:
            container[name] = item
        else:
            container.append(
                item
                if isinstance(item, str)
                else json.dumps(item, indent=2, ensure_ascii=False)
            )

    def json_wrap(status, value_):
        return {"status": status, "value": value_}

    if not cases:
        return StatusString(result.template, status=True)

    for case in cases:
        # snippet / template
        if case in ("snippet", "template"):
            value = getattr(result, case)
            add(parts, json_wrap("ok", value) if is_json else value, case)
            continue

        # sample
        if case == "sample":
            add(parts, json_wrap("ok", sample) if is_json else sample, case)
            continue

        # explicit result
        if case == "result":
            if result.warning:
                reason = "warning"
                add(
                    parts,
                    json_wrap("warning", result.warning) if is_json else result.warning,
                    "result",
                )
            else:
                add(
                    parts,
                    json_wrap("ok", result.result) if is_json else result.result,
                    "result",
                )
            continue

        # parsed result (default)
        if result.warning:
            reason = "warning"
            add(
                parts,
                json_wrap("warning", result.warning) if is_json else result.warning,
                "result",
            )
            continue

        parsed = result.result

        if case == "default":
            add(
                parts,
                json_wrap("ok", str(parsed)) if is_json else str(parsed),
                "result",
            )
            continue

        if case == "tabular":
            tab = get_data_as_tabular(parsed)
            add(parts, json_wrap("ok", tab) if is_json else tab, "result")
            continue

        # raw parsed result
        add(parts, json_wrap("ok", parsed) if is_json else parsed, "result")

    # Final output
    content = (
        json.dumps(parts, indent=2, ensure_ascii=False)
        if is_json
        else "\n======\n".join(parts)
    )

    return StatusString(content, status=(reason is None), reason=reason)


# ------------------------------------------------------------
# Debug printer
# ------------------------------------------------------------
def debug_print(sample_file, cmd, params, config, sample, save, show):
    click.echo(f"[INFO] Loaded sample from: {sample_file or cmd}")
    click.echo(f"[INFO] Sample size: {len(sample)} characters")

    click.echo("=== DEBUG INFO ===")
    click.echo(f"sample_file    = {sample_file!r}")
    click.echo(f"command        = {cmd!r}")
    click.echo(f"params         = {params}")
    params_txt = json.dumps(params, indent=2, ensure_ascii=False)
    click.echo(render_text_block(params_txt, subject="params         ="))
    if isinstance(config, dict):
        config_txt = json.dumps(config, indent=2, ensure_ascii=False)
        click.echo(render_text_block(config_txt, subject="config         ="))
    else:
        click.echo(f"config         = {config}")
    click.echo(f"save           = {save!r}")
    click.echo(f"show           = {show!r}")
    click.echo("==================")


# ------------------------------------------------------------
# Unified workflow engine
# ------------------------------------------------------------
def run_builder_workflow(
    builder_class,
    sample_file=None,
    cmd="",
    params=None,
    save="",
    show="",
    config=None,
    debug=False,
    dry_run=False,
):

    params = params or {}

    # Load sample
    sample = load_sample(sample_file, cmd)
    if not sample:
        emit_status(sample)
        return 1

    # Debug
    if debug:
        debug_print(sample_file, cmd, params, config, sample, save, show)

    # Instantiate builder
    builder = builder_class()

    # Apply sample/snippet depending on builder type
    if hasattr(builder, "set_sample"):
        builder.set_sample(sample, **params)
    elif hasattr(builder, "set_snippet"):
        builder.set_snippet(sample)
    else:
        status = StatusString(
            f"Builder {builder_class.__name__} does not support sample/snippet input",
            status=False,
            reason="error",
        )
        emit_status(status)
        return 1

    # Build
    try:
        builder.build()
    except Exception as exc:
        status = StatusString(
            f"{builder_class.__name__} build error ({type(exc).__name__}): {exc}",
            status=False,
            reason="error",
        )
        emit_status(status)
        return 1

    # Convert to BuildResult
    result: BuildResult = builder.to_result()

    if not builder:
        status = StatusString(
            f"Cannot create builder from sample (reference: {sample_file or cmd!r})\n"
            "===========================================\n"
            f"{sample}\n",
            status=False,
            reason="warning",
        )
        emit_status(status)
        return 1

    # Save
    if save:
        statuses = (
            dry_run_save(result, sample, save)
            if dry_run
            else save_outputs(result, sample, save)
        )
        exit_code = 0
        for st in statuses:
            emit_status(st)
            if not st:
                exit_code = 1
        return exit_code

    # Show
    status = show_outputs(result, sample, show)
    emit_status(status)
    return 0 if status else 1
