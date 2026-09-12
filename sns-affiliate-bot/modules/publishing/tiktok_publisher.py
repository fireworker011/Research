"""
TikTok Content Posting API v2 — 動画アップロードモジュール

使い方:
  1. .env に TIKTOK_CLIENT_KEY / TIKTOK_CLIENT_SECRET を設定
  2. python -m modules.publishing.tiktok_publisher --auth  でアクセストークン取得
  3. publisher = TikTokPublisher()
     publisher.publish_video("output/videos/xxx.mp4", caption="...", hashtags=["#美容"])
"""

from __future__ import annotations

import json
import math
import os
import time
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from threading import Thread
from typing import Optional

import requests
from dotenv import load_dotenv

load_dotenv()

# TikTok API エンドポイント
_BASE = "https://open.tiktokapis.com/v2"
_AUTH_URL = "https://www.tiktok.com/v2/auth/authorize/"
_TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"

# 動画チャンクサイズ: 10MB
_CHUNK_SIZE = 10 * 1024 * 1024

# トークン保存パス
_TOKEN_PATH = Path(__file__).parent.parent.parent / ".tiktok_token.json"


# ─────────────────────────────────────────────────────────────────────────────
# OAuth 2.0 ヘルパー
# ─────────────────────────────────────────────────────────────────────────────

class _OAuthCallbackHandler(BaseHTTPRequestHandler):
    """ローカルリダイレクトサーバーで認可コードを受け取る"""
    code: Optional[str] = None

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        _OAuthCallbackHandler.code = params.get("code", [None])[0]
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"<html><body><h2>TikTok認証完了。このタブを閉じてください。</h2></body></html>")

    def log_message(self, *args):
        pass


def _run_oauth_flow(client_key: str, client_secret: str) -> dict:
    """ブラウザを開いてOAuthフローを完了し、トークンを返す"""
    redirect_uri = "http://localhost:8080/callback"
    state = "tiktok_auth"
    scope = "video.publish,video.upload,user.info.basic"

    auth_url = (
        f"{_AUTH_URL}?client_key={client_key}"
        f"&scope={urllib.parse.quote(scope)}"
        f"&response_type=code"
        f"&redirect_uri={urllib.parse.quote(redirect_uri)}"
        f"&state={state}"
    )

    print(f"\n  ブラウザが開きます。TikTokでログインして「許可」をクリックしてください。")
    print(f"  自動で開かない場合: {auth_url}\n")

    server = HTTPServer(("localhost", 8080), _OAuthCallbackHandler)
    thread = Thread(target=server.handle_request)
    thread.start()

    webbrowser.open(auth_url)
    thread.join(timeout=120)
    server.server_close()

    code = _OAuthCallbackHandler.code
    if not code:
        raise RuntimeError("認証コードを取得できませんでした（タイムアウト）")

    # アクセストークン取得
    resp = requests.post(_TOKEN_URL, data={
        "client_key": client_key,
        "client_secret": client_secret,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri,
    })
    resp.raise_for_status()
    token_data = resp.json()

    if "error" in token_data:
        raise RuntimeError(f"トークン取得失敗: {token_data}")

    token_data["client_key"] = client_key
    token_data["client_secret"] = client_secret
    token_data["expires_at"] = int(time.time()) + token_data.get("expires_in", 86400)
    return token_data


def _refresh_token(token_data: dict) -> dict:
    """リフレッシュトークンでアクセストークンを更新"""
    resp = requests.post(_TOKEN_URL, data={
        "client_key": token_data["client_key"],
        "client_secret": token_data["client_secret"],
        "grant_type": "refresh_token",
        "refresh_token": token_data["refresh_token"],
    })
    resp.raise_for_status()
    new_data = resp.json()
    new_data["client_key"] = token_data["client_key"]
    new_data["client_secret"] = token_data["client_secret"]
    new_data["expires_at"] = int(time.time()) + new_data.get("expires_in", 86400)
    return new_data


def _load_token() -> dict:
    """保存済みトークンを読み込み、期限切れなら自動更新"""
    if not _TOKEN_PATH.exists():
        raise FileNotFoundError(
            f"トークンが見つかりません。先に認証を実行してください:\n"
            f"  python -m modules.publishing.tiktok_publisher --auth"
        )
    token_data = json.loads(_TOKEN_PATH.read_text())

    # 期限5分前から更新
    if time.time() > token_data.get("expires_at", 0) - 300:
        print("  アクセストークンを更新中...")
        token_data = _refresh_token(token_data)
        _TOKEN_PATH.write_text(json.dumps(token_data, ensure_ascii=False, indent=2))

    return token_data


# ─────────────────────────────────────────────────────────────────────────────
# TikTokPublisher
# ─────────────────────────────────────────────────────────────────────────────

class TikTokPublisher:
    """TikTok Content Posting API v2 で動画を投稿する"""

    def __init__(self):
        token_data = _load_token()
        self._access_token = token_data["access_token"]
        self._open_id = token_data.get("open_id", "")

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self._access_token}"}

    def publish_video(
        self,
        video_path: str,
        caption: str,
        hashtags: list[str] | None = None,
        privacy: str = "SELF_ONLY",
    ) -> str:
        """
        動画をTikTokに投稿する

        Args:
            video_path: MP4ファイルのパス
            caption: 動画の説明文
            hashtags: ハッシュタグのリスト（例: ["#美容", "#スキンケア"]）
            privacy: "SELF_ONLY" | "FOLLOWER_OF_CREATOR" | "MUTUAL_FOLLOW_FRIENDS" | "PUBLIC_TO_EVERYONE"
                     ※ 審査通過前は SELF_ONLY のみ有効

        Returns:
            publish_id (投稿ID)
        """
        video_path = Path(video_path)
        if not video_path.exists():
            raise FileNotFoundError(f"動画ファイルが見つかりません: {video_path}")

        video_size = video_path.stat().st_size
        chunk_count = max(1, math.ceil(video_size / _CHUNK_SIZE))

        if hashtags:
            full_caption = caption + " " + " ".join(hashtags)
        else:
            full_caption = caption

        print(f"  [1/3] アップロード初期化中...")
        publish_id, upload_url = self._init_upload(full_caption, video_size, chunk_count, privacy)

        print(f"  [2/3] 動画アップロード中... ({video_size // 1024} KB, {chunk_count}チャンク)")
        self._upload_chunks(upload_url, video_path, video_size, chunk_count)

        print(f"  [3/3] 投稿ステータス確認中...")
        self._wait_for_publish(publish_id)

        return publish_id

    def _init_upload(
        self, caption: str, video_size: int, chunk_count: int, privacy: str
    ) -> tuple[str, str]:
        resp = requests.post(
            f"{_BASE}/post/publish/video/init/",
            headers={**self._headers(), "Content-Type": "application/json; charset=UTF-8"},
            json={
                "post_info": {
                    "title": caption[:150],
                    "privacy_level": privacy,
                    "disable_duet": False,
                    "disable_comment": False,
                    "disable_stitch": False,
                },
                "source_info": {
                    "source": "FILE_UPLOAD",
                    "video_size": video_size,
                    "chunk_size": _CHUNK_SIZE,
                    "total_chunk_count": chunk_count,
                },
            },
        )
        resp.raise_for_status()
        data = resp.json().get("data", {})
        publish_id = data.get("publish_id")
        upload_url = data.get("upload_url")
        if not publish_id or not upload_url:
            raise RuntimeError(f"初期化失敗: {resp.json()}")
        return publish_id, upload_url

    def _upload_chunks(
        self, upload_url: str, video_path: Path, video_size: int, chunk_count: int
    ):
        with open(video_path, "rb") as f:
            for i in range(chunk_count):
                chunk = f.read(_CHUNK_SIZE)
                start = i * _CHUNK_SIZE
                end = min(start + len(chunk) - 1, video_size - 1)
                resp = requests.put(
                    upload_url,
                    headers={
                        "Content-Type": "video/mp4",
                        "Content-Range": f"bytes {start}-{end}/{video_size}",
                        "Content-Length": str(len(chunk)),
                    },
                    data=chunk,
                    timeout=120,
                )
                if resp.status_code not in (200, 206):
                    raise RuntimeError(f"チャンク {i+1}/{chunk_count} アップロード失敗: {resp.status_code} {resp.text}")
                print(f"    チャンク {i+1}/{chunk_count} 完了")

    def _wait_for_publish(self, publish_id: str, timeout: int = 120):
        deadline = time.time() + timeout
        while time.time() < deadline:
            resp = requests.post(
                f"{_BASE}/post/publish/status/fetch/",
                headers={**self._headers(), "Content-Type": "application/json; charset=UTF-8"},
                json={"publish_id": publish_id},
            )
            resp.raise_for_status()
            status = resp.json().get("data", {}).get("status", "")
            print(f"    ステータス: {status}")
            if status == "PUBLISH_COMPLETE":
                return
            if status in ("FAILED", "SPAM_RISK_TOO_MANY_REQUESTS", "SPAM_RISK_USER_BANNED_FROM_POSTING"):
                raise RuntimeError(f"投稿失敗: {status}")
            time.sleep(3)
        raise TimeoutError(f"投稿タイムアウト (publish_id={publish_id})")

    def get_user_info(self) -> dict:
        """ログインユーザー情報を取得（疎通確認用）"""
        resp = requests.get(
            f"{_BASE}/user/info/",
            headers=self._headers(),
            params={"fields": "open_id,union_id,avatar_url,display_name"},
        )
        resp.raise_for_status()
        return resp.json().get("data", {}).get("user", {})


# ─────────────────────────────────────────────────────────────────────────────
# CLI エントリポイント
# ─────────────────────────────────────────────────────────────────────────────

def _cmd_auth():
    client_key = os.getenv("TIKTOK_CLIENT_KEY", "")
    client_secret = os.getenv("TIKTOK_CLIENT_SECRET", "")
    if not client_key or not client_secret:
        print("❌ .env に TIKTOK_CLIENT_KEY と TIKTOK_CLIENT_SECRET を設定してください")
        return

    print("TikTok OAuth 認証を開始します...")
    token_data = _run_oauth_flow(client_key, client_secret)
    _TOKEN_PATH.write_text(json.dumps(token_data, ensure_ascii=False, indent=2))
    print(f"✅ トークン保存完了: {_TOKEN_PATH}")


def _cmd_test():
    pub = TikTokPublisher()
    user = pub.get_user_info()
    print(f"✅ 接続OK: {user.get('display_name')} ({user.get('open_id')})")


def _cmd_post(video_path: str, caption: str):
    pub = TikTokPublisher()
    publish_id = pub.publish_video(video_path, caption, privacy="SELF_ONLY")
    print(f"✅ 投稿完了 (publish_id={publish_id})")


if __name__ == "__main__":
    import sys
    args = sys.argv[1:]
    if not args or args[0] == "--auth":
        _cmd_auth()
    elif args[0] == "--test":
        _cmd_test()
    elif args[0] == "--post" and len(args) >= 3:
        _cmd_post(args[1], args[2])
    else:
        print("使い方:")
        print("  python -m modules.publishing.tiktok_publisher --auth")
        print("  python -m modules.publishing.tiktok_publisher --test")
        print('  python -m modules.publishing.tiktok_publisher --post output/videos/xxx.mp4 "キャプション"')
