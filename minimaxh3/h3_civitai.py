"""Load a Civitai API token in Colab without printing it.

Secrets are optional. Preferred on a phone: a one-line Drive file.
Never log or return the token in status strings.
"""

from __future__ import annotations

import os
import re
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

TOKEN_NAME = "CIVITAI_API_TOKEN"
TOKEN_FILE = "civitai_api_token.txt"
ACCOUNT_URL = "https://civitai.com/user/account"
PLACEHOLDERS = frozenset(
    {
        "",
        "your_token",
        "paste_here",
        "xxxxxxxx",
        "<paste>",
        "ここに貼る",
        "paste",
    }
)

SOURCE_FORM = "form"
SOURCE_SECRET = "secret"
SOURCE_ENV = "env"
SOURCE_DRIVE = "drive"
SOURCE_MISSING = "missing"

_STATUS = {
    SOURCE_FORM: "読み込みOK（①のフォーム。このノートは保存しない）",
    SOURCE_SECRET: "読み込みOK（Colab の鍵 CIVITAI_API_TOKEN）",
    SOURCE_ENV: "読み込みOK（環境変数）",
    SOURCE_DRIVE: f"読み込みOK（Drive の {TOKEN_FILE}）",
    SOURCE_MISSING: (
        "まだありません。シークレットは不要です。"
        f"Drive の minimax-h3-comfyui/{TOKEN_FILE} にキーを1行置くか、"
        f"①のフォームに貼って再実行。取り方: {ACCOUNT_URL} → API Keys"
    ),
}


def _clean(raw: str | None) -> str:
    text = str(raw or "").strip().strip('"').strip("'")
    if not text or text.lower() in PLACEHOLDERS:
        return ""
    if "\n" in text:
        text = text.splitlines()[0].strip()
    if text.startswith("#"):
        return ""
    return text


def _from_drive(drive_root: Path | str | None) -> str:
    if not drive_root:
        return ""
    path = Path(drive_root) / TOKEN_FILE
    if not path.is_file():
        return ""
    try:
        blob = path.read_text(encoding="utf-8")
    except OSError:
        return ""
    for line in blob.splitlines():
        token = _clean(line)
        if token:
            return token
    return ""


def _from_userdata() -> str:
    try:
        from google.colab import userdata  # type: ignore
    except Exception:
        return ""
    try:
        return _clean(userdata.get(TOKEN_NAME))
    except Exception:
        return ""


def load_civitai_token(
    *,
    pasted: str = "",
    drive_root: Path | str | None = None,
    environ: dict[str, str] | None = None,
) -> tuple[str, str]:
    """Return (token, source). source never contains the token."""
    env = environ if environ is not None else os.environ
    order: list[tuple[str, str]] = [
        (SOURCE_FORM, _clean(pasted)),
        (SOURCE_SECRET, _from_userdata()),
        (SOURCE_ENV, _clean(env.get(TOKEN_NAME))),
        (SOURCE_DRIVE, _from_drive(drive_root)),
    ]
    for source, token in order:
        if token:
            return token, source
    return "", SOURCE_MISSING


def apply_civitai_token(token: str, *, environ: dict[str, str] | None = None) -> None:
    env = environ if environ is not None else os.environ
    token = _clean(token)
    if token:
        env[TOKEN_NAME] = token
    elif TOKEN_NAME in env:
        env.pop(TOKEN_NAME, None)


def describe_civitai_status(source: str, present: bool) -> str:
    if not present:
        return _STATUS[SOURCE_MISSING]
    return _STATUS.get(source, _STATUS[SOURCE_MISSING])


def assert_no_token_leak(text: str, token: str) -> None:
    blob = (text or "").lower()
    if token and token.lower() in blob:
        raise SystemExit("refusing to print API keys")
    if "civitai_api_token=" in blob and not blob.strip().startswith("#"):
        # Form default `CIVITAI_API_TOKEN = ""` is allowed; a filled assignment is not.
        if re.search(r'civitai_api_token\s*=\s*["\'][^"\']+["\']', blob):
            raise SystemExit("refusing to print API keys")


def civitai_headers(token: str) -> dict[str, str]:
    headers = {"User-Agent": "minimax-h3-colab"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def civitai_download_url(version_id: int, file_id: int | None = None) -> str:
    url = f"https://civitai.com/api/download/models/{int(version_id)}"
    if file_id:
        url += f"?fileId={int(file_id)}"
    return url


def parse_civitai_lora_url(raw: str) -> str | None:
    """Accept a download URL, a model page with modelVersionId, or a bare version id."""
    text = str(raw or "").strip()
    if not text:
        return None
    if text.isdigit():
        return civitai_download_url(int(text))
    if "civitai.com/api/download/models/" in text:
        return text.split()[0]
    m = re.search(r"civitai\.com/models/\d+[^?\s]*\?[^#]*modelVersionId=(\d+)", text)
    if m:
        return civitai_download_url(int(m.group(1)))
    m = re.search(r"modelVersionId=(\d+)", text)
    if m:
        return civitai_download_url(int(m.group(1)))
    return None


def fetch_civitai_weight(
    url: str,
    dest: Path,
    *,
    token: str,
    min_bytes: int = 1_000_000,
) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.is_file() and dest.stat().st_size > min_bytes:
        print(f"skip {dest.name} ({dest.stat().st_size / 1e6:.1f} MB)")
        return
    tmp = dest.with_name(dest.name + ".part")
    req = urllib.request.Request(url, headers=civitai_headers(token))
    try:
        with urllib.request.urlopen(req, timeout=600) as resp, open(tmp, "wb") as out:
            while True:
                chunk = resp.read(1024 * 1024)
                if not chunk:
                    break
                out.write(chunk)
    except urllib.error.HTTPError as exc:
        if tmp.exists():
            tmp.unlink()
        if exc.code in {401, 403}:
            raise SystemExit(
                f"Civitai が {exc.code} を返した: {dest.name}。"
                f"Drive の {TOKEN_FILE} か ①のフォームに API キーを入れてやり直す。"
                f"取り方: {ACCOUNT_URL} → API Keys。キー自体はログに出さない。"
            ) from exc
        raise SystemExit(f"DL 失敗 {exc.code}: {dest.name}") from exc
    if not tmp.is_file() or tmp.stat().st_size < min_bytes:
        if tmp.exists():
            tmp.unlink()
        raise SystemExit(f"DL 失敗（小さい）: {dest.name}")
    tmp.replace(dest)
    print(f"saved {dest.name} ({dest.stat().st_size / 1e6:.1f} MB)")


def lora_dest_from_url(url: str, lora_dir: Path | str) -> Path:
    name = Path(url.split("?", 1)[0]).name or "civitai_lora.safetensors"
    if not name.endswith(".safetensors"):
        name = "civitai_lora.safetensors"
    return Path(lora_dir) / name
