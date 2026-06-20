import os
import cloudinary
import cloudinary.uploader
from pathlib import Path


class CloudinaryUploader:
    """動画・画像を Cloudinary にアップロードして公開 URL を返す。"""

    def __init__(self):
        cloudinary.config(
            cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME", ""),
            api_key=os.getenv("CLOUDINARY_API_KEY", ""),
            api_secret=os.getenv("CLOUDINARY_API_SECRET", ""),
        )
        if not os.getenv("CLOUDINARY_CLOUD_NAME"):
            raise EnvironmentError(
                "CLOUDINARY_CLOUD_NAME / API_KEY / API_SECRET が .env に設定されていません。"
            )

    def upload_video(self, file_path: str, folder: str = "sns-affiliate-bot") -> str:
        """動画をアップロードして公開 URL を返す。"""
        print(f"[Cloudinary] アップロード中: {Path(file_path).name} ...")
        result = cloudinary.uploader.upload(
            file_path,
            resource_type="video",
            folder=folder,
            overwrite=True,
        )
        url = result["secure_url"]
        print(f"[Cloudinary] アップロード完了: {url}")
        return url
