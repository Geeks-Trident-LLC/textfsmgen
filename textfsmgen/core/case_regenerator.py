# textfsmgen/core/case_regenerator.py

import os
import json
import platform
import subprocess
from datetime import datetime
from pathlib import Path

import textfsm
import textfsmgen

from textfsmgen.core.case_loader import CaseLoader
from textfsmgen.core.drift_checker import DriftChecker
from textfsmgen import parse_textfsm_to_dicts, TabularBuilder, CategoryBuilder


class CaseRegenerator:
    """
    Regenerates canonical or integration golden files.
    """

    BUILDERS = {
        "tabular": TabularBuilder,
        "category": CategoryBuilder,
    }

    def __init__(self, loader: CaseLoader):
        self.loader = loader

    def regenerate(self):
        # --------------------------------------------------------------
        # EXACT behavior from your old DataLoader:
        # Only regenerate when explicitly requested
        # --------------------------------------------------------------
        if not os.getenv("GOLDEN_REGEN"):
            return

        if self.loader.kind == "main":
            self.regen_main()
            return
        self.regen_integration()

    def regen_main(self):
        Builder = self.BUILDERS[self.loader.builder_type]
        builder = Builder()

        builder.set_sample(self.loader.canonical_sample, **self.loader.parameters)
        builder.build()

        # Write snippet/template
        (self.loader.canonical_dir / "snippet.txt").write_text(builder.snippet, "utf-8")
        (self.loader.canonical_dir / "textfsm.template").write_text(
            builder.template, "utf-8"
        )

        # Write canonical result
        result = parse_textfsm_to_dicts(builder.template, self.loader.canonical_sample)
        (self.loader.canonical_dir / "result.json").write_text(
            json.dumps(result, indent=2, ensure_ascii=False), "utf-8"
        )

        # Regenerate expected results
        for inp, res in self.loader.iter_input_result_pairs():
            parsed = parse_textfsm_to_dicts(builder.template, inp.data)
            Path(res.path).write_text(
                json.dumps(parsed, indent=2, ensure_ascii=False), "utf-8"
            )

        # Write meta.json (only when allowed)
        self.generate_meta()

        # Write golden.hash (always during regen)
        DriftChecker(self.loader).write_hash()

    def regen_integration(self):
        # Integration regen = simply re-run integration logic
        from textfsmgen.core.case_runner import CaseRunner

        # Avoid recursion: call the internal method directly
        CaseRunner(self.loader).run_integration()

    def generate_meta(self):
        # Only write meta when explicitly allowed
        if not os.getenv("GOLDEN_WRITE_META") and not os.getenv("GOLDEN_REGEN"):
            return

        # Only main cases have meta.json
        if self.loader.kind != "main":
            return

        meta = self.loader.meta
        author = meta.get("author", "")
        email = meta.get("email", "")
        description = meta.get("description", "")
        notes = meta.get("notes", "")
        schema_version = meta.get("schema_version", "1.0")

        if not author:
            raise ValueError("Author name is required to generate metadata.")

        file_path = self.loader.file_path / "meta.json"
        file_path.parent.mkdir(parents=True, exist_ok=True)

        approved_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            git_commit = (
                subprocess.check_output(["git", "rev-parse", "HEAD"])
                .decode("utf-8")
                .strip()
            )
        except Exception:
            git_commit = None

        meta_obj = {
            "schema_version": schema_version,
            "approved_by": author,
            "approved_at": approved_at,
            "description": description,
            "email": email,
            "notes": notes,
            "textfsmgen_version": textfsmgen.__version__,
            "textfsm_version": textfsm.__version__,
            "python_version": platform.python_version(),
            "operating_system": f"{platform.system()} {platform.release()}",
            "machine": platform.machine(),
            "git_commit": git_commit,
        }

        file_path.write_text(
            json.dumps(meta_obj, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
