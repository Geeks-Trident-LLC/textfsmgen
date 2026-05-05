<#
.SYNOPSIS
  Unified dispatcher for all project scripts.

.EXAMPLE
  ./scripts/run.ps1 test
  ./scripts/run.ps1 release draft
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$Command,
    [string[]]$Args
)

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path

$Routes = @{
  # dev
  "test"        = "dev/test.ps1"
  "lint"        = "dev/lint.ps1"
  "format"      = "dev/format.ps1"
  "typecheck"   = "dev/typecheck.ps1"
  "doctor"      = "dev/doctor.ps1"
  "watch"       = "dev/watch.ps1"
  "build"       = "dev/build.ps1"

  # ci
  "ci"          = "ci/ci.ps1"
  "ci-full"     = "ci/ci-full.ps1"
  "ci-matrix"   = "ci/ci-matrix.ps1"

  # release
  "release"     = "release/release.ps1"
  "release-draft" = "release/release-draft.ps1"
  "release-finalize" = "release/release-finalize.ps1"

  # docs
  "docs"        = "docs/docs.ps1"
  "serve-docs"  = "docs/serve-docs.ps1"
  "api-docs"    = "docs/generate-api-docs.ps1"

  # validate
  "validate"    = "validate/validate-all.ps1"
  "validate-python" = "validate/validate-python.ps1"
  "validate-template" = "validate/validate-template.ps1"

  # bench
  "bench"       = "bench/bench.ps1"
}

if (-not $Routes.ContainsKey($Command)) {
    Write-Host "Unknown command: $Command"
    Write-Host "Available commands:"
    $Routes.Keys | Sort-Object | ForEach-Object { Write-Host "  $_" }
    exit 1
}

$Script = Join-Path $Root $Routes[$Command]
& $Script @Args
