"""One span of a live-remake plan, as a ComfyUI API prompt.

This module builds the official MiniMax H3 Ref2VA graph and the ffmpeg command
that puts the source audio on the trimmed span. It does not start ComfyUI and
it does not post a prompt unless ``post_prompt`` is called.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Mapping, Sequence

try:
    from h3.live_remake import FPS, MODEL_FILE, RemakeError
except ImportError:
    from live_remake import FPS, MODEL_FILE, RemakeError

NOTEBOOK_A_VIDEO_VAE = "minimax_h3_video_vae_fp16.safetensors"
INT8_VIDEO_VAE = "minimax_h3_video_vae_int8_convrot.safetensors"


def select_span(plan: Mapping[str, Any], index: int) -> dict[str, Any]:
    """The one span to queue. Empty motion text and the 4-step LoRA stay out."""
    if plan.get("lightning") or plan.get("loras"):
        raise RemakeError("この投入は 4step LoRA なし")
    if int(plan.get("model", {}).get("steps") or 0) != 20:
        raise RemakeError("steps は 20")
    if plan.get("status") != "ready":
        raise RemakeError("計画が ready ではない")
    found = [item for item in plan.get("spans") or [] if int(item.get("index") or 0) == int(index)]
    if len(found) != 1:
        raise RemakeError(f"範囲 {index} が無い")
    span = found[0]
    if not str(span.get("prompt") or "").strip():
        raise RemakeError(f"範囲 {index} の文が空")
    if not span.get("pictures"):
        raise RemakeError(f"範囲 {index} の静止画が無い")
    if int(span.get("length") or 0) < 124:
        raise RemakeError(f"範囲 {index} の length が足りない")
    return dict(span)


def output_paths(out_dir: str | Path, index: int) -> tuple[Path, Path]:
    """Destination paths. An existing file is left where it is."""
    folder = Path(out_dir)
    video = folder / f"span-{int(index):02d}.mp4"
    with_audio = folder / f"span-{int(index):02d}_with-audio.mp4"
    existing = [item for item in (video, with_audio) if item.exists()]
    if existing:
        names = ", ".join(str(item) for item in existing)
        raise RemakeError(f"既にあるので上書きしない: {names}")
    return video, with_audio


def video_vae_name(plan: Mapping[str, Any], present: Sequence[str]) -> str:
    """Official int8 VAE when it is on disk, otherwise the fp16 file notebook A downloads."""
    wanted = str((plan.get("model") or {}).get("video_vae") or INT8_VIDEO_VAE)
    have = set(present)
    if wanted in have:
        return wanted
    if NOTEBOOK_A_VIDEO_VAE in have:
        return NOTEBOOK_A_VIDEO_VAE
    return wanted


def build_ref2va_prompt(
    plan: Mapping[str, Any],
    span: Mapping[str, Any],
    *,
    image_files: Sequence[str],
    video_file: str,
    video_vae: str,
    seed: int = 1,
) -> dict[str, dict[str, Any]]:
    """API prompt for MiniMaxH3ReferenceToVideo. No lightning LoRA node."""
    pictures = list(span.get("pictures") or [])
    if len(image_files) != len(pictures):
        raise RemakeError("静止画の数とファイルの数が違う")
    if len(pictures) > 9:
        raise RemakeError("静止画は 9 枚まで")
    model = plan["model"]
    width = int(plan["width"])
    height = int(plan["height"])
    length = int(span["length"])
    prompt_text = str(span["prompt"])
    nodes: dict[str, dict[str, Any]] = {
        "1": {
            "class_type": "CLIPLoader",
            "inputs": {"clip_name": model["clip"], "type": model["clip_type"], "device": "default"},
        },
        "2": {"class_type": "VAELoader", "inputs": {"vae_name": video_vae}},
        "3": {"class_type": "VAELoader", "inputs": {"vae_name": model["audio_vae"]}},
        "4": {
            "class_type": "UNETLoader",
            "inputs": {"unet_name": model.get("file") or MODEL_FILE, "weight_dtype": "default"},
        },
        "5": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": model["sampler"]}},
        "6": {
            "class_type": "BasicScheduler",
            "inputs": {
                "model": ["4", 0],
                "scheduler": model["scheduler"],
                "steps": int(model["steps"]),
                "denoise": float(model["denoise"]),
            },
        },
        "7": {"class_type": "RandomNoise", "inputs": {"noise_seed": int(seed)}},
        "8": {
            "class_type": "MiniMaxH3ReferenceToVideo",
            "inputs": {
                "clip": ["1", 0],
                "vae": ["2", 0],
                "audio_vae": ["3", 0],
                "prompt": prompt_text,
                "width": width,
                "height": height,
                "length": length,
                "ref_image_size": model["ref_image_size"],
                "ref_videos.ref_video_0": ["13", 0],
            },
        },
        "12": {"class_type": "LoadVideo", "inputs": {"file": video_file}},
        "13": {"class_type": "GetVideoComponents", "inputs": {"video": ["12", 0]}},
        "14": {
            "class_type": "BasicGuider",
            "inputs": {"model": ["4", 0], "conditioning": ["8", 0]},
        },
        "15": {
            "class_type": "SamplerCustomAdvanced",
            "inputs": {
                "noise": ["7", 0],
                "guider": ["14", 0],
                "sampler": ["5", 0],
                "sigmas": ["6", 0],
                "latent_image": ["8", 1],
            },
        },
        "16": {"class_type": "VAEDecode", "inputs": {"samples": ["15", 0], "vae": ["2", 0]}},
        "17": {"class_type": "VAEDecodeAudio", "inputs": {"samples": ["15", 0], "vae": ["3", 0]}},
        "18": {
            "class_type": "CreateVideo",
            "inputs": {"images": ["16", 0], "fps": float(plan["fps"]), "audio": ["17", 0]},
        },
        "19": {
            "class_type": "SaveVideo",
            "inputs": {
                "video": ["18", 0],
                "filename_prefix": f"video/span-{int(span['index']):02d}",
                "format": "mp4",
                "codec": "auto",
            },
        },
    }
    for number, name in enumerate(image_files):
        node_id = str(20 + number)
        nodes[node_id] = {"class_type": "LoadImage", "inputs": {"image": name}}
        nodes["8"]["inputs"][f"ref_images.ref_image_{number}"] = [node_id, 0]
    if any(item["class_type"] == "LoraLoaderModelOnly" for item in nodes.values()):
        raise RemakeError("LoRA ノードが混ざった")
    return nodes


def mux_source_audio_argv(video: str, source: str, start_s: float, frames: int, out: str) -> list[str]:
    """Trim the generated span to its measured frames and lay the source audio under it."""
    duration = frames / FPS
    return [
        "ffmpeg",
        "-y",
        "-i",
        video,
        "-ss",
        f"{start_s:.3f}",
        "-t",
        f"{duration:.3f}",
        "-i",
        source,
        "-filter_complex",
        f"[0:v]trim=end_frame={int(frames)},setpts=PTS-STARTPTS[v]",
        "-map",
        "[v]",
        "-map",
        "1:a:0",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-shortest",
        out,
    ]


def history_video(history_item: Mapping[str, Any]) -> str | None:
    """Filename of the first mp4 recorded on a Comfy history item."""
    for node in (history_item.get("outputs") or {}).values():
        if not isinstance(node, Mapping):
            continue
        for value in node.values():
            if not isinstance(value, list):
                continue
            for item in value:
                if isinstance(item, Mapping) and str(item.get("filename") or "").endswith(".mp4"):
                    return str(item["filename"])
    return None


def finished_history(body: Mapping[str, Any], prompt_id: str) -> dict[str, Any] | None:
    """The history item once Comfy marks it complete. An error stops the wait."""
    item = body.get(prompt_id)
    if not isinstance(item, Mapping):
        return None
    status = item.get("status") or {}
    if status.get("status_str") == "error":
        raise RemakeError(f"Comfy が失敗した: {status}")
    if status.get("completed"):
        return dict(item)
    return None


def post_prompt(base_url: str, prompt: Mapping[str, Any], opener: Any = urllib.request.urlopen) -> str:
    """POST /prompt and return the prompt id. Does nothing until called."""
    payload = json.dumps({"prompt": prompt}).encode("utf-8")
    request = urllib.request.Request(
        base_url.rstrip("/") + "/prompt",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    try:
        with opener(request, timeout=120) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:2000]
        raise RemakeError(f"Comfy が投入を受けなかった: {detail}") from exc
    if body.get("node_errors"):
        raise RemakeError(f"Comfy がノードを拒否した: {body['node_errors']}")
    prompt_id = body.get("prompt_id")
    if not prompt_id:
        raise RemakeError("Comfy が prompt_id を返さなかった")
    return str(prompt_id)
