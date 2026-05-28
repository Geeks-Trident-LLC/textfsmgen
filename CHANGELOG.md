## [0.7.0] - 2026-05-27

### Added
- Major expansion of the golden-tests subsystem:
  - New commands: `identical`, `promote-plan`, `promote-review`, `promote-diff`, `merge-plan`, `merge-preview`, `merge-review`, `merge-diff`, `merge-view`, `merge`, `drift`, `duplicate`, `copy`, `new`, `batch-*` commands, and more.
  - New CLI options: `--json`, `--compact`, `--diff`, `--quiet`, `--dry-run`, `--verbose`, `--debug`, `--author`, `--summary`, and additional workflow metadata.
  - New shared logging improvements (`shared.log`).
  - New JSON workflow models: `WorkflowMeta`, `ErrorInfo`, `ArtifactIndex`, `WorkflowSteps`.

- CLI improvements:
  - New `file.name_path` support.
  - New debug report builder.
  - New `--headered` / `--headerless` handling.
  - New `--sample-file` support across builders.
  - New config creation enhancements and validation improvements.

- Core improvements:
  - Added `BuilderResult` and integrated builder workflow modules.
  - Added async shell execution (`execute_command_async`).
  - Added improved `emit_status` and DotDict enhancements.

### Changed
- Massive refactor of golden-tests command architecture:
  - Moved click command/option definitions into dedicated modules.
  - Streamlined batch commands, diff, drift, regen, generate, duplicate, and run.
  - Reworked merge commands and diff output formatting.
  - Improved identical command behavior and output.

- CLI refactors:
  - Streamlined shared_builder_cli, builder_runner, workflow_steps, and category/tabular/freeform commands.
  - Unified JSON output handling and validation.
  - Improved parameter parsing, save expressions, and output handling.

- Core refactors:
  - Streamlined data_loader, line parser, shell execution, and common utilities.
  - Reworked DotDict and generic utilities.

- CI/CD:
  - Updated all workflows for Node.js 24 compatibility.
  - Migrated PyPI/TestPyPI publishing to OIDC Trusted Publishing.
  - Modernized CI, docs deployment, and golden test workflows.

### Fixed
- Numerous golden-tests bugs across merge, identical, diff, and run commands.
- Fixed manifest.json creation in CLI.
- Fixed validator and workflow_steps issues.
- Fixed click option bugs (`--has-header`, `--create-config-file`, etc.).
- Fixed state.exit_code handling.

### Removed
- Legacy PyPI/TestPyPI API token usage.
- Deprecated CLI options (`--create-config-file`, `--create-golden-test-path`, old dry-run behavior).
- Removed old `new_from_input` command.
