from instareciprocal.app_paths import app_path, application_root, ensure_app_directories


def test_app_path_is_inside_project_in_source_mode():
    root = application_root()
    assert app_path("exports").parent == root
    assert root.name == "InstaReciprocal"


def test_app_path_in_frozen_mode(monkeypatch, tmp_path):
    fake_dir = tmp_path / "InstaReciprocal"
    fake_exe = fake_dir / "InstaReciprocal.exe"
    monkeypatch.setattr("sys.frozen", True, raising=False)
    monkeypatch.setattr("sys.executable", str(fake_exe))
    root = application_root()
    assert root == fake_dir
    assert app_path("data") == fake_dir / "data"
    assert app_path("exports") == fake_dir / "exports"

    ensure_app_directories()
    assert (fake_dir / "data").is_dir()
    assert (fake_dir / "exports").is_dir()

