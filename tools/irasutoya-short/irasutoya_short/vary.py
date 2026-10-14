"""未公開の金メモ #15 から #61 を、署名ごとに違う見た目で書き出す。投稿はしない。"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

from irasutoya_short.pipeline import _persist, _render_from_project, _summary, _synthesize
from irasutoya_short.qa import dead_air
from irasutoya_short.sprites import load_rgba, mouth_levels
from irasutoya_short.stylevar import (
    apply_signature,
    assign_unpublished,
    check_signature,
    gaps_ok,
    kane_published_history,
    length_code_for,
    length_ok,
    load_jobs,
    parse_signature,
    published_signatures,
    repair_signature,
    result_row,
    seed_log_rows,
    write_log,
)
from irasutoya_short.templates import settings_for
from irasutoya_short.tts import Speaker

ROOT = Path(__file__).resolve().parents[3]
RENDERER = "stills-vary-2"
POOLS = (
    Path("/tmp/irasu-rest/15-furusato-onestop/assets"),
    Path("/tmp/irasu-b4/35-juminzei-qa/assets"),
    Path("/tmp/irasu-b6/50-furikomi-kouza/assets"),
    Path("/tmp/irasu-b5/47-kinmemo-paper/assets"),
)


def _pool_file(name: str) -> Path | None:
    for root in POOLS:
        path = root / f"{name}.png"
        if path.is_file():
            return path
    return None


def ensure_assets(project: dict, work: Path) -> None:
    dest = work / "assets"
    dest.mkdir(parents=True, exist_ok=True)
    found: dict[str, str] = {}
    for key, raw in list((project.get("asset_paths") or {}).items()):
        src = Path(raw)
        if not src.is_file():
            alt = _pool_file(key)
            if alt is None:
                continue
            src = alt
        target = dest / f"{key}.png"
        if src.resolve() != target.resolve():
            shutil.copy2(src, target)
        found[key] = str(target)
    for key in ("hero_trouble", "hero_tired", "hero_angry", "hero_smile", "rival_smug", "boss_angry"):
        if key in found:
            continue
        alt = _pool_file(key)
        if alt is None:
            continue
        target = dest / f"{key}.png"
        shutil.copy2(alt, target)
        found[key] = str(target)
    if not found:
        raise RuntimeError("いらすとやの画像がありません")
    project["asset_paths"] = found


def _spoken(project: dict) -> list[tuple[int, str, str]]:
    rows = []
    for scene in project["scenes"]:
        if scene.get("role") == "credit":
            continue
        rows.append((int(scene["id"]), str(scene.get("text") or ""), str(scene.get("telop") or "")))
    return rows


def _ffprobe(path: Path) -> tuple[float, int, int]:
    duration = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
        text=True,
    )
    size = subprocess.check_output(
        [
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries", "stream=width,height", "-of", "csv=p=0", str(path),
        ],
        text=True,
    )
    width, height = size.strip().split(",")
    return float(duration.strip()), int(width), int(height)


def _grab(mp4: Path, dest: Path, seconds: float) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{seconds:.3f}", "-i", str(mp4), "-frames:v", "1", "-q:v", "3", str(dest)],
        check=True,
    )


def _add_upload_credit(folder: Path) -> None:
    path = folder / "UPLOAD.md"
    if not path.is_file():
        return
    text = path.read_text(encoding="utf-8")
    if "イラスト：いらすとや" in text:
        return
    lines = text.splitlines()
    indexes = [index for index, line in enumerate(lines) if line.startswith("VOICEVOX:")]
    if indexes:
        lines.insert(indexes[-1] + 1, "イラスト：いらすとや")
    else:
        lines.append("イラスト：いらすとや")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _ahead(video_id: str) -> list[tuple]:
    rows = json.loads((ROOT / "affiliate-shorts" / "style-plan.json").read_text(encoding="utf-8"))
    ids = [str(row["video_id"]) for row in rows]
    if video_id not in ids:
        return []
    start = ids.index(video_id) + 1
    ahead = []
    for row in rows[start : start + 5]:
        ahead.append((parse_signature(row["signature"]), True))
    return ahead


def _history_before(video_id: str) -> list:
    rows = json.loads((ROOT / "affiliate-shorts" / "style-plan.json").read_text(encoding="utf-8"))
    history = kane_published_history()
    for row in rows:
        if str(row["video_id"]) == video_id:
            break
        history.append(parse_signature(row["signature"]))
    return history


def render_job(folder: str, signature_text: str) -> dict:
    folder_path = Path(folder)
    marker_path = folder_path / "style.json"
    if marker_path.is_file():
        cached = json.loads(marker_path.read_text(encoding="utf-8"))
        if cached.get("renderer") == RENDERER and cached.get("signature") == signature_text and (folder_path / "out.mp4").is_file():
            return cached
    signature = parse_signature(signature_text)
    project = json.loads((folder_path / "project.json").read_text(encoding="utf-8"))
    spoken = _spoken(project)
    work = Path("/tmp/irasu-vary") / folder_path.name
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    ensure_assets(project, work)
    project["settings"] = settings_for(str(project["template"]))
    apply_signature(project, signature)
    if _spoken(project) != spoken:
        raise RuntimeError(f"{folder_path.name} の台詞が変わりました")
    credit = next(scene["telop"] for scene in project["scenes"] if scene.get("role") == "credit")
    if "イラスト：いらすとや" not in credit or "VOICEVOX:" not in credit:
        raise RuntimeError(f"{folder_path.name} のクレジットが足りません")
    _synthesize(project, Speaker(), work / "audio")
    total = sum(float(scene["duration"]) for scene in project["scenes"])
    code = length_code_for(total)
    if code is None:
        raise RuntimeError(f"{folder_path.name} の尺 {total:.2f} が長さの枠に入りません")
    if code != signature.L:
        video_id = folder_path.name.split("-", 1)[0]
        signature = repair_signature(
            signature,
            _history_before(video_id),
            published_signatures(),
            code,
            _ahead(video_id),
        )
        apply_signature(project, signature)
    if not length_ok(total, signature.L):
        raise RuntimeError(f"{folder_path.name} の尺 {total:.2f} が {signature.L} に入りません")
    if not gaps_ok(project["scenes"]):
        raise RuntimeError(f"{folder_path.name} に1.5秒を超える隙間があります")
    out = work / "out.mp4"
    _render_from_project(project, work, out, preview=False)
    probed, width, height = _ffprobe(out)
    if (width, height) != (1080, 1920):
        raise RuntimeError(f"{folder_path.name} の画面が {width}x{height}")
    if abs(probed - total) > 0.15:
        raise RuntimeError(f"{folder_path.name} の ffprobe {probed:.2f} とシーン合計 {total:.2f} が違います")
    air = dead_air(out)
    if air:
        raise RuntimeError(f"{folder_path.name} の無音か静止: {', '.join(air)}")
    used = list(project.get("style_used_assets") or [])
    if len(used) > 20 or (signature.A == "A6" and len(used) > 5):
        raise RuntimeError(f"{folder_path.name} のいらすとやが {len(used)} 枚です")
    sample = load_rgba(next(iter(project["asset_paths"].values())))
    levels, _anchor = mouth_levels(sample)
    if any(not np.array_equal(levels[0], frame) for frame in levels[1:]):
        raise RuntimeError(f"{folder_path.name} に口の重ね絵があります")
    shutil.copy2(out, folder_path / "out.mp4")
    stills = folder_path / "stills"
    for name, ratio in (("01.jpg", 0.18), ("02.jpg", 0.55), ("03.jpg", 0.82)):
        _grab(out, stills / name, max(0.2, probed * ratio))
    _grab(out, folder_path / "thumb.jpg", max(0.2, probed * 0.32))
    summary = _summary(project, folder_path / "out.mp4")
    summary["within_style_length"] = True
    summary["style_thumb"] = signature.thumb()
    (folder_path / "REPORT.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    _persist(project, folder_path / "project.json")
    _add_upload_credit(folder_path)
    payload = {
        "renderer": RENDERER,
        "video_id": folder_path.name.split("-", 1)[0],
        "signature": signature.text(),
        "thumb": signature.thumb(),
        "duration": round(total, 2),
        "irasutoya_count": len(used),
        "credit_ok": "yes",
        "bgm": signature.B,
    }
    marker_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"done {payload['video_id']} {signature.text()} {payload['duration']}s assets={len(used)}", flush=True)
    return payload


def write_plan(root: Path, jobs: list[dict], signatures) -> None:
    rows = [
        {"video_id": job["video_id"], "folder": job["folder"], "signature": signature.text(), "thumb": signature.thumb()}
        for job, signature in zip(jobs, signatures)
    ]
    path = root / "affiliate-shorts" / "style-plan.json"
    path.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def update_samples(root: Path, durations: dict[str, float]) -> None:
    path = root / "affiliate-shorts" / "SAMPLES.md"
    text = path.read_text(encoding="utf-8")
    note = "各動画の構図・配色・テロップ・フォント・テンポ・BGM・尺は `style-plan.json` と `style-log.csv`。同じ型の使い回しはしていない。公開済みの #01・#13・#14 は書き直していない。"
    if "style-log.csv" not in text:
        text = text.replace(
            "投稿はしない。CTA も URL も入れてない。",
            "投稿はしない。CTA も URL も入れてない。\n\n" + note,
        )
    for folder, seconds in durations.items():
        rel = str(Path(folder).relative_to(root / "affiliate-shorts"))
        pattern = rf"(`{re.escape(rel)}`(?: \|[^|\n]+){{2}} \|) [0-9]+\.[0-9]+ \|"
        updated, count = re.subn(pattern, rf"\1 {seconds:.2f} |", text, count=1)
        if count != 1:
            raise RuntimeError(f"SAMPLES.md の尺を更新できません: {rel}")
        text = updated
    path.write_text(text, encoding="utf-8")


def _child_env() -> tuple[str, dict[str, str]]:
    package = str(ROOT / "tools" / "irasutoya-short")
    env = os.environ.copy()
    env["PYTHONPATH"] = package
    return package, env


def load_plan(root: Path, jobs: list[dict]):
    path = root / "affiliate-shorts" / "style-plan.json"
    if not path.is_file():
        signatures = assign_unpublished(jobs)
        write_plan(root, jobs, signatures)
        return signatures
    rows = json.loads(path.read_text(encoding="utf-8"))
    by_id = {row["video_id"]: parse_signature(row["signature"]) for row in rows}
    return [by_id[job["video_id"]] for job in jobs]


def render_all(root: Path, workers: int = 3, only: set[str] | None = None) -> None:
    jobs = load_jobs(root)
    signatures = load_plan(root, jobs)
    selected = [(job, signature) for job, signature in zip(jobs, signatures) if only is None or job["video_id"] in only]
    done: dict[str, dict] = {}
    errors: list[str] = []
    cwd, env = _child_env()
    pending = list(selected)
    running: list[tuple[dict, subprocess.Popen[bytes]]] = []
    while pending or running:
        while pending and len(running) < workers:
            job, signature = pending.pop(0)
            proc = subprocess.Popen(
                [sys.executable, "-m", "irasutoya_short.vary", "--job", str(root / job["folder"]), signature.text()],
                cwd=cwd,
                env=env,
            )
            running.append((job, proc))
        still: list[tuple[dict, subprocess.Popen[bytes]]] = []
        for job, proc in running:
            code = proc.poll()
            if code is None:
                still.append((job, proc))
                continue
            marker = root / job["folder"] / "style.json"
            if code != 0 or not marker.is_file():
                errors.append(f"#{job['video_id']} exit {code}")
                print(f"FAIL #{job['video_id']} exit {code}", flush=True)
                continue
            done[job["video_id"]] = json.loads(marker.read_text(encoding="utf-8"))
        running = still
        if running:
            time.sleep(2)
    if errors or (only is None and len(done) != len(jobs)):
        raise RuntimeError("書き出しが揃っていません\n" + "\n".join(errors))
    history = kane_published_history()
    published = published_signatures()
    rows = seed_log_rows()
    durations: dict[str, float] = {}
    plan_rows = []
    for job in jobs:
        if job["video_id"] in done:
            payload = done[job["video_id"]]
        else:
            marker = root / job["folder"] / "style.json"
            payload = json.loads(marker.read_text(encoding="utf-8"))
        signature = parse_signature(payload["signature"])
        report = check_signature(signature, history, published)
        if not report["ok"]:
            raise RuntimeError(f"#{job['video_id']} {signature.text()} {report['errors']}")
        rows.append(
            result_row(
                signature,
                job["video_id"],
                shared_prev=int(report["shared_prev"] or 0),
                shared_last5=int(report["shared_last5"]),
                length_sec=float(payload["duration"]),
                irasutoya_count=int(payload["irasutoya_count"]),
                credit_ok="yes",
                notes=f"published_shared={report['shared_published']}",
            )
        )
        history.append(signature)
        durations[str(root / job["folder"])] = float(payload["duration"])
        plan_rows.append(
            {
                "video_id": job["video_id"],
                "folder": job["folder"],
                "signature": signature.text(),
                "thumb": signature.thumb(),
            }
        )
    write_log(root / "affiliate-shorts" / "style-log.csv", rows)
    (root / "affiliate-shorts" / "style-plan.json").write_text(
        json.dumps(plan_rows, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    update_samples(root, durations)


def main() -> None:
    if "--job" in sys.argv:
        index = sys.argv.index("--job")
        render_job(sys.argv[index + 1], sys.argv[index + 2])
        return
    only = None
    if "--only" in sys.argv:
        only = {item.zfill(2) for item in sys.argv[sys.argv.index("--only") + 1].split(",")}
    render_all(ROOT, workers=3, only=only)


if __name__ == "__main__":
    main()
