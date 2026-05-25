from __future__ import annotations

from pathlib import Path
import json
import click
from dataclasses import dataclass

from ..core.utils import catch_path_errors
from ..core.golden_case import GoldenCase


@catch_path_errors
def drift(
    case_path: Path,
    names_only=False,
    drift_type="all",
    json_mode=False,
    summary=False,
    fail_on_drift=False,
    quiet=False,
):

    case = GoldenCase.from_path(case_path)

    # Integration cases do not define authoritative truth
    if case.is_integration():
        msg = f"[INFO] Drift check skipped for integration case '{case.name}'."
        if json_mode:
            payload = {"skipped": True, "case": case.name, "reason": "integration-case"}
            click.echo(json.dumps(payload, indent=2))

            return 0
        if not quiet:
            click.echo(msg)
        return 0

    # MAIN CASE DRIFT CHECK
    checker = DriftChecker(case)
    drift_items = checker.check_drift(drift_type=drift_type)

    any_drift = any(item.has_drift for item in drift_items)

    # JSON MODE
    if json_mode:
        payload = {
            "case": case.name,
            "drift": [
                {
                    "name": item.name,
                    "has_drift": item.has_drift,
                    "reason": item.reason,
                }
                for item in drift_items
            ],
            "drift_detected": any_drift,
        }
        click.echo(json.dumps(payload, indent=2, ensure_ascii=False))

        return 1 if any_drift and fail_on_drift else 0

    # TEXT MODE
    for item in drift_items:
        if quiet and not item.has_drift:
            continue

        if names_only:
            if item.has_drift:
                click.echo(f"[DRIFT] {item.name}")
            elif not quiet:
                click.echo(f"[OK] {item.name}")
            continue

        # Full text output
        if item.has_drift:
            click.echo(f"[FAIL] Drift detected in: {item.name}")
            click.echo(f"       {item.reason}")
        else:
            if not quiet:
                click.echo(f"[OK] {item.name}")

    # Summary
    if summary:
        total = len(drift_items)
        drifted = sum(1 for i in drift_items if i.has_drift)
        passed = total - drifted
        status = "FAIL" if drifted else "OK"
        click.echo(f"[{status}] Summary: {passed}/{total} clean, {drifted} drifted")

    # Final message
    if not any_drift and not quiet:
        click.echo(f"[OK] No drift detected in '{case.name}'.")

    if any_drift and not quiet:
        click.echo(f"[FAIL] Golden files drift detected in '{case.name}'.")
        click.echo("       The authoritative files have changed since last regen.")

    return 1 if any_drift and fail_on_drift else 0


@dataclass
class DriftItem:
    name: str
    has_drift: bool
    reason: str


class DriftChecker:
    def __init__(self, case: GoldenCase):
        self.case = case

    def check_drift(self, drift_type="all") -> list[DriftItem]:
        stored_hash = self.case.data.load_golden_hash()
        current_hash, changed_files = self.case.data.compute_golden_hash(
            drift_type=drift_type, return_changed_files=True
        )

        if stored_hash is None:
            return [
                DriftItem(
                    name="golden.hash",
                    has_drift=True,
                    reason="Missing golden.hash; regen required.",
                )
            ]

        if stored_hash == current_hash:
            return [DriftItem(name="golden.hash", has_drift=False, reason="No drift")]

        # Hash mismatch → list changed authoritative files
        items = []
        for f in changed_files:
            items.append(
                DriftItem(
                    name=f,
                    has_drift=True,
                    reason="Authoritative file changed since last regen.",
                )
            )

        return items
