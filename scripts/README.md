# 🛠️ Project Scripts Overview

This directory contains **PowerShell helper scripts** used for development, testing, docs, and releases.

All examples assume **PowerShell 7+ (`pwsh`)**.  
If you don’t have it, see: `docs/miscellaneous/powershell-install.md`.

---

## 🔧 Core Development

- `dev.ps1` — Start a development environment (venv, deps, etc.)
- `bootstrap.ps1` — One-time setup for a fresh clone
- `upgrade.ps1` — Upgrade dependencies and tooling

---

## 🧹 Cleanup & Formatting

- `clean.ps1` — Clean build artifacts
- `format.ps1` — Apply code formatting
- `lint.ps1` — Run linters
- `validate-python.ps1` — Validate Python code (lint + typecheck)

---

## 🧪 Testing & Validation

- `test.ps1` — Run the test suite
- `coverage.ps1` — Run tests with coverage
- `typecheck.ps1` — Run static type checking
- `validate-template.ps1` — Validate TextFSM templates
- `validate-docs.ps1` — Validate documentation
- `validate-all.ps1` — Run all validation checks
- `verify.ps1` / `verify-all.ps1` — Higher-level verification bundles

---

## 📚 Documentation

- `docs.ps1` — Build documentation
- `serve-docs.ps1` — Serve docs locally with live reload
- `serve-api-docs.ps1` — Serve API docs
- `publish-docs.ps1` — Publish docs (used by CI)

---

## 📦 Packaging & Release

- `build.ps1` — Build Python package
- `pack.ps1` — Build distribution artifacts
- `pack-release.ps1` — Build release bundle
- `release-test.ps1` — TestPyPI release
- `release.ps1` — PyPI release
- `release-draft.ps1` — Create a release draft
- `release-finalize.ps1` — Finalize a release
- `release-notify.ps1` — Notify channels (e.g., Slack)

---

## 🩺 Diagnostics

- `doctor.ps1` / `doctor-all.ps1` — Environment diagnostics
- `doctor-report.ps1` — Generate diagnostic report
- `monitor.ps1` — Monitor long-running tasks
- `watch.ps1` — Watch files and rerun tasks

---

## 🧪 Benchmarks

- `bench.ps1` — Run a benchmark
- `bench-suite.ps1` — Run the full benchmark suite

---

## 🔁 CI Helpers

These are primarily used by CI workflows:

- `ci.ps1`
- `ci-full.ps1`
- `ci-matrix.ps1`
- `ci-docs.ps1`
- `ci-release-test.ps1`
- `ci-release.ps1`

You normally don’t need to run these manually.
