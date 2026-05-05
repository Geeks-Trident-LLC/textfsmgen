# Scripts Folder

This directory contains all automation used for development, CI, releases, docs, validation, and benchmarking.  
Scripts are grouped by purpose for clarity and maintainability.

---

## dev/
Developer‑focused commands for local workflows.

Includes:
- Environment setup (`bootstrap.ps1`, `setup-dev.ps1`)
- Linting, formatting, type checking
- Test execution
- Version sync tools
- Monitoring and watch utilities
- Doctor diagnostics

---

## ci/
Scripts executed by CI pipelines.

Includes:
- Matrix builds
- Full test runs
- Docs CI
- Release CI
- Verification and coverage

---

## release/
Release automation and packaging.

Includes:
- Packaging and artifact creation
- Drafting and finalizing releases
- Release notifications
- Changelog and release note generation

---

## docs/
Documentation generation and publishing.

Includes:
- Building docs
- Serving docs locally
- API documentation generation
- Publishing to GitHub Pages

---

## validate/
Validation tools.

Includes:
- Python validation
- Template validation
- Docs validation
- Import checks
- All‑in‑one validators

---

## bench/
Benchmarking and performance tools.

Includes:
- Benchmark runner
- Benchmark suite

---

## Root Modules
These remain at the top level:

- `ProjectTools.psd1`
- `ProjectTools.psm1`
- `doctor.psd1`
- `doctor.psm1`
- `README.md`
