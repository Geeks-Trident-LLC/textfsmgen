import json
import platform
import subprocess
from datetime import datetime
from pathlib import Path
import difflib
import textwrap

import re
import textfsm
import textfsmgen


gold_root = Path(__file__).parent


# ---------- Meta generation -------------------------------------------------


def generate_meta(
    kind: str,
    case: str,
    author: str,
    description: str = "",
    notes: str = "",
    schema_version: str = "1.0",
) -> None:
    if not author:
        raise ValueError("Author name is required to generate metadata.")

    file_path = gold_root / kind / case / "meta.json"
    file_path.parent.mkdir(parents=True, exist_ok=True)

    approved_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        git_commit = (
            subprocess.check_output(["git", "rev-parse", "HEAD"])
            .decode("utf-8")
            .strip()
        )
    except Exception:       # noqa
        git_commit = None

    meta = {
        "schema_version": schema_version,
        "approved_by": author,
        "approved_at": approved_at,
        "description": description,
        "notes": notes,
        "textfsmgen_version": textfsmgen.__version__,
        "textfsm_version": textfsm.__version__,
        "python_version": platform.python_version(),
        "operating_system": f"{platform.system()} {platform.release()}",
        "machine": platform.machine(),
        "git_commit": git_commit,
    }

    with file_path.open("w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)


# ---------- Discovery & scaffolding ----------------------------------------


def iter_testcases():
    """Yield (kind, case, case_dir) for all golden test cases."""
    for kind_dir in gold_root.iterdir():
        if not kind_dir.is_dir():
            continue
        if kind_dir.name.startswith("_"):
            continue

        for case_dir in kind_dir.iterdir():
            if not case_dir.is_dir():
                continue
            if case_dir.name.startswith("_") or case_dir.name == "__pycache__":
                continue

            yield kind_dir.name, case_dir.name, case_dir


def ensure_scaffold(kind: str, case: str) -> Path:
    """Ensure the folder structure for a golden test case exists."""
    case_dir = gold_root / kind / case
    (case_dir / "inputs").mkdir(parents=True, exist_ok=True)
    (case_dir / "expected" / "results").mkdir(parents=True, exist_ok=True)
    return case_dir


# ---------- File helpers ----------------------------------------------------


def sync_datetime(curr: str, expected: str) -> str:
    """Replace expected template's created-date line with the generated one."""
    pattern = r"# Created date: \d{4}-\d{2}-\d{2}"

    generated = next((l for l in curr.splitlines() if re.match(pattern, l)), "")
    out = []

    for line in expected.splitlines():
        if generated and re.match(pattern, line):
            out.append(generated)
            generated = ""
        else:
            out.append(line)
    return "\n".join(out)


def get_inputs_and_results(kind: str, case: str):
    inputs_path = gold_root / kind / case / "inputs"
    results_path = gold_root / kind / case / "expected" / "results"

    for input_file in sorted(inputs_path.glob("*.txt")):
        basename = input_file.stem
        result_path = results_path / f"{basename}_result.json"

        sample = input_file.read_text(encoding="utf-8")

        if result_path.exists():
            raw_result = result_path.read_text(encoding="utf-8")
            expected_result = json.loads(raw_result) or []
        else:
            expected_result = []

        yield basename, sample, expected_result, result_path


def get_expected_snippet_and_templates(kind: str, case: str):
    snippet_path = gold_root / kind / case / "expected" / "snippet.txt"
    template_path = gold_root / kind / case / "expected" / "textfsm.template"

    exp_snippet = snippet_path.read_text(encoding="utf-8") if snippet_path.exists() else ""
    exp_template = template_path.read_text(encoding="utf-8") if template_path.exists() else ""

    return exp_snippet, exp_template, snippet_path, template_path


def get_parameters(kind: str, case: str):
    config_path = gold_root / kind / case / "config.json"
    if not config_path.exists():
        return {}
    raw_config = config_path.read_text(encoding="utf-8")
    return json.loads(raw_config) or {}


# ---------- Diff reporting --------------------------------------------------


def format_diff(expected: str, actual: str, header: str) -> str:
    expected_lines = expected.splitlines(keepends=True)
    actual_lines = actual.splitlines(keepends=True)

    diff = difflib.unified_diff(
        expected_lines,
        actual_lines,
        fromfile="expected",
        tofile="actual",
    )
    body = "".join(diff)
    if not body:
        return header

    return header + "\n" + textwrap.indent(body, "    ")


def json_dumps_pretty(obj) -> str:
    """Return stable, human‑readable JSON for golden files."""
    return json.dumps(
        obj,
        indent=2,
        ensure_ascii=False,
        sort_keys=True,
    )


def validate_golden_schema(kind, case):
    case_dir = gold_root / kind / case

    required_files = [
        "snippet.txt",
        "template.txt",
        "config.json",
        "meta.json",
    ]

    for f in required_files:
        if not (case_dir / f).exists():
            raise FileNotFoundError(f"Missing required file: {case_dir / f}")

    if not (case_dir / "input").is_dir():
        raise FileNotFoundError(f"Missing input/ folder: {case_dir}")

    if not (case_dir / "expected").is_dir():
        raise FileNotFoundError(f"Missing expected/ folder: {case_dir}")

    # Optional: warn about unexpected files
    allowed = set(required_files + ["input", "expected"])
    for item in case_dir.iterdir():
        if item.name not in allowed:
            print(f"WARNING: unexpected file in golden case: {item}")
