import json
from datetime import datetime
from pathlib import Path

from .client import YouTubeClient


class YouTubeUploader:
    """YouTube Shorts のアップロード高レベルインターフェース。"""

    def __init__(self, niche_config: dict):
        self.niche_id = niche_config["id"]
        self.channel_id = niche_config["accounts"]["youtube"].get("channel_id_env", "")
        self.client = YouTubeClient.from_niche(niche_config)
        self.log_dir = Path(f"queue/youtube/{self.niche_id}")
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def upload_short(self, video_path: str, script: dict, privacy: str = "public") -> dict:
        """
        YouTube Shorts として動画をアップロードする。
        script: generate_youtube_script() の戻り値
        privacy: public / unlisted / private
        """
        title = script["title"]
        description = script["description"]
        tags = script.get("tags", []) + ["Shorts", "#Shorts"]

        if "#Shorts" not in description:
            description = f"#Shorts\n\n{description}"

        response = self.client.upload_video(
            file_path=video_path,
            title=title,
            description=description,
            tags=tags,
            category_id="22",
            privacy=privacy,
        )

        video_id = response.get("id", "")
        result = {
            **script,
            "video_id": video_id,
            "video_url": f"https://youtube.com/shorts/{video_id}",
            "platform": "youtube",
            "privacy": privacy,
            "uploaded_at": datetime.now().isoformat(),
        }
        log_path = self.log_dir / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{video_id}.json"
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        print(f"[YouTube] アップロード完了 → https://youtube.com/shorts/{video_id}")
        return result
