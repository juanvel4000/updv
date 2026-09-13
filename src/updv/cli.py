"""functions for the cli frontend"""

import sys
from getopt import GetoptError, getopt
from importlib.metadata import version
from pathlib import Path

from .engine import process_config
from .parser import Configuration


def print_error(
    s: str,
) -> None:
    print(s, file=sys.stderr)


def print_usage() -> None:
    print("usage: updv [-vVxh] [-c file] [-n version]", file=sys.stderr)


def print_help() -> None:
    print("updv - version string updater")
    print_usage()
    print("options:")
    print(f"  {'-V':<10} {'print the updv version'}")
    print(f"  {'-h':<10} {'show this message'}")
    print(f"  {'-v':<10} {'enable detailed output'}")
    print(f"  {'-x':<10} {"don't run the updv engine"}")
    print(f"  {'-c file':<10} {'specify a config file'}")
    print(f"  {'-n version':<10} {'update version string in the config file'}")


def get_config(config: Path | None = None) -> Path:
    if config:
        if config.is_file():
            try:
                return config
            except Exception as exc:
                print_error(f"error: {exc}")
                sys.exit(1)
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
            try:
                return fil
            except Exception as exc:
                print_error(f"error: {exc}")
                sys.exit(1)

    print_error("could not find a valid updv.toml")
    sys.exit(1)


def run_engine(config: Configuration, verbose: bool = False) -> None:
    _ = process_config(config, verbose)


def update_version(cfg: Path, newver: str) -> None:
    """duct tape to update the version string, blindly assumes the config file is proper TOML"""
    config = Configuration.from_toml(cfg)
    txt = cfg.read_text()
    txt = txt.replace(f'version = "{config.version}"', f'version = "{newver}"')
    txt = txt.replace(
        f'previous_version = "{config.previous_version}"',
        f'previous_version = "{config.version}"',
    )
    oldver = config.version

    cfg.write_text(txt)
    config = Configuration.from_toml(cfg)
    if not config.version == newver:
        print_error("updv: update_version failed")
        sys.exit(1)

    if not config.previous_version == oldver:
        print_error("updv: update_version failed")
        sys.exit(1)


def main():
    verbose = False
    config = None
    newver = None
    cfg = None
    argv = sys.argv[1:]
    argc = len(argv)
    run = True
    if argc == 0:
        print_usage()
        sys.exit(1)

    try:
        opts, args = getopt(argv, "vVhxc:n:")
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

    config = get_config(cfg)
    if newver:
        update_version(config, newver)
    if run:
        run_engine(Configuration.from_toml(config), verbose)
    sys.exit(0)
