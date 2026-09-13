"""core updv engine"""

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from .parser import Configuration, FileDescriptor, OnMissingFile, OnNoMatch


@dataclass
class ProcessResult:
    """represents the result of a file process"""

    path: Path
    status: Literal["updated", "skipped", "error"]
    reason: str = ""
    matches: int = 0

    @classmethod
    def error(cls, path: Path, reason: str) -> "ProcessResult":
        return cls(path, "error", reason=reason)

    @classmethod
    def updated(cls, path: Path, reason: str, matches: int) -> "ProcessResult":
        return cls(path, "updated", reason=reason, matches=matches)

    @classmethod
    def skipped(cls, path: Path, reason: str) -> "ProcessResult":
        return cls(path, "skipped", reason=reason)


def substitute(template: str, *, old: str, new: str, name: str, date: str) -> str:
    return (
        template.replace("{old}", old)
        .replace("{new}", new)
        .replace("{name}", name)
        .replace("{date}", date)
    )


def process_file(
    version: str, fd: FileDescriptor, old: str, new: str, name: str, date: str
) -> ProcessResult:
    """process and write the new version to a file"""
    matches = 0
    path = Path(substitute(str(fd.path), old=old, new=new, name=name, date=date))
    if not fd.enabled:
        return ProcessResult.skipped(path, f"{fd.name} is disabled")

    if not path.exists():
        match fd.on_missing_file:
            case OnMissingFile.SKIP:
                return ProcessResult.skipped(path, "missing file")
            case OnMissingFile.FAIL:
                return ProcessResult.error(path, "missing file")
            case OnMissingFile.CREATE:
                path.touch()

    txt = path.read_text()
    if fd.line:
        lines = txt.splitlines(keepends=True)
        if txt == "":
            return ProcessResult.error(path, "cannot use 'line' if file is empty")
        if not (1 <= fd.line <= len(lines)):
            return ProcessResult.error(path, f"line {fd.line} out of range")

        lines[fd.line - 1] = version + "\n"
        _ = path.write_text("".join(lines))
        matches = 1
    else:
        pattern = substitute(fd.pattern, old=old, new=new, name=name, date=date)
        replacement = substitute(fd.replacement, old=old, new=new, name=name, date=date)

        new_text, n = re.subn(pattern, replacement, txt)
        if n == 0:
            match fd.on_no_match:
                case OnNoMatch.FAIL:
                    return ProcessResult.error(path, "match not found")
                case OnNoMatch.SKIP:
                    return ProcessResult.skipped(path, "match not found")
                case OnNoMatch.APPEND:
                    new_text = txt + "\n" + replacement
                case OnNoMatch.PREPEND:
                    new_text = replacement + "\n" + txt
                case OnNoMatch.WRITE:
                    new_text = replacement
        _ = path.write_text(new_text)
        matches = n

    return ProcessResult.updated(path, "succeeded", matches=matches)


def process_config(
    config: Configuration, verbose: bool = False, dryrun: bool = False
) -> list[ProcessResult]:
    """process all files under Configuration"""
    old = config.previous_version
    new = config.version
    name = config.name
    date = datetime.now(UTC).strftime("%Y-%m-%d")

    res = []
    for fd in config.files:
        if verbose:
            print(f"processing {fd.name}")
        if not dryrun:
            r = process_file(config.version, fd, old, new, name, date)
            res.append(r)
            if verbose:
                print(f"{fd.name}: {r.status}: {r.reason} ({r.matches})")
        else:
            print(
                f"dry run: would update {substitute(str(fd.path), old=old, new=new, name=name, date=date)}"
            )
    return res
