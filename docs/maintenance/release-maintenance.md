# 🟧 Release Maintenance

Build, validate, and prepare releases.

```powershell
pwsh scripts/build.ps1                     # Build package
pwsh scripts/release-test.ps1 -DryRun      # TestPyPI dry-run
pwsh scripts/release-test.ps1              # Publish to TestPyPI
pwsh scripts/release.ps1                   # Publish to PyPI
pwsh scripts/generate-release-notes.ps1
pwsh scripts/pack-release.ps1              # Release bundle
pwsh scripts/release-draft.ps1 -Tag vX.Y.Z
pwsh scripts/release-finalize.ps1 -Tag vX.Y.Z
```