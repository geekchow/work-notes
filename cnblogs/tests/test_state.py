import os
import publish


def test_repo_relative_key_is_relative_to_repo_root():
    abs_path = os.path.join(publish.REPO_ROOT, "cnblogs", "foo.md")
    assert publish.repo_relative_key(abs_path) == os.path.join("cnblogs", "foo.md")


def test_state_save_then_load_roundtrip(tmp_path):
    path = str(tmp_path / "state.json")
    publish.save_state({"cnblogs/a.md": {"cnblogs_id": "7"}}, path)
    assert publish.load_state(path) == {"cnblogs/a.md": {"cnblogs_id": "7"}}


def test_load_state_missing_file_returns_empty(tmp_path):
    assert publish.load_state(str(tmp_path / "nope.json")) == {}
