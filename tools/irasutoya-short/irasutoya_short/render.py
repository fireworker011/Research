"""テロップと画面演出を乗せて、1本の mp4 に書き出す。"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from irasutoya_short.audio import fit_length, samples_for_frames, write_wav
from irasutoya_short.backgrounds import concentration, render_bg
from irasutoya_short.constants import FONT_CANDIDATES, FPS, HEIGHT, WIDTH
from irasutoya_short.qa import caption_hits_edge, caption_overlaps_face
from irasutoya_short.sprites import load_rgba, mouth_levels, scale_rgba
from irasutoya_short.style_draw import build_still, face_rects, load_font, telop_placement
from irasutoya_short.templates import telop_bar_fill, telop_color, telop_style

def bundled_font() -> str:
    for path in FONT_CANDIDATES:
        if Path(path).is_file():
            return path
    return ""


def find_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    path = bundled_font()
    if path:
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


def _bar_radius(kind: str, bar_h: int) -> int:
    if kind == "round":
        return 22
    if kind == "square":
        return 4
    if kind == "pill":
        return max(4, bar_h // 2)
    raise ValueError(f"未知のテロップ枠です: {kind}")


def render_telop(
    text: str,
    role: str,
    width: int,
    height: int,
    scale: float,
    y_ratio: float,
    tone: str = "",
    style: dict | None = None,
    placement: dict | None = None,
) -> np.ndarray:
    if placement is not None:
        return _render_placed_telop(text, role, placement, scale)
    overlay = np.zeros((height, width, 4), dtype=np.uint8)
    if not text.strip():
        return overlay
    look = style or telop_style("sukatto")
    tone_name = tone or role
    max_w = int(width * 0.92)
    start = 64 if role == "credit" else max(int(look["size"]), 104)
    size = max(36, int(start * scale))
    font = find_font(size)
    while size > 28:
        font = find_font(size)
        tw, th = _text_size(font, text)
        if tw <= max_w and th <= int(height * 0.34):
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
    radius = _bar_radius(str(look["bar"]), bar_h)
    draw.rounded_rectangle(
        (left, top, left + bar_w, top + bar_h),
        radius=radius,
        fill=telop_bar_fill(look, tone_name, role),
    )
    fill = telop_color(look, tone_name, role)
    tx = cx - tw // 2
    ty = top + pad_y - 4
    stroke = 4 if role == "credit" else max(6, int(look["stroke"]))
    for dx in range(-stroke, stroke + 1):
        for dy in range(-stroke, stroke + 1):
            if dx * dx + dy * dy > stroke * stroke:
                continue
            draw.multiline_text((tx + dx, ty + dy), text, font=font, fill=(0, 0, 0, 255), spacing=8, align="center")
    draw.multiline_text((tx, ty), text, font=font, fill=fill, spacing=8, align="center")
    return np.array(img)


def _stroke_ink(fill: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    lum = 0.3 * fill[0] + 0.59 * fill[1] + 0.11 * fill[2]
    if lum > 170:
        return (0, 0, 0, 255)
    return (255, 255, 255, 255)


def _wrap_chars(text: str, font: ImageFont.ImageFont, max_w: int) -> str:
    lines: list[str] = []
    for paragraph in text.split("\n"):
        line = ""
        for char in paragraph:
            trial = f"{line}{char}"
            if line and _text_size(font, trial)[0] > max_w:
                lines.append(line)
                line = char
            else:
                line = trial
        lines.append(line)
    return "\n".join(lines)


def _boxes_overlap(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> bool:
    return not (a[2] <= b[0] or b[2] <= a[0] or a[3] <= b[1] or b[3] <= a[1])


def _clear_of_faces(box: tuple[int, int, int, int], faces: list[tuple[int, int, int, int]]) -> bool:
    return all(not _boxes_overlap(box, face) for face in faces)


def _place_caption(
    width: int,
    height: int,
    bar_w: int,
    bar_h: int,
    faces: list[tuple[int, int, int, int]],
    mode: str,
    y_ratio: float,
) -> tuple[int, int]:
    margin = 32
    if bar_w > width - margin * 2:
        bar_w = width - margin * 2
    if bar_h > height - margin * 2:
        bar_h = height - margin * 2
    candidates: list[tuple[int, int]] = []
    if mode == "note":
        candidates.append((width - bar_w - margin, height - bar_h - margin))
    elif mode == "center":
        candidates.append(((width - bar_w) // 2, (height - bar_h) // 2))
    elif y_ratio >= 0.5:
        candidates.append((margin, height - bar_h - margin))
    else:
        candidates.append((margin, margin))
    candidates.append(((width - bar_w) // 2, margin))
    candidates.append(((width - bar_w) // 2, height - bar_h - margin))
    for top in range(margin, max(margin + 1, height - margin - bar_h), 20):
        candidates.append(((width - bar_w) // 2, top))
    for left, top in candidates:
        left = max(margin, min(left, width - margin - bar_w))
        top = max(margin, min(top, height - margin - bar_h))
        box = (left, top, left + bar_w, top + bar_h)
        if _clear_of_faces(box, faces):
            return left, top
    return margin, margin


def _render_placed_telop(text: str, role: str, placement: dict, scale: float) -> np.ndarray:
    width = int(placement.get("width") or WIDTH)
    height = int(placement.get("height") or HEIGHT)
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    if not text.strip():
        return np.array(image)
    mode = str(placement["mode"])
    size = max(28, int(int(placement["size"]) * scale))
    if role == "credit":
        size = min(size, 48)
    faces = [tuple(item) for item in placement.get("faces") or []]
    fill = tuple(placement["fill"])
    stroke_color = _stroke_ink(fill)
    stroke = 3 if role == "credit" else int(placement["stroke"])
    margin = 32
    max_w = width - margin * 2 - 48
    max_h = int(height * (0.55 if role == "credit" else 0.34))
    font_path = str(placement["font"])
    bold_path = str(placement.get("font_bold") or "")
    if mode == "vertical":
        font, size, columns = _fit_vertical(text, font_path, size, max_w, height - margin * 2)
        block_w = max(size, len(columns) * (size + 16))
        block_h = max((size + 4) * max(len(column) for column in columns), size)
        left, top = _place_vertical(width, height, block_w, block_h, faces)
        draw = ImageDraw.Draw(image)
        _draw_vertical(draw, columns, font, fill, stroke_color, stroke, size, left, top)
        return np.array(image)
    font = load_font(font_path, size)
    wrapped = text
    while size > 22:
        font = load_font(font_path, size)
        wrapped = _wrap_chars(text, font, max_w)
        tw, th = _text_size(font, wrapped)
        if tw <= max_w and th <= max_h:
            break
        size -= 2
    tw, th = _text_size(font, wrapped)
    pad_x, pad_y = 24, 14
    bar_w = min(width - margin * 2, max(tw + pad_x * 2, 80))
    bar_h = min(height - margin * 2, th + pad_y * 2)
    left, top = _place_caption(width, height, bar_w, bar_h, faces, mode, float(placement["y_ratio"]))
    draw = ImageDraw.Draw(image)
    if mode == "note":
        _draw_note(image, wrapped, font, fill, stroke_color, stroke, bar_w, bar_h, left, top)
        return np.array(image)
    bar_fill = tuple(placement["bar_fill"])
    radius = 8 if placement.get("bar") == "square" else 18
    draw.rounded_rectangle((left, top, left + bar_w, top + bar_h), radius=min(radius, bar_h // 2), fill=bar_fill)
    _draw_emphasis(
        draw, wrapped, font, bold_path, size, fill, stroke_color, stroke,
        left, top, bar_w, pad_y, bool(placement.get("emphasis")),
    )
    return np.array(image)


def _place_vertical(
    width: int,
    height: int,
    block_w: int,
    block_h: int,
    faces: list[tuple[int, int, int, int]],
) -> tuple[int, int]:
    margin = 32
    top = max(margin, min((height - block_h) // 2, height - margin - block_h))
    xs = [margin, max(margin, width - margin - block_w)]
    xs.extend(range(margin, max(margin + 1, width - margin - block_w), 24))
    for left in xs:
        box = (left, top, left + block_w, top + block_h)
        if _clear_of_faces(box, faces):
            return left, top
    return margin, top


def _draw_emphasis(draw, text, font, bold_path, size, fill, stroke_color, stroke, left, top, bar_w, pad_y, emphasis: bool) -> None:
    if not emphasis or "\n" not in text or not bold_path:
        tw, _th = _text_size(font, text)
        tx = left + (bar_w - tw) // 2
        ty = top + pad_y - 2
        _stroke_text(draw, (tx, ty), text, font, fill, stroke_color, stroke, align="center")
        return
    head, _, rest = text.partition("\n")
    head_font = load_font(bold_path, size + 8)
    body_font = font
    hw, hh = _text_size(head_font, head)
    rw, _rh = _text_size(body_font, rest) if rest else (0, 0)
    y = top + 8
    _stroke_text(draw, (left + (bar_w - hw) // 2, y), head, head_font, fill, stroke_color, stroke + 2, align="center")
    if rest:
        _stroke_text(draw, (left + (bar_w - rw) // 2, y + hh + 6), rest, body_font, fill, stroke_color, max(2, stroke - 1), align="center")


def _stroke_text(draw, xy, text, font, fill, stroke_color, stroke, align: str) -> None:
    x, y = xy
    if stroke > 0:
        for dx in range(-stroke, stroke + 1, 2):
            for dy in range(-stroke, stroke + 1, 2):
                if dx * dx + dy * dy > stroke * stroke:
                    continue
                draw.multiline_text((x + dx, y + dy), text, font=font, fill=stroke_color, spacing=6, align=align)
    draw.multiline_text((x, y), text, font=font, fill=fill, spacing=6, align=align)


def _fit_vertical(text: str, path: str, size: int, max_w: int, max_h: int) -> tuple[ImageFont.ImageFont, int, list[str]]:
    source = [column for column in text.split("\n") if column] or [text]
    columns = source
    while size > 22:
        limit = max(1, max_h // (size + 4))
        columns = []
        for column in source:
            for start in range(0, len(column), limit):
                columns.append(column[start : start + limit])
        columns = columns or source
        tall = max(len(column) for column in columns) * (size + 4)
        wide = len(columns) * (size + 16)
        if tall <= max_h and wide <= max_w:
            break
        size -= 2
    return load_font(path, size), size, columns


def _draw_vertical(draw, columns, font, fill, stroke_color, stroke, size, left: int, top: int) -> None:
    x = left
    for column in columns:
        y = top
        for char in column:
            _stroke_text(draw, (x, y), char, font, fill, stroke_color, max(1, stroke), align="left")
            y += size + 4
        x += size + 16


def _draw_note(image, text, font, fill, stroke_color, stroke, bar_w, bar_h, left: int, top: int) -> None:
    note = Image.new("RGBA", (bar_w, bar_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(note)
    paper = (255, 248, 220, 235)
    draw.rounded_rectangle((0, 0, bar_w - 1, bar_h - 1), radius=6, fill=paper)
    tw, _th = _text_size(font, text)
    _stroke_text(draw, (max(8, (bar_w - tw) // 2), 10), text, font, fill, stroke_color, stroke, align="center")
    turned = note.rotate(7, expand=True, resample=Image.Resampling.BICUBIC)
    x = min(left, image.size[0] - turned.width - 8)
    y = min(top, image.size[1] - turned.height - 8)
    image.alpha_composite(turned, (max(8, x), max(8, y)))


def _zoom(frame: np.ndarray, zoom: float) -> np.ndarray:
    if zoom <= 1.01:
        return frame
    h, w = frame.shape[:2]
    cw, ch = int(w / zoom), int(h / zoom)
    x0, y0 = (w - cw) // 2, (h - ch) // 2
    crop = frame[y0 : y0 + ch, x0 : x0 + cw]
    im = Image.fromarray(crop, "RGB").resize((w, h), Image.Resampling.BILINEAR)
    return np.array(im)


def shift_frame(frame: np.ndarray, dx: int, dy: int) -> np.ndarray:
    """画面をずらす。はみ出した分は端の色を伸ばし、反対側へ回さない。"""
    if dx == 0 and dy == 0:
        return frame
    height, width = frame.shape[:2]
    y_idx = np.clip(np.arange(height) - dy, 0, height - 1)
    x_idx = np.clip(np.arange(width) - dx, 0, width - 1)
    return frame[y_idx[:, None], x_idx[None, :]]


def _shake(frame: np.ndarray, amp: int, t: float) -> np.ndarray:
    if amp <= 0:
        return frame
    dx = int(amp * np.sin(t * 47))
    dy = int(amp * np.cos(t * 33))
    return shift_frame(frame, dx, dy)


def _is_reaction(scene: dict) -> bool:
    if scene.get("effect") in ("shake", "zoom_shake"):
        return True
    return scene.get("sfx") in ("shock",)


def _light_motion(frame: np.ndarray, scene: dict, local_t: float, axes: dict | None = None) -> np.ndarray:
    """ゆっくりズームとパン。反応のシーンだけ、小さく揺らす。字幕はここより後に載せる。"""
    tempo = "" if not axes else str(axes.get("M") or "")
    duration = max(float(scene.get("duration") or 0.01), 0.01)
    p = min(1.0, local_t / duration)
    # 署名なしの旧作は、以前のパンとズームのまま。
    if not axes:
        dx = int(round((p - 0.5) * 28))
        dy = int(round((0.5 - p) * 12))
        moved = shift_frame(frame, dx, dy)
        if _is_reaction(scene):
            moved = _shake(moved, 5, local_t)
        return _zoom(moved, 1.02 + 0.045 * p)
    # 1.5秒以上同じ絵が続かないよう、どのテンポでも少しずつずらす。
    drift_x = int(round(local_t * 8))
    drift_y = int(round(local_t * 10))
    if tempo == "M6":
        moved = shift_frame(frame, drift_x, drift_y)
        return moved if moved is not frame else frame.copy()
    if tempo == "M2":
        pan, rise, base = 28, 0.045, 1.02
    elif tempo == "M1":
        pan, rise, base = 48, 0.08, 1.03
    elif tempo == "M3":
        pan, rise, base = 16, 0.02, 1.01
    else:
        pan, rise, base = 28, 0.045, 1.02
    dx = int(round((p - 0.5) * pan)) + drift_x
    dy = int(round((0.5 - p) * 12)) + drift_y
    moved = shift_frame(frame, dx, dy)
    if _is_reaction(scene):
        moved = _shake(moved, 5, local_t)
    return _zoom(moved, base + rise * p)


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
        blit(frame, sprite, x, y)


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


def compose_frame(scene, book, bg, lines, telop, openness, mouth_gain, layout, local_t, style=None) -> np.ndarray:
    frame = bg.copy()
    if scene["effect"] == "lines" or scene["bg"] == "lines":
        blit(frame, lines, 0, 0)
    _draw_papers(frame, scene)
    _place_props(frame, scene, book)
    _place_characters(frame, scene, book, openness, mouth_gain, layout)
    look = style or telop_style("sukatto")
    slide_seconds = max(0.04, float(look.get("slide", 0.16)))
    slide = int(30 * max(0.0, 1.0 - local_t / slide_seconds))
    frame = _light_motion(frame, scene, local_t)
    blit(frame, telop, 0, slide)
    return frame


def _styled_layers(project: dict, scenes: list[dict], book: SpriteBook, settings: dict):
    axes = project["style_axes"]
    cast = list(project.get("style_cast") or [])
    used: set[str] = set()
    stills = []
    leads = []
    telops = []
    for index, scene in enumerate(scenes):
        stills.append(build_still(scene, book, axes, cast, index, len(scenes), used))
        if float(scene.get("lead") or 0) > 0:
            leads.append(build_still(scene, book, axes, cast, index, len(scenes), used, hide_people=True))
        else:
            leads.append(None)
        placement = telop_placement(axes, scene)
        if scene.get("role") == "credit":
            faces: list[tuple[int, int, int, int]] = []
        else:
            slop = 48 + int(float(scene.get("duration") or 1) * 12)
            faces = [
                (
                    max(0, x0 - slop),
                    max(0, y0 - slop),
                    min(WIDTH, x1 + slop),
                    min(HEIGHT, y1 + slop),
                )
                for x0, y0, x1, y1 in face_rects(book, axes, cast, index)
            ]
        placement["faces"] = faces
        telop = render_telop(
            scene["telop"],
            scene["role"],
            WIDTH,
            HEIGHT,
            settings["telop_scale"],
            0.5,
            str(scene.get("tone") or scene["role"]),
            None,
            placement,
        )
        if caption_overlaps_face(telop, faces):
            raise RuntimeError(f"テロップが顔にかかっています: scene {scene.get('id')}")
        if caption_hits_edge(telop):
            raise RuntimeError(f"テロップが画面の端で切れています: scene {scene.get('id')}")
        telops.append(telop)
    project["style_used_assets"] = sorted(used)
    return stills, leads, telops


def render_movie(project: dict, out_path: Path, preview_dir: Path | None = None, *, pictures_only: bool = False) -> int:
    """フレームを書き出す。pictures_only のときは声を載せない。戻り値はフレーム数。"""
    scenes = project["scenes"]
    settings = project["settings"]
    layout = project["layout"]
    style = project.get("telop_style") or telop_style(str(project.get("template") or "sukatto"))
    book = SpriteBook(project["asset_paths"])
    axes = project.get("style_axes")
    if axes:
        bgs = {}
        lines = None
        stills, leads, telops = _styled_layers(project, scenes, book, settings)
    else:
        stills, leads = [], []
        bgs = {name: render_bg(name) for name in {s["bg"] for s in scenes}}
        lines = concentration()
        telops = [
            render_telop(
                s["telop"],
                s["role"],
                WIDTH,
                HEIGHT,
                settings["telop_scale"],
                0.5 if s["role"] == "credit" else layout["telop_y_ratio"],
                str(s.get("tone") or s["role"]),
                style,
            )
            for s in scenes
        ]
    nframes = sum(int(round(s["duration"] * FPS)) for s in scenes)
    if preview_dir is not None:
        preview_dir.mkdir(parents=True, exist_ok=True)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    wav_path = out_path.with_suffix(".mix.wav")
    if pictures_only:
        proc = _open_video_encoder(out_path)
    else:
        audio = fit_length(np.asarray(project["audio"], dtype=np.float32), samples_for_frames(nframes))
        write_wav(wav_path, audio)
        proc = _open_encoder(out_path, wav_path)
    scene_i = 0
    scene_frame = 0
    scene_len = int(round(scenes[0]["duration"] * FPS))
    print(f"scene {scenes[0]['id']}/{len(scenes)}", flush=True)
    try:
        for _ in range(nframes):
            if scene_frame >= scene_len and scene_i < len(scenes) - 1:
                scene_i += 1
                scene_frame = 0
                scene_len = int(round(scenes[scene_i]["duration"] * FPS))
                print(f"scene {scenes[scene_i]['id']}/{len(scenes)}", flush=True)
            scene = scenes[scene_i]
            env = scene["envelope"]
            openness = float(env[scene_frame]) if scene_frame < len(env) else 0.0
            local_t = scene_frame / FPS
            if axes:
                lead = float(scene.get("lead") or 0)
                base = leads[scene_i] if leads[scene_i] is not None and local_t < lead else stills[scene_i]
                frame = _light_motion(base.copy(), scene, local_t, axes)
                blit(frame, telops[scene_i], 0, 0)
            else:
                frame = compose_frame(
                    scene, book, bgs[scene["bg"]], lines, telops[scene_i],
                    openness, settings["mouth_gain"], layout, local_t, style,
                )
            peak = int(np.argmax(env)) if len(env) else 0
            if preview_dir is not None and scene_frame == peak:
                Image.fromarray(frame, "RGB").save(preview_dir / f"scene_{scene['id']:02d}.png")
            _write_frame(proc, frame)
            scene_frame += 1
    except Exception:
        _stop_encoder(proc)
        raise
    else:
        _finish_encoder(proc, out_path)
    finally:
        if not pictures_only:
            wav_path.unlink(missing_ok=True)
    return nframes


def mux_voice(video: Path, wav: Path, out_path: Path) -> None:
    """書き出した絵はそのままに、声だけ載せる。"""
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("ffmpeg がありません。docs/GROK_BUILD.md のパッケージ手順を実行してください。")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-i", str(video),
        "-i", str(wav),
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "160k",
        "-movflags", "+faststart",
        "-shortest",
        str(out_path),
    ]
    proc = subprocess.run(cmd, capture_output=True)
    if proc.returncode != 0:
        err = proc.stderr.decode("utf-8", "replace").strip()
        raise RuntimeError(f"ffmpeg が失敗しました: {err or out_path}")


def _open_video_encoder(path: Path) -> subprocess.Popen[bytes]:
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("ffmpeg がありません。docs/GROK_BUILD.md のパッケージ手順を実行してください。")
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{WIDTH}x{HEIGHT}", "-r", str(FPS),
        "-i", "pipe:0",
        "-an",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
        "-pix_fmt", "yuv420p", "-vsync", "cfr",
        "-movflags", "+faststart",
        str(path),
    ]
    return subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)


def _open_encoder(path: Path, wav_path: Path) -> subprocess.Popen[bytes]:
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("ffmpeg がありません。docs/GROK_BUILD.md のパッケージ手順を実行してください。")
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{WIDTH}x{HEIGHT}", "-r", str(FPS),
        "-i", "pipe:0",
        "-i", str(wav_path),
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
        "-pix_fmt", "yuv420p", "-vsync", "cfr",
        "-c:a", "aac", "-b:a", "160k",
        "-movflags", "+faststart",
        "-shortest",
        str(path),
    ]
    return subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)


def _write_frame(proc: subprocess.Popen[bytes], frame: np.ndarray) -> None:
    if proc.stdin is None:
        raise RuntimeError("ffmpeg の入力が開いていません。")
    try:
        proc.stdin.write(frame.tobytes())
    except BrokenPipeError as exc:
        err = _read_stderr(proc)
        raise RuntimeError(f"ffmpeg が失敗しました: {err or '入力が閉じられました'}") from exc


def _finish_encoder(proc: subprocess.Popen[bytes], path: Path) -> None:
    if proc.stdin is not None:
        try:
            proc.stdin.close()
        except BrokenPipeError as exc:
            err = _read_stderr(proc)
            proc.wait(timeout=30)
            raise RuntimeError(f"ffmpeg が失敗しました: {err or path}") from exc
    try:
        code = proc.wait(timeout=600)
    except subprocess.TimeoutExpired as exc:
        proc.kill()
        proc.wait(timeout=30)
        raise RuntimeError(f"ffmpeg が時間内に終わりませんでした: {path}") from exc
    err = _read_stderr(proc)
    if code != 0:
        raise RuntimeError(f"ffmpeg が失敗しました: {err or path}")


def _stop_encoder(proc: subprocess.Popen[bytes]) -> None:
    if proc.poll() is None:
        proc.kill()
    if proc.stdin is not None:
        try:
            proc.stdin.close()
        except BrokenPipeError:
            pass
    try:
        proc.wait(timeout=30)
    except subprocess.TimeoutExpired:
        pass


def _read_stderr(proc: subprocess.Popen[bytes]) -> str:
    if proc.stderr is None:
        return ""
    return proc.stderr.read().decode("utf-8", "replace").strip()
