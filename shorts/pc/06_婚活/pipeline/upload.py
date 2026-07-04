"""
YouTube Shorts 自動アップロード (YouTube Data API v3)

初回のみ:
  1. Google Cloud Console で OAuth クライアント(デスクトップ)を作成しJSONをDL
  2. python upload.py auth client_secrets.json
以降は保存済みトークンで完全自動。
"""

from __future__ import annotations

import pickle
import sys
from pathlib import Path

TOKEN_PATH = Path(__file__).parent / ".youtube_token.pickle"
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def _get_credentials(client_secrets: str | None = None):
    from google.auth.transport.requests import Request

    creds = None
    if TOKEN_PATH.exists():
        creds = pickle.loads(TOKEN_PATH.read_bytes())
    if creds and creds.valid:
        return creds
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        TOKEN_PATH.write_bytes(pickle.dumps(creds))
        return creds
    if not client_secrets:
        raise RuntimeError("初回認証が必要: python upload.py auth <client_secrets.json>")
    from google_auth_oauthlib.flow import InstalledAppFlow

    flow = InstalledAppFlow.from_client_secrets_file(client_secrets, SCOPES)
    creds = flow.run_local_server(port=0)
    TOKEN_PATH.write_bytes(pickle.dumps(creds))
    print("✅ 認証完了。トークンを保存しました。")
    return creds


def upload_short(video_path: Path, title: str, description: str,
                 tags: list[str] | None = None, privacy: str = "public") -> str:
    """Shorts をアップロードして動画IDを返す"""
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload

    yt = build("youtube", "v3", credentials=_get_credentials())
    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags or [],
            "categoryId": "22",  # People & Blogs
        },
        "status": {"privacyStatus": privacy, "selfDeclaredMadeForKids": False},
    }
    media = MediaFileUpload(str(video_path), chunksize=-1, resumable=True,
                            mimetype="video/mp4")
    req = yt.videos().insert(part="snippet,status", body=body, media_body=media)
    resp = None
    while resp is None:
        status, resp = req.next_chunk()
        if status:
            print(f"  アップロード中… {int(status.progress() * 100)}%")
    vid = resp["id"]
    print(f"✅ 投稿完了: https://youtube.com/shorts/{vid}")
    return vid


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "auth":
        _get_credentials(sys.argv[2])
