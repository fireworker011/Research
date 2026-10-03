"""LoRA files for the fast FL2VA path. Header checks do not load tensor bytes.

The pinned diffusers commit converts ComfyUI keys. A LoRA trained on the pruned
checkpoint has an AdaLN input width of 8. The released BF16 AdaLN projection is
2688 wide, so that file is refused before ``load_lora_weights``.
"""

from __future__ import annotations

import json
import os
import re
import shutil
from dataclasses import dataclass
from pathlib import Path

from h3_runner.weights import staging_dir

# Hugging Face tree listing for lightx2v/Minimax-h3-Turbo.
TURBO_REPO = "lightx2v/Minimax-h3-Turbo"
TURBO_FILENAME = "minimax_h3_fl2v_turbo_8step_v1.0_768p_comfyui_bf16.safetensors"

# Same file the studio registers. Civitai 3246572 under combat_base_v2.safetensors is not a second LoRA.
COMBAT_REPO = "JOKER141/MiniMax-H3-Combat-Base-V2"
COMBAT_FILENAME = "H3_Combat_V2.safetensors"

# JOKER141/MiniMax-H3-General-Motion-Continuity-Repair listing (2026-09-28).
# Motion_Repair.safetensors is V1. The card's BUNNY Motion Repair V2 is this file.
REPAIR_REPO = "JOKER141/MiniMax-H3-General-Motion-Continuity-Repair"
REPAIR_FILENAME = "Motion_Repair_V2.safetensors"

# Header of Motion_Repair_V2.safetensors (416 tensors, no AdaLN keys):
# diffusion_model.blocks.{i}.attn.qkv_proj|attn.out_proj|mlp.fc1|mlp.fc2 .lora_{A,B}.weight
# __metadata__.software is ai-toolkit. Not ComfyUI (no .alpha, no lora_down).
# diffusers 5ff8e59 lora_state_dict sees the diffusion_model. prefix and calls
# _convert_non_diffusers_minimax_h3_lora_to_diffusers. The file is not rewritten.

PRUNED_ADALN_IN = 8
# Released MiniMax-H3 AdaLN projection input. Documented by diffusers PR 14408.
RELEASE_ADALN_IN = 2688
_HEADER_CAP = 32_000_000


@dataclass(frozen=True)
class LoraSpec:
    path: Path
    scale: float
    name: str


def split_lora_arg(raw: str) -> tuple[Path, float]:
    """``path:strength``. The strength is the last colon, so the path may contain one."""
    text = (raw or "").strip()
    if ":" not in text:
        raise ValueError(f"--lora は パス:強さ の形で渡す: {raw!r}")
    path_s, scale_s = text.rsplit(":", 1)
    if not path_s:
        raise ValueError(f"--lora のパスが空: {raw!r}")
    try:
        scale = float(scale_s)
    except ValueError as exc:
        raise ValueError(f"--lora の強さが数ではない: {raw!r}") from exc
    if scale < 0:
        raise ValueError(f"--lora の強さは 0 以上: {raw!r}")
    return Path(path_s), scale


def adapter_name(path: Path, used: set[str]) -> str:
    raw = re.sub(r"[^0-9A-Za-z_]+", "_", path.stem).strip("_") or "lora"
    if raw[0].isdigit():
        raw = "lora_" + raw
    name = raw
    index = 2
    while name in used:
        name = f"{raw}_{index}"
        index += 1
    used.add(name)
    return name


def parse_lora_args(raws: list[str] | None) -> list[LoraSpec]:
    specs: list[LoraSpec] = []
    used: set[str] = set()
    for raw in raws or []:
        path, scale = split_lora_arg(raw)
        specs.append(LoraSpec(path=path, scale=scale, name=adapter_name(path, used)))
    return specs


def read_safetensors_header(path: Path) -> dict:
    """JSON header only. Tensor bytes stay on disk."""
    with path.open("rb") as handle:
        raw_len = handle.read(8)
        if len(raw_len) != 8:
            raise ValueError(f"safetensors のヘッダ長が読めない: {path}")
        header_len = int.from_bytes(raw_len, "little")
        if header_len <= 0 or header_len > _HEADER_CAP:
            raise ValueError(f"safetensors のヘッダ長が範囲外 ({header_len}): {path}")
        raw = handle.read(header_len)
    if len(raw) != header_len:
        raise ValueError(f"safetensors のヘッダが途中で切れている: {path}")
    try:
        header = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"safetensors のヘッダが JSON ではない: {path}") from exc
    if not isinstance(header, dict):
        raise ValueError(f"safetensors のヘッダがオブジェクトではない: {path}")
    return header


def adaln_input_width(name: str, shape: list[int] | tuple[int, ...]) -> int | None:
    """Input width of an AdaLN down-projection, or None when the key is not one.

    ``lora_A`` / ``lora_down`` is ``[rank, in_features]``. A full linear weight is
    ``[out, in]``. ``lora_B`` does not carry the input width.
    """
    low = name.lower()
    if "adaln" not in low:
        return None
    if len(shape) < 2:
        return None
    if "lora_b" in low or "lora_up" in low:
        return None
    if "lora_a" in low or "lora_down" in low or low.endswith(".weight"):
        return int(shape[-1])
    return None


_NATIVE_PREFIXES = (
    "diffusion_model.",
    "blocks.",
    "token_refiner.",
    "final_layer.",
    "lora_unet_",
    "video_patch_proj",
    "audio_patch_proj",
    "condition_proj",
    "time_embedder.",
)


def classify_lora_header(header: dict) -> str:
    """``native`` when diffusers converts the keys, ``diffusers`` when they already match.

    ``native`` covers ai-toolkit (``diffusion_model.`` + ``lora_A``/``lora_B``) and ComfyUI
    (the same prefix, often with ``.alpha`` or ``lora_down``). Both go through
    ``MiniMaxH3LoraLoaderMixin.lora_state_dict`` at ``load_lora_weights``. This runner
    does not write a second file.
    """
    keys = [key for key in header if key != "__metadata__"]
    if not keys:
        raise ValueError("LoRA のテンソルが無い")
    if any(key.startswith(("transformer.", "transformer_ref.")) for key in keys):
        return "diffusers"
    if any(key.startswith(_NATIVE_PREFIXES) for key in keys):
        return "native"
    if any(".default.weight" in key for key in keys):
        return "diffusers"
    sample = ", ".join(keys[:3])
    raise ValueError(
        "LoRA のキーが diffusers の load_lora_weights が変換する形ではない。"
        f"diffusion_model. / blocks. / lora_unet_ / transformer. のどれでもない。例: {sample}"
    )


def inspect_lora_file(path: Path) -> str:
    """Refuse pruned AdaLN, then say whether ``load_lora_weights`` converts the keys."""
    path = Path(path)
    reject_pruned_adaln(path)
    header = read_safetensors_header(path)
    layout = classify_lora_header(header)
    meta = header.get("__metadata__")
    software = ""
    if isinstance(meta, dict):
        software = str(meta.get("software") or meta.get("target_format") or "")
    keys = [key for key in header if key != "__metadata__"]
    kind = "ai-toolkit / ComfyUI などの非 diffusers"
    if layout == "diffusers":
        kind = "diffusers"
    elif any(key.endswith(".lora_down.weight") or key.endswith(".alpha") for key in keys):
        kind = "ComfyUI（lora_down または .alpha）"
    elif software and "ai-toolkit" in software:
        kind = "ai-toolkit（diffusion_model. + lora_A/lora_B）"
    note = (
        "diffusers の load_lora_weights がキーを変換する。ファイルは書き換えない。"
        if layout == "native"
        else "load_lora_weights がそのまま読める。変換ファイルは作らない。"
    )
    extra = f" metadata={software[:80]}" if software else ""
    print(f"LoRA {path.name}: {kind}。キー {len(keys)}。{note}{extra}", flush=True)
    return layout


def reject_pruned_adaln(path: Path) -> None:
    """Refuse a LoRA whose AdaLN input width is 8 (pruned training)."""
    path = Path(path)
    if not path.is_file():
        raise ValueError(f"LoRA が無い: {path}")
    if path.suffix != ".safetensors":
        raise ValueError(f"LoRA は safetensors だけ読む: {path}")
    header = read_safetensors_header(path)
    for name, meta in header.items():
        if name == "__metadata__" or not isinstance(meta, dict):
            continue
        shape = meta.get("shape")
        if not isinstance(shape, list):
            continue
        width = adaln_input_width(name, shape)
        if width == PRUNED_ADALN_IN:
            raise ValueError(
                f"LoRA {path.name} は AdaLN の入力幅が {PRUNED_ADALN_IN} で、Pruned 学習の重みです。"
                f"このランナーのベースは公開 BF16（AdaLN 入力 {RELEASE_ADALN_IN}）なので読みません。"
                f"該当キー: {name} shape={shape}"
            )


def _already(path: Path) -> bool:
    return path.is_file() and path.stat().st_size > 0


def _publish(src: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    partial = dest.with_name(dest.name + ".partial")
    if partial.exists():
        partial.unlink()
    shutil.copyfile(src, partial)
    os.replace(partial, dest)


def _download_hf(repo: str, filename: str, dest: Path, hub_download) -> None:
    if _already(dest):
        print(f"飛ばす: {dest.name} は既にある ({dest.stat().st_size} bytes)", flush=True)
        return
    staging = staging_dir() / "loras"
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True, exist_ok=True)
    print(f"落とす: {repo}/{filename} → {dest}", flush=True)
    got = Path(hub_download(repo, filename, local_dir=str(staging)))
    _publish(got, dest)
    shutil.rmtree(staging, ignore_errors=True)
    print(f"書いた: {dest} ({dest.stat().st_size} bytes)", flush=True)


def prepare_fast_loras(
    dest_dir: Path,
    *,
    hub_download=None,
) -> list[Path]:
    """Put Turbo, Repair, and Combat under ``dest_dir``. Skip files already there.

    All three come from Hugging Face. Combat is ``H3_Combat_V2.safetensors``.
    The Civitai name ``combat_base_v2.safetensors`` is not downloaded.
    """
    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    if hub_download is None:
        # Deferred so header checks and dry runs do not import huggingface_hub.
        from huggingface_hub import hf_hub_download

        hub_download = hf_hub_download
    written: list[Path] = []
    turbo = dest_dir / TURBO_FILENAME
    _download_hf(TURBO_REPO, TURBO_FILENAME, turbo, hub_download)
    written.append(turbo)
    repair = dest_dir / REPAIR_FILENAME
    _download_hf(REPAIR_REPO, REPAIR_FILENAME, repair, hub_download)
    written.append(repair)
    combat = dest_dir / COMBAT_FILENAME
    _download_hf(COMBAT_REPO, COMBAT_FILENAME, combat, hub_download)
    written.append(combat)
    for path in written:
        inspect_lora_file(path)
    print(
        "LoRA 準備完了: "
        + ", ".join(f"{path.name}={path.stat().st_size}" for path in written),
        flush=True,
    )
    return written
