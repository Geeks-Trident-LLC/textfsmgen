# 📘 **Man Page Style: `textfsmgen tester`**

```
NAME
    textfsmgen tester - Golden test development and maintenance tool.

SYNOPSIS
    textfsmgen tester <command> [options] <args>

DESCRIPTION
    The tester CLI provides commands for creating, validating, regenerating,
    diffing, merging, and maintaining golden test cases.

COMMANDS
    run <case>
        Execute a full test run (build, parse, compare).

    quicktest <case>
        Fast validation without regeneration.

    regen <case>
        Regenerate derived files for a single case.

    diff <case>
        Show differences between expected and generated results.

    drift <case>
        Detect drift between authoritative and derived files.

    new <case>
        Create a new case scaffold.

    new-from-input --builder B --author A <case> <inputs>
        Create a case from input samples.

    copy <author> <src> <dst>
        Copy a case.

    duplicate <author> <src>
        Duplicate a case with auto-naming.

    batch-generate <root>
        Run generate on all cases under a directory.

    batch-regen <root>
        Regenerate all cases under a directory.

    batch-quicktest <root>
        Quicktest all cases under a directory.

    merge --author A <dst> <srcs...>
        Merge multiple integration cases.

    merge-review <dst> <srcs...>
        Preview a merge using <dst> as reference.

    merge-preview <srcs...>
        Preview a merge with auto-selected reference.

    merge-diff <srcs...>
        Diff merged expected_results against golden.

    identical <srcs...>
        Identify cases that produce identical results.

NOTES
    Use the tester CLI for day-to-day development.
    Use pytest for full-suite validation and CI.

```
