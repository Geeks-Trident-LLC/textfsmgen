function Clean-Project {
    [CmdletBinding()]
    param([switch]$DryRun)

    $root = Get-Location
    $targets = @("build", "dist")

    foreach ($t in $targets) {
        $path = Join-Path $root $t
        if (Test-Path $path) {
            if ($DryRun) { Write-Host "[DIR]  $path" }
            else { Remove-Item $path -Recurse -Force -ErrorAction SilentlyContinue }
        }
    }

    Get-ChildItem -Path $root -Directory -Filter "*.egg-info" -Force |
        ForEach-Object {
            if ($DryRun) { Write-Host "[DIR]  $($_.FullName)" }
            else { Remove-Item $_.FullName -Recurse -Force -ErrorAction SilentlyContinue }
        }
}

function DeepClean-Project {
    [CmdletBinding()]
    param([switch]$DryRun)

    Clean-Project -DryRun:$DryRun

    $root = Get-Location

    $rootDirs = @(".tox", "htmlcov", ".pytest_cache", ".ruff_cache")
    $rootFiles = @(".coverage", "search.txt")

    foreach ($d in $rootDirs) {
        $path = Join-Path $root $d
        if (Test-Path $path) {
            if ($DryRun) { Write-Host "[DIR]  $path" }
            else { Remove-Item $path -Recurse -Force -ErrorAction SilentlyContinue }
        }
    }

    foreach ($f in $rootFiles) {
        $path = Join-Path $root $f
        if (Test-Path $path) {
            if ($DryRun) { Write-Host "[FILE] $path" }
            else { Remove-Item $path -Force -ErrorAction SilentlyContinue }
        }
    }

    Get-ChildItem -Path $root -File -Filter ".coverage.*" -Force |
        ForEach-Object {
            if ($DryRun) { Write-Host "[FILE] $($_.FullName)" }
            else { Remove-Item $_.FullName -Force -ErrorAction SilentlyContinue }
        }

    $items = Get-ChildItem -Recurse -Force

    $dirs = $items | Where-Object { $_.PSIsContainer -and $_.Name -eq "__pycache__" }
    $files = $items | Where-Object { -not $_.PSIsContainer -and $_.Extension -eq ".pyc" }

    foreach ($d in $dirs) {
        if ($DryRun) { Write-Host "[DIR]  $($d.FullName)" }
        else { Remove-Item $d.FullName -Recurse -Force -ErrorAction SilentlyContinue }
    }

    foreach ($f in $files) {
        if ($DryRun) { Write-Host "[FILE] $($f.FullName)" }
        else { Remove-Item $f.FullName -Force -ErrorAction SilentlyContinue }
    }
}
