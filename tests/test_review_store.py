from instareciprocal.review_store import ReviewStore


def test_new_accounts_are_pending_and_status_persists(tmp_path):
    store = ReviewStore(tmp_path / "review.db")
    assert store.get_status("@Example_User") == "pending"
    store.set_status("Example_User", "reviewed", "Checked profile")
    assert store.get_status("example_user") == "reviewed"

    reopened = ReviewStore(tmp_path / "review.db")
    assert reopened.get_status("EXAMPLE_USER") == "reviewed"


def test_status_transitions_are_logged(tmp_path):
    store = ReviewStore(tmp_path / "review.db")
    store.set_status("alice", "reviewed")
    store.set_status("alice", "skipped", "Review later")
    history = store.get_history("ALICE")
    assert len(history) == 2
    assert history[0]["old_status"] == "reviewed"
    assert history[0]["new_status"] == "skipped"
    assert history[0]["note"] == "Review later"


def test_manual_unfollow_status_is_distinct(tmp_path):
    store = ReviewStore(tmp_path / "review.db")
    store.set_status("alice", "unfollowed_manually", "Unfollowed manually on Instagram")
    assert store.get_status("alice") == "unfollowed_manually"


def test_invalid_status_rejected(tmp_path):
    import pytest
    store = ReviewStore(tmp_path / "review.db")
    with pytest.raises(ValueError):
        store.set_status("alice", "auto_unfollowed")


def test_status_counts(tmp_path):
    store = ReviewStore(tmp_path / "review.db")
    store.set_status("alice", "reviewed")
    store.set_status("bob", "skipped")
    counts = store.status_counts()
    assert counts["reviewed"] == 1
    assert counts["skipped"] == 1
    assert counts["pending"] == 0
