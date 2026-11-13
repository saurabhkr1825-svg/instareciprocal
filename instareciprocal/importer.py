"""Load Instagram follower/following JSON files from a folder or ZIP archive."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from zipfile import BadZipFile, ZipFile
import json
import re

from .parser import InstagramExportError, parse_json_text

FOLLOWER_RE = re.compile(r"^followers(?:_\d+)?\.json$", re.IGNORECASE)
FOLLOWING_RE = re.compile(r"^following\.json$", re.IGNORECASE)


@dataclass(frozen=True)
class ImportResult:
    imported_at: str
    followers: list[str]
    following: list[str]
    follower_sources: list[str]
    following_source: str

    @property
    def follower_count(self) -> int:
        return len(self.followers)

    @property
    def following_count(self) -> int:
        return len(self.following)

    def to_dict(self) -> dict:
        data = asdict(self)
        data["counts"] = {
            "followers": self.follower_count,
            "following": self.following_count,
        }
        return data


def _parse_named_files(named_texts: list[tuple[str, str]]) -> ImportResult:
    follower_files = [(name, content) for name, content in named_texts
                      if FOLLOWER_RE.fullmatch(Path(name).name)]
    following_files = [(name, content) for name, content in named_texts
                       if FOLLOWING_RE.fullmatch(Path(name).name)]

    if not follower_files:
        raise InstagramExportError("No followers_1.json / followers.json file found.")
    if not following_files:
        raise InstagramExportError("No following.json file found.")
    if len(following_files) > 1:
        # Prefer the file in a followers_and_following folder, then the shortest path.
        following_files.sort(key=lambda item: (
            "followers_and_following" not in item[0].replace("\\", "/").lower(),
            len(item[0]),
        ))

    followers: set[str] = set()
    used_follower_sources: list[str] = []
    for name, content in follower_files:
        followers.update(parse_json_text(content, following=False, source_name=name))
        used_follower_sources.append(name)

    following_name, following_content = following_files[0]
    following = parse_json_text(
        following_content, following=True, source_name=following_name
    )

    return ImportResult(
        imported_at=datetime.now(timezone.utc).isoformat(),
        followers=sorted(followers),
        following=sorted(following),
        follower_sources=sorted(used_follower_sources),
        following_source=following_name,
    )


def import_from_folder(folder: Path) -> ImportResult:
    folder = folder.expanduser().resolve()
    if not folder.is_dir():
        raise InstagramExportError(f"Input folder does not exist: {folder}")

    candidates = [
        path for path in folder.rglob("*.json")
        if FOLLOWER_RE.fullmatch(path.name) or FOLLOWING_RE.fullmatch(path.name)
    ]
    named_texts: list[tuple[str, str]] = []
    for path in candidates:
        try:
            named_texts.append((str(path.relative_to(folder)), path.read_text(encoding="utf-8-sig")))
        except OSError as exc:
            raise InstagramExportError(f"Could not read {path.name}: {exc}") from exc

    return _parse_named_files(named_texts)


def import_from_zip(zip_path: Path) -> ImportResult:
    zip_path = zip_path.expanduser().resolve()
    if not zip_path.is_file():
        raise InstagramExportError(f"ZIP file does not exist: {zip_path}")

    try:
        with ZipFile(zip_path) as archive:
            named_texts = []
            for name in archive.namelist():
                base = Path(name).name
                if FOLLOWER_RE.fullmatch(base) or FOLLOWING_RE.fullmatch(base):
                    try:
                        content = archive.read(name).decode("utf-8-sig")
                    except (KeyError, UnicodeError, OSError) as exc:
                        raise InstagramExportError(f"Could not read {base}: {exc}") from exc
                    named_texts.append((name, content))
    except BadZipFile as exc:
        raise InstagramExportError(f"Not a valid ZIP archive: {zip_path.name}") from exc

    return _parse_named_files(named_texts)


def import_instagram_export(source: str | Path) -> ImportResult:
    path = Path(source).expanduser()
    if path.is_dir():
        return import_from_folder(path)
    if path.is_file() and path.suffix.lower() == ".zip":
        return import_from_zip(path)
    raise InstagramExportError(
        "Choose an extracted Instagram export folder or a .zip archive."
    )


def save_import(result: ImportResult, output: str | Path) -> Path:
    output_path = Path(output).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result.to_dict(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return output_path


def import_from_json_files(json_paths: list[str | Path]) -> ImportResult:
    """Import explicitly selected follower/following JSON files.

    Select the following.json file and all follower split files
    (followers_1.json, followers_2.json, etc.) together.
    """
    if not json_paths:
        raise InstagramExportError("No JSON files were selected.")

    named_texts: list[tuple[str, str]] = []
    for raw_path in json_paths:
        path = Path(raw_path).expanduser().resolve()
        if not path.is_file() or path.suffix.lower() != ".json":
            raise InstagramExportError(f"Not a JSON file: {path}")
        try:
            named_texts.append((path.name, path.read_text(encoding="utf-8-sig")))
        except OSError as exc:
            raise InstagramExportError(f"Could not read {path.name}: {exc}") from exc

    return _parse_named_files(named_texts)
