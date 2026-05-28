# Release Maintenance Guide

This document describes how to maintain releases after they are published,
including patch releases, backports, and regression handling.

## Patch Releases

Patch releases should be created when:

- A bug fix is required
- No breaking changes are introduced
- No new features are added

Flow:

1. Create a branch from the latest tag.
2. Apply the fix.
3. Update `CHANGELOG.md`.
4. Run `bump2version patch`.
5. Push commit and tag.
6. Verify PyPI publishing.

## Backports

If a fix must be applied to an older version:

1. Create a branch from the older tag.
2. Apply the fix manually.
3. Bump patch version.
4. Publish as usual.

## Regression Handling

If a release introduces a regression:

- Document the issue clearly.
- Prioritize a patch release.
- Add a regression test to prevent recurrence.

## Long-Term Maintenance

- Keep dependencies updated.
- Periodically review CI workflows.
- Ensure docs remain accurate after major changes.

This guide is for maintainers only.