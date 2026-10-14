#!/usr/bin/env python3
"""COEIROINK のアンジーさんで 27〜31 を合成する。公開はしない。

目標ラウドネスは -16 LUFS、トゥルーピーク -1 dBFS。
効果音は合成のみ。セクシー（styleId 121）は使わない。
"""

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
import zipfile
from pathlib import Path

import numpy as np

ENGINE = "/home/ubuntu/coeiroink/COEIROINK_LINUX_CPU_v.2025.4.1/engine/engine"
API = "http://127.0.0.1:50032/v1/synthesis"
SPEAKER = "cc213e6d-d847-45b5-a1df-415744c890f2"
SR = 44100
RESEARCH = Path("/workspace/research/booth/2026-10-14")
OUT = Path("/home/ubuntu/booth-out/2026-10-14")
ARTIFACTS = Path("/opt/cursor/artifacts/booth-2026-10-14")
FILE_LIMIT = 95 * 1024 * 1024
TARGET_I = -16.0

CUE_RE = re.compile(r"^［(?:(左|右|両方)・)?(.+)（(\d+(?:\.\d+)?)秒）］$")
TRACK_RE = re.compile(r"^##\s+トラック(\d+)")
SAMPLE_END = {
    "27": "すぐに、やめますね",
    "28": "すぐに、やめますね",
    "29": "すぐに、やめますね",
    "30": "キャップは、したままです",
    "31": "すぐに、やめますね",
}
SAMPLE_SKIP = ("キス", "手", "指", "肌", "すべる", "乳首", "聴き手")


def speak_text(line: str) -> str:
    text = re.sub(r"[一-龥々]+[ぁ-んー]{0,6}（([ぁ-んー]+)）", r"\1", line)
    text = re.sub(r"([ぁ-んー]{1,16})（\1）", r"\1", text)
    text = text.replace("……", "、、").replace("…", "、")
    return text.strip()


def parse_script(path: Path) -> list[dict]:
    tracks: list[dict] = []
    current: dict | None = None
    whisper = False
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("# ") or line.startswith("声：") or line.startswith("左右："):
            continue
        if line.startswith("読みがな：") or line.startswith("間の指定") or line.startswith("登場人物"):
            continue
        if line.startswith("［］"):
            continue
        match = TRACK_RE.match(line)
        if match:
            current = {"id": int(match.group(1)), "title": line, "events": []}
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
        if line.startswith("［") and not cue:
            continue
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
        style = 122 if whisper or current["id"] == "bonus" else 120
        if current["id"] != 1:
            style = 122
        speed = 0.9 if current["id"] == "bonus" else 0.95
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
    base = 0.8 if track_id in (1, "bonus") else 0.7
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
    if style not in (120, 122):
        raise RuntimeError(f"style {style} is not Angie normal or whisper")
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
    last: Exception | None = None
    for attempt in range(12):
        try:
            ensure_engine()
            req = urllib.request.Request(API, data=data, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=180) as resp:
                raw = resp.read()
            if len(raw) < 1000:
                raise RuntimeError(f"short wav {len(raw)}")
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(raw)
            return
        except (urllib.error.URLError, TimeoutError, RuntimeError, ConnectionError) as exc:
            last = exc
            print(f"  retry {attempt + 1} {text[:24]!r} {exc}", flush=True)
            time.sleep(5)
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
    if any(k in name for k in ("手", "指", "すべる", "肌", "乳首", "聴き手")):
        if "止まる" in name or "離" in name:
            return "wet_stop"
        if "早め" in name:
            return "wet_fast"
        if "中" in name:
            return "wet_mid"
        if "静止" in name or "添え" in name:
            return "wet_still"
        return "wet_slow"
    if any(k in name for k in ("吐息", "息だけ", "寝息")):
        return "breath"
    if "時計" in name:
        return "clock"
    if any(k in name for k in ("雨", "スタジオ", "和室", "部屋", "環境", "夜の音", "昼", "朝")):
        return "bed"
    if any(k in name for k in ("湯", "コーヒー", "トースター", "水道", "ポット")):
        return "kettle"
    if any(k in name for k in ("布", "シーツ", "カーテン", "毛布", "タオル")):
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


def synth_sfx(path: Path, seconds: float, name: str, pan: str, seed: int) -> None:
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
        pos = int(0.2 * SR)
        while pos < n:
            span = min(n, pos + int(0.02 * SR))
            mono[pos:span] += np.linspace(0.8, 0, span - pos, dtype=np.float32)
            pos += SR
    elif kind == "breath":
        noise = rng.normal(0, 1, n).astype(np.float32)
        kernel = 80
        mono = np.convolve(noise, np.ones(kernel, dtype=np.float32) / kernel, mode="same")
        env_t = np.linspace(0, seconds, n, dtype=np.float32)
        mono *= 0.35 + 0.65 * np.abs(np.sin(2 * np.pi * env_t / 3.5))
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
    gl, gr = pan_gains(pan)
    write_stereo(path, mono * gl, mono * gr)


def write_silence(path: Path, seconds: float) -> None:
    if path.exists() and path.stat().st_size > 44:
        return
    n = max(1, int(max(seconds, 0.01) * SR))
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
    summary = proc.stderr.split("Summary:")[-1]
    integrated = re.search(r"^\s+I:\s+(-?[\d.]+|inf|-inf)", summary, re.M)
    if not integrated:
        raise RuntimeError(f"ebur128 failed for {path}\n{proc.stderr[-500:]}")
    found = {"I": integrated.group(1)}
    true_peak = re.search(r"True peak:[\s\S]*?Peak:\s+(-?[\d.]+|inf|-inf)", summary)
    if true_peak:
        found["TP"] = true_peak.group(1)
    return found


def loudnorm(src: Path, dest: Path) -> dict[str, str]:
    proc = subprocess.run(
        [
            "ffmpeg", "-hide_banner", "-nostats", "-i", str(src),
            "-af", f"loudnorm=I={TARGET_I}:TP=-1:LRA=11:print_format=json",
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
        f"loudnorm=I={TARGET_I}:TP=-1:LRA=11:"
        f"measured_I={measured['input_i']}:measured_TP={measured['input_tp']}:"
        f"measured_LRA={measured['input_lra']}:measured_thresh={measured['input_thresh']}:"
        f"offset={measured['target_offset']}:linear=true"
    )
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-i", str(src), "-af", filt, "-ar", str(SR), "-ac", "2", "-sample_fmt", "s16", str(dest)],
        check=True,
    )
    return ebur128(dest)


def to_mp3(src: Path, dest: Path) -> None:
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-i", str(src), "-codec:a", "libmp3lame", "-b:a", "320k", str(dest)],
        check=True,
    )


def build_events(track: dict, seg_dir: Path, cache: Path) -> list[Path]:
    seg_dir.mkdir(parents=True, exist_ok=True)
    pieces: list[Path] = []
    events = track["events"]
    for index, event in enumerate(events):
        piece = seg_dir / f"{index:04d}.wav"
        if event["type"] == "speech":
            key = hashlib.sha1(f"{event['style']}|{event['speed']}|{event['speak']}".encode()).hexdigest()[:16]
            raw = cache / f"{key}.wav"
            if not raw.exists():
                print(f"  tts {track['id']} {event['speak'][:28]}", flush=True)
            synthesize(event["speak"], event["style"], event["speed"], raw)
            voice = seg_dir / f"{index:04d}-voice.wav"
            to_stereo(raw, voice)
            gap = sentence_gap(track["id"], events[index + 1] if index + 1 < len(events) else None)
            gap_path = seg_dir / f"{index:04d}-gap.wav"
            write_silence(gap_path, gap)
            concat([voice, gap_path], piece)
        elif event["type"] == "silence":
            write_silence(piece, event["seconds"])
        else:
            synth_sfx(piece, event["seconds"], event["name"], event["pan"], seed=index + int(event["seconds"] * 10))
        pieces.append(piece)
    return pieces


def render_track(track: dict, work_dir: Path, cache: Path, name: str) -> Path:
    final = work_dir / "audio" / f"{name}.wav"
    final.parent.mkdir(parents=True, exist_ok=True)
    if final.exists() and final.stat().st_size > 1000 and (work_dir / "measure" / f"{name}.json").exists():
        print(f"skip {name}", flush=True)
        return final
    pieces = build_events(track, work_dir / "seg" / name, cache)
    dry = work_dir / "dry" / f"{name}.wav"
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
    after = loudnorm(bed, final)
    measure = {"after": after, "seconds": ffprobe_seconds(final), "target_lufs": TARGET_I}
    measure_path = work_dir / "measure" / f"{name}.json"
    measure_path.parent.mkdir(parents=True, exist_ok=True)
    measure_path.write_text(json.dumps(measure, ensure_ascii=False, indent=2), encoding="utf-8")
    to_mp3(final, final.with_suffix(".mp3"))
    print(f"rendered {name} {measure['seconds']:.2f}s I={after.get('I')} TP={after.get('TP')}", flush=True)
    return final


def sample_track(track: dict, work_id: str) -> dict:
    end = SAMPLE_END[work_id]
    kept: list[dict] = []
    for event in track["events"]:
        if event["type"] == "sfx" and any(k in event["name"] for k in SAMPLE_SKIP):
            continue
        kept.append(dict(event))
        if event["type"] == "speech" and end in event["text"]:
            break
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
    return {"id": 1, "title": "sample", "events": kept}


def split_wav(src: Path, dest_dir: Path) -> list[Path]:
    dest_dir.mkdir(parents=True, exist_ok=True)
    if src.stat().st_size <= FILE_LIMIT:
        dest = dest_dir / src.name
        if not dest.exists():
            shutil.copy2(src, dest)
        return [dest]
    pattern = dest_dir / f"{src.stem}-%03d.wav"
    subprocess.run(
        [
            "ffmpeg", "-y", "-v", "error", "-i", str(src),
            "-f", "segment", "-segment_time", "480", "-c", "copy", str(pattern),
        ],
        check=True,
    )
    parts = sorted(dest_dir.glob(f"{src.stem}-*.wav"))
    for part in parts:
        if part.stat().st_size > FILE_LIMIT:
            raise RuntimeError(f"{part} is still over the file limit")
    return parts


def write_zip(dest: Path, files: list[Path], folder: str) -> None:
    with zipfile.ZipFile(dest, "w", compression=zipfile.ZIP_STORED) as handle:
        for file in files:
            handle.write(file, arcname=f"{folder}/{file.name}")
    with zipfile.ZipFile(dest) as handle:
        bad = handle.testzip()
        names = handle.namelist()
    if bad is not None:
        raise RuntimeError(f"bad zip {dest}: {bad}")
    if any(name.lower().endswith(".zip") for name in names):
        raise RuntimeError(f"nested zip {dest}")
    if dest.stat().st_size > FILE_LIMIT:
        raise RuntimeError(f"{dest} is {dest.stat().st_size} bytes")


def pack_work(work_id: str, work_dir: Path, script_text: str) -> None:
    art = ARTIFACTS / work_id / "audio"
    if art.exists():
        shutil.rmtree(art)
    art.mkdir(parents=True)
    note = art / "readme.txt"
    note.write_text(
        "公開・出品・申請はしていません。話者は COEIROINK のアンジーさん。"
        "目標は -16 LUFS、トゥルーピーク -1 dBFS。効果音は合成。\n",
        encoding="utf-8",
    )
    script_copy = art / "台本.txt"
    script_copy.write_text(script_text, encoding="utf-8")
    audio = work_dir / "audio"
    mp3s = sorted(audio.glob("*.mp3"))
    wav_pieces: list[Path] = []
    wav_dir = art / "wav-parts"
    for wav in sorted(audio.glob("*.wav")):
        wav_pieces.extend(split_wav(wav, wav_dir))
    for mp3 in mp3s:
        if mp3.stat().st_size > FILE_LIMIT:
            raise RuntimeError(f"{mp3} exceeds file limit")
        shutil.copy2(mp3, art / mp3.name)
    groups: list[list[Path]] = []
    current: list[Path] = []
    current_size = note.stat().st_size + script_copy.stat().st_size
    for piece in mp3s + wav_pieces:
        size = piece.stat().st_size
        if current and current_size + size > FILE_LIMIT:
            groups.append(current)
            current = []
            current_size = note.stat().st_size + script_copy.stat().st_size
        current.append(piece)
        current_size += size
    if current:
        groups.append(current)
    for index, group in enumerate(groups, start=1):
        folder = f"{work_id}-{index:02d}"
        dest = art / f"{folder}.zip"
        write_zip(dest, group + [note, script_copy], folder)
        print(f"zip {dest.name} {dest.stat().st_size}", flush=True)
    lines = []
    for path in sorted(art.rglob("*")):
        if path.is_file():
            lines.append(f"{path.relative_to(art)}\t{path.stat().st_size}")
    (art / "files.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def process_work(work_id: str) -> None:
    print(f"=== work {work_id} ===", flush=True)
    script_path = RESEARCH / work_id / "script.md"
    tracks = parse_script(script_path)
    work_dir = OUT / work_id
    cache = work_dir / "line-cache"
    cache.mkdir(parents=True, exist_ok=True)
    for track in tracks:
        if track["id"] == "bonus":
            name = "bonus"
        else:
            name = f"part{track['id']:02d}"
        render_track(track, work_dir, cache, name)
    first = next(track for track in tracks if track["id"] == 1)
    render_track(sample_track(first, work_id), work_dir, cache, "sample")
    pack_work(work_id, work_dir, script_path.read_text(encoding="utf-8"))


def main() -> None:
    ensure_engine()
    for work_id in ("27", "28", "29", "30", "31"):
        process_work(work_id)
    print("ALL DONE", flush=True)


if __name__ == "__main__":
    main()
