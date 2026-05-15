# textfsmgen/cli/shared_builder_cli.py

import json
from pathlib import Path
import click
from textfsmgen.libs.generic import StatusString, emit_status
from textfsmgen.libs.common import parse_textfsm_to_dicts
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

    required_keys = ["params", "input_file", "command", "show", "save"]
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

    if not data.get("input_file") and not data.get("command"):
        return StatusString(
            "Config must contain either 'input_file' or 'command'",
            status=False,
            reason="warning",
        )

    return StatusString(data, status=True)


# ------------------------------------------------------------
# Sample loading
# ------------------------------------------------------------
def load_sample(input_file, cmd):
    if input_file:
        try:
            content = Path(input_file).read_text(encoding="utf-8")
        except Exception as exc:
            return StatusString(
                f"Failed to read input-file: {exc}",
                status=False,
                reason="error",
            )
        if content.strip():
            return StatusString(content, status=True)
        return StatusString("Empty data from input-file",
                            status=False, reason="warning")

    if cmd:
        result = shell.execute_command(cmd)
        if not result.is_success:
            return StatusString(result.output,
                                status=False, reason="error")

        output = result.output or ""
        if output.strip():
            return StatusString(output, status=True)

        return StatusString(f"{cmd} has no output",
                            status=False, reason="warning")

    return StatusString("No input_file or cmd provided",
                        status=False, reason="warning")


# ------------------------------------------------------------
# Save outputs
# ------------------------------------------------------------
def save_outputs(builder, sample, save_spec):
    results = []
    items = [x.strip() for x in save_spec.split(",") if x.strip()]

    for item in items:
        # Validate format
        if "-" not in item:
            results.append(StatusString(
                f"Invalid save format: {item}\n"
                "Save format must be: <type>-<filename>\n"
                "  <type> may be: snippet, template, json-snippet, json-template, result\n"
                "\n"
                "Examples:\n"
                "  snippet-out.txt             → write builder.snippet to out.txt\n"
                "  template-template.textfsm   → write builder.template to template.textfsm\n"
                "  result-output.json          → write parsed result to output.json\n"
                "  json-snippet-snippet.json   → write {\"snippet\": ...} to snippet.json\n"
                "  json-template-template.json → write {\"template\": ...} to template.json\n",
                status=False,
                reason="error"
            ))
            continue

        # Handle json-snippet
        if item.lower().startswith("json-snippet-"):
            filename = item[len("json-snippet-"):].strip()
            content = json.dumps({"snippet": getattr(builder, "snippet", None)},
                                 indent=2, ensure_ascii=False)
            results.append(_write_file(filename, content))
            continue

        # Handle json-template
        if item.lower().startswith("json-template-"):
            filename = item[len("json-template-"):].strip()
            content = json.dumps({"template": getattr(builder, "template", None)},
                                 indent=2, ensure_ascii=False)
            results.append(_write_file(filename, content))
            continue

        # Normal split for snippet/template/result
        t, filename = item.split("-", 1)
        t, filename = t.strip(), filename.strip()

        # snippet / template
        if t in ("snippet", "template"):
            content = getattr(builder, t, None)
            if not content:
                results.append(StatusString(
                    f"Builder has no '{t}' content",
                    status=False, reason="warning"))
                continue
            results.append(_write_file(filename, content))
            continue

        # result
        if t == "result":
            parsed = parse_textfsm_to_dicts(builder.template, sample)
            content = json.dumps(parsed, indent=2, ensure_ascii=False)
            if not parsed:
                results.append(StatusString(
                    f"No records found for {filename}",
                    status=False, reason="warning"))
            results.append(_write_file(filename, content))
            continue

        # Unknown type
        results.append(StatusString(
            f"Unknown save type '{t}'",
            status=False, reason="error"
        ))

    return results


def _write_file(filename, content):
    try:
        Path(filename).write_text(content, encoding="utf-8")
        return StatusString(f"Successfully saved {filename}", status=True)
    except Exception as exc:
        return StatusString(
            f"Failed to save {filename}: {exc}",
            status=False, reason="error")


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

    def parse_result():
        try:
            parsed_ = parse_textfsm_to_dicts(builder.template, sample)
            return parsed_, None
        except Exception as exc:
            return None, str(exc)

    if not cases:
        return StatusString(builder.template, status=True)

    for case in cases:
        if case in ("snippet", "template"):
            add(parts, getattr(builder, case), case)
            continue

        if case == "sample":
            add(parts, sample, case)
            continue

        parsed, err = parse_result()
        if err:
            add(parts, err, "result")
            reason = "error"
            continue

        if not parsed:
            msg = "no record found after parsed sample with textfsm template"
            add(parts, msg, "result")
            reason = "warning"
            continue

        if case == "default":
            add(parts, str(parsed), "result")
            continue

        if case == "tabular":
            add(parts, get_data_as_tabular(parsed), "result")
            continue

        add(parts, parsed, "result")

    content = (
        json.dumps(parts, indent=2, ensure_ascii=False)
        if is_json else "\n======\n".join(parts)
    )
    return StatusString(content, status=(reason == ""), reason=reason or None)


# ------------------------------------------------------------
# Dry-run save
# ------------------------------------------------------------
def dry_run_save(builder, sample, save_spec):   # noqa
    results = []
    items = [x.strip() for x in save_spec.split(",") if x.strip()]

    for item in items:
        if "-" not in item:
            results.append(StatusString(
                f"[DRY-RUN] Invalid save format: {item}\n"
                "Save format must be: <type>-<filename>\n"
                "  <type> may be: snippet, template, json-snippet, json-template, result\n"
                "\n"
                "Examples:\n"
                "  snippet-out.txt             → write builder.snippet to out.txt\n"
                "  template-template.textfsm   → write builder.template to template.textfsm\n"
                "  result-output.json          → write parsed result to output.json\n"
                '  json-snippet-snippet.json   → write {"snippet": builder.snippet} to snippet.json\n'
                '  json-template-template.json → write {"template": builder.template} to template.json\n',
                status=False,
                reason=""
            ))
            continue

        # Handle json-snippet
        if item.lower().startswith("json-snippet-"):
            filename = item[len("json-snippet-"):].strip()
            results.append(StatusString(
                '[DRY-RUN] Would save {"snippet": builder.snippet} → ' + filename,
                status=True))
            continue

        # Handle json-template
        if item.lower().startswith("json-template-"):
            filename = item[len("json-template-"):].strip()
            results.append(StatusString(
                '[DRY-RUN] Would save {"template": builder.template} → ' + filename,
                status=True))
            continue

        t, filename = item.split("-", 1)
        t, filename = t.strip(), filename.strip()

        if t in ("snippet", "template", "result"):
            case = "parsed result" if t == "result" else f"builder.{t}"
            results.append(StatusString(
                f"[DRY-RUN] Would save {case} → {filename}",
                status=True))
            continue

        results.append(StatusString(
            f"[DRY-RUN] Unknown save type '{t}'",
            status=False, reason=""))

    return results


# ------------------------------------------------------------
# Debug printer
# ------------------------------------------------------------
def debug_print(input_file, cmd, params, config, sample, save, show):
    click.echo(f"[INFO] Loaded sample from: {input_file or cmd}")
    click.echo(f"[INFO] Sample size: {len(sample)} characters")
    click.echo("=== DEBUG INFO ===")
    click.echo(f"input_file     = {input_file!r}")
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
    input_file,
    cmd,
    params,
    save,
    show,
    config,
    debug,
    dry_run,
):
    # Load sample
    sample = load_sample(input_file, cmd)
    if not sample:
        emit_status(sample)
        return 1

    # Debug
    if debug:
        debug_print(input_file, cmd, params, config, sample, save, show)

    # Build
    builder = builder_class(user_data=sample, **params)
    if not builder:
        status = StatusString(
            f"Cannot create builder from sample (reference: {input_file or cmd!r})\n"
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
            if dry_run else save_outputs(builder, sample, save)
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
