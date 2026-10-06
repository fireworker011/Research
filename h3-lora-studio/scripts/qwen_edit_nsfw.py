#!/usr/bin/env python3
"""Qwen Image Edit NSFW helper for H3 start stills.

Clothed AI stills become nude erect futanari. Face, hair, pose, and background stay.
Never commit JPGs. Never undress photoreal strangers.

Proven call (2026-09, Cloud Agent bc-01a0a99c):
  Mk1227/Qwen-Image-Edit-NSFW  api_name=/infer
  576x1024 (portrait) or 1024x576 (landscape)
  steps=4  guidance=1.0  rewrite_prompt=False  zerogpu_budget=80
Fallbacks: ayooo123 / Cengizl / metaloz clones of the same /infer.
Quota is reserved seconds (80s/run), not wall GPU time.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any, Callable, Literal

try:
    from PIL import Image
except ImportError:  # pragma: no cover - tests skip image I/O
    Image = None  # type: ignore[assignment]

try:
    from gradio_client import Client, handle_file
except ImportError:
    Client = None  # type: ignore[assignment]
    handle_file = None  # type: ignore[assignment]

ROOT = Path(__file__).resolve().parents[2]
STUDIO = ROOT / "h3-lora-studio"
DEFAULT_MANIFEST = STUDIO / "start-stills.json"

SPACES = (
    "Mk1227/Qwen-Image-Edit-NSFW",
    "ayooo123/Qwen-Image-Edit-NSFWpyyy",
    "Cengizl/Qwen-Image-Edit-NSFW",
    "metaloz/Qwen-Image-Edit-NSFWoz",
)
API_NAME = "/infer"
PORTRAIT = (576, 1024)
LANDSCAPE = (1024, 576)
STEPS = 4
GUIDANCE = 1.0
REWRITE_PROMPT = False
ZEROGPU_BUDGET = 80
JPEG_QUALITY = 92
DEFAULT_OUT = Path("/tmp/h3-start")

Mode = Literal["undress_futa", "crotch_only", "copy", "skip_photoreal"]
MODES: tuple[Mode, ...] = ("undress_futa", "crotch_only", "copy", "skip_photoreal")

PHOTOREAL_NAME_MARKS = (
    "photoreal",
    "realperson",
    "real-person",
    "実写",
)
QUOTA_NEEDLES = (
    "no gpu",
    "zerogpu",
    "gpu quota",
    "gpu budget",
    "runs limit",
    "429",
    "too many requests",
    "queue full",
    "cuda",
)
DEFAULT_NEG = (
    "clothes, dress, underwear, skirt, testicles, scrotum, balls, "
    "male body, child"
)

UNDRESS_KEEP = (
    "Keep the exact same face, hair, pose, camera, lighting, and background. "
    "Adult woman clearly over 21. "
)
FUTA_ANATOMY = (
    "Futanari: hairless female pussy at the base of a clearly visible fully erect "
    "20 centimeter human penis, pale shaft, pink glans. No testicles, no scrotum. "
    "Do not change hairstyle. Do not enlarge the breasts. Not a man."
)


def target_wh(size: tuple[int, int]) -> tuple[int, int]:
    width, height = size
    if width > height:
        return LANDSCAPE
    return PORTRAIT


def is_quota_error(exc: BaseException) -> bool:
    text = str(exc).lower()
    return any(needle in text for needle in QUOTA_NEEDLES)


def is_photoreal_path(path: Path, extra: tuple[str, ...] = ()) -> bool:
    name = path.name.lower()
    marks = PHOTOREAL_NAME_MARKS + tuple(m.lower() for m in extra)
    return any(mark in name for mark in marks)


def assert_out_outside_repo(path: Path, repo: Path = ROOT) -> None:
    resolved = path.resolve()
    repo_r = repo.resolve()
    if resolved == repo_r or repo_r in resolved.parents:
        raise SystemExit("JPGをリポジトリに入れるな")


def undress_futa_prompt(clothes: str, keep: str = "") -> str:
    extra = f" {keep.strip()}" if keep.strip() else ""
    cloth = clothes.strip() or "clothes"
    return (
        f"Remove only the {cloth}. Fully nude. {UNDRESS_KEEP}{extra} {FUTA_ANATOMY}"
    ).strip()


def crotch_only_prompt(keep: str = "") -> str:
    extra = f" {keep.strip()}" if keep.strip() else ""
    return (
        f"Keep everything identical.{extra} She stays fully nude. "
        "Only change the crotch: add a clearly visible fully erect "
        "20 centimeter human penis with a pale shaft and pink glans. "
        f"{FUTA_ANATOMY} No clothes."
    ).strip()


def prompt_for(mode: Mode, clothes: str = "", keep: str = "") -> str:
    if mode == "undress_futa":
        return undress_futa_prompt(clothes, keep)
    if mode == "crotch_only":
        return crotch_only_prompt(keep)
    if mode == "copy":
        return ""
    if mode == "skip_photoreal":
        return ""
    raise ValueError(f"unhandled mode: {mode}")


def parse_mode(raw: str) -> Mode:
    if raw in MODES:
        return raw  # type: ignore[return-value]
    raise SystemExit(f"unknown mode: {raw}")


def infer_payload(
    image_path: Path,
    prompt: str,
    *,
    negative_prompt: str = DEFAULT_NEG,
    seed: int = 0,
    randomize_seed: bool = True,
    width: int = PORTRAIT[0],
    height: int = PORTRAIT[1],
    file_wrapper: Callable[[str], Any] | None = None,
) -> dict[str, Any]:
    wrap = file_wrapper or handle_file
    if wrap is None:
        raise SystemExit("gradio_client is not installed")
    return {
        "images": [{"image": wrap(str(image_path)), "caption": None}],
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "seed": seed,
        "randomize_seed": randomize_seed,
        "true_guidance_scale": GUIDANCE,
        "num_inference_steps": STEPS,
        "height": height,
        "width": width,
        "rewrite_prompt": REWRITE_PROMPT,
        "zerogpu_budget": ZEROGPU_BUDGET,
        "api_name": API_NAME,
    }


def space_queue(preferred: str | None = None) -> list[str]:
    ordered = list(SPACES)
    if preferred and preferred not in ordered:
        ordered.insert(0, preferred)
    elif preferred:
        ordered.remove(preferred)
        ordered.insert(0, preferred)
    return ordered


def infer_with_fallback(
    payload: dict[str, Any],
    *,
    spaces: list[str] | None = None,
    client_factory: Callable[[str], Any] | None = None,
) -> tuple[str, Any]:
    factory = client_factory or _default_client
    last: BaseException | None = None
    for space in spaces or space_queue():
        try:
            client = factory(space)
            return space, client.predict(**payload)
        except Exception as exc:  # noqa: BLE001 - remote space errors
            last = exc
            if is_quota_error(exc):
                print(f"quota {space}: {exc}", file=sys.stderr)
                continue
            raise
    raise SystemExit(f"all Qwen Edit spaces failed: {last}")


def _default_client(space: str) -> Any:
    if Client is None:
        raise SystemExit("gradio_client is not installed")
    return Client(space)


def result_image_path(result: Any) -> Path:
    gallery = result[0]
    first = gallery[0]
    if isinstance(first, dict):
        return Path(first["image"])
    return Path(first)


def resize_rgb(src: Path, dest: Path) -> tuple[int, int]:
    if Image is None:
        raise SystemExit("Pillow is not installed")
    image = Image.open(src).convert("RGB")
    width, height = target_wh(image.size)
    image = image.resize((width, height))
    dest.parent.mkdir(parents=True, exist_ok=True)
    image.save(dest, quality=90)
    return width, height


def save_jpeg(src: Path, dest: Path, quality: int = JPEG_QUALITY) -> None:
    if Image is None:
        raise SystemExit("Pillow is not installed")
    assert_out_outside_repo(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    Image.open(src).convert("RGB").save(dest, quality=quality)


def load_manifest(path: Path = DEFAULT_MANIFEST) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def plan_frame(frame: dict[str, Any]) -> dict[str, Any]:
    mode = parse_mode(str(frame.get("mode") or "copy"))
    photoreal = bool(frame.get("photoreal")) or mode == "skip_photoreal"
    if photoreal:
        mode = "skip_photoreal"
    clothes = str(frame.get("clothes") or "")
    keep = str(frame.get("keep") or "")
    return {
        "id": frame.get("id"),
        "name": frame.get("name"),
        "mode": mode,
        "photoreal": photoreal,
        "out": frame.get("out"),
        "prompt": prompt_for(mode, clothes, keep),
        "negative_prompt": DEFAULT_NEG if mode in ("undress_futa", "crotch_only") else "",
        "spaces": list(SPACES),
        "steps": STEPS,
        "guidance": GUIDANCE,
        "rewrite_prompt": REWRITE_PROMPT,
        "zerogpu_budget": ZEROGPU_BUDGET,
        "api": API_NAME,
    }


def copy_still(src: Path, dest: Path) -> None:
    assert_out_outside_repo(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)


def edit_still(
    src: Path,
    dest: Path,
    *,
    mode: Mode,
    clothes: str = "",
    keep: str = "",
    space: str | None = None,
    work_dir: Path | None = None,
) -> dict[str, Any]:
    if is_photoreal_path(src) or mode == "skip_photoreal":
        raise SystemExit("実写の他人を全裸化するな")
    assert_out_outside_repo(dest)
    if mode == "copy":
        copy_still(src, dest)
        return {"mode": "copy", "out": str(dest), "space": None}

    work = work_dir or dest.parent
    work.mkdir(parents=True, exist_ok=True)
    resized = work / f"in-{src.stem}-edit.jpg"
    width, height = resize_rgb(src, resized)
    payload = infer_payload(
        resized,
        prompt_for(mode, clothes, keep),
        width=width,
        height=height,
    )
    used, result = infer_with_fallback(payload, spaces=space_queue(space))
    raw = result_image_path(result)
    save_jpeg(raw, dest)
    return {"mode": mode, "out": str(dest), "space": used, "size": [width, height]}


def _check() -> int:
    manifest = load_manifest()
    editor = manifest["editor"]
    assert editor["primary"] == SPACES[0]
    assert editor["api"] == API_NAME
    assert tuple(editor["portrait"]) == PORTRAIT
    assert editor["steps"] == STEPS
    assert editor["guidance"] == GUIDANCE
    assert editor["rewrite_prompt"] is False
    assert editor["zerogpu_budget"] == ZEROGPU_BUDGET
    modes = [parse_mode(str(frame["mode"])) for frame in manifest["frames"]]
    assert "undress_futa" in modes
    assert "skip_photoreal" in modes
    print("qwen_edit_nsfw ok")
    print("primary", SPACES[0])
    print("api", API_NAME)
    print("portrait", "x".join(map(str, PORTRAIT)))
    print("steps", STEPS, "guidance", GUIDANCE, "budget", ZEROGPU_BUDGET)
    return 0


def _plan(args: argparse.Namespace) -> int:
    if args.manifest:
        for frame in load_manifest(Path(args.manifest))["frames"]:
            print(json.dumps(plan_frame(frame), ensure_ascii=False))
        return 0
    mode = parse_mode(args.mode)
    src = Path(args.src) if args.src else Path("IN.jpg")
    if args.photoreal or is_photoreal_path(src):
        mode = "skip_photoreal"
    print(
        json.dumps(
            plan_frame(
                {
                    "id": src.stem,
                    "name": src.name,
                    "mode": mode,
                    "clothes": args.clothes,
                    "keep": args.keep,
                    "photoreal": mode == "skip_photoreal",
                    "out": args.dest or src.stem + "-futa.jpg",
                }
            ),
            ensure_ascii=False,
        )
    )
    return 0


def _run(args: argparse.Namespace) -> int:
    src = Path(args.src)
    dest = Path(args.dest) if args.dest else DEFAULT_OUT / f"{src.stem}-futa.jpg"
    mode = parse_mode(args.mode)
    if args.photoreal or is_photoreal_path(src):
        raise SystemExit("実写の他人を全裸化するな")
    info = edit_still(
        src,
        dest,
        mode=mode,
        clothes=args.clothes,
        keep=args.keep,
        space=args.space,
    )
    print(json.dumps(info, ensure_ascii=False))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="offline recipe lock")
    parser.add_argument("--plan", action="store_true", help="print prompts, do not call GPU")
    parser.add_argument("--manifest", help="start-stills.json")
    parser.add_argument("--in", dest="src", help="source still")
    parser.add_argument("--out", dest="dest", help="jpeg outside the git repo")
    parser.add_argument("--mode", default="undress_futa", choices=MODES)
    parser.add_argument("--clothes", default="", help="garment to remove")
    parser.add_argument("--keep", default="", help="face/hair/scene lock")
    parser.add_argument("--space", default="", help="preferred HF space")
    parser.add_argument(
        "--photoreal",
        action="store_true",
        help="mark as a real person; always refused",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.check:
        return _check()
    if args.plan or args.manifest and args.src is None:
        return _plan(args)
    if not args.src:
        raise SystemExit("need --in or --check / --plan")
    return _run(args)


if __name__ == "__main__":
    raise SystemExit(main())
