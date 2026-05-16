from __future__ import annotations

from pathlib import Path
import json
import shutil

from ..core.data_loader import extract_subpath_after



def new(case_path: Path) -> int:
    """
    Create a new golden test case scaffold.

    Case type is auto-detected from the path:
        .../main/<case>        → MAIN case
        .../integration/<case> → INTEGRATION case

    MAIN scaffold:
        canonical/{sample.txt, snippet.txt, textfsm.template, result.json}
        inputs/
        expected_results/
        manifest.json

    INTEGRATION scaffold:
        expected/{snippet.txt, textfsm.template}
        inputs/
        expected_results/
        manifest.json
    """

    case_dir = Path(case_path)
    case_dir.mkdir(parents=True, exist_ok=True)

    # --------------------------------------------------------------
    # Detect case type
    # --------------------------------------------------------------
    parts = case_dir.parts
    if "main" in parts:
        case_type = "main"
    elif "integration" in parts:
        case_type = "integration"
    else:
        print("[FAIL] Path must contain either 'main' or 'integration'")
        return 1

    updated = []

    # --------------------------------------------------------------
    # MAIN CASE
    # --------------------------------------------------------------
    if case_type == "main":
        canonical_dir = case_dir / "canonical"
        canonical_dir.mkdir(exist_ok=True)

        for fname in ["sample.txt", "snippet.txt", "textfsm.template", "result.json"]:
            fpath = canonical_dir / fname
            fpath.write_text("")
            updated.append(str(fpath))

        for d in ["inputs", "expected_results"]:
            dpath = case_dir / d
            if dpath.exists():
                shutil.rmtree(dpath)
            dpath.mkdir(parents=True, exist_ok=True)
            updated.append(str(dpath))

    # --------------------------------------------------------------
    # INTEGRATION CASE
    # --------------------------------------------------------------
    if case_type == "integration":
        expected_dir = case_dir / "expected"
        expected_dir.mkdir(exist_ok=True)

        for fname in ["snippet.txt", "textfsm.template"]:
            fpath = expected_dir / fname
            fpath.write_text("")
            updated.append(str(fpath))

        for d in ["inputs", "expected_results"]:
            dpath = case_dir / d
            if dpath.exists():
                shutil.rmtree(dpath)
            dpath.mkdir(parents=True, exist_ok=True)
            updated.append(str(dpath))

    # --------------------------------------------------------------
    # Write manifest.json
    # --------------------------------------------------------------
    manifest_path = case_dir / "manifest.json"
    manifest = {
        "builder": "",
        "parameters": {},
        "meta": {
            "author": "",
            "email": "",
            "description": "",
            "notes": "",
            "schema_version": "1.0",
        },
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
    updated.append(str(manifest_path))

    # --------------------------------------------------------------
    # Success output
    # --------------------------------------------------------------
    tc_name = extract_subpath_after("golden", case_dir)
    print(f"[SUCCESS] created new {case_type} case {tc_name}")
    for f in updated:
        print(f"          + {f}")

    return 0
