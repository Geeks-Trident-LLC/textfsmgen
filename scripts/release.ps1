# Stop on first error
$ErrorActionPreference = "Stop"

param(
    [ValidateSet("patch", "minor", "major")]
    [string]$Part = "patch"
)

Write-Host "==> Bumping version ($Part)..."
bump2version $Part

Write-Host "==> Cleaning old build artifacts..."
Remove-Item -Recurse -Force build, dist, *.egg-info -ErrorAction Ignore

Write-Host "==> Running tests..."
pytest

Write-Host "==> Building package..."
python -m build

Write-Host "==> Uploading to PyPI..."
twine upload dist/*

Write-Host "==> Tagging version..."
$version = python -c "import textfsmgen; print(textfsmgen.__version__)"
git tag "v$version"
git push --tags

Write-Host "==> Pushing commits..."
git push

Write-Host "==> Release complete!"
