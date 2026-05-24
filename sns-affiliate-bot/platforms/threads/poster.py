import json
import os
import time
from datetime import datetime
from pathlib import Path

from .client import ThreadsClient


class ThreadsPoster:
    """
    Threads に投稿する高レベルインターフェース。
    テキスト・画像・動画・カルーセルに対応。
    """

    def __init__(self, niche_id: str):
        self.niche_id = niche_id
        self.client = ThreadsClient.from_env(niche_id)
        self.log_dir = Path(f"queue/threads/{niche_id}")
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def post_text(self, content: dict) -> dict:
        """テキスト投稿を行う。content は generate_threads_post() の戻り値。"""
        text = content["text"]
        container_id = self.client.create_text_container(text)
        # Threads API はコンテナ作成直後に publish すると 500 になることがある
        time.sleep(3)
        post_id = self.client.publish(container_id)
        result = self._log_result(content, post_id, "text")
        print(f"[Threads] 投稿完了 post_id={post_id}")
        return result

    def post_image(self, content: dict, image_url: str) -> dict:
        """画像付き投稿を行う。image_url は公開アクセス可能なURL。"""
        text = content["text"]
        container_id = self.client.create_image_container(text, image_url)
        self.client.wait_for_container(container_id)
        post_id = self.client.publish(container_id)
        result = self._log_result(content, post_id, "image")
        print(f"[Threads] 画像投稿完了 post_id={post_id}")
        return result

    def post_video(self, content: dict, video_url: str) -> dict:
        """動画付き投稿を行う。video_url は公開アクセス可能なURL。"""
        text = content["text"]
        container_id = self.client.create_video_container(text, video_url)
        self.client.wait_for_container(container_id, max_wait_sec=120)
        post_id = self.client.publish(container_id)
        result = self._log_result(content, post_id, "video")
        print(f"[Threads] 動画投稿完了 post_id={post_id}")
        return result

    def _log_result(self, content: dict, post_id: str, media_type: str) -> dict:
        result = {
            **content,
            "post_id": post_id,
            "media_type": media_type,
            "platform": "threads",
            "posted_at": datetime.now().isoformat(),
        }
        log_path = self.log_dir / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{post_id}.json"
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        return result
