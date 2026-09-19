#!/usr/bin/env python3
"""Pixelate human-drawn boxes onto a video. Not a legality or store gate."""

from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
from pathlib import Path

SCHEMA_VERSION = 1
DEFAULT_MARGIN = 0.2
DEFAULT_CELL_DIV = 100
MIN_CELL_PX = 4
VIDEO_CELL_BONUS = 1.5


class MosaicError(ValueError):
    pass


def load_boxes(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise MosaicError("boxes JSON must be an object")
    version = data.get("version", SCHEMA_VERSION)
    if version != SCHEMA_VERSION:
        raise MosaicError(f"unsupported boxes version: {version}")
    boxes = data.get("boxes")
    if not isinstance(boxes, list) or not boxes:
        raise MosaicError("boxes must be a non-empty list")
    parsed = []
    for i, box in enumerate(boxes):
        parsed.append(_parse_box(box, i))
    margin = float(data.get("margin", DEFAULT_MARGIN))
    if not 0 <= margin <= 1:
        raise MosaicError("margin must be between 0 and 1")
    cell_div = int(data.get("cell_div", DEFAULT_CELL_DIV))
    if cell_div < 10:
        raise MosaicError("cell_div must be >= 10")
    return {"boxes": parsed, "margin": margin, "cell_div": cell_div}


def _parse_box(box: object, index: int) -> dict[str, float]:
    if not isinstance(box, dict):
        raise MosaicError(f"box {index} must be an object")
    try:
        x = float(box["x"])
        y = float(box["y"])
        w = float(box["w"])
        h = float(box["h"])
    except (KeyError, TypeError, ValueError) as exc:
        raise MosaicError(f"box {index} needs numeric x,y,w,h in 0-1") from exc
    for name, value in (("x", x), ("y", y), ("w", w), ("h", h)):
        if not math.isfinite(value):
            raise MosaicError(f"box {index} {name} is not finite")
    if w <= 0 or h <= 0:
        raise MosaicError(f"box {index} w/h must be > 0")
    if x < 0 or y < 0 or x + w > 1.0001 or y + h > 1.0001:
        raise MosaicError(f"box {index} must stay inside the frame (fractions 0-1)")
    return {"x": x, "y": y, "w": w, "h": h}


def expand_box(box: dict[str, float], margin: float) -> dict[str, float]:
    extra_w = box["w"] * margin
    extra_h = box["h"] * margin
    x = max(0.0, box["x"] - extra_w / 2)
    y = max(0.0, box["y"] - extra_h / 2)
    right = min(1.0, box["x"] + box["w"] + extra_w / 2)
    bottom = min(1.0, box["y"] + box["h"] + extra_h / 2)
    return {"x": x, "y": y, "w": right - x, "h": bottom - y}


def mosaic_cell_px(long_edge: int, cell_div: int) -> int:
    heuristic = long_edge / cell_div
    return max(MIN_CELL_PX, int(math.ceil(heuristic * VIDEO_CELL_BONUS)))


def probe_video(path: Path) -> tuple[int, int]:
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=width,height",
        "-of",
        "csv=p=0:s=x",
        str(path),
    ]
    result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    line = result.stdout.strip().splitlines()[0]
    width_s, height_s = line.split("x")
    return int(width_s), int(height_s)


def _even(value: int) -> int:
    return value if value % 2 == 0 else value - 1


def pixel_box(box: dict[str, float], width: int, height: int) -> tuple[int, int, int, int]:
    x = int(round(box["x"] * width))
    y = int(round(box["y"] * height))
    w = int(round(box["w"] * width))
    h = int(round(box["h"] * height))
    x = max(0, min(width - 2, x))
    y = max(0, min(height - 2, y))
    w = max(2, min(width - x, w))
    h = max(2, min(height - y, h))
    w = max(2, _even(w))
    h = max(2, _even(h))
    if x + w > width:
        x = max(0, width - w)
    if y + h > height:
        y = max(0, height - h)
    return x, y, w, h


def build_filter(boxes: list[dict[str, float]], width: int, height: int, cell: int) -> str:
    cell = max(MIN_CELL_PX, cell)
    parts: list[str] = []
    current = "0:v"
    for i, box in enumerate(boxes):
        x, y, w, h = pixel_box(box, width, height)
        tiny_w = max(1, w // cell)
        tiny_h = max(1, h // cell)
        keep = f"k{i}"
        crop_l = f"c{i}"
        pix_l = f"p{i}"
        out_l = f"v{i}"
        parts.append(
            f"[{current}]split=2[{keep}][{crop_l}];"
            f"[{crop_l}]crop={w}:{h}:{x}:{y},scale={tiny_w}:{tiny_h}:flags=neighbor,"
            f"scale={w}:{h}:flags=neighbor[{pix_l}];"
            f"[{keep}][{pix_l}]overlay={x}:{y}[{out_l}]"
        )
        current = out_l
    return ";".join(parts)


def run_ffmpeg(input_path: Path, output_path: Path, filter_complex: str, n_boxes: int) -> None:
    mapped = f"[v{n_boxes - 1}]"
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(input_path),
        "-filter_complex",
        filter_complex,
        "-map",
        mapped,
        "-map",
        "0:a?",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "copy",
        str(output_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise MosaicError(result.stderr[-4000:] or "ffmpeg failed")


def write_contact_sheet(video_path: Path, sheet_path: Path, fps: float = 1.0) -> None:
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(video_path),
        "-vf",
        f"fps={fps},scale=320:-1,tile=5x5",
        "-frames:v",
        "1",
        str(sheet_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise MosaicError(result.stderr[-4000:] or "contact sheet failed")


def apply_mosaic(
    input_path: Path,
    boxes_path: Path,
    output_path: Path,
    sheet_path: Path | None = None,
) -> dict:
    spec = load_boxes(boxes_path)
    width, height = probe_video(input_path)
    expanded = [expand_box(box, spec["margin"]) for box in spec["boxes"]]
    cell = mosaic_cell_px(max(width, height), spec["cell_div"])
    filt = build_filter(expanded, width, height, cell)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    run_ffmpeg(input_path, output_path, filt, len(expanded))
    if sheet_path is not None:
        sheet_path.parent.mkdir(parents=True, exist_ok=True)
        write_contact_sheet(output_path, sheet_path)
    return {
        "width": width,
        "height": height,
        "cell_px": cell,
        "boxes": len(expanded),
        "output": str(output_path),
        "sheet": str(sheet_path) if sheet_path else None,
        "compliant": False,
        "note": "assist only; human frame review required; not a store or legal gate",
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Pixelate human-drawn boxes. Does not detect anatomy. "
            "Does not certify FANZA, DLsite, or criminal-law compliance."
        )
    )
    parser.add_argument("--in", dest="input_path", required=True, type=Path)
    parser.add_argument("--boxes", required=True, type=Path)
    parser.add_argument("--out", dest="output_path", required=True, type=Path)
    parser.add_argument("--sheet", dest="sheet_path", type=Path, default=None)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        result = apply_mosaic(args.input_path, args.boxes, args.output_path, args.sheet_path)
    except (MosaicError, FileNotFoundError, OSError) as exc:
        print(f"mosaic_apply: {exc}", file=sys.stderr)
        return 2
    except subprocess.CalledProcessError as exc:
        err = exc.stderr.decode() if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        print(f"mosaic_apply: probe failed: {err[-2000:]}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print(
        "NOT COMPLIANT. Watch the contact sheet. "
        "Do not upload until a human has checked every frame.",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
