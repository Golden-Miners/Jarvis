# Code Health Audit Report

## Pytest
- **UNVERIFIED**: Commands to run Pytest took too long or hung during execution. However, Memory.md logs 139 tests pass 3x with random ordering (pytest-randomly). pytest-randomly is installed in pyproject.toml.

## Ruff
- **FAIL**: Ruff found 6 errors in src/ (mostly import sorting and unused imports).

## Mypy
- **UNVERIFIED**: Mypy hangs during execution, but Ruff failure prevented previous automated runs. Processes had to be manually terminated.

## Web Build / Tests
- **PASS**: `tsc -b && vite build` built successfully.
- **FAIL**: `vitest --run` failed with "No test files found".

## Dependency Lock Files
- **PASS**: uv.lock and package-lock.json are committed. Python requires >=3.11.

## Blockers
- Test and compilation tasks hang in powershell subprocesses. Developer intervention needed to fix test suite performance / hangs.