from __future__ import annotations

from pathlib import Path
import json
import click
from dataclasses import dataclass

from ..core.golden_case import GoldenCase

from ..cli_decorator import (
    timed_command,
    # validate_sandbox_flags,
)
from ..core.utils import validate_case_path


@click.command(
    name="drift",
    help="Detect drift between current outputs and golden expected results.",
)
@timed_command
@click.argument("case", type=click.Path())
@click.option(
    "--names-only", "--names", is_flag=True, help="List only files that have drift."
)
@click.option(
    "--type",
    "drift_type",
    type=click.Choice(["all", "results", "snippet", "template"]),
    default="all",
    help="Limit drift check to specific artifact types.",
)
@click.option(
    "--json", "json_mode", is_flag=True, help="Emit machine-readable JSON drift report."
)
@click.option("--summary", is_flag=True, help="Show summary of drift results.")
@click.option(
    "--fail-on-drift", is_flag=True, help="Exit with code 1 if any drift is detected."
)
@click.option("--quiet", is_flag=True, help="Suppress OK lines; only show drift.")
def cmd_drift(case, names_only, drift_type, json_mode, summary, fail_on_drift, quiet):
    return cmd_drift_(
        Path(case).resolve(),
        names_only=names_only,
        drift_type=drift_type,
        json_mode=json_mode,
        summary=summary,
        fail_on_drift=fail_on_drift,
        quiet=quiet,
    )


def cmd_drift_(
    case_path,
    names_only=False,
    drift_type="all",
    json_mode=False,
    summary=False,
    fail_on_drift=False,
    quiet=False,
):

    ok = validate_case_path(case_path)
    if not ok:
        click.echo(f"[FAIL] {ok}")
        return 1

    gc = GoldenCase.from_path(case_path)

    # Integration cases do not define authoritative truth
    if gc.is_integration():
        msg = f"[INFO] Drift check skipped for integration case '{gc.name}'."
        if json_mode:
            payload = {"skipped": True, "case": gc.name, "reason": "integration-case"}
            click.echo(json.dumps(payload, indent=2))

            return 0
        if not quiet:
            click.echo(msg)
        return 0

    # MAIN CASE DRIFT CHECK
    checker = DriftChecker(gc)
    drift_items = checker.check_drift(drift_type=drift_type)

    any_drift = any(item.has_drift for item in drift_items)

    # JSON MODE
    if json_mode:
        payload = {
            "case": gc.name,
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
        click.echo(f"[OK] No drift detected in '{gc.name}'.")

    if any_drift and not quiet:
        click.echo(f"[FAIL] Golden files drift detected in '{gc.name}'.")
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
