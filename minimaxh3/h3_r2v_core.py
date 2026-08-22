"""Helpers for MiniMax H3 ComfyUI R2V (identity from stills, motion from video).

No ComfyUI / network required. Used by minimax_h3_colab_完全版.ipynb cell 8.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def frames(duration_s: float) -> int:
    """H3 length grid: 17k+5 at 24fps."""
    base = max(5, int(round(float(duration_s) * 24)))
    return int(base + (5 - (base % 17)) % 17)


def parse_list(s: str) -> list[str]:
    s = (s or "").strip()
    if not s or s.lower() in ("none", "-", "null"):
        return []
    return [x.strip().lstrip("./") for x in s.replace(";", ",").split(",") if x.strip()]


def comfy_media_name(rel: str | Path) -> str:
    """ComfyUI LoadImage / VHS video widgets want a path relative to input/, not basename-only."""
    return str(rel).replace("\\", "/").lstrip("./")


def prefer_ref2v_lora(lora_paths: list[Path], use_lora: bool) -> str | None:
    """Prefer Ref2V turbo for ref2va unet; never prefer FL2V-only when ref2v exists."""
    if not use_lora or not lora_paths:
        return None
    names = [p.name for p in lora_paths if p.suffix.lower() == ".safetensors"]
    if not names:
        return None

    def score(n: str) -> tuple:
        nl = n.lower()
        is_ref2v = 1 if ("ref2v" in nl or "ref2va" in nl) else 0
        is_fl2v = 1 if ("fl2v" in nl or "fl2va" in nl) and not is_ref2v else 0
        is_turbo = 1 if "turbo" in nl else 0
        is_4step = 1 if "4step" in nl or "4_step" in nl else 0
        is_comfy = 1 if "comfyui" in nl else 0
        return (is_ref2v, is_turbo, is_4step, is_comfy, -is_fl2v, n)

    ref2v = [n for n in names if "ref2v" in n.lower() or "ref2va" in n.lower()]
    if ref2v:
        return sorted(ref2v, key=score, reverse=True)[0]
    return sorted(names, key=score, reverse=True)[0]


def role_lock_preamble(img_names: list[str], vid_names: list[str]) -> str:
    lines = [
        "ROLE LOCK (mandatory):",
        "REFERENCE VIDEO = MOTION ONLY (hard rule):",
        "- From every <Video N>, read ONLY: body motion, hand trajectories, footwork, camera path,",
        "  framing changes, pacing, cut rhythm, and timing.",
        "- From every <Video N>, IGNORE completely: faces, gender presentation, age, hair, skin tone,",
        "  body build, costumes, logos, on-screen text, and the original actor's identity.",
        "- Never retarget appearance from the motion clip. The motion clip is a choreography/camera guide only.",
    ]
    for i, n in enumerate(img_names):
        lines.append(
            f"- <Picture {i+1}> ({n}) = IDENTITY + COSTUME only. "
            "Copy exact face, hair, skin, body proportions, and wardrobe from this still. "
            "Do NOT replace this person with anyone visible in any motion video."
        )
    for i, n in enumerate(vid_names):
        lines.append(
            f"- <Video {i+1}> ({n}) = MOTION + CAMERA + TIMING ONLY (not appearance). "
            "Follow camera path, pacing, body action, shot rhythm. "
            "Do NOT invent different choreography. "
            "Do NOT copy faces, body type, age, hair, or costumes from people in this video. "
            "Drive the still-locked characters through this motion like motion capture."
        )
    if not vid_names:
        lines.append("- No motion video: invent plausible cinematic motion consistent with the stills.")
    lines.append(
        "CONFLICT RULE: appearance always wins from Pictures; motion always wins from Videos. "
        "If the video actors look different from the stills, keep the still faces and only transfer motion."
    )
    return "\n".join(lines) + "\n\n"


def build_default_prompt(img_names: list[str], vid_names: list[str], duration_s: float) -> str:
    lock = role_lock_preamble(img_names, vid_names)
    pic_lines = [f"- <Picture {i+1}> = {n}" for i, n in enumerate(img_names)]
    vid_lines = [
        f"- <Video {i+1}> = {n} (MOTION ONLY: body/camera/timing — ignore faces & costumes in this clip)"
        for i, n in enumerate(vid_names)
    ]
    extra = ""
    if vid_names:
        extra = (
            " Transfer ONLY motion and camera from <Video 1> onto those still-locked characters "
            "(motion-capture style). Do not inherit the video actors' appearance."
        )
    pics = " and <Picture 2>" if len(img_names) > 1 else ""
    return (
        lock
        + "Use these references:\n"
        + "\n".join(pic_lines + vid_lines)
        + "\nSTYLE: photorealistic live-action cinematic, real skin pores, natural materials, "
        "no anime cel, no text, no subtitles, no logos.\n"
        f"integrated_multimodal_description: [Shot 1] Live-action remake for about "
        f"{duration_s:.0f} seconds. Characters must match <Picture 1>{pics} faces exactly."
        + extra
        + "\noverall_soundscape: Ambient and action SFX matching motion."
        + "\nnon_diegetic_music: None."
    )


def finalize_prompt(
    prompt: str,
    img_names: list[str],
    vid_names: list[str],
    duration_s: float,
    inject_role_lock: bool = True,
) -> str:
    raw = (prompt or "").strip()
    if not raw:
        return build_default_prompt(img_names, vid_names, duration_s)
    pics = "\n".join(f"<Picture {i+1}>:{n}" for i, n in enumerate(img_names))
    vids = "\n".join(f"<Video {i+1}>:{n}" for i, n in enumerate(vid_names))
    out = raw.replace("{pictures}", pics).replace("{videos}", vids)
    if inject_role_lock:
        has_lock = "ROLE LOCK" in out or "MOTION LOCK" in out or "APPEARANCE LOCK" in out
        if not has_lock:
            out = role_lock_preamble(img_names, vid_names) + out
        if img_names and "<Picture 1>" not in out and "<picture 1>" not in out.lower():
            out = f"Identity for character 1 is locked to <Picture 1> ({img_names[0]}).\n" + out
        if len(img_names) > 1 and "<Picture 2>" not in out:
            out = f"Identity for character 2 is locked to <Picture 2> ({img_names[1]}).\n" + out
        if vid_names and "<Video 1>" not in out:
            out = (
                f"MOTION ONLY from <Video 1> ({vid_names[0]}): body action, camera, timing. "
                "Ignore faces/costumes in the video; keep still-image identity.\n"
                + out
            )
        if vid_names and "MOTION ONLY" not in out.upper() and "motion only" not in out.lower():
            out = (
                "HARD CONSTRAINT: Reference videos provide MOTION ONLY "
                "(choreography + camera + timing). Appearance comes exclusively from still Pictures.\n"
                + out
            )
    return out


def image_ref_key(i: int) -> str:
    return f"ref_images.ref_image_{i}"


def video_ref_key(i: int) -> str:
    return f"ref_videos.ref_video_{i}"


def cap_duration_for_vram(
    duration_s: float,
    *,
    vram_gb: float,
    n_images: int,
    has_video: bool,
    ref_image_size: str,
) -> float:
    """R2V VRAM scales with frames × ref_image_size × video tokens. 14s+max OOMs on 40GB."""
    duration_s = float(duration_s)
    if duration_s < 1:
        duration_s = 5
    if not has_video:
        return min(duration_s, 15.0)
    if vram_gb < 24:
        cap = 5.0
    elif vram_gb < 48:
        # A100 40GB: 14s + max + 2 stills + motion clip requested 18.5GiB extra and died
        cap = 6.0 if (ref_image_size == "max" and n_images >= 2) else 8.0
    else:
        cap = 15.0
    return min(duration_s, cap)


def r2v_retry_plans(
    *,
    duration_s: float,
    ref_image_size: str,
    width: int,
    height: int,
    n_images: int,
    has_video: bool,
    vram_gb: float,
) -> list[dict[str, Any]]:
    """Smaller later. Never drops the motion video."""
    first_dur = cap_duration_for_vram(
        duration_s,
        vram_gb=vram_gb,
        n_images=n_images,
        has_video=has_video,
        ref_image_size=ref_image_size,
    )
    plans = [
        {
            "duration_s": first_dur,
            "ref_image_size": ref_image_size if ref_image_size in ("match", "max") else "max",
            "width": width,
            "height": height,
            "motion_max_edge": 768 if has_video else None,
            "label": f"dur={first_dur:.0f}s size={ref_image_size} motion_edge=768",
        }
    ]
    if has_video:
        plans.append(
            {
                "duration_s": min(first_dur, 6.0),
                "ref_image_size": "match",
                "width": width,
                "height": height,
                "motion_max_edge": 640,
                "label": "dur<=6s size=match motion_edge=640",
            }
        )
        plans.append(
            {
                "duration_s": 5.0,
                "ref_image_size": "match",
                "width": min(width, 768) if width >= height else width,
                "height": min(height, 448) if width >= height else min(height, 768),
                "motion_max_edge": 512,
                "label": "dur=5s size=match 768-class canvas motion_edge=512",
            }
        )
    # snap spatial to multiple of 32
    for p in plans:
        p["width"] = max(32, int(p["width"]) // 32 * 32)
        p["height"] = max(32, int(p["height"]) // 32 * 32)
    # de-dupe identical plans
    out: list[dict[str, Any]] = []
    seen: set[tuple] = set()
    for p in plans:
        key = (p["duration_s"], p["ref_image_size"], p["width"], p["height"], p["motion_max_edge"])
        if key in seen:
            continue
        seen.add(key)
        out.append(p)
    return out


def is_oom_error(payload: Any) -> bool:
    text = str(payload).lower()
    return "out of memory" in text or "outofmemory" in text or "cuda oom" in text


def vhs_load_video_inputs(
    object_info: dict[str, Any] | None,
    filename: str,
    length: int,
    motion_max_edge: int | None = 768,
) -> dict[str, Any]:
    """Fill VHS_LoadVideo widgets from live object_info so schema drift does not drop the clip."""
    filename = comfy_media_name(filename)
    info = ((object_info or {}).get("VHS_LoadVideo") or {}).get("input") or {}
    required = info.get("required") or {}
    optional = info.get("optional") or {}
    merged = {**required, **optional}
    inputs: dict[str, Any] = {}
    for name, spec in merged.items():
        if isinstance(spec, list) and len(spec) > 1 and isinstance(spec[1], dict) and "default" in spec[1]:
            inputs[name] = spec[1]["default"]
    if "video" in merged:
        inputs["video"] = filename
    elif "file" in merged:
        inputs["file"] = filename
    else:
        inputs["video"] = filename
    if "force_rate" in merged:
        inputs["force_rate"] = 24
    if "frame_load_cap" in merged:
        inputs["frame_load_cap"] = int(length)
    if "skip_first_frames" in merged:
        inputs["skip_first_frames"] = 0
    if "select_every_nth" in merged:
        inputs["select_every_nth"] = 1
    if motion_max_edge:
        _apply_vhs_motion_size(inputs, merged, int(motion_max_edge))
    elif "force_size" in merged:
        inputs["force_size"] = "Disabled"
    return inputs


def _apply_vhs_motion_size(inputs: dict[str, Any], merged: dict[str, Any], max_edge: int) -> None:
    """Downscale motion frames. Full-res 14s clips blow 40GB during sampling."""
    max_edge = max(256, int(max_edge))
    if "force_size" in merged:
        spec = merged["force_size"]
        choices = spec[0] if isinstance(spec, list) and spec else []
        picked = None
        if isinstance(choices, list):
            for cand in ("Custom", "Custom Width", str(max_edge), "768", "512"):
                if cand in choices:
                    picked = cand
                    break
        inputs["force_size"] = picked or "Custom"
    if "custom_width" in merged:
        inputs["custom_width"] = max_edge
    if "custom_height" in merged:
        h = max(256, (max_edge * 9 // 16) // 2 * 2)
        inputs["custom_height"] = h


def native_load_video_inputs(filename: str) -> dict[str, Any]:
    name = comfy_media_name(filename)
    return {"file": name, "video": name}


def build_r2v_graph(
    *,
    img_names: list[str],
    vid_names: list[str],
    prompt: str,
    unet: str,
    lora_name: str | None,
    lora_strength: float,
    width: int,
    height: int,
    duration_s: float,
    seed: int,
    steps: int,
    filename_prefix: str,
    ref_image_size: str = "max",
    use_videos: bool = True,
    has_vhs: bool = True,
    has_lora_loader: bool = True,
    has_audio_decode: bool = True,
    object_info: dict[str, Any] | None = None,
    motion_max_edge: int | None = 768,
    clip_name: str = "qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors",
    vvae: str = "minimax_h3_video_vae_fp16.safetensors",
    avae: str = "minimax_h3_audio_vae_fp32.safetensors",
) -> dict[str, Any]:
    """Build ComfyUI API graph for MiniMaxH3ReferenceToVideo."""
    if width % 32 or height % 32:
        raise ValueError(f"H3 width/height must be multiples of 32, got {width}x{height}")
    g: dict[str, Any] = {}
    length = frames(duration_s)

    for i, fname in enumerate(img_names):
        g[str(100 + i)] = {
            "class_type": "LoadImage",
            "inputs": {"image": comfy_media_name(fname)},
        }

    g["1"] = {
        "class_type": "UNETLoader",
        "inputs": {"unet_name": unet, "weight_dtype": "default"},
    }
    model: list[Any] = ["1", 0]
    if lora_name and has_lora_loader:
        g["2"] = {
            "class_type": "LoraLoaderModelOnly",
            "inputs": {
                "model": ["1", 0],
                "lora_name": lora_name,
                "strength_model": float(lora_strength),
            },
        }
        model = ["2", 0]

    g["3"] = {
        "class_type": "CLIPLoader",
        "inputs": {"clip_name": clip_name, "type": "minimax", "device": "default"},
    }
    g["4"] = {"class_type": "VAELoader", "inputs": {"vae_name": vvae}}
    g["5"] = {"class_type": "VAELoader", "inputs": {"vae_name": avae}}

    r_inputs: dict[str, Any] = {
        "clip": ["3", 0],
        "vae": ["4", 0],
        "audio_vae": ["5", 0],
        "prompt": prompt,
        "width": int(width),
        "height": int(height),
        "length": length,
        "ref_image_size": ref_image_size if ref_image_size in ("match", "max") else "max",
    }

    for i in range(len(img_names)):
        r_inputs[image_ref_key(i)] = [str(100 + i), 0]

    if use_videos and vid_names:
        for vi, vname in enumerate(vid_names[:3]):
            node_id = str(190 + vi)
            if has_vhs:
                g[node_id] = {
                    "class_type": "VHS_LoadVideo",
                    "inputs": vhs_load_video_inputs(
                        object_info, vname, length, motion_max_edge=motion_max_edge
                    ),
                }
            else:
                g[node_id] = {
                    "class_type": "LoadVideo",
                    "inputs": native_load_video_inputs(vname),
                }
            r_inputs[video_ref_key(vi)] = [node_id, 0]

    for bad in ("ref_videos", "ref_images", "ref_audios", "ref_video_audios"):
        r_inputs.pop(bad, None)

    g["20"] = {"class_type": "MiniMaxH3ReferenceToVideo", "inputs": r_inputs}
    g["21"] = {"class_type": "RandomNoise", "inputs": {"noise_seed": int(seed)}}
    sampler = "euler" if lora_name else "res_multistep"
    scheduler = "simple" if lora_name else "beta"
    g["22"] = {"class_type": "KSamplerSelect", "inputs": {"sampler_name": sampler}}
    g["23"] = {
        "class_type": "BasicScheduler",
        "inputs": {
            "model": model,
            "scheduler": scheduler,
            "steps": int(steps) if lora_name else max(int(steps), 16),
            "denoise": 1.0,
        },
    }
    g["24"] = {
        "class_type": "BasicGuider",
        "inputs": {"model": model, "conditioning": ["20", 0]},
    }
    g["25"] = {
        "class_type": "SamplerCustomAdvanced",
        "inputs": {
            "noise": ["21", 0],
            "guider": ["24", 0],
            "sampler": ["22", 0],
            "sigmas": ["23", 0],
            "latent_image": ["20", 1],
        },
    }
    g["26"] = {
        "class_type": "VAEDecode",
        "inputs": {"samples": ["25", 0], "vae": ["4", 0]},
    }
    if has_audio_decode:
        g["27"] = {
            "class_type": "VAEDecodeAudio",
            "inputs": {"samples": ["25", 0], "vae": ["5", 0]},
        }
        g["28"] = {
            "class_type": "CreateVideo",
            "inputs": {"images": ["26", 0], "audio": ["27", 0], "fps": 24},
        }
    else:
        g["28"] = {
            "class_type": "CreateVideo",
            "inputs": {"images": ["26", 0], "fps": 24},
        }
    g["29"] = {
        "class_type": "SaveVideo",
        "inputs": {
            "video": ["28", 0],
            "filename_prefix": filename_prefix,
            "format": "auto",
            "codec": "auto",
        },
    }
    return g


def assert_graph_identity_motion(
    graph: dict[str, Any],
    *,
    expect_images: int,
    expect_videos: int,
    prompt: str,
) -> list[str]:
    """Return list of error strings (empty = ok)."""
    errs: list[str] = []
    node = graph.get("20") or {}
    if node.get("class_type") != "MiniMaxH3ReferenceToVideo":
        errs.append("node 20 is not MiniMaxH3ReferenceToVideo")
        return errs
    inputs = node.get("inputs") or {}
    for bad in ("ref_videos", "ref_images"):
        if bad in inputs:
            errs.append(f"parent key {bad} must not be used alone")
    for i in range(expect_images):
        k = image_ref_key(i)
        if k not in inputs:
            errs.append(f"missing {k}")
    if expect_videos:
        for i in range(expect_videos):
            k = video_ref_key(i)
            if k not in inputs:
                errs.append(f"missing {k}")
        if "190" not in graph:
            errs.append("missing video load node 190")
        else:
            vin = graph["190"].get("inputs") or {}
            klass = graph["190"].get("class_type")
            if klass == "VHS_LoadVideo" and int(vin.get("force_rate") or 0) not in (0, 24):
                # 0 = keep source rate in some VHS versions; 24 is required by H3
                errs.append("VHS force_rate must be 24")
            media = vin.get("video") or vin.get("file") or ""
            if not media:
                errs.append("video loader has empty filename")
    ris = inputs.get("ref_image_size")
    if ris not in ("match", "max"):
        errs.append(f"bad ref_image_size: {ris}")
    if expect_images and "<Picture 1>" not in prompt and "Picture 1" not in prompt:
        errs.append("prompt missing Picture 1 identity lock")
    if expect_videos and "<Video 1>" not in prompt and "Video 1" not in prompt:
        errs.append("prompt missing Video 1 motion lock")
    if expect_videos:
        pu = prompt.upper()
        if "MOTION ONLY" not in pu and "MOTION + CAMERA" not in pu and "MOTION/CAMERA" not in pu:
            if "MOTION" not in pu:
                errs.append("prompt missing MOTION-only language for reference video")
        if "FACE" not in pu and "IDENTITY" not in pu and "PICTURE" not in pu:
            errs.append("prompt missing still-identity vs video-motion separation")
    return errs


def _find_ffmpeg() -> str | None:
    import shutil

    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    for c in ("/usr/bin/ffmpeg", "/usr/local/bin/ffmpeg"):
        if Path(c).is_file():
            return c
    return None


def strip_motion_identity_video(
    src: Path,
    dst: Path,
    *,
    mode: str = "edges",
    ffmpeg_bin: str | None = None,
) -> Path:
    """Optional last resort: destroy photoreal identity while keeping coarse motion."""
    import subprocess

    src = Path(src)
    dst = Path(dst)
    if not src.is_file():
        raise FileNotFoundError(src)
    dst.parent.mkdir(parents=True, exist_ok=True)
    mode = (mode or "edges").lower().strip()
    if mode not in ("edges", "blur"):
        mode = "edges"
    ff = ffmpeg_bin or _find_ffmpeg()
    if not ff:
        raise RuntimeError("Cannot strip video identity: ffmpeg is required")
    if mode == "blur":
        vf = "format=gray,gblur=sigma=12,format=yuv420p"
    else:
        vf = "format=gray,edgedetect=mode=colormix:high=0.12:low=0.04,format=yuv420p"
    r = subprocess.run(
        [ff, "-y", "-i", str(src), "-vf", vf, "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(dst)],
        capture_output=True,
        text=True,
    )
    if r.returncode != 0 or not dst.is_file() or dst.stat().st_size < 1000:
        raise RuntimeError(f"ffmpeg strip failed: {(r.stderr or '')[-800:]}")
    return dst


def prepare_motion_refs(
    inp_dir: Path,
    rel_names: list[str],
    *,
    enabled: bool = True,
    mode: str = "edges",
) -> list[str]:
    if not enabled or not rel_names:
        return list(rel_names)
    out_names: list[str] = []
    for rel in rel_names:
        src = Path(inp_dir) / rel
        if not src.is_file():
            hits = list(Path(inp_dir).rglob(Path(rel).name))
            if not hits:
                raise FileNotFoundError(rel)
            src = hits[0]
        stem = src.stem
        if stem.endswith("_motion_only_edges") or stem.endswith("_motion_only_blur"):
            try:
                out_names.append(str(src.relative_to(inp_dir)).replace("\\", "/"))
            except ValueError:
                out_names.append(src.name)
            continue
        suffix = "_motion_only_edges" if mode == "edges" else "_motion_only_blur"
        dst = src.with_name(f"{stem}{suffix}.mp4")
        strip_motion_identity_video(src, dst, mode=mode)
        try:
            out_names.append(str(dst.relative_to(inp_dir)).replace("\\", "/"))
        except ValueError:
            out_names.append(dst.name)
    return out_names
