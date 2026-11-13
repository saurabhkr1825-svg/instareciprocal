"""Run Phase 2 comparison from a Phase 1 import JSON file."""

from __future__ import annotations

import argparse
import sys

from .comparator import (
    compare_accounts, load_import, load_whitelist, save_reports,
)
from .parser import InstagramExportError


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="instareciprocal-compare",
        description="Compare followers and following from a local Instagram export.",
    )
    parser.add_argument("--input", required=True, help="Phase 1 phase1-import.json")
    parser.add_argument("--whitelist", default="data/whitelist.json",
                        help="JSON array of protected usernames")
    parser.add_argument("--output-dir", default="exports",
                        help="Directory for JSON and CSV reports")
    args = parser.parse_args()

    try:
        imported = load_import(args.input)
        whitelist = load_whitelist(args.whitelist)
        result = compare_accounts(imported, whitelist)
        json_path, csv_path = save_reports(result, args.output_dir)
    except (OSError, ValueError, ImportError) as exc:
        print(f"Comparison failed: {exc}", file=sys.stderr)
        return 2

    print("Comparison completed.")
    print(f"Followers: {result.followers_count}")
    print(f"Following: {result.following_count}")
    print(f"Mutual: {len(result.mutual)}")
    print(f"Not following back: {len(result.not_following_back)}")
    print(f"Protected by whitelist: {len(result.protected)}")
    print(f"Needs review: {len(result.review_queue)}")
    print(f"JSON report: {json_path}")
    print(f"CSV report: {csv_path}")
    print("No Instagram actions were performed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
