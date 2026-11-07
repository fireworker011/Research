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
    FPS,
    MODEL_FILE,
    REF_IMAGE_SIZE,
    SAMPLER,
    SCHEDULER,
    STEPS,
    RemakeError,
    align_frames,
    canvas_for,
    conform_argv,
)
from h3.sakura_clip import SOURCE_FRAMES, SOURCE_HEIGHT, SOURCE_WIDTH, scaled_marks

VIDEO_NAME = "sakura-sword.mp4"
AUDIO_NAME = "sakura-sword_with-audio.mp4"
FL2VA_UNET = "minimax_h3_fl2va_pruned_int8_convrot.safetensors"
TURBO_FILE = "minimax_h3_fl2v_turbo_8step_v1.0_768p_comfyui_bf16.safetensors"
TURBO_STRENGTH = 1.0
TURBO_STEPS = 8
# 244 frames is the measured source. H3 accepts 17k+5, so the next legal length is 260.
FL2VA_FRAMES = align_frames(SOURCE_FRAMES)
# Source is 1280x714. H3's wide canvas is 1344x768, the 16:9 768P size.
FL2VA_WIDTH, FL2VA_HEIGHT = canvas_for(SOURCE_WIDTH, SOURCE_HEIGHT)
FL2VA_FIRST = "sakura-16x9-open.jpg"
FL2VA_LAST = "sakura-16x9-yokai-end.jpg"
FL2VA_FAST = "速い 8step"
FL2VA_QUALITY = "きれい 20step"
FL2VA_STEM = "sakura-fl2va-fly8"
FL2VA_NAME = f"{FL2VA_STEM}.mp4"
STILL_DIR = "/content/drive/MyDrive/動画倉庫/ネタBOX"
MODELS_DIR = "/content/drive/MyDrive/minimax-h3-comfyui/models"


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


def fl2va_prompt() -> str:
    """The measured sword beats, aimed at the yokai, ending on the last frame."""
    marks = scaled_marks()
    end = FL2VA_FRAMES / FPS
    shots = (
        (
            marks[0],
            marks[1],
            "Extreme low angle on the stone path. Within the first moment she bursts from a still stance into a fast dash. "
            "The path cracks under her feet and debris kicks outward. Her hair and the red and gold kimono stream backward. "
            "She draws the tachi. The camera closes on the blade and a crimson edge lights the steel. "
            "Ahead of her is the giant horned yokai from the last frame, taller than the temple gate.",
        ),
        (
            marks[1],
            marks[2],
            "The camera tracks. Close strikes pass her with no pause, then the pace doubles. She stays low and leaves afterimages. "
            "Three tachi cuts hit the yokai: a horizontal slash, an upward thrust, and a spinning cut. "
            "The blade weaves a net of red light and throws sparks.",
        ),
        (
            marks[2],
            marks[3],
            "Wide low angle. She leaves the ground in one motion and stays in the air. "
            "The tachi cuts a scarlet arc and releases a cone of red sword light downward onto the yokai. "
            "The impact hits. The camera shakes. The weapon remains the tachi.",
        ),
        (
            marks[3],
            marks[4],
            "The camera circles her once while she is airborne, then comes close. "
            "She turns, changes direction in the air, and thrusts at the yokai. "
            "Red sword-light afterimages cross the temple garden. She does not land.",
        ),
        (
            marks[4],
            marks[5],
            "She is still in the air. A vertical fall starts. She blocks a heavy strike from the yokai and answers with one tachi thrust. "
            "She breaks through the blow and keeps the tachi raised.",
        ),
        (
            marks[5],
            end,
            "The camera pulls wide and drops to the last frame: cherry trees on both sides, lanterns, and the giant white-maned horned yokai filling the courtyard. "
            "She comes down through that frame and cuts the yokai down with one full slash of the tachi. "
            "The yokai falls into the pose of the last frame. She finishes small in front of it, tachi raised into its body. "
            "The golden characters 祝千三百 stand in the sky as in the last frame.",
        ),
    )
    lines = [
        "Photorealistic live-action. The woman, the tachi, and the temple corridor are the first frame.",
        "The giant yokai and the final wide view are the last frame.",
        "She wears the red and gold floral kimono and flower hairpin from the first frame, and she holds a tachi.",
        "The place is that Japanese temple garden, wide 16:9.",
        "She is airborne from the wide low-angle takeoff through the vertical fall. She meets the ground only on the final slash.",
        "Timeline:",
    ]
    lines.extend(f"[{start:.3f}s-{stop:.3f}s] {text}" for start, stop, text in shots)
    lines.extend(
        [
            "The weapon is a tachi in every moment. The last moment matches the last frame, including the golden characters 祝千三百.",
            "No other subtitles, logos, or watermarks.",
            "Audio: steel draws and clashes, sword-light tearing air, and low impacts on stone. No music.",
        ]
    )
    return "\n".join(lines)


def fl2va_still_names() -> tuple[str, str]:
    return (FL2VA_FIRST, FL2VA_LAST)


def fl2va_choice(mode: str = FL2VA_FAST) -> dict[str, Any]:
    """Fast keeps the 8-step LoRA. Quality is the official 20 steps with that LoRA off."""
    table = {
        FL2VA_FAST: {
            "steps": TURBO_STEPS,
            "lora": TURBO_FILE,
            "strength": TURBO_STRENGTH,
            "stem": FL2VA_STEM,
            "name": FL2VA_NAME,
            "wait_minutes": 90,
        },
        FL2VA_QUALITY: {
            "steps": STEPS,
            "lora": None,
            "strength": 0.0,
            "stem": "sakura-fl2va-fly20",
            "name": "sakura-fl2va-fly20.mp4",
            "wait_minutes": 90 * STEPS // TURBO_STEPS,
        },
    }
    try:
        return table[mode]
    except KeyError as exc:
        raise RemakeError(f"画質の選択が違う: {mode}") from exc


def missing_fl2va(mode: str = FL2VA_FAST, still_dir: str | Path | None = None) -> list[str]:
    """Both stills, the FL2VA weight, and the 8-step LoRA when that mode is selected."""
    choice = fl2va_choice(mode)
    folder = Path(still_dir) if still_dir is not None else Path(STILL_DIR)
    paths = [
        folder / FL2VA_FIRST,
        folder / FL2VA_LAST,
        Path(MODELS_DIR) / "diffusion_models" / FL2VA_UNET,
    ]
    if choice["lora"]:
        paths.append(Path(MODELS_DIR) / "loras" / str(choice["lora"]))
    return [str(path) for path in paths if not path.is_file()]


def fl2va_output_path(out_dir: str | Path, mode: str = FL2VA_FAST) -> Path:
    """Destination for the selected mode. An existing file is left where it is."""
    video = Path(out_dir) / str(fl2va_choice(mode)["name"])
    if video.exists():
        raise RemakeError(f"既にあるので上書きしない: {video}")
    return video


def build_fl2va_prompt(
    *,
    first_file: str,
    last_file: str,
    video_vae: str,
    seed: int = 1,
    mode: str = FL2VA_FAST,
) -> dict[str, dict[str, Any]]:
    """The open still starts the clip. The yokai still is the last frame."""
    choice = fl2va_choice(mode)
    model_ref: list[object] = ["30", 0] if choice["lora"] else ["4", 0]
    nodes = {
        "1": {
            "class_type": "CLIPLoader",
            "inputs": {"clip_name": CLIP_FILE, "type": CLIP_TYPE, "device": "default"},
        },
        "2": {"class_type": "VAELoader", "inputs": {"vae_name": video_vae}},
        "3": {"class_type": "VAELoader", "inputs": {"vae_name": AUDIO_VAE}},
        "4": {
            "class_type": "UNETLoader",
            "inputs": {"unet_name": FL2VA_UNET, "weight_dtype": "default"},
        },
        "5": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": SAMPLER}},
        "6": {
            "class_type": "BasicScheduler",
            "inputs": {
                "model": model_ref,
                "scheduler": SCHEDULER,
                "steps": int(choice["steps"]),
                "denoise": DENOISE,
            },
        },
        "7": {"class_type": "RandomNoise", "inputs": {"noise_seed": int(seed)}},
        "8": {
            "class_type": "MiniMaxH3ImageToVideo",
            "inputs": {
                "clip": ["1", 0],
                "vae": ["2", 0],
                "first_frame": ["20", 0],
                "last_frame": ["21", 0],
                "prompt": fl2va_prompt(),
                "width": FL2VA_WIDTH,
                "height": FL2VA_HEIGHT,
                "length": FL2VA_FRAMES,
            },
        },
        "14": {
            "class_type": "BasicGuider",
            "inputs": {"model": model_ref, "conditioning": ["8", 0]},
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
            "inputs": {"images": ["16", 0], "fps": 24, "audio": ["17", 0]},
        },
        "19": {
            "class_type": "SaveVideo",
            "inputs": {
                "video": ["18", 0],
                "filename_prefix": f"video/{choice['stem']}",
                "format": "mp4",
                "codec": "auto",
            },
        },
        "20": {"class_type": "LoadImage", "inputs": {"image": first_file}},
        "21": {"class_type": "LoadImage", "inputs": {"image": last_file}},
    }
    if choice["lora"]:
        nodes["30"] = {
            "class_type": "LoraLoaderModelOnly",
            "inputs": {
                "model": ["4", 0],
                "lora_name": choice["lora"],
                "strength_model": choice["strength"],
            },
        }
    return nodes
