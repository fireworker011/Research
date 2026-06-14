"""
DALL-E 3 を使ってシーン画像を生成するモジュール
"""

from __future__ import annotations

import os
import time
from pathlib import Path

import requests
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

_STYLE_SUFFIX = (
    "Photorealistic, cinematic lighting, vertical 9:16 portrait format, "
    "Japanese setting, no text or watermarks."
)


class ImageGenerator:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY が .env に設定されていません")
        self.client = OpenAI(api_key=api_key)

    def generate_scene_images(self, script: dict, out_dir: str | None = None) -> list[Path]:
        """
        スクリプトの各シーンから画像を生成して保存する

        Args:
            script: ScriptGenerator が返す dict（scenes キーを含む）
            out_dir: 保存先ディレクトリ（省略時は output/images/{project_id}）

        Returns:
            生成した画像ファイルのパスリスト
        """
        scenes = script.get("scenes", [])
        project_id = script.get("project_id", "project")

        save_dir = Path(out_dir) if out_dir else Path("output/images") / project_id
        save_dir.mkdir(parents=True, exist_ok=True)

        paths = []
        for i, scene in enumerate(scenes, 1):
            visual = scene.get("visual", "")
            if not visual:
                print(f"  scene{i:02d}: visual がないためスキップ")
                paths.append(None)
                continue

            prompt = f"{visual} {_STYLE_SUFFIX}"
            print(f"  scene{i:02d}: 画像生成中...")

            try:
                resp = self.client.images.generate(
                    model="dall-e-3",
                    prompt=prompt,
                    size="1024x1792",  # 縦型 (9:16 近似)
                    quality="standard",
                    n=1,
                )
                url = resp.data[0].url
                img_data = requests.get(url, timeout=30).content
                img_path = save_dir / f"scene{i:02d}.png"
                img_path.write_bytes(img_data)
                print(f"  scene{i:02d}: 保存 → {img_path}")
                paths.append(img_path)

            except Exception as e:
                print(f"  scene{i:02d}: エラー → {e}")
                paths.append(None)

            # レート制限対策
            if i < len(scenes):
                time.sleep(2)

        return paths
