"""
Utility helpers for the tester subsystem.

This module intentionally stays very small and focused.
Only generic, reusable helpers that do NOT belong to any
specific tester action should live here.
"""

from __future__ import annotations

from pathlib import Path

import functools

from textfsmgen.exceptions import raise_runtime_error
from textfsmgen.libs.generic import StatusString

from textfsmgen.libs import file


def catch_path_errors(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Extract case_path from either args or kwargs
        try:
            if args or "case_path" in kwargs:
                case_path = args[0] if args else kwargs["case_path"]
                multi_case_path = []
                if isinstance(case_path, Path):
                    multi_case_path = [case_path]
                elif isinstance(case_path, (list, tuple)):
                    for item in case_path:
                        if isinstance(item, Path):
                            multi_case_path.append(item)
                for case_path_ in multi_case_path:
                    require_case_dir(case_path_)
            return func(*args, **kwargs)
        except Exception as e:
            exc_name = type(e).__name__
            if exc_name.startswith("TestCasePath"):
                print(f"{exc_name}: {e}")
                return 1
            print(f"ERROR => {exc_name}: {e}")
            return 1

    return wrapper


# ----------------------------------------------------------------------
# Error helpers
# ----------------------------------------------------------------------
def require_case_dir(case_path: Path) -> Path:
    """
    Validate that `case_path` is a proper test case directory.

    Requirements:
      - Must exist and be a directory.
      - Must contain:
            inputs/
            expected_results/
        AND one of:
            canonical/  OR  expected/
    """

    case_path = Path(case_path).resolve()

    if not case_path.exists():
        raise_runtime_error(
            obj="TestCasePathError",
            msg=f"Case path does not exist: {file.path_name(case_path)}",
        )

    if not case_path.is_dir():
        raise_runtime_error(
            obj="TestCasePathError",
            msg=f"Case path is not a directory: {file.path_name(case_path)}",
        )

    # Required folders
    inputs_path = case_path / "inputs"
    results_path = case_path / "expected_results"

    # Optional mutually exclusive folders
    canonical_path = case_path / "canonical"
    expected_path = case_path / "expected"

    has_inputs = inputs_path.is_dir()
    has_results = results_path.is_dir()
    has_canonical = canonical_path.is_dir()
    has_expected = expected_path.is_dir()

    # Correct structure check
    if not (has_inputs and has_results and (has_canonical or has_expected)):
        raise_runtime_error(
            obj="TestCasePathStructureError",
            msg=(
                "Invalid test case structure.\n"
                "Required folders:\n"
                "  - inputs/\n"
                "  - expected_results/\n"
                "And one of:\n"
                "  - canonical/\n"
                "  - expected/\n"
                f"Found in {file.path_name(case_path)}:\n"
                f"  inputs: {has_inputs}\n"
                f"  expected_results: {has_results}\n"
                f"  canonical: {has_canonical}\n"
                f"  expected: {has_expected}"
            ),
        )

    return case_path


def validate_case_path(case_path: Path) -> Path:
    """
    Validate that `case_path` is a proper test case directory.

    Requirements:
      - Must exist and be a directory.
      - Must contain:
            inputs/
            expected_results/
        AND one of:
            canonical/  OR  expected/
    """

    case_path = Path(case_path).resolve()

    if not case_path.exists():
        return StatusString(
            f"Case path does not exist: {file.path_name(case_path)}", status=False
        )

    if not case_path.is_dir():
        return StatusString(
            f"Case path is not a directory: {file.path_name(case_path)}", status=False
        )

    # Required folders
    inputs_path = case_path / "inputs"
    results_path = case_path / "expected_results"

    # Optional mutually exclusive folders
    canonical_path = case_path / "canonical"
    expected_path = case_path / "expected"

    has_inputs = inputs_path.is_dir()
    has_results = results_path.is_dir()
    has_canonical = canonical_path.is_dir()
    has_expected = expected_path.is_dir()

    # Correct structure check
    if not (has_inputs and has_results and (has_canonical or has_expected)):
        msg = (
            "Invalid test case structure.\n"
            "Required folders:\n"
            "  - inputs/\n"
            "  - expected_results/\n"
            "And one of:\n"
            "  - canonical/\n"
            "  - expected/\n"
            f"Found in {file.path_name(case_path)}:\n"
            f"  inputs: {has_inputs}\n"
            f"  expected_results: {has_results}\n"
            f"  canonical: {has_canonical}\n"
            f"  expected: {has_expected}"
        )
        return StatusString(msg, status=False)

    return StatusString(status=True)


# ----------------------------------------------------------------------
# Path helpers
# ----------------------------------------------------------------------
def safe_join(base: Path, *parts: str) -> Path:
    """
    Join paths safely and return a resolved Path.
    """
    return (base.joinpath(*parts)).resolve()


def is_protected_dir(path: Path) -> bool:
    """
    Return True if the path is one of the protected directories
    that tester actions must NEVER write into.
    """
    protected = {"canonical", "expected", "expected_results", "inputs"}
    return path.name in protected


def strip_header_block(text: str) -> str:
    """
    Remove the first two header lines that contain at least 40 '#' characters.
    """
    header_count = 0
    body_lines = []

    for line in text.splitlines():
        if header_count < 2 and line.count("#") >= 40:
            header_count += 1
            continue

        if header_count >= 2:
            body_lines.append(line)

    return "\n".join(body_lines).lstrip() if body_lines else text
