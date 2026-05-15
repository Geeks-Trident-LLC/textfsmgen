# textfsmgen/cli/category_cmd.py
import click
import json
import sys

from textfsmgen.libs.generic import StatusString, emit_status
from textfsmgen.libs.common import parse_textfsm_to_dicts
from textfsmgen.libs import shell

from textfsmgen import CategoryTemplateBuilder, TabularTemplateBuilder, TemplateBuilder
from textfsmgen.libs.utils import get_data_as_tabular

from pathlib import Path


# Register the command with the root CLI
def register(cli):
    cli.add_command(category)


@click.command(
    help="Category builder for snippet/template/result generation.",
    context_settings=dict(help_option_names=["-h", "--help"])
)
@click.option(
    "--input-file",
    default=None,
    type=click.Path(exists=True),
    help="Input filename (default: empty)."
)
@click.option(
    "--command",
    "cmd",
    default="",
    help="Shell command to generate real-world sample (default: empty)."
)
@click.option(
    "--count",
    default=1,
    type=int,
    show_default=True,
    help="Number of category pairs to generate."
)
@click.option(
    "--separator",
    default=":",
    show_default=True,
    help="Separator between key/value pairs."
)
@click.option(
    "--starting-from",
    default="",
    help="Starting-from marker (default: empty)."
)
@click.option(
    "--ending-at",
    default="",
    help="Ending-at marker (default: empty)."
)
@click.option(
    "--replacing-rules",
    default="",
    help="Replacing rules (string or JSON-like). Default empty."
)
@click.option(
    "--show",
    default="",
    help="Show output: snippet, template, result."
)
@click.option(
    "--save",
    default="",
    help="Save output to a file (default empty)."
)
@click.option(
    "--config",
    default=None,
    type=click.Path(exists=True),
    help="JSON config file (optional)."
)
@click.pass_context
def category(
    ctx,
    input_file,
    cmd,
    count,
    separator,
    starting_from,
    ending_at,
    replacing_rules,
    show,
    save,
    config,
):
    # ------------------------------------------------------------
    # Case 1: no options → print help
    # ------------------------------------------------------------
    if not input_file and not cmd and config is None:
        click.echo(ctx.get_help())
        return 0

    # ------------------------------------------------------------
    # Case 2: input-file or command provided → print values
    # ------------------------------------------------------------
    if input_file or cmd:
        sample = load_sample_from_input_or_cmd(input_file, cmd)
        if not sample:
            emit_status(sample)
            return 1
        params = {
            "count": abs(count) or 1,
            "separator": separator or ":",
            "starting_from": starting_from or None,
            "ending_at": ending_at or None,
            "replacing_rules": replacing_rules or None,
        }

        builder = CategoryTemplateBuilder(user_data=sample, **params)
        if not builder:
            ref = input_file or cmd
            status = StatusString(
                (
                    f"Cannot create category builder from sample (reference: {ref!r})\n"
                    "===========================================\n"
                    f"{sample}\n"
                ),
                status=False,
                reason="warning"
            )
            emit_status(status)
            return 1

        if save:
            statuses = save_outputs(builder, sample, save)
            exit_code = 0
            for ok in statuses:
                emit_status(ok)
                if not ok:
                    exit_code = 1
            return exit_code

        status = show_outputs(builder, sample, show)

        emit_status(status)
        if not status:
            return 1
        return 0

    # ------------------------------------------------------------
    # Case 3: config provided → validate config
    # ------------------------------------------------------------
    if config:
        # Load JSON
        try:
            raw = click.open_file(config).read()
            data = json.loads(raw)
        except Exception as exc:
            click.echo(f"[ERROR] Failed to load config JSON: {exc}", err=True)
            return 1

        # Required top-level keys
        required_keys = ["params", "input_file", "command", "show", "save"]
        for key in required_keys:
            if key not in data:
                click.echo(f"[ERROR] Missing required key in config: '{key}'",
                           err=True)
                return 1

        # input_file or command must have value
        if not data["input_file"] and not data["command"]:
            click.echo(
                "Error: Config must contain either 'input_file' or "
                "'command' with a non-empty value",
                err=True,
            )
            return 1

        # Validate params
        params = data["params"]

        if not validate_params(params):
            return 1

    # ------------------------------------------------------------
    # Should never reach here
    # ------------------------------------------------------------
    click.echo("Error: Unexpected state", err=True)
    return 1


def validate_params(params):
    required_params = [
        "count",
        "separator",
        "starting_from",
        "ending_at",
        "replacing_rules",
    ]

    for key in required_params:
        if key not in params:
            click.echo(f"Error: Missing required params key: '{key}'",
                       err=True)
            return False

    click.echo("Config file validated successfully.")
    return True


def load_sample_from_input_or_cmd(input_file, cmd):
    """
    Load sample data from either input_file or cmd.

    Rules:
      - If input_file is provided:
            * Read file
            * If content has at least one non-whitespace char → success
            * Else → failure ("Empty data from input-file")
      - If cmd is provided:
            * Execute shell command
            * If execution succeeds and output has data → success
            * Else if execution succeeds but empty → failure ("cmd has no output")
            * Else → failure with error message
    """
    # ------------------------------------------------------------
    # Case 1: input_file provided → read file
    # ------------------------------------------------------------
    if input_file:
        try:
            content = Path(input_file).read_text(encoding="utf-8")
        except Exception as exc:
            return StatusString(
                "Failed to read input-file: {}".format(exc),
                status=False,
                reason="error",
            )

        if content.strip():
            return StatusString(content, status=True)

        return StatusString(
            "Empty data from input-file",
            status=False,
            reason="warning",
        )

    # ------------------------------------------------------------
    # Case 2: cmd provided → execute command
    # ------------------------------------------------------------
    if cmd:
        result = shell.execute_command(cmd)

        if not result.is_success:
            return StatusString(
                result.output,
                status=False,
                reason="error",
            )

        output = result.output or ""
        if output.strip():
            return StatusString(output, status=True)

        return StatusString(
            "{} has no output".format(cmd),
            status=False,
            reason="warning",
        )

    # ------------------------------------------------------------
    # Should not reach here (caller ensures one is provided)
    # ------------------------------------------------------------
    return StatusString(
        "No input_file or cmd provided",
        status=False,
        reason="warning",
    )


def save_outputs(builder, sample, save_spec):
    """
    Save builder outputs based on save_spec string.

    save_spec format:
        "<type>-<filename>, <type>-<filename>, ..."

    Returns:
        list[StatusString]
    """
    results = []

    # ------------------------------------------------------------
    # Parse save_spec into (type, filename) pairs
    # ------------------------------------------------------------
    items = [x.strip() for x in save_spec.split(",") if x.strip()]
    pairs = []

    for item in items:
        if "-" not in item:
            results.append(
                StatusString(
                    "Invalid save format: '{}'".format(item),
                    status=False,
                    reason="error",
                )
            )
            continue

        t, fname = item.split("-", 1)
        pairs.append((t.strip(), fname.strip()))

    # ------------------------------------------------------------
    # Helper: write file safely
    # ------------------------------------------------------------
    def write_file(filename_, content_):
        try:
            Path(filename_).write_text(content_, encoding="utf-8")
            return StatusString(
                f"Successfully saved {filename_!r}",
                status=True,
            )
        except Exception as exc:
            return StatusString(
                f"Failed to save {filename_!r}: {exc}",
                status=False,
                reason="error",
            )

    # ------------------------------------------------------------
    # Dispatch table for save types
    # ------------------------------------------------------------
    for t, filename in pairs:

        # snippet / template
        if t in ("snippet", "template"):
            content = getattr(builder, t, None)
            if not content:
                results.append(
                    StatusString(
                        "Builder has no '{}' content".format(t),
                        status=False,
                        reason="warning",
                    )
                )
                continue

            results.append(write_file(filename, content))
            continue

        # json-snippet
        if t == "json-snippet":
            obj = {"snippet": builder.snippet}
            content = json.dumps(obj, indent=2, ensure_ascii=False)
            results.append(write_file(filename, content))
            continue

        # json-template
        if t == "json-template":
            obj = {"template": builder.template}
            content = json.dumps(obj, indent=2, ensure_ascii=False)
            results.append(write_file(filename, content))
            continue

        # result
        if t == "result":
            parsed = parse_textfsm_to_dicts(builder.template, sample)
            content = json.dumps(parsed, indent=2, ensure_ascii=False)

            if not parsed:
                results.append(
                    StatusString(
                        "No records found for '{}'".format(filename),
                        status=False,
                        reason="warning",
                    )
                )

            results.append(write_file(filename, content))
            continue

        # unknown type
        results.append(
            StatusString(
                "Unknown save type '{}'".format(t),
                status=False,
                reason="error",
            )
        )

    return results


def show_outputs(builder, sample, show_spec):
    """
    Produce output for the --show option.

    show_spec formats:
        "json(snippet, template, result)"
        "snippet, template, result"
        "json(default)"
        "default"

    Returns:
        StatusString
    """
    # ------------------------------------------------------------
    # Detect JSON mode
    # ------------------------------------------------------------
    show_spec = show_spec.strip()
    is_json = show_spec.startswith("json(") and show_spec.endswith(")")

    if is_json:
        inner = show_spec[len("json("):-1].strip()
        cases = [x.strip() for x in inner.split(",") if x.strip()]
    else:
        cases = [x.strip() for x in show_spec.split(",") if x.strip()]

    # ------------------------------------------------------------
    # Prepare container
    # ------------------------------------------------------------
    parts = {} if is_json else []
    reason = ""

    # ------------------------------------------------------------
    # Helper: add item to dict or list
    # ------------------------------------------------------------
    def add_item(container, item, name="", json_mode=False):
        if json_mode:
            container[name] = item
        else:
            container.append(
                item
                if isinstance(item, str) else
                json.dumps(item, indent=2, ensure_ascii=False)
            )

    # ------------------------------------------------------------
    # Helper: parse result safely
    # ------------------------------------------------------------
    def parse_result():
        try:
            parsed = parse_textfsm_to_dicts(builder.template, sample)
            return parsed, None
        except Exception as exc:
            return None, str(exc)

    # ------------------------------------------------------------
    # If no cases → default to template
    # ------------------------------------------------------------
    if not cases:
        return StatusString(builder.template, status=True)

    # ------------------------------------------------------------
    # Process each case
    # ------------------------------------------------------------
    for case in cases:

        # snippet / template
        if case in ("snippet", "template"):
            content = getattr(builder, case, None)
            add_item(parts, content, name=case, json_mode=is_json)
            continue

        if case == "sample":
            add_item(parts, sample, name=case, json_mode=is_json)
            continue

        # parse result
        parsed, err = parse_result()

        if err:
            add_item(parts, err, name="result", json_mode=is_json)
            reason = "error"
            continue

        if not parsed:
            msg = "no record found after parsed sample with textfsm template"
            add_item(parts, msg, name="result", json_mode=is_json)
            reason = "warning"
            continue

        # default → stringified result
        if case == "default":
            add_item(parts, str(parsed), name="result", json_mode=is_json)
            continue

        # tabular
        if case == "tabular":
            from textfsmgen.libs.utils import get_data_as_tabular
            tabular_text = get_data_as_tabular(parsed)
            add_item(parts, tabular_text, name="result", json_mode=is_json)
            continue

        # raw result
        add_item(parts, parsed, name="result", json_mode=is_json)

    # ------------------------------------------------------------
    # Final output
    # ------------------------------------------------------------
    if is_json:
        content = json.dumps(parts, indent=2, ensure_ascii=False)
        return StatusString(
            content,
            status=(reason == ""),
            reason=reason or None,
        )

    # plain text
    content = "\n======\n".join(parts)
    return StatusString(
        content,
        status=(reason == ""),
        reason=reason or None,
    )
