"""One entry for T2VA (no image) and Ref2VA (one still, no reference video)."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from h3_runner.official import DEFAULT_STEPS, README_MAX_DURATION_S, README_MIN_DURATION_S
from h3_runner.planner import orbis01_plan, single_plan

# diffusers and torch are imported inside the generate step. A dry run only
# prints the official request plan and must not require a CUDA install.


def package_root() -> Path:
    return Path(__file__).resolve().parents[1]


def detect_vram_gb() -> float | None:
    # torch is optional so a dry run on a machine without it still prints the plan.
    try:
        import torch
    except ImportError:
        return None
    if not torch.cuda.is_available():
        return None
    return float(torch.cuda.get_device_properties(0).total_memory) / 1024**3


def detect_host_ram_gb() -> float:
    meminfo = Path("/proc/meminfo").read_text(encoding="utf-8")
    for line in meminfo.splitlines():
        if line.startswith("MemTotal:"):
            return int(line.split()[1]) / 1024**2
    raise RuntimeError("/proc/meminfo に MemTotal が無い")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="MiniMax H3 still or text to a 9:16 mp4")
    parser.add_argument("--preset", choices=["orbis01"], help="bundled Sakura 6s+9s job")
    parser.add_argument("--task", choices=["t2va", "ref2va"])
    parser.add_argument("--prompt-file", type=Path)
    parser.add_argument("--image", type=Path, help="Ref2VA still. Omit for T2VA.")
    parser.add_argument("--duration", type=float, help=f"{README_MIN_DURATION_S:g} to {README_MAX_DURATION_S:g} seconds")
    parser.add_argument("--aspect", default="9:16")
    parser.add_argument("--short-edge", type=int, help="default 768, lowered when the 80GB budget says so")
    parser.add_argument("--width", type=int)
    parser.add_argument("--height", type=int)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--steps", type=int, default=DEFAULT_STEPS)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--out-dir", type=Path)
    parser.add_argument("--offload", choices=["auto", "bf16", "int8"], default="auto")
    parser.add_argument("--force-one-shot", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--vram-gb", type=float)
    parser.add_argument("--host-ram-gb", type=float)
    parser.add_argument("--split-t2va-prompt", type=Path)
    parser.add_argument("--split-ref2va-prompt", type=Path)
    parser.add_argument("--split-image", type=Path)
    return parser.parse_args(argv)


def _resources(args: argparse.Namespace) -> tuple[float, float]:
    vram = args.vram_gb if args.vram_gb is not None else detect_vram_gb()
    if vram is None:
        vram = 80.0
    if args.host_ram_gb is not None:
        host = args.host_ram_gb
    else:
        host = detect_host_ram_gb()
    return float(vram), float(host)


def build_from_args(args: argparse.Namespace):
    vram, host = _resources(args)
    root = package_root()
    if args.preset == "orbis01":
        out_dir = args.out_dir or args.out or Path(os.environ.get("H3_OUT_DIR", "output"))
        if args.out and args.out.suffix == ".mp4" and args.out_dir is None:
            out_dir = args.out.parent
        return orbis01_plan(
            root,
            Path(out_dir),
            seed=args.seed,
            steps=args.steps,
            aspect=args.aspect,
            vram_gb=vram,
            host_ram_gb=host,
            offload=args.offload,
            force_one_shot=args.force_one_shot,
        )
    if not args.task or not args.prompt_file or args.duration is None or not args.out:
        raise SystemExit("preset 以外は --task --prompt-file --duration --out が要る")
    return single_plan(
        task=args.task,
        prompt_path=args.prompt_file,
        image_path=args.image,
        duration_s=float(args.duration),
        aspect=args.aspect,
        seed=args.seed,
        steps=args.steps,
        out_path=args.out,
        short_edge=args.short_edge,
        width=args.width,
        height=args.height,
        vram_gb=vram,
        host_ram_gb=host,
        offload=args.offload,
        force=args.force_one_shot,
        split_t2va=args.split_t2va_prompt,
        split_ref2va=args.split_ref2va_prompt,
        split_image=args.split_image,
    )


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        plan = build_from_args(args)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    print(plan.report(), flush=True)
    if args.dry_run:
        return 0 if not plan.blocked else 2
    if plan.blocked:
        raise SystemExit(plan.blocked)
    # Optional CUDA stack. Dry-run and unit tests do not import it.
    from h3_runner.generate import run_plan

    return run_plan(plan)
