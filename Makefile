.PHONY: clean deep-clean

clean:
    rm -rf build dist *.egg-info

deep-clean:
    rm -rf build dist *.egg-info
    python clean.py


# Run tests
test:
    pytest

# Run tox (all environments)
tox:
    tox

# Build package (wheel + sdist)
build: clean
    python -m build

# Upload to TestPyPI
upload-test:
    twine upload --repository testpypi dist/*

# Upload to PyPI
upload:
    twine upload dist/*

# Full release workflow
release: test build upload

# Upload to TestPyPI
upload-test:
    twine upload --repository testpypi dist/*

# Full TestPyPI release workflow
release-test: test build upload-test

# -----------------------------
# Version bumping
# -----------------------------

bump-patch:
    bump2version patch

bump-minor:
    bump2version minor

bump-major:
    bump2version major


# -----------------------------
# Combined bump + release
# -----------------------------

release-patch: bump-patch release
release-minor: bump-minor release
release-major: bump-major release

release-test-patch: bump-patch release-test
release-test-minor: bump-minor release-test
release-test-major: bump-major release-test


# -----------------------------
# Git tagging helpers
# -----------------------------

tag:
    git tag v$(shell python -c "import textfsmgen; print(textfsmgen.__version__)")
    git push --tags

push:
    git push


# Full automated release pipeline
release-auto-patch: bump-patch release tag push
release-auto-minor: bump-minor release tag push
release-auto-major: bump-major release tag push


changelog:
    git log --pretty=format:"* %s" v$$(git describe --tags --abbrev=0 --tags --match "v*")..HEAD > CHANGELOG.md

check:
    pytest

release: check build upload
release-test: check build upload-test

