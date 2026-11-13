"""Username normalization helpers."""

from __future__ import annotations

import re
from urllib.parse import urlparse, unquote

_USERNAME_RE = re.compile(r"^[a-zA-Z0-9._]{1,30}$")


def normalize_username(raw: object) -> str | None:
    """Return a canonical lowercase username, or None for unusable input.

    Accepts a username or an Instagram profile URL. Display names and arbitrary
    strings are deliberately rejected rather than guessed.
    """
    if raw is None:
        return None

    value = unquote(str(raw)).strip()
    if not value:
        return None

    if value.startswith("@"):
        value = value[1:]

    if "://" in value:
        parsed = urlparse(value)
        host = (parsed.hostname or "").lower()
        if host not in {"instagram.com", "www.instagram.com"}:
            return None
        parts = [part for part in parsed.path.split("/") if part]
        if not parts:
            return None
        value = parts[0]

    value = value.strip().strip("/")
    if value.lower() in {"instagram.com", "www.instagram.com", "accounts", "explore", "direct", "reels", "stories", "p"}:
        return None
    if not _USERNAME_RE.fullmatch(value):
        return None

    return value.lower()
