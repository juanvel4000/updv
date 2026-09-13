"""unit test for parser.py"""

from pathlib import Path

import pytest
from packaging.version import Version

from updv.parser import Configuration, OnMissingFile, OnNoMatch


@pytest.fixture
def config(tmp_path: Path):
    VALID_TOML = """
    [project]
    name = "updv"
    version = "0.1.0"
    previous_version = "0.0.0"

    [project.files.pyproject]
    path = "pyproject.toml"
    on-missing-file = "skip"
    on-no-match = "fail"
    enabled = true
    pattern = 'version = "{old}"'
    replacement = 'version = "{new}"'
    """

    p = Path(tmp_path / "updv.toml")
    _ = p.write_text(VALID_TOML)
    return Configuration.from_toml(p)


def test_parse_valid_config(config: Configuration):

    assert config.name == "updv"
    assert Version(config.version) == Version("0.1.0")
    assert Version(config.previous_version) == Version("0.0.0")
    assert len(config.files) == 1

    descriptor = config.files[0]
    assert descriptor.name == "pyproject"
    assert descriptor.path == Path("pyproject.toml")
    assert descriptor.on_missing_file == OnMissingFile.SKIP
    assert descriptor.on_no_match == OnNoMatch.FAIL
    assert descriptor.enabled is True
    assert descriptor.pattern == 'version = "{old}"'
    assert descriptor.replacement == 'version = "{new}"'


def test_missing_path_raises_value_error(tmp_path: Path):
    invalid_toml = """
    [project.files.invalid]
    enabled = true
    """
    p = tmp_path / "invalid.toml"
    _ = p.write_text(invalid_toml)

    with pytest.raises(ValueError, match="'path' key not found"):
        _ = Configuration.from_toml(p)
