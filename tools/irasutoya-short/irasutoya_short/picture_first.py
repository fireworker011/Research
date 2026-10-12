"""口パクの絵を先に固定し、そのあと声を絵の区間へ置く。

ツール本体は声の長さから尺を決める。ここでは仮の声で尺と口の開きを決め、
絵を書き出したあと、話速 0.9〜1.1 倍と無音の間だけで声を合わせる。
絵のフレームは切り直さない。
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from irasutoya_short.audio import samples_for_frames, write_wav
from irasutoya_short.constants import FPS, SAMPLE_RATE
from irasutoya_short.irasutoya import collect_assets
from irasutoya_short.layout import analyze_screenshots, default_layout
from irasutoya_short.pipeline import (
    TERMS,
    _attach_performance,
    _debug_mouths,
    _mix,
    _persist,
    _summary,
    _synthesize,
)
from irasutoya_short.render import mux_voice, render_movie
from irasutoya_short.scriptgen import generate_script
from irasutoya_short.templates import scene_speed, settings_for, telop_style
from irasutoya_short.tts import Speaker

SPEED_MIN = 0.9
SPEED_MAX = 1.1


def make_picture_first(
    brief_path: Path,
    work_dir: Path,
    out_path: Path,
    screenshots: list[Path] | None = None,
    bgm: bool = True,
    template: str = "",
) -> dict:
    brief = json.loads(Path(brief_path).read_text(encoding="utf-8"))
    if template:
        brief = dict(brief)
        brief["template"] = template
    work_dir.mkdir(parents=True, exist_ok=True)
    script = generate_script(brief)
    shots = list(screenshots or [])
    layout = analyze_screenshots(shots) if shots else default_layout()
    style = telop_style(script["template"])
    if not shots:
        layout["telop_y_ratio"] = float(style["y_ratio"])
    asset_dir = work_dir / "assets"
    report = collect_assets(script["asset_ids"], asset_dir, brief.get("asset_urls"))
    _debug_mouths(report["accepted"], asset_dir / "debug_mouth")
    project = {
        "brief": brief,
        "template": script["template"],
        "title": script["title"],
        "punchline": script["punchline"],
        "scenes": script["scenes"],
        "credits": script["credits"],
        "asset_ids": script["asset_ids"],
        "asset_report": report,
        "asset_paths": {item["id"]: item["path"] for item in report["accepted"]},
        "layout": layout,
        "settings": settings_for(script["template"]),
        "telop_style": style,
        "terms": TERMS,
        "picture_first": True,
    }
    project["settings"]["bgm"] = bgm
    speaker = Speaker()
    audio_dir = work_dir / "audio"
    _synthesize(project, speaker, audio_dir)
    _attach_performance(project)
    locks = _lock_pictures(project)
    pictures = work_dir / "pictures.mp4"
    render_movie(project, pictures, work_dir / "mouth", pictures_only=True)
    fit_voice_to_lock(project, speaker, audio_dir, locks)
    project["audio"] = _mix(project)
    mix_path = audio_dir / "mix.wav"
    mux_voice(pictures, mix_path, out_path)
    project.pop("audio", None)
    for scene in project["scenes"]:
        scene.pop("envelope", None)
        scene.pop("_voice", None)
    _persist(project, work_dir / "project.json")
    summary = _summary(project, out_path)
    summary["picture_first"] = True
    summary["voice_fit"] = [
        {
            "id": int(scene["id"]),
            "voice_rate": scene.get("voice_rate"),
            "voice_rate_factor": scene.get("voice_rate_factor"),
            "voice_pause_sec": scene.get("voice_pause_sec"),
        }
        for scene in project["scenes"]
    ]
    (work_dir / "REPORT.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


def _lock_pictures(project: dict) -> dict[int, dict]:
    """仮の声から、シーンの長さと口の開きを固定する。"""
    locks: dict[int, dict] = {}
    for scene in project["scenes"]:
        env = np.asarray(scene["envelope"], dtype=np.float32).copy()
        scene["envelope"] = env
        scene["picture_locked"] = True
        locks[int(scene["id"])] = {
            "duration": float(scene["duration"]),
            "envelope": env.copy(),
            "voice_samples": int(len(scene["_voice"])),
        }
    return locks


def speed_factor(spoken_len: int, target_len: int) -> float:
    """話速の倍率。1より大きいと短くなる。0.9〜1.1 に収める。"""
    if spoken_len <= 0 or target_len <= 0:
        return 1.0
    raw = spoken_len / float(target_len)
    return float(min(SPEED_MAX, max(SPEED_MIN, raw)))


def fit_voice_to_lock(project: dict, speaker: Speaker, audio_dir: Path, locks: dict[int, dict]) -> None:
    """固定した口の区間へ声を置く。尺と口の開きは変えない。"""
    settings = project["settings"]
    audio_dir.mkdir(parents=True, exist_ok=True)
    for scene in project["scenes"]:
        lock = locks[int(scene["id"])]
        base = float(scene_speed(settings, scene))
        target = int(lock["voice_samples"])
        samples = np.asarray(scene["_voice"], dtype=np.float32)
        factor = 1.0
        if target > 0 and len(samples) != target:
            factor = speed_factor(len(samples), target)
            if abs(factor - 1.0) >= 0.01:
                samples = np.asarray(
                    speaker.speak(str(scene["text"]), int(scene["style_id"]), base * factor),
                    dtype=np.float32,
                )
        nframes = max(1, int(round(float(lock["duration"]) * FPS)))
        slot = samples_for_frames(nframes)
        placed = np.zeros(slot, dtype=np.float32)
        use = samples[:slot]
        placed[: len(use)] = use
        pause = max(0, slot - len(use))
        path = audio_dir / f"scene_{int(scene['id']):02d}.wav"
        write_wav(path, placed)
        scene["voice_path"] = str(path)
        scene["voice_seconds"] = round(len(samples) / SAMPLE_RATE, 3)
        scene["_voice"] = placed
        scene["duration"] = float(lock["duration"])
        scene["envelope"] = np.asarray(lock["envelope"], dtype=np.float32).copy()
        scene["picture_locked"] = True
        scene["voice_rate"] = round(base * factor, 3)
        scene["voice_rate_factor"] = round(factor, 3)
        scene["voice_pause_sec"] = round(pause / SAMPLE_RATE, 3)
