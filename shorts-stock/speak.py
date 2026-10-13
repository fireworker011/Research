"""Synthesize pack lines on a local VOICEVOX engine and record measured lengths.

The engine is not started here. It must already be listening, default
http://127.0.0.1:50021. Spoken text is taken only from VOICE.md.
"""

from __future__ import annotations

import json
import os
import subprocess
import urllib.parse
import urllib.request
from pathlib import Path

from pack_meta import STOCK, atempo_chain, iter_packs

BASE = os.environ.get("VOICEVOX_URL", "http://127.0.0.1:50021").rstrip("/")
SPEAKER_NAME = "冥鳴ひまり"
STYLE_NAME = "ノーマル"
CREDIT = "VOICEVOX:冥鳴ひまり"


def _request(url: str, data: bytes | None, content_type: str | None) -> bytes:
    headers = {}
    if content_type is not None:
        headers["Content-Type"] = content_type
    req = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=180) as res:
        return res.read()


def find_speaker() -> tuple[int, str]:
    speakers = json.loads(_request(f"{BASE}/speakers", None, None))
    for speaker in speakers:
        if speaker.get("name") != SPEAKER_NAME:
            continue
        for style in speaker.get("styles", []):
            if style.get("name") == STYLE_NAME:
                version = _request(f"{BASE}/version", None, None).decode().strip()
                if version.startswith('"'):
                    version = json.loads(version)
                return int(style["id"]), version
    names = sorted({speaker.get("name", "") for speaker in speakers})
    raise SystemExit(f"{SPEAKER_NAME} {STYLE_NAME} が無い。エンジンの話者: {names}")


def synthesize(text: str, speaker_id: int) -> tuple[bytes, dict]:
    query_url = f"{BASE}/audio_query?{urllib.parse.urlencode({'text': text, 'speaker': speaker_id})}"
    query = json.loads(_request(query_url, b"", "application/json"))
    wav = _request(
        f"{BASE}/synthesis?speaker={speaker_id}",
        json.dumps(query).encode(),
        "application/json",
    )
    return wav, query


def probe_wav(path: Path) -> tuple[float, int, int]:
    raw = subprocess.check_output(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "a:0",
            "-show_entries",
            "stream=sample_rate,channels",
            "-show_entries",
            "format=duration",
            "-of",
            "json",
            str(path),
        ],
        text=True,
    )
    data = json.loads(raw)
    duration = float(data["format"]["duration"])
    stream = data["streams"][0]
    return duration, int(stream["sample_rate"]), int(stream["channels"])


def fmt_num(value: int | float) -> str:
    number = float(value)
    if number.is_integer():
        return str(int(number))
    return str(number)


def write_fitted(src: Path, dest: Path, rate: float) -> None:
    chain = atempo_chain(rate)
    if not chain:
        dest.write_bytes(src.read_bytes())
        return
    subprocess.check_call(
        ["ffmpeg", "-y", "-nostdin", "-loglevel", "error", "-i", str(src), "-af", chain, str(dest)]
    )


def place_timeline(segments: list[tuple[Path, float]], picture_sec: float, dest: Path) -> None:
    """Place each line at its window start. The picture length is not changed."""
    inputs: list[str] = []
    filters: list[str] = []
    pads: list[str] = []
    for index, (path, start) in enumerate(segments):
        inputs.extend(["-i", str(path)])
        delay = int(round(start * 1000))
        filters.append(
            f"[{index}:a]adelay={delay}|{delay},apad=whole_dur={picture_sec},atrim=0:{picture_sec}[a{index}]"
        )
        pads.append(f"[a{index}]")
    filters.append(
        "".join(pads)
        + f"amix=inputs={len(segments)}:duration=longest:dropout_transition=0:normalize=0,atrim=0:{picture_sec}[a]"
    )
    subprocess.check_call(
        [
            "ffmpeg",
            "-y",
            "-nostdin",
            "-loglevel",
            "error",
            *inputs,
            "-filter_complex",
            ";".join(filters),
            "-map",
            "[a]",
            str(dest),
        ]
    )


def fits_note(duration: float | None, available: float | None) -> str:
    if duration is None or available is None:
        return "声は作らない"
    rate = duration / available
    if rate <= 1.0 + 1e-3:
        return "入る"
    if rate <= 1.1:
        return f"自然長が区間より長い。finish.sh は声を {rate:.3f} 倍にして収め、絵は切らない"
    return f"窓の1.1倍を超える（{rate:.3f}倍）。文を短くする。倍速では収めない"


def main() -> None:
    speaker_id, version = find_speaker()
    packs = iter_packs()
    spoken = 0
    silent = 0
    for pack in packs:
        voice_dir = pack["dir"] / "voice"
        voice_dir.mkdir(exist_ok=True)
        voice = pack["voice"]
        record: dict = {
            "narration": voice["narration"],
            "text": voice["text"],
            "pack": pack["rel"],
            "line": pack["line"],
            "picture_sec": pack["picture_sec"],
            "window_start_sec": voice["window_start_sec"],
            "window_end_sec": voice["window_end_sec"],
        }
        if not voice["narration"]:
            record.update(
                {
                    "wav": None,
                    "duration_sec": None,
                    "sample_rate": None,
                    "channels": None,
                    "engine": None,
                    "reason": "ナレーションは無し。心の声も無し。",
                }
            )
            silent += 1
        elif voice.get("lines"):
            fitted: list[tuple[Path, float]] = []
            line_records: list[dict] = []
            sample_rate = None
            channels = None
            speed_scale = None
            for index, item in enumerate(voice["lines"], start=1):
                wav, query = synthesize(item["text"], speaker_id)
                raw_path = voice_dir / f"line-{index:02d}.wav"
                raw_path.write_bytes(wav)
                duration, sample_rate, channels = probe_wav(raw_path)
                available = float(item["window_end_sec"]) - float(item["window_start_sec"])
                rate = duration / available if duration > available else 1.0
                fit_path = voice_dir / f"line-{index:02d}-fit.wav"
                write_fitted(raw_path, fit_path, rate)
                fitted.append((fit_path, float(item["window_start_sec"])))
                speed_scale = query.get("speedScale")
                line_records.append(
                    {
                        "text": item["text"],
                        "window_start_sec": item["window_start_sec"],
                        "window_end_sec": item["window_end_sec"],
                        "duration_sec": duration,
                        "wav": raw_path.name,
                    }
                )
            timeline = voice_dir / "narration.wav"
            place_timeline(fitted, float(pack["picture_sec"]), timeline)
            for path, _start in fitted:
                path.unlink()
            timeline_sec, _sample_rate, _channels = probe_wav(timeline)
            record.update(
                {
                    "wav": "narration.wav",
                    "duration_sec": timeline_sec,
                    "lines": line_records,
                    "sample_rate": sample_rate,
                    "channels": channels,
                    "engine": "VOICEVOX",
                    "engine_version": version,
                    "speaker_name": SPEAKER_NAME,
                    "speaker_style": STYLE_NAME,
                    "speaker_id": speaker_id,
                    "speed_scale": speed_scale,
                    "pitch_scale": query.get("pitchScale"),
                    "intonation_scale": query.get("intonationScale"),
                    "credit": CREDIT,
                    "placed": "各文を窓の頭に置いた。窓を超えるときだけ、その文を速くしてから置いた。",
                }
            )
            spoken += 1
        else:
            wav, query = synthesize(voice["text"], speaker_id)
            wav_path = voice_dir / "narration.wav"
            wav_path.write_bytes(wav)
            duration, sample_rate, channels = probe_wav(wav_path)
            record.update(
                {
                    "wav": "narration.wav",
                    "duration_sec": duration,
                    "sample_rate": sample_rate,
                    "channels": channels,
                    "engine": "VOICEVOX",
                    "engine_version": version,
                    "speaker_name": SPEAKER_NAME,
                    "speaker_style": STYLE_NAME,
                    "speaker_id": speaker_id,
                    "speed_scale": query.get("speedScale"),
                    "pitch_scale": query.get("pitchScale"),
                    "intonation_scale": query.get("intonationScale"),
                    "credit": CREDIT,
                }
            )
            spoken += 1
        (voice_dir / "speech-length.json").write_text(
            json.dumps(record, ensure_ascii=False, indent=2) + "\n"
        )
        if record.get("lines"):
            label = " / ".join(item["text"] for item in record["lines"])
        else:
            label = record["text"] if record["text"] else "（無し）"
        print(f"{pack['rel']} {label} {record['duration_sec']}")

    if spoken != len(packs) or silent != 0:
        raise SystemExit(f"声 {spoken} 無言 {silent}（{len(packs)} と 0 であるべき）")
    too_long = []
    for pack in packs:
        voice = pack["voice"]
        if not voice["narration"]:
            continue
        data = json.loads((pack["dir"] / "voice" / "speech-length.json").read_text())
        if data.get("lines"):
            for item in data["lines"]:
                available = float(item["window_end_sec"]) - float(item["window_start_sec"])
                rate = float(item["duration_sec"]) / available
                if rate > 1.1:
                    too_long.append(f"{pack['rel']} {rate:.3f}倍 {item['text']}")
            continue
        if voice["window_start_sec"] is None:
            available = float(pack["picture_sec"])
        else:
            available = float(voice["window_end_sec"]) - float(voice["window_start_sec"])
        rate = float(data["duration_sec"]) / available
        if rate > 1.1:
            too_long.append(f"{pack['rel']} {rate:.3f}倍 {voice['text']}")
    if too_long:
        raise SystemExit("窓の1.1倍を超える。倍速にせず文を短くする:\n" + "\n".join(too_long))
    write_summary(packs)
    print(f"spoke {spoken} silent {silent} speaker_id={speaker_id} version={version}")


def write_summary(packs: list[dict]) -> None:
    rows = ["# 声の長さ", ""]
    rows.append("長さは書き出した WAV を ffprobe で測った秒。推定ではない。")
    rows.append(f"話者は {SPEAKER_NAME}（{STYLE_NAME}）。ペットのナレーション、婚活の1文、美容の1文、すべてこの声。")
    rows.append(f"この声を投稿に使うときは説明へ `{CREDIT}` を書く。規約: https://www.meimeihimari.com/terms-of-use")
    rows.append("最終の置き位置は絵ができたあと。`finish.sh` は絵の秒を変えず、声が窓を 1.1 倍以内ではみ出すときだけ声を速くする。")
    rows.append("1.1 倍を超えるときは倍速にせず、文を短くして測り直す。ペットは 2026-10-12 の 10 本も日記の 1 文。")
    rows.append("`2026-10-13/pet/06-white-tail` の文は「しっぽの先、1回。」。")
    rows.append("2026-10-14 はペット、婚活、美容を 10 本ずつ足した。説明には `VOICEVOX:冥鳴ひまり` を書いてある。")
    rows.append("2026-10-14b は台本のショットごとに1文。Imagine は保留（未開始）。")
    rows.append("")
    rows.append("| 順 | パック | 文 | 測った秒 | 置く区間 | 絵の秒 | 収まり |")
    rows.append("| --- | --- | --- | --- | --- | --- | --- |")
    for pack in packs:
        data = json.loads((pack["dir"] / "voice" / "speech-length.json").read_text())
        if data.get("lines"):
            for item in data["lines"]:
                window = f"{fmt_num(item['window_start_sec'])}–{fmt_num(item['window_end_sec'])}秒"
                available = float(item["window_end_sec"]) - float(item["window_start_sec"])
                note = fits_note(float(item["duration_sec"]), available)
                rows.append(
                    f"| {pack['order']} | `{pack['rel']}` | {item['text']} | {float(item['duration_sec']):.3f} | {window} | {data['picture_sec']} | {note} |"
                )
            continue
        if data["window_start_sec"] is None:
            window = "指定なし（絵の頭から）"
            available = float(data["picture_sec"])
        else:
            window = f"{data['window_start_sec']}–{data['window_end_sec']}秒"
            available = float(data["window_end_sec"]) - float(data["window_start_sec"])
        duration = data["duration_sec"]
        duration_cell = "—" if duration is None else f"{duration:.3f}"
        text = "（ナレーション無し）" if not data["narration"] else data["text"]
        note = fits_note(None if duration is None else float(duration), None if duration is None else available)
        rows.append(
            f"| {pack['order']} | `{pack['rel']}` | {text} | {duration_cell} | {window} | {data['picture_sec']} | {note} |"
        )
    rows.append("")
    (STOCK / "SPEECH-LENGTHS.md").write_text("\n".join(rows))


if __name__ == "__main__":
    main()
