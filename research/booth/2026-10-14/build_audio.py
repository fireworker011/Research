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
import sys
import time
import urllib.error
import urllib.request
import wave
import zipfile
from decimal import Decimal, ROUND_HALF_UP
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
TARGET_TP = -1.0
# 8倍に上げてからサンプルピークを抑える。MP3のトゥルーピークが -1.0 を超えない
# いちばん浅い天井を、ファイルごとにこの順で試す。
TP_CEILINGS_DB = (-1.2, -1.5, -1.8, -2.0, -2.3, -2.6, -3.0, -3.5)
NAMES = ("part01", "part02", "part03", "part04", "part05", "part06", "bonus", "sample")

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


def tp_value(stats: dict[str, str]) -> float:
    if "TP" not in stats:
        raise RuntimeError(f"ebur128 has no true peak: {stats}")
    return float(stats["TP"])


def exceeds_tp(stats: dict[str, str]) -> bool:
    return tp_value(stats) > TARGET_TP


def limiter_filter(ceiling_db: float) -> str:
    limit = 10 ** (ceiling_db / 20.0)
    return (
        "aresample=352800:resampler=soxr:precision=28,"
        f"alimiter=limit={limit:.8f}:attack=1:release=80:level=disabled:latency=true,"
        "aresample=44100:resampler=soxr:precision=28"
    )


def render_limited(src: Path, dest: Path, ceiling_db: float) -> None:
    subprocess.run(
        [
            "ffmpeg", "-y", "-v", "error", "-i", str(src),
            "-af", limiter_filter(ceiling_db),
            "-ar", str(SR), "-ac", "2", "-sample_fmt", "s16", str(dest),
        ],
        check=True,
    )


def limit_true_peak(wav: Path, mp3: Path) -> tuple[dict[str, str], dict[str, str], float]:
    """Bring wav and mp3 true peaks to -1.0 dBTP or lower. Keep the shallowest ceiling."""
    original = wav.with_suffix(".pre-limit.wav")
    mp3_backup = mp3.with_suffix(".pre-limit.mp3")
    if original.exists():
        shutil.copy2(original, wav)
        original.unlink()
    shutil.copy2(wav, original)
    shutil.copy2(mp3, mp3_backup)
    kept: tuple[dict[str, str], dict[str, str], float] | None = None
    try:
        for ceiling in TP_CEILINGS_DB:
            print(f"  ceiling {ceiling} {wav.name}", flush=True)
            render_limited(original, wav, ceiling)
            wav_stats = ebur128(wav)
            if exceeds_tp(wav_stats):
                continue
            to_mp3(wav, mp3)
            mp3_stats = ebur128(mp3)
            if exceeds_tp(mp3_stats):
                continue
            print(
                f"  kept {wav.name} ceiling {ceiling} "
                f"wav I={wav_stats['I']} TP={wav_stats['TP']} "
                f"mp3 I={mp3_stats['I']} TP={mp3_stats['TP']}",
                flush=True,
            )
            kept = (wav_stats, mp3_stats, ceiling)
            return kept
        raise RuntimeError(f"{wav} still exceeds {TARGET_TP} dBTP")
    finally:
        if kept is None and original.exists():
            shutil.copy2(original, wav)
            shutil.copy2(mp3_backup, mp3)
        original.unlink(missing_ok=True)
        mp3_backup.unlink(missing_ok=True)


def relimit_all() -> None:
    """Limit files whose true peak is above -1 dBTP, then rebuild every zip."""
    for work_id in ("27", "28", "29", "30", "31"):
        print(f"=== relimit {work_id} ===", flush=True)
        audio = OUT / work_id / "audio"
        for name in NAMES:
            wav = audio / f"{name}.wav"
            mp3 = audio / f"{name}.mp3"
            measure_path = OUT / work_id / "measure" / f"{name}.json"
            data = json.loads(measure_path.read_text(encoding="utf-8"))
            wav_hot = exceeds_tp(data["after"])
            mp3_stats = ebur128(mp3)
            mp3_hot = exceeds_tp(mp3_stats)
            if not wav_hot and not mp3_hot:
                data["mp3"] = mp3_stats
                data["true_peak_limit_db"] = None
                measure_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                print(f"ok {name} wav TP={data['after']['TP']} mp3 TP={mp3_stats['TP']}", flush=True)
                continue
            print(
                f"limit {name} wav TP={data['after']['TP']} mp3 TP={mp3_stats['TP']}",
                flush=True,
            )
            wav_stats, mp3_stats, ceiling = limit_true_peak(wav, mp3)
            if exceeds_tp(wav_stats) or exceeds_tp(mp3_stats):
                raise RuntimeError(f"{work_id} {name} still hot")
            seconds = ffprobe_seconds(wav)
            if abs(seconds - float(data["seconds"])) < 0.001:
                seconds = data["seconds"]
            data["after"] = wav_stats
            data["mp3"] = mp3_stats
            data["seconds"] = seconds
            data["true_peak_limit_db"] = ceiling
            measure_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        script_path = RESEARCH / work_id / "script.md"
        pack_work(work_id, OUT / work_id, script_path.read_text(encoding="utf-8"))
    write_measure_doc()
    print("RELIMIT DONE", flush=True)


def clock_from_seconds(seconds: float) -> str:
    total = int(Decimal(str(seconds)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    minutes, secs = divmod(total, 60)
    return f"{minutes}:{secs:02d}"


def write_measure_doc() -> None:
    titles = {
        "27": "柊真帆",
        "28": "相沢玲",
        "29": "久遠紗英",
        "30": "七瀬葵",
        "31": "水瀬透子",
    }
    lines: list[str] = []
    add = lines.append
    add("# 2026-10-14 音声の実測（27〜31）")
    add("")
    add("公開・出品・申請はしていません。")
    add("")
    add("話者は COEIROINK のアンジーさんです。スタイル 120（のーまる）は、トラック1の「ここから、ささやき」より前です。スタイル 122（ささやき）は、その指示以降と後日談です。試聴はトラック1の頭から、同意の止め台詞までです。セクシーは使っていません。あみたろの声は使いません。")
    add("")
    add("書き出しは 44100 Hz、ステレオ、16 bit です。各トラックの下に、350 Hz でローパスしたブラウンノイズを -28 dB で混ぜています。そのあと ffmpeg の loudnorm（I=-16、TP=-1、LRA=11、linear=true）を2パスかけています。トゥルーピークが -1.0 dBTP を超えたファイルは、8倍オーバーサンプルの alimiter（level は切る、遅延は戻す）で抑えました。天井は -1.2 dB からファイルごとに下げ、WAV と MP3 の ebur128 がどちらも -1.0 dBTP 以下になるいちばん浅い値です。MP3 は 320 kbps です。通しの full.mp3 は作っていません。")
    add("")
    add("秒は ffprobe です。I と TP は WAV、MP3のI と MP3のTP は同じ内容の mp3 です。目標の積分ラウドネスは -16 LUFS です。時計は、秒を四捨五入した分:秒です。本編は part01 から part06 の秒を足し、小数第6位で丸めたものです。おまけと試聴は本編に入れていません。台本の［］は企画のままです。")
    add("")
    integrated: list[float] = []
    ceilings: list[str] = []
    for work_id in ("27", "28", "29", "30", "31"):
        for name in NAMES:
            data = json.loads((OUT / work_id / "measure" / f"{name}.json").read_text(encoding="utf-8"))
            integrated.append(float(data["after"]["I"]))
            integrated.append(float(data["mp3"]["I"]))
            if data.get("true_peak_limit_db") is not None:
                ceilings.append(f"{work_id} {name} {data['true_peak_limit_db']}")
            if exceeds_tp(data["after"]) or exceeds_tp(data["mp3"]):
                raise RuntimeError(f"{work_id} {name} is still above {TARGET_TP}")
    add(
        "WAV も MP3 も、トゥルーピークは -1.0 dBTP 以下です。"
        f"積分ラウドネスは {min(integrated):.1f} から {max(integrated):.1f} です。"
        "リミットした天井（dB）は次のとおりです。"
        + "、".join(ceilings)
        + "。"
    )
    add("")
    for work_id, title in titles.items():
        parts: list[Decimal] = []
        rows: list[str] = []
        for name in NAMES:
            raw = (OUT / work_id / "measure" / f"{name}.json").read_text(encoding="utf-8")
            data = json.loads(raw)
            token = re.search(r'"seconds": ([0-9.]+)', raw)
            if token is None:
                raise RuntimeError(f"seconds missing in {work_id} {name}")
            seconds = token.group(1)
            if name.startswith("part"):
                parts.append(Decimal(seconds))
            rows.append(
                f"| {name} | {seconds} | {clock_from_seconds(float(seconds))} | "
                f"{data['after']['I']} | {data['after']['TP']} | {data['mp3']['I']} | {data['mp3']['TP']} |"
            )
        main = sum(parts).quantize(Decimal("0.000001"))
        add(f"## {work_id} {title}")
        add("")
        add(f"本編は {main} 秒、時計は {clock_from_seconds(float(main))} です。")
        add("")
        add("| ファイル | 秒 | 時計 | I | TP | MP3のI | MP3のTP |")
        add("| --- | --- | --- | --- | --- | --- | --- |")
        add("\n".join(rows))
        add("")
    art = ARTIFACTS
    sizes: list[tuple[int, str]] = []
    split_notes: list[str] = []
    zip_counts: list[str] = []
    for path in art.rglob("*"):
        if path.is_file():
            sizes.append((path.stat().st_size, str(path.relative_to(art))))
    for work_id in titles:
        audio = art / work_id / "audio"
        zips = sorted(audio.glob("*.zip"))
        zip_counts.append(f"{work_id} が {len(zips)}")
        split_stems = sorted(
            {
                re.sub(r"-\d{3}$", "", p.stem)
                for p in (audio / "wav-parts").glob("*.wav")
                if re.search(r"-\d{3}\.wav$", p.name)
            }
        )
        if split_stems:
            split_notes.append(f"{work_id} の " + "、".join(split_stems))
    sizes.sort(reverse=True)
    biggest = sizes[0]
    over = [item for item in sizes if item[0] >= 100 * 1024 * 1024]
    if over:
        raise RuntimeError(f"files at or over 100MiB: {over[:5]}")
    add("## 置き場所")
    add("")
    add("WAV と MP3 は、このリポジトリに入れていません。試聴、分割した WAV、zip は `/opt/cursor/artifacts/booth-2026-10-14/` の各番号の `audio/` です。表紙は同じ番号の `cover/` と、リポジトリの `27/`〜`31/` の `cover/` です。紹介画像は 560×420、サムネイルは 100×100 です。")
    add("")
    add(
        f"リミットのあとに、そのツリーの音声ファイル {len(sizes)} 個を見ました。"
        "100×1024×1024 バイト以上のファイルはありませんでした。"
        f"いちばん大きいのは `{biggest[1]}` の {biggest[0]} バイトです。"
        "zip を作るときの上限は 95×1024×1024 バイトです。それを超える WAV は 480 秒で分割しています。"
        f"分割があるのは、{'、'.join(split_notes)} です。"
        "zip は無圧縮で、中に zip も画像も入れていません。"
        f"zip の数は、{'、'.join(zip_counts)} です。"
    )
    add("")
    add("公開・出品・申請はしていません。")
    add("")
    (RESEARCH / "audio-measure.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "relimit":
        relimit_all()
        return
    ensure_engine()
    for work_id in ("27", "28", "29", "30", "31"):
        process_work(work_id)
    print("ALL DONE", flush=True)


if __name__ == "__main__":
    main()
