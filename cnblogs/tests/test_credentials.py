import pytest
import publish


def test_load_credentials_reads_env_vars(monkeypatch, tmp_path):
    monkeypatch.setenv("CNBLOGS_TOKEN", "tok")
    monkeypatch.setenv("CNBLOGS_BLOGNAME", "blog")
    monkeypatch.setenv("CNBLOGS_USERNAME", "user")
    creds = publish.load_credentials(str(tmp_path / "absent.env"))
    assert creds == {"blogname": "blog", "username": "user", "token": "tok"}


def test_load_credentials_missing_token_exits(monkeypatch, tmp_path):
    monkeypatch.delenv("CNBLOGS_TOKEN", raising=False)
    with pytest.raises(SystemExit):
        publish.load_credentials(str(tmp_path / "absent.env"))
