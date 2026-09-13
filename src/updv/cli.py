"""functions for the cli frontend"""

import os
import sys
from getopt import GetoptError, getopt
from importlib.metadata import version
from pathlib import Path

from updv.parser import Configuration


def print_error(
    s: str,
) -> None:
    print(s, file=sys.stderr)


def print_usage() -> None:
    print("usage: updv [-vVh] [-c file] [-n version]", file=sys.stderr)


def print_help() -> None:
    print("updv - version string updater")
    print_usage()
    print("options:")
    print(f"  {'-V':<10} {'print the updv version'}")
    print(f"  {'-h':<10} {'show this message'}")
    print(f"  {'-v':<10} {'enable detailed output'}")
    print(f"  {'-c file':<10} {'specify a config file'}")
    print(f"  {'-n version':<10} {'update version string in the config file'}")


def get_config(config: Path | None = None) -> Configuration:
    if config:
        if config.is_file():
            try:
                return Configuration.from_toml(config)
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
                return Configuration.from_toml(fil)
            except Exception as exc:
                print_error(f"error: {exc}")
                sys.exit(1)

    print_error("could not find a valid updv.toml")
    sys.exit(1)


def main():
    verbose = False
    config = None
    newver = None
    cfg = None
    argv = sys.argv[1:]
    argc = len(argv)
    if argc == 0:
        print_usage()
        sys.exit(1)

    try:
        opts, args = getopt(argv, "vVhc:n:")
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
    sys.exit(0)
