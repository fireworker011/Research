#!/usr/bin/env python3
"""
SNS Affiliate Bot - メインエントリーポイント
使い方:
  python main.py reel instagram marriage       # Instagram 読むリール（テキストスライドMP4）を生成
  python main.py reel instagram marriage confession dark  # テーマ・タイプ指定
  python main.py post threads career           # Threads にテキスト投稿（確認あり）
  python main.py post video threads career     # Threads に動画投稿（VOICEVOX + Pexels + Cloudinary）
  python main.py post youtube career           # YouTube Shorts を1本作成・アップロード
  python main.py autopost threads career       # Threads に自動投稿（確認なし／タスクスケジューラ用）
  python main.py generate threads career       # Threads 投稿コンテンツを生成してキューに保存
  python main.py generate youtube career       # YouTube 台本を生成してキューに保存
  python main.py run career                    # スケジューラ起動（常時実行）
  python main.py check                         # 環境チェック（API接続確認）
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


def cmd_autopost(platform: str, niche_id: str):
    """確認なしで自動投稿する（Windows タスクスケジューラから呼ばれる）。"""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] 自動投稿開始: {platform}/{niche_id}")

    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    try:
        niche = load_niche(niche_id)

        from ai.provider import AIProvider
        from content.generator import ContentGenerator
        gen = ContentGenerator(niche, AIProvider())

        if platform == "threads":
            content = gen.generate_threads_post()
            from platforms.threads.poster import ThreadsPoster
            poster = ThreadsPoster(niche_id)
            result = poster.post_text(content)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ 投稿完了 post_id={result['post_id']}")
            print(f"  本文（先頭60字）: {content['text'][:60]}")
        else:
            print(f"❌ 未対応のプラットフォーム: {platform}")

    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ エラー: {e}")
        err_log = log_dir / "autopost_errors.log"
        with open(err_log, "a", encoding="utf-8") as f:
            f.write(f"{datetime.now().isoformat()} [{platform}/{niche_id}] {e}\n")
        raise


def cmd_post_video(platform: str, niche_id: str):
    """動画を生成して Threads に投稿する（VOICEVOX + Pexels + Ken Burns + Cloudinary）。"""
    if platform != "threads":
        print(f"❌ video 投稿は現在 threads のみ対応しています。")
        return

    niche = load_niche(niche_id)

    from ai.provider import AIProvider
    from content.generator import ContentGenerator
    gen = ContentGenerator(niche, AIProvider())

    print("台本を生成中...")
    script = gen.generate_threads_video_script()

    print(f"\n--- 生成された台本 ---")
    print(f"キャプション（先頭100字）: {script['caption'][:100]}...")
    for i, scene in enumerate(script["scenes"]):
        text_preview = scene["text"][:40].replace("\n", " / ")
        print(f"  シーン{i+1}: {text_preview}... ({scene.get('duration_sec', '?')}秒)")

    confirm = input("\n動画を生成・Cloudinaryアップロード・Threads投稿しますか？ [y/N]: ").strip().lower()
    if confirm != "y":
        print("キャンセルしました。")
        return

    from video.composer import VideoComposer
    from video.cloudinary_uploader import CloudinaryUploader
    from platforms.threads.poster import ThreadsPoster

    print("\n動画を生成中... (VOICEVOX + Pexels + FFmpeg Ken Burns)")
    composer = VideoComposer()
    filename = f"threads_video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
    video_path = composer.compose(script, filename)
    print(f"動画生成完了: {video_path}")

    print("Cloudinary にアップロード中...")
    uploader = CloudinaryUploader()
    video_url = uploader.upload_video(video_path)

    print("Threads に投稿中...")
    content = {"text": script["caption"]}
    poster = ThreadsPoster(niche_id)
    result = poster.post_video(content, video_url)
    print(f"✅ 動画投稿完了: post_id={result['post_id']}")


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


def cmd_reel_instagram(niche_id: str, content_type: str = None, theme: str = "dark"):
    """Instagram 読むリール（テキストスライド型MP4）を生成する。"""
    niche = load_niche(niche_id)

    from ai.provider import AIProvider
    from content.generator import ContentGenerator
    from video.instagram_reel import InstagramReelGenerator

    gen = ContentGenerator(niche, AIProvider())
    print(f"スライド台本を生成中... (theme={theme})")
    script = gen.generate_instagram_reel_script(content_type)

    print(f"\n--- スライド構成 ({script['content_type']}) ---")
    for i, s in enumerate(script["slides"], 1):
        preview = s["text"].replace("\n", " / ")[:60]
        print(f"  [{i}] {preview}  ({s['duration']}秒)")
    print(f"\nキャプション（先頭80字）: {script['caption'][:80]}...")

    confirm = input("\nこの構成でMP4を生成しますか？ [y/N]: ").strip().lower()
    if confirm != "y":
        print("キャンセルしました。")
        return

    reel_gen = InstagramReelGenerator()
    filename = f"instagram_reel_{niche_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
    video_path = reel_gen.generate(script["slides"], filename, theme=theme)

    print(f"\n✅ MP4生成完了: {video_path}")
    print(f"\n--- Instagramキャプション（コピペ用）---")
    print(script["caption"])
    print("---")


def cmd_run(niche_id: str):
    niche = load_niche(niche_id)
    schedule_cfg = load_schedule()

    from scheduler.runner import SchedulerRunner
    runner = SchedulerRunner(schedule_cfg, niche)
    runner.setup()
    runner.run_forever()


def cmd_check():
    print("=== 環境チェック ===\n")

    # 共通・インフラ系
    common_checks = [
        ("PEXELS_API_KEY",        "Pexels API（画像取得）"),
        ("A8_AFFILIATE_ID",       "A8.net Affiliate ID"),
        ("VOICEVOX_URL",          "VOICEVOX URL（動画音声）"),
        ("CLOUDINARY_CLOUD_NAME", "Cloudinary Cloud Name"),
        ("CLOUDINARY_API_KEY",    "Cloudinary API Key"),
        ("CLOUDINARY_API_SECRET", "Cloudinary API Secret"),
    ]
    # ニッチ別アカウント
    niche_checks = {
        "career（転職×AI）": [
            ("THREADS_CAREER_USER_ID",     "Threads User ID"),
            ("THREADS_CAREER_ACCESS_TOKEN","Threads Access Token"),
            ("YOUTUBE_CAREER_CHANNEL_ID",  "YouTube Channel ID"),
        ],
        "marriage（婚活×マッチング）": [
            ("THREADS_MARRIAGE_USER_ID",      "Threads User ID"),
            ("THREADS_MARRIAGE_ACCESS_TOKEN", "Threads Access Token"),
            ("YOUTUBE_MARRIAGE_CHANNEL_ID",   "YouTube Channel ID"),
        ],
    }
    optional_checks = [
        ("SEEDANCE_API_KEY", "Seedance 2.0 API Key (fal.ai)  ← 動画品質向上"),
    ]

    all_ok = True
    print("  ─── 共通 ───")
    for env_key, label in common_checks:
        val = os.getenv(env_key, "")
        status = "✅" if val else "❌"
        display = val[:20] + "..." if val and len(val) > 20 else (val or "未設定")
        print(f"  {status} {label}: {display}")
        if not val:
            all_ok = False

    for niche_label, checks in niche_checks.items():
        print(f"\n  ─── {niche_label} ───")
        for env_key, label in checks:
            val = os.getenv(env_key, "")
            status = "✅" if val else "⚪"
            display = val[:20] + "..." if val and len(val) > 20 else (val or "未設定")
            print(f"  {status} {label} ({env_key}): {display}")

    print("\n  ─── オプション ───")
    for env_key, label in optional_checks:
        val = os.getenv(env_key, "")
        status = "✅" if val else "⚪"
        display = val[:20] + "..." if val and len(val) > 20 else (val or "未設定（Ken Burnsで動作）")
        print(f"  {status} {label}: {display}")

    print()
    from video.voicevox import VoiceVox
    vvx = VoiceVox()
    vvx_ok = vvx.is_available()
    print(f"  {'✅' if vvx_ok else '⚠️ '} VOICEVOX サーバー: {'起動中' if vvx_ok else '未起動（動画生成時に必要）'}")

    for niche_id in ("career", "marriage"):
        creds = Path(f"config/credentials/youtube_{niche_id}.json")
        print(f"  {'✅' if creds.exists() else '⚪ '} YouTube 認証ファイル ({niche_id}): "
              f"{'あり' if creds.exists() else 'なし'}")

    seedance_key = os.getenv("SEEDANCE_API_KEY", "")
    print(f"  {'✅' if seedance_key else '⚪ '} Seedance 動画モード: "
          f"{'有効（AI動画生成）' if seedance_key else '無効（Ken Burns フォールバック）'}")

    print()
    if all_ok:
        print("🚀 共通設定OK！")
        print("   career: python main.py post threads career")
        print("   marriage: python main.py post threads marriage")
    else:
        print("⚠️  共通設定に未設定の項目があります。")


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return

    cmd = args[0]

    if cmd == "reel" and len(args) >= 3 and args[1] == "instagram":
        content_type = args[3] if len(args) >= 4 else None
        theme = args[4] if len(args) >= 5 else "dark"
        cmd_reel_instagram(args[2], content_type, theme)
    elif cmd == "post" and len(args) >= 4 and args[1] == "video":
        cmd_post_video(args[2], args[3])
    elif cmd == "post" and len(args) >= 3:
        cmd_post(args[1], args[2])
    elif cmd == "autopost" and len(args) >= 3:
        cmd_autopost(args[1], args[2])
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
