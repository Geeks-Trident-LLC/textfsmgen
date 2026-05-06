"""
Golden test utilities using manifest.json for structured metadata.
"""

import json
import pathlib
import re

from textfsmgen import (
    TemplateBuilder,
    CategoryTemplateBuilder,
    TabularTemplateBuilder,
)


# ---------------------------------------------------------------------------
# Manifest loading
# ---------------------------------------------------------------------------

def load_manifest(case_dir: pathlib.Path) -> dict:
    """
    Load manifest.json for a golden test case.
    """
    manifest_path = case_dir / "manifest.json"
    return json.loads(manifest_path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Builder selection
# ---------------------------------------------------------------------------

def get_builder_type(manifest: dict):
    """
    Return the appropriate TemplateBuilder subclass based on manifest 'kind'.
    """
    kind = manifest.get("kind", "")
    if kind == "tabular":
        return TabularTemplateBuilder
    if kind == "category":
        return CategoryTemplateBuilder
    return TemplateBuilder


# ---------------------------------------------------------------------------
# Canonical loading
# ---------------------------------------------------------------------------

def load_canonical_from_manifest(case_dir: pathlib.Path, manifest: dict):
    c = manifest["canonical"]

    sample = (case_dir / c["sample"]).read_text(encoding="utf-8")
    snippet = (case_dir / c["snippet"]).read_text(encoding="utf-8")
    template = (case_dir / c["template"]).read_text(encoding="utf-8")

    result_path = case_dir / c["result"]
    raw = result_path.read_text(encoding="utf-8").strip()

    # Empty file → empty list
    result = json.loads(raw) if raw else []

    return sample, snippet, template, result


# ---------------------------------------------------------------------------
# Input/expected loading
# ---------------------------------------------------------------------------

def load_inputs_from_manifest(case_dir: pathlib.Path, manifest: dict):
    for entry in manifest.get("inputs", []):
        input_path = case_dir / entry["input"]
        expected_path = case_dir / entry["expected"]

        sample = input_path.read_text(encoding="utf-8")

        raw = expected_path.read_text(encoding="utf-8").strip()
        expected = json.loads(raw) if raw else []

        yield sample, expected

# ---------------------------------------------------------------------------
# Template normalization
# ---------------------------------------------------------------------------

def sync_datetime(curr: str, canonical: str) -> str:
    """
    Replace canonical template's created-date line with the generated one.
    """
    pattern = r"# Created date: \d{4}-\d{2}-\d{2}"

    generated = next((l for l in curr.splitlines() if re.match(pattern, l)), "")
    out = []

    for line in canonical.splitlines():
        if generated and re.match(pattern, line):
            out.append(generated)
            generated = ""
        else:
            out.append(line)

    return "\n".join(out)
