param(
    [Parameter(Mandatory=$true)]
    [ValidateSet(
        "clean", "deep-clean",
        "lint", "format",
        "test", "build",
        "docs", "release"
    )]
    [string]$Command,

    [switch]$DryRun,
    [switch]$Verbose
)

$root = Split-Path $PSScriptRoot -Parent

Import-Module "$PSScriptRoot/ProjectTools.psm1" -Force

switch ($Command) {

    "clean" {
        Clean-Project -DryRun:$DryRun
    }

    "deep-clean" {
        DeepClean-Project -DryRun:$DryRun
    }

    "lint" {
        pwsh "$PSScriptRoot/lint.ps1"
    }

    "format" {
        pwsh "$PSScriptRoot/format.ps1"
    }

    "test" {
        pwsh "$PSScriptRoot/test.ps1" -Verbose:$Verbose
    }

    "build" {
        pwsh "$PSScriptRoot/build.ps1"
    }

    "docs" {
        pwsh "$PSScriptRoot/docs.ps1"
    }

    "release" {
        pwsh "$PSScriptRoot/release.ps1" -DryRun:$DryRun
    }
}

Write-Host "`nDone." -ForegroundColor Green
