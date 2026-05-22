# textfsmgen/cli/shared_builder_cli.py
import copy
import json
from pathlib import Path


from textfsmgen.libs.generic import StatusString, DotDict
from textfsmgen.libs.common import emit_status
from textfsmgen.libs.utils import get_data_as_tabular
from textfsmgen.libs.text import render_text_block

from textfsmgen.core.builder import (
    BuildResult,
    FreeFormBuilder,
    TabularBuilder,
    CategoryBuilder,
)

from .config_cmd import get_config_template


BUILDER_MAPPING = {
    "freeform": FreeFormBuilder,
    "tabular": TabularBuilder,
    "category": CategoryBuilder,
}


def parse_save_expression(expr: str):
    """
    Parse save syntax:

        sample-out.txt,result-a.json
        dryrun(sample-out.txt,result-a.json)

    Returns:
        ("", parsed)              # normal mode
        ("dryrun", parsed)        # dry-run mode

    Where parsed is:
        [
            {"kind": "sample", "path": "out.txt"},
            {"kind": "result", "path": "a.json"},
        ]

    Raises:
        ValueError on invalid syntax.
    """
    expr = expr.strip()
    if not expr:
        raise ValueError("Empty --save expression")

    mode = ""
    inner = expr

    # Detect dryrun(...) wrapper
    if expr.startswith("dryrun(") and expr.endswith(")"):
        mode = "dryrun"
        inner = expr[len("dryrun(") : -1].strip()

    if not inner:
        raise ValueError("Empty save list inside expression")

    allowed_kinds = {"sample", "snippet", "template", "result"}

    raw_items = [x.strip() for x in inner.split(",") if x.strip()]
    if not raw_items:
        raise ValueError("No valid save items found")

    parsed = []

    for item in raw_items:
        if "-" not in item:
            raise ValueError(f"Invalid save item '{item}'. Expected <kind>-<filename>")

        kind, filename = item.split("-", 1)
        kind = kind.strip()
        filename = filename.strip()

        if kind not in allowed_kinds:
            raise ValueError(
                f"Invalid save kind '{kind}'. "
                f"Allowed kinds: {', '.join(sorted(allowed_kinds))}"
            )

        if not filename:
            raise ValueError(f"Missing filename for kind '{kind}'")

        parsed.append({"kind": kind, "path": filename})

    return mode, parsed


def _write_file(filename: str, content: str, kind: str, mode: str = "") -> StatusString:
    """
    Write content to filename, or simulate writing in dry-run mode.

    Returns:
        StatusString with a kind-aware message.
    """
    is_dry_run = mode == "dryrun"

    if is_dry_run:
        return StatusString(
            f"[DRY-RUN] {kind} → {filename}",
            status=True,
            reason="info",
        )

    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)

        return StatusString(
            f"Saved {kind} → {filename}",
            status=True,
            reason="info",
        )

    except Exception as exc:
        return StatusString(
            f"Failed to save {kind} → {filename}: {exc}",
            status=False,
            reason="code-error",
        )


def save_outputs(api_params, builder_result):
    """
    Save outputs using the unified syntax:
        --save=sample-out.txt,snippet-snippet.txt,template-template.textfsm,result-out.json

    Returns:
        DotDict(
            status=StatusString(...),
            files=[...],
            exit_code=int,
        )
    """

    # ------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------
    def append(kind_, path, status_):
        files.append(
            {
                "kind": kind_,
                "path": path,
                "severity": status_.reason,
                "message": str(status_),
            }
        )

    def record_failure(status_):
        msg = emit_status(status_)
        failure_messages.append(msg)
        return "[FATAL]" in msg

    # ------------------------------------------------------------
    # Parse save expression
    # ------------------------------------------------------------
    try:
        _, items = parse_save_expression(api_params.save)
    except ValueError as exc:
        message = f"Parse-Expression ({type(exc).__name__}: {exc})"
        return DotDict(
            status=StatusString(message, status=False, reason="code-error"),
            save_info={"raw": api_params.save, "files": []},
            exit_code=2,
        )

    files = []
    failure_messages = []
    fatal = False

    # ------------------------------------------------------------
    # Process each save item
    # ------------------------------------------------------------
    for entry in items:
        kind = entry["kind"]
        filename = entry["path"]

        # ------------------------------------------------------------
        # sample is always allowed
        # ------------------------------------------------------------
        if kind == "sample":
            content = api_params.sample_data
            status = _write_file(filename, content, kind)
            if not status:
                fatal |= record_failure(status)
            append(kind, filename, status)
            continue

        # ------------------------------------------------------------
        # builder-level warning blocks snippet/template/result
        # ------------------------------------------------------------
        if builder_result.warning:
            msg = f"Build result contains warning: {builder_result.warning}. Cannot proceed."
            status = StatusString(msg, status=False, reason="error")
            fatal |= record_failure(status)
            append("build-result", None, status)
            continue

        # ------------------------------------------------------------
        # Load content
        # ------------------------------------------------------------
        if kind in ("snippet", "template"):
            content = getattr(builder_result, kind, None)
            if not content:
                msg = f"Builder has no '{kind}' content"
                status = StatusString(msg, status=False, reason="warning")
                fatal |= record_failure(status)
                append(kind, filename, status)
                continue

        elif kind == "result":
            content = builder_result.result
            if not content:
                msg = f"No records found for '{filename}'"
                status = StatusString(msg, status=False, reason="warning")
                fatal |= record_failure(status)
                append(kind, filename, status)
                continue

        else:
            msg = f"Unknown save kind '{kind}'"
            status = StatusString(msg, status=False, reason="error")
            fatal |= record_failure(status)
            append(f"unknown-{kind}", None, status)
            continue

        # ------------------------------------------------------------
        # Normalize content to string
        # ------------------------------------------------------------
        if not isinstance(content, str):
            content = json.dumps(content, indent=2, ensure_ascii=False)

        # ------------------------------------------------------------
        # Write file
        # ------------------------------------------------------------
        status = _write_file(filename, content, kind)
        if not status:
            fatal |= record_failure(status)
        append(kind, filename, status)

    # ------------------------------------------------------------
    # Final result
    # ------------------------------------------------------------
    if failure_messages:
        return DotDict(
            status=StatusString(
                "\n".join(failure_messages), status=False, reason="error"
            ),
            save_info={"raw": api_params.save, "files": files},
            exit_code=2 if fatal else 1,
        )

    return DotDict(
        status=StatusString(status=True),
        save_info={"raw": api_params.save, "files": files},
        exit_code=0,
    )


def show_outputs(api_params, builder_result):
    show_spec = (api_params.show or "").strip()
    cases = [c for c in (x.strip() for x in show_spec.split(",")) if c]

    if not cases:
        return DotDict(
            status=StatusString(True),
            show_info=DotDict(
                raw=show_spec, resolved={"template": builder_result.template}
            ),
            exit_code=0,
        )

    resolved = {}

    def resolve_result(kind):
        if builder_result.warning:
            return builder_result.warning
        if kind == "result":
            return builder_result.result
        if kind == "default":
            return str(builder_result.result)
        if kind == "tabular":
            return get_data_as_tabular(builder_result.result)

    for case in cases:
        if case == "sample":
            resolved["sample"] = api_params.sample_data
        elif case in ("snippet", "template"):
            resolved[case] = (
                getattr(builder_result, case) or f"Builder has no '{case}' content"
            )
        elif case in ("result", "default", "tabular"):
            resolved["result"] = resolve_result(case)
        else:
            resolved[case] = f"Unknown show target '{case}'"

    return DotDict(
        status=StatusString(True),
        show_info=DotDict(raw=show_spec, resolved=resolved),
        exit_code=0,
    )


def build_debug_report(api_params):
    if not api_params.debug:
        return ""

    lines = []

    # -------------------------------------------
    # helper
    # -------------------------------------------
    def _add(label, value):
        lines.append(f"{label:<23} = {value!r}")

    header_width = 60

    # -------------------------------------------
    # High-level info
    # -------------------------------------------
    if api_params.snippet_file:
        lines.append(f"[INFO] Loaded snippet from: {api_params.snippet_file!r}")
        if api_params.snippet_data:
            lines.append(
                f"[INFO] Snippet size: {len(api_params.snippet_data)} characters"
            )

    if api_params.sample_data:
        source = api_params.sample_file or api_params.command
        lines.append(f"[INFO] Loaded sample from: {source!r}")
        lines.append(f"[INFO] Sample size: {len(api_params.sample_data)} characters")

    # -------------------------------------------
    # Debug header
    # -------------------------------------------
    lines.append("")
    lines.append(" DEBUG INFO ".center(header_width, "="))
    lines.append("")

    # -------------------------------------------
    # Builder params
    # -------------------------------------------
    lines.append(" BUILDER PARAMS ".center(header_width, "-"))

    if api_params.snippet_file:
        _add("snippet_file", api_params.snippet_file)

    _add("sample_file", api_params.sample_file)
    _add("command", api_params.command)

    # Params block (pretty JSON)
    params_json = json.dumps(api_params.params, indent=2, ensure_ascii=False)
    lines.append(render_text_block(params_json, subject=f"{'params':<23} ="))

    # -------------------------------------------
    # Execution flags
    # -------------------------------------------
    lines.append("")
    lines.append(" EXECUTION FLAGS ".center(header_width, "-"))

    _add("config", api_params.config)
    _add("save", api_params.save)
    _add("show", api_params.show)
    _add("create_config", api_params.create_config)
    _add("create_config_file", api_params.create_config_file)
    _add("create_golden_test", api_params.create_golden_test)
    _add("create_golden_test_path", api_params.create_golden_test_path)
    _add("json_mode", api_params.json_mode)

    lines.append("=" * header_width)

    return "\n".join(lines)


def execute_builder(api_params):
    builder_cls = BUILDER_MAPPING[api_params.builder]
    builder = builder_cls()

    try:
        if api_params.builder == "freeform":
            builder.set_snippet(api_params.snippet_data)
            if api_params.sample_data.strip():
                builder.set_sample(api_params.sample_data)
        else:
            builder.set_sample(api_params.sample_data, **api_params.params)

        builder.build()
    except Exception as exc:
        return DotDict(
            builder_result=None,
            status=StatusString(f"Builder {builder_cls.__name__} failed: {exc}", False, "code-error"),
            exit_code=2,
        )

    result = builder.to_result()

    if not builder:
        ref = (
            api_params.snippet_file or "snippet"
            if api_params.builder == "freeform" else
            api_params.sample_file or api_params.command
        )
        msg = f"Cannot create {api_params.builder} builder from {ref!r}\n{'-'*60}\n{api_params.sample_data}"
        return DotDict(
            builder_result=result,
            status=StatusString(msg, False, "error"),
            exit_code=1,
        )

    return DotDict(
        builder_result=result,
        status=StatusString(True),
        exit_code=0,
    )



def create_config(api_params):
    builder_name = api_params.builder

    # ------------------------------------------------------------
    # 1. Build config payload
    # ------------------------------------------------------------
    template = get_config_template(builder_name)
    cfg = json.loads(json.dumps(template))  # safe deep copy

    # Overlay resolved values
    for key in cfg:
        cfg[key] = copy.deepcopy(api_params[key])

    path = (
        Path(api_params.create_config_file) if api_params.create_config_file else None
    )

    generated_config = DotDict(
        stream="stream" if not api_params.create_config_file else "io",
        path=None if not api_params.create_config_file else str(path.resolve()),
        payload=cfg,
    )

    # ------------------------------------------------------------
    # 2. Stream mode (print to stdout)
    # ------------------------------------------------------------
    if not api_params.create_config_file:
        return DotDict(
            status=StatusString(status=True),
            generated_config=generated_config,
            exit_code=0,
        )

    # ------------------------------------------------------------
    # 3. File mode (write to disk)
    # ------------------------------------------------------------
    path = Path(api_params.create_config_file)
    parent = path.parent

    # Ensure parent directory exists
    if not parent.exists():
        try:
            parent.mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            return DotDict(
                status=StatusString(
                    f"Cannot create directory {str(parent)!r}: {exc}",
                    status=False,
                    reason="code-error",
                ),
                generated_config=generated_config,
                exit_code=2,
            )

    # Prevent overwriting
    if path.exists():
        return DotDict(
            status=StatusString(
                f"Config file {str(path)!r} already exists!",
                status=False,
                reason="error",
            ),
            generated_config=generated_config,
            exit_code=1,
        )

    # Write file
    try:
        content = json.dumps(cfg, indent=2, ensure_ascii=False)
        path.write_text(content, encoding="utf-8")
    except Exception as exc:
        return DotDict(
            status=StatusString(
                f"Failed to write config file {str(path)!r}: {exc}",
                status=False,
                reason="code-error",
            ),
            generated_config=generated_config,
            exit_code=2,
        )

    # Success
    return DotDict(
        status=StatusString(f"[INFO] Config file {str(path)!r} created!", status=True),
        generated_config=generated_config,
        exit_code=0,
    )


def create_golden_test(api_params, builder_result):
    """
    Create or dry-run a golden test case based on builder output and API params.
    """

    # ------------------------------------------------------------
    # 0. Validate sample
    # ------------------------------------------------------------
    if not api_params.sample_data.strip():
        ref = api_params.sample_file or api_params.command
        return DotDict(
            status=StatusString(
                f"Cannot create Golden Test without sample (reference: {ref!r}).",
                status=False,
                reason="error",
            ),
            creation_result=None,
            output="",
            exit_code=1,
        )

    builder_name = api_params.builder

    # ------------------------------------------------------------
    # 1. Determine mode + base path
    # ------------------------------------------------------------
    if api_params.create_golden_test_path:
        mode = "create"
        base_path = Path(api_params.create_golden_test_path).resolve()

        # Must be inside .../golden/integration/<case>
        if not (
            base_path.parent.name == "integration"
            and base_path.parent.parent.name == "golden"
        ):
            return DotDict(
                status=StatusString(
                    f"Golden test path {str(base_path)!r} must be inside "
                    f".../golden/integration/<case>",
                    status=False,
                    reason="error",
                ),
                creation_result=None,
                output="",
                exit_code=1,
            )

    else:
        mode = "dry-run"
        case_name = f"{builder_name}-case"
        base_path = Path("tests") / "golden" / "integration" / case_name

    # ------------------------------------------------------------
    # 2. Prepare manifest + file layout
    # ------------------------------------------------------------
    manifest = {
        "builder": builder_name,
        "params": api_params.params,
        "meta": {
            "author": "",
            "email": "",
            "description": "",
            "notes": "",
            "schema_version": "1.0",
        },
    }

    inputs_dir = base_path / "inputs"
    expected_dir = base_path / "expected"
    expected_results_dir = base_path / "expected_results"

    files = {
        "sample": inputs_dir / "sample.txt",
        "snippet": expected_dir / "snippet.txt",
        "template": expected_dir / "textfsm.template",
        "result": expected_results_dir / "sample_result.json",
        "manifest": base_path / "manifest.json",
    }

    # ------------------------------------------------------------
    # 3. Dry-run mode
    # ------------------------------------------------------------
    if mode == "dry-run":
        lines = [f"[DRY-RUN] Golden test base path: {str(base_path)}"]
        for label, path in files.items():
            lines.append(f"[DRY-RUN] Would create: {str(path)}")

        return DotDict(
            status=StatusString(status=True),
            creation_result=None,
            output="\n".join(lines),
            exit_code=0,
        )

    # ------------------------------------------------------------
    # 4. Actual creation mode
    # ------------------------------------------------------------
    # Create directories
    for d in (inputs_dir, expected_dir, expected_results_dir):
        d.mkdir(parents=True, exist_ok=True)

    # Prevent overwriting
    for label, path in files.items():
        if path.exists():
            return DotDict(
                status=StatusString(
                    f"{label} file {str(path)!r} already exists!",
                    status=False,
                    reason="error",
                ),
                creation_result=None,
                output="",
                exit_code=1,
            )

    # ------------------------------------------------------------
    # 5. Write files
    # ------------------------------------------------------------
    lines = [f"[INFO] Golden test created at {str(base_path)!r}"]

    files["sample"].write_text(api_params.sample_data, encoding="utf-8")
    lines.append(f"  - sample   => {str(files['sample'])}")

    files["snippet"].write_text(builder_result.snippet, encoding="utf-8")
    lines.append(f"  - snippet  => {str(files['snippet'])}")

    files["template"].write_text(builder_result.template, encoding="utf-8")
    lines.append(f"  - template => {str(files['template'])}")

    files["result"].write_text(
        json.dumps(builder_result.result, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    lines.append(f"  - result   => {str(files['result'])}")

    files["manifest"].write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    lines.append(f"  - manifest => {str(files['manifest'])}")

    # ------------------------------------------------------------
    # 6. Build creation_result structure
    # ------------------------------------------------------------
    creation_result = DotDict(
        path=str(base_path),
        manifest={
            "path": str(files["manifest"]),
            "content": json.dumps(manifest, indent=2, ensure_ascii=False),
        },
        inputs={
            "path": str(inputs_dir),
            "files": [
                {
                    "path": str(files["sample"]),
                    "content": api_params.sample_data,
                }
            ],
        },
        expected_results={
            "path": str(expected_results_dir),
            "files": [
                {
                    "path": str(files["result"]),
                    "content": json.dumps(
                        builder_result.result, indent=2, ensure_ascii=False
                    ),
                }
            ],
        },
        expected={
            "path": str(expected_dir),
            "files": [
                {
                    "path": str(files["snippet"]),
                    "content": builder_result.snippet,
                },
                {
                    "path": str(files["template"]),
                    "content": builder_result.template,
                },
            ],
        },
    )

    return DotDict(
        status=StatusString(status=True),
        creation_result=creation_result,
        output="\n".join(lines),
        exit_code=0,
    )
