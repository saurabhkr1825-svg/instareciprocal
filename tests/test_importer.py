import json
from pathlib import Path
from zipfile import ZipFile

from instareciprocal.importer import import_from_folder, import_from_zip, save_import


def follower_data(names):
    return json.dumps([
        {"string_list_data": [{"value": name}]}
        for name in names
    ])


def following_data(names):
    return json.dumps({
        "relationships_following": [
            {"title": name, "string_list_data": [{"value": name}]}
            for name in names
        ]
    })


def test_import_folder_and_merge_split_followers(tmp_path: Path):
    export = tmp_path / "export" / "followers_and_following"
    export.mkdir(parents=True)
    (export / "followers_1.json").write_text(follower_data(["Alice", "Bob"]), encoding="utf-8")
    (export / "followers_2.json").write_text(follower_data(["BOB", "Carol"]), encoding="utf-8")
    (export / "following.json").write_text(following_data(["Alice", "Dave"]), encoding="utf-8")

    result = import_from_folder(export.parent.parent)
    assert result.followers == ["alice", "bob", "carol"]
    assert result.following == ["alice", "dave"]
    assert result.follower_count == 3
    assert result.following_count == 2
    assert len(result.follower_sources) == 2


def test_import_zip_and_save_output(tmp_path: Path):
    zip_path = tmp_path / "instagram.zip"
    with ZipFile(zip_path, "w") as archive:
        archive.writestr("account/followers_and_following/followers_1.json",
                         follower_data(["Alice", "Bob"]))
        archive.writestr("account/followers_and_following/following.json",
                         following_data(["Bob", "Carol"]))

    result = import_from_zip(zip_path)
    assert result.followers == ["alice", "bob"]
    assert result.following == ["bob", "carol"]

    output = save_import(result, tmp_path / "out" / "import.json")
    saved = json.loads(output.read_text(encoding="utf-8"))
    assert saved["counts"] == {"followers": 2, "following": 2}
    assert saved["followers"] == ["alice", "bob"]


def test_import_selected_json_files_individually(tmp_path: Path):
    from instareciprocal.importer import import_from_json_files

    followers = tmp_path / "followers_1.json"
    following = tmp_path / "following.json"
    followers.write_text(follower_data(["Alice", "Bob"]), encoding="utf-8")
    following.write_text(following_data(["Bob", "Carol"]), encoding="utf-8")

    result = import_from_json_files([followers, following])
    assert result.followers == ["alice", "bob"]
    assert result.following == ["bob", "carol"]


def test_import_selected_split_follower_json_files(tmp_path: Path):
    from instareciprocal.importer import import_from_json_files

    followers_1 = tmp_path / "followers_1.json"
    followers_2 = tmp_path / "followers_2.json"
    following = tmp_path / "following.json"
    followers_1.write_text(follower_data(["Alice"]), encoding="utf-8")
    followers_2.write_text(follower_data(["Bob"]), encoding="utf-8")
    following.write_text(following_data(["Alice", "Bob"]), encoding="utf-8")

    result = import_from_json_files([followers_1, followers_2, following])
    assert result.followers == ["alice", "bob"]
    assert result.following == ["alice", "bob"]
