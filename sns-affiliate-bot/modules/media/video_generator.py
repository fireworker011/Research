"""
Media Synthesis Module — VideoGenerator

入力 JSON → 縦型ショート動画 (1080×1920 MP4) を完全自動生成。

処理フロー（シーンごと）:
  1. 画像生成   — DALL-E 3 (OpenAI Images API)
                  ※ 画像プロンプトへのテキスト混入を自動除去・禁止指示を付加
  2. 音声合成   — Edge TTS (ja-JP-NanamiNeural)  APIキー不要・無料
  3. テロップ   — Pillow で日本語テキストを画像に焼き付け (NotoSansJP-Bold)
  4. Ken Burns  — FFmpeg でゆっくりズームイン + TTS 音声を合成
  5. 結合       — 全シーン concat → 最終 MP4

使い方:
  gen = VideoGenerator()
  path = gen.generate({
      "project_id": "test_001",
      "scenes": [
          {"image_prompt": "cyberpunk city, neon lights", "speech_text": "人生を変える方法"},
      ]
  })
"""

import asyncio
import os
import re
import subprocess
import tempfile
from io import BytesIO
from pathlib import Path
from typing import Optional

import imageio_ffmpeg
import requests
from openai import OpenAI
from PIL import Image, ImageDraw, ImageFont

# ── 定数 ─────────────────────────────────────────────────────────────────────
WIDTH = 1080
HEIGHT = 1920
FPS = 25
TTS_VOICE = "ja-JP-NanamiNeural"          # Edge TTS 日本語女性音声（高品質）
DALL_E_MODEL = "dall-e-3"
DALL_E_SIZE = "1024x1792"                 # 縦型 9:16 に最も近い DALL-E 3 サイズ

_FONT_CANDIDATES = [
    str(Path(__file__).parent.parent.parent / "assets/fonts/NotoSansJP-Bold.otf"),
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.otf",
    r"C:\Windows\Fonts\YuGothB.ttc",
    r"C:\Windows\Fonts\meiryo.ttc",
]

# 画像プロンプトに混入させてはいけないキーワード
_TEXT_INJECTION_RE = re.compile(
    r'\b(text|words?|letters?|caption|subtitle|label|title|heading|'
    r'sign\s+saying|writing|written|typed|printed|'
    r'japanese\s+text|kanji|hiragana|katakana|chinese\s+character)\b',
    re.IGNORECASE,
)


# ── ユーティリティ ─────────────────────────────────────────────────────────────
def _find_font() -> str:
    for path in _FONT_CANDIDATES:
        if os.path.exists(path):
            return path
    return ""


def _sanitize_prompt(prompt: str) -> str:
    """画像プロンプトからテキスト描画指示を除去し、テキストなし指示を末尾に付加する。"""
    cleaned = _TEXT_INJECTION_RE.sub("", prompt)
    cleaned = re.sub(r",\s*,", ",", cleaned).strip().strip(",").strip()
    return cleaned + ", no text, no letters, no words, no watermark, no UI"


def _audio_duration(ffmpeg_bin: str, audio_path: str) -> float:
    """音声ファイルの長さ（秒）を FFmpeg から取得する。"""
    result = subprocess.run(
        [ffmpeg_bin, "-i", audio_path],
        capture_output=True, text=True,
    )
    for line in result.stderr.split("\n"):
        if "Duration" in line:
            try:
                dur_str = line.split("Duration:")[1].split(",")[0].strip()
                h, m, s = dur_str.split(":")
                return float(h) * 3600 + float(m) * 60 + float(s)
            except Exception:
                pass
    return 5.0  # 取得失敗時のフォールバック


def _wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    """日本語テキストを max_width px に収まるよう折り返す。"""
    lines = []
    for raw in text.split("\n"):
        raw = raw.strip()
        if not raw:
            lines.append("")
            continue
        current = ""
        for ch in raw:
            test = current + ch
            bbox = font.getbbox(test)
            if bbox[2] - bbox[0] > max_width and current:
                lines.append(current)
                current = ch
            else:
                current = test
        if current:
            lines.append(current)
    return lines


def _generate_gradient_image(output_path: str, genre: str = ""):
    """
    DALL-E 3 が利用できない場合のフォールバック。
    ジャンルに合わせた色のグラデーション背景を生成する。
    """
    _GENRE_COLORS = {
        "beauty":     ((255, 182, 193), (255, 105, 180)),   # ピンク系
        "gadget":     ((30, 30, 60),   (0, 120, 200)),       # ダーク青
        "lifehack":   ((255, 200, 100), (255, 120, 30)),      # オレンジ
        "marriage":   ((200, 160, 220), (150, 80, 180)),      # 紫・ロマンス
        "sidehustle": ((30, 50, 30),   (50, 160, 80)),        # ダーク緑
        "diet":       ((180, 230, 160), (60, 180, 80)),       # グリーン
    }
    col_top, col_bot = _GENRE_COLORS.get(genre, ((40, 40, 60), (100, 60, 120)))

    _img = Image.new("RGB", (WIDTH, HEIGHT))
    _pixels = []
    for _row in range(HEIGHT):
        _t = _row / (HEIGHT - 1)
        _r = int(col_top[0] * (1 - _t) + col_bot[0] * _t)
        _g = int(col_top[1] * (1 - _t) + col_bot[1] * _t)
        _b = int(col_top[2] * (1 - _t) + col_bot[2] * _t)
        _pixels.extend([(_r, _g, _b)] * WIDTH)
    _img.putdata(_pixels)
    _img.save(output_path, "JPEG", quality=92)


def _make_gradient(width: int, height: int, max_alpha: int = 190) -> Image.Image:
    """下方向に濃くなる黒グラデーション画像 (RGBA) を生成する。"""
    grad = Image.new("RGBA", (width, height))
    pixels = []
    for row in range(height):
        alpha = int(max_alpha * row / max(height - 1, 1))
        pixels.extend([(0, 0, 0, alpha)] * width)
    grad.putdata(pixels)
    return grad


# ── メインクラス ──────────────────────────────────────────────────────────────
class VideoGenerator:
    """
    スクリプト JSON → 縦型ショート動画 (1080×1920 MP4) を自動生成。

    Args:
        output_dir: 完成 MP4 の保存先ディレクトリ
    """

    def __init__(self, output_dir: str = "output/videos"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.client = OpenAI()                     # OPENAI_API_KEY 環境変数を参照
        self.ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
        self.font_path = _find_font()

    def generate(
        self,
        script: dict,
        output_filename: Optional[str] = None,
    ) -> str:
        """
        スクリプトから動画を生成して MP4 パスを返す。

        Args:
            script: {
                "project_id": "test_001",
                "scenes": [
                    {"image_prompt": "...", "speech_text": "..."},
                    ...
                ]
            }
            output_filename: 省略時は project_id + タイムスタンプで自動命名
        """
        from datetime import datetime

        project_id = script.get("project_id", "video")
        scenes = script["scenes"]

        if not output_filename:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"{project_id}_{ts}.mp4"

        print(f"\n🎬 動画生成開始: {project_id}  ({len(scenes)} シーン)")

        genre = script.get("genre", "")

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            scene_paths = []

            for i, scene in enumerate(scenes):
                print(f"\n  ▶ シーン {i+1}/{len(scenes)}")
                sp = self._process_scene(scene, i, tmp, genre)
                scene_paths.append(sp)

            output_path = str(self.output_dir / output_filename)
            print(f"\n  🔗 シーン結合中...")
            self._concat_scenes(scene_paths, output_path)

        print(f"\n✅ 完了: {output_path}\n")
        return output_path

    # ── シーン処理 ──────────────────────────────────────────────────────────
    def _process_scene(self, scene: dict, idx: int, tmp: Path, genre: str = "") -> str:
        prompt = scene.get("image_prompt", "")
        speech = scene.get("speech_text", "")

        # 1. 画像生成 (DALL-E 3 or フォールバック)
        raw_img = str(tmp / f"img_{idx:02d}_raw.jpg")
        print(f"    [1/3] 画像生成中... (DALL-E 3)")
        self._generate_image(_sanitize_prompt(prompt), raw_img, genre)

        # 2. テロップ焼き付け (Pillow)
        print(f"    [2/3] テロップ合成中...")
        img_with_text = str(tmp / f"img_{idx:02d}.jpg")
        self._burn_caption(raw_img, speech, img_with_text)

        # 3. TTS 音声生成 (Edge TTS)
        audio_path = str(tmp / f"audio_{idx:02d}.mp3")
        print(f"    [3/3] 音声生成中... (Edge TTS)")
        duration = self._generate_tts(speech, audio_path)

        # 4. Ken Burns + 音声合成 → シーン MP4
        scene_path = str(tmp / f"scene_{idx:02d}.mp4")
        self._make_scene(img_with_text, audio_path, duration, scene_path)

        return scene_path

    # ── 画像生成 ─────────────────────────────────────────────────────────────
    def _generate_image(self, prompt: str, output_path: str, genre: str = ""):
        """
        DALL-E 3 で縦型画像を生成して保存する。
        API が利用不可の場合はグラデーション背景にフォールバックする。
        """
        try:
            response = self.client.images.generate(
                model=DALL_E_MODEL,
                prompt=prompt,
                size=DALL_E_SIZE,
                quality="standard",
                n=1,
            )
            url = response.data[0].url
            r = requests.get(url, timeout=60)
            r.raise_for_status()
            img = Image.open(BytesIO(r.content)).resize((WIDTH, HEIGHT), Image.LANCZOS)
            img.save(output_path, "JPEG", quality=92)
        except Exception as e:
            print(f"    ⚠️  DALL-E 3 unavailable ({type(e).__name__}), グラデーション背景を使用")
            _generate_gradient_image(output_path, genre)

    # ── テロップ焼き付け ────────────────────────────────────────────────────
    def _burn_caption(self, img_path: str, text: str, output_path: str):
        """
        Pillow で日本語テロップを画像に焼き付ける。
        - 下部にグラデーションを敷いて視認性を確保
        - テキストは下部 30% 中央に配置
        - ドロップシャドウで立体感を付与
        """
        img = Image.open(img_path).convert("RGBA")

        if not text or not self.font_path:
            img.convert("RGB").save(output_path, "JPEG", quality=92)
            return

        draw = ImageDraw.Draw(img)
        margin_x = int(WIDTH * 0.06)
        max_text_w = WIDTH - margin_x * 2

        # フォントサイズを行数に応じて自動決定
        n_lines_hint = len(text.split("\n"))
        base_size = 74 if n_lines_hint <= 2 else (62 if n_lines_hint <= 4 else 50)

        for fontsize in range(base_size, 26, -4):
            font = ImageFont.truetype(self.font_path, fontsize)
            lines = _wrap_text(text, font, max_text_w)
            line_h = int(fontsize * 1.85)
            total_h = len(lines) * line_h
            if total_h <= HEIGHT * 0.32:
                break

        # 下部グラデーションを合成
        grad_h = int(HEIGHT * 0.38)
        grad = _make_gradient(WIDTH, grad_h)
        img.paste(grad, (0, HEIGHT - grad_h), grad)

        # テキストを下部 30% 中央に配置
        y_start = int(HEIGHT * 0.73) - total_h // 2

        draw = ImageDraw.Draw(img)
        for i, line in enumerate(lines):
            if not line:
                continue
            bbox = font.getbbox(line)
            w = bbox[2] - bbox[0]
            x = (WIDTH - w) // 2
            y = y_start + i * line_h
            # ドロップシャドウ
            draw.text((x + 3, y + 3), line, font=font, fill=(0, 0, 0, 200))
            # 本文（白）
            draw.text((x, y), line, font=font, fill=(255, 255, 255, 255))

        img.convert("RGB").save(output_path, "JPEG", quality=92)

    # ── TTS 音声生成 ────────────────────────────────────────────────────────
    def _generate_tts(self, text: str, output_path: str) -> float:
        """
        Edge TTS で MP3 を生成し、音声長（秒）を返す。
        ネットワーク不可の場合は FFmpeg 無音プレースホルダーにフォールバック。
        """
        duration_estimate = max(2.5, len(text) / 7.0)   # 日本語 7文字/秒 目安

        async def _run():
            import edge_tts
            import edge_tts.communicate as _ec
            _ec._SSL_CTX = False   # プロキシ環境の SSL 検証を無効化
            comm = edge_tts.Communicate(text, TTS_VOICE)
            await comm.save(output_path)

        try:
            try:
                asyncio.run(_run())
            except RuntimeError:
                loop = asyncio.new_event_loop()
                try:
                    loop.run_until_complete(_run())
                finally:
                    loop.close()
            return _audio_duration(self.ffmpeg, output_path)
        except Exception as e:
            print(f"    ⚠️  TTS unavailable ({type(e).__name__}), 無音プレースホルダーを使用")
            return self._generate_silent_audio(output_path, duration_estimate)

    def _generate_silent_audio(self, output_path: str, duration: float) -> float:
        """ネットワーク不可時の音声フォールバック: FFmpeg で無音 MP3 を生成する。"""
        cmd = [
            self.ffmpeg, "-y",
            "-f", "lavfi", "-i", f"anullsrc=r=24000:cl=mono",
            "-t", str(duration),
            "-c:a", "mp3", "-b:a", "64k",
            output_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg silent audio エラー:\n{result.stderr[-500:]}")
        return duration

    # ── シーン動画生成 ──────────────────────────────────────────────────────
    def _make_scene(
        self,
        img_path: str,
        audio_path: str,
        duration: float,
        output: str,
    ):
        """
        Ken Burns エフェクト（ゆっくりズームイン）+ TTS 音声を合成して
        1 シーン分の MP4 を生成する。
        """
        frames = max(1, int((duration + 0.5) * FPS))
        ken_burns = (
            f"zoompan=z='min(zoom+0.0007,1.12)':d={frames}:"
            f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
            f"s={WIDTH}x{HEIGHT},fps={FPS}"
        )
        cmd = [
            self.ffmpeg, "-y",
            "-loop", "1", "-i", img_path,
            "-i", audio_path,
            "-vf", ken_burns,
            "-c:v", "libx264", "-preset", "fast", "-crf", "20",
            "-c:a", "aac", "-b:a", "128k",
            "-shortest", "-pix_fmt", "yuv420p",
            output,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg シーン生成エラー:\n{result.stderr[-1500:]}")

    # ── シーン結合 ──────────────────────────────────────────────────────────
    def _concat_scenes(self, scene_paths: list, output: str):
        """全シーンを連結して最終 MP4 を出力する。"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as f:
            for sp in scene_paths:
                f.write(f"file '{sp.replace(chr(92), '/')}'\n")
            list_file = f.name

        try:
            cmd = [
                self.ffmpeg, "-y",
                "-f", "concat", "-safe", "0", "-i", list_file,
                "-c:v", "libx264", "-preset", "fast", "-crf", "20",
                "-c:a", "aac", "-b:a", "128k",
                "-pix_fmt", "yuv420p",
                output,
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise RuntimeError(f"FFmpeg concat エラー:\n{result.stderr[-1500:]}")
        finally:
            os.unlink(list_file)
