"""Rules and HTTP calls for posting to the operator's own channels.

The command-line tools default to a dry run. Importing this module does not
post anything.
"""

from __future__ import annotations

import csv
import hashlib
import http.client
import json
import os
import secrets
import time
import urllib.parse
import webbrowser
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent

A8_DISCLOSURE = "アフィリエイト広告を含みます"
YOUTUBE_CHUNK = 8 * 1024 * 1024
TIKTOK_MAX_BYTES = 4_000_000_000
YOUTUBE_MAX_BYTES = 256 * 1024 * 1024 * 1024
DONE_STATUSES = frozenset({"uploaded", "scheduled", "inbox_sent", "publish_complete"})
BLOCK_REUPLOAD = DONE_STATUSES | frozenset(
    {"processing", "PROCESSING_UPLOAD", "PROCESSING_DOWNLOAD"}
)

YOUTUBE_SCOPES = (
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
)
YOUTUBE_ANALYTICS_SCOPE = "https://www.googleapis.com/auth/yt-analytics.readonly"
TIKTOK_SCOPES = ("user.info.basic", "video.list", "video.publish", "video.upload")

YOUTUBE_PRIVACY = frozenset({"public", "unlisted", "private"})
TIKTOK_PRIVACY = {
    "public": "PUBLIC_TO_EVERYONE",
    "private": "SELF_ONLY",
    "friends": "MUTUAL_FOLLOW_FRIENDS",
    "followers": "FOLLOWER_OF_CREATOR",
}

POSTED_COLUMNS = [
    "recorded_at",
    "platform",
    "channel_key",
    "mode",
    "video_id",
    "publish_id",
    "url",
    "privacy",
    "scheduled_at",
    "title",
    "a8",
    "status",
    "file_sha256",
    "note",
]
STATS_COLUMNS = [
    "fetched_at",
    "platform",
    "channel_key",
    "video_id",
    "url",
    "view_count",
    "like_count",
    "comment_count",
    "share_count",
    "analytics_period_views",
    "analytics_start",
    "analytics_end",
    "click_count",
    "click_note",
]
CLICK_NOTE = "このAPIにアフィリエイトのクリック数は無い。A8の数字はA8の管理画面だけ。"
SHORTS_LINK_WARNING = (
    "説明にURLがあります。Shortsの説明欄は押す場所にしません。"
    "リンクはプロフィールに置きます。"
    " https://support.google.com/youtube/answer/13748639"
)


class ValidationError(Exception):
    """The operator can fix this before any network call."""


class ChannelMismatch(ValidationError):
    """Token is for a different channel than channels.json."""


class ApiError(Exception):
    """A remote API rejected the call. The message has no credentials."""


def assert_attended(publish: bool) -> None:
    if not publish:
        return
    if os.environ.get("GITHUB_ACTIONS") == "true" or os.environ.get("CI") == "true":
        raise ValidationError(
            "CIやGitHub ActionsではAPIを呼びません。手元の端末で実行します。"
        )


def utf16_len(value: str) -> int:
    return len(value.encode("utf-16-le")) // 2


def assert_no_affiliate_url(*parts: str) -> None:
    for part in parts:
        if "a8.net" in part.casefold():
            raise ValidationError(
                "説明欄にアフィURLは置きません。開示の文だけにして、リンクはプロフィールに置きます。"
            )


def link_warning(*parts: str) -> str:
    for part in parts:
        lowered = part.casefold()
        if "http://" in lowered or "https://" in lowered:
            return SHORTS_LINK_WARNING
    return ""


def assert_disclosure(text: str, a8: bool) -> None:
    if a8 and A8_DISCLOSURE not in text:
        raise ValidationError(
            "A8動画の説明には「アフィリエイト広告を含みます」を入れます。"
        )


def assert_youtube_text(title: str, description: str) -> None:
    if not title.strip():
        raise ValidationError("タイトルが空です。")
    if len(title) > 100:
        raise ValidationError("YouTubeのタイトルは100文字までです。")
    if "<" in title or ">" in title or "<" in description or ">" in description:
        raise ValidationError("タイトルと説明に < と > は使えません。")
    if len(description.encode("utf-8")) > 5000:
        raise ValidationError("YouTubeの説明は5000バイトまでです。")


def tiktok_caption(title: str, description: str) -> str:
    clean_title = title.strip()
    clean_description = description.strip()
    if not clean_title:
        raise ValidationError("タイトルが空です。")
    caption = clean_title if not clean_description else f"{clean_title}\n{clean_description}"
    if utf16_len(caption) > 2200:
        raise ValidationError("TikTokのキャプションは2200（UTF-16）までです。")
    return caption


def parse_future_iso(value: str) -> datetime:
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValidationError(
            "予約時刻は 2026-10-22T21:00:00+09:00 の形で渡します。"
        ) from exc
    if parsed.tzinfo is None or parsed.tzinfo.utcoffset(parsed) is None:
        raise ValidationError("予約時刻にはタイムゾーンを付けます。日本時間は +09:00 です。")
    if parsed <= datetime.now(timezone.utc):
        raise ValidationError(
            "予約時刻は未来にします。過去にするとYouTubeはすぐ公開します。"
        )
    return parsed.astimezone(timezone.utc).replace(microsecond=0)


def youtube_status(privacy: str, schedule: str) -> tuple[str, str | None, str]:
    if privacy not in YOUTUBE_PRIVACY:
        raise ValidationError("YouTubeの公開範囲は public、unlisted、private です。")
    if not schedule.strip():
        return privacy, None, ""
    when = parse_future_iso(schedule)
    if privacy == "unlisted":
        raise ValidationError(
            "限定公開の予約はAPIにありません。予約はその時刻に公開になります。"
        )
    stamp = when.strftime("%Y-%m-%dT%H:%M:%SZ")
    note = "予約時刻に公開になります。APIへは公開まで private と publishAt を送ります。"
    return "private", stamp, note


def reject_tiktok_schedule(schedule: str) -> None:
    if schedule.strip():
        raise ValidationError(
            "TikTokの投稿APIに予約時刻はありません。"
            "YouTubeは publishAt が使えます。"
            "TikTokは --inbox で下書きを送り、アプリから出します。"
        )


def build_youtube_body(
    *,
    title: str,
    description: str,
    category_id: str,
    language: str,
    privacy_status: str,
    publish_at: str | None,
    made_for_kids: bool,
    synthetic: bool,
    a8: bool,
) -> tuple[dict, str]:
    if not category_id.isdigit():
        raise ValidationError("カテゴリIDは数字です。videoCategories.list の番号を使います。")
    status: dict[str, object] = {
        "privacyStatus": privacy_status,
        "selfDeclaredMadeForKids": made_for_kids,
    }
    if publish_at:
        status["publishAt"] = publish_at
    if synthetic:
        status["containsSyntheticMedia"] = True
    body: dict[str, object] = {
        "snippet": {
            "title": title,
            "description": description,
            "categoryId": category_id,
            "defaultLanguage": language,
        },
        "status": status,
    }
    parts = ["snippet", "status"]
    if a8:
        body["paidProductPlacementDetails"] = {"hasPaidProductPlacement": True}
        parts.append("paidProductPlacementDetails")
    return body, ",".join(parts)


def tiktok_chunk_plan(size: int) -> tuple[int, int, list[tuple[int, int]]]:
    """Return chunk_size, count, and half-open byte slices.

    Files up to 64MB go in one request. Larger files use 10_000_000-byte
    chunks, and the remainder is merged into the final chunk, matching
    https://developers.tiktok.com/doc/content-posting-api-media-transfer-guide
    """
    if size <= 0:
        raise ValidationError("動画ファイルが空です。")
    if size > TIKTOK_MAX_BYTES:
        raise ValidationError("TikTokの上限は4GBです。")
    if size <= 64_000_000:
        return size, 1, [(0, size)]
    chunk = 10_000_000
    count = size // chunk
    if count < 2 or count > 1000:
        raise ValidationError("TikTokの分割数は2から1000です。")
    slices: list[tuple[int, int]] = []
    start = 0
    for _ in range(count - 1):
        slices.append((start, start + chunk))
        start += chunk
    slices.append((start, size))
    last_len = size - start
    if last_len > 128_000_000:
        raise ValidationError("最終チャンクがTikTokの128MBを超えます。")
    return chunk, count, slices


def youtube_slices(size: int, chunk: int = YOUTUBE_CHUNK) -> list[tuple[int, int]]:
    if size <= 0:
        raise ValidationError("動画ファイルが空です。")
    if size > YOUTUBE_MAX_BYTES:
        raise ValidationError("YouTubeの上限は256GBです。")
    if chunk % (256 * 1024) != 0:
        raise ValidationError("YouTubeの分割サイズは256KBの倍数です。")
    slices: list[tuple[int, int]] = []
    start = 0
    while start < size:
        end = min(start + chunk, size)
        slices.append((start, end))
        start = end
    return slices


def assert_video_file(path: Path) -> int:
    if path.suffix.casefold() != ".mp4":
        raise ValidationError("入力は mp4 です。")
    if not path.is_file():
        raise ValidationError(f"動画ファイルがありません: {path}")
    size = path.stat().st_size
    if size <= 0:
        raise ValidationError("動画ファイルが空です。")
    return size


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def resolve_description(description: str | None, description_file: str | None) -> str:
    if description is not None and description_file:
        raise ValidationError("説明は --description か --description-file のどちらか一方です。")
    if description_file:
        file_path = Path(description_file)
        if not file_path.is_file():
            raise ValidationError(f"説明ファイルがありません: {file_path}")
        return file_path.read_text(encoding="utf-8")
    if description is None:
        raise ValidationError("説明文を --description か --description-file で渡します。")
    return description


def load_channels(path: Path) -> list[dict]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValidationError(f"channels.json がありません: {path}") from exc
    if not isinstance(data, list):
        raise ValidationError("channels.json は配列です。")
    return data


def find_channel(rows: list[dict], platform: str, key: str) -> dict:
    matches = [
        row for row in rows if row.get("platform") == platform and row.get("key") == key
    ]
    if len(matches) != 1:
        known = [str(row.get("key")) for row in rows if row.get("platform") == platform]
        raise ValidationError(
            f"{platform} のチャンネル {key} が見つかりません。使えるキー: {', '.join(known)}"
        )
    return matches[0]


def norm_name(value: str) -> str:
    return value.strip().lstrip("@").casefold()


def names_match(
    expected_title: str,
    expected_handle: str,
    actual_title: str,
    actual_handle: str,
) -> bool:
    expected = {norm_name(expected_title)}
    if expected_handle.strip():
        expected.add(norm_name(expected_handle))
    expected.discard("")
    actual = {norm_name(actual_title), norm_name(actual_handle)}
    actual.discard("")
    return bool(expected & actual)


def read_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValidationError(f"ファイルがありません: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValidationError(f"JSONとして読めません: {path}") from exc
    if not isinstance(data, dict):
        raise ValidationError(f"JSONオブジェクトではありません: {path}")
    return data


def google_client_fields(data: dict) -> tuple[str, str]:
    block = data
    if isinstance(data.get("installed"), dict):
        block = data["installed"]
    elif isinstance(data.get("web"), dict):
        block = data["web"]
    return str(block.get("client_id") or ""), str(block.get("client_secret") or "")


def assert_youtube_channel_ready(channel: dict) -> None:
    status = str(channel.get("status") or "active")
    if status in {"", "active"}:
        return
    if status == "hold":
        title = str(channel.get("title") or channel.get("key") or "")
        raise ValidationError(f"{title} はアカウント未定のため保留です。許可も投稿もしません。")
    if status == "reserved":
        key = str(channel.get("key") or "")
        raise ValidationError(f"{key} はチャンネル名が未定のため、まだ許可しません。")
    raise ValidationError(f"チャンネルの status が不明です: {status}")


def find_client_secret(directory: Path) -> Path:
    if not directory.is_dir():
        raise ValidationError(f"client_secret のフォルダがありません: {directory}")
    matches = sorted(path for path in directory.glob("client_secret_*.json") if path.is_file())
    if len(matches) == 1:
        return matches[0]
    shown = ", ".join(path.name for path in matches) if matches else "なし"
    extra = ""
    if not matches:
        names = sorted(path.name for path in directory.glob("*.json") if path.is_file())
        if names:
            extra = " フォルダ内のJSON: " + ", ".join(names)
    raise ValidationError(
        f"{directory} には client_secret_*.json を1つだけ置きます。該当: {shown}.{extra}"
    )


def path_inside_repo(path: Path, root: Path) -> bool:
    repo = git_root(root)
    if repo is None:
        return False
    resolved = path.resolve()
    repo_resolved = repo.resolve()
    return resolved == repo_resolved or repo_resolved in resolved.parents


def default_youtube_token_path(root: Path, channel_key: str, client_path: Path) -> Path:
    if path_inside_repo(client_path, root):
        return root / "tokens" / "youtube" / f"{channel_key}.json"
    return client_path.parent / "token.json"


def resolve_youtube_client(
    root: Path,
    channel: dict,
    client_file: str = "",
    client_dir: str = "",
) -> tuple[Path | None, str, str]:
    assert_youtube_channel_ready(channel)
    path: Path | None = None
    if client_file:
        path = Path(client_file)
        if not path.is_file():
            raise ValidationError(f"client_secret がありません: {path}")
    elif client_dir:
        path = find_client_secret(Path(client_dir))
    elif str(channel.get("client_secret") or "").strip():
        path = Path(str(channel["client_secret"]))
        if not path.is_file():
            raise ValidationError(f"client_secret がありません: {path}")
    elif str(channel.get("client_secret_dir") or "").strip():
        path = find_client_secret(Path(str(channel["client_secret_dir"])))
    else:
        legacy = root / "secrets" / "youtube-client.json"
        if legacy.is_file():
            path = legacy
    client_id = ""
    client_secret = ""
    if path is not None:
        client_id, client_secret = google_client_fields(read_json(path))
    client_id = client_id or os.environ.get("YOUTUBE_CLIENT_ID", "")
    client_secret = client_secret or os.environ.get("YOUTUBE_CLIENT_SECRET", "")
    return path, client_id, client_secret


def youtube_token_path(
    root: Path,
    channel_key: str,
    token_file: str,
    client_path: Path | None,
) -> Path:
    if token_file:
        return Path(token_file)
    repo_token = root / "tokens" / "youtube" / f"{channel_key}.json"
    if client_path is not None and not path_inside_repo(client_path, root):
        beside = client_path.parent / "token.json"
        if beside.is_file() or not repo_token.is_file():
            return beside
    return repo_token


def git_root(start: Path) -> Path | None:
    for candidate in [start, *start.parents]:
        if (candidate / ".git").exists():
            return candidate
    return None


def assert_safe_secret_path(path: Path, root: Path) -> None:
    resolved = path.resolve()
    allowed = (root / "tokens").resolve()
    if resolved == allowed or allowed in resolved.parents:
        return
    repo = git_root(root)
    if repo is not None and (resolved == repo.resolve() or repo.resolve() in resolved.parents):
        raise ValidationError(
            "トークンは tokens/ か、このgitリポジトリの外に保存します。"
        )


def write_secret_json(path: Path, payload: dict, root: Path) -> None:
    assert_safe_secret_path(path, root)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.chmod(temporary, 0o600)
    os.replace(temporary, path)
    os.chmod(path, 0o600)


def _env_or_file(file_value: str, env_value: str) -> str:
    return file_value or env_value


def google_credentials(
    root: Path,
    channel_key: str,
    token_file: str,
    *,
    channel: dict | None = None,
    client_file: str = "",
    client_dir: str = "",
) -> dict:
    if channel is None:
        channel = find_channel(load_channels(root / "channels.json"), "youtube", channel_key)
    client_path, client_id, client_secret = resolve_youtube_client(
        root,
        channel,
        client_file,
        client_dir,
    )
    token_path = youtube_token_path(root, channel_key, token_file, client_path)
    saved: dict = {}
    refresh = ""
    if token_path.is_file():
        saved = read_json(token_path)
        refresh = str(saved.get("refresh_token") or "")
    refresh = _env_or_file(refresh, os.environ.get("YOUTUBE_REFRESH_TOKEN", ""))
    if not client_id or not client_secret or not refresh:
        folder = client_dir or str(channel.get("client_secret_dir") or "")
        place = folder or "channels.json の client_secret_dir"
        raise ValidationError(
            "YouTubeのクライアントとrefresh tokenがありません。"
            f" client_secret は {place} の client_secret_*.json。"
            f" トークンは同じフォルダの token.json か tokens/youtube/{channel_key}.json。"
        )
    return {
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh,
        "token_path": token_path,
        "client_path": client_path,
        "saved": saved,
    }


def tiktok_credentials(root: Path, channel_key: str, token_file: str) -> dict:
    client_path = root / "secrets" / "tiktok-client.json"
    client_key = os.environ.get("TIKTOK_CLIENT_KEY", "")
    client_secret = os.environ.get("TIKTOK_CLIENT_SECRET", "")
    if client_path.is_file():
        client = read_json(client_path)
        client_key = _env_or_file(str(client.get("client_key") or ""), client_key)
        client_secret = _env_or_file(str(client.get("client_secret") or ""), client_secret)
    token_path = Path(token_file) if token_file else root / "tokens" / "tiktok" / f"{channel_key}.json"
    saved: dict = {}
    refresh = ""
    if token_path.is_file():
        saved = read_json(token_path)
        refresh = str(saved.get("refresh_token") or "")
    refresh = _env_or_file(refresh, os.environ.get("TIKTOK_REFRESH_TOKEN", ""))
    if not client_key or not client_secret or not refresh:
        raise ValidationError(
            "TikTokのクライアントとrefresh tokenがありません。"
            "SETUP_TIKTOK.md のあと、secrets/tiktok-client.json と tokens/tiktok/<key>.json に置きます。"
        )
    return {
        "client_key": client_key,
        "client_secret": client_secret,
        "refresh_token": refresh,
        "token_path": token_path,
        "saved": saved,
    }


def append_csv(path: Path, columns: list[str], row: dict[str, str]) -> None:
    is_new = not path.exists()
    with path.open("a", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        if is_new:
            writer.writeheader()
        writer.writerow({key: row.get(key, "") for key in columns})


def already_posted(path: Path, platform: str, channel_key: str, digest: str) -> bool:
    if not path.is_file():
        return False
    with path.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            if (
                row.get("platform") == platform
                and row.get("channel_key") == channel_key
                and row.get("file_sha256") == digest
                and row.get("status") in BLOCK_REUPLOAD
            ):
                return True
    return False


def safe_url(url: str) -> str:
    parts = urllib.parse.urlsplit(url)
    return urllib.parse.urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))


def public_api_error(url: str, status: int, payload: bytes) -> str:
    shown = safe_url(url)
    try:
        data = json.loads(payload.decode("utf-8"))
    except json.JSONDecodeError:
        return f"HTTP {status} {shown}"
    if not isinstance(data, dict):
        return f"HTTP {status} {shown}"
    if isinstance(data.get("error"), str):
        message = f"HTTP {status} {shown} {data.get('error')} {data.get('error_description', '')}"
        if data.get("error") == "invalid_grant":
            message += " refresh tokenが無効です。Testing中の同意は7日で切れます。許可をやり直します。"
        return message.strip()
    error = data.get("error")
    if isinstance(error, dict) and "errors" in error:
        reasons = [
            str(item.get("reason"))
            for item in error.get("errors") or []
            if isinstance(item, dict)
        ]
        text = f"HTTP {status} {shown} {','.join(reasons)} {error.get('message', '')}"
        if any("quota" in item.casefold() for item in reasons):
            text += " https://developers.google.com/youtube/v3/determine_quota_cost"
        return text.strip()
    if isinstance(error, dict) and "code" in error:
        code = str(error.get("code"))
        hints = {
            "unaudited_client_can_only_post_to_private_accounts": (
                "審査前のDirect Postは非公開アカウントのSELF_ONLYだけです。代替は --inbox です。"
            ),
            "privacy_level_option_mismatch": (
                "creator_info の privacy_level_options にある値だけ送れます。"
            ),
            "spam_risk_too_many_pending_share": "未投稿の下書きは24時間で5本までです。",
            "reached_active_user_cap": "未審査クライアントは24時間で5ユーザーまでです。",
            "scope_not_authorized": "許可したスコープに、この呼び出しが入っていません。",
        }
        return (
            f"HTTP {status} {shown} {code} {error.get('message', '')} "
            f"{hints.get(code, '')} log_id={error.get('log_id', '')}"
        ).strip()
    return f"HTTP {status} {shown}"


def http_send(
    method: str,
    url: str,
    headers: dict[str, str],
    body: bytes | None,
    timeout: int,
) -> tuple[int, dict[str, str], bytes]:
    parts = urllib.parse.urlsplit(url)
    if parts.scheme not in {"https", "http"} or not parts.hostname:
        raise ApiError(f"URLが不正です: {safe_url(url)}")
    path = parts.path or "/"
    if parts.query:
        path += "?" + parts.query
    port = parts.port or (443 if parts.scheme == "https" else 80)
    connection_type = (
        http.client.HTTPSConnection if parts.scheme == "https" else http.client.HTTPConnection
    )
    connection = connection_type(parts.hostname, port, timeout=timeout)
    try:
        connection.request(method, path, body=body, headers=headers)
        response = connection.getresponse()
        payload = response.read()
        header_map: dict[str, str] = {}
        for key, value in response.getheaders():
            header_map[key.lower()] = value
        return response.status, header_map, payload
    finally:
        connection.close()


def parse_json(payload: bytes) -> dict:
    if not payload.strip():
        return {}
    try:
        data = json.loads(payload.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise ApiError("APIの応答がJSONではありません。") from exc
    if not isinstance(data, dict):
        raise ApiError("APIの応答がJSONオブジェクトではありません。")
    return data


def auth_header(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}


def google_access_token(creds: dict) -> str:
    url = "https://oauth2.googleapis.com/token"
    body = urllib.parse.urlencode(
        {
            "client_id": creds["client_id"],
            "client_secret": creds["client_secret"],
            "refresh_token": creds["refresh_token"],
            "grant_type": "refresh_token",
        }
    ).encode()
    status, _, payload = http_send(
        "POST",
        url,
        {"Content-Type": "application/x-www-form-urlencoded"},
        body,
        60,
    )
    data = parse_json(payload)
    token = data.get("access_token")
    if status != 200 or not isinstance(token, str) or not token:
        raise ApiError(public_api_error(url, status, payload))
    return token


def youtube_mine(access_token: str) -> tuple[str, str, str]:
    url = "https://www.googleapis.com/youtube/v3/channels?part=snippet&mine=true"
    status, _, payload = http_send("GET", url, auth_header(access_token), None, 60)
    if status != 200:
        raise ApiError(public_api_error(url, status, payload))
    data = parse_json(payload)
    items = data.get("items") or []
    if not items:
        raise ChannelMismatch(
            "このGoogleアカウントのチャンネルが取れません。"
            "同意画面で、投稿先のチャンネル（ブランドアカウント）を選び直します。"
        )
    item = items[0]
    snippet = item.get("snippet") or {}
    return (
        str(item.get("id") or ""),
        str(snippet.get("title") or ""),
        str(snippet.get("customUrl") or ""),
    )


def require_channel_match(
    channel: dict,
    actual_title: str,
    actual_handle: str,
) -> None:
    if names_match(
        str(channel.get("title") or ""),
        str(channel.get("handle") or ""),
        actual_title,
        actual_handle,
    ):
        return
    raise ChannelMismatch(
        "許可したアカウントが channels.json と違います。"
        f" APIの名前={actual_title!r} ハンドル={actual_handle!r}。"
        " channels.json の title か handle をこの名前に直します。"
        " トークンは保存済みなら、許可のやり直しは不要です。"
    )


def upload_chunks(
    session_url: str,
    path: Path,
    slices: list[tuple[int, int]],
    *,
    access_token: str | None,
    content_type: str,
    done: frozenset[int],
    continue_codes: frozenset[int],
) -> bytes:
    size = path.stat().st_size
    last_body = b""
    with path.open("rb") as handle:
        for start, end in slices:
            handle.seek(start)
            chunk = handle.read(end - start)
            if len(chunk) != end - start:
                raise ApiError("動画ファイルの読込サイズが一致しません。")
            headers = {
                "Content-Type": content_type,
                "Content-Length": str(len(chunk)),
                "Content-Range": f"bytes {start}-{end - 1}/{size}",
            }
            if access_token:
                headers["Authorization"] = f"Bearer {access_token}"
            status = 0
            payload = b""
            for attempt in range(3):
                status, _, payload = http_send("PUT", session_url, headers, chunk, 300)
                if status in done or status in continue_codes:
                    break
                if status >= 500 and attempt < 2:
                    time.sleep(2)
                    continue
                raise ApiError(public_api_error(session_url, status, payload))
            last_body = payload
            if status in done and end == size:
                return payload
            if status in continue_codes and end != size:
                continue
            if status in done and end != size:
                raise ApiError("転送が最後の分割より前に完了扱いになりました。")
            raise ApiError(public_api_error(session_url, status, payload))
    return last_body


def youtube_insert(
    access_token: str,
    path: Path,
    body: dict,
    part: str,
    *,
    notify: bool,
) -> dict:
    size = path.stat().st_size
    query = {"uploadType": "resumable", "part": part}
    if not notify:
        query["notifySubscribers"] = "false"
    url = "https://www.googleapis.com/upload/youtube/v3/videos?" + urllib.parse.urlencode(query)
    raw = json.dumps(body).encode()
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json; charset=UTF-8",
        "X-Upload-Content-Length": str(size),
        "X-Upload-Content-Type": "video/mp4",
        "Content-Length": str(len(raw)),
    }
    status, response_headers, payload = http_send("POST", url, headers, raw, 120)
    if status not in {200, 201}:
        raise ApiError(public_api_error(url, status, payload))
    location = response_headers.get("location") or ""
    if location.startswith("/"):
        location = "https://www.googleapis.com" + location
    if not location:
        raise ApiError("アップロード先が応答にありません。")
    uploaded = upload_chunks(
        location,
        path,
        youtube_slices(size),
        access_token=access_token,
        content_type="video/mp4",
        done=frozenset({200, 201}),
        continue_codes=frozenset({308}),
    )
    data = parse_json(uploaded)
    if not data.get("id"):
        raise ApiError("YouTubeの応答に動画IDがありません。")
    return data


def youtube_videos(access_token: str, video_ids: list[str]) -> list[dict]:
    url = (
        "https://www.googleapis.com/youtube/v3/videos?part=statistics,snippet&id="
        + urllib.parse.quote(",".join(video_ids))
    )
    status, _, payload = http_send("GET", url, auth_header(access_token), None, 60)
    if status != 200:
        raise ApiError(public_api_error(url, status, payload))
    data = parse_json(payload)
    items = data.get("items") or []
    if not isinstance(items, list):
        raise ApiError("videos.list の応答が想定と違います。")
    return items


def youtube_analytics(access_token: str, video_id: str, start: str, end: str) -> str:
    query = urllib.parse.urlencode(
        {
            "ids": "channel==MINE",
            "startDate": start,
            "endDate": end,
            "metrics": "views",
            "filters": f"video=={video_id}",
        }
    )
    url = "https://youtubeanalytics.googleapis.com/v2/reports?" + query
    status, _, payload = http_send("GET", url, auth_header(access_token), None, 60)
    if status != 200:
        raise ApiError(public_api_error(url, status, payload))
    data = parse_json(payload)
    headers = [str(item.get("name")) for item in data.get("columnHeaders") or []]
    rows = data.get("rows") or []
    if "views" not in headers or not rows:
        return ""
    value = rows[0][headers.index("views")]
    return str(value)


def tiktok_form(fields: dict[str, str]) -> bytes:
    return urllib.parse.urlencode(fields).encode()


def tiktok_access_token(root: Path, creds: dict) -> str:
    url = "https://open.tiktokapis.com/v2/oauth/token/"
    status, _, payload = http_send(
        "POST",
        url,
        {"Content-Type": "application/x-www-form-urlencoded"},
        tiktok_form(
            {
                "client_key": creds["client_key"],
                "client_secret": creds["client_secret"],
                "grant_type": "refresh_token",
                "refresh_token": creds["refresh_token"],
            }
        ),
        60,
    )
    data = parse_json(payload)
    token = data.get("access_token")
    if status != 200 or not isinstance(token, str) or not token:
        raise ApiError(public_api_error(url, status, payload))
    rotated = data.get("refresh_token")
    if isinstance(rotated, str) and rotated and rotated != creds["refresh_token"]:
        saved = dict(creds.get("saved") or {})
        saved["refresh_token"] = rotated
        saved["open_id"] = str(data.get("open_id") or saved.get("open_id") or "")
        write_secret_json(creds["token_path"], saved, root)
        creds["refresh_token"] = rotated
        creds["saved"] = saved
    return token


def tiktok_ok(url: str, status: int, payload: bytes) -> dict:
    data = parse_json(payload)
    error = data.get("error")
    code = error.get("code") if isinstance(error, dict) else None
    if status != 200 or (code not in {None, "ok"}):
        raise ApiError(public_api_error(url, status, payload))
    return data


def tiktok_user(access_token: str) -> tuple[str, str]:
    url = "https://open.tiktokapis.com/v2/user/info/?fields=open_id,display_name"
    status, _, payload = http_send("GET", url, auth_header(access_token), None, 60)
    data = tiktok_ok(url, status, payload)
    user = (data.get("data") or {}).get("user") or {}
    return str(user.get("open_id") or ""), str(user.get("display_name") or "")


def tiktok_creator(access_token: str) -> dict:
    url = "https://open.tiktokapis.com/v2/post/publish/creator_info/query/"
    headers = {**auth_header(access_token), "Content-Type": "application/json; charset=UTF-8"}
    status, _, payload = http_send("POST", url, headers, b"{}", 60)
    data = tiktok_ok(url, status, payload)
    creator = data.get("data") or {}
    if not isinstance(creator, dict):
        raise ApiError("creator_info の応答が想定と違います。")
    return creator


def tiktok_init(access_token: str, url: str, body: dict) -> dict:
    headers = {**auth_header(access_token), "Content-Type": "application/json; charset=UTF-8"}
    status, _, payload = http_send("POST", url, headers, json.dumps(body).encode(), 60)
    data = tiktok_ok(url, status, payload)
    block = data.get("data") or {}
    if not isinstance(block, dict) or not block.get("publish_id"):
        raise ApiError("TikTokの応答に publish_id がありません。")
    return block


def tiktok_put(upload_url: str, path: Path, slices: list[tuple[int, int]]) -> None:
    upload_chunks(
        upload_url,
        path,
        slices,
        access_token=None,
        content_type="video/mp4",
        done=frozenset({200, 201}),
        continue_codes=frozenset({206}),
    )


def tiktok_status(access_token: str, publish_id: str) -> dict:
    url = "https://open.tiktokapis.com/v2/post/publish/status/fetch/"
    headers = {**auth_header(access_token), "Content-Type": "application/json; charset=UTF-8"}
    body = json.dumps({"publish_id": publish_id}).encode()
    status, _, payload = http_send("POST", url, headers, body, 60)
    data = tiktok_ok(url, status, payload)
    block = data.get("data") or {}
    if not isinstance(block, dict):
        raise ApiError("投稿ステータスの応答が想定と違います。")
    return block


def tiktok_post_ids(data: dict) -> list[str]:
    for key in ("publicaly_available_post_id", "publicly_available_post_id"):
        value = data.get(key)
        if isinstance(value, list):
            return [str(item) for item in value if str(item)]
        if value:
            return [str(value)]
    return []


def tiktok_query(access_token: str, video_ids: list[str]) -> list[dict]:
    fields = "id,share_url,view_count,like_count,comment_count,share_count"
    url = f"https://open.tiktokapis.com/v2/video/query/?fields={fields}"
    headers = {**auth_header(access_token), "Content-Type": "application/json; charset=UTF-8"}
    body = json.dumps({"filters": {"video_ids": video_ids}}).encode()
    status, _, payload = http_send("POST", url, headers, body, 60)
    data = tiktok_ok(url, status, payload)
    videos = (data.get("data") or {}).get("videos") or []
    if not isinstance(videos, list):
        raise ApiError("video.query の応答が想定と違います。")
    return videos


def poll_tiktok(access_token: str, publish_id: str) -> dict:
    last: dict = {}
    for attempt in range(12):
        last = tiktok_status(access_token, publish_id)
        state = str(last.get("status") or "")
        if state in {"PUBLISH_COMPLETE", "FAILED", "SEND_TO_USER_INBOX"}:
            return last
        if attempt < 11:
            time.sleep(5)
    return last


def wait_for_oauth_callback(port: int, timeout: int) -> dict[str, list[str]]:
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            parsed = urllib.parse.urlparse(self.path)
            query = urllib.parse.parse_qs(parsed.query)
            if "code" in query or "error" in query:
                self.server.result = query  # type: ignore[attr-defined]
            body = "受け取りました。このタブを閉じて端末に戻ってください。".encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args: object) -> None:  # noqa: A003
            return

    try:
        server = HTTPServer(("127.0.0.1", port), Handler)
    except OSError as exc:
        raise ValidationError(
            f"127.0.0.1:{port} が使用中です。空いてからやり直します。"
        ) from exc
    server.result = {}  # type: ignore[attr-defined]
    deadline = time.time() + timeout
    try:
        while time.time() < deadline:
            found = server.result  # type: ignore[attr-defined]
            if found.get("code") or found.get("error"):
                return found
            server.timeout = max(1, int(deadline - time.time()))
            server.handle_request()
    finally:
        server.server_close()
    return server.result  # type: ignore[attr-defined]


def open_authorization(url: str, *, browser: bool = True) -> None:
    print(url)
    if browser:
        webbrowser.open(url)


def pkce_pair() -> tuple[str, str]:
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~"
    verifier = "".join(secrets.choice(alphabet) for _ in range(64))
    challenge = hashlib.sha256(verifier.encode("ascii")).hexdigest()
    return verifier, challenge


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def watch_url(video_id: str) -> str:
    return f"https://www.youtube.com/watch?v={video_id}"
