from dataclasses import dataclass, field
import copy

import pathlib

from .config_cmd import CONFIG_TYPES

from textfsmgen.libs.generic import StatusString
from textfsmgen.libs.generic import DotDict
from textfsmgen.libs.shell import execute_command
from textfsmgen.libs.common import emit_status


DEFAULT_VALUES = {
    "sample_file": None,
    "command": "",
    "debug": False,
    "show": "",
    "save": "",
    "create_config": False,
    "create_config_file": None,
    "create_golden_test": False,
    "create_golden_test_path": None,
    "json_mode": False,
    "count": 1,
    "separator": ":",
    "column_divider": "",
    "column_count": 0,
    "column_widths": "",
    "headers": None,
    "header_rows": None,
    "custom_header_text": "",
    "starting_from": None,
    "ending_at": None,
    "has_header_row": None,
    "replacing_rules": None,
}


@dataclass
class PreparedParams:
    options: DotDict = field(default_factory=DotDict)
    status: str = ""
    message: str = ""
    exit_code: int = 0

    def __bool__(self):
        return self.exit_code == 0

    def to_json(self):
        return {
            "options": self.options,
            "status": self.status,
            "message": self.message,
            "exit_code": self.exit_code,
        }


def merge(builder_name, cli_options, loaded_config):
    base = copy.deepcopy(CONFIG_TYPES.get(builder_name, {}))
    defaults = DEFAULT_VALUES  # move your defaults into a constant

    merged = {}

    # Helper: pick value with your rules
    def pick(cli_val_, cfg_val_, default_val_):
        # Treat empty string or None as missing
        if cli_val_ not in ("", None):
            return cli_val_
        if cfg_val_ not in ("", None):
            return cfg_val_
        return default_val_

    # --- merge top-level keys ---
    for key in base:
        if key in ("params", "builder"):
            merged[key] = base[key]
            continue

        cli_val = cli_options.get(key)
        cfg_val = loaded_config.get(key) if loaded_config else None
        default_val = defaults.get(key)

        merged[key] = pick(cli_val, cfg_val, default_val)

    # --- merge params ---
    merged["params"] = {}
    cfg_params = loaded_config.get("params", {}) if loaded_config else {}
    base_params = base.get("params", {})

    for key in base_params:
        cli_val = cli_options.get(key)
        cfg_val = cfg_params.get(key)
        default_val = defaults.get(key)

        merged["params"][key] = pick(cli_val, cfg_val, default_val)

    merged["config"] = cli_options["config"]

    return DotDict(merged)


def validate_required_params(merged_options):
    merged_options.snippet_data = ""
    merged_options.sample_data = ""

    # -------------------------------
    # FREEFORM BUILDER
    # -------------------------------
    if merged_options.builder == "freeform":
        # Require snippet OR snippet_file
        if not merged_options.snippet and not merged_options.snippet_file:
            return StatusString(
                "freeform builder needs inline snippet or snippet from snippet_file",
                status=False,
                reason="error",
            )

        # Load snippet from file if needed
        content = ""
        if not merged_options.snippet and merged_options.snippet_file:
            try:
                path = pathlib.Path(merged_options.snippet_file)
                content = path.read_text()
                if not content.strip():
                    return StatusString(
                        f"{str(path)!r} has no content.",
                        status=False,
                        reason="error",
                    )
            except Exception as ex:
                return StatusString(
                    f"{type(ex).__name__}: {ex}",
                    status=False,
                    reason="code-error",
                )

        merged_options.snippet_data = merged_options.snippet or content

        # Try sample_file first
        if merged_options.sample_file:
            try:
                path = pathlib.Path(merged_options.sample_file)
                content = path.read_text()
                if content.strip():
                    merged_options.sample_data = content
                    return StatusString(status=True)
            except Exception as ex:
                return StatusString(
                    f"{type(ex).__name__}: {ex}",
                    status=False,
                    reason="code-error",
                )

        # Fallback to command
        result = execute_command(merged_options.command)
        if result.exit_code != 0:
            return StatusString(
                result.output,
                status=False,
                reason="error",
            )

        merged_options.sample_data = result.output
        return StatusString(status=True)

    # -------------------------------
    # NON-FREEFORM BUILDER
    # -------------------------------

    # Require sample_file OR command
    if not merged_options.sample_file and not merged_options.command:
        return StatusString(
            f"{merged_options.builder} builder needs sample or sample from command",
            status=False,
            reason="error",
        )

    # Try sample_file first
    if merged_options.sample_file:
        try:
            path = pathlib.Path(merged_options.sample_file)
            content = path.read_text()
            if content.strip():
                merged_options.sample_data = content
                return StatusString(status=True)
        except Exception as ex:
            return StatusString(
                f"{type(ex).__name__}: {ex}",
                status=False,
                reason="code-error",
            )

    # Fallback to command
    result = execute_command(merged_options.command)
    if result.exit_code != 0:
        return StatusString(
            result.output,
            status=False,
            reason="error",
        )

    merged_options.sample_data = result.output
    return StatusString(status=True)


def prepare_params(builder_name, cli_options, loaded_config):
    merged_options = merge(builder_name, cli_options, loaded_config)
    validated = validate_required_params(merged_options)

    # Determine status
    if validated:
        status = "ok"
    else:
        status = validated.reason  # "error" or "code-error"

    # Determine exit code
    if validated:
        exit_code = 0
    elif validated.reason == "code-error":
        exit_code = 2
    else:
        exit_code = 1

    return PreparedParams(
        options=merged_options,
        status=status,
        message=emit_status(validated, display=False),
        exit_code=exit_code,
    )
