# contributing to updv

updv is maintained on [github](https://github.com/juanvel4000/updv) -- this document explains how to report bugs and send patches there.

## reporting bugs / requesting features

use the [issue tracker](https://github.com/juanvel4000/updv/issues). when filing a bug include

- your OS and updv version (`pip show updv`)
- steps to reproduce
- what you expected vs. what happened

## sending patches

1. fork the repo and make your changes on a branch
2. commit with a clear, scoped message (see "commit style" below)
3. open a pull request against `main`

## commit style

- one logical change per commit
- imperative, lowercase summary line (`add X`, not `Added X` or `adds X`) -- matches the existing log
- keep the summary under ~72 chars; use the body for anything that needs more explanation

## before submitting

- install dev dependencies: `pip install -e ".[dev]"`
- run the test suite: `pytest -v`
- if your change affects behavior, consider whether it needs a test (see `tests/`) or a CHANGELOG.md entry under `[Unreleased]`

## code style

- Python >=3.11, type hints expected on public functions
- see existing code for naming conventions (`snake_case`, docstrings on modules/classes.)
- format/lint with `ruff format` and `ruff check` before submitting

## license

by contributing, you agree your changes are licensed under BSD-3-Clause, matching the rest of the project (see LICENSE).
