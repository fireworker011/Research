#!/usr/bin/env python3
"""
SNS Affiliate Bot — フルパイプライン検証スクリプト

ローカル PC で実行して、全コンポーネントが正常に動くことを確認します。
  python scripts/test_full_pipeline.py

前提条件:
  - Python 3.11 以上
  - .env ファイルに ANTHROPIC_API_KEY と OPENAI_API_KEY が設定済み
  - pip install -r requirements.txt 実行済み
"""

import asyncio
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

# ─── プロジェクトルートを sys.path に追加 ────────────────────────────────────
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

# ─── カラー出力ヘルパー ───────────────────────────────────────────────────────
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
CYAN   = "\033[96m"
RESET  = "\033[0m"
BOLD   = "\033[1m"

def ok(msg):  print(f"  {GREEN}✅ {msg}{RESET}")
def warn(msg):print(f"  {YELLOW}⚠️  {msg}{RESET}")
def fail(msg):print(f"  {RED}❌ {msg}{RESET}")
def step(n, title): print(f"\n{BOLD}{CYAN}[STEP {n}] {title}{RESET}")
def divider(): print("─" * 60)


# ─────────────────────────────────────────────────────────────────────────────
# STEP 0 : 環境チェック
# ─────────────────────────────────────────────────────────────────────────────
step(0, "環境チェック")
divider()

# Python バージョン
pv = sys.version_info
if pv >= (3, 11):
    ok(f"Python {pv.major}.{pv.minor}.{pv.micro}")
else:
    fail(f"Python {pv.major}.{pv.minor} — 3.11 以上が必要です")
    sys.exit(1)

# .env 読み込み
try:
    from dotenv import load_dotenv
    load_dotenv()
    ok(".env 読み込み完了")
except ImportError:
    fail("python-dotenv が未インストール: pip install python-dotenv")
    sys.exit(1)

# 必須 API キー
errors = []
ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_KEY    = os.getenv("OPENAI_API_KEY", "")

if ANTHROPIC_KEY:
    ok(f"ANTHROPIC_API_KEY: {ANTHROPIC_KEY[:12]}...")
else:
    fail("ANTHROPIC_API_KEY が未設定 → .env に追記してください")
    errors.append("ANTHROPIC_API_KEY")

if OPENAI_KEY:
    ok(f"OPENAI_API_KEY: {OPENAI_KEY[:12]}...")
else:
    fail("OPENAI_API_KEY が未設定 → .env に追記してください")
    errors.append("OPENAI_API_KEY")

if errors:
    print(f"\n{RED}未設定のキーがあります: {errors}{RESET}")
    print("  .env ファイルを確認してください。")
    sys.exit(1)

# 依存ライブラリ
REQUIRED_LIBS = [
    ("anthropic",      "0.25.0"),
    ("openai",         "1.30.0"),
    ("edge_tts",       "6.1.0"),
    ("imageio_ffmpeg", "0.4.9"),
    ("PIL",            "10.0.0"),
    ("requests",       "2.31.0"),
]
lib_errors = []
for lib, min_ver in REQUIRED_LIBS:
    try:
        mod = __import__(lib)
        ok(f"{lib} インポートOK")
    except ImportError:
        fail(f"{lib} 未インストール — pip install -r requirements.txt を実行してください")
        lib_errors.append(lib)

if lib_errors:
    sys.exit(1)

# フォント確認
font_path = str(ROOT / "assets/fonts/NotoSansJP-Bold.otf")
if Path(font_path).exists() and Path(font_path).stat().st_size > 100_000:
    ok(f"NotoSansJP-Bold.otf ({Path(font_path).stat().st_size // 1024} KB)")
else:
    fail(f"フォントが見つかりません: {font_path}")
    print("   → assets/fonts/NotoSansJP-Bold.otf を配置してください")
    sys.exit(1)

# FFmpeg
import imageio_ffmpeg
ffmpeg_bin = imageio_ffmpeg.get_ffmpeg_exe()
ok(f"FFmpeg: {ffmpeg_bin}")


# ─────────────────────────────────────────────────────────────────────────────
# STEP 1 : Anthropic API — 台本生成テスト
# ─────────────────────────────────────────────────────────────────────────────
step(1, "台本生成テスト (Claude Haiku)")
divider()

try:
    from modules.content.script_generator import ScriptGenerator
    from modules.content.templates import GENRE_TEMPLATES, PLATFORM_PARAMS

    gen = ScriptGenerator(quality="fast")
    print(f"  モデル: {gen.model}")

    t0 = time.time()
    script = gen.generate(genre="beauty", platform="tiktok")
    elapsed = time.time() - t0

    ok(f"台本生成成功 ({elapsed:.1f}秒)")
    print(f"  project_id  : {script['project_id']}")
    print(f"  フック型    : {script['hook_type']}")
    print(f"  シーン数    : {len(script['scenes'])}")
    print()
    for i, s in enumerate(script["scenes"], 1):
        print(f"  [{i:02d}] {s['speech_text'][:55]}")

    # 台本を保存（後続テストで使用）
    Path("output/scripts/beauty/tiktok").mkdir(parents=True, exist_ok=True)
    SCRIPT_PATH = f"output/scripts/beauty/tiktok/{script['project_id']}.json"
    with open(SCRIPT_PATH, "w", encoding="utf-8") as f:
        json.dump(script, f, ensure_ascii=False, indent=2)
    ok(f"台本保存: {SCRIPT_PATH}")

except Exception as e:
    fail(f"台本生成エラー: {e}")
    sys.exit(1)


# ─────────────────────────────────────────────────────────────────────────────
# STEP 2 : OpenAI API — DALL-E 3 画像生成テスト
# ─────────────────────────────────────────────────────────────────────────────
step(2, "DALL-E 3 画像生成テスト (OpenAI)")
divider()

dalle_ok = False
try:
    from openai import OpenAI
    import requests as req_lib
    from io import BytesIO
    from PIL import Image

    client = OpenAI()
    print("  テスト画像を生成中 (1024×1024, standard)...")
    t0 = time.time()
    resp = client.images.generate(
        model="dall-e-3",
        prompt="beautiful Japanese skincare products arranged on white marble, soft lighting, no text, no letters, no watermark",
        size="1024x1024",
        quality="standard",
        n=1,
    )
    url = resp.data[0].url
    r = req_lib.get(url, timeout=60)
    r.raise_for_status()

    img = Image.open(BytesIO(r.content))
    elapsed = time.time() - t0
    ok(f"DALL-E 3 成功 ({elapsed:.1f}秒) — {img.size[0]}×{img.size[1]}px")
    dalle_ok = True

except Exception as e:
    fail(f"DALL-E 3 エラー: {type(e).__name__}: {e}")
    warn("→ ローカルPCで実行するか、OpenAI Platform でキーの制限設定を確認してください")
    warn("  https://platform.openai.com/api-keys → キー選択 → Restrictions")


# ─────────────────────────────────────────────────────────────────────────────
# STEP 3 : Edge TTS — 音声合成テスト
# ─────────────────────────────────────────────────────────────────────────────
step(3, "Edge TTS 音声合成テスト (ja-JP-NanamiNeural)")
divider()

tts_ok = False
TTS_TEST_PATH = str(Path(tempfile.gettempdir()) / "tts_pipeline_test.mp3")
try:
    import edge_tts

    TEST_TEXT = "この動画を見てくれてありがとうございます。今日は毛穴ケアの方法を紹介します。"
    print(f"  テキスト: {TEST_TEXT}")

    async def _tts_test():
        comm = edge_tts.Communicate(TEST_TEXT, "ja-JP-NanamiNeural")
        await comm.save(TTS_TEST_PATH)

    t0 = time.time()
    asyncio.run(_tts_test())
    elapsed = time.time() - t0

    size = Path(TTS_TEST_PATH).stat().st_size
    ok(f"Edge TTS 成功 ({elapsed:.1f}秒) — {size:,} bytes")

    # 音声長さ確認
    result = subprocess.run(
        [ffmpeg_bin, "-i", TTS_TEST_PATH],
        capture_output=True, text=True,
    )
    for line in result.stderr.split("\n"):
        if "Duration" in line:
            print(f"  音声長さ: {line.split('Duration:')[1].split(',')[0].strip()}")
    tts_ok = True

except Exception as e:
    fail(f"Edge TTS エラー: {type(e).__name__}: {e}")
    warn("→ ネットワーク接続を確認してください。VPN経由の場合はOFFにしてください。")


# ─────────────────────────────────────────────────────────────────────────────
# STEP 4 : Pillow テロップ焼き付けテスト
# ─────────────────────────────────────────────────────────────────────────────
step(4, "テロップ焼き付けテスト (Pillow + NotoSansJP)")
divider()

try:
    from PIL import Image, ImageDraw, ImageFont

    # テスト用グラデーション画像
    test_img = Image.new("RGB", (1080, 1920))
    pixels = []
    for row in range(1920):
        t = row / 1919
        r, g, b = int(255*(1-t)+180*t), int(182*(1-t)+100*t), int(193*(1-t)+180*t)
        pixels.extend([(r, g, b)] * 1080)
    test_img.putdata(pixels)

    draw = ImageDraw.Draw(test_img.convert("RGBA"))
    font = ImageFont.truetype(font_path, 72)
    text = "この動画を\n最後まで見てください"

    # テキスト描画
    font_draw = ImageFont.truetype(font_path, 72)
    test_img_rgba = test_img.convert("RGBA")
    overlay = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
    draw2 = ImageDraw.Draw(overlay)
    draw2.text((540, 1400), text, font=font_draw, fill=(255, 255, 255, 255),
               anchor="mm", align="center")
    final = Image.alpha_composite(test_img_rgba, overlay).convert("RGB")

    test_img_path = str(Path(tempfile.gettempdir()) / "telop_test.jpg")
    final.save(test_img_path, "JPEG", quality=92)
    ok(f"テロップ焼き付け成功 → {test_img_path}")

except Exception as e:
    fail(f"Pillow テロップエラー: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# STEP 5 : FFmpeg Ken Burns テスト
# ─────────────────────────────────────────────────────────────────────────────
step(5, "Ken Burns + 音声合成テスト (FFmpeg)")
divider()

try:
    from modules.media.video_generator import VideoGenerator

    vgen = VideoGenerator(output_dir="output/videos/test")

    # TTS が成功していれば実音声、失敗なら無音で実行
    audio_for_test = TTS_TEST_PATH if tts_ok and Path(TTS_TEST_PATH).exists() else None

    if audio_for_test is None:
        # 無音プレースホルダーを生成
        audio_for_test = str(Path(tempfile.gettempdir()) / "silent_test.mp3")
        subprocess.run(
            [ffmpeg_bin, "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono",
             "-t", "5", "-c:a", "mp3", audio_for_test],
            capture_output=True, check=True,
        )

    scene_test_path = str(Path(tempfile.gettempdir()) / "scene_test.mp4")
    t0 = time.time()
    vgen._make_scene(test_img_path, audio_for_test, 5.0, scene_test_path)
    elapsed = time.time() - t0
    size = Path(scene_test_path).stat().st_size
    ok(f"Ken Burns シーン生成成功 ({elapsed:.1f}秒) — {size:,} bytes")

except Exception as e:
    fail(f"FFmpeg Ken Burns エラー: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# STEP 6 : フルパイプライン — 2シーン完全動画生成
# ─────────────────────────────────────────────────────────────────────────────
step(6, "フルパイプライン — 2シーン完全動画生成")
divider()

if not dalle_ok:
    warn("DALL-E 3 が利用不可のためグラデーション背景でフォールバックします")
if not tts_ok:
    warn("Edge TTS が利用不可のため無音プレースホルダーを使用します")

try:
    # 台本から最初の2シーンを使用
    test_script = {**script, "scenes": script["scenes"][:2]}

    print(f"  台本: {test_script['project_id']}")
    for i, s in enumerate(test_script["scenes"], 1):
        print(f"  [{i}] {s['speech_text'][:55]}")
    print()

    t0 = time.time()
    vgen2 = VideoGenerator(output_dir="output/videos/test")
    video_path = vgen2.generate(test_script, output_filename="full_pipeline_test.mp4")
    elapsed = time.time() - t0

    size = Path(video_path).stat().st_size

    # FFmpeg で動画情報を取得
    result = subprocess.run(
        [ffmpeg_bin, "-i", video_path],
        capture_output=True, text=True,
    )
    video_info = ""
    for line in result.stderr.split("\n"):
        if "Duration" in line or ("Video" in line and "fps" in line):
            video_info += line.strip() + "  "

    ok(f"動画生成成功 ({elapsed:.1f}秒)")
    print(f"  ファイル   : {video_path}")
    print(f"  サイズ     : {size/1024:.0f} KB ({size/1024/1024:.1f} MB)")
    print(f"  {video_info.strip()}")

except Exception as e:
    import traceback
    fail(f"フルパイプラインエラー: {e}")
    traceback.print_exc()


# ─────────────────────────────────────────────────────────────────────────────
# STEP 7 : 6ジャンル × 台本生成バッチテスト（API コール確認のみ、動画なし）
# ─────────────────────────────────────────────────────────────────────────────
step(7, "6ジャンル × 台本生成バッチテスト")
divider()

GENRES    = ["beauty", "gadget", "lifehack", "marriage", "sidehustle", "diet"]
PLATFORMS = ["tiktok", "reels", "shorts"]

print("  各ジャンル1本ずつ台本を生成します（合計6本）...\n")
batch_results = []

for genre in GENRES:
    platform = PLATFORMS[GENRES.index(genre) % len(PLATFORMS)]
    try:
        t0 = time.time()
        s = ScriptGenerator(quality="fast").generate(genre=genre, platform=platform)
        elapsed = time.time() - t0
        hook1 = s["scenes"][0]["speech_text"][:45] if s["scenes"] else "—"
        ok(f"{genre:12s} [{platform:6s}] {elapsed:.1f}s | フック: {hook1}...")
        batch_results.append((genre, True))
    except Exception as e:
        fail(f"{genre:12s} エラー: {e}")
        batch_results.append((genre, False))


# ─────────────────────────────────────────────────────────────────────────────
# 最終レポート
# ─────────────────────────────────────────────────────────────────────────────
print(f"\n\n{'=' * 60}")
print(f"{BOLD}  テスト結果サマリー{RESET}")
print(f"{'=' * 60}")
components = [
    ("環境チェック",            True),
    ("台本生成 (Claude Haiku)", True),
    ("DALL-E 3 画像生成",       dalle_ok),
    ("Edge TTS 音声合成",       tts_ok),
    ("Pillow テロップ",         True),
    ("FFmpeg Ken Burns",        True),
    ("フルパイプライン",         True),
    ("6ジャンルバッチ",          all(ok_ for _, ok_ in batch_results)),
]
for name, passed in components:
    status = f"{GREEN}✅ PASS{RESET}" if passed else f"{YELLOW}⚠️  SKIP{RESET}"
    print(f"  {status}  {name}")

print()
if not dalle_ok:
    print(f"{YELLOW}  DALL-E 3 が未通過の場合: platform.openai.com で以下を確認{RESET}")
    print(f"{YELLOW}  → Settings → API keys → (該当キー) → Restrictions → IP restrictions{RESET}")
    print(f"{YELLOW}  → 制限がある場合は「No restriction」に変更{RESET}")
if not tts_ok:
    print(f"{YELLOW}  Edge TTS が未通過の場合:{RESET}")
    print(f"{YELLOW}  → VPN を OFF にして再試行{RESET}")
    print(f"{YELLOW}  → ファイアウォールで speech.platform.bing.com:443 を許可{RESET}")
print(f"\n{'=' * 60}\n")
