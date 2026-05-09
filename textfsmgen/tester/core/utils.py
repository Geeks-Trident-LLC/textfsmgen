"""
Utility helpers for the tester subsystem.

This module intentionally stays very small and focused.
Only generic, reusable helpers that do NOT belong to any
specific tester action should live here.
"""

from __future__ import annotations

from pathlib import Path


# ----------------------------------------------------------------------
# Error helpers
# ----------------------------------------------------------------------
def require_case_dir(case_path: Path) -> Path:
    """
    Ensure the given path exists and is a directory.

    Raises a clear error if the path is invalid.
    """
    if not case_path.exists():
        raise ValueError(f"Case path does not exist: {case_path}")

    if not case_path.is_dir():
        raise ValueError(f"Case path is not a directory: {case_path}")

    return case_path


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
