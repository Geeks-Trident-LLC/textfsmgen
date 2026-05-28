# Python API Reference

This page provides an overview of the Python API exposed by `textfsmgen`. It is
intended for developers who want to integrate the library directly into their
applications or automation workflows.

## Overview

`textfsmgen` exposes a set of builder, runner, and workflow utilities that allow
you to:

- Load and execute builders programmatically
- Generate golden tests
- Validate workflow steps
- Produce JSON workflow metadata
- Run CLI-equivalent operations from Python

## Basic Usage

```python
import textfsmgen
```