param(
    [Parameter(Mandatory = $true)]
    [string]$Version
)

$ErrorActionPreference = "Stop"

Write-Host ">>> Ensuring clean working tree..." -ForegroundColor Cyan
git status --porcelain
if ($LASTEXITCODE -ne 0) { throw "git status failed" }
if ((git status --porcelain) -ne "") {
    throw "Working tree is not clean. Commit or stash changes before releasing."
}

Write-Host ">>> Running tests..." -ForegroundColor Cyan
pytest
if ($LASTEXITCODE -ne 0) { throw "Tests failed." }

Write-Host ">>> Building docs (mkdocs --strict)..." -ForegroundColor Cyan
mkdocs build --strict
if ($LASTEXITCODE -ne 0) { throw "Docs build failed." }

Write-Host ">>> Bumping version to $Version..." -ForegroundColor Cyan
bump2version --new-version $Version minor
if ($LASTEXITCODE -ne 0) { throw "bump2version failed." }

Write-Host ">>> Pushing commits and tags..." -ForegroundColor Cyan
git push
git push --tags

Write-Host ">>> Release flow complete. GitHub Actions should now build & publish." -ForegroundColor Green
