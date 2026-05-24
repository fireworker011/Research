import os
import random
import requests
from pathlib import Path


class PexelsClient:
    """
    Pexels API から無料ストック写真を取得する。
    API キー取得: https://www.pexels.com/api/（無料、商用利用OK）
    """

    BASE_URL = "https://api.pexels.com/v1"

    def __init__(self):
        self.api_key = os.getenv("PEXELS_API_KEY", "")
        if not self.api_key:
            raise EnvironmentError(
                "PEXELS_API_KEY が .env に設定されていません。\n"
                "https://www.pexels.com/api/ で無料取得できます。"
            )
        self.session = requests.Session()
        self.session.headers.update({"Authorization": self.api_key})

    def search_photo(self, query: str, orientation: str = "portrait") -> dict:
        """
        クエリに合う写真を1枚検索して返す。
        orientation: portrait（縦型、Shorts用）/ landscape（横型）
        """
        resp = self.session.get(
            f"{self.BASE_URL}/search",
            params={
                "query": query,
                "orientation": orientation,
                "size": "large",
                "per_page": 15,
            },
            timeout=15,
        )
        resp.raise_for_status()
        photos = resp.json().get("photos", [])
        if not photos:
            resp = self.session.get(
                f"{self.BASE_URL}/search",
                params={"query": "business office", "orientation": orientation, "per_page": 15},
                timeout=15,
            )
            resp.raise_for_status()
            photos = resp.json().get("photos", [])
        return random.choice(photos) if photos else {}

    def download_photo(self, photo: dict, output_path: str, size: str = "large2x") -> str:
        """
        写真をダウンロードして output_path に保存する。
        戻り値: output_path
        """
        url = photo.get("src", {}).get(size) or photo.get("src", {}).get("large")
        if not url:
            raise ValueError("写真のURLが取得できませんでした")

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        resp = requests.get(url, timeout=30, stream=True)
        resp.raise_for_status()
        with open(output_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
        return output_path

    def fetch_and_save(self, keywords: list, output_path: str) -> str:
        """キーワードリストからランダムに1つ選んで画像を取得・保存する。"""
        query = random.choice(keywords)
        photo = self.search_photo(query, orientation="portrait")
        return self.download_photo(photo, output_path)
