# Release Checklist for textfsmgen

## Pre‑release
- [ ] Review commit history since last tag
- [ ] Ensure all tests pass (pytest + golden tests)
- [ ] Ensure documentation builds cleanly (`mkdocs build --strict`)
- [ ] Update CHANGELOG with new version section
- [ ] Confirm version bump target (patch/minor/major)

## Version bump
- [ ] Run: bump2version --new-version 0.7.0 minor
- [ ] Verify version updated in textfsmgen/__init__.py
- [ ] Verify bump2version created a commit and tag

## GitHub Actions
- [ ] Push commit and tag (`git push && git push --tags`)
- [ ] Confirm TestPyPI publish succeeded
- [ ] Confirm PyPI publish succeeded
- [ ] Confirm GitHub Release draft generated (if enabled)

## Documentation
- [ ] Confirm GitHub Pages deployment succeeded
- [ ] Verify docs render correctly on the site

## Post‑release
- [ ] Publish GitHub Release notes
- [ ] Announce release (optional)
- [ ] Start next development cycle
