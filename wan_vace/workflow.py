"""Build a ComfyUI API prompt for one Wan2.1 VACE cut."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any

from wan_vace.camera import spec_from_vector
from wan_vace.controls import CutControl, wan_length
from wan_vace.paths import (
    CLIP_NAME,
    FAST_CFG,
    FAST_STEPS,
    HEIGHT,
    LORA_CAUSVID,
    LORA_LIGHTX2V,
    LORA_SAKURA,
    LORA_STYLE,
    QUALITY_CFG,
    QUALITY_STEPS,
    SHIFT,
    UPSCALE_NAME,
    UNET_FP8,
    VAE_NAME,
    WIDTH,
)
from wan_vace.prompts import CutPrompt


class WorkflowError(ValueError):
    """The prompt cannot be built with the files and options given."""


@dataclass(frozen=True)
class JobOptions:
    width: int = WIDTH
    height: int = HEIGHT
    seed: int = 1
    steps: int = FAST_STEPS
    cfg: float = FAST_CFG
    shift: float = SHIFT
    sampler: str = "uni_pc"
    scheduler: str = "simple"
    unet_name: str = UNET_FP8
    clip_name: str = CLIP_NAME
    vae_name: str = VAE_NAME
    weight_dtype: str = "default"
    distill: str = "lightx2v"
    distill_strength: float = 1.0
    sakura_lora: str = LORA_SAKURA
    sakura_strength: float = 0.0
    style_lora: str = LORA_STYLE
    style_strength: float = 0.0
    face_consistency: bool = True
    face_protect: float = 0.35
    vace_strength: float = 1.0
    teacache: bool = False
    teacache_thresh: float = 0.2
    upscale: bool = False
    upscale_model: str = UPSCALE_NAME
    rife: bool = False
    rife_multiplier: int = 2
    source: str = "prerendered"
    crf: int = 19

    def resolved_distill(self) -> str:
        if self.distill not in ("none", "lightx2v", "causvid"):
            raise WorkflowError("distill は none、lightx2v、causvid")
        return self.distill


def fast_options(**overrides: Any) -> JobOptions:
    return replace(JobOptions(distill="lightx2v", steps=FAST_STEPS, cfg=FAST_CFG), **overrides)


def quality_options(**overrides: Any) -> JobOptions:
    return replace(
        JobOptions(distill="none", steps=QUALITY_STEPS, cfg=QUALITY_CFG, teacache=False),
        **overrides,
    )


def causvid_options(**overrides: Any) -> JobOptions:
    return replace(JobOptions(distill="causvid", steps=FAST_STEPS, cfg=FAST_CFG), **overrides)


def options_for_mode(mode: str, **overrides: Any) -> JobOptions:
    if mode == "fast":
        return fast_options(**overrides)
    if mode == "quality":
        return quality_options(**overrides)
    if mode == "causvid":
        return causvid_options(**overrides)
    raise WorkflowError("MODE は fast、quality、causvid")


@dataclass(frozen=True)
class BuiltPrompt:
    prompt: dict[str, Any]
    notes: tuple[str, ...]
    frames: int
    fps: int
    filename_prefix: str


def _node(class_type: str, inputs: dict[str, Any], title: str) -> dict[str, Any]:
    return {"class_type": class_type, "inputs": inputs, "_meta": {"title": title}}


def _link(node_id: str, output: int = 0) -> list[Any]:
    return [node_id, output]


def _distill_file(name: str) -> str:
    if name == "lightx2v":
        return LORA_LIGHTX2V
    if name == "causvid":
        return LORA_CAUSVID
    raise WorkflowError(f"未知の蒸留 LoRA: {name}")


def _append_lora(
    prompt: dict[str, Any],
    model: str,
    node_id: str,
    filename: str,
    strength: float,
    title: str,
    present: set[str],
    notes: list[str],
    required: bool,
) -> str:
    if strength == 0:
        notes.append(f"{title} は strength 0 なので入れない")
        return model
    if filename not in present:
        if required:
            raise WorkflowError(f"Drive の loras に無い: {filename}")
        notes.append(f"{title} のファイルが Drive に無いので飛ばす: {filename}")
        return model
    prompt[node_id] = _node(
        "LoraLoaderModelOnly",
        {"model": _link(model), "lora_name": filename, "strength_model": strength},
        title,
    )
    return node_id


def preprocessor_resolution(width: int, height: int) -> int:
    raw = max(width, height)
    stepped = ((raw + 63) // 64) * 64
    return min(2048, max(64, stepped))


def playback_rate(frame_count: int, model_frames: int, fps: int, multiplier: int) -> int:
    if multiplier <= 1:
        return fps
    produced = (frame_count - 1) * multiplier + 1
    if model_frames <= 0:
        return fps * multiplier
    return max(1, int(round(produced * fps / model_frames)))


def build_prompt(
    control: CutControl,
    cut_prompt: CutPrompt,
    *,
    pose_dir: str,
    depth_dir: str,
    face_image: str | None,
    options: JobOptions,
    present_files: set[str],
    plate_dir: str | None = None,
) -> BuiltPrompt:
    if options.width % 16 or options.height % 16:
        raise WorkflowError("幅と高さは 16 の倍数")
    if options.width * 16 != options.height * 9:
        raise WorkflowError("幅:高さ は 9:16（例 576x1024、720x1280）")
    source = options.source
    if plate_dir:
        source = "preprocess"
    if source not in ("prerendered", "preprocess"):
        raise WorkflowError("source は prerendered か preprocess")
    frames = wan_length(control.duration_s, control.fps)
    notes: list[str] = []
    prompt: dict[str, Any] = {}
    prompt["unet"] = _node(
        "UNETLoader",
        {"unet_name": options.unet_name, "weight_dtype": options.weight_dtype},
        "VACE 14B",
    )
    model = "unet"
    distill = options.resolved_distill()
    if distill != "none":
        model = _append_lora(
            prompt,
            model,
            "lora_distill",
            _distill_file(distill),
            options.distill_strength,
            f"蒸留 LoRA {distill}",
            present_files,
            notes,
            required=True,
        )
    sakura_strength = options.sakura_strength
    if options.face_consistency and cut_prompt.uses_sakura and sakura_strength == 0:
        notes.append("顔の固定は参照画像で行う。サクラ LoRA は strength が 0 より大きいときだけ")
    model = _append_lora(
        prompt,
        model,
        "lora_sakura",
        options.sakura_lora,
        sakura_strength if cut_prompt.uses_sakura else 0.0,
        "サクラ顔 LoRA",
        present_files,
        notes,
        required=False,
    )
    model = _append_lora(
        prompt,
        model,
        "lora_style",
        options.style_lora,
        options.style_strength,
        "dreamcore LoRA",
        present_files,
        notes,
        required=False,
    )
    prompt["shift"] = _node(
        "ModelSamplingSD3",
        {"model": _link(model), "shift": options.shift},
        "shift",
    )
    model = "shift"
    if options.teacache:
        prompt["teacache"] = _node(
            "TeaCache",
            {
                "model": _link(model),
                "model_type": "wan2.1_t2v_14B",
                "rel_l1_thresh": options.teacache_thresh,
                "start_percent": 0.0,
                "end_percent": 1.0,
                "cache_device": "cuda",
            },
            "TeaCache",
        )
        model = "teacache"
        notes.append("TeaCache は Wan2.1 T2V 14B の公開推奨値 rel_l1_thresh 0.2")
    prompt["clip"] = _node("CLIPLoader", {"clip_name": options.clip_name, "type": "wan"}, "UMT5")
    prompt["positive"] = _node(
        "CLIPTextEncode",
        {"clip": _link("clip"), "text": cut_prompt.positive},
        "positive",
    )
    prompt["negative"] = _node(
        "CLIPTextEncode",
        {"clip": _link("clip"), "text": cut_prompt.negative},
        "negative",
    )
    prompt["vae"] = _node("VAELoader", {"vae_name": options.vae_name}, "Wan VAE")
    prompt["pose_frames"] = _node(
        "VHS_LoadImagesPath",
        {
            "directory": pose_dir,
            "image_load_cap": frames,
            "skip_first_images": 0,
            "select_every_nth": 1,
        },
        "OpenPose guides",
    )
    prompt["depth_frames"] = _node(
        "VHS_LoadImagesPath",
        {
            "directory": depth_dir,
            "image_load_cap": frames,
            "skip_first_images": 0,
            "select_every_nth": 1,
        },
        "Depth guides",
    )
    plate_link_pose = _link("pose_frames")
    plate_link_depth = _link("depth_frames")
    if plate_dir:
        prompt["plate_frames"] = _node(
            "VHS_LoadImagesPath",
            {
                "directory": plate_dir,
                "image_load_cap": frames,
                "skip_first_images": 0,
                "select_every_nth": 1,
            },
            "plate",
        )
        plate_link_pose = _link("plate_frames")
        plate_link_depth = _link("plate_frames")
    prompt["openpose"] = _node(
        "OpenposePreprocessor",
        {
            "image": plate_link_pose,
            "detect_hand": "enable",
            "detect_body": "enable",
            "detect_face": "enable",
            "resolution": preprocessor_resolution(options.width, options.height),
            "scale_stick_for_xinsr_cn": "disable",
        },
        "OpenPose preprocessor",
    )
    prompt["depth_pre"] = _node(
        "DepthAnythingPreprocessor",
        {
            "image": plate_link_depth,
            "ckpt_name": "depth_anything_vits14.pth",
            "resolution": preprocessor_resolution(options.width, options.height),
        },
        "Depth preprocessor",
    )
    prompt["control_source"] = _node(
        "VaceControlSource",
        {
            "source": source,
            "pose_prerendered": _link("pose_frames"),
            "depth_prerendered": _link("depth_frames"),
            "pose_preprocessed": _link("openpose"),
            "depth_preprocessed": _link("depth_pre"),
        },
        "control source",
    )
    camera = spec_from_vector(
        control.camera,
        face_protect=options.face_protect if options.face_consistency and cut_prompt.uses_sakura else 0.0,
    )
    prompt["camera"] = _node(
        "VacePoseDepthCamera",
        {
            "pose": _link("control_source", 0),
            "depth": _link("control_source", 1),
            "width": options.width,
            "height": options.height,
            "length": frames,
            "tx": camera.tx,
            "ty": camera.ty,
            "tz": camera.tz,
            "rx": camera.rx,
            "ry": camera.ry,
            "rz": camera.rz,
            "shake_x": camera.shake_x,
            "shake_y": camera.shake_y,
            "shake_seed": camera.seed,
            "irregular": camera.irregular,
            "face_protect": camera.face_protect,
        },
        "camera on pose and depth",
    )
    vace_inputs: dict[str, Any] = {
        "positive": _link("positive"),
        "negative": _link("negative"),
        "vae": _link("vae"),
        "width": options.width,
        "height": options.height,
        "length": frames,
        "batch_size": 1,
        "strength": options.vace_strength,
        "control_video": _link("camera", 0),
        "control_masks": _link("camera", 1),
    }
    if cut_prompt.uses_sakura:
        if not face_image:
            raise WorkflowError(f"{control.cut} はサクラの参照画像が必要")
        prompt["face"] = _node("LoadImage", {"image": face_image}, "face reference")
        vace_inputs["reference_image"] = _link("face")
    else:
        notes.append(f"{control.cut} は人がいないので顔参照を渡さない")
    prompt["vace"] = _node("WanVaceToVideo", vace_inputs, "WanVaceToVideo")
    prompt["sampler"] = _node(
        "KSampler",
        {
            "model": _link(model),
            "seed": int(options.seed) + control.camera.shake.seed,
            "steps": options.steps,
            "cfg": options.cfg,
            "sampler_name": options.sampler,
            "scheduler": options.scheduler,
            "positive": _link("vace", 0),
            "negative": _link("vace", 1),
            "latent_image": _link("vace", 2),
            "denoise": 1.0,
        },
        "KSampler",
    )
    prompt["trim"] = _node(
        "TrimVideoLatent",
        {"samples": _link("sampler"), "trim_amount": _link("vace", 3)},
        "trim reference latents",
    )
    prompt["decode"] = _node(
        "VAEDecode",
        {"samples": _link("trim"), "vae": _link("vae")},
        "VAEDecode",
    )
    images = "decode"
    if options.upscale:
        if options.upscale_model not in present_files:
            raise WorkflowError(f"Drive の upscale_models に無い: {options.upscale_model}")
        prompt["upscale_loader"] = _node(
            "UpscaleModelLoader",
            {"model_name": options.upscale_model},
            "upscale model",
        )
        prompt["upscale"] = _node(
            "ImageUpscaleWithModel",
            {"upscale_model": _link("upscale_loader"), "image": _link(images)},
            "RealESRGAN x2",
        )
        images = "upscale"
    rate = control.fps
    if options.rife:
        prompt["rife"] = _node(
            "RIFE VFI",
            {
                "ckpt_name": "rife47.pth",
                "frames": _link(images),
                "clear_cache_after_n_frames": 10,
                "multiplier": options.rife_multiplier,
                "fast_mode": True,
                "ensemble": False,
                "scale_factor": 1.0,
                "dtype": "bfloat16",
                "torch_compile": False,
                "batch_size": 1,
            },
            "RIFE",
        )
        images = "rife"
        rate = playback_rate(frames, frames, control.fps, options.rife_multiplier)
    prefix = f"trial-01/{control.cut}"
    prompt["save"] = _node(
        "VHS_VideoCombine",
        {
            "images": _link(images),
            "frame_rate": rate,
            "loop_count": 0,
            "filename_prefix": prefix,
            "format": "video/h264-mp4",
            "pingpong": False,
            "save_output": True,
            "crf": options.crf,
            "pix_fmt": "yuv420p",
            "save_metadata": False,
        },
        "H.264 mp4",
    )
    return BuiltPrompt(prompt, tuple(notes), frames, rate, prefix)


def describe(options: JobOptions) -> list[str]:
    distill = options.resolved_distill()
    lines = [
        f"解像度 {options.width}x{options.height}（9:16）",
        f"steps {options.steps} / cfg {options.cfg} / shift {options.shift} / {options.sampler}",
        f"本体 {options.unet_name} / CLIP {options.clip_name} / VAE {options.vae_name}",
        f"蒸留 LoRA: {distill}" + ("" if distill == "none" else f" strength {options.distill_strength}"),
        f"TeaCache: {'on' if options.teacache else 'off'}",
        f"アップスケール: {'on' if options.upscale else 'off'} / RIFE: {'on' if options.rife else 'off'}",
        f"顔の固定: {'on' if options.face_consistency else 'off'} / face_protect {options.face_protect}",
        f"サクラ LoRA strength {options.sakura_strength} / dreamcore LoRA strength {options.style_strength}",
    ]
    return lines


def linked_nodes(prompt: dict[str, Any]) -> None:
    """Raise when an API link points at a missing node. Used by tests."""
    for node_id, node in prompt.items():
        if "class_type" not in node or "inputs" not in node:
            raise WorkflowError(f"{node_id} に class_type か inputs が無い")
        for value in node["inputs"].values():
            if (
                isinstance(value, list)
                and len(value) == 2
                and isinstance(value[0], str)
                and isinstance(value[1], int)
            ):
                if value[0] not in prompt:
                    raise WorkflowError(f"{node_id} が無いノード {value[0]} を指している")
    seen: set[str] = set()
    stack = ["save"]
    while stack:
        current = stack.pop()
        if current in seen:
            continue
        seen.add(current)
        for value in prompt[current]["inputs"].values():
            if (
                isinstance(value, list)
                and len(value) == 2
                and isinstance(value[0], str)
                and isinstance(value[1], int)
            ):
                stack.append(value[0])
    missing = set(prompt) - seen
    if missing:
        raise WorkflowError("出力から辿れないノード: " + ", ".join(sorted(missing)))
