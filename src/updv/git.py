"""tiny helpers for git interaction"""

import subprocess
from datetime import UTC, datetime

from .engine import substitute
from .parser import Configuration


def git_tag(config: Configuration, message: str | None = None) -> None:
    """tag the updated version with git"""
    msg = message or f"v{config.version}"
    tag = "v" + config.version
    _ = subprocess.run(["git", "tag", "-a", tag, "-m", msg], check=True)


def git_commit_updates(config: Configuration, message: str | None = None) -> bool:
    """commit the version updates"""
    msg = (
        message
        or f"updv: update version values from {config.previous_version} to {config.version}"
    )
    date = datetime.now(UTC).strftime("%Y-%m-%d")

    paths = [
        substitute(
            str(file.path),
            old=config.previous_version,
            new=config.version,
            name=config.name,
            date=date,
        )
        for file in config.files
        if file.enabled and file.path is not None
    ]

    if paths:
        _ = subprocess.run(["git", "add", *paths], check=True)
        _ = subprocess.run(["git", "commit", "-m", msg], check=True)
        return True
    return False
