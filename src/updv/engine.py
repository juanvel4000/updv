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

    descriptor: FileDescriptor
    path: Path
    status: Literal["updated", "skipped", "error"]
    reason: str = ""
    matches: int = 0

    @classmethod
    def error(
        cls, path: Path, reason: str, descriptor: FileDescriptor
    ) -> "ProcessResult":
        return cls(descriptor, path, "error", reason=reason)

    @classmethod
    def updated(
        cls, path: Path, reason: str, matches: int, descriptor: FileDescriptor
    ) -> "ProcessResult":
        return cls(descriptor, path, "updated", reason=reason, matches=matches)

    @classmethod
    def skipped(
        cls, path: Path, reason: str, descriptor: FileDescriptor
    ) -> "ProcessResult":
        return cls(descriptor, path, "skipped", reason=reason)


def path_resolve(path: Path, config: Configuration) -> Path:
    old = config.previous_version
    new = config.version
    name = config.name
    date = datetime.now(UTC).strftime("%Y-%m-%d")
    return Path(
        substitute(
            str(path), old=old, new=new, name=name, date=date, **config.extra_vars
        )
    )


def substitute(
    template: str, *, old: str, new: str, name: str, date: str, **extra
) -> str:
    values = {"old": old, "new": new, "name": name, "date": date, **extra}
    for key, val in values.items():
        template = template.replace(f"{{{key}}}", val)
    return template


def process_file(
    version: str,
    fd: FileDescriptor,
    old: str,
    new: str,
    name: str,
    date: str,
    extra: dict[str, str] | None = None,
) -> ProcessResult:
    """process and write the new version to a file"""
    extra = extra or {}
    matches = 0
    note = "succeeded"
    path = Path(
        substitute(str(fd.path), old=old, new=new, name=name, date=date, **extra)
    )
    if not fd.enabled:
        return ProcessResult.skipped(path, f"{fd.name} is disabled", fd)

    if not path.exists():
        match fd.on_missing_file:
            case OnMissingFile.SKIP:
                return ProcessResult.skipped(path, "missing file", fd)
            case OnMissingFile.FAIL:
                return ProcessResult.error(path, "missing file", fd)
            case OnMissingFile.CREATE:
                note += f"file {path!s} was created\n"
                path.touch()

    txt = path.read_text()
    if fd.line:
        lines = txt.splitlines(keepends=True)
        if txt == "":
            return ProcessResult.error(path, "cannot use 'line' if file is empty", fd)
        if not (1 <= fd.line <= len(lines)):
            return ProcessResult.error(path, f"line {fd.line} out of range", fd)

        lines[fd.line - 1] = version + "\n"
        _ = path.write_text("".join(lines))
        matches = 1
    else:
        pattern = substitute(
            fd.pattern, old=old, new=new, name=name, date=date, **extra
        )
        replacement = substitute(
            fd.replacement, old=old, new=new, name=name, date=date, **extra
        )

        new_text, n = re.subn(pattern, replacement, txt)
        if n == 0:
            match fd.on_no_match:
                case OnNoMatch.FAIL:
                    return ProcessResult.error(path, "match not found", fd)
                case OnNoMatch.SKIP:
                    return ProcessResult.skipped(path, "match not found", fd)
                case OnNoMatch.APPEND:
                    note += "used append\n"
                    new_text = txt + "\n" + replacement
                case OnNoMatch.PREPEND:
                    note += "used prepend\n"
                    new_text = replacement + "\n" + txt
                case OnNoMatch.WRITE:
                    new_text = replacement
        _ = path.write_text(new_text)
        matches = n

    return ProcessResult.updated(path, note, matches, fd)


def process_config(
    config: Configuration,
    verbose: bool = False,
    dryrun: bool = False,
    quiet: bool = False,
) -> tuple[list[ProcessResult], bool]:
    """process all files under Configuration"""
    old = config.previous_version
    new = config.version
    name = config.name
    date = datetime.now(UTC).strftime("%Y-%m-%d")
    res = []
    snapshots = {}
    rollback = False
    for fd in config.files:
        if not fd.enabled:
            continue
        path = path_resolve(fd.path, config)
        if verbose and not quiet:
            print(f"taking snapshot of {path}")
        if not dryrun and path.exists():
            snapshots[path] = path.read_text()
        else:
            if not quiet:
                print("dry run: skipping snapshot")

    for fd in config.files:
        if verbose and not quiet:
            print(f"processing {fd.name}")
        if not dryrun:
            r = process_file(
                config.version, fd, old, new, name, date, config.extra_vars
            )
            if not quiet and not verbose:
                match r.status:
                    case "updated":
                        print(
                            f" \033[34m>\033[0m \033[32m\033[1mDONE\033[0m\033[1m {r.descriptor.name}\033[0m \033[4m({r.path})\033[0m"
                        )
                    case "error":
                        print(
                            f" \033[34m>\033[0m \033[31m\033[1mFAIL\033[0m\033[1m {r.descriptor.name}\033[0m \033[4m({r.path})\033[0m: {r.reason}"
                        )
                    case "skipped":
                        print(
                            f" \033[34m>\033[0m \033[36m\033[1mSKIP\033[0m\033[1m {r.descriptor.name}\033[0m \033[4m({r.path})\033[0m"
                        )

            res.append(r)
            if r.status == "error":
                if verbose and not quiet:
                    print(f"{fd.name} failed, running rollback on all files.")
                if not quiet and not verbose:
                    print(f" \033[34m>\033[0m \033[35m\033[1mROLLBACK\033[0m")
                rollback = True
                break
            if verbose and not quiet:
                matches = "match" if r.matches == 1 else "matches"
                print(f"{fd.name}: {r.status}: {r.reason} ({r.matches} {matches})")
        else:
            if verbose and not quiet:
                print(
                    f"{fd.name}: dry run: would update {path_resolve(fd.path, config)}"
                )
    if rollback and not dryrun:
        for fd in config.files:
            path = path_resolve(fd.path, config)
            if verbose and not quiet:
                print(f"running rollback on {fd.name} ({path})")
            _ = path.write_text(snapshots[path])

    return res, rollback
