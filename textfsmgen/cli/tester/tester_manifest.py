# tester_manifest.py

from __future__ import annotations

import json
from typing import List, Any, Dict, Optional

from .tester_common import find_case_root, load_manifest

from .tester_paths import resolve_existing_case_path
from .tester_manifest_model import (
    Manifest,
    load_manifest,
    write_manifest,
    SUPPORTED_BUILDERS,
    CATEGORY_PARAM_FIELDS,
    TABULAR_PARAM_FIELDS,
)


# ------------------------------------------------------------
# Public API
# ------------------------------------------------------------

def handle_tester_manifest(argv):
    if not argv:
        print("error: missing case name")
        return 1

    case = argv[0]
    case_root = find_case_root(case)
    if not case_root:
        print(f"error: case not found: {case}")
        return 1

    manifest = load_manifest(case_root)

    print(json.dumps(manifest_to_dict(manifest), indent=2))
    return 0


def handle_tester_edit_manifest(argv: List[str]) -> int:
    """
    textfsmgen tester edit-manifest <case>

    Opens manifest.json in the user's $EDITOR.
    If $EDITOR is not set, prints the manifest to stdout.
    """
    if not argv:
        print("error: missing <case>")
        return 1

    case = argv[0]
    case_dir = resolve_existing_case_path(case)
    if case_dir is None:
        print(f"error: case not found: {case}")
        return 1

    manifest_path = case_dir / "manifest.json"

    editor = _get_editor()
    if editor:
        import subprocess
        subprocess.call([editor, str(manifest_path)])
        return 0

    # Fallback: print manifest
    print(manifest_path.read_text(encoding="utf-8"))
    return 0


def handle_tester_set(argv: List[str]) -> int:
    """
    textfsmgen tester set <case> <field> <value>

    Mutates manifest.json safely.

    Examples:
      textfsmgen tester set mycase builder tabular
      textfsmgen tester set mycase parameters.count 3
      textfsmgen tester set mycase meta.saved true
    """
    if len(argv) < 3:
        print("error: usage: tester set <case> <field> <value>")
        return 1

    case, field, raw_value = argv[0], argv[1], argv[2]

    case_dir = resolve_existing_case_path(case)
    if case_dir is None:
        print(f"error: case not found: {case}")
        return 1

    manifest = load_manifest(case_dir)

    if not _apply_field_update(manifest, field, raw_value):
        return 1

    write_manifest(case_dir, manifest)
    print(f"Updated {field} = {raw_value}")
    return 0


# ------------------------------------------------------------
# Internal helpers
# ------------------------------------------------------------

def _get_editor() -> Optional[str]:
    """
    Return $EDITOR if set.
    """
    import os
    return os.environ.get("EDITOR")


def _apply_field_update(manifest: Manifest, field: str, raw_value: str) -> bool:
    """
    Apply a field update to the manifest.
    Supports:
      builder
      parameters.<key>
      meta.<key>
    """
    if field == "builder":
        return _update_builder(manifest, raw_value)

    if field.startswith("parameters."):
        key = field.split(".", 1)[1]
        return _update_parameters(manifest, key, raw_value)

    if field.startswith("meta."):
        key = field.split(".", 1)[1]
        return _update_meta(manifest, key, raw_value)

    print(f"error: unknown field: {field}")
    return False


# ------------------------------------------------------------
# Builder update
# ------------------------------------------------------------

def _update_builder(manifest: Manifest, value: str) -> bool:
    if value not in SUPPORTED_BUILDERS:
        print(f"error: unsupported builder: {value}")
        return False

    manifest.builder = value
    manifest.parameters = _default_parameters_for(value)
    return True


# ------------------------------------------------------------
# Parameters update
# ------------------------------------------------------------

def _update_parameters(manifest: Manifest, key: str, raw_value: str) -> bool:
    builder = manifest.builder

    if builder == "category":
        if key not in CATEGORY_PARAM_FIELDS:
            print(f"error: unknown category parameter: {key}")
            return False

    if builder == "tabular":
        if key not in TABULAR_PARAM_FIELDS:
            print(f"error: unknown tabular parameter: {key}")
            return False

    value = _parse_value(raw_value)
    manifest.parameters[key] = value
    return True


# ------------------------------------------------------------
# Meta update
# ------------------------------------------------------------

def _update_meta(manifest: Manifest, key: str, raw_value: str) -> bool:
    if not hasattr(manifest.meta, key):
        print(f"error: unknown meta field: {key}")
        return False

    value = _parse_value(raw_value)
    setattr(manifest.meta, key, value)
    return True


# ------------------------------------------------------------
# Value parsing
# ------------------------------------------------------------

def _parse_value(raw: str) -> Any:
    """
    Parse a raw string into:
      - int
      - float
      - bool
      - null
      - list (JSON)
      - dict (JSON)
      - string (fallback)
    """
    # Try JSON
    try:
        return json.loads(raw)
    except Exception:   # noqa
        pass

    # Try bool
    if raw.lower() == "true":
        return True
    if raw.lower() == "false":
        return False

    # Try null
    if raw.lower() == "null":
        return None

    # Try int
    try:
        return int(raw)
    except ValueError:
        pass

    # Try float
    try:
        return float(raw)
    except ValueError:
        pass

    # Fallback: string
    return raw


# ------------------------------------------------------------
# Defaults (copied from manifest model)
# ------------------------------------------------------------

def _default_parameters_for(builder: str) -> Dict[str, Any]:
    if builder == "category":
        return {
            "user_data": "",
            "user_data_file": "",
            "count": 1,
            "separator": ":",
            "starting_from": None,
            "ending_at": None,
            "replacing_rules": None,
        }

    if builder == "tabular":
        return {
            "user_data": "",
            "user_data_file": "",
            "column_divider": "",
            "column_count": 0,
            "column_widths": None,
            "headers": None,
            "header_rows": None,
            "custom_header_text": "",
            "starting_from": None,
            "ending_at": None,
            "has_header_row": True,
            "replacing_rules": None,
        }

    raise ValueError(f"Unsupported builder: {builder}")


def manifest_to_dict(manifest: Manifest) -> dict:
    return {
        "builder": manifest.builder,
        "parameters": manifest.parameters,
        "meta": manifest.meta.__dict__,
    }
