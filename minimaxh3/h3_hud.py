"""HUD, title cards, and ffmpeg assembly for MiniMax H3 episode trailers.

H3 cannot render Japanese UI text. Everything on screen that is not the
generated footage (health bars, minimap, mission subtitle, hints, title and
end cards, the fictional-game disclaimer) is drawn here with Pillow and
composited afterwards with ffmpeg. The clean stills and raw clips never carry
a HUD, so they stay usable as first frames.

No network. No ComfyUI. Works on Colab and on a plain Linux box with ffmpeg.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Sequence

from PIL import Image, ImageDraw, ImageFont

FPS = 24
AUDIO_RATE = 48000

# Japanese-first, and the font must also carry Latin + ¥ (HUD money, button hints, "Dist.").
# DroidSansFallback has CJK but no Latin, so it is a last resort behind WenQuanYi.
FONT_CANDIDATES = (
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJKjp-Regular.otf",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansJP-Regular.ttf",
    "/usr/share/fonts/opentype/ipaexfont-gothic/ipaexg.ttf",
    "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf",
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
    "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
)
FONT_INSTALL_HINT = "apt-get install -y fonts-noto-cjk  (Colab) / brew install font-noto-sans-cjk-jp"
# One glyph from each block the HUD draws: ASCII digit, yen sign, hiragana, katakana, kanji.
FONT_PROBE_CHARS = ("0", "¥", "あ", "ミ", "湯")


def _glyph_mask(font: ImageFont.FreeTypeFont, ch: str) -> bytes:
    im = Image.new("L", (64, 64), 0)
    ImageDraw.Draw(im).text((6, 6), ch, font=font, fill=255)
    return im.tobytes()


# Unassigned code points; whatever most of them render as is the font's .notdef box.
_UNMAPPED_PROBES = ("\u0378", "\u0380", "\u038b", "\u2065", "\u2fe0", "\ufff0")


def font_covers(path: Path | str, chars: Sequence[str] = FONT_PROBE_CHARS) -> bool:
    """True when every probe char renders as something other than .notdef (box) or nothing."""
    try:
        font = ImageFont.truetype(str(path), 28)
    except OSError:
        return False
    masks = [_glyph_mask(font, c) for c in _UNMAPPED_PROBES]
    notdef = max(set(masks), key=masks.count)
    blank = Image.new("L", (64, 64), 0).tobytes()
    for ch in chars:
        mask = _glyph_mask(font, ch)
        if mask == notdef or mask == blank:
            return False
    return True

THEMES: dict[str, dict[str, Any]] = {
    "bandai": {
        "health": (222, 72, 84),
        "stamina": (72, 200, 140),
        "heat": (255, 170, 60),
        "panel": (8, 8, 8, 165),
        "text": (255, 255, 255, 245),
        "muted": (230, 230, 215, 220),
        "map_bg": (28, 42, 28, 210),
        "map_line": (92, 112, 82, 210),
        "player": (80, 180, 255, 240),
        "objective": (255, 80, 80, 235),
        "complete": (255, 214, 90, 255),
    },
    "mono": {
        "health": (230, 230, 230),
        "stamina": (170, 170, 170),
        "heat": (255, 120, 120),
        "panel": (0, 0, 0, 170),
        "text": (255, 255, 255, 245),
        "muted": (220, 220, 220, 220),
        "map_bg": (24, 24, 24, 210),
        "map_line": (90, 90, 90, 210),
        "player": (255, 255, 255, 240),
        "objective": (255, 90, 90, 235),
        "complete": (255, 255, 255, 255),
    },
}

Size = tuple[int, int]


class HudError(RuntimeError):
    pass


def find_font(explicit: str | None = None) -> Path:
    """First existing font covering Latin + kana + kanji. `H3_HUD_FONT` wins when it covers them."""
    partial: Path | None = None
    for cand in (explicit, os.environ.get("H3_HUD_FONT"), *FONT_CANDIDATES):
        if not cand or not Path(cand).is_file():
            continue
        if font_covers(cand):
            return Path(cand)
        partial = partial or Path(cand)
    if partial is not None:
        print(f"font warning: {partial} lacks Latin or CJK glyphs; HUD text may show boxes. {FONT_INSTALL_HINT}")
        return partial
    raise HudError("Japanese font missing. " + FONT_INSTALL_HINT)


def load_font(size: int, path: Path | None = None) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(path or find_font()), int(size))


def theme(name: str | None) -> dict[str, Any]:
    return THEMES.get(str(name or "bandai"), THEMES["bandai"])


def scale(size: Size) -> float:
    """Layout is authored for 1280 wide 16:9; everything scales from the short edge."""
    return min(size) / 720.0


def _center_text(draw: ImageDraw.ImageDraw, y: int, text: str, font: ImageFont.FreeTypeFont, fill: Any, width: int) -> None:
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    draw.text(((width - tw) // 2 - bbox[0], y), text, font=font, fill=fill)


def render_hud_layer(size: Size, hud: dict[str, Any], *, theme_name: str = "bandai", district: str = "", icons: Sequence[str] = (), font_path: Path | None = None) -> Image.Image:
    """Static per-beat HUD: bars, money, heat, minimap, item icons, button hint."""
    w, h = size
    s = scale(size)
    t = theme(theme_name)
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    f_tiny = load_font(round(14 * s), font_path)
    f_sm = load_font(round(18 * s), font_path)
    pad = round(28 * s)

    # health / stamina
    bar_w, bar_h = round(220 * s), round(14 * s)
    health = float(hud.get("health", 1.0))
    stamina = float(hud.get("stamina", 1.0))
    d.rounded_rectangle([pad - 8 * s, pad - 8 * s, pad + bar_w + 8 * s, pad + 52 * s], radius=round(6 * s), fill=(0, 0, 0, 110))
    d.rectangle([pad, pad, pad + bar_w, pad + bar_h], fill=(40, 20, 20, 200))
    d.rectangle([pad, pad, pad + int(bar_w * max(0.0, min(1.0, health))), pad + bar_h], fill=(*t["health"], 230))
    y2 = pad + round(22 * s)
    d.rectangle([pad, y2, pad + bar_w, y2 + bar_h], fill=(20, 40, 30, 200))
    d.rectangle([pad, y2, pad + int(bar_w * max(0.0, min(1.0, stamina))), y2 + bar_h], fill=(*t["stamina"], 230))
    money = str(hud.get("money") or "")
    if money:
        d.text((pad, pad + round(40 * s)), money, font=f_tiny, fill=t["muted"])

    # heat (wanted level): 0-5 filled diamonds
    heat = int(hud.get("heat", 0) or 0)
    if heat > 0:
        hx = pad + bar_w + round(24 * s)
        for i in range(5):
            cx = hx + i * round(20 * s)
            cy = pad + round(7 * s)
            r = round(7 * s)
            fill = (*t["heat"], 240) if i < heat else (60, 60, 60, 170)
            d.polygon([(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)], fill=fill)

    # minimap
    mm = round(118 * s)
    mx, my = pad + round(8 * s), h - pad - mm
    d.ellipse([mx - 6 * s, my - 6 * s, mx + mm + 6 * s, my + mm + 6 * s], fill=(0, 0, 0, 140))
    d.ellipse([mx, my, mx + mm, my + mm], fill=t["map_bg"], outline=(180, 200, 160, 180), width=max(1, round(2 * s)))
    d.line([mx + 20 * s, my + mm / 2, mx + mm - 20 * s, my + mm / 2], fill=t["map_line"], width=max(1, round(3 * s)))
    d.line([mx + mm / 2, my + 18 * s, mx + mm / 2, my + mm - 18 * s], fill=t["map_line"], width=max(1, round(3 * s)))
    cx, cy = mx + mm / 2, my + mm / 2
    d.polygon([(cx, cy - 10 * s), (cx - 7 * s, cy + 8 * s), (cx + 7 * s, cy + 8 * s)], fill=t["player"])
    import math

    bearing = float(hud.get("objective_bearing", 40.0))
    dist = float(hud.get("objective_distance", 0.62))
    rad = math.radians(bearing)
    ox = cx + math.sin(rad) * (mm / 2 - 14 * s) * max(0.15, min(1.0, dist))
    oy = cy - math.cos(rad) * (mm / 2 - 14 * s) * max(0.15, min(1.0, dist))
    r = round(5 * s)
    d.ellipse([ox - r, oy - r, ox + r, oy + r], fill=t["objective"])
    if district:
        d.text((mx, my + mm + 4 * s), district, font=f_tiny, fill=t["muted"])

    # item icons (right)
    if icons:
        ix = w - pad - round(46 * s)
        iy = h - pad - round(48 * s) * len(icons) - round(16 * s)
        d.rounded_rectangle([ix - 8 * s, iy - 8 * s, ix + 46 * s, iy + 48 * s * len(icons) + 6 * s], radius=round(8 * s), fill=(0, 0, 0, 120))
        active = set(hud.get("icons_active") or ())
        for i, label in enumerate(icons):
            yy = iy + i * round(48 * s)
            outline = (255, 214, 90, 230) if label in active else (200, 200, 200, 160)
            d.ellipse([ix, yy, ix + 38 * s, yy + 38 * s], fill=(20, 20, 20, 200), outline=outline, width=max(1, round(2 * s)))
            d.text((ix + 9 * s, yy + 7 * s), str(label)[:1], font=f_sm, fill=t["text"])

    # button hint (top right)
    hint = str(hud.get("hint") or "")
    if hint:
        bbox = d.textbbox((0, 0), hint, font=f_sm)
        tw = bbox[2] - bbox[0]
        x0 = w - pad - tw - round(24 * s)
        d.rounded_rectangle([x0, pad - 4 * s, w - pad, pad + 36 * s], radius=round(6 * s), fill=(0, 0, 0, 140))
        d.text((x0 + 12 * s, pad + 4 * s), hint, font=f_sm, fill=t["muted"])
    return layer


def render_mission_layer(size: Size, mission: str, *, theme_name: str = "bandai", font_path: Path | None = None) -> Image.Image:
    """Bottom-center mission subtitle. Faded in by ffmpeg."""
    w, h = size
    s = scale(size)
    t = theme(theme_name)
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    if not mission:
        return layer
    d = ImageDraw.Draw(layer)
    f = load_font(round(32 * s), font_path)
    bbox = d.textbbox((0, 0), mission, font=f)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    bx = (w - tw) // 2
    by = h - round(78 * s)
    d.rounded_rectangle([bx - 28 * s, by - 10 * s, bx + tw + 28 * s, by + th + 16 * s], radius=round(8 * s), fill=t["panel"])
    d.text((bx - bbox[0], by), mission, font=f, fill=t["text"])
    return layer


def render_complete_layer(size: Size, text: str = "ミッション完了", *, theme_name: str = "bandai", font_path: Path | None = None) -> Image.Image:
    """Center flash shown for the last ~1.4s of a beat that closes its mission."""
    w, h = size
    s = scale(size)
    t = theme(theme_name)
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    f = load_font(round(44 * s), font_path)
    bbox = d.textbbox((0, 0), text, font=f)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    y = h // 2 - th
    d.rectangle([0, y - 22 * s, w, y + th + 26 * s], fill=(0, 0, 0, 150))
    d.text(((w - tw) // 2 - bbox[0], y), text, font=f, fill=t["complete"])
    return layer


def _background(size: Size, image: Path | None, darken: int) -> Image.Image:
    if image and Path(image).is_file():
        bg = Image.open(image).convert("RGB").resize(size, Image.LANCZOS)
    else:
        bg = Image.new("RGB", size, (14, 14, 16))
    if darken:
        shade = Image.new("RGBA", size, (0, 0, 0, darken))
        bg = Image.alpha_composite(bg.convert("RGBA"), shade).convert("RGB")
    return bg


def render_title_card(size: Size, *, title: str, subtitle: str = "", kicker: str = "", image: Path | None = None, font_path: Path | None = None) -> Image.Image:
    w, h = size
    s = scale(size)
    bg = _background(size, image, 70).convert("RGBA")
    ov = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    d.rectangle([0, h - round(170 * s), w, h], fill=(0, 0, 0, 150))
    _center_text(d, h - round(148 * s), title, load_font(round(54 * s), font_path), (255, 255, 255, 245), w)
    if subtitle:
        _center_text(d, h - round(78 * s), subtitle, load_font(round(22 * s), font_path), (220, 220, 210, 230), w)
    if kicker:
        d.rectangle([0, 0, w, round(72 * s)], fill=(0, 0, 0, 120))
        _center_text(d, round(24 * s), kicker, load_font(round(20 * s), font_path), (230, 230, 230, 220), w)
    return Image.alpha_composite(bg, ov).convert("RGB")


def render_end_card(size: Size, *, title: str, lines: Sequence[str], image: Path | None = None, font_path: Path | None = None) -> Image.Image:
    """Title + disclaimer lines. The disclaimer is how a fictional-game trailer stays honest."""
    w, h = size
    s = scale(size)
    bg = _background(size, image, 110).convert("RGBA")
    ov = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    top = h // 2 - round(90 * s)
    d.rectangle([0, top, w, top + round(96 * s)], fill=(0, 0, 0, 150))
    _center_text(d, top + round(18 * s), title, load_font(round(54 * s), font_path), (255, 255, 255, 245), w)
    f = load_font(round(20 * s), font_path)
    y = top + round(124 * s)
    for line in lines:
        if not line:
            continue
        _center_text(d, y, line, f, (225, 225, 215, 230), w)
        y += round(32 * s)
    return Image.alpha_composite(bg, ov).convert("RGB")


# ---------------------------------------------------------------- ffmpeg

def ffmpeg_bin() -> str:
    path = shutil.which("ffmpeg")
    if not path:
        raise HudError("ffmpeg missing (apt-get install -y ffmpeg)")
    return path


def ffprobe_bin() -> str:
    path = shutil.which("ffprobe")
    if not path:
        raise HudError("ffprobe missing (comes with ffmpeg)")
    return path


def run(cmd: Sequence[str], *, quiet: bool = True) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(list(cmd), check=False, text=True, capture_output=True)
    if proc.returncode != 0:
        tail = (proc.stderr or proc.stdout or "")[-3000:]
        raise HudError(f"{Path(cmd[0]).name} failed ({proc.returncode}): {tail}")
    if not quiet and proc.stderr:
        print(proc.stderr[-1500:])
    return proc


def probe(path: Path | str) -> dict[str, Any]:
    out = run([ffprobe_bin(), "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(path)]).stdout
    return json.loads(out or "{}")


def probe_duration(path: Path | str) -> float:
    info = probe(path)
    dur = float((info.get("format") or {}).get("duration") or 0.0)
    if dur <= 0:
        for st in info.get("streams") or []:
            try:
                dur = max(dur, float(st.get("duration") or 0.0))
            except (TypeError, ValueError):
                continue
    return dur


def probe_has_audio(path: Path | str) -> bool:
    return any(st.get("codec_type") == "audio" for st in probe(path).get("streams") or [])


def probe_video_size(path: Path | str) -> Size:
    for st in probe(path).get("streams") or []:
        if st.get("codec_type") == "video":
            return int(st.get("width") or 0), int(st.get("height") or 0)
    return (0, 0)


def _encode_args() -> list[str]:
    return ["-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-ar", str(AUDIO_RATE), "-ac", "2", "-movflags", "+faststart"]


def compose_beat(
    clip_in: Path | str,
    clip_out: Path | str,
    *,
    out_size: Size,
    hud_png: Path | str,
    mission_png: Path | str,
    complete_png: Path | str | None = None,
    fade_in_s: float = 0.45,
    complete_s: float = 1.4,
) -> Path:
    """Scale the raw clip to the delivery size and layer HUD + mission (+ completion flash)."""
    clip_in = Path(clip_in)
    clip_out = Path(clip_out)
    clip_out.parent.mkdir(parents=True, exist_ok=True)
    dur = probe_duration(clip_in)
    if dur <= 0:
        raise HudError(f"cannot read duration: {clip_in}")
    w, h = out_size
    has_audio = probe_has_audio(clip_in)
    inputs: list[str] = ["-i", str(clip_in), "-loop", "1", "-t", f"{dur:.3f}", "-i", str(hud_png), "-loop", "1", "-t", f"{dur:.3f}", "-i", str(mission_png)]
    parts = [
        f"[0:v]scale={w}:{h}:flags=lanczos,setsar=1,fps={FPS},format=yuv420p[base]",
        "[1:v]format=rgba[hud]",
        f"[2:v]format=rgba,fade=t=in:st=0:d={fade_in_s:.2f}:alpha=1[mis]",
        "[base][hud]overlay=0:0:format=auto[v1]",
        "[v1][mis]overlay=0:0:format=auto[v2]",
    ]
    last = "[v2]"
    if complete_png:
        st = max(0.0, dur - complete_s)
        inputs += ["-loop", "1", "-t", f"{dur:.3f}", "-i", str(complete_png)]
        parts.append(f"[3:v]format=rgba,fade=t=in:st={st:.2f}:d=0.25:alpha=1[cmp]")
        parts.append(f"[v2][cmp]overlay=0:0:format=auto:enable='gte(t,{st:.2f})'[v3]")
        last = "[v3]"
    parts.append(f"{last}format=yuv420p[vout]")
    audio_in = len(inputs) // 2  # index of the next input
    if not has_audio:
        inputs += ["-f", "lavfi", "-t", f"{dur:.3f}", "-i", f"anullsrc=r={AUDIO_RATE}:cl=stereo"]
        audio_map = f"{audio_in}:a"
    else:
        audio_map = "0:a"
    cmd = [ffmpeg_bin(), "-y", "-hide_banner", "-loglevel", "error", *inputs, "-filter_complex", ";".join(parts), "-map", "[vout]", "-map", audio_map, "-t", f"{dur:.3f}", *_encode_args(), str(clip_out)]
    run(cmd)
    return clip_out


def card_clip(image: Path | str, clip_out: Path | str, *, seconds: float, out_size: Size, fade_s: float = 0.35) -> Path:
    """Still → silent clip with fades. Same codec/size/fps as beats so xfade accepts it."""
    clip_out = Path(clip_out)
    clip_out.parent.mkdir(parents=True, exist_ok=True)
    w, h = out_size
    vf = f"scale={w}:{h}:flags=lanczos,setsar=1,fps={FPS},format=yuv420p,fade=t=in:st=0:d={fade_s:.2f},fade=t=out:st={max(0.0, seconds - fade_s):.2f}:d={fade_s:.2f}"
    cmd = [ffmpeg_bin(), "-y", "-hide_banner", "-loglevel", "error", "-loop", "1", "-t", f"{seconds:.3f}", "-i", str(image), "-f", "lavfi", "-t", f"{seconds:.3f}", "-i", f"anullsrc=r={AUDIO_RATE}:cl=stereo", "-vf", vf, "-map", "0:v", "-map", "1:a", "-t", f"{seconds:.3f}", *_encode_args(), str(clip_out)]
    run(cmd)
    return clip_out


def still_clip(image: Path | str, clip_out: Path | str, *, seconds: float, canvas: Size) -> Path:
    """Stills-only preview: a clean still held for N seconds at the H3 canvas size (stand-in for a raw clip)."""
    clip_out = Path(clip_out)
    clip_out.parent.mkdir(parents=True, exist_ok=True)
    w, h = canvas
    cmd = [ffmpeg_bin(), "-y", "-hide_banner", "-loglevel", "error", "-loop", "1", "-t", f"{seconds:.3f}", "-i", str(image), "-f", "lavfi", "-t", f"{seconds:.3f}", "-i", f"anullsrc=r={AUDIO_RATE}:cl=stereo", "-vf", f"scale={w}:{h}:flags=lanczos,setsar=1,fps={FPS},format=yuv420p", "-map", "0:v", "-map", "1:a", "-t", f"{seconds:.3f}", *_encode_args(), str(clip_out)]
    run(cmd)
    return clip_out


def synthetic_clip(clip_out: Path | str, *, seconds: float, canvas: Size, color: str = "0x334455", tone_hz: int = 440) -> Path:
    """Dry-run stand-in for an H3 render: flat colour + sine so the HUD/stitch path runs for real."""
    clip_out = Path(clip_out)
    clip_out.parent.mkdir(parents=True, exist_ok=True)
    w, h = canvas
    cmd = [ffmpeg_bin(), "-y", "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i", f"color=c={color}:s={w}x{h}:r={FPS}:d={seconds:.3f}", "-f", "lavfi", "-i", f"sine=frequency={tone_hz}:sample_rate={AUDIO_RATE}:duration={seconds:.3f}", "-map", "0:v", "-map", "1:a", "-t", f"{seconds:.3f}", *_encode_args(), str(clip_out)]
    run(cmd)
    return clip_out


def extract_last_frame(clip: Path | str, jpg_out: Path | str) -> Path:
    """Last frame → JPEG, used as the next beat's first frame when `source: chain`."""
    clip = Path(clip)
    jpg_out = Path(jpg_out)
    jpg_out.parent.mkdir(parents=True, exist_ok=True)
    dur = probe_duration(clip)
    ss = max(0.0, dur - 0.12)
    cmd = [ffmpeg_bin(), "-y", "-hide_banner", "-loglevel", "error", "-ss", f"{ss:.3f}", "-i", str(clip), "-frames:v", "1", "-q:v", "2", "-update", "1", str(jpg_out)]
    run(cmd)
    if not jpg_out.is_file() or jpg_out.stat().st_size < 1000:
        raise HudError(f"last frame extraction failed: {clip}")
    return jpg_out


def stitch(
    clips: Sequence[Path | str],
    out: Path | str,
    *,
    out_size: Size,
    transition: str = "xfade",
    xfade_s: float = 0.35,
    loudnorm: bool = True,
) -> Path:
    """Join normalized clips. `xfade` crossfades video+audio so H3 audio does not cut at beat borders."""
    paths = [Path(p) for p in clips]
    if not paths:
        raise HudError("nothing to stitch")
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    w, h = out_size
    durs = [probe_duration(p) for p in paths]
    if any(d <= 0 for d in durs):
        raise HudError("clip with zero duration in stitch")
    inputs: list[str] = []
    for p in paths:
        inputs += ["-i", str(p)]
    parts: list[str] = []
    for i, p in enumerate(paths):
        parts.append(f"[{i}:v]scale={w}:{h}:flags=lanczos,setsar=1,fps={FPS},format=yuv420p,settb=AVTB,setpts=PTS-STARTPTS[v{i}]")
        if probe_has_audio(p):
            parts.append(f"[{i}:a]aformat=sample_fmts=fltp:sample_rates={AUDIO_RATE}:channel_layouts=stereo,asetpts=PTS-STARTPTS[a{i}]")
        else:
            raise HudError(f"clip without audio (run compose_beat/card_clip first): {p}")
    n = len(paths)
    if n == 1:
        vlast, alast = "[v0]", "[a0]"
    elif transition == "cut" or xfade_s <= 0:
        chain = "".join(f"[v{i}][a{i}]" for i in range(n))
        parts.append(f"{chain}concat=n={n}:v=1:a=1[vc][ac]")
        vlast, alast = "[vc]", "[ac]"
    else:
        x = min(xfade_s, min(durs) / 2.5)
        vprev, aprev = "[v0]", "[a0]"
        total = durs[0]
        for i in range(1, n):
            offset = total - x
            vout = f"[vx{i}]"
            aout = f"[ax{i}]"
            parts.append(f"{vprev}[v{i}]xfade=transition=fade:duration={x:.3f}:offset={offset:.3f}{vout}")
            parts.append(f"{aprev}[a{i}]acrossfade=d={x:.3f}:c1=tri:c2=tri{aout}")
            total = total + durs[i] - x
            vprev, aprev = vout, aout
        vlast, alast = vprev, aprev
    if loudnorm:
        parts.append(f"{alast}loudnorm=I=-16:TP=-1.5:LRA=11[aout]")
        alast = "[aout]"
    cmd = [ffmpeg_bin(), "-y", "-hide_banner", "-loglevel", "error", *inputs, "-filter_complex", ";".join(parts), "-map", vlast, "-map", alast, *_encode_args(), str(out)]
    run(cmd)
    return out


def expected_stitch_duration(durations: Sequence[float], *, transition: str = "xfade", xfade_s: float = 0.35) -> float:
    ds = [float(d) for d in durations]
    if not ds:
        return 0.0
    if len(ds) == 1 or transition == "cut" or xfade_s <= 0:
        return sum(ds)
    x = min(xfade_s, min(ds) / 2.5)
    return sum(ds) - x * (len(ds) - 1)
