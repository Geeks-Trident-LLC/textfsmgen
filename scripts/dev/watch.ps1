param(
    [ValidateSet("test", "lint", "format")]
    [string]$Mode = "test"
)

$root = Split-Path $PSScriptRoot -Parent

Write-Host "Watching for changes... (Mode: $Mode)" -ForegroundColor Cyan

$action = {
    switch ($args[0]) {
        "test"   { pwsh "$PSScriptRoot/test.ps1" }
        "lint"   { pwsh "$PSScriptRoot/lint.ps1" }
        "format" { pwsh "$PSScriptRoot/format.ps1" }
    }
}

$watcher = New-Object System.IO.FileSystemWatcher
$watcher.Path = $root
$watcher.IncludeSubdirectories = $true
$watcher.Filter = "*.py"
$watcher.EnableRaisingEvents = $true

Register-ObjectEvent $watcher Changed -Action { $action.Invoke($Mode) }
Register-ObjectEvent $watcher Created -Action { $action.Invoke($Mode) }
Register-ObjectEvent $watcher Deleted -Action { $action.Invoke($Mode) }
Register-ObjectEvent $watcher Renamed -Action { $action.Invoke($Mode) }

while ($true) { Start-Sleep -Seconds 1 }
