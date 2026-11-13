import json

from instareciprocal.comparator import (
    compare_accounts, load_whitelist, save_reports, save_whitelist,
)


def sample_import():
    return {
        "imported_at": "2026-11-13T00:00:00+00:00",
        "followers": ["alice", "bob", "carol", "erin"],
        "following": ["alice", "bob", "dave", "frank"],
    }


def test_sets_and_counts_are_correct():
    result = compare_accounts(sample_import())
    assert result.mutual == ["alice", "bob"]
    assert result.not_following_back == ["dave", "frank"]
    assert result.you_dont_follow_back == ["carol", "erin"]
    assert result.review_queue == ["dave", "frank"]


def test_whitelist_protects_accounts_from_review_queue():
    result = compare_accounts(sample_import(), {"@DAVE"})
    assert result.protected == ["dave"]
    assert result.review_queue == ["frank"]
    assert result.not_following_back == ["dave", "frank"]


def test_duplicates_and_case_are_normalized():
    data = {"followers": ["Alice", "alice"], "following": ["ALICE", "Bob", "bob"]}
    result = compare_accounts(data)
    assert result.followers_count == 1
    assert result.following_count == 2
    assert result.mutual == ["alice"]
    assert result.not_following_back == ["bob"]


def test_empty_lists():
    result = compare_accounts({"followers": [], "following": []})
    assert result.mutual == []
    assert result.review_queue == []


def test_whitelist_round_trip_and_reports(tmp_path):
    whitelist_path = tmp_path / "data" / "whitelist.json"
    save_whitelist({"@Alice", "BOB"}, whitelist_path)
    assert load_whitelist(whitelist_path) == {"alice", "bob"}

    result = compare_accounts(sample_import(), load_whitelist(whitelist_path))
    json_path, csv_path = save_reports(result, tmp_path / "reports")
    report = json.loads(json_path.read_text(encoding="utf-8"))
    assert report["counts"]["review_queue"] == 2
    assert csv_path.exists()
