import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from h3_civitai import (
    ACCOUNT_URL,
    SOURCE_DRIVE,
    SOURCE_ENV,
    SOURCE_FORM,
    SOURCE_MISSING,
    TOKEN_FILE,
    TOKEN_NAME,
    apply_civitai_token,
    civitai_download_url,
    civitai_headers,
    describe_civitai_status,
    load_civitai_token,
    lora_dest_from_url,
    parse_civitai_lora_url,
)


def test_load_prefers_form_then_env_then_drive(tmp_path, monkeypatch):
    monkeypatch.delenv(TOKEN_NAME, raising=False)
    drive = tmp_path / "minimax-h3-comfyui"
    drive.mkdir()
    (drive / TOKEN_FILE).write_text("drive-token-value\n", encoding="utf-8")
    token, src = load_civitai_token(pasted="form-token", drive_root=drive, environ={})
    assert token == "form-token" and src == SOURCE_FORM

    token, src = load_civitai_token(pasted="", drive_root=drive, environ={TOKEN_NAME: "env-token"})
    assert token == "env-token" and src == SOURCE_ENV

    token, src = load_civitai_token(pasted="ここに貼る", drive_root=drive, environ={})
    assert token == "drive-token-value" and src == SOURCE_DRIVE

    token, src = load_civitai_token(pasted="", drive_root=tmp_path / "empty", environ={})
    assert token == "" and src == SOURCE_MISSING


def test_status_never_includes_token():
    secret = "sk-live-abcdefghijklmnopqrstuvwxyz"
    text = describe_civitai_status(SOURCE_DRIVE, True)
    assert TOKEN_FILE in text
    assert secret not in text
    missing = describe_civitai_status(SOURCE_MISSING, False)
    assert "シークレットは不要" in missing
    assert ACCOUNT_URL in missing
    assert "API Keys" in missing


def test_apply_sets_env_without_placeholder():
    env: dict[str, str] = {}
    apply_civitai_token("  abc  ", environ=env)
    assert env[TOKEN_NAME] == "abc"
    apply_civitai_token("", environ=env)
    assert TOKEN_NAME not in env


def test_parse_civitai_lora_url():
    assert parse_civitai_lora_url("") is None
    assert parse_civitai_lora_url("3280824") == "https://civitai.com/api/download/models/3280824"
    assert parse_civitai_lora_url("https://civitai.com/api/download/models/1?fileId=2").endswith("fileId=2")
    parsed = parse_civitai_lora_url("https://civitai.com/models/2901443?modelVersionId=3280824")
    assert parsed == civitai_download_url(3280824)
    dest = lora_dest_from_url(parsed, "/tmp/loras")
    assert dest.name.endswith(".safetensors")
    assert "Authorization" in civitai_headers("tok")
    assert "Authorization" not in civitai_headers("")


def test_studio_wrapper_uses_drive(tmp_path, monkeypatch):
    monkeypatch.delenv(TOKEN_NAME, raising=False)
    from h3_lora_studio import civitai_token

    drive = tmp_path / "d"
    drive.mkdir()
    (drive / TOKEN_FILE).write_text("# comment\nreal-key\n", encoding="utf-8")
    assert civitai_token(drive_root=drive) == "real-key"
    assert os.environ.get(TOKEN_NAME) == "real-key"
