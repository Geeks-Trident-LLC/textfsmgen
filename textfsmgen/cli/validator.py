import json
import click
from textfsmgen.libs.generic import StatusString


# ------------------------------------------------------------
# Declarative builder rules
# ------------------------------------------------------------

REQUIRED_TOP_KEYS = {
    "freeform": [
        "builder",
        "params",
        "snippet",
        "snippet_file",
        "show",
        "save",
        "create_config",
        "create_config_file",
        "create_golden",
        "create_golden_path",
        "json_mode",
    ],
    "category": [
        "builder",
        "params",
        "sample_file",
        "command",
        "show",
        "save",
        "create_config",
        "create_config_file",
        "create_golden",
        "create_golden_path",
        "json_mode",
    ],
    "tabular": [
        "builder",
        "params",
        "sample_file",
        "command",
        "show",
        "save",
        "create_config",
        "create_config_file",
        "create_golden",
        "create_golden_path",
        "json_mode",
    ],
}

REQUIRED_PARAM_KEYS = {
    "freeform": [],
    "category": ["count", "separator", "starting_from", "ending_at", "replacing_rules"],
    "tabular": [
        "column_divider",
        "column_count",
        "column_widths",
        "headers",
        "header_rows",
        "custom_header_text",
        "has_header_row",
        "starting_from",
        "ending_at",
        "replacing_rules",
    ],
}


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------


def _load_json(config_path):
    try:
        raw = click.open_file(config_path).read()
        return json.loads(raw), None
    except Exception as exc:
        return None, StatusString(
            f"Failed to load config JSON: {exc}",
            status=False,
            reason="code-error",
        )


def _validate_builder(data, config_path):
    if not isinstance(data, dict):
        return StatusString(
            f"{str(config_path)} must be a dictionary-JSON format.",
            status=False,
            reason="error",
        )

    if "builder" not in data:
        return StatusString(
            f"{str(config_path)} does not have 'builder' key",
            status=False,
            reason="error",
        )

    builder = str(data["builder"]).lower()
    if builder not in REQUIRED_TOP_KEYS:
        return StatusString(
            f"Expected builder must be freeform | category | tabular, "
            f"but received {builder!r}",
            status=False,
            reason="error",
        )

    return StatusString(builder, status=True)


def _validate_required_keys(data, builder):
    required = REQUIRED_TOP_KEYS[builder]
    missing = [k for k in required if k not in data]

    if missing:
        return StatusString(
            f"Missing required key(s): {', '.join(missing)}\n"
            f"Required: {', '.join(required)}",
            status=False,
            reason="error",
        )
    return StatusString("", status=True)


def _validate_params(data, builder):
    params = data.get("params")
    if not isinstance(params, dict):
        return StatusString(
            "Config 'params' must be a dictionary",
            status=False,
            reason="error",
        )

    required = REQUIRED_PARAM_KEYS[builder]
    missing = [k for k in required if k not in params]

    if missing:
        return StatusString(
            f"Missing required params: {', '.join(missing)}\n"
            f"Required: {', '.join(required)}",
            status=False,
            reason="warning",
        )
    return StatusString("", status=True)


def _validate_snippet_rules(data, builder):
    if builder == "freeform":
        if not data.get("snippet") and not data.get("snippet_file"):
            return StatusString(
                "'snippet' and 'snippet_file' are both empty; one of them must be provided.",
                status=False,
                reason="warning",
            )
    else:
        if not data.get("sample_file") and not data.get("command"):
            return StatusString(
                "'sample_file' and 'command' are both empty; one of them must be provided.",
                status=False,
                reason="warning",
            )
    return StatusString("", status=True)


# ------------------------------------------------------------
# Main validator
# ------------------------------------------------------------


def validate_config(config_path):
    data, err = _load_json(config_path)
    if err:
        return err

    builder = _validate_builder(data, config_path)
    if not builder:
        return builder

    builder_name = str(builder)
    err = _validate_required_keys(data, builder_name)
    if err:
        return err

    err = _validate_params(data, builder_name)
    if err:
        return err

    err = _validate_snippet_rules(data, builder_name)
    if err:
        return err

    return StatusString(data, status=True)
