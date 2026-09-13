"""parse and read config files"""

import tomllib
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any

from packaging.version import Version


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
    def from_dict(cls, name: str, d: dict[str, Any]) -> "FileDescriptor":
        """initialize a FileDescriptor instance from a dict"""

        if "path" not in d:
            raise ValueError(f"'path' key not found in files['{name}']")

        if not isinstance(d.get("path"), (str, Path)):
            raise TypeError(f"files['{name}']['path'] is not a Path or str.")
        return cls(
            name=name,
            path=Path(d["path"]),
            on_no_match=OnNoMatch(d.get("on-no-match", "skip")),
            on_missing_file=OnMissingFile(d.get("on-missing-file", "skip")),
            line=int(d.get("line", 0)),
            enabled=bool(d.get("enabled", True)),
            pattern=str(d.get("pattern", "")),
            replacement=str(d.get("replacement", "")),
        )


@dataclass
class Configuration:
    """represents a updv configuration file"""

    name: str = ""
    version: str = "0.1.0"
    previous_version: str = "0.0.0"

    files: list[FileDescriptor] = field(default_factory=list)

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
            previous_version=proj.get("previous_version", "0.0.0"),
            files=[FileDescriptor.from_dict(k, item) for k, item in files.items()],
        )


def compute_bump(
    version: str = "0.1.0",
    bump_amount: int = 1,
    bump_type: str = "minor",
    zero_lower: bool = True,
) -> str:
    v = Version(version)

    major = v.major
    minor = v.minor
    patch = v.micro

    type = bump_type.strip().lower()
    if type not in ["major", "minor", "patch"]:
        raise ValueError(f"{bump_type} is not one of: major, minor, patch")

    match type:
        case "major":
            major += bump_amount
            if zero_lower:
                minor = 0
                patch = 0
        case "minor":
            minor += bump_amount
            if zero_lower:
                patch = 0
        case "patch":
            patch += bump_amount

    return f"{major}.{minor}.{patch}"
