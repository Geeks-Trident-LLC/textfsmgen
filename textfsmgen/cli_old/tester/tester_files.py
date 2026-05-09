# tester_files.py

from __future__ import annotations

import shutil
from pathlib import Path


# ------------------------------------------------------------
# Public API
# ------------------------------------------------------------

def create_main_case_files(case_dir: Path) -> None:
    """
    Create directory structure for a 'main' category case.
    Authoritative directory: canonical/
    Derived directories: expected_results/, inputs/
    """
    canonical = case_dir / "canonical"
    inputs = case_dir / "inputs"
    expected_results = case_dir / "expected_results"

    canonical.mkdir(parents=True, exist_ok=True)
    inputs.mkdir(parents=True, exist_ok=True)
    expected_results.mkdir(parents=True, exist_ok=True)

    _touch_empty(canonical / "result.json")
    _touch_empty(canonical / "sample.txt")
    _touch_empty(canonical / "snippet.txt")
    _touch_empty(canonical / "textfsm.template")

    _create_readme(case_dir)


def create_non_main_case_files(case_dir: Path) -> None:
    """
    Create directory structure for a non-main category case.
    Authoritative directory: expected/
    Derived directories: expected_results/, inputs/
    """
    expected = case_dir / "expected"
    inputs = case_dir / "inputs"
    expected_results = case_dir / "expected_results"

    expected.mkdir(parents=True, exist_ok=True)
    inputs.mkdir(parents=True, exist_ok=True)
    expected_results.mkdir(parents=True, exist_ok=True)

    _touch_empty(expected / "snippet.txt")
    _touch_empty(expected / "textfsm.template")

    _create_readme(case_dir)


def copy_main_authoritative_files(src: Path, dst: Path) -> None:
    """
    Copy authoritative files for a main category case:
    canonical/ + inputs/
    Do NOT copy expected_results/, golden.hash, meta.json.
    """
    canonical_src = src / "canonical"
    inputs_src = src / "inputs"

    canonical_dst = dst / "canonical"
    inputs_dst = dst / "inputs"

    canonical_dst.mkdir(parents=True, exist_ok=True)
    inputs_dst.mkdir(parents=True, exist_ok=True)

    _copy_tree(canonical_src, canonical_dst)
    _copy_tree(inputs_src, inputs_dst)

    _create_readme(dst)


def copy_non_main_authoritative_files(src: Path, dst: Path) -> None:
    """
    Copy authoritative files for a non-main category case:
    expected/ + inputs/
    Do NOT copy expected_results/, golden.hash, meta.json.
    """
    expected_src = src / "expected"
    inputs_src = src / "inputs"

    expected_dst = dst / "expected"
    inputs_dst = dst / "inputs"

    expected_dst.mkdir(parents=True, exist_ok=True)
    inputs_dst.mkdir(parents=True, exist_ok=True)

    _copy_tree(expected_src, expected_dst)
    _copy_tree(inputs_src, inputs_dst)

    _create_readme(dst)


# ------------------------------------------------------------
# Internal helpers
# ------------------------------------------------------------

def _touch_empty(path: Path) -> None:
    """
    Create an empty file if it does not exist.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch(exist_ok=True)


def _create_readme(case_dir: Path) -> None:
    """
    Create a placeholder README.md if not present.
    """
    readme = case_dir / "README.md"
    if readme.exists():
        return

    readme.write_text(
        "# Golden Test Case\n\n"
        "This directory contains a golden test case for TextFSMGen.\n"
        "Edit canonical/ or expected/ files as needed.\n",
        encoding="utf-8",
    )


def _copy_tree(src: Path, dst: Path) -> None:
    """
    Copy all files from src to dst, preserving directory structure.
    Only copies files; does not copy derived artifacts.
    """
    if not src.is_dir():
        return

    for item in src.iterdir():
        if item.is_file():
            shutil.copy2(item, dst / item.name)
        elif item.is_dir():
            sub_dst = dst / item.name
            sub_dst.mkdir(exist_ok=True)
            _copy_tree(item, sub_dst)
