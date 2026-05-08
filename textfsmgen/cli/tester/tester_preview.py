# tester_preview.py

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

from .tester_paths import resolve_existing_case_path
from .tester_manifest_model import Manifest
from .tester_quicktest import _run_builder


# ------------------------------------------------------------
# Public API
# ------------------------------------------------------------

def handle_tester_preview(argv: List[str]) -> int:
    """
    Handles:
      textfsmgen tester preview-template <case>
      textfsmgen tester preview-snippet <case>
      textfsmgen tester preview-generated-template <case>
      textfsmgen tester preview-results <case>

    The dispatcher in cli_tester.py routes all preview-* commands here.
    """
    if len(argv) < 2:
        print("error: usage: tester preview-<type> <case>")
        return 1

    preview_type = argv[0]
    case = argv[1]

    case_dir = resolve_existing_case_path(case)
    if case_dir is None:
        print(f"error: case not found: {case}")
        return 1

    if preview_type == "preview-template":
        return _preview_template(case_dir)

    if preview_type == "preview-snippet":
        return _preview_snippet(case_dir)

    if preview_type == "preview-generated-template":
        return _preview_generated_template(case_dir)

    if preview_type == "preview-results":
        return _preview_results(case_dir)

    print(f"error: unknown preview type: {preview_type}")
    return 1


# ------------------------------------------------------------
# Preview handlers
# ------------------------------------------------------------

def _preview_template(case_dir: Path) -> int:
    """
    Show authoritative template:
      - main category → canonical/textfsm.template
      - non-main → expected/textfsm.template
    """
    path = _resolve_authoritative_file(case_dir, "textfsm.template")
    if path is None:
        print("error: template not found")
        return 1

    print(path.read_text(encoding="utf-8"))
    return 0


def _preview_snippet(case_dir: Path) -> int:
    """
    Show authoritative snippet:
      - main category → canonical/snippet.txt
      - non-main → expected/snippet.txt
    """
    path = _resolve_authoritative_file(case_dir, "snippet.txt")
    if path is None:
        print("error: snippet not found")
        return 1

    print(path.read_text(encoding="utf-8"))
    return 0


def _preview_generated_template(case_dir: Path) -> int:
    """
    Run builder and show generated template.
    The builder must return a dict containing "generated_template".
    """
    manifest = _load_manifest(case_dir)
    inputs = _load_inputs(case_dir)

    result = _run_builder(manifest, inputs)

    # Expect builder to return a dict with "generated_template"
    if not result or not isinstance(result, list):
        print("error: builder returned invalid result")
        return 1

    first = result[0]
    template = first.get("generated_template")
    if not template:
        print("error: builder did not produce generated_template")
        return 1

    print(template)
    return 0


def _preview_results(case_dir: Path) -> int:
    """
    Show expected_results/result.json.
    """
    path = case_dir / "expected_results" / "result.json"
    if not path.is_file():
        print("error: expected_results/result.json not found")
        return 1

    data = json.loads(path.read_text(encoding="utf-8"))
    print(json.dumps(data, indent=2))
    return 0


# ------------------------------------------------------------
# Internal helpers
# ------------------------------------------------------------

def _load_manifest(case_dir: Path) -> Manifest:
    from .tester_manifest_model import load_manifest
    return load_manifest(case_dir)


def _load_inputs(case_dir: Path) -> List[str]:
    inputs_dir = case_dir / "inputs"
    if not inputs_dir.is_dir():
        return []

    texts: List[str] = []
    for file in sorted(inputs_dir.iterdir()):
        if file.is_file():
            texts.append(file.read_text(encoding="utf-8"))
    return texts


def _resolve_authoritative_file(case_dir: Path, filename: str) -> Optional[Path]:
    """
    Return authoritative file path depending on category:
      - main → canonical/<filename>
      - non-main → expected/<filename>
    """
    category = case_dir.parent.name

    if category == "main":
        path = case_dir / "canonical" / filename
    else:
        path = case_dir / "expected" / filename

    return path if path.is_file() else None
