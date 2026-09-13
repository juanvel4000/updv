"""functions for the cli frontend"""

import sys
from getopt import GetoptError, getopt
from importlib.metadata import version
from pathlib import Path

from packaging.version import InvalidVersion

from .engine import process_config
from .git import git_commit_updates, git_tag
from .parser import Configuration, compute_bump


def print_error(
    s: str,
) -> None:
    print(s, file=sys.stderr)


def print_usage() -> None:
    print(
        "usage: updv [-vVxhgz] [-c file] [-n version] [-b type] [-a amount]",
        file=sys.stderr,
    )


def print_help() -> None:
    print("updv - version string updater")
    print_usage()
    print("options:")
    print(f"  {'-V':<10} {'print the updv version'}")
    print(f"  {'-h':<10} {'show this message'}")
    print(f"  {'-v':<10} {'show detailed output'}")
    print(f"  {'-d':<10} {'enable dry run mode'}")
    print(f"  {'-x':<10} {'skip running the updv engine'}")
    print(f"  {'-g':<10} {'commit and tag the version with git'}")
    print(f"  {'-b':<10} {'bump a section of the version tag'}")
    print(f"  {'-z':<10} {'set everything lower to zero with bump'}")
    print(f"  {'-a amount':<10} {'the amount to add with bump'}")
    print(f"  {'-c file':<10} {'specify a config file'}")
    print(f"  {'-n version':<10} {'update version string in the config file'}")


def get_config(config: Path | None = None) -> Path:
    if config:
        if config.is_file():
            return config
        else:
            print_error(f"error: {config} not found")
            sys.exit(1)

    options = [
        Path("updv.toml"),
        Path(".updv.toml"),
        Path("updv.config"),
        Path(".updv.config"),
    ]

    for fil in options:
        if fil.is_file():
            return fil

    print_error("could not find a valid updv.toml")
    sys.exit(1)


def run_engine(
    config: Configuration, verbose: bool = False, dryrun: bool = False
) -> None:
    _ = process_config(config, verbose, dryrun)


def vprint(s: str, verbose: bool = False) -> None:
    if verbose:
        print(s)


def update_version(
    cfg: Path, newver: str, dryrun: bool = False, verbose: bool = False
) -> None:
    """naive method to update the version string, blindly assumes the config file is proper TOML"""
    vprint(f"reading config file: {cfg}", verbose)
    config = Configuration.from_toml(cfg)
    if config.version == newver:
        print_error("new version cannot be the same as the current one.")
        sys.exit(1)

    txt = cfg.read_text()
    old = txt
    vprint(f"updating version strings in {cfg}", verbose)
    txt = txt.replace(f'version = "{config.version}"', f'version = "{newver}"')
    vprint(f"updating previous_version strings in {cfg}", verbose)
    txt = txt.replace(
        f'previous_version = "{config.previous_version}"',
        f'previous_version = "{config.version}"',
    )
    oldver = config.version

    if not dryrun:
        vprint(f"writing to {cfg}", verbose)
        _ = cfg.write_text(txt)
    else:
        print(f"dry run: would edit {cfg}")

    if not dryrun:
        vprint(f"verifying {cfg}")
        config = Configuration.from_toml(cfg)
        if config.version != newver:
            vprint(f"attempting to rollback {cfg}")
            _ = cfg.write_text(old)
            print_error("updv: update_version failed")
            sys.exit(1)

        if config.previous_version != oldver:
            vprint(f"attempting to rollback {cfg}")
            _ = cfg.write_text(old)
            print_error("updv: update_version failed")
            sys.exit(1)
    else:
        print("dry run: skipped verification")


def run_bump(
    cfg: Path,
    version: str = "0.1.0",
    bump_type: str = "minor",
    bump_amount: int = 1,
    zero_lower: bool = False,
    dryrun: bool = False,
    verbose: bool = False,
) -> None:
    """wrapper around parser.compute_bump"""
    vprint("running compute_bump", verbose)
    try:
        v = compute_bump(version, bump_amount, bump_type, zero_lower)
        vprint(f"got {v}", verbose)
    except InvalidVersion:
        print_error(f"invalid version string: '{version}'")
        sys.exit(1)
    update_version(cfg, v, dryrun, verbose)


def main():
    verbose = False
    dryrun = False
    config = None
    newver = None
    cfg = None
    argv = sys.argv[1:]
    argc = len(argv)
    run = True
    git = False
    bump = False
    bump_type = "minor"
    bump_amount = 1
    zero_lower = False

    if argc == 0:
        print_usage()
        sys.exit(1)

    try:
        opts, _ = getopt(argv, "vVhdxgzc:n:b:a:")
    except GetoptError as exc:
        print(f"updv: {exc}", file=sys.stderr)
        print_usage()
        sys.exit(1)

    for opt in opts:
        match opt[0]:
            case "-V":
                print(f"updv {version('updv')}")
                sys.exit(0)
            case "-v":
                verbose = True
            case "-h":
                print_help()
                sys.exit(0)
            case "-c":
                cfg = Path(opt[1])
            case "-n":
                newver = opt[1]
            case "-d":
                dryrun = True
            case "-x":
                run = False
            case "-g":
                git = True
            case "-b":
                bump = True
                bump_type = opt[1] or "minor"
            case "-a":
                bump_amount = opt[1]
            case "-z":
                zero_lower = True
            case _:
                print_usage()
                sys.exit(1)
    cfg = get_config(cfg)
    if newver:
        update_version(cfg, newver, dryrun, verbose)
    config = Configuration.from_toml(cfg)
    if bump:
        run_bump(
            cfg,
            config.version,
            bump_type,
            int(bump_amount),
            zero_lower,
            dryrun,
            verbose,
        )
        config = Configuration.from_toml(cfg)
    if run:
        run_engine(config, verbose, dryrun)
    if git and git_commit_updates(config):
        git_tag(config)
    sys.exit(0)
