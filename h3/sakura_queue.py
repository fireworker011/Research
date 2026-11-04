"""ComfyUI prompt for the Sakura sword clip.

Builds the Ref2VA graph with the two combat LoRAs and the ffmpeg command that
pads the measured video onto the H3 frame grid. It does not start ComfyUI and
it does not post unless the caller uses ``post_prompt``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence

from h3.live_remake import (
    AUDIO_VAE,
    CLIP_FILE,
    CLIP_TYPE,
    DENOISE,
    MODEL_FILE,
    REF_IMAGE_SIZE,
    SAMPLER,
    SCHEDULER,
    STEPS,
    RemakeError,
    conform_argv,
)
from h3.sakura_clip import SOURCE_FRAMES

VIDEO_NAME = "sakura-sword.mp4"
AUDIO_NAME = "sakura-sword_with-audio.mp4"


def output_paths(out_dir: str | Path) -> tuple[Path, Path]:
    """Destination paths. An existing file is left where it is."""
    folder = Path(out_dir)
    video = folder / VIDEO_NAME
    with_audio = folder / AUDIO_NAME
    existing = [item for item in (video, with_audio) if item.exists()]
    if existing:
        names = ", ".join(str(item) for item in existing)
        raise RemakeError(f"既にあるので上書きしない: {names}")
    return video, with_audio


def missing_paths(plan: Mapping[str, Any]) -> list[str]:
    """Stills, the source video, and the two LoRA files that are not on disk."""
    paths = [str(item["path"]) for item in plan["pictures"]]
    paths.append(str(plan["video"]))
    paths.extend(str(Path(plan["lora_dir"]) / str(row["file"])) for row in plan["loras"])
    return [item for item in paths if not Path(item).is_file()]


def reference_argv(plan: Mapping[str, Any], out: str) -> list[str]:
    """The measured clip, scaled to the canvas and padded to the H3 frame count."""
    return conform_argv(
        str(plan["video"]),
        0,
        int(plan["source_frames"]),
        int(plan["request_frames"]),
        (int(plan["width"]), int(plan["height"])),
        out,
    )


def build_sakura_prompt(
    plan: Mapping[str, Any],
    *,
    image_files: Sequence[str],
    video_file: str,
    video_vae: str,
    seed: int = 1,
) -> dict[str, dict[str, Any]]:
    """API prompt. Action LoRA then combat LoRA, then the 20-step sampler."""
    pictures = list(plan.get("pictures") or [])
    loras = list(plan.get("loras") or [])
    if len(image_files) != len(pictures):
        raise RemakeError("静止画の数とファイルの数が違う")
    if len(pictures) > 9:
        raise RemakeError("静止画は 9 枚まで")
    if [str(row["file"]) for row in loras] != [
        "Motion_Repair_V2.safetensors",
        "H3_Combat_V2.safetensors",
    ]:
        raise RemakeError("LoRA は Motion Repair の次に Combat")
    if int(plan.get("source_frames") or 0) != SOURCE_FRAMES:
        raise RemakeError("尺は計測したコマ数")
    model_ref: list[object] = ["4", 0]
    nodes: dict[str, dict[str, Any]] = {
        "1": {
            "class_type": "CLIPLoader",
            "inputs": {"clip_name": CLIP_FILE, "type": CLIP_TYPE, "device": "default"},
        },
        "2": {"class_type": "VAELoader", "inputs": {"vae_name": video_vae}},
        "3": {"class_type": "VAELoader", "inputs": {"vae_name": AUDIO_VAE}},
        "4": {
            "class_type": "UNETLoader",
            "inputs": {"unet_name": MODEL_FILE, "weight_dtype": "default"},
        },
        "5": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": SAMPLER}},
        "7": {"class_type": "RandomNoise", "inputs": {"noise_seed": int(seed)}},
        "8": {
            "class_type": "MiniMaxH3ReferenceToVideo",
            "inputs": {
                "clip": ["1", 0],
                "vae": ["2", 0],
                "audio_vae": ["3", 0],
                "prompt": str(plan["prompt"]),
                "width": int(plan["width"]),
                "height": int(plan["height"]),
                "length": int(plan["request_frames"]),
                "ref_image_size": REF_IMAGE_SIZE,
                "ref_videos.ref_video_0": ["13", 0],
            },
        },
        "12": {"class_type": "LoadVideo", "inputs": {"file": video_file}},
        "13": {"class_type": "GetVideoComponents", "inputs": {"video": ["12", 0]}},
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
                "filename_prefix": "video/sakura-sword",
                "format": "mp4",
                "codec": "auto",
            },
        },
    }
    for index, row in enumerate(loras):
        node_id = str(30 + index)
        nodes[node_id] = {
            "class_type": "LoraLoaderModelOnly",
            "inputs": {
                "model": model_ref,
                "lora_name": str(row["file"]),
                "strength_model": float(row["strength"]),
            },
        }
        model_ref = [node_id, 0]
    nodes["6"] = {
        "class_type": "BasicScheduler",
        "inputs": {
            "model": model_ref,
            "scheduler": SCHEDULER,
            "steps": STEPS,
            "denoise": DENOISE,
        },
    }
    nodes["14"] = {
        "class_type": "BasicGuider",
        "inputs": {"model": model_ref, "conditioning": ["8", 0]},
    }
    nodes["15"] = {
        "class_type": "SamplerCustomAdvanced",
        "inputs": {
            "noise": ["7", 0],
            "guider": ["14", 0],
            "sampler": ["5", 0],
            "sigmas": ["6", 0],
            "latent_image": ["8", 1],
        },
    }
    for number, name in enumerate(image_files):
        node_id = str(20 + number)
        nodes[node_id] = {"class_type": "LoadImage", "inputs": {"image": name}}
        nodes["8"]["inputs"][f"ref_images.ref_image_{number}"] = [node_id, 0]
    return nodes
