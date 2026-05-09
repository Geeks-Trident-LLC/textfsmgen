# tester_quicktest.py

from __future__ import annotations

import os
import json
import hashlib
from pathlib import Path
from typing import Any, Dict, List

from .tester_manifest_model import Manifest


# ------------------------------------------------------------
# Public API
# ------------------------------------------------------------

def run_quick_test_for_case(case_dir: Path) -> None:
    """
    Run a minimal builder pipeline to generate:
      - expected_results/
      - meta.json
      - golden.hash

    This is used by:
      - create
      - copy
      - duplicate

    The goal is NOT to run pytest, but to ensure the case is
    structurally valid and has fresh derived artifacts.
    """
    manifest = _load_manifest(case_dir)
    inputs = _load_inputs(case_dir)

    results = _run_builder(manifest, inputs)

    _write_expected_results(case_dir, results)
    _write_meta_json(case_dir, manifest, results)
    _write_golden_hash(case_dir)


# ------------------------------------------------------------
# Internal helpers
# ------------------------------------------------------------

def _load_manifest(case_dir: Path) -> Manifest:
    from .tester_manifest_model import load_manifest
    return load_manifest(case_dir)


def _load_inputs(case_dir: Path) -> List[str]:
    """
    Load all input files under inputs/ as raw text.
    Returns a list of strings.
    """
    inputs_dir = case_dir / "inputs"
    if not inputs_dir.is_dir():
        return []

    texts: List[str] = []
    for file in sorted(inputs_dir.iterdir()):
        if file.is_file():
            texts.append(file.read_text(encoding="utf-8"))
    return texts


def _run_builder(manifest: Manifest, inputs: List[str]) -> List[Dict[str, Any]]:
    """
    Execute the real builder engine.

    Returns a list of dicts, each representing a parsed row.
    Also includes generated artifacts in the first element:
        {
            "generated_template": "...",
            "generated_snippet": "...",
            "rows": [...]
        }

    This unified structure allows:
      - preview-generated-template
      - preview-snippet
      - diff-template
      - diff-snippet
      - run
      - quicktest
    """
    builder = _instantiate_builder(manifest)

    # Build artifacts
    generated_template = builder.template
    generated_snippet = builder.snippet

    # Parse inputs
    rows = []
    for text in inputs:
        rows.extend(builder.parse(text))

    # Unified return format
    return [{
        "generated_template": generated_template,
        "generated_snippet": generated_snippet,
        "rows": rows,
    }]


def _write_expected_results(case_dir: Path, results: List[Dict[str, Any]]) -> None:
    """
    Write expected_results/result.json.
    """
    out_dir = case_dir / "expected_results"
    out_dir.mkdir(parents=True, exist_ok=True)

    out_path = out_dir / "result.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
        f.write("\n")


def _write_meta_json(case_dir: Path, manifest: Manifest, results: List[Dict[str, Any]]) -> None:
    """
    Write meta.json with minimal metadata.
    """
    meta_path = case_dir / "meta.json"

    meta = {
        "builder": manifest.builder,
        "category": manifest.category,
        "result_count": len(results),
        "schema_version": manifest.meta.schema_version,
    }

    with meta_path.open("w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
        f.write("\n")


def _write_golden_hash(case_dir: Path) -> None:
    """
    Compute a stable hash of all authoritative + derived files.
    This ensures drift detection works correctly.
    """
    hash_path = case_dir / "golden.hash"

    files_to_hash = _collect_files_for_hash(case_dir)
    digest = _compute_hash(files_to_hash)

    hash_path.write_text(digest + "\n", encoding="utf-8")


def _collect_files_for_hash(case_dir: Path) -> List[Path]:
    """
    Collect all files that should be included in golden.hash.
    Excludes:
      - golden.hash itself
      - meta.json (optional, but usually included)
    """
    collected: List[Path] = []

    for root, _, files in os.walk(case_dir):
        for name in files:
            path = Path(root) / name
            if path.name == "golden.hash":
                continue
            collected.append(path)

    return sorted(collected)


def _compute_hash(files: List[Path]) -> str:
    """
    Compute SHA256 hash of all file contents in sorted order.
    """
    h = hashlib.sha256()

    for file in files:
        data = file.read_bytes()
        h.update(data)

    return h.hexdigest()


def _instantiate_builder(manifest: Manifest):
    """
    Create the correct builder instance based on manifest.builder.
    """
    from textfsmgen import (
        CategoryTemplateBuilder,
        TabularTemplateBuilder,
    )

    params = manifest.parameters

    if manifest.builder == "category":
        return CategoryTemplateBuilder(**params)

    if manifest.builder == "tabular":
        return TabularTemplateBuilder(**params)

    raise ValueError(f"Unsupported builder: {manifest.builder}")
