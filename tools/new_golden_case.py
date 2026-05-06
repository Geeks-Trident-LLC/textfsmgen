#!/usr/bin/env python3
import json
import pathlib
import argparse
import sys


ROOT = pathlib.Path("tests/golden")


def create_case(case_name: str):
    case_dir = ROOT / case_name

    if case_dir.exists():
        print(f"[ERROR] Golden case '{case_name}' already exists: {case_dir}")
        sys.exit(1)

    # Create directory structure
    (case_dir / "canonical").mkdir(parents=True)
    (case_dir / "inputs").mkdir()
    (case_dir / "expected").mkdir()

    # Create empty canonical files
    (case_dir / "canonical/sample.txt").write_text("", encoding="utf-8")
    (case_dir / "canonical/expected_snippet.txt").write_text("", encoding="utf-8")
    (case_dir / "canonical/expected_textfsm.template").write_text("", encoding="utf-8")
    (case_dir / "canonical/expected_result.json").write_text("{}", encoding="utf-8")

    # Write manifest.json
    manifest = {
        "case": case_name,
        "kind": "tabular",
        "parameters": {},
        "canonical": {
            "sample": "canonical/sample.txt",
            "snippet": "canonical/expected_snippet.txt",
            "template": "canonical/expected_textfsm.template",
            "result": "canonical/expected_result.json"
        },
        "inputs": []
    }

    manifest_path = case_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(f"[OK] Created golden case: {case_name}")
    print(f"     Path: {case_dir}")
    print("")
    print("Next steps:")
    print(f"  1. Edit {manifest_path}")
    print("  2. Fill in canonical/sample.txt with real device output")
    print("  3. Fill in expected_snippet.txt, expected_textfsm.template, expected_result.json")
    print("  4. Add input samples under inputs/")
    print("  5. Add expected results under expected/")
    print("")
    print("Run golden tests:")
    print("  pytest --enable-golden --diff-golden tests/golden")


def main():
    parser = argparse.ArgumentParser(description="Create a new golden test case")
    parser.add_argument("case", help="Name of the golden test case")
    args = parser.parse_args()

    create_case(args.case)


if __name__ == "__main__":
    main()
