# Release Guide (Developer Documentation)

This document describes the internal release process for maintainers of
`textfsmgen`. It complements the public release checklist and provides deeper
context for versioning, tagging, and CI/CD behavior.

## Versioning Strategy

`textfsmgen` follows **Semantic Versioning**:

- **MAJOR** – breaking changes
- **MINOR** – new features, no breaking changes
- **PATCH** – bug fixes only

## Release Flow

1. Ensure the working tree is clean.
2. Run full test suite (pytest + golden tests).
3. Build documentation with `mkdocs build --strict`.
4. Update `CHANGELOG.md`.
5. Run `bump2version` with the appropriate level.
6. Push commit and tag.
7. Verify TestPyPI and PyPI publishing.
8. Publish GitHub Release notes.

## CI/CD Behavior

- Tags trigger PyPI publishing via OIDC Trusted Publishing.
- Docs deploy automatically to GitHub Pages.
- Golden tests run on every PR and release.

## Notes

This document is for maintainers only. Public-facing release notes belong in the
GitHub Release UI.