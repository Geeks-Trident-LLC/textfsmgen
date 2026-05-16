# textfsmgen/cli/shared_builder_cli.py

import json
from pathlib import Path
import click
from textfsmgen.libs.generic import StatusString
from textfsmgen.libs.common import parse_textfsm_to_dicts, emit_status
from textfsmgen.libs import shell
from textfsmgen.libs.utils import get_data_as_tabular
from textfsmgen.libs.text import render_text_block


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
def validate_config(config, required_params):
    try:
        raw = click.open_file(config).read()
        data = json.loads(raw)
    except Exception as exc:
        return StatusString(
            f"Failed to load config JSON: {exc}",
            status=False,
            reason="error",
        )

    required_keys = ["params", "sample_file", "command", "show", "save"]
    missing_top = [k for k in required_keys if k not in data]
    if missing_top:
        return StatusString(
            f"Missing required key(s): {', '.join(missing_top)}\n"
            f"Required: {', '.join(required_keys)}",
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

    missing_params = [k for k in required_params if k not in params]
    if missing_params:
        return StatusString(
            f"Missing required params: {', '.join(missing_params)}\n"
            f"Required: {', '.join(required_params)}",
            status=False,
            reason="warning",
        )

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

    return StatusString("No sample_file or cmd provided", status=False, reason="warning")


# ------------------------------------------------------------
# Dry-run save
# ------------------------------------------------------------
def dry_run_save(builder, sample, save_spec):
    try:
        parsed_items = parse_save_expression(save_spec)
    except ValueError as exc:
        if save_spec.strip().startswith("json("):
            return [json.dumps({"status": "error", "error": str(exc)}, indent=2)]
        return [f"[DRY-RUN] {exc}"]

    wrapper = parsed_items[0][0]  # JSON or None

    json_results = []
    lines = []

    for _, kind, filename in parsed_items:
        content = None  # always defined

        # Load content
        if kind in ("snippet", "template"):
            content = getattr(builder, kind, None)
        elif kind == "result":
            content = parse_textfsm_to_dicts(builder.template, sample)

        # JSON mode
        if wrapper == "json":
            json_results.append({
                "kind": kind,
                "filename": filename,
                "content": content
            })
            continue

        # Plain mode
        lines.append(
            f"[DRY-RUN] Would write {filename}:\n{content}\n"
        )

    if wrapper == "json":
        return [json.dumps(json_results, indent=2, ensure_ascii=False)]

    return lines


# ------------------------------------------------------------
# Save outputs
# ------------------------------------------------------------
def save_outputs(builder, sample, save_spec):
    try:
        parsed_items = parse_save_expression(save_spec)
    except ValueError as exc:
        # JSON mode → return JSON error
        if save_spec.strip().startswith("json("):
            return {
                "status": "error",
                "error": str(exc)
            }
        # Plain mode → return StatusString
        return [StatusString(str(exc), status=False, reason="error")]

    wrapper = parsed_items[0][0]  # JSON or None

    # JSON mode accumulates structured results
    json_results = {}

    # Plain mode accumulates StatusString objects
    results = []

    for _, kind, filename in parsed_items:
        content = None  # always defined

        # Load content
        if kind in ("snippet", "template"):
            content = getattr(builder, kind, None)
            if not content:
                msg = f"Builder has no '{kind}' content"
                if wrapper == "json":
                    json_results[kind] = {
                        "status": "error",
                        "filename": filename,
                        "reason": msg
                    }
                    continue
                results.append(StatusString(msg, status=False, reason="warning"))
                continue

        elif kind == "result":
            content = parse_textfsm_to_dicts(builder.template, sample)
            if not content:
                msg = f"No records found for {filename}"
                if wrapper == "json":
                    json_results[kind] = {
                        "status": "warning",
                        "filename": filename,
                        "reason": msg
                    }
                    continue
                results.append(StatusString(msg, status=False, reason="warning"))
                continue

        # JSON mode
        if wrapper == "json":
            try:
                json_content = json.dumps({kind: content}, indent=2, ensure_ascii=False)
                _write_file(filename, json_content)
                json_results[kind] = {
                    "status": "ok",
                    "filename": filename
                }
            except Exception as exc:
                json_results[kind] = {
                    "status": "error",
                    "filename": filename,
                    "reason": str(exc)
                }
            continue

        # Plain mode
        results.append(_write_file(filename, content))

    # JSON mode → return JSON object
    if wrapper == "json":
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


# ------------------------------------------------------------
# Show outputs
# ------------------------------------------------------------
def show_outputs(builder, sample, show_spec):
    show_spec = show_spec.strip()
    is_json = show_spec.startswith("json(") and show_spec.endswith(")")

    if is_json:
        inner = show_spec[len("json("):-1].strip()
        cases = [x.strip() for x in inner.split(",") if x.strip()]
    else:
        cases = [x.strip() for x in show_spec.split(",") if x.strip()]

    parts = {} if is_json else []
    reason = ""

    def add(container, item, name):
        if is_json:
            container[name] = item
        else:
            container.append(
                item if isinstance(item, str)
                else json.dumps(item, indent=2, ensure_ascii=False)
            )

    def json_wrap(status, value):
        return {
            "status": status,
            "value": value
        }

    def parse_result():
        try:
            parsed_ = parse_textfsm_to_dicts(builder.template, sample)
            return parsed_, None
        except Exception as exc:
            return None, str(exc)

    if not cases:
        return StatusString(builder.template, status=True)

    for case in cases:
        # snippet / template
        if case in ("snippet", "template"):
            value = getattr(builder, case)
            add(parts, json_wrap("ok", value) if is_json else value, case)
            continue

        # sample
        if case == "sample":
            add(parts, json_wrap("ok", sample) if is_json else sample, case)
            continue

        # parse result
        parsed, err = parse_result()
        if err:
            reason = "error"
            add(parts, json_wrap("error", err) if is_json else err, "result")
            continue

        if not parsed:
            msg = "no record found after parsed sample with textfsm template"
            reason = "warning"
            add(parts, json_wrap("warning", msg) if is_json else msg, "result")
            continue

        # default
        if case == "default":
            value = str(parsed)
            add(parts, json_wrap("ok", value) if is_json else value, "result")
            continue

        # tabular
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

    return StatusString(content, status=(reason == ""), reason=reason or None)


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
    sample_file,
    cmd,
    params,
    save,
    show,
    config,
    debug,
    dry_run,
):
    # Load sample
    sample = load_sample(sample_file, cmd)
    if not sample:
        emit_status(sample)
        return 1

    # Debug
    if debug:
        debug_print(sample_file, cmd, params, config, sample, save, show)

    # Build
    builder = builder_class(user_data=sample, **params)
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
            dry_run_save(builder, sample, save)
            if dry_run
            else save_outputs(builder, sample, save)
        )
        exit_code = 0
        for st in statuses:
            emit_status(st)
            if not st:
                exit_code = 1
        return exit_code

    # Show
    status = show_outputs(builder, sample, show)
    emit_status(status)
    return 0 if status else 1
