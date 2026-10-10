"""テロップと画面演出を乗せて、6秒ごとに書き出して結合する。"""

from __future__ import annotations

import subprocess
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from irasutoya_short.audio import write_wav
from irasutoya_short.backgrounds import concentration, render_bg
from irasutoya_short.constants import FONT_CANDIDATES, FPS, HEIGHT, SAMPLE_RATE, WIDTH
from irasutoya_short.sprites import load_rgba, mouth_levels, scale_rgba

TELOP_COLORS = {
    "hook": (255, 226, 40, 255),
    "punch": (255, 226, 40, 255),
    "close": (255, 226, 40, 255),
    "develop": (255, 255, 255, 255),
    "credit": (255, 255, 255, 255),
}


def find_font(size: int) -> ImageFont.FreeTypeFont:
    for path in FONT_CANDIDATES:
        if Path(path).is_file():
            return ImageFont.truetype(path, size=size)
    return ImageFont.load_default()


def blit(dst: np.ndarray, src: np.ndarray, x: int, y: int) -> None:
    sh, sw = src.shape[:2]
    dh, dw = dst.shape[:2]
    x0, y0 = int(x), int(y)
    sx0, sy0 = max(0, -x0), max(0, -y0)
    dx0, dy0 = max(0, x0), max(0, y0)
    bw = min(sw - sx0, dw - dx0)
    bh = min(sh - sy0, dh - dy0)
    if bw <= 0 or bh <= 0:
        return
    crop = src[sy0 : sy0 + bh, sx0 : sx0 + bw]
    if crop.shape[2] == 3:
        dst[dy0 : dy0 + bh, dx0 : dx0 + bw] = crop
        return
    alpha = crop[:, :, 3:4].astype(np.float32) / 255.0
    if float(alpha.max()) <= 0:
        return
    base = dst[dy0 : dy0 + bh, dx0 : dx0 + bw].astype(np.float32)
    out = crop[:, :, :3].astype(np.float32) * alpha + base * (1.0 - alpha)
    dst[dy0 : dy0 + bh, dx0 : dx0 + bw] = out.astype(np.uint8)


def _text_size(font: ImageFont.ImageFont, text: str) -> tuple[int, int]:
    dummy = Image.new("RGB", (8, 8))
    draw = ImageDraw.Draw(dummy)
    box = draw.multiline_textbbox((0, 0), text, font=font, spacing=8)
    return box[2] - box[0], box[3] - box[1]


def render_telop(text: str, role: str, width: int, height: int, scale: float, y_ratio: float) -> np.ndarray:
    overlay = np.zeros((height, width, 4), dtype=np.uint8)
    if not text.strip():
        return overlay
    max_w = int(width * 0.88)
    start = 64 if role == "credit" else 78
    size = max(28, int(start * scale))
    font = find_font(size)
    while size > 28:
        font = find_font(size)
        tw, th = _text_size(font, text)
        if tw <= max_w and th <= int(height * 0.28):
            break
        size -= 2
    tw, th = _text_size(font, text)
    pad_x, pad_y = 28, 18
    bar_w = min(width - 40, tw + pad_x * 2)
    bar_h = th + pad_y * 2
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    cx = width // 2
    top = int(height * y_ratio - bar_h / 2)
    top = max(8, min(height - bar_h - 8, top))
    left = cx - bar_w // 2
    draw.rounded_rectangle((left, top, left + bar_w, top + bar_h), radius=22, fill=(0, 0, 0, 170))
    fill = TELOP_COLORS.get(role, (255, 255, 255, 255))
    tx = cx - tw // 2
    ty = top + pad_y - 4
    stroke = 5 if role != "credit" else 3
    for dx in range(-stroke, stroke + 1):
        for dy in range(-stroke, stroke + 1):
            if dx * dx + dy * dy > stroke * stroke:
                continue
            draw.multiline_text((tx + dx, ty + dy), text, font=font, fill=(0, 0, 0, 255), spacing=8, align="center")
    draw.multiline_text((tx, ty), text, font=font, fill=fill, spacing=8, align="center")
    return np.array(img)


@lru_cache(maxsize=32)
def _label(text: str) -> np.ndarray:
    font = find_font(36)
    tw, th = _text_size(font, text)
    img = Image.new("RGBA", (tw + 36, th + 20), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle((0, 0, img.width - 1, img.height - 1), radius=12, fill=(220, 60, 30, 230))
    draw.text((18, 6), text, font=font, fill=(255, 255, 255, 255))
    return np.array(img)


def _zoom(frame: np.ndarray, zoom: float) -> np.ndarray:
    if zoom <= 1.01:
        return frame
    h, w = frame.shape[:2]
    cw, ch = int(w / zoom), int(h / zoom)
    x0, y0 = (w - cw) // 2, (h - ch) // 2
    crop = frame[y0 : y0 + ch, x0 : x0 + cw]
    im = Image.fromarray(crop, "RGB").resize((w, h), Image.Resampling.BILINEAR)
    return np.array(im)


def _shake(frame: np.ndarray, amp: int, t: float) -> np.ndarray:
    if amp <= 0:
        return frame
    dx = int(amp * np.sin(t * 47))
    dy = int(amp * np.cos(t * 33))
    return np.roll(np.roll(frame, dy, axis=0), dx, axis=1)


class SpriteBook:
    def __init__(self, assets: dict[str, str]) -> None:
        self.raw = {key: load_rgba(path) for key, path in assets.items()}
        self.cache: dict[tuple, list[np.ndarray]] = {}

    def frames(self, asset_id: str, height: int) -> list[np.ndarray]:
        key = ("mouth", asset_id, height)
        if key not in self.cache:
            levels, _anchor = mouth_levels(self.raw[asset_id])
            self.cache[key] = [scale_rgba(frame, height) for frame in levels]
        return self.cache[key]

    def still(self, asset_id: str, height: int) -> np.ndarray:
        key = ("still", asset_id, height)
        if key not in self.cache:
            self.cache[key] = [scale_rgba(self.raw[asset_id], height)]
        return self.cache[key][0]


def _char_height(scene: dict, frame_h: int) -> int:
    count = len(scene["characters"])
    if scene["bg"] == "chat":
        return int(frame_h * 0.36)
    if count >= 2:
        return int(frame_h * 0.50)
    return int(frame_h * 0.60)


def _place_characters(frame, scene, book: SpriteBook, openness: float, mouth_gain: float, layout: dict) -> None:
    chars = scene["characters"]
    if not chars:
        return
    height = _char_height(scene, frame.shape[0])
    foot = int(frame.shape[0] * (0.70 if scene["bg"] == "chat" else 0.76))
    xs = _xs(len(chars), frame.shape[1], layout, scene["bg"])
    for index, ch in enumerate(chars):
        talking = _talking(ch, scene, index)
        level = float(np.clip(openness * mouth_gain, 0, 1)) if talking else 0.0
        frames = book.frames(ch["id"], height)
        pick = int(round(level * (len(frames) - 1)))
        sprite = frames[pick]
        x = int(xs[index] - sprite.shape[1] / 2)
        y = foot - sprite.shape[0]
        if talking:
            y += int(level * 8)
        blit(frame, sprite, x, y)
        if ch.get("label"):
            tag = _label(ch["label"])
            blit(frame, tag, x + sprite.shape[1] // 2 - tag.shape[1] // 2, max(0, y - tag.shape[0] - 6))


def _talking(ch: dict, scene: dict, index: int) -> bool:
    if scene["speaker"] == "narrator":
        return index == 0
    return ch.get("who") == scene["speaker"]


def _xs(count: int, width: int, layout: dict, bg: str) -> list[int]:
    if bg == "chat":
        return [int(width * 0.22)]
    if count == 1:
        return [int(width * layout.get("character_x_ratio", 0.5))]
    return [int(width * 0.32), int(width * 0.72)]


def _draw_papers(frame: np.ndarray, scene: dict) -> None:
    if "papers" not in scene.get("code_props", []):
        return
    h, w = frame.shape[:2]
    img = Image.fromarray(frame, "RGB")
    draw = ImageDraw.Draw(img)
    x0, y0 = int(w * 0.58), int(h * 0.58)
    for i, color in enumerate(((236, 236, 240), (248, 248, 252), (255, 255, 255))):
        ox, oy = i * 16, -i * 12
        box = (x0 + ox, y0 + oy, x0 + ox + 250, y0 + oy + 300)
        draw.rounded_rectangle(box, radius=8, fill=color, outline=(40, 40, 40), width=4)
        for k in range(6):
            yy = box[1] + 36 + k * 38
            draw.line((box[0] + 24, yy, box[2] - 24, yy), fill=(190, 190, 196), width=4)
    frame[:] = np.array(img)


def _place_props(frame, scene, book: SpriteBook) -> None:
    for i, prop in enumerate(scene.get("props") or []):
        if prop not in book.raw:
            continue
        sprite = book.still(prop, int(frame.shape[0] * 0.22))
        x = int(frame.shape[1] * 0.72 - sprite.shape[1] / 2 + i * 20)
        y = int(frame.shape[0] * 0.74) - sprite.shape[0]
        blit(frame, sprite, x, y)


def compose_frame(scene, book, bg, lines, telop, openness, mouth_gain, layout, local_t) -> np.ndarray:
    frame = bg.copy()
    if scene["effect"] == "lines" or scene["bg"] == "lines":
        blit(frame, lines, 0, 0)
    _draw_papers(frame, scene)
    _place_props(frame, scene, book)
    _place_characters(frame, scene, book, openness, mouth_gain, layout)
    slide = int(30 * max(0.0, 1.0 - local_t / 0.16))
    blit(frame, telop, 0, slide)
    zoom = 1.0
    if scene["effect"] in ("zoom", "zoom_shake"):
        p = min(1.0, local_t / max(scene["duration"], 0.01))
        zoom = 1.0 + 0.08 * np.sin(p * np.pi)
    amp = 12 if scene["effect"] in ("shake", "zoom_shake") else 0
    frame = _shake(frame, amp, local_t)
    return _zoom(frame, float(zoom))


def render_movie(project: dict, out_path: Path, preview_dir: Path | None = None) -> None:
    scenes = project["scenes"]
    settings = project["settings"]
    layout = project["layout"]
    book = SpriteBook(project["asset_paths"])
    bgs = {name: render_bg(name) for name in {s["bg"] for s in scenes}}
    lines = concentration()
    telops = [
        render_telop(s["telop"], s["role"], WIDTH, HEIGHT, settings["telop_scale"], layout["telop_y_ratio"] if s["role"] != "credit" else 0.5)
        for s in scenes
    ]
    nframes = sum(int(round(s["duration"] * FPS)) for s in scenes)
    audio = project["audio"]
    if preview_dir is not None:
        preview_dir.mkdir(parents=True, exist_ok=True)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    chunk_dir = out_path.parent / "chunks"
    chunk_dir.mkdir(exist_ok=True)
    chunk_frames = int(round(project.get("chunk_seconds", 6) * FPS))
    paths: list[Path] = []
    scene_i = 0
    scene_frame = 0
    scene_len = int(round(scenes[0]["duration"] * FPS))
    for start in range(0, nframes, chunk_frames):
        end = min(nframes, start + chunk_frames)
        frames: list[np.ndarray] = []
        for _ in range(start, end):
            if scene_frame >= scene_len and scene_i < len(scenes) - 1:
                scene_i += 1
                scene_frame = 0
                scene_len = int(round(scenes[scene_i]["duration"] * FPS))
            scene = scenes[scene_i]
            env = scene["envelope"]
            openness = float(env[scene_frame]) if scene_frame < len(env) else 0.0
            local_t = scene_frame / FPS
            frame = compose_frame(
                scene, book, bgs[scene["bg"]], lines, telops[scene_i],
                openness, settings["mouth_gain"], layout, local_t,
            )
            if preview_dir is not None and scene_frame == min(8, max(0, scene_len // 3)):
                Image.fromarray(frame, "RGB").save(preview_dir / f"scene_{scene['id']:02d}.png")
            frames.append(frame)
            scene_frame += 1
        audio_slice = _slice_audio(audio, start, end)
        chunk_path = chunk_dir / f"chunk_{start:05d}.mp4"
        _encode(frames, audio_slice, chunk_path)
        paths.append(chunk_path)
        print(f"chunk {len(paths)}: frames {start}-{end}", flush=True)
    _concat(paths, out_path)


def _slice_audio(audio: np.ndarray, start: int, end: int) -> np.ndarray:
    a = int(start / FPS * SAMPLE_RATE)
    b = int(end / FPS * SAMPLE_RATE)
    return audio[a:b]


def _encode(frames: list[np.ndarray], audio: np.ndarray, path: Path) -> None:
    wav_path = path.with_suffix(".wav")
    write_wav(wav_path, audio)
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{WIDTH}x{HEIGHT}", "-r", str(FPS),
        "-i", "pipe:0",
        "-i", str(wav_path),
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "160k",
        "-shortest",
        str(path),
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    assert proc.stdin is not None
    for frame in frames:
        proc.stdin.write(frame.tobytes())
    proc.stdin.close()
    code = proc.wait()
    wav_path.unlink(missing_ok=True)
    if code != 0:
        raise RuntimeError(f"ffmpeg が失敗しました: {path}")


def _concat(paths: list[Path], out_path: Path) -> None:
    if len(paths) == 1:
        paths[0].replace(out_path)
        return
    listing = out_path.with_suffix(".txt")
    listing.write_text("".join(f"file '{p}'\n" for p in paths), encoding="utf-8")
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "concat", "-safe", "0", "-i", str(listing),
        "-c", "copy", str(out_path),
    ]
    subprocess.run(cmd, check=True)
    listing.unlink(missing_ok=True)
