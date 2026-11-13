from instareciprocal.history_store import HistoryStore


def test_snapshots_are_saved_once_per_export_timestamp(tmp_path):
    store = HistoryStore(tmp_path / "history.db")
    assert store.save_snapshot("scan-a", ["a"], ["a", "b"], ["b"]) is True
    assert store.save_snapshot("scan-a", ["a"], ["a", "b"], ["b"]) is False
    assert len(store.list_snapshots()) == 1


def test_latest_scan_delta_comparison(tmp_path):
    store = HistoryStore(tmp_path / "history.db")
    store.save_snapshot("older", ["a", "b"], ["a", "x"], ["x"])
    store.save_snapshot("newer", ["a", "c"], ["a", "x", "y"], ["x", "y"])

    delta = store.compare_latest()
    assert delta["new_followers"] == ["c"]
    assert delta["lost_followers"] == ["b"]
    assert delta["new_following"] == ["y"]
    assert delta["new_non_followers"] == ["y"]


def test_compare_returns_none_until_two_snapshots_exist(tmp_path):
    store = HistoryStore(tmp_path / "history.db")
    store.save_snapshot("only", [], [], [])
    assert store.compare_latest() is None
