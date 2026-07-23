"""
YouTube Data API v3 — Shorts 動画アップロードモジュール

使い方:
  1. Google Cloud Console で OAuth2.0 認証情報を作成し JSON をダウンロード
  2. python main.py youtube auth <client_secrets.json のパス>  でトークン取得
  3. publisher = YouTubePublisher()
     publisher.upload_short("output/videos/xxx.mp4", title="...", description="...")
"""

from __future__ import annotations

import json
import os
import pickle
from datetime import date
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

_TOKEN_PATH = Path(__file__).parent.parent.parent / ".youtube_token.pickle"
_SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

# 投稿記録ファイル（daily_check.py が翌日リサーチを起動するために使用）
_POST_LOG = Path(__file__).parent.parent.parent / "posted_log.json"


# ─────────────────────────────────────────────────────────────────────────────
# 投稿記録
# ─────────────────────────────────────────────────────────────────────────────

def _save_post_log(result: dict):
    """投稿記録を posted_log.json に追記する"""
    log = []
    if _POST_LOG.exists():
        try:
            log = json.loads(_POST_LOG.read_text(encoding="utf-8"))
        except Exception:
            log = []

    log.append({
        "posted_date": str(date.today()),
        "video_id":    result["video_id"],
        "title":       result["title"],
        "url":         result["video_url"],
    })

    _POST_LOG.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  📝 投稿記録保存: {_POST_LOG.name}（翌日リサーチ予約済み）")


# ─────────────────────────────────────────────────────────────────────────────
# OAuth 2.0 ヘルパー
# ─────────────────────────────────────────────────────────────────────────────

def _get_credentials(client_secrets_path: Optional[str] = None):
    """認証情報を取得（キャッシュ済みなら再利用、なければ OAuth フロー実行）"""
    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError:
        raise ImportError(
            "google-api-python-client, google-auth-oauthlib が必要です:\n"
            "  pip install google-api-python-client google-auth-oauthlib google-auth-httplib2"
        )

    creds = None

    if _TOKEN_PATH.exists():
        with open(_TOKEN_PATH, "rb") as f:
            creds = pickle.load(f)

    if creds and creds.valid:
        return creds

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(_TOKEN_PATH, "wb") as f:
            pickle.dump(creds, f)
        return creds

    if not client_secrets_path:
        raise FileNotFoundError(
            "YouTube 認証が完了していません。以下を実行してください:\n"
            "  python main.py youtube auth <client_secrets.json のパス>"
        )

    flow = InstalledAppFlow.from_client_secrets_file(client_secrets_path, _SCOPES)
    creds = flow.run_local_server(port=0)

    with open(_TOKEN_PATH, "wb") as f:
        pickle.dump(creds, f)

    return creds


def _build_service(client_secrets_path: Optional[str] = None):
    try:
        from googleapiclient.discovery import build
    except ImportError:
        raise ImportError(
            "google-api-python-client が必要です:\n"
            "  pip install google-api-python-client google-auth-oauthlib google-auth-httplib2"
        )
    creds = _get_credentials(client_secrets_path)
    return build("youtube", "v3", credentials=creds)


# ─────────────────────────────────────────────────────────────────────────────
# YouTubePublisher
# ─────────────────────────────────────────────────────────────────────────────

class YouTubePublisher:
    """YouTube Data API v3 で Shorts 動画をアップロードする"""

    def __init__(self):
        self._service = _build_service()

    def upload_short(
        self,
        video_path: str,
        title: str,
        description: str = "",
        hashtags: list[str] | None = None,
        privacy: str = "private",
        category_id: str = "22",
    ) -> dict:
        """
        動画を YouTube Shorts としてアップロードする

        Args:
            video_path: MP4ファイルのパス（縦型 1080×1920, 60秒以内 推奨）
            title: 動画タイトル（100文字以内）
            description: 動画説明文
            hashtags: ハッシュタグのリスト
            privacy: "private" | "unlisted" | "public"
            category_id: "22"=People&Blogs, "24"=Entertainment, "26"=Howto&Style

        Returns:
            {"video_id": str, "video_url": str, "title": str}
        """
        try:
            from googleapiclient.http import MediaFileUpload
        except ImportError:
            raise ImportError("pip install google-api-python-client")

        video_path = Path(video_path)
        if not video_path.exists():
            raise FileNotFoundError(f"動画ファイルが見つかりません: {video_path}")

        # Shorts は #Shorts タグを説明文に含めると認識されやすい
        if hashtags:
            tag_str = " ".join(hashtags)
            full_description = f"{description}\n\n{tag_str}\n#Shorts"
        else:
            full_description = f"{description}\n\n#Shorts"

        # タグリスト（# なしの文字列）
        tag_list = [t.lstrip("#") for t in (hashtags or [])]
        tag_list.append("Shorts")

        body = {
            "snippet": {
                "title": title[:100],
                "description": full_description[:5000],
                "tags": tag_list[:500],
                "categoryId": category_id,
            },
            "status": {
                "privacyStatus": privacy,
                "selfDeclaredMadeForKids": False,
            },
        }

        media = MediaFileUpload(
            str(video_path),
            mimetype="video/mp4",
            resumable=True,
            chunksize=5 * 1024 * 1024,
        )

        print(f"  アップロード開始: {video_path.name}")
        request = self._service.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media,
        )

        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                pct = int(status.progress() * 100)
                print(f"  アップロード進捗: {pct}%", end="\r")

        print()
        video_id = response["id"]
        video_url = f"https://www.youtube.com/shorts/{video_id}"
        result = {
            "video_id": video_id,
            "video_url": video_url,
            "title": response["snippet"]["title"],
        }

        # 翌日リサーチ用に投稿記録を保存
        _save_post_log(result)

        return result

    def get_channel_info(self) -> dict:
        """チャンネル情報を取得（疎通確認用）"""
        resp = self._service.channels().list(part="snippet,statistics", mine=True).execute()
        items = resp.get("items", [])
        if not items:
            return {}
        ch = items[0]
        return {
            "channel_id": ch["id"],
            "title": ch["snippet"]["title"],
            "subscriber_count": ch["statistics"].get("subscriberCount", "N/A"),
        }


# ─────────────────────────────────────────────────────────────────────────────
# CLI エントリポイント
# ─────────────────────────────────────────────────────────────────────────────

def _cmd_auth(client_secrets_path: str):
    print("YouTube OAuth 認証を開始します...")
    print("ブラウザが開くので Google アカウントでログインして許可をクリックしてください。")
    _build_service(client_secrets_path)
    print(f"✅ 認証完了。トークン保存: {_TOKEN_PATH}")


def _cmd_test():
    creds = _get_credentials()
    expiry = creds.expiry.strftime("%Y-%m-%d %H:%M") if creds.expiry else "不明"
    scopes = ", ".join(creds.scopes or [])
    print(f"✅ 認証OK: トークン有効")
    print(f"   有効期限 : {expiry} UTC")
    print(f"   スコープ : {scopes}")
    print(f"   次のステップ: python main.py youtube post beauty shorts private")


def _cmd_post(video_path: str, title: str, description: str = "", privacy: str = "private"):
    pub = YouTubePublisher()
    result = pub.upload_short(video_path, title, description=description, privacy=privacy)
    print(f"✅ アップロード完了!")
    print(f"   タイトル : {result['title']}")
    print(f"   URL      : {result['video_url']}")


if __name__ == "__main__":
    import sys
    args = sys.argv[1:]
    if not args:
        print("使い方:")
        print("  python -m modules.publishing.youtube_publisher --auth client_secrets.json")
        print("  python -m modules.publishing.youtube_publisher --test")
        print('  python -m modules.publishing.youtube_publisher --post output/videos/xxx.mp4 "タイトル"')
    elif args[0] == "--auth" and len(args) >= 2:
        _cmd_auth(args[1])
    elif args[0] == "--test":
        _cmd_test()
    elif args[0] == "--post" and len(args) >= 3:
        _cmd_post(args[1], args[2])
    else:
        print("引数が不正です。--auth / --test / --post を指定してください。")
