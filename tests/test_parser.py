import json
import pytest

from instareciprocal.parser import InstagramExportError, parse_json_text


def test_parse_followers_shape():
    payload = [
        {"string_list_data": [{"value": "Alice", "href": "https://instagram.com/alice/"}]},
        {"string_list_data": [{"value": "BOB"}]},
    ]
    assert parse_json_text(json.dumps(payload), following=False) == {"alice", "bob"}


def test_parse_following_shape():
    payload = {
        "relationships_following": [
            {"title": "Alice", "string_list_data": [{"value": "Alice"}]},
            {"title": "Carol", "string_list_data": [{"value": "Carol"}]},
        ]
    }
    assert parse_json_text(json.dumps(payload), following=True) == {"alice", "carol"}


def test_empty_or_unexpected_json_fails_clearly():
    with pytest.raises(InstagramExportError):
        parse_json_text('{"unexpected": []}', following=False)


def test_invalid_json_fails_clearly():
    with pytest.raises(InstagramExportError):
        parse_json_text("{broken", following=False)
