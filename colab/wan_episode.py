#!/usr/bin/env python3
"""Wan 2.2 T2V / I2V renderer for an already-prepared H3 episode.

Sits beside MiniMax H3. Does not replace h3_episode.run_episode or the H3 notebook.
Does not load 10Eros, MiniMax H3, or H3 LoRA weights. Does not use pose_motion_lock
(that module is Wan 2.2 Animate skeleton replacement, not this episode renderer).

Story text, overlay order, trim seconds, and the final HUD stitch stay in h3_episode.
This module only decides how each prepared beat is drawn:

  source t2v  -> Wan 2.2 T2V, no start image
  source chain or still -> Wan 2.2 I2V, previous beat's last frame only
  raw/<id>.mp4 already on disk -> skip, unless fresh=True

Episode output (raw, hud, final, logs) goes under OneDrive, never Google Drive.
The human presses the Colab generate cell. Nothing here starts a GPU job on import.
"""

from __future__ import annotations

import os
import shutil
import urllib.parse
from pathlib import Path
from typing import Any

from h3_episode import (
    EpisodeError,
    beat_clip_seconds,
    beat_source,
    build_beat_prompt,
    canvas_for,
    ensure_episode_tree,
    extra_lora_entries,
    finish_episode,
    is_ui_beat,
    load_status,
    prepare_episode,
    previous_footage,
    save_status,
)
from h3_hud import extract_frame, synthetic_clip
from h3_i2v_phone import collect_output_videos
from h3_i2v_runtime import PORT, post_prompt, wait_prompt

# Slot names copied from beat.extra_loras. Files below are Wan 2.2 high/low pairs, not H3 weights.
WAN_SLOTS = (
    "mystic",
    "penis",
    "synth",
    "thrust",
    "sideride",
    "kiss",
    "blowjob",
    "cunny",
    "thumbinbutt",
    "cumshot",
    "anal",
    "nelson",
    "doggy",
    "missionary",
    "pee",
    "scat",
)

_COMFY_ORG = "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files"
_TIAN = "https://huggingface.co/tianbugao/wan_i2v/resolve/main/loras"

WAN_TEXT_ENCODER = "umt5_xxl_fp8_e4m3fn_scaled.safetensors"
WAN_TEXT_ENCODER_TYPE = "wan"
WAN_VAE = "wan_2.1_vae.safetensors"
# NSFW Fast Move V2 Q8. Lightning is already inside these GGUFs.
# The linked page is the high half (2540892). Wan still needs the matching low (2540896).
WAN_CKPT_HIGH = "wan22EnhancedNSFWSVICamera_nsfwFASTMOVEV2Q8H.gguf"
WAN_CKPT_LOW = "wan22EnhancedNSFWSVICamera_nsfwFASTMOVEV2Q8L.gguf"
WAN_CKPT_HIGH_URL = "https://civitai.com/api/download/models/2540892"
WAN_CKPT_LOW_URL = "https://civitai.com/api/download/models/2540896"
WAN_T2V_HIGH = WAN_CKPT_HIGH
WAN_T2V_LOW = WAN_CKPT_LOW
WAN_I2V_HIGH = WAN_CKPT_HIGH
WAN_I2V_LOW = WAN_CKPT_LOW

# Wan's own latent grid. Story length stays beat trim.seconds / clip_seconds.
# This checkpoint wants 2 high steps + 2 low steps, CFG 1. Do not stack another Lightning LoRA.
WAN_FPS = 16
WAN_SAMPLE_STEPS = 4
WAN_SAMPLE_CFG = 1.0


def _tian(name: str) -> str:
    return f"{_TIAN}/{urllib.parse.quote(name)}"


def _pair(slot: str, high_remote: str, low_remote: str) -> dict[str, str]:
    return _url_pair(slot, _tian(high_remote), _tian(low_remote))


def _url_pair(slot: str, high_url: str, low_url: str, *, trigger: str = "") -> dict[str, str]:
    row = {
        "high_name": f"wan-{slot}-high.safetensors",
        "low_name": f"wan-{slot}-low.safetensors",
        "high_url": high_url,
        "low_url": low_url,
    }
    if trigger:
        row["trigger"] = trigger
    return row


# Each H3 slot name maps to a Wan 2.2 14B high-noise file and a low-noise file.
# Missing files are skipped at strength 0. H3 filenames are never opened.
WAN_SLOT_LORAS: dict[str, dict[str, str]] = {
    "mystic": _pair("mystic", "NSFW-22-H-e8.safetensors", "NSFW-22-L-e8.safetensors"),
    "penis": _pair("penis", "PenInsert_high_noise.safetensors", "PenInsert_low_noise.safetensors"),
    "synth": _pair(
        "synth",
        "PussyLoRA_HighNoise_Wan2.2_HearmemanAI.safetensors",
        "PussyLoRA_LowNoise_Wan2.2_HearmemanAI.safetensors",
    ),
    "thrust": _pair(
        "thrust",
        "Wan2.2 - I2V - Orgasm v2 - 14B_high_noise.safetensors",
        "Wan2.2 - I2V - Orgasm v2 - 14B_low_noise.safetensors",
    ),
    "sideride": _pair(
        "sideride",
        "mql_casting_sex_reverse_cowgirl_lie_front_vagina_wan22_i2v_v1_high_noise.safetensors",
        "mql_casting_sex_reverse_cowgirl_lie_front_vagina_wan22_i2v_v1_low_noise.safetensors",
    ),
    "kiss": _pair(
        "kiss",
        "Wan2.2 - T2V - Kissing - HIGH 14B.safetensors",
        "Wan2.2 - T2V - Kissing - LOW 14B.safetensors",
    ),
    "blowjob": _pair(
        "blowjob",
        "iGOON_Blink_Blowjob_I2V_HIGH.safetensors",
        "iGOON_Blink_Blowjob_I2V_LOW.safetensors",
    ),
    "cunny": _pair("cunny", "cunn_wan_epoch_80.safetensors", "cunn_wan_epoch_80.safetensors"),
    "thumbinbutt": _pair("thumbinbutt", "WanTwoFingers.safetensors", "WanTwoFingers.safetensors"),
    "cumshot": _pair(
        "cumshot",
        "23High noise-Cumshot Aesthetics.safetensors",
        "56Low noise-Cumshot Aesthetics.safetensors",
    ),
    # pikenrover Wan 2.2 I2V anal. High 2161023, low 2161067. Trigger stays on the Wan prompt.
    "anal": _url_pair(
        "anal",
        "https://huggingface.co/jinksa77/analsex/resolve/main/wan22_i2v_anal_v1_high_noise.safetensors",
        "https://huggingface.co/jinksa77/analsex/resolve/main/wan22_i2v_anal_v1_low_noise.safetensors",
        trigger="anal sex",
    ),
    "nelson": _url_pair(
        "nelson",
        "https://civitai.com/api/download/models/2332735",
        "https://civitai.com/api/download/models/2332853",
        trigger="FU11N31S0N",
    ),
    "doggy": _url_pair(
        "doggy",
        "https://civitai.com/api/download/models/2306421",
        "https://civitai.com/api/download/models/2306425",
    ),
    "missionary": _url_pair(
        "missionary",
        "https://civitai.com/api/download/models/2098405",
        "https://civitai.com/api/download/models/2098396",
    ),
    "pee": _url_pair(
        "pee",
        "https://huggingface.co/obsxrver/wan2.2-i2v-piss/resolve/main/WAN2.2-I2V_HighNoise_I2Pee-V4.safetensors",
        "https://huggingface.co/obsxrver/wan2.2-i2v-piss/resolve/main/WAN2.2-I2V_LowNoise_I2Pee-V4.safetensors",
    ),
    "scat": _url_pair(
        "scat",
        "https://huggingface.co/obsxrver/wan2.2-i2v-scat/resolve/main/WAN2.2-I2V-HighNoise_scat-xxi-i2v.safetensors",
        "https://huggingface.co/obsxrver/wan2.2-i2v-scat/resolve/main/WAN2.2-I2V-LowNoise_scat-xxi-i2v.safetensors",
    ),
}

H3_WEIGHT_MARKERS = (
    "minimax",
    "mh3",
    "10eros",
    "eros",
    "thumbinbutt",
    "cowgirl-side",
    "h3-",
)

_DRIVE_MARKERS = ("mydrive", "google drive", "/content/drive")


def onedrive_root() -> Path:
    """Runtime store. WAN_ONEDRIVE_ROOT wins. Otherwise this PC's OneDrive folder."""
    env = (os.environ.get("WAN_ONEDRIVE_ROOT") or "").strip()
    if env:
        root = Path(env)
    else:
        local = Path.home() / "OneDrive"
        root = local / "wan-hospital" if local.is_dir() else Path("/content/onedrive/wan-hospital")
    _reject_google_drive(root)
    return root


def episode_work_root(slug: str, root: Path | str | None = None) -> Path:
    base = Path(root) if root is not None else onedrive_root()
    _reject_google_drive(base)
    return base / "episodes" / slug


def _reject_google_drive(path: Path) -> None:
    text = str(path).replace("\\", "/").lower()
    if any(marker in text for marker in _DRIVE_MARKERS):
        raise EpisodeError(f"Wan episode data must stay on OneDrive, not Google Drive: {path}")


def wan_needs_start_image(source: str) -> bool:
    """chain and still take one start image. cut and t2v do not."""
    return source in ("chain", "still")


def _h3_weight(name: str) -> bool:
    low = name.replace("\\", "/").lower()
    return any(marker in low for marker in H3_WEIGHT_MARKERS)


def wan_weight_jobs() -> list[tuple[str, str]]:
    """(url, path under the OneDrive models directory). Base Wan 2.2 files plus slot LoRAs."""
    jobs = [
        (WAN_CKPT_HIGH_URL, f"diffusion_models/{WAN_CKPT_HIGH}"),
        (WAN_CKPT_LOW_URL, f"diffusion_models/{WAN_CKPT_LOW}"),
        (f"{_COMFY_ORG}/text_encoders/{WAN_TEXT_ENCODER}", f"text_encoders/{WAN_TEXT_ENCODER}"),
        (f"{_COMFY_ORG}/vae/{WAN_VAE}", f"vae/{WAN_VAE}"),
    ]
    seen: set[str] = set()
    for spec in WAN_SLOT_LORAS.values():
        for url, name in ((spec["high_url"], spec["high_name"]), (spec["low_url"], spec["low_name"])):
            rel = f"loras/{name}"
            if rel in seen:
                continue
            seen.add(rel)
            jobs.append((url, rel))
    return jobs


def _action_text(beat: dict[str, Any]) -> str:
    return str(beat.get("action") or "").lower()


def scene_slot_entries(beat: dict[str, Any]) -> list[tuple[str, float]]:
    """Wan-only LoRAs for acts the prepared beat already performs.

    H3 extra_loras and the episode text stay as authored. Thumb-only and the
    exit walk do not take the shaft anal pair.
    """
    act = _action_text(beat)
    bid = str(beat.get("id") or "")
    if bid.endswith("-walk") or bid.endswith("-spot"):
        return []
    rows: list[tuple[str, float]] = []
    shaft_anal = "thumb" not in act and "brown log" not in act and any(
        phrase in act
        for phrase in (
            "into the anus",
            "into aya's anus",
            "inside the anus",
            "travels into the anus",
            "fills the anus",
        )
    )
    if shaft_anal:
        rows.append(("anal", 0.8))
    if shaft_anal and "held up" in act and "thighs" in act:
        rows.append(("nelson", 0.75))
    if "all fours" in act:
        rows.append(("doggy", 0.8))
    if "stays on her back" in act and "straddl" not in act and (
        "between" in act or "into the pussy" in act
    ):
        rows.append(("missionary", 0.8))
    if "lemon-yellow water" in act and "streaming" in act:
        rows.append(("pee", 0.8))
    if "brown log" in act and "slides" in act:
        rows.append(("scat", 0.75))
    return rows


def wan_beat_prompt(ep: dict[str, Any], beat: dict[str, Any]) -> str:
    """H3 prompt, plus the Wan LoRA trigger when that scene slot is on."""
    prompt = build_beat_prompt(ep, beat)
    extra: list[str] = []
    for name, _strength in scene_slot_entries(beat):
        trigger = str(WAN_SLOT_LORAS.get(name, {}).get("trigger") or "").strip()
        if trigger and trigger.lower() not in prompt.lower():
            extra.append(trigger)
    if not extra:
        return prompt
    return prompt.rstrip() + "\n" + ", ".join(extra)


def wan_slot_plan(beat: dict[str, Any], loras_dir: Path | None = None) -> list[dict[str, Any]]:
    """Keep extra_loras names. Each slot uses its Wan 2.2 high and low files.

    Scene slots are added beside those names. A slot whose Wan files are not on
    disk is strength 0 and omitted. H3 weights are never substituted.
    """
    plan: list[dict[str, Any]] = []
    entries = list(extra_lora_entries(beat))
    for name, strength in scene_slot_entries(beat):
        if name not in {key for key, _strength in entries}:
            entries.append((name, strength))
    for name, strength in entries:
        spec = WAN_SLOT_LORAS.get(name)
        if spec is None or float(strength) <= 0:
            continue
        if _h3_weight(spec["high_name"]) or _h3_weight(spec["low_name"]):
            continue
        if loras_dir is not None:
            high = loras_dir / spec["high_name"]
            low = loras_dir / spec["low_name"]
            if not high.is_file() or not low.is_file():
                continue
        plan.append({
            "slot": name,
            "strength": float(strength),
            "high": spec["high_name"],
            "low": spec["low_name"],
        })
    return plan


def _trim_seconds(ep: dict[str, Any], beat: dict[str, Any]) -> float:
    trim = beat.get("trim") if isinstance(beat.get("trim"), dict) else {}
    try:
        seconds = float(trim.get("seconds") or 0.0)
    except (TypeError, ValueError):
        seconds = 0.0
    if seconds <= 0:
        seconds = float(beat_clip_seconds(ep, beat))
    return seconds


def wan_length(seconds: float) -> int:
    """Wan 16fps length, 4n+1. The story second-count is unchanged."""
    frames = int(round(float(seconds) * WAN_FPS)) + 1
    frames = max(5, frames)
    return frames + (4 - ((frames - 1) % 4)) % 4


def plan_wan_shots(ep: dict[str, Any], loras_dir: Path | None = None) -> list[dict[str, Any]]:
    """One row per GPU beat after prepare_episode. UI beats are not drawn."""
    canvas = canvas_for(ep)
    shots: list[dict[str, Any]] = []
    for beat in ep.get("beats") or []:
        if not isinstance(beat, dict) or is_ui_beat(beat):
            continue
        source = beat_source(beat)
        if source not in ("t2v", "chain", "still"):
            raise EpisodeError(f"{beat.get('id')}: Wan draws t2v, chain, or still, not {source}")
        shots.append({
            "id": str(beat["id"]),
            "source": source,
            "seconds": _trim_seconds(ep, beat),
            "start_image": wan_needs_start_image(source),
            "canvas": canvas,
            "slots": wan_slot_plan(beat, loras_dir),
        })
    return shots


def _loader(class_type: str, **inputs: Any) -> dict[str, Any]:
    return {"class_type": class_type, "inputs": inputs}


def build_wan_graph(
    *,
    source: str,
    prompt: str,
    width: int,
    height: int,
    seconds: float,
    seed: int,
    filename_prefix: str,
    start_image: str | None = None,
    slots: list[dict[str, Any]] | None = None,
    use_lightx2v: bool = False,
) -> dict[str, Any]:
    """ComfyUI API graph. T2V has no LoadImage. I2V has exactly one start image.

    High-noise LoRAs attach only to the high expert. Low-noise LoRAs attach only to the low expert.
    """
    if source == "t2v":
        if start_image:
            raise EpisodeError("Wan T2V does not take a start image")
        high, low = WAN_T2V_HIGH, WAN_T2V_LOW
    elif source in ("chain", "still"):
        if not start_image:
            raise EpisodeError("Wan I2V needs the previous beat's last frame")
        high, low = WAN_I2V_HIGH, WAN_I2V_LOW
    else:
        raise EpisodeError(f"Wan graph does not draw source {source}")
    for row in slots or []:
        for key in ("high", "low"):
            if _h3_weight(str(row.get(key) or "")):
                raise EpisodeError(f"refusing H3 weight in a Wan graph: {row.get(key)}")
    if use_lightx2v:
        raise EpisodeError("NSFW Fast Move V2 already contains Lightning. Do not stack another Lightning LoRA.")
    steps = WAN_SAMPLE_STEPS
    cfg = WAN_SAMPLE_CFG
    g: dict[str, Any] = {
        "1": _loader("CLIPLoader", clip_name=WAN_TEXT_ENCODER, type=WAN_TEXT_ENCODER_TYPE),
        "2": _loader("CLIPTextEncode", text=prompt, clip=["1", 0]),
        "3": _loader("CLIPTextEncode", text="", clip=["1", 0]),
        "4": _loader("UnetLoaderGGUF", unet_name=high),
        "5": _loader("UnetLoaderGGUF", unet_name=low),
        "6": _loader("VAELoader", vae_name=WAN_VAE),
    }
    model_high, model_low = "4", "5"
    chain: list[tuple[str, str, float]] = []
    for row in slots or []:
        chain.append((str(row["high"]), str(row["low"]), float(row["strength"])))
    for i, (high_name, low_name, strength) in enumerate(chain):
        hid, lid = f"h{i}", f"l{i}"
        g[hid] = _loader(
            "LoraLoaderModelOnly",
            model=[model_high, 0],
            lora_name=high_name,
            strength_model=strength,
        )
        g[lid] = _loader(
            "LoraLoaderModelOnly",
            model=[model_low, 0],
            lora_name=low_name,
            strength_model=strength,
        )
        model_high, model_low = hid, lid
    length = wan_length(seconds)
    if source == "t2v":
        g["7"] = _loader(
            "EmptyHunyuanLatentVideo",
            width=int(width),
            height=int(height),
            length=length,
            batch_size=1,
        )
        latent_from = ["7", 0]
    else:
        g["8"] = _loader("LoadImage", image=start_image)
        g["7"] = _loader(
            "WanImageToVideo",
            positive=["2", 0],
            negative=["3", 0],
            vae=["6", 0],
            width=int(width),
            height=int(height),
            length=length,
            batch_size=1,
            start_image=["8", 0],
        )
        latent_from = ["7", 2]
    positive = ["7", 0] if source != "t2v" else ["2", 0]
    negative = ["7", 1] if source != "t2v" else ["3", 0]
    g["10"] = _loader(
        "KSamplerAdvanced",
        model=[model_high, 0],
        add_noise="enable",
        noise_seed=int(seed),
        steps=steps,
        cfg=cfg,
        sampler_name="euler",
        scheduler="simple",
        positive=positive,
        negative=negative,
        latent_image=latent_from,
        start_at_step=0,
        end_at_step=steps // 2,
        return_with_leftover_noise="enable",
    )
    g["11"] = _loader(
        "KSamplerAdvanced",
        model=[model_low, 0],
        add_noise="disable",
        noise_seed=int(seed),
        steps=steps,
        cfg=cfg,
        sampler_name="euler",
        scheduler="simple",
        positive=positive,
        negative=negative,
        latent_image=["10", 0],
        start_at_step=steps // 2,
        end_at_step=steps,
        return_with_leftover_noise="disable",
    )
    g["12"] = _loader("VAEDecode", samples=["11", 0], vae=["6", 0])
    g["13"] = _loader(
        "CreateVideo",
        images=["12", 0],
        fps=float(WAN_FPS),
    )
    g["14"] = _loader(
        "SaveVideo",
        video=["13", 0],
        filename_prefix=filename_prefix,
        format="mp4",
        codec="h264",
    )
    assert_wan_graph(g, source=source)
    return g


def assert_wan_graph(graph: dict[str, Any], *, source: str) -> None:
    names: list[str] = []
    classes: list[str] = []
    for node in graph.values():
        classes.append(str(node.get("class_type") or ""))
        inputs = node.get("inputs") or {}
        for key in ("clip_name", "unet_name", "vae_name", "lora_name", "type"):
            if key in inputs:
                names.append(str(inputs[key]))
    blob = " ".join(names).lower()
    if "umt5" not in blob or WAN_TEXT_ENCODER_TYPE not in blob:
        raise EpisodeError("Wan graph must use the umt5 text encoder")
    for marker in H3_WEIGHT_MARKERS:
        if marker in blob:
            raise EpisodeError(f"Wan graph contains an H3 weight marker: {marker}")
    if any(token in blob for token in ("pose", "animate", "dwpose")):
        raise EpisodeError("Wan episode graph must not use Animate / pose lock")
    if any("Animate" in name or "DWPose" in name for name in classes):
        raise EpisodeError("Wan episode graph must not use Animate / pose lock")
    has_image = any(node.get("class_type") == "LoadImage" for node in graph.values())
    if source == "t2v" and has_image:
        raise EpisodeError("T2V graph must not load a start image")
    if source in ("chain", "still") and not has_image:
        raise EpisodeError("I2V graph must load the previous last frame")


def _now_status_id(ep: dict[str, Any]) -> str:
    return str(ep.get("slug") or "episode")


def run_wan_episode(
    ep: dict[str, Any],
    root: Path | str,
    *,
    loras_dir: Path | str | None = None,
    comfy_dir: Path | str | None = None,
    dry_run: bool = False,
    fresh: bool = False,
    port: int = PORT,
    poster: Any = post_prompt,
    waiter: Any = wait_prompt,
    **prepare_kwargs: Any,
) -> Path:
    """Prepare with the H3 dropdowns, draw with Wan, then the existing HUD stitch.

    dry_run writes synthetic clips so the stitch can be checked without a GPU.
    A real generate is the Colab cell the human runs.
    """
    root = Path(root)
    _reject_google_drive(root)
    ensure_episode_tree(root)
    ep = prepare_episode(ep, **prepare_kwargs)
    canvas = canvas_for(ep)
    loras = Path(loras_dir) if loras_dir else None
    shots = {row["id"]: row for row in plan_wan_shots(ep, loras)}
    status = load_status(root)
    status.update({
        "slug": ep.get("slug"),
        "renderer": "wan2.2",
        "canvas": f"{canvas[0]}x{canvas[1]}",
        "store": str(root),
        "dry_run": bool(dry_run),
    })
    save_status(root, status)
    beats = ep.get("beats") or []
    for idx, beat in enumerate(beats):
        if not isinstance(beat, dict) or is_ui_beat(beat):
            continue
        bid = str(beat["id"])
        raw_out = root / "raw" / f"{bid}.mp4"
        if raw_out.is_file() and not fresh:
            status.setdefault("beats", {}).setdefault(bid, {})["state"] = "done"
            continue
        shot = shots[bid]
        source = shot["source"]
        start_name = None
        if shot["start_image"]:
            prev_clip, at = previous_footage(ep, idx, root, root / "raw")
            frame = root / "input" / f"{bid}-last.jpg"
            extract_frame(prev_clip, frame, at_s=at)
            start_name = frame.name
        prompt = wan_beat_prompt(ep, beat)
        (root / "logs" / f"{bid}.prompt.txt").write_text(prompt, encoding="utf-8")
        status.setdefault("beats", {})[bid] = {"state": "running", "source": source, "renderer": "wan2.2"}
        save_status(root, status)
        if dry_run:
            hue = (idx * 37) % 255
            synthetic_clip(
                raw_out,
                seconds=float(shot["seconds"]),
                canvas=canvas,
                color=f"0x{hue:02x}{(120 + idx * 13) % 255:02x}{(80 + idx * 17) % 255:02x}",
            )
        else:
            graph = build_wan_graph(
                source=source,
                prompt=prompt,
                width=canvas[0],
                height=canvas[1],
                seconds=float(shot["seconds"]),
                seed=int((ep.get("render") or {}).get("seed") or 42) + idx,
                filename_prefix=f"video/wan_ep_{_now_status_id(ep)}_{bid}",
                start_image=start_name,
                slots=shot["slots"],
                use_lightx2v=False,
            )
            (root / "logs" / f"{bid}.wan.json").write_text(
                __import__("json").dumps(graph, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            if comfy_dir is None:
                raise EpisodeError("Wan generate needs ComfyUI. The human runs that cell; this call has no comfy_dir.")
            res, err = poster(graph, port)
            if err or not (res and res.get("prompt_id")):
                raise EpisodeError(f"{bid}: Wan prompt rejected: {err or res}")
            ok, payload = waiter(res["prompt_id"], port)
            if not ok:
                raise EpisodeError(f"{bid}: Wan failed: {payload}")
            videos = collect_output_videos(payload, Path(comfy_dir) / "output")
            if not videos:
                raise EpisodeError(f"{bid}: Wan produced no mp4")
            shutil.copy2(videos[-1], raw_out)
        status["beats"][bid].update({"state": "done", "raw": str(raw_out), "start_image": bool(start_name)})
        save_status(root, status)
    final = finish_episode(ep, root)
    status["final"] = str(final)
    save_status(root, status)
    return final
