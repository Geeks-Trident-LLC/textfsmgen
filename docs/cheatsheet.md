
# 🧭 textfsmgen — Developer Cheat Sheet

> **Note:** Commands use `pwsh` (PowerShell 7+).  
> If unavailable, use `powershell`.  
> See: [Installing PowerShell 7](miscellaneous/powershell-install.md)


## Regular Maintenance
```powershell
make clean                     # Clean project
pwsh scripts/format.ps1        # Format code
pwsh scripts/lint.ps1          # Lint code
pwsh scripts/test.ps1          # Run tests
pwsh scripts/bootstrap.ps1     # Full environment setup
```

## Testing Maintenance
```powershell
pwsh scripts/test.ps1                      # Full test suite
pwsh scripts/coverage.ps1                  # Coverage
pwsh scripts/typecheck.ps1                 # Type checking
pwsh scripts/validate-template.ps1 -Template file.textfsm
pwsh scripts/validate-docs.ps1             # Docs validation
pwsh scripts/validate-all.ps1              # Full validation
```

## Release Maintenance
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

## Deployment Maintenance
```powershell
pwsh scripts/validate-all.ps1
pwsh scripts/pack-release.ps1
pwsh scripts/release.ps1
pwsh scripts/release-draft.ps1 -Tag vX.Y.Z
pwsh scripts/release-finalize.ps1 -Tag vX.Y.Z
pwsh scripts/release-notify.ps1 -Tag vX.Y.Z -SlackWebhook <url>
```

## Makefile Quick Reference
```makefile
make clean       # Clean project
make format      # Format code
make lint        # Lint code
make test        # Run tests
make coverage    # Coverage
make typecheck   # Type checking
make build       # Build package
make docs        # Build docs
make api         # API docs
make verify      # Full verification
```