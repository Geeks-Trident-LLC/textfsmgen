# textfsmgen/cli/tabular_cmd.py

import json
from pathlib import Path
import click

from textfsmgen.libs.generic import StatusString, emit_status
from textfsmgen.libs.common import parse_textfsm_to_dicts
from textfsmgen.libs import shell
from textfsmgen import TabularTemplateBuilder
from textfsmgen.libs.utils import get_data_as_tabular


# ------------------------------------------------------------
# CLI Registration
# ------------------------------------------------------------
def register(cli):
    cli.add_command(tabular)


# ------------------------------------------------------------
# Main CLI Command
# ------------------------------------------------------------
@click.command(
    help="Tabular builder for snippet/template/result generation.",
    context_settings=dict(help_option_names=["-h", "--help"])
)
@click.option("--input-file", default=None, type=click.Path(exists=True))
@click.option("--command", "cmd", default="")
@click.option("--column-divider", default="")
@click.option("--column-count", default=0, type=int)
@click.option("--column-widths", default=None)
@click.option("--headers", default=None)
@click.option("--header-rows", default=None)
@click.option("--custom-header", default="")
@click.option("--starting-from", default=None)
@click.option("--ending-at", default=None)
@click.option("--has-header", is_flag=True, default=True)
@click.option("--replacing-rules", default=None)
@click.option("--show", default="")
@click.option("--save", default="")
@click.option("--config", default=None, type=click.Path(exists=True))
@click.option("--debug", is_flag=True, default=False)
@click.option("--dry-run", is_flag=True, default=False)
@click.pass_context
def tabular(
    ctx,
    input_file,
    cmd,
    column_divider,
    column_count,
    column_widths,
    headers,
    header_rows,
    custom_header,
    starting_from,
    ending_at,
    has_header,
    replacing_rules,
    show,
    save,
    config,
    debug,
    dry_run,
):
    # ------------------------------------------------------------
    # Show help if nothing provided
    # ------------------------------------------------------------
    if not input_file and not cmd and config is None:
        click.echo(ctx.get_help())
        return 0

    # ------------------------------------------------------------
    # Load config
    # ------------------------------------------------------------
    config_data = {}
    if config:
        status = validate_config(config)
        if not status:
            emit_status(status)
            return 1
        config_data = status.raw or {}

    # ------------------------------------------------------------
    # Merge CLI + config
    # ------------------------------------------------------------
    input_file_ = merge(input_file, config_data, "input_file", "")
    cmd_ = merge(cmd, config_data, "command", "")
    save_ = merge(save, config_data, "save", "")
    show_ = merge(show, config_data, "show", "")

    params = {
        "column_divider": merge(column_divider, config_data, "column_divider", ""),
        "column_count": merge(column_count, config_data, "column_count", 0),
        "column_widths": merge(column_widths, config_data, "column_widths", None),
        "headers": merge(headers, config_data, "headers", None),
        "header_rows": merge(header_rows, config_data, "header_rows", None),
        "custom_header_text": merge(custom_header, config_data, "custom_header_text", ""),
        "starting_from": merge(starting_from, config_data, "starting_from", None),
        "ending_at": merge(ending_at, config_data, "ending_at", None),
        "has_header_row": merge(has_header, config_data, "has_header_row", True),
        "replacing_rules": merge(replacing_rules, config_data, "replacing_rules", None),
    }

    # ------------------------------------------------------------
    # Must have input_file or cmd
    # ------------------------------------------------------------
    if not input_file_ and not cmd_:
        emit_status(StatusString("Either input_file or command must be provided",
                                 status=False, reason="warning"))
        return 1

    # ------------------------------------------------------------
    # Load sample
    # ------------------------------------------------------------
    sample = load_sample_from_input_or_cmd(input_file_, cmd_)
    if not sample:
        emit_status(sample)
        return 1

    # ------------------------------------------------------------
    # Debug mode
    # ------------------------------------------------------------
    if debug:
        debug_print(input_file_, cmd_, params, config, sample, save_, show_)

    # ------------------------------------------------------------
    # Build template
    # ------------------------------------------------------------

    builder = TabularTemplateBuilder(user_data=sample, **params)
    if not builder:
        ref = input_file_ or cmd_
        status = StatusString(
            f"Cannot create tabular builder from sample (reference: {ref!r})\n"
            "===========================================\n"
            f"{sample}\n",
            status=False,
            reason="warning",
        )
        emit_status(status)
        return 1

    # ------------------------------------------------------------
    # Save mode
    # ------------------------------------------------------------
    if save_:
        if dry_run:
            click.echo("[DRY-RUN] No files will be written.")
            statuses = dry_run_save(builder, sample, save_)
        else:
            statuses = save_outputs(builder, sample, save_)

        exit_code = 0
        for st in statuses:
            emit_status(st)
            if not st:
                exit_code = 1
        return exit_code

    # ------------------------------------------------------------
    # Show mode
    # ------------------------------------------------------------
    status = show_outputs(builder, sample, show_)
    emit_status(status)
    return 0 if status else 1


# ------------------------------------------------------------
# Debug Printer
# ------------------------------------------------------------
def debug_print(input_file, cmd, params, config, sample, save, show):
    click.echo(f"[INFO] Loaded sample from: {input_file or cmd}")
    click.echo(f"[INFO] Sample size: {len(sample)} characters")
    click.echo("=== DEBUG INFO ===")
    click.echo(f"input_file     = {input_file!r}")
    click.echo(f"command        = {cmd!r}")
    click.echo(f"params         = {params}")
    click.echo(f"config         = {config}")
    click.echo(f"save           = {save!r}")
    click.echo(f"show           = {show!r}")
    click.echo("==================")


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------
def merge(cli_value, cfg, key, default=None):
    if cli_value not in (None, "", 0):
        return cli_value
    return cfg.get(key, default)


def write_file(filename, content):
    try:
        Path(filename).write_text(content, encoding="utf-8")
        return StatusString(f"Successfully saved {filename}", status=True)
    except Exception as exc:
        return StatusString(f"Failed to save {filename}: {exc}",
                            status=False, reason="error")


# ------------------------------------------------------------
# Config Validation
# ------------------------------------------------------------
def validate_config(config):
    try:
        raw = click.open_file(config).read()
        data = json.loads(raw)
    except Exception as exc:
        return StatusString(f"Failed to load config JSON: {exc}",
                            status=False, reason="error")

    required_keys = [
        "params", "input_file", "command", "show", "save"
    ]
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
        return StatusString("Config 'params' must be a dictionary",
                            status=False, reason="warning")

    required_params = [
        "column_divider",
        "column_count",
        "column_widths",
        "headers",
        "header_rows",
        "custom_header_text",
        "starting_from",
        "ending_at",
        "has_header_row",
        "replacing_rules",
    ]

    missing_params = [k for k in required_params if k not in params]
    if missing_params:
        return StatusString(
            f"Missing required params: {', '.join(missing_params)}\n"
            f"Required: {', '.join(required_params)}",
            status=False,
            reason="warning",
        )

    if not data.get("input_file") and not data.get("command"):
        return StatusString("Config must contain either 'input_file' or 'command'",
                            status=False, reason="warning")

    return StatusString(data, status=True)


# ------------------------------------------------------------
# Sample Loading
# ------------------------------------------------------------
def load_sample_from_input_or_cmd(input_file, cmd):
    if input_file:
        try:
            content = Path(input_file).read_text(encoding="utf-8")
        except Exception as exc:
            return StatusString(f"Failed to read input-file: {exc}",
                                status=False, reason="error")
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
# Save Outputs
# ------------------------------------------------------------
def save_outputs(builder, sample, save_spec):
    results = []
    items = [x.strip() for x in save_spec.split(",") if x.strip()]

    for item in items:
        if "-" not in item:
            results.append(StatusString(
                f"Invalid save format: {item}",
                status=False, reason="error"))
            continue

        t, filename = item.split("-", 1)
        t, filename = t.strip(), filename.strip()

        if t in ("snippet", "template"):
            content = getattr(builder, t, None)
            if not content:
                results.append(StatusString(
                    f"Builder has no '{t}' content",
                    status=False, reason="warning"))
                continue
            results.append(write_file(filename, content))
            continue

        if t == "json-snippet":
            obj = {"snippet": builder.snippet}
            content = json.dumps(obj, indent=2, ensure_ascii=False)
            results.append(write_file(filename, content))
            continue

        if t == "json-template":
            obj = {"template": builder.template}
            content = json.dumps(obj, indent=2, ensure_ascii=False)
            results.append(write_file(filename, content))
            continue

        if t == "result":
            parsed = parse_textfsm_to_dicts(builder.template, sample)
            content = json.dumps(parsed, indent=2, ensure_ascii=False)
            if not parsed:
                results.append(StatusString(
                    f"No records found for {filename}",
                    status=False, reason="warning"))
            results.append(write_file(filename, content))
            continue

        results.append(StatusString(
            f"Unknown save type '{t}'",
            status=False, reason="error"))

    return results


# ------------------------------------------------------------
# Show Outputs
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

    def add_item(container, item, name, json_mode):
        if json_mode:
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
            add_item(parts, getattr(builder, case), case, is_json)
            continue

        if case == "sample":
            add_item(parts, sample, case, is_json)
            continue

        parsed, err = parse_result()
        if err:
            add_item(parts, err, "result", is_json)
            reason = "error"
            continue

        if not parsed:
            msg = "no record found after parsed sample with textfsm template"
            add_item(parts, msg, "result", is_json)
            reason = "warning"
            continue

        if case == "default":
            add_item(parts, str(parsed), "result", is_json)
            continue

        if case == "tabular":
            tabular_text = get_data_as_tabular(parsed)
            add_item(parts, tabular_text, "result", is_json)
            continue

        add_item(parts, parsed, "result", is_json)

    if is_json:
        content = json.dumps(parts, indent=2, ensure_ascii=False)
        return StatusString(content, status=(reason == ""), reason=reason or None)

    content = "\n======\n".join(parts)
    return StatusString(content, status=(reason == ""), reason=reason or None)


# ------------------------------------------------------------
# Dry-run Save
# ------------------------------------------------------------
def dry_run_save(builder, sample, save_spec):   # noqa
    results = []
    items = [x.strip() for x in save_spec.split(",") if x.strip()]

    for item in items:
        if "-" not in item:
            results.append(StatusString(
                f"[DRY-RUN] Invalid save format: {item}",
                status=False, reason="error"))
            continue

        t, filename = item.split("-", 1)
        t, filename = t.strip(), filename.strip()

        if t in ("snippet", "template", "json-snippet", "json-template", "result"):
            results.append(StatusString(
                f"[DRY-RUN] Would save {t} → {filename}",
                status=True))
            continue

        results.append(StatusString(
            f"[DRY-RUN] Unknown save type '{t}'",
            status=False, reason="error"))

    return results
