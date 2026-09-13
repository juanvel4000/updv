"""unit test for parser.py, assumes top-level updv.toml.example was not modified."""

import shutil
from pathlib import Path

import pytest
from packaging.version import InvalidVersion, Version

from updv.parser import Configuration


@pytest.fixture
def config(tmp_path):
    p = Path(tmp_path / "updv.toml")
    shutil.copy(Path(__file__).parent / "updv.toml.example", p)
    return Configuration.from_toml(p)


def test_load_config_file(config: Configuration):
    assert isinstance(config, Configuration)


def assert_valid_version(v: str):
    try:
        Version(v)
    except InvalidVersion:
        raise AssertionError(f"invalid version string: '{v}'")


def test_validate_config_file(config: Configuration):
    assert config.name == "updv"
    assert_valid_version(config.version)
    assert config.files is not None
