import inspect

from app import config


def test_read_secret_prefers_file_over_env_var(tmp_path, monkeypatch) -> None:
    secret_file = tmp_path / "my_secret.txt"
    secret_file.write_text("from-file\n")
    monkeypatch.setenv("MY_SECRET_FILE", str(secret_file))
    monkeypatch.setenv("MY_SECRET", "from-env")

    assert config._read_secret("MY_SECRET") == "from-file"


def test_read_secret_falls_back_to_env_var_when_file_missing(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("MY_SECRET_FILE", str(tmp_path / "does-not-exist.txt"))
    monkeypatch.setenv("MY_SECRET", "from-env")

    assert config._read_secret("MY_SECRET") == "from-env"


def test_read_secret_treats_empty_file_as_absent(tmp_path, monkeypatch) -> None:
    secret_file = tmp_path / "empty.txt"
    secret_file.write_text("   \n")
    monkeypatch.setenv("MY_SECRET_FILE", str(secret_file))
    monkeypatch.setenv("MY_SECRET", "from-env")

    assert config._read_secret("MY_SECRET") == "from-env"


def test_read_secret_returns_none_when_nothing_configured(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("MY_SECRET_FILE", str(tmp_path / "does-not-exist.txt"))
    monkeypatch.delenv("MY_SECRET", raising=False)

    assert config._read_secret("MY_SECRET") is None


def test_default_secret_file_path_matches_bind_mounted_filename() -> None:
    # docker-compose.yml bind-mounts ./secrets into /run/secrets as a plain
    # directory (not Compose's native `secrets:` construct, which renames to
    # the bare secret name) — so the mounted file keeps its original name,
    # `minimax_api_key.txt`. A regression here means the secrets-file
    # credential path silently falls through to "not configured" even when
    # a real file is present. Caught by live end-to-end testing once before;
    # guarded here so it can't regress silently again.
    source = inspect.getsource(config._read_secret)
    assert "/run/secrets/{name.lower()}.txt" in source
