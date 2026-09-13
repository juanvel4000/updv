"""parse and read config files"""

import tomllib
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path


class OnNoMatch(StrEnum):
    SKIP = "skip"
    APPEND = "append"
    PREPEND = "prepend"
    WRITE = "write"
    FAIL = "fail"


class OnMissingFile(StrEnum):
    SKIP = "skip"
    CREATE = "create"
    FAIL = "fail"


@dataclass
class FileDescriptor:
    """represents a target file configuration"""

    name: str = ""
    path: Path | None = None
    on_no_match: OnNoMatch = OnNoMatch.SKIP
    on_missing_file: OnMissingFile = OnMissingFile.SKIP
    line: int = 0
    enabled: bool = True

    pattern: str = ""
    replacement: str = ""

    @classmethod
    def from_dict(cls, name: str, d: dict[str, str | int]) -> "FileDescriptor":
        """initialize a FileDescriptor instance from a dict"""
        return cls(
            name=name,
            path=Path(d.get("path")),
            on_no_match=OnNoMatch(d.get("on-no-match")),
            on_missing_file=OnMissingFile(d.get("on-missing-file")),
            line=d.get("line", 0),
            enabled=d.get("enabled", True),
            pattern=d.get("pattern"),
            replacement=d.get("replacement"),
        )


@dataclass
class Configuration:
    """represents a updv configuration file"""

    name: str = ""
    version: str = "0.1.0"

    files: list[FileDescriptor] | None = None

    @classmethod
    def from_toml(cls, path: Path | str) -> "Configuration":
        """initialize a Configurator instance from a toml file"""
        path = Path(path)
        with path.open("rb") as fp:
            data = tomllib.load(fp)

        proj = data.get("project", {})
        files = proj.get("files", {})

        return cls(
            name=proj.get("name", "updv"),
            version=proj.get("version", "0.1.0"),
            files=[FileDescriptor.from_dict(k, item) for k, item in files.items()],
        )
