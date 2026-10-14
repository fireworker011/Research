"""VOICEVOX、いらすとや、字幕、ffmpeg で 9:16 の静止画ショートを1本にする。"""

from __future__ import annotations

import json
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from irasutoya_short.audio import fit_length, mix_tracks, read_wav, samples_for_frames, write_wav
from irasutoya_short.backgrounds import render_bg
from irasutoya_short.constants import FPS, HEIGHT, MAX_DURATION, MIN_DURATION, SAMPLE_RATE, WIDTH
from irasutoya_short.layout import default_layout
from irasutoya_short.render import (
    _finish_encoder,
    _light_motion,
    _open_encoder,
    _stop_encoder,
    _text_size,
    _write_frame,
    blit,
    find_font,
)
from irasutoya_short.sfx import bgm_loop, make_sfx
from irasutoya_short.sprites import draw_mouth, load_rgba, mouth_anchor, scale_rgba, skin_color
from irasutoya_short.templates import scale_speeds, scene_speed, settings_for
from irasutoya_short.tts import Speaker

from qa_gate import caption_overlay_has_box, diff_centroid, judge_mouth

CACHE = Path.home() / ".cache" / "irasutoya-short" / "pipeline-assets"
FLOORS = {"hook": 2.15, "develop": 2.35, "punch": 3.6, "credit": 2.2}
PAD_TARGET = 20.6
HOLD = 0.55


def ensure_asset(asset: dict, cache: Path | None = None) -> Path:
    dest_dir = cache or CACHE
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f"{asset['id']}.png"
    if dest.is_file() and dest.stat().st_size > 1000:
        return dest
    request = urllib.request.Request(
        asset["source_url"],
        headers={"User-Agent": "kanememo-pipeline/1.0"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        dest.write_bytes(response.read())
    if dest.stat().st_size < 1000:
        raise RuntimeError(f"素材が取れません: {asset['id']}")
    return dest


def prepare_sprite(rgba: np.ndarray, line: dict, mouth_overlay: bool, height: int) -> tuple[np.ndarray, dict]:
    overlay_used = False
    center = None
    source = rgba
    errors: list[str] = []
    speaking = line["speaker"] not in ("narrator", "") and line["speaker"] == line.get("who")
    if mouth_overlay and speaking:
        anchor = mouth_anchor(rgba)
        if anchor is None:
            errors.append(f"{line['character']} の口の位置が取れない")
        else:
            skin = skin_color(rgba, anchor.x, anchor.y, anchor.width)
            drawn = draw_mouth(rgba, anchor, 0.65, skin)
            center = diff_centroid(rgba, drawn)
            source = drawn
            overlay_used = True
            errors.extend(judge_mouth(rgba, overlay=True, center=center))
    else:
        errors.extend(judge_mouth(rgba, overlay=False, center=None))
        if source is not rgba and not np.array_equal(source, rgba):
            errors.append(f"{line['character']} に口の重ね絵が残っている")
    return scale_rgba(source, height), {
        "character": line.get("character") or "",
        "overlay_used": overlay_used,
        "center": center,
        "errors": errors,
        "checked": True,
    }


def _caption_fill(style: dict, role: str) -> tuple[int, int, int, int]:
    colors = style["colors"]
    if role in colors:
        return colors[role]
    return colors["develop"]


def render_caption(text: str, role: str, style: dict) -> tuple[np.ndarray, dict]:
    overlay = np.zeros((HEIGHT, WIDTH, 4), dtype=np.uint8)
    info = {"role": role, "overflow": False, "has_box": False, "size": 0, "text": text}
    if not text.strip():
        return overlay, info
    fill = _caption_fill(style, role)
    max_w = int(WIDTH * 0.88)
    max_h = int(HEIGHT * 0.28)
    size = int(style["credit_size"] if role == "credit" else style["size"])
    floor = int(style["credit_min_size"] if role == "credit" else style["min_size"])
    font = find_font(size)
    tw, th = _text_size(font, text)
    while size > floor and (tw > max_w or th > max_h):
        size -= 2
        font = find_font(size)
        tw, th = _text_size(font, text)
    y_ratio = float(style["credit_y_ratio"] if role == "credit" else style["y_ratio"])
    top = int(HEIGHT * y_ratio - th / 2)
    top = max(24, min(HEIGHT - th - 36, top))
    left = (WIDTH - tw) // 2
    overflow = tw > max_w or th > max_h or left < 24 or top < 24 or left + tw > WIDTH - 24 or top + th > HEIGHT - 36
    img = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    stroke = int(style["credit_stroke"] if role == "credit" else style["stroke"])
    for dx in range(-stroke, stroke + 1):
        for dy in range(-stroke, stroke + 1):
            if dx * dx + dy * dy > stroke * stroke:
                continue
            draw.multiline_text((left + dx, top + dy), text, font=font, fill=(0, 0, 0, 255), spacing=8, align="center")
    draw.multiline_text((left, top), text, font=font, fill=fill, spacing=8, align="center")
    overlay = np.array(img)
    info["size"] = size
    info["overflow"] = overflow
    info["has_box"] = caption_overlay_has_box(overlay)
    return overlay, info


def _snap(seconds: float) -> float:
    frames = max(1, int(round(seconds * FPS)))
    return frames / FPS


def _apply_floors(lines: list[dict]) -> None:
    for line in lines:
        voice = float(line["voice_seconds"])
        floor = FLOORS.get(str(line["role"]), 2.0)
        line["duration"] = _snap(max(voice + HOLD, floor))


def _total(lines: list[dict]) -> float:
    return float(sum(float(line["duration"]) for line in lines))


def synthesize(lines: list[dict], speaker: Speaker, audio_dir: Path, settings: dict, depth: int = 0) -> None:
    audio_dir.mkdir(parents=True, exist_ok=True)
    for index, line in enumerate(lines, start=1):
        text = str(line["text"])
        if line["role"] == "credit" or not text.strip():
            samples = np.zeros(int(0.2 * SAMPLE_RATE), dtype=np.float32)
        else:
            samples = speaker.speak(text, int(line["style_id"]), scene_speed(settings, line))
        path = audio_dir / f"line_{index:02d}.wav"
        write_wav(path, samples)
        line["voice_path"] = str(path)
        line["voice_seconds"] = round(len(samples) / SAMPLE_RATE, 3)
    _apply_floors(lines)
    total = _total(lines)
    if total > MAX_DURATION and depth < 2:
        factor = total / (MAX_DURATION - 1.5)
        scale_speeds(settings, factor, factor)
        synthesize(lines, speaker, audio_dir, settings, depth + 1)
        return
    _fit_range(lines)


def _fit_range(lines: list[dict]) -> None:
    total = _total(lines)
    if total < PAD_TARGET:
        extra = PAD_TARGET - total
        target = next((line for line in lines if line["role"] == "punch"), lines[-2])
        target["duration"] = _snap(float(target["duration"]) + extra)
    total = _total(lines)
    if total <= MAX_DURATION:
        return
    overflow = total - (MAX_DURATION - 0.8)
    for line in lines:
        if line["role"] == "credit":
            continue
        spare = float(line["duration"]) - (float(line["voice_seconds"]) + 0.25)
        cut = min(max(0.0, spare), overflow)
        if cut <= 0:
            continue
        line["duration"] = _snap(float(line["duration"]) - cut)
        overflow -= cut
    if _total(lines) > MAX_DURATION:
        raise RuntimeError(f"尺が30秒を超えます: {_total(lines):.2f}")


def mix_audio(lines: list[dict], audio_dir: Path, settings: dict) -> Path:
    pieces: list[np.ndarray] = []
    bed = bgm_loop(90.0)
    offset = 0
    for line in lines:
        nframes = max(1, int(round(float(line["duration"]) * FPS)))
        n = samples_for_frames(nframes)
        voice = fit_length(read_wav(line["voice_path"]), n)
        sfx = make_sfx(str(line["sfx"]))
        bgm_slice = bed[offset : offset + n]
        if len(bgm_slice) < n:
            bgm_slice = fit_length(bgm_slice, n)
        pieces.append(mix_tracks(voice, sfx, float(settings["sfx_gain"]), bgm_slice, float(settings["bgm_gain"])))
        offset += n
    audio = np.concatenate(pieces) if pieces else np.zeros(1, dtype=np.float32)
    path = audio_dir / "mix.wav"
    write_wav(path, audio)
    return path


def _place(frame: np.ndarray, sprite: np.ndarray, layout: dict) -> None:
    foot = int(frame.shape[0] * 0.76)
    x = int(frame.shape[1] * float(layout.get("character_x_ratio", 0.5)) - sprite.shape[1] / 2)
    y = foot - sprite.shape[0]
    blit(frame, sprite, x, y)


def render_mp4(lines: list[dict], sprites: list[np.ndarray | None], captions: list[np.ndarray], mix_path: Path, out_path: Path, layout: dict) -> list[tuple[str, np.ndarray]]:
    bgs = {
        "office": render_bg("office"),
        "credit": render_bg("credit"),
    }
    shots: list[tuple[str, np.ndarray]] = []
    nframes = sum(max(1, int(round(float(line["duration"]) * FPS))) for line in lines)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    proc = _open_encoder(out_path, mix_path)
    try:
        for index, line in enumerate(lines):
            scene_len = max(1, int(round(float(line["duration"]) * FPS)))
            bg_name = "credit" if line["role"] == "credit" else "office"
            sprite = sprites[index]
            shot_at = min(scene_len - 1, max(0, int(0.45 * scene_len)))
            print(f"scene {index + 1}/{len(lines)}", flush=True)
            for frame_i in range(scene_len):
                local_t = frame_i / FPS
                frame = bgs[bg_name].copy()
                if sprite is not None:
                    _place(frame, sprite, layout)
                frame = _light_motion(frame, line, local_t)
                slide = int(20 * max(0.0, 1.0 - local_t / 0.16))
                blit(frame, captions[index], 0, slide)
                if frame_i == shot_at:
                    label = str(line["caption"]).split("\n", 1)[0][:18]
                    shots.append((f"{index + 1:02d} {line['role']} {label}", frame.copy()))
                _write_frame(proc, frame)
        _finish_encoder(proc, out_path)
    except Exception:
        _stop_encoder(proc)
        raise
    if nframes <= 0:
        raise RuntimeError("フレームがありません。")
    return shots


def contact_sheet(shots: list[tuple[str, np.ndarray]], dest: Path) -> None:
    cols = 2
    thumb_w, thumb_h = 360, 640
    label_h = 64
    rows = max(1, (len(shots) + cols - 1) // cols)
    sheet = Image.new("RGB", (cols * thumb_w, rows * (thumb_h + label_h)), (245, 242, 236))
    draw = ImageDraw.Draw(sheet)
    font = find_font(26)
    for index, (label, frame) in enumerate(shots):
        col = index % cols
        row = index // cols
        thumb = Image.fromarray(frame, "RGB").resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        x = col * thumb_w
        y = row * (thumb_h + label_h)
        sheet.paste(thumb, (x, y))
        draw.text((x + 12, y + thumb_h + 16), label, fill=(20, 20, 20), font=font)
    dest.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(dest, quality=86)


def build(script: dict, work: Path, speaker: Speaker) -> dict:
    """絵と声を作る。QA に落ちる形なら mp4 は書かない。"""
    work.mkdir(parents=True, exist_ok=True)
    layout = default_layout()
    settings = settings_for("sukatto")
    settings["bgm"] = True
    mouth_overlay = bool(script["mouth_overlay"])
    char_h = int(HEIGHT * 0.60)
    raw: dict[str, np.ndarray] = {}
    sprites: list[np.ndarray | None] = []
    mouths = []
    captions = []
    caption_info = []
    for line in script["lines"]:
        character = line.get("character") or ""
        if character:
            if character not in raw:
                path = ensure_asset({"id": character, "source_url": line["source_url"]})
                raw[character] = load_rgba(path)
            sprite, report = prepare_sprite(raw[character], line, mouth_overlay, char_h)
            sprites.append(sprite)
        else:
            sprites.append(None)
            report = {
                "character": "",
                "overlay_used": False,
                "center": None,
                "errors": [],
                "checked": True,
            }
        mouths.append(report)
        overlay, info = render_caption(str(line["caption"]), str(line["role"]), script["caption"])
        captions.append(overlay)
        caption_info.append(info)
    tags = []
    for line in script["lines"]:
        if line.get("label") or line.get("tag"):
            tags.append(str(line.get("character") or line["role"]))
        if "#" in str(line.get("caption") or ""):
            tags.append("caption")
    images = [
        {
            "id": line["character"],
            "emotion": line.get("emotion") or "",
            "source_url": line["source_url"],
            "recolor": bool(line.get("recolor")),
        }
        for line in script["lines"]
        if line.get("source_url")
    ]
    max_height = 0.0
    max_width = 0.0
    max_area = 0.0
    caption_count = 0
    frame_area = float(HEIGHT * WIDTH)
    for line, sprite in zip(script["lines"], sprites):
        if line["role"] != "credit" and str(line.get("caption") or "").strip():
            caption_count += 1
        if sprite is None:
            continue
        max_height = max(max_height, sprite.shape[0] / float(HEIGHT))
        max_width = max(max_width, sprite.shape[1] / float(WIDTH))
        max_area = max(max_area, (sprite.shape[0] * sprite.shape[1]) / frame_area)
    blocked = any(item["errors"] for item in mouths) or any(item["overflow"] or item["has_box"] for item in caption_info) or bool(tags)
    plan = {
        "mouth_overlay": mouth_overlay,
        "mouths": mouths,
        "captions": caption_info,
        "tags": tags,
        "duration_sec": None,
        "blocked_before_encode": blocked,
        "images": images,
        "thumbnail": script.get("thumbnail"),
        "subject": {
            "background": "generated",
            "max_height_ratio": round(max_height, 4),
            "max_width_ratio": round(max_width, 4),
            "max_area_ratio": round(max_area, 4),
            "caption_count": caption_count,
        },
        "branding": {
            "name": str(script.get("channel_name") or ""),
            "genre": str(script.get("genre") or ""),
            "title": str(script.get("title") or ""),
            "theme": str(script.get("theme") or ""),
            "tags": list(script.get("tags") or []),
            "texts": [
                str(script.get("hook") or ""),
                *[str(line.get("text") or "") for line in script["lines"]],
                *[str(line.get("caption") or "") for line in script["lines"]],
            ],
        },
        "credits": [
            {"id": line["character"], "source_url": line["source_url"]}
            for line in script["lines"]
            if line.get("source_url")
        ],
    }
    if blocked:
        return {"plan": plan, "mp4": None, "shots": [], "mix": None}
    audio_dir = work / "audio"
    synthesize(script["lines"], speaker, audio_dir, settings)
    plan["duration_sec"] = round(_total(script["lines"]), 2)
    if not (MIN_DURATION <= plan["duration_sec"] <= MAX_DURATION):
        plan["blocked_before_encode"] = True
        return {"plan": plan, "mp4": None, "shots": [], "mix": None}
    mix_path = mix_audio(script["lines"], audio_dir, settings)
    out_path = work / "out.mp4"
    shots = render_mp4(script["lines"], sprites, captions, mix_path, out_path, layout)
    sheet = work / "contact-sheet.jpg"
    contact_sheet(shots, sheet)
    (work / "script.json").write_text(json.dumps(script, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"plan": plan, "mp4": out_path, "shots": shots, "mix": mix_path, "sheet": sheet}

