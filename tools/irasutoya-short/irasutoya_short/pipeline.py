"""台本、素材、音声、口パク、書き出しまでを通す。"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import numpy as np
from PIL import Image

from irasutoya_short.audio import fit_length, mix_tracks, read_wav, write_wav
from irasutoya_short.constants import FPS, MAX_DURATION, MIN_DURATION, SAMPLE_RATE
from irasutoya_short.irasutoya import collect_assets
from irasutoya_short.layout import analyze_screenshots, default_layout
from irasutoya_short.lipsync import mouth_envelope
from irasutoya_short.render import render_movie
from irasutoya_short.revise import apply_note
from irasutoya_short.scriptgen import generate_script
from irasutoya_short.sfx import bgm_loop, make_sfx
from irasutoya_short.sprites import load_rgba, mark_mouth, mouth_anchor
from irasutoya_short.tts import Speaker

TERMS = {
    "irasutoya": (
        "いらすとやは1つの制作物につき20点まで商用無料（同じ絵の重複は1点）。"
        "21点以上の商用利用は有償。クレジット表記は不要。"
        "素材そのものの再配布や、イラストを主体にした商品化は不可。"
        "背景はコード描画にして点数をキャラと小物に使っている。"
    ),
    "voicevox": (
        "使った声はクレジットが要る。"
        "四国めたん、白上虎太郎、玄野武宏、剣崎雌雄はクレジットを書けば商用可。"
        "青山龍星は個人事業・法人だと事前許可が要るので使っていない。"
        "効果音とBGMはこの場で合成したオリジナルなのでクレジット不要。"
    ),
}


def default_settings() -> dict:
    return {
        "speed": 1.28,
        "hook_speed": 1.48,
        "telop_scale": 1.0,
        "sfx_gain": 0.22,
        "bgm_gain": 0.045,
        "mouth_gain": 1.0,
        "bgm": True,
    }


def make(brief_path: Path, work_dir: Path, out_path: Path, screenshots: list[Path] | None = None, bgm: bool = True) -> dict:
    brief = json.loads(Path(brief_path).read_text(encoding="utf-8"))
    work_dir.mkdir(parents=True, exist_ok=True)
    script = generate_script(brief)
    shots = list(screenshots or [])
    layout = analyze_screenshots(shots) if shots else default_layout()
    asset_dir = work_dir / "assets"
    report = collect_assets(script["asset_ids"], asset_dir, brief.get("asset_urls"))
    _debug_mouths(report["accepted"], asset_dir / "debug_mouth")
    project = {
        "brief": brief,
        "title": script["title"],
        "punchline": script["punchline"],
        "scenes": script["scenes"],
        "credits": script["credits"],
        "asset_ids": script["asset_ids"],
        "asset_report": report,
        "asset_paths": {item["id"]: item["path"] for item in report["accepted"]},
        "layout": layout,
        "settings": default_settings(),
        "terms": TERMS,
    }
    project["settings"]["bgm"] = bgm
    speaker = Speaker()
    _synthesize(project, speaker, work_dir / "audio")
    _persist(project, work_dir / "project.json")
    _render_from_project(project, work_dir, out_path)
    summary = _summary(project, out_path)
    (work_dir / "REPORT.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


def revise(work_dir: Path, note: str, out_path: Path) -> dict:
    project = json.loads((work_dir / "project.json").read_text(encoding="utf-8"))
    changes = apply_note(project, note)
    speed_changed = any("テンポ" in c for c in changes)
    text_changed = any("分けた" in c for c in changes)
    if speed_changed or text_changed:
        _synthesize(project, Speaker(), work_dir / "audio")
    _persist(project, work_dir / "project.json")
    _render_from_project(project, work_dir, out_path)
    summary = _summary(project, out_path)
    summary["revise"] = changes
    (work_dir / "REPORT.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


def _synthesize(project: dict, speaker: Speaker, audio_dir: Path, depth: int = 0) -> None:
    audio_dir.mkdir(parents=True, exist_ok=True)
    settings = project["settings"]
    for scene in project["scenes"]:
        speed = settings["hook_speed"] if scene["role"] == "hook" else settings["speed"]
        samples = speaker.speak(scene["text"], int(scene["style_id"]), float(speed))
        path = audio_dir / f"scene_{int(scene['id']):02d}.wav"
        write_wav(path, samples)
        scene["voice_path"] = str(path)
        scene["voice_seconds"] = round(len(samples) / SAMPLE_RATE, 3)
        tail = 0.16 if scene["text"] else 0.0
        scene["duration"] = max(scene["voice_seconds"] + tail, 2.0 if scene["role"] == "credit" else 0.8)
    total = sum(float(s["duration"]) for s in project["scenes"])
    if total > MAX_DURATION and depth < 2:
        factor = (MAX_DURATION - 1.0) / total
        settings["speed"] = round(float(settings["speed"]) / factor, 3)
        settings["hook_speed"] = round(float(settings["hook_speed"]) / factor, 3)
        _synthesize(project, speaker, audio_dir, depth + 1)
        return
    if total < MIN_DURATION:
        extra = (MIN_DURATION + 0.6 - total) / len(project["scenes"])
        for scene in project["scenes"]:
            scene["duration"] = float(scene["duration"]) + extra
    for scene in project["scenes"]:
        frames = max(1, int(round(float(scene["duration"]) * FPS)))
        scene["duration"] = frames / FPS


def _render_from_project(project: dict, work_dir: Path, out_path: Path) -> None:
    _attach_performance(project)
    project["audio"] = _mix(project)
    project["chunk_seconds"] = 6
    render_movie(project, out_path, work_dir / "preview")
    project.pop("audio", None)
    for scene in project["scenes"]:
        scene.pop("envelope", None)
        scene.pop("_voice", None)


def _attach_performance(project: dict) -> None:
    for scene in project["scenes"]:
        voice = read_wav(scene["voice_path"])
        nframes = int(round(float(scene["duration"]) * FPS))
        voice_frames = min(nframes, max(1, int(round(len(voice) / SAMPLE_RATE * FPS))))
        env = mouth_envelope(voice, voice_frames)
        if len(env) < nframes:
            env = np.concatenate([env, np.zeros(nframes - len(env), dtype=np.float32)])
        scene["envelope"] = env[:nframes]
        scene["_voice"] = voice


def _mix(project: dict) -> np.ndarray:
    settings = project["settings"]
    pieces: list[np.ndarray] = []
    bed = bgm_loop(80.0) if settings.get("bgm", True) else None
    offset = 0
    for scene in project["scenes"]:
        n = int(round(float(scene["duration"]) * SAMPLE_RATE))
        voice = fit_length(scene["_voice"], n)
        sfx = make_sfx(scene["sfx"])
        bgm_slice = None if bed is None else bed[offset : offset + n]
        pieces.append(mix_tracks(voice, sfx, float(settings["sfx_gain"]), bgm_slice, float(settings["bgm_gain"])))
        offset += n
    audio = np.concatenate(pieces) if pieces else np.zeros(1, dtype=np.float32)
    mix_path = Path(project["scenes"][0]["voice_path"]).parent / "mix.wav"
    write_wav(mix_path, audio)
    return audio


def _debug_mouths(accepted: list[dict], dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    for item in accepted:
        if item["kind"] != "person":
            continue
        rgba = load_rgba(item["path"])
        anchor = mouth_anchor(rgba)
        if anchor is None:
            Image.fromarray(rgba, "RGBA").save(dest / f"{item['id']}.png")
            continue
        Image.fromarray(mark_mouth(rgba, anchor.x, anchor.y), "RGBA").save(dest / f"{item['id']}.png")


def _persist(project: dict, path: Path) -> None:
    data = json.loads(json.dumps(_public(project), ensure_ascii=False))
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _public(project: dict) -> dict:
    scenes = []
    for scene in project["scenes"]:
        item = {k: v for k, v in scene.items() if k not in ("envelope", "_voice")}
        scenes.append(item)
    return {
        "title": project.get("title"),
        "punchline": project.get("punchline"),
        "brief": project.get("brief"),
        "scenes": scenes,
        "credits": project.get("credits"),
        "asset_ids": project.get("asset_ids"),
        "asset_report": project.get("asset_report"),
        "asset_paths": project.get("asset_paths"),
        "layout": project.get("layout"),
        "settings": project.get("settings"),
        "terms": project.get("terms"),
        "notes": project.get("notes", []),
    }


def _summary(project: dict, out_path: Path) -> dict:
    duration = round(sum(float(s["duration"]) for s in project["scenes"]), 2)
    accepted = project["asset_report"]["accepted"]
    return {
        "out": str(out_path),
        "duration_sec": duration,
        "scene_count": len(project["scenes"]),
        "asset_count": len(accepted),
        "asset_limit": 20,
        "assets": [
            {"id": a["id"], "title": a["title"], "alt": a["alt"], "url": a["url"]}
            for a in accepted
        ],
        "rejected_count": len(project["asset_report"]["rejected"]),
        "credits": project["credits"],
        "terms": TERMS,
        "within_25_40": MIN_DURATION <= duration <= MAX_DURATION,
    }


def copy_out(src: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
