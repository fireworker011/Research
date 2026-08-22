import os
import time
import requests


class ThreadsClient:
    """
    Threads API クライアント。
    Meta Graph API v21.0 ベース。
    ドキュメント: https://developers.facebook.com/docs/threads
    """

    BASE_URL = "https://graph.threads.net/v1.0"
    RATE_LIMIT_PER_DAY = 250

    def __init__(self, user_id: str, access_token: str):
        self.user_id = user_id
        self.access_token = access_token

    @classmethod
    def from_env(cls, niche_id: str) -> "ThreadsClient":
        niche_upper = niche_id.upper()
        user_id = os.getenv(f"THREADS_{niche_upper}_USER_ID", "")
        token = os.getenv(f"THREADS_{niche_upper}_ACCESS_TOKEN", "")
        if not user_id or not token:
            raise EnvironmentError(
                f"THREADS_{niche_upper}_USER_ID または THREADS_{niche_upper}_ACCESS_TOKEN が "
                f".env に設定されていません。\n"
                f"Threads API セットアップガイド: skills/SKILL.md を参照してください。"
            )
        return cls(user_id, token)

    def _auth_params(self) -> dict:
        return {"access_token": self.access_token}

    def _post_container(self, data: dict) -> str:
        """コンテナ作成の共通処理。textはbodyに、その他はparamsに分離してURLを短縮。"""
        text = data.pop("text", "")
        resp = requests.post(
            f"{self.BASE_URL}/{self.user_id}/threads",
            params={**self._auth_params(), **data},
            data={"text": text},
            timeout=30,
        )
        if not resp.ok:
            try:
                detail = resp.json()
            except Exception:
                detail = resp.text
            raise RuntimeError(f"コンテナ作成失敗 ({resp.status_code}): {detail}")
        return resp.json()["id"]

    def create_text_container(self, text: str) -> str:
        """テキスト投稿のコンテナを作成して container_id を返す。"""
        return self._post_container({"media_type": "TEXT", "text": text})

    def create_image_container(self, text: str, image_url: str) -> str:
        """画像付き投稿のコンテナを作成して container_id を返す。"""
        return self._post_container({"media_type": "IMAGE", "image_url": image_url, "text": text})

    def create_video_container(self, text: str, video_url: str) -> str:
        """動画付き投稿のコンテナを作成して container_id を返す。"""
        return self._post_container({"media_type": "VIDEO", "video_url": video_url, "text": text})

    def wait_for_container(self, container_id: str, max_wait_sec: int = 60) -> bool:
        """コンテナの処理完了を待つ（動画・画像の場合）。"""
        for _ in range(max_wait_sec // 5):
            resp = requests.get(
                f"{self.BASE_URL}/{container_id}",
                params=self._auth_params() | {"fields": "status,error_message"},
                timeout=15,
            )
            data = resp.json()
            status = data.get("status", "")
            if status == "FINISHED":
                return True
            if status == "ERROR":
                raise RuntimeError(f"コンテナ処理エラー: {data.get('error_message')}")
            time.sleep(5)
        raise TimeoutError(f"コンテナ処理がタイムアウトしました (container_id={container_id})")

    def publish(self, container_id: str) -> str:
        """コンテナを公開して post_id を返す。"""
        resp = requests.post(
            f"{self.BASE_URL}/{self.user_id}/threads_publish",
            params=self._auth_params() | {"creation_id": container_id},
            timeout=30,
        )
        if not resp.ok:
            try:
                detail = resp.json()
            except Exception:
                detail = resp.text
            raise RuntimeError(
                f"Threads publish 失敗 ({resp.status_code}): {detail}\n"
                f"container_id={container_id}"
            )
        return resp.json()["id"]

    def get_user_info(self) -> dict:
        resp = requests.get(
            f"{self.BASE_URL}/{self.user_id}",
            params=self._auth_params() | {"fields": "id,username,name,threads_profile_picture_url"},
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()
