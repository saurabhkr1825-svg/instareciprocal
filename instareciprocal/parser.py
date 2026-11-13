"""Parsers for common Instagram followers/following JSON exports."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from .normalizer import normalize_username


class InstagramExportError(ValueError):
    """Raised when an Instagram export file cannot be parsed safely."""


def _extract_from_record(record: Any, *, following: bool) -> set[str]:
    found: set[str] = set()
    if not isinstance(record, dict):
        return found

    # Instagram exports commonly put the username in string_list_data[].value.
    string_data = record.get("string_list_data")
    if isinstance(string_data, list):
        for item in string_data:
            if isinstance(item, dict):
                username = normalize_username(item.get("value"))
                if username:
                    found.add(username)

    # Some export variants use title or username fields.
    for key in ("username", "value"):
        username = normalize_username(record.get(key))
        if username:
            found.add(username)

    # For following records, title is usually the account username.
    if following:
        username = normalize_username(record.get("title"))
        if username:
            found.add(username)

    return found


def _walk_records(data: Any, *, following: bool) -> set[str]:
    """Extract usernames from known list/dict structures without guessing keys."""
    found: set[str] = set()

    if isinstance(data, list):
        for item in data:
            found.update(_extract_from_record(item, following=following))
            if isinstance(item, (dict, list)):
                found.update(_walk_records(item, following=following))
        return found

    if isinstance(data, dict):
        # Following export commonly wraps records in relationships_following.
        preferred_keys = (
            ("relationships_following", "following")
            if following
            else ("relationships_followers", "followers")
        )
        for key in preferred_keys:
            if key in data:
                found.update(_walk_records(data[key], following=following))

        # Also support exports where the top-level object itself is a record.
        found.update(_extract_from_record(data, following=following))
        return found

    return found


def parse_json_file(path: Path, *, following: bool) -> set[str]:
    try:
        with path.open("r", encoding="utf-8-sig") as handle:
            payload = json.load(handle)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise InstagramExportError(f"Could not read valid JSON from {path.name}: {exc}") from exc

    usernames = _walk_records(payload, following=following)
    if not usernames:
        raise InstagramExportError(
            f"No usernames found in {path.name}. Check that this is an Instagram "
            "followers/following JSON export."
        )
    return usernames


def parse_json_text(text: str, *, following: bool, source_name: str = "input.json") -> set[str]:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise InstagramExportError(f"Invalid JSON in {source_name}: {exc}") from exc
    usernames = _walk_records(payload, following=following)
    if not usernames:
        raise InstagramExportError(f"No usernames found in {source_name}.")
    return usernames
