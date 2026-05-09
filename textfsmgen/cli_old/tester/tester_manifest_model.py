# tester_manifest_model.py

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict


# ------------------------------------------------------------
# Public API
# ------------------------------------------------------------

SUPPORTED_SCHEMA_VERSION = "1.0"
SUPPORTED_BUILDERS = {"category", "tabular"}


@dataclass
class ManifestMeta:
    saved: bool
    author: str
    email: str
    description: str
    notes: str
    schema_version: str = SUPPORTED_SCHEMA_VERSION


@dataclass
class Manifest:
    builder: str
    parameters: Dict[str, Any]
    meta: ManifestMeta
    category: str  # inferred from directory structure, but stored here for convenience

    # --------------------------------------------------------
    # Factory methods
    # --------------------------------------------------------

    @staticmethod
    def from_flags(
        builder: str,
        category: str,
        author: str = "",
        email: str = "",
        saved: bool = False,
    ) -> "Manifest":
        return Manifest(
            builder=builder,
            parameters=_default_parameters_for(builder),
            meta=ManifestMeta(
                saved=saved,
                author=author,
                email=email,
                description="",
                notes="",
            ),
            category=category,
        )

    @staticmethod
    def from_json(data: Dict[str, Any], category: str) -> "Manifest":
        _validate_manifest_top_level(data)

        builder = data["builder"]
        parameters = data["parameters"]
        meta = _parse_meta(data["meta"])

        _validate_builder(builder)
        _validate_parameters(builder, parameters)
        _validate_meta(meta)

        return Manifest(
            builder=builder,
            parameters=parameters,
            meta=meta,
            category=category,
        )

    # --------------------------------------------------------
    # Serialization
    # --------------------------------------------------------

    def to_json(self) -> Dict[str, Any]:
        return {
            "builder": self.builder,
            "parameters": self.parameters,
            "meta": {
                "saved": self.meta.saved,
                "author": self.meta.author,
                "email": self.meta.email,
                "description": self.meta.description,
                "notes": self.meta.notes,
                "schema_version": self.meta.schema_version,
            },
        }


# ------------------------------------------------------------
# Load / Save
# ------------------------------------------------------------

def load_manifest(case_dir: Path) -> Manifest:
    manifest_path = case_dir / "manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"manifest.json not found in {case_dir}")

    with manifest_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    category = case_dir.parent.name  # tests/golden/<category>/<case>
    return Manifest.from_json(data, category)


def load_manifest_config(config_file: str) -> Manifest:
    path = Path(config_file)
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if "category" not in data:
        raise ValueError("Config file must include 'category' field")

    category = data["category"]
    return Manifest.from_json(data, category)


def write_manifest(case_dir: Path, manifest: Manifest) -> None:
    manifest_path = case_dir / "manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    with manifest_path.open("w", encoding="utf-8") as f:
        json.dump(manifest.to_json(), f, indent=2)
        f.write("\n")


# ------------------------------------------------------------
# Validation
# ------------------------------------------------------------

def _validate_manifest_top_level(data: Dict[str, Any]) -> None:
    required = {"builder", "parameters", "meta"}
    if not required.issubset(data):
        missing = required - data.keys()
        raise ValueError(f"Manifest missing required fields: {missing}")


def _validate_builder(builder: str) -> None:
    if builder not in SUPPORTED_BUILDERS:
        raise ValueError(f"Unsupported builder: {builder}")


def _validate_parameters(builder: str, params: Dict[str, Any]) -> None:
    if builder == "category":
        _validate_category_params(params)
    elif builder == "tabular":
        _validate_tabular_params(params)


def _validate_meta(meta: ManifestMeta) -> None:
    if meta.schema_version != SUPPORTED_SCHEMA_VERSION:
        raise ValueError(
            f"Unsupported schema_version: {meta.schema_version}. "
            f"Expected: {SUPPORTED_SCHEMA_VERSION}"
        )


# ------------------------------------------------------------
# Builder-specific parameter validation
# ------------------------------------------------------------

CATEGORY_PARAM_FIELDS = {
    "user_data",
    "user_data_file",
    "count",
    "separator",
    "starting_from",
    "ending_at",
    "replacing_rules",
}

TABULAR_PARAM_FIELDS = {
    "user_data",
    "user_data_file",
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
}


def _validate_category_params(params: Dict[str, Any]) -> None:
    unknown = set(params.keys()) - CATEGORY_PARAM_FIELDS
    if unknown:
        raise ValueError(f"Unknown category parameters: {unknown}")


def _validate_tabular_params(params: Dict[str, Any]) -> None:
    unknown = set(params.keys()) - TABULAR_PARAM_FIELDS
    if unknown:
        raise ValueError(f"Unknown tabular parameters: {unknown}")


# ------------------------------------------------------------
# Defaults
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


# ------------------------------------------------------------
# Meta parsing
# ------------------------------------------------------------

def _parse_meta(data: Dict[str, Any]) -> ManifestMeta:
    required = {
        "saved",
        "author",
        "email",
        "description",
        "notes",
        "schema_version",
    }
    if not required.issubset(data):
        missing = required - data.keys()
        raise ValueError(f"Manifest meta missing fields: {missing}")

    return ManifestMeta(
        saved=bool(data["saved"]),
        author=str(data["author"]),
        email=str(data["email"]),
        description=str(data["description"]),
        notes=str(data["notes"]),
        schema_version=str(data["schema_version"]),
    )
