#!/usr/bin/env python3
"""
SNS Affiliate Bot - メインエントリーポイント
使い方:
  python main.py post threads career     # Threads に1投稿
  python main.py post youtube career     # YouTube Shorts を1本作成・アップロード
  python main.py generate threads career # Threads 投稿コンテンツを生成してキューに保存
  python main.py generate youtube career # YouTube 台本を生成してキューに保存
  python main.py run career              # スケジューラ起動（常時実行）
  python main.py check                   # 環境チェック（API接続確認）
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def load_niche(niche_id: str) -> dict:
    path = Path(f"config/niches/{niche_id}.json")
    if not path.exists():
        available = [p.stem for p in Path("config/niches").glob("*.json")]
        raise FileNotFoundError(
            f"ニッチ設定が見つかりません: {niche_id}\n"
            f"利用可能: {available}"
        )
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_schedule() -> dict:
    with open("config/schedule.json", encoding="utf-8") as f:
        return json.load(f)


def cmd_post(platform: str, niche_id: str):
    niche = load_niche(niche_id)

    from ai.provider import AIProvider
    from content.generator import ContentGenerator
    ai = AIProvider()
    gen = ContentGenerator(niche, ai)

    if platform == "threads":
        content = gen.generate_threads_post()
        print(f"\n--- 生成されたコンテンツ ---\n{content['text']}\n")
        confirm = input("このコンテンツを投稿しますか？ [y/N]: ").strip().lower()
        if confirm == "y":
            from platforms.threads.poster import ThreadsPoster
            poster = ThreadsPoster(niche_id)
            result = poster.post_text(content)
            print(f"✅ 投稿完了: post_id={result['post_id']}")
        else:
            print("投稿をキャンセルしました。")

    elif platform == "youtube":
        script = gen.generate_youtube_script()
        print(f"\n--- 生成された台本 ---")
        print(f"タイトル: {script['title']}")
        for scene in script["scenes"]:
            print(f"[{scene['type']}] {scene['text'][:50]}... ({scene.get('duration_sec', '?')}秒)")
        confirm = input("\n動画を生成・アップロードしますか？ [y/N]: ").strip().lower()
        if confirm == "y":
            from video.composer import VideoComposer
            from platforms.youtube.uploader import YouTubeUploader
            print("動画を生成中... (VOICEVOX + Pexels + FFmpeg)")
            composer = VideoComposer()
            filename = f"short_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
            video_path = composer.compose(script, filename)
            print(f"動画生成完了: {video_path}")
            uploader = YouTubeUploader(niche)
            result = uploader.upload_short(video_path, script, privacy="private")
            print(f"✅ アップロード完了: {result['video_url']}")
        else:
            print("アップロードをキャンセルしました。")


def cmd_generate(platform: str, niche_id: str, count: int = 7):
    niche = load_niche(niche_id)
    queue_dir = Path(f"queue/{platform}/{niche_id}")
    queue_dir.mkdir(parents=True, exist_ok=True)

    from ai.provider import AIProvider
    from content.generator import ContentGenerator
    gen = ContentGenerator(niche, AIProvider())

    print(f"{platform} / {niche_id} のコンテンツを {count} 件生成します...")
    for i in range(count):
        if platform == "threads":
            content = gen.generate_threads_post()
        else:
            content = gen.generate_youtube_script()
        filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i:02d}.json"
        filepath = queue_dir / filename
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(content, f, ensure_ascii=False, indent=2)
        print(f"  [{i+1}/{count}] 保存: {filepath.name}")

    print(f"✅ {count} 件のコンテンツを queue/{platform}/{niche_id}/ に保存しました。")


def cmd_run(niche_id: str):
    niche = load_niche(niche_id)
    schedule_cfg = load_schedule()

    from scheduler.runner import SchedulerRunner
    runner = SchedulerRunner(schedule_cfg, niche)
    runner.setup()
    runner.run_forever()


def cmd_check():
    print("=== 環境チェック ===\n")
    checks = [
        ("PEXELS_API_KEY", "Pexels API"),
        ("THREADS_CAREER_USER_ID", "Threads (career) User ID"),
        ("THREADS_CAREER_ACCESS_TOKEN", "Threads (career) Access Token"),
        ("YOUTUBE_CAREER_CHANNEL_ID", "YouTube (career) Channel ID"),
        ("A8_AFFILIATE_ID", "A8.net Affiliate ID"),
        ("VOICEVOX_URL", "VOICEVOX URL"),
    ]
    all_ok = True
    for env_key, label in checks:
        val = os.getenv(env_key, "")
        status = "✅" if val else "❌"
        display = val[:20] + "..." if val and len(val) > 20 else (val or "未設定")
        print(f"  {status} {label}: {display}")
        if not val:
            all_ok = False

    print()
    from video.voicevox import VoiceVox
    vvx = VoiceVox()
    vvx_ok = vvx.is_available()
    print(f"  {'✅' if vvx_ok else '⚠️ '} VOICEVOX サーバー: {'起動中' if vvx_ok else '未起動（動画生成時に必要）'}")

    creds_career = Path("config/credentials/youtube_career.json")
    creds_ok = creds_career.exists()
    print(f"  {'✅' if creds_ok else '❌'} YouTube 認証ファイル (career): "
          f"{'あり' if creds_ok else 'なし → skills/SKILL.md 参照'}")

    print()
    if all_ok and vvx_ok and creds_ok:
        print("🚀 全チェック通過！python main.py post threads career で投稿できます。")
    else:
        print("⚠️  未設定の項目があります。skills/SKILL.md のセットアップ手順を確認してください。")


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return

    cmd = args[0]

    if cmd == "post" and len(args) >= 3:
        cmd_post(args[1], args[2])
    elif cmd == "generate" and len(args) >= 3:
        count = int(args[3]) if len(args) >= 4 else 7
        cmd_generate(args[1], args[2], count)
    elif cmd == "run" and len(args) >= 2:
        cmd_run(args[1])
    elif cmd == "check":
        cmd_check()
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
