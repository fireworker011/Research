"""
Grok Imagine API クライアント — 画像生成 & 画像→動画生成

xAI API (https://docs.x.ai) を使用。
  - 画像: grok-imagine-image  ($0.02/枚)
  - 動画: grok-imagine-video  ($0.05/秒, 最大15秒, 720p)

環境変数:
  XAI_API_KEY  … xAI開発者ポータル(console.x.ai)で発行
"""

from __future__ import annotations

import os
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("XAI_BASE_URL", "https://api.x.ai/v1")
IMAGE_MODEL = os.getenv("XAI_IMAGE_MODEL", "grok-imagine-image")
VIDEO_MODEL = os.getenv("XAI_VIDEO_MODEL", "grok-imagine-video")


class GrokClient:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("XAI_API_KEY")
        if not self.api_key:
            raise RuntimeError(
                "XAI_API_KEY が未設定です。console.x.ai でAPIキーを発行し .env に設定してください。"
            )
        self.headers = {"Authorization": f"Bearer {self.api_key}"}

    # ── 画像生成 ──────────────────────────────────────────────
    def generate_image(self, prompt: str, out_path: Path) -> Path:
        """テキストプロンプト → 縦型画像 (9:16)"""
        resp = requests.post(
            f"{BASE_URL}/images/generations",
            headers=self.headers,
            json={
                "model": IMAGE_MODEL,
                "prompt": prompt,
                "n": 1,
                "aspect_ratio": "9:16",
                "response_format": "url",
            },
            timeout=120,
        )
        resp.raise_for_status()
        url = resp.json()["data"][0]["url"]
        img = requests.get(url, timeout=120)
        img.raise_for_status()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(img.content)
        print(f"  ✅ 画像生成: {out_path.name}")
        return out_path

    # ── 画像 → 動画 ──────────────────────────────────────────
    def image_to_video(
        self,
        image_path: Path,
        motion_prompt: str,
        duration_sec: int,
        out_path: Path,
        poll_interval: int = 5,
        timeout_sec: int = 600,
    ) -> Path:
        """参照画像 + モーション指示 → 動画 (非同期ジョブ + ポーリング)"""
        duration_sec = min(duration_sec, 15)  # APIの上限は15秒

        with open(image_path, "rb") as f:
            resp = requests.post(
                f"{BASE_URL}/videos/generations",
                headers=self.headers,
                files={"image": (image_path.name, f, "image/png")},
                data={
                    "model": VIDEO_MODEL,
                    "prompt": motion_prompt,
                    "duration": str(duration_sec),
                    "resolution": "720p",
                    "aspect_ratio": "9:16",
                },
                timeout=120,
            )
        resp.raise_for_status()
        job = resp.json()
        job_id = job.get("id")

        # 同期レスポンスの場合
        if job.get("data"):
            return self._download_video(job["data"][0]["url"], out_path)

        # 非同期ジョブのポーリング
        deadline = time.time() + timeout_sec
        while time.time() < deadline:
            time.sleep(poll_interval)
            st = requests.get(
                f"{BASE_URL}/videos/generations/{job_id}",
                headers=self.headers,
                timeout=60,
            )
            st.raise_for_status()
            status = st.json()
            if status.get("status") == "completed":
                return self._download_video(status["data"][0]["url"], out_path)
            if status.get("status") == "failed":
                raise RuntimeError(f"動画生成失敗: {status}")
        raise TimeoutError(f"動画生成タイムアウト: job={job_id}")

    def _download_video(self, url: str, out_path: Path) -> Path:
        r = requests.get(url, timeout=300)
        r.raise_for_status()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(r.content)
        print(f"  ✅ 動画生成: {out_path.name}")
        return out_path
