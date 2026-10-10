#!/usr/bin/env python3
"""Gate first-frame stills (Drive `input/phone`, `phone-refs/*`) before ③ uses them.

For every image: read the embedded generation prompt (A1111 / ComfyUI metadata) and run
the same minor lock as the text prompt (`select_loras.forbidden_hits`). Pixels are not
judged here; a human still looks at pose and anatomy. Exit 1 when anything is BLOCK.

    BLOCK  prompt names a minor (loli, 12-years-old, canon-minor character, ...) or file is broken
    WARN   no embedded prompt (phone photo / Imagine download: cannot verify, look yourself)
           or short side under --min-side (coarse still)
    OK     embedded prompt is clean and the still is large enough

usage:
    python3 check_ref_images.py /content/drive/MyDrive/minimax-h3-comfyui/input/phone
    python3 check_ref_images.py phone-refs/anal-doggy --min-side 900 --quarantine phone-refs/_blocked
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

from select_loras import ref_image_hits, ref_image_prompt

try:
    from PIL import Image
except ImportError:  # pragma: no cover - Pillow is present on Colab
    Image = None

IMAGE_SUFFIXES = (".png", ".jpg", ".jpeg", ".webp")
DEFAULT_MIN_SIDE = 720


def iter_images(targets: list[Path]) -> list[Path]:
    out: list[Path] = []
    for target in targets:
        if target.is_dir():
            out.extend(sorted(p for p in target.rglob("*") if p.suffix.lower() in IMAGE_SUFFIXES))
        elif target.is_file():
            out.append(target)
    return out


def image_size(path: Path) -> tuple[int, int] | None:
    if Image is None:
        return None
    try:
        with Image.open(path) as im:
            im.load()
            return int(im.width), int(im.height)
    except (OSError, ValueError, SyntaxError):
        return None


def judge(path: Path, *, min_side: int = DEFAULT_MIN_SIDE) -> tuple[str, str]:
    """Return (verdict, reason). Verdict is BLOCK / WARN / OK."""
    size = image_size(path)
    if size is None:
        return "BLOCK", "broken or truncated image"
    hits = ref_image_hits(path)
    if hits:
        return "BLOCK", "minors lock: embedded prompt has " + ", ".join(hits)
    notes: list[str] = []
    if min(size) < min_side:
        notes.append(f"coarse: {size[0]}x{size[1]} (short side under {min_side})")
    if not ref_image_prompt(path).strip():
        notes.append("no embedded prompt: cannot verify, check age/anatomy yourself")
    if notes:
        return "WARN", "; ".join(notes)
    return "OK", f"{size[0]}x{size[1]}, embedded prompt clean"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("targets", nargs="+", help="image files or folders (searched recursively)")
    ap.add_argument("--min-side", type=int, default=DEFAULT_MIN_SIDE, help="short side below this is WARN")
    ap.add_argument("--quarantine", help="move BLOCK files into this folder instead of leaving them")
    args = ap.parse_args(argv)
    paths = iter_images([Path(t) for t in args.targets])
    if not paths:
        print("no images found")
        return 0
    blocked = 0
    quarantine = Path(args.quarantine) if args.quarantine else None
    for path in paths:
        verdict, reason = judge(path, min_side=args.min_side)
        print(f"{verdict:5s} {path}  {reason}")
        if verdict != "BLOCK":
            continue
        blocked += 1
        if quarantine is not None:
            quarantine.mkdir(parents=True, exist_ok=True)
            shutil.move(str(path), str(quarantine / path.name))
    print(f"{len(paths)} images, {blocked} BLOCK")
    return 1 if blocked else 0


if __name__ == "__main__":
    sys.exit(main())
