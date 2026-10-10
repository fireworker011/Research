"""Pose-locked character replacement for action footage.

MiniMax H3 R2V is NOT motion capture: it re-generates from a video hint.
Action (fights, swords, fast camera) needs per-frame pose + Mix replace.

This module builds a ComfyUI API graph for Wan 2.2 Animate:
  still image = identity + costume
  DWPose video = body/hand motion
  Mix mode = drop the new person into the original clip (camera/timing stay)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from h3_r2v_core import comfy_media_name, vhs_load_video_inputs

H3_NOT_MOCAP = (
    "MiniMax H3 R2V はモーションキャプチャではない。"
    "参照動画を見て再生成するだけなので、激しいアクションは手足・刀・カメラがずれる。"
    "完全模倣したい場合は Wan 2.2 Animate Mix（骨格ロック＋元映像へ置換）を使う。"
)

WAN_MODELS = {
    "unet": (
        "Wan2_2-Animate-14B_fp8_e4m3fn_scaled_KJ.safetensors",
        "https://huggingface.co/Kijai/WanVideo_comfy_fp8_scaled/resolve/main/Wan22Animate/Wan2_2-Animate-14B_fp8_e4m3fn_scaled_KJ.safetensors",
        "diffusion_models",
    ),
    "lora": (
        "lightx2v_I2V_14B_480p_cfg_step_distill_rank64_bf16.safetensors",
        "https://huggingface.co/Kijai/WanVideo_comfy/resolve/main/Lightx2v/lightx2v_I2V_14B_480p_cfg_step_distill_rank64_bf16.safetensors",
        "loras",
    ),
    "relight": (
        "WanAnimate_relight_lora_fp16.safetensors",
        "https://huggingface.co/Kijai/WanVideo_comfy/resolve/main/LoRAs/Wan22_relight/WanAnimate_relight_lora_fp16.safetensors",
        "loras",
    ),
    "clip": (
        "umt5_xxl_fp8_e4m3fn_scaled.safetensors",
        "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors",
        "text_encoders",
    ),
    "clip_vision": (
        "clip_vision_h.safetensors",
        "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/clip_vision/clip_vision_h.safetensors",
        "clip_vision",
    ),
    "vae": (
        "wan_2.1_vae.safetensors",
        "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors",
        "vae",
    ),
}

CUSTOM_NODES = {
    "comfyui_controlnet_aux": "https://github.com/Fannovel16/comfyui_controlnet_aux.git",
}


def wan_length(duration_s: float, fps: float = 16.0, chunk: int = 77) -> int:
    """Wan Animate length is 4k+1. Official Mix chunk is 77 (~4.8s @16fps)."""
    n = max(5, int(round(float(duration_s) * float(fps))))
    n = n + (1 - n % 4) % 4
    if n % 4 != 1:
        n += 1
    return min(int(n), int(chunk))


def chunk_count(duration_s: float, fps: float = 16.0, chunk: int = 77) -> int:
    total = max(1, int(round(float(duration_s) * float(fps))))
    return max(1, (total + chunk - 1) // chunk)


def assign_people_left_to_right(
    boxes: list[tuple[Any, float, float, float, float]],
) -> dict[Any, int]:
    """Map detector id → person index 0..n-1 by x-center (left = Image 1)."""
    ranked = sorted(boxes, key=lambda b: (b[1] + b[3]) / 2.0)
    return {b[0]: i for i, b in enumerate(ranked)}


def mix_pass_plan(img_names: list[str], video_name: str) -> list[dict[str, Any]]:
    """Two-person fight: replace left person, then right person, keeping camera."""
    jobs: list[dict[str, Any]] = []
    background = video_name
    for i, img in enumerate(img_names):
        out_prefix = f"video/h3_mix_pass{i + 1}"
        jobs.append(
            {
                "pass_index": i,
                "reference_image": img,
                "background_video": background,
                "person_index": i,
                "filename_prefix": out_prefix,
                "label": f"mix pass{i + 1}: {img} into {background}",
            }
        )
        background = out_prefix
    return jobs


def dwpose_inputs(*, body: bool, face: bool, hands: bool, resolution: int = 512) -> dict[str, Any]:
    on, off = "enable", "disable"
    return {
        "detect_hand": on if hands else off,
        "detect_body": on if body else off,
        "detect_face": on if face else off,
        "resolution": int(resolution),
        "bbox_detector": "yolox_l.onnx",
        "pose_estimator": "dw-ll_ucoco_384_bs5.torchscript.pt",
    }


def build_pose_preview_graph(
    *,
    video_name: str,
    filename_prefix: str = "video/pose_preview",
    length: int = 77,
    fps: float = 16.0,
    object_info: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """DWPose only. Inspect this before spending a Mix run on a fight clip."""
    g: dict[str, Any] = {}
    g["190"] = {
        "class_type": "VHS_LoadVideo",
        "inputs": vhs_load_video_inputs(object_info, video_name, length, motion_max_edge=None),
    }
    g["101"] = {
        "class_type": "DWPreprocessor",
        "inputs": {"image": ["190", 0], **dwpose_inputs(body=True, face=False, hands=True)},
    }
    g["29"] = {
        "class_type": "CreateVideo",
        "inputs": {"images": ["101", 0], "fps": float(fps)},
    }
    g["30"] = {
        "class_type": "SaveVideo",
        "inputs": {
            "video": ["29", 0],
            "filename_prefix": filename_prefix,
            "format": "auto",
            "codec": "auto",
        },
    }
    return g


def build_wan_animate_graph(
    *,
    image_name: str,
    video_name: str,
    prompt: str,
    negative: str = "text, watermark, logo, subtitles, blurry, extra limbs",
    mode: str = "mix",
    mask_name: str | None = None,
    unet: str = WAN_MODELS["unet"][0],
    lora_name: str | None = WAN_MODELS["lora"][0],
    relight_lora: str | None = WAN_MODELS["relight"][0],
    clip_name: str = WAN_MODELS["clip"][0],
    clip_vision_name: str = WAN_MODELS["clip_vision"][0],
    vae_name: str = WAN_MODELS["vae"][0],
    width: int = 640,
    height: int = 368,
    length: int = 77,
    fps: float = 16.0,
    seed: int = 42,
    steps: int = 4,
    cfg: float = 1.0,
    filename_prefix: str = "video/wan_animate_mix",
    object_info: dict[str, Any] | None = None,
    grow_mask: int = 28,
) -> dict[str, Any]:
    """One Mix/Move pass. Mix keeps the source camera; Move re-stages onto the still."""
    if width % 16 or height % 16:
        raise ValueError(f"Wan Animate width/height must be multiples of 16, got {width}x{height}")
    mode = (mode or "mix").lower()
    if mode not in ("mix", "move"):
        raise ValueError("mode must be mix or move")
    if mode == "mix" and not mask_name:
        raise ValueError("mix mode needs a per-person mask video (character_mask)")

    g: dict[str, Any] = {}
    g["10"] = {
        "class_type": "LoadImage",
        "inputs": {"image": comfy_media_name(image_name)},
    }
    g["190"] = {
        "class_type": "VHS_LoadVideo",
        "inputs": vhs_load_video_inputs(object_info, video_name, length, motion_max_edge=None),
    }
    g["101"] = {
        "class_type": "DWPreprocessor",
        "inputs": {"image": ["190", 0], **dwpose_inputs(body=True, face=False, hands=True)},
    }
    g["100"] = {
        "class_type": "DWPreprocessor",
        "inputs": {"image": ["190", 0], **dwpose_inputs(body=False, face=True, hands=False)},
    }
    g["14"] = {
        "class_type": "CLIPLoader",
        "inputs": {"clip_name": clip_name, "type": "wan", "device": "default"},
    }
    g["15"] = {
        "class_type": "CLIPTextEncode",
        "inputs": {"clip": ["14", 0], "text": prompt},
    }
    g["16"] = {
        "class_type": "CLIPTextEncode",
        "inputs": {"clip": ["14", 0], "text": negative},
    }
    g["17"] = {
        "class_type": "UNETLoader",
        "inputs": {"unet_name": unet, "weight_dtype": "default"},
    }
    model: list[Any] = ["17", 0]
    next_id = 18
    if lora_name:
        g[str(next_id)] = {
            "class_type": "LoraLoaderModelOnly",
            "inputs": {"model": model, "lora_name": lora_name, "strength_model": 1.0},
        }
        model = [str(next_id), 0]
        next_id += 1
    if mode == "mix" and relight_lora:
        g[str(next_id)] = {
            "class_type": "LoraLoaderModelOnly",
            "inputs": {"model": model, "lora_name": relight_lora, "strength_model": 1.0},
        }
        model = [str(next_id), 0]
        next_id += 1
    g["20"] = {
        "class_type": "ModelSamplingSD3",
        "inputs": {"model": model, "shift": 8.0},
    }
    g["21"] = {"class_type": "VAELoader", "inputs": {"vae_name": vae_name}}
    g["22"] = {
        "class_type": "CLIPVisionLoader",
        "inputs": {"clip_name": clip_vision_name},
    }
    g["23"] = {
        "class_type": "CLIPVisionEncode",
        "inputs": {"clip_vision": ["22", 0], "image": ["10", 0], "crop": "center"},
    }

    wan_in: dict[str, Any] = {
        "positive": ["15", 0],
        "negative": ["16", 0],
        "vae": ["21", 0],
        "clip_vision_output": ["23", 0],
        "reference_image": ["10", 0],
        "face_video": ["100", 0],
        "pose_video": ["101", 0],
        "width": int(width),
        "height": int(height),
        "length": int(length),
        "batch_size": 1,
        "continue_motion_max_frames": 5,
        "video_frame_offset": 0,
    }
    if mode == "mix":
        g["191"] = {
            "class_type": "VHS_LoadVideo",
            "inputs": vhs_load_video_inputs(object_info, mask_name, length, motion_max_edge=None),
        }
        g["24"] = {
            "class_type": "ImageToMask",
            "inputs": {"image": ["191", 0], "channel": "red"},
        }
        g["241"] = {
            "class_type": "GrowMask",
            "inputs": {"mask": ["24", 0], "expand": int(grow_mask), "tapered_corners": True},
        }
        wan_in["background_video"] = ["190", 0]
        wan_in["character_mask"] = ["241", 0]

    g["25"] = {"class_type": "WanAnimateToVideo", "inputs": wan_in}
    g["26"] = {
        "class_type": "KSampler",
        "inputs": {
            "model": ["20", 0],
            "positive": ["25", 0],
            "negative": ["25", 1],
            "latent_image": ["25", 2],
            "seed": int(seed),
            "steps": int(steps),
            "cfg": float(cfg),
            "sampler_name": "euler",
            "scheduler": "simple",
            "denoise": 1.0,
        },
    }
    g["27"] = {
        "class_type": "TrimVideoLatent",
        "inputs": {"samples": ["26", 0], "trim_amount": ["25", 3]},
    }
    g["28"] = {
        "class_type": "VAEDecode",
        "inputs": {"samples": ["27", 0], "vae": ["21", 0]},
    }
    g["29"] = {
        "class_type": "CreateVideo",
        "inputs": {"images": ["28", 0], "fps": float(fps)},
    }
    g["30"] = {
        "class_type": "SaveVideo",
        "inputs": {
            "video": ["29", 0],
            "filename_prefix": filename_prefix,
            "format": "auto",
            "codec": "auto",
        },
    }
    return g


def assert_graph_pose_lock(
    g: dict[str, Any],
    *,
    mode: str,
    expect_mask: bool,
) -> list[str]:
    errs: list[str] = []
    wan = next((n for n in g.values() if n.get("class_type") == "WanAnimateToVideo"), None)
    if wan is None:
        return ["WanAnimateToVideo missing"]
    inn = wan.get("inputs") or {}
    if "pose_video" not in inn:
        errs.append("pose_video not wired")
    if "reference_image" not in inn:
        errs.append("reference_image not wired")
    if any(n.get("class_type") == "MiniMaxH3ReferenceToVideo" for n in g.values()):
        errs.append("H3 R2V node must not be in the pose-lock graph")
    clip = next((n for n in g.values() if n.get("class_type") == "CLIPLoader"), None)
    if clip and (clip.get("inputs") or {}).get("type") != "wan":
        errs.append("CLIPLoader type must be wan")
    if mode == "mix":
        if "background_video" not in inn:
            errs.append("mix needs background_video")
        if expect_mask and "character_mask" not in inn:
            errs.append("mix needs character_mask")
    else:
        if "background_video" in inn or "character_mask" in inn:
            errs.append("move mode must not wire background/mask")
    if not any(n.get("class_type") == "DWPreprocessor" for n in g.values()):
        errs.append("DWPreprocessor missing")
    return errs


def default_mix_prompt(image_name: str) -> str:
    return (
        f"The character from the reference image ({image_name}) performs the motion. "
        "Keep the exact face, hair, body, and costume from the still. "
        "Photoreal live-action, same camera as the source clip, no text."
    )


def even16(n: int) -> int:
    return max(16, int(n) // 16 * 16)


def snap_video_size(width: int, height: int, max_edge: int = 640) -> tuple[int, int]:
    width, height = int(width), int(height)
    if max(width, height) > max_edge:
        scale = max_edge / float(max(width, height))
        width = int(width * scale)
        height = int(height * scale)
    return even16(width), even16(height)


def write_person_mask_videos(
    video_path: str | Path,
    out_dir: str | Path,
    n_people: int = 2,
    max_frames: int = 77,
) -> list[str]:
    """Write one binary mask mp4 per person (left-to-right on first frame).

    Needs ultralytics YOLO-seg. Crossing fighters can swap IDs; inspect the masks.
    Returns filenames relative to out_dir (usually Comfy input/).
    """
    try:
        import cv2  # type: ignore
        from ultralytics import YOLO  # type: ignore
    except ImportError as e:
        raise RuntimeError(
            "人物マスクには ultralytics が必要です。セル9で pip install ultralytics を実行してください。"
        ) from e

    video_path = Path(video_path)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"cannot open {video_path}")
    fps = cap.get(cv2.CAP_PROP_FPS) or 16.0
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()
    model = YOLO("yolov8n-seg.pt")
    # Track IDs so crossing fighters do not swap left/right every frame.
    stream = model.track(
        source=str(video_path),
        persist=True,
        classes=[0],
        stream=True,
        verbose=False,
        tracker="bytetrack.yaml",
    )
    first_map: dict[Any, int] | None = None
    writers = []
    names: list[str] = []
    n_written = 0
    for result in stream:
        if n_written >= max_frames:
            break
        frame = result.orig_img
        if frame is None:
            continue
        if not writers:
            for i in range(n_people):
                name = f"{video_path.stem}_mask_p{i + 1}.mp4"
                path = out_dir / name
                fourcc = cv2.VideoWriter_fourcc(*"mp4v")
                writers.append(cv2.VideoWriter(str(path), fourcc, fps, (w, h), True))
                names.append(name)
        canvases = [(frame * 0).astype("uint8") for _ in range(n_people)]
        boxes = result.boxes
        if boxes is not None and len(boxes) and boxes.xyxy is not None:
            xyxy = boxes.xyxy.cpu().tolist()
            ids = boxes.id.cpu().tolist() if boxes.id is not None else list(range(len(xyxy)))
            recs = [
                (ids[i], float(xyxy[i][0]), float(xyxy[i][1]), float(xyxy[i][2]), float(xyxy[i][3]))
                for i in range(len(xyxy))
            ]
            if first_map is None:
                first_map = assign_people_left_to_right(recs[:n_people])
            if result.masks is not None:
                for j, rec in enumerate(recs):
                    person_i = first_map.get(rec[0])
                    if person_i is None or person_i >= n_people:
                        continue
                    m = result.masks.data[j].cpu().numpy()
                    m = cv2.resize(m, (w, h), interpolation=cv2.INTER_NEAREST)
                    canvases[person_i][m > 0.5] = (255, 255, 255)
        for wr, canvas in zip(writers, canvases):
            wr.write(canvas)
        n_written += 1
    for wr in writers:
        wr.release()
    if not n_written or first_map is None:
        raise RuntimeError("最初のフレームで人物を検出できませんでした")
    return names
