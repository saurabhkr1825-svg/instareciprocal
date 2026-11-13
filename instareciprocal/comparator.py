"""Compare imported follower and following snapshots."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import csv
import json


@dataclass(frozen=True)
class ComparisonResult:
    imported_at: str
    followers_count: int
    following_count: int
    mutual: list[str]
    not_following_back: list[str]
    you_dont_follow_back: list[str]
    protected: list[str]
    review_queue: list[str]

    def to_dict(self) -> dict:
        return {
            "compared_at": datetime.now(timezone.utc).isoformat(),
            "source_imported_at": self.imported_at,
            "counts": {
                "followers": self.followers_count,
                "following": self.following_count,
                "mutual": len(self.mutual),
                "not_following_back": len(self.not_following_back),
                "you_dont_follow_back": len(self.you_dont_follow_back),
                "protected": len(self.protected),
                "review_queue": len(self.review_queue),
            },
            "mutual": self.mutual,
            "not_following_back": self.not_following_back,
            "you_dont_follow_back": self.you_dont_follow_back,
            "protected": self.protected,
            "review_queue": self.review_queue,
        }


def compare_accounts(import_data: dict, whitelist: set[str] | None = None) -> ComparisonResult:
    """Compare all accounts; whitelist only removes entries from review_queue."""
    whitelist = {name.strip().lstrip("@").lower() for name in (whitelist or set())}
    followers = {str(name).strip().lstrip("@").lower()
                 for name in import_data.get("followers", []) if str(name).strip()}
    following = {str(name).strip().lstrip("@").lower()
                 for name in import_data.get("following", []) if str(name).strip()}

    not_back = sorted(following - followers)
    protected = sorted(set(not_back) & whitelist)
    review_queue = sorted(set(not_back) - whitelist)

    return ComparisonResult(
        imported_at=import_data.get("imported_at", "unknown"),
        followers_count=len(followers),
        following_count=len(following),
        mutual=sorted(followers & following),
        not_following_back=not_back,
        you_dont_follow_back=sorted(followers - following),
        protected=protected,
        review_queue=review_queue,
    )


def load_import(path: str | Path) -> dict:
    with Path(path).expanduser().open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict) or not isinstance(data.get("followers"), list) or not isinstance(data.get("following"), list):
        raise ValueError("Import JSON must contain 'followers' and 'following' arrays.")
    return data


def load_whitelist(path: str | Path) -> set[str]:
    """Load a JSON array of usernames; a missing file means an empty whitelist."""
    file_path = Path(path).expanduser()
    if not file_path.exists():
        return set()
    with file_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, list) or not all(isinstance(item, str) for item in data):
        raise ValueError("Whitelist must be a JSON array of usernames.")
    return {item.strip().lstrip("@").lower() for item in data if item.strip()}


def save_whitelist(usernames: set[str], path: str | Path) -> Path:
    file_path = Path(path).expanduser()
    file_path.parent.mkdir(parents=True, exist_ok=True)
    normalized = sorted({item.strip().lstrip("@").lower() for item in usernames if item.strip()})
    file_path.write_text(json.dumps(normalized, indent=2), encoding="utf-8")
    return file_path


def save_reports(result: ComparisonResult, output_dir: str | Path) -> tuple[Path, Path]:
    directory = Path(output_dir).expanduser()
    directory.mkdir(parents=True, exist_ok=True)

    json_path = directory / "comparison-report.json"
    csv_path = directory / "comparison-report.csv"
    json_path.write_text(json.dumps(result.to_dict(), indent=2), encoding="utf-8")

    categories = {
        "mutual": result.mutual,
        "not_following_back": result.not_following_back,
        "you_dont_follow_back": result.you_dont_follow_back,
        "protected": result.protected,
        "review_queue": result.review_queue,
    }
    with csv_path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.writer(handle)
        writer.writerow(["username", "category"])
        for category, usernames in categories.items():
            writer.writerows((username, category) for username in usernames)

    return json_path, csv_path
