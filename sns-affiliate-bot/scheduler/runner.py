import json
import os
import time
from datetime import datetime
from pathlib import Path

import schedule


class SchedulerRunner:
    """
    config/schedule.json の設定にしたがって投稿・アップロードを自動実行する。
    使い方: python main.py run
    """

    def __init__(self, schedule_config: dict, niche_config: dict):
        self.schedule_cfg = schedule_config
        self.niche = niche_config
        self.niche_id = niche_config["id"]

    def setup(self):
        """スケジュールを登録する。"""
        threads_cfg = self.schedule_cfg.get("threads", {}).get(self.niche_id, {})
        youtube_cfg = self.schedule_cfg.get("youtube", {}).get(self.niche_id, {})

        for t in threads_cfg.get("times", []):
            schedule.every().day.at(t).do(self._run_threads_post)
            print(f"[Scheduler] Threads 投稿: 毎日 {t}")

        for t in youtube_cfg.get("times", []):
            schedule.every().day.at(t).do(self._run_youtube_upload)
            print(f"[Scheduler] YouTube アップロード: 毎日 {t}")

    def run_forever(self):
        """スケジューラをループ実行する（Ctrl+C で停止）。"""
        print(f"[Scheduler] 起動しました。スケジュール実行中... (Ctrl+C で停止)")
        try:
            while True:
                schedule.run_pending()
                time.sleep(30)
        except KeyboardInterrupt:
            print("[Scheduler] 停止しました。")

    def _run_threads_post(self):
        from content.generator import ContentGenerator
        from platforms.threads.poster import ThreadsPoster
        from ai.provider import AIProvider

        print(f"[Threads] 投稿開始 {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        try:
            generator = ContentGenerator(self.niche, AIProvider())
            content = generator.generate_threads_post()
            poster = ThreadsPoster(self.niche_id)
            poster.post_text(content)
        except Exception as e:
            print(f"[Threads] エラー: {e}")
            self._log_error("threads", str(e))

    def _run_youtube_upload(self):
        from content.generator import ContentGenerator
        from video.composer import VideoComposer
        from platforms.youtube.uploader import YouTubeUploader
        from ai.provider import AIProvider

        print(f"[YouTube] アップロード開始 {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        try:
            generator = ContentGenerator(self.niche, AIProvider())
            script = generator.generate_youtube_script()

            composer = VideoComposer()
            filename = f"short_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
            video_path = composer.compose(script, filename)

            uploader = YouTubeUploader(self.niche)
            uploader.upload_short(video_path, script)
        except Exception as e:
            print(f"[YouTube] エラー: {e}")
            self._log_error("youtube", str(e))

    def _log_error(self, platform: str, message: str):
        log_dir = Path(f"queue/{platform}/{self.niche_id}/errors")
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(f"{datetime.now().isoformat()}\n{message}")
