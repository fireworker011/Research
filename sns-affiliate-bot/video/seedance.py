"""
Seedance 2.0 image-to-video client via fal.ai (default) or Replicate.

必要な環境変数:
  SEEDANCE_API_KEY   fal.ai API キー (https://fal.ai/dashboard/keys)
  SEEDANCE_PROVIDER  'fal' (default) | 'replicate'
  SEEDANCE_MODEL     モデル名を上書きしたい場合（省略可）

fal.ai 料金の目安: ~$0.03/秒 → 5秒クリップ ≈ $0.15、30秒動画 ≈ $0.90
"""

import os
import time
import requests


_DEFAULT_MODEL_FAL = "fal-ai/seedance/v1/image-to-video"
_DEFAULT_MODEL_REPLICATE = "bytedance/seedance-2.0"

# シーンキーワード → Seedance 英語プロンプト変換テーブル
_PROMPT_MAP = {
    "残業": "exhausted office worker at desk late night, cinematic lighting, realistic",
    "副業": "focused person working on laptop at home, warm lighting, productive atmosphere",
    "転職": "professional person reviewing documents, confident expression, modern office",
    "AI": "glowing laptop screen with code and AI interface, futuristic office environment",
    "Claude": "person typing on laptop with focus, AI assistant on screen, modern workspace",
    "ビフォー": "tired businessman looking stressed, overwhelmed office setting, realistic",
    "アフター": "confident businessperson smiling, clean organized workspace, success feeling",
    "スキル": "professional development, person studying digital content, growth mindset",
    "自動化": "computer running automated tasks, data flowing on screen, efficient workflow",
}
_PROMPT_DEFAULT = (
    "professional Japanese businessman at modern office, cinematic shot, "
    "soft natural lighting, authentic emotion, 9:16 vertical video"
)


def _scene_to_prompt(text: str) -> str:
    """シーンテキストからSeedance用英語プロンプトを生成する。"""
    for keyword, prompt in _PROMPT_MAP.items():
        if keyword in text:
            return prompt + ", 9:16 vertical format, cinematic"
    return _PROMPT_DEFAULT


class SeedanceClient:
    """Seedance 2.0 I2V クライアント。API キーがなければ is_available() == False。"""

    def __init__(self):
        self.api_key = os.getenv("SEEDANCE_API_KEY", "")
        self.provider = os.getenv("SEEDANCE_PROVIDER", "fal").lower()
        self.model = os.getenv(
            "SEEDANCE_MODEL",
            _DEFAULT_MODEL_FAL if self.provider == "fal" else _DEFAULT_MODEL_REPLICATE,
        )

    def is_available(self) -> bool:
        return bool(self.api_key)

    def generate_from_image(
        self,
        image_url: str,
        scene_text: str,
        duration: int,
        save_path: str,
    ) -> str:
        """
        Pexels 画像 URL + シーンテキスト → Seedance I2V → ローカル MP4 保存。
        戻り値: save_path
        """
        prompt = _scene_to_prompt(scene_text)
        clip_duration = max(5, min(duration + 1, 10))  # Seedance: 5〜10秒

        if self.provider == "fal":
            video_url = self._run_fal(image_url, prompt, clip_duration)
        elif self.provider == "replicate":
            video_url = self._run_replicate(image_url, prompt, clip_duration)
        else:
            raise ValueError(f"未対応のプロバイダー: {self.provider}")

        return self._download(video_url, save_path)

    # ------------------------------------------------------------------
    # fal.ai
    # ------------------------------------------------------------------

    def _run_fal(self, image_url: str, prompt: str, duration: int) -> str:
        try:
            import fal_client  # noqa: PLC0415
        except ImportError as e:
            raise ImportError("fal-client が必要です: pip install fal-client") from e

        os.environ["FAL_KEY"] = self.api_key
        result = fal_client.run(
            self.model,
            arguments={
                "image_url": image_url,
                "prompt": prompt,
                "duration": str(duration),
                "aspect_ratio": "9:16",
                "resolution": "1080p",
            },
        )
        # fal.ai の一般的なレスポンス形式
        url = (
            result.get("video", {}).get("url")
            or result.get("url")
            or (result.get("videos") or [{}])[0].get("url", "")
        )
        if not url:
            raise RuntimeError(f"Seedance (fal): 動画URLが取得できません: {result}")
        return url

    # ------------------------------------------------------------------
    # Replicate
    # ------------------------------------------------------------------

    def _run_replicate(self, image_url: str, prompt: str, duration: int) -> str:
        try:
            import replicate  # noqa: PLC0415
        except ImportError as e:
            raise ImportError("replicate が必要です: pip install replicate") from e

        os.environ["REPLICATE_API_TOKEN"] = self.api_key
        output = replicate.run(
            self.model,
            input={
                "image": image_url,
                "prompt": prompt,
                "duration": duration,
                "aspect_ratio": "9:16",
            },
        )
        return str(output)

    # ------------------------------------------------------------------
    # 共通: ダウンロード
    # ------------------------------------------------------------------

    def _download(self, url: str, save_path: str) -> str:
        resp = requests.get(url, timeout=180, stream=True)
        resp.raise_for_status()
        with open(save_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
        return save_path
