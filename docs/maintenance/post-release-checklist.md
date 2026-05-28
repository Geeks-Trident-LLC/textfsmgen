# Post-release checklist

## Immediately after tag

- [ ] Confirm GitHub Actions workflows completed successfully
  - [ ] Tests
  - [ ] Build (wheel + sdist)
  - [ ] Publish to TestPyPI (if configured)
  - [ ] Publish to PyPI
  - [ ] Docs deployment (GitHub Pages)

- [ ] Verify package on PyPI
  - [ ] Version is correct
  - [ ] Long description renders correctly
  - [ ] Project URLs are correct

- [ ] Verify documentation
  - [ ] Open docs site
  - [ ] Check navigation and search
  - [ ] Spot-check a few key pages (Quickstart, Usage, API)

## Communication

- [ ] Publish GitHub Release notes
- [ ] Update any pinned examples/snippets in README if needed
- [ ] Announce release (Slack, mailing list, etc., if applicable)

## Follow-up

- [ ] Create issues for any known limitations or deferred work
- [ ] Update ROADMAP.md if priorities changed
- [ ] Start next development cycle (e.g., bump to `0.7.1-dev` if you use dev versions)
