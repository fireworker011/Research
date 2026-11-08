"""TTS と BGM/SE を混ぜて master_audio.wav と audio_timing.json を書く。

第一候補はローカルの VOICEVOX (http://127.0.0.1:50021)。等倍速。
つながらないときはエラーで止まる。別のTTSには落とさない。
--dummy-tts は無音で長さだけ作り、target_duration_sec に合わせる。
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
import wave
from pathlib import Path

import numpy as np

SR = 24000
ROOT = Path(__file__).resolve().parents[1]
BGM_DB = -18.0
SMALL_KANA = set("ぁぃぅぇぉゃゅょっァィゥェォャュョッ")


def log(message: str) -> None:
    print(message, file=sys.stderr)


def mora_count(text: str) -> float:
    total = 0.0
    for ch in text.strip():
        if ch.isspace() or ch in "、。！？「」…・":
            total += 0.35
        elif ch in SMALL_KANA:
            total += 0.25
        else:
            total += 1.0
    return total


def speech_units(job: dict) -> list[dict]:
    units = []
    for seg in job["segments"]:
        units.append(
            {
                "kind": "segment",
                "segment_id": seg.get("id"),
                "scene": seg.get("scene"),
                "text": seg.get("subtitle") or "",
                "pause_after_ms": int(seg.get("pause_after_ms") or 0),
                "se": seg.get("se"),
            }
        )
    choice = job.get("choice_card") or {}
    units.append(
        {
            "kind": "choice_card",
            "segment_id": None,
            "scene": "choice_card",
            "text": choice.get("narration") or "",
            "pause_after_ms": 0,
            "se": None,
        }
    )
    day_end = job.get("day_end_card") or {}
    units.append(
        {
            "kind": "day_end_card",
            "segment_id": None,
            "scene": "day_end_card",
            "text": day_end.get("narration") or "",
            "pause_after_ms": 0,
            "se": None,
        }
    )
    promo = job.get("promo_outro") or {}
    if promo.get("enabled"):
        units.append(
            {
                "kind": "promo_outro",
                "segment_id": None,
                "scene": "promo_outro",
                "text": promo.get("narration") or "",
                "pause_after_ms": 0,
                "se": None,
                "steps": promo.get("steps") or [],
            }
        )
    return units


def ensure_assets(names: list[str]) -> None:
    bgm = ROOT / "assets" / "bgm" / "dark_ambient_drone.wav"
    missing = not bgm.exists()
    for name in names:
        if name and not (ROOT / "assets" / "se" / f"{name}.wav").exists():
            missing = True
    if not missing:
        return
    script = ROOT / "tools" / "make_assets.py"
    log("BGM/SE が無いので tools/make_assets.py で生成します")
    result = subprocess.run([sys.executable, str(script)], check=False)
    if result.returncode != 0:
        raise SystemExit("make_assets.py が失敗しました")
    if not bgm.exists():
        raise SystemExit(f"BGM が生成されませんでした: {bgm}")
    for name in names:
        path = ROOT / "assets" / "se" / f"{name}.wav"
        if name and not path.exists():
            raise SystemExit(f"SE がありません: {name}")


def write_wav(path: Path, samples: np.ndarray, channels: int, sr: int = SR) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pcm = np.clip(np.asarray(samples, dtype=np.float32) * 32767.0, -32768, 32767).astype(np.int16)
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(channels)
        handle.setsampwidth(2)
        handle.setframerate(sr)
        handle.writeframes(pcm.tobytes())


def write_silence(path: Path, seconds: float) -> None:
    frames = max(1, int(round(seconds * SR)))
    write_wav(path, np.zeros(frames, dtype=np.float32), channels=1)


def wav_duration(path: Path) -> float:
    with wave.open(str(path), "rb") as handle:
        if handle.getframerate() <= 0:
            raise SystemExit(f"WAVのサンプルレートが不正です: {path}")
        return handle.getnframes() / float(handle.getframerate())


def load_mono(path: Path) -> tuple[np.ndarray, int]:
    with wave.open(str(path), "rb") as handle:
        sr = handle.getframerate()
        channels = handle.getnchannels()
        width = handle.getsampwidth()
        frames = handle.getnframes()
        raw = handle.readframes(frames)
    if width != 2:
        raise SystemExit(f"16bit WAV だけ読めます: {path}")
    data = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    if channels > 1:
        data = data.reshape(-1, channels).mean(axis=1)
    return data, sr


def resample(data: np.ndarray, src_sr: int, dst_sr: int) -> np.ndarray:
    if src_sr == dst_sr or len(data) == 0:
        return data.astype(np.float32)
    dst_n = max(1, int(round(len(data) * dst_sr / src_sr)))
    src_x = np.linspace(0.0, 1.0, len(data), endpoint=False)
    dst_x = np.linspace(0.0, 1.0, dst_n, endpoint=False)
    return np.interp(dst_x, src_x, data).astype(np.float32)


def voicevox_wav(text: str, speaker: int, base_url: str) -> bytes:
    query = urllib.parse.urlencode({"text": text, "speaker": str(speaker)})
    query_url = f"{base_url.rstrip('/')}/audio_query?{query}"
    request = urllib.request.Request(query_url, data=b"", method="POST")
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")
        raise SystemExit(
            f"VOICEVOXの audio_query に失敗しました (speaker={speaker}, HTTP {exc.code})。"
            f"別のTTSには切り替えません。{detail}"
        ) from exc
    except urllib.error.URLError as exc:
        raise SystemExit(
            f"VOICEVOXに接続できません ({base_url})。エンジンを起動してください。"
            f"別のTTSには切り替えません。詳細: {exc.reason}"
        ) from exc
    payload["speedScale"] = 1.0
    synth_url = f"{base_url.rstrip('/')}/synthesis?speaker={speaker}"
    body = json.dumps(payload).encode("utf-8")
    synth = urllib.request.Request(
        synth_url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(synth, timeout=180) as response:
            return response.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")
        raise SystemExit(
            f"VOICEVOXの合成に失敗しました (speaker={speaker}, HTTP {exc.code})。"
            f"別のTTSには切り替えません。{detail}"
        ) from exc
    except urllib.error.URLError as exc:
        raise SystemExit(
            f"VOICEVOXに接続できません ({base_url})。エンジンを起動してください。"
            f"別のTTSには切り替えません。詳細: {exc.reason}"
        ) from exc


def timeline(units: list[dict], audio_lengths: list[float]) -> tuple[list[dict], float]:
    items = []
    cursor = 0.0
    for index, (unit, audio_sec) in enumerate(zip(units, audio_lengths), start=1):
        audio_sec = max(0.05, float(audio_sec))
        pause = max(0.0, unit["pause_after_ms"] / 1000.0)
        pad = 0.0
        if unit["kind"] == "promo_outro":
            step_sum = sum(float(step.get("duration_sec") or 0) for step in unit.get("steps") or [])
            need = max(audio_sec + pause, step_sum)
            pad = max(0.0, need - audio_sec - pause)
        start = cursor
        end = cursor + audio_sec + pause + pad
        items.append(
            {
                "index": index,
                "kind": unit["kind"],
                "segment_id": unit["segment_id"],
                "scene": unit["scene"],
                "text": unit["text"],
                "wav": f"seg_{index:02d}.wav",
                "se": unit["se"],
                "audio_sec": round(audio_sec, 4),
                "pause_after_ms": unit["pause_after_ms"],
                "pad_sec": round(pad, 4),
                "start_sec": round(start, 4),
                "end_sec": round(end, 4),
            }
        )
        cursor = end
    return items, cursor


def pad_to_target(items: list[dict], total: float, target: float) -> tuple[list[dict], float]:
    if target <= 0 or total >= target or target > 95.0:
        return items, total
    extra = target - total
    items[-1]["end_sec"] = round(items[-1]["end_sec"] + extra, 4)
    items[-1]["pad_sec"] = round(items[-1]["pad_sec"] + extra, 4)
    return items, target


def dummy_lengths(units: list[dict], target: float) -> list[float]:
    weights = [max(1.0, mora_count(unit["text"])) for unit in units]

    def lengths(rate: float) -> list[float]:
        return [max(0.35, 0.2 + weight * rate) for weight in weights]

    lo, hi = 0.01, 0.8
    best = lo
    for _ in range(28):
        mid = (lo + hi) / 2.0
        _, total = timeline(units, lengths(mid))
        if total > target:
            hi = mid
        else:
            lo = mid
            best = mid
    return lengths(best)


def synthesize_real(units: list[dict], out_dir: Path, speaker: int, base_url: str) -> list[float]:
    lengths = []
    for index, unit in enumerate(units, start=1):
        dest = out_dir / f"seg_{index:02d}.wav"
        text = (unit["text"] or "").strip()
        if not text:
            write_silence(dest, 0.35)
            lengths.append(0.35)
            continue
        dest.write_bytes(voicevox_wav(text, speaker, base_url))
        lengths.append(wav_duration(dest))
        log(f"VOICEVOX seg_{index:02d} {lengths[-1]:.2f}s speaker={speaker}")
    return lengths


def mix_master(items: list[dict], out_dir: Path, duration: float) -> None:
    total = max(1, int(round(duration * SR)))
    mix = np.zeros(total, dtype=np.float32)
    drone, drone_sr = load_mono(ROOT / "assets" / "bgm" / "dark_ambient_drone.wav")
    drone = resample(drone, drone_sr, SR)
    if len(drone) == 0:
        raise SystemExit("BGMが空です")
    repeats = int(np.ceil(total / len(drone)))
    bed = np.tile(drone, repeats)[:total] * (10.0 ** (BGM_DB / 20.0))
    mix += bed
    for item in items:
        start = int(round(item["start_sec"] * SR))
        wav_path = out_dir / item["wav"]
        speech, speech_sr = load_mono(wav_path)
        speech = resample(speech, speech_sr, SR) * 0.9
        end = min(total, start + len(speech))
        if end > start:
            mix[start:end] += speech[: end - start]
        if item.get("se"):
            se_path = ROOT / "assets" / "se" / f"{item['se']}.wav"
            se, se_sr = load_mono(se_path)
            se = resample(se, se_sr, SR) * 0.55
            se_end = min(total, start + len(se))
            if se_end > start:
                mix[start:se_end] += se[: se_end - start]
    peak = float(np.max(np.abs(mix))) if len(mix) else 1.0
    if peak > 0.98:
        mix *= 0.98 / peak
    stereo = np.column_stack([mix, mix])
    write_wav(out_dir / "master_audio.wav", stereo, channels=2)


def build(job_path: Path, speaker: int, dummy: bool, base_url: str, out_dir: Path) -> dict:
    job = json.loads(job_path.read_text(encoding="utf-8"))
    units = speech_units(job)
    names = [unit.get("se") for unit in units if unit.get("se")]
    ensure_assets(names)
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob("seg_*.wav"):
        old.unlink()
    target = float(job.get("target_duration_sec") or 0.0)
    if dummy:
        log("dummy-tts: VOICEVOXは呼びません。無音で長さだけ作ります。")
        if target <= 0:
            raise SystemExit("dummy-tts には job の target_duration_sec が必要です")
        lengths = dummy_lengths(units, target)
        for index, length in enumerate(lengths, start=1):
            write_silence(out_dir / f"seg_{index:02d}.wav", length)
    else:
        log(f"VOICEVOX {base_url} speaker={speaker} speedScale=1.0")
        lengths = synthesize_real(units, out_dir, speaker, base_url)
    items, total = timeline(units, lengths)
    items, total = pad_to_target(items, total, target)
    timing = {
        "job_id": job["job_id"],
        "generator": "build_audio",
        "dummy_tts": dummy,
        "speaker": None if dummy else speaker,
        "sample_rate": SR,
        "duration_sec": round(total, 4),
        "items": items,
    }
    (out_dir / "audio_timing.json").write_text(
        json.dumps(timing, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    mix_master(items, out_dir, total)
    log(f"audio {total:.3f}s -> {out_dir / 'master_audio.wav'}")
    return timing


def main() -> None:
    parser = argparse.ArgumentParser(description="VOICEVOX と BGM/SE から master_audio.wav を作る")
    parser.add_argument("--job", required=True)
    parser.add_argument("--speaker", type=int, default=13, help="VOICEVOX の話者ID。既定は低音の男性（青山龍星ノーマル=13）")
    parser.add_argument("--dummy-tts", action="store_true", help="無音で長さだけ作る。VOICEVOXには接続しない")
    parser.add_argument("--voicevox-url", default="http://127.0.0.1:50021")
    parser.add_argument("--out-dir", default="out/temp_audio")
    args = parser.parse_args()
    if args.speaker < 0:
        raise SystemExit("--speaker は 0 以上の話者IDにしてください")
    out_dir = Path(args.out_dir)
    if not out_dir.is_absolute():
        out_dir = Path.cwd() / out_dir
    build(Path(args.job), args.speaker, args.dummy_tts, args.voicevox_url, out_dir)


if __name__ == "__main__":
    main()
