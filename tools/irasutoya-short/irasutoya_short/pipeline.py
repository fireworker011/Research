"""台本、素材、音声、口パク、書き出しまでを通す。"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import numpy as np
from PIL import Image

from irasutoya_short.audio import fit_length, mix_tracks, read_wav, samples_for_frames, write_wav
from irasutoya_short.constants import FPS, MAX_DURATION, MIN_DURATION, SAMPLE_RATE
from irasutoya_short.irasutoya import collect_assets
from irasutoya_short.layout import analyze_screenshots, default_layout
from irasutoya_short.lipsync import mouth_envelope
from irasutoya_short.render import render_movie
from irasutoya_short.revise import apply_note
from irasutoya_short.scriptgen import generate_script
from irasutoya_short.sfx import bgm_loop, make_sfx
from irasutoya_short.sprites import load_rgba, mark_mouth, mouth_anchor
from irasutoya_short.stylevar import fit_scene_durations
from irasutoya_short.templates import scale_speeds, scene_speed, scene_tail, settings_for, telop_style
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
    return settings_for("sukatto")


def make(
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
        speed = scene_speed(settings, scene)
        samples = speaker.speak(scene["text"], int(scene["style_id"]), float(speed))
        path = audio_dir / f"scene_{int(scene['id']):02d}.wav"
        write_wav(path, samples)
        scene["voice_path"] = str(path)
        scene["voice_seconds"] = round(len(samples) / SAMPLE_RATE, 3)
        floor = 2.0 if scene["role"] == "credit" else float(scene.get("hold") or 0.8)
        scene["duration"] = max(scene["voice_seconds"] + scene_tail(settings, scene), floor)
    if project.get("style_axes"):
        status = fit_scene_durations(project)
        total = sum(float(scene["duration"]) for scene in project["scenes"])
        if status == "short" and depth < 6:
            voice = sum(
                float(scene["voice_seconds"])
                for scene in project["scenes"]
                if scene.get("role") != "credit"
            )
            need = 16.0 - total
            if voice <= 0.2 or need <= 0.05:
                raise RuntimeError(f"尺を15秒まで戻せません: {project.get('style_signature')}")
            factor = max(0.5, voice / (voice + need))
            scale_speeds(settings, factor, factor)
            _synthesize(project, speaker, audio_dir, depth + 1)
            return
        if status == "speedup" and depth < 6:
            scale_speeds(settings, 1.16, 1.12)
            _synthesize(project, speaker, audio_dir, depth + 1)
            return
        if status not in ("ok", "retarget"):
            raise RuntimeError(f"尺が署名に合いません: {status} {project.get('style_signature')}")
        return
    total = sum(float(s["duration"]) for s in project["scenes"])
    if total > MAX_DURATION and depth < 2:
        boost = total / (MAX_DURATION - 1.0)
        scale_speeds(settings, boost, boost)
        _synthesize(project, speaker, audio_dir, depth + 1)
        return
    if total < MIN_DURATION:
        _add_slack(project["scenes"], (MIN_DURATION + 0.6) - total, str(project.get("template") or "sukatto"))
    for scene in project["scenes"]:
        frames = max(1, int(round(float(scene["duration"]) * FPS)))
        scene["duration"] = frames / FPS


def _render_from_project(project: dict, work_dir: Path, out_path: Path, *, preview: bool = True) -> None:
    _attach_performance(project)
    project["audio"] = _mix(project)
    render_movie(project, out_path, work_dir / "preview" if preview else None)
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
        lead_frames = int(round(float(scene.get("lead") or 0) * FPS))
        if lead_frames > 0:
            env = np.concatenate([np.zeros(lead_frames, dtype=np.float32), env])
        if len(env) < nframes:
            env = np.concatenate([env, np.zeros(nframes - len(env), dtype=np.float32)])
        scene["envelope"] = env[:nframes]
        scene["_voice"] = voice


def _delay_voice(voice: np.ndarray, n: int, lead: float) -> np.ndarray:
    lead_n = int(round(lead * SAMPLE_RATE))
    if lead_n <= 0:
        return fit_length(voice, n)
    out = np.zeros(n, dtype=np.float32)
    start = min(max(lead_n, 0), n)
    take = min(int(voice.shape[0]), n - start)
    if take > 0:
        out[start : start + take] = voice[:take]
    return out


def _mix(project: dict) -> np.ndarray:
    settings = project["settings"]
    pieces: list[np.ndarray] = []
    kind = str(settings.get("bgm_kind") or "B4")
    use_bgm = bool(settings.get("bgm", True)) and kind != "B1"
    total_sec = sum(float(scene["duration"]) for scene in project["scenes"])
    bed = bgm_loop(max(80.0, total_sec + 2.0), kind) if use_bgm else None
    offset = 0
    for scene in project["scenes"]:
        nframes = max(1, int(round(float(scene["duration"]) * FPS)))
        n = samples_for_frames(nframes)
        voice = _delay_voice(scene["_voice"], n, float(scene.get("lead") or 0))
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
        "template": project.get("template"),
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
        "telop_style": project.get("telop_style"),
        "terms": project.get("terms"),
        "notes": project.get("notes", []),
        "style_signature": project.get("style_signature"),
        "style_axes": project.get("style_axes"),
        "style_cast": project.get("style_cast"),
        "style_used_assets": project.get("style_used_assets"),
    }


def _summary(project: dict, out_path: Path) -> dict:
    duration = round(sum(float(s["duration"]) for s in project["scenes"]), 2)
    accepted = project["asset_report"]["accepted"]
    return {
        "out": str(out_path),
        "template": project.get("template"),
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
        "within_20_30": MIN_DURATION <= duration <= MAX_DURATION,
        "style_signature": project.get("style_signature") or "",
        "irasutoya_count": len(project.get("style_used_assets") or []),
    }


def _add_slack(scenes: list[dict], slack: float, template: str) -> None:
    if slack <= 0 or not scenes:
        return
    weights = [_slack_weight(scene, template) for scene in scenes]
    total = sum(weights) or float(len(scenes))
    for scene, weight in zip(scenes, weights):
        scene["duration"] = float(scene["duration"]) + slack * weight / total


def _slack_weight(scene: dict, template: str) -> float:
    if template == "sukatto":
        return 1.0
    tone = str(scene.get("tone") or scene.get("role") or "")
    if tone == "item":
        return 0.2
    if scene.get("role") in ("close", "credit"):
        return 2.0
    if scene.get("role") == "hook":
        return 1.4
    return 1.0


def copy_out(src: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
