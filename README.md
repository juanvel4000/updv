# updv

tiny version string updater written in python.

`updv` updates a version string across a project from a single version value, using a configurable `TOML`-based configuration file. this keeps version values in source files, package metadata, documentation, and other project files synchronized.

## features

- toml-based configuration (`.updv.toml`)
- simple `getopt`-based cli frontend
- update multiple files from a single version value
- configurable file creation and failure behavior
- templated paths, patterns, and replacements
- minimal runtime dependencies

## dependencies

updv requires at least

- a python 3.11 or newer interpreter

development dependencies include

- `pytest`: to execute the unit tests

## installation

clone the repository and install `updv` in editable mode.

```sh
python -m pip install -e .
```

## configuration

create a project configuration from the included example:

```sh
cp updv.toml.example .updv.toml
```

edit `.updv.toml` to define which files and version values updv should update.

> example `.updv.toml`:
>
> ```toml
> [project]
> name = "hello"
> version = "0.0.0"
> previous_version = "0.0.0"
>
> [project.files.initpy]
> path = "src/{name}/__init__.py"
> on-missing-file = "fail"
> on-no-match = "fail"
> enabled = true
>
> pattern = "__version__ = \"{old}\""
> replacement = "__version__ = \"{new}\""
>
> [project.files.changelog]
> path = "CHANGELOG.md"
> on-missing-file = "fail"
> on-no-match = "skip"
> enabled = true
>
> pattern = "## \\[Unreleased\\]"
> replacement = "## [{new}] - {date}"
>
> [project.files.version]
> path = "VERSION"
> on-missing-file = "create"
> on-no-match = "write"
> enabled = true
>
> pattern = "{old}"
> replacement = "{new}"
> ```
>
> paths, patterns, and replacements support project and version variables such as `{old}`, `{new}`, `{version}`, `{name}`, and `{date}`.

### policies

`on-missing-file`

- `create`: create an empty file
- `skip`: skip the file
- `fail`: fail with an error

`on-no-match`

- `append`: append the replacement to the file
- `prepend`: prepend the replacement to the file
- `write`: overwrite the file with the replacement
- `skip`: skip the file
- `fail`: fail with an error

## usage

```sh
updv -n 0.2.0 # updates version values to 0.2.0
updv -h # view all available cmd options
```

## testing

running the test suite can be done with `pytest`

```sh
pip install -e ".[dev]" # install dev dependencies
pytest -vs . # run the unit tests
```

## project status

updv is in active development. while functional, it is **not yet production-ready** for real-world usage.

- [CHANGELOG.md](CHANGELOG.md) -- release history
- [CONTRIBUTING.md](CONTRIBUTING.md) -- how to report bugs and send patches

## license

BSD-3-Clause, see [LICENSE](LICENSE)
