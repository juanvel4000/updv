from datetime import UTC, datetime
from pathlib import Path

import pytest

from updv.engine import process_config, process_file, substitute
from updv.parser import Configuration


@pytest.fixture
def example_file(tmp_path: Path) -> Path:
    p = Path(tmp_path / "VERSION")
    _ = p.write_text("0.0.0")
    return p


@pytest.fixture
def config(tmp_path: Path, example_file: Path) -> Configuration:
    VALID_TOML = f"""
    [project]
    name = "updv"
    version = "0.1.0"
    previous_version = "0.0.0"

    [project.files.version]
    path = "{example_file!s}"
    on-missing-file = "fail"
    on-no-match = "fail"
    enabled = true
    pattern = '{{old}}'
    replacement = '{{new}}'

    [project.files.invalid]
    path = "{tmp_path}/does_not_exist"
    on-missing-file = "skip"
    on-no-match = "fail"
    enabled = true
    pattern = '{{old}}'
    replacement = '{{new}}'
    """

    p = Path(tmp_path / "updv.toml")
    _ = p.write_text(VALID_TOML)
    return Configuration.from_toml(p)


def test_process_config(config: Configuration):
    res = process_config(config)
    assert res[0].status == "updated"


def test_process_file(config: Configuration):
    fd = config.files[0]
    assert (
        process_file(
            "0.1.0",
            fd,
            old="0.0.0",
            new="0.1.0",
            name="updv",
            date=datetime.now(UTC).strftime("%Y-%m-%d"),
        ).status
        == "updated"
    )


def test_process_skipped(config: Configuration):
    fd = config.files[1]
    res = process_file(
        "0.1.0",
        fd,
        old="0.0.0",
        new="0.1.0",
        name="updv",
        date=datetime.now(UTC).strftime("%Y-%m-%d"),
    )
    assert res.status == "skipped"
    assert res.reason == "missing file"


def test_substitute():
    old = "0.0.0"
    new = "0.1.0"
    name = "updv"
    date = datetime.now(UTC).strftime("%Y-%m-%d")
    n = substitute("{old} {new} {name} {date}", old=old, new=new, name=name, date=date)
    assert n == f"{old} {new} {name} {date}"
