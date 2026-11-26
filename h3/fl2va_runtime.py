"""Local staging and timing for one FL2VA Colab run.

Copies only the files that cell uses onto the Colab disk, then points ComfyUI
at those copies. Other weights stay linked at Drive. This module does not
download and does not start ComfyUI.
"""

from __future__ import annotations

import re
import shutil
import time
from datetime import datetime
from pathlib import Path
from typing import Mapping

RESERVE_BYTES = 15 * 1024**3
HIGH_VRAM_BYTES = 75 * 1024**3

# Copy priority when the disk cannot hold every file and still leave the reserve.
STAGE_FILES = (
    "text_encoders/qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors",
    "vae/minimax_h3_video_vae_fp16.safetensors",
    "vae/minimax_h3_audio_vae_fp32.safetensors",
    "diffusion_models/minimax_h3_fl2va_pruned_int8_convrot.safetensors",
    "loras/minimax_h3_fl2v_turbo_8step_v1.0_768p_comfyui_bf16.safetensors",
)

_PROMPT_EXECUTED = re.compile(r"Prompt executed in ([0-9.]+) seconds")
_S_PER_IT = re.compile(r"([0-9.]+)s/it")
_NODE_SECONDS = re.compile(r"#\s*([A-Za-z0-9_]+)\s+([0-9.]+)s\b")
_SECONDS_NODE = re.compile(r"([0-9.]+)s\s*-\s*([A-Za-z0-9_]+)")
_STAMPED = re.compile(
    r"^(?P<ts>\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:[.,]\d{1,6})?)\b.*?(?P<msg>Requested to load .+)$"
)


def format_hardware(
    gpu_name: str,
    vram_bytes: int,
    ram_total: int,
    ram_available: int,
    disk_free: int,
) -> str:
    """One block of the measurements cell 5 and cell 5c print."""
    return "\n".join(
        [
            f"GPU: {gpu_name}",
            f"VRAM: {vram_bytes / 1024**3:.1f} GiB ({int(vram_bytes)} bytes)",
            f"RAM: 空き {ram_available / 1024**3:.1f} GiB / 総量 {ram_total / 1024**3:.1f} GiB",
            f"ディスク /content: 空き {disk_free / 1024**3:.1f} GiB",
        ]
    )


def vram_launch_arg(total_bytes: int, extra: str = "auto") -> str:
    """``auto`` uses --highvram only at 75 GiB and above. An explicit flag is kept."""
    choice = extra.strip()
    if choice not in ("", "auto"):
        return choice
    if choice == "":
        return ""
    if int(total_bytes) >= HIGH_VRAM_BYTES:
        return "--highvram"
    return ""


def select_local_files(
    sizes: Mapping[str, int],
    free_bytes: int,
    reserve: int = RESERVE_BYTES,
) -> list[str]:
    """Files that fit on disk while leaving ``reserve`` bytes free."""
    present = [name for name in STAGE_FILES if name in sizes]
    total = sum(int(sizes[name]) for name in present)
    if int(free_bytes) - int(reserve) >= total:
        return present
    chosen: list[str] = []
    used = 0
    for name in present:
        size = int(sizes[name])
        if int(free_bytes) - int(reserve) - used >= size:
            chosen.append(name)
            used += size
    return chosen


def _overlay(comfy_dir: Path, drive_dir: Path, local_names: Mapping[str, Path]) -> None:
    """Replace one Comfy model folder with per-file links. Drive files are not copied."""
    staging = comfy_dir.parent / f"{comfy_dir.name}.staging"
    if staging.exists() or staging.is_symlink():
        if staging.is_symlink():
            staging.unlink()
        else:
            shutil.rmtree(staging)
    staging.mkdir(parents=True)
    for item in sorted(drive_dir.iterdir(), key=lambda path: path.name):
        if not item.is_file():
            continue
        target = local_names.get(item.name, item)
        (staging / item.name).symlink_to(target)
    backup = comfy_dir.parent / f"{comfy_dir.name}.drivebak"
    if backup.exists() or backup.is_symlink():
        if backup.is_symlink():
            backup.unlink()
        else:
            shutil.rmtree(backup)
    if comfy_dir.exists() or comfy_dir.is_symlink():
        comfy_dir.rename(backup)
    staging.rename(comfy_dir)
    if backup.is_symlink() or backup.exists():
        if backup.is_symlink():
            backup.unlink()
        else:
            shutil.rmtree(backup)


def stage_fl2va_models(
    drive_models: Path,
    comfy_models: Path,
    local_root: Path,
    free_bytes: int,
    reserve: int = RESERVE_BYTES,
) -> dict[str, object]:
    """Copy the FL2VA files that fit, then point Comfy at the local copies."""
    root = Path(drive_models)
    sizes = {rel: (root / rel).stat().st_size for rel in STAGE_FILES if (root / rel).is_file()}
    chosen = select_local_files(sizes, free_bytes, reserve)
    local_root = Path(local_root)
    local_root.mkdir(parents=True, exist_ok=True)
    copied: list[dict[str, object]] = []
    local_by_folder: dict[str, dict[str, Path]] = {}
    started = time.perf_counter()
    for rel in chosen:
        src = root / rel
        dest = local_root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        tick = time.perf_counter()
        reused = dest.is_file() and dest.stat().st_size == src.stat().st_size
        if not reused:
            if dest.is_symlink():
                dest.unlink()
            shutil.copy2(src, dest)
        seconds = 0.0 if reused else time.perf_counter() - tick
        folder, name = rel.split("/", 1)
        local_by_folder.setdefault(folder, {})[name] = dest
        copied.append({"path": rel, "seconds": seconds, "reused": reused})
    for folder in ("diffusion_models", "text_encoders", "vae", "loras"):
        drive_dir = root / folder
        comfy_dir = Path(comfy_models) / folder
        if drive_dir.is_dir():
            comfy_dir.parent.mkdir(parents=True, exist_ok=True)
            _overlay(comfy_dir, drive_dir, local_by_folder.get(folder, {}))
    return {
        "copied": copied,
        "drive": [rel for rel in STAGE_FILES if rel in sizes and rel not in chosen],
        "seconds": time.perf_counter() - started,
    }


def format_stage_report(report: Mapping[str, object]) -> str:
    """The copy log for cell 5c."""
    lines = ["ローカルへコピー:"]
    copied = report.get("copied") or []
    if not copied:
        lines.append("- なし")
    for item in copied:
        mark = "既存を使う" if item["reused"] else f"{float(item['seconds']):.1f}秒"
        lines.append(f"- {item['path']} {mark}")
    lines.append("Driveのまま:")
    drive = report.get("drive") or []
    if not drive:
        lines.append("- なし")
    for name in drive:
        lines.append(f"- {name}")
    lines.append(f"コピー合計: {float(report.get('seconds') or 0):.1f}秒")
    return "\n".join(lines)


def _load_span(text: str, label: str) -> float | None:
    """Seconds from a timestamped load request until the next load request."""
    hits: list[tuple[float, str]] = []
    for line in text.splitlines():
        match = _STAMPED.match(line.strip())
        if match is None:
            continue
        raw = match.group("ts").replace(",", ".")
        try:
            stamp = datetime_seconds(raw)
        except ValueError:
            continue
        hits.append((stamp, match.group("msg")))
    for index, (stamp, msg) in enumerate(hits):
        if label not in msg:
            continue
        if index + 1 < len(hits):
            return max(0.0, hits[index + 1][0] - stamp)
    return None


def datetime_seconds(raw: str) -> float:
    """Parse a Comfy log timestamp into seconds from the epoch."""
    for pattern in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(raw, pattern).timestamp()
        except ValueError:
            continue
    raise ValueError(raw)


def parse_comfy_log(text: str) -> dict[str, float | None]:
    """Pull phase seconds out of one run's Comfy log. Missing lines stay None."""
    phases: dict[str, float | None] = {
        "text_encoder_s": None,
        "diffusion_s": None,
        "s_per_it": None,
        "video_vae_s": None,
        "audio_vae_s": None,
        "prompt_executed_s": None,
    }
    executed = _PROMPT_EXECUTED.findall(text)
    if executed:
        phases["prompt_executed_s"] = float(executed[-1])
    rates = _S_PER_IT.findall(text)
    if rates:
        phases["s_per_it"] = float(rates[-1])
    nodes: dict[str, float] = {}
    for match in _NODE_SECONDS.finditer(text):
        nodes[match.group(1)] = float(match.group(2))
    for match in _SECONDS_NODE.finditer(text):
        nodes[match.group(2)] = float(match.group(1))
    if "CLIPLoader" in nodes:
        phases["text_encoder_s"] = nodes["CLIPLoader"]
    else:
        phases["text_encoder_s"] = _load_span(text, "CLIP")
    diffusion = 0.0
    found = False
    for key in ("UNETLoader", "LoraLoaderModelOnly", "MiniMaxH3ImageToVideo", "SamplerCustomAdvanced"):
        if key in nodes:
            diffusion += nodes[key]
            found = True
    if found:
        phases["diffusion_s"] = diffusion
    if "VAEDecode" in nodes:
        phases["video_vae_s"] = nodes["VAEDecode"]
    if "VAEDecodeAudio" in nodes:
        phases["audio_vae_s"] = nodes["VAEDecodeAudio"]
    return phases


def format_phase_report(phases: Mapping[str, float | None], wall_s: float) -> str:
    """The five lines cell 5c prints after one clip."""

    def seconds(value: float | None) -> str:
        return "未計測" if value is None else f"{value:.1f}秒"

    rate = "未計測" if phases.get("s_per_it") is None else f"{float(phases['s_per_it']):.2f}s/it"
    if phases.get("diffusion_s") is None:
        diffusion = f"未計測, {rate}" if phases.get("s_per_it") is not None else "未計測"
    else:
        diffusion = f"{float(phases['diffusion_s']):.1f}秒, {rate}"
    lines = [
        "フェーズ実測:",
        f"1. テキストエンコーダ: {seconds(phases.get('text_encoder_s'))}",
        f"2. 拡散ループ: {diffusion}",
        f"3. 動画VAE: {seconds(phases.get('video_vae_s'))}",
        f"4. 音声VAE: {seconds(phases.get('audio_vae_s'))}",
        f"5. 投入から保存まで: {float(wall_s):.1f}秒",
    ]
    if phases.get("prompt_executed_s") is not None:
        lines.append(f"Comfy Prompt executed: {float(phases['prompt_executed_s']):.1f}秒")
    return "\n".join(lines)


def read_hardware() -> str:
    """Live GPU, RAM, and /content measurements. Used by the Colab cells.

    torch and psutil stay inside this function. The unit tests import this
    module without a GPU stack, and those packages are only present on Colab.
    """
    import psutil
    import torch

    props = torch.cuda.get_device_properties(0)
    ram = psutil.virtual_memory()
    disk = shutil.disk_usage("/content")
    return format_hardware(
        torch.cuda.get_device_name(0),
        int(props.total_memory),
        int(ram.total),
        int(ram.available),
        int(disk.free),
    )
