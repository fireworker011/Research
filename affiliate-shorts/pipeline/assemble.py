"""VOICEVOX、いらすとや、字幕、ffmpeg で 9:16 の静止画ショートを1本にする。"""

from __future__ import annotations

import json
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from irasutoya_short.audio import fit_length, mix_tracks, read_wav, samples_for_frames, write_wav
from irasutoya_short.backgrounds import render_bg
from irasutoya_short.constants import FPS, HEIGHT, MAX_DURATION, MIN_DURATION, SAMPLE_RATE, WIDTH
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
from irasutoya_short.sfx import make_sfx
from irasutoya_short.sprites import draw_mouth, load_rgba, mouth_anchor, scale_rgba, skin_color
from irasutoya_short.templates import scale_speeds, scene_speed, settings_for
from irasutoya_short.tts import Speaker

from qa_gate import caption_overlay_has_box, diff_centroid, judge_mouth
from styles import alert_blip, fit_line_durations, render_bed

CACHE = Path.home() / ".cache" / "irasutoya-short" / "pipeline-assets"
FLOORS = {"hook": 2.15, "develop": 2.35, "punch": 3.6, "credit": 2.2}
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


def _caption_text(text: str, align: str) -> tuple[str, str]:
    if align != "vertical":
        return text, "center"
    chars = [char for char in text.replace("\n", "") if not char.isspace()]
    return "\n".join(chars), "center"


def render_caption(text: str, role: str, style: dict, look: dict) -> tuple[np.ndarray, dict]:
    overlay = np.zeros((HEIGHT, WIDTH, 4), dtype=np.uint8)
    info = {"role": role, "overflow": False, "has_box": False, "size": 0, "text": text}
    if not text.strip():
        return overlay, info
    layout = look["layout"]
    credit = role == "credit"
    fill = (255, 255, 255, 255) if credit else tuple(look["palette"]["caption"])
    font_path = look["fonts"]["body"] if credit or role == "develop" else look["fonts"]["emphasis"]
    align = "center" if credit else str(layout["text_align"])
    drawn, draw_align = _caption_text(text, align)
    scale = 1.0 if credit else float(layout["text_scale"])
    if role == "hook":
        scale *= float(look["hook"]["hook_scale"])
    base = int(style["credit_size"] if credit else style["size"])
    floor = int(style["credit_min_size"] if credit else style["min_size"])
    size = max(floor, int(base * scale))
    max_w = int(WIDTH * (0.42 if align == "vertical" else 0.88))
    max_h = int(HEIGHT * (0.72 if align == "vertical" else 0.34 if credit else 0.28))
    font = ImageFont.truetype(font_path, size=size)
    tw, th = _text_size(font, drawn)
    while size > floor and (tw > max_w or th > max_h):
        size -= 2
        font = ImageFont.truetype(font_path, size=size)
        tw, th = _text_size(font, drawn)
    y_ratio = float(style["credit_y_ratio"] if credit else layout["text_y"])
    top = int(HEIGHT * y_ratio - th / 2)
    top = max(24, min(HEIGHT - th - 36, top))
    if align == "left":
        left = 48
    elif align == "right":
        left = WIDTH - tw - 48
    else:
        left = (WIDTH - tw) // 2
    overflow = tw > max_w or th > max_h or left < 24 or top < 24 or left + tw > WIDTH - 24 or top + th > HEIGHT - 36
    img = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    stroke = int(style["credit_stroke"] if credit else style["stroke"])
    for dx in range(-stroke, stroke + 1):
        for dy in range(-stroke, stroke + 1):
            if dx * dx + dy * dy > stroke * stroke:
                continue
            draw.multiline_text((left + dx, top + dy), drawn, font=font, fill=(0, 0, 0, 255), spacing=8, align=draw_align)
    draw.multiline_text((left, top), drawn, font=font, fill=fill, spacing=8, align=draw_align)
    overlay = np.array(img)
    info["size"] = size
    info["overflow"] = overflow
    info["has_box"] = caption_overlay_has_box(overlay)
    return overlay, info


def _snap(seconds: float) -> float:
    frames = max(1, int(round(seconds * FPS)))
    return frames / FPS


def _apply_tempo(lines: list[dict], tempo: dict) -> None:
    for line in lines:
        role = str(line["role"])
        if role == "hook":
            factor = float(tempo["early"])
        elif role == "punch":
            factor = float(tempo["late"]) * float(tempo["punch"])
        elif role == "credit":
            factor = float(tempo["late"])
        else:
            factor = (float(tempo["early"]) + float(tempo["late"])) / 2
        voice = float(line["voice_seconds"])
        floor = FLOORS.get(role, 2.0) * factor
        line["duration"] = _snap(max(voice + HOLD, floor))


def _total(lines: list[dict]) -> float:
    return float(sum(float(line["duration"]) for line in lines))


def synthesize(lines: list[dict], speaker: Speaker, audio_dir: Path, settings: dict, look: dict, depth: int = 0) -> None:
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
    _apply_tempo(lines, look["tempo"])
    fitted = fit_line_durations(
        [float(line["duration"]) for line in lines],
        [float(line["voice_seconds"]) for line in lines],
        int(look["length_target_frames"]),
    )
    if fitted is None:
        if depth < 2:
            scale_speeds(settings, 1.12, 1.12)
            synthesize(lines, speaker, audio_dir, settings, look, depth + 1)
            return
        look["fit_failed"] = True
        return
    for line, duration in zip(lines, fitted):
        line["duration"] = duration
    look["fit_failed"] = _total(lines) > MAX_DURATION


def mix_audio(lines: list[dict], audio_dir: Path, settings: dict, look: dict) -> Path:
    pieces: list[np.ndarray] = []
    bed = render_bed(str(look["bgm"]), 90.0)
    blip = alert_blip() if look["hook"]["alert"] else None
    offset = 0
    for line in lines:
        nframes = max(1, int(round(float(line["duration"]) * FPS)))
        n = samples_for_frames(nframes)
        voice = fit_length(read_wav(line["voice_path"]), n)
        if line["role"] == "hook" and blip is not None:
            voice = voice.copy()
            span = min(len(voice), len(blip))
            voice[:span] += blip[:span]
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


def _place(frame: np.ndarray, sprite: np.ndarray, x_ratio: float) -> None:
    foot = int(frame.shape[0] * 0.76)
    x = int(frame.shape[1] * float(x_ratio) - sprite.shape[1] / 2)
    y = foot - sprite.shape[0]
    blit(frame, sprite, x, y)


def _paint_bg(look: dict) -> np.ndarray:
    palette = look["palette"]
    flat = Image.new("RGB", (WIDTH, HEIGHT), tuple(palette["wall"]))
    draw = ImageDraw.Draw(flat)
    floor_y = int(HEIGHT * 0.72)
    draw.rectangle((0, floor_y, WIDTH, HEIGHT), fill=tuple(palette["floor"]))
    office = render_bg("office").astype(np.float32)
    mix = float(look["layout"]["office"])
    mixed = office * mix + np.array(flat).astype(np.float32) * (1.0 - mix)
    return mixed.astype(np.uint8)


def _draw_motif(frame: np.ndarray, look: dict) -> None:
    strength = float(look["layout"]["motif_strength"])
    if strength < 0.05:
        return
    red, green, blue = look["palette"]["accent"]
    accent = (int(red), int(green), int(blue), int(200 * strength))
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    motif = str(look["layout"]["motif"])
    if motif == "diagram":
        for index, wide in enumerate((420, 300, 510)):
            top = 280 + index * 90
            draw.rounded_rectangle((120, top, 120 + wide, top + 36), radius=8, fill=accent)
    elif motif == "checklist":
        for index in range(4):
            top = 260 + index * 110
            draw.rounded_rectangle((80, top, 148, top + 68), radius=8, outline=accent, width=6)
    elif motif == "timeline":
        draw.line((160, 240, 160, 1100), fill=accent, width=8)
        for index in range(4):
            top = 280 + index * 180
            draw.ellipse((136, top, 184, top + 48), fill=accent)
    elif motif == "items":
        for index in range(3):
            left = 120 + index * 300
            draw.rounded_rectangle((left, 300, left + 240, 620), radius=24, outline=accent, width=8)
    elif motif == "qa":
        draw.line((80, int(HEIGHT * 0.42), WIDTH - 80, int(HEIGHT * 0.42)), fill=accent, width=6)
    elif motif == "room":
        draw.rounded_rectangle((140, 220, WIDTH - 140, int(HEIGHT * 0.62)), radius=16, outline=accent, width=8)
    elif motif == "panels":
        for row in range(2):
            for col in range(2):
                left = 90 + col * 480
                top = 180 + row * 420
                draw.rounded_rectangle((left, top, left + 420, top + 360), radius=12, outline=accent, width=8)
    blit(frame, np.array(overlay), 0, 0)


def render_mp4(lines: list[dict], sprites: list[np.ndarray | None], captions: list[np.ndarray], mix_path: Path, out_path: Path, look: dict) -> list[tuple[str, np.ndarray]]:
    bgs = {
        "scene": _paint_bg(look),
        "credit": render_bg("credit"),
    }
    shots: list[tuple[str, np.ndarray]] = []
    nframes = sum(max(1, int(round(float(line["duration"]) * FPS))) for line in lines)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    proc = _open_encoder(out_path, mix_path)
    try:
        for index, line in enumerate(lines):
            scene_len = max(1, int(round(float(line["duration"]) * FPS)))
            credit = line["role"] == "credit"
            sprite = sprites[index]
            if sprite is not None and line["role"] == "hook" and look["axes"]["H"] == "H6":
                sprite = scale_rgba(sprite, max(1, int(sprite.shape[0] * 0.72)))
            motion = dict(line)
            if line["role"] == "hook" and look["hook"]["hook_effect"]:
                motion["effect"] = look["hook"]["hook_effect"]
            shot_at = min(scene_len - 1, max(0, int(0.45 * scene_len)))
            print(f"scene {index + 1}/{len(lines)}", flush=True)
            for frame_i in range(scene_len):
                local_t = frame_i / FPS
                frame = bgs["credit" if credit else "scene"].copy()
                if not credit:
                    _draw_motif(frame, look)
                if sprite is not None:
                    _place(frame, sprite, float(look["layout"]["character_x"]))
                frame = _light_motion(frame, motion, local_t)
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


def build(script: dict, work: Path, speaker: Speaker, look: dict) -> dict:
    """絵と声を作る。QA に落ちる形なら mp4 は書かない。"""
    work.mkdir(parents=True, exist_ok=True)
    settings = settings_for("sukatto")
    settings["bgm"] = look["bgm"] != "B1"
    scale_speeds(settings, float(look["tempo"]["speech"]), float(look["tempo"]["hook_speech"]))
    mouth_overlay = bool(script["mouth_overlay"])
    char_h = int(HEIGHT * float(look["layout"]["character_h"]))
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
        overlay, info = render_caption(str(line["caption"]), str(line["role"]), script["caption"], look)
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
        "video_id": str(script.get("id") or ""),
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
                *[str(line.get("text") or "") for line in script["lines"] if line.get("role") != "credit"],
                *[str(line.get("caption") or "") for line in script["lines"] if line.get("role") != "credit"],
            ],
        },
        "style": {
            "line": look["line"],
            "axes": dict(look["axes"]),
            "signature": look["signature"],
            "thumb_signature": look["thumb_signature"],
            "length_options": look["length_options"],
            "bgm": look["bgm"],
            "length_target": look["length_target"],
            "fit_failed": False,
        },
        "credit_caption": next((str(line.get("caption") or "") for line in script["lines"] if line.get("role") == "credit"), ""),
        "voice_credits": list(script.get("credits") or []),
        "credits": [
            {"id": line["character"], "source_url": line["source_url"]}
            for line in script["lines"]
            if line.get("source_url")
        ],
    }
    if blocked:
        return {"plan": plan, "mp4": None, "shots": [], "mix": None, "thumb": None}
    audio_dir = work / "audio"
    synthesize(script["lines"], speaker, audio_dir, settings, look)
    plan["style"]["fit_failed"] = bool(look.get("fit_failed"))
    plan["duration_sec"] = round(_total(script["lines"]), 2)
    if look.get("fit_failed") or not (MIN_DURATION <= plan["duration_sec"] <= MAX_DURATION):
        plan["blocked_before_encode"] = True
        return {"plan": plan, "mp4": None, "shots": [], "mix": None, "thumb": None}
    mix_path = mix_audio(script["lines"], audio_dir, settings, look)
    out_path = work / "out.mp4"
    shots = render_mp4(script["lines"], sprites, captions, mix_path, out_path, look)
    sheet = work / "contact-sheet.jpg"
    contact_sheet(shots, sheet)
    thumb = work / "thumb.jpg"
    if shots:
        Image.fromarray(shots[0][1], "RGB").save(thumb, quality=86)
    (work / "script.json").write_text(json.dumps(script, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"plan": plan, "mp4": out_path, "shots": shots, "mix": mix_path, "sheet": sheet, "thumb": thumb}

