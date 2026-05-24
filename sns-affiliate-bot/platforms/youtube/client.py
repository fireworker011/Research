import os
import pickle
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


class YouTubeClient:
    """
    YouTube Data API v3 クライアント。
    OAuth2.0 認証を使用（各ジャンルごとに credentials JSON を用意）。
    """

    def __init__(self, credentials_file: str, token_cache_file: str = None):
        self.credentials_file = credentials_file
        self.token_cache = token_cache_file or credentials_file.replace(".json", "_token.pickle")
        self.service = self._build_service()

    @classmethod
    def from_niche(cls, niche_config: dict) -> "YouTubeClient":
        creds_file = niche_config["accounts"]["youtube"]["credentials_file"]
        if not os.path.exists(creds_file):
            raise FileNotFoundError(
                f"YouTube 認証ファイルが見つかりません: {creds_file}\n"
                f"セットアップ手順: skills/SKILL.md の YouTube セクションを参照してください。"
            )
        return cls(creds_file)

    def _build_service(self):
        creds = None
        if os.path.exists(self.token_cache):
            with open(self.token_cache, "rb") as f:
                creds = pickle.load(f)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, SCOPES
                )
                creds = flow.run_local_server(port=0)
            with open(self.token_cache, "wb") as f:
                pickle.dump(creds, f)

        return build("youtube", "v3", credentials=creds)

    def upload_video(
        self,
        file_path: str,
        title: str,
        description: str,
        tags: list,
        category_id: str = "22",
        privacy: str = "public",
    ) -> dict:
        """
        動画をアップロードする。
        category_id: 22 = People & Blogs（転職・副業系に合う）
        privacy: public / unlisted / private
        """
        body = {
            "snippet": {
                "title": title[:100],
                "description": description[:5000],
                "tags": tags[:500],
                "categoryId": category_id,
                "defaultLanguage": "ja",
            },
            "status": {
                "privacyStatus": privacy,
                "selfDeclaredMadeForKids": False,
            },
        }
        media = MediaFileUpload(
            file_path,
            mimetype="video/mp4",
            resumable=True,
            chunksize=256 * 1024,
        )
        request = self.service.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media,
        )

        response = None
        while response is None:
            _, response = request.next_chunk()

        return response
