"""Command-line entry point for Phase 1 imports."""

from __future__ import annotations

import argparse
import sys

from .importer import import_instagram_export, save_import
from .parser import InstagramExportError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="instareciprocal",
        description="Import Instagram followers/following JSON exports locally.",
    )
    parser.add_argument("--input", required=True, help="Instagram export ZIP or extracted folder")
    parser.add_argument("--output", default="exports/phase1-import.json",
                        help="Output JSON path (default: exports/phase1-import.json)")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        result = import_instagram_export(args.input)
        output = save_import(result, args.output)
    except InstagramExportError as exc:
        print(f"Import failed: {exc}", file=sys.stderr)
        return 2

    print("Import completed.")
    print(f"Followers: {result.follower_count}")
    print(f"Following: {result.following_count}")
    print(f"Saved: {output}")
    print("Note: These counts reflect the export snapshot, not live Instagram data.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
