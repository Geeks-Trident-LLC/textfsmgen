# textfsmgen/cli/config_cmd.py

import json
from pathlib import Path
import click
import copy

from textfsmgen.libs.generic import StatusString
from textfsmgen.libs.common import emit_status
from textfsmgen.libs.text import normalize_text_values
from textwrap import indent


# ------------------------------------------------------------
# Register with main CLI
# ------------------------------------------------------------
def register(cli):
    cli.add_command(config)


# ------------------------------------------------------------
# Config templates
# ------------------------------------------------------------
FREEFORM_TEMPLATE = {
    "builder": "freeform",
    "params": {},
    "snippet": "",
    "snippet_file": "",
    "sample_file": "",
    "command": "",
    "show": "",
    "save": "",
}

CATEGORY_TEMPLATE = {
    "builder": "category",
    "params": {
        "count": 1,
        "separator": ":",
        "starting_from": None,
        "ending_at": None,
        "replacing_rules": None,
    },
    "sample_file": "",
    "command": "",
    "show": "",
    "save": "",
}

TABULAR_TEMPLATE = {
    "builder": "tabular",
    "params": {
        "column_divider": "",
        "column_count": 0,
        "column_widths": "",
        "headers": None,
        "header_rows": None,
        "custom_header_text": "",
        "starting_from": None,
        "ending_at": None,
        "has_header_row": True,
        "replacing_rules": None,
    },
    "sample_file": "",
    "command": "",
    "show": "",
    "save": "",
}

CONFIG_TYPES = {
    "category": CATEGORY_TEMPLATE,
    "tabular": TABULAR_TEMPLATE,
    "freeform": FREEFORM_TEMPLATE,
}

TOP_LEVEL_DOCS_MAPPING = {
    "builder": "category | tabular | freeform",
    "params": """
        Parameter/value pairs that control how the __PLACEHOLDER__ builder
        parses __PLACEHOLDER__‑like text.
    """,
    "snippet": """
        Inline snippet text used as the source text for __PLACEHOLDER__ builder.
        """,
    "snippet_file": """
        Path to a snippet text whose contents serve as the source input 
        for __PLACEHOLDER__ builder.""",
    "sample_file": """
        Path to a sample input file used as the source text for the
        __PLACEHOLDER__ builder.
    """,
    "command": """
        Shell command used to generate sample text dynamically.
        If provided, its output is used instead of sample_file.
    """,
    "show": """
        Selects which output to display on the console.

        Formats:
          <kind>
          <kind1>,...,<kindK>

        Kinds:
          sample, snippet, template, result

        Examples:
          result
              Display the parsed result.

          template, result
              Display both the generated template and the parsed result.

    """,
    "save": """
        Selects which output to write to file(s) or to simulate in dry‑run mode.
        
        Formats:
          <kind>-<filename>
          <kind1>-<filename1>,...,<kindK>-<filenameK>
          dryrun(<kind>-<filename>)
          dryrun(<kind1>-<filename1>,...,<kindK>-<filenameK>)
        
        Kinds:
          sample, snippet, template, result
        
        Examples:
          template-b.textfsm, result-out.json
              Write the generated template to b.textfsm and the parsed result to out.json.
        
          dryrun(result-out.json)
              Show a dry‑run message describing how the result would be saved to out.json.

    """,
}
normalize_text_values(TOP_LEVEL_DOCS_MAPPING)

PARAMS_DOCS_MAPPING = {
    "count": """
        Number of category key/value pairs to extract.
        Higher values improve extraction accuracy.
        Default is 1.
    """,
    "separator": """
        Separator between key and value fields.
        Default is ":".
    """,
    "column_divider": """
        Character or string that separates columns in the raw text.
        The tabular builder uses this divider to determine where one
        column ends and the next begins.
        Default is an empty string.
    """,
    "column_count": """
        Number of columns expected in the table.
        Default is 0.
    """,
    "column_widths": """
        Comma‑separated list of expected column widths used for parsing
        fixed‑width or mixed‑width tables.
        Format: <width1>,<width2>,...,<widthN>.
        Default is None.
    """,
    "headers": """
        Comma‑separated list of header names.
        Useful for headerless tables so the generated template can
        produce structured results with explicit field names.
        Default is None.
    """,
    "header_rows": """
        One or more consecutive rows that define header lines when the
        builder cannot automatically infer correct headers.
        Default is None.
    """,
    "custom_header_text": """
        Manually defined header‑separator line used to determine column
        boundaries in headerless tabular text. This is helpful when the
        builder cannot infer column structure automatically.
        Users should inspect the sample text and create an appropriate
        separator line (e.g., "---------- --------- --------------- -----").
        Default is None.
    """,
    "has_header_row": """
        Indicates whether the tabular text contains a header row.
        Set to True for headered tables; set to False for headerless tables.
        Default is True.
    """,
    "starting_from": """
        Specifies where tabular parsing should begin when the text contains
        a mix of non‑tabular and tabular sections. Accepts either a line
        number or a lookup string marking the first row of the table.
        Default is None.
    """,
    "ending_at": """
        Specifies where tabular parsing should end when the text contains
        a mix of non‑tabular and tabular sections. Accepts either a line
        number or a lookup string marking the last row of the table.
        Default is None.
    """,
    "replacing_rules": """
        Post‑processing replacement rules applied to the generated snippet,
        allowing users to customize the final template.
        Format: [(old, new), ...].
        Default is None.
    """,
}
normalize_text_values(PARAMS_DOCS_MAPPING)


# ------------------------------------------------------------
# Main command group
# ------------------------------------------------------------
@click.group(
    help="Manage TextFSMGen config templates.",
    context_settings=dict(help_option_names=["-h", "--help"]),
)
def config():
    pass


# ------------------------------------------------------------
# config create <type> [--output FILE]
# ------------------------------------------------------------
@config.command(
    name="create", help="Create a config template for a given builder type."
)
@click.argument(
    "config_type", type=click.Choice(CONFIG_TYPES.keys(), case_sensitive=False)
)
@click.option(
    "--output",
    "-o",
    default=None,
    type=click.Path(),
    help="Write config template to a file instead of stdout.",
)
def create_config(config_type, output):
    config_type = config_type.lower()
    template = CONFIG_TYPES[config_type]
    content = json.dumps(template, indent=2, ensure_ascii=False)

    if output:
        try:
            Path(output).write_text(content, encoding="utf-8")
            emit_status(
                StatusString(f"Config template written to {output}", status=True)
            )
            return 0
        except Exception as exc:
            emit_status(
                StatusString(
                    f"Failed to write config file: {exc}", status=False, reason="error"
                )
            )
            raise SystemExit(1)

    click.echo(content)
    return 0


# ------------------------------------------------------------
# config validate <file>
# ------------------------------------------------------------
@config.command(
    name="validate",
    help="Validate a config JSON file for category or tabular builders.",
)
@click.argument("file", type=click.Path(exists=True))
def validate_config_cmd(file):
    # Load JSON
    try:
        raw = json.loads(Path(file).read_text(encoding="utf-8"))
    except Exception as exc:
        emit_status(
            StatusString(f"Failed to load JSON: {exc}", status=False, reason="error")
        )

        raise SystemExit(1)

    # Detect config type by matching keys
    detected_type = None
    for name, template in CONFIG_TYPES.items():
        if set(template["params"].keys()) == set(raw.get("params", {}).keys()):
            detected_type = name
            break

    if not detected_type:
        emit_status(
            StatusString(
                "Unable to detect config type. "
                "Ensure 'params' keys match either category or tabular template.",
                status=False,
                reason="error",
            )
        )
        raise SystemExit(1)

    template = CONFIG_TYPES[detected_type]

    # Validate top-level keys
    errors = []

    for key in template.keys():
        if key not in raw:
            errors.append(f"Missing top-level key: {key}")

    # Validate params keys
    raw_params = raw.get("params", {})
    tmpl_params = template["params"]

    for key in tmpl_params.keys():
        if key not in raw_params:
            errors.append(f"Missing params key: params.{key}")

    # Validate types (simple type check)
    for key, default in tmpl_params.items():
        if key in raw_params:
            if default is not None and raw_params[key] is not None:
                if type(raw_params[key]) is not type(default):
                    errors.append(
                        f"Invalid type for params.{key}: "
                        f"expected {type(default).__name__}, "
                        f"got {type(raw_params[key]).__name__}"
                    )

    # Report errors
    if errors:
        emit_status(
            StatusString(
                "Config validation failed:\n" + "\n".join(f"- {e}" for e in errors),
                status=False,
                reason="error",
            )
        )
        raise SystemExit(1)

    # Success
    emit_status(
        StatusString(f"Config file '{file}' is valid ({detected_type}).", status=True)
    )
    return 0


@config.command(name="list", help="List all available config types.")
def list_configs():
    click.echo("Available config types:")
    for name in CONFIG_TYPES.keys():
        click.echo(f"  - {name}")


@config.command(
    name="explain", help="Explain the structure and fields of a config type."
)
@click.argument(
    "config_type", type=click.Choice(CONFIG_TYPES.keys(), case_sensitive=False)
)
def explain_config(config_type):
    config_type = config_type.lower()
    template = CONFIG_TYPES[config_type]

    click.echo(f"Config type: {config_type}")

    # ------------------------------------------------------------
    # Top-level keys
    # ------------------------------------------------------------

    click.echo("\nTop-level keys:")
    for key in template.keys():
        click.echo(f"\n  - {key}")
        doc = TOP_LEVEL_DOCS_MAPPING[key].replace("__PLACEHOLDER__", config_type)
        if doc:
            click.echo(indent(doc, prefix=" " * 6))

    # ------------------------------------------------------------
    # Params section
    # ------------------------------------------------------------
    click.echo("\n\nparams:")

    # These params are always treated as strings in CLI usage
    force_str = {
        "starting_from",
        "ending_at",
        "replacing_rules",
        "column_widths",
        "headers",
        "header_rows",
    }

    for key, default in template["params"].items():
        # Determine type name
        typename = "str" if key in force_str else type(default).__name__
        default_repr = f'"{default}"' if isinstance(default, str) else default
        click.echo(f"\n  - {key:<21} (type: {typename}, default: {default_repr})")
        txt = PARAMS_DOCS_MAPPING.get(key, "")
        if txt:
            click.echo(indent(txt, prefix=" " * 6))

    # ------------------------------------------------------------
    # Description
    # ------------------------------------------------------------
    click.echo("\n\nDescription:")

    if config_type == "category":
        click.echo("  Category builder config controls key/value extraction from text.")
        click.echo(
            "  Use 'params' to define separators, ranges, and replacement rules."
        )

    elif config_type == "tabular":
        click.echo(
            "  Tabular builder config controls column parsing for table-like text."
        )
        click.echo(
            "  Use 'params' to define column structure, headers, and parsing rules."
        )


def get_config_template(name):
    name = str(name).lower()
    if name not in CONFIG_TYPES:
        raise SystemExit(f"Config type '{name}' not supported.")
    return copy.deepcopy(CONFIG_TYPES[name])
