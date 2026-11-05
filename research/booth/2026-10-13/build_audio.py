#!/usr/bin/env python3
"""COEIROINK（アンジーさん）で台本を1行ずつ合成し、効果音は合成のみで重ねずにつなぐ。"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import time
import urllib.error
import urllib.request
import wave
from pathlib import Path

import numpy as np

ENGINE = "/home/ubuntu/coeiroink/COEIROINK_LINUX_CPU_v.2025.4.1/engine/engine"
API = "http://127.0.0.1:50032/v1/synthesis"
SPEAKER = "cc213e6d-d847-45b5-a1df-415744c890f2"
SR = 44100
RESEARCH = Path("/workspace/research/booth/2026-10-13")
# 作業用の完全ファイル。artifacts の保存先は1ファイル約100MBで切れるため、書き出し後に分ける。
ARTIFACTS = Path("/home/ubuntu/booth-out")
LINE_CACHE = Path("/home/ubuntu/booth-out/line-cache")
ZIP_LIMIT = 290 * 1024 * 1024

CUE_RE = re.compile(r"^［(?:(左|右|両方)・)?(.+)（(\d+(?:\.\d+)?)秒）］$")
TRACK_RE = re.compile(r"^##\s+トラック(\d+)")


def speak_text(line: str) -> str:
    """括弧の読みは、直前の漢字（送りがな可）だけを読みに置き換える。"""
    text = re.sub(r"[一-龥々]+[ぁ-んー]{0,6}（([ぁ-んー]+)）", r"\1", line)
    text = re.sub(r"([ぁ-んー]{1,16})（\1）", r"\1", text)
    text = text.replace("……", "、、").replace("…", "、")
    # 香織は行内に読みがない。Whisper が spear と聞いたため、読みだけを渡す。原稿の漢字は残す。
    text = text.replace("香織", "かおり")
    return text.strip()


def parse_script(path: Path) -> list[dict]:
    tracks: list[dict] = []
    current: dict | None = None
    whisper = False
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("# ") or line.startswith("声：") or line.startswith("左右："):
            continue
        if line.startswith("読みがな：") or line.startswith("間の指定"):
            continue
        m = TRACK_RE.match(line)
        if m:
            current = {"id": int(m.group(1)), "title": line, "events": []}
            tracks.append(current)
            whisper = False
            continue
        if line.startswith("## おまけ"):
            current = {"id": "bonus", "title": line, "events": []}
            tracks.append(current)
            whisper = True
            continue
        if current is None:
            continue
        if line.startswith("（"):
            if "ささやき" in line and "ここから" in line:
                whisper = True
            continue
        cue = CUE_RE.match(line)
        if cue:
            kind = "silence" if cue.group(2) == "無音" else "sfx"
            current["events"].append(
                {
                    "type": kind,
                    "pan": cue.group(1) or "両方",
                    "name": cue.group(2),
                    "seconds": float(cue.group(3)),
                    "line": line,
                }
            )
            continue
        style = 122 if whisper or current["id"] != 1 else 120
        speed = 0.9 if current["id"] in (7, "bonus") else 0.95
        current["events"].append(
            {
                "type": "speech",
                "text": line,
                "speak": speak_text(line),
                "style": style,
                "speed": speed,
            }
        )
    return tracks


def sentence_gap(track_id: int | str, nxt: dict | None) -> float:
    if track_id == 1:
        base = 0.8
    elif track_id == 7:
        base = 1.2
    elif track_id == "bonus":
        base = 0.8
    else:
        base = 0.7
    if track_id == 2 and nxt and nxt["type"] == "speech":
        return 1.6
    return base


def ensure_engine() -> None:
    try:
        urllib.request.urlopen("http://127.0.0.1:50032/v1/speakers", timeout=3)
        return
    except Exception:
        pass
    subprocess.run(["pkill", "-f", "COEIROINK_LINUX_CPU_v.2025.4.1/engine/engine"], check=False)
    time.sleep(1)
    log = open("/tmp/coeiroink-engine.log", "a", encoding="utf-8")
    subprocess.Popen(
        [ENGINE],
        cwd=str(Path(ENGINE).parents[1]),
        stdout=log,
        stderr=subprocess.STDOUT,
    )
    for _ in range(90):
        try:
            urllib.request.urlopen("http://127.0.0.1:50032/v1/speakers", timeout=2)
            return
        except Exception:
            time.sleep(1)
    raise RuntimeError("COEIROINK engine did not start")


def synthesize(text: str, style: int, speed: float, dest: Path) -> None:
    if dest.exists() and dest.stat().st_size > 1000:
        return
    body = {
        "speakerUuid": SPEAKER,
        "styleId": style,
        "text": text,
        "speedScale": speed,
        "volumeScale": 1.0,
        "pitchScale": 0.0,
        "intonationScale": 1.0,
        "prePhonemeLength": 0.1,
        "postPhonemeLength": 0.3,
        "outputSamplingRate": SR,
    }
    data = json.dumps(body).encode()
    last = None
    for attempt in range(20):
        try:
            ensure_engine()
            req = urllib.request.Request(API, data=data, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=180) as resp:
                raw = resp.read()
            if len(raw) < 1000:
                raise RuntimeError(f"short wav {len(raw)}")
            dest.write_bytes(raw)
            return
        except (urllib.error.URLError, TimeoutError, RuntimeError, ConnectionError) as exc:
            last = exc
            print(f"  retry {attempt + 1} {text[:20]!r} {exc}", flush=True)
            time.sleep(10)
    raise RuntimeError(f"synthesis failed: {text}") from last


def pan_gains(pan: str) -> tuple[float, float]:
    if pan == "左":
        return 0.85, 0.28
    if pan == "右":
        return 0.28, 0.85
    return 0.62, 0.62


def sfx_kind(name: str) -> str:
    if "キス" in name:
        return "kiss"
    if any(k in name for k in ("口", "舌", "パイズリ", "ローション", "肌", "すべる", "太もも", "揺れ", "挟んで", "飲み")):
        if "止まる" in name:
            return "wet_stop"
        if "早め" in name:
            return "wet_fast"
        if "中" in name:
            return "wet_mid"
        if "静止" in name:
            return "wet_still"
        return "wet_slow"
    if any(k in name for k in ("吐息", "息だけ", "寝息")):
        return "breath"
    if "時計" in name:
        return "clock"
    if any(k in name for k in ("小鳥", "街")):
        return "birds"
    if any(k in name for k in ("環境音", "エンドロール")):
        return "bed"
    if any(k in name for k in ("湯", "コーヒー", "トースター")):
        return "kettle"
    if any(k in name for k in ("布", "シーツ", "カーテン")):
        return "rustle"
    return "transient"


def write_stereo(path: Path, left: np.ndarray, right: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pcm = np.stack([left, right], axis=1)
    pcm = np.clip(pcm, -1.0, 1.0)
    ints = (pcm * 32767.0).astype(np.int16)
    with wave.open(str(path), "w") as handle:
        handle.setnchannels(2)
        handle.setsampwidth(2)
        handle.setframerate(SR)
        handle.writeframes(ints.tobytes())


def synth_sfx(path: Path, seconds: float, name: str, pan: str, fade_last: float, seed: int) -> None:
    if path.exists() and path.stat().st_size > 1000:
        return
    n = max(1, int(seconds * SR))
    rng = np.random.default_rng(seed)
    kind = sfx_kind(name)
    mono = np.zeros(n, dtype=np.float32)
    if kind == "bed":
        white = rng.normal(0, 1, n).astype(np.float32)
        mono = np.cumsum(white)
        mono -= np.mean(mono)
    elif kind == "clock":
        white = rng.normal(0, 0.15, n).astype(np.float32)
        mono = np.cumsum(white) * 0.05
        step = SR
        pos = int(0.2 * SR)
        while pos < n:
            span = min(n, pos + int(0.02 * SR))
            mono[pos:span] += np.linspace(0.8, 0, span - pos, dtype=np.float32)
            pos += step
    elif kind == "birds":
        white = rng.normal(0, 1, n).astype(np.float32)
        mono = np.cumsum(white) * 0.02
        t = 0.4
        while t < seconds:
            start = int(t * SR)
            length = int(0.12 * SR)
            end = min(n, start + length)
            freq = float(rng.uniform(1400, 2800))
            tt = np.arange(end - start, dtype=np.float32) / SR
            chirp = np.sin(2 * np.pi * freq * tt) * np.linspace(0.25, 0, end - start, dtype=np.float32)
            mono[start:end] += chirp
            t += float(rng.uniform(1.5, 4.0))
    elif kind == "breath":
        noise = rng.normal(0, 1, n).astype(np.float32)
        kernel = 80
        mono = np.convolve(noise, np.ones(kernel, dtype=np.float32) / kernel, mode="same")
        env_t = np.linspace(0, seconds, n, dtype=np.float32)
        mono *= (0.35 + 0.65 * np.abs(np.sin(2 * np.pi * env_t / 3.5)))
    elif kind.startswith("wet"):
        interval = {"wet_fast": 0.22, "wet_mid": 0.38, "wet_slow": 0.7, "wet_still": 1.6, "wet_stop": 0.9}[kind]
        noise = rng.normal(0, 0.04, n).astype(np.float32)
        mono += np.convolve(noise, np.ones(40, dtype=np.float32) / 40, mode="same")
        pos = int(0.1 * SR)
        hop = max(1, int(interval * SR))
        burst_n = int(0.07 * SR)
        while pos < n:
            end = min(n, pos + burst_n)
            burst = rng.normal(0, 1, end - pos).astype(np.float32)
            burst *= np.linspace(1, 0, end - pos, dtype=np.float32)
            mono[pos:end] += burst * (0.35 if kind == "wet_stop" else 0.7)
            if kind == "wet_stop":
                hop = int(hop * 1.04)
            pos += hop
    elif kind == "kiss":
        pos = int(0.15 * SR)
        k = 0
        while pos < n and k < max(2, int(seconds / 1.2)):
            end = min(n, pos + int(0.09 * SR))
            burst = rng.normal(0, 1, end - pos).astype(np.float32)
            burst *= np.linspace(1, 0, end - pos, dtype=np.float32)
            mono[pos:end] += burst
            pos += int(float(rng.uniform(0.7, 1.3)) * SR)
            k += 1
    elif kind == "kettle":
        noise = rng.normal(0, 1, n).astype(np.float32)
        mono = np.convolve(noise, np.ones(20, dtype=np.float32) / 20, mode="same")
        mono *= np.linspace(0.2, 1.0, n, dtype=np.float32)
    elif kind == "rustle":
        noise = rng.normal(0, 1, n).astype(np.float32)
        mono = np.diff(noise, prepend=noise[:1])
        gate = rng.random(n).astype(np.float32)
        mono *= (gate > 0.55).astype(np.float32)
    else:
        noise = rng.normal(0, 0.05, n).astype(np.float32)
        mono = np.cumsum(noise)
        hit = min(n, int(0.35 * SR))
        mono[:hit] += rng.normal(0, 1, hit).astype(np.float32) * np.linspace(1, 0, hit, dtype=np.float32)
    peak = float(np.max(np.abs(mono))) or 1.0
    mono = mono / peak * 0.45
    if fade_last > 0 and seconds > fade_last:
        fade_n = int(fade_last * SR)
        mono[-fade_n:] *= np.linspace(1, 0, fade_n, dtype=np.float32)
    gl, gr = pan_gains(pan)
    write_stereo(path, mono * gl, mono * gr)


def write_silence(path: Path, seconds: float) -> None:
    if seconds <= 0:
        seconds = 0.01
    if path.exists():
        return
    n = max(1, int(seconds * SR))
    write_stereo(path, np.zeros(n, dtype=np.float32), np.zeros(n, dtype=np.float32))


def to_stereo(src: Path, dest: Path) -> None:
    if dest.exists() and dest.stat().st_size > 1000:
        return
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-i", str(src), "-ar", str(SR), "-ac", "2", "-sample_fmt", "s16", str(dest)],
        check=True,
    )


def concat(parts: list[Path], dest: Path) -> None:
    lst = dest.with_suffix(".txt")
    lst.write_text("".join(f"file '{p}'\n" for p in parts), encoding="utf-8")
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(dest)],
        check=True,
    )


def ffprobe_seconds(path: Path) -> float:
    out = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(path)],
        text=True,
    )
    return float(out.strip())


def ebur128(path: Path) -> dict[str, str]:
    proc = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-af", "ebur128=peak=true", "-f", "null", "-"],
        capture_output=True,
        text=True,
    )
    text = proc.stderr
    summary = text.split("Summary:")[-1]
    found: dict[str, str] = {}
    integrated = re.search(r"^\s+I:\s+(-?[\d.]+|inf|-inf)", summary, re.M)
    if not integrated:
        raise RuntimeError(f"ebur128 failed for {path}\n{text[-500:]}")
    found["I"] = integrated.group(1)
    true_peak = re.search(r"True peak:[\s\S]*?Peak:\s+(-?[\d.]+|inf|-inf)", summary)
    if true_peak:
        found["TP"] = true_peak.group(1)
        found["Peak"] = true_peak.group(1)
    return found


def loudnorm(src: Path, dest: Path) -> tuple[dict[str, str], dict[str, str]]:
    before = ebur128(src)
    proc = subprocess.run(
        [
            "ffmpeg", "-hide_banner", "-nostats", "-i", str(src),
            "-af", "loudnorm=I=-22.5:TP=-1:LRA=11:print_format=json",
            "-f", "null", "-",
        ],
        capture_output=True,
        text=True,
    )
    match = re.search(r"\{[\s\S]+\}", proc.stderr)
    if not match:
        raise RuntimeError(proc.stderr[-800:])
    measured = json.loads(match.group(0))
    filt = (
        "loudnorm=I=-22.5:TP=-1:LRA=11:"
        f"measured_I={measured['input_i']}:measured_TP={measured['input_tp']}:"
        f"measured_LRA={measured['input_lra']}:measured_thresh={measured['input_thresh']}:"
        f"offset={measured['target_offset']}:linear=true"
    )
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-i", str(src), "-af", filt, "-ar", str(SR), "-ac", "2", "-sample_fmt", "s16", str(dest)],
        check=True,
    )
    after = ebur128(dest)
    return before, after


def to_mp3(src: Path, dest: Path) -> None:
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-i", str(src), "-codec:a", "libmp3lame", "-b:a", "320k", str(dest)],
        check=True,
    )


def build_events(track: dict, seg_dir: Path, cache: Path, fade_last_bed: bool) -> list[Path]:
    seg_dir.mkdir(parents=True, exist_ok=True)
    pieces: list[Path] = []
    events = track["events"]
    for index, event in enumerate(events):
        piece = seg_dir / f"{index:04d}.wav"
        if event["type"] == "speech":
            key = hashlib.sha1(f"{event['style']}|{event['speed']}|{event['speak']}".encode()).hexdigest()[:16]
            raw = cache / f"{key}.wav"
            synthesize(event["speak"], event["style"], event["speed"], raw)
            voice = seg_dir / f"{index:04d}-voice.wav"
            to_stereo(raw, voice)
            gap = sentence_gap(track["id"], events[index + 1] if index + 1 < len(events) else None)
            gap_path = seg_dir / f"{index:04d}-gap.wav"
            write_silence(gap_path, gap)
            # concat voice+gap into piece
            concat([voice, gap_path], piece)
        elif event["type"] == "silence":
            write_silence(piece, event["seconds"])
        else:
            fade = 120.0 if fade_last_bed and index == len(events) - 1 and event["seconds"] >= 120 else 0.0
            synth_sfx(piece, event["seconds"], event["name"], event["pan"], fade, seed=index + int(event["seconds"] * 10))
        pieces.append(piece)
    return pieces


def render_track(track: dict, work_dir: Path, cache: Path, name: str, fade_bed: bool) -> Path:
    dry = work_dir / "dry" / f"{name}.wav"
    final = work_dir / "audio" / f"{name}.wav"
    final.parent.mkdir(parents=True, exist_ok=True)
    if final.exists() and final.stat().st_size > 1000:
        return final
    pieces = build_events(track, work_dir / "seg" / name, cache, fade_bed)
    dry.parent.mkdir(parents=True, exist_ok=True)
    concat(pieces, dry)
    dur = ffprobe_seconds(dry)
    bed = work_dir / "dry" / f"{name}-bed.wav"
    subprocess.run(
        [
            "ffmpeg", "-y", "-v", "error",
            "-i", str(dry),
            "-f", "lavfi", "-t", f"{dur:.3f}", "-i", f"anoisesrc=color=brown:r={SR}:amplitude=0.03",
            "-filter_complex",
            "[1:a]lowpass=f=350,volume=-28dB,pan=stereo|c0=c0|c1=c0[b];"
            "[0:a][b]amix=inputs=2:duration=first:normalize=0:dropout_transition=0",
            "-ar", str(SR), "-ac", "2", "-sample_fmt", "s16", str(bed),
        ],
        check=True,
    )
    before, after = loudnorm(bed, final)
    (work_dir / "measure" / f"{name}.json").parent.mkdir(parents=True, exist_ok=True)
    (work_dir / "measure" / f"{name}.json").write_text(
        json.dumps({"before": before, "after": after, "seconds": ffprobe_seconds(final)}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    to_mp3(final, final.with_suffix(".mp3"))
    print(f"rendered {name} {ffprobe_seconds(final):.2f}s I={after.get('I')} TP={after.get('TP')}", flush=True)
    return final


def make_env(work_dir: Path) -> Path:
    final = work_dir / "audio" / "env.wav"
    if final.exists():
        return final
    raw = work_dir / "dry" / "env-raw.wav"
    raw.parent.mkdir(parents=True, exist_ok=True)
    synth_sfx(raw, 1800, "部屋の環境音と時計", "両方", 0, seed=19)
    # overlay clock already in kind if name has 環境音 only. Rebuild with clock mixed.
    clock = work_dir / "dry" / "env-clock.wav"
    synth_sfx(clock, 1800, "時計", "両方", 0, seed=23)
    mixed = work_dir / "dry" / "env-mix.wav"
    subprocess.run(
        [
            "ffmpeg", "-y", "-v", "error", "-i", str(raw), "-i", str(clock),
            "-filter_complex", "[0:a][1:a]amix=inputs=2:duration=first:normalize=0,atrim=0:1800",
            "-ar", str(SR), "-ac", "2", "-sample_fmt", "s16", str(mixed),
        ],
        check=True,
    )
    loudnorm(mixed, final)
    # force exact 30:00
    exact = work_dir / "audio" / "env-exact.wav"
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-i", str(final), "-af", "apad=whole_dur=1800,atrim=0:1800", "-ar", str(SR), "-ac", "2", "-sample_fmt", "s16", str(exact)],
        check=True,
    )
    exact.replace(final)
    to_mp3(final, final.with_suffix(".mp3"))
    return final


def sample_from_t1(track: dict, work_dir: Path, cache: Path) -> Path:
    """T1の頭から「すぐに、やめますね。」まで。キスと肌の効果音は入れない。"""
    kept: list[dict] = []
    for event in track["events"]:
        if event["type"] == "sfx" and any(k in event["name"] for k in ("キス", "胸", "パイズリ", "ローション", "肌", "口", "舌", "太もも")):
            continue
        kept.append(dict(event))
        if event["type"] == "speech" and "すぐに、やめますね" in event["text"]:
            break
    sample_track = {"id": 1, "title": "sample", "events": kept}
    # shorten opening bed if over 90s by rewriting the first long sfx after a rough estimate
    est = 0.0
    for event in kept:
        if event["type"] == "speech":
            est += max(2.5, len(event["speak"]) * 0.18) + 0.8
        else:
            est += event["seconds"]
    if est > 90:
        for event in kept:
            if event["type"] == "sfx" and event["seconds"] >= 8:
                event["seconds"] = max(2.0, event["seconds"] - (est - 85))
                break
    out = work_dir / "sample"
    fake_work = work_dir / "sample-build"
    path = render_track(sample_track, fake_work, cache, "sample", fade_bed=False)
    dest = out / "sample.mp3"
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(path.with_suffix(".mp3"), dest)
    shutil.copy(path, out / "sample.wav")
    return dest


def pack_zips(work_id: str, work_dir: Path, script_text: str, summary: str) -> list[dict]:
    zip_dir = work_dir / "zip"
    if zip_dir.exists():
        shutil.rmtree(zip_dir)
    zip_dir.mkdir(parents=True)
    audio = work_dir / "audio"
    readme = summary
    script_path = zip_dir / "台本.txt"
    script_path.write_text(script_text, encoding="utf-8")
    (zip_dir / "readme.txt").write_text(readme, encoding="utf-8")
    mp3s = [audio / f"part{i:02d}.mp3" for i in range(1, 8)]
    mp3s += [audio / "bonus.mp3", audio / "env.mp3"]
    made = []
    made.append(write_zip(zip_dir / f"{work_id}_MP3.zip", mp3s + [script_path, zip_dir / "readme.txt"], f"{work_id}_MP3"))
    wavs = [audio / f"part{i:02d}.wav" for i in range(1, 8)] + [audio / "bonus.wav", audio / "env.wav"]
    groups: list[list[Path]] = []
    current: list[Path] = []
    current_size = 0
    for wav in wavs:
        size = wav.stat().st_size
        if current and current_size + size > ZIP_LIMIT:
            groups.append(current)
            current = []
            current_size = 0
        current.append(wav)
        current_size += size
    if current:
        groups.append(current)
    for index, group in enumerate(groups, start=1):
        label = f"{work_id}_WAV_その{index}"
        made.append(write_zip(zip_dir / f"{label}.zip", group + [script_path, zip_dir / "readme.txt"], label))
    files_txt = zip_dir / "files.txt"
    lines = []
    for item in made:
        lines.append(f"{item['name']}\t{item['bytes']}\t{item['ok']}")
        lines.extend(f"  {name}" for name in item["files"])
    files_txt.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return made


def write_zip(dest: Path, files: list[Path], folder: str) -> dict:
    import zipfile

    with zipfile.ZipFile(dest, "w", compression=zipfile.ZIP_STORED) as zf:
        for file in files:
            zf.write(file, arcname=f"{folder}/{file.name}")
    with zipfile.ZipFile(dest) as zf:
        bad = zf.testzip()
        names = zf.namelist()
    images = [n for n in names if n.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp"))]
    nested = [n for n in names if n.lower().endswith(".zip")]
    size = dest.stat().st_size
    ok = bad is None and not images and not nested and size <= 300 * 1024 * 1024
    return {"name": dest.name, "bytes": size, "ok": ok, "bad": bad, "images": images, "nested": nested, "files": names}


def t6_ratio(measures: dict[str, float]) -> float:
    main = sum(measures[f"part{i:02d}"] for i in range(1, 8))
    head = sum(measures[f"part{i:02d}"] for i in range(1, 7))
    return head / main


def adjust_bed(track: dict, ratio: float) -> tuple[bool, str]:
    if 0.60 <= ratio <= 0.85:
        return False, f"T6の終わりは{ratio * 100:.2f}%で、60〜85%の範囲なので秒数は変えていない。"
    target = 0.82
    # head / (head + tail) = target => tail = head * (1-target)/target
    # We only scale the last bed, so approximate by setting bed seconds.
    last = track["events"][-1]
    if last["type"] != "sfx":
        return False, "T7の最後が効果音ではないため、秒数は変えていない。"
    # caller passes current ratio and durations via last['_head']
    head = last.pop("_head")
    tail_now = last.pop("_tail")
    desired_tail = head * (1 - target) / target
    delta = desired_tail - tail_now
    new_sec = last["seconds"] + delta
    new_sec = min(540.0, max(180.0, new_sec))
    old = last["seconds"]
    last["seconds"] = round(new_sec, 1)
    return True, f"［{last['name']}（{old:g}秒）］を{last['seconds']:g}秒にした。理由: T6の終わりが{ratio * 100:.2f}%。"


def process_work(work_id: str) -> None:
    script_path = RESEARCH / work_id / "script.md"
    tracks = parse_script(script_path)
    work_dir = ARTIFACTS / work_id
    cache = LINE_CACHE / work_id / "line-cache"
    cache.mkdir(parents=True, exist_ok=True)
    by_id = {t["id"]: t for t in tracks}
    for number in range(1, 8):
        fade = number == 7
        render_track(by_id[number], work_dir, cache, f"part{number:02d}", fade_bed=fade)
    render_track(by_id["bonus"], work_dir, cache, "bonus", fade_bed=False)
    measures = {}
    for number in range(1, 8):
        measures[f"part{number:02d}"] = json.loads((work_dir / "measure" / f"part{number:02d}.json").read_text())["seconds"]
    ratio = t6_ratio(measures)
    head = sum(measures[f"part{n:02d}"] for n in range(1, 7))
    tail = measures["part07"]
    by_id[7]["events"][-1]["_head"] = head
    by_id[7]["events"][-1]["_tail"] = tail
    changed, reason = adjust_bed(by_id[7], ratio)
    if changed:
        for suffix in (".wav", ".mp3"):
            p = work_dir / "audio" / f"part07{suffix}"
            if p.exists():
                p.unlink()
        for folder, name in (("dry", "part07.wav"), ("measure", "part07.json")):
            p = work_dir / folder / name
            if p.exists():
                p.unlink()
        bedmix = work_dir / "dry" / "part07-bed.wav"
        if bedmix.exists():
            bedmix.unlink()
        seg = work_dir / "seg" / "part07"
        if seg.exists():
            shutil.rmtree(seg)
        render_track(by_id[7], work_dir, cache, "part07", fade_bed=True)
        new_sec = by_id[7]["events"][-1]["seconds"]
        lines = script_path.read_text(encoding="utf-8").splitlines()
        start = next(i for i, line in enumerate(lines) if line.startswith("## トラック7"))
        end = next((i for i, line in enumerate(lines) if i > start and line.startswith("## ")), len(lines))
        for i in range(end - 1, start, -1):
            if CUE_RE.match(lines[i].strip()):
                lines[i] = CUE_RE.sub(
                    lambda m: f"［{(m.group(1) + '・') if m.group(1) else ''}{m.group(2)}（{new_sec:g}秒）］",
                    lines[i].strip(),
                )
                break
        v2 = RESEARCH / work_id / "script_v2.md"
        v2.write_text("\n".join(lines) + "\n", encoding="utf-8")
    subprocess.run(["pkill", "-f", "COEIROINK_LINUX_CPU_v.2025.4.1/engine/engine"], check=False)
    make_env(work_dir)
    sample = sample_from_t1(by_id[1], work_dir, cache)
    # refresh measures
    report = {"work": work_id, "t6_reason": reason, "changed": changed, "tracks": {}}
    for number in range(1, 8):
        data = json.loads((work_dir / "measure" / f"part{number:02d}.json").read_text())
        report["tracks"][f"part{number:02d}"] = data
    report["bonus"] = json.loads((work_dir / "measure" / "bonus.json").read_text())
    report["sample_seconds"] = ffprobe_seconds(sample)
    report["env_seconds"] = ffprobe_seconds(work_dir / "audio" / "env.wav")
    main = sum(report["tracks"][f"part{n:02d}"]["seconds"] for n in range(1, 8))
    head = sum(report["tracks"][f"part{n:02d}"]["seconds"] for n in range(1, 7))
    report["main_seconds"] = main
    report["t6_percent"] = head / main * 100
    (work_dir / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("t6_percent", "t6_reason", "main_seconds", "sample_seconds")}, ensure_ascii=False), flush=True)


def synth_work19_line() -> None:
    dest_dir = LINE_CACHE / "19"
    dest_dir.mkdir(parents=True, exist_ok=True)
    raw = dest_dir / "line-raw.wav"
    # 原稿の文は「原稿をチェックする仕事」。「原稿」だけだと健康と聞こえるため、合成は「書いた原稿」。
    synthesize("平日は、書いた原稿をチェックする仕事で", 122, 0.95, raw)
    stereo = dest_dir / "kouetsu-line.wav"
    to_stereo(raw, stereo)
    to_mp3(stereo, dest_dir / "kouetsu-line.mp3")
    print("work19 line", ffprobe_seconds(stereo), flush=True)


def clear_track(work_dir: Path, name: str) -> None:
    for path in (
        work_dir / "audio" / f"{name}.wav",
        work_dir / "audio" / f"{name}.mp3",
        work_dir / "dry" / f"{name}.wav",
        work_dir / "dry" / f"{name}-bed.wav",
        work_dir / "measure" / f"{name}.json",
    ):
        if path.exists():
            path.unlink()
    seg = work_dir / "seg" / name
    if seg.exists():
        shutil.rmtree(seg)


def rebuild_affected() -> None:
    """読みを直した行が入るトラックだけ、作り直す。"""
    for raw in (
        LINE_CACHE / "19" / "line-raw.wav",
        LINE_CACHE / "19" / "kouetsu-line.wav",
        LINE_CACHE / "19" / "kouetsu-line.mp3",
    ):
        if raw.exists():
            raw.unlink()
    ensure_engine()
    synth_work19_line()
    for work_id, names in (("20", ("part01",)), ("21", ("part01", "part02"))):
        work_dir = ARTIFACTS / work_id
        for name in names:
            clear_track(work_dir, name)
        clear_track(work_dir / "sample-build", "sample")
        sample_dir = work_dir / "sample"
        for path in (sample_dir / "sample.wav", sample_dir / "sample.mp3"):
            if path.exists():
                path.unlink()
    process_work("20")
    process_work("21")
    subprocess.run(["pkill", "-f", "COEIROINK_LINUX_CPU_v.2025.4.1/engine/engine"], check=False)


def main() -> None:
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "rebuild":
        rebuild_affected()
        return
    ensure_engine()
    synth_work19_line()
    process_work("20")
    process_work("21")
    subprocess.run(["pkill", "-f", "COEIROINK_LINUX_CPU_v.2025.4.1/engine/engine"], check=False)


if __name__ == "__main__":
    main()
