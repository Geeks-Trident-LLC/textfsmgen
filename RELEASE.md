# Release Guide

This document describes the full release workflow for the project, including
version bumping, building, testing, publishing, tagging, and CI/CD behavior.

---

## 1. Prerequisites

- Python 3.12+
- pipx or pip
- bump2version
- twine
- build
- GitHub CLI (optional)

Install required tools:

```
pip install bump2version build twine
```

---

## 2. Versioning

The project uses semantic versioning:

- MAJOR: incompatible API changes
- MINOR: new features, backwards compatible
- PATCH: bug fixes only

Version is stored in:

```
textfsmgen/__init__.py
```

Do not manually edit the version.  
Use bump2version:

```
bump2version patch
bump2version minor
bump2version major
```

---

## 3. Local Release (PyPI)

### Patch release
```
make release-auto-patch
```

### Minor release
```
make release-auto-minor
```

### Major release
```
make release-auto-major
```

This performs:

1. bump2version  
2. commit + tag  
3. build  
4. upload to PyPI  
5. push commit + tag  

---

## 4. Local Test Release (TestPyPI)

```
make release-test-auto-minor
```

This performs the same steps but uploads to TestPyPI.

---

## 5. GitHub Actions Release

Pushing a tag like:

```
git tag v0.7.0
git push --tags
```

automatically triggers the PyPI workflow defined in:

```
.github/workflows/release.yml
```

---

## 6. Changelog Generation

Generate a changelog from commits since the last tag:

```
make changelog
```

This writes to:

```
CHANGELOG.md
```

---

## 7. Safety Checks

All release targets run tests before building.  
If tests fail, the release is aborted.

---

## 8. Troubleshooting

### Missing API tokens
Ensure these are set in GitHub Secrets:

- `PYPI_API_TOKEN`
- `TEST_PYPI_API_TOKEN`

### Local environment issues
Try cleaning:

```
rm -rf build dist *.egg-info
```

### Version mismatch
Ensure version is only defined in:

```
textfsmgen/__init__.py
```

---

## 9. Summary

Your release workflow is:

### Test release:
```
make release-test-auto-minor
```

### Real release:
```
make release-auto-minor
```

### CI/CD release:
Push a tag:
```
git tag v0.7.0
git push --tags
```

This triggers GitHub Actions to publish to PyPI.
```