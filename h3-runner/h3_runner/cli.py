"""One entry for T2VA (no image) and Ref2VA (one still, no reference video)."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

from h3_runner.official import DEFAULT_STEPS, README_MAX_DURATION_S, README_MIN_DURATION_S
from h3_runner.planner import orbis01_plan, single_plan
from h3_runner.weights import disk_preview, model_dir_name, prepare_all

# diffusers and torch are imported inside the generate step. A dry run only
# prints the official request plan and must not require a CUDA install.


def package_root() -> Path:
    return Path(__file__).resolve().parents[1]


def resolve_vram_gb(torch_gb: float | None, smi_gb: float | None) -> float | None:
    """Ignore a near-zero torch reading. That probe failure used to look like a tiny GPU."""
    if torch_gb is not None and torch_gb >= 1.0:
        return float(torch_gb)
    if smi_gb is not None and smi_gb >= 1.0:
        return float(smi_gb)
    return None


def _torch_vram_gb() -> tuple[float | None, str | None]:
    try:
        import torch
    except ImportError:
        return None, None
    try:
        if not torch.cuda.is_available():
            return None, None
        torch.cuda.init()
        props = torch.cuda.get_device_properties(0)
        raw = getattr(props, "total_memory", None)
        if raw is None:
            raw = getattr(props, "total_mem", None)
        if raw is None:
            return None, "total_memory が無い"
        return float(raw) / 1024**3, None
    except Exception as exc:
        return None, str(exc)


def _smi_vram_gb() -> float | None:
    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=memory.total", "--format=csv,noheader,nounits"],
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=15,
        )
    except (OSError, subprocess.SubprocessError, ValueError):
        return None
    line = out.strip().splitlines()
    if not line or not line[0].strip():
        return None
    # nvidia-smi reports MiB.
    return float(line[0].split()[0]) / 1024


def detect_vram_gb() -> float | None:
    # torch is optional so a dry run on a machine without it still prints the plan.
    torch_gb, torch_err = _torch_vram_gb()
    smi_gb = _smi_vram_gb()
    if torch_err:
        print(f"torch の VRAM 検出に失敗: {torch_err}", file=sys.stderr, flush=True)
    chosen = resolve_vram_gb(torch_gb, smi_gb)
    if torch_gb is not None and torch_gb < 1.0 and chosen is not None:
        print(
            f"torch の VRAM {torch_gb:.3f} GB は検出失敗とみなす。nvidia-smi の {chosen:.1f} GB を使う。",
            flush=True,
        )
    return chosen


def detect_host_ram_gb() -> float:
    meminfo = Path("/proc/meminfo").read_text(encoding="utf-8")
    for line in meminfo.splitlines():
        if line.startswith("MemTotal:"):
            return int(line.split()[1]) / 1024**2
    raise RuntimeError("/proc/meminfo に MemTotal が無い")


def default_cache_root() -> Path:
    raw = os.environ.get("H3_HF_CACHE")
    if raw:
        return Path(raw)
    drive = Path("/content/drive/MyDrive/h3-weights")
    if drive.parent.is_dir():
        return drive
    return Path("hf-cache")


def model_dir(cache_root: Path) -> Path:
    return cache_root / model_dir_name()


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
    parser.add_argument(
        "--cache-dir",
        type=Path,
        help="weight root. Colab uses /content/drive/MyDrive/h3-weights",
    )
    parser.add_argument(
        "--prepare-weights",
        action="store_true",
        help="CPU-only. Download missing folders into --cache-dir and exit.",
    )
    parser.add_argument("--split-t2va-prompt", type=Path)
    parser.add_argument("--split-ref2va-prompt", type=Path)
    parser.add_argument("--split-image", type=Path)
    return parser.parse_args(argv)


def _resources(args: argparse.Namespace) -> tuple[float, float]:
    if args.vram_gb is not None:
        vram = float(args.vram_gb)
    else:
        vram_detected = detect_vram_gb()
        if vram_detected is None:
            print(
                "VRAM を検出できなかった。80 として計画する。ノートの実測を --vram-gb で渡すこと。",
                file=sys.stderr,
                flush=True,
            )
            vram = 80.0
        else:
            vram = vram_detected
            print(f"検出 VRAM: {vram:.1f} GB", flush=True)
    if args.host_ram_gb is not None:
        host = args.host_ram_gb
    else:
        host = detect_host_ram_gb()
        print(f"検出 ホストRAM: {host:.1f} GB", flush=True)
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
    try:
        args = parse_args(argv)
    except SystemExit as exc:
        # argparse uses exit code 2. Say so on stderr; Colab hides a child's fd otherwise.
        code = exc.code if isinstance(exc.code, int) else 2
        if code not in (0, None):
            print(f"引数エラー。終了コード {code}。", file=sys.stderr, flush=True)
        raise
    try:
        plan = build_from_args(args)
    except ValueError as exc:
        print(str(exc), file=sys.stderr, flush=True)
        raise SystemExit(str(exc)) from exc
    print(plan.report(), flush=True)
    cache = model_dir(args.cache_dir or default_cache_root())
    tasks = [job.task for job in plan.jobs]
    preview = disk_preview(cache, tasks)
    print(preview.text, flush=True)
    if not preview.ok:
        print(preview.text, file=sys.stderr, flush=True)
        raise SystemExit(preview.text)
    if args.dry_run:
        return 0
    if args.prepare_weights:
        prepare_all(cache, tasks)
        return 0
    if plan.blocked:
        print(plan.blocked, file=sys.stderr, flush=True)
        raise SystemExit(plan.blocked)
    # Optional CUDA stack. Dry-run and weight prep do not import it.
    # run_plan reads the snapshot and does not download.
    from h3_runner.generate import run_plan

    return run_plan(plan, cache)
