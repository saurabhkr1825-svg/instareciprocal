import json
from pathlib import Path
from zipfile import ZipFile
import pytest
from instareciprocal.gui import InstaReciprocalApp
from instareciprocal.importer import import_instagram_export, save_import


def test_gui_initialization_and_filtering(tmp_path, monkeypatch):
    # Set mock app paths so tests stay in tmp_path
    monkeypatch.setattr("instareciprocal.gui.DEFAULT_DATABASE", tmp_path / "data" / "instareciprocal.db")
    monkeypatch.setattr("instareciprocal.gui.DEFAULT_WHITELIST", tmp_path / "data" / "whitelist.json")
    monkeypatch.setattr("instareciprocal.gui.DEFAULT_IMPORT", tmp_path / "exports" / "phase1-import.json")
    monkeypatch.setattr("instareciprocal.gui.DEFAULT_REPORTS", tmp_path / "exports")

    # Create dummy export
    export_zip = tmp_path / "export.zip"
    with ZipFile(export_zip, "w") as archive:
        archive.writestr("followers_and_following/followers_1.json", json.dumps([
            {"string_list_data": [{"value": "user1"}]},
            {"string_list_data": [{"value": "user2"}]},
        ]))
        archive.writestr("followers_and_following/following.json", json.dumps({
            "relationships_following": [
                {"title": "user1", "string_list_data": [{"value": "user1"}]},
                {"title": "user3", "string_list_data": [{"value": "user3"}]},
            ]
        }))

    app = InstaReciprocalApp()
    app.withdraw()

    try:
        import_res = import_instagram_export(export_zip)
        save_import(import_res, tmp_path / "exports" / "phase1-import.json")
        app.import_path = tmp_path / "exports" / "phase1-import.json"
        app.refresh_comparison()

        assert app.result is not None
        assert app.result.followers_count == 2
        assert app.result.following_count == 2
        assert app.result.mutual == ["user1"]
        assert app.result.not_following_back == ["user3"]
        assert app.result.you_dont_follow_back == ["user2"]

        # Filter tests
        app.set_filter("Mutual follows")
        assert app._visible_usernames() == ["user1"]

        app.set_filter("Not following back")
        assert app._visible_usernames() == ["user3"]

        # Search test
        app.search_var.set("user3")
        assert app._visible_usernames() == ["user3"]
        app.search_var.set("nomatch")
        assert app._visible_usernames() == []
        app.search_var.set("")

        # Selection test
        app.select_visible()
        assert app.selected == {"user3"}
        app.clear_selection()
        assert len(app.selected) == 0

        # Review status updates
        app.update_review_status("user3", "reviewed")
        assert app.review_store.get_status("user3") == "reviewed"

        app.update_review_status("user3", "skipped")
        assert app.review_store.get_status("user3") == "skipped"

        app.update_review_status("user3", "unfollowed_manually")
        assert app.review_store.get_status("user3") == "unfollowed_manually"
    finally:
        app.destroy()
