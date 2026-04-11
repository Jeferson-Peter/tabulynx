from __future__ import annotations

import argparse
from pathlib import Path

from tabulynx.viewer import launch_viewer


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tabulynx", description="Desktop spreadsheet viewer")
    subparsers = parser.add_subparsers(dest="command")

    open_parser = subparsers.add_parser("open", help="Open a file in the viewer")
    open_parser.add_argument("path", nargs="?", help="Path to a CSV, XLSX, or Parquet file")
    open_parser.add_argument("--sheet", help="Sheet name for XLSX files")

    parser.add_argument("path", nargs="?", help=argparse.SUPPRESS)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    path = None
    sheet = None
    if args.command == "open":
        path = args.path
        sheet = args.sheet
    elif getattr(args, "path", None):
        path = args.path

    if path:
        return launch_viewer(Path(path), sheet=sheet)
    return launch_viewer()


if __name__ == "__main__":
    raise SystemExit(main())
